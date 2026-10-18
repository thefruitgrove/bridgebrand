#!/usr/bin/env python3
"""Reapply the approved brand shell after deterministic site generation.

The daily pipeline rebuilds site/*.html from build.py. This post-build step keeps
presentation-only navigation and wordmark changes stable without touching the
scoring engine, data exports, article bodies, or publication rules.
"""
from pathlib import Path
import re

SITE = Path(__file__).resolve().parents[1] / "site"
WORDMARK = (
    '<a class="logo brand-logo-static" href="index.html" aria-label="SIGNALBRIDGE">'
    '<img class="brand-wordmark-image" src="assets/signalbridge-wordmark.svg?v=20261018-1" '
    'alt="SIGNALBRIDGE"></a>'
)
FOOTER_WORDMARK = (
    '<span class="logo brand-logo-static" aria-label="SIGNALBRIDGE">'
    '<img class="brand-wordmark-image" src="assets/signalbridge-wordmark.svg?v=20261018-1" '
    'alt="SIGNALBRIDGE"></span>'
)
PRIMARY_PUBLICITY = '<div class="mm-group"><a href="publicity.html">PUBLICITY</a></div>'
THIS_WEEK = '<div class="mm-group"><a href="this-week.html">THIS WEEK</a></div>'

def apply(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    updated = text
    updated = updated.replace(
        '<a class="logo" href="index.html">SIGNALBRIDGE</a>', WORDMARK
    )
    updated = updated.replace(
        '<span class="logo">SIGNALBRIDGE</span>', FOOTER_WORDMARK
    )
    updated = re.sub(
        r'\s*<a href="publicity\.html" class="mm-util">PUBLICITY</a>',
        "",
        updated,
    )
    if PRIMARY_PUBLICITY not in updated and THIS_WEEK in updated:
        updated = updated.replace(THIS_WEEK, THIS_WEEK + PRIMARY_PUBLICITY, 1)
    updated = re.sub(
        r'style\.css\?v=[^"\']+',
        'style.css?v=20261018-mobilebrand2',
        updated,
    )
    updated = re.sub(
        r'script\.js\?v=[^"\']+',
        'script.js?v=20261018-mobilebrand2',
        updated,
    )
    updated = updated.replace("VOL. 01 — WEEK", "VOL. 02 — WEEK")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False

def main() -> None:
    files = sorted(SITE.glob("*.html")) + sorted((SITE / "site_fix").glob("*.html"))
    changed = [str(path.relative_to(SITE.parent)) for path in files if apply(path)]
    print(f"brand shell applied to {len(changed)} generated pages")

if __name__ == "__main__":
    main()
