# BRIDGE 비밀값 등록 지침

비밀값은 ZIP에 저장하지 않는다. 새 운영 환경에서 다음 이름으로 다시 등록한다.

| 이름 | 용도 | 저장 위치 |
|---|---|---|
| SUPABASE_SECRET_KEY | 원장 쓰기와 비공개 테이블 접근 | GitHub Actions Secret |
| DART_API_KEY | 기업 공시와 재무 기준자료 수집 | GitHub Actions Secret |
| CLOUDFLARE_DEPLOY_HOOK | 정적 사이트 재배포 | GitHub Actions Secret |

브라우저에서 사용하는 공개키와 서버 전용 비밀키를 혼동하지 않는다. 서비스 역할 키는 HTML, JavaScript, JSON, 커밋, 문서, 로그에 기록하지 않는다.
