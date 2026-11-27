# BRIDGE Stability 1.1 — 운영 모니터링 대시보드 v1
기준일: 2026-11-28

## 목표
기존 05:15 수집→06:45 복구→07:15 재시도→08:30 공개 확인→09:30 종합 점검 절차는 그대로 유지한다. 매번 SQL·로그·JSON을 확인하지 않아도 09:30 점검 산출물 하나에서 운영 상태를 확인하도록 한다.

## 구현
- 기존 `.github/workflows/bridge-7day-reliability.yml` 종합 점검이 `bridge-reliability.json`을 생성한 뒤 `tools/render_private_ops_dashboard.py`를 실행해 `bridge-ops-dashboard.html`을 만든다.
- 두 파일을 동일한 GitHub Actions artifact에 묶어 30일 보관한다. 원장, 점수, 데이터베이스, Cloudflare, GitHub 운영 브랜치는 이 과정에서 변경하지 않는다.
- 화면에는 최신 점검 시각, 상태(정상/복구·주의/실패/기록 없음), 검증된 날짜, 실제 발행 확보 일수, 무장애 일수, 7일 달성 여부를 표시한다.
- GitHub 공개 JSON의 기준일, Cloudflare 공개 데이터 날짜 및 건수, DB→점수→공개 JSON 정합성 검증 성공 여부를 별도로 표시한다.
- 정규 수집/근거 복구/재수집 판단/실서비스 확인/종합점검의 기존 Actions 링크를 제공한다.
- CPR·ENT·GOV·UNI 분야의 100건은 '기대값'으로 표기한다. 실측치가 아니며 확인 완료로 오인하지 않는다.
- 실패 사유의 원문·비밀값·대상별 내부 자료·DB 진단 상세는 HTML로 렌더링하지 않는다. 사용자 제공 값은 HTML 이스케이프 처리한다.

## 보안 경계
**중요:** 현재 `thefruitgrove/bridgebrand` 저장소는 공개 저장소이다. GitHub Actions artifact를 이 저장소에서 생성하는 것만으로 역할 기반의 비공개 관리자 인증이 제공되지 않는다. 접근권한을 갖춘 GitHub 이용자가 아티팩트를 볼 수 있으므로, 운영 대시보드에는 공개되어도 문제가 없는 '집계 상태'만 넣는다. `<meta name="robots" content="noindex">`는 접근제어 수단이 아니다.

이 대시보드는 운영 홈페이지 `site/`에 넣지 않으며 사이트 네비게이션에도 추가하지 않는다. 고유한 관리자 로그인·실시간 DB 조회·민감한 수집 증거 열람을 제공하려면 추후 별도 인증된 서비스(비공개 저장소 또는 접근제어된 API/Cloudflare Access)를 구축하고 권한을 검증해야 한다. 현 단계의 범위는 '점검 시점의 안전한 집계 시각화'로 제한한다.

## 실제 사용 방법
1. GitHub `thefruitgrove/bridgebrand` → Actions → `BRIDGE 7-Day Reliability Monitor`.
2. 해당 날짜의 실행을 선택한다. 기본적으로 KST 오전 9시 30분 자동 실행한다.
3. 실행의 Artifacts에서 `bridge-reliability-<run_id>` ZIP을 받는다.
4. 압축 해제 후 `bridge-ops-dashboard.html`을 브라우저에서 연다. 원시 집계가 필요하면 `bridge-reliability.json`을 확인한다.
5. 오류나 복구·주의 표시가 나오면 화면의 해당 GitHub Actions 링크 및 GitHub Issue 기록을 확인한다.

## 완료와 미완료
- 코드·자동 회귀검사·운영 main 병합 = '구현 완료'
- 첫 09:30 정규 실행에서 HTML과 JSON 아티팩트 저장 확인 = '운영 연결 검증 완료'
- 2026.11.28~12.04 날짜별 근거 7일 검증 = '안정성 7일 결과 확정'
- 30일 연속 실측 및 별도 권한 관리 = 후속 과제
