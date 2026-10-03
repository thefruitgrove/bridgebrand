import os
_HERE = os.path.dirname(os.path.abspath(__file__))
import json, html, os, sys
sys.path.insert(0, _HERE)
import build_pilot

with open(os.path.join(_HERE, "data/bridge_data_v2.json"), encoding="utf-8") as f:
    DATA = json.load(f)
WEEK = DATA["week"]
CPR, STAR, GOV = DATA["CPR"], DATA["STAR"], DATA["GOV"]

def esc(s): return html.escape(str(s))

def subset(pool, subcat, limit):
    filtered = sorted([r for r in pool if r["subcat"] == subcat], key=lambda r: -r["totalScore"])
    out = []
    for i, r in enumerate(filtered[:limit], start=1):
        rr = dict(r); rr["localRank"] = i
        out.append(rr)
    return out

def with_local_rank(pool):
    out = []
    for r in pool:
        rr = dict(r); rr["localRank"] = r["rank"]
        out.append(rr)
    return out

def change_badge(r):
    ch = r["rankChange"]
    if ch > 0: return f'<span class="wow wow-up">▲ {ch}</span>'
    if ch < 0: return f'<span class="wow wow-down">▼ {abs(ch)}</span>'
    return '<span class="wow wow-flat">— 0</span>'

def score_delta(r):
    ch = r["scoreChange"]
    if ch > 0: return f'<span class="sd sd-up">+{ch:.1f}</span>'
    if ch < 0: return f'<span class="sd sd-down">{ch:.1f}</span>'
    return '<span class="sd sd-flat">0.0</span>'

def table_head():
    return '''
        <div class="rk-head">
          <div>RANK</div><div>NAME / ID</div><div>MARKET</div><div>BRIDGE (B·R·I·D·G·E)</div>
          <div>SCORE</div><div>WoW</div><div>TRUST</div>
        </div>'''

def table_rows(rows):
    out = []
    for r in rows:
        top3 = "top3" if r["localRank"] <= 3 else ""
        agency_part = f' · 소속 {esc(r["agency"])}' if r.get("agency") and r["agency"] != "-" else ""
        out.append(f'''
        <div class="rk-row {top3}">
          <div class="rk-num">{r["localRank"]:02d}</div>
          <div class="rk-name">
            <div class="nm">{esc(r["entityName"])}</div>
            <div class="sub">{esc(r["entityId"])}{agency_part} · {esc(r["sector"])}</div>
          </div>
          <div class="rk-market">{esc(r["market"])}</div>
          <div class="rk-dims">
            {''.join(f'<span class="dm"><b>{k}</b>{r["dimensions"][k]}</span>' for k in ["B","R","I","D","G","E"])}
          </div>
          <div class="rk-score">{r["totalScore"]:.1f}{score_delta(r)}</div>
          <div class="rk-wow">{change_badge(r)}</div>
          <div class="rk-trust"><span class="trust-badge grade-{r["trustGrade"]}">{r["trustGrade"]}</span></div>
        </div>''')
    return "\n".join(out)

def seg_control(active_key, segs, page):
    btns = []
    for key, label, count in segs:
        cls = "seg-btn active" if key == active_key else "seg-btn"
        btns.append(f'<button class="{cls}" data-target="{page}-{key}">{label} <span>{count}</span></button>')
    return f'<div class="seg-control">{"".join(btns)}</div>'

def panel(page, key, rows, visible):
    disp = "" if visible else "hidden"
    return f'''
      <div class="rk-panel {disp}" id="{page}-{key}">
        {table_head()}
        {table_rows(rows)}
      </div>'''

def ticker_items():
    """Real entities only — no fabricated score/delta (see build.py for rationale)."""
    cpr = build_pilot.CPR_REAL
    star = build_pilot.STAR_REAL
    gov = build_pilot.GOV_REAL
    items = []
    n = max(len(cpr), len(star), len(gov))
    for i in range(n):
        if i < len(cpr): items.append(("CPR", cpr[i][0]))
        if i < len(star): items.append(("STAR", star[i][0]))
        if i < len(gov): items.append(("GOV", gov[i][0]))
    return items

def ticker_html():
    def item_span(tag, name):
        pilot = build_pilot.REAL_PILOT_CASES.get(name)
        if pilot:
            return f'<span><b>{tag}</b>{esc(name)} <span class="t-score">{pilot["score"]}</span></span>'
        return f'<span><b>{tag}</b>{esc(name)} <span class="t-flat">N/R</span></span>'
    spans = [item_span(tag, name) for tag, name in ticker_items()]
    all_spans = "\n    ".join(spans)
    return f'''
<div class="ticker">
  <button class="ticker-toggle" id="tickerToggle" aria-label="일시정지">LIVE ⏸</button>
  <div class="ticker-viewport">
    <div class="ticker-track" id="tickerTrack">
    {all_spans}
    {all_spans}
    </div>
  </div>
</div>'''

NAV_ITEMS = [
    ("HOME", "home", None),
    ("THIS WEEK", "this-week", None),
    ("CPR", "cpr", [("CPR B-T100","cpr","t100"),("CPR B-BC70","cpr","bc70"),("CPR B-BB30","cpr","bb30")]),
    ("GOV", "gov", [("GOV B-T100","gov","t100"),("GOV B-M40","gov","m40"),("GOV B-C60","gov","c60")]),
    ("UNI", "uni", [("UNI B-T100","uni","t100"),("UNI B-U60","uni","u60"),("UNI B-C40","uni","c40")]),
    ("ENT", "star", [("ENT B-T100","star","t100"),("ENT B-AM45","star","am45"),("ENT B-AW45","star","aw45"),("ENT B-AN10","star","an10")]),
]
NAV_UTIL_ITEMS = [("INDEX","methodology"),("데이터추출","data-extraction"),("신뢰등급이란?","trust")]

def nav_html():
    parts = []
    for label, view, sub in NAV_ITEMS:
        if sub:
            subitems = "".join(f'<a href="#" data-view="{v}" data-seg="{seg}">{s_label}</a>' for s_label, v, seg in sub)
            parts.append(f'''
      <div class="nav-item has-drop">
        <a href="#" data-view="{view}" class="nav-link">{label}</a>
        <div class="nav-drop">{subitems}</div>
      </div>''')
        else:
            parts.append(f'<div class="nav-item"><a href="#" data-view="{view}" class="nav-link">{label}</a></div>')
    return "".join(parts)

def mobile_menu_html():
    return "".join(f'<a href="#" data-view="{view}">{label}</a>' for label, view, sub in NAV_ITEMS)

PRE_INDEX_NOTICE = "본 결과는 BRIDGE 모형의 초기 데이터 파이프라인을 검증하기 위한 예비지수이며, 데이터 범위와 신뢰등급에 따라 순위가 수정될 수 있습니다."

def footer(note):
    return f'''
<footer>
  <div class="wrap">
    <div class="footer-top">
      <span class="logo">BRIDGE</span>
      <div class="footer-links">
        <a href="#" data-view="about">시그널브릿지 회사소개</a>
        <a href="#" data-view="methodology">이의제기</a>
        <a href="mailto:hello@signalbridge.kr">문의</a>
      </div>
    </div>
    <p class="footer-op">BRIDGE is developed and operated by SignalBridge.</p>
    <p class="footer-note">{note}</p>
  </div>
</footer>'''

FN_INDEX = "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 화면에 표시된 대상명과 수치는 데모를 위해 임의로 구성한 가상의 예시이며, 실제 기업·인물·기관의 평판과 무관합니다. 본 지수는 공개 접근 데이터에 대한 통계적 분석이며, 사실판단·법률판단·투자판단을 대신하지 않습니다."
FN_CPR = FN_INDEX
FN_STAR = "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 화면에 표시된 인물명과 수치는 데모를 위해 임의로 구성한 가상의 예시이며, 실제 인물의 평판과 무관합니다. 인물 이미지는 초상권 확인 전이므로 추상 데이터 아트로 대체했습니다."
FN_GOV = "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 화면에 표시된 기관명과 수치는 데모를 위해 임의로 구성한 가상의 예시이며, 실제 기관의 평판과 무관합니다. 본 지수는 정책 찬반이 아닌 소통·설명책임에 대한 통계적 분석입니다."
FN_METH = "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 표기된 버전·정정 이력은 데모를 위한 예시입니다."
FN_TRUST = "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 표기된 등급 기준은 데모를 위한 예시입니다."
FN_ABOUT = "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다."

def view_home():
    cpr_count = len(build_pilot.CPR_REAL)
    from gov_real import GOV_M40, GOV_C60
    from uni_real import UNI_4YEAR, UNI_2YEAR
    gov_count = len(GOV_M40) + len(GOV_C60)
    uni_count = len(UNI_4YEAR) + len(UNI_2YEAR)
    star_count = len(build_pilot.STAR_REAL)
    cpr_b2c = len([1 for e in build_pilot.CPR_REAL if e[6]=="B2C"])
    cpr_b2b = len([1 for e in build_pilot.CPR_REAL if e[6]=="B2B"])
    star_am = len([1 for e in build_pilot.STAR_REAL if e[2]=="AM"])
    star_aw = len([1 for e in build_pilot.STAR_REAL if e[2]=="AW"])
    star_an = len([1 for e in build_pilot.STAR_REAL if e[2]=="AN"])
    tower_rows = [
        ("CPR", cpr_count, "cpr", f"B2C {cpr_b2c} · B2B {cpr_b2b}"),
        ("GOV", gov_count, "gov", f"중앙 {len(GOV_M40)} · 지자체·공공 {len(GOV_C60)}"),
        ("UNI", uni_count, "uni", f"4년제 {len(UNI_4YEAR)} · 2년제 {len(UNI_2YEAR)}"),
        ("ENT", star_count, "star", f"남 {star_am} · 여 {star_aw} · 신인 {star_an}"),
    ]
    tower_html = "".join(f'''
      <div class="tower-card">
        <span class="tc-lbl">{tag} / 표본<br><span class="tc-hook">{hook}</span></span>
        <span class="tc-val">{count}</span>
        <span class="tc-foot">TRUST N/R</span>
      </div>''' for tag, count, view, hook in tower_rows)
    return f'''
<section class="view active" id="view-home">
<section id="hero-cinematic">
  <svg class="hero-lines" viewBox="0 0 1400 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#3a3a42" stop-opacity="0.5"/>
        <stop offset="1" stop-color="#101014" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <rect x="820" y="0" width="1" height="900" fill="url(#lg1)"/>
    <rect x="920" y="0" width="1" height="900" fill="url(#lg1)"/>
    <rect x="1040" y="0" width="1" height="900" fill="url(#lg1)"/>
    <path d="M 950 900 C 1150 650, 1300 500, 1390 260" stroke="#b6924f" stroke-opacity="0.55" fill="none" stroke-width="1.4"/>
    <circle cx="1330" cy="330" r="46" fill="#8a6a34" fill-opacity="0.5"/>
    <ellipse cx="750" cy="900" rx="420" ry="60" fill="#000" fill-opacity="0.35"/>
  </svg>
  <div class="hero-inner">
    <div>
      <div class="hero-meta">VOL. 01 — WEEK 37<br>SEOUL · 12 SEP 2026</div>
      <div class="hero-headline">
        <div class="l1">Reputation</div>
        <div class="l2">is a signal.</div>
      </div>
    </div>
    <div class="hero-bottom">
      <div class="hero-tagline">화제의 크기가 아니라<br>신뢰가 움직이는 방향을 읽습니다.
        <div class="hero-identity">BRIDGE 브랜드평판지수 INDEX™</div>
      </div>
      <div class="hero-explore">
        <div class="hero-tower-inline">{tower_html}</div>
        <a class="btn" href="#" data-view="this-week">EXPLORE THIS WEEK ↓</a>
      </div>
    </div>
  </div>
</section>
{footer(FN_INDEX)}
</section>'''

def view_list(page, title, note, pools):
    segs = [(k, l, c) for k, l, c, _ in pools]
    seg_ctrl = seg_control(pools[0][0], segs, page)
    panels = "".join(panel(page, k, rows, visible=(i == 0)) for i, (k, l, c, rows) in enumerate(pools))
    fn = {"cpr":FN_CPR, "star":FN_STAR, "gov":FN_GOV}[page]
    return f'''
<section class="view" id="view-{page}">
  <div class="list-page">
    <header class="list-hero-photo hero-{page}">
      <div class="wrap">
        <h1>{title}</h1>
        <p class="list-note">{note}</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        {seg_ctrl}
        {panels}
      </div>
    </section>
  </div>
  {footer(fn)}
</section>'''

def real_view(page, title, note, model_blurb, seg_html, panels_html, footer_key, period_unit="week"):
    return f'''
<section class="view" id="view-{page}">
  <div class="list-page">
    <header class="list-hero-photo hero-{page}">
      <div class="wrap">
        <h1>{title}</h1>
        <p class="list-note">{note}</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <div class="pilot-notice">{model_blurb}</div>
        <div class="example-toggle-row">
          <button class="format-toggle active" data-page="{page}">형식 예시 끄기 (실제 값 아님)</button>
          <span class="format-toggle-note">기본값으로 형식 예시가 켜져 있습니다 — 모든 값에 "예시" 표기가 붙어 있으며 실명 대상의 실제 산출값이 아닙니다. 버튼을 누르면 N/R(미산출)로 전환됩니다.</span>
        </div>
        {build_pilot.period_selector_html(page, period_unit)}
        <div class="rk-legend">
          <span class="rk-legend-item"><b>점수</b> 0~100점 (높을수록 긍정)</span>
          <span class="rk-legend-item"><b>N/R</b> 근거 부족으로 미산출(Not Rated)</span>
          <span class="rk-legend-item"><span class="trust-badge grade-A" style="font-size:11px">A</span>~<span class="trust-badge grade-D" style="font-size:11px">D</span> 신뢰등급(근거의 양·질)</span>
        </div>
        <div class="rk-toolbar">
          <input type="search" class="rk-search" data-page="{page}" placeholder="이름으로 검색…" aria-label="대상 이름 검색">
          <div class="rk-sort">
            <span class="rk-sort-label">정렬</span>
            <button class="rk-sort-btn active" data-sort="default" data-page="{page}">기본</button>
            <button class="rk-sort-btn" data-sort="score" data-page="{page}">점수순</button>
            <button class="rk-sort-btn" data-sort="name" data-page="{page}">가나다순</button>
          </div>
        </div>
        {seg_html}
        {panels_html}
      </div>
    </section>
  </div>
  {footer(footer_key)}
</section>'''

cpr_segs = [("t100","CPR B-T100",len(build_pilot.CPR_REAL)), ("bc70","CPR B-BC70",len([1 for e in build_pilot.CPR_REAL if e[6]=="B2C"])), ("bb30","CPR B-BB30",len([1 for e in build_pilot.CPR_REAL if e[6]=="B2B"]))]
cpr_seg_html = seg_control("t100", cpr_segs, "cpr")
cpr_panels_html = (
    f'<div class="rk-panel" id="cpr-t100">{build_pilot.cpr_rows()}</div>'
    f'<div class="rk-panel hidden" id="cpr-bc70">{build_pilot.cpr_rows("B2C")}</div>'
    f'<div class="rk-panel hidden" id="cpr-bb30">{build_pilot.cpr_rows("B2B")}</div>'
)
THIS_WEEK_VIEW = f'''
<section class="view" id="view-this-week">
{build_pilot.this_week_digest_html()}
{footer(FN_INDEX)}
</section>'''

CPR_VIEW = real_view("cpr", "CPR — Corporate",
    f"코스피·코스닥 실제 상장기업 {len(build_pilot.CPR_REAL)}개 표본. B-T100(통합) · B-BC70(소비재 브랜드 B2C) · "
    f"B-BB30(기간산업 브랜드 B2B) 탭으로 구분합니다. " + PRE_INDEX_NOTICE,
    build_pilot.MODEL_BLURBS["CPR"], cpr_seg_html, cpr_panels_html, FN_CPR)

star_segs = [("t100","STAR B-T100",len(build_pilot.STAR_REAL)),
             ("am45","STAR B-AM45",len([1 for e in build_pilot.STAR_REAL if e[2]=="AM"])),
             ("aw45","STAR B-AW45",len([1 for e in build_pilot.STAR_REAL if e[2]=="AW"])),
             ("an10","STAR B-AN10",len([1 for e in build_pilot.STAR_REAL if e[2]=="AN"]))]
star_seg_html = seg_control("t100", star_segs, "star")
star_panels_html = (
    f'<div class="rk-panel" id="star-t100">{build_pilot.star_rows()}</div>'
    f'<div class="rk-panel hidden" id="star-am45">{build_pilot.star_rows("AM")}</div>'
    f'<div class="rk-panel hidden" id="star-aw45">{build_pilot.star_rows("AW")}</div>'
    f'<div class="rk-panel hidden" id="star-an10">{build_pilot.star_rows("AN")}</div>'
)
STAR_VIEW = real_view("star", "ENT — 광고모델·공인",
    f"실제 활동 중인 공인·광고모델 {len(build_pilot.STAR_REAL)}명 표본. B-T100(통합) · B-AM45(남자 연예인) · "
    f"B-AW45(여자 연예인) · B-AN10(남녀 신인급) 탭으로 구분합니다. 기존 평판 점수·순위는 어떤 출처에서도 "
    f"인용하지 않았습니다. " + PRE_INDEX_NOTICE,
    build_pilot.MODEL_BLURBS["STAR"], star_seg_html, star_panels_html, FN_STAR)

from gov_real import GOV_M40, GOV_C60
gov_segs = [("t100","GOV B-T100",len(GOV_M40)+len(GOV_C60)), ("m40","GOV B-M40",len(GOV_M40)), ("c60","GOV B-C60",len(GOV_C60))]
gov_seg_html = seg_control("t100", gov_segs, "gov")
gov_panels_html = (
    f'<div class="rk-panel" id="gov-t100">{build_pilot.gov_t100_rows()}</div>'
    f'<div class="rk-panel hidden" id="gov-m40">{build_pilot.gov_m40_rows()}</div>'
    f'<div class="rk-panel hidden" id="gov-c60">{build_pilot.gov_c60_rows()}</div>'
)
GOV_VIEW = real_view("gov", "GOV — 공공기관",
    f"중앙행정기관 각부 {len(GOV_M40)}개 + 지자체·공공기관 {len(GOV_C60)}개 = {len(GOV_M40)+len(GOV_C60)}개 표본. "
    f"B-T100(통합) · B-M40(중앙행정기관 각부) · B-C60(지자체 및 공공기관) 탭으로 구분합니다. " + PRE_INDEX_NOTICE,
    build_pilot.MODEL_BLURBS["GOV"], gov_seg_html, gov_panels_html, FN_GOV)

with open(os.path.join(_HERE, "original_methodology_confirmed.html"), encoding="utf-8") as f:
    _m = f.read()
_i = _m.index('<header class="about-hero wrap">')
_j = _m.index('<footer>')
METHODOLOGY_BODY = _m[_i:_j]
# UNI_DESIGN_BLOCK 제거됨(사용자 요청) — 백서에만 전체 공개, 라이브 페이지에는 미노출
_meth_body_patched = METHODOLOGY_BODY.split("</header>",1)[1]
METHODOLOGY_VIEW = f'''
<section class="view" id="view-methodology">
<header class="list-hero-photo hero-methodology">
  <div class="wrap">
    <div class="about-kicker">INDEX · 방법론과 데이터정책</div>
    <h1>이 페이지는<br>팔리지 않습니다.</h1>

  </div>
</header>
{_meth_body_patched}
{footer(FN_METH)}
</section>'''

TRUST_VIEW = f'''
<section class="view" id="view-trust">
<header class="list-hero-photo hero-trust">
  <div class="wrap">
    <h1>신뢰등급이란?</h1>
    <p class="list-note">신뢰등급은 평판점수가 아니라 '그 점수를 얼마나 믿을 수 있는가'를 나타냅니다.
    등급이 낮다는 것은 평판이 나쁘다는 뜻이 아니라, 데이터의 검증 수준이 아직 낮다는 뜻입니다.</p>
  </div>
</header>
<section class="section">
  <div class="wrap">
    <table class="mini-table" style="max-width:820px">
      <tr><th>등급</th><th>기준</th></tr>
      <tr><td><b>A</b></td><td>핵심자료원 90% 이상 확보, 다원출처 확보, 표본 충분, 검증 완료</td></tr>
      <tr><td><b>B</b></td><td>핵심자료원 75% 이상, 3종 이상의 독립자료원 확보</td></tr>
      <tr><td><b>C</b></td><td>핵심자료원 60% 이상, 일부 자료원에 편중</td></tr>
      <tr><td><b>D</b></td><td>단일 주간 또는 제한된 자료원에 의한 예비측정</td></tr>
      <tr><td><b>N/R</b></td><td>최소 산출기준 미충족 — 점수를 산출하지 않음</td></tr>
    </table>
    <p class="pullquote" style="margin-top:40px">데이터가 부족한 대상은 낮은 점수가 아니라 별도의 데이터 신뢰등급으로 표시합니다.</p>
  </div>
</section>
{footer(FN_TRUST)}
</section>'''

ABOUT_VIEW = f'''
<section class="view" id="view-about">
<header class="list-hero-photo hero-about">
  <div class="wrap">
    <h1>SignalBridge</h1>
    <p class="list-note">시그널브릿지가 개발한 BRIDGE 브랜드평판지수. BRIDGE는 시그널브릿지가 보유하고
    관리하는 평가 프레임워크이자 방법론 브랜드이며, SignalBridge는 이 서비스를 운영하는 회사입니다.</p>
  </div>
</header>
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>독립성 원칙</h2></div>
    <ul class="make-list">
      <li><span class="o">＋</span>평가·분석 조직과 광고·영업 조직을 인사·보고체계상 분리합니다</li>
      <li><span class="o">＋</span>광고 게재 여부, BRIDGE-V 계약 여부가 공개 점수·순위에 어떠한 영향도 주지 않습니다</li>
      <li><span class="o">＋</span>이해상충이 발생할 수 있는 경우(예: 광고주의 경쟁사가 평가대상) 사전에 공시합니다</li>
      <li><span class="o">＋</span>지수는 사실적시가 아닌 통계적 진단 의견이며, 방법론과 근거자료를 사전 공개합니다</li>
    </ul>
  </div>
</section>
<section class="section tint">
  <div class="wrap">
    <div class="section-head"><h2>하지 않는 일</h2></div>
    <ul class="make-list">
      <li><span class="o">－</span>사실판단·법률판단·투자판단을 대신하지 않습니다</li>
      <li><span class="o">－</span>개별 기업·인물·기관의 요청으로 순위를 임의 조정하지 않습니다</li>
      <li><span class="o">－</span>소비자 전체의 내면적 신뢰, 실제 구매, 시장가치까지 직접 측정한다고 주장하지 않습니다</li>
      <li><span class="o">－</span>단순히 결과가 불리하다는 이유의 이의제기로 점수를 변경하지 않습니다</li>
    </ul>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>서비스 체계</h2></div>
    <table class="mini-table" style="max-width:820px">
      <tr><th>계층</th><th>정식 명칭</th><th>역할</th></tr>
      <tr><td>운영회사</td><td>시그널브릿지 SignalBridge</td><td>서비스 운영, 계약, 데이터 거버넌스</td></tr>
      <tr><td>핵심 프레임워크</td><td>BRIDGE Brand Reputation Framework</td><td>6축 평가철학과 공통 산식</td></tr>
      <tr><td>공개 평가모듈</td><td>BRIDGE-CPR · BRIDGE-STAR · BRIDGE-GOV</td><td>분야별 평판지수</td></tr>
      <tr><td>서비스 계층</td><td>BRIDGE-D · BRIDGE-V</td><td>무료 공개형과 내부자료 결합 확장형 구분</td></tr>
    </table>
    <p class="list-note" style="margin-top:20px">문의: hello@signalbridge.kr</p>
  </div>
</section>
{footer(FN_ABOUT)}
</section>'''

from uni_real import UNI_4YEAR, UNI_2YEAR
uni_segs = [("t100","UNI B-T100",len(UNI_4YEAR)+len(UNI_2YEAR)), ("u60","UNI B-U60",len(UNI_4YEAR)), ("c40","UNI B-C40",len(UNI_2YEAR))]
uni_seg_html = seg_control("t100", uni_segs, "uni")
uni_panels_html = (
    f'<div class="rk-panel" id="uni-t100">{build_pilot.uni_rows(UNI_4YEAR)}{build_pilot.uni_rows(UNI_2YEAR, is_2year=True)}</div>'
    f'<div class="rk-panel hidden" id="uni-u60">{build_pilot.uni_rows(UNI_4YEAR)}</div>'
    f'<div class="rk-panel hidden" id="uni-c40">{build_pilot.uni_rows(UNI_2YEAR, is_2year=True)}</div>'
)
UNI_VIEW = real_view("uni", "UNI — 대학",
    f"전국 4년제 대학 {len(UNI_4YEAR)}개교 + 2년제 대학 {len(UNI_2YEAR)}개교 = {len(UNI_4YEAR)+len(UNI_2YEAR)}개 표본. "
    f"B-T100(통합) · B-U60(4년제) · B-C40(2년제) 탭으로 구분합니다. " + PRE_INDEX_NOTICE,
    build_pilot.MODEL_BLURBS["UNI"], uni_seg_html, uni_panels_html, FN_INDEX, period_unit="month") + build_pilot.BRIDGE_MODAL_HTML

DATA_EXTRACTION_VIEW = f'''
<section class="view" id="view-data-extraction">
<header class="list-hero-photo hero-data-extraction">
  <div class="wrap">
    <h1>데이터 추출</h1>
    <p class="list-note">BRIDGE가 CPR·GOV·UNI·ENT 네 영역에서 무엇을 근거로, 왜 그렇게 산출하는지에 대한
    요약입니다. 각 항목의 상세 산출식과 자료원 가중치, 검증 절차는 내부 운영 기준에 따라
    별도로 관리됩니다 — 이 페이지는 외부 설명용 요약입니다.</p>
  </div>
</header>
<section class="section">
  <div class="wrap">
    <div class="pilot-block">
      <h2>공통 원칙</h2>
      <ul class="make-list">
        <li><span class="o">＋</span>대상선정(누구를 평가할 것인가)과 평판측정(그 대상이 몇 점인가)을 분리합니다</li>
        <li><span class="o">＋</span>모든 점수에는 근거자료 링크(Evidence Card)와 신뢰등급(A~D, N/R)을 함께 표시합니다</li>
        <li><span class="o">＋</span>산정방식을 비공개로 두는 외부 지수의 점수·순위는 근거자료로 인용하지 않습니다</li>
      </ul>
    </div>
    <div class="pilot-block"><h2>CPR</h2><p class="list-note">{build_pilot.MODEL_BLURBS["CPR"]}</p></div>
    <div class="pilot-block"><h2>GOV</h2><p class="list-note">{build_pilot.MODEL_BLURBS["GOV"]}</p></div>
    <div class="pilot-block"><h2>UNI</h2><p class="list-note">{build_pilot.MODEL_BLURBS["UNI"]}</p></div>
    <div class="pilot-block"><h2>ENT</h2><p class="list-note">{build_pilot.MODEL_BLURBS["STAR"]}</p></div>
  </div>
</section>
{footer(FN_INDEX)}
</section>'''


with open(os.path.join(_HERE, "site/style_inline.css"), encoding="utf-8") as f:
    CSS = f.read()

EXTRA_CSS = '''
.view{ display:none; }
.view.active{ display:block; }
'''

JS = r'''
(function(){
  var track = document.getElementById('tickerTrack');
  var toggleBtn = document.getElementById('tickerToggle');
  var viewport = track ? track.parentElement : null;
  var paused = false;
  function setPaused(p){
    paused = p;
    if(track) track.classList.toggle('paused', paused);
    if(toggleBtn) toggleBtn.textContent = paused ? 'PAUSED ▶' : 'LIVE ⏸';
  }
  if(viewport){
    viewport.addEventListener('mouseenter', function(){ if(track) track.classList.add('paused'); });
    viewport.addEventListener('mouseleave', function(){ if(track && !paused) track.classList.remove('paused'); });
  }
  if(toggleBtn) toggleBtn.addEventListener('click', function(){ setPaused(!paused); });

  var dropItems = document.querySelectorAll('.nav-item.has-drop');
  dropItems.forEach(function(item){
    var link = item.querySelector('a.nav-link');
    link.addEventListener('click', function(e){
      if(window.matchMedia('(hover: none)').matches){
        if(!item.classList.contains('open')){
          e.preventDefault();
          dropItems.forEach(function(i){ if(i !== item) i.classList.remove('open'); });
          item.classList.add('open');
        }
      }
    });
  });
  document.addEventListener('click', function(e){
    dropItems.forEach(function(item){ if(!item.contains(e.target)) item.classList.remove('open'); });
  });

  var navToggle = document.querySelector('.nav-toggle');
  var mobileMenu = document.getElementById('mobileMenu');
  var mmClose = document.getElementById('mmClose');
  function openMobile(){ if(mobileMenu) mobileMenu.classList.add('open'); }
  function closeMobile(){ if(mobileMenu) mobileMenu.classList.remove('open'); }
  if(navToggle) navToggle.addEventListener('click', openMobile);
  if(mmClose) mmClose.addEventListener('click', closeMobile);
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeMobile(); });
  if(mobileMenu) mobileMenu.addEventListener('click', function(e){ if(e.target === mobileMenu) closeMobile(); });

  var segBtns = document.querySelectorAll('.seg-btn');
  segBtns.forEach(function(btn){
    btn.addEventListener('click', function(){
      var target = btn.dataset.target;
      var group = btn.parentElement;
      group.querySelectorAll('.seg-btn').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      var panelsContainer = group.parentElement;
      panelsContainer.querySelectorAll('.rk-panel').forEach(function(p){ p.classList.add('hidden'); });
      var targetPanel = document.getElementById(target);
      if(targetPanel) targetPanel.classList.remove('hidden');
    });
  });

  var navEl = document.querySelector('nav.nav');
  function showView(view){
    document.querySelectorAll('.view').forEach(function(v){ v.classList.remove('active'); });
    var target = document.getElementById('view-' + view);
    if(target) target.classList.add('active');
    document.querySelectorAll('.nav-link').forEach(function(l){ l.classList.remove('active'); });
    var activeLink = document.querySelector('.nav-link[data-view="' + view + '"]');
    if(activeLink) activeLink.classList.add('active');
    if(navEl){
      if(view === 'home') navEl.classList.add('on-dark'); else navEl.classList.remove('on-dark');
    }
    closeMobile();
    window.scrollTo(0,0);
  }
  document.querySelectorAll('[data-view]').forEach(function(el){
    el.addEventListener('click', function(e){
      e.preventDefault();
      var view = el.dataset.view;
      var seg = el.dataset.seg;
      showView(view);
      if(seg){
        var btn = document.querySelector('.seg-btn[data-target="' + view + '-' + seg + '"]');
        if(btn) btn.click();
      }
    });
  });

  // ---- BRIDGE sample diagram modal (UNI demo): deterministic illustrative axis values ----
  function hashSeed(str){
    var h = 0;
    for(var i=0;i<str.length;i++){ h = (h*31 + str.charCodeAt(i)) >>> 0; }
    return h;
  }
  function seededAxisValues(name){
    var seed = hashSeed(name);
    var vals = [];
    ['B','R','I','D','G','E'].forEach(function(k, idx){
      var v = 45 + ((seed >> (idx*4)) % 50);
      vals.push(v);
    });
    return vals;
  }
  function polygonPoints(vals, cx, cy, maxR){
    var angles = [-90, -30, 30, 90, 150, 210];
    return vals.map(function(v, i){
      var r = (v/100) * maxR;
      var rad = angles[i] * Math.PI/180;
      var x = cx + r*Math.cos(rad);
      var y = cy + r*Math.sin(rad);
      return x.toFixed(1) + ',' + y.toFixed(1);
    }).join(' ');
  }
  function buildRadarSVG(vals){
    var cx=160, cy=160, maxR=120;
    var rings = [0.33, 0.66, 1.0].map(function(f){
      return '<polygon points="' + polygonPoints([f*100,f*100,f*100,f*100,f*100,f*100], cx, cy, maxR) + '" fill="none" stroke="#DEDAD1" stroke-width="1"/>';
    }).join('');
    var dataPoly = '<polygon points="' + polygonPoints(vals, cx, cy, maxR) + '" fill="rgba(169,136,79,0.25)" stroke="#a9884f" stroke-width="2"/>';
    var labels = ['B','R','I','D','G','E'];
    var angles = [-90,-30,30,90,150,210];
    var labelEls = labels.map(function(l, i){
      var rad = angles[i]*Math.PI/180;
      var x = cx + (maxR+20)*Math.cos(rad);
      var y = cy + (maxR+20)*Math.sin(rad);
      return '<text x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" text-anchor="middle" dominant-baseline="middle" font-size="15" font-weight="700" fill="#161513">'+l+'</text>';
    }).join('');
    return rings + dataPoly + labelEls;
  }
  var modalOverlay = document.getElementById('bridgeModalOverlay');
  var modalClose = document.getElementById('bridgeModalClose');
  function openBridgeModal(name, region, type){
    if(!modalOverlay) return;
    var vals = seededAxisValues(name);
    document.getElementById('bridgeModalTitle').textContent = name;
    document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · BRIDGE 모형 예시 다이어그램';
    var svg = document.getElementById('bridgeRadar');
    svg.innerHTML = buildRadarSVG(vals);
    ['B','R','I','D','G','E'].forEach(function(k, i){
      document.getElementById('bm'+k).textContent = vals[i] + ' (예시)';
    });
    modalOverlay.classList.add('open');
  }
  function closeBridgeModal(){ if(modalOverlay) modalOverlay.classList.remove('open'); }
  document.querySelectorAll('.rk-clickable').forEach(function(row){
    row.addEventListener('click', function(){
      openBridgeModal(row.dataset.entity, row.dataset.region, row.dataset.type);
    });
    row.addEventListener('keydown', function(e){
      if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); row.click(); }
    });
  });
  if(modalClose) modalClose.addEventListener('click', closeBridgeModal);
  if(modalOverlay) modalOverlay.addEventListener('click', function(e){ if(e.target === modalOverlay) closeBridgeModal(); });
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeBridgeModal(); });

  showView('home');
})();

/* ===== [2026-09 신설] 검색 + 정렬 (동료 피드백 반영) ===== */
(function(){
  function rowsIn(page){
    // 해당 페이지의 활성 패널 내 rk-row 수집
    return Array.from(document.querySelectorAll('.rk-panel'))
      .filter(function(p){ return p.id && p.id.indexOf(page+'-')===0; });
  }
  function scoreOf(row){
    var el=row.querySelector('.rk-score'); if(!el) return -1;
    var v=parseFloat(el.textContent.replace(/[^\d.]/g,'')); return isNaN(v)?-1:v;
  }
  function nameOf(row){ return (row.getAttribute('data-entity')||'').trim(); }

  // 검색
  document.querySelectorAll('.rk-search').forEach(function(inp){
    inp.addEventListener('input', function(){
      var page=inp.getAttribute('data-page');
      var q=inp.value.trim().toLowerCase();
      rowsIn(page).forEach(function(panel){
        panel.querySelectorAll('[data-entity]').forEach(function(row){
          var hit = nameOf(row).toLowerCase().indexOf(q)>=0;
          row.setAttribute('data-search-hidden', (q==='' || hit) ? '0' : '1');
        });
      });
      if(window.__bridgeRepage) window.__bridgeRepage(page);
    });
  });

  // 정렬
  document.querySelectorAll('.rk-sort-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      var page=btn.getAttribute('data-page');
      var mode=btn.getAttribute('data-sort');
      // 버튼 활성표시 (같은 페이지 내)
      document.querySelectorAll('.rk-sort-btn[data-page="'+page+'"]').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      rowsIn(page).forEach(function(panel){
        var rows=Array.from(panel.querySelectorAll('[data-entity]'));
        if(rows.length<2) return;
        if(mode==='default'){
          rows.sort(function(a,b){ return (parseInt(a.getAttribute('data-idx')||0)) - (parseInt(b.getAttribute('data-idx')||0)); });
        } else if(mode==='score'){
          rows.sort(function(a,b){ return scoreOf(b)-scoreOf(a); }); // 높은 점수 먼저(N/R=-1은 뒤로)
        } else if(mode==='name'){
          rows.sort(function(a,b){ return nameOf(a).localeCompare(nameOf(b),'ko'); });
        }
        rows.forEach(function(r){ panel.appendChild(r); });
      });
      if(window.__bridgeRepage) window.__bridgeRepage(page);
    });
  });
})();

(function(){
  document.querySelectorAll('.rk-panel').forEach(function(panel){
    Array.from(panel.querySelectorAll('[data-entity]')).forEach(function(row,i){
      if(!row.getAttribute('data-idx')) row.setAttribute('data-idx', i);
    });
  });
})();


/* ===== [2026-09] 페이지네이션 + 검색/정렬 연동 (동료 피드백 ④) ===== */
(function(){
  var PAGE_SIZE = 20;

  function visibleRows(panel){
    // 검색으로 display:none 처리되지 않은 행만 대상
    return Array.from(panel.querySelectorAll('[data-entity]'))
      .filter(function(r){ return r.getAttribute('data-search-hidden')!=='1'; });
  }

  function applyPaging(panel){
    if(panel.classList.contains('hidden')) return;
    var rows = visibleRows(panel);
    var shown = parseInt(panel.getAttribute('data-shown')||PAGE_SIZE, 10);
    rows.forEach(function(r,i){
      // 검색으로 숨긴 건 그대로 숨김, 그 외에는 페이지 범위만 표시
      if(r.getAttribute('data-search-hidden')==='1'){ r.style.display='none'; return; }
      r.style.display = (i < shown) ? '' : 'none';
    });
    // 기존 더보기 버튼 제거
    var old = panel.querySelector('.rk-more-wrap'); if(old) old.remove();
    if(rows.length > shown){
      var wrap=document.createElement('div'); wrap.className='rk-more-wrap';
      var btn=document.createElement('button'); btn.className='rk-more-btn';
      btn.textContent='더 보기';
      var cnt=document.createElement('span'); cnt.className='rk-more-count';
      cnt.textContent='('+shown+' / '+rows.length+')';
      btn.addEventListener('click', function(){
        panel.setAttribute('data-shown', Math.min(shown+PAGE_SIZE, rows.length));
        applyPaging(panel);
      });
      wrap.appendChild(btn); wrap.appendChild(cnt);
      panel.appendChild(wrap);
    }
  }

  // 전역 훅: 검색/정렬 후 호출
  window.__bridgeRepage = function(page){
    document.querySelectorAll('.rk-panel').forEach(function(panel){
      if(page && panel.id.indexOf(page+'-')!==0) return;
      panel.setAttribute('data-shown', PAGE_SIZE); // 검색·정렬 시 첫 페이지로 리셋
      applyPaging(panel);
    });
  };

  // 초기 적용
  document.querySelectorAll('.rk-panel').forEach(function(panel){
    panel.setAttribute('data-shown', PAGE_SIZE);
    applyPaging(panel);
  });

  // 탭 전환 시에도 적용 (seg-btn 클릭 후 패널이 보이게 되면)
  document.querySelectorAll('.seg-btn').forEach(function(b){
    b.addEventListener('click', function(){ setTimeout(function(){ window.__bridgeRepage(); }, 30); });
  });
})();


/* ===== [2026-09] 모바일 압축 카드: 탭하면 펼침 (데스크탑은 모달 유지) ===== */
(function(){
  function isMobile(){ return window.matchMedia('(max-width:600px)').matches; }
  document.querySelectorAll('.rk-row[data-entity]').forEach(function(row){
    row.addEventListener('click', function(e){
      if(!isMobile()) return;              // 데스크탑: 기존 모달 동작에 맡김
      // 모바일: 펼침 토글, 모달 억제
      e.stopPropagation();
      e.preventDefault();
      row.classList.toggle('rk-open');
    }, true);                              // capture 단계에서 먼저 가로채 모달 차단
  });
})();

'''

HEAD = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BRIDGE — Reputation is a signal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,400;1,400;1,500&display=swap" rel="stylesheet">
<style>
{CSS}
{EXTRA_CSS}
</style>
</head>
<body>'''

HEADER = f'''
{ticker_html()}
<nav class="nav on-dark">
  <div class="nav-inner">
    <a class="logo" href="#" data-view="home">BRIDGE <span class="op">SIGNALBRIDGE</span></a>
    <div class="nav-menu">{nav_html()}</div>
    <div class="nav-right">
      {"".join(f'<a class="nav-util" href="#" data-view="{uv}">{ul}</a>' for ul, uv in NAV_UTIL_ITEMS)}
      <button class="nav-toggle" aria-label="메뉴 열기">&#9776;</button>
    </div>
  </div>
</nav>
<div class="mobile-menu" id="mobileMenu">
  <div class="mobile-menu-top"><span class="logo">BRIDGE</span><button class="mm-close" id="mmClose" aria-label="닫기">&times;</button></div>
  {mobile_menu_html()}
  <a href="#" data-view="about" class="mm-util">회사소개</a>
  <a href="#" data-view="trust" class="mm-util">신뢰등급이란?</a>
</div>'''

FULL = HEAD + HEADER + view_home() + THIS_WEEK_VIEW + CPR_VIEW + GOV_VIEW + UNI_VIEW + STAR_VIEW + METHODOLOGY_VIEW + TRUST_VIEW + ABOUT_VIEW + DATA_EXTRACTION_VIEW + f'<script>{JS}</script></body></html>'

out_path = os.path.join(_HERE, "site/bridge_full_site.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(FULL)
print("written", out_path, len(FULL), "bytes")
