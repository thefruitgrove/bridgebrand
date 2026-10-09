from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable

from .targets import load_targets


GRADE_SCORE = {"가": 100.0, "나": 80.0, "다": 60.0, "라": 40.0, "마": 20.0}


def number(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", "").replace("%", "")
    if not text or text.lower() in {"na", "n/a", "null", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def percentile(values: list[float], value: float, higher_is_better: bool = True) -> float:
    """Mid-rank percentile with 5/95% winsorization for stable small cohorts."""
    clean = sorted(v for v in values if v is not None and math.isfinite(v))
    if not clean:
        return 50.0
    lo = clean[max(0, math.floor((len(clean) - 1) * 0.05))]
    hi = clean[min(len(clean) - 1, math.ceil((len(clean) - 1) * 0.95))]
    clipped = min(hi, max(lo, value))
    below = sum(v < clipped for v in clean)
    equal = sum(v == clipped for v in clean)
    pct = 100.0 * (below + 0.5 * equal) / len(clean)
    return round(pct if higher_is_better else 100.0 - pct, 2)


def mean_present(values: Iterable[float | None]) -> float | None:
    present = [float(v) for v in values if v is not None]
    return round(sum(present) / len(present), 2) if present else None


def coverage(values: Iterable[float | None]) -> float:
    values = list(values)
    return round(sum(value is not None for value in values) / len(values), 2) if values else 0.0


def _cohort(rows, keys):
    groups = {}
    for row in rows:
        key = tuple((row.get(k) or "미분류").strip() for k in keys)
        groups.setdefault(key, []).append(row)
    return groups


def _pct(groups, row, field, higher=True, cohort_keys=("school_type", "region_group")):
    key = tuple((row.get(k) or "미분류").strip() for k in cohort_keys)
    value = number(row.get(field))
    if value is None:
        return None
    values = [number(r.get(field)) for r in groups.get(key, [])]
    return percentile([v for v in values if v is not None], value, higher)


def normalize_uni(rows: list[dict]) -> list[dict]:
    groups = _cohort(rows, ("school_type", "region_group"))
    output = []
    for row in rows:
        competition = number(row.get("competition_rate"))
        fill = number(row.get("freshman_fill_rate"))
        international = number(row.get("international_student_rate"))
        b_parts = [
            _pct(groups, row, "competition_rate"),
            _pct(groups, row, "freshman_fill_rate"),
            _pct(groups, row, "international_student_rate"),
        ]
        i_parts = [
            _pct(groups, row, "program_distinctiveness"),
            _pct(groups, row, "specialization_concentration"),
        ]
        d_parts = [
            _pct(groups, row, "retention_rate"),
            _pct(groups, row, "dropout_rate", False),
            _pct(groups, row, "scholarship_per_student"),
            _pct(groups, row, "education_spend_per_student"),
            _pct(groups, row, "dorm_capacity_rate"),
            _pct(groups, row, "faculty_capacity_rate"),
            _pct(groups, row, "library_resources_per_student"),
        ]
        g_parts = [
            _pct(groups, row, "employment_rate"),
            _pct(groups, row, "research_per_faculty"),
            _pct(groups, row, "industry_revenue_per_student"),
            _pct(groups, row, "tech_transfer_income"),
        ]
        e_parts = [
            _pct(groups, row, "disclosure_completeness"),
            _pct(groups, row, "financial_stability"),
            _pct(groups, row, "education_condition_trend"),
        ]
        values = {"B": b_parts, "I": i_parts, "D": d_parts, "G": g_parts, "E": e_parts}
        for axis, parts in values.items():
            score = mean_present(parts)
            if score is not None:
                output.append(_official_row(row, axis, score, "academyinfo", coverage(parts), sum(value is not None for value in parts)))
    return output


def grade(value):
    return GRADE_SCORE.get(str(value or "").strip())


def normalize_gov(rows: list[dict]) -> list[dict]:
    output = []
    for row in rows:
        b = mean_present([grade(row.get("communication_grade")), number(row.get("owned_communication_score"))])
        i = mean_present([number(row.get("mandate_coherence")), grade(row.get("strategy_grade"))])
        d = mean_present([
            grade(row.get("overall_grade")), grade(row.get("strategy_grade")),
            grade(row.get("system_grade")), grade(row.get("epeople_grade")),
            grade(row.get("grievance_grade")), grade(row.get("satisfaction_grade")),
        ])
        g = mean_present([grade(row.get("performance_grade")), grade(row.get("innovation_grade"))])
        e = mean_present([grade(row.get("integrity_grade")), grade(row.get("disclosure_grade"))])
        for axis, score in {"B": b, "I": i, "D": d, "G": g, "E": e}.items():
            if score is not None:
                output.append(_official_row(row, axis, score, "gov_official_evaluations"))
    return output


def _official_row(row, axis, score, source_id, coverage_value=1.0, evidence_count=1):
    return {
        "external_id": row["external_id"], "axis": axis, "score": f"{score:.2f}",
        "confidence": "0.95", "coverage": f"{coverage_value:.2f}", "source_families": "1",
        "evidence_count": str(evidence_count), "freshness_days": row.get("freshness_days") or "0",
        "source_id": source_id, "evidence_url": row.get("evidence_url") or "",
        "note": row.get("note") or "official baseline"
    }


def attach_external_ids(rows: list[dict], domain: str) -> list[dict]:
    targets = [r for r in load_targets() if r["domain"] == domain]
    by_name = {r["name"].replace(" ", ""): r["external_id"] for r in targets}
    for target in targets:
        for alias in target.get("aliases") or []:
            by_name.setdefault(alias.replace(" ", ""), target["external_id"])
    attached = []
    for row in rows:
        external_id = (row.get("external_id") or "").strip()
        name = (row.get("institution") or row.get("name") or "").strip().replace(" ", "")
        if not external_id:
            external_id = by_name.get(name, "")
        if external_id:
            attached.append({**row, "external_id": external_id})
    return attached


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert official BRIDGE baseline data to the canonical axis CSV")
    parser.add_argument("--domain", required=True, choices=("UNI", "GOV"))
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        rows = attach_external_ids(list(csv.DictReader(handle)), args.domain)
    normalized = normalize_uni(rows) if args.domain == "UNI" else normalize_gov(rows)
    fields = ["external_id", "axis", "score", "confidence", "coverage", "source_families", "evidence_count", "freshness_days", "source_id", "evidence_url", "note"]
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(normalized)
    print(f"normalized {len(rows)} {args.domain} entities into {len(normalized)} axis observations")


if __name__ == "__main__":
    main()
