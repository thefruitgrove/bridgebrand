"""BRIDGE scheduled-job punctuality from immutable GitHub Actions run metadata.

GitHub's cron uses UTC and is best-effort; use KST observed creation timestamps
rather than pretending that YAML schedule times are guaranteed start times.
No workflow dispatch, DB write, scoring, secret or raw log access.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
# Workflow name -> expected Korean clock, independent of data pipeline outcomes.
SCHEDULES = (
    ("BRIDGE Daily Pipeline", "정규 수집", 5, 15),
    ("BRIDGE Recover Existing Observations", "근거 복구", 6, 45),
    ("BRIDGE Daily Fallback — verify before dispatch", "재수집 판단", 7, 15),
    ("BRIDGE Live Deployment Verification", "실서비스 검증", 8, 30),
)
DELAY_LIMIT_MINUTES = 60
ALLOWED_BRANCH = "main"


def scheduled_datetime(day: dt.date, hour: int, minute: int) -> dt.datetime:
    return dt.datetime.combine(day, dt.time(hour, minute), tzinfo=KST)


def parse_utc(value) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def punctuality(runs: list[dict], now: dt.datetime,
                *, tolerance_minutes: int = DELAY_LIMIT_MINUTES,
                observed_window_days: int = 7) -> dict:
    if now.tzinfo is None:
        raise ValueError("local observation time must have timezone")
    if tolerance_minutes < 1 or observed_window_days < 1 or observed_window_days > 30:
        raise ValueError("invalid schedule audit bounds")
    now = now.astimezone(KST)
    day = now.date()
    rows = []
    for workflow, label, hour, minute in SCHEDULES:
        expected = scheduled_datetime(day, hour, minute)
        matches = []
        past_delays: list[int] = []
        for run in runs:
            if (run.get("name") != workflow or run.get("head_branch") != ALLOWED_BRANCH
                or run.get("event") != "schedule"):
                continue
            started = parse_utc(run.get("created_at"))
            if started is None:
                continue
            local = started.astimezone(KST)
            # The event timestamp is when GitHub created the run, not the
            # runner's first step nor proof of successful publication.
            if local.date() == day:
                matches.append(local)
            past_date = local.date()
            if (0 <= (day - past_date).days < observed_window_days
                and local >= scheduled_datetime(past_date, hour, minute)):
                past_delays.append(int((local - scheduled_datetime(past_date, hour, minute)).total_seconds() // 60))
        observed = min(matches) if matches else None
        lag = int((observed - expected).total_seconds() // 60) if observed else None
        if observed:
            current_status = "late" if lag > tolerance_minutes else "observed"
        elif now < expected:
            current_status = "pending"
        elif (now - expected).total_seconds() // 60 <= tolerance_minutes:
            current_status = "within_grace"
        else:
            current_status = "overdue"
        rows.append({
            "name": workflow,
            "label": label,
            "expectedKst": expected.strftime("%H:%M"),
            "observedKst": observed.strftime("%H:%M") if observed else None,
            "status": current_status,
            "delayMinutes": lag,
            "historicalObservedRuns": len(past_delays),
            "historicalMaxDelayMinutes": max(past_delays) if past_delays else None,
        })
    return {
        "date": day.isoformat(),
        "observedAtKst": now.isoformat(),
        "graceMinutes": tolerance_minutes,
        "jobs": rows,
        "overdueCount": sum(row["status"] == "overdue" for row in rows),
        "lateCount": sum(row["status"] == "late" for row in rows),
        "scheduleRisk": any(row["status"] in {"overdue", "late"} for row in rows),
        "note": "GitHub run creation timestamp, not successful collection or exact runner start",
    }
