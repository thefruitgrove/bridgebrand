# BRIDGE 브랜드평판지수 — SignalBridge

화제성(언급량·규모)이 아니라 반응·책임·회복을 6개 축(B·R·I·D·G·E)으로 진단하는
브랜드 평판 지수. 기업(CPR)·공공기관(GOV)·대학(UNI)·공인(ENT) 4개 영역을 각기 다른
잣대로 평가한다. 운영: SignalBridge. 공식 도메인: bridgebrand.co.kr (Cloudflare Pages).

## 빠른 시작 (재빌드)

압축 해제 후 이 디렉터리에서 그대로 실행 — 절대경로 하드코딩 없음(어디서든 동작):

```
python3 build.py        # site/ 개별 페이지(index·cpr·gov·uni·star·about·methodology·data-extraction·this-week·trust)
python3 build_spa.py    # site/bridge_full_site.html 단일 배포본
```

- **배포**: site/ 폴더 내용물을 Cloudflare Pages(프로젝트 bridgebrand)에 업로드.
- **발행일 변경**: data/bridge_data_v2.json 의 "published" 날짜만 바꾸면 hero의
  VOL·WEEK·날짜가 ISO 주차 기준으로 자동 갱신된다.

## 핵심 파일

| 파일 | 역할 |
|---|---|
| build.py | 개별 페이지 오케스트레이터 (헤더·푸터·네비·페이지 조립) |
| build_pilot.py | 도메인 row 렌더, REAL_PILOT_CASES(실측 105건), 방법론 박스, B규칙/3층 안전값 헬퍼 |
| build_spa.py | 단일 파일(SPA) 빌더 |
| engine2/axis_extension.py | 축 변환 함수 (esg_to_e_axis, public_eval_to_axis, rank_to_b_axis 등) |
| real_data/*.py | 대상 명단 (CPR 100 / GOV 60 / STAR 100), UNI(uni_real.py) |
| data/bridge_data_v2.json | 발행 주차/날짜 + UI 시드데이터(배포 미반영) |
| site/ | 빌드 산출물(배포 대상) + style.css / style_inline.css / script.js / img/ |

## 산출 규칙 요약

- **B규칙(공개 게이트)**: 실측·verified 축 2개 이상만 공개, 미만은 N/R.
- **3층 안전값**: measured(실측) / verified-default(탐색 후 무사건) / blind-default(미탐색, 불인정).
- **종합점수**: 존재하는 축의 단순 평균. 없는 축은 0이 아니라 N/R.
- **배지**: 순수 실측 = "실측 파일럿", R안전값 섞임 = "부분 실측"(호박색).

## 데이터 획득 경로

개발 환경(샌드박스)에서 공식 포털(KRX·DART·공공데이터포털·KCGS·ALIO 등) 접근 차단.
→ (주력) 운영자가 각 기관에서 CSV/엑셀 전체명단 다운로드 후 대조 반영,
   (보조) 대화형 검색으로 개별 R축 탐색. 대부분 연 1회 갱신(주간 갱신은 R축뿐).

## 데일리 자동화

- 매일 05:15 KST에 `.github/workflows/bridge-daily.yml`이 실행된다.
- CPR·ENT·GOV·UNI 400개 대상을 수집하고 Supabase 원장에 근거·축점수·랭킹을 적재한다.
- 검증을 통과한 네 영역의 T100만 `site/data/latest.json`으로 공개한다.
- 내부 도메인 코드 `STAR`는 홈페이지와 공개 JSON에서 `ENT`로 표시한다.
- 하위랭킹은 모집단 쿼터가 정확히 일치할 때까지 별도 공개 게이트를 적용한다.
- 기존 주간 수집기는 충돌 방지를 위해 수동 실행 전용으로 전환했다.

GitHub Actions Secrets:

```text
SUPABASE_URL
SUPABASE_SECRET_KEY
DART_API_KEY
CLOUDFLARE_DEPLOY_HOOK  # 선택 사항; Git 연동만 사용하면 생략 가능
```

## 문서

- 쉽게배우는_BRIDGE_교과서.docx — 입문·설명용
- BRIDGE_지표명세서.docx — 정밀 수식·구현 명세
- BRIDGE_종합매뉴얼_완전판.docx — 개발 이력 총기록
- BRIDGE_운영매뉴얼_홈페이지.docx — 사이트 구조·운영·재배포 가이드 (본 백업 기준 최신)
- CHANGELOG.md — 전체 변경 이력
