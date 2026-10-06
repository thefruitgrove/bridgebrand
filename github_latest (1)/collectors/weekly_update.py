# -*- coding: utf-8 -*-
"""
BRIDGE 주간 갱신 오케스트레이터
================================
수집기(collect_dart 등) → scoring_v3 엔진 → 데이터 갱신을 잇는 다리.
GitHub Actions가 매주 이 파일을 실행한다.

흐름:
  1. 각 수집기로 이번 주 신호 수집 (DART=D·G, 네이버=R·I[추후])
  2. 신호를 scoring_v3 형식으로 변환
  3. 엔진으로 점수 산출 → REAL_PILOT_CASES 갱신 (추후 연결)
  4. build.py 재빌드 → Cloudflare 자동 배포
"""
import os, sys, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine3"))
import scoring_v3 as eng

# ── 수집기 신호 → 엔진 입력 변환 ──────────────────────────
def dart_to_signals(dart_result):
    """
    DART 분석결과 → 엔진 입력(G 모멘텀, D 유무, 활동 유무).
    ※ v0.3.1: 성과 공시가 있으면 G 모멘텀(+4~6), 없으면 활동부재 플래그.
    """
    growth_cnt = len(dart_result.get("growth_events", []))
    g_momentum = 0.0
    if growth_cnt >= 3:   g_momentum = 6.0   # 대규모 활동
    elif growth_cnt == 2: g_momentum = 5.0
    elif growth_cnt == 1: g_momentum = 4.0
    return {
        "g_momentum": g_momentum,                      # G축 가산
        "has_depth": len(dart_result.get("depth_events", [])) > 0,
        "has_activity": dart_result.get("has_activity", False),  # 정체 판정
    }

# ── 주간 G축 갱신 (100점 모델) ────────────────────────────
def update_g_axis(prev_g, signals):
    """
    전주 G점수 + 이번 주 신호 → 새 G점수.
    v0.3.1: 모멘텀 있으면 +가산, 없으면(활동부재) 정체 신호.
    """
    g = prev_g if prev_g is not None else 50.0  # G 중립 출발
    if signals["g_momentum"] > 0:
        g = min(100.0, g + signals["g_momentum"])     # 성과 가산
        stagnant_weeks = 0
    else:
        stagnant_weeks = 1  # 활동 없음 → 정체 카운트 (감점은 엔진 플래그 ON일 때만)
    return round(g, 1), stagnant_weeks


if __name__ == "__main__":
    # ── 모의 검증 (실제 수집 대신 샘플 신호로 전체 흐름 확인) ──
    print("=== 주간 갱신 흐름 모의 검증 ===")
    # 시나리오 A: 삼성전자 — 이번 주 공급계약 2건(성과)
    sigA = dart_to_signals({"growth_events":[{"date":"2026-09-29","report":"단일판매공급계약"},
                                             {"date":"2026-09-30","report":"신규시설투자"}],
                            "depth_events":[{"date":"2026-09-28","report":"분기보고서"}],
                            "has_activity":True})
    gA, stA = update_g_axis(prev_g=35.0, signals=sigA)
    print(f"[삼성전자] 성과2건 → G 35.0 → {gA} (정체주 {stA})")

    # 시나리오 B: 어떤 기업 — 이번 주 공시 전무(정체)
    sigB = dart_to_signals({"growth_events":[], "depth_events":[], "has_activity":False})
    gB, stB = update_g_axis(prev_g=60.0, signals=sigB)
    print(f"[정체기업] 공시0건 → G 60.0 → {gB} (정체주 {stB}) ※ 엔진 플래그 ON시 감점")

    # 종합점수 산출 (A기업: G 반영 후)
    dims = {"B":82, "R":42, "I":62, "G":gA, "E":66.7}
    stag = {"G": stA}
    score, axes, renorm = eng.composite_v3(dims, stagnation_weeks=stag)
    print(f"\n[삼성전자] 종합 = {score} (축 {''.join(axes)})")
    print(f"  재정규화 가중치: {renorm}")
    print("\n✓ 수집 → 변환 → 엔진 → 점수 전체 흐름 정상 작동")
