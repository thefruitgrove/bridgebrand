"""BES 1.0: page, evidence semantics and visual-layout contracts.

These checks are static safeguards, not a substitute for browser/PDF rendering
or independent expert/user language review. No network or DB access.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Standard29EditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        js = (ROOT / "site" / "briefing.js").read_text(encoding="utf-8")
        cls.js = js
        cls.standard = js.split("function buildPrintReport(){", 1)[1].split(
            "function buildBasicPrintReport(){", 1
        )[0]
        cls.css = (ROOT / "site" / "briefing.css").read_text(encoding="utf-8")

    def test_standard_has_twenty_nine_pages_and_detailed_prose(self):
        self.assertEqual(self.standard.count("pages.push(printPage("), 29)
        for page in range(1, 30):
            self.assertIn("pages.push(printPage(" + str(page) + ",", self.standard)
        self.assertIn("printProse('근거 상태를 먼저 읽는 이유'", self.standard)
        self.assertIn("printProse('이번 보고서가 말할 수 있는 범위'", self.standard)

    def test_charts_show_selected_subject_beyond_top_twenty(self):
        self.assertIn("function printDotPlot(rows,pick)", self.js)
        self.assertIn("pickIndex<20?sorted.slice(0,20)", self.js)
        self.assertIn("omitted ranks are not shown", self.js)
        self.assertIn("printEnglishScoreDistribution(fieldRows,pick)", self.js)
        self.assertIn("printSplitTable(", self.js)

    def test_score_not_confused_with_evidence_or_causation(self):
        self.assertNotIn("높은 축은 현재 근거가 선명한 지점", self.standard)
        self.assertIn("근거의 충실성과 관측 기간은 각 축의 상태와 신뢰등급", self.standard)
        self.assertIn("어느 축의 근거가 더 정확하다거나 특정 부정적 사건", self.standard)
        self.assertIn("참조 상태에는 대상별 유효 평가값이 없어", self.standard)

    def test_visual_layout_has_page_25_and_distribution_guards(self):
        self.assertIn('.print-sheet[data-page="25"].print-type-strategy', self.css)
        self.assertIn('.print-table-split{display:grid', self.css)
        self.assertIn('.print-sheet[data-page="10"] .dot-row', self.css)


if __name__ == "__main__":
    unittest.main()
