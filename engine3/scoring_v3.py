# -*- coding: utf-8 -*-
"""
BRIDGE 채점 엔진 v3 (v0.3.1 마스터 매뉴얼 구현)
================================================
서영 설계(100점 차감/상쇄 모델·차등 가중치·정체 페널티·3원 포인트)와
기존 v2 엔진(등급별 심각도·반감기·귀속계수)을 최적 결합한다.

핵심 철학:
  - 평판 기본값 = 100점(완벽한 신뢰)에서 출발, 사건으로 차감·회복으로 상쇄
  - "정체는 퇴보": 갱신 없으면 정체 페널티 (단, 주간수집 가동 후 ON)
  - 쟁점(소문)~위기(보도) 전 생애주기를 R축으로 포착 — PR 위기관리 레이더
  - 우리는 좋다/나쁘다를 판단하지 않는다. 현재 상태를 점수로 '측정'한다.
"""
import datetime as _dt

# ══════════════════════════════════════════════════════════
# [1] 차등 가중치 (총 100%) — 매뉴얼 제2장
# ══════════════════════════════════════════════════════════
AXIS_WEIGHTS = {
    "B": 0.15,  # Base 도달·체급 (비변동성)
    "R": 0.25,  # Reaction 반응·여론 (변동성) — 가장 민감
    "I": 0.15,  # Impact 임팩트·파급 (변동성)
    "D": 0.10,  # Depth 서사·깊이 (비변동성)
    "G": 0.20,  # Growth 행동·성과 (변동성)
    "E": 0.15,  # ESG 책임·지속 (비변동성)
}
VOLATILE_AXES = {"R", "I", "G"}        # 변동성(주간)
NONVOLATILE_AXES = {"B", "D", "E"}     # 비변동성(반기/연)

# ══════════════════════════════════════════════════════════
# [2] R축 심각도·반감기 — v2 등급 + v0.3.1 '실금' 통합
# ══════════════════════════════════════════════════════════
# 실금(3) = 커뮤니티 쟁점/소문 점화 단계 (PR 이슈 단계) — 신규
# 경미(5)~초대형(50) = 기존 v2 유지 (보도된 사건)
SEVERITY = {"실금": 3, "경미": 5, "중대": 15, "심각": 30, "초대형": 50}

# 반감기: 소문·해프닝은 빠르게 회복(14일), 중대사건은 오래(90~180일)
HALF_LIFE = {"실금": 14, "경미": 14, "중대": 90, "심각": 90, "초대형": 180}
# ※ 실금/경미 14일: v0.3.1 "해프닝 빠른 회복" 철학. 중대이상은 v2 지속성 유지.

# 귀속계수 — 책임 주체 분리 (기존 v2)
ATTRIBUTION = {"A": 1.0, "B": 0.5, "C": 0.2, "D": 0.0, "F": 0.3}
# A직접 / B관련 / C간접 / D무관(피해자 포함) / F전직구성원

# 긍정 상쇄 — v2 등급형 + v0.3.1 정량형 둘 다 지원
POSITIVE_GRADE = {"우수": 5, "최우수": 15, "역대급": 30}   # 정성(등급)
POSITIVE_FIXED = {"일반호평": 3.0, "대규모성과": 5.0}       # 정량(v0.3.1)

# 정체 페널티 (v0.3.1) — 주간 수집 가동 전까지 OFF
STAGNATION_PENALTY = 3.0
STAGNATION_ENABLED = False   # ※ R축 자동수집 라인 완성 후 True로 전환
# ※ 지금 켜면 갱신 없는 대상이 매주 -3씩 깎여 전멸한다. 공급 라인 선행 필수.


def _decay(days: float, severity: str) -> float:
    """시간감쇠 = (1/2)^(경과일/반감기). 등급별 반감기 적용."""
    half = HALF_LIFE.get(severity, 90)
    return 0.5 ** (days / half)


def r_axis_v3(incidents=None, positives=None, as_of=None):
    """
    R축 산출 (100점 차감/상쇄 모델).
    incidents: [{"severity","attribution","date"(YYYY-MM-DD),"category"?}]
      - category: 쟁점 분류만 저장(채용·갑질 등). 소문 원문은 저장하지 않는다.
    positives: [{"grade"? or "fixed"?, "date"}]
    반환: (R점수 0~100, 차감총액, 상쇄총액)
    """
    incidents = incidents or []
    positives = positives or []
    today = _dt.date.fromisoformat(as_of) if as_of else _dt.date.today()

    neg = 0.0
    for ev in incidents:
        sev = ev["severity"]; attr = ev.get("attribution", "A")
        d = (today - _dt.date.fromisoformat(ev["date"])).days
        neg += SEVERITY[sev] * ATTRIBUTION.get(attr, 1.0) * _decay(d, sev)

    pos = 0.0
    for pv in positives:
        d = (today - _dt.date.fromisoformat(pv["date"])).days
        if "grade" in pv:
            pos += POSITIVE_GRADE[pv["grade"]] * (0.5 ** (d / 90))  # 긍정은 90일 반감
        elif "fixed" in pv:
            pos += POSITIVE_FIXED.get(pv["fixed"], pv.get("value", 3.0)) * (0.5 ** (d / 90))

    net = max(0.0, neg - pos)          # 긍정이 부정을 상쇄
    r = round(max(0.0, 100.0 - min(100.0, net)), 1)
    return r, round(neg, 1), round(pos, 1)


# ══════════════════════════════════════════════════════════
# [3] 종합점수 — 차등 가중치 + 존재축 재정규화
# ══════════════════════════════════════════════════════════
def composite_v3(dims: dict, stagnation_weeks=None):
    """
    dims: {"B":82,"R":100,...} (없는 축은 None 또는 생략)
    stagnation_weeks: {"R":2,...} 축별 미갱신 주 수 (정체 페널티용, 옵션)
    반환: (종합점수, 사용축목록, 재정규화가중치)

    ※ 존재하는 축만으로 가중치를 재정규화한다.
      예) B·R·E만 있으면 (0.15·0.25·0.15)를 합(0.55)으로 나눠 비율 유지.
      이로써 '없는 축 때문에 억울하게 낮아지는' 왜곡을 막는다.
    """
    present = {k: v for k, v in dims.items() if v is not None}
    if len(present) < 2:
        return None, [], {}        # B규칙: 2축 미만 N/R

    # 정체 페널티 적용(옵션)
    adj = dict(present)
    if STAGNATION_ENABLED and stagnation_weeks:
        for k, wk in stagnation_weeks.items():
            if k in adj and wk and wk > 0:
                adj[k] = max(0.0, adj[k] - STAGNATION_PENALTY * wk)

    wsum = sum(AXIS_WEIGHTS[k] for k in adj)
    renorm = {k: AXIS_WEIGHTS[k] / wsum for k in adj}
    score = round(sum(adj[k] * renorm[k] for k in adj), 1)
    return score, sorted(adj.keys()), {k: round(v, 3) for k, v in renorm.items()}


# ══════════════════════════════════════════════════════════
# [4] 3원 포인트 — 매뉴얼 제4장
# ══════════════════════════════════════════════════════════
def three_points(weekly_history):
    """
    weekly_history: [{"week":"W36","score":57.5}, ...] 주차 오름차순
    반환: {주간, 누적합계, 누적평균, 차등(모멘텀)}
    """
    if not weekly_history:
        return {"weekly": None, "cum_total": None, "cum_avg": None, "delta": None}
    scores = [h["score"] for h in weekly_history if h.get("score") is not None]
    weekly = scores[-1] if scores else None
    cum_total = round(sum(scores), 1) if scores else None
    cum_avg = round(sum(scores) / len(scores), 1) if scores else None
    delta = round(scores[-1] - scores[-2], 1) if len(scores) >= 2 else None
    return {"weekly": weekly, "cum_total": cum_total, "cum_avg": cum_avg, "delta": delta}
