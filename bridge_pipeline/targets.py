from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "real_data"))

TARGET_QUOTAS = {
    ("CPR", "BC70"): 70,
    ("CPR", "BB30"): 30,
    ("STAR", "AM40"): 40,
    ("STAR", "AW40"): 40,
    ("STAR", "AN20"): 20,
    ("GOV", "GM40"): 40,
    ("GOV", "GC60"): 60,
    ("UNI", "U60"): 60,
    ("UNI", "C40"): 40,
}

COHORT_CODES = {
    "B2C": "BC70",
    "B2B": "BB30",
    "AM": "AM40",
    "AW": "AW40",
    "AN": "AN20",
}

GOV_NAME_ALIASES = {
    "재정경제부": ["기획재정부"],
    "산업통상부": ["산업통상자원부"],
    "환경부": ["기후에너지환경부"],
    "여성가족부": ["성평등가족부"],
    "국가데이터처": ["통계청"],
    "검찰청": ["대검찰청"],
    "특허청": ["지식재산처"],
    "문화재청": ["국가유산청"],
}


def load_targets() -> list[dict]:
    from cpr_real import CPR_REAL
    from gov_real import GOV_C60, GOV_M40
    from star_real import STAR_REAL
    from uni_real import UNI_2YEAR, UNI_4YEAR

    rows: list[dict] = []
    for index, item in enumerate(CPR_REAL, 1):
        name, market, sector, *_rest = item
        subcat = COHORT_CODES.get(item[-1]) if item else None
        rows.append({"domain": "CPR", "external_id": f"CPR-{index:03d}", "name": name, "category": sector, "subcategory": subcat, "aliases": [], "metadata": {"market": market}, "active": True})
    for index, (name, level) in enumerate(GOV_M40, 1):
        rows.append({"domain": "GOV", "external_id": f"GOV-M{index:02d}", "name": name, "category": level, "subcategory": "GM40", "aliases": GOV_NAME_ALIASES.get(name, []), "metadata": {}, "active": True})
    for index, item in enumerate(GOV_C60, 1):
        name, owner, kind = item
        aliases = [f"{owner} {name}"] if kind == "기초지자체" else []
        rows.append({"domain": "GOV", "external_id": f"GOV-C{index:02d}", "name": name, "category": kind, "subcategory": "GC60", "aliases": aliases, "metadata": {"owner": owner}, "active": True})
    for index, (name, category, subcat) in enumerate(STAR_REAL, 1):
        rows.append({"domain": "STAR", "external_id": f"STAR-{index:03d}", "name": name, "category": category, "subcategory": COHORT_CODES.get(subcat, subcat), "aliases": [], "metadata": {}, "active": True})
    for index, (name, region, kind) in enumerate(UNI_4YEAR, 1):
        rows.append({"domain": "UNI", "external_id": f"UNI-U{index:02d}", "name": name, "category": kind, "subcategory": "U60", "aliases": [], "metadata": {"region": region}, "active": True})
    for index, (name, region) in enumerate(UNI_2YEAR, 1):
        rows.append({"domain": "UNI", "external_id": f"UNI-C{index:02d}", "name": name, "category": "전문대학", "subcategory": "C40", "aliases": [], "metadata": {"region": region}, "active": True})
    return rows


def target_quota_report(rows: list[dict] | None = None) -> list[dict]:
    rows = rows if rows is not None else load_targets()
    actual: dict[tuple[str, str], int] = {}
    for row in rows:
        if not row.get("active", True):
            continue
        key = (row["domain"], row.get("subcategory"))
        actual[key] = actual.get(key, 0) + 1
    return [
        {
            "domain": domain,
            "cohort_code": cohort,
            "expected_count": expected,
            "actual_count": actual.get((domain, cohort), 0),
            "exact_match": actual.get((domain, cohort), 0) == expected,
        }
        for (domain, cohort), expected in TARGET_QUOTAS.items()
    ]
