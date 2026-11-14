"""Read-only go/no-go gate for the BRIDGE 06:45 KST recovery.

skip    = complete metrics and current published Git export; no work.
export  = complete metrics but a stale/missing Git export; publish/export only.
score   = incomplete metrics but sufficient recorded observations and
          successful essential collection jobs; score/publish/export only.
blocked = source evidence incomplete or inconsistent; alert without blindly
          recollecting or publishing a partial index.

No data mutation or external collection. A failed early run remains visible
instead of being masked by a later superficial 'success'.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

from bridge_pipeline.core import SupabaseRest, publication_date

ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCES = (
    "google_news_rss", "opendart", "academyinfo",
    "gov_official_evaluations", "opendart_financials",
    "wikimedia_pageviews",
)
EXPECTED_ENTITIES = 400
# Observed daily axis coverage is typically ~2,000. Do not rescore from a
# partial ~1,100-row observation set after an interrupted collection.
MIN_OBSERVATIONS = 1600


def choose(date: str, *, source_date: str | None, source_published: bool,
           metric_rows: list[dict], observation_rows: list[dict],
           collection_rows: list[dict]) -> dict:
    unique_metrics = {x.get("entity_id") for x in metric_rows}
    metric_complete = len(metric_rows) == EXPECTED_ENTITIES and len(unique_metrics) == EXPECTED_ENTITIES
    unique_observations = {
        (x.get("entity_id"), x.get("axis")) for x in observation_rows
    }
    has_core_collection = all(
        any(x.get("source_id") == src and x.get("status") == "success" for x in collection_rows)
        for src in CORE_SOURCES
    )
    result = {"date": date, "metrics_count": len(metric_rows),
              "unique_metrics": len(unique_metrics),
              "observations_count": len(observation_rows),
              "unique_entity_axes": len(unique_observations),
              "essential_collectors_succeeded": has_core_collection,
              "source_date": source_date, "source_published": source_published}
    if source_date and source_date > date:
        result.update(mode="skip", reason="repository_contains_newer_publication")
    elif metric_complete:
        if source_date == date and source_published:
            result.update(mode="skip", reason="metrics_and_publication_complete")
        else:
            result.update(mode="export", reason="metrics_complete_publication_missing")
    elif len(observation_rows) >= MIN_OBSERVATIONS and len(unique_observations) >= MIN_OBSERVATIONS and has_core_collection:
        result.update(mode="score", reason="existing_evidence_ready_for_scoring")
    else:
        result.update(mode="blocked", reason="insufficient_validated_existing_evidence")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    date = publication_date(args.date).isoformat()
    dt.date.fromisoformat(date)

    source = json.loads((ROOT / "site/data/latest.json").read_text(encoding="utf-8"))
    db = SupabaseRest()
    metrics = db.select(
        "bridge_index_metrics",
        f"select=entity_id&as_of_date=eq.{date}&limit=500",
    )
    observations = db.select(
        "bridge_axis_observations",
        f"select=entity_id,axis&as_of_date=eq.{date}",
    )
    # Keep this query bounded. The morning's current source successes will
    # be in collection_runs with started_at on the requested KST day.
    kst_start = dt.datetime.combine(dt.date.fromisoformat(date), dt.time.min, dt.timezone(dt.timedelta(hours=9)))
    kst_end = kst_start + dt.timedelta(days=1)
    collections = db.select(
        "bridge_collection_runs",
        f"select=source_id,status,started_at&started_at=gte.{kst_start.isoformat()}"
        f"&started_at=lt.{kst_end.isoformat()}&limit=200",
    )
    result = choose(
        date, source_date=source.get("asOfDate"),
        source_published=source.get("dataStatus") == "published"
        and source.get("recordCount") == EXPECTED_ENTITIES
        and len(source.get("rankings", [])) == EXPECTED_ENTITIES,
        metric_rows=metrics, observation_rows=observations,
        collection_rows=collections,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"mode={result['mode']}\n")
    if result["mode"] == "blocked":
        print("::error::Cannot safely recover from incomplete evidence. No recollection attempted.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
