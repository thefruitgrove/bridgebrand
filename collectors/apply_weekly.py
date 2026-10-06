# -*- coding: utf-8 -*-
"""
주간 수집 적용기 — 수집 결과를 실제 데이터에 반영
====================================================
DART 수집 → G축 갱신 → data/weekly_updates.json 에 기록.
build_pilot.py가 이 파일을 읽어 REAL_PILOT_CASES의 G축을 덮어쓴다.

※ 코드(build_pilot.py)를 직접 수정하지 않는다 — 데이터 파일만 갱신.
   이로써 자동 커밋이 안전하고, 사람의 코드와 충돌하지 않는다.
"""
import os, json, sys, datetime

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "engine3"))

MAP_FILE = os.path.join(HERE, "corp_code_map.json")
OUT_FILE = os.path.join(HERE, "..", "data", "weekly_updates.json")


def run():
    if not os.path.exists(MAP_FILE):
        print("corp_code_map.json 없음 — 매핑 먼저 실행"); return
    corp_map = json.load(open(MAP_FILE, encoding="utf-8"))

    import collect_dart as dart
    bgn, end = dart.weekly_range()
    today = datetime.date.today().isoformat()

    updates = {}  # {기업명: {"G_delta":+5, "evidence":"...", "week":...}}
    for name, code in corp_map.items():
        try:
            r = dart.analyze_entity(code, bgn, end)
        except Exception:
            continue
        g_cnt = len(r.get("growth_events", []))
        if g_cnt == 0:
            continue  # 변동 없으면 기록 안 함 (정체는 엔진 플래그가 처리)
        # 성과 공시 수 → G 모멘텀
        g_delta = min(6.0, 4.0 + (g_cnt - 1))  # 1건+4, 2건+5, 3건+6
        ev = "; ".join(e["report"] for e in r["growth_events"][:3])
        updates[name] = {
            "g_delta": g_delta,
            "evidence": f"[DART {today}] 성과 공시 {g_cnt}건: {ev}",
            "week": end,
        }

    # 누적 기록 (기존 + 신규, 주차별 히스토리 보존)
    allupd = {}
    if os.path.exists(OUT_FILE):
        allupd = json.load(open(OUT_FILE, encoding="utf-8"))
    allupd[end] = updates  # 이번 주 키로 저장
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(allupd, f, ensure_ascii=False, indent=2)
    print(f"✅ 주간 적용: {len(updates)}개 기업 G축 변동 기록 → {OUT_FILE}")


if __name__ == "__main__":
    run()
