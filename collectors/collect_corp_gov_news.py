# -*- coding: utf-8 -*-
"""
BRIDGE 수집기 — 구글뉴스 RSS (CPR·GOV) v2
=========================================
개선: ① 기간 이원화(휘발성 7d / 구조적 1m) ② 업종 키워드 확장
      ③ 전주 이월(0건이면 전주 유지, 가짜 데이터 안 넣음)
축별 수집: R(위기·7d) / I(화제·7d증감) / G(성과·1m) / D(경험·1m)
산출: data/corpgov_updates.json + 히스토리
"""
import os, json, time, datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(__file__)
HIST_FILE = os.path.join(HERE, "..", "data", "corpgov_news_history.json")
UPDATE_FILE = os.path.join(HERE, "..", "data", "corpgov_updates.json")

CPR_TARGETS = [
    "삼성전자","SK하이닉스","현대차","삼성바이오로직스","기아","셀트리온","삼성SDI",
    "POSCO홀딩스","NAVER","카카오","현대모비스","LG화학","KB금융","한화에어로스페이스",
    "두산에너빌리티","삼성물산","SK텔레콤","리노공업","GS건설","현대건설","SK이노베이션",
    "LG전자","아모레퍼시픽","LG생활건강","신세계",
]
GOV_TARGETS = [
    "한국전력공사","한국수력원자력","한국토지주택공사","한국철도공사","한국가스공사",
    "한국도로공사","인천국제공항공사","신용보증기금","한국자산관리공사","강원랜드",
    "한국석유공사","한국가스안전공사","한국산업단지공단","한국무역보험공사","한국가스기술공사",
    "한국산업기술진흥원","한국석유관리원","대한석탄공사","대한무역투자진흥공사",
    "한국광해광업공단","국민건강보험공단","한국관광공사",
]

# 위기(R·7d) / 화제(I·7d) / 성과(G·1m) / 경험·구조(D·1m) 키워드
CPR_CRISIS = "논란 OR 리콜 OR 제재 OR 파업 OR 횡령 OR 불매 OR 담합 OR 과징금 OR 결함 OR 소송"
CPR_GROWTH = "수주 OR 신기록 OR 흑자 OR 수출 OR 최대실적 OR 신제품 OR 계약 OR 돌파 OR 증설 OR 투자"
CPR_DEPTH  = "품질 OR 서비스 OR FDA OR 승인 OR 파트너십 OR 공장 OR 특허 OR 기술 OR 수상"
GOV_CRISIS = "비리 OR 감사 OR 징계 OR 사고 OR 논란 OR 횡령 OR 방만 OR 적발 OR 중대재해"
GOV_GROWTH = "표창 OR 우수 OR 선정 OR 협약 OR 수상 OR 개선 OR 달성 OR 혁신 OR 투자 OR 유치"
GOV_DEPTH  = "서비스 OR 민원 OR 개선 OR 안전 OR 공공 OR 지원사업 OR 협력 OR 정책"

def _count(query, period="7d", retries=2):
    url = (f"https://news.google.com/rss/search?"
           f"q={urllib.parse.quote(query)}+when:{period}&hl=ko&gl=KR&ceid=KR:ko")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                root = ET.fromstring(r.read())
            return len(root.findall(".//channel/item"))
        except Exception:
            if i == retries - 1: return None
            time.sleep(2)
    return None

def i_from_trend(prev, curr):
    if prev is None or curr is None: return 0.0, ""
    if prev == 0: prev = 1
    rate = (curr - prev) / prev
    if rate >= 1.0: return 6.0, f"화제성 급증 +{round(rate*100)}%"
    if rate >= 0.5: return 5.0, f"화제성 상승 +{round(rate*100)}%"
    if rate >= 0.2: return 4.0, f"화제성 증가 +{round(rate*100)}%"
    if rate <= -0.5: return -3.0, f"화제성 급감 {round(rate*100)}%"
    if rate <= -0.2: return -2.0, f"화제성 감소 {round(rate*100)}%"
    return 0.0, ""

def r_from_crisis(cnt):
    if cnt is None or cnt == 0: return 0.0, ""
    if cnt >= 20: return -15.0, f"대형 악재(위기기사 {cnt}건)"
    if cnt >= 10: return -8.0, f"악재 확산(위기기사 {cnt}건)"
    if cnt >= 5:  return -5.0, f"악재 발생(위기기사 {cnt}건)"
    if cnt >= 2:  return -3.0, f"구설 감지(위기기사 {cnt}건)"
    return 0.0, ""

def g_from_growth(cnt):
    if cnt is None or cnt == 0: return 0.0, ""
    if cnt >= 15: return 4.0, f"성과 다수(성과기사 {cnt}건)"
    if cnt >= 5:  return 3.0, f"성과 발생(성과기사 {cnt}건)"
    if cnt >= 1:  return 2.0, f"성과 포착(성과기사 {cnt}건)"
    return 0.0, ""

def d_from_depth(cnt):
    """경험·구조 기사(1개월) → D축. B2B 결측 방어용."""
    if cnt is None or cnt == 0: return 0.0, ""
    if cnt >= 15: return 4.0, f"경험·활동 활발(기사 {cnt}건)"
    if cnt >= 5:  return 3.0, f"경험·활동 포착(기사 {cnt}건)"
    if cnt >= 1:  return 2.0, f"경험·활동 소수(기사 {cnt}건)"
    return 0.0, ""

def collect(targets, kw, hist, today):
    tw, upd = {}, {}
    prev_weeks = sorted(hist.keys())
    prev_data = hist[prev_weeks[-1]] if prev_weeks else {}
    for name in targets:
        vol = _count(f'"{name}"', "7d")              # 전체 화제성(7d)
        crisis = _count(f'"{name}" ({kw["crisis"]})', "7d")   # 위기(7d)
        growth = _count(f'"{name}" ({kw["growth"]})', "1m")   # 성과(1m)
        depth  = _count(f'"{name}" ({kw["depth"]})', "1m")    # 경험·구조(1m)
        # 전주 이월: None(수집실패)이면 전주값 사용
        pv = prev_data.get(name, {})
        if vol is None: vol = pv.get("vol")
        if crisis is None: crisis = pv.get("crisis", 0)
        if growth is None: growth = pv.get("growth", 0)
        if depth is None: depth = pv.get("depth", 0)
        tw[name] = {"vol": vol, "crisis": crisis or 0, "growth": growth or 0, "depth": depth or 0}

        prev_vol = pv.get("vol")
        i_d, i_r = i_from_trend(prev_vol, vol)
        r_d, r_r = r_from_crisis(crisis)
        g_d, g_r = g_from_growth(growth)
        d_d, d_r = d_from_depth(depth)
        if i_d or r_d or g_d or d_d:
            parts = [x for x in [i_r, r_r, g_r, d_r] if x]
            upd[name] = {"i_delta": i_d, "r_delta": r_d, "g_delta": g_d, "d_delta": d_d,
                         "evidence": f"[구글뉴스 {today}] " + " / ".join(parts), "week": today}
        time.sleep(1.8)  # 대상당 4회 호출
    return tw, upd

def run():
    today = datetime.date.today().isoformat()
    hist = json.load(open(HIST_FILE, encoding="utf-8")) if os.path.exists(HIST_FILE) else {}
    tw_all, upd_all = {}, {}
    cpr_kw = {"crisis": CPR_CRISIS, "growth": CPR_GROWTH, "depth": CPR_DEPTH}
    gov_kw = {"crisis": GOV_CRISIS, "growth": GOV_GROWTH, "depth": GOV_DEPTH}
    for targets, kw in [(CPR_TARGETS, cpr_kw), (GOV_TARGETS, gov_kw)]:
        tw, upd = collect(targets, kw, hist, today)
        tw_all.update(tw); upd_all.update(upd)
    hist[today] = tw_all
    for old in sorted(hist.keys())[:-12]: del hist[old]
    os.makedirs(os.path.dirname(HIST_FILE), exist_ok=True)
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    allupd = json.load(open(UPDATE_FILE, encoding="utf-8")) if os.path.exists(UPDATE_FILE) else {}
    allupd[today] = upd_all
    json.dump(allupd, open(UPDATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ CPR·GOV 수집(v2): {len(tw_all)}개 / 변동 {len(upd_all)}개")

if __name__ == "__main__":
    run()
