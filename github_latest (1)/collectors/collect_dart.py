# -*- coding: utf-8 -*-
"""
BRIDGE 수집기 — DART 전자공시 (D·G축)
=====================================
금융감독원 OpenDART 공시검색 API로 주간 신규 공시를 수집해
G축(행동·성과 신호)과 D축(서사·깊이) 근거를 산출한다.

실행: GitHub Actions 또는 로컬 PC (Claude 샌드박스는 네트워크 차단).
키:  환경변수 DART_API_KEY 에서 읽는다 (코드에 키를 적지 않는다).

산출 철학(v0.3.1):
  - G축: 이번 주 '성과형 공시'(수주·투자·신제품·실적)가 있으면 모멘텀 가산(+).
         아무 공시도 없으면 '고여 있는 상태' → 정체 신호(수집기는 플래그만, 감점은 엔진이).
  - D축: 정기보고서(사업/반기/분기)·지속가능경영보고서 제출 이력 = 구조적 깊이.
"""
import os, json, time, datetime, urllib.request, urllib.parse

DART_KEY = os.environ.get("DART_API_KEY", "")
BASE = "https://opendart.fss.or.kr/api/list.json"

# 공시유형 코드 (pblntf_ty)
#   A=정기공시  B=주요사항보고  C=발행공시  D=지분공시  E=기타  F=외부감사  I=거래소공시
# G축(성과 신호)로 볼 주요사항/거래소 공시의 보고서명 키워드
GROWTH_KEYWORDS = ["단일판매", "공급계약", "수주", "투자", "신규시설", "유형자산",
                   "자기주식취득", "영업실적", "매출액", "신제품", "출시", "증설", "인수"]
# D축(구조적 깊이)로 볼 정기보고서
DEPTH_KEYWORDS = ["사업보고서", "반기보고서", "분기보고서", "지속가능경영", "기업지배구조"]


def _get(params, retries=3):
    """DART API GET 요청 (표준 라이브러리만 사용)."""
    params = dict(params); params["crtfc_key"] = DART_KEY
    url = BASE + "?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if i == retries - 1:
                return {"status": "ERR", "message": str(e)}
            time.sleep(1.5)
    return {"status": "ERR"}


def fetch_filings(corp_code, bgn, end, pblntf_ty=None):
    """한 기업의 기간 내 공시 목록. corp_code=8자리 DART 고유번호."""
    params = {"corp_code": corp_code, "bgn_de": bgn, "end_de": end,
              "page_no": 1, "page_count": 100}
    if pblntf_ty:
        params["pblntf_ty"] = pblntf_ty
    out = []
    while True:
        res = _get(params)
        if res.get("status") == "000":
            out.extend(res.get("list", []))
            total_pages = int(res.get("total_page", 1))
            if params["page_no"] >= total_pages:
                break
            params["page_no"] += 1
            time.sleep(0.3)  # 레이트리밋 예의
        else:
            break  # 013=데이터없음 포함, 조용히 종료
    return out


def analyze_entity(corp_code, bgn, end):
    """
    한 기업의 주간 공시를 분석해 D·G 신호를 반환.
    반환: {"growth_events":[...], "depth_events":[...], "has_activity":bool}
    ※ 공시 '제목(보고서명)'만 근거로 쓴다 — 본문 내용은 저장하지 않는다.
    """
    filings = fetch_filings(corp_code, bgn, end)
    growth, depth = [], []
    for f in filings:
        name = f.get("report_nm", "")
        dt = f.get("rcept_dt", "")
        if any(k in name for k in GROWTH_KEYWORDS):
            growth.append({"date": dt, "report": name})
        if any(k in name for k in DEPTH_KEYWORDS):
            depth.append({"date": dt, "report": name})
    return {
        "corp_code": corp_code,
        "growth_events": growth,          # G축 모멘텀 근거
        "depth_events": depth,            # D축 깊이 근거
        "has_activity": len(filings) > 0, # 정체 판정용(활동 유무)
        "total_filings": len(filings),
    }


def weekly_range(as_of=None):
    """이번 주 월요일~오늘(또는 지정일) 범위를 YYYYMMDD로 반환."""
    today = datetime.date.fromisoformat(as_of) if as_of else datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    return monday.strftime("%Y%m%d"), today.strftime("%Y%m%d")


if __name__ == "__main__":
    if not DART_KEY:
        print("※ DART_API_KEY 환경변수가 없습니다. GitHub Secrets 또는 .env에 설정하세요.")
        raise SystemExit(1)
    bgn, end = weekly_range()
    # 예시: 삼성전자(00126380)·현대차(00164779) 주간 공시 분석
    for name, code in [("삼성전자", "00126380"), ("현대차", "00164779")]:
        r = analyze_entity(code, bgn, end)
        print(f"[{name}] 공시 {r['total_filings']}건 / 성과신호 {len(r['growth_events'])} / 깊이 {len(r['depth_events'])}")
        for g in r["growth_events"][:3]:
            print(f"   +G {g['date']} {g['report']}")
