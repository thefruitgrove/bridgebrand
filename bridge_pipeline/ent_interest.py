from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .baseline import percentile
from .targets import load_targets


ACTION_API = "https://ko.wikipedia.org/w/api.php"
FIELDS = ["external_id", "axis", "score", "confidence", "coverage", "source_families",
          "evidence_count", "freshness_days", "source_id", "evidence_url", "note"]
TITLE_OVERRIDES = {
    "박지훈": "박지훈 (가수)", "김도영": "김도영 (야구 선수)", "김재원": "김재원 (배우)",
    "비비": "비비 (가수)", "수지": "배수지", "아이들": "(여자)아이들", "엔시티": "NCT",
    "지드래곤": "G-DRAGON", "연준(투모로우바이투게더)": "연준", "성한빈(제로베이스원)": "성한빈",
    "리센느": "RESCENE",
}


def page_title(name: str) -> str:
    return TITLE_OVERRIDES.get(name, name)


def fetch_batch_views(titles: list[str], start: dt.date, end: dt.date) -> dict[str, list[int]]:
    """Fetch up to 10 titles (the production PageViewInfo lookup limit)."""
    params = urllib.parse.urlencode({
        "action": "query", "prop": "pageviews", "titles": "|".join(titles),
        "redirects": "1", "format": "json", "formatversion": "2",
    }).encode()
    request = urllib.request.Request(
        ACTION_API, data=params,
        headers={"User-Agent": "SignalBridgeBot/1.0 (contact: bridgebrand.co.kr)"},
    )
    payload = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code in {400, 404}:
                return {title: [] for title in titles}
            if exc.code != 429 or attempt == 4:
                raise
            retry_after = int(exc.headers.get("Retry-After") or 2 ** attempt)
            time.sleep(min(30, max(1, retry_after)))
        except urllib.error.URLError:
            if attempt == 4:
                return {title: [] for title in titles}
            time.sleep(2 ** attempt)
    if payload is None:
        return {title: [] for title in titles}
    query = payload.get("query") or {}
    aliases = {item["from"]: item["to"] for item in (query.get("normalized") or [])}
    aliases.update({item["from"]: item["to"] for item in (query.get("redirects") or [])})
    pages = {page.get("title"): page for page in (query.get("pages") or [])}
    result = {}
    for title in titles:
        resolved = aliases.get(title, title)
        resolved = aliases.get(resolved, resolved)
        pageviews = (pages.get(resolved) or {}).get("pageviews") or {}
        values = []
        for offset in range((end - start).days + 1):
            day = (start + dt.timedelta(days=offset)).isoformat()
            values.append(int(pageviews.get(day) or 0))
        result[title] = values if pageviews else []
    return result


def metrics(views: list[int]) -> dict:
    if len(views) < 14:
        return {"visibility": None, "momentum": None, "endurance": None}
    recent = views[-7:]
    previous = views[:-7]
    recent_mean = statistics.fmean(recent)
    previous_mean = statistics.fmean(previous) if previous else 0
    mean = statistics.fmean(views)
    std = statistics.pstdev(views)
    momentum = ((recent_mean / previous_mean) - 1) * 100 if previous_mean > 0 else None
    # 반복적으로 찾아보는 관심의 지속성. 윤리 점수가 아니라 E의 Endurance 성분만 측정한다.
    endurance = 100 / (1 + (std / mean)) if mean > 0 else None
    return {"visibility": math.log1p(mean), "momentum": momentum, "endurance": endurance}


def normalize(records: list[dict], as_of: dt.date) -> list[dict]:
    output = []
    specs = (("B", "visibility", True, "일평균 문서 열람량(로그)"),
             ("G", "momentum", True, "최근 7일 대 직전 21일 관심 모멘텀"),
             ("E", "endurance", True, "28일 열람 지속성; Ethics 제외 Endurance 한정"))
    for row in records:
        for axis, field, higher, note in specs:
            value = row.get(field)
            if value is None:
                continue
            population = [member[field] for member in records if member.get(field) is not None]
            score = percentile(population, value, higher)
            output.append({
                "external_id": row["external_id"], "axis": axis, "score": f"{score:.2f}",
                "confidence": "0.90", "coverage": f"{min(1, row['days'] / 28):.2f}",
                "source_families": "1", "evidence_count": str(row["days"]), "freshness_days": "0",
                "source_id": "wikimedia_pageviews",
                "evidence_url": f"https://ko.wikipedia.org/wiki/{urllib.parse.quote(row['title'].replace(' ', '_'))}",
                "note": f"{note}; T100 전체 내부 백분위; 평판 호감도와 동일시하지 않음",
            })
    return output


def collect(as_of: dt.date) -> tuple[list[dict], list[str]]:
    start = as_of - dt.timedelta(days=27)
    records, missing = [], []
    targets = [row for row in load_targets() if row["domain"] == "STAR"]
    for offset in range(0, len(targets), 10):
        batch = targets[offset:offset + 10]
        titles = [page_title(target["name"]) for target in batch]
        views_by_title = fetch_batch_views(titles, start, as_of)
        for target, title in zip(batch, titles):
            views = views_by_title.get(title) or []
            if len(views) < 14:
                missing.append(target["name"])
            else:
                records.append({"external_id": target["external_id"], "title": title, "days": len(views), **metrics(views)})
        time.sleep(1)
    return records, missing


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build ENT public-interest B/G/E axes from Wikimedia pageviews")
    parser.add_argument("--date")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    as_of = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    records, missing = collect(as_of)
    rows = normalize(records, as_of)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"ENT Wikimedia baseline: matched={len(records)} missing={len(missing)} axes={len(rows)}")
    if missing:
        print("missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
