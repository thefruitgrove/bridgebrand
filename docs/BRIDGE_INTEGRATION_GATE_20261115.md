# BRIDGE 운영 복구 + 포지셔닝 브랜치 통합 게이트 (2026-11-15)

## 상태
2026-11-15 사용자 전달 Work 보고: DB 11/14 20:28:49 KST 발행은 계보 검증 성공한 선행 실행에서 생성. 이후 과거 축 이력 조회 시 SQLSTATE 57014 시간초과로 JSON 출력 중단. 후속 실행은 정책상 허용된 CPR shadow 31개를 계보 검증이 거부. eligible/shadow CPR 69/31, 다른 3분야 각각 eligible 100. 실제 배포 및 GitHub JSON 정규화 해시 일치, 11/13. 11/15 오전 자동 실행 기록 부재(원인 미확정). 로컬 커밋 4b2e9d1, 신규 테스트 14개 통과·기존 Python 1개/Node 3종 실패. 운영 변경 없음.

## 접근 검증
GitHub 저장소 thefruitgrove/bridgebrand에서 Work 로컬 커밋 4b2e9d1 및 bridge-operational-integrity 브랜치 검색이 실패. 원본 패치의 diff와 테스트 로그를 확인하지 못했으므로 수정의 정당성/회귀 실패 원인/안전성은 **아직 독립검증 불가**.
제품 개발 브랜치 bridge-positioning-20261115는 main 대비 22 commits ahead, 11개 파일 변경, Work가 보고한 운영 브랜치와 통합하지 않음.

## 통합 전 필수 승인 기준
1. Work가 운영 복구 브랜치 및 로컬 커밋을 GitHub에 push하거나 패치·실패 로그·보고서를 공유.
2. 사용자 전달 요약만으로 SQLSTATE 57014 해결 여부를 선언하지 말 것. EXPLAIN (ANALYZE는 실제 과부하 주의), 인덱스·배치·페이징·조회기간을 검토.
3. shadow 허용 정책을 기존 공식 문서와 코드로 확정. 테스트가 이를 허용하도록 조정하되 2축 미만·미관측·비공개 대상의 누출 금지.
4. 발행·export의 동일 스냅샷 식별자, 일치하는 대상 400건(정책 확인 후), 점수·신뢰등급·축 상태 및 날짜 검증. 불일치 시 배포 차단.
5. 기존 Python 1개와 Node 3종의 실패 원인을 각각 기능 결함/환경 의존/기존 기대치 오류로 분류하고 변경 근거·수정 전후 테스트 제시. 검증 게이트를 삭제·무조건 통과시키지 말 것.
6. 11/15 자동작업 트리거 미발생 원인 확인 (스케줄 정의, UTC/KST, workflow 비활성화, 실행 큐 등) 및 별도 기록.
7. 제품 브랜치의 WHAT·WHY·WHAT NEXT 추가 요소 검증: JS syntax, node tests/test_evidence_action_rules.js, python -m unittest tests.test_positioning_copy, PC/모바일 브리핑, PDF 기본/일반/영문 출력 및 페이지 넘침.
8. 두 브랜치를 통합 브랜치에서 병합 및 전체 테스트 후 승인된 최신 스냅샷만 배포. 운영 DB 변경·강제 재발행·배포는 별도 명시적 승인 이후.
9. 원장 보호, 수정 전후 파일 백업, 롤백 명령 및 데이터 백업 확인.
10. 상태를 '코드 수정안', '테스트 성공', '통합 검증', '운영 복구', '배포 정상화'로 각각 분리해 보고.

## 고유 개선사항 보호
- 슬로건: Reputation is a signal. Evidence makes it meaningful.
- BRIDGE Evidence-Based Reputation Intelligence.
- 무료 WHAT, WHY의 근거·신뢰등급 검증 가능.
- WHAT NEXT는 근거 적격성 확인 우선순위와 실제 실무 처방을 구분.
- 원자료 링크·개별 점수 기여도는 검증된 스키마가 없으면 생성하지 않음.

## 통합 대상
제품 브랜치: bridge-positioning-20261115
Work 복구 브랜치: push 후 식별
main/실서비스: 승인 전 불변
