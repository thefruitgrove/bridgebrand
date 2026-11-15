# BRIDGE 2026-11-15 오전 운영점검 + Evidence Attribution 1.0 Phase A

## 확인된 운영 기준선 (KST 2026-11-15 08:38)
- Supabase 프로젝트: `bridgebrand-production` (Newsgraphy 프로젝트와 혼동 금지).
- `bridge_rankings` 최신 T100: 기준일 `2026-11-14`, CPR/GOV/STAR/UNI 각 100건, 합계 400건. DB `published_at`은 `2026-11-14 11:28:49 UTC` = **2026-11-14 20:28:49 KST**.
- `bridge_scores` 2026-11-14: `eligible` 369건, `shadow` 31건. T100 400건과의 자격 매핑은 **추가 조사 필요**. 400건의 DB 순위 존재가 곧 완전한 공식 공개 자격을 뜻하지 않는다.
- 연결 GitHub 개발 브랜치의 `site/data/latest.json`: `asOfDate=2026-11-13`, `snapshotId=6d88761601ec087fc3aa`, `recordCount=400`. 공개 JSON은 DB의 최신 순위보다 하루 뒤처져 있다.
- `bridge_collection_runs`에서 확인된 2026-11-14 오후 실행의 일부 공식 수집기들은 `success`였으나, 전체 파이프라인 성공 또는 2026-11-15 처리 완료를 뜻하지 않는다.
- `bridge_pipeline_alerts` 최신 기록은 2026-10-11까지. 11월 발행 실패가 이 테이블에 보이지 않는 것은 정상 확인의 증거가 아니다.
- Work가 별도로 보고한 11월 14일 계보 검증 실패 및 기존 회귀검사 실패는 여전히 원인 확인 대상.

## 새 개발 내용: Evidence Attribution 1.0 Phase A
- 기존 `site/briefing.html`의 Relationship Intelligence 분석에 **WHY · 공개 근거 상태와 발행 이력** 섹션 추가.
- `site/briefing.js`의 `evidenceAxisRows`, `evidenceAxisTable`, `evidencePublicationMeta`, `evidenceLimits`, `renderPublicEvidence` 추가.
- 공개 JSON의 `axis_scores`, `axis_status`, `axis_evidence_dates`, `snapshotId`, `generatedAt`, `methodologyVersion` 및 row의 `evidence_policy_version`만 이용한다.
- 일반 PDF의 기존 24쪽에 같은 축별 근거 상태표와 스냅샷 메타데이터를 넣는다. PDF 페이지 수 변경 없음. 기본 PDF·영문 PDF·모바일 표시 검증은 **미완료**.
- **원자료 ID/기여도/인과 원인은 공개 JSON에 없으므로 표시하지 않는다.** 데이터 원장 연결 성공과 정량 기여도 계산 가능은 구분한다.
- 테스트 보호조건을 `tests/test_positioning_copy.py`에 추가했다.
- 개발 브랜치에서 수정했으며 main·운영 DB·공개 JSON·배포는 변경하지 않았다.

## 담당 분리 및 위험 통제
- ChatGPT 개발 브랜치: `bridge-positioning-20261115`, 홈페이지/브리핑 문구·근거 상태 표시만 담당.
- Work: **별도 브랜치** 예: `bridge-operational-integrity-20261115`, 발행 파이프라인·실행 로그·DB/JSON 차이·계보 검증·회귀 검사의 근본 원인 조사 담당.
- Work는 위 개발 브랜치를 수정하거나 임의 병합하지 않는다. 승인 없는 운영 DB 수정/재발행/강제 배포 금지.
- 가장 중요한 현안: DB 최신 `2026-11-14` 대 공개 JSON `2026-11-13` 불일치, 369 eligible 대 400 T100, Work가 보고한 계보 실패 시점 대 DB published_at 후속 기록의 관계.
