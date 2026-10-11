# BRIDGE 전체 시스템 복원 가이드

이 문서는 SignalBridge의 BRIDGE 브랜드평판지수 시스템을 새 컴퓨터, 새 GitHub 저장소 또는 새 Supabase 프로젝트에서 복원하기 위한 실행 순서다. 비밀키는 백업에 포함하지 않는다.

## 1. 복원에 필요한 계정

- GitHub 저장소
- Supabase 프로젝트
- Cloudflare Pages 프로젝트와 사용자 도메인
- OpenDART API 키

## 2. 소스 복원

가장 간단한 방법은 `SOURCE` 폴더를 새 Git 저장소에 올리는 것이다. 전체 Git 이력을 복원하려면 `GIT/bridgebrand_all_refs.bundle`을 사용한다.

```bash
git clone GIT/bridgebrand_all_refs.bundle bridgebrand
cd bridgebrand
git switch main
```

## 3. Supabase 복원

Supabase SQL Editor에서 `supabase/migrations`의 파일을 파일명 순서대로 실행한다.

1. `202610090001_bridge_automation.sql`
2. `202610090002_bridge_security_indexes.sql`
3. `202610090003_target_quota_governance.sql`
4. `202610090004_daily_beta_release_policy.sql`
5. `202610090005_all_domain_daily_beta.sql`
6. `202610110001_dynamic_universe_metrics.sql`

마이그레이션 후 RLS가 활성화되었는지 확인한다. 서비스 역할 키는 GitHub Actions에서만 사용하고 브라우저 코드에는 절대 넣지 않는다.

## 4. GitHub Actions 비밀값 등록

저장소의 Settings, Secrets and variables, Actions에서 다음 값을 등록한다.

```text
SUPABASE_SECRET_KEY
DART_API_KEY
CLOUDFLARE_DEPLOY_HOOK
```

`SUPABASE_URL`은 워크플로에 공개 프로젝트 URL로 지정되어 있다. 새 Supabase 프로젝트를 쓰면 `.github/workflows/bridge-daily.yml`의 URL을 바꾼다.

## 5. 데이터 초기화

```bash
python -m bridge_pipeline.run bootstrap
python -m bridge_pipeline.run audit-targets
python -m unittest discover -s tests -v
python engine3/test_scoring_v3.py
```

그 다음 GitHub Actions의 `BRIDGE Daily Pipeline`을 수동 실행한다. 최초 실행은 데이터 수집량에 따라 수십 분이 걸릴 수 있다.

## 6. 홈페이지 빌드

```bash
python build.py
python build_spa.py
```

Cloudflare Pages의 빌드 출력 디렉터리는 `site`로 설정한다. Git 연동 또는 배포 훅 중 하나를 사용한다.

## 7. 운영 스케줄

기본 자동 실행은 매일 05:15 KST다. GitHub Actions cron은 UTC 기준 `15 20 * * *`이다.

## 8. 정상 동작 확인

- GitHub Actions 테스트 20개와 엔진 회귀 테스트 7개 통과
- 뉴스 수집, DART 수집, 공식 기준축 적재가 각각 성공
- `bridge_index_metrics`에 당일 행 생성
- `bridge_rankings`에 CPR, STAR, GOV, UNI T100 생성
- `site/data/latest.json`의 `generatedAt` 갱신
- `https://bridgebrand.co.kr`에서 Daily, Weekly, Activity Points, Cumulative Performance 표시
- 공개 소스에 비밀키나 세부 산식이 노출되지 않음

## 9. 장애 복구 원칙

- 외부 API의 단일 대상 오류는 해당 대상만 건너뛰고 전체 실행을 계속한다.
- 수집 실패는 원장과 실행 로그에 남기고 기존의 마지막 정상 공개본을 유지한다.
- 빈 값은 0점으로 강제 변환하지 않고 N/R로 유지한다.
- 생성 파일은 원장에서 다시 만들 수 있어야 한다.
- 복원 직후 공개하지 말고 테스트와 적격 게이트를 먼저 통과시킨다.

