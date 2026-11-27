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
    if source.get("asOfDate") == day and source.get("dataStatus") == "published":
        source_id, live_id = source.get("snapshotId"), deployed.get("snapshotId")
        if source_id and live_id and source_id != live_id:
            issues.append("same_date_snapshot_id_mismatch")
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


# Published JSON uses ENT; STAR is the internal scoring domain only.
EXPECTED_DOMAINS = ("CPR", "ENT", "GOV", "UNI")


def content_integrity(source, deployed):
    """Check all 400 live record values, not merely date/count/snapshot ID."""
    problems = []
    records = deployed.get("rankings")
    if not isinstance(records, list) or len(records) != 400:
        return ["invalid_live_content_count"]

    for domain in EXPECTED_DOMAINS:
        members = [r for r in records if isinstance(r, dict) and r.get("domain") == domain]
        if len(members) != 100:
            problems.append("invalid_live_domain_quota:" + domain)
            continue
        ranks = [r.get("rank") for r in members]
        if not all(type(p) is int for p in ranks) or sorted(ranks) != list(range(1, 101)):
            problems.append("invalid_live_domain_ranks:" + domain)
        ids = [r.get("external_id") for r in members]
        if any(not isinstance(eid, str) or not eid for eid in ids) or len(set(ids)) != 100:
            problems.append("duplicate_or_missing_live_entities:" + domain)
        for row in members:
            if (type(row.get("score")) not in (int, float)
                or not isinstance(row.get("trust_grade"), str)
                or not row.get("trust_grade")
                or not isinstance(row.get("axis_scores"), dict)):
                problems.append("incomplete_live_ranking_fields:" + domain)
                break

    if any(not isinstance(row, dict) or row.get("domain") not in EXPECTED_DOMAINS for row in records):
        problems.append("unexpected_live_domain")

    if source.get("asOfDate") == deployed.get("asOfDate"):
        expected = source.get("rankings")
        if not isinstance(expected, list) or len(expected) != 400:
            problems.append("invalid_repository_content")
        else:
            import hashlib
            def fingerprint(rows):
                # Covers every published score, evidence date, axis state,
                # rank and trust grade; only row order is immaterial.
                ordered = sorted(rows, key=lambda r: (
                    str(r.get("domain")), str(r.get("external_id")), str(r.get("rank"))
                ))
                raw = json.dumps(ordered, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False).encode("utf-8")
                return hashlib.sha256(raw).hexdigest()
            try:
                if fingerprint(expected) != fingerprint(records):
                    problems.append("live_ranking_content_mismatch")
            except (ValueError, TypeError, AttributeError, OverflowError):
                problems.append("unreadable_live_ranking_content")
    return sorted(set(problems))


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
    content_issues = content_integrity(source, live)
    if content_issues:
        report["issues"] = sorted(set(report["issues"] + content_issues))
        report["status"] = "failure"
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
