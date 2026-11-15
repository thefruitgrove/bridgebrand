# BRIDGE 2.0 정식 배포 사전검사 — 조건부 NO-GO 기록
2026-11-15 KST / 배포 허가 접수 후 운영 검사 / 검증 당시 상태

## 판정: NO-GO — 운영 main/Cloudflare에는 병합·배포하지 않음
사용자는 2026-11-15 정식 배포를 명시적으로 승인했다. 그러나 배포의 필수 조건 가운데 **운영 일간 발행/원장 연결 및 라이브 스냅샷 최신성**이 충족되지 않았다. 기능을 검증하지 않은 상태에서 성공 또는 정식 운영 시작으로 보고하지 않는다.

### 1. 안전하게 완료한 준비 작업
- PR #12(`bridge-editorial-standard-v1`)는 2026-11-15 편집 브랜치 CI 성공을 확인한 후 비운영 배포 후보 PR #11의 base 브랜치 `bridge-integration-candidate-20261115`로 **merge**했다.
- 통합 후보 커밋 `9c97fbaa63114c5b498dc39366738e3e47dca404`.
- 통합 후보 Actions run **43685471812 SUCCESS**: 전체 오프라인 Python/Node 회귀검사, JS syntax, 정적 사이트 재빌드, 원본 공개 JSON 보존 및 diff 검사. 이는 운영 REST 성공을 뜻하지 않는다.
- 기존 production main `7b5e644e0c943f8da7cb2d66d02eb09b4645591f`을 `backup/pre-release-20261115` 브랜치로 별도 보존해 코드 롤백 지점을 확보했다. 이 백업은 Supabase 데이터 및 Cloudflare 배포의 완전한 복구본을 의미하지 않는다.
- 운영 DB에 쓰기, 재계산, 강제 publish, GitHub main 병합, Cloudflare 배포는 실행하지 않았다.

### 2. 확인된 실제 운영 상태
- 운영 Supabase 프로젝트 `gorlbfqvyxtdsxgoqinf`: 2026-11-14 T100 400개, 지수 `bridge_index_metrics` 400개, UNI T100 100개.
- **2026-11-15 T100 0개**. 최근 점수·지수·순위 날짜는 2026-11-14.
- 2026-11-15 GitHub Daily Pipeline run **43655673565 FAILURE**: 초기 `Unit and regression tests`에서 `test_footer_copy` 검증 실패(`27 not greater than or equal to 28`), 근거 수집·점수 산출·발행 단계에 도달하지 못함. 통합 후보에는 이미 해당 테스트 가정의 수정이 포함됨.
- Recover Existing Observations run **43662598659 FAILURE**: 해당 날짜 metrics 0, observation 0, `essential_collectors_succeeded=false`, `mode=blocked`, `reason=insufficient_validated_existing_evidence`. 안전장치가 부정확한 재발행을 중지함.
- Live Deployment Verification run **43669904335 SUCCESS(health classifier warning)**: 2026-11-15 11:54 KST 무렵 실제 사이트 `https://bridgebrand.co.kr` 및 GitHub 공개 파일이 모두 **2026-11-13 기준 400개**로 확인됐고 `warnings:[live_snapshot_not_today]`. 성공한 워크플로는 최신성 GO가 아니라 경고 허용 정책의 성공이다.
- 운영 DB 11/14 vs 공개 사이트 11/13의 발행 날짜 불일치 상태. **원장 → 점수 → 공개 JSON → 라이브 화면**을 동시 검증한 적격한 최신 스냅샷이 필요.

### 3. 계속 차단하는 조건
1. 고정 2026-11-14 운영 REST read-only export `python tools/dry_run_public_export.py --date 2026-11-14`를 실제 Supabase API 자격으로 실측, SQLSTATE 57014 과거 관측 조회가 재발하지 않는지 확인. 현재는 CLI help/offline unit test만 완료.
2. 11/15 수집 근거가 누락된 상태에서 재출판을 강행하지 말 것. 원인을 해결한 뒤 **당일 정규 수집을 실제로 실행하여** 400개 적격 순위와 지수의 일치, CPR shadow 보호를 확인할 것.
3. Cloudflare 연결 방식 및 배포 후 실제 화면/데이터 날짜 확인. 현재 이 채팅 환경에서는 Cloudflare Pages 계정에 직접 접근·배포할 수 있는 연결이 없음.
4. CPR/GOV/UNI/ENT 실제 대상의 현재 날짜를 사용해 03/04 내용·15개 조합·PDF BASIC/STANDARD와 모바일 시각·클릭 검증.
5. 통합 후보 GO일 때만 PR #11을 `main`에 병합하고 자동 연결된 Cloudflare 배포를 검증한 뒤, GitHub main SHA와 라이브 배포 SHA를 기록할 것. 실패 시 이전 commit과 **사이트/DB 각각의 복구방법**을 사용해야 함.

### 4. 증거 링크
- PR #11: https://github.com/thefruitgrove/bridgebrand/pull/11
- 통합 완료 PR #12: https://github.com/thefruitgrove/bridgebrand/pull/12
- 통합 후보 CI: https://github.com/thefruitgrove/bridgebrand/actions/runs/43685471812
- Daily 실패: https://github.com/thefruitgrove/bridgebrand/actions/runs/43655673565
- Recover 차단: https://github.com/thefruitgrove/bridgebrand/actions/runs/43662598659
- 라이브 최신성 경고: https://github.com/thefruitgrove/bridgebrand/actions/runs/43669904335

**현재 상태:** 코드 통합과 main 백업 완료. **정식 배포/운영 최신성 NO-GO**. 마케팅·편집 품질의 성공을 운영 데이터 최신성의 성공으로 혼동하지 않는다.


## 5. 추가 실측: 2026-11-14 REST 400건 검증 통과와 원인 수정

초기 실제 PostgREST read-only 전체 export 테스트 [43685644640](https://github.com/thefruitgrove/bridgebrand/actions/runs/43685644640)는 **400건을 읽었지만 2개 순위가 DB와 달라 실패**했다. DB `bridge_rankings`의 STAR T100 순위 68위 `STAR-096`, 69위 `STAR-016`은 공개 score가 모두 **53.65**인데, `export_latest`가 공식 DB 순위를 무시하고 공개 외부 ID 사전순으로 **동점 대상만 다시 정렬**하여 68·69위를 뒤바꿨다. 오류는 실제 운영 근거를 통해 재현되었다.

**수정:** `bridge_pipeline/run.py`에서 이미 발행된 DB `rank`와 `rank_change`를 절대로 다시 계산하지 않도록 고쳤다. 대신 분야/순위별 1부터 N까지의 유일성·연속성 및 점수의 내림차순 정합성을 검사하고, 이상이 있으면 공개 export 자체를 중단한다. `tests/test_authoritative_rank_export.py`에 동점·순위 중복·점수 역전 3개 회귀검사를 추가하고, 종전의 암묵적인 재정렬을 기대하던 `tests/test_public_export.py`의 mock 데이터를 DB 권위 기준으로 교정했다. 이 수정은 DB 데이터와 점수를 변경하지 않았다.

수정 이후 실제 운영 REST 테스트 [43686165918](https://github.com/thefruitgrove/bridgebrand/actions/runs/43686165918) **SUCCESS**:
- `as_of_date=2026-11-14`, `row_count=400`, `domains=4`
- `diff_count=0` (**DB와 생성 공개 파일의 대상·순위·점수·신뢰등급 일치**)
- `read_queries=207`, `elapsed_sec=162.48`, `mode=READ_ONLY_TEMPORARY_FILES`
- `snapshot_id=3ed14e3b87d066c04a8c`
- 57014 재발 없이 해당 고정 날짜의 과거 자료를 조회·생성·검증 완료.
- 통합 후보 전체 오프라인 테스트도 [43686267863](https://github.com/thefruitgrove/bridgebrand/actions/runs/43686267863) **SUCCESS**.

**판정 변경 없음:** 11/15 순위 0건, 라이브 홈페이지 11/13 데이터, 오늘 정규 수집 중단 상태는 해결되지 않았다. 따라서 **시스템 배포 종합 GO/NO-GO는 여전히 NO-GO**. 새로 검증한 `2026-11-14` 가상 공개 산출물은 임시 파일에서만 생성했으며 GitHub main·배포용 JSON·Cloudflare·Supabase에 게시하지 않았다. 정식 운영 전 남은 조건은 실제 최신 수집/발행 및 사이트와 DB 스냅샷 일치, PC/모바일/실대상 PDF 라이브 점검, 클라우드 배포 확인이다.


## 6. ChatGPT 직접 운영 긴급수정 및 2026-11-15 20:20 KST 재검증

### 운영 main 최소 핫픽스(실제 적용 완료)
- main 기존 기준: `7b5e644e0c943f8da7cb2d66d02eb09b4645591f`; 원상복구 브랜치 `backup/pre-release-20261115`은 변경하지 않음.
- main 커밋 `091ce54e23325e2939cc172be9e4fb3b0ada5719`: `tests/test_footer_copy.py`의 잘못된 28개 HTML 개수 조건을 명시적 실제 중요 화면 목록 + v2 푸터 계약 검사로 대체. 운영 첫 단계에서 발생한 확정적 false-positive CI 실패에 대한 최소 변경이며 데이터 생성·점수·발행 코드를 변경하지 않음.
- main 커밋 `1e0116ffc5c87890548f13daf50db19b28a41f57`: `.github/workflows/bridge-live-verify.yml`의 08:30 KST 검증에서 최대 2일 경과를 허용하던 `--max-age-days 2`를 `0`으로 수정. 정해진 검증 시각에 당일 발행이 없으면 CI 실패로 표시하게 함. 기존 네 가지 오프라인 분류 테스트는 유지.
- main 두 핫픽스는 **정식 BRIDGE 2.0 PR 병합/지수 발행/Cloudflare 직접 배포가 아니다**. GitHub main 새 SHA를 확인하였으나 Cloudflare 실제 사이트의 적용 여부는 검증되지 않음.

### PR #11 통합 후보의 추가 보호코드
- `.github/workflows/bridge-daily.yml`: 운영 전 점검을 핵심 점수·원장·순위·공개 검증으로 분리하고, 전체 편집·Node 회귀검사는 비운영 후보 QA로 옮기는 수정(아직 main에 미반영).
- `.github/workflows/bridge-live-verify.yml`: 동일한 당일 신선도 강화(운영 main에는 위 최소 핫픽스만 별도로 적용).
- `site/script.js`: null/비숫자 직전 주간 이력을 숫자 0으로 강제 변환하지 않도록 방어, 이전 주간 결측은 `N/R`로 표기.
- `tests/test_missing_week_display.js`, `tests/test_live_freshness_gate.py`: 결측/실제 0 분리 및 당일 필수 정책 회귀검사.
- `.github/workflows/bridge-integration-readonly-qa.yml`: 새 JS 검증 포함.
- 통합 후보 SHA `f8b96f223e900c97096a441a2142468fa0c4fac6`; Actions `43708154740` **SUCCESS** (읽기 전용 전체 회귀검사와 사이트 재빌드, 공개 데이터 불변 검증).

### 운영 DB 직접 조회 결과
- 2026-11-14 `bridge_index_metrics` 총 400건 중 `last_week_index IS NULL` 386건, 실제 `last_week_index = 0` 0건. 과거 지표 0.00 오인 문제는 DB 수치가 0인 문제가 아니라 프런트엔드/배포 표시 구분 문제임.
- 운영 DB `bridge_axis_observations`: 11/14 2,113건, 11/15 0건.
- `bridge_scores`와 `bridge_index_metrics`: 11/14 각각 400건, 11/15 0건.
- `bridge_rankings` T100: 11/14 각 분야 100건, 총 400건. 11/15 0건.
- 실측 시각 2026-11-15 20:20 KST: 11/15 원장·지수·순위는 존재하지 않음. 없는 근거를 복제하거나 날짜를 바꾸지 않음.

### 여전히 차단되는 사항
1. 11/15 실제 수집/점수/발행 미실행. main의 CI false-positive 수정은 다음 정상 실행에서 이 특정 장애를 예방하기 위한 것이지 당일 데이터 복구가 아님.
2. Cloudflare 계정 제어 403, 실제 Cloudflare 자동 배포·롤백 동작 검증 미완료.
3. PR #11 전체 코드 통합은 main에 **미병합**. 실운영 모바일·PDF·문자 인코딩 점검 미완료.
4. 11/14 DB와 11/13 GitHub 공개 JSON 간 날짜 차이 미복구.

**판정: BRIDGE 2.0 정식 배포 NO-GO 유지. 운영 main 최소 CI·모니터링 핫픽스는 완료.**
