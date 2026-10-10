from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
AXES = ("B", "R", "I", "D", "G", "E")
KST = ZoneInfo("Asia/Seoul")


def load_methodology() -> dict[str, Any]:
    return json.loads((ROOT / "automation" / "methodology.v1.json").read_text(encoding="utf-8"))


def now_kst() -> dt.datetime:
    return dt.datetime.now(tz=KST)


def publication_date(value: str | None = None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return now_kst().date()


def iso_week(value: dt.date) -> str:
    year, week, _ = value.isocalendar()
    return f"{year}-W{week:02d}"


def stable_hash(*parts: object) -> str:
    normalized = "\x1f".join(str(p or "").strip() for p in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def canonical_url(url: str) -> str:
    if not url:
        return ""
    p = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith("utm_")]
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), urllib.parse.urlencode(query), ""))


@dataclass(frozen=True)
class RawItem:
    source_id: str
    source_item_id: str
    title: str
    canonical_url: str
    publisher: str | None
    published_at: str | None
    payload: dict[str, Any]
    content_hash: str


@dataclass(frozen=True)
class Signal:
    external_id: str
    axis: str
    signal_type: str
    direction: int
    magnitude: float
    confidence: float
    occurred_at: str
    review_status: str
    rationale: str
    raw_content_hash: str


class SupabaseRest:
    """Small PostgREST client; Supabase secret credentials remain in CI secrets."""

    def __init__(self, url: str | None = None, key: str | None = None):
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.key = key or os.environ.get("SUPABASE_SECRET_KEY", "") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.url or not self.key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY are required")

    def request(self, method: str, table: str, data: Any = None, query: str = "", prefer: str = "return=representation") -> Any:
        endpoint = f"{self.url}/rest/v1/{table}"
        if query:
            endpoint += "?" + query
        body = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(endpoint, data=body, method=method)
        req.add_header("apikey", self.key)
        # New sb_secret_ keys are supplied only through apikey. Legacy JWT
        # service-role keys still require the Authorization header.
        if not self.key.startswith("sb_secret_"):
            req.add_header("Authorization", f"Bearer {self.key}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Prefer", prefer)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"Supabase {method} {table} failed ({exc.code}): {detail}") from exc

    def upsert(self, table: str, rows: list[dict[str, Any]], conflict: str) -> Any:
        if not rows:
            return []
        return self.request("POST", table, rows, f"on_conflict={urllib.parse.quote(conflict)}", "resolution=merge-duplicates,return=representation")

    def select(self, table: str, query: str) -> list[dict[str, Any]]:
        return self.request("GET", table, query=query) or []

    def insert(self, table: str, rows: list[dict[str, Any]]) -> Any:
        return self.request("POST", table, rows)

    def patch(self, table: str, values: dict[str, Any], query: str) -> Any:
        return self.request("PATCH", table, values, query)


def fetch_google_news(query: str, days: int = 1) -> list[RawItem]:
    q = f'{query} when:{days}d'
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
    req = urllib.request.Request(url, headers={"User-Agent": "SignalBridgeBot/1.0 (+https://bridgebrand.co.kr)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    items: list[RawItem] = []
    for node in root.findall(".//channel/item"):
        title = (node.findtext("title") or "").strip()
        link = canonical_url((node.findtext("link") or "").strip())
        guid = (node.findtext("guid") or link).strip()
        pub = (node.findtext("pubDate") or "").strip() or None
        source = node.find("source")
        publisher = source.text.strip() if source is not None and source.text else None
        content_hash = stable_hash(title.casefold(), link or guid)
        items.append(RawItem("google_news_rss", guid, title, link, publisher, pub, {"query": query}, content_hash))
    return items


NEGATIVE = {
    "논란": 2, "리콜": 3, "제재": 3, "횡령": 5, "불매": 3, "담합": 4,
    "과징금": 4, "결함": 3, "소송": 2, "비리": 5, "징계": 3, "사고": 4,
    "마약": 5, "음주운전": 5, "학폭": 4, "갑질": 4, "성추행": 5
}
POSITIVE = {
    "수상": 2, "선정": 2, "협약": 1, "신기록": 3, "최대실적": 3, "흑자": 3,
    "수주": 2, "신제품": 1, "출시": 1, "돌파": 2, "혁신": 2, "개선": 1
}
EXPERIENCE = {"서비스", "품질", "고객", "민원", "사용자", "안전", "지원"}
COMMERCIAL_RELEVANCE = {"광고", "광고모델", "전속모델", "브랜드", "앰배서더", "캠페인", "화보", "협찬", "CF"}
REPUTATION_RESPONSE = {"호평", "화제", "인기", "흥행", "완판", "선호", "팬덤", "반응", "찬사"}


def entity_match(title: str, name: str, aliases: Iterable[str] = ()) -> bool:
    compact = re.sub(r"\s+", "", title).casefold()
    return any(re.sub(r"\s+", "", candidate).casefold() in compact for candidate in (name, *aliases) if candidate)


def classify_headline(item: RawItem, external_id: str, name: str, aliases: Iterable[str] = (), ruleset: str = "2026.10-shadow-1") -> list[Signal]:
    if not entity_match(item.title, name, aliases):
        return []
    title = item.title
    occurred = item.published_at or now_kst().isoformat()
    signals: list[Signal] = []
    neg = sum(weight for word, weight in NEGATIVE.items() if word in title)
    pos = sum(weight for word, weight in POSITIVE.items() if word in title)
    if neg:
        signals.append(Signal(external_id, "R", "adverse_mention", -1, min(100.0, neg * 8.0), 0.55, occurred, "pending", "부정 키워드 탐지이며 사실관계와 귀속은 검토 전", item.content_hash))
    if pos:
        signals.append(Signal(external_id, "G", "verified_action_candidate", 1, min(100.0, pos * 7.0), 0.60, occurred, "auto", "성과·행동 키워드가 포함된 공개 보도", item.content_hash))
    if any(word in title for word in COMMERCIAL_RELEVANCE):
        signals.append(Signal(external_id, "I", "commercial_relevance", 1, 14.0, 0.65, occurred, "auto", "광고·브랜드 적합성 맥락의 공개 보도", item.content_hash))
    if any(word in title for word in REPUTATION_RESPONSE):
        signals.append(Signal(external_id, "R", "positive_public_response", 1, 12.0, 0.55, occurred, "auto", "대중 반응을 명시한 공개 보도", item.content_hash))
    if any(word in title for word in EXPERIENCE):
        signals.append(Signal(external_id, "D", "experience_mention", 0, 12.0, 0.45, occurred, "auto", "경험 관련 공개 보도 포착", item.content_hash))
    signals.append(Signal(external_id, "B", "qualified_visibility", 1, 1.0, 0.70, occurred, "auto", "정확한 대상명과 일치한 고유 기사", item.content_hash))
    return signals


def weighted_score(axis_scores: dict[str, float | None], confidences: dict[str, float], config: dict[str, Any]) -> tuple[float | None, float, list[str]]:
    present = {axis: float(score) for axis, score in axis_scores.items() if axis in AXES and score is not None}
    if len(present) < config["minimum_publishable_axes"]:
        return None, 0.0, sorted(present)
    weights = config["axis_weights"]
    denominator = sum(weights[a] for a in present)
    score = sum(present[a] * weights[a] for a in present) / denominator
    confidence = sum(confidences.get(a, 0.0) * weights[a] for a in present) / denominator * 100
    return round(score, 2), round(confidence, 2), sorted(present)


def trust_grade(confidence_score: float, config: dict[str, Any]) -> str:
    for grade in ("A", "B", "C", "D"):
        if confidence_score >= config["trust_thresholds"][grade]:
            return grade
    return "N/R"


def robust_rank(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic rank: score, confidence, entity id. Ties receive competition rank."""
    ordered = sorted(rows, key=lambda x: (-float(x["score"]), -float(x["confidence_score"]), x["external_id"]))
    last_key = None
    rank = 0
    for position, row in enumerate(ordered, 1):
        key = (round(float(row["score"]), 2), round(float(row["confidence_score"]), 2))
        if key != last_key:
            rank = position
            last_key = key
        row["rank"] = rank
    return ordered


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
