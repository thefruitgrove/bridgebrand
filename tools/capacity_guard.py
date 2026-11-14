"""Read-only BRIDGE file capacity / publication guard.

No database access, external API, writes, or data deletion. The historical
source archive is retained in Git and split only in Cloudflare Pages builds.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MIB = 1024 * 1024
WARN_FILE = 15 * MIB
FAIL_FILE = 20 * MIB
WARN_HISTORY = 100 * MIB
WARN_TOTAL = 250 * MIB
HISTORY_PATH = Path("site/data/history.json")


def assess(root: Path = ROOT, today: dt.date | None = None) -> dict:
    today = today or dt.datetime.now(ZoneInfo("Asia/Seoul")).date()
    site = root / "site"
    issues, warnings = [], []
    files = [(p, p.stat().st_size) for p in site.rglob("*") if p.is_file()]
    total_size = sum(n for _, n in files)
    if total_size >= WARN_TOTAL:
        warnings.append("static_source_total_above_250MiB")
    # The legacy history is intentionally over Cloudflare's limit in the
    # Git source; Cloudflare's build-time sharding is separately validated.
    oversize = [
        {"path": p.relative_to(root).as_posix(), "bytes": n}
        for p, n in files if p.relative_to(root) != HISTORY_PATH and n >= WARN_FILE
    ]
    for item in oversize:
        (issues if item["bytes"] >= FAIL_FILE else warnings).append(
            "large_deployment_asset:" + item["path"]
        )

    history = root / HISTORY_PATH
    history_stats = None
    if history.exists():
        size = history.stat().st_size
        if size >= WARN_HISTORY:
            warnings.append("history_archive_over_100MiB")
        try:
            archive = json.loads(history.read_text(encoding="utf-8"))
            if not isinstance(archive, dict) or not isinstance(archive.get("rankings"), list):
                issues.append("invalid_history_archive_schema")
            elif not (root / "tools/prepare_pages_assets.py").exists():
                issues.append("missing_pages_archive_sharding")
            else:
                items = archive["rankings"]
                # Simulate the production chunking algorithm without creating
                # large files or altering the source archive.
                batches, current, largest = 0, 2, 0
                for entry in items:
                    encoded = json.dumps(entry, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                    item_size = len(encoded) + 1
                    if item_size >= FAIL_FILE:
                        issues.append("individual_history_record_exceeds_limit")
                        break
                    if current > 2 and current + item_size > 5 * MIB:
                        batches += 1
                        largest = max(largest, current)
                        current = 2
                    current += item_size
                if current > 2:
                    batches += 1
                    largest = max(largest, current)
                history_stats = {"bytes": size, "records": len(items),
                                 "estimated_shards": batches, "max_estimated_shard_bytes": largest}
        except (OSError, ValueError, TypeError):
            issues.append("unreadable_history_archive")

    published = root / "site/data/latest.json"
    snapshot = {}
    try:
        snapshot = json.loads(published.read_text(encoding="utf-8"))
        day = dt.date.fromisoformat(snapshot.get("asOfDate"))
        if snapshot.get("dataStatus") != "published":
            issues.append("snapshot_not_published")
        if snapshot.get("recordCount") != 400 or len(snapshot.get("rankings", [])) != 400:
            issues.append("snapshot_incomplete")
        if day > today:
            issues.append("snapshot_from_future")
        elif (today - day).days > 2:
            warnings.append("repository_snapshot_older_than_2_days")
    except (OSError, ValueError, TypeError):
        issues.append("snapshot_unreadable")

    return {
        "status": "failure" if issues else ("warning" if warnings else "healthy"),
        "run_date_kst": today.isoformat(),
        "site_source_bytes": total_size,
        "site_file_count": len(files),
        "largest_deployable": sorted(oversize, key=lambda x: x["bytes"], reverse=True)[:10],
        "historical_archive": history_stats,
        "snapshot_date": snapshot.get("asOfDate"),
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = assess(args.root)
    result = json.dumps(report, ensure_ascii=False, indent=2)
    print(result)
    if args.out:
        args.out.write_text(result + "\n", encoding="utf-8")
    return 1 if report["status"] == "failure" else 0


if __name__ == "__main__":
    raise SystemExit(main())
