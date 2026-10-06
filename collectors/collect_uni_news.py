# -*- coding: utf-8 -*-
"""
BRIDGE 수집기 — 구글 뉴스 RSS (UNI I축·화제성)
구글 뉴스 RSS로 대학 주간 보도량 수집. API키 불필요, 내장 라이브러리만.
보도량 '증감'을 I축 모멘텀으로 반영(상한 100 우회 + 화제성 포착).
실행: GitHub Actions / 로컬. 산출: data/uni_updates.json, uni_news_history.json
"""
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

def get_weekly_news_volume(uni_name, retries=2):
    query = f'"{uni_name}" 대학'
    url = (f"https://news.google.com/rss/search?"
           f"q={urllib.parse.quote(query)}+when:7d&hl=ko&gl=KR&ceid=KR:ko")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                root = ET.fromstring(r.read())
            return len(root.findall(".//channel/item"))
        except Exception:
            if i == retries - 1:
                return None
            time.sleep(2)
    return None

def i_axis_from_trend(prev, curr):
    if prev is None or curr is None:
        return 0.0, "데이터 부족"
    if prev == 0: prev = 1
    rate = (curr - prev) / prev
    if rate >= 1.0:   return 6.0, f"보도량 급증 +{round(rate*100)}%(화제 폭발)"
    if rate >= 0.5:   return 5.0, f"보도량 상승 +{round(rate*100)}%"
    if rate >= 0.2:   return 4.0, f"보도량 증가 +{round(rate*100)}%"
    if rate <= -0.5:  return -3.0, f"보도량 급감 {round(rate*100)}%(모멘텀 소멸)"
    if rate <= -0.2:  return -2.0, f"보도량 감소 {round(rate*100)}%"
    return 0.0, "보도량 변화 미미"

def run():
    today = datetime.date.today().isoformat()
    hist = json.load(open(HIST_FILE, encoding="utf-8")) if os.path.exists(HIST_FILE) else {}
    this_week, updates = {}, {}
    for uni in UNI_TARGETS:
        vol = get_weekly_news_volume(uni)
        if vol is None: continue
        this_week[uni] = vol
        prev_weeks = sorted(hist.keys())
        prev_vol = hist[prev_weeks[-1]].get(uni) if prev_weeks else None
        delta, reason = i_axis_from_trend(prev_vol, vol)
        if delta != 0.0:
            updates[uni] = {"i_delta": delta,
                            "evidence": f"[구글뉴스 {today}] {reason} (이번주 {vol}건)", "week": today}
        time.sleep(1.2)
    hist[today] = this_week
    for old in sorted(hist.keys())[:-12]: del hist[old]
    os.makedirs(os.path.dirname(HIST_FILE), exist_ok=True)
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    allupd = json.load(open(UPDATE_FILE, encoding="utf-8")) if os.path.exists(UPDATE_FILE) else {}
    allupd[today] = updates
    json.dump(allupd, open(UPDATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ UNI 뉴스 수집: {len(this_week)}개 대학 / I축 변동 {len(updates)}개")

if __name__ == "__main__":
    run()
