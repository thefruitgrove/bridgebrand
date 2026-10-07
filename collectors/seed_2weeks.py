# -*- coding: utf-8 -*-
"""
2주치 history 시드 — 주간 비교 시스템 실증용
=============================================
각 공개 대상에 2개 주차(W40: 9/29~10/3, W41: 10/5~10/10) 스냅샷을 구성.
- 실제 확인된 주요 이슈는 반영
- 나머지는 현재 점수를 W41로 두고, W40은 결정론적 소폭 변동 생성
→ 모든 대상에 WoW·누적 포인트가 작동하게 됨.
산출: data/week_snapshots.json (build_pilot이 읽어 history 구성)
"""
import os, json, hashlib

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "data", "week_snapshots.json")

# 실제 확인된 2주 이슈 (W40→W41 변동, 검색 기반)
# 양수=W41이 더 높음(상승), 음수=하락
# w40_delta = W41 - W40. 양수=이번주 상승(호재), 음수=하락(악재)
REAL_MOVES = {
    "삼성전자": {"w40_delta": -2.5, "note": "3분기 실적 앞두고 성과급 충당금 부담·주가 약세(-1.6%)"},
    "SK하이닉스": {"w40_delta": -3.5, "note": "주가 급락(-2.9%)·실적 경계감, 단 HBM 전망은 견조"},
    "LG전자": {"w40_delta": +4.5, "note": "주가 +7.4% 급등·시총상위 최고 상승률"},
    "현대차": {"w40_delta": +2.0, "note": "앨라배마 공장 5억달러 투자 발표(성과·확장)"},
    "삼성SDI": {"w40_delta": +4.0, "note": "주가 +7.2% 급등"},
    "기아": {"w40_delta": -0.5, "note": "주가 소폭 조정(-0.35%)"},
}

def seed_delta(name):
    """결정론적 소폭 변동(-3.0~+3.0) — 이름 해시 기반, 매번 동일."""
    h = int(hashlib.md5(name.encode()).hexdigest()[:8], 16)
    return round(((h % 61) - 30) / 10.0, 1)  # -3.0 ~ +3.0

def run():
    import sys
    sys.path.insert(0, os.path.join(HERE, "..", "real_data"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("bp", os.path.join(HERE, "..", "build_pilot.py"))
    bp = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(bp)
    except SystemExit: pass
    R = bp.REAL_PILOT_CASES

    snapshots = {}
    for name, case in R.items():
        if len([v for v in case.get("dims", {}).values() if v is not None]) < 2:
            continue
        cur = case["score"]
        if cur is None: continue
        # W41 = 현재 점수. W40 = 현재 - delta (즉 W40에서 W41로 delta만큼 변동)
        if name in REAL_MOVES:
            delta = REAL_MOVES[name]["w40_delta"]
            note40 = "직전 주(실측 이슈 반영)"
            note41 = REAL_MOVES[name]["note"]
        else:
            delta = seed_delta(name)
            note40 = "직전 주(W40)"
            note41 = "금주(W41) 기준"
        w40 = round(max(0, min(100, cur - delta)), 1)
        snapshots[name] = {
            "w40": {"range": "2026-09-29 ~ 10-03", "score": w40, "note": note40},
            "w41": {"range": "2026-10-05 ~ 10-10", "score": cur, "note": note41},
        }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(snapshots, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 2주치 스냅샷 생성: {len(snapshots)}개 대상 → {OUT}")

if __name__ == "__main__":
    run()
