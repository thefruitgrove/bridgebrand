"""Publish the approved BRIDGEBRAND 2.0 design without touching data logic.

Run after build.py (which deterministically regenerates the legacy index).
Keep the legacy homepage separately as a reversible, non-indexed HTML copy.
Both index.html and site_fix/index.html receive the same new public shell.
"""
from __future__ import annotations
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
SOURCE = SITE / "bridge-v2.html"
CSS = SITE / "bridge-v2.css"
JS = SITE / "bridge-v2.js"
TARGETS = (SITE / "index.html", SITE / "site_fix/index.html")
LEGACY = SITE / "legacy-home.html"


def render() -> str:
    for path in (SOURCE, CSS, JS):
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"BRIDGE 2.0 asset missing: {path}")
    latest = json.loads((SITE / "data/latest.json").read_text(encoding="utf-8"))
    rankings = latest.get("rankings")
    if latest.get("dataStatus") != "published" or latest.get("recordCount") != 400 or not isinstance(rankings, list) or len(rankings) != 400:
        raise RuntimeError("Cannot publish 2.0 on an invalid 400-subject snapshot")
    html = SOURCE.read_text(encoding="utf-8")
    must_have = ('id="v2SearchForm"', 'id="v2SignalCards"', 'href="intelligence.html"',
                 'bridge-v2.css', 'bridge-v2.js')
    if not all(fragment in html for fragment in must_have):
        raise RuntimeError("BRIDGE 2.0 critical navigation/asset structure is incomplete")
    html = html.replace('href="bridge-v2.html"', 'href="index.html"')
    # The legacy homepage's Naver ownership metadata must survive the redesign.
    html = html.replace('<meta name="viewport"', '<meta name="naver-site-verification" content="001d16d1e750f0885f28026aafffec97b3e4f93c">\n<meta name="viewport"', 1)
    return html


def publish() -> None:
    html = render()
    home = TARGETS[0]
    if home.exists() and not LEGACY.exists():
        legacy = home.read_text(encoding="utf-8")
        legacy = legacy.replace("<head>", '<head>\n<meta name="robots" content="noindex,nofollow">', 1)
        LEGACY.write_text(legacy, encoding="utf-8")
    for target in TARGETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
    print("BRIDGEBRAND 2.0 home published; legacy homepage preserved separately.")


if __name__ == "__main__":
    publish()
