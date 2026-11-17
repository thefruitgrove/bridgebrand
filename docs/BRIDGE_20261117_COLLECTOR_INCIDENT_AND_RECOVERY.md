# BRIDGE 2026-11-17 수집 장애 및 운영 복구 기록

## 확인된 사건과 기준
- 점검 대상: 공식 웹 https://bridgebrand.co.kr 및 NEWSGRAPHY https://newsgraphy.co.kr/.
- 2026-11-17: 첫 공식 수집 재실행 `43983551965`는 `test_public_export` fixture 순위 연속성 오류로 중단.
- 재실행 `43983793213`는 미등록 후보 탐색 `discover_candidates` 중 Google News RSS HTTP 429로 중단.
- 수정 후 실행 `43987869528`는 독립 뉴스 원장 `collect-news`에서 429가 8/25/60초 제한 재시도 후에도 지속되어 필수 근거 미확보로 실패. **2026-11-17 점수와 공개 JSON을 생성하지 않음.**
- 2026-11-16: 운영 Supabase의 `bridge_axis_observations` 2,103건, `bridge_scores` 400건, `bridge_rankings` T100 400건. 공식 JSON도 `asOfDate=2026-11-16`, 400개.
- 2026-11-17 08:55 전후 실제 Cloudflare JSON은 11월 16일, snapshotId `daedab9767cec94d181c`, CPR/ENT/GOV/UNI 각 100개. 공식 GitHub와 동일한 ID임을 확인한 Actions `43983340172` 통과.
- NEWSGRAPHY `newsgraphy_bridge_snapshot`도 `as_of_date=2026-11-16`. 실제 웹 브라우저에서 BRIDGE Brand Index 위젯의 11월 16일 표시 확인: Actions `43988199222`. 이용자 제출 구화면의 11월 13일 자료는 현재 표시와 다름.

## 직접 적용된 운영 보완
1. `cfcfed79eef7ce92de564f8e897336e199377797` (운영 main) — `core.py` Google News RSS 요청 간 1.5초 간격, HTTP 429/503 한정 3회 유한 재시도, 원본 실패 시 예외 전파. 필수 RSS 수집이 실패하면 날짜·점수·순위를 생성하지 않음. 후보 발굴은 별도 advisory 단계로 분리.
2. `66dfa924f530c9da2543c80702ce68f261463f21` (운영 main) — 편집용 전체 단위검사가 일일 수집을 차단하지 않도록 핵심 정확성 회귀검사만 preflight에 포함. 미등록 후보 발굴을 점수 발행 이후로 이동. 운영 main이 실행 도중 변경된 경우 잘못된 공개 파일 발행을 성공으로 처리하지 않고 명시적 실패. 07:15 KST 자동 스케줄 보완: 당일 파일이 없고 본 수집이 활성 상태가 아닐 때만 기존 공식 파이프라인 dispatch. 후보 QA `43988402725` 성공.
3. NEWSGRAPHY Supabase `cron.jobid=9`: 매일 KST 06:00~20:40 사이 20분 간격(`*/20 21-23,0-11 * * *` UTC)으로 공식 GitHub 공개 JSON 동기화.
4. NEWSGRAPHY Supabase migration `harden_newsgraphy_bridge_snapshot_validation_20261117`: 원본 400건, 4개 분야 T100 각 100건, 발행 상태, 날짜, 각 분야 위젯 TOP3 존재를 확인한 후에만 위젯 갱신. `asOfDate`가 없으면 당일 날짜를 임의 생성하지 않음. 내용과 날짜가 같으면 `updated_at`을 새로 기록하지 않음. 실제 호출 결과 2026-11-16 유지, 수치 변경 없음.
5. 다른 프로그램에 넘기지 않고 GitHub Actions / Supabase에 직접 수정했고, 실사이트 HTTP·Chrome·DB 확인을 분리해서 수행.

## 남은 문제 및 NO-GO 판정
- **2026-11-17 당일 신규 T100 400건: 미발행.** Google News RSS의 HTTP 429가 계속돼 필수 뉴스 원장 근거를 확보하지 못했음. 단순 재시도로 해결됐다고 주장하지 않음.
- 검증용 대체 검색 조사: Bing News RSS 8개 대상 조회는 HTTP 200. 그러나 비공식 RSS이고 Microsoft 약관의 상업적 재사용 제한 및 공급자·출처·URL 리디렉션·방법론 일관성 문제가 있어 **운영 데이터 엔진에 무승인 편입하지 않음**. GDELT 쿼리 HTTP 429.
- 장기 해결은 상업적 사용이 허용된 뉴스 수집 API/언론사 공급자 계약, 독립 원천 2개 이상, 질의량 통제, 원자료별 출처 식별, 사업자별 실패 격리, 실제 수집된 축의 유효성/신뢰등급/공개날짜 강제 일치로 추진해야 함.
- NEWSGRAPHY는 상류 BRIDGE가 검증된 새 날짜를 공개하기 전까지 최근 확정일(현재 11월 16일)을 그대로 유지한다. 17일로 날짜만 올리는 행위 금지.


## 후속 운영 무결성 강화 — 날짜·원장·발행 연결검사

2026-11-17 재점검에서 완료한 추가 운영 변경:

1. 운영 커밋 `f3dfefc9d3f4ffaa8da86d64174df3fbd11a86b8`:
   - `bridge_pipeline.run healthcheck --date`로 실제 지정 KST 날짜 안에서 시작된 최신 필수 `google_news_rss`·`opendart` 수집만 승인. 과거 날짜의 성공, 종료되지 않은 `running` 상태, 같은 날 앞선 성공 이후 최신 실패를 정상으로 처리하지 않음.
   - 실제 점수 계산에 들어가기 **전** 필수 수집 완료 확인. 발행 후에도 같은 날짜로 다시 검사.
   - 복구 게이트 `tools/recovery_gate.py`가 점수 400개만 있는 경우 당일 필수 근거 6종의 최신 성공을 별도 확인. 일부 근거나 실패 로그만 존재하면 발행하지 않음. 이미 실제로 발행된 같은 날짜 자료는 보존.
   - 07:15 KST 보완 실행은 기존 수집·복구 작업이 진행 중인 경우 중복 발행/수집을 예약하지 않음.
   - `tools/verify_live.py`: 공개 페이지의 날짜와 개수가 동일해도 GitHub와 Cloudflare `snapshotId`가 다르면 명시적 오류.
   - 신규 단위/회귀검사 `43990489563` **SUCCESS**.

2. 운영 커밋 `8dcbcab8bad564861c195d4851b46faf25e81660`:
   - 매일 수집의 공개 JSON `export` 직후, **GitHub 커밋 및 Cloudflare 배포 이전** `tools.verify_export_file`을 실행.
   - 기존 읽기 전용 원장 비교 `tools.dry_run_public_export.validate`를 재사용하여 `asOfDate`, `methodologyVersion`, 4개 분야 T100 각 100건(합계 400건), rank/score/trust_grade 일치, 축 최소 가용성, `snapshotId`를 모두 검사. DB 불일치 시 발행 파일 변경을 중단.
   - 06:45 복구 경로에도 같은 DB→JSON 검사를 적용.
   - 전반 회귀검사 `43990723848` **SUCCESS**.
   - 실제 운영 읽기 전용 교차 검증 `43990856637` **SUCCESS**. DB→Git JSON: 2026-11-16, 400건, 차이 0건, snapshotId `daedab9767cec94d181c`; Git→실제 Cloudflare: 날짜·버전·개수·snapshotId 정확히 일치.

### 당일 일부 수집과 날짜 갱신에 관한 공개 원칙
- **일부 근거 수집 성공 ≠ 당일 전체 평가 발행 가능**. 400개 대상의 숫자는 필요한 근거·축·필수 수집 완료·원장 대조가 통과한 경우에만 변경.
- 실패하거나 취소된 날짜는 이전 검증 일자의 **실제 날짜를 그대로 표기**. 임의로 최신 날짜만 증가시키거나 지난 점수를 재활용하는 일은 금지.
- 2026-11-17 T100은 이 재점검 시점에도 0건. 출처 RSS 429 장애 자체는 미해결. 11월 16일 공개자료를 17일 자료로 표현하지 않음.
- **과거 실패 날짜의 자동 소급 발행은 구현돼 있지 않음**. 그 날짜의 진짜 근거가 이후 완성되더라도 당일 정기 파이프라인만으로 자동 보충되는 것은 아님. 기존 `bridge-recover-publish.yml`은 `workflow_dispatch`에 `as_of_date`를 명시하면 그 날짜 근거가 충분할 때만 검증 후 복구 가능. 과거 날짜 복구 시 최신 공개 날짜를 낮추지 않도록 별도 날짜·발행 가드가 필요.
- 데이터 공급원인 Google News RSS의 HTTP 429가 유지될 경우 본 변경은 **정확한 중단과 빠른 탐지**를 보장할 뿐, 100% 매일 지수 발행을 보장하지 않음. 적법한 안정형 뉴스 공급원, 출처별 격리와 백필 로직이 차기 선행 과제.
