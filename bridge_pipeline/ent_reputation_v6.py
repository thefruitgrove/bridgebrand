"""ENT-specific relationship evidence layered on the common BRIDGE model.

The layer improves evidence meaning and public-safe diagnostics. It does not
change common axis weights, eligibility thresholds, or the scoring formula.
"""
from __future__ import annotations
from typing import Iterable

POLICY_VERSION = "ent-rel-2026.10-1"

RELATIONSHIP_POSITIVE = {
    "직접 소통": "direct_communication", "팬 소통": "fan_communication",
    "팬미팅": "fan_contact", "팬사인회": "fan_contact",
    "질문에 답": "response", "의견에 답": "response",
    "교감": "mutuality", "관계 회복": "relationship_recovery",
}
RELATIONSHIP_NEGATIVE = {
    "소통 논란": "communication_strain", "팬 기만": "trust_breach",
    "팬 차별": "relationship_strain", "팬과 갈등": "relationship_strain",
    "팬 이탈": "relationship_exit",
}
IDENTITY = {
    "공식 콘셉트": "official_concept", "새 콘셉트": "official_concept",
    "정체성": "identity", "팬덤명": "fandom_symbol",
    "공식 색상": "fandom_symbol", "공식색": "fandom_symbol",
    "응원봉": "fandom_symbol", "공식 로고": "fandom_symbol",
    "브랜드 이미지": "public_association",
}
ACTION = {
    "예매": "ticketing", "매진": "ticketing", "관람": "attendance",
    "시청": "viewing", "스트리밍": "streaming", "구독": "subscription",
    "투표": "voting", "음반 구매": "purchase", "앨범 구매": "purchase",
    "팬 프로젝트": "fan_project", "팬 기부": "fan_contribution",
}
LIFECYCLE = {
    "공식 확인": "acknowledged", "사과": "acknowledged", "해명": "explained",
    "입장문": "explained", "조사 착수": "investigating", "활동 중단": "paused",
    "개선": "implemented", "시정": "corrected", "복귀": "recovered",
    "관계 회복": "recovered", "재발 방지": "implemented",
    "재발": "recurred", "반복 논란": "recurred", "미이행": "unresolved",
}
RESPONSIBILITY = {
    "기부": "donation", "봉사활동": "volunteering",
    "자선활동": "charity", "사회공헌": "social_contribution",
}
CRAFT = {
    "연기 호평": "actor_performance", "캐릭터 소화": "actor_performance",
    "라이브 호평": "music_performance", "무대 호평": "music_performance",
    "퍼포먼스 호평": "music_performance", "경기력 호평": "sports_performance",
    "플레이 호평": "sports_performance", "진행 호평": "broadcast_performance",
    "콘텐츠 전문성": "creator_expertise",
}
PUBLIC_EXPANSION = {
    "대중적 관심": "general_public_reach", "해외 화제": "cross_market_reach",
    "글로벌 화제": "cross_market_reach", "역주행": "renewed_discovery",
    "입소문": "organic_discovery",
}


def _matches(title: str, vocabulary: dict[str, str]) -> list[tuple[str, str]]:
    folded = title.casefold()
    return [(term, concept) for term, concept in vocabulary.items() if term.casefold() in folded]


def classify_ent_evidence(title: str) -> list[dict]:
    rows: list[dict] = []
    for term, concept in _matches(title, RELATIONSHIP_POSITIVE):
        rows.append({"axis": "R", "type": f"ent_relation_{concept}", "direction": 1,
                     "magnitude": 10.0, "confidence": .55, "term": term, "review_status": "auto"})
    for term, concept in _matches(title, RELATIONSHIP_NEGATIVE):
        rows.append({"axis": "R", "type": f"ent_relation_{concept}", "direction": -1,
                     "magnitude": 12.0, "confidence": .52, "term": term, "review_status": "pending"})
    for term, concept in _matches(title, IDENTITY):
        rows.append({"axis": "I", "type": f"ent_identity_{concept}", "direction": 0,
                     "magnitude": 8.0, "confidence": .48, "term": term, "review_status": "auto"})
    for term, concept in _matches(title, ACTION):
        rows.append({"axis": "D", "type": f"ent_action_{concept}", "direction": 0,
                     "magnitude": 9.0, "confidence": .52, "term": term, "review_status": "auto"})
    for term, stage in _matches(title, LIFECYCLE):
        direction = -1 if stage in {"recurred", "unresolved"} else 1
        rows.append({"axis": "E", "type": f"ent_lifecycle_{stage}", "direction": direction,
                     "magnitude": 12.0, "confidence": .54, "term": term,
                     "review_status": "pending" if direction < 0 else "auto"})
    for term, concept in _matches(title, RESPONSIBILITY):
        rows.append({"axis": "E", "type": f"ent_responsibility_{concept}", "direction": 1,
                     "magnitude": 10.0, "confidence": .56, "term": term, "review_status": "auto"})
    for term, concept in _matches(title, CRAFT):
        rows.append({"axis": "G", "type": f"ent_craft_{concept}", "direction": 1,
                     "magnitude": 8.0, "confidence": .50, "term": term, "review_status": "auto"})
    for term, concept in _matches(title, PUBLIC_EXPANSION):
        rows.append({"axis": "B", "type": f"ent_discovery_{concept}", "direction": 1,
                     "magnitude": 1.0, "confidence": .55, "term": term, "review_status": "auto"})
    unique = {}
    for row in rows:
        unique.setdefault((row["axis"], row["type"]), row)
    return list(unique.values())


def diagnostics(signals: Iterable[dict]) -> dict:
    types = [str(row.get("signal_type") or "") for row in signals]
    enriched = [value for value in types if value.startswith("ent_")]
    def concepts(prefix: str) -> list[str]:
        return sorted({value.removeprefix(prefix) for value in enriched if value.startswith(prefix)})
    return {
        "policy_version": POLICY_VERSION,
        "relationship_concepts": concepts("ent_relation_"),
        "identity_concepts": concepts("ent_identity_"),
        "action_paths": concepts("ent_action_"),
        "lifecycle_stages": concepts("ent_lifecycle_"),
        "responsibility_concepts": concepts("ent_responsibility_"),
        "craft_contexts": concepts("ent_craft_"),
        "discovery_contexts": concepts("ent_discovery_"),
        "enriched_evidence_count": len(enriched),
        "interpretation_boundary": "popularity_activity_and_reputation_are_separate",
    }
