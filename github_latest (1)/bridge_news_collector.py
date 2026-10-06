#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BRIDGE 뉴스 수집기 — 네이버 뉴스 검색 API 버전
=================================================

이 스크립트는 지금까지 대화(백서 21.2.1절 발행일 게이트, 38장 검색 도구 한계)에서
확인된 문제를 실제로 해결합니다:

  1. web_search는 특정 날짜 구간을 하드 필터로 못 걸었다  →  이 스크립트는 pubDate를
     실제로 파싱해서 지정한 [시작일, 종료일] 구간에 정확히 속하는 기사만 남긴다.
  2. "카카오"(기업) vs "카카오"(초콜릿) 같은 동음이의어 충돌(21.2.2절)  →  네거티브
     필터 키워드로 무관한 기사를 제거한다.
  3. 자료원별 신뢰계수(21.2절 표)를 도메인 기준으로 자동 태깅한다.

사용 전 준비물
----------------
1. https://developers.naver.com 접속 → 로그인 → Application 등록(무료, 즉시 발급)
   - 사용 API: "검색" 선택
   - 발급받은 Client ID / Client Secret을 아래 CLIENT_ID / CLIENT_SECRET에 채워 넣는다.
2. 파이썬 3.8 이상, requests 라이브러리만 있으면 됨:
       pip install requests

주의할 점 (정직하게 명시)
--------------------------
- 네이버 뉴스 검색 API는 "시작일~종료일"을 직접 받는 파라미터가 없다. 대신
  sort="date"(최신순)로 요청한 뒤, pubDate를 직접 파싱해 원하는 구간만 걸러내는
  방식으로 동작한다 — 이게 이 스크립트의 핵심 로직이다.
- 한 쿼리당 최대 1000건(start+display-1 <= 1000)까지만 조회 가능하다. 화제성이
  매우 높은 키워드는 하루이틀 안에 1000건을 넘길 수 있으므로, 그런 경우 쿼리를
  더 구체적으로 좁혀야 한다(예: "삼성전자" 대신 "삼성전자 갤럭시").
- 무료 쿼터 안에서 동작하며, 개인 프로젝트 규모(하루 수백~수천 회 호출)에서는
  일반적으로 비용이 발생하지 않는다. 정확한 한도는 네이버 개발자센터 대시보드에서
  본인 계정 기준으로 직접 확인할 것.
"""

import requests
import re
import sys
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

# ============================================================
# 1) 발급받은 키를 여기 채워 넣으세요
# ============================================================
CLIENT_ID = "여기에_발급받은_Client_ID_입력"
CLIENT_SECRET = "여기에_발급받은_Client_Secret_입력"

# ============================================================
# 2) 21.2절 신뢰계수표 — 도메인을 알아보는 대로 계속 추가해서 채워나가면 됨
#    (지금은 뼈대만 채워둔 상태. 실제 도메인은 originallink를 보고 하나씩 확인해서
#    보강해야 정확도가 올라간다.)
# ============================================================
SOURCE_CREDIBILITY = {
    "yna.co.kr": (0.85, "통신사(연합뉴스)"),
    "news1.kr": (0.85, "통신사(뉴스1)"),
    "newsis.com": (0.85, "통신사(뉴시스)"),
    "hankyung.com": (0.55, "중견언론(한국경제)"),
    "mk.co.kr": (0.55, "중견언론(매일경제)"),
    "edaily.co.kr": (0.55, "중견언론(이데일리)"),
    "biz.sbs.co.kr": (0.55, "중견언론(SBS Biz)"),
    "namu.wiki": (0.35, "크라우드 위키"),
    "kakaocorp.com": (0.40, "자체 발표"),
    "samsung.com": (0.40, "자체 발표"),
    "skhynix.co.kr": (0.40, "자체 발표"),
}
DEFAULT_CREDIBILITY = (0.55, "미분류 언론사(수동 확인 필요)")


def credibility_for(url: str):
    """originallink의 도메인을 보고 21.2절 신뢰계수를 매긴다."""
    try:
        domain = urlparse(url).netloc.replace("www.", "")
    except Exception:
        return DEFAULT_CREDIBILITY
    for known_domain, info in SOURCE_CREDIBILITY.items():
        if known_domain in domain:
            return info
    return DEFAULT_CREDIBILITY


def strip_html(text: str) -> str:
    """네이버 API는 title/description에 <b> 태그로 검색어를 강조해서 준다. 제거한다."""
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&apos;", "'")
    return text.strip()


def fetch_news_in_window(
    query: str,
    window_start: datetime,
    window_end: datetime,
    negative_filter_terms=None,
    max_pages: int = 5,
):
    """
    지정한 [window_start, window_end] 구간에 속하는 뉴스만 골라서 반환한다.
    (21.2.1절 발행일 검증 게이트를 실제 코드로 구현한 것)

    Parameters
    ----------
    query : str
        검색어. 엔터티명 그대로 넣는다 (예: "삼성전자").
    window_start, window_end : datetime (timezone-aware, KST 권장)
        원하는 주간/기간의 시작일과 종료일. 예: Week 35 = 2026-08-31 ~ 2026-09-04.
    negative_filter_terms : list[str] or None
        21.2.2절 엔터티-일반명사 충돌 필터. 예: 카카오 검색 시 ["초콜릿", "코코아", "가나슈"].
        이 단어가 title+description에 있으면 그 기사는 버린다.
    max_pages : int
        한 번에 몇 페이지(100건씩)까지 훑을지. 화제성이 낮은 키워드는 1~2페이지로도
        window_start 이전까지 도달한다. 화제성이 매우 높으면 늘려야 할 수 있다.

    Returns
    -------
    list[dict] : window 안에 속하는 기사만, 최신순으로.
                 각 dict: title, description, url, source_domain, credibility,
                          credibility_label, pub_date(datetime)
    """
    negative_filter_terms = negative_filter_terms or []
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    endpoint = "https://openapi.naver.com/v1/search/news.json"

    collected = []
    for page in range(max_pages):
        start_idx = page * 100 + 1
        if start_idx > 1000:
            break  # 네이버 API 자체 한도

        params = {
            "query": query,
            "display": 100,
            "start": start_idx,
            "sort": "date",  # 최신순 — 이래야 날짜 기준으로 끊어나갈 수 있다
        }
        resp = requests.get(endpoint, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"[경고] API 응답 오류 {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            break

        items = resp.json().get("items", [])
        if not items:
            break

        reached_before_window = False
        for item in items:
            try:
                pub_date = parsedate_to_datetime(item["pubDate"])
            except Exception:
                continue  # pubDate 파싱 실패 시 21.2.1절 원칙대로 폐기(사용 안 함)

            if pub_date > window_end:
                continue  # 아직 너무 최신 — window 진입 전, 계속 다음 항목 확인
            if pub_date < window_start:
                reached_before_window = True
                continue  # window보다 오래됨 — 정렬이 최신순이므로 이 페이지 이후는 볼 필요 없음

            title = strip_html(item["title"])
            description = strip_html(item["description"])
            combined_text = title + " " + description

            # 21.2.2절: 엔터티-일반명사 충돌 필터
            if any(term in combined_text for term in negative_filter_terms):
                continue

            credibility, label = credibility_for(item["originallink"] or item["link"])
            collected.append({
                "title": title,
                "description": description,
                "url": item["originallink"] or item["link"],
                "source_domain": urlparse(item["originallink"] or item["link"]).netloc,
                "credibility": credibility,
                "credibility_label": label,
                "pub_date": pub_date,
            })

        if reached_before_window:
            # 최신순 정렬이므로, window보다 오래된 기사가 나오기 시작했다는 것은
            # 더 뒤 페이지를 봐도 전부 window 밖이라는 뜻. 여기서 멈춘다.
            break

    collected.sort(key=lambda x: x["pub_date"], reverse=True)
    return collected


def kst(y, m, d, hh=0, mm=0):
    """한국 시간대(KST, UTC+9) datetime을 간편하게 만드는 헬퍼."""
    return datetime(y, m, d, hh, mm, tzinfo=timezone(timedelta(hours=9)))


# ============================================================
# 사용 예시 — Week 35(2026-08-31~09-04) 삼성전자 공백을 메우는 실제 호출
# ============================================================
if __name__ == "__main__":
    if CLIENT_ID.startswith("여기에") or CLIENT_SECRET.startswith("여기에"):
        print("먼저 CLIENT_ID / CLIENT_SECRET을 발급받은 값으로 채워주세요.")
        print("발급: https://developers.naver.com → Application 등록 → '검색' API 선택")
        sys.exit(1)

    # Week 35 = 2026-08-31 ~ 2026-09-04 (백서 20장 기준 실제 구간)
    week35_start = kst(2026, 8, 31, 0, 0)
    week35_end = kst(2026, 9, 4, 23, 59)

    results = fetch_news_in_window(
        query="삼성전자",
        window_start=week35_start,
        window_end=week35_end,
        negative_filter_terms=[],  # 삼성전자는 일반명사 충돌 없음(카카오 검색 시엔 채울 것)
        max_pages=5,
    )

    print(f"\n=== 삼성전자 — Week 35 (2026-08-31~09-04) 실제 발행 기사: {len(results)}건 ===\n")
    for r in results:
        print(f"[{r['pub_date'].strftime('%Y-%m-%d %H:%M')}] "
              f"(신뢰계수 {r['credibility']}, {r['credibility_label']}) {r['title']}")
        print(f"  {r['url']}\n")

    if not results:
        print("이 구간에 해당하는 기사가 없습니다 — 이것도 유효한 결과입니다")
        print("(백서 34장: '근거 0건'은 결측이 아니라 그 자체로 하나의 측정 결과)")
