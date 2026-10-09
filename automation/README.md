# BRIDGE 자동화 전환안

이 디렉터리는 기존 정적 JSON·하드코딩 중심 구조를 Supabase 원장 중심으로 전환하는 1단계 구현이다. 기존 공개 화면은 유지하고 새 파이프라인은 먼저 shadow 상태로 병행한다.

## 핵심 원칙

1. 수집 실패와 실제 0건을 분리한다. 실패 시 점수를 이월하지 않고 collection run을 failed로 기록한다.
2. 뉴스 건수만으로 평판을 확정하지 않는다. 부정 신호와 윤리 신호는 검토 전 pending으로 둔다.
3. 모든 점수는 원시자료, 정규화 신호, 축 관측치, 종합점수, 랭킹의 다섯 층으로 추적한다.
4. 점수와 신뢰도를 분리한다. 높은 점수라도 근거가 빈약하면 낮은 신뢰등급을 받는다.
5. 공개 랭킹은 approved/published 스냅샷만 노출한다. 수집 중간값과 shadow 점수는 공개하지 않는다.
6. 시드용 가상 변동은 운영 원장에 적재하지 않는다.

## 최초 설정

1. Supabase에 아래 migration을 번호 순서대로 적용한다.
   - `supabase/migrations/202610090001_bridge_automation.sql`
   - `supabase/migrations/202610090002_bridge_security_indexes.sql`
   - `supabase/migrations/202610090003_target_quota_governance.sql`
   - `supabase/migrations/202610090004_daily_beta_release_policy.sql`
   - `supabase/migrations/202610090005_all_domain_daily_beta.sql`
2. GitHub Actions Secrets에 다음 값을 등록한다.
   - `SUPABASE_URL`
   - `SUPABASE_SECRET_KEY` (`sb_secret_...`; 브라우저·프론트엔드에 절대 포함하지 않음)
   - `DART_API_KEY`
   - `CLOUDFLARE_DEPLOY_HOOK` 선택 사항
3. 최초 한 번 대상과 방법론을 적재한다.

```bash
python -m bridge_pipeline.run bootstrap
```

4. Actions의 `BRIDGE Daily Pipeline`을 수동 실행해 검증한다.

현재 운영 프로젝트 URL은 `https://gorlbfqvyxtdsxgoqinf.supabase.co`이다. 프로젝트 secret key는 저장소 파일이 아니라 GitHub Actions Secret에만 둔다.

## 대상 쿼터 검증 상태

- 승인 구조: CPR `BC70/BB30`, STAR `AM40/AW40/AN20`, GOV `GM40/GC60`
- 현재 베타 명단: CPR `B2C35/B2B65`, STAR `AM45/AW45/AN10`, GOV `GM40/GC60`
- 따라서 현재 명단은 shadow 수집에는 사용할 수 있으나 CPR·STAR 하위랭킹의 정식 공개에는 사용할 수 없다.
- Supabase `bridge_pipeline_alerts`에 `TARGET_QUOTA_MISMATCH` 경고를 기록했으며, 검증된 교체 명단 반영 후에만 해제한다.
- `bridge_target_quota_status`가 확정 쿼터와 활성 대상 수를 실시간 비교한다.
- 주간 공개 직전에 `python -m bridge_pipeline.run audit-targets`를 실행하며, 하나라도 불일치하면 종료코드 2로 공개를 차단한다.
- 데일리 베타는 CPR·ENT·GOV·UNI의 `T100`을 공개한다. 내부 코드 `STAR`는 공개 JSON에서 `ENT`로 변환한다.
- BC70·BB30·AM40·AW40·AN20 하위랭킹은 쿼터가 정확히 일치할 때까지 데일리 공개에서 제외한다.

## 운영 주기

- 매일 05:15 KST: 공개자료 수집, 중복 제거, 대상 매칭, 신호 적재, CPR·ENT·GOV·UNI T100 베타 공개, 공개 JSON 갱신
- 매주 월요일 06:00 KST: 주간 공개 게이트 점검 및 승인된 랭킹 export
- 분기·연간: KRX, KCGS, ALIO 등 구조 데이터는 별도 승인 후 적재

## 현재 단계에서 자동화하지 않은 판단

- 기사 제목만으로 사건의 사실 여부·책임 귀속·심각도를 확정하는 일
- R축 부정 사건과 E축 윤리 판단의 자동 공개
- 소셜 플랫폼 약관을 우회하는 크롤링
- 데이터가 없다는 이유로 100점 또는 업계 평균을 부여하는 일

이 네 가지는 자동화할수록 신뢰 리스크가 커지므로 검토 큐를 거친다. 이후 12주 shadow 결과에서 사람과 규칙의 일치도를 측정한 뒤 자동 승인 범위를 넓힌다.

## 전환 순서

1. 2주: 기존 사이트와 병행 수집, 수집 성공률과 중복률 측정
2. 4주: CPR 20개 대상 shadow 점수 비교
3. 8주: CPR 100개 및 STAR/GOV 확대
4. 12주: 가중치 민감도, 순위 안정성, 검토자 일치도 통과 시 정식 공개 원장 전환

## 제거 대상

기존 `.github/workflows/weekly-collect.yml`은 새 파이프라인이 2주 연속 정상 동작한 뒤 비활성화한다. 즉시 삭제하면 운영 공백이 생기므로 현재는 병행 상태로 둔다.
