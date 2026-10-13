# -*- coding: utf-8 -*-
"""BRIDGE UNI v4.3 official baseline builder.

Official disclosures form a slow baseline. I/R/E remain N/R until their
own evidence layers provide observations.
"""
from __future__ import annotations
import argparse, json, os, re
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_XLSX = os.path.join(HERE, "대학주요정보.xlsx")
DEFAULT_OUT = os.path.join(HERE, "data", "uni_baseline_v43.json")

def norm(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace("[본교]", "").strip()

def stable_id(row: pd.Series) -> str:
    identity = "|".join(norm(row.get(k)) for k in ("학교명", "본분교명", "학교종류", "지역명"))
    return "UNI-" + sha256(identity.encode("utf-8")).hexdigest()[:12].upper()

def find_col(columns: list[str], *needles: str) -> str | None:
    candidates = [c for c in columns if all(norm(n) in norm(c) for n in needles)]
    return max(candidates, key=lambda c: max([int(x) for x in re.findall(r"20\d{2}", c)] or [0])) if candidates else None

def numeric(df: pd.DataFrame, col: str | None) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce") if col else pd.Series(float("nan"), index=df.index)

def percentile(series: pd.Series, reverse: bool = False) -> pd.Series:
    result = pd.to_numeric(series, errors="coerce").rank(method="average", pct=True) * 100
    return 100 - result if reverse else result

def weighted_row(parts: list[tuple[pd.Series, float]]) -> pd.Series:
    frame = pd.concat([s.rename(str(i)) for i, (s, _) in enumerate(parts)], axis=1)
    weights = pd.Series({str(i): w for i, (_, w) in enumerate(parts)})
    numerator = frame.mul(weights, axis=1).sum(axis=1, min_count=1)
    denominator = frame.notna().mul(weights, axis=1).sum(axis=1)
    return numerator.div(denominator.where(denominator > 0))

def source_year(col: str | None) -> int | None:
    years = re.findall(r"20\d{2}", col or "")
    return int(max(years)) if years else None

def build(xlsx: str) -> dict[str, Any]:
    df = pd.read_excel(xlsx)
    columns = [str(c) for c in df.columns]
    if "학교명" not in df or "학교종류" not in df:
        raise ValueError("대학알리미 원자료에 학교명 또는 학교종류 열이 없습니다.")
    df = df[df["학교종류"].isin(["대학", "전문대학"])].copy()
    cmap = {
        "재학생": find_col(columns, "재학생"), "경쟁률": find_col(columns, "신입생", "경쟁률"),
        "충원율": find_col(columns, "신입생", "충원율"), "취업률": find_col(columns, "취업률"),
        "외국인": find_col(columns, "외국인", "학생"), "교원당학생": find_col(columns, "전임교원1인당학생수"),
        "교원강의": find_col(columns, "전임교원강의담당비율"), "장학금": find_col(columns, "학생1인당연간장학금"),
        "교육비": find_col(columns, "학생1인당교육비"), "기숙사": find_col(columns, "기숙사수용률"),
    }
    missing = [k for k in ("재학생", "경쟁률", "충원율", "취업률") if not cmap[k]]
    if missing:
        raise ValueError("필수 열을 찾지 못했습니다: " + ", ".join(missing))
    for key, col in cmap.items(): df[key] = numeric(df, col)
    df["외국인비율"] = df["외국인"] / df["재학생"].replace(0, float("nan")) * 100
    df["university_id"] = df.apply(stable_id, axis=1)

    outputs = []
    for kind, group in df.groupby("학교종류", sort=False):
        g = group.copy()
        g["B"] = weighted_row([(percentile(g["경쟁률"]), .45), (percentile(g["충원율"]), .35), (percentile(g["외국인비율"]), .20)])
        g["D"] = weighted_row([(percentile(g["교육비"]), .30), (percentile(g["장학금"]), .25),
                                (percentile(g["기숙사"]), .20), (percentile(g["교원당학생"], True), .15),
                                (percentile(g["교원강의"]), .10)])
        g["G"] = percentile(g["취업률"])
        for _, row in g.iterrows():
            dims0 = {"B": row["B"], "R": None, "I": None, "D": row["D"], "G": row["G"], "E": None}
            dims = {k: None if pd.isna(v) else round(float(v), 1) for k, v in dims0.items()}
            raw_keys = ("경쟁률", "충원율", "외국인비율", "교육비", "장학금", "기숙사", "교원당학생", "교원강의", "취업률")
            raw = {k: None if pd.isna(row.get(k)) else round(float(row.get(k)), 4) for k in raw_keys}
            count = sum(v is not None for v in dims.values())
            outputs.append({
                "university_id": row["university_id"], "name": str(row["학교명"]),
                "campus": str(row.get("본분교명") or ""), "school_kind": kind,
                "school_type": str(row.get("학교유형") or ""), "establishment": str(row.get("설립유형") or ""),
                "region": str(row.get("지역명") or ""), "dims": dims, "raw": raw,
                "eligible": count >= 3, "official_axis_count": count, "trust": "B" if count >= 3 else "C",
            })
    stat = os.stat(xlsx)
    with open(xlsx, "rb") as f: file_hash = sha256(f.read()).hexdigest()
    return {
        "schema_version": "UNI-4.3", "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {"provider": "대학알리미", "source_file": os.path.basename(xlsx), "sha256": file_hash,
                   "source_years": {k: source_year(v) for k, v in cmap.items()},
                   "retrieved_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()},
        "operational_notes": {"R": "공중 반응 관측 시에만 산출", "I": "자기 제시·특성화·외부 연상 결합 시 산출",
                              "E": "공시 충실도·시정·인증·재정지속 결합 시 산출"},
        "universities": outputs,
    }

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--xlsx", default=DEFAULT_XLSX); p.add_argument("--out", default=DEFAULT_OUT)
    a = p.parse_args(); result = build(a.xlsx); os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f: json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"UNI v4.3 official baseline: {sum(r['eligible'] for r in result['universities'])}/{len(result['universities'])} eligible → {a.out}")

if __name__ == "__main__": main()

