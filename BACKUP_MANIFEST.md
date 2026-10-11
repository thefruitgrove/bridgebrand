# BRIDGE 운영 백업 매니페스트

백업 기준일은 2026년 10월 11일이다.

## 운영 식별 정보

- 운영 주체: SignalBridge
- 서비스: BRIDGE Brand Reputation Framework
- 공식 도메인: https://bridgebrand.co.kr
- GitHub: https://github.com/thefruitgrove/bridgebrand
- Supabase 프로젝트 ID: `gorlbfqvyxtdsxgoqinf`
- 공개 도메인: CPR, ENT, GOV, UNI
- 내부 호환 코드: ENT는 데이터베이스에서 STAR로 유지

## 포함 범위

- 전체 웹사이트 소스와 이미지
- CPR, ENT, GOV, UNI 대상 및 기준자료
- BRIDGE 6축 점수 엔진
- 동적 후보 발견과 T100 산출 로직
- 일별, 주별, 전주 대비, 활동량, 누적성과 지표
- Supabase 전체 마이그레이션
- GitHub Actions 일일 자동화
- 테스트와 회귀 검증 코드
- Git 전체 이력 번들
- 시스템 복원 가이드
- BRIDGE 방법론 및 운영 백서 v4

## 백업에 포함하지 않는 항목

- Supabase 서비스 역할 비밀키
- OpenDART API 키
- Cloudflare 배포 훅 URL
- 개인 액세스 토큰

비밀값은 의도적으로 제외했으며 `RESTORE_GUIDE.md`에 재등록 위치가 기록되어 있다.

## 백업 시점 운영 데이터 요약

- 엔터티: 400
- 축 관측값: 1,717
- 랭킹 행: 608
- 원시 수집 항목: 6,106
- 동적 후보: 0
- 신규 통합 지표 행: 0

신규 통합 지표 행은 2026년 10월 11일 첫 운영 실행이 CPR OpenDART 빈 응답으로 중단되어 아직 생성되지 않은 상태였다. 백업 기준 소스에는 이 문제가 개별 대상 재시도와 건너뛰기로 보완되어 있다.

## 무결성

ZIP 최상위의 `CHECKSUMS_SHA256.txt`로 주요 파일의 무결성을 확인한다.

