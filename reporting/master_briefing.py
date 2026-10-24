"""Audited 21-page BRIDGE briefing composer.

This module belongs to the interpretation layer.  It never recalculates scores,
changes evidence states or replaces a published trust grade.  It converts an
already-published snapshot into two parallel readings: an accessible entrance
and a professional analysis, then blocks export when the editorial contract is
not satisfied.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from typing import Mapping, Sequence

from .interpretation import (
    AXES, Claim, PAGE_TITLES, audit_page_contract, finding_dicts,
    usable_axis, validate_observation, validate_same_scope,
)

AXIS_NAMES = {
    "B": "도달", "R": "반응", "I": "정체성", "D": "경험",
    "G": "행동유발", "E": "책임·지속",
}
AXIS_QUESTIONS = {
    "B": "얼마나 널리 발견되는가", "R": "공중은 어떻게 응답하는가",
    "I": "무엇으로 기억되는가", "D": "실제 접점은 어떠한가",
    "G": "어떤 움직임을 만드는가", "E": "신뢰를 얼마나 지켜내는가",
}
DOMAIN_CONTEXT = {
    "ENT": "팬과 일반 공중, 인기와 관계 평판, 활동과 관계 수준을 구분합니다.",
    "UNI": "학생·학부모·구성원·사회와 대학의 관계를 보며 교육·연구 역량 전체를 판정하지 않습니다.",
    "GOV": "시민·이용자·정책 공중과 기관의 관계를 보며 행정능력이나 정책 성과 전체를 판정하지 않습니다.",
    "CPR": "고객·시장·이해관계자와 기업의 관계를 보며 기업가치·투자등급·재무전망을 판정하지 않습니다.",
}
PAIR_RULES = {
    "BR": ("발견 반응력", "널리 발견된 관심이 실제 반응과 함께 관측되는가"),
    "BI": ("인지도 정체성", "많이 알려진 만큼 무엇으로 기억되는지도 분명한가"),
    "BD": ("도달 경험 전환", "노출과 실제 접점 경험이 함께 관측되는가"),
    "BG": ("발견 행동 전환", "발견과 검색·참여·구매 등 행동이 함께 관측되는가"),
    "BE": ("확산 지속성", "넓은 노출과 책임·지속 신호가 함께 관측되는가"),
    "RI": ("반응 정체성 결속", "반응이 특정 이미지와 의미를 중심으로 모이는가"),
    "RD": ("반응 경험 일치", "온라인 반응과 실제 접점 경험이 같은 방향인가"),
    "RG": ("반응 행동 동반", "반응과 후속 행동이 함께 관측되는가"),
    "RE": ("반응 관계 유지", "현재 반응과 지속 관계 신호가 함께 관측되는가"),
    "ID": ("약속 경험 일치", "알려진 정체성과 실제 경험이 일치하는가"),
    "IG": ("정체성 행동 동력", "선명한 정체성과 공중 행동이 함께 관측되는가"),
    "IE": ("정체성 지속성", "현재 이미지와 책임·지속 신호가 함께 관측되는가"),
    "DG": ("경험 행동 동반", "접점 경험과 재참여·행동이 함께 관측되는가"),
    "DE": ("경험 신뢰 축적", "반복 경험과 장기 신뢰 신호가 함께 관측되는가"),
    "GE": ("행동 관계 지속", "행동과 지속 관계 신호가 함께 관측되는가"),
}


def _name(row: Mapping) -> str:
    return str(row.get("name") or row.get("target_name") or row.get("external_id"))


def _score(row: Mapping) -> float:
    value = row.get("daily_index", row.get("score"))
    if not isinstance(value, (int, float)):
        raise ValueError(f"{_name(row)}의 당일지수가 숫자가 아닙니다.")
    return float(value)


def _activity_text(row: Mapping) -> str:
    value = row.get("activity_points")
    if value is None:
        return "활동량은 이번 입력에서 확인되지 않았습니다."
    if float(value) == 0:
        return "활동량 0P는 검증·귀속·중복 제거 기준을 통과한 사건 활동이 이번 범위에서 기록되지 않았다는 뜻이며, 실제 활동이 전혀 없었다는 뜻은 아닙니다."
    return f"활동량 {value:g}P는 이번 범위에서 검증·귀속·중복 제거된 사건 움직임의 크기이며, 긍정 평판의 크기가 아닙니다."


def _usable_axes(row: Mapping) -> list[str]:
    return [axis for axis in AXES if usable_axis(row, axis)]


def _axis_extremes(row: Mapping) -> tuple[str, str]:
    axes = _usable_axes(row)
    if not axes:
        raise ValueError(f"{_name(row)}에 산출 가능한 축이 없습니다.")
    scores = row["axis_scores"]
    return max(axes, key=lambda a: scores[a]), min(axes, key=lambda a: scores[a])


def _pair(row: Mapping) -> tuple[str, str, str] | None:
    axes = sorted(_usable_axes(row), key=lambda a: row["axis_scores"][a], reverse=True)
    if len(axes) < 2:
        return None
    pair = "".join(axis for axis in AXES if axis in axes[:2])
    label, question = PAIR_RULES[pair]
    return pair, label, question


def _claim(text: str, role: str, keys=(), certainty="bounded") -> Claim:
    return Claim(text, role, tuple(keys), certainty, "professional")


class BridgeBriefingEngine:
    """Create a publish-audited single-target or three-target briefing."""

    def __init__(self, rows: Sequence[Mapping]):
        self.rows = [dict(row) for row in rows]
        if len(self.rows) not in {1, 3}:
            raise ValueError("기본 브리핑은 1개, 일반 브리핑은 3개 대상을 사용해야 합니다.")
        findings = validate_same_scope(self.rows)
        for row in self.rows:
            findings.extend(validate_observation(row))
            if not str(row.get("trust_grade", "")).strip():
                raise ValueError(f"{_name(row)}의 실제 근거 신뢰등급이 없습니다.")
        blocked = [finding for finding in findings if finding.blocks_publication]
        if blocked:
            raise ValueError("비교 범위 검증 실패: " + "; ".join(f.code for f in blocked))
        self.primary = self.rows[0]
        self.domain = str(self.primary["domain"]).upper()
        if self.domain not in DOMAIN_CONTEXT:
            raise ValueError(f"지원하지 않는 분야입니다: {self.domain}")

    def _easy(self, page: int) -> str:
        row, name = self.primary, _name(self.primary)
        high, low = _axis_extremes(row)
        copies = {
            1: f"{name}의 오늘 숫자가 무엇을 말하고 무엇을 말하지 않는지부터 확인합니다.",
            2: "BRIDGE는 사람의 마음을 직접 읽지 않고, 공개자료에서 확인 가능한 관계 신호를 반복 관측합니다.",
            3: f"점수와 근거 신뢰등급 {row['trust_grade']}은 서로 다른 값입니다. 신뢰등급은 평판등급이 아닙니다.",
            4: "여섯 축은 ‘발견되고, 반응받고, 기억되고, 경험되고, 행동과 지속으로 이어지는가’를 나누어 묻습니다.",
            5: "두 축을 함께 보는 것은 원인을 단정하는 일이 아니라, 함께 나타난 관계의 모양을 읽는 일입니다.",
            6: "오늘·이번 주·지난주·활동량은 서로 다른 시간과 질문을 나타내므로 한 숫자처럼 합쳐 읽지 않습니다.",
            7: "다른 지수와 BRIDGE는 승패 관계가 아니라 서로 다른 질문에 답하는 도구입니다.",
            8: _activity_text(row),
            9: "관측과 유지는 점수에 반영되지만 참조 50은 화면의 기준선일 뿐 대상의 실제 평가점수가 아니며 산출에서 제외됩니다.",
            10: DOMAIN_CONTEXT[self.domain],
            11: "순위는 같은 날 같은 분야 안에서의 상대적 위치이며, 대상의 절대적 우열이 아닙니다.",
            12: "T100 명단은 고정 출연자 목록이 아니며 공개 적격성과 최신 관측에 따라 바뀔 수 있습니다.",
            13: f"{name}은 오늘 {_score(row):.2f}점이며, 가장 강하게 관측된 축은 {high}·{AXIS_NAMES[high]}입니다.",
            14: f"{name}의 여섯 축은 하나의 평균보다 관계의 강약 배치를 보여주는 지도에 가깝습니다.",
            15: f"{high}·{AXIS_NAMES[high]}이 높게 관측됐다는 사실과 그 원인은 구분해서 읽어야 합니다.",
            16: f"{low}·{AXIS_NAMES[low]}은 현재 산출축 중 상대적으로 낮지만, 곧바로 부정 경험이나 실패를 뜻하지 않습니다.",
            17: "두 축 조합은 함께 관측된 신호에서 다음에 확인할 질문을 찾는 해석 도구입니다.",
            18: _activity_text(row),
            19: "비교는 누가 더 훌륭한지를 판정하기보다 관계 구조가 어디에서 다른지를 설명합니다.",
            20: "PUBLICITY는 검증된 분석을 대중 언어로 다시 쓰되, 새로운 사실이나 원인을 덧붙이지 않습니다.",
            21: "확인되지 않은 것은 한계로 남기고, 필요한 데이터와 다음 관측 질문을 함께 제시합니다.",
        }
        return copies[page]

    def _dense_claims(self, page: int) -> list[Claim]:
        row, name = self.primary, _name(self.primary)
        high, low = _axis_extremes(row)
        pair = _pair(row)
        scope = f"{row['as_of_date']} {self.domain} {row.get('ranking_type', 'T100')}"
        base = [
            _claim(f"{scope} 공개 스냅샷에서 {name}의 당일 관계 평판지수는 {_score(row):.2f}로 기록됐습니다.", "fact", ("as_of_date", "domain", "daily_index"), "confirmed"),
            _claim(f"산출에 사용할 수 있는 축은 {len(_usable_axes(row))}/6개이며 참조축은 강약 판정과 종합 해석에서 제외했습니다.", "fact", ("axis_status", "axis_scores"), "confirmed"),
            _claim(f"산출축 가운데 {high}·{AXIS_NAMES[high]}은 상대적으로 높고 {low}·{AXIS_NAMES[low]}은 상대적으로 낮게 관측됐습니다.", "comparison", ("axis_scores", "axis_status"), "confirmed"),
            _claim(f"이 배치는 {name}의 현재 관계 구조를 설명하지만, 각 축의 구체적 원인이나 공중 전체의 내면을 직접 증명하지는 않습니다.", "limitation", certainty="bounded"),
            _claim(_activity_text(row), "meaning", ("activity_points",) if row.get("activity_points") is not None else (), "confirmed" if row.get("activity_points") is not None else "bounded"),
            _claim(f"다음 회차에서는 {low}·{AXIS_NAMES[low]}의 유효 근거가 확대되는지, 상태가 관측·유지·참조 사이에서 바뀌는지 확인해야 합니다.", "verification_question", certainty="hypothesis"),
            _claim(f"실무에서는 {high}·{AXIS_NAMES[high]}의 확인된 강점을 유지하되, {low}·{AXIS_NAMES[low]}의 원인을 단정하지 말고 관련 접점 데이터를 별도로 점검하는 편이 타당합니다.", "practical_implication", certainty="recommendation"),
        ]
        if pair:
            code, label, question = pair
            base[3] = _claim(f"{code} 조합은 ‘{label}’이라는 관점에서 ‘{question}’를 묻지만 두 축 사이의 인과관계를 판정하지는 않습니다.", "meaning", ("axis_scores", "axis_status"), "bounded")
        # Give each analytical page a distinct editorial purpose without inventing facts.
        page_focus = {
            11: "순위는 비교집합의 상대적 이동도 함께 반영하므로 점수 변화와 분리해 확인해야 합니다.",
            12: "T100의 진입·이탈과 비교집합 크기 변화가 있으면 같은 순위 번호의 의미도 달라질 수 있습니다.",
            13: "중심 명제는 가장 강한 축과 낮은 축, 현재 의미와 다음 검증 질문을 한 문장 안에서 연결해야 합니다.",
            14: "여섯 축의 독립값과 상태를 함께 공개해야 종합점수 뒤의 구조를 재검토할 수 있습니다.",
            15: f"{high}축의 높은 값은 해당 정의의 신호가 강했다는 뜻이며 대상의 모든 역량이 우수하다는 뜻은 아닙니다.",
            16: f"{low}축의 낮은 값은 현재 근거 범위의 상대적 위치이며 부정 사건이나 관계 실패와 동일하지 않습니다.",
            17: "축 조합은 공동 관측 패턴에서 질문을 만드는 장치이며 전환·축적·회복을 자동으로 입증하지 않습니다.",
            18: "활동량, 점수 변화, 축 커버리지 변화는 각각 사건 규모, 관계 수준, 근거 범위라는 서로 다른 변수를 나타냅니다.",
            19: "복수 대상 비교에서는 중심 대상에 유리한 축만 고르지 않고 각 대상의 독립적인 강점과 한계를 함께 제시해야 합니다.",
            20: "대외 문장은 주목도를 확보할 수 있지만 기준일·대상군·근거 상태·해석 한계를 생략해서는 안 됩니다.",
            21: "장기 이력이 부족하거나 안정성이 N/R이면 안정적·불안정하다고 판정하지 않고 산출 불가 상태를 그대로 밝힙니다.",
        }
        base[3] = _claim(page_focus[page], "limitation", certainty="bounded")
        return base

    def build(self) -> dict:
        pages = []
        for number in range(1, 22):
            claims = self._dense_claims(number) if number >= 11 else []
            pages.append({
                "number": number,
                "part": 1 if number <= 6 else 2 if number <= 10 else 3 if number <= 12 else 4,
                "title": PAGE_TITLES[number],
                "easy_read": self._easy(number),
                "professional_read": [asdict(claim) for claim in claims],
                "claims": [asdict(claim) for claim in claims],
            })
        audit = audit_page_contract(pages)
        return {
            "metadata": {
                "domain": self.domain,
                "as_of_date": self.primary["as_of_date"],
                "methodology_version": self.primary["methodology_version"],
                "mode": "single" if len(self.rows) == 1 else "comparison",
                "targets": [_name(row) for row in self.rows],
                "trust_grades": {_name(row): row["trust_grade"] for row in self.rows},
                "reading_model": "easy_and_professional",
            },
            "pages": pages,
            "audit": finding_dicts(audit),
            "publishable": not any(f.blocks_publication for f in audit),
        }

    def export_json(self) -> str:
        report = self.build()
        if not report["publishable"]:
            codes = ", ".join(item["code"] for item in report["audit"] if item["blocks_publication"])
            raise ValueError("브리핑 발행 계약 검증 실패: " + codes)
        return json.dumps(report, ensure_ascii=False, indent=2)

