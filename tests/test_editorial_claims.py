"""BRIDGE editorial P0 claim protection (offline; no database or network).

Tests text invariants only; passing does not establish browser/PDF readability.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EditorialClaimsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intelligence = (ROOT / "site" / "intelligence.html").read_text(encoding="utf-8")
        cls.briefing = (ROOT / "site" / "briefing.html").read_text(encoding="utf-8")
        cls.report_generator = (ROOT / "site" / "briefing.js").read_text(encoding="utf-8")

    def test_intelligence_hero_does_not_promise_causal_attribution(self):
        self.assertIn("점수와 순위의 변화를</span><span>여섯 영역으로 살펴봅니다.", self.intelligence)
        self.assertNotIn("점수와 순위가 달라진 이유를", self.intelligence)

    def test_premium_service_does_not_promise_unverified_causes(self):
        for html in (self.intelligence, self.briefing):
            self.assertNotIn("사건과 변화 원인을 심층 분석합니다.", html)
            self.assertIn("관측된 변화를 자세히 분석합니다.", html)
        for forbidden in ("변화 원인 해설", "변화 원인, 데이터 의미"):
            self.assertNotIn(forbidden, self.intelligence)

    def test_fixed_trust_grade_is_not_presented_as_selected_entity_grade(self):
        self.assertNotIn("근거 신뢰등급 D는 평판등급이 아닙니다.", self.briefing)
        self.assertIn("근거 신뢰등급은 평판등급이 아닙니다.", self.briefing)

    def test_report_marketing_copy_preserves_explanation_depth(self):
        self.assertIn("각 결과를 어떻게 읽어야 하는지도 함께 안내합니다.", self.intelligence)
        self.assertIn("표와 그래프에서는 어떤 값과 차이에 주목해야 하는지", self.intelligence)
        self.assertNotIn("요약형 보고서", self.intelligence)
        self.assertNotIn("7~10개의 설명 문장", self.intelligence)

    def test_easy_reading_label_is_valid_korean(self):
        css = (ROOT / "site" / "briefing.css").read_text(encoding="utf-8")
        self.assertIn("EASY READ · 먼저 이렇게 이해하세요", css)
        self.assertNotIn("EASY READ Â·", css)

    def test_basic_report_explains_and_guards_missing_history(self):
        basic = self.report_generator.split("function buildBasicPrintReport()", 1)[1]
        self.assertIn("hasNumber(pick.previous_rank)", basic)
        self.assertIn("이전 순위를 확인할 수 없어", basic)
        self.assertIn("hasNumber(pick.score_change)", basic)
        self.assertIn("전일 대비 지수 자료가 없어", basic)
        self.assertNotIn("순위는 ${pick.previous_rank}위에서 ${pick.rank}위", basic)
        self.assertIn("pick.comparison_status==='same_scope'?'동일 범위 비교':'비교 보류'", basic)
        self.assertIn("변화 수치를 제시하지 않고 N/R로 표시", basic)

    def test_basic_report_does_not_confuse_evidence_quality_with_score(self):
        basic = self.report_generator.split("function buildBasicPrintReport()", 1)[1]
        self.assertIn("근거의 충실성은 점수와 별개로", basic)
        self.assertIn("참조 축은 대상별 평가값이 없으므로 낮은 점수의 축으로 분류하지 않습니다.", basic)
        self.assertNotIn("이 고정 샘플은", basic)
        self.assertIn("이 보고서는 ${dateKo(date)} 공개 스냅샷을 기준으로 작성했습니다.", basic)

    def test_data_boundaries_and_public_elements_remain(self):
        for term in ('id="bridgePublicEvidence"', 'id="bridgeActionChecks"', 'id="briefingRadar"'):
            self.assertIn(term, self.briefing)
        self.assertIn("원자료별 점수 기여도는 공개 데이터에 포함되지 않아", self.briefing)
        self.assertIn("해석 범위를", self.intelligence)


if __name__ == "__main__":
    unittest.main()
