"""BRIDGE GOV-PCE YouTube collector.

Measures public consumption and response, not publishing volume.  The module
uses verified channel mappings only, stores a daily snapshot, and writes
auditable B/R signals to the existing Signal Ledger.  Channel search is used
only to create review candidates; it never changes a score automatically.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import statistics
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .core import KST, SupabaseRest, load_methodology, now_kst, stable_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "youtube_data_api"
CHANNELS_FILE = ROOT / "config" / "gov_youtube_channels.json"
IDENTITY_FILE = ROOT / "config" / "gov_identity_reviews.json"
SNAPSHOT_DIR = ROOT / "data" / "gov_youtube" / "snapshots"
CANDIDATE_FILE = ROOT / "data" / "gov_youtube" / "channel_candidates.json"
API = "https://www.googleapis.com/youtube/v3"


def percentile_scores(values: dict[str, float]) -> dict[str, float]:
    """Return deterministic 0..100 mid-rank percentiles; ties remain equal."""
    if not values:
        return {}
    ordered = sorted(values.values())
    if len(ordered) == 1:
        return {key: 50.0 for key in values}
    result = {}
    for key, value in values.items():
        first = ordered.index(value)
        last = len(ordered) - 1 - ordered[::-1].index(value)
        result[key] = round(((first + last) / 2) / (len(ordered) - 1) * 100, 2)
    return result


def public_name_variants(entity: dict[str, Any]) -> set[str]:
    names = {entity["name"], *(entity.get("aliases") or [])}
    replacements = {
        "서울특별시": "서울시", "부산광역시": "부산시", "대구광역시": "대구시",
        "인천광역시": "인천시", "광주광역시": "광주시", "대전광역시": "대전시",
        "울산광역시": "울산시", "세종특별자치시": "세종시",
        "제주특별자치도": "제주도", "강원특별자치도": "강원도",
        "전북특별자치도": "전북"
    }
    if entity["name"] in replacements:
        names.add(replacements[entity["name"]])
    return {"".join(ch for ch in name.casefold() if ch.isalnum()) for name in names if name}


def title_matches_entity(title: str, entity: dict[str, Any]) -> bool:
    normalized = "".join(ch for ch in title.casefold() if ch.isalnum())
    return any(len(name) >= 3 and name in normalized for name in public_name_variants(entity))


def approved_identity_score(external_id: str, reviews: dict[str, Any]) -> float | None:
    review = (reviews.get("reviews") or {}).get(external_id) or {}
    if review.get("status") != "approved" or not review.get("evidence_urls"):
        return None
    return max(0.0, min(100.0, 100.0 - float(review.get("penalty") or 0)))


class YouTube:
    def __init__(self, key: str):
        if not key:
            raise RuntimeError("YOUTUBE_API_KEY is required")
        self.key = key

    def get(self, resource: str, **params) -> dict[str, Any]:
        query = urllib.parse.urlencode({**params, "key": self.key})
        request = urllib.request.Request(
            f"{API}/{resource}?{query}",
            headers={"User-Agent": "SignalBridge-GOV-PCE/1.0 (+https://bridgebrand.co.kr)"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def channel(self, *, channel_id: str | None = None, handle: str | None = None, username: str | None = None) -> dict[str, Any] | None:
        params = {"part": "snippet,statistics,contentDetails"}
        if channel_id:
            params["id"] = channel_id
        elif handle:
            params["forHandle"] = handle.lstrip("@")
        elif username:
            params["forUsername"] = username
        else:
            return None
        items = self.get("channels", **params).get("items") or []
        return items[0] if items else None

    def latest_videos(self, uploads_playlist: str, limit: int = 25) -> list[dict[str, Any]]:
        items = self.get("playlistItems", part="contentDetails", playlistId=uploads_playlist,
                         maxResults=min(50, limit)).get("items") or []
        ids = [item.get("contentDetails", {}).get("videoId") for item in items]
        ids = [value for value in ids if value]
        if not ids:
            return []
        return self.get("videos", part="snippet,statistics", id=",".join(ids)).get("items") or []

    def search_channel_candidate(self, query: str) -> dict[str, Any] | None:
        items = self.get("search", part="snippet", q=query, type="channel", maxResults=1,
                         regionCode="KR").get("items") or []
        return items[0] if items else None


def video_window_metrics(videos: list[dict[str, Any]], as_of: dt.date, days: int = 28) -> dict[str, float]:
    start = as_of - dt.timedelta(days=days - 1)
    rows = []
    titles = []
    action_rows = []
    action_pattern = re.compile(r"(신청|참여|접수|공모|모집|예약|투표|캠페인|설문|제안|신고)")
    for video in videos:
        published = (video.get("snippet") or {}).get("publishedAt")
        try:
            date = dt.datetime.fromisoformat(str(published).replace("Z", "+00:00")).astimezone(KST).date()
        except (TypeError, ValueError):
            continue
        if not start <= date <= as_of:
            continue
        stats = video.get("statistics") or {}
        snippet = video.get("snippet") or {}
        views = max(0, int(stats.get("viewCount") or 0))
        likes = max(0, int(stats.get("likeCount") or 0))
        comments = max(0, int(stats.get("commentCount") or 0))
        age = max(1, (as_of - date).days + 1)
        rows.append((views, likes, comments, views / age))
        title = str(snippet.get("title") or "").strip()
        if title:
            titles.append(title)
        if action_pattern.search(title + " " + str(snippet.get("description") or "")):
            action_rows.append((views, likes, comments))
    views = sum(row[0] for row in rows)
    # Identity is observed as continuity of public messages, not guessed from
    # reputation. Repeated meaningful title tokens indicate a recognisable
    # communication agenda; small samples remain unscored.
    stop = {"공식", "영상", "대한민국", "브리핑", "뉴스", "안내", "이야기", "함께", "위한"}
    tokens = [token for title in titles for token in re.findall(r"[가-힣A-Za-z0-9]{2,}", title)
              if token not in stop]
    token_counts = {token: tokens.count(token) for token in set(tokens)}
    repeated = sum(count for count in token_counts.values() if count >= 2)
    identity_continuity = (repeated / len(tokens) * 100) if len(titles) >= 5 and tokens else None
    action_views = sum(row[0] for row in action_rows)
    action_engagement = ((sum(row[1] for row in action_rows) + 2 * sum(row[2] for row in action_rows))
                         / max(1, action_views) * 1000)
    return {
        "output_count": len(rows),
        "views": views,
        "median_views": statistics.median([row[0] for row in rows]) if rows else 0.0,
        "median_views_per_day": statistics.median([row[3] for row in rows]) if rows else 0.0,
        "likes": sum(row[1] for row in rows),
        "comments": sum(row[2] for row in rows),
        "engagement_per_1000_views": ((sum(row[1] for row in rows) + 2 * sum(row[2] for row in rows))
                                      / max(1, views) * 1000),
        "identity_continuity": identity_continuity,
        "action_content_count": len(action_rows),
        "action_engagement_per_1000_views": action_engagement,
    }


def score_cohorts(rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, float]]:
    scores: dict[str, dict[str, float]] = {}
    for prefix in ("GOV-M", "GOV-C"):
        cohort = {key: value for key, value in rows.items() if key.startswith(prefix)}
        reach = percentile_scores({key: math.log1p(value["metrics"]["views"]) for key, value in cohort.items()})
        median = percentile_scores({key: math.log1p(value["metrics"]["median_views_per_day"]) for key, value in cohort.items()})
        response = percentile_scores({key: value["metrics"]["engagement_per_1000_views"] for key, value in cohort.items()})
        identity = percentile_scores({key: value["metrics"].get("identity_continuity") for key, value in cohort.items()
                                      if value["metrics"].get("identity_continuity") is not None})
        action = percentile_scores({key: math.log1p(value["metrics"].get("action_content_count", 0))
                                    + math.log1p(value["metrics"].get("action_engagement_per_1000_views", 0))
                                    for key, value in cohort.items() if value["metrics"].get("action_content_count", 0) > 0})
        for key in cohort:
            scores[key] = {
                "B": round(0.65 * reach[key] + 0.35 * median[key], 2),
                "R": response[key],
            }
            if key in identity:
                scores[key]["I"] = identity[key]
            if key in action:
                scores[key]["G"] = action[key]
    return scores


def previous_snapshot(as_of: dt.date) -> dict[str, Any]:
    candidates = sorted(path for path in SNAPSHOT_DIR.glob("*.json") if path.stem < as_of.isoformat())
    if not candidates:
        return {}
    try:
        return json.loads(candidates[-1].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def collect(as_of: dt.date, discover_limit: int = 5) -> dict[str, Any]:
    client = YouTube(os.environ.get("YOUTUBE_API_KEY", ""))
    db = SupabaseRest()
    cfg = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
    reviews = json.loads(IDENTITY_FILE.read_text(encoding="utf-8"))
    entities = db.select("bridge_entities", "select=id,external_id,name,aliases,subcategory&domain=eq.GOV&active=eq.true")
    entity_by_external = {row["external_id"]: row for row in entities}
    mappings = cfg.get("channels") or {}

    db.upsert("bridge_source_registry", [{
        "id": SOURCE_ID, "name": "YouTube Data API — verified GOV channels",
        "family": "public_data", "base_url": "https://www.googleapis.com/youtube/v3",
        "terms_url": "https://developers.google.com/youtube/terms/api-services-terms-of-service",
        "enabled": True, "collection_mode": "api", "default_refresh": "1 day"
    }], "id")
    start = dt.datetime.combine(as_of, dt.time(5, 15), tzinfo=KST)
    run = db.insert("bridge_collection_runs", [{
        "source_id": SOURCE_ID, "status": "running", "window_start": start.isoformat(),
        "window_end": (start + dt.timedelta(days=1)).isoformat(),
        "diagnostics": {"module": "GOV-PCE", "mapping_version": cfg.get("version")}
    }])[0]
    run_id = run["id"]
    collected: dict[str, dict[str, Any]] = {}
    candidates: dict[str, Any] = {}
    failures = []
    try:
        for external_id, mapping in mappings.items():
            entity = entity_by_external.get(external_id)
            if not entity:
                continue
            try:
                if mapping.get('status')!='verified' or not mapping.get('evidence_urls'):
                    candidates[external_id]={'reason':'ownership_evidence_required'}
                    continue
                verified_date=str(mapping.get('verified_at') or '')[:10]
                if not verified_date or (as_of-dt.date.fromisoformat(verified_date)).days>30:
                    candidates[external_id]={'reason':'ownership_verification_expired'}
                    continue
                channel = client.channel(channel_id=mapping.get('channel_id'),handle=mapping.get('handle'),username=mapping.get('username'))
                if not channel:
                    failures.append({"external_id": external_id, "reason": "channel_not_found"})
                    continue
                if mapping.get("status") == "verify_title" and not title_matches_entity(channel["snippet"]["title"], entity):
                    candidates[external_id] = {"channel_id": channel["id"], "title": channel["snippet"]["title"], "reason": "title_mismatch"}
                    continue
                if mapping.get("status") not in {"verified", "verify_title"}:
                    continue
                uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
                videos = client.latest_videos(uploads)
                stats = channel.get("statistics") or {}
                collected[external_id] = {
                    "entity": entity,
                    "channel": {"id": channel["id"], "title": channel["snippet"]["title"],
                                "subscribers": None if stats.get("hiddenSubscriberCount") else int(stats.get("subscriberCount") or 0),
                                "total_views": int(stats.get("viewCount") or 0), "video_count": int(stats.get("videoCount") or 0)},
                    "metrics": video_window_metrics(videos, as_of),
                }
            except Exception as exc:  # one unavailable channel must not stop T100
                failures.append({"external_id": external_id, "reason": type(exc).__name__})

        # Search is deliberately review-only and rotated to protect quota.
        unmapped = [row for row in entities if row["external_id"] not in mappings]
        offset = as_of.toordinal() % max(1, len(unmapped)) if unmapped else 0
        rotated = (unmapped[offset:] + unmapped[:offset])[:max(0, discover_limit)]
        for entity in rotated:
            try:
                found = client.search_channel_candidate(f'{entity["name"]} 공식 유튜브')
                if found:
                    candidates[entity["external_id"]] = {
                        "channel_id": found["snippet"]["channelId"], "title": found["snippet"]["title"],
                        "reason": "awaiting_human_verification"
                    }
            except Exception as exc:
                failures.append({"external_id": entity["external_id"], "reason": type(exc).__name__})

        axis_scores = score_cohorts(collected)
        previous = previous_snapshot(as_of)
        raw_rows = []
        staged = []
        snapshot = {"as_of_date": as_of.isoformat(), "mapping_version": cfg.get("version"), "entities": {}}
        for external_id, row in collected.items():
            entity = row["entity"]
            scores = axis_scores[external_id]
            prior = (previous.get("entities") or {}).get(external_id, {})
            total_delta = max(0, row["channel"]["total_views"] - int((prior.get("channel") or {}).get("total_views") or row["channel"]["total_views"]))
            identity = approved_identity_score(external_id, reviews)
            observed_identity = scores.get("I")
            if identity is None:
                identity = observed_identity
            snapshot["entities"][external_id] = {"channel": row["channel"], "metrics": row["metrics"],
                                                        "daily_total_view_delta": total_delta, "scores": scores,
                                                        "identity_score": identity}
            content_hash = stable_hash(SOURCE_ID, external_id, as_of.isoformat(), row["channel"]["id"])
            raw_rows.append({
                "source_id": SOURCE_ID, "collection_run_id": run_id,
                "source_item_id": f'{row["channel"]["id"]}:{as_of.isoformat()}',
                "canonical_url": f'https://www.youtube.com/channel/{row["channel"]["id"]}',
                "title": f'{entity["name"]} 공식 유튜브 공공소통 관측', "publisher": entity["name"],
                "published_at": start.isoformat(), "payload": snapshot["entities"][external_id],
                "content_hash": content_hash,
            })
            staged.extend([(entity, content_hash, "B", "gov_pce_reach", scores["B"], 0.85),
                           (entity, content_hash, "R", "gov_pce_response", scores["R"], 0.75)])
            if identity is not None:
                staged.append((entity, content_hash, "I", "gov_pce_identity_continuity", identity, 0.70))
            if scores.get("G") is not None:
                staged.append((entity, content_hash, "G", "gov_pce_action_response", scores["G"], 0.60))

        inserted = db.upsert("bridge_raw_items", raw_rows, "source_id,content_hash")
        raw_ids = {row["content_hash"]: row["id"] for row in inserted}
        signals = []
        for entity, content_hash, axis, signal_type, magnitude, confidence in staged:
            if content_hash not in raw_ids:
                continue
            signals.append({
                "entity_id": entity["id"], "raw_item_id": raw_ids[content_hash], "source_id": SOURCE_ID,
                "axis": axis, "signal_type": signal_type, "direction": 1, "magnitude": magnitude,
                "confidence": confidence, "occurred_at": start.isoformat(), "review_status": "auto",
                "rationale": "검증된 공식 채널의 도달·반응을 동일 기관군 내 강건 백분위로 관측",
                "ruleset_version": load_methodology()["version"],
            })
        db.upsert("bridge_signals", signals, "entity_id,raw_item_id,axis,signal_type")
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        (SNAPSHOT_DIR / f"{as_of.isoformat()}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        CANDIDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CANDIDATE_FILE.write_text(json.dumps({"as_of_date": as_of.isoformat(), "candidates": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")
        status = "partial" if failures else "success"
        db.patch("bridge_collection_runs", {"status": status, "finished_at": now_kst().isoformat(),
                 "fetched_count": len(collected), "accepted_count": len(signals), "rejected_count": len(candidates),
                 "diagnostics": {"mapped": len(collected), "universe": len(entities), "failures": failures[:20]}}, f"id=eq.{run_id}")
        return {"status": status, "mapped": len(collected), "universe": len(entities), "signals": len(signals), "candidates": len(candidates)}
    except Exception as exc:
        db.patch("bridge_collection_runs", {"status": "failed", "finished_at": now_kst().isoformat(),
                 "error_code": type(exc).__name__, "error_detail": str(exc)[:2000]}, f"id=eq.{run_id}")
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Collect verified GOV YouTube PCE signals")
    parser.add_argument("--date")
    parser.add_argument("--discover-limit", type=int, default=5)
    args = parser.parse_args(argv)
    as_of = dt.date.fromisoformat(args.date) if args.date else now_kst().date()
    print(json.dumps(collect(as_of, args.discover_limit), ensure_ascii=False))


if __name__ == "__main__":
    main()
