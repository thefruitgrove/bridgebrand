"""BRIDGE public-language standard.

This module does not alter scores, weights, eligibility, or evidence.  It keeps
public copy aligned with the claim strength of the underlying observation.
"""
from __future__ import annotations

import re
from collections import Counter

FOOTER_COPY = (
    "시그널브릿지(SIGNALBRIDGE)는 공개자료에서 확인되는 신호를 바탕으로 브랜드와 공중 사이의 평판을 반복 관측합니다. "
    "BRIDGE 브랜드평판지수는 기업(CPR), 공공기관(GOV), 대학(UNI), 공인(ENT)을 각 분야의 맥락 안에서 살피고, "
    "도달(B)·반응(R)·정체성(I)·경험(D)·행동유발(G)·책임·지속(E)의 여섯 축으로 현재 수준과 축별 구성, 변화의 흐름을 설명합니다. "
    "순위는 같은 분야·같은 기준일·같은 공개 범위에서 관측된 상대적 위치이며, 대상의 절대적 가치나 능력 전체를 판정하지 않습니다. "
    "결과를 읽을 때는 기준기간, 축의 관측·유지·참조 상태, 비교 가능 여부와 근거 신뢰등급을 함께 확인해야 합니다."
)

DOMAIN_COPY = {
    "CPR": {
        "title": "CPR — 기업과 공중 사이의 평판을 읽습니다",
        "deck": "기업의 규모나 재무성과가 아니라, 고객·시장·사회와 만나는 과정에서 확인된 도달·반응·경험·행동·책임의 상태를 같은 분야 안에서 비교합니다.",
        "model": "기업 규모는 관측 대상을 구성하는 참고 조건이며 평판점수를 대신하지 않습니다. CPR은 기업·브랜드·제품·계열사의 귀속을 구분하고, 공개자료에서 확인된 여섯 축만 종합지수에 반영합니다. 활동량은 사건의 규모, 지수는 관측 가능한 관계 평판 수준을 뜻하므로 서로 바꾸어 읽지 않습니다. 새로운 자료가 들어오면 실제 평판 변화와 근거 범위의 변화를 나누어 표시합니다.",
        "source": "공시·공식 발표·뉴스·고객 접점·책임 이행 등 출처와 기준시점을 확인할 수 있는 자료를 사용합니다. 세부 가중치와 수집 전략은 지식재산과 조작 방지를 위해 내부에서 관리하며, 공개 화면에는 기준일·축 상태·신뢰등급과 해석 범위를 제공합니다.",
    },
    "GOV": {
        "title": "GOV — 공공기관과 정책 수요자의 접점을 읽습니다",
        "deck": "정책 성과나 기관의 우열 전체를 평가하지 않습니다. 주민·민원인·정책 수요자에게 정책이 어떻게 발견되고 이해되며 경험과 신뢰로 이어지는지를 관측합니다.",
        "model": "중앙행정기관, 지방자치단체와 공공기관은 역할과 공중이 다릅니다. GOV는 공통 BRIDGE 6축을 유지하되 정책 안내, 이용 경험, 민원 접점, 시정·이행과 책임의 시간 흐름을 분야별 보완층에서 구분합니다. 같은 GOV 안에서도 비교 조건이 다른 경우에는 순위보다 축 상태와 근거 범위를 먼저 확인합니다.",
        "source": "공식 정책자료·업무평가·공공서비스 정보·민원 및 이용 접점·검증된 보도를 출처별 용도에 맞게 사용합니다. 공식 홍보량을 공중의 긍정 반응으로 간주하지 않으며, 기관 개편과 사업 주체의 귀속을 확인합니다.",
    },
    "UNI": {
        "title": "UNI — 대학이 약속하고 경험하게 하는 평판을 읽습니다",
        "deck": "교육·연구 역량 전체의 서열이 아니라, 대학이 지원자·학생·졸업생·사회와 형성하는 발견·정체성·경험·행동·책임의 상태를 관측합니다.",
        "model": "UNI는 모든 분야에 공통인 BRIDGE 6축 위에 대학의 공식 정체성과 외부 반복 연상의 일치, 학생·지원자 접점, 시정·이행·회복의 흐름을 보완해 읽습니다. 대학알리미 등 기준자료와 일별 변화 신호의 역할을 구분하며, 자료가 많은 대학이 자동으로 유리해지지 않도록 중복과 근거 상태를 관리합니다.",
        "source": "대학의 공식 공시·교육 및 학생지원 자료·공식 채널·검증 가능한 경험 신호를 기준기간에 맞춰 사용합니다. UNI 점수는 교육의 질 전체, 취업 가능성 또는 대학의 절대적 우수성을 뜻하지 않습니다.",
    },
    "ENT": {
        "title": "ENT — 화제의 크기와 지속되는 평판을 나누어 읽습니다",
        "deck": "인기투표나 팬덤 경쟁이 아닙니다. 공인이 대중에게 발견되고 반응을 얻으며, 어떤 이미지와 경험·행동·책임의 흐름으로 이어지는지를 관측합니다.",
        "model": "ENT는 급격한 이슈와 신규 대상의 등장을 빠르게 포착하되, 반복 전재와 독립적인 발견을 구분합니다. 팬과 일반 공중, 직군별 접점의 차이를 분야별 보완층에서 해석하며, 높은 활동량을 호감이나 신뢰로 자동 변환하지 않습니다. T100은 고정 명단이 아니며 매 회차 같은 공개 적격 규칙으로 다시 구성됩니다.",
        "source": "공식 활동·검증된 보도·공중 반응·검색과 참여 신호를 대상과 사건에 정확히 귀속합니다. 확인되지 않은 사생활, 인격, 도덕성 또는 미래 성과는 평가하지 않습니다.",
    },
}

FORBIDDEN_PUBLIC_PHRASES = (
    "진짜 평판", "완벽히", "완벽하게", "오차 없이", "완전한 독립성",
    "압도적", "독보적", "철옹성", "유일한 나침반", "구조적 비밀",
    "마음을 측정", "객관성을 보장", "반드시 반등",
)

GENERIC_OPENERS = ("이를 통해", "따라서", "한편", "이러한 구조는")
OVERUSED_ANALYSIS_NOUNS = ("관계 구조", "입체적", "유기적", "실무적 시사점")

TERM_POLICY = {
    "recommended": (
        "기준일", "동일 분야", "공개 범위", "관측됐다", "확인됐다",
        "구분해 읽는다", "직접 근거", "비교 가능", "제한 해석",
        "대안 설명", "다음 관측 질문", "활용 선택지", "축별 프로필",
    ),
    "conditional": ("원인", "신뢰", "강점", "약점", "전망", "예측", "긍정", "부정", "트렌드"),
}

CHANNEL_RULES = {
    "homepage": "짧은 정의와 읽는 법을 우선하고 한 화면에서 같은 철학을 반복하지 않는다.",
    "report": "질문·사실·비교조건·제한해석·활용제안·다음관측을 연결한다.",
    "publicity": "기사형 관심 장치 뒤에 기준 사실, 축 해석, 변화, 활동량, 한계와 다음 질문을 둔다.",
}


def audit_public_copy(text: str) -> list[str]:
    """Return editorial warnings; this is deliberately independent of scoring QA."""
    plain = re.sub(r"<[^>]+>", " ", text)
    warnings = [f"과장·모호 표현: {p}" for p in FORBIDDEN_PUBLIC_PHRASES if p in plain]
    for opener in GENERIC_OPENERS:
        if plain.count(opener) > 3:
            warnings.append(f"접속 표현 반복: {opener} {plain.count(opener)}회")
    for noun in OVERUSED_ANALYSIS_NOUNS:
        if plain.count(noun) > 3:
            warnings.append(f"추상 명사 반복: {noun} {plain.count(noun)}회")
    endings = re.findall(r"(확인됩니다|보여줍니다|의미합니다|필요합니다|수 있습니다)\.", plain)
    for ending, count in Counter(endings).items():
        if count > 5:
            warnings.append(f"종결어 반복: {ending} {count}회")
    long_sentences = [s for s in re.split(r"[.!?]\s*", plain) if len(s.strip()) > 120]
    if len(long_sentences) > 1:
        warnings.append(f"장문 반복: 120자 초과 {len(long_sentences)}문장")
    return warnings
