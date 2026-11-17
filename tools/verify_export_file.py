"""Final zero-write DB-to-JSON gate before a daily release is committed.

Checks actual published scores/ranks/trust against authoritative Postgres rows.
A partial or stale snapshot is a hard failure, never a successful publication.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from bridge_pipeline.core import SupabaseRest
from tools.dry_run_public_export import ReadOnlyDB, validate


def verify_file(path: Path, as_of: dt.date, db: ReadOnlyDB) -> dict:
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("dataStatus") != "published":
        raise RuntimeError("Public JSON not marked published")
    if snapshot.get("asOfDate") != as_of.isoformat():
        raise RuntimeError("Public JSON date differs from actual observation date")
    report = validate(snapshot, db, as_of)
    if report["row_count"] != 400 or report["diff_count"] != 0:
        raise RuntimeError("Public JSON lacks exactly 400 matched subjects")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Actual KST observation date YYYY-MM-DD")
    parser.add_argument("--file", type=Path, default=Path("site/data/latest.json"))
    args = parser.parse_args()
    as_of = dt.date.fromisoformat(args.date)
    if as_of > dt.datetime.now(ZoneInfo("Asia/Seoul")).date():
        parser.error("Future observation date is forbidden")
    report = verify_file(args.file, as_of, ReadOnlyDB(SupabaseRest()))
    print("PASS authoritative daily export: " + json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
