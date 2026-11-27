"""Target-isolated Google News collection with a strict publication failure gate.

Transient provider failures are never returned as an empty successful result.
Successful targets remain available for idempotent evidence persistence, while
the *whole* required collector stays failed until all targets were searched.
"""
from __future__ import annotations

import urllib.error
from collections.abc import Callable, Sequence
from typing import Any

TRANSIENT_HTTP = frozenset({429, 502, 503, 504})
MAX_CONSECUTIVE_FAILURES = 2


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

    for entity in entities:
        eid = str(entity["id"])
        names = search_names(entity)
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
