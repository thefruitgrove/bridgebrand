import unittest
from pathlib import Path

from presentation.editorial_standard import FOOTER_COPY


ROOT = Path(__file__).resolve().parents[1]


class FooterCopyContractTests(unittest.TestCase):
    def test_all_public_pages_use_the_fixed_footer_copy(self):
        pages = []
        for path in sorted((ROOT / "site").rglob("*.html")):
            text = path.read_text(encoding="utf-8")
            if 'class="footer-note"' in text or 'class="footer-method"' in text:
                pages.append(path)
                self.assertIn(FOOTER_COPY, text, str(path.relative_to(ROOT)))

        # The V2 home has its own operator/limitations footer. Enumerate
        # required legacy surfaces instead of equating a page count with coverage.
        covered = {p.relative_to(ROOT / 'site').as_posix() for p in pages}
        self.assertTrue({'cpr.html', 'gov.html', 'uni.html', 'star.html',
                         'trust.html', 'methodology.html', 'subscribe.html'} <= covered)
        for name in ('index.html', 'bridge-v2.html', 'site_fix/index.html'):
            text = (ROOT / 'site' / name).read_text(encoding='utf-8')
            self.assertIn('class="v2-footer"', text, name)
            self.assertIn('Developed and operated by SIGNALBRIDGE.', text, name)
            self.assertIn('class="v2-legal"', text, name)
            self.assertIn('contact.html', text, name)

    def test_retired_footer_wording_does_not_return(self):
        retired = (
            "브랜드와 공중 사이의 평판을 반복 관측",
            "순위는 같은 분야·같은 기준일·같은 공개 범위",
            "결과를 읽을 때는 기준기간",
        )
        for path in sorted((ROOT / "site").rglob("*.html")):
            text = path.read_text(encoding="utf-8")
            for phrase in retired:
                self.assertNotIn(phrase, text, str(path.relative_to(ROOT)))


if __name__ == "__main__":
    unittest.main()
