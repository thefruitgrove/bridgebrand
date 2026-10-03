# -*- coding: utf-8 -*-
"""
BRIDGE 2기 엔진 — "내부자 시각" 비변동성 축 확장 모듈
=========================================================

출처: 박재현(2023), "기업의 평판과 가시성 및 ESG(Environment, Social,
Governance) 성과", 연세대학교 대학원 박사학위논문.

이 논문의 변수 설계(내부평판=잡플래닛, 외부평판=사람인 찜하기,
ESG등급 7점 척도 변환)를 BRIDGE의 6축 체계에 이식한다.

왜 이게 N/R 문제를 실제로 줄이는가
------------------------------------
지금까지 BRIDGE의 비변동성 실측은 "뉴스에 논란이 있어야" 점수가 나왔다.
그런데 잡플래닛 점수·ESG 등급·사람인 찜하기 수는 논란과 무관하게
"거의 모든 상장기업에 항상 존재하는 숫자"다. 즉 이번 확장은 근거가
있을 때만 채워지는 축(R축 등)과 달리, 대상만 있으면 거의 항상 채울 수
있는 축이다 — N/R을 줄이는 데 구조적으로 유리하다.

주의: 이 세 지표는 "논란 감지"가 아니라 "상시 존재하는 상태값"이므로,
44~45장의 R(반응)축 공식(귀속×심각도×시간가중치)과는 성격이 다르다.
이 모듈은 그 공식을 대체하지 않고, I·E·B축에 보조/대체 데이터를
공급하는 별도 트랙이다.
"""


def public_eval_to_axis(grade: str) -> float:
    """공공기관 경영평가 등급(S/A/B/C/D/E) → E(책임·지속)축 0~100.
    6단계 균등 매핑: S=100, A=80, B=60, C=40, D=20, E=0."""
    scale = {"S": 100.0, "A": 80.0, "B": 60.0, "C": 40.0, "D": 20.0, "E": 0.0}
    g = str(grade).strip().upper()
    if g not in scale:
        raise ValueError(f"알 수 없는 경영평가 등급: {grade}")
    return scale[g]


def esg_to_e_axis(esg_grade: str) -> float:
    """
    E(책임·지속)축 — ESG 등급을 0~100으로 변환.

    논문 원 척도: S=7, A+=6, A=5, B+=4, B=3, C=2, D=1 (7단계)
    BRIDGE 0~100 척도로 재변환: (원점수-1)/(7-1) * 100
    즉 S등급=100, D등급=0.

    한국ESG기준원(KCGS)이 매년 발표하는 등급을 그대로 쓴다 — 신뢰계수
    표(21.2절) 기준으로도 뉴스 매체 등급(0.55~0.85)보다 상위인
    "정부/준정부 공식 평가"(국민연금·중대재해 사례처럼 0.9급)로 취급한다.
    """
    scale = {"S": 7, "A+": 6, "A": 5, "B+": 4, "B": 3, "C": 2, "D": 1}
    if esg_grade not in scale:
        raise ValueError(f"알 수 없는 ESG 등급: {esg_grade}")
    raw = scale[esg_grade]
    return round((raw - 1) / (7 - 1) * 100, 1)


def jobplanet_to_i_axis(score_out_of_5: float) -> float:
    """
    I(정체성)축 — 잡플래닛 기업만족도 총점(1.0~5.0)을 0~100으로 변환.

    (점수-1)/(5-1) * 100. 3.0점(중간값)이 50점이 되도록 설계.
    """
    if not (1.0 <= score_out_of_5 <= 5.0):
        raise ValueError("잡플래닛 점수는 1.0~5.0 범위여야 함")
    return round((score_out_of_5 - 1) / (5 - 1) * 100, 1)


def saramin_to_b_axis_aux(interest_count: int, reference_max: int = 50000) -> float:
    """
    B(도달)축 보조지표 — 사람인 "관심기업 등록"(찜하기) 수를 로그변환.

    39~40장에서 이미 쓴 로그변환 원리(순위/카운트가 클수록 완만해짐)를
    절대 카운트에도 그대로 적용. reference_max는 대형 인기기업 기준 근사치
    (실제 최댓값 확인 시 갱신 필요 — 현재는 잠정치).

    주의: 이건 "일반 소비자의 관심"이 아니라 "구직자의 관심"이다. B축
    본래 정의(대중 노출)와 모집단이 다르므로, 독립된 B축이 아니라
    "B축 보조지표"로 별도 표기해야 한다 — 직접 합산 금지.
    """
    import math
    if interest_count <= 0:
        return 0.0
    val = 100 * math.log(interest_count + 1) / math.log(reference_max + 1)
    return round(min(100, val), 1)


def rank_to_b_axis(rank: int, total: int = 100) -> float:
    """
    B(도달)축 — 시가총액(또는 동급 규모지표) 순위를 로그변환.

    39~40장에서 확립한 로그변환 원리(QS순위·멜론차트와 동일 논리)를
    '대상선정에 이미 쓰인 규모 데이터'에 재적용한 것 — 추가 검색 없이
    도메인 전체(예: CPR 100개)에 즉시 적용 가능하다는 것이 핵심 이점이다.

    도메인별 매핑 예시:
      CPR: 시가총액 순위 (대상선정에 이미 사용한 데이터)
      GOV: 예산 규모 순위 또는 소관 정책대상 인구 순위
      UNI: 재학생 수 순위 (대학알리미 공시)
      ENT: 공식 SNS 팔로워/구독자 순위

    [2026-09 결함 수정] 원래 공식 100×(1−log(rank)/log(total+1))은 rank=1일 때
    log(1)=0이 되어 항상 정확히 100점(만점)을 산출하는 경계값 결함이 있었다
    (손흥민 MLS 어시스트 1위 사례에서 발견, 매뉴얼 제6부·제9부 참고). 이를
    고치기 위해 순위에 0.5를 더한 half-rank 보정을 적용한다 — 순위가 1위여도
    "0.5등과 1.5등 사이 어딘가"로 취급해, log(0.5)라는 음수·미정의 상황을
    피하면서도 1위가 정확히 만점이 되는 것을 막는다. 이 보정으로 1위의 상한은
    총 모집단 규모에 따라 대략 91~92점 선에서 형성된다.
    """
    import math
    if rank < 1 or rank > total:
        raise ValueError(f"순위는 1~{total} 범위여야 함")
    return round(100 * (1 - math.log(rank + 0.5) / math.log(total + 1.5)), 1)


def build_insider_view_case(entity_name, esg_grade=None, jobplanet_score=None,
                              saramin_count=None, evidence=None):
    """
    세 지표를 모아 REAL_PILOT_CASES 형식의 '내부자 시각' 항목을 만든다.
    R축(반응)은 이 트랙의 대상이 아니므로 None으로 둔다 — 뉴스 기반
    R축 실측과 이 모듈의 결과는 병렬로 존재하되 서로 다른 근거를 쓴다.
    """
    dims = {"B": None, "R": None, "I": None, "D": None, "G": None, "E": None}
    notes = []
    if esg_grade:
        dims["E"] = esg_to_e_axis(esg_grade)
        notes.append(f"E(책임·지속) = ESG {esg_grade}등급 → {dims['E']}점 "
                      f"(공식: (등급점수-1)/6*100)")
    if jobplanet_score:
        dims["I"] = jobplanet_to_i_axis(jobplanet_score)
        notes.append(f"I(정체성) = 잡플래닛 {jobplanet_score}점 → {dims['I']}점 "
                      f"(공식: (점수-1)/4*100)")
    if saramin_count:
        b_aux = saramin_to_b_axis_aux(saramin_count)
        notes.append(f"B(도달) 보조지표 = 사람인 관심기업 {saramin_count}건 → "
                      f"{b_aux}점(로그변환, 구직자 모집단 — 참고용, 정식 B축 아님)")

    filled = [v for v in dims.values() if v is not None]
    score = round(sum(filled) / len(filled), 1) if filled else None

    return {
        "week": "비변동성 데이터 기준(내부자 시각 트랙) — 특정 시점 스냅숏",
        "method": "비변동성-내부자시각",
        "dims": dims,
        "score": score,
        "trust": "D",
        "revision_note": None,
        "evidence": evidence or [],
        "formula_notes": notes,
        "limitations": [
            "이 항목은 R(반응)축 논란 실측과 다른 트랙 — 직접 비교/합산 금지",
            "잡플래닛·사람인 데이터는 특정 스냅숏 시점 기준 — 주기적 갱신 필요",
            "ESG 등급은 연 1회 발표라 갱신 주기가 김(39장 QS순위와 유사한 성격)",
        ],
    }


def merge_insider_view(existing_dims: dict, esg_grade=None, jobplanet_avg=None,
                         jobseeker_views=None, jobseeker_reference_max=300000):
    """
    기존 뉴스기반 dims(6축 dict)에 '내부자 시각' 트랙(E·I·B보조)을 병합한다.

    병합 규칙 (설계 근거는 모듈 docstring 및 백서 논의 참고):
      - E(책임·지속): ESG 등급이 존재하면 항상 대체(replace). 뉴스 기반 E 추정치보다
        한국ESG기준원 등 제3자 공식평가가 신뢰계수상 상위 자료원이기 때문.
      - I(정체성): 잡플래닛 점수가 존재하면 항상 대체(replace). 조직 구성원의 직접
        평가가 뉴스에서 추론한 I축 추정치보다 근거가 직접적이기 때문.
      - B(도달): 원래 값을 그대로 유지한다. 구직플랫폼 조회수는 '구직자'라는 다른
        모집단의 관심도라 일반 소비자 노출(B축 정의)과 다르다 — 절대 덮어쓰지 않고
        별도 'B_aux' 키에 각주로만 병기한다.
      - D·G축은 이 트랙의 대상이 아니므로 손대지 않는다.

    반환: (병합된 dims, 적용 로그 문자열 리스트)
    """
    dims = dict(existing_dims)
    log = []

    if esg_grade:
        old = dims.get("E")
        dims["E"] = esg_to_e_axis(esg_grade)
        log.append(f"E축: {old} → {dims['E']} (ESG {esg_grade}등급으로 대체)")

    if jobplanet_avg:
        old = dims.get("I")
        dims["I"] = jobplanet_to_i_axis(jobplanet_avg)
        log.append(f"I축: {old} → {dims['I']} (잡플래닛 평균 {jobplanet_avg}점으로 대체)")

    if jobseeker_views:
        dims["B_aux"] = saramin_to_b_axis_aux(jobseeker_views, jobseeker_reference_max)
        log.append(f"B_aux(참고, 원 B값 유지): {dims['B_aux']} "
                    f"(구직플랫폼 조회수 {jobseeker_views:,}회, 모집단 다름 — 병합 안 함)")

    filled = [v for k, v in dims.items() if k != "B_aux" and v is not None]
    new_score = round(sum(filled) / len(filled), 1) if filled else None
    log.append(f"종합점수(단순평균, B_aux 제외) = {new_score}")

    return dims, new_score, log


if __name__ == "__main__":
    # 자체 검증
    assert esg_to_e_axis("S") == 100.0
    assert esg_to_e_axis("D") == 0.0
    assert esg_to_e_axis("B+") == 50.0
    assert jobplanet_to_i_axis(3.0) == 50.0
    assert jobplanet_to_i_axis(5.0) == 100.0
    print("자체 검증 통과")

    # 병합 실사례 재현
    print("\n--- SK하이닉스 ---")
    d, s, log = merge_insider_view(
        {"B": 85, "R": 55, "I": 70, "D": None, "G": 50, "E": 65},
        esg_grade="A+", jobplanet_avg=21.11/5, jobseeker_views=253000)
    print(d, s); [print(" ", l) for l in log]

    print("\n--- NAVER ---")
    d, s, log = merge_insider_view(
        {"B": 90, "R": 65, "I": 72, "D": 68, "G": 70, "E": 60},
        esg_grade="A+", jobplanet_avg=20.40/5)
    print(d, s); [print(" ", l) for l in log]

    print("\n--- 현대차 ---")
    d, s, log = merge_insider_view(
        {"B": None, "R": 94.1, "I": None, "D": None, "G": None, "E": None},
        esg_grade="A+", jobplanet_avg=19.92/5, jobseeker_views=56000)
    print(d, s); [print(" ", l) for l in log]
