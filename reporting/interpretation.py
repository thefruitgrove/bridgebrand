"""BRIDGE interpretation, audit and briefing contracts.

This is the third layer of BRIDGE.  It consumes already-published observations
and produces diagnostics for editors.  It deliberately contains no scoring
weights, no source thresholds and no code that writes to the evidence ledger.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping, Sequence

AXES = ("B", "R", "I", "D", "G", "E")
VALID_STATES = {"observed", "maintained", "reference"}
REFLECTIVE_ROLES = {
    "fact", "comparison", "meaning", "limitation",
    "verification_question", "practical_implication",
}
PAGE_TITLES = {
    1: "표지와 핵심 명제", 2: "선택 대상과 BRIDGE의 공식 정의",
    3: "점수·신뢰등급·축 상태", 4: "BRIDGE 6축 독립 해석",
    5: "BRIDGE 축 결합 해석", 6: "종합지표 읽기",
    7: "두 지수가 묻는 질문", 8: "BRIDGE의 일곱 가지 차별점",
    9: "서로 다른 순위가 나오는 이유", 10: "어느 지수가 어떤 질문에 적합한가",
    11: "순위와 등락의 의미", 12: "T100과 보조 관측군",
    13: "분석 개요와 중심 명제", 14: "선택 대상 집중분석",
    15: "비교 대상 A 기본 브리핑", 16: "비교 대상 B 기본 브리핑",
    17: "세 대상 6축 비교", 18: "활동량·변화·근거 범위 분석",
    19: "종합 해석과 다음 관측 질문", 20: "PUBLICITY",
    21: "해석상 한계와 참고자료",
}
PUBLICITY_BLOCKS = (
    "attention_headline", "fact_lead", "relationship_structure",
    "movement_reason", "evidence_scope", "domain_context",
    "interpretation_boundary", "next_checkpoint",
)

# Public prose rules.  Internal exploratory cut-offs are intentionally absent.
FORBIDDEN_PUBLIC_PATTERNS = {
    "압도적 우위": "점수 간격과 관측 범위를 설명하세요.",
    "무조건 더 정확": "측정 질문과 검증 범위를 설명하세요.",
    "정체성 전환력": "정의되지 않은 용어입니다.",
    "모든 사람이 긍정": "반응 강도와 방향을 분리하세요.",
    "도덕성이 낮": "E축은 도덕성 판정이 아닙니다.",
}


@dataclass(frozen=True)
class Claim:
    text: str
    role: str
    evidence_keys: tuple[str, ...] = ()

    def __post_init__(self):
        if self.role not in REFLECTIVE_ROLES:
            raise ValueError(f"Unknown claim role: {self.role}")
        if not self.text.strip():
            raise ValueError("Empty analysis sentence")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    blocks_publication: bool = False


def usable_axis(row: Mapping, axis: str) -> bool:
    return (
        row.get("axis_status", {}).get(axis) in {"observed", "maintained"}
        and isinstance(row.get("axis_scores", {}).get(axis), (int, float))
    )


def validate_observation(row: Mapping) -> list[Finding]:
    findings: list[Finding] = []
    states = row.get("axis_status") or {}
    if set(states) != set(AXES):
        findings.append(Finding("high", "AXIS_STATE_MISSING", "6축 상태가 명시되지 않았습니다.", True))
        return findings
    unknown = sorted(set(states.values()) - VALID_STATES)
    if unknown:
        findings.append(Finding("high", "AXIS_STATE_INVALID", f"검증되지 않은 축 상태: {', '.join(unknown)}", True))
    if sum(usable_axis(row, axis) for axis in AXES) < 2:
        findings.append(Finding("high", "MEASURED_AXES_INSUFFICIENT", "산출 가능한 축이 2개 미만입니다.", True))
    return findings


def validate_same_scope(rows: Sequence[Mapping]) -> list[Finding]:
    findings: list[Finding] = []
    if not rows:
        return [Finding("high", "EMPTY_SELECTION", "비교 대상이 없습니다.", True)]
    fields = {
        "domain": {row.get("domain") for row in rows},
        "date": {row.get("as_of_date") for row in rows},
        "methodology": {row.get("methodology_version") for row in rows},
        "ranking_type": {row.get("ranking_type", "T100") for row in rows},
    }
    for name, values in fields.items():
        if len(values) != 1 or None in values:
            findings.append(Finding("high", f"MIXED_{name.upper()}", f"비교 대상의 {name} 범위가 다릅니다.", True))
    ids = [str(row.get("external_id")) for row in rows]
    if len(ids) != len(set(ids)):
        findings.append(Finding("high", "DUPLICATE_TARGET", "동일 대상이 비교군에 중복되었습니다.", True))
    return findings


def rank_movement(current: Mapping, previous: Mapping | None) -> dict:
    if previous is None:
        return {"type": "no_baseline", "score_delta": None, "rank_delta": None}
    score_delta = round(float(current["score"]) - float(previous["score"]), 4)
    rank_delta = int(previous["rank"]) - int(current["rank"])
    if abs(score_delta) < 1e-9 and rank_delta:
        kind = "relative_move_with_static_score"
    elif score_delta > 0 and rank_delta > 0:
        kind = "score_and_rank_rise"
    elif score_delta > 0 and rank_delta <= 0:
        kind = "score_rise_without_rank_rise"
    elif score_delta < 0 and rank_delta > 0:
        kind = "rank_rise_despite_score_fall"
    elif score_delta < 0 and rank_delta < 0:
        kind = "score_and_rank_fall"
    else:
        kind = "mixed_or_static"
    return {"type": kind, "score_delta": score_delta, "rank_delta": rank_delta}


def set_change(current: Sequence[Mapping], previous: Sequence[Mapping]) -> dict:
    cur = {str(row["external_id"]) for row in current}
    prev = {str(row["external_id"]) for row in previous}
    return {"current_size": len(cur), "previous_size": len(prev), "entered": sorted(cur-prev), "exited": sorted(prev-cur)}


def axis_coverage(rows: Sequence[Mapping]) -> dict[str, int]:
    return {axis: sum(usable_axis(row, axis) for row in rows) for axis in AXES}


def coverage_change(current: Sequence[Mapping], previous: Sequence[Mapping]) -> dict[str, dict[str, int]]:
    cur, prev = axis_coverage(current), axis_coverage(previous)
    return {axis: {"previous": prev[axis], "current": cur[axis], "delta": cur[axis]-prev[axis]} for axis in AXES}


def period_label(observation_dates: Iterable[str], calendar_days: int = 7) -> dict:
    dates = sorted({d for d in observation_dates if d})
    count = len(dates)
    return {"status": "complete" if count == calendar_days else "partial", "observed_days": count, "calendar_days": calendar_days}


def four_week_label(observed_weeks: int | None) -> str:
    n = int(observed_weeks or 0)
    if n <= 0:
        return "AVAILABLE-WEEK AVERAGE · N/R"
    return "4-WEEK AVERAGE" if n >= 4 else f"AVAILABLE-WEEK AVERAGE · 관측 {n}주"


def trust_coverage_review(row: Mapping) -> Finding | None:
    """Coverage and trust are separate.  Flag only for human review."""
    usable = sum(usable_axis(row, axis) for axis in AXES)
    if row.get("trust_grade") == "A" and usable < 5:
        return Finding("review", "TRUST_COVERAGE_REVIEW", f"신뢰 A와 산출축 {usable}/6의 의미를 함께 재검토해야 합니다.", False)
    return None


def lint_public_text(text: str) -> list[Finding]:
    findings = []
    for pattern, guidance in FORBIDDEN_PUBLIC_PATTERNS.items():
        if pattern in text:
            findings.append(Finding("high", "PUBLIC_OVERCLAIM", f"'{pattern}': {guidance}", True))
    if "참조 50" in text and "실제 평가점수가 아니" not in text:
        findings.append(Finding("high", "REFERENCE_AS_SCORE", "참조선 50을 실제 평가값처럼 쓸 수 없습니다.", True))
    return findings


def audit_page_contract(pages: Sequence[Mapping]) -> list[Finding]:
    findings: list[Finding] = []
    if len(pages) < 21:
        findings.append(Finding("high", "PAGE_COUNT", "일반 브리핑은 최소 21페이지여야 합니다.", True))
    seen = set()
    for page in pages:
        number = int(page.get("number", 0))
        if number in seen:
            findings.append(Finding("high", "DUPLICATE_PAGE", f"{number}페이지가 중복되었습니다.", True))
        seen.add(number)
        claims = page.get("claims") or []
        if 11 <= number <= 21 and not 7 <= len(claims) <= 10:
            findings.append(Finding("high", "ANALYSIS_DENSITY", f"{number}페이지 분석문장은 7~10개여야 합니다.", True))
        texts = set()
        for raw in claims:
            claim = raw if isinstance(raw, Claim) else Claim(str(raw.get("text", "")), str(raw.get("role", "")), tuple(raw.get("evidence_keys", ())))
            normalized = " ".join(claim.text.split())
            if normalized in texts:
                findings.append(Finding("high", "REPEATED_SENTENCE", f"{number}페이지에 동일 문장이 반복됩니다.", True))
            texts.add(normalized)
            findings.extend(lint_public_text(claim.text))
    return findings


def audit_publicity_payload(payload: Mapping) -> list[Finding]:
    findings: list[Finding] = []
    blocks = tuple(payload.get("editorial_blocks") or ())
    if blocks != PUBLICITY_BLOCKS:
        findings.append(Finding("high", "PUBLICITY_BLOCKS", "PUBLICITY 8블록 계약이 일치하지 않습니다.", True))
    prose = " ".join(
        [str(payload.get("title", "")), str(payload.get("standfirst", ""))]
        + [str(p) for section in payload.get("sections", ()) for p in section.get("paragraphs", ())]
    )
    findings.extend(lint_public_text(prose))
    if "활동량" in prose and not any(boundary in prose for boundary in ("긍정", "우호", "방향")):
        findings.append(Finding("high", "ACTIVITY_BOUNDARY", "활동량과 긍정·우호 방향의 차이를 설명해야 합니다.", True))
    return findings


def assert_publishable(payload: Mapping) -> None:
    blocked = [f for f in audit_publicity_payload(payload) if f.blocks_publication]
    if blocked:
        raise ValueError("PUBLICITY interpretation audit failed: " + "; ".join(f.code for f in blocked))


def finding_dicts(findings: Sequence[Finding]) -> list[dict]:
    return [asdict(finding) for finding in findings]
