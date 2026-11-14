# BRIDGEBRAND 2.0
## Brand Identity & Editorial Experience Book

**Edition:** Implementation baseline v2.0 · 2026-11-15  
**Status:** 적용 중 / 최종 UX·운영 승인 전  
**Tagline:** **Reputation is a signal.**  
**Position:** Public-data-based relationship reputation intelligence.

---

### COVER / The signal behind the ranking

![BRIDGE editorial cover image](../site/img/bridge-editorial-cover.webp)

**순위 너머의 관계를 읽다.**

BRIDGEBRAND는 브랜드와 공중 사이의 관계 상태와 그 변화 방향을 공개 근거를 바탕으로 반복 관측한다. 눈에 보이는 순위만으로 판단을 끝내지 않고, 여섯 축과 근거 신뢰등급을 함께 읽는다.

BRIDGE의 브랜드 경험은 두 개의 독립적 엔진이 아니라 **하나의 지수·원장과 두 가지 이용 깊이** 위에 세운다.

| Discover / 발견 | Intelligence / 해석 |
|---|---|
| 누구나 브랜드를 검색하고, 분야별 현재 위치와 주간 변화를 발견한다 | MY PICK과 두 대상을 비교하며, 여섯 축과 6단계 분석으로 해석한다 |
| 첫 화면의 호기심·이해도·진입성을 담당한다 | 심층 보고서·전문 진단·서비스 구성을 담당한다 |
| 사진·큰 편집 제목·짧은 정보 단위 | 정제된 표·차트·근거·전문 문장 |
| 공개 HOME 및 분야별 페이지 | 기존 `intelligence.html`, `briefing.html`, `subscribe.html` |

실제 2.0 구현은 HOME에 Discover 경험을 부여한 것이다. **별도 Discover 홈페이지·별도 엔진은 만들지 않는다.** 필요하면 이후 방문자 행동 데이터를 바탕으로 별도 탐색 경로를 검토한다.

### 01 / Brand personality

**Editorial / Evidence / Clarity / Continuity**

브랜드의 기품은 금색 버튼이나 거대한 숫자 카드를 반복하는 데서 오지 않는다. 사진과 타이포그래피로 사람을 끌어들이고, 데이터로 질문에 답하며, 불확실성을 명확히 표시하는 일관성에서 나온다.

- **사진은 질문을 시작한다.** 인물이 언급된 화보가 특정 평가 결과를 증명하는 것처럼 사용하지 않는다.
- **숫자는 근거를 가진다.** 순위, 점수, 기준일, 대상군, 결측, 신뢰등급은 시각적으로 구별한다.
- **해설은 책임을 가진다.** 사실·추론·해석 범위를 구분하고, 관측 실패를 낮은 평판으로 해석하지 않는다.
- **행동은 단순해야 한다.** 검색 → MY PICK → 비교 대상 → 해석 → 보고서 → 서비스 검토.

### 02 / Colour system

| 용도 | 토큰 | 실제 값 | 사용 원칙 |
|---|---|---|---|
| 기본 지면 | Warm Paper | `#FFFDF7` | 대부분의 일반 본문·화보 여백 |
| 제목·본문 | Deep Ink | `#17191D` | 가독성의 기본 |
| 링크·주요 강조 | Signal Blue | `#2458F5` | 브랜드 시그널·기능·현재 위치 |
| 드문 장식과 보조 강조 | Signal Yellow | `#FFD633` | 시각적 리듬, 소량만 사용 |
| 선택·보조 바탕 | Ice Blue | `#E9F0FF` | 전문 분석 인터랙션 배경 |
| 구분선 | Paper Line | `#D1D7DE` | 편집 그리드의 얇은 선 |

**금지:** 화이트·노랑·파랑 배경을 슬라이드처럼 계속 교대시키지 않는다. 웜화이트에서 연한 노랑 또는 흰 글씨를 사용하지 않는다. 옐로를 긍정평판, 블루를 고평가, 신뢰등급의 의미로 암시하지 않는다. 실측 상승·하락을 색으로 표시할 때에는 브랜드 강조색과 데이터의 방향 의미를 혼동하지 않는다.

### 03 / Typography and hierarchy

- **큰 편집 제목:** `Noto Serif KR` · 일반적으로 500~600 weight, 긴 호흡과 여백을 중시.
- **한글 UI·수치·설명:** `Noto Sans KR`, 숫자 대비 및 모바일 가독성을 우선.
- **영문 호·에디션 표기:** 작은 대문자, 절제된 자간; 텍스트 자체보다 크기와 간격으로 계층을 만든다.
- **접근성 목표:** 일반 글자 WCAG AA 4.5:1 이상, 큰 글자 3:1 이상을 지향한다. 현재 자동검사는 '심각하게 보이지 않는 글자'를 선별하는 운영검사이며 전체 AA 적합 인증은 아니다.
- 작은 본문 글자는 화보 이미지 안에 직접 긴 단락으로 놓지 않는다.

### 04 / Imagery and editorial pacing

![BRIDGE editorial movement image](../site/img/bridge-editorial-rhythm.webp)

**Cover:** 시선을 사로잡는 주제 이미지 1점과 큰 제목.  
**Spread:** 사진과 기사형 해설을 2열로 연결.  
**Data chapter:** 실제 점수·시점·축 상태를 읽을 수 있는 표·차트.  
**Insight:** 논리적 해석과 데이터의 한계를 텍스트로 연결.  
**Report:** 인쇄물처럼 정제된 PDF 화면과 보고서 출력.

![BRIDGE editorial structure image](../site/img/bridge-editorial-structure.webp)

![BRIDGE editorial reading image](../site/img/bridge-editorial-reading.webp)

사진은 사이트의 실제 `site/img/`에 저장된 자산을 사용한다. 외부 화보를 임의로 복제하지 않는다. 모든 사용 이미지의 취득 경로, 저작권, 인물·상표 노출 관련 권리를 확인하고 자료 원장에 남긴다. 출처·권리 상태를 검증하지 않은 이미지를 유료 보고서의 증빙 사진으로 활용하지 않는다.

### 05 / Page architecture

| 화면 | 편집 구성 | 핵심 동작 |
|---|---|---|
| HOME | Cover → 공개 지수 변화 → 분야별 탐색 → Photo Essay → Intelligence | 400개 공개대상 검색 |
| CPR / GOV / UNI / ENT | 분야 Cover → 탐색 안내 → 방법론 소개 → Photo Spread → 조회 기간 → 실측 순위 | 동일 분야 안의 조회 |
| THIS WEEK | 주간 Cover → Photo Spread → 점수 읽는 법 → 분야별 변화 지면 | 기준일·변화 조건 확인 |
| INTELLIGENCE | 분석 Cover → 5단계 이용 여정 → 분야 선택 → MY PICK/COMPARE → 브리핑 | 사용자가 비교 대상 선택 |
| BRIEFING 01 | 공식 정의와 사진 → 예시임을 알리는 수치 → 6축과 근거 | 이해 |
| BRIEFING 02 | 사진 + 장기 지형 설명 → 실제 TOP 20 + 분포 차트 | 배경 |
| BRIEFING 03 | 화보형 질문 → 실제 3대상 비교표 → 등락 해석 | 현재 위치 |
| BRIEFING 04 | 6축·레이더·15개 축 조합 → 근거 한계 | 관계 구조 |
| BRIEFING 05 | 사진과 동적 PUBLICITY 헤드라인 → 기사형 해설 | 대외 커뮤니케이션 |
| BRIEFING 06 | 실제 보고서 정보 → PDF 미리보기·다운로드·인쇄 → 서비스 구성 | 결과 활용 |
| SUBSCRIBE | 서비스 분류 → 4단계 구성 → 저장 상태 고지 | 현재는 결제가 아닌 구성 체험 |

**중요:** 화면 전체에 같은 기본 지면과 타이포그래피를 적용하지만, 순위 데이터와 연구 보고서를 억지로 같은 카드 모양으로 맞추지는 않는다. 구조적 공통성은 여백·모서리·선·사진·수치 규칙에서 나온다.

### 06 / Real customer experience

```text
DISCOVER
브랜드 검색 → 같은 분야 인지
    ↓
SELECT
MY PICK → COMPARE A · COMPARE B
    ↓
UNDERSTAND
실제 순위 · 여섯 축 · 근거 상태
    ↓
ANALYZE
6단계 전문 해석 · PUBLICITY
    ↓
APPLY
PDF 보고서 미리보기 · 저장 · 인쇄
    ↓
CONSIDER
단건·정기 서비스 구성을 검토
```

**반드시 정확하게 표기할 것:** 비교 후보 자동 적용은 '같은 분야·인접 순위'에 한정된 탐색 도움말이지, 사업상의 경쟁관계나 ML 유사도를 판정하는 기능이 아니다. 구매는 아직 개통되지 않았다. 현재 가격·상품 구성은 사업자가 향후 확정할 임시 검증값이다.

### 07 / Data trust and evidence boundaries

- 400개 대상은 CPR·GOV·UNI·ENT 각각 100개 T100 공개대상으로 구성된다.
- 대상군과 기준일이 다른 점수의 직접 비교를 하지 않는다.
- 관측·유지·참조·미관측과 실측값 0을 구별한다.
- 신뢰등급 A–D는 대상의 평판등급이 아니라 **근거 상태**를 나타낸다.
- 여섯 축의 미관측을 강제로 0으로 채우지 않는다.
- 사진·화보·그래프 장식은 평가 근거 자체가 아니며, 근거 원장과 다른 출처임을 명확하게 구분한다.
- 추세는 원자료·계산기간·산출 기준에 의해 뒷받침될 때만 주장한다.

### 08 / System tokens and source of truth

| 유형 | 유지해야 할 파일 |
|---|---|
| HOME | `site/bridge-v2.html`, `site/bridge-v2-magazine.css`, `site/bridge-v2.js` |
| 공통 편집형 지면 | `site/bridge-v2-editorial.css`, `site/bridge-v2-art-direction.css`, `site/bridge-v2-edition-full.css` |
| 실제 분석 리딩룸 | `site/bridge-v2-reading-room.css`, `site/bridge-v2-reading-room.js` |
| 고객 흐름 | `site/bridge-v2-journey.js` |
| 구조 생성 | `tools/apply_v2_editorial_layout.py`, `tools/apply_brand_shell.py` |
| 기존 핵심 엔진 | `site/briefing.js`, `site/intelligence.js`, `site/subscribe.js` |
| 홈페이지 복구 | `site/legacy-home.html`, `tools/publish_v2_home.py` |
| 반복 검증 | `tests/test_v2_editorial.py`, `tests/test_v2_full_edition.py`, 관련 `.github/workflows/bridge-v2-*.yml` |

매일 자동 사이트 빌드 시 `tools/apply_brand_shell.py`가 해당 편집 구조를 반복 적용하며, 같은 지면을 중복 생성하지 않도록 테스트한다.

**변경 금지 영역:** 평가 원장, 수집 규칙, 점수·신뢰등급 산식, 역사 데이터, Entity ID, 6단계 보고서 문서 내용과 PDF 엔진. 디자인 편집은 위 영역을 직접 덮어쓰지 않는다.

### 09 / Quality gates

1. GitHub 배포 성공과 실제 공개 Cloudflare 사이트 응답 성공을 별도로 확인한다.
2. 1440·390·320px에서 내용이 가로로 넘치지 않아야 한다.
3. 6단계 모든 화면이 표시되고 20개 TOP 20·6개 축·15개 조합·실제 3대상 비교 데이터가 유지되어야 한다.
4. Chrome의 실제 화면에서 심각한 저명암 텍스트를 발견하면 배포를 보류하고 수정한다. 이미지 위의 글자는 별도의 육안 검수 대상으로 남긴다.
5. PDF 미리보기, 실제 파일 다운로드, 페이지 수·A4 크기, 기본/영문 보고서의 개별 검증을 실시한다.
6. 서비스 구성은 **미확정 요금·결제 미개통**을 알리고 실제 구매와 구분한다.
7. 정보·사진·상품 명칭의 검증 이력이 브랜드북 개정기록에 남아야 한다.
8. 사용자와 실제 고객의 시각적·사용성 승인 후에만 **2.0 최종 승인** 상태를 부여한다.

### 10 / Release and rollback

- 편집형 HTML 생성: `tools/apply_v2_editorial_layout.py`  
- 공통 적용: `tools/apply_brand_shell.py`  
- 일관성·배포 검사: `.github/workflows/bridge-v2-magazine-release.yml`  
- 전체 사용자 여정 검사: `.github/workflows/bridge-v2-complete-qa.yml`  
- 6단계 명암비 검사: `.github/workflows/bridge-v2-contrast.yml`  
- 실제 PDF 파일 검사: `.github/workflows/bridge-v2-pdf-download-smoke.yml`

기존 홈페이지는 `site/legacy-home.html`로 보존한다. 장애 시 메인·편집 레이어만 이전 상태로 복구하며 **지수 데이터는 롤백 대상에서 제외**한다. 모든 변경은 Git commit을 기준으로 추적한다.

---

**BRIDGE — Reputation is a signal.**  
*Brand system maintained by SignalBridge.*

> 이 문서는 현재 배포된 구현에 대응하는 운영형 브랜드북이다. 상업상품의 최종 가격, 사진의 법적 사용승인, 모든 기기·언어·접근성 테스트와 고객 검증이 끝난 최종 브랜드북으로 오인하지 않는다.
