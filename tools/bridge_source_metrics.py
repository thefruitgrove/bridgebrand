"""BRIDGE collection-source reliability aggregates from read-only DB evidence.

No raw diagnostics, articles, company names, errors, or database credentials
are exported. Counts refer to collector attempts, NOT distinct observed days.
These are operational run metrics, not a statistical confidence estimate.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
SOURCE_LABELS = {
    "google_news_rss": "뉴스 RSS",
    "opendart": "DART 공시",
    "opendart_financials": "기업 재무자료",
    "academyinfo": "대학 공식자료",
    "gov_official_evaluations": "정부 공식평가",
    "wikimedia_pageviews": "위키미디어 조회",
    "youtube_data_api": "YouTube 공식 채널",
    "google_news_discovery": "뉴스 탐색(참고)",
}
REQUIRED_SOURCES = frozenset({
    "google_news_rss", "opendart", "opendart_financials",
    "academyinfo", "gov_official_evaluations", "wikimedia_pageviews",
})
SUCCESS = frozenset({"success"})
FAILURES = frozenset({"failed", "failure", "error"})
MAX_WINDOW_DAYS = 30


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        value = value.replace("Z", "+00:00")
        result = dt.datetime.fromisoformat(value)
        return result if result.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def summarize_sources(rows: list[dict], today: dt.date,
                      *, window_days: int = 30) -> dict:
    if window_days < 1 or window_days > MAX_WINDOW_DAYS:
        raise ValueError("invalid collection observation horizon")
    start = today - dt.timedelta(days=window_days - 1)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        source = row.get("source_id")
        if source not in SOURCE_LABELS:
            continue
        started = parse_time(row.get("started_at"))
        if started is None:
            continue
        day = started.astimezone(KST).date()
        if start <= day <= today:
            grouped[source].append({**row, "_start": started, "_day": day})

    summaries = []
    for source in SOURCE_LABELS:
        items = sorted(grouped[source], key=lambda r: r["_start"])
        last = items[-1] if items else None
        successes = sum(bool(r.get("status") in SUCCESS and parse_time(r.get("finished_at"))) for r in items)
        failures = sum(r.get("status") in FAILURES for r in items)
        incomplete = len(items) - successes - failures
        durations = []
        days: set[dt.date] = set()
        success_days: set[dt.date] = set()
        for row in items:
            days.add(row["_day"])
            finished = parse_time(row.get("finished_at"))
            if finished and finished >= row["_start"]:
                seconds = (finished - row["_start"]).total_seconds()
                if seconds <= 86400:
                    durations.append(round(seconds / 60, 2))
            if row.get("status") in SUCCESS and finished is not None:
                success_days.add(row["_day"])

        # Distinguish run success ratio (attempts) from daily observation
        # coverage; a successful retry does not erase earlier run failures.
        count = len(items)
        last_status = (last or {}).get("status")
        # "success" without a completion timestamp is not verified success.
        if last_status in SUCCESS and parse_time((last or {}).get("finished_at")) is None:
            last_status = "unknown"
        summaries.append({
            "sourceId": source,
            "label": SOURCE_LABELS[source],
            "required": source in REQUIRED_SOURCES,
            "runs": count,
            "successfulRuns": successes,
            "failedRuns": failures,
            "incompleteRuns": incomplete,
            "successRatePct": round(100 * successes / count, 1) if count else None,
            "observedDays": len(days),
            "successfulDays": len(success_days),
            "averageDurationMinutes": round(sum(durations) / len(durations), 1) if durations else None,
            "lastRunDate": last["_day"].isoformat() if last else None,
            "lastRunStatus": str(last_status) if last_status in (SUCCESS | FAILURES) else (
                "unknown" if last else "not_observed"
            ),
        })
    total_runs = sum(r["runs"] for r in summaries)
    return {
        "windowStart": start.isoformat(),
        "windowEnd": today.isoformat(),
        "windowDays": window_days,
        "totalRuns": total_runs,
        "sourceCount": len(SOURCE_LABELS),
        "metricsAvailable": bool(total_runs),
        "sources": summaries,
    }


def collect_source_summary(db, today: dt.date, *, window_days: int = 30) -> dict:
    """Read-only, paginated DB query with a bounded date range; no error details."""
    if not 1 <= window_days <= MAX_WINDOW_DAYS:
        raise ValueError("invalid days")
    start = today - dt.timedelta(days=window_days - 1)
    start_iso = dt.datetime.combine(start, dt.time.min, tzinfo=KST).isoformat()
    end_iso = dt.datetime.combine(today + dt.timedelta(days=1), dt.time.min, tzinfo=KST).isoformat()
    query = (
        "select=source_id,status,started_at,finished_at"
        f"&started_at=gte.{start_iso}&started_at=lt.{end_iso}"
        "&order=started_at.desc"
    )
    rows = db.select("bridge_collection_runs", query)
    return summarize_sources(rows, today, window_days=window_days)
