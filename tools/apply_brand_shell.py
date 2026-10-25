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
    apply_home_seo(SITE)
    print(f"brand shell applied to {len(changed)} generated pages")

if __name__ == "__main__":
    main()

