from __future__ import annotations

import datetime as dt
import re
from typing import Any, Iterable

from .core import RawItem, Signal, stable_hash


# BRIDGE Signal Ledger: keywords discover event candidates; they do not by
# themselves prove wrongdoing or responsibility. Adverse and recovery events
# remain review-gated, while externally observable activity/outcome events can
# be recorded automatically with conservative confidence.
ADVERSE = {
    "논란": 2, "리콜": 3, "제재": 3, "횡령": 5, "불매": 3, "담합": 4,
    "과징금": 4, "결함": 3, "소송": 2, "비리": 5, "징계": 3, "사고": 4,
    "마약": 5, "음주운전": 5, "학폭": 4, "갑질": 4, "성추행": 5,
}
RECOVERY = {
    "사과": 2, "해명": 1, "정정": 2, "시정": 3, "보상": 3, "환불": 2,
    "재발방지": 4, "복귀": 1, "활동 재개": 1, "개선대책": 3,
}
ACTION = {
    "출시": 1, "컴백": 1, "출연": 1, "공연": 1, "월드투어": 3,
    "수주": 2, "협약": 1, "채용": 1, "투자": 2, "참여": 1,
    "신청": 1, "이용": 1, "지원": 1, "기술이전": 3, "산학협력": 2,
}
OUTCOME = {
    "수상": 2, "신기록": 3, "돌파": 2, "완판": 3, "흥행": 2,
    "빌보드": 3, "차트": 2, "1위": 2, "취업률": 1, "충원율": 1,
    "성과": 1, "흑자": 2, "최대실적": 3,
}


def _hits(title: str, vocabulary: dict[str, int]) -> tuple[list[str], int]:
    words = [word for word in vocabulary if word in title]
    return words, sum(vocabulary[word] for word in words)


def _event_key(entity_id: str, title: str) -> str:
    # Google News titles commonly end in " - publisher". Removing that tail
    # makes syndicated copies converge without merging genuinely distinct days.
    core = re.sub(r"\s+-\s+[^-]{2,40}$", "", title).casefold()
    core = re.sub(r"[^0-9a-z가-힣]+", " ", core).strip()
    return stable_hash(entity_id, core)


def build_event_record(
    entity: dict[str, Any], item: RawItem, raw_item_id: str,
    signals: Iterable[Signal],
) -> dict[str, Any] | None:
    title = item.title
    adverse_words, adverse_weight = _hits(title, ADVERSE)
    recovery_words, recovery_weight = _hits(title, RECOVERY)
    action_words, action_weight = _hits(title, ACTION)
    outcome_words, outcome_weight = _hits(title, OUTCOME)
    signal_axes = {signal.axis for signal in signals}

    if adverse_weight:
        event_type, lifecycle, direction = "issue", "detected", -1
        severity = min(5, max(1, round(adverse_weight / 2)))
        review_status = "pending"
        axes = ["R", "E"]
    elif recovery_weight:
        event_type, lifecycle, direction = "response", "recovery_candidate", 1
        severity = min(5, max(1, round(recovery_weight / 2)))
        review_status = "pending"
        axes = ["E"]
    elif outcome_weight:
        event_type, lifecycle, direction = "outcome", "observed", 1
        severity = min(5, max(1, round(outcome_weight / 2)))
        review_status = "auto"
        axes = ["G"]
    elif action_weight or "G" in signal_axes:
        event_type, lifecycle, direction = "activity", "observed", 1
        severity = min(5, max(1, round(max(action_weight, 1) / 2)))
        review_status = "auto"
        axes = ["G"]
    else:
        return None

    occurred = item.published_at or dt.datetime.now(dt.timezone.utc).isoformat()
    return {
        "entity_id": entity["id"],
        "raw_item_id": raw_item_id,
        "event_key": _event_key(entity["id"], title),
        "domain": entity["domain"],
        "event_type": event_type,
        "lifecycle_status": lifecycle,
        "direction": direction,
        "severity": severity,
        "action_strength": min(100.0, (action_weight + outcome_weight) * 10.0),
        "response_quality": min(100.0, recovery_weight * 12.5),
        "axes": axes,
        "source_ids": [item.source_id],
        "evidence_count": 1,
        "confidence": 0.60 if review_status == "auto" else 0.45,
        "review_status": review_status,
        "occurred_at": occurred,
        "last_seen_at": occurred,
        "metadata": {
            "matched_terms": {
                "adverse": adverse_words, "recovery": recovery_words,
                "action": action_words, "outcome": outcome_words,
            },
            "public_summary": {
                "issue": "책임·지속 관련 사건이 관측되었습니다.",
                "response": "책임 있는 대응과 회복 신호가 관측되었습니다.",
                "activity": "행동유발 관련 활동이 관측되었습니다.",
                "outcome": "행동유발 성과가 관측되었습니다.",
            }[event_type],
        },
    }


def diagnosis_tags(metric: dict[str, Any]) -> list[str]:
    weekly = metric.get("weekly_index")
    last = metric.get("last_week_index")
    four = metric.get("four_week_average")
    activity = float(metric.get("activity_points") or 0)
    stability = metric.get("stability")
    if weekly is None:
        return []
    tags: list[str] = []
    if last is not None:
        tags.append("상승 흐름" if weekly > last else "단기 조정" if weekly < last else "전주 수준 유지")
    if four is not None:
        tags.append("중기 평균 상회" if weekly > four else "중기 평균 하회" if weekly < four else "중기 평균 유지")
    if activity >= 10:
        tags.append("활동 신호 활발")
    elif activity <= 1:
        tags.append("활동 신호 제한적")
    if stability is not None and stability >= 80:
        tags.append("안정적 평판 기반")
    elif stability is not None and stability < 55:
        tags.append("변동성 관찰 필요")
    return tags[:3]
