# -*- coding: utf-8 -*-
"""
DART 고유번호(corp_code) 매핑기
================================
우리 CPR 대상 기업명 → DART 8자리 corp_code 매핑.
corpCode.xml(전체 상장사)을 한 번 받아 캐시하고, 기업명으로 매칭한다.

실행: GitHub Actions / 로컬 (샌드박스 네트워크 차단).
키:  환경변수 DART_API_KEY.
산출: collectors/corp_code_map.json  {"삼성전자":"00126380", ...}
"""
import os, io, json, zipfile, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

DART_KEY = os.environ.get("DART_API_KEY", "")
CORPCODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
HERE = os.path.dirname(__file__)
CACHE_XML = os.path.join(HERE, "corpcode_cache.xml")
MAP_OUT = os.path.join(HERE, "corp_code_map.json")

# 서비스 표기명과 DART 법인명이 다른 상장사. 별칭은 추측하지 않고
# 사업보고서 법인명으로만 관리한다.
DART_NAME_ALIASES = {
    "현대차": "현대자동차",
    "동양생명": "동양생명보험",
    "한국조선해양": "HD한국조선해양",
}


def download_corpcode():
    """corpCode.xml(ZIP) 다운로드 → CORPCODE.xml 추출 → 캐시 저장."""
    url = CORPCODE_URL + "?" + urllib.parse.urlencode({"crtfc_key": DART_KEY})
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    # ZIP인지 확인 (에러 시 JSON/XML 에러메시지가 올 수 있음)
    if data[:2] != b"PK":
        raise RuntimeError("corpCode 응답이 ZIP이 아님 — API키·한도 확인: " + data[:200].decode("utf-8", "ignore"))
    zf = zipfile.ZipFile(io.BytesIO(data))
    xml = zf.read("CORPCODE.xml").decode("utf-8")
    with open(CACHE_XML, "w", encoding="utf-8") as f:
        f.write(xml)
    return xml


def load_corpcode():
    """캐시 있으면 사용, 없으면 다운로드."""
    if os.path.exists(CACHE_XML):
        return open(CACHE_XML, encoding="utf-8").read()
    return download_corpcode()


def _norm(name):
    """기업명 정규화 — (주)·공백·㈜ 제거해 매칭률↑."""
    return (name.replace("(주)", "").replace("㈜", "").replace("주식회사", "")
                .replace(" ", "").replace("(유)", "").strip())


def build_map(target_names):
    """
    target_names: 우리 대상 기업명 리스트.
    반환: {기업명: corp_code}  — 상장사(stock_code 있는 것) 우선.
    """
    xml = load_corpcode()
    root = ET.fromstring(xml)

    # DART 전체: 정규화명 → (corp_code, 상장여부)
    dart_index = {}
    for item in root.iter("list"):
        cc = (item.findtext("corp_code") or "").strip()
        cn = (item.findtext("corp_name") or "").strip()
        sc = (item.findtext("stock_code") or "").strip()
        if not cc or not cn:
            continue
        key = _norm(cn)
        listed = bool(sc and sc != " ")
        # 상장사 우선 저장 (동명이인 시 상장사 선택)
        if key not in dart_index or (listed and not dart_index[key][1]):
            dart_index[key] = (cc, listed)

    result, unmatched = {}, []
    for nm in target_names:
        key = _norm(DART_NAME_ALIASES.get(nm, nm))
        match = dart_index.get(key)
        # CPR 모집단은 코스피·코스닥 상장사다. 비상장 동명 법인이나 재단을
        # 잡을 수 있는 광범위한 부분일치(fuzzy match)는 사용하지 않는다.
        if match and match[1]:
            result[nm] = match[0]
        else:
            unmatched.append(nm)
    return result, unmatched


if __name__ == "__main__":
    if not DART_KEY:
        print("※ DART_API_KEY 없음. GitHub Secrets/.env 설정 필요."); raise SystemExit(1)
    # CPR + GOV(공기업) 대상 명단 로드 — DART 공시 대상만 매핑됨(비상장은 자동 제외)
    import sys
    sys.path.insert(0, os.path.join(HERE, "..", "real_data"))
    names = []
    try:
        import cpr_real
        names += [t[0] for t in cpr_real.CPR_REAL]
    except Exception:
        pass
    try:
        # GOV 공기업도 추가 — DART에 있는 것만 매핑되고 나머지는 미매칭으로 남음
        import gov_real
        names += [t[0] for t in gov_real.GOV_REAL]
    except Exception:
        try:
            # gov_real이 real_data 밖에 있을 수 있음
            sys.path.insert(0, os.path.join(HERE, ".."))
            import gov_real
            names += [t[0] for t in gov_real.GOV_REAL]
        except Exception:
            pass
    if not names:
        names = ["삼성전자", "한국전력공사"]  # 폴백
    mp, un = build_map(names)
    with open(MAP_OUT, "w", encoding="utf-8") as f:
        json.dump(mp, f, ensure_ascii=False, indent=2)
    print(f"✅ 매핑 {len(mp)}개 / 미매칭 {len(un)}개 → {MAP_OUT}")
    if un:
        print("미매칭:", un[:20])
