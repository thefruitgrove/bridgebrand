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

    def test_data_boundaries_and_public_elements_remain(self):
        for term in ('id="bridgePublicEvidence"', 'id="bridgeActionChecks"', 'id="briefingRadar"'):
            self.assertIn(term, self.briefing)
        self.assertIn("원자료별 점수 기여도는 공개 데이터에 포함되지 않아", self.briefing)
        self.assertIn("해석 범위를", self.intelligence)


if __name__ == "__main__":
    unittest.main()
