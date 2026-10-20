"""CPR-specific relationship evidence layered on the common BRIDGE model.

This layer improves corporate evidence meaning without changing common axis
weights, eligibility thresholds, or the public scoring formula. Headline-only
matches remain conservative candidates; performance and publicity are not
treated as reputation by themselves.
"""
from __future__ import annotations
from typing import Iterable

POLICY_VERSION = "cpr-rel-2026.10-1"

RELATIONSHIP_POSITIVE = {
    "고객 신뢰": "consumer_trust", "소비자 신뢰": "consumer_trust",
    "고객 만족": "consumer_satisfaction", "만족도 상승": "consumer_satisfaction",
    "상생": "partner_mutuality", "동반성장": "partner_mutuality",
    "의견 반영": "responsiveness", "고객 의견": "responsiveness",
    "노사 합의": "employee_commitment", "협력사 지원": "partner_commitment",
}
RELATIONSHIP_NEGATIVE = {
    "고객 불만": "consumer_dissatisfaction", "소비자 불만": "consumer_dissatisfaction",
    "불신": "distrust", "불매": "relationship_exit", "해지": "relationship_exit",
    "거래 중단": "partner_exit", "노사 갈등": "employee_strain",
    "협력사 갈등": "partner_strain", "갑질": "fairness_breach",
}
IDENTITY = {
    "기업 비전": "official_promise", "핵심가치": "official_promise",
    "고객 중심": "customer_orientation", "안전 최우선": "safety_promise",
    "브랜드 정체성": "corporate_identity", "기업 정체성": "corporate_identity",
    "이미지 쇄신": "identity_reframing", "브랜드 이미지": "public_association",
}
ACTION = {
    "재구매": "repurchase", "추천": "recommendation", "구독": "subscription",
    "회원 탈퇴": "exit", "환불": "refund", "불매": "boycott",
    "집단 민원": "collective_complaint", "소송": "dispute",
    "거래 중단": "partner_exit", "채용 지원": "employment_interest",
}
CAPABILITY = {
    "품질 개선": "quality_delivery", "품질 인증": "quality_verification",
    "서비스 개선": "service_delivery", "고객지원 강화": "customer_support",
    "장애 복구": "service_recovery", "공급 정상화": "supply_recovery",
    "보안 강화": "security_delivery", "개인정보 보호": "privacy_delivery",
    "혁신 기술 상용화": "innovation_delivery", "출시 완료": "implementation",
}
LIFECYCLE = {
    "공식 확인": "acknowledged", "사과": "acknowledged", "해명": "explained",
    "조사 착수": "investigating", "리콜": "corrective_action",
    "보상안": "compensation_planned", "보상 완료": "compensated",
    "시정": "corrected", "개선 조치": "implemented", "이행 완료": "implemented",
    "재발 방지": "prevention", "정상화": "recovered",
    "재발": "recurred", "반복 적발": "recurred", "미이행": "unresolved",
}
RESPONSIBILITY = {
    "환경정보 공개": "environmental_disclosure",
    "인권경영": "human_rights", "공정거래": "fair_trade",
    "소비자 보호": "consumer_protection", "준법경영": "compliance",
    "윤리경영": "ethics", "투명경영": "transparency",
    "사회공헌": "social_contribution", "지역사회 협력": "community_partnership",
}
DISCOVERY = {
    "입소문": "organic_discovery", "외신 주목": "cross_market_discovery",
    "독립 평가": "independent_evaluation", "소비자 조사": "stakeholder_observation",
}


def _matches(title: str, vocabulary: dict[str, str]) -> list[tuple[str, str]]:
    folded = title.casefold()
    return [(term, concept) for term, concept in vocabulary.items() if term.casefold() in folded]


def classify_cpr_evidence(title: str) -> list[dict]:
    rows: list[dict] = []
    for term, concept in _matches(title, RELATIONSHIP_POSITIVE):
        rows.append({"axis": "R", "type": f"cpr_relation_{concept}", "direction": 1,
                     "magnitude": 10.0, "confidence": .56, "term": term, "review_status": "auto"})
    for term, concept in _matches(title, RELATIONSHIP_NEGATIVE):
        rows.append({"axis": "R", "type": f"cpr_relation_{concept}", "direction": -1,
                     "magnitude": 12.0, "confidence": .52, "term": term, "review_status": "pending"})
    for term, concept in _matches(title, IDENTITY):
        rows.append({"axis": "I", "type": f"cpr_identity_{concept}", "direction": 0,
                     "magnitude": 8.0, "confidence": .48, "term": term, "review_status": "auto"})
    for term, concept in _matches(title, ACTION):
        direction = -1 if concept in {"exit", "refund", "boycott", "collective_complaint", "dispute", "partner_exit"} else 0
        rows.append({"axis": "D", "type": f"cpr_action_{concept}", "direction": direction,
                     "magnitude": 9.0, "confidence": .50, "term": term,
                     "review_status": "pending" if direction < 0 else "auto"})
    for term, concept in _matches(title, CAPABILITY):
        rows.append({"axis": "G", "type": f"cpr_capability_{concept}", "direction": 1,
                     "magnitude": 8.0, "confidence": .52, "term": term, "review_status": "auto"})
    for term, stage in _matches(title, LIFECYCLE):
        direction = -1 if stage in {"recurred", "unresolved"} else 1
        rows.append({"axis": "E", "type": f"cpr_lifecycle_{stage}", "direction": direction,
                     "magnitude": 12.0, "confidence": .54, "term": term,
                     "review_status": "pending" if direction < 0 else "auto"})
    for term, concept in _matches(title, RESPONSIBILITY):
        rows.append({"axis": "E", "type": f"cpr_responsibility_{concept}", "direction": 0,
                     "magnitude": 8.0, "confidence": .48, "term": term, "review_status": "auto"})
    for term, concept in _matches(title, DISCOVERY):
        rows.append({"axis": "B", "type": f"cpr_discovery_{concept}", "direction": 1,
                     "magnitude": 1.0, "confidence": .54, "term": term, "review_status": "auto"})
    unique = {}
    for row in rows:
        unique.setdefault((row["axis"], row["type"]), row)
    return list(unique.values())


def diagnostics(signals: Iterable[dict]) -> dict:
    types = [str(row.get("signal_type") or "") for row in signals]
    enriched = [value for value in types if value.startswith("cpr_")]

    def concepts(prefix: str) -> list[str]:
        return sorted({value.removeprefix(prefix) for value in enriched if value.startswith(prefix)})

    return {
        "policy_version": POLICY_VERSION,
        "relationship_concepts": concepts("cpr_relation_"),
        "identity_concepts": concepts("cpr_identity_"),
        "action_paths": concepts("cpr_action_"),
        "capability_contexts": concepts("cpr_capability_"),
        "lifecycle_stages": concepts("cpr_lifecycle_"),
        "responsibility_concepts": concepts("cpr_responsibility_"),
        "discovery_contexts": concepts("cpr_discovery_"),
        "enriched_evidence_count": len(enriched),
        "interpretation_boundary": "performance_publicity_and_reputation_are_separate",
        "attribution_boundary": "corporate_product_subsidiary_and_ceo_require_distinct_attribution",
    }
