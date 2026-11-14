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

IDENTITY_SECTION = '''<section class="section bridge-identity" data-bridge-identity="v1">
  <div class="wrap public-copy">
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">01-1 / BRIDGE IDENTITY</span><h2 class="dx-title">랭킹 산업이 압축해서 버린 맥락을 복원합니다</h2></div>
      <p class="dx-body">BRIDGE는 공개자료와 공중의 관측 신호를 근거 원장에 축적하고, 브랜드와 공중 사이의 관계 상태·구성·변화·관측 신뢰도를 분리해 반복적으로 진단하는 관계 기반 평판 인텔리전스 시스템입니다. 온라인 화제성을 평판 전체로 오인하지 않고, 능력 평가와 관계 평가를 구분하며, 종합점수 뒤의 여섯 축과 변화 원인을 함께 보여줍니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">THE QUESTION</span><h2 class="dx-title">BRIDGE가 묻는 질문은 다릅니다</h2></div>
      <p class="dx-body">누가 더 많이 언급·검색되었는지, 누가 긍정 반응이나 선호를 얻었는지, 누가 특정 역량에서 우수한지만 묻지 않습니다. “이 대상은 공중에게 어떻게 발견되고, 어떤 반응을 얻으며, 무엇으로 기억되고, 어떤 경험과 행동으로 연결되고, 책임과 신뢰를 어떻게 유지하고 있는가?”를 묻습니다.</p>
    </div>
    <div class="public-triptych">
      <div><small>DISTINGUISH</small><h2>구분</h2><p>대상의 실제 상태와 관측 가능한 상태, 0과 미관측, 무언급과 수집 실패를 구분합니다.</p></div>
      <div><small>TRACE</small><h2>추적</h2><p>새 사건과 반복 전재, 실제 변화와 근거 범위 확대, 직접 관측과 유지·참조값을 구분합니다.</p></div>
      <div><small>EXPLAIN</small><h2>설명</h2><p>순위를 해석의 출발점으로 삼고 축별 구조·변화 원인·산출 근거의 신뢰등급을 함께 읽습니다.</p></div>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">PUBLIC EVIDENCE</span><h2 class="dx-title">공개 근거 기반 관계 평판 인텔리전스</h2></div>
      <p class="dx-body">BRIDGE의 상품은 순위 그 자체가 아닙니다. 순위 뒤에 있는 관계를 설명하는 능력과, 그 설명이 어디까지 유효한지를 스스로 밝히는 능력입니다. 순위는 독자의 시선을 여는 입구이며, 축별 구조와 변화 원인, 근거 상태가 해석의 본체입니다.</p>
    </div>
  </div>
</section>'''
IDENTITY_ANCHOR = '<div class="about-figure"><img src="img/about_bridge.jpg"'

PUBLIC_PRINCIPLES = '''<section class="section bridge-public-principles" data-bridge-principles="v1">
  <div class="wrap public-copy">
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">BRIDGE / PUBLIC STANDARD</span><h2 class="dx-title">순위를 보여주되, 순위로 평판을 단정하지 않습니다</h2></div>
      <p class="dx-body"><strong>BRIDGE 브랜드평판지수는 공개자료와 공중의 관측 신호를 바탕으로 브랜드와 공중 사이의 관계 상태, 구성과 변화 방향을 반복 관측하는 관계 기반 평판지수입니다.</strong></p>
      <p class="dx-body">BRIDGE는 언급량을 평판 전체로 보지 않습니다. 도달·반응·정체성·경험·행동유발·책임과 지속을 나누어 보고, 결과를 뒷받침하는 근거의 충실성도 함께 제시합니다.</p>
      <p class="dx-body">순위는 정해진 기간과 공개자료 범위에서 관측된 상대적 위치입니다. 대상의 절대적 가치·능력·윤리성 전체를 판정하지 않습니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">SIGNALBRIDGE</span><h2 class="dx-title">Reputation is a signal.</h2></div>
      <p class="dx-body"><strong>BRIDGE reads the relationship behind the rank.</strong></p>
    </div>
  </div>
</section>'''
PRINCIPLE_PAGES = {"methodology.html", "data-extraction.html", "trust.html"}
PRINCIPLES_ANCHOR = "<footer>"

# BRIDGEBRAND 2.0 magazine edition is shared across the existing site.
# Do not add an extra application or replace any existing analysis scripts.
EDITORIAL_PAGES = {
    "cpr.html", "gov.html", "uni.html", "star.html", "this-week.html",
    "intelligence.html", "subscribe.html", "briefing.html",
    "methodology.html", "trust.html", "data-extraction.html", "about.html",
    "contact.html", "publicity.html",
}
EDITORIAL_WORDMARK = (
    '<a class="logo bridge-editorial-logo" href="index.html" '
    'aria-label="BRIDGEBRAND 홈페이지">BRIDGE<b aria-hidden="true">.</b>'
    '<small>BRAND</small></a>'
)

# New 2.0 page architecture. Keep all existing data-target IDs unchanged.
BRIDGE_JOURNEY = '''<section class="bridge-journey" data-bridge-journey="v2" aria-labelledby="bridgeJourneyTitle">
  <div class="bridge-journey-header"><span>SERVICE JOURNEY / DISCOVER · UNDERSTAND · APPLY</span></div>
  <h2 id="bridgeJourneyTitle">관심에서 분석으로, 분석에서 활용으로.</h2>
  <ol>
    <li><b>01</b><strong>관심 대상 발견</strong><p>홈페이지에서 궁금한 기업·기관·대학·인물을 검색합니다.</p></li>
    <li><b>02</b><strong>비교 대상 직접 선택</strong><p>같은 분야의 대상 두 곳을 더해 분석 대상을 구성합니다.</p></li>
    <li><b>03</b><strong>데이터와 근거 확인</strong><p>순위·6축·신뢰등급과 해석 범위를 구분해 읽습니다.</p></li>
    <li><b>04</b><strong>6단계 전문 브리핑</strong><p>관계 구조·장기 흐름·PUBLICITY를 거쳐 PDF로 보관합니다.</p></li>
    <li><b>05</b><strong>전문 서비스 검토</strong><p>단건 분석이나 정기 관측 구성을 선택해 신청을 검토합니다.</p></li>
  </ol>
  <p class="bridge-journey-note">비교 대상은 현재 이용자가 직접 선택합니다. 유료 신청·계정·결제의 실제 개통 여부는 별도로 확인해야 합니다.</p>
</section>'''

PULSE_FEATURE_OLD = (
    '<section id="fp-current"><span class="subject-label">CUMULATIVE PERFORMANCE · CURRENT VIEW</span>'
    '<h3 id="fieldPulseTitle">영역별 장기 평판 성과</h3>'
    '<p class="lead-copy compact" id="fieldPulseLead">공개 데이터를 불러오고 있습니다.</p></section>'
)
PULSE_FEATURE_NEW = (
    '<section id="fp-current" class="bridge-pulse-feature" aria-labelledby="fieldPulseTitle">'
    '<div class="bridge-pulse-copy">'
    '<span class="subject-label">CUMULATIVE PERFORMANCE · CURRENT VIEW</span>'
    '<h3 id="fieldPulseTitle">영역별 장기 평판 성과</h3>'
    '<p class="lead-copy compact" id="fieldPulseLead">공개 데이터를 불러오고 있습니다.</p>'
    '<p class="bridge-pulse-note">AN EDITORIAL PERSPECTIVE · NOT EVALUATION EVIDENCE</p>'
    '</div>'
    '<figure class="bridge-pulse-photo">'
    '<img id="bridgePulsePhoto" src="img/hero_uni.jpg" '
    'alt="장기 평판 성과를 표현한 분야별 편집 이미지" loading="lazy">'
    '<figcaption><span id="bridgePulsePhotoCaption">EDITORIAL FIELD STUDY / BRIDGE</span>'
    '<b>The long view of reputation.</b></figcaption>'
    '</figure></section>'
)


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
        'style.css?v=20261031-bilingual1',
        updated,
    )
    updated = re.sub(
        r'script\.js\?v=[^"\']+',
        'script.js?v=20261018-mobilebrand2',
        updated,
    )
    bilingual_pages = {
        'index.html', 'this-week.html', 'cpr.html', 'gov.html', 'uni.html',
        'star.html', 'methodology.html', 'data-extraction.html', 'trust.html',
        'about.html', 'intelligence.html', 'subscribe.html',
    }
    if path.name in EDITORIAL_PAGES:
        # Cache-bust updated visual styles on existing pages as well as
        # first-time injections. Reusing the same version left old text
        # colours in visitors' browsers even after a successful deployment.
        updated = re.sub(
            r'(bridge-v2-art-direction[.]css[?]v=)[^"]+',
            r'\g<1>20261114-06',
            updated,
        )
        # The art-direction layer comes last so it can safely repair old
        # dark text/colour declarations without changing underlying data UI.
        if 'bridge-v2-art-direction.css?' not in updated:
            updated = updated.replace(
                '</head>',
                '<link rel="stylesheet" href="bridge-v2-art-direction.css?v=20261114-06">\n</head>',
                1,
            )
        # The same photo-led cover structure serves every existing index page.
        if path.name in {
            'cpr.html','gov.html','uni.html','star.html','this-week.html',
            'methodology.html','trust.html','data-extraction.html',
            'about.html','contact.html',
        } and 'class="bridge-cover-strap"' not in updated:
            updated = re.sub(
                r'(<header class="list-hero-photo[^"]*"[^>]*>)',
                r'\1<div class="bridge-cover-strap" aria-hidden="true"><strong>BRIDGE JOURNAL</strong><span>REPUTATION / RELATIONSHIPS / EVIDENCE</span></div>',
                updated, count=1,
            )
        if path.name == 'intelligence.html' and 'class="bridge-intel-photo"' not in updated:
            updated = updated.replace(
                '<section class="intel-hero"><div class="wrap">',
                '<section class="intel-hero"><figure class="bridge-intel-photo">'
                '<img src="img/hero_data.jpg" alt="" loading="eager">'
                '<figcaption>THE READING ROOM / INTELLIGENCE</figcaption>'
                '</figure><div class="wrap">',
                1,
            )
        if path.name == 'subscribe.html' and 'class="bridge-service-photo"' not in updated:
            updated = updated.replace(
                '<header class="subscribe-hero"><div class="wrap">',
                '<header class="subscribe-hero"><figure class="bridge-service-photo">'
                '<img src="img/about_prism.jpg" alt="" loading="eager">'
                '<figcaption>THE SERVICES / BRIDGE</figcaption>'
                '</figure><div class="wrap">',
                1,
            )
        if 'bridge-v2-editorial.css?' not in updated:
            updated = updated.replace(
                '</head>',
                '<link rel="stylesheet" href="bridge-v2-editorial.css?v=20261114-02">\n</head>',
                1,
            )
        if 'bridge-editorial' not in updated.split('</head>', 1)[-1].split('>', 1)[0]:
            updated = re.sub(
                r'<body(?: class="([^"]*)")?>',
                lambda match: '<body class="' + ' '.join(
                    x for x in [match.group(1) or '', 'bridge-editorial'] if x
                ) + '">',
                updated,
                count=1,
            )
        updated = updated.replace(WORDMARK, EDITORIAL_WORDMARK, 1)
    # Keep reading-room layout and service journey across the daily build.
    if path.name in {"briefing.html", "intelligence.html"}:
        updated = re.sub(
            r'(bridge-v2-reading-room[.]css[?]v=)[^"]+',
            r'\\g<1>20261114-01',
            updated,
        )
        if 'bridge-v2-reading-room.css?' not in updated:
            updated = updated.replace(
                '</head>',
                '<link rel="stylesheet" href="bridge-v2-reading-room.css?v=20261114-01">\\n</head>',
                1,
            )
    if path.name == "briefing.html":
        if PULSE_FEATURE_OLD in updated:
            updated = updated.replace(PULSE_FEATURE_OLD, PULSE_FEATURE_NEW, 1)
        if 'bridge-v2-reading-room.js?' not in updated:
            updated = updated.replace(
                '</body>',
                '<script src="bridge-v2-reading-room.js?v=20261114-01" defer></script>\\n</body>',
                1,
            )
    if path.name == "intelligence.html" and 'data-bridge-journey="v2"' not in updated:
        updated = updated.replace(
            '<section class="field-engine-section" id="fieldEngines">',
            BRIDGE_JOURNEY + '\\n' + '<section class="field-engine-section" id="fieldEngines">',
            1,
        )
    # Retire the first V2 color-block experiment rather than stacking
    # incompatible styles on the new editorial reading system.
    if path.name == 'intelligence.html':
        updated = re.sub(r'<link rel="stylesheet" href="bridge-v2-intelligence[.]css[^"]*">[\\s]*', '', updated)
    if path.name in bilingual_pages and 'i18n.js?' not in updated:
        updated = updated.replace(
            '</body>',
            '<script src="i18n.js?v=20261101-bilingual3" defer></script>\n</body>',
            1,
        )
    updated = updated.replace("VOL. 01 — WEEK", "VOL. 02 — WEEK")
    if path.name == "about.html" and 'data-bridge-identity="v1"' not in updated and IDENTITY_ANCHOR in updated:
        updated = updated.replace(IDENTITY_ANCHOR, IDENTITY_SECTION + IDENTITY_ANCHOR, 1)
    if path.name in PRINCIPLE_PAGES and 'data-bridge-principles="v1"' not in updated and PRINCIPLES_ANCHOR in updated:
        updated = updated.replace(PRINCIPLES_ANCHOR, PUBLIC_PRINCIPLES + PRINCIPLES_ANCHOR, 1)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False

def main() -> None:
    files = sorted(SITE.glob("*.html")) + sorted((SITE / "site_fix").glob("*.html"))
    changed = [str(path.relative_to(SITE.parent)) for path in files if apply(path)]
    try:
        from tools.seo_metadata import apply_home_seo
    except ModuleNotFoundError:
        from seo_metadata import apply_home_seo
    # The 2.0 homepage is composed after legacy build.py output and before
    # SEO normalization. This preserves the experience across every daily
    # regeneration without modifying scoring, data collection or reports.
    try:
        from tools.publish_v2_home import publish as publish_v2_home
    except ModuleNotFoundError:
        # python tools/apply_brand_shell.py starts with tools/ on sys.path,
        # whereas build.py imports this module from the repository root.
        from publish_v2_home import publish as publish_v2_home
    publish_v2_home()
    apply_home_seo(SITE)
    print(f"brand shell applied to {len(changed)} generated pages; V2 home active")

if __name__ == "__main__":
    main()

