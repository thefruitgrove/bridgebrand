from __future__ import annotations

import argparse
import csv
import email.utils
import datetime as dt
import json
import math
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

from .core import (
    ROOT, RawItem, SupabaseRest, attention_continuity_score, classify_headline, dump_json, fetch_google_news,
    iso_week, load_methodology, now_kst, publication_date, robust_rank,
    trust_grade, weighted_score
)
from .targets import TARGET_QUOTAS, load_targets, target_quota_report
from .events import build_event_record, diagnosis_tags
from .evidence_v5 import (POLICY_VERSION, collection_states, valid_signal, unique_signals, profile, comparison, event_activity, weighted_level, day, carry_valid)


def bootstrap(db: SupabaseRest) -> None:
    cfg = load_methodology()
    stale=(now_kst()-dt.timedelta(hours=3)).isoformat()
    db.patch('bridge_collection_runs',{'status':'failed','finished_at':now_kst().isoformat(),'error_code':'STALE_RUNNING_TIMEOUT','error_detail':'No completion within 3 hours; next scheduled run retries collection.'},f'status=eq.running&started_at=lt.{stale}')
    db.upsert("bridge_methodology_versions", [{"version": cfg["version"], "config": cfg, "status": "shadow"}], "version")
    db.upsert("bridge_entities", load_targets(), "domain,external_id")
    # Keep the database governance table synchronized with the versioned target
    # registry. Legacy cohort rules stay auditable but no longer participate in
    # the quota-status view.
    db.patch("bridge_target_quota_rules", {"active": False}, "domain=eq.CPR&cohort_code=in.(BC70,BB30)")
    quota_names = {
        ("CPR", "BC50"): "소비자 직접접점 기업 50선", ("CPR", "BB50"): "기업·산업재 중심 기업 50선",
        ("STAR", "AM40"): "남자 광고모델 40선", ("STAR", "AW40"): "여자 광고모델 40선",
        ("STAR", "AN20"): "라이징 스타 20선", ("GOV", "GM40"): "중앙행정기관 40선",
        ("GOV", "GC60"): "지방자치단체 60선", ("UNI", "U60"): "일반·4년제 대학 60선",
        ("UNI", "C40"): "전문대학 40선",
    }
    quota_rows = [{"domain": domain, "cohort_code": cohort, "display_name": quota_names[(domain, cohort)],
                   "expected_count": count, "active": True}
                  for (domain, cohort), count in TARGET_QUOTAS.items()]
    db.upsert("bridge_target_quota_rules", quota_rows, "domain,cohort_code")
    print(f"bootstrapped {len(load_targets())} entities and methodology {cfg['version']}")


def audit_targets(db: SupabaseRest | None = None) -> list[dict]:
    report = (db.select("bridge_target_quota_status", "select=*&order=domain.asc,cohort_code.asc")
              if db else target_quota_report())
    print(json.dumps({"ok": all(row["exact_match"] for row in report), "cohorts": report}, ensure_ascii=False, indent=2))
    return report


def _start_run(db: SupabaseRest, source_id: str, start: dt.datetime, end: dt.datetime) -> str:
    result = db.insert("bridge_collection_runs", [{"source_id": source_id, "window_start": start.isoformat(), "window_end": end.isoformat(), "status": "running"}])
    return result[0]["id"]


def collect_news(
    db: SupabaseRest, as_of: dt.date, domain: str | None = None,
    window_start: dt.date | None = None, window_end: dt.date | None = None,
) -> None:
    entities = db.select("bridge_entities", "select=id,external_id,domain,name,aliases&active=eq.true" + (f"&domain=eq.{quote(domain)}" if domain else ""))
    first_date = window_start or (as_of-dt.timedelta(days=1))
    last_date = window_end or as_of
    if window_start or window_end:
        end = dt.datetime.combine(last_date + dt.timedelta(days=1), dt.time.min, tzinfo=now_kst().tzinfo)
        start = dt.datetime.combine(first_date, dt.time.min, tzinfo=now_kst().tzinfo)
    else:
        end=dt.datetime.combine(as_of,dt.time(5,15),tzinfo=now_kst().tzinfo)
        start=end-dt.timedelta(days=1)
    run_id = _start_run(db, "google_news_rss", start, end)
    fetched = accepted = rejected = 0
    entity_results = {}
    seen_entity_items: set[tuple[str, str]] = set()
    try:
        raw_by_hash: dict[str, dict] = {}
        items_by_hash: dict[str, RawItem] = {}
        staged: list[tuple[dict, object]] = []
        for entity in entities:
            search_names = [entity["name"]] + list(entity.get("aliases") or [])[:2]
            query = " OR ".join(f'"{name}"' for name in dict.fromkeys(search_names) if name)
            items = fetch_google_news(query, 1, first_date, last_date)
            if not (window_start or window_end):
                filtered=[]
                for item in items:
                    try:published=email.utils.parsedate_to_datetime(item.published_at)
                    except (TypeError,ValueError):continue
                    if start<=published<end:filtered.append(item)
                items=filtered
            fetched += len(items)
            entity_results[entity['id']] = {'status':'success','fetched_count':len(items),'matched_count':0,'query_names':search_names}
            for item in items:
                entity_item = (entity["id"], item.content_hash)
                if entity_item in seen_entity_items:
                    continue
                seen_entity_items.add(entity_item)
                signals = classify_headline(item, entity["external_id"], entity["name"], entity.get("aliases") or [], domain=entity["domain"])
                if not signals:
                    rejected += 1
                    continue
                accepted += 1
                entity_results[entity['id']]['matched_count'] += 1
                raw_by_hash[item.content_hash] = {**asdict(item), "collection_run_id": run_id}
                items_by_hash[item.content_hash] = item
                staged.extend((entity, signal) for signal in signals)
        inserted = db.upsert("bridge_raw_items", list(raw_by_hash.values()), "source_id,content_hash")
        raw_ids = {row["content_hash"]: row["id"] for row in inserted}
        signal_rows = []
        event_groups: dict[tuple[str, str], tuple[dict, list]] = {}
        for entity, signal in staged:
            raw_id = raw_ids.get(signal.raw_content_hash)
            if not raw_id:
                continue
            signal_rows.append({
                "entity_id": entity["id"], "raw_item_id": raw_id, "source_id": "google_news_rss",
                "axis": signal.axis, "signal_type": signal.signal_type, "direction": signal.direction,
                "magnitude": signal.magnitude, "confidence": signal.confidence,
                "occurred_at": signal.occurred_at, "review_status": signal.review_status,
                "rationale": signal.rationale, "ruleset_version": load_methodology()["version"]
            })
            key = (entity["id"], signal.raw_content_hash)
            if key not in event_groups:
                event_groups[key] = (entity, [])
            event_groups[key][1].append(signal)
        db.upsert("bridge_signals", signal_rows, "entity_id,raw_item_id,axis,signal_type")
        event_rows_by_key: dict[tuple[str, str], dict] = {}
        for (_, content_hash), (entity, item_signals) in event_groups.items():
            raw_id = raw_ids.get(content_hash)
            item = items_by_hash.get(content_hash)
            if not raw_id or not item:
                continue
            event = build_event_record(entity, item, raw_id, item_signals)
            if event:
                event_key = (event["entity_id"], event["event_key"])
                existing = event_rows_by_key.get(event_key)
                if existing is None:
                    event_rows_by_key[event_key] = event
                else:
                    # Syndicated headlines may have different raw content
                    # hashes but intentionally converge on one public event.
                    # Merge them before the ON CONFLICT upsert so Postgres
                    # never receives the same constrained key twice.
                    existing["evidence_count"] += 1
                    existing["source_ids"] = sorted(set(existing["source_ids"] + event["source_ids"]))
                    existing["last_seen_at"] = max(existing["last_seen_at"], event["last_seen_at"])
                    existing["severity"] = max(existing["severity"], event["severity"])
                    existing["action_strength"] = max(existing["action_strength"], event["action_strength"])
                    existing["response_quality"] = max(existing["response_quality"], event["response_quality"])
                    existing["confidence"] = max(existing["confidence"], event["confidence"])
        event_rows = list(event_rows_by_key.values())
        db.upsert("bridge_event_ledger", event_rows, "entity_id,event_key")
        db.patch("bridge_collection_runs", {"status": "success", "finished_at": now_kst().isoformat(), "fetched_count": fetched, "accepted_count": accepted, "rejected_count": rejected, "diagnostics":{"entity_results":entity_results,"policy_version":POLICY_VERSION,"observation_as_of":as_of.isoformat()}}, f"id=eq.{run_id}")
        print(f"news collection success: fetched={fetched} accepted={accepted} rejected={rejected}")
    except Exception as exc:
        db.patch("bridge_collection_runs", {"status": "failed", "finished_at": now_kst().isoformat(), "fetched_count": fetched, "accepted_count": accepted, "rejected_count": rejected, "error_code": type(exc).__name__, "error_detail": str(exc)[:2000]}, f"id=eq.{run_id}")
        db.insert("bridge_pipeline_alerts", [{"run_id": run_id, "severity": "critical", "code": "COLLECTOR_FAILED", "message": str(exc)[:1000], "context": {"source": "google_news_rss"}}])
        raise


DISCOVERY_QUERIES = {
    "CPR": (
        '코스피 코스닥 기업 신제품 실적 논란',
        '신생 기업 브랜드 상장 투자 화제',
    ),
    "STAR": (
        '광고모델 배우 가수 아이돌 스포츠스타 화제',
        '신인 아이돌 그룹 데뷔 컴백',
        '신인 배우 가수 스포츠스타 화제',
    ),
    "GOV": (
        '정부 부처 지자체 정책 민원 발표',
        '공공기관 지방자치단체 정책 이슈',
    ),
    "UNI": (
        '대학교 전문대학 입시 교육 연구 논란',
        '대학 교육 연구 산학협력 이슈',
    ),
}

DISCOVERY_PATTERNS = {
    "CPR": (
        re.compile(r"(?<![가-힣])([가-힣]{2,12}(?:전자|그룹|홀딩스|바이오|테크|건설|금융|은행|카드|보험|제약|모빌리티|엔터테인먼트))(?![가-힣])"),
        re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9&.]{1,15}(?:[ -]+[A-Z][A-Z0-9&.]{1,15}){0,2})(?![A-Za-z0-9])"),
    ),
    "STAR": (
        re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9]{1,15}(?:[ -]+[A-Z][A-Z0-9]{1,15}){0,4})(?![A-Za-z0-9])"),
        re.compile(r"(?:신인|걸그룹|보이그룹|아이돌|가수|배우|선수)[ '‘’\"“”]*([가-힣]{2,12})(?![가-힣])"),
        re.compile(r"(?<![가-힣])([가-힣]{2,12})(?=[ '’\"”]*(?:데뷔|컴백|신곡|열애|논란|화제|광고모델))"),
    ),
    "GOV": (
        re.compile(r"(?<![가-힣])([가-힣]{2,14}(?:부|청|처|위원회|특별시|광역시|특별자치시|특별자치도|도|시|군|구|공사|공단))(?![가-힣])"),
    ),
    "UNI": (
        re.compile(r"(?<![가-힣])([가-힣]{2,14}(?:대학교|대학))(?![가-힣])"),
    ),
}

DISCOVERY_STOPWORDS = {
    "CPR": {"AI", "CEO", "ESG", "IPO", "KOSPI", "KOSDAQ", "M&A"},
    "STAR": {"AI", "AAA", "KPOP", "K-POP", "SMP", "VS", "TV", "OTT", "SNS", "MV"},
}


def _extract_candidate_names(domain: str, title: str) -> set[str]:
    names: set[str] = set()
    stopwords = DISCOVERY_STOPWORDS.get(domain, set())
    for pattern in DISCOVERY_PATTERNS.get(domain, ()):
        for match in pattern.findall(title or ""):
            name = re.sub(r"\s+", " ", match).strip(" -'‘’\"“”·:[]()")
            if len(name) < 2 or name.upper() in stopwords:
                continue
            names.add(name)
    return names

def discover_candidates(db: SupabaseRest, as_of: dt.date) -> None:
    """Discover challengers outside the current roster; never auto-publish unverified names."""
    existing = db.select("bridge_entities", "select=domain,name,aliases")
    known = {(row["domain"], row["name"]) for row in existing}
    for row in existing:
        known.update((row["domain"], alias) for alias in (row.get("aliases") or []))
    candidate_hits: dict[tuple[str, str], dict] = {}
    start = dt.datetime.combine(as_of, dt.time.min, tzinfo=now_kst().tzinfo)
    end = start + dt.timedelta(days=1)
    run_id = _start_run(db, "google_news_discovery", start, end)
    fetched = accepted = 0
    try:
        for domain, queries in DISCOVERY_QUERIES.items():
            for query in queries:
                items = fetch_google_news(query, 1)
                fetched += len(items)
                for item in items:
                    for name in _extract_candidate_names(domain, item.title):
                        if (domain, name) in known:
                            continue
                        hit = candidate_hits.setdefault((domain, name), {"publishers": set(), "evidence": []})
                        hit["publishers"].add(item.publisher or "unknown")
                        if len(hit["evidence"]) < 5:
                            hit["evidence"].append({"title": item.title[:180], "url": item.canonical_url, "publisher": item.publisher})
        rows = []
        for (domain, name), hit in candidate_hits.items():
            mentions = len(hit["evidence"])
            publishers = len(hit["publishers"])
            score = min(100.0, 12.0 * mentions + 18.0 * publishers)
            rows.append({"domain": domain, "canonical_name": name, "discovery_score": score,
                         "mention_count": mentions, "publisher_count": publishers,
                         "status": "review" if mentions >= 2 and publishers >= 2 else "discovered",
                         "last_seen_at": now_kst().isoformat(), "evidence": hit["evidence"],
                         "metadata": {"discovery_date": as_of.isoformat()}})
        if rows:
            db.upsert("bridge_entity_candidates", rows, "domain,canonical_name")
        accepted = len(rows)
        db.patch("bridge_collection_runs", {"status": "success", "finished_at": now_kst().isoformat(),
                 "fetched_count": fetched, "accepted_count": accepted}, f"id=eq.{run_id}")
        print(f"candidate discovery success: fetched={fetched} candidates={accepted}")
    except Exception as exc:
        db.patch("bridge_collection_runs", {"status": "failed", "finished_at": now_kst().isoformat(),
                 "fetched_count": fetched, "accepted_count": accepted, "error_code": type(exc).__name__,
                 "error_detail": str(exc)[:2000]}, f"id=eq.{run_id}")
        raise


def collect_dart(db: SupabaseRest, as_of: dt.date) -> None:
    from collectors import collect_dart as dart

    map_path = ROOT / "collectors" / "corp_code_map.json"
    if not map_path.exists():
        raise RuntimeError("collectors/corp_code_map.json missing; run corp_code_mapper.py first")
    corp_map = json.loads(map_path.read_text(encoding="utf-8"))
    entities = {r["name"]: r for r in db.select("bridge_entities", "select=id,external_id,name&active=eq.true&domain=in.(CPR,GOV)")}
    # 휴일·주말에도 안정적으로 근거가 남도록 최근 7일을 재수집한다.
    # raw/signals의 고유키 upsert가 중복을 제거한다.
    start_date = as_of - dt.timedelta(days=6)
    start = dt.datetime.combine(start_date, dt.time.min, tzinfo=now_kst().tzinfo)
    end = dt.datetime.combine(as_of + dt.timedelta(days=1), dt.time.min, tzinfo=now_kst().tzinfo)
    run_id = _start_run(db, "opendart", start, end)
    fetched = accepted = rejected = 0
    raw_rows: list[dict] = []
    staged: list[tuple[dict, str, str, int, float, str, str]] = []
    try:
        for name, corp_code in corp_map.items():
            entity = entities.get(name)
            if not entity:
                continue
            filings = dart.fetch_filings(corp_code, start_date.strftime("%Y%m%d"), as_of.strftime("%Y%m%d"))
            fetched += len(filings)
            for filing in filings:
                title = filing.get("report_nm", "").strip()
                receipt = filing.get("rcept_no", "").strip()
                if not title or not receipt:
                    rejected += 1
                    continue
                url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}"
                content_hash = __import__("hashlib").sha256(f"opendart\x1f{receipt}".encode()).hexdigest()
                raw_rows.append({
                    "source_id": "opendart", "collection_run_id": run_id, "source_item_id": receipt,
                    "canonical_url": url, "title": title, "publisher": filing.get("corp_name") or name,
                    "published_at": dt.datetime.strptime(filing.get("rcept_dt"), "%Y%m%d").date().isoformat(), "payload": {"corp_code": corp_code, "report_type": filing.get("pblntf_ty")},
                    "content_hash": content_hash
                })
                axes = []
                if any(word in title for word in dart.GROWTH_KEYWORDS):
                    axes.append(("G", "regulatory_action", 1, 18.0, "성과형 공시"))
                if any(word in title for word in dart.DEPTH_KEYWORDS):
                    axes.append(("D", "regulatory_depth", 1, 12.0, "정기·지속가능 공시"))
                if not axes:
                    rejected += 1
                    continue
                accepted += 1
                for axis, kind, direction, magnitude, rationale in axes:
                    staged.append((entity, content_hash, axis, direction, magnitude, kind, rationale))
        inserted = db.upsert("bridge_raw_items", raw_rows, "source_id,content_hash")
        raw_ids = {row["content_hash"]: row["id"] for row in inserted}
        signal_rows = []
        for entity, content_hash, axis, direction, magnitude, kind, rationale in staged:
            raw_id = raw_ids.get(content_hash)
            if not raw_id:
                continue
            signal_rows.append({
                "entity_id": entity["id"], "raw_item_id": raw_id, "source_id": "opendart", "axis": axis,
                "signal_type": kind, "direction": direction, "magnitude": magnitude, "confidence": 0.95,
                "occurred_at": as_of.isoformat(), "review_status": "auto", "rationale": rationale,
                "ruleset_version": load_methodology()["version"]
            })
        db.upsert("bridge_signals", signal_rows, "entity_id,raw_item_id,axis,signal_type")
        db.patch("bridge_collection_runs", {"status": "success", "finished_at": now_kst().isoformat(), "fetched_count": fetched, "accepted_count": accepted, "rejected_count": rejected}, f"id=eq.{run_id}")
        print(f"DART collection success: fetched={fetched} accepted={accepted} rejected={rejected}")
    except Exception as exc:
        db.patch("bridge_collection_runs", {"status": "failed", "finished_at": now_kst().isoformat(), "fetched_count": fetched, "accepted_count": accepted, "rejected_count": rejected, "error_code": type(exc).__name__, "error_detail": str(exc)[:2000]}, f"id=eq.{run_id}")
        db.insert("bridge_pipeline_alerts", [{"run_id": run_id, "severity": "critical", "code": "COLLECTOR_FAILED", "message": str(exc)[:1000], "context": {"source": "opendart"}}])
        raise


def export_latest(db: SupabaseRest, as_of: dt.date) -> None:
    # Use the same version-scoped authoritative export for latest and history.
    # The legacy public view can include multiple published methodology versions.
    export_history(db, as_of)
    archive = json.loads((ROOT / "site" / "data" / "history.json").read_text(encoding="utf-8"))
    rows = [r for r in archive["rankings"] if r["as_of_date"] == as_of.isoformat() and r.get("methodology_version",load_methodology()["version"])==load_methodology()["version"]]
    if not rows:raise RuntimeError('new methodology snapshot missing; last public file retained')
    seen = set()
    groups = {}
    for row in rows:
        if any(row.get(k) is None for k in ("domain", "ranking_type", "external_id", "score", "as_of_date")):
            raise RuntimeError("incomplete public ranking blocked")
        key = (row["domain"], row["ranking_type"], row["external_id"])
        if key in seen:
            raise RuntimeError(f"duplicate public ranking blocked: {key}")
        seen.add(key)
        groups.setdefault((row["domain"], row["ranking_type"]), []).append(row)
    for members in groups.values():
        members.sort(key=lambda r: (-float(r["score"]), str(r["external_id"])))
        for position, row in enumerate(members, 1):
            row["rank"] = position
            previous = row.get("previous_rank")
            row["rank_change"] = int(previous) - position if previous is not None else 0
    rows.sort(key=lambda r: (r["domain"], r["ranking_type"], r["rank"]))
    payload = {
        "schemaVersion": "2.0",
        "methodologyVersion":load_methodology()["version"],
        "snapshotId":__import__("hashlib").sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:20],
        "generatedAt": now_kst().isoformat(),
        "asOfDate": as_of.isoformat(),
        "week": iso_week(as_of),
        "rankings": rows,
        "recordCount": len(rows),
        "dataStatus": "published" if rows else "no-published-snapshot"
    }
    for row in rows:
        if not 0<=float(row['score'])<=100:raise RuntimeError('out-of-range public score blocked')
        states=row.get('axis_status') or {}
        if states and row.get('axes_available',0)<load_methodology()['minimum_publishable_axes']:
            raise RuntimeError('public ranking has insufficient evidence axes')
    dump_json(ROOT / "site" / "data" / "latest.json", payload)
    dump_json(ROOT / "data" / "pipeline_status.json", {"generatedAt": payload["generatedAt"], "asOfDate": payload["asOfDate"], "recordCount": len(rows)})
    print(f"exported {len(rows)} published ranking rows")


def export_history(db: SupabaseRest, as_of: dt.date) -> None:
    """Export a compact public archive used by the period selector.

    Reputation levels remain averages; only Activity Points are additive. The
    archive contains public outcomes, never raw evidence or internal formulas.
    """
    cfg = load_methodology()
    start = dt.date(2026, 9, 1)
    rankings = db.select(
        "bridge_rankings",
        f"select=entity_id,as_of_date,domain,ranking_type,rank,previous_rank,rank_change,score,score_change,trust_grade,methodology_version"
        f"&as_of_date=gte.{start.isoformat()}&as_of_date=lte.{as_of.isoformat()}"
        f"&ranking_type=eq.T100&published_at=not.is.null&methodology_version=in.({cfg['version']},2026.10-shadow-3)"
        f"&order=as_of_date.asc,domain.asc,rank.asc"
    )
    entity_map = {row["id"]: row for row in db.select("bridge_entities", "select=id,external_id,name,category,subcategory")}
    metrics = db.select(
        "bridge_index_metrics",
        f"select=entity_id,as_of_date,daily_index,weekly_index,last_week_index,wow_delta,weighted_index,activity_points,"
        f"cumulative_performance,momentum,stability,observed_days,four_week_average,cumulative_activity,observed_weeks,methodology_version,diagnostics"
        f"&as_of_date=gte.{start.isoformat()}&as_of_date=lte.{as_of.isoformat()}"
        f"&methodology_version=in.({cfg['version']},2026.10-shadow-3)"
    )
    metric_map = {(row["entity_id"], row["as_of_date"],row["methodology_version"]): row for row in metrics}
    observations = db.select(
        "bridge_axis_observations",
        f"select=entity_id,as_of_date,axis,score,status,diagnostics,methodology_version"
        f"&as_of_date=gte.{start.isoformat()}&as_of_date=lte.{as_of.isoformat()}"
        f"&methodology_version=in.({cfg['version']},2026.10-shadow-3)"
    )
    axes_map: dict[tuple[str, str], dict[str, float]] = {}
    for observation in observations:
        if observation.get("score") is None or observation.get("status") not in {"measured", "carried"}:
            continue
        key = (observation["entity_id"], observation["as_of_date"],observation["methodology_version"])
        axes_map.setdefault(key, {})[observation["axis"]] = observation
    chosen={}
    for r in rankings:
        k=(r['entity_id'],r['as_of_date'],r['ranking_type'])
        if k not in chosen or r['methodology_version']==cfg['version']:chosen[k]=r
    v5_groups={(r['domain'],r['ranking_type'],r['as_of_date']) for r in rankings if r['methodology_version']==cfg['version']}
    rankings=[r for r in chosen.values() if r['methodology_version']==cfg['version'] or (r['domain'],r['ranking_type'],r['as_of_date']) not in v5_groups]
    labels = cfg.get("release_policy", {}).get("public_domain_labels", {})
    public_rows = []
    for ranking in rankings:
        entity = entity_map.get(ranking["entity_id"])
        if not entity:
            continue
        metric = metric_map.get((ranking["entity_id"], ranking["as_of_date"],ranking["methodology_version"]), {})
        row = {k: v for k, v in ranking.items() if k != "entity_id"}
        row.update({k: v for k, v in entity.items() if k != "id"})
        row.update({k: v for k, v in metric.items() if k not in {"entity_id", "as_of_date", "diagnostics"}})
        public_axes = axes_map.get((ranking["entity_id"], ranking["as_of_date"],ranking["methodology_version"]), {})
        row.update(profile(list(public_axes.values()),dt.date.fromisoformat(ranking['as_of_date'])))
        diag=metric.get('diagnostics') or {}
        row['comparison_status']=diag.get('comparison_status','legacy_unverified')
        row['collection_ok_days']=diag.get('collection_ok_days')
        row['new_evidence_days']=diag.get('new_evidence_days')
        row['four_week_observed_weeks']=diag.get('four_week_observed_weeks')
        row['activity_period']=diag.get('activity_period','legacy_signal_sum')
        row['daily_activity_points']=diag.get('daily_activity_points')
        row['observation_window_start']=diag.get('observation_window_start')
        row['observation_window_end']=diag.get('observation_window_end')
        if 'weekly_activity_points' in diag:row['activity_points']=diag['weekly_activity_points']
        row['history_type']='historical_weekly_backfill' if ranking['as_of_date']<'2026-10-11' else 'daily_observation'
        row['evidence_policy_version']=diag.get('evidence_policy_version','v4.2-legacy')
        row["domain"] = labels.get(row["domain"], row["domain"])
        row["diagnosis_tags"] = diagnosis_tags(row)
        public_rows.append(row)
    dump_json(ROOT / "site" / "data" / "history.json", {
        "schemaVersion": "1.0", "generatedAt": now_kst().isoformat(),
        "fromDate": start.isoformat(), "throughDate": as_of.isoformat(),
        "rankings": public_rows, "recordCount": len(public_rows),
    })


def import_official(db: SupabaseRest, csv_path: str, as_of: dt.date) -> None:
    cfg = load_methodology()
    entities = {r["external_id"]: r for r in db.select("bridge_entities", "select=id,external_id&active=eq.true")}
    rows = []
    raw_rows=[]
    sources={}
    with open(csv_path, newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            entity = entities.get(record["external_id"].strip())
            if not entity:
                raise ValueError(f"unknown external_id: {record['external_id']}")
            axis = record["axis"].strip().upper()
            if axis not in "BRIDGE":
                raise ValueError(f"invalid axis: {axis}")
            score = float(record["score"])
            confidence = float(record["confidence"])
            if not 0 <= score <= 100 or not 0 <= confidence <= 1:
                raise ValueError("score must be 0..100 and confidence 0..1")
            source_id=record.get('source_id') or 'official_baseline'
            source_url=record.get('evidence_url') or ''
            signature=__import__('hashlib').sha256(json.dumps([entity['id'],axis,source_id,source_url,record.get('note'),score],ensure_ascii=False).encode()).hexdigest()
            sources[source_id]={'id':source_id,'name':source_id,'family':'official','base_url':source_url,'enabled':True,'collection_mode':'file','default_refresh':'7 days'}
            raw_rows.append({'source_id':source_id,'source_item_id':signature,'title':record.get('note') or '공식 기준자료',
                             'canonical_url':source_url,'publisher':source_id,'content_hash':signature,
                             'payload':{'entity_id':entity['id'],'external_id':record['external_id'],'axis':axis,'score':score,'reference_period':record.get('reference_period') or record.get('note'),'kind':'baseline_not_activity'}})
            fresh=int(record.get('freshness_days') or 0)
            evidence_date=record.get('evidence_date') or ((as_of-dt.timedelta(days=fresh)).isoformat() if fresh>0 else None)
            rows.append({
                "entity_id": entity["id"], "as_of_date": as_of.isoformat(), "axis": axis,
                "score": score, "confidence": confidence, "coverage": float(record.get("coverage") or confidence),
                "source_families": int(record.get("source_families") or 1),
                "evidence_count": int(record.get("evidence_count") or 1),
                "freshness_days": fresh, "status": "carried" if source_id in {"academyinfo","gov_official_evaluations","opendart_financials"} else "measured",
                "methodology_version": cfg["version"],
                "diagnostics": {"source_id":source_id,"evidence_url":source_url,"note":record.get('note'),
                                "evidence_date":evidence_date,"reference_period":record.get('reference_period') or record.get('note'),
                                "reference_date_known":bool(evidence_date),"baseline_fingerprint":signature,"policy_version":POLICY_VERSION}
            })
    db.upsert('bridge_source_registry',list(sources.values()),'id')
    import_runs={}
    for sid in sources:
        run=db.insert('bridge_collection_runs',[{'source_id':sid,'status':'running','window_start':dt.datetime.combine(as_of,dt.time.min,tzinfo=now_kst().tzinfo).isoformat(),'window_end':dt.datetime.combine(as_of+dt.timedelta(days=1),dt.time.min,tzinfo=now_kst().tzinfo).isoformat(),'diagnostics':{'module':'canonical_baseline_import','policy_version':POLICY_VERSION}}])[0]
        import_runs[sid]=run['id']
    for raw in raw_rows:raw['collection_run_id']=import_runs[raw['source_id']]
    inserted=db.upsert('bridge_raw_items',raw_rows,'source_id,content_hash')
    raw_ids={r['content_hash']:r['id'] for r in inserted}
    for row in rows:row['diagnostics']['raw_item_id']=raw_ids.get(row['diagnostics']['baseline_fingerprint'])
    db.upsert("bridge_axis_observations", rows, "entity_id,as_of_date,axis,methodology_version")
    for sid,rid in import_runs.items():db.patch('bridge_collection_runs',{'status':'success','finished_at':now_kst().isoformat(),'fetched_count':sum(r['source_id']==sid for r in raw_rows),'accepted_count':sum(r['source_id']==sid for r in raw_rows)},f'id=eq.{rid}')
    print(f"imported {len(rows)} official axis observations")


OFFICIAL_BASELINE_WEIGHTS = {"CPR": 0.55, "STAR": 0.25, "GOV": 0.65, "UNI": 0.78}


def merge_official_and_flow(official: dict, flow: dict, domain: str) -> dict:
    """Preserve official baseline while adding current public-response flow."""
    baseline_weight = OFFICIAL_BASELINE_WEIGHTS.get(domain, 0.5)
    flow_weight = 1.0 - baseline_weight
    official_diag = official.get("diagnostics") or {}
    flow_diag = flow.get("diagnostics") or {}
    source_ids = set(official_diag.get("source_ids") or [])
    if official_diag.get("source_id"):
        source_ids.add(official_diag["source_id"])
    source_ids.update(flow_diag.get("source_ids") or [])
    merged = dict(flow)
    merged.update({
        "score": round(float(official["score"]) * baseline_weight + float(flow["score"]) * flow_weight, 2),
        "confidence": round(float(official["confidence"]) * baseline_weight + float(flow["confidence"]) * flow_weight, 4),
        "coverage": round(float(official.get("coverage") or 0) * baseline_weight + float(flow.get("coverage") or 0) * flow_weight, 4),
        "source_families": len(source_ids),
        "evidence_count": int(official.get("evidence_count") or 0) + int(flow.get("evidence_count") or 0),
        "freshness_days": min(int(official.get("freshness_days") or 0), int(flow.get("freshness_days") or 0)),
        "diagnostics": {
            "aggregation": "official_baseline_plus_public_flow",
            "baseline_weight": baseline_weight,
            "flow_weight": flow_weight,
            "source_ids": sorted(source_ids),
            "official": official_diag,
            "flow": flow_diag,
        },
    })
    return merged


def compute_index_metrics(db: SupabaseRest, as_of: dt.date, cfg: dict, entities: list[dict],
                          score_rows: list[dict], accepted_by_entity: dict[str, list[dict]]) -> None:
    """Persist level indices separately from additive activity volume."""
    monday = as_of - dt.timedelta(days=as_of.weekday())
    previous_monday = monday - dt.timedelta(days=7)
    history_start = as_of - dt.timedelta(days=371)
    history = db.select(
        "bridge_scores",
        f"select=entity_id,as_of_date,score,confidence_score,axes_used,methodology_version,diagnostics&as_of_date=gte.{history_start.isoformat()}"
        f"&as_of_date=lte.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}"
    )
    by_entity: dict[str, list[dict]] = {}
    for row in history:
        if row.get("score") is not None:
            by_entity.setdefault(row["entity_id"], []).append(row)
    metric_history = db.select(
        "bridge_index_metrics",
        f"select=entity_id,as_of_date,activity_points&as_of_date=gte.{history_start.isoformat()}"
        f"&as_of_date=lt.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}"
    )
    activity_by_entity: dict[str, float] = {}
    for metric in metric_history:
        entity_id = metric["entity_id"]
        activity_by_entity[entity_id] = activity_by_entity.get(entity_id, 0.0) + float(metric.get("activity_points") or 0)
    window_end=dt.datetime.combine(as_of,dt.time(5,15),tzinfo=now_kst().tzinfo)
    window_start=window_end-dt.timedelta(days=1)
    event_rows=db.select('bridge_event_ledger',f"select=entity_id,event_key,occurred_at,review_status,action_strength,confidence&occurred_at=gte.{quote(window_start.isoformat())}&occurred_at=lt.{quote(window_end.isoformat())}")
    daily_activity=event_activity(event_rows,as_of,window_start,window_end)
    current = {row["entity_id"]: row for row in score_rows}
    metric_rows = []
    for entity in entities:
        row = current.get(entity["id"])
        if not row or row.get("score") is None:
            continue
        daily = float(row["score"])
        dated = [(dt.date.fromisoformat(h["as_of_date"]), float(h["score"])) for h in by_entity.get(entity["id"], [])]
        this_week = [v for d, v in dated if monday <= d <= as_of]
        last_week = [v for d, v in dated if previous_monday <= d < monday]
        weekly = weighted_level([h for h in by_entity.get(entity["id"],[]) if monday<=dt.date.fromisoformat(h["as_of_date"])<=as_of]) or daily
        previous = weighted_level([h for h in by_entity.get(entity["id"],[]) if previous_monday<=dt.date.fromisoformat(h["as_of_date"])<monday])
        week_buckets: dict[dt.date, list[float]] = {}
        for observed_day, value in dated:
            key = observed_day - dt.timedelta(days=observed_day.weekday())
            week_buckets.setdefault(key, []).append(value)
        weekly_series = [weighted_level([h for h in by_entity.get(entity['id'],[]) if key<=dt.date.fromisoformat(h['as_of_date'])<key+dt.timedelta(days=7)]) for key in sorted(week_buckets)]
        cumulative = round(sum(weekly_series) / len(weekly_series), 2) if weekly_series else weekly
        recent = weekly_series[-4:]
        four_week_average = round(sum(recent) / len(recent), 2) if recent else weekly
        weights = [0.1, 0.2, 0.3, 0.4][-len(recent):]
        momentum = round(sum(v * w for v, w in zip(recent, weights)) / sum(weights), 2) if recent else weekly
        mean = sum(weekly_series[-12:]) / max(1, len(weekly_series[-12:]))
        variance = sum((v - mean) ** 2 for v in weekly_series[-12:]) / max(1, len(weekly_series[-12:]))
        stability = round(max(0.0, 100.0 - math.sqrt(variance) * 5.0), 2) if len(weekly_series)>=3 else None
        if len(weekly_series)<2:momentum=None
        else:
            prior_recent=weekly_series[-5:-1]
            prior_weights=[.1,.2,.3,.4][-len(prior_recent):]
            prior_level=sum(v*w for v,w in zip(prior_recent,prior_weights))/sum(prior_weights)
            momentum=round(momentum-prior_level,2)
        activity=daily_activity.get(entity['id'],0.0)
        history_rows=by_entity.get(entity['id'],[])
        prior=sorted([h for h in history_rows if h['as_of_date']<as_of.isoformat()],key=lambda h:h['as_of_date'])
        comparison_status=comparison(row,prior[-1] if prior else None)
        week_rows=[h for h in history_rows if monday<=dt.date.fromisoformat(h['as_of_date'])<=as_of]
        collection_ok_days=sum((h.get('diagnostics') or {}).get('collection_status')=='success' for h in week_rows)
        metric_rows.append({
            "entity_id": entity["id"], "as_of_date": as_of.isoformat(), "daily_index": round(daily, 2),
            "weekly_index": weekly, "last_week_index": previous,
            "wow_delta": round(weekly - previous, 2) if previous is not None else None,
            "weighted_index": round(daily, 2), "activity_points": round(activity, 2),
            "four_week_average": four_week_average,
            "cumulative_activity": round(activity_by_entity.get(entity["id"], 0.0) + activity, 2),
            "cumulative_performance": cumulative, "momentum": momentum, "stability": stability,
            "observed_days": len(this_week), "observed_weeks": len(weekly_series),
            "methodology_version": cfg["version"],
            "diagnostics": {"weekly_method": "daily_quality_weighted_mean", "cumulative_method": "weekly_level_mean", "evidence_policy_version":POLICY_VERSION,
                            "comparison_status":comparison_status, "collection_ok_days":collection_ok_days,
                            "new_evidence_days":sum(bool((h.get('diagnostics') or {}).get('new_evidence_observed')) for h in week_rows),
                            "four_week_observed_weeks":len(recent),
                            "reference_axes_count":(row.get('diagnostics') or {}).get('axis_profile',{}).get('reference_axes_count',0),
                            "observation_window_start":window_start.isoformat(),"observation_window_end":window_end.isoformat(),
                            "activity_period":"weekly", "daily_activity_points":round(activity,2),
                            "weekly_activity_points":round(activity+sum(float(m.get('activity_points') or 0) for m in metric_history if m['entity_id']==entity['id'] and monday<=dt.date.fromisoformat(m['as_of_date'])<as_of),2),
                            "series_start":"v5 method effective date"}
        })
    if metric_rows:
        db.upsert("bridge_index_metrics", metric_rows, "entity_id,as_of_date,methodology_version")


def score_day(db: SupabaseRest, as_of: dt.date) -> None:
    cfg = load_methodology()
    # 같은 날짜를 재실행할 때 이전 실행의 적격 행이 공개 상태로 남으면 서로
    # 다른 스냅샷의 순위가 섞인다. 현재 방법론의 당일 공개표시를 먼저 해제하고
    # 이번 계산에서 통과한 행만 publish 단계에서 다시 공개한다.
    db.patch("bridge_rankings", {"published_at": None}, f"as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}")
    entities = db.select("bridge_entities", "select=id,external_id,domain,subcategory&active=eq.true")
    entity_by_id = {e["id"]: e for e in entities}
    since = (as_of - dt.timedelta(days=28)).isoformat()
    end_utc = dt.datetime.combine(as_of + dt.timedelta(days=1), dt.time.min, tzinfo=now_kst().tzinfo).astimezone(dt.timezone.utc)
    upper = end_utc.isoformat().replace("+00:00", "Z")
    signals = db.select("bridge_signals", f"select=id,entity_id,raw_item_id,axis,signal_type,direction,magnitude,confidence,occurred_at,expires_at,review_status,source_id&occurred_at=gte.{since}T00:00:00Z&occurred_at=lt.{upper}")
    raw_items = db.select("bridge_raw_items", f"select=id,title,published_at&published_at=gte.{since}T00:00:00Z&published_at=lt.{upper}")
    signals = unique_signals([v for v in signals if valid_signal(v, as_of)], {r['id']:r for r in raw_items})
    runs = db.select("bridge_collection_runs", f"select=source_id,status,started_at,finished_at,window_start,window_end,diagnostics&window_start=gte.{since}T00:00:00Z&order=started_at.desc")
    observed_states = collection_states(runs, as_of)
    grouped: dict[tuple[str, str], list[dict]] = {}
    accepted_by_entity: dict[str, list[dict]] = {}
    for signal in signals:
        # 부정 귀속은 사람의 승인을 요구하지만, 명시적인 긍정 반응 신호는
        # 자동 집계한다. 무보도 자체를 부정 감성으로 간주하지는 않는다.
        needs_review = signal["axis"] in cfg["review_required"] and int(signal["direction"]) < 0
        if signal["review_status"] == "rejected" or (needs_review and signal["review_status"] != "approved"):
            continue
        grouped.setdefault((signal["entity_id"], signal["axis"]), []).append(signal)
        accepted_by_entity.setdefault(signal["entity_id"], []).append(signal)

    max_counts: dict[tuple[str, str], int] = {}
    for (entity_id, axis), values in grouped.items():
        domain = entity_by_id.get(entity_id, {}).get("domain")
        max_counts[(domain, axis)] = max(max_counts.get((domain, axis), 0), len(values))

    existing_rows = db.select(
        "bridge_axis_observations",
        f"select=entity_id,axis,score,confidence,coverage,source_families,evidence_count,freshness_days,status,diagnostics"
        f"&as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}"
    )
    prior_observations=db.select('bridge_axis_observations',f'select=entity_id,axis,score,confidence,coverage,source_families,evidence_count,freshness_days,status,diagnostics,as_of_date&as_of_date=lt.{as_of.isoformat()}&as_of_date=gte.{(as_of-dt.timedelta(days=400)).isoformat()}&order=as_of_date.desc')
    carried=carry_valid(prior_observations,as_of,{(r['entity_id'],r['axis']) for r in existing_rows})
    for r in carried:r['methodology_version']=cfg['version']
    db.upsert('bridge_axis_observations',carried,'entity_id,as_of_date,axis,methodology_version')
    existing_rows+=carried
    existing = {(row["entity_id"], row["axis"]): row for row in existing_rows}
    observations: list[dict] = []
    for (entity_id, axis), values in grouped.items():
        entity = entity_by_id.get(entity_id)
        if not entity:
            continue
        # GOV-PCE signals carry a calibrated 0..100 level rather than an event
        # count.  Keep them separate from news volume so a daily observation is
        # not accidentally treated as another mention or added to sentiment.
        pce_values = [v for v in values if v["source_id"] == "youtube_data_api"
                      and str(v["signal_type"]).startswith("gov_pce_")]
        flow_values = [v for v in values if v not in pce_values]
        count = len(values)
        max_count = max_counts[(entity["domain"], axis)]
        if axis == "R" and flow_values:
            penalty = sum(float(v["magnitude"]) * float(v["confidence"]) for v in flow_values if int(v["direction"]) < 0)
            benefit = sum(float(v["magnitude"]) * float(v["confidence"]) for v in flow_values if int(v["direction"]) > 0)
            # 반응은 중립점 50에서 시작한다. 반응이 없다는 이유만으로 긍정
            # 100점을 부여하던 종전 구조를 제거한다.
            flow_score = max(0.0, min(100.0, 50.0 + benefit - penalty))
        elif flow_values:
            flow_score = 100.0 * math.log1p(len(flow_values)) / math.log1p(max_count) if max_count else None
        else:
            flow_score = None
        if pce_values:
            weight_total = sum(float(v["confidence"]) for v in pce_values) or 1.0
            pce_score = sum(float(v["magnitude"]) * float(v["confidence"]) for v in pce_values) / weight_total
            # Platform-observed consumption is the primary GOV communication
            # measure; news flow remains a complementary public signal.
            score = pce_score if flow_score is None else 0.70 * pce_score + 0.30 * flow_score
        else:
            score = flow_score
        families = len({v["source_id"] for v in values})
        confidence = min(1.0, (sum(float(v["confidence"]) for v in values) / count) * min(1.0, count / 5) * min(1.0, families / 2))
        observation = {
            "entity_id": entity_id, "as_of_date": as_of.isoformat(), "axis": axis,
            "score": round(score, 2) if score is not None else None,
            "confidence": round(confidence, 4), "coverage": round(min(1.0, count / 5), 4),
            "source_families": families, "evidence_count": count, "freshness_days": min((as_of-day(v["occurred_at"])).days for v in values),
            "status": "measured", "methodology_version": cfg["version"],
            "diagnostics": {"window_days": 28,
                            "aggregation": "gov_pce_level_plus_news" if pce_values else "domain_log_count" if axis != "R" else "reviewed_event_decay_pending",
                            "source_ids": sorted({v["source_id"] for v in values}),
                            "signal_ids": sorted({v['id'] for v in values}),
                            "evidence_date":max(day(v['occurred_at']).isoformat() for v in values),
                            "policy_version":POLICY_VERSION}
        }
        official = existing.get((entity_id, axis))
        if official and (official.get("diagnostics") or {}).get("source_id"):
            observation = merge_official_and_flow(official, observation, entity["domain"])
        observations.append(observation)

    # 뉴스 검색을 실제 수행했으나 적격 노출/브랜드 맥락이 한 건도 없었던
    # 경우는 '결측'이 아니라 관측된 0이다. ENT와 CPR에서만 적용한다.
    # R은 감성 축이므로 무보도를 부정 반응으로 위조하지 않는다.
    observed_keys = {(row["entity_id"], row["axis"]) for row in observations}
    for entity in entities:
        if entity["domain"] not in {"STAR", "CPR"}:
            continue
        state = observed_states.get((entity['id'],'google_news_rss'),{})
        if state.get('status') != 'success':
            continue
        for axis in ("B",):
            key = (entity["id"], axis)
            if key in observed_keys:
                continue
            zero = {
                "entity_id": entity["id"], "as_of_date": as_of.isoformat(), "axis": axis,
                "score": 0.0, "confidence": 0.70 if axis == "B" else 0.60,
                "coverage": 1.0, "source_families": 1, "evidence_count": 0,
                "freshness_days": 0, "status": "measured", "methodology_version": cfg["version"],
                "diagnostics": {"window_days": 28, "aggregation": "observed_zero_news_monitoring",
                                "source_ids": ["google_news_rss"], "meaning": "검색 수행 후 적격 신호 0건", "evidence_date":as_of.isoformat(), "policy_version":POLICY_VERSION}
            }
            official = existing.get(key)
            if official and (official.get("diagnostics") or {}).get("source_id"):
                zero = merge_official_and_flow(official, zero, entity["domain"])
            observations.append(zero)
            observed_keys.add(key)
    if observations:
        db.upsert("bridge_axis_observations", observations, "entity_id,as_of_date,axis,methodology_version")

    all_obs = db.select("bridge_axis_observations", f"select=entity_id,axis,score,confidence,source_families,status,diagnostics&as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}")
    by_entity: dict[str, list[dict]] = {}
    for obs in all_obs:
        by_entity.setdefault(obs["entity_id"], []).append(obs)
    score_rows: list[dict] = []
    candidates: list[dict] = []
    for entity in entities:
        obs = by_entity.get(entity["id"], [])
        axis_scores = {o["axis"]: o["score"] for o in obs if o["status"] in {"measured", "carried"}}
        confidences = {o["axis"]: float(o["confidence"]) for o in obs}
        score, confidence_score, axes = weighted_score(axis_scores, confidences, cfg)
        # 공중기억 연속성: 언급 자체의 기억 유지효과와 언급 내용의 방향을
        # 분리한다. 무언급은 중립보다 소폭 낮게, 오래된 언급은 감쇠한다.
        attention_cfg = cfg.get("attention_continuity") or {}
        attention_weight = float((attention_cfg.get("domain_weight") or {}).get(entity["domain"], 0))
        attention_score, attention_diag = attention_continuity_score(
            accepted_by_entity.get(entity["id"], []),
            max_counts.get((entity["domain"], "B"), 0),
            as_of, entity["domain"], cfg,
        )
        base_score = score
        news_state=observed_states.get((entity['id'],'google_news_rss'),{})
        attention_available=bool(attention_diag.get('unique_mentions')) or news_state.get('status')=='success'
        attention_diag['observation_status']='observed' if attention_available else 'not_observed'
        if not attention_available: attention_score=None
        if score is not None and attention_weight and attention_available:
            score = round(base_score * (1.0 - attention_weight) + attention_score * attention_weight, 2)
        source_ids = set()
        for observation in obs:
            diagnostics = observation.get("diagnostics") or {}
            source_ids.update(diagnostics.get("source_ids") or ([diagnostics.get("source_id")] if diagnostics.get("source_id") else []))
        # A completed daily search with zero accepted mentions is still an
        # observed result, not missing data.  Count that monitored absence as
        # a source family for CPR eligibility; its value is already expressed
        # conservatively by the attention-continuity score (45), so this does
        # not manufacture a positive event or an extra axis.
        if entity["domain"] == "CPR" and attention_available and attention_diag.get("no_mention_observed"):
            source_ids.add("google_news_rss")
        source_families = len(source_ids)
        beta_gate = (cfg.get("beta_eligibility") or {}).get(entity["domain"], {})
        min_families = beta_gate.get("minimum_source_families", cfg["minimum_source_families"])
        min_confidence = beta_gate.get("minimum_confidence_score", cfg["trust_thresholds"]["C"])
        eligible = score is not None and source_families >= min_families and confidence_score >= min_confidence
        status = "eligible" if eligible else ("withheld" if score is None else "shadow")
        grade = trust_grade(confidence_score, cfg) if score is not None else "N/R"
        score_rows.append({
            "entity_id": entity["id"], "as_of_date": as_of.isoformat(), "score": score,
            "confidence_score": confidence_score, "trust_grade": grade, "axes_used": axes,
            "publish_status": status, "methodology_version": cfg["version"],
            "diagnostics": {"source_families": source_families,
                            "base_score_before_attention": base_score,
                            "attention_score": attention_score,
                            "attention_diagnostics": attention_diag,
                            "attention_weight": attention_weight,
                            "beta_gate": {"minimum_source_families": min_families, "minimum_confidence_score": min_confidence},
                            "evidence_policy_version":POLICY_VERSION,
                            "axis_profile":profile(obs,as_of),
                            "collection_status":news_state.get('status','not_observed'),
                            "new_evidence_observed":any(day(v.get('occurred_at')) in {as_of,as_of-dt.timedelta(days=1)} for v in accepted_by_entity.get(entity['id'],[])),
                            "trust_basis":{"axes_available":len(axes),"source_families":source_families,"confidence_score":confidence_score},
                            **({"uni_relationship_enrichment": __import__("bridge_pipeline.uni_reputation_v6", fromlist=["diagnostics"]).diagnostics(accepted_by_entity.get(entity["id"], []))}
                               if entity["domain"] == "UNI" else {}),
                            **({"gov_relationship_enrichment": __import__("bridge_pipeline.gov_reputation_v6", fromlist=["diagnostics"]).diagnostics(accepted_by_entity.get(entity["id"], []))}
                               if entity["domain"] == "GOV" else {}),
                            **({"ent_relationship_enrichment": __import__("bridge_pipeline.ent_reputation_v6", fromlist=["diagnostics"]).diagnostics(accepted_by_entity.get(entity["id"], []))}
                               if entity["domain"] == "STAR" else {})}
        })
        if eligible:
            candidates.append({**entity, "score": score, "confidence_score": confidence_score, "trust_grade": grade})
    db.upsert("bridge_scores", score_rows, "entity_id,as_of_date,methodology_version")
    compute_index_metrics(db, as_of, cfg, entities, score_rows, accepted_by_entity)

    previous_rows = db.select("bridge_rankings", f"select=entity_id,rank,score,domain,ranking_type&as_of_date=lt.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}&order=as_of_date.desc&limit=1000")
    previous = {}
    for row in previous_rows:
        previous.setdefault((row["domain"], row["ranking_type"], row["entity_id"]), row)
    ranking_rows = []
    for domain in sorted({c["domain"] for c in candidates}):
        domain_rows = [c for c in candidates if c["domain"] == domain]
        ranking_types = {"T100": domain_rows}
        for subcat in sorted({c.get("subcategory") for c in domain_rows if c.get("subcategory")}):
            ranking_types[subcat] = [c for c in domain_rows if c.get("subcategory") == subcat]
        for ranking_type, members in ranking_types.items():
            limits = {"T100": 100, "BC50": 50, "BB50": 50, "AM40": 40, "AW40": 40,
                      "AN20": 20, "GM40": 40, "GC60": 60, "U60": 60, "C40": 40}
            for member in robust_rank(members)[:limits.get(ranking_type, 100)]:
                prev = previous.get((domain, ranking_type, member["id"]))
                ranking_rows.append({
                    "as_of_date": as_of.isoformat(), "domain": domain, "ranking_type": ranking_type,
                    "entity_id": member["id"], "rank": member["rank"],
                    "previous_rank": prev["rank"] if prev else None,
                    "rank_change": (prev["rank"] - member["rank"]) if prev else 0,
                    "score": member["score"], "score_change": round(member["score"] - float(prev["score"]), 2) if prev else 0,
                    "trust_grade": member["trust_grade"], "methodology_version": cfg["version"],
                    "published_at": None
                })
    if ranking_rows:
        db.upsert("bridge_rankings", ranking_rows, "as_of_date,domain,ranking_type,entity_id,methodology_version")
    print(f"scored {len(score_rows)} entities; eligible={len(candidates)}; ranking_rows={len(ranking_rows)}")


def publish_eligible(db: SupabaseRest, as_of: dt.date) -> None:
    cfg = load_methodology()
    mismatches = [row for row in audit_targets(db) if not row["exact_match"]]
    if mismatches:
        raise RuntimeError(f"publication blocked: target quota mismatch: {mismatches}")
    eligible = db.select("bridge_scores", f"select=entity_id&as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}&publish_status=eq.eligible")
    if not eligible:
        raise RuntimeError("publication blocked: no eligible scores")
    db.patch("bridge_rankings", {"published_at": now_kst().isoformat()}, f"as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}")
    db.patch("bridge_scores", {"publish_status": "published"}, f"as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}&publish_status=eq.eligible")
    print(f"published {len(eligible)} eligible scores for {as_of}")


def publish_daily_beta(db: SupabaseRest, as_of: dt.date) -> None:
    """Publish daily T100 beta data while keeping cohort rankings quota-gated."""
    cfg = load_methodology()
    policy = cfg.get("release_policy") or {}
    domains = policy.get("daily_domains") or []
    ranking_types = policy.get("daily_ranking_types") or ["T100"]
    if not domains:
        raise RuntimeError("daily beta publication blocked: no release domains configured")
    ranking_query = (
        f"as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}"
        f"&domain=in.({','.join(domains)})&ranking_type=in.({','.join(ranking_types)})"
    )
    eligible = db.select("bridge_scores", f"select=entity_id&as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}&publish_status=in.(eligible,published)")
    if not eligible:
        raise RuntimeError("daily beta publication blocked: no current eligible scores")
    entity_ids = ",".join(sorted({row["entity_id"] for row in eligible}))
    ranking_query += f"&entity_id=in.({entity_ids})"
    candidates = db.select("bridge_rankings", f"select=id&{ranking_query}&limit=1")
    if not candidates:
        raise RuntimeError("daily beta publication blocked: no eligible CPR/ENT T100 rankings")
    db.patch("bridge_rankings", {"published_at": now_kst().isoformat()}, ranking_query)
    print(f"daily beta published domains={domains} ranking_types={ranking_types} date={as_of}")


def healthcheck(db: SupabaseRest) -> None:
    runs = db.select("bridge_collection_runs", "select=source_id,status,finished_at,fetched_count,accepted_count,error_code&order=started_at.desc&limit=20")
    latest = {}
    for run in runs:
        latest.setdefault(run["source_id"], run)
    required = {"google_news_discovery", "google_news_rss", "opendart"}
    missing = sorted(required - set(latest))
    # Optional expansion sources may legitimately be partial while verified
    # mappings are widened. They are reported but must not block publication
    # of an otherwise valid daily snapshot. Required sources remain hard gates.
    critical = [r for source, r in latest.items() if source in required and r["status"] != "success"]
    print(json.dumps({"ok": not critical and not missing, "latestRuns": list(latest.values()), "missingSources": missing}, ensure_ascii=False, indent=2))
    if critical or missing:
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="BRIDGE data automation")
    parser.add_argument("command", choices=("bootstrap", "audit-targets", "discover", "collect-news", "collect-news-window", "collect-dart", "import-official", "score", "publish-daily", "publish", "export", "healthcheck"))
    parser.add_argument("--date")
    parser.add_argument("--domain", choices=("CPR", "STAR", "GOV", "UNI"))
    parser.add_argument("--file")
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args(argv)
    db = SupabaseRest()
    as_of = publication_date(args.date)
    if args.command == "bootstrap": bootstrap(db)
    elif args.command == "audit-targets":
        if not all(row["exact_match"] for row in audit_targets(db)):
            raise SystemExit(2)
    elif args.command == "discover": discover_candidates(db, as_of)
    elif args.command == "collect-news": collect_news(db, as_of, args.domain)
    elif args.command == "collect-news-window":
        if not args.start or not args.end:
            parser.error("collect-news-window requires --start and --end")
        collect_news(db, as_of, args.domain, dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end))
    elif args.command == "collect-dart": collect_dart(db, as_of)
    elif args.command == "import-official":
        if not args.file:
            parser.error("import-official requires --file")
        import_official(db, args.file, as_of)
    elif args.command == "score": score_day(db, as_of)
    elif args.command == "publish-daily": publish_daily_beta(db, as_of)
    elif args.command == "publish": publish_eligible(db, as_of)
    elif args.command == "export": export_latest(db, as_of)
    elif args.command == "healthcheck": healthcheck(db)


if __name__ == "__main__":
    main()
