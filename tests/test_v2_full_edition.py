"""BRIDGEBRAND 2.0 structural release regression suite.
Never recalculate reputation or mutate official data in these tests.
"""
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.apply_brand_shell import apply
from tools.apply_v2_editorial_layout import compose, SECTORS
from tools.publish_v2_home import SITE


class IndexIDs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = {}
    def handle_starttag(self, tag, attrs):
        ident = dict(attrs).get("id")
        if ident:
            self.ids[ident] = self.ids.get(ident, 0) + 1


def composed(name):
    original = (SITE / name).read_text(encoding="utf-8")
    with TemporaryDirectory() as d:
        p = Path(d) / name
        p.write_text(original, encoding="utf-8")
        apply(p)
        first = p.read_text(encoding="utf-8")
        apply(p)
        assert first == p.read_text(encoding="utf-8"), name + ": non-idempotent"
        return original, first


class EditionTests(unittest.TestCase):
    def test_all_six_stages_and_pdf_interface_are_preserved(self):
        original, html = composed("briefing.html")
        for stage in range(1, 7):
            self.assertEqual(len(re.findall(r'data-stage-panel="' + str(stage) + r'"', html)), 1)
        self.assertEqual(html.count('bridge-v2-edition-full.css'), 1)
        self.assertIn('class="bridge-guide-spread"', html)
        self.assertIn('class="bridge-chapter-banner bridge-chapter-position"', html)
        self.assertIn('class="bridge-axis-editorial"', html)
        self.assertIn('class="bridge-publicity-spread"', html)
        self.assertIn('class="bridge-report-folio"', html)
        for required in (
            "fieldPulseList", "fieldPulseBars", "fieldPulseLead",
            "positionRows", "briefingRadar", "pairGrid", "pairPriority",
            "publicityHeadline", "publicityBody", "reportId",
            "printReportDocument", "savePdf", "previewPdf",
            "prevStage", "nextStage", "trialConversion"
        ):
            self.assertIn('id="' + required + '"', html, required)
        before=IndexIDs();before.feed(original)
        after=IndexIDs();after.feed(html)
        self.assertEqual(before.ids, {k:v for k,v in after.ids.items() if k in before.ids})
        self.assertTrue(all(n == 1 for n in after.ids.values()))
        self.assertIn('class="bridge-example-note"', html)
        self.assertNotIn('이번 스냅샷에서는 여섯 축이 모두 산출에 반영됐습니다.', html)

    def test_all_sectors_have_an_actual_reading_sequence(self):
        for path in SECTORS:
            with self.subTest(path=path):
                original, html = composed(path)
                self.assertEqual(html.count('class="bridge-sector-guide"'), 1)
                self.assertEqual(html.count('class="bridge-sector-spread"'), 1)
                self.assertEqual(html.count('id="bridge-index-data"'), 1)
                self.assertIn('intelligence.html?field=', html)
                self.assertEqual(html.count('bridge-v2-edition-full.css'), 1)
                self.assertEqual(original.count('class="rk-row '), html.count('class="rk-row '))
                self.assertEqual(original.count('class="period-selector"'),html.count('class="period-selector"'))
                self.assertEqual(original.count('class="rk-toolbar"'),html.count('class="rk-toolbar"'))

    def test_weekly_keeps_original_cards_and_data(self):
        original, html = composed("this-week.html")
        self.assertEqual(html.count('class="bridge-weekly-feature"'), 1)
        self.assertEqual(original.count('class="twr-col'), html.count('class="twr-col'))
        self.assertEqual(original.count('class="tw-card'), html.count('class="tw-card'))
        self.assertIn('bridge-v2-edition-full.css', html)

    def test_full_css_is_screen_only(self):
        css=(SITE/"bridge-v2-edition-full.css").read_text(encoding="utf-8")
        self.assertIn("@media screen {",css)
        self.assertIn("@media screen and (max-width:760px)",css)
        self.assertNotIn(".print-report",css)
        self.assertNotIn(".print-sheet",css)
        self.assertNotIn("html2canvas",css)

    def test_no_change_to_published_score_or_legacy_report_js(self):
        snapshot=json.loads((SITE/"data/latest.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot.get("dataStatus"), "published")
        self.assertEqual(snapshot.get("recordCount"),400)
        self.assertEqual(len(snapshot.get("rankings",[])),400)
        self.assertTrue((SITE/"briefing.js").is_file())
        self.assertTrue((SITE/"intelligence.js").is_file())


if __name__=="__main__":
    unittest.main()
