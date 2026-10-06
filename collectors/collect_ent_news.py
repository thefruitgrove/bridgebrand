# -*- coding: utf-8 -*-
"""
BRIDGE 수집기 — 구글 뉴스 RSS (ENT 아티스트)
=============================================
공개 중인 아티스트 24명의 주간 여론을 3중 수집:
  - 전체 보도량 → I축(화제성) 증감
  - 위기 보도량(논란·사과·의혹·하차·마약) → R축 감점
  - 성과 보도량(수상·빌보드·앰버서더·월드투어) → G축 가산
API키 불필요, 내장 라이브러리만. 산출: data/ent_updates.json + 히스토리
"""
import os, json, time, datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(__file__)
HIST_FILE = os.path.join(HERE, "..", "data", "ent_news_history.json")
UPDATE_FILE = os.path.join(HERE, "..", "data", "ent_updates.json")

# 공개 중인 아티스트 (REAL_PILOT_CASES에 있는 것)
ENT_TARGETS = [
    "방탄소년단","임영웅","변우석","손흥민","지창욱","투모로우바이투게더","세븐틴",
    "스트레이키즈","박서준","남주혁","이민호","김수현","아이브","블랙핑크","트와이스",
    "에스파","수지","한소희","아이유","태연","화사","뉴진스","엔하이픈","아일릿",
]

# 위기 키워드 (R축 감점) / 성과 키워드 (G축 가산)
CRISIS_KW = "논란 OR 사과 OR 의혹 OR 폭로 OR 하차 OR 마약 OR 음주운전 OR 학폭"
GROWTH_KW = "수상 OR 대상 OR 빌보드 OR 앰버서더 OR 월드투어 OR 1위 OR 신기록 OR 완판"

def _count(query, retries=2):
    url = (f"https://news.google.com/rss/search?"
           f"q={urllib.parse.quote(query)}+when:7d&hl=ko&gl=KR&ceid=KR:ko")
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
    """전체 보도량 증감 → I축 모멘텀."""
    if prev is None or curr is None: return 0.0, ""
    if prev == 0: prev = 1
    rate = (curr - prev) / prev
    if rate >= 1.0: return 6.0, f"화제성 급증 +{round(rate*100)}%"
    if rate >= 0.5: return 5.0, f"화제성 상승 +{round(rate*100)}%"
    if rate >= 0.2: return 4.0, f"화제성 증가 +{round(rate*100)}%"
    if rate <= -0.5: return -3.0, f"화제성 급감 {round(rate*100)}%"
    if rate <= -0.2: return -2.0, f"화제성 감소 {round(rate*100)}%"
    return 0.0, ""

def r_from_crisis(crisis_cnt):
    """위기 기사 수 → R축 감점. 많을수록 심각."""
    if crisis_cnt is None or crisis_cnt == 0: return 0.0, ""
    if crisis_cnt >= 20: return -15.0, f"대형 논란 감지(위기기사 {crisis_cnt}건)"
    if crisis_cnt >= 10: return -8.0, f"논란 확산(위기기사 {crisis_cnt}건)"
    if crisis_cnt >= 5:  return -5.0, f"논란 발생(위기기사 {crisis_cnt}건)"
    if crisis_cnt >= 2:  return -3.0, f"구설 감지(위기기사 {crisis_cnt}건)"
    return 0.0, ""

def g_from_growth(growth_cnt):
    """성과 기사 수 → G축 가산."""
    if growth_cnt is None or growth_cnt == 0: return 0.0, ""
    if growth_cnt >= 15: return 6.0, f"성과 폭발(성과기사 {growth_cnt}건)"
    if growth_cnt >= 8:  return 5.0, f"성과 다수(성과기사 {growth_cnt}건)"
    if growth_cnt >= 3:  return 4.0, f"성과 발생(성과기사 {growth_cnt}건)"
    return 0.0, ""

def run():
    today = datetime.date.today().isoformat()
    hist = json.load(open(HIST_FILE, encoding="utf-8")) if os.path.exists(HIST_FILE) else {}
    this_week, updates = {}, {}
    for name in ENT_TARGETS:
        vol = _count(f'"{name}"')
        if vol is None: continue
        crisis = _count(f'"{name}" ({CRISIS_KW})')
        growth = _count(f'"{name}" ({GROWTH_KW})')
        this_week[name] = {"vol": vol, "crisis": crisis or 0, "growth": growth or 0}

        prev_weeks = sorted(hist.keys())
        prev_vol = hist[prev_weeks[-1]].get(name, {}).get("vol") if prev_weeks else None
        i_d, i_r = i_from_trend(prev_vol, vol)
        r_d, r_r = r_from_crisis(crisis)
        g_d, g_r = g_from_growth(growth)

        if i_d or r_d or g_d:
            parts = [x for x in [i_r, r_r, g_r] if x]
            updates[name] = {"i_delta": i_d, "r_delta": r_d, "g_delta": g_d,
                             "evidence": f"[구글뉴스 {today}] " + " / ".join(parts),
                             "week": today}
        time.sleep(1.5)  # 대상당 3회 호출이라 간격 넉넉히

    hist[today] = this_week
    for old in sorted(hist.keys())[:-12]: del hist[old]
    os.makedirs(os.path.dirname(HIST_FILE), exist_ok=True)
    json.dump(hist, open(HIST_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    allupd = json.load(open(UPDATE_FILE, encoding="utf-8")) if os.path.exists(UPDATE_FILE) else {}
    allupd[today] = updates
    json.dump(allupd, open(UPDATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ ENT 뉴스 수집: {len(this_week)}명 / 변동 {len(updates)}명")

if __name__ == "__main__":
    run()
