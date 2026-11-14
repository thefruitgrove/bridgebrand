"""BRIDGEBRAND 2.0 — idempotent *structural* editorial composition.

This module changes HTML presentation only. In particular:
- Never touch data/latest.json or data history.
- Preserve IDs consumed by briefing.js, intelligence.js and script.js.
- Keep #printReportDocument and print/PDF generation unchanged.
- Avoid adding sample scores, claims of causality or guaranteed paid checkout.
- Called after build.py by tools/apply_brand_shell.py on every daily refresh.
"""
from __future__ import annotations

import re
from pathlib import Path

SECTORS = {
    "cpr.html": ("CPR", "기업", "hero_cpr.jpg", "관계 평판은 기업의 규모보다 공중의 접점에서 읽힙니다."),
    "gov.html": ("GOV", "정부·지자체", "hero_gov.jpg", "정책을 알리는 것과 경험하고 신뢰하는 것은 다른 질문입니다."),
    "uni.html": ("UNI", "대학교", "hero_uni.jpg", "교육·연구의 우열이 아니라 대학과 공중의 관계를 읽습니다."),
    "star.html": ("ENT", "광고모델·인물", "hero_star.jpg", "화제의 크기와 오래 남는 관계를 구분합니다."),
}


def inject_once(html: str, anchor: str, insertion: str, marker: str) -> str:
    if marker in html:
        return html
    if anchor not in html:
        raise ValueError(f"Editorial composition target missing: {anchor[:75]}")
    return html.replace(anchor, insertion + anchor, 1)


def brief(html: str) -> str:
    # A factual warning for sample numbers in the learning guide; the number
    # 78.33 and grade D are ILLUSTRATIONS, not the evaluated target.
    html = html.replace(
        '<section id="sg-reading"><h3>점수와 근거 신뢰등급은 다릅니다</h3>',
        '<section id="sg-reading"><h3>점수와 근거 신뢰등급은 다릅니다</h3>'
        '<p class="bridge-example-note">아래 숫자와 등급은 지표의 읽는 법을 설명하는 예시입니다. '
        '선택 대상의 실제 점수와 신뢰등급은 이후 분석 단계에서 확인합니다.</p>',
        1,
    ) if 'class="bridge-example-note"' not in html else html
    html = html.replace(
        '<small>6 / 6</small><b>산출 범위</b><p>이번 스냅샷에서는 여섯 축이 모두 산출에 반영됐습니다.</p>',
        '<small>6 AXES</small><b>평가 영역</b><p>실제 반영 축은 기준일의 관측·유지·참조 상태에 따라 구분합니다.</p>',
        1,
    )
    html = html.replace(
        '<small>78.33</small><b>당일 관계 평판 수준</b>',
        '<small>78.33</small><b>점수 예시</b>',
        1,
    )
    html = html.replace(
        '<small>D</small><b>근거 신뢰등급</b>',
        '<small>D</small><b>신뢰등급 예시</b>',
        1,
    )
    # Chapter 01: the printed essay and the official methodology, in one
    # actual split composition rather than a decorative extra section.
    if 'class="bridge-guide-spread"' not in html:
        original = (
            '<section id="sg-definition"><h3>BRIDGE의 공식 정의</h3><p class="lead-copy">'
            'BRIDGE 브랜드평판지수는 공개자료와 공중의 관측 신호를 바탕으로 브랜드와 공중 사이의 관계 상태, 구성과 변화 방향을 반복 관측하는 관계 기반 평판지수입니다.'
            '</p></section>'
        )
        replacement = (
            '<section id="sg-definition" class="bridge-guide-spread">'
            '<div class="bridge-guide-copy"><span class="subject-label">THE QUESTION / RELATIONSHIPS</span>'
            '<h3>BRIDGE의 공식 정의</h3><p class="lead-copy">'
            'BRIDGE 브랜드평판지수는 공개자료와 공중의 관측 신호를 바탕으로 브랜드와 공중 사이의 관계 상태, 구성과 변화 방향을 반복 관측하는 관계 기반 평판지수입니다.'
            '</p></div>'
            '<figure class="bridge-guide-photo"><img src="img/bridge-editorial-reading.webp" '
            'alt="관계와 관측의 의미를 상징하는 편집 화보" loading="lazy">'
            '<figcaption>THE RELATIONSHIP JOURNAL / EDITORIAL IMAGE</figcaption></figure>'
            '</section>'
        )
        if original not in html:
            raise ValueError("Briefing chapter 1 definition changed without updating V2 composer")
        html = html.replace(original, replacement, 1)

    # Chapter 03: an editorial scene and the unchanged ranking comparison.
    html = inject_once(
        html,
        '<section id="pr-position">',
        '<figure class="bridge-chapter-banner bridge-chapter-position">'
        '<img src="img/bridge-editorial-structure.webp" alt="다양한 주체 사이의 관계 구조를 표현한 편집 이미지" loading="lazy">'
        '<figcaption><span>03 / POSITION READ</span><b>순위가 보여주는 것.<br>순위가 말하지 않는 것.</b></figcaption>'
        '</figure>',
        'bridge-chapter-position',
    )
    if '<section id="pr-position" class="bridge-data-chapter">' not in html:
        html = html.replace('<section id="pr-position">', '<section id="pr-position" class="bridge-data-chapter">', 1)
    # Chapter 04: 6-axis method becomes a full research spread; the real
    # radar SVG, differences and all 15 pair readings stay in their IDs.
    if 'class="bridge-axis-editorial"' not in html:
        original = '<section id="ri-structure"><h3>BRIDGE 6축 구조 비교</h3>'
        replacement = (
            '<section id="ri-structure" class="bridge-axis-editorial">'
            '<div class="bridge-axis-spread-head"><div><span class="subject-label">'
            '04 / RELATIONSHIP INTELLIGENCE · SIX AXES</span>'
            '<h3>BRIDGE 6축 구조 비교</h3></div><p>'
            '도달(B)·반응(R)·정체성(I)·경험(D)·행동유발(G)·책임과 지속(E)을 '
            '실제 관측 범위와 함께 읽습니다. 빈 축을 0으로 간주하지 않습니다.</p></div>'
        )
        if original not in html:
            raise ValueError("Briefing chapter 4 structure header changed")
        html = html.replace(original, replacement, 1)
    if 'class="bridge-pair-reading-label"' not in html:
        html = html.replace(
            '<section id="ri-combinations">',
            '<div class="bridge-pair-reading-label"><b>INTERPRET THE RELATIONSHIPS</b>'
            '<span>축 조합은 새로운 점수나 인과판정이 아닌 해석의 출발점입니다.</span></div>'
            '<section id="ri-combinations">',
            1,
        )

    # Chapter 05: a full-size magazine story cover. The live headline and
    # standfirst IDs remain in precisely the original section.
    if 'class="bridge-publicity-spread"' not in html:
        html = html.replace(
            '<section class="publicity-story" id="pb-headline">',
            '<div class="bridge-publicity-spread"><section class="publicity-story" id="pb-headline">',
            1,
        )
        original = '</p></section>\n      <section class="publicity-body" id="pb-story">'
        replacement = (
            '</p></section>'
            '<figure class="bridge-publicity-photo"><img src="img/bridge-editorial-rhythm.webp" '
            'alt="소통과 공개적 맥락을 표현한 편집 화보" loading="lazy">'
            '<figcaption>05 / PUBLICITY BRIEF · EDITORIAL IMAGE</figcaption>'
            '</figure></div>'
            '\n      <section class="publicity-body" id="pb-story">'
        )
        if original not in html:
            raise ValueError("Briefing chapter 5 content changed, cannot close photo spread")
        html = html.replace(original, replacement, 1)
    if '<section class="publicity-body bridge-publicity-reading" id="pb-story">' not in html:
        html = html.replace(
            '<section class="publicity-body" id="pb-story">',
            '<section class="publicity-body bridge-publicity-reading" id="pb-story">',
            1,
        )
    # Chapter 06: add an editorial folio to the REAL report with the same
    # PDF/print/download buttons, report IDs, selectors and generation logic.
    if 'class="bridge-report-folio"' not in html:
        html = html.replace(
            '<div class="report-edition">',
            '<div class="bridge-report-folio"><span>BRIDGE REPORT EDITION</span>'
            '<span>ANALYSIS / EVIDENCE / INTERPRETATION</span><span>06 OF 06</span></div>'
            '<div class="report-edition bridge-report-edition">',
            1,
        )
    return html


def sector(html: str, name: str) -> str:
    code, korean, photo, commentary = SECTORS[name]
    if 'class="bridge-sector-guide"' not in html:
        anchor = '<section class="section">\n    <div class="wrap">\n      <div class="pilot-notice">'
        if anchor not in html:
            raise ValueError(f"Sector lead section changed: {name}")
        nav = (
            '<nav class="bridge-sector-guide" aria-label="지수 탐색 순서">'
            f'<span>BRIDGE FIELD EDITION / {code}</span>'
            '<a href="#bridge-index-data"><b>01</b> 지수 탐색</a>'
            f'<a href="intelligence.html?field={code}#trioBeta"><b>02</b> 6단계 분석 체험</a>'
            '<a href="methodology.html"><b>03</b> 평가 기준</a>'
            '</nav>'
        )
        html = html.replace(anchor, nav + '\n  ' + anchor, 1)
    if 'class="bridge-sector-spread"' not in html:
        # Insert AFTER existing field definition, before the date-scoped controls.
        block = (
            '<div class="bridge-sector-spread">'
            '<figure><img src="img/' + photo + '" alt="' + korean +
            ' 관계 분야를 소개하는 편집 이미지" loading="lazy">'
            '<figcaption>FIELD NOTES / ' + code + '</figcaption></figure>'
            '<div class="bridge-sector-spread-copy"><span>HOW TO READ / ' + code + '</span>'
            '<h2>' + commentary + '</h2>'
            '<p>실제 점수·순위·비교기간은 아래 공개 지수에서 확인합니다. '
            '근거가 확인되지 않은 부분을 0점이나 부정적 평판으로 단정하지 않습니다.</p>'
            f'<a href="intelligence.html?field={code}#trioBeta">이 분야의 6단계 브리핑 시작하기 ↗</a>'
            '</div></div>'
        )
        target = '<div class="period-selector"'
        if target not in html:
            raise ValueError(f"Period selector missing: {name}")
        html = html.replace(target, '<span class="bridge-index-anchor" id="bridge-index-data"></span>\n'+block+'\n'+target, 1)
    return html


def weekly(html: str) -> str:
    if 'class="bridge-weekly-feature"' not in html:
        anchor = '<section class="section tw-about">'
        if anchor not in html:
            raise ValueError("This-week editorial introduction changed")
        section = (
            '<section class="bridge-weekly-feature" aria-labelledby="bridgeWeekTitle">'
            '<figure><img src="img/bridge-editorial-rhythm.webp" '
            'alt="일주일의 움직임과 관계를 표현한 편집 화보" loading="lazy">'
            '<figcaption>THE WEEKLY REPUTATION JOURNAL</figcaption></figure>'
            '<div><span>THIS WEEK / FIELD NOTES</span>'
            '<h2 id="bridgeWeekTitle">숫자와 뉴스 사이,<br>변화의 맥락을 읽습니다.</h2>'
            '<p>이번 주의 변화는 출발점입니다. 각 분야 안에서 같은 기준일과 비교 조건이 '
            '확보된 지표를 읽고, 활동량과 평판 수준을 구분해야 합니다.</p>'
            '<a href="intelligence.html">더 깊은 분석 시작하기 ↗</a></div>'
            '</section>'
        )
        html=html.replace(anchor, section+'\n  '+anchor,1)
    return html


def intelligence(html: str) -> str:
    # Progressive disclosure is user-controlled. "Near-rank" does not
    # imply a validated competitor, similarity score or an automatic purchase.
    if 'id="bridgePeerSuggest"' not in html:
        helper = (
            '<div class="bridge-peer-help" aria-label="비교 대상 선택 지원">'
            '<div><b>COMPARE / 같은 분야에서 비교하기</b>'
            '<p>직접 두 대상을 선택하거나, 인접 순위 대상을 참고 후보로 적용하세요. '
            '가까운 순위가 실제 경쟁관계를 의미하지는 않습니다.</p></div>'
            '<button type="button" id="bridgePeerSuggest">'
            '인접 순위 두 대상 넣기 ↗</button></div>'
            '<p class="bridge-peer-status" id="bridgePeerStatus" role="status" '
            'aria-live="polite">비교 대상은 언제든 자유롭게 변경할 수 있습니다.</p>'
            '<p class="bridge-peer-status" id="bridgePrefilledStatus" '
            'aria-live="polite"></p>'
        )
        anchor = '<p class="trio-snapshot-meta" id="trioSnapshotMeta"'
        if anchor not in html:
            raise ValueError("Intelligence comparison snapshot insertion point missing")
        html=html.replace(anchor, helper + '\\n  ' + anchor, 1)
    return html


def compose(path: Path, html: str) -> str:
    if path.name == "briefing.html":
        return brief(html)
    if path.name in SECTORS:
        return sector(html, path.name)
    if path.name == "this-week.html":
        return weekly(html)
    if path.name == "intelligence.html":
        return intelligence(html)
    return html
