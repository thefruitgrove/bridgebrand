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

        self.assertGreaterEqual(len(pages), 28)

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
