"""Target-isolated Google News collection with a strict publication failure gate.

Transient provider failures are never returned as an empty successful result.
Successful targets remain available for idempotent evidence persistence, while
the *whole* required collector stays failed until all targets were searched.
"""
from __future__ import annotations

import urllib.error
import datetime as dt
from collections.abc import Mapping
from collections.abc import Callable, Sequence
from typing import Any

TRANSIENT_HTTP = frozenset({429, 502, 503, 504})
MAX_CONSECUTIVE_FAILURES = 2
RESUME_CONTRACT_VERSION = "rss-target-resume-v1"


class NewsCollectionIncomplete(RuntimeError):
    """Some required target queries failed or were not attempted."""


def search_names(entity: dict) -> list[str]:
    return list(dict.fromkeys(
        name for name in [entity["name"], *(entity.get("aliases") or [])[:2]] if name
    ))


def collect_targets(
    entities: Sequence[dict],
    fetch: Callable[[dict, str], list[Any]],
    *,
    max_consecutive_failures: int = MAX_CONSECUTIVE_FAILURES,
    prior_results: Mapping[str, dict] | None = None,
) -> tuple[list[tuple[dict, list[Any]]], dict[str, dict], list[str]]:
    """Collect target-by-target; stop hammering provider after consecutive errors.

    Empty successful RSS searches are distinct from failed/unattempted queries.
    All results carry explicit per-target statuses. Nothing is scored here.
    """
    if max_consecutive_failures < 1:
        raise ValueError("max_consecutive_failures must be >= 1")
    successes: list[tuple[dict, list[Any]]] = []
    results: dict[str, dict] = {}
    failed: list[str] = []
    streak = 0

    prior_results = prior_results or {}
    for entity in entities:
        eid = str(entity["id"])
        names = search_names(entity)
        if eid in prior_results:
            results[eid] = {**prior_results[eid], "status": "success", "reused_from_prior_run": True}
            continue
        query = " OR ".join(f'"{name}"' for name in names)
        if streak >= max_consecutive_failures:
            results[eid] = {
                "status": "not_attempted", "fetched_count": None,
                "matched_count": 0, "query_names": names,
                "error_code": "PROVIDER_CIRCUIT_OPEN",
            }
            failed.append(eid)
            continue
        try:
            items = fetch(entity, query)
        except urllib.error.HTTPError as exc:
            if exc.code not in TRANSIENT_HTTP:
                raise
            streak += 1
            results[eid] = {
                "status": "failed", "fetched_count": None,
                "matched_count": 0, "query_names": names,
                "error_code": f"HTTP_{exc.code}",
            }
            failed.append(eid)
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            streak += 1
            results[eid] = {
                "status": "failed", "fetched_count": None,
                "matched_count": 0, "query_names": names,
                "error_code": type(exc).__name__,
            }
            failed.append(eid)
            continue
        streak = 0
        successes.append((entity, items))
        results[eid] = {
            "status": "success", "fetched_count": len(items),
            "matched_count": 0, "query_names": names,
        }

    return successes, results, failed


def _same_instant(value: str | None, reference: dt.datetime) -> bool:
    try:
        timestamp = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return bool(timestamp.tzinfo and timestamp == reference)
    except (TypeError, ValueError):
        return False


def resumable_successes(
    runs: Sequence[dict], entities: Sequence[dict], as_of: dt.date,
    window_start: dt.datetime, window_end: dt.datetime, methodology_version: str,
) -> dict[str, dict]:
    """Reuse only a completed, persisted partial attempt with identical scope.

    Never resume from an unknown/legacy failure, an interrupted database write,
    another day/window/methodology, or a changed target roster/search alias.
    The current run must still verify every non-reused target before success.
    """
    roster = {str(e["id"]): search_names(e) for e in entities}
    for attempt in runs:
        diag = attempt.get("diagnostics") or {}
        statuses = diag.get("entity_results") or {}
        if (
            attempt.get("status") != "failed"
            or diag.get("partial_evidence_saved") is not True
            or diag.get("observation_as_of") != as_of.isoformat()
            or diag.get("methodology_version") != methodology_version
            or diag.get("resume_contract_version") != RESUME_CONTRACT_VERSION
            or not _same_instant(attempt.get("window_start"), window_start)
            or not _same_instant(attempt.get("window_end"), window_end)
            or not isinstance(statuses, dict)
            or set(statuses) != set(roster)
        ):
            continue
        if any(not isinstance(v, dict) or v.get("query_names") != roster[eid]
               for eid, v in statuses.items()):
            continue
        eligible = {
            eid: details for eid, details in statuses.items()
            if details.get("status") == "success"
            and isinstance(details.get("fetched_count"), int)
            and details["fetched_count"] >= 0
            and isinstance(details.get("matched_count"), int)
            and details["matched_count"] >= 0
        }
        return eligible
    return {}
