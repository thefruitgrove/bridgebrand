# -*- coding: utf-8 -*-
"""BRIDGE 수집기 — 구글뉴스 RSS (UNI 대학) v2
화제(I·7d증감) + 위기(R·7d) + 성과(G·1m) + 구조(D·1m) + 전주 이월."""
import os, json, time, datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
HERE = os.path.dirname(__file__)
HIST_FILE = os.path.join(HERE, "..", "data", "uni_news_history.json")
UPDATE_FILE = os.path.join(HERE, "..", "data", "uni_updates.json")
UNI_TARGETS = [
    "서울대학교","연세대학교","고려대학교","서강대학교","성균관대학교","한양대학교",
    "중앙대학교","경희대학교","한국외국어대학교","서울시립대학교","이화여자대학교",
    "숙명여자대학교","건국대학교","동국대학교","홍익대학교","국민대학교","숭실대학교",
    "세종대학교","단국대학교","광운대학교","명지대학교","상명대학교","가톨릭대학교",
    "성신여자대학교","동덕여자대학교","덕성여자대학교","서울여자대학교",
    "인하대학교","아주대학교","가천대학교","인천대학교","경기대학교",
    "KAIST","POSTECH","UNIST","GIST","DGIST",
    "부산대학교","경북대학교","전남대학교","충남대학교","전북대학교","충북대학교",
    "강원대학교","경상국립대학교","제주대학교","부경대학교","공주대학교",
    "영남대학교","동아대학교","조선대학교","계명대학교","원광대학교","한림대학교",
    "울산대학교","순천향대학교","한남대학교","동의대학교","경성대학교","한동대학교",
]
UNI_CRISIS = "논란 OR 비리 OR 입시비리 OR 사건 OR 징계 OR 적발 OR 성추행 OR 갑질"
UNI_GROWTH = "글로컬 OR 선정 OR 국책사업 OR 계약학과 OR 신설 OR 수주 OR BK21 OR 협약"
UNI_DEPTH  = "연구 OR 논문 OR 특허 OR 취업 OR 장학금 OR 등록금 OR 축제 OR 경쟁률"

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
    if cnt >= 15: return -10.0, f"논란 확산(위기기사 {cnt}건)"
    if cnt >= 7:  return -6.0, f"논란 발생(위기기사 {cnt}건)"
    if cnt >= 2:  return -3.0, f"구설 감지(위기기사 {cnt}건)"
    return 0.0, ""
def g_from_growth(cnt):
    if cnt is None or cnt == 0: return 0.0, ""
    if cnt >= 10: return 5.0, f"국책·성과 다수(기사 {cnt}건)"
    if cnt >= 3:  return 4.0, f"국책·성과 발생(기사 {cnt}건)"
    if cnt >= 1:  return 2.0, f"성과 포착(기사 {cnt}건)"
    return 0.0, ""
def d_from_depth(cnt):
    if cnt is None or cnt == 0: return 0.0, ""
    if cnt >= 15: return 4.0, f"연구·교육 활발(기사 {cnt}건)"
    if cnt >= 5:  return 3.0, f"연구·교육 포착(기사 {cnt}건)"
    if cnt >= 1:  return 2.0, f"연구·교육 소수(기사 {cnt}건)"
    return 0.0, ""

def run():
    today = datetime.date.today().isoformat()
    hist = json.load(open(HIST_FILE, encoding="utf-8")) if os.path.exists(HIST_FILE) else {}
    prev_weeks = sorted(hist.keys())
    prev_data = hist[prev_weeks[-1]] if prev_weeks else {}
    tw, upd = {}, {}
    for uni in UNI_TARGETS:
        vol = _count(f'"{uni}" 대학', "7d")
        crisis = _count(f'"{uni}" ({UNI_CRISIS})', "7d")
        growth = _count(f'"{uni}" ({UNI_GROWTH})', "1m")
        depth  = _count(f'"{uni}" ({UNI_DEPTH})', "1m")
        pv = prev_data.get(uni, {})
        if vol is None: vol = pv.get("vol")
        if crisis is None: crisis = pv.get("crisis", 0)
        if growth is None: growth = pv.get("growth", 0)
        if depth is None: depth = pv.get("depth", 0)
        tw[uni] = {"vol": vol, "crisis": crisis or 0, "growth": growth or 0, "depth": depth or 0}
        i_d, i_r = i_from_trend(pv.get("vol"), vol)
        r_d, r_r = r_from_crisis(crisis)
        g_d, g_r = g_from_growth(growth)
        d_d, d_r = d_from_depth(depth)
        if i_d or r_d or g_d or d_d:
            parts = [x for x in [i_r, r_r, g_r, d_r] if x]
            upd[uni] = {"i_delta": i_d, "r_delta": r_d, "g_delta": g_d, "d_delta": d_d,
                        "evidence": f"[구글뉴스 {today}] " + " / ".join(parts), "week": today}
        time.sleep(1.8)
    hist[today] = tw
    for old in sorted(hist.keys())[:-12]: del hist[old]
    os.makedirs(os.path.dirname(HIST_FILE), exist_ok=True)
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    allupd = json.load(open(UPDATE_FILE, encoding="utf-8")) if os.path.exists(UPDATE_FILE) else {}
    allupd[today] = upd
    json.dump(allupd, open(UPDATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ UNI 수집(v2): {len(tw)}개 / 변동 {len(upd)}개")
if __name__ == "__main__":
    run()
