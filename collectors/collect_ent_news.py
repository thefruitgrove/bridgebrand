# -*- coding: utf-8 -*-
"""BRIDGE 수집기 — 구글뉴스 RSS (ENT 아티스트) v2
기간 이원화(위기·화제 7d / 성과·활동 1m) + D축 추가 + 전주 이월."""
import os, json, time, datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
HERE = os.path.dirname(__file__)
HIST_FILE = os.path.join(HERE, "..", "data", "ent_news_history.json")
UPDATE_FILE = os.path.join(HERE, "..", "data", "ent_updates.json")
ENT_TARGETS = [
    "방탄소년단","임영웅","변우석","손흥민","지창욱","투모로우바이투게더","세븐틴",
    "스트레이키즈","박서준","남주혁","이민호","김수현","아이브","블랙핑크","트와이스",
    "에스파","수지","한소희","아이유","태연","화사","뉴진스","엔하이픈","아일릿",
]
CRISIS_KW = "논란 OR 사과 OR 의혹 OR 폭로 OR 하차 OR 마약 OR 음주운전 OR 학폭"
GROWTH_KW = "수상 OR 대상 OR 빌보드 OR 앰버서더 OR 월드투어 OR 1위 OR 신기록 OR 완판"
DEPTH_KW  = "컴백 OR 앨범 OR 신곡 OR 드라마 OR 영화 OR 출연 OR 화보 OR 팬미팅"
# 커뮤니티 site: 검색 — 구글이 색인한 공개글만, 건수 집계(원문 저장 안 함)
COMMUNITY = "site:theqoo.net OR site:instiz.net OR site:pann.nate.com"

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
    if cnt >= 20: return -15.0, f"대형 논란(위기기사 {cnt}건)"
    if cnt >= 10: return -8.0, f"논란 확산(위기기사 {cnt}건)"
    if cnt >= 5:  return -5.0, f"논란 발생(위기기사 {cnt}건)"
    if cnt >= 2:  return -3.0, f"구설 감지(위기기사 {cnt}건)"
    return 0.0, ""
def g_from_growth(cnt):
    if cnt is None or cnt == 0: return 0.0, ""
    if cnt >= 15: return 6.0, f"성과 폭발(성과기사 {cnt}건)"
    if cnt >= 8:  return 5.0, f"성과 다수(성과기사 {cnt}건)"
    if cnt >= 3:  return 4.0, f"성과 발생(성과기사 {cnt}건)"
    if cnt >= 1:  return 2.0, f"성과 포착(성과기사 {cnt}건)"
    return 0.0, ""
def d_from_depth(cnt):
    if cnt is None or cnt == 0: return 0.0, ""
    if cnt >= 15: return 4.0, f"활동 활발(기사 {cnt}건)"
    if cnt >= 5:  return 3.0, f"활동 포착(기사 {cnt}건)"
    if cnt >= 1:  return 2.0, f"활동 소수(기사 {cnt}건)"
    return 0.0, ""

def run():
    today = datetime.date.today().isoformat()
    hist = json.load(open(HIST_FILE, encoding="utf-8")) if os.path.exists(HIST_FILE) else {}
    prev_weeks = sorted(hist.keys())
    prev_data = hist[prev_weeks[-1]] if prev_weeks else {}
    tw, upd = {}, {}
    for name in ENT_TARGETS:
        vol = _count(f'"{name}"', "7d")
        crisis = _count(f'"{name}" ({CRISIS_KW})', "7d")
        growth = _count(f'"{name}" ({GROWTH_KW})', "1m")
        depth  = _count(f'"{name}" ({DEPTH_KW})', "1m")
        community = _count(f'"{name}" ({COMMUNITY})', "1m")  # 커뮤니티 화제
        pv = prev_data.get(name, {})
        if vol is None: vol = pv.get("vol")
        if crisis is None: crisis = pv.get("crisis", 0)
        if growth is None: growth = pv.get("growth", 0)
        if depth is None: depth = pv.get("depth", 0)
        if community is None: community = pv.get("community", 0)
        # 커뮤니티 건수를 전체 화제량(vol)에 합산 — I축(화제성) 보강
        vol_total = (vol or 0) + (community or 0)
        tw[name] = {"vol": vol_total, "crisis": crisis or 0, "growth": growth or 0, "depth": depth or 0, "community": community or 0}
        i_d, i_r = i_from_trend(pv.get("vol"), vol_total)
        r_d, r_r = r_from_crisis(crisis)
        g_d, g_r = g_from_growth(growth)
        d_d, d_r = d_from_depth((depth or 0) + (community or 0))  # 커뮤니티 경험담도 D축 보강
        if i_d or r_d or g_d or d_d:
            parts = [x for x in [i_r, r_r, g_r, d_r] if x]
            upd[name] = {"i_delta": i_d, "r_delta": r_d, "g_delta": g_d, "d_delta": d_d,
                         "evidence": f"[구글뉴스 {today}] " + " / ".join(parts), "week": today}
        time.sleep(2.2)
    hist[today] = tw
    for old in sorted(hist.keys())[:-12]: del hist[old]
    os.makedirs(os.path.dirname(HIST_FILE), exist_ok=True)
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    allupd = json.load(open(UPDATE_FILE, encoding="utf-8")) if os.path.exists(UPDATE_FILE) else {}
    allupd[today] = upd
    json.dump(allupd, open(UPDATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ ENT 수집(v2): {len(tw)}명 / 변동 {len(upd)}명")
if __name__ == "__main__":
    run()
