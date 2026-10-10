from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

from .core import (
    ROOT, SupabaseRest, classify_headline, dump_json, fetch_google_news,
    iso_week, load_methodology, now_kst, publication_date, robust_rank,
    trust_grade, weighted_score
)
from .targets import load_targets, target_quota_report


def bootstrap(db: SupabaseRest) -> None:
    cfg = load_methodology()
    db.upsert("bridge_methodology_versions", [{"version": cfg["version"], "config": cfg, "status": "shadow"}], "version")
    db.upsert("bridge_entities", load_targets(), "domain,external_id")
    print(f"bootstrapped {len(load_targets())} entities and methodology {cfg['version']}")


def audit_targets(db: SupabaseRest | None = None) -> list[dict]:
    report = (db.select("bridge_target_quota_status", "select=*&order=domain.asc,cohort_code.asc")
              if db else target_quota_report())
    print(json.dumps({"ok": all(row["exact_match"] for row in report), "cohorts": report}, ensure_ascii=False, indent=2))
    return report


def _start_run(db: SupabaseRest, source_id: str, start: dt.datetime, end: dt.datetime) -> str:
    result = db.insert("bridge_collection_runs", [{"source_id": source_id, "window_start": start.isoformat(), "window_end": end.isoformat(), "status": "running"}])
    return result[0]["id"]


def collect_news(db: SupabaseRest, as_of: dt.date, domain: str | None = None) -> None:
    entities = db.select("bridge_entities", "select=id,external_id,domain,name,aliases&active=eq.true" + (f"&domain=eq.{quote(domain)}" if domain else ""))
    end = dt.datetime.combine(as_of + dt.timedelta(days=1), dt.time.min, tzinfo=now_kst().tzinfo)
    start = end - dt.timedelta(days=1)
    run_id = _start_run(db, "google_news_rss", start, end)
    fetched = accepted = rejected = 0
    seen: set[str] = set()
    try:
        raw_rows: list[dict] = []
        staged: list[tuple[dict, object]] = []
        for entity in entities:
            items = fetch_google_news(f'"{entity["name"]}"', 1)
            fetched += len(items)
            for item in items:
                if item.content_hash in seen:
                    continue
                seen.add(item.content_hash)
                signals = classify_headline(item, entity["external_id"], entity["name"], entity.get("aliases") or [])
                if not signals:
                    rejected += 1
                    continue
                accepted += 1
                raw_rows.append({**asdict(item), "collection_run_id": run_id})
                staged.extend((entity, signal) for signal in signals)
        inserted = db.upsert("bridge_raw_items", raw_rows, "source_id,content_hash")
        raw_ids = {row["content_hash"]: row["id"] for row in inserted}
        signal_rows = []
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
        db.upsert("bridge_signals", signal_rows, "entity_id,raw_item_id,axis,signal_type")
        db.patch("bridge_collection_runs", {"status": "success", "finished_at": now_kst().isoformat(), "fetched_count": fetched, "accepted_count": accepted, "rejected_count": rejected}, f"id=eq.{run_id}")
        print(f"news collection success: fetched={fetched} accepted={accepted} rejected={rejected}")
    except Exception as exc:
        db.patch("bridge_collection_runs", {"status": "failed", "finished_at": now_kst().isoformat(), "fetched_count": fetched, "accepted_count": accepted, "rejected_count": rejected, "error_code": type(exc).__name__, "error_detail": str(exc)[:2000]}, f"id=eq.{run_id}")
        db.insert("bridge_pipeline_alerts", [{"run_id": run_id, "severity": "critical", "code": "COLLECTOR_FAILED", "message": str(exc)[:1000], "context": {"source": "google_news_rss"}}])
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
    rows = db.select("bridge_public_latest_rankings", "select=*&order=domain.asc,ranking_type.asc,rank.asc")
    labels = load_methodology().get("release_policy", {}).get("public_domain_labels", {})
    for row in rows:
        row["internalDomain"] = row["domain"]
        row["domain"] = labels.get(row["domain"], row["domain"])
    payload = {
        "schemaVersion": "1.0",
        "generatedAt": now_kst().isoformat(),
        "asOfDate": as_of.isoformat(),
        "week": iso_week(as_of),
        "rankings": rows,
        "recordCount": len(rows),
        "dataStatus": "published" if rows else "no-published-snapshot"
    }
    dump_json(ROOT / "site" / "data" / "latest.json", payload)
    dump_json(ROOT / "data" / "pipeline_status.json", {"generatedAt": payload["generatedAt"], "asOfDate": payload["asOfDate"], "recordCount": len(rows)})
    print(f"exported {len(rows)} published ranking rows")


def import_official(db: SupabaseRest, csv_path: str, as_of: dt.date) -> None:
    cfg = load_methodology()
    entities = {r["external_id"]: r for r in db.select("bridge_entities", "select=id,external_id&active=eq.true")}
    rows = []
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
            rows.append({
                "entity_id": entity["id"], "as_of_date": as_of.isoformat(), "axis": axis,
                "score": score, "confidence": confidence, "coverage": float(record.get("coverage") or confidence),
                "source_families": int(record.get("source_families") or 1),
                "evidence_count": int(record.get("evidence_count") or 1),
                "freshness_days": int(record.get("freshness_days") or 0), "status": "measured",
                "methodology_version": cfg["version"],
                "diagnostics": {"source_id": record.get("source_id"), "evidence_url": record.get("evidence_url"), "note": record.get("note")}
            })
    db.upsert("bridge_axis_observations", rows, "entity_id,as_of_date,axis,methodology_version")
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


def score_day(db: SupabaseRest, as_of: dt.date) -> None:
    cfg = load_methodology()
    # 같은 날짜를 재실행할 때 이전 실행의 적격 행이 공개 상태로 남으면 서로
    # 다른 스냅샷의 순위가 섞인다. 현재 방법론의 당일 공개표시를 먼저 해제하고
    # 이번 계산에서 통과한 행만 publish 단계에서 다시 공개한다.
    db.patch(
        "bridge_rankings", {"published_at": None},
        f"as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}"
    )
    entities = db.select("bridge_entities", "select=id,external_id,domain,subcategory&active=eq.true")
    entity_by_id = {e["id"]: e for e in entities}
    since = (as_of - dt.timedelta(days=28)).isoformat()
    signals = db.select("bridge_signals", f"select=entity_id,axis,direction,magnitude,confidence,occurred_at,review_status,source_id&occurred_at=gte.{since}T00:00:00Z")
    grouped: dict[tuple[str, str], list[dict]] = {}
    for signal in signals:
        # 부정 귀속은 사람의 승인을 요구하지만, 명시적인 긍정 반응 신호는
        # 자동 집계한다. 무보도 자체를 부정 감성으로 간주하지는 않는다.
        needs_review = signal["axis"] in cfg["review_required"] and int(signal["direction"]) < 0
        if signal["review_status"] == "rejected" or (needs_review and signal["review_status"] != "approved"):
            continue
        grouped.setdefault((signal["entity_id"], signal["axis"]), []).append(signal)

    max_counts: dict[tuple[str, str], int] = {}
    for (entity_id, axis), values in grouped.items():
        domain = entity_by_id.get(entity_id, {}).get("domain")
        max_counts[(domain, axis)] = max(max_counts.get((domain, axis), 0), len(values))

    existing_rows = db.select(
        "bridge_axis_observations",
        f"select=entity_id,axis,score,confidence,coverage,source_families,evidence_count,freshness_days,status,diagnostics"
        f"&as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{cfg['version']}"
    )
    existing = {(row["entity_id"], row["axis"]): row for row in existing_rows}
    observations: list[dict] = []
    for (entity_id, axis), values in grouped.items():
        entity = entity_by_id.get(entity_id)
        if not entity:
            continue
        count = len(values)
        max_count = max_counts[(entity["domain"], axis)]
        if axis == "R":
            penalty = sum(float(v["magnitude"]) * float(v["confidence"]) for v in values if int(v["direction"]) < 0)
            benefit = sum(float(v["magnitude"]) * float(v["confidence"]) for v in values if int(v["direction"]) > 0)
            # 반응은 중립점 50에서 시작한다. 반응이 없다는 이유만으로 긍정
            # 100점을 부여하던 종전 구조를 제거한다.
            score = max(0.0, min(100.0, 50.0 + benefit - penalty))
        else:
            score = 100.0 * math.log1p(count) / math.log1p(max_count) if max_count else None
        families = len({v["source_id"] for v in values})
        confidence = min(1.0, (sum(float(v["confidence"]) for v in values) / count) * min(1.0, count / 5) * min(1.0, families / 2))
        observation = {
            "entity_id": entity_id, "as_of_date": as_of.isoformat(), "axis": axis,
            "score": round(score, 2) if score is not None else None,
            "confidence": round(confidence, 4), "coverage": round(min(1.0, count / 5), 4),
            "source_families": families, "evidence_count": count, "freshness_days": 0,
            "status": "measured", "methodology_version": cfg["version"],
            "diagnostics": {"window_days": 28, "aggregation": "domain_log_count" if axis != "R" else "reviewed_event_decay_pending", "source_ids": sorted({v["source_id"] for v in values})}
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
        for axis in ("B", "I"):
            key = (entity["id"], axis)
            if key in observed_keys:
                continue
            zero = {
                "entity_id": entity["id"], "as_of_date": as_of.isoformat(), "axis": axis,
                "score": 0.0, "confidence": 0.70 if axis == "B" else 0.60,
                "coverage": 1.0, "source_families": 1, "evidence_count": 0,
                "freshness_days": 0, "status": "measured", "methodology_version": cfg["version"],
                "diagnostics": {"window_days": 28, "aggregation": "observed_zero_news_monitoring",
                                "source_ids": ["google_news_rss"], "meaning": "검색 수행 후 적격 신호 0건"}
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
        # 기억 점유/활동 지속성 보정. 28일 적격 뉴스 노출을 동일 영역 내
        # 로그 정규화하고, ENT 최대 35%, CPR 최대 10%의 감쇠를 적용한다.
        attention_weight = float((cfg.get("attention_continuity") or {}).get(entity["domain"], 0))
        attention_count = len(grouped.get((entity["id"], "B"), []))
        attention_max = max_counts.get((entity["domain"], "B"), 0)
        attention_index = (math.log1p(attention_count) / math.log1p(attention_max)) if attention_max else 0.0
        base_score = score
        if score is not None and attention_weight:
            score = round(score * ((1.0 - attention_weight) + attention_weight * attention_index), 2)
        source_ids = set()
        for observation in obs:
            diagnostics = observation.get("diagnostics") or {}
            source_ids.update(diagnostics.get("source_ids") or ([diagnostics.get("source_id")] if diagnostics.get("source_id") else []))
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
                            "attention_count_28d": attention_count,
                            "attention_index": round(attention_index, 4),
                            "attention_weight": attention_weight,
                            "beta_gate": {"minimum_source_families": min_families, "minimum_confidence_score": min_confidence}}
        })
        if eligible:
            candidates.append({**entity, "score": score, "confidence_score": confidence_score, "trust_grade": grade})
    db.upsert("bridge_scores", score_rows, "entity_id,as_of_date,methodology_version")

    previous_rows = db.select("bridge_rankings", f"select=entity_id,rank,score,domain,ranking_type&as_of_date=lt.{as_of.isoformat()}&order=as_of_date.desc&limit=1000")
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
            for member in robust_rank(members):
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
    required = {"google_news_rss", "opendart"}
    missing = sorted(required - set(latest))
    critical = [r for r in latest.values() if r["status"] != "success"]
    print(json.dumps({"ok": not critical and not missing, "latestRuns": list(latest.values()), "missingSources": missing}, ensure_ascii=False, indent=2))
    if critical or missing:
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="BRIDGE data automation")
    parser.add_argument("command", choices=("bootstrap", "audit-targets", "collect-news", "collect-dart", "import-official", "score", "publish-daily", "publish", "export", "healthcheck"))
    parser.add_argument("--date")
    parser.add_argument("--domain", choices=("CPR", "STAR", "GOV", "UNI"))
    parser.add_argument("--file")
    args = parser.parse_args(argv)
    db = SupabaseRest()
    as_of = publication_date(args.date)
    if args.command == "bootstrap": bootstrap(db)
    elif args.command == "audit-targets":
        if not all(row["exact_match"] for row in audit_targets(db)):
            raise SystemExit(2)
    elif args.command == "collect-news": collect_news(db, as_of, args.domain)
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
