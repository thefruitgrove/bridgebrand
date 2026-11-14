"""BRIDGE live production read-only health gate.

A source commit may precede Cloudflare Pages deployment; do not fail an
otherwise healthy live site merely because GitHub has a newer revision.
No collection, writes, or deployment. Exit 1 only on confirmed health failure.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def classify(source, deployed, page, today, max_age_days=2):
    issues, warnings = [], []
    day = deployed.get("asOfDate")
    try:
        live_date = dt.date.fromisoformat(day)
    except (ValueError, TypeError):
        live_date = None
        issues.append("invalid_live_date")
    if deployed.get("dataStatus") != "published":
        issues.append("unpublished_live_snapshot")
    rows = deployed.get("rankings")
    if deployed.get("recordCount") != 400 or not isinstance(rows, list) or len(rows) != 400:
        issues.append("invalid_live_record_count")
    if live_date:
        age = (today - live_date).days
        if age > max_age_days:
            issues.append("stale_live_snapshot")
        elif age < 0:
            issues.append("future_dated_live_snapshot")
        elif age:
            warnings.append("live_snapshot_not_today")
        if f"{day} 기준" not in page:
            issues.append("this_week_date_mismatch")
        try:
            source_day = dt.date.fromisoformat(source.get("asOfDate"))
            if source_day > live_date:
                if age > max_age_days:
                    issues.append("deployment_lag_overdue")
                else:
                    warnings.append("deployment_lag_within_tolerance")
        except (ValueError, TypeError):
            warnings.append("invalid_repository_date")
    return {
        "status": "failure" if issues else ("warning" if warnings else "healthy"),
        "live_date": day, "repository_date": source.get("asOfDate"),
        "record_count": deployed.get("recordCount"),
        "issues": sorted(set(issues)), "warnings": sorted(set(warnings)),
    }


def fetch(origin, path):
    process = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--location",
         "--connect-timeout", "8", "--max-time", "20",
         "--header", "Cache-Control: no-cache", origin.rstrip("/") + "/" + path],
        capture_output=True, check=False,
    )
    if process.returncode:
        raise RuntimeError(f"{path}: curl exit {process.returncode}: " +
                           process.stderr.decode("utf-8", "replace")[:250])
    return process.stdout


def verify(origin, source_file, today, max_age_days):
    source = json.loads(Path(source_file).read_text(encoding="utf-8"))
    live = json.loads(fetch(origin, "data/latest.json"))
    page = fetch(origin, "this-week.html").decode("utf-8", "replace")
    report = classify(source, live, page, today, max_age_days)
    report["origin"] = origin
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="https://bridgebrand.co.kr")
    parser.add_argument("--source", default=str(ROOT / "site/data/latest.json"))
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--delay", type=int, default=30)
    parser.add_argument("--max-age-days", type=int, default=2)
    args = parser.parse_args()
    if args.attempts < 1 or args.delay < 0 or args.max_age_days < 0:
        parser.error("invalid attempts, delay or max-age-days")
    today = dt.datetime.now(ZoneInfo("Asia/Seoul")).date()
    report = None
    for attempt in range(args.attempts):
        try:
            report = verify(args.origin, args.source, today, args.max_age_days)
        except (OSError, RuntimeError, ValueError) as exc:
            report = {"status": "failure", "issues": ["site_fetch_or_parse_failed"],
                      "origin": args.origin, "error": str(exc)[:350]}
        report["attempt"] = attempt + 1
        print(json.dumps(report, ensure_ascii=False), flush=True)
        if report["status"] != "failure":
            break
        if attempt + 1 < args.attempts:
            time.sleep(args.delay)
    print("BRIDGE HEALTH:", report["status"], flush=True)
    return 1 if report["status"] == "failure" else 0


if __name__ == "__main__":
    sys.exit(main())
