"""Regression suite for the user-reviewed BRIDGEBRAND 2.0 polish."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.apply_brand_shell import apply
from tools.apply_v2_refinement import SECTOR_HEADLINES
from tools.publish_v2_home import SITE


def rebuild_twice(name):
    original = (SITE / name).read_text(encoding="utf-8")
    with TemporaryDirectory() as directory:
        file = Path(directory) / name
        file.write_text(original, encoding="utf-8")
        apply(file)
        first = file.read_text(encoding="utf-8")
        apply(file)
        assert first == file.read_text(encoding="utf-8"), name
        return original, first


class V2RefinementTests(unittest.TestCase):
    def test_home_is_an_intelligence_brand_not_a_periodical(self):
        home = (SITE / 'bridge-v2.html').read_text(encoding="utf-8")
        self.assertIn("REPUTATION INTELLIGENCE",home)
        self.assertIn("BRIDGE REPUTATION INDEX",home)
        self.assertIn("EVIDENCE-BASED REPUTATION INTELLIGENCE",home)
        self.assertIn("EVIDENCE MAKES IT MEANINGFUL.",home)
        self.assertNotIn("THE REPUTATION JOURNAL",home)
        self.assertNotIn("ISSUE 02",home)
        self.assertIn("Editorial photography:",home)
        css = (SITE / "bridge-v2-magazine.css").read_text(encoding="utf-8")
        self.assertIn(".v2-footer .v2-photo-credit",css)
        self.assertIn("font:400 12px/1.8",css)

    def test_all_four_sector_titles_have_two_designed_lines(self):
        for name,(old,line1,line2) in SECTOR_HEADLINES.items():
            with self.subTest(name=name):
                before,after=rebuild_twice(name)
                self.assertIn('<h1 class="bridge-field-headline">',after)
                self.assertIn(f'<span class="bridge-field-line">{line1}</span>',after)
                self.assertIn(f'<span class="bridge-field-line">{line2}</span>',after)
                self.assertEqual(after.count('class="bridge-field-line"'),2)
                self.assertNotIn('<h1>'+old+'</h1>',after)
                self.assertIn("BRIDGE RESEARCH",after)
                self.assertIn('bridge-v2-final-polish.css',after)
                self.assertEqual(before.count('id="bridge-index-data"'),after.count('id="bridge-index-data"'))
                self.assertEqual(before.count('class="rk-row '),after.count('class="rk-row '))

    def test_intelligence_is_free_of_visible_literal_linebreaks(self):
        before,after=rebuild_twice('intelligence.html')
        self.assertIn('id="bridgePeerStatus"',after)
        self.assertIn('id="bridgePeerSuggest"',after)
        self.assertNotIn('\\n  <p class="trio-snapshot-meta"',after)
        self.assertEqual(before.count('id="trioPick1"'),after.count('id="trioPick1"'))

    def test_web_briefing_textual_values_and_report_design_are_preserved(self):
        before,after=rebuild_twice('briefing.html')
        self.assertIn('bridge-v2-final-polish.css',after)
        self.assertIn('bridge-v2-report-edition.css',after)
        self.assertEqual(after.count('id="printReportDocument"'),1)
        self.assertEqual(after.count('data-stage-panel='),6)
        self.assertIn('RELATIONSHIP RESEARCH / EDITORIAL IMAGE',after)
        script=(SITE/'briefing.js').read_text(encoding='utf-8')
        self.assertIn('br-cover-title-line',script)
        self.assertIn("br-title-extra-long",script)
        self.assertIn('metric-textual',script)
        self.assertIn('coordinationParticle(b.name)',script)
        self.assertIn('briefing.js?v=20261115-08',after)
        self.assertIn('현재<br>위치',script)
        self.assertIn('무엇을<br>보여주나',script)
        self.assertIn('print-brand-name',script)
        self.assertIn('print-cover-editorial-photo',script)
        self.assertIn('buildPrintReport()',script)
        self.assertIn('window.html2canvas',script)
        self.assertIn('window.jspdf.jsPDF',script)

    def test_pdf_css_is_inherited_and_print_stays_a4(self):
        css=(SITE/'bridge-v2-report-edition.css').read_text(encoding='utf-8')
        for need in ('@media screen', '@media print', '.print-cover-editorial-photo',
                     '.print-brand-name', '#FFFDF7', '#2458F5', '.print-sheet-footer'):
            self.assertIn(need,css)
        briefing=(SITE/'briefing.css').read_text(encoding='utf-8')
        self.assertIn('@page{size:A4 portrait;margin:0}',briefing)
        script=(SITE/'briefing.js').read_text(encoding='utf-8')
        self.assertIn("const total=reportMode==='basic'?18:29",script)
        self.assertIn("const styles=[",script) if "const styles=[" in script else self.assertIn("styles=[...document.querySelectorAll",script)


if __name__=='__main__':
    unittest.main()
