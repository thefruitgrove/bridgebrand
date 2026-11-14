"""Brand 2.0 issue-free terminology and responsive *semantic* refinements.

Run at the tail of apply_brand_shell.py after the generated data page is ready.
This never changes any score, measurement, ranking, trust or PDF report content.
"""
from __future__ import annotations

from pathlib import Path

SECTOR_HEADLINES: dict[str, tuple[str, str, str]] = {
    "cpr.html": (
        "CPR — 기업과 공중 사이의 평판을 읽습니다",
        "CPR - 기업과 공중",
        "사이의 평판을 읽습니다",
    ),
    "gov.html": (
        "GOV — 공공기관과 정책 수요자의 접점을 읽습니다",
        "GOV - 공공기관과 정책",
        "수요자의 접점을 읽습니다",
    ),
    "uni.html": (
        "UNI — 대학이 약속하고 경험하게 하는 평판을 읽습니다",
        "UNI - 대학이 약속하고 경험하게",
        "하는 평판을 읽습니다",
    ),
    "star.html": (
        "ENT — 화제의 크기와 지속되는 평판을 나누어 읽습니다",
        "ENT - 화제의 크기와 지속되는",
        "평판을 나누어 읽습니다",
    ),
}


def refine(path: Path, html: str) -> str:
    name = path.name
    if name in SECTOR_HEADLINES:
        old, line1, line2 = SECTOR_HEADLINES[name]
        markup = (
            '<h1 class="bridge-field-headline">'
            f'<span class="bridge-field-line">{line1}</span>'
            f'<span class="bridge-field-line">{line2}</span></h1>'
        )
        if 'class="bridge-field-headline"' not in html:
            needle=f'<h1>{old}</h1>'
            if needle not in html:
                raise ValueError(f"Sector heading unknown: {name}")
            html=html.replace(needle,markup,1)
        html=html.replace("<strong>BRIDGE JOURNAL</strong>","<strong>BRIDGE RESEARCH</strong>")
    if name == "briefing.html":
        html=html.replace(
            "THE RELATIONSHIP JOURNAL / EDITORIAL IMAGE",
            "RELATIONSHIP RESEARCH / EDITORIAL IMAGE",
        )
    if name == "intelligence.html":
        # Regression correction: an escaped source literal was printed as
        # characters backslash+n between two real HTML paragraphs.
        html=html.replace('\\n  <p class="trio-snapshot-meta"', '\n  <p class="trio-snapshot-meta"')
    return html
