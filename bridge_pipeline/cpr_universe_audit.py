"""Audit the CPR universe from registry through public T100 generation.

This module is deliberately read-only. It identifies the first stage that
shrinks the active CPR universe without changing scores, weights, evidence,
or publication eligibility.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .core import ROOT, SupabaseRest, load_methodology, publication_date


def diagnose(rows: dict[str, list[dict[str, Any]]], config: dict[str, Any]) -> dict[str, Any]:
    entities = rows["entities"]
    entity_ids = {row["id"] for row in entities}
    observations = [row for row in rows["observations"] if row["entity_id"] in entity_ids]
    scores = [row for row in rows["scores"] if row["entity_id"] in entity_ids]
    rankings = [row for row in rows["rankings"] if row["entity_id"] in entity_ids]
    collection = rows.get("collection", [])

    latest_run = collection[0] if collection else {}
    entity_results = (latest_run.get("diagnostics") or {}).get("entity_results") or {}
    collected = {entity_id for entity_id, state in entity_results.items()
                 if state.get("status") == "success" and entity_id in entity_ids}
    observed = {row["entity_id"] for row in observations}
    scored = {row["entity_id"] for row in scores}
    eligible = {row["entity_id"] for row in scores
                if row.get("publish_status") in {"eligible", "published"}}
    generated = {row["entity_id"] for row in rankings}
    published = {row["entity_id"] for row in rankings if row.get("published_at")}

    gate = (config.get("beta_eligibility") or {}).get("CPR", {})
    min_families = int(gate.get("minimum_source_families", config["minimum_source_families"]))
    min_confidence = float(gate.get("minimum_confidence_score", config["trust_thresholds"]["C"]))
    reasons = Counter()
    for row in scores:
        if row["entity_id"] in eligible:
            continue
        diagnostics = row.get("diagnostics") or {}
        families = int(diagnostics.get("source_families") or 0)
        confidence = float(row.get("confidence_score") or 0)
        if row.get("score") is None:
            reasons["score_unavailable"] += 1
        if families < min_families:
            reasons["insufficient_source_families"] += 1
        if confidence < min_confidence:
            reasons["confidence_below_gate"] += 1

    stages = {
        "active_registry": len(entity_ids),
        "collection_completed": len(collected),
        "axis_observed": len(observed),
        "score_computed": len(scored),
        "publication_eligible": len(eligible),
        "t100_generated": len(generated),
        "t100_published": len(published),
    }
    ordered = list(stages.items())
    losses = [
        {"from": ordered[i - 1][0], "to": ordered[i][0],
         "count": ordered[i - 1][1] - ordered[i][1]}
        for i in range(1, len(ordered)) if ordered[i - 1][1] > ordered[i][1]
    ]
    largest = max(losses, key=lambda item: item["count"], default=None)
    return {
        "domain": "CPR",
        "as_of_date": rows["as_of_date"],
        "methodology_version": config["version"],
        "stages": stages,
        "largest_loss": largest,
        "eligibility_exclusion_reasons": dict(sorted(reasons.items())),
        "stale_generated_rows": len(generated - eligible),
        "status": "warning" if len(published) < len(entity_ids) else "ok",
    }


def collect(db: SupabaseRest, as_of: dt.date, config: dict[str, Any]) -> dict[str, Any]:
    day = as_of.isoformat()
    version = config["version"]
    entities = db.select(
        "bridge_entities", "select=id,name,external_id&domain=eq.CPR&active=eq.true"
    )
    collection = db.select(
        "bridge_collection_runs",
        "select=id,status,diagnostics,finished_at&source_id=eq.google_news_rss&status=eq.success"
        f"&diagnostics->>observation_as_of=eq.{day}&order=finished_at.desc&limit=1",
    )
    observations = db.select(
        "bridge_axis_observations",
        f"select=entity_id,axis,status&as_of_date=eq.{day}&methodology_version=eq.{version}",
    )
    scores = db.select(
        "bridge_scores",
        "select=entity_id,score,confidence_score,publish_status,diagnostics"
        f"&as_of_date=eq.{day}&methodology_version=eq.{version}",
    )
    rankings = db.select(
        "bridge_rankings",
        "select=entity_id,published_at"
        f"&as_of_date=eq.{day}&domain=eq.CPR&ranking_type=eq.T100&methodology_version=eq.{version}",
    )
    return {
        "as_of_date": day, "entities": entities, "collection": collection,
        "observations": observations, "scores": scores, "rankings": rankings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only CPR universe/T100 bottleneck audit")
    parser.add_argument("--date", help="KST date YYYY-MM-DD")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    as_of = dt.date.fromisoformat(args.date) if args.date else publication_date()
    config = load_methodology()
    report = diagnose(collect(SupabaseRest(), as_of, config), config)
    output = (Path(args.output) if args.output
              else ROOT / "data" / "audit" / f"cpr_universe_{as_of.isoformat()}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "ok":
        print("::warning title=CPR T100 coverage::"
              + json.dumps(report["largest_loss"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
