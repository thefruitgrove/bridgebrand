"""BRIDGE daily read-only production monitor and evidence-backed 7-day scorecard.

No scoring, publishing, source collection, DB mutation or deployment.
Historical delivery is only credited to completed monitor runs; never infer
past live correctness from today's snapshot.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
FIRST_DAY = dt.date(2026, 11, 28)
DAILY_WORKFLOW = "BRIDGE Daily Pipeline"
RECOVERY_WORKFLOW = "BRIDGE Recover Existing Observations"
MONITOR_WORKFLOW = "BRIDGE 7-Day Reliability Monitor"
ALLOWED_EVENTS = frozenset({"schedule", "workflow_dispatch"})
ROOT = Path(__file__).resolve().parents[1]


def run_day(run: dict) -> dt.date | None:
    try:
        timestamp = dt.datetime.fromisoformat(str(run["created_at"]).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            return None
        return timestamp.astimezone(KST).date()
    except (KeyError, ValueError, TypeError):
        return None


def successful_run(runs: list[dict], day: dt.date, workflow_name: str) -> bool:
    return any(
        run.get("name") == workflow_name
        and run.get("head_branch") == "main"
        and run.get("event") in ALLOWED_EVENTS
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and run_day(run) == day
        for run in runs
    )


def failed_run_count(runs: list[dict], day: dt.date, workflow_name: str) -> int:
    return sum(
        run.get("name") == workflow_name
        and run.get("head_branch") == "main"
        and run.get("event") in ALLOWED_EVENTS
        and run.get("status") == "completed"
        and run.get("conclusion") == "failure"
        and run_day(run) == day
        for run in runs
    )


def day_status(day: dt.date, today: dt.date, *, live_ok: bool,
               db_ok: bool, repository_date: str | None,
               runs: list[dict], first_day: dt.date = FIRST_DAY) -> dict:
    if day < first_day or day > today:
        return {"date": day.isoformat(), "status": "not_observed"}
    primary = successful_run(runs, day, DAILY_WORKFLOW)
    recovery = successful_run(runs, day, RECOVERY_WORKFLOW)
    primary_failures = failed_run_count(runs, day, DAILY_WORKFLOW)
    if day == today:
        delivered = bool(live_ok and db_ok and repository_date == day.isoformat())
        status = ("healthy" if primary and delivered and not primary_failures else
                  "degraded" if delivered else "failure")
    else:
        # Past live status cannot be reconstructed from the CURRENT live page.
        # Count only completed monitor-run evidence from that day.
        verified = successful_run(runs, day, MONITOR_WORKFLOW)
        if verified:
            status = "healthy" if primary and not primary_failures else "degraded"
        elif failed_run_count(runs, day, MONITOR_WORKFLOW):
            status = "failure"
        else:
            status = "not_observed"
    return {"date": day.isoformat(), "status": status,
            "primary_success": primary, "primary_failures": primary_failures,
            "recovery_success": recovery}


def scorecard(today: dt.date, *, live_ok: bool, db_ok: bool,
              repository_date: str | None, runs: list[dict],
              first_day: dt.date = FIRST_DAY) -> dict:
    if today < first_day:
        return {"status": "not_started", "today": today.isoformat(),
                "startDate": first_day.isoformat(), "days": [], "observed_days": 0,
                "delivered_days": 0, "clean_days": 0, "seven_day_clean": False}
    first = max(first_day, today - dt.timedelta(days=6))
    days = [day_status(first + dt.timedelta(days=n), today,
                       live_ok=live_ok, db_ok=db_ok,
                       repository_date=repository_date, runs=runs,
                       first_day=first_day)
            for n in range((today - first).days + 1)]
    observed = [row for row in days if row["status"] != "not_observed"]
    clean = sum(row["status"] == "healthy" for row in days)
    delivered = sum(row["status"] in {"healthy", "degraded"} for row in days)
    result = {
        "status": days[-1]["status"], "today": today.isoformat(),
        "startDate": first_day.isoformat(), "windowStart": first.isoformat(),
        "windowEnd": today.isoformat(), "days": days,
        "observed_days": len(observed), "delivered_days": delivered,
        "clean_days": clean,
        "seven_day_delivery": len(days) == 7 and delivered == 7,
        "seven_day_clean": len(days) == 7 and clean == 7,
    }
    return result


def github_runs(repo: str, token: str) -> list[dict]:
    """Fetch completed production workflow runs, not untrusted QA branch runs."""
    if not token:
        raise RuntimeError("GITHUB_TOKEN_MISSING")
    result: list[dict] = []
    for workflow in ("bridge-7day-reliability.yml", "bridge-daily.yml",
                     "bridge-recover-publish.yml", "bridge-daily-fallback.yml",
                     "bridge-live-verify.yml"):
        url = (f"https://api.github.com/repos/{repo}/actions/workflows/"
               f"{workflow}/runs?per_page=100")
        request = urllib.request.Request(
            url, headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "User-Agent": "BRIDGE-ReliabilityMonitor/1.0",
                "X-GitHub-Api-Version": "2022-11-28",
            })
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
        for run in payload.get("workflow_runs", []):
            result.append({k: run.get(k) for k in
                          ("id", "name", "event", "status", "conclusion",
                           "head_branch", "created_at", "html_url")})
    return result


def current_checks(source_path: Path, origin: str, today: dt.date) -> dict:
    """Independently verify source, Cloudflare and authoritative DB read-only."""
    from tools.verify_live import verify
    from tools.verify_export_file import verify_file
    from tools.dry_run_public_export import ReadOnlyDB
    from bridge_pipeline.core import SupabaseRest

    source = json.loads(source_path.read_text(encoding="utf-8"))
    repository_date = source.get("asOfDate")
    report = {"repositoryDate": repository_date, "live": None,
              "database": None, "live_ok": False, "db_ok": False, "errors": []}
    try:
        live = verify(origin, str(source_path), today, 0)
        report["live"] = live
        report["live_ok"] = live.get("status") == "healthy"
        if not report["live_ok"]:
            report["errors"].append("LIVE_SNAPSHOT_NOT_HEALTHY")
    except Exception as exc:
        report["errors"].append("LIVE_CHECK_FAILED:" + type(exc).__name__)

    if repository_date != today.isoformat():
        report["errors"].append("REPOSITORY_NOT_CURRENT")
        return report
    try:
        report["database"] = verify_file(source_path, today, ReadOnlyDB(SupabaseRest()))
        report["db_ok"] = True
    except Exception as exc:
        report["errors"].append("DATABASE_LINEAGE_FAILED:" + type(exc).__name__)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="thefruitgrove/bridgebrand")
    parser.add_argument("--origin", default="https://bridgebrand.co.kr")
    parser.add_argument("--source", type=Path, default=ROOT / "site/data/latest.json")
    parser.add_argument("--output", type=Path, default=Path("bridge-reliability.json"))
    args = parser.parse_args()
    today = dt.datetime.now(KST).date()
    report: dict = {"checkedAt": dt.datetime.now(KST).isoformat(),
                    "observationDate": today.isoformat(), "readOnly": True,
                    "checks": {}, "scorecard": None, "errors": []}
    try:
        report["checks"] = current_checks(args.source, args.origin, today)
    except Exception as exc:
        report["errors"].append("CURRENT_CHECK_ERROR:" + type(exc).__name__)
    try:
        runs = github_runs(args.repo, os.environ.get("GH_TOKEN", ""))
    except Exception as exc:
        runs = []
        report["errors"].append("WORKFLOW_HISTORY_UNAVAILABLE:" + type(exc).__name__)
    try:
        from tools.bridge_stage_diagnostics import summarize_runs, inspect_failures
        report["stages"] = inspect_failures(
            args.repo, os.environ.get("GH_TOKEN", ""),
            summarize_runs(runs, today),
        )
    except Exception:
        # Never fabricate stage diagnoses; the existing full-snapshot health
        # report remains authoritative when workflow metadata is unavailable.
        report["stages"] = []
    try:
        from tools.bridge_schedule_slo import punctuality
        report["scheduleAudit"] = punctuality(
            runs, dt.datetime.now(KST),
        )
    except Exception:
        report["scheduleAudit"] = {"scheduleRisk": None, "jobs": [], "status": "unavailable"}
        report.setdefault("warnings", []).append("SCHEDULE_AUDIT_UNAVAILABLE")
    try:
        from tools.bridge_source_metrics import collect_source_summary
        from bridge_pipeline.core import SupabaseRest
        report["sourceMetrics"] = collect_source_summary(SupabaseRest(), today, window_days=30)
    except Exception:
        # This optional telemetry must not turn a verified 400-row production
        # publication into a false "outage". Surface a warning instead.
        report["sourceMetrics"] = {"metricsAvailable": False, "sources": [], "status": "unavailable"}
        report.setdefault("warnings", []).append("SOURCE_METRICS_UNAVAILABLE")
    checks = report["checks"]
    report["scorecard"] = scorecard(
        today, live_ok=bool(checks.get("live_ok")),
        db_ok=bool(checks.get("db_ok")),
        repository_date=checks.get("repositoryDate"), runs=runs,
    )
    if report["errors"]:
        report["scorecard"]["status"] = "failure"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    status = report["scorecard"]["status"]
    print(json.dumps({
        "date": today.isoformat(), "status": status,
        "sourceDate": checks.get("repositoryDate"),
        "liveOk": checks.get("live_ok"), "databaseOk": checks.get("db_ok"),
        "observedDays": report["scorecard"]["observed_days"],
        "deliveredDays": report["scorecard"]["delivered_days"],
        "cleanDays": report["scorecard"]["clean_days"],
        "sevenDayDelivery": report["scorecard"].get("seven_day_delivery", False),
        "sevenDayClean": report["scorecard"]["seven_day_clean"],
        "errors": report["errors"] + checks.get("errors", []),
        "warnings": report.get("warnings", []),
    }, ensure_ascii=False, flush=True))
    # A recovered/degraded day is a delivery success, but not a clean day.
    return 0 if status in {"healthy", "degraded"} and not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
