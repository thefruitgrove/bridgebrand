from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .targets import load_targets


SOURCE_URL = "https://www.data.go.kr/data/15131141/fileData.do?recommendDataYn=Y"
OUTPUT_FIELDS = [
    "institution", "external_id", "org_type", "overall_grade", "strategy_grade",
    "system_grade", "epeople_grade", "grievance_grade", "satisfaction_grade",
    "performance_grade", "communication_grade", "innovation_grade", "integrity_grade",
    "disclosure_grade", "owned_communication_score", "mandate_coherence",
    "freshness_days", "evidence_url", "note",
]


def compact(value: str | None) -> str:
    return (value or "").replace(" ", "").strip()


def latest_gov_rows(rows: list[dict]) -> tuple[str, list[dict]]:
    years = [int((row.get("평가연도") or "0").rstrip("년")) for row in rows]
    latest = max(years)
    return str(latest), [row for row in rows if int((row.get("평가연도") or "0").rstrip("년")) == latest]


def convert(rows: list[dict]) -> tuple[list[dict], list[str]]:
    year, latest = latest_gov_rows(rows)
    by_name = {compact(row.get("기관명")): row for row in latest}
    output: list[dict] = []
    missing: list[str] = []
    for target in (row for row in load_targets() if row["domain"] == "GOV"):
        candidates = [target["name"], *(target.get("aliases") or [])]
        source = next((by_name[compact(name)] for name in candidates if compact(name) in by_name), None)
        if source is None:
            missing.append(target["name"])
            continue
        output.append({
            "institution": source["기관명"],
            "external_id": target["external_id"],
            "org_type": source["기관유형"],
            "overall_grade": source["종합등급"],
            "strategy_grade": source["민원행정 전략 및 체계"],
            "system_grade": source["민원제도운영"],
            "epeople_grade": source["국민신문고민원 처리"],
            "grievance_grade": source["고충민원 처리"],
            "satisfaction_grade": source["민원만족도"],
            "freshness_days": "0",
            "evidence_url": SOURCE_URL,
            "note": f"{year} 국민신문고 민원서비스 종합평가",
        })
    return output, missing


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert the official civil-service evaluation CSV to BRIDGE GOV input")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        converted, missing = convert(list(csv.DictReader(handle)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(converted)
    print(f"matched {len(converted)}/100 GOV targets; missing={','.join(missing) or '-'}")


if __name__ == "__main__":
    main()
