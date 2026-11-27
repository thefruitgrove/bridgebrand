"""Fail-closed, read-only prepublication check for BRIDGE daily T100.

Never changes scores, ranks or evidence. This MUST run before any published_at
mutation, so a bad single domain cannot replace the last valid publication.
"""
from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Mapping

EXPECTED_PER_DOMAIN = 100
AXES = frozenset("BRIDGE")  # Only labels; scoring is done upstream.


def validate_rows(rankings: list[dict], scores: list[dict], metrics: list[dict],
                  expected_domains: list[str], as_of: dt.date) -> dict:
    if not expected_domains or len(set(expected_domains)) != len(expected_domains):
        raise RuntimeError("PREPUBLISH_BAD_DOMAIN_CONFIG")
    score_map = {(r["entity_id"], r.get("methodology_version")): r for r in scores}
    metric_entities = {r["entity_id"] for r in metrics}
    errors: list[str] = []
    report: dict[str, dict] = {}

    if len(metrics) != len(set(r["entity_id"] for r in metrics)):
        errors.append("duplicate daily index metrics")
    if len(rankings) != EXPECTED_PER_DOMAIN * len(expected_domains):
        errors.append(f"ranking count {len(rankings)} != {EXPECTED_PER_DOMAIN * len(expected_domains)}")
    if len(metric_entities) != EXPECTED_PER_DOMAIN * len(expected_domains):
        errors.append(f"metrics count {len(metric_entities)} != {EXPECTED_PER_DOMAIN * len(expected_domains)}")

    for domain in expected_domains:
        members = [r for r in rankings if r.get("domain") == domain and r.get("ranking_type") == "T100"]
        positions = sorted((r.get("rank") for r in members), key=lambda v: (v is None, str(v)))
        try:
            numeric_positions = sorted(int(p) for p in positions)
        except (ValueError, TypeError):
            numeric_positions = []
        identities = [r.get("entity_id") for r in members]
        if len(members) != EXPECTED_PER_DOMAIN:
            errors.append(f"{domain}: {len(members)} rows instead of 100")
        if numeric_positions != list(range(1, EXPECTED_PER_DOMAIN + 1)):
            errors.append(f"{domain}: non-contiguous or duplicate ranks")
        if len(set(identities)) != len(identities) or None in identities:
            errors.append(f"{domain}: duplicate/missing entity ids")
        ordered = sorted(members, key=lambda r: int(r.get("rank") or 0))
        for i, row in enumerate(ordered):
            score = row.get("score")
            try:
                score_number = float(score)
            except (TypeError, ValueError):
                score_number = float("nan")
            if not math.isfinite(score_number) or not 0 <= score_number <= 100:
                errors.append(f"{domain}: invalid score at rank {row.get('rank')}")
                continue
            if i and float(ordered[i - 1].get("score") or 0) + 1e-9 < score_number:
                errors.append(f"{domain}: ascending score at rank {row.get('rank')}")
            version = row.get("methodology_version")
            authoritative = score_map.get((row.get("entity_id"), version))
            if authoritative is None:
                errors.append(f"{domain}: missing source score for {row.get('entity_id')}")
            elif (authoritative.get("score") is None or
                  abs(float(authoritative["score"]) - score_number) > 0.001 or
                  authoritative.get("trust_grade") != row.get("trust_grade")):
                errors.append(f"{domain}: score/trust mismatch for {row.get('entity_id')}")
            if row.get("entity_id") not in metric_entities:
                errors.append(f"{domain}: missing index metric for {row.get('entity_id')}")
        report[domain] = {"rows": len(members), "unique_entities": len(set(identities)),
                          "rank_sequence_valid": numeric_positions == list(range(1, EXPECTED_PER_DOMAIN + 1))}
    unexpected = set(r.get("domain") for r in rankings) - set(expected_domains)
    if unexpected:
        errors.append(f"unexpected domains: {sorted(unexpected)}")
    result = {"date": as_of.isoformat(), "expected_total": EXPECTED_PER_DOMAIN * len(expected_domains),
              "actual_total": len(rankings), "domains": report, "errors": errors, "ok": not errors}
    if errors:
        raise RuntimeError("PREPUBLISH_BLOCKED " + json.dumps(result, ensure_ascii=False))
    return result


def check(db, as_of: dt.date, cfg: Mapping) -> dict:
    policy = cfg.get("release_policy") or {}
    domains = policy.get("daily_domains") or []
    types = policy.get("daily_ranking_types") or ["T100"]
    if types != ["T100"]:
        raise RuntimeError("PREPUBLISH_UNSUPPORTED_RANKING_TYPES: " + repr(types))
    if not domains:
        raise RuntimeError("PREPUBLISH_NO_DOMAINS")
    version = cfg["version"]
    base = f"as_of_date=eq.{as_of.isoformat()}&methodology_version=eq.{version}"
    domain_filter = f"&domain=in.({','.join(domains)})&ranking_type=eq.T100"
    ranks = db.select("bridge_rankings",
        "select=entity_id,domain,ranking_type,rank,score,trust_grade,methodology_version&" + base + domain_filter)
    scores = db.select("bridge_scores",
        "select=entity_id,score,trust_grade,methodology_version&" + base)
    metrics = db.select("bridge_index_metrics",
        "select=entity_id&" + base)
    result = validate_rows(ranks, scores, metrics, domains, as_of)
    print("PASS prepublication contract: " + json.dumps(result, ensure_ascii=False))
    return result


def main() -> None:
    import argparse
    from bridge_pipeline.core import SupabaseRest, load_methodology, publication_date
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    as_of = publication_date(args.date)
    check(SupabaseRest(), as_of, load_methodology())


if __name__ == "__main__":
    main()
