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
