# -*- coding: utf-8 -*-
"""scoring_v3 회귀 테스트 — 엔진 수정 시 python3 engine3/test_scoring_v3.py 로 검증"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import scoring_v3 as s

def approx(a, b, tol=0.15): return abs(a - b) <= tol

def run():
    ok = 0; fail = []
    # R축: 심각(30)·30일경과 → 100 - 30*1.0*0.5^(30/90)
    r,_,_ = s.r_axis_v3([{"severity":"심각","attribution":"A","date":"2026-08-31"}], as_of="2026-09-30")
    (ok:=ok+1) if approx(r,76.2) else fail.append(f"심각30일 {r}≠76.2")
    # 실금(3)·14일 → 절반 → 100-1.5=98.5
    r,_,_ = s.r_axis_v3([{"severity":"실금","attribution":"A","date":"2026-09-16"}], as_of="2026-09-30")
    (ok:=ok+1) if approx(r,98.5) else fail.append(f"실금14일 {r}≠98.5")
    # 귀속 D(피해자)=0 → 감점 없음 → 100
    r,_,_ = s.r_axis_v3([{"severity":"심각","attribution":"D","date":"2026-09-01"}], as_of="2026-09-30")
    (ok:=ok+1) if approx(r,100.0) else fail.append(f"귀속D {r}≠100")
    # 긍정상쇄: 중대(15)-대규모성과(5) 동시, 당일 → 100-10=90
    r,_,_ = s.r_axis_v3([{"severity":"중대","attribution":"A","date":"2026-09-30"}],
                        [{"fixed":"대규모성과","date":"2026-09-30"}], as_of="2026-09-30")
    (ok:=ok+1) if approx(r,90.0) else fail.append(f"긍정상쇄 {r}≠90")
    # 차등가중: B100 R100 E100 → 100 (전축 만점)
    sc,_,_ = s.composite_v3({"B":100,"R":100,"E":100})
    (ok:=ok+1) if approx(sc,100.0) else fail.append(f"전축만점 {sc}≠100")
    # B규칙: 1축만 → None(N/R)
    sc,_,_ = s.composite_v3({"R":100})
    (ok:=ok+1) if sc is None else fail.append(f"B규칙 {sc}≠None")
    # 3원 모멘텀: 57.5→62.1 → Δ+4.6
    tp = s.three_points([{"week":"W39","score":57.5},{"week":"W40","score":62.1}])
    (ok:=ok+1) if approx(tp["delta"],4.6) else fail.append(f"모멘텀 {tp['delta']}≠4.6")

    print(f"통과 {ok}/7", "✓ 전부 통과" if not fail else f"✗ 실패: {fail}")
    return not fail

if __name__ == "__main__":
    import sys as _s; _s.exit(0 if run() else 1)
