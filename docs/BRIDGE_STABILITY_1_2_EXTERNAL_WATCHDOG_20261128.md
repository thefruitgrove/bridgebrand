# BRIDGE Stability 1.2 — Cloudflare 독립 예약 Watchdog (배포 대기)

작성일: 2026-11-28 | 저장소: `thefruitgrove/bridgebrand` | 범위: 기존 BRIDGE 운영 보호

## 도입 목적과 판단
GitHub Actions의 예약 이벤트는 지연·누락될 수 있다. BRIDGE는 2026-11-27의 05:15 KST 예정 수집이 11:51 KST에 생성된 사례가 있다. GitHub 내부 07:15 fallback도 GitHub 예약 이벤트에 의존하므로 동일 플랫폼의 스케줄 장애를 독립적으로 복구한다고 볼 수 없다.

이번 모듈은 Cloudflare Worker의 독립 Cron에서 기존 GitHub `bridge-daily.yml`의 `workflow_dispatch`를 1회 요청하도록 설계했다. 수집·점수계산·검증·발행은 기존 GitHub workflow와 Supabase의 보호장치만 수행하며 Worker는 절대 직접 만지지 않는다.

## 실제 코드
- `external_scheduler/src/index.js`: 예약 이벤트·사전 확인·GitHub API 요청 로직.
- `external_scheduler/wrangler.toml`: Worker 이름·진입점. **초기 상태에서는 `crons = []`, `DISPATCH_ENABLED = "false"`**이므로 운영 실행이 시작되지 않는다.
- `external_scheduler/watchdog.test.mjs`: 오프라인 안전성 검증 및 POST 차단 테스트.
- `PREFLIGHT_ENABLED=true`는 실제 GitHub 인증키를 사용해 읽기 요청만 진행하며, 배포 승인 없이도 실행 가능 여부를 진단한다.
- `external_scheduler/package.json`: 외부 런타임 의존성이 없는 테스트 설정.
- `.github/workflows/bridge-stability-qa.yml`: PR마다 `node --test external_scheduler/watchdog.test.mjs` 수행.

## 운영 연결을 준비할 때의 필수 체크
1. GitHub의 `thefruitgrove/bridgebrand` 전용 **fine-grained PAT** 또는 동등한 최소권한 GitHub App 토큰을 준비한다. 접근 범위는 해당 저장소 하나로 제한하고 GitHub Actions 조회(Read)·워크플로우 실행 요청(Write)에 필요한 최소 권한만 사용한다. **토큰 값을 채팅·GitHub·Worker 소스·로그에 기록하지 않는다.**
2. 기존 Cloudflare 운영 계정에 로그인하여 **별도의** `bridge-external-watchdog` Worker를 준비한다. 기존 BRIDGE Pages/Workers/도메인 및 배포 훅을 변경하지 않는다. Worker의 필수 Secret 이름은 `GH_DISPATCH_TOKEN`이다.
3. **동일한 코드, 동일한 토큰으로 사전 검증**한다. 인증된 GitHub API에 대한 읽기 권한, 공개 스냅샷 다운로드, 호출 대상 워크플로우 ID, GitHub 사전검사 결과를 확인한다. 첫 검사는 `DISPATCH_ENABLED=false`, `PREFLIGHT_ENABLED=true`인 **읽기 전용 사전검증**으로 진행한다. 이 모드에서는 동일한 GitHub 토큰으로 공개 JSON·Actions 실행이력을 실제 조회하지만, 의사결정이 실행 필요(`dispatch`)라고 나오더라도 `dry_run_would_dispatch`로 보고하고 **POST 요청을 하지 않는다**. Cron 비활성 상태에서는 Cloudflare 테스트 기능 또는 로컬 `wrangler dev --test-scheduled`를 통해 예약 핸들러를 수동 호출한다. 실제 실행 없이 로그의 `preflight_failed`, `configuration_error`, `dry_run_would_dispatch`, `published_today` 등 안전 결과를 확인한다. 모의 테스트 통과만으로 실제 API 권한 검증 완료로 간주하지 않는다.
4. 정식 활성화가 승인되고 운영연결 검증이 끝난 경우에만 `[triggers] crons = ["35 22 * * *"]`(UTC 22:35 = 다음 날 07:35 KST)과 `DISPATCH_ENABLED = "true"`를 함께 적용하되 `PREFLIGHT_ENABLED`는 `false`로 되돌린다. 실제 Worker가 활성화되었는지 Cloudflare 관리화면에서 확인한다.
5. 실제 첫 이벤트의 결과가 `published_today`, `existing_active_run`, `already_dispatched_today`, `collection_succeeded`, `recovery_succeeded`, `dispatched` 중 하나인지 기록한다. `dispatched`인 경우 GitHub main의 `BRIDGE Daily Pipeline` 수동 실행이 실제 생성됐는지 별도로 확인하고 해당 날짜 400건만 발행됐는지 검증한다.
6. `preflight_failed`, `dispatch_rejected`, `configuration_error` 상태라면 자동 재시도를 하지 않는다. 계정 권한·토큰 갱신·GitHub API 상태를 점검한다. 비밀값은 재출력하지 않는다.
7. 종료하려면 Worker `DISPATCH_ENABLED=false`, `PREFLIGHT_ENABLED=false` 및 `crons=[]`를 적용한다. 기존 GitHub 05:15 정규 수집·06:45 복구·07:15 fallback·09:30 모니터는 그대로 유지된다.

## 중복·오발행 방지
- KST 07:30~10:00 범위에서만 실제 Dispatch가 허용된다. 늦게 실행된 Cron은 당일이 바뀌면 과거 날짜를 요청하지 않는다.
- 저장소 main의 최신 공개 JSON이 `dataStatus=published`, `recordCount=400`, 실제 rankings 400개, 기준일이 당일이면 요청하지 않는다.
- GitHub의 당일 정규 수집 또는 복구가 진행 중이거나 대기 중이면 요청하지 않는다.
- 당일 기존 `workflow_dispatch` 수집 요청이 한 차례라도 존재하면 요청하지 않는다. 예약 정규/복구 실행이 이미 성공했다면 불필요한 재수집을 하지 않는다.
- GitHub API 또는 공개 JSON 확인에 실패하면 **실패 상태로 종료**하며 실행을 요청하지 않는다.
- 모든 실행 요청은 `ref=main`, `inputs.as_of_date=KST 당일`만 사용한다.
- GitHub 수집 workflow의 기존 concurrency 및 원자적 발행·사전 검증은 유지한다.

## 구체적인 한계
- Cloudflare Cron도 클라우드 서비스이므로 **정확한 실행 시각이나 무중단을 보장하지는 않는다.** 다만 GitHub와 독립된 예약 실행 경로를 제공한다.
- 독립적인 일정이 있더라도 GitHub API·GitHub Actions 실행 자체에 장애가 발생하면 수집은 진행할 수 없다.
- Worker의 GitHub 체크와 Dispatch 사이에 GitHub 예약 이벤트가 동시에 생성되는 경쟁 상황은 존재한다. 기존 GitHub concurrency가 실행을 직렬화하지만, 완전한 분산 잠금이나 영구 중복 실행 차단과 동등하지 않다. 이 문제를 확인 없이 '중복 0건 보장'으로 표현하지 않는다.
- 이 저장소에 Worker 코드를 추가하는 것은 Cloudflare 실제 Worker 배포와 다르다. Cloudflare 연결권한과 운영 토큰 상태가 확인되기 전에는 활성화를 완료했다고 주장하지 않는다.
- 오프라인 테스트의 mock 응답은 인위적인 테스트 자료로서 운영 결과에 합산하지 않는다.

## 비용·보안
별도 Worker 사용량과 계정별 요금 조건은 실제 Cloudflare 계정에서 확인해야 한다. 요금제 또는 유료변경을 수반하는 배포는 별도 확인 뒤 진행한다. 인증 Secret을 공개 저장소에 커밋하거나 프런트엔드의 환경변수로 제공하지 않는다.

## 1차 합격 조건
(1) GitHub QA·Node 테스트 통과, (2) PR 병합, (3) Cloudflare Token·배포 권한 확인, (4) 비활성 Worker 사전 검증, (5) 실제 Cron 배포 및 GitHub 실행 연결, (6) 실행 이력과 운영 데이터 기준일 검증. **2까지는 코드 준비, 3~6은 실운영 연결 검증**으로 구분한다.

관련 문서: <https://developers.cloudflare.com/workers/configuration/cron-triggers/> , <https://docs.github.com/en/rest/actions/workflows>.
