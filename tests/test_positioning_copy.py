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
        self.assertIn("근거 신뢰등급", IDENTITY_SECTION)

    def test_hero_copy_retains_data_hooks(self):
        home = (ROOT / "site" / "bridge-v2.html").read_text(encoding="utf-8")
        for data_hook in ('id="v2SearchForm"', 'id="v2SignalCards"', 'href="intelligence.html"'):
            self.assertIn(data_hook, home)
        self.assertIn("Evidence-Based Reputation Intelligence", home)
        self.assertIn("BRIDGE는 그 신호의 근거와 의미를 분석합니다.", home)


if __name__ == "__main__":
    unittest.main()
