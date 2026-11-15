"""Regression guards for BRIDGE 2.0 positioning copy.

Presentation-only. Does not import the scoring engine or read live data.
Run: python -m unittest tests.test_positioning_copy -v
"""
import unittest
from pathlib import Path

from presentation.public_copy import ABOUT, INDEX, AXIS_ROWS
from tools.apply_brand_shell import IDENTITY_SECTION, PUBLIC_PRINCIPLES

ROOT = Path(__file__).resolve().parents[1]


class TestBridgePositioningCopy(unittest.TestCase):
    def test_six_distinct_axes_remain_defined(self):
        self.assertEqual([item[0] for item in AXIS_ROWS], list("BRIDGE"))
        self.assertIn("실제 접점", INDEX)
        self.assertIn("신뢰등급", INDEX)

    def test_what_why_what_next_set_boundaries(self):
        for name in ("WHAT", "WHY", "WHAT NEXT"):
            self.assertIn(name, INDEX)
            self.assertIn(name, ABOUT + IDENTITY_SECTION)
        self.assertIn("인과관계의 입증은 아닙니다", INDEX)
        self.assertIn("관리 후보", INDEX)

    def test_brand_identity_and_public_trust(self):
        self.assertIn("Evidence-Based Reputation Intelligence", PUBLIC_PRINCIPLES)
        self.assertIn("Evidence makes it meaningful.", PUBLIC_PRINCIPLES)
        self.assertIn("신뢰등급", IDENTITY_SECTION)

    def test_hero_copy_retains_data_hooks(self):
        home = (ROOT / "site" / "bridge-v2.html").read_text(encoding="utf-8")
        for data_hook in ('id="v2SearchForm"', 'id="v2SignalCards"', 'href="intelligence.html"'):
            self.assertIn(data_hook, home)
        self.assertIn("Evidence-Based Reputation Intelligence", home)
        self.assertIn("BRIDGE는 그 신호의 근거와 의미를 분석합니다.", home)


    def test_briefing_does_not_promote_missing_values_to_zero(self):
        script = (ROOT / "site" / "briefing.js").read_text(encoding="utf-8")
        self.assertIn("hasNumber=(v)=>v!==null&&v!==undefined&&v!==''", script)
        self.assertIn("num=(v,d=2)=>hasNumber(v)", script)
        self.assertIn("signed=(v)=>hasNumber(v)", script)
        self.assertIn("['observed','maintained'].includes(e.axis_status[a])", script)
        self.assertIn("!hasNumber(e.score_change)?'delta-flat'", script)
        self.assertIn("!hasNumber(e.wow_delta)?'delta-flat'", script)
        self.assertIn("hasNumber(pick.previous_rank)?", script)

    def test_existing_report_action_and_evidence_sections_preserved(self):
        script = (ROOT / "site" / "briefing.js").read_text(encoding="utf-8")
        for fragment in ("printEvidence(pick)", "ACTION PRIORITIES", "근거 지도와 해석 한계",
                         "nextQuestions", "buildPrintReport()"):
            self.assertIn(fragment, script)


    def test_public_evidence_metadata_is_traceable_but_not_invented(self):
        js = (ROOT / "site" / "briefing.js").read_text(encoding="utf-8")
        html = (ROOT / "site" / "briefing.html").read_text(encoding="utf-8")
        snapshot = __import__("json").loads((ROOT / "site" / "data" / "latest.json").read_text(encoding="utf-8"))
        row = snapshot["rankings"][0]
        self.assertIn("id=\"bridgePublicEvidence\"", html)
        self.assertIn("renderPublicEvidence(pick)", js)
        self.assertIn("e.axis_evidence_dates?.[a]", js)
        self.assertIn("evidenceAxisCompact(pick)", js)
        self.assertIn("개별 원자료 ID·원문 링크·자료별 점수 기여도", js)
        self.assertIn("snapshotId", snapshot)
        self.assertIn("axis_evidence_dates", row)
        self.assertNotIn("score_contributions", row)


    def test_action_checks_are_evidence_gated(self):
        script = (ROOT / "site" / "briefing.js").read_text(encoding="utf-8")
        html = (ROOT / "site" / "briefing.html").read_text(encoding="utf-8")
        for fragment in ("function actionCheckItems(e)", "function actionCheckSummary(e,maxItems=3)",
                         "function actionCheckHtml(e,maxItems=3)", "priority={reference:0,maintained:1,observed:2}",
                         "actionCheckCompact(pick)", "escEvidence(v.question)"):
            self.assertIn(fragment, script)
        self.assertIn('id="bridgeActionChecks"', html)
        self.assertIn("이 목록은 데이터의 적격성 및 검증 필요성에 따른 점검 순서", script)


if __name__ == "__main__":
    unittest.main()
