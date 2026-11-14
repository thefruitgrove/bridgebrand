"""Offline release gates for reversible BRIDGEBRAND 2.0 homepage."""
import unittest
from html.parser import HTMLParser
from pathlib import Path

from tools.publish_v2_home import render, SITE


class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            if d["id"] in self.ids:
                raise ValueError("Repeated HTML id: " + d["id"])
            self.ids.add(d["id"])
        if tag == "a" and "href" in d:
            self.links.append(d["href"])


class BridgeV2Tests(unittest.TestCase):
    def test_source_structure_and_real_handoff(self):
        html = render()
        doc = Structure()
        doc.feed(html)
        for element in ("v2SearchForm", "v2SearchInput", "v2SearchResults",
                        "v2SignalCards", "v2MenuToggle", "v2MobileMenu"):
            self.assertIn(element, doc.ids)
        self.assertIn("intelligence.html", doc.links)
        self.assertIn("index.html", doc.links)
        self.assertNotIn("bridge-v2.html", doc.links)
        self.assertIn("naver-site-verification", html)

    def test_mobile_and_accessibility(self):
        css = (SITE / "bridge-v2.css").read_text(encoding="utf-8")
        js = (SITE / "bridge-v2.js").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:760px)", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn('aria-expanded', js)
        self.assertIn("data/latest.json", js)
        self.assertIn("intelligence.html?", js)
        self.assertIn("data.dataStatus!=='published'", js)
        self.assertIn("replaceChildren", js)

    def test_no_index_mutation_in_client(self):
        js = (SITE / "bridge-v2.js").read_text(encoding="utf-8")
        self.assertNotIn("/rest/v1/", js)
        self.assertNotIn("SUPABASE_SECRET_KEY", js)
        self.assertNotIn("methodology_version=", js)


if __name__ == "__main__":
    unittest.main()
