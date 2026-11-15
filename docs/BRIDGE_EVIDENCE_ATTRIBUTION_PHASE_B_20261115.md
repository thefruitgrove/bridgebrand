# BRIDGE Evidence Attribution 1.0 — Phase B 설계 및 WHAT NEXT 검증 (2026-11-15)

## 1. 목적과 변경 범위
- 정체성: **Reputation is a signal. Evidence makes it meaningful.**
- 개발 브랜치: `bridge-positioning-20261115`.
- 담당 구분: 본 브랜치는 보고서 해석·표시 및 검증 코드만 변경. Work가 수행 중인 발행 계보 실패·DB/JSON 불일치·재발행 문제는 별도 브랜치에서 처리.
- 운영 DB, 점수 엔진, 배포, `main`, `site/data/latest.json`은 수정하지 않음.

## 2. 실제 운영 원장에 확인한 데이터 계약
프로젝트 `bridgebrand-production`의 다음 테이블을 읽기 전용으로 조사함.
- `bridge_axis_observations`: `entity_id, as_of_date, axis, score, status, confidence, coverage, source_families, evidence_count, freshness_days, methodology_version, diagnostics`.
- `bridge_signals`: `id, entity_id, raw_item_id, source_id, axis, signal_type, direction, magnitude, confidence, occurred_at, review_status, rationale, ruleset_version`.
- `bridge_raw_items`: `id, source_id, canonical_url, title, publisher, published_at, collected_at, content_hash`.
- `bridge_scores`: `entity_id, as_of_date, score, confidence_score, trust_grade, axes_used, publish_status, methodology_version, diagnostics`.
- `bridge_rankings`: `entity_id, as_of_date, domain, ranking_type, rank, score, trust_grade, methodology_version, published_at`.

**실제 사례(2026-11-13, CPR-021, 특정 축 관측):**
- B 축: score 93.71, evidence_count 1,109, source_families 2, freshness_days 1; `diagnostics.signal_ids` 배열 1,109개.
- D 축: score 73.64, evidence_count 58, `diagnostics.signal_ids` 58개.
- `diagnostics`의 키: `aggregation, evidence_date, policy_version, signal_ids, source_ids, window_days`.
- D/E 축에서 `aggregation='domain_log_count'` 확인. 따라서 단일 기사 또는 신호가 종합점수를 몇 점 변화시켰는지를 산식·중복·정규화·기존 점수와의 반사실적 계산 없이 단정할 수 없음.
- 단일 대상·단일 날짜의 검토 사례를 전체 400개 대상으로 일반화하면 안 됨.
- `source_families`와 `diagnostics.source_ids`의 의미/산출 기준이 서로 정확히 어떻게 대응하는지는 원본 계산 규칙 확인 전까지 미확정.
- 원문 링크는 저작권·접근권한·민감정보 검토 없이 공개 JSON에 직접 옮기지 않음.

## 3. 현재 구현된 범위
- Phase A: 공개 JSON의 축 상태·근거 기준일·스냅샷 메타만 WHY 섹션/일반 PDF에 연결.
- Phase B-1: WHAT NEXT의 **근거 검증 우선순위**를 규칙 기반으로 구성.
  1. 참조(결측, 부적격) 축: 자료 적격성, 대상 귀속, 수집 실패, 적용 가능성 확인.
  2. 유지 축: 기존 근거의 유효기간 및 새 독립 근거 확인.
  3. 관측 축: 실제 점수가 낮은 축부터 비교 가능한 기간과 자료 범위 확인.
- 이 우선순위는 진단용 **검증 질문의 순서**이며 조직의 문제 심각도, 경영 의사결정 우선순위, 미래 지수 예측이나 인과효과 추정이 아님.
- `site/briefing.js`의 `actionCheckItems`, `actionCheckSummary`, `actionCheckHtml`과 브리핑 화면, 보고서 일부에 반영.
- 테스트: 실제 2026-11-13 공개 JSON의 400개 대상에 대해 전수 규칙 실행. 오류 0건, 평가축 2,400개 중 참조 330·유지 242·관측 1,828. 가장 먼저 점검할 그룹은 참조 209개 대상, 유지 32개 대상, 관측 159개 대상.
- 신규 자동 테스트: `tests/test_evidence_action_rules.js` (Node 내장 테스트, DB 쓰기 없음). GitHub 저장소에 코드를 추가했으나 CI에서 실제 Node 실행은 아직 미확인.

## 4. Evidence Attribution 정량화 전 필수 검증
아래 계약이 성립하지 않으면 개별 신호의 점수 기여도를 공개하지 않음.

1. **입력 집합 고정:** `score_run_id` 또는 동일한 의미의 발행 실행 ID, 평가시점, 산식 버전, 입력 신호 ID 집합과 중복 제거 규칙을 저장.
2. **집계 방식 분리:** `domain_log_count`, 기타 정규화·가중·상한·축간 상호작용의 순서를 재현. 단순 신호 개수/전체 개수는 점수 기여도가 아님.
3. **기여도 정의:** 산식이 선형·가법인 구간에 한해서 정해진 기여도 계산 사용. 비선형 집계는 특정 신호 제외 전후 재산출(leave-one-out) 등 재현 가능한 정의를 마련하되 다른 자료의 영향과 인과효과가 아님을 표시.
4. **전일 대비 분해:** 근거 신규 편입, 만료·제외, 정제 변경, 대상 귀속 변경, 정규화 모집단 변동, 엔진 버전 변경을 분리. 차이가 남으면 '설명되지 않은 잔차'로 남김.
5. **검증:** 축별 재산출값과 DB 공식값 비교, 최소 표본 20개 심층감사, 동일 입력 반복 실행, null/참조값 제외, 400 대상 품질 검사.
6. **공개 정책:** 원문 저작권·개인정보·보안·원장 직접 노출 위험을 심사하고, 공개 가능한 제목·URL만 요약 또는 허용된 링크로 노출. 임의 근거 생성 금지.

## 5. Work 복구 완료 후 연결할 API 제안 (제안, 아직 미구현)
`GET /api/reputation/evidence-summary?entity_id=...&snapshot_id=...` 형태를 **구조 구상**으로 검토할 수 있으나, 기존 프로젝트의 API 스택·권한·배포방식 확인 전 신규 서버/테이블을 생성하지 않는다.

필드 후보:
- `entity_id, domain, snapshot_id, as_of_date, methodology_version, evidence_policy_version`
- `axes:[{axis, state, score, evidence_date, evidence_count, source_family_count, summary_source_types, contribution_status}]`
- `contribution_status: "not_computed"|"verified"`
- 기여도는 `verified` 상태에서만 수치 허용. `not_computed` 시 수치는 null.
- 기존 `axis_status`와 `bridge_axis_observations.status`의 매핑 및 스냅샷과 기준일을 실측 검증한 뒤 발행.
- 발행 원장·새 요약 API·JSON·화면이 동일한 스냅샷 식별자를 가졌을 때에만 화면에 상세 WHY를 활성화.

## 6. 통합 및 배포 보류 사유
- Work가 조사 중인 2026-11-14 계보 검증 실패, 369 eligible/31 shadow와 400 T100, 최신 DB와 JSON의 불일치가 남아 있음.
- JavaScript 구문과 단위 로직의 일부는 함수 수준에서 검증했으나 실제 페이지·PDF 레이아웃·CI 회귀검사는 미완료.
- Work의 운영 브랜치와 병합하지 않았고, 운영 배포하지 않았다.
