import os
_HERE = os.path.dirname(os.path.abspath(__file__))
import json, html, sys
sys.path.insert(0, _HERE)
import build_pilot

with open(os.path.join(_HERE, "data/bridge_data_v2.json"), encoding="utf-8") as f:
    DATA = json.load(f)

WEEK = DATA["week"]
# 발행일 기반 자동 VOL/WEEK/날짜 표기 (발행일만 바꾸면 자동 갱신)
import datetime as _dt
from zoneinfo import ZoneInfo as _ZoneInfo
_PUB = DATA.get("published") or DATA.get("verifiedAt") or "auto"
# published가 "auto"이거나 비어있으면 빌드하는 날(오늘)을 자동 사용 — 재배포 시 날짜 자동 갱신
if _PUB in ("auto", "", None):
    _pubdate = _dt.datetime.now(_ZoneInfo('Asia/Seoul')).date()
else:
    _pubdate = _dt.date.fromisoformat(_PUB)
_iso = _pubdate.isocalendar()
_MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
HERO_VOL = f"VOL. 01 — WEEK {_iso[1]}"
HERO_DATE = f"SEOUL · {_pubdate.day:02d} {_MONTHS[_pubdate.month-1]} {_pubdate.year}"
CPR, STAR, GOV = DATA["CPR"], DATA["STAR"], DATA["GOV"]

OUT = os.path.join(_HERE, "site")
os.makedirs(OUT, exist_ok=True)

# ---------- helpers ----------
def esc(s): return html.escape(str(s))

def subset(pool, subcat, limit):
    filtered = [r for r in pool if r["subcat"] == subcat]
    filtered = sorted(filtered, key=lambda r: -r["totalScore"])
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

# ---------- LIVE ticker: real entities, cross-arranged CPR/STAR/GOV, no fabricated scores ----------
# ---------- LIVE ticker: real entities, cross-arranged CPR/STAR/GOV, no fabricated scores ----------
def ticker_items():
    """Real entities only. Shows actual score for the 101 real-measured entries
    (REAL_PILOT_CASES), N/R for everything else — no fabricated deltas."""
    cpr = build_pilot.CPR_REAL
    star = build_pilot.STAR_REAL
    gov = build_pilot.GOV_REAL
    items = []
    n = max(len(cpr), len(star), len(gov))
    for i in range(n):
        if i < len(cpr): items.append(("CPR", cpr[i][0]))
        if i < len(star): items.append(("ENT", star[i][0]))
        if i < len(gov): items.append(("GOV", gov[i][0]))
    return items

def ticker_html():
    items = ticker_items()
    def item_span(tag, name):
        pilot = build_pilot.REAL_PILOT_CASES.get(name)
        if pilot:
            return f'<span><b>{tag}</b>{esc(name)} <span class="t-score">{pilot["score"]}</span></span>'
        return f'<span><b>{tag}</b>{esc(name)} <span class="t-flat">N/R</span></span>'
    spans = [item_span(tag, name) for tag, name in items]
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
    ("HOME", "index.html", None),
    ("THIS WEEK", "this-week.html", None),
    ("CPR", "cpr.html", [("CPR B-T100","cpr.html#t100"),("CPR B-BC50","cpr.html#bc50"),("CPR B-BB50","cpr.html#bb50")]),
    ("GOV", "gov.html", [("GOV B-T100","gov.html#t100"),("GOV B-M40","gov.html#m40"),("GOV B-C60","gov.html#c60")]),
    ("UNI", "uni.html", [("UNI B-T100","uni.html#t100"),("UNI B-U60","uni.html#u60"),("UNI B-C40","uni.html#c40")]),
    ("ENT", "star.html", [("ENT B-T100","star.html#t100"),("ENT B-AM40","star.html#am45"),("ENT B-AW40","star.html#aw45"),("ENT B-AN20","star.html#an10")]),
]
# 상단 우측 유틸 메뉴 항목 (INDEX·데이터추출·신뢰등급이란?)
NAV_UTIL_ITEMS = [
    ("INDEX", "methodology.html"),
    ("DATA TRACE", "data-extraction.html"),
    ("신뢰등급", "trust.html"),
]

def nav_html(active):
    parts = []
    for label, href, sub in NAV_ITEMS:
        act = "active" if label == active else ""
        if sub:
            subitems = "".join(f'<a href="{s_href}"><span>{i:02d}</span>{s_label}</a>' for i, (s_label, s_href) in enumerate(sub, 1))
            parts.append(f'''
      <div class="nav-item has-drop">
        <a href="{href}" class="{act}">{label}<i aria-hidden="true"></i></a>
        <div class="nav-drop"><div class="nav-drop-kicker">{label} INDEX SERIES</div>{subitems}</div>
      </div>''')
        else:
            parts.append(f'<div class="nav-item"><a href="{href}" class="{act}">{label}</a></div>')
    return "".join(parts)

def head(title, desc=None):
    desc = desc or "BRIDGE 브랜드 평판 지수 — 화제성이 아니라 반응·책임·회복을 6개 축(B·R·I·D·G·E)으로 진단하는 평판 지수. 기업·공공기관·대학·공인을 공개 데이터로 평가합니다."
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="BRIDGE">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;600;700&family=Nanum+Myeongjo:wght@400;700;800&family=Source+Serif+4:ital,wght@0,400;1,400;1,500&display=swap" rel="stylesheet">
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=20261014">
<link rel="apple-touch-icon" href="/icons/bridge-192.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#121923">
<link rel="stylesheet" href="style.css?v=20261015-editorial">
</head>
<body>'''

def base_header(active):
    nav_cls = "nav on-dark" if active == "HOME" else "nav"
    return f'''
{ticker_html()}
<nav class="{nav_cls}">
  <div class="nav-inner">
    <a class="logo" href="index.html">SIGNALBRIDGE</a>
    <div class="nav-menu">{nav_html(active)}</div>
    <div class="nav-right">
      {"".join(f'<a class="nav-util" href="{u_href}">{u_label}</a>' for u_label, u_href in NAV_UTIL_ITEMS)}
      <button class="nav-toggle" aria-label="메뉴 열기">&#9776;</button>
    </div>
  </div>
</nav>
<div class="mobile-menu" id="mobileMenu">
  <div class="mobile-menu-top"><span class="logo">BRIDGE</span><button class="mm-close" id="mmClose" aria-label="닫기">&times;</button></div>
  {"".join(f'<div class="mm-group"><a href="{href}">{label}</a>' + (''.join(f'<a class="mm-child" href="{s_href}">{s_label}</a>' for s_label,s_href in sub) if sub else '') + '</div>' for label, href, sub in NAV_ITEMS)}
  {"".join(f'<a href="{u_href}" class="mm-util">{u_label}</a>' for u_label, u_href in NAV_UTIL_ITEMS)}
  <a href="about.html" class="mm-util">시그널브릿지 회사소개</a>
</div>'''

PRE_INDEX_NOTICE = "본 결과는 BRIDGE 모형의 초기 데이터 파이프라인을 검증하기 위한 예비지수이며, 데이터 범위와 신뢰등급에 따라 순위가 수정될 수 있습니다."

from presentation.public_copy import FOOTER_COPY, INDEX, TRUST, TRACE, ABOUT
FOOTER_NOTES = {"index": FOOTER_COPY}

def footer(page_key):
    note = FOOTER_NOTES["index"]  # 모든 페이지 하단 문구를 SignalBridge 소개로 통일
    return f'''
<footer>
  <div class="wrap">
    <div class="footer-top">
      <span class="logo">SIGNALBRIDGE</span>
      <div class="footer-links">
        <a href="about.html">시그널브릿지 회사소개</a>
        <a href="contact.html">문의 | 이의제기</a>
      </div>
    </div>
    <p class="footer-op">BRIDGE is developed and operated by SignalBridge.</p>
    <p class="footer-note">{note}</p>
  </div>
</footer>
<script src="script.js?v=20261015-editorial" defer></script>
</body>
</html>'''

# ---------- INDEX (THIS WEEK) — cinematic hero per user's design-reference screenshot ----------
# SUPERSEDES the earlier verbatim splice of the "real" navy/card index.html. The user has
# now explicitly directed the visual design back to this cinematic dark hero (matching
# their original reference screenshots), which is a different, later design iteration than
# the navy/card source files confirmed earlier. The underlying data/content logic (leader
# card pulling from real CPR data, ticker, nav) is unchanged — only the visual skin.
def home_top5_html():
    """홈 우측: 도메인별 공개 점수 TOP5 + 주간 업앤다운(이력 있는 것만)."""
    import uni_real as _uni
    R = build_pilot.REAL_PILOT_CASES
    cpr_set = set(t[0] for t in build_pilot.CPR_REAL)
    gov_set = set(t[0] for t in build_pilot.GOV_REAL)
    ent_set = set(t[0] for t in build_pilot.STAR_REAL)
    uni_set = set(t[0] for t in _uni.UNI_4YEAR) | set(t[0] for t in _uni.UNI_2YEAR)
    def measured_cnt(n):
        return len([v for v in R[n]["dims"].values() if v is not None])
    def top5(names):
        pub = [(n, R[n]["score"]) for n in names if n in R and measured_cnt(n) >= 2]
        return sorted(pub, key=lambda x: (-x[1], x[0]))[:5]
    def wow_html(name):
        rec = R.get(name, {})
        hist = rec.get("history")
        if hist:
            prev = hist[-1].get("score")
            if prev is not None:
                d = round(rec["score"] - prev, 1)
                if d > 0:  return f'<span class="t5-up">▲ {abs(d)}</span>'
                if d < 0:  return f'<span class="t5-down">▼ {abs(d)}</span>'
                return '<span class="t5-flat">—</span>'
        return '<span class="t5-flat">—</span>'
    domains = [("CPR", cpr_set, "cpr.html"), ("GOV", gov_set, "gov.html"),
               ("UNI", uni_set, "uni.html"), ("ENT", ent_set, "star.html")]
    blocks = []
    for tag, names, href in domains:
        rows = top5(names)
        if rows:
            lis = "".join(
                f'<li><span class="t5-nm">{esc(n)}</span>'
                f'<span class="t5-sc">{sc}</span>{wow_html(n)}</li>'
                for n, sc in rows)
        else:
            lis = '<li class="t5-empty">공개 대상 없음 (근거 축 2개 미만)</li>'
        blocks.append(
            f'<a class="t5-block" href="{href}">'
            f'<div class="t5-head">{tag} <span class="t5-more">TOP 5 →</span></div>'
            f'<ol class="t5-list">{lis}</ol></a>')
    return '<div class="hero-top5">' + "".join(blocks) + '</div>'

def build_hero():
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
        ("CPR", cpr_count, "cpr.html", f"B2C {cpr_b2c} · B2B {cpr_b2b}"),
        ("GOV", gov_count, "gov.html", f"중앙 {len(GOV_M40)} · 지자체·공공 {len(GOV_C60)}"),
        ("UNI", uni_count, "uni.html", f"4년제 {len(UNI_4YEAR)} · 2년제 {len(UNI_2YEAR)}"),
        ("ENT", star_count, "star.html", f"남 {star_am} · 여 {star_aw} · 신인 {star_an}"),
    ]
    tower_html = "".join(f'''
      <div class="tower-card">
        <span class="tc-lbl">{tag} / 표본<br><span class="tc-hook">{hook}</span></span>
        <span class="tc-val">{count}</span>
        <span class="tc-foot">TRUST N/R</span>
      </div>''' for tag, count, href, hook in tower_rows)
    return f'''
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
      <div class="hero-meta" id="heroSeoulClock">{HERO_VOL}<br>{HERO_DATE}</div>
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
        <div class="hero-tower-inline">{home_top5_html()}</div>
        <div class="hero-actions"><a class="btn" href="this-week.html">EXPLORE THIS WEEK ↓</a><a class="btn publicity-link" href="publicity.html">PUBLICITY</a></div>
      </div>
    </div>
  </div>
</section>'''

index_html = head("BRIDGE — Reputation is a signal") + base_header("HOME") + build_hero() + footer("index")
with open(f"{OUT}/index.html","w",encoding="utf-8") as f: f.write(index_html)

this_week_html = head("BRIDGE — THIS WEEK") + base_header("THIS WEEK") + build_pilot.this_week_digest_html() + footer("index")
with open(f"{OUT}/this-week.html","w",encoding="utf-8") as f: f.write(this_week_html)

# ---------- CPR / STAR / GOV / UNI — REAL entities (PILOT data), same principle site-wide ----------
# Per explicit user instruction: apply the PILOT approach (real names, objectively
# sourced, BRIDGE score left N/R) to the MAIN pages themselves, replacing the earlier
# synthetic/fictional 100-entity demo dataset. Light on-page explanation of the BRIDGE
# model + extraction rationale per domain; the detailed proprietary methodology lives
# in the white paper (see build_pilot.py MODEL_BLURBS and the whitepaper source).

def real_list_page(active, page, title, note, model_blurb, seg_html, panels_html, footer_key, period_unit="week", desc=None):
    return head(title, desc) + base_header(active) + f'''
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
      <div class="ranking-workspace" data-ranking-page="{page}">
        {seg_html}
        <div class="ranking-panels">{panels_html}</div>
      </div>
    </div>
  </section>
</div>''' + footer(footer_key)

# --- CPR: T100 / BC50(consumer-facing) / BB50(business-facing) ---
cpr_segs = [("t100","CPR B-T100",len(build_pilot.CPR_REAL)), ("bc50","CPR B-BC50",len([1 for e in build_pilot.CPR_REAL if e[6]=="B2C"])), ("bb50","CPR B-BB50",len([1 for e in build_pilot.CPR_REAL if e[6]=="B2B"]))]
cpr_seg_html = seg_control("t100", cpr_segs, "cpr")
cpr_panels_html = (
    f'<div class="rk-panel" id="cpr-t100">{build_pilot.cpr_rows()}</div>'
    f'<div class="rk-panel hidden" id="cpr-bc50">{build_pilot.cpr_rows("B2C")}</div>'
    f'<div class="rk-panel hidden" id="cpr-bb50">{build_pilot.cpr_rows("B2B")}</div>'
)
cpr_html = real_list_page(
    "CPR", "cpr", "CPR — 시장의 소음을 걷어낸 진짜 가치, Corporate",
    "대한민국을 대표하는 상장 기업 100곳, 그 이면의 진짜 평판을 읽어냅니다. 산업별 특성에 꼭 맞게 "
    "전체 기업(B-T100), 소비자 직접접점 기업(B-BC50), 기업·산업재 중심 기업(B-BB50) 3가지 기준으로 세분화하여 "
    "가장 유의미한 결과를 보여드립니다. 지금 보시는 데이터는 BRIDGE 모델의 정밀한 알고리즘을 통해 "
    "도출되는 평판 지표입니다. 억지로 점수를 채워 순위를 고정하는 낡은 방식은 지양합니다. 검증된 데이터에 따라 "
    "평판 지수가 어떻게 갱신되는지, 그 정직한 변화 과정을 투명하게 경험해 보세요.",
    build_pilot.MODEL_BLURBS["CPR"],
    cpr_seg_html, cpr_panels_html, footer_key="cpr", desc='BRIDGE CPR — 코스피·코스닥 상장기업의 공중관계 평판 지수. 시가총액·ESG·논란·행동유발을 6개 축으로 진단합니다.'
)
cpr_html = cpr_html.replace("</body>", build_pilot.BRIDGE_MODAL_HTML + "</body>")
with open(f"{OUT}/cpr.html","w",encoding="utf-8") as f: f.write(cpr_html)

# --- ENT: T100 / AM40(남) / AW40(여) / AN20(신인급) ---
star_segs = [("t100","STAR B-T100",len(build_pilot.STAR_REAL)),
             ("am45","ENT B-AM40",40),
             ("aw45","ENT B-AW40",40),
             ("an10","ENT B-AN20",20)]
star_seg_html = seg_control("t100", star_segs, "star")
star_panels_html = (
    f'<div class="rk-panel" id="star-t100">{build_pilot.star_rows()}</div>'
    f'<div class="rk-panel hidden" id="star-am45">{build_pilot.star_rows("AM")}</div>'
    f'<div class="rk-panel hidden" id="star-aw45">{build_pilot.star_rows("AW")}</div>'
    f'<div class="rk-panel hidden" id="star-an10">{build_pilot.star_rows("AN")}</div>'
)
star_html = real_list_page(
    "ENT", "star", "ENT — 스포트라이트 이면에서 증명된 품격, 광고모델·공인",
    "대중의 시선이 머무는 100명의 공인, 그 화려한 스포트라이트 이면에 자리한 진짜 평판을 읽어냅니다. "
    "의미 없는 통합 순위를 지양하고 대상의 특성을 고려하여 전체(B-T100), 남자 광고모델(B-AM40), "
    "여자 광고모델(B-AW40), 라이징 스타(B-AN20)의 네 가지 시선으로 평판을 입체적으로 분해합니다. 본 지수는 기존 매체들이 "
    "관행적으로 발표하던 기성 평판 순위를 일절 인용하지 않은 독자적 지표입니다. 철저한 제로 베이스에서 출발하여, "
    "출처가 명확하고 검증 가능한 데이터만이 누적됨에 따라 지수가 갱신되는 과정을 투명하게 공개합니다.",
    build_pilot.MODEL_BLURBS["STAR"],
    star_seg_html, star_panels_html, footer_key="star", desc='BRIDGE ENT — 광고모델·공인의 공중 평판 지수. SNS 도달·논란·화제성을 6개 축으로 진단합니다.'
)
star_html = star_html.replace("</body>", build_pilot.BRIDGE_MODAL_HTML + "</body>")
with open(f"{OUT}/star.html","w",encoding="utf-8") as f: f.write(star_html)

# --- GOV: T100 / M40(중앙행정기관 각부) / C60(지자체·공공기관) ---
from gov_real import GOV_M40, GOV_C60
gov_segs = [("t100","GOV B-T100",len(GOV_M40)+len(GOV_C60)), ("m40","GOV B-M40",len(GOV_M40)), ("c60","GOV B-C60",len(GOV_C60))]
gov_seg_html = seg_control("t100", gov_segs, "gov")
gov_panels_html = (
    f'<div class="rk-panel" id="gov-t100">{build_pilot.gov_t100_rows()}</div>'
    f'<div class="rk-panel hidden" id="gov-m40">{build_pilot.gov_m40_rows()}</div>'
    f'<div class="rk-panel hidden" id="gov-c60">{build_pilot.gov_c60_rows()}</div>'
)
gov_html = real_list_page(
    "GOV", "gov", "GOV — 공중의 일상과 교감하는 신뢰의 파동, 공공기관",
    "정부 부처와 지자체, 공기업을 아울러 대한민국 공공 영역을 대표하는 100대 기관의 실질적인 평판을 심층 진단합니다. "
    "기관의 역할과 성격이 다름에도 획일적으로 순위를 매기는 관행을 탈피하기 위해, 전체 통합(B-T100), "
    "중앙행정기관(B-M40), 지자체 및 공공기관(B-C60)으로 그룹을 나누어 맞춤형 분석 결과를 제공합니다. "
    "현재 공개된 수치는 고도화된 BRIDGE 분석 체계를 통해 도출되는 평판 지표입니다. 이 지표는 완성된 BRIDGE "
    "알고리즘이 실시간으로 구동되어 산출하는 최종 결과물입니다. 베일에 싸인 데이터가 아니라, 명확히 입증할 수 있는 "
    "실체적 데이터가 누적됨에 따라 공공기관 평판의 궤적은 스스로 정직하게 움직입니다.",
    build_pilot.MODEL_BLURBS["GOV"],
    gov_seg_html, gov_panels_html, footer_key="gov", desc='BRIDGE GOV — 중앙행정기관·공공기관의 공공소통 평판 지수. 예산·경영평가·중대재해·이용지표를 6개 축으로 진단합니다.'
)
gov_html = gov_html.replace("</body>", build_pilot.BRIDGE_MODAL_HTML + "</body>")
with open(f"{OUT}/gov.html","w",encoding="utf-8") as f: f.write(gov_html)

# --- UNI: dynamic T100 / U60(4년제) / C40(전문대) ---
_uni43_path = os.path.join(_HERE, "data", "latest", "uni_latest.json")
_uni43 = json.load(open(_uni43_path, encoding="utf-8")) if os.path.exists(_uni43_path) else {"rankings": {}, "waiting": []}
_uni_rankings = _uni43.get("rankings", {})
_uni_t100, _uni_u60, _uni_c40 = _uni_rankings.get("T100", []), _uni_rankings.get("U60", []), _uni_rankings.get("C40", [])
_uni_waiting = _uni43.get("waiting", [])[:20]
uni_segs = [("t100","UNI B-T100",len(_uni_t100)), ("u60","UNI B-U60",len(_uni_u60)), ("c40","UNI B-C40",len(_uni_c40)), ("waiting","진입 대기",len(_uni_waiting))]
uni_seg_html = seg_control("t100", uni_segs, "uni")
uni_panels_html = (
    f'<div class="rk-panel" id="uni-t100">{build_pilot.uni_rows_dynamic(_uni_t100)}</div>'
    f'<div class="rk-panel hidden" id="uni-u60">{build_pilot.uni_rows_dynamic(_uni_u60)}</div>'
    f'<div class="rk-panel hidden" id="uni-c40">{build_pilot.uni_rows_dynamic(_uni_c40)}</div>'
    f'<div class="rk-panel hidden" id="uni-waiting">{build_pilot.uni_rows_dynamic(_uni_waiting)}</div>'
)
uni_html = real_list_page(
    "UNI", "uni", "UNI — 상아탑이 뿜어내는 고유한 철학의 온도, 대학",
    "대한민국 고등교육 생태계를 견인하는 100대 대학(4년제 60개교, 2년제 40개교)의 실질적인 평판을 심층 진단합니다. "
    "학제가 다른 교육 기관들을 획일적으로 섞어 줄 세우는 관행을 탈피하기 위해, 전체 통합(B-T100), 4년제 대학(B-U60), "
    "2년제 대학(B-C40)으로 그룹을 나누어 맞춤형 분석 결과를 제공합니다. 현재 공개된 수치는 고도화된 BRIDGE 분석 "
    "체계를 통해 도출되는 평판 지표입니다. 출처가 불분명한 이면의 데이터는 철저히 배제하며, 오직 투명하게 공개된 "
    "검증 데이터만을 바탕으로 지수가 갱신되는 과정을 명확히 공개합니다.",
    build_pilot.MODEL_BLURBS["UNI"],
    uni_seg_html, uni_panels_html, footer_key="index", period_unit="month",
    desc="BRIDGE UNI — 전국 대학의 브랜드 평판 지수. 전임교원 여건·경쟁률·논란을 재학생 경험 중심으로 진단합니다."
)
uni_html = uni_html.replace("</body>", build_pilot.BRIDGE_MODAL_HTML + "</body>")
with open(f"{OUT}/uni.html","w",encoding="utf-8") as f: f.write(uni_html)

# ---------- INDEX(methodology) 페이지: 5단 구성 (철학·무기·렌즈+표·원칙·자정) ----------
INDEX_BODY = INDEX
methodology_html = head("INDEX — BRIDGE 분석의 기준", "현재 위치·관계 구성·변화 방향으로 읽는 BRIDGE의 정의와 분석 틀.") + base_header("INDEX") + INDEX_BODY + footer("methodology")
with open(f"{OUT}/methodology.html","w",encoding="utf-8") as f: f.write(methodology_html)

# ---------- trust: grounded in the confirmed white paper §14 (신뢰등급) ----------
# Previous drafts used my own approximation of A~D. This version uses the actual
# grade criteria from "BRIDGE 브랜드평판지수 방법론 및 신뢰성 백서" §14, including the
# N/R grade that my earlier drafts omitted entirely.
trust_html = head("신뢰등급 — 근거의 충실성", "평판의 수준과 측정 근거의 충실성을 구분해 읽습니다.") + base_header("INDEX") + TRUST + footer("index")
with open(f"{OUT}/trust.html","w",encoding="utf-8") as f: f.write(trust_html)

# ---------- contact: 문의|이의제기 (Web3Forms 실제 전송 + 완료 표시) ----------
contact_html = head("BRIDGE — 문의·이의제기", "BRIDGE 지수에 대한 문의 또는 이의제기를 접수합니다.") + base_header("INDEX") + '''
<header class="list-hero-photo hero-methodology">
  <div class="wrap">
    <div class="about-kicker">CONTACT · 소통 창구</div>
    <h1 class="idx-hero-h">문의 · 이의제기</h1>
  </div>
</header>
<section class="section">
  <div class="wrap" style="max-width:760px">
    <div id="ctFormWrap">
      <p class="about-body">BRIDGE 지수에 대한 <b>문의</b>, 또는 대상 식별 오류·데이터 누락·산식 적용 오류 등에 대한 <b>이의제기</b>를 접수합니다. 유형을 선택하고 내용을 작성한 뒤 보내기를 누르시면 접수됩니다.</p>
      <div class="ct-form">
        <div class="ct-type">
          <button type="button" class="ct-type-btn active" data-type="문의">문의</button>
          <button type="button" class="ct-type-btn" data-type="이의제기">이의제기</button>
        </div>
        <label class="ct-label">보내는 분 (선택)</label>
        <input type="text" id="ctName" class="ct-input" placeholder="이름 또는 소속 (선택)">
        <label class="ct-label">회신받을 이메일 (선택)</label>
        <input type="email" id="ctEmail" class="ct-input" placeholder="example@email.com (선택)">
        <label class="ct-label">내용 <span class="ct-count"><span id="ctLen">0</span> / 1000자</span></label>
        <textarea id="ctBody" class="ct-textarea" maxlength="1000" placeholder="문의 또는 이의제기 내용을 1000자 이내로 작성해 주세요."></textarea>
        <button type="button" id="ctSend" class="ct-send">보내기</button>
        <p class="ct-note">보내기를 누르면 작성하신 내용이 시그널브릿지로 접수됩니다.</p>
      </div>
    </div>
    <div id="ctDone" style="display:none; text-align:center; padding:60px 0;">
      <div style="font-size:52px; margin-bottom:20px;">✓</div>
      <h2 class="about-h2" style="border:none;">문의 | 이의제기 내용이 전달되었습니다.</h2>
      <p class="about-body" style="max-width:560px; margin:16px auto 0;">소중한 의견 감사합니다. 검토 후 회신 이메일을 남겨주신 경우 순차적으로 답변드리겠습니다.</p>
      <a href="index.html" class="ct-send" style="display:inline-block; width:auto; padding:12px 32px; margin-top:28px; text-decoration:none;">홈으로 돌아가기</a>
    </div>
  </div>
</section>
<script>
(function(){
  var type="문의";
  document.querySelectorAll(".ct-type-btn").forEach(function(b){
    b.addEventListener("click",function(){
      document.querySelectorAll(".ct-type-btn").forEach(function(x){x.classList.remove("active");});
      b.classList.add("active"); type=b.getAttribute("data-type");
    });
  });
  var body=document.getElementById("ctBody"), len=document.getElementById("ctLen");
  body.addEventListener("input",function(){ len.textContent=body.value.length; });

  document.getElementById("ctSend").addEventListener("click",function(){
    var content=body.value.trim();
    if(!content){ alert("내용을 입력해 주세요."); return; }
    var btn=this; btn.disabled=true; btn.textContent="전송 중...";
    var name=document.getElementById("ctName").value.trim();
    var email=document.getElementById("ctEmail").value.trim();
    var payload={
      access_key: "f6aecbb5-c813-4114-8de2-fa173191408b",
      subject: "[BRIDGE "+type+"]"+(name?(" "+name):""),
      from_name: "BRIDGE 문의·이의제기",
      "유형": type,
      "보내는 분": name || "(미기재)",
      "회신 이메일": email || "(미기재)",
      "내용": content
    };
    fetch("https://api.web3forms.com/submit",{
      method:"POST",
      headers:{"Content-Type":"application/json", "Accept":"application/json"},
      body: JSON.stringify(payload)
    }).then(function(r){ return r.json(); }).then(function(res){
      if(res.success){
        document.getElementById("ctFormWrap").style.display="none";
        document.getElementById("ctDone").style.display="block";
        window.scrollTo(0,0);
      } else {
        alert("전송에 실패했습니다. 잠시 후 다시 시도해 주세요."); btn.disabled=false; btn.textContent="보내기";
      }
    }).catch(function(){
      alert("전송 중 오류가 발생했습니다. 네트워크를 확인해 주세요."); btn.disabled=false; btn.textContent="보내기";
    });
  });
})();
</script>
''' + footer("contact")
with open(f"{OUT}/contact.html","w",encoding="utf-8") as f: f.write(contact_html)

# ---------- about: grounded in 전략기획서 v0.3 §1.4 (운영회사와 브랜드 체계) + §15/16 ----------
about_html = head("SIGNALBRIDGE — 회사소개", "데이터를 관계로, 관계를 의미로. 시그널브릿지의 관점과 운영 원칙.") + base_header("INDEX") + ABOUT + footer("index")
with open(f"{OUT}/about.html","w",encoding="utf-8") as f: f.write(about_html)

print("pages written:", os.listdir(OUT))

# ---------- 데이터 추출 (DATA EXTRACTION): cross-domain light explanation ----------
# PILOT's original content is now absorbed into the CPR/STAR/GOV/UNI pages themselves
# (real names, N/R grade). This page is the light, on-site explanation of HOW BRIDGE
# extracts and reasons about data across all four domains; the detailed proprietary
# methodology (the actual know-how) lives in the white paper §21-24, not here.
import importlib
importlib.reload(build_pilot)
data_extraction_html = head("DATA TRACE — 근거의 맥락", "공개자료의 시점·귀속·유효성과 비교 가능성을 읽는 원칙.") + base_header("INDEX") + TRACE + footer("index")
with open(f"{OUT}/data-extraction.html","w",encoding="utf-8") as f: f.write(data_extraction_html)

# site_fix is retained as a compatibility mirror by the legacy deployment layout.
# Keep it synchronized so an old directly-addressable URL cannot expose stale copy.
import shutil as _shutil
_site_fix = os.path.join(OUT, "site_fix")
os.makedirs(_site_fix, exist_ok=True)
for _public_file in ("cpr.html", "gov.html", "uni.html", "star.html", "methodology.html",
                     "this-week.html", "index.html", "contact.html", "about.html", "trust.html", "data-extraction.html", "script.js", "style.css"):
    _shutil.copy2(os.path.join(OUT, _public_file), os.path.join(_site_fix, _public_file))
print("data-extraction.html written")

# PUBLICITY is built from the same brand shell, without internal score inputs.
from publicity.build import build_publicity
build_publicity(head, base_header, footer)
