"""No new data pipeline or index; editorial releases only change the view."""
import unittest
from pathlib import Path
from tools.publish_v2_home import render, SITE
from tools.apply_brand_shell import EDITORIAL_PAGES, apply
from tempfile import TemporaryDirectory


class EditorialTests(unittest.TestCase):
    def test_home_is_a_photo_led_editorial_page(self):
        html = render()
        for required in ('v2SearchForm', 'id="v2SignalCards"', 'v2-mag-cover-photo',
                         'v2-mag-photo', 'v2-mag-intel-image', 'bridge-v2-magazine.css',
                         'img/hero_home.jpg', 'img/hero_data.jpg'):
            self.assertIn(required, html)

    def test_magazine_palette_does_not_turn_every_section_into_a_color_card(self):
        css = (SITE/'bridge-v2-magazine.css').read_text(encoding='utf-8')
        for required in ('.v2-mag-cover-photo', '.v2-mag-feature-row',
                         '.v2-field-grid', '@media(max-width:760px)'):
            self.assertIn(required, css)
        self.assertIn('background:#FFFDF7', css)
        self.assertIn('filter:saturate', css)

    def test_all_detailed_pages_have_shared_style_and_wordmark(self):
        css = (SITE/'bridge-v2-editorial.css').read_text(encoding='utf-8')
        self.assertIn('.bridge-editorial .list-hero-photo', css)
        self.assertIn('.bridge-editorial.intel-page .trio-picker', css)
        self.assertIn('.bridge-editorial.briefing-page .briefing-cover', css)
        self.assertGreaterEqual(len(EDITORIAL_PAGES), 13)

    def test_postbuild_hook_is_idempotent(self):
        original = (SITE/'intelligence.html').read_text(encoding='utf-8')
        with TemporaryDirectory() as directory:
            file = Path(directory)/'intelligence.html'
            file.write_text(original, encoding='utf-8')
            apply(file)
            first = file.read_text(encoding='utf-8')
            apply(file)
            self.assertEqual(first, file.read_text(encoding='utf-8'))
            self.assertEqual(first.count('bridge-v2-editorial.css'), 1)
            self.assertIn('bridge-editorial-logo', first)
            self.assertNotIn('bridge-v2-intelligence.css', first)


if __name__ == '__main__':
    unittest.main()
