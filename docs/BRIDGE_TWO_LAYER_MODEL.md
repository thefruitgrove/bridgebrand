# BRIDGE 2단 방법론 구조

상태: 확정 원칙  
확정일: 2026-10-20  
적용 순서: UNI → GOV → ENT → CPR

## 1. 1차 공통층

CPR, GOV, UNI, ENT 모두에 동일한 BRIDGE 공통 골격을 적용한다.

- B·R·I·D·G·E 여섯 축
- 근거 원장과 대상·축·날짜 연결
- 동일 사건 중복 제거
- 직접 관측값, 유지값, 추정값, 참조값의 구분
- 신뢰등급과 관측 범위
- 시점, 버전, 정정 이력 관리
- 공통 공개 적격 기준과 재현성 검증

공통층은 분야 간 비교 가능성과 방법론적 일관성을 보장한다.

## 2. 2차 분야별 보완층

공통 철학과 점수 골격은 유지하되 CPR, GOV, UNI, ENT 각각의 관계 특성에 맞는 조작적 정의, 근거 유형, 귀속 규칙, 시간 구조를 보완한다. 분야마다 별개의 지수를 만드는 것이 아니라 공통 골격의 관측 정확도를 높이는 부분 맞춤형 계층이다.

### GOV 확정 보완

- 기능 맥락: 규제·서비스·지원·정책조정·지방행정의 관계 차이를 진단하되 가중치는 임의 변경하지 않는다.
- 경험 경로: 직접 서비스 경험, 제도 경험, 매체 경험, 대리 경험을 구분한다.
- E: 적법성, 절차적 공정성, 설명책임, 의견수렴 및 확인·계획·집행·감사·시정·재발의 생애주기
- R: 국민·주민 참여, 응답성, 상호통제, 의견의 실제 반영
- G: 기관간·민관 협업의 실제 공동 이행; 단순 업무협약은 낮은 강도의 연결 근거로만 기록
- D: 민원·신청·상담·신고·급부·허가·단속 등 직접 또는 의무적 공공서비스 경험
- 보조 진단: 이미지-실적 정합성과 공식 설명-외부 경험 정합성
- 혁신·ESG·전문성은 수상·홍보 표현이 아니라 공개적으로 확인된 행동과 결과가 있을 때만 관계 신호로 인정한다.

### UNI 확정 보완

- R: 신뢰, 만족, 상호성, 불신, 불만, 관계이탈
- I: 대학의 공식 정체성과 외부의 반복 연상 사이의 일치
- E: 사건의 시정, 이행, 회복, 재발이라는 시간 흐름
- B: 독립적 발견과 동일 사건의 반복 전재 구분

### ENT 확정 보완

ENT는 공통 BRIDGE 6축과 공통 가중치·공개 적격 기준을 유지하면서, 팬덤과 일반 공중의 관계 구조, 인기·활동·평판의 경계, 직군별 본업 맥락, 빠른 대상 변화를 2차 보완층에서 해석한다.

```mermaid
flowchart TD
    A["BRIDGE 공통 6축"] --> B["ENT 공통 관계 보완"]
    B --> C["팬·일반공중 분리"]
    B --> D["인기·평판·활동 분리"]
    B --> E["직군별 해석 프로필"]
    C --> F["배우·아이돌·스포츠·인플루언서"]
    D --> F
    E --> F
```

- B: 팬덤 반복확산과 독립적 발견, 팬덤 내부 순환과 일반 공중 확장을 구분한다.
- R: 직접 소통, 응답성, 상호성, 관계 긴장·이탈·회복을 구분한다.
- I: 공식 콘셉트·정체성과 외부 반복 연상 및 팬덤 상징의 관계를 진단한다.
- D: 관심이 시청·관람·예매·구독·구매·투표·팬 프로젝트로 이어지는 행동 경로를 기록한다.
- G: 배우·아이돌/가수·스포츠 스타·인플루언서/방송인의 직군별 본업 맥락을 구분하되, 절대 능력평가로 확대하지 않는다.
- E: 확인·설명·조사·중단·시정·복귀·회복·재발의 시간 흐름과 실제 기부·봉사·사회공헌을 기록한다.
- 외모, 확인되지 않은 사생활, 비공개 산업 네트워크, 루머, 팬덤의 독립 행동은 공개 점수에 직접 귀속하지 않는다.
- ENT B-AN20은 NEW·SURGE·SHIFT 후보를 민감하게 탐지하는 조기관측층으로 운용하고, 화제 발생만으로 높은 평판이나 T100 진입을 단정하지 않는다.
- 신규 후보 탐색은 기존 명단에 한정하지 않으며, 별칭·멤버·소속사·동명이인 귀속과 동일 사건 반복 전재를 검증한다.
- 세부 수집어와 내부 판단 규칙은 지식재산 및 조작 방지를 위해 공개 문서에서 원문 그대로 노출하지 않는다.

### CPR 확정 보완

CPR은 공통 BRIDGE 6축과 공통 가중치·공개 적격 기준을 유지하면서, 기업·제품·계열사·CEO 귀속, 기업성과·활동·평판의 경계, 이해관계자별 관계, 약속과 행동의 일치, 책임의 시간 흐름을 2차 보완층에서 해석한다.

```mermaid
flowchart TD
    A["BRIDGE 공통 6축"] --> B["CPR 관계 보완층"]
    B --> C["주체·사건 귀속 분리"]
    B --> D["성과·활동·평판 분리"]
    B --> E["이해관계자 맥락 분리"]
    C --> F["기업·제품·계열사·CEO"]
    D --> G["실적·홍보·관계반응"]
    E --> H["소비자·임직원·투자자·협력사·지역사회"]
    B --> I["책임의 시간 흐름"]
    I --> J["확인·시정·이행·회복·재발"]
```

- B: 기업발 보도자료·광고와 독립 취재·독립 평가를 구분하고, 동일 자료의 반복 전재와 복수의 독립 발견을 분리한다.
- R: 신뢰·만족·상호성·공정성·헌신과 불신·불만·갈등·이탈을 소비자·임직원·투자자·협력사·지역사회 등 이해관계자 맥락과 함께 기록한다.
- I: 공식 미션·비전·핵심가치 및 브랜드 약속과 실제 행동·외부 반복 연상의 일치 또는 충돌을 진단한다.
- D: 관심과 호감이 추천·재구매·구독·참여 또는 환불·해지·불매·분쟁·거래 중단으로 이어지는 행동 경로를 기록한다.
- G: 품질·서비스·고객지원·보안·공급·혁신의 실제 이행을 업종 맥락에서 기록하되, 절대적 기업 능력·투자 가치 평가로 확대하지 않는다.
- E: 확인·설명·조사·리콜·보상·시정·이행·회복·재발의 생애주기와 환경·인권·공정거래·소비자 보호·준법·윤리·투명성의 실제 이행을 기록한다.
- 기업·제품·계열사·CEO·임직원·협력사 사건은 동일하게 합산하지 않으며, 기업의 공식 책임·의사결정·대응과 직접 연결될 때만 기업에 귀속한다.
- 매출·영업이익·주가·시가총액·판매량·시장점유율·광고량·수상·ESG 선언은 평판점수에 자동 가점하지 않는다.
- NCSI·KCSI·K-BPI·ESG 평가 등 외부 지표는 직접 입력값보다 수렴타당도와 외부 타당화 자료로 우선 사용한다.
- 내부 근거에는 공중, 주체, 출처, 증거 단계, 업종 맥락 태그를 보존하되 세부 수집어와 내부 판단 규칙은 공개하지 않는다.

## 3. 변경 통제

- 분야별 보완은 공통 축의 의미를 훼손하거나 임의의 새 축을 만들지 않는다.
- 내부 가중치, 임계값, 공개 적격 기준은 별도 검증 없이 변경하지 않는다.
- 동일 입력에 대해 기존 결과와 보강 결과를 병행 산출하여 순위·점수 안정성과 설명력 개선을 검증한다.
- 자료가 없거나 수집에 실패한 값을 추정하여 채우지 않는다.
- 분야별 보완 근거는 원장부터 점수, 공개 JSON, 화면까지 추적 가능해야 한다.
- 보완층의 효과는 구성타당도, 변별타당도, 수렴타당도, 사건타당도, 강건성, 결측 편향, 귀속 정확도, 시간 안정성으로 검증한다.

## 4. 향후 문서화 의무

사용자가 백서, 운영 매뉴얼 또는 검증 프레임워크의 상세 개정을 요청하면 다음 내용을 반드시 포함한다.

1. 공통층과 분야별 보완층의 목적 및 경계
2. 분야별 공중 범위와 조작적 정의
3. 수집 가능한 근거와 제외 기준
4. 원장 기록 및 중복·귀속 처리
5. 점수 반영 여부와 변경 통제
6. 보강 전후 병행 검증 절차
7. 공개 가능한 설명과 비공개 지식재산의 경계
8. 한계, 정정, 버전 및 재현성 관리

## Weekly six-axis observability contract — effective 2026-W43

The two-layer model is operationally complete only when every active entity and
each B·R·I·D·G·E axis is checked during the Monday-Sunday week. A check does
not force a score. It produces one auditable internal state:

- O (new observation): new valid evidence was measured during the week.
- M (verified maintenance): prior evidence was rechecked and remains valid.
- R (confirmed reference): collection completed but no valid entity-level
  evaluation value was available. The display reference is excluded from score
  and rank.
- F (collection failure): collection or attribution verification was not
  completed. F is an operating defect, not evidence about reputation.

Weekly collection completion and score coverage are different measures. A week
may be collection-complete at 6/6 while only 5/6 axes are score-available.
Reference never becomes a neutral score merely because the calendar closes.

Consecutive R states trigger internal remediation: supplementary-source search
at two weeks, attribution/alias review at three weeks, operational-definition
review at four weeks, and measurement-design review at six weeks. Weekly and
monthly reporting must retain axis coverage alongside level indices.
