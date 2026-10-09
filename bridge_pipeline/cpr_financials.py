from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .baseline import coverage, mean_present, percentile
from .targets import load_targets


API_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
ACCOUNT_ALIASES = {
    "revenue": ("매출액", "영업수익", "수익(매출액)", "매출"),
    "operating_income": ("영업이익", "영업이익(손실)"),
    "net_income": ("당기순이익", "당기순이익(손실)", "연결당기순이익"),
    "assets": ("자산총계",),
    "liabilities": ("부채총계",),
    "equity": ("자본총계",),
}
FIELDS = ["external_id", "axis", "score", "confidence", "coverage", "source_families",
          "evidence_count", "freshness_days", "source_id", "evidence_url", "note"]


def _number(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _safe_ratio(numerator, denominator, scale=1.0):
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator * scale


def fetch_accounts(corp_code: str, year: int, api_key: str) -> list[dict]:
    params = {"crtfc_key": api_key, "corp_code": corp_code, "bsns_year": str(year), "reprt_code": "11011"}
    url = API_URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("status") == "013":
        return []
    if payload.get("status") != "000":
        raise RuntimeError(f"OpenDART {corp_code}: {payload.get('status')} {payload.get('message')}")
    return payload.get("list") or []


def extract_metrics(rows: list[dict]) -> dict:
    # 연결재무제표(CFS)를 우선하고, 없는 기업은 별도재무제표(OFS)를 쓴다.
    chosen = [row for row in rows if row.get("fs_div") == "CFS"] or [row for row in rows if row.get("fs_div") == "OFS"]
    values = {}
    for key, aliases in ACCOUNT_ALIASES.items():
        match = next((row for row in chosen if (row.get("account_nm") or "").strip() in aliases), None)
        if match:
            values[key] = _number(match.get("thstrm_amount"))
            values[key + "_prior"] = _number(match.get("frmtrm_amount"))
        else:
            values[key] = values[key + "_prior"] = None
    revenue = values["revenue"]
    return {
        "revenue_growth": _safe_ratio(revenue - values["revenue_prior"], abs(values["revenue_prior"]), 100)
            if revenue is not None and values["revenue_prior"] not in (None, 0) else None,
        "operating_margin": _safe_ratio(values["operating_income"], revenue, 100),
        "net_margin": _safe_ratio(values["net_income"], revenue, 100),
        "debt_ratio": _safe_ratio(values["liabilities"], values["equity"], 100),
        "equity_ratio": _safe_ratio(values["equity"], values["assets"], 100),
        "profitable": 1.0 if values["net_income"] is not None and values["net_income"] > 0 else (0.0 if values["net_income"] is not None else None),
    }


def normalize(records: list[dict], year: int) -> list[dict]:
    groups = {}
    for row in records:
        groups.setdefault(row["cohort"], []).append(row)

    def pct(row, field, higher=True):
        value = row.get(field)
        if value is None:
            return None
        values = [member.get(field) for member in groups[row["cohort"]] if member.get(field) is not None]
        return percentile(values, value, higher)

    output = []
    for row in records:
        g_parts = [pct(row, "revenue_growth"), pct(row, "operating_margin"), pct(row, "net_margin")]
        e_parts = [pct(row, "debt_ratio", False), pct(row, "equity_ratio"), pct(row, "profitable")]
        for axis, parts in (("G", g_parts), ("E", e_parts)):
            score = mean_present(parts)
            if score is None:
                continue
            count = sum(value is not None for value in parts)
            output.append({
                "external_id": row["external_id"], "axis": axis, "score": f"{score:.2f}",
                "confidence": "0.95", "coverage": f"{coverage(parts):.2f}", "source_families": "1",
                "evidence_count": str(count), "freshness_days": str(max(0, (dt.date.today() - dt.date(year + 1, 3, 31)).days)),
                "source_id": "opendart_financials",
                "evidence_url": "https://opendart.fss.or.kr/disclosureinfo/fnltt/singl/main.do",
                "note": f"{year} 사업연도 OpenDART 재무제표; {row['cohort']} 내부 백분위",
            })
    return output


def build_records(corp_map: dict[str, str], year: int, api_key: str) -> tuple[list[dict], list[str]]:
    targets = {row["name"]: row for row in load_targets() if row["domain"] == "CPR"}
    records, missing = [], []
    for index, (name, target) in enumerate(targets.items()):
        corp_code = corp_map.get(name)
        if not corp_code:
            missing.append(name)
            continue
        rows = fetch_accounts(corp_code, year, api_key)
        metrics = extract_metrics(rows)
        if not any(value is not None for value in metrics.values()):
            missing.append(name)
            continue
        records.append({"external_id": target["external_id"], "cohort": target["subcategory"], **metrics})
        if index and index % 20 == 0:
            time.sleep(0.3)
    return records, missing


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build CPR G/E official baseline from OpenDART annual statements")
    parser.add_argument("--map", default=str(Path(__file__).resolve().parents[1] / "collectors" / "corp_code_map.json"))
    parser.add_argument("--year", type=int, default=dt.date.today().year - 1)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    api_key = os.environ.get("DART_API_KEY", "")
    if not api_key:
        raise SystemExit("DART_API_KEY is required")
    corp_map = json.loads(Path(args.map).read_text(encoding="utf-8"))
    records, missing = build_records(corp_map, args.year, api_key)
    normalized = normalize(records, args.year)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(normalized)
    print(f"CPR OpenDART baseline: matched={len(records)} missing={len(missing)} axes={len(normalized)}")
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
