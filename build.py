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
_PUB = DATA.get("published") or DATA.get("verifiedAt") or "auto"
# published가 "auto"이거나 비어있으면 빌드하는 날(오늘)을 자동 사용 — 재배포 시 날짜 자동 갱신
if _PUB in ("auto", "", None):
    _pubdate = _dt.date.today()
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
    ("CPR", "cpr.html", [("CPR B-T100","cpr.html#t100"),("CPR B-BC70","cpr.html#bc70"),("CPR B-BB30","cpr.html#bb30")]),
    ("GOV", "gov.html", [("GOV B-T100","gov.html#t100"),("GOV B-M40","gov.html#m40"),("GOV B-C60","gov.html#c60")]),
    ("UNI", "uni.html", [("UNI B-T100","uni.html#t100"),("UNI B-U60","uni.html#u60"),("UNI B-C40","uni.html#c40")]),
    ("ENT", "star.html", [("ENT B-T100","star.html#t100"),("ENT B-AM45","star.html#am45"),("ENT B-AW45","star.html#aw45"),("ENT B-AN10","star.html#an10")]),
]
# 상단 우측 유틸 메뉴 항목 (INDEX·데이터추출·신뢰등급이란?)
NAV_UTIL_ITEMS = [
    ("INDEX", "methodology.html"),
    ("신뢰등급 | 데이터추출", "trust.html"),
]

def nav_html(active):
    parts = []
    for label, href, sub in NAV_ITEMS:
        act = "active" if label == active else ""
        if sub:
            subitems = "".join(f'<a href="{s_href}">{s_label}</a>' for s_label, s_href in sub)
            parts.append(f'''
      <div class="nav-item has-drop">
        <a href="{href}" class="{act}">{label}</a>
        <div class="nav-drop">{subitems}</div>
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
<link rel="stylesheet" href="style.css">
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
  {"".join(f'<a href="{href}">{label}</a>' for label, href, sub in NAV_ITEMS)}
  {"".join(f'<a href="{u_href}" class="mm-util">{u_label}</a>' for u_label, u_href in NAV_UTIL_ITEMS)}
  <a href="about.html" class="mm-util">시그널브릿지 회사소개</a>
</div>'''

PRE_INDEX_NOTICE = "본 결과는 BRIDGE 모형의 초기 데이터 파이프라인을 검증하기 위한 예비지수이며, 데이터 범위와 신뢰등급에 따라 순위가 수정될 수 있습니다."

FOOTER_NOTES = {
    "index": "시그널브릿지(SIGNALBRIDGE)는 브랜드의 가치가 단순히 &lsquo;얼마나 자주 입에 오르내리는지&rsquo;나 &lsquo;규모가 얼마나 큰지&rsquo;로 결정될 수 없다고 믿습니다. 화제성 뒤에 가려진 진짜 목소리를 입체적으로 읽어내기 위해, 시그널브릿지는 독자적인 분석 솔루션 &lsquo;BRIDGE 브랜드평판지수&rsquo;를 선보입니다. 하나의 뭉뚱그려진 점수로 모든 대상을 줄 세우는 방식은 이제 의미가 없습니다. 시그널브릿지는 평가 대상을 기업(CPR), 공공기관(GOV), 대학(UNI), 공인(ENT)의 4개 영역으로 세분화하여 각기 다른 환경과 맥락에 맞춘 &lsquo;맞춤형 잣대&rsquo;를 적용합니다. 나아가 도달(B), 반응(R), 정체성(I), 경험(D), 행동유발(G), 책임·지속(E)이라는 6개의 독립적인 렌즈로 브랜드를 둘러싼 정보와 데이터를 정밀 분해하여, 왜곡 없는 브랜드의 본연의 가치와 내일의 경쟁력을 투명하게 비춥니다.",
    "cpr": "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 화면에 표시된 대상명과 수치는 데모를 위해 임의로 구성한 가상의 예시이며, 실제 기업·인물·기관의 평판과 무관합니다. 본 지수는 공개 접근 데이터에 대한 통계적 분석이며, 사실판단·법률판단·투자판단을 대신하지 않습니다.",
    "star": "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 화면에 표시된 인물명과 수치는 데모를 위해 임의로 구성한 가상의 예시이며, 실제 인물의 평판과 무관합니다. 인물 이미지는 초상권 확인 전이므로 추상 데이터 아트로 대체했습니다.",
    "gov": "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 화면에 표시된 기관명과 수치는 데모를 위해 임의로 구성한 가상의 예시이며, 실제 기관의 평판과 무관합니다. 본 지수는 정책 찬반이 아닌 소통·설명책임에 대한 통계적 분석입니다.",
    "methodology": "본 페이지는 서비스 출시 전 제작된 샘플 화면입니다. 표기된 버전·정정 이력은 데모를 위한 예시입니다.",
    # trust/about: no real source provided yet — reuse the index/cpr-family note as the
    # closest match until the real files are confirmed (flagged in CHANGELOG).
    "trust": "",
    "about": "",
}

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
<script src="script.js" defer></script>
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
        return sorted(pub, key=lambda x: -x[1])[:5]
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
      <div class="hero-meta">{HERO_VOL}<br>{HERO_DATE}</div>
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
        <a class="btn" href="this-week.html">EXPLORE THIS WEEK ↓</a>
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
      {seg_html}
      {panels_html}
    </div>
  </section>
</div>''' + footer(footer_key)

# --- CPR: T100 / BC70(B2C) / BB30(B2B) ---
cpr_segs = [("t100","CPR B-T100",len(build_pilot.CPR_REAL)), ("bc70","CPR B-BC70",len([1 for e in build_pilot.CPR_REAL if e[6]=="B2C"])), ("bb30","CPR B-BB30",len([1 for e in build_pilot.CPR_REAL if e[6]=="B2B"]))]
cpr_seg_html = seg_control("t100", cpr_segs, "cpr")
cpr_panels_html = (
    f'<div class="rk-panel" id="cpr-t100">{build_pilot.cpr_rows()}</div>'
    f'<div class="rk-panel hidden" id="cpr-bc70">{build_pilot.cpr_rows("B2C")}</div>'
    f'<div class="rk-panel hidden" id="cpr-bb30">{build_pilot.cpr_rows("B2B")}</div>'
)
cpr_html = real_list_page(
    "CPR", "cpr", "CPR — 시장의 소음을 걷어낸 진짜 가치, Corporate",
    "대한민국을 대표하는 상장 기업 100곳, 그 이면의 진짜 평판을 읽어냅니다. 산업별 특성에 꼭 맞게 "
    "전체 기업(B-T100), 소비재 및 B2C(B-BC70), 기간산업 및 B2B(B-BB30) 3가지 기준으로 세분화하여 "
    "가장 유의미한 결과를 보여드립니다. 지금 보시는 데이터는 BRIDGE 모델의 정밀한 알고리즘을 통해 "
    "도출되는 평판 지표입니다. 억지로 점수를 채워 순위를 고정하는 낡은 방식은 지양합니다. 검증된 데이터에 따라 "
    "평판 지수가 어떻게 갱신되는지, 그 정직한 변화 과정을 투명하게 경험해 보세요.",
    build_pilot.MODEL_BLURBS["CPR"],
    cpr_seg_html, cpr_panels_html, footer_key="cpr", desc='BRIDGE CPR — 코스피·코스닥 상장기업의 공중관계 평판 지수. 시가총액·ESG·논란·행동유발을 6개 축으로 진단합니다.'
)
cpr_html = cpr_html.replace("</body>", build_pilot.BRIDGE_MODAL_HTML + "</body>")
with open(f"{OUT}/cpr.html","w",encoding="utf-8") as f: f.write(cpr_html)

# --- STAR: T100 / AM45(남) / AW45(여) / AN10(신인급) ---
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
star_html = real_list_page(
    "ENT", "star", "ENT — 스포트라이트 이면에서 증명된 품격, 광고모델·공인",
    "대중의 시선이 머무는 100명의 공인, 그 화려한 스포트라이트 이면에 자리한 진짜 평판을 읽어냅니다. "
    "의미 없는 통합 순위를 지양하고 대상의 특성을 고려하여 전체(B-T100), 남자 연예인(B-AM45), "
    "여자 연예인(B-AW45), 신인급(B-AN10)의 네 가지 시선으로 평판을 입체적으로 분해합니다. 본 지수는 기존 매체들이 "
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

# --- UNI: T100 / U60(4년제) / C40(2년제) ---
from uni_real import UNI_4YEAR, UNI_2YEAR
uni_segs = [("t100","UNI B-T100",len(UNI_4YEAR)+len(UNI_2YEAR)), ("u60","UNI B-U60",len(UNI_4YEAR)), ("c40","UNI B-C40",len(UNI_2YEAR))]
uni_seg_html = seg_control("t100", uni_segs, "uni")
uni_panels_html = (
    f'<div class="rk-panel" id="uni-t100">{build_pilot.uni_rows(UNI_4YEAR)}{build_pilot.uni_rows(UNI_2YEAR, is_2year=True)}</div>'
    f'<div class="rk-panel hidden" id="uni-u60">{build_pilot.uni_rows(UNI_4YEAR)}</div>'
    f'<div class="rk-panel hidden" id="uni-c40">{build_pilot.uni_rows(UNI_2YEAR, is_2year=True)}</div>'
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
INDEX_BODY = '''
<section class="section tw-about idx-about">
  <div class="wrap">
    <h2 class="tw-about-h">이 페이지에 대하여</h2>
    <p class="tw-about-p">우리는 순위를 흥정하지 않습니다. 과정 없는 결과는 기만이며, 산출 방식을 숨긴 점수는 신뢰할 수 없기 때문입니다. 상업적 압력으로부터 완벽히 격리된 이 공간에서, BRIDGE가 데이터를 정제하고 평판 신호를 추출하는 모든 뼈대를 투명하게 공개합니다.</p>
  </div>
</section>
<section class="section" style="padding-top:8px">
  <div class="wrap">
    <div class="dx-domain" id="philosophy">
      <div class="dx-head"><span class="dx-tag">철학</span><span class="dx-title">순위를 흥정하지 않습니다</span></div>
      <p class="dx-body">과정 없는 결과는 기만이며, 산출 방식을 숨긴 점수는 신뢰할 수 없습니다. &ldquo;팔리지 않는다&rdquo;는 것은 단순한 수사가 아닌 BRIDGE의 구체적인 약속입니다. 방문자가 늘어난다고 순위가 바뀌지 않으며, 광고비를 대가로 점수를 조정하지 않습니다. 이 공간은 트래픽이나 자본의 논리가 개입할 수 없도록, 우리의 모든 산식과 데이터 통제 과정을 남김없이 공개하는 절대적인 독립 구역입니다.</p>
    </div>

    <div class="dx-domain" id="why-free">
      <div class="dx-head"><span class="dx-tag">무기</span><span class="dx-title">독점적 데이터가 아닌 &lsquo;투명한 프로토콜&rsquo;</span></div>
      <p class="dx-body">BRIDGE의 권위는 우리만 아는 은밀한 데이터가 아니라, 누구나 검증할 수 있는 분석 프로토콜에서 나옵니다. 단순한 언급량으로 대상을 줄 세우지 않습니다. 브랜드 사전 구축, 감정 분류, 규모 보정, 시간축 처리 등 흩어진 데이터를 정제하고 진짜 평판 신호로 변환해 내는 이 정교한 해석 방법론 자체가 우리의 가장 강력한 자산입니다.</p>
    </div>

    <div class="dx-domain" id="axes">
      <div class="dx-head"><span class="dx-tag">렌즈</span><span class="dx-title">평판의 6대 축 (B·R·I·D·G·E)</span></div>
      <p class="dx-body">발견(B)에서 시작해 평가(R), 정체성(I), 경험(D), 행동(G), 책임과 지속성(E)으로 이어지는 하나의 흐름입니다. 각 축은 통계적으로 구별되지만 실제 현상에서는 서로 영향을 주고받습니다. 높은 가시성이 긍정 평가로 이어지지 않을 수 있고, 긍정 평가가 행동으로 전환되지 않을 수도 있습니다 — BRIDGE는 바로 이 단절 지점을 찾아 보여줍니다.</p>
      <table class="idx-table">
        <thead><tr><th>축</th><th>핵심 질문</th><th>대표 관측지표</th></tr></thead>
        <tbody>
          <tr><td><b>B</b> Brand Visibility</td><td>얼마나 발견되고 도달되는가</td><td>검색점유율, 고유기사, 영상도달, 채널다양성</td></tr>
          <tr><td><b>R</b> Reputation Response</td><td>어떻게 평가되고 반응되는가</td><td>순평판, 신뢰·호감, 분노·실망, 반응지속</td></tr>
          <tr><td><b>I</b> Identity &amp; Relevance</td><td>무엇으로 구별되고 적합한가</td><td>핵심연상, 의미집중도, 경쟁중복, 메시지적합</td></tr>
          <tr><td><b>D</b> Direct Public Experience</td><td>어떤 경험이 표현되는가</td><td>품질·서비스·광고·행정 경험, 불만유형</td></tr>
          <tr><td><b>G</b> Generated Action</td><td>무엇을 하게 만들었는가</td><td>공유·추천·탐색·참여·구매관련 행동신호</td></tr>
          <tr><td><b>E</b> Ethics &amp; Endurance</td><td>책임 있게 지속·회복하는가</td><td>제재·위기·책임인정·시정·재발·회복속도</td></tr>
        </tbody>
      </table>
    </div>

    <div class="dx-domain" id="calc">
      <div class="dx-head"><span class="dx-tag">원칙</span><span class="dx-title">타협 없는 데이터 통제</span></div>
      <p class="dx-body">출처가 명확한 데이터(A·B등급) 위주로 산출하며, 출처 불명의 불확실한 자료(D등급)는 즉각 배제합니다. 수집된 데이터는 관련성, 진정성, 출처 신뢰도, 시간 감쇠 등 5가지 승수 함수를 거치며, 로버스트 표준화(중앙값·MAD 기반)를 통해 통계적 극단치가 제거된 유효가중치만이 점수화됩니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 신뢰등급의 세부 기준은 <a href="trust.html" style="color:var(--gold);">신뢰등급 | 데이터추출</a> 페이지에서 확인하실 수 있습니다.</div>
    </div>

    <div class="dx-domain" id="version">
      <div class="dx-head"><span class="dx-tag">자정</span><span class="dx-title">정정 이력과 이의제기</span></div>
      <p class="dx-body" id="dispute">평가하는 자가 가장 먼저 평가받아야 합니다. 데이터 식별 및 산출 과정의 오류는 덮어두지 않고 투명하게 [정정 이력]에 기록하여 시스템의 자정 작용을 증명합니다. 데이터 오류에 대한 이의 제기는 엄밀히 검토하지만, 단순히 &lsquo;결과가 불리하다&rsquo;는 이유의 홍보성 점수 조정 요청은 영구히 차단됩니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">CONTACT</span> 대상 식별 오류·데이터 누락·산식 적용 오류 등에 대한 이의제기는 <a href="contact.html" style="color:var(--gold);">문의 | 이의제기</a> 페이지에서 접수합니다.</div>
    </div>
  </div>
</section>
'''

methodology_html = head("INDEX — BRIDGE 방법론·데이터정책", "우리는 순위를 흥정하지 않습니다. BRIDGE가 데이터를 정제하고 평판 신호를 추출하는 모든 뼈대를 투명하게 공개하는, 사이트에서 유일하게 상업적 목적이 없는 화면입니다.") + base_header("INDEX") + '''
<header class="list-hero-photo hero-methodology">
  <div class="wrap">
    <div class="about-kicker">INDEX · 방법론과 데이터정책</div>
    <h1 class="idx-hero-h">이 페이지는 팔리지 않습니다.</h1>
  </div>
</header>''' + INDEX_BODY + footer("methodology")
with open(f"{OUT}/methodology.html","w",encoding="utf-8") as f: f.write(methodology_html)

# ---------- trust: grounded in the confirmed white paper §14 (신뢰등급) ----------
# Previous drafts used my own approximation of A~D. This version uses the actual
# grade criteria from "BRIDGE 브랜드평판지수 방법론 및 신뢰성 백서" §14, including the
# N/R grade that my earlier drafts omitted entirely.
trust_html = head("TRUST — 신뢰등급 | 데이터추출", "신뢰등급과 4개 영역별 데이터 추출 원리를 밝힙니다.") + base_header("INDEX") + '''
<header class="list-hero-photo hero-trust">
  <div class="wrap">
    <h1>신뢰등급 | 데이터추출</h1>
    <p class="list-note">기업(CPR), 공공(GOV), 대학(UNI), 공인(ENT)이라는 각기 다른 네 개의 생태계에서 BRIDGE가 어떠한 근거와 논리로 유의미한 평판 신호를 추출하는지 명확히 밝힙니다. 발생 기전이 전혀 다른 평판들을 단일한 지표로 재단하는 것은 필연적으로 데이터의 왜곡을 낳습니다. 우리는 이러한 오류를 원천 차단하기 위해 각 영역이 지닌 고유한 특성을 분석하고, 데이터 수집부터 가중치 산정까지 완전히 차별화된 맞춤형 추출 알고리즘을 구축했습니다.</p>
  </div>
</header>
<section class="section">
  <div class="wrap">
    <div class="dx-common">
      <h2 class="about-h2">공통 원칙</h2>
      <ul class="about-donot dx-plus">
        <li>대상선정(누구를 평가할 것인가)과 평판측정(그 대상이 몇 점인가)을 분리합니다.</li>
        <li>모든 점수에는 근거자료(Evidence Card)와 신뢰등급(A~D, N/R)을 함께 표시합니다.</li>
        <li>산정방식을 비공개로 두는 외부 지수의 점수·순위는 근거자료로 인용하지 않습니다.</li>
      </ul>
    </div>

    <div class="dx-domain dx-trust">
      <div class="dx-head"><span class="dx-tag">신뢰등급</span><span class="dx-title">그 점수를 얼마나 믿을 수 있는가</span></div>
      <p class="dx-body">신뢰등급은 평판점수가 아니라 &lsquo;그 점수를 얼마나 믿을 수 있는가&rsquo;를 나타냅니다. 등급이 낮다는 것은 평판이 나쁘다는 뜻이 아니라, 데이터의 검증 수준이 아직 낮다는 뜻입니다.</p>
      <table class="trust-grade-table">
        <tr><th>등급</th><th>기준</th></tr>
        <tr><td><span class="tg-badge tg-a">A</span></td><td>핵심자료원 90% 이상 확보, 다원출처 확보, 표본 충분, 검증 완료</td></tr>
        <tr><td><span class="tg-badge tg-b">B</span></td><td>핵심자료원 75% 이상, 3종 이상의 독립자료원 확보</td></tr>
        <tr><td><span class="tg-badge tg-c">C</span></td><td>핵심자료원 60% 이상, 일부 자료원에 편중</td></tr>
        <tr><td><span class="tg-badge tg-d">D</span></td><td>단일 주간 또는 제한된 자료원에 의한 예비측정</td></tr>
        <tr><td><span class="tg-badge tg-nr">N/R</span></td><td>최소 산출기준 미충족 — 점수를 산출하지 않음</td></tr>
      </table>
      <div class="dx-routing"><span class="dx-routing-k">DATA POLICY</span> 데이터가 부족한 대상은 낮은 점수가 아니라 별도의 데이터 신뢰등급으로 표시합니다.</div>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">CPR</span><span class="dx-title">기업 | 위상적 분리와 로버스트 정제</span></div>
      <p class="dx-body">기업의 경제적 규모와 실질적인 평판을 혼동하지 않기 위해, 시가총액과 매출 등 객관적 지표로 평가 대상을 먼저 확정하는 철저한 분리 원칙을 적용합니다. 이후 수집된 데이터는 엄격한 교차 검증을 거쳐 통계적 편향과 극단적인 노이즈를 걷어내며, 시간의 흐름과 정보의 신뢰도까지 통제하는 5가지 복합 가중치 알고리즘을 거치게 됩니다. 이처럼 까다로운 정제 과정을 통과한 진짜 데이터만이 6개의 핵심 평판 축(B·R·I·D·G·E)에 정밀하게 맵핑되어 거대 기업의 이름값에 가려지지 않은 투명한 가치를 비춰줍니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 공시 데이터 1차 집계인 MCNA와 심층 추출망 BRIDGE DB를 활용하며, 확고한 외부 평가는 비변동성 데이터의 2기 엔진 자체 DB를 통해 산출됩니다.</div>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">GOV</span><span class="dx-title">공공기관 | 제한적 비교와 매체 편중 제어</span></div>
      <p class="dx-body">각기 다른 무게의 책임을 진 공공기관들을 무의미한 통합 서열표로 묶지 않고, 역할의 궤를 같이하는 기관 사이에서만 유의미한 평판 척도를 산출합니다. 찰나의 여론이나 특정 정보망의 과도한 쏠림 현상에 휩쓸리지 않도록, 폭넓은 신호의 다양성을 점수화하여 공공 평판의 묵직한 중심을 잡습니다. 나아가 기관이 묵묵히 쌓아온 본연의 가치가 소수의 단편적인 논란에 훼손되지 않도록, 텍스트 이면의 주체를 추적하는 귀속 규칙을 적용해 흔들림 없는 객관적 데이터만을 투명하게 분리합니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 공공기관 현황 1차 집계망인 AGK와 BRIDGE DB를 교차시키며, 기관 경영평가 등은 비변동성 데이터의 2기 엔진 자체 DB 안에서 독립 관리됩니다.</div>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">UNI</span><span class="dx-title">대학 | 서사 지표 추출과 발화자 계층화</span></div>
      <p class="dx-body">취업률과 논문 건수에 의존하던 기존의 획일적인 서열화 방식에서 벗어나, 평판 측정의 새로운 기준을 제시합니다. 단편적인 결과(Outcome) 대신 &lsquo;경쟁률의 증감&rsquo;과 같은 서사적 변화(Narrative)를 핵심 지표로 측정하여, 소수 알려진 대학에 쏠리던 평가의 편향성을 원천 차단합니다. 나아가 발화 주체를 예비 수험생, 재학생, 졸업생으로 세밀하게 층화(Stratification)하여, 각 교육 수요자 그룹이 실질적으로 체감하는 입체적인 평판을 완성합니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 대학 공시 1차 집계망인 AGK와 BRIDGE DB를 거쳐 목소리를 텍스트화하며, 평가의 뼈대는 비변동성 데이터의 2기 엔진 자체 DB가 지탱합니다.</div>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">ENT</span><span class="dx-title">공인 | 감성 분해와 결측의 허용</span></div>
      <p class="dx-body">대중적인 유명세가 곧 특정 브랜드와의 적합성을 의미하지는 않기에, 대중적 인지도(STAR-P)와 실질적 브랜드 적합성(STAR-F)을 철저하게 분리하여 진단합니다. 텍스트 이면의 뉘앙스를 세밀하게 해체하는 감성 분석과 시간의 흐름에 따라 영향력을 제어하는 가중치 함수를 통해, 찰나의 &lsquo;반짝 이슈&rsquo;와 단단한 &lsquo;구조적 신뢰&rsquo;를 뚜렷하게 갈라냅니다. 특히 검증할 수 있는 적합성 데이터가 부족할 경우 억지로 점수를 채워 넣지 않고 과감히 공란으로 남겨두어, 불확실한 데이터를 아는 척하지 않는 투명성의 원칙을 지킵니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 공개 보도 집계망 ABAJN과 BRIDGE DB를 통해 뉴스의 거품을 걷어내며, 기저의 절대 지표들은 비변동성 데이터의 2기 엔진 자체 DB로 굳건히 제어합니다.</div>
    </div>
  </div>
</section>
''' + footer("trust")
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
about_html = head("SignalBridge — 회사소개", "소음을 걷어내고, 진짜 평판의 해상도를 높이다. 시그널브릿지는 독자적 BRIDGE 모형으로 기업·공공기관·대학·공인의 진짜 평판 신호를 해독합니다.") + base_header("INDEX") + '''
<header class="list-hero-photo hero-about about-hero-big">
  <div class="wrap">
    <div class="about-kicker">SIGNALBRIDGE · COMPANY</div>
    <h1 class="about-slogan">소음을 걷어내고,<br>진짜 평판의 해상도를 높이다.</h1>
    <p class="about-hero-sub">시그널브릿지 (SignalBridge)</p>
  </div>
</header>

<section class="section about-lead-sec">
  <div class="wrap">
    <p class="about-lead">우리는 데이터 속에 숨겨진 <b>평판의 진짜 시그널을 해독(Decode)</b>합니다.</p>
    <p class="about-body">찰나의 화제성이나 일시적인 대중의 쏠림 현상만으로 브랜드의 진짜 가치가 결정될 수는 없습니다. 시그널브릿지는 외부의 노이즈에 흔들리지 않기 위해 독자적인 <b>&lsquo;BRIDGE 모형&rsquo;</b>을 가동합니다. 평가 대상을 무대에 올리는 기준과 실제 평판을 측정하는 기준을 철저하게 분리함으로써, 단순히 규모가 크거나 인지도가 높다는 이유만으로 계속해서 유리한 고지를 차지하는 <b>&lsquo;결과 편향&rsquo;</b>의 낡은 고리를 단호히 끊어냅니다.</p>
  </div>
</section>

<div class="about-figure">
  <img src="img/about_bridge.jpg" alt="두 개의 축을 잇는 다리 — BRIDGE" loading="lazy">
  <div class="about-figure-cap">이미 큰 목소리가 아니라, 신뢰가 움직이는 방향을 잇습니다.</div>
</div>

<section class="section">
  <div class="wrap">
    <div class="about-sec-head">
      <h2 class="about-h2">4개의 무대, 4개의 잣대</h2>
      <p class="about-h2-sub">왜 영역을 한정하는가</p>
    </div>
    <p class="about-body" style="margin-bottom:28px">획일화된 잣대는 필연적으로 평판의 왜곡을 낳습니다. 기업과 공공기관, 대학과 공인은 대중의 신뢰가 형성되고 소비되는 방식이 완전히 다르기 때문입니다. 시그널브릿지는 이 <b>4개의 생태계(CPR, GOV, UNI, ENT)</b>를 명확히 구분하고, 각 영역의 본질에 가장 완벽하게 들어맞는 4개의 독립적인 잣대를 통해 완전히 새로운 평판의 기준을 제시합니다.</p>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">CPR</span><span class="dx-title">기업</span></div>
      <p class="dx-body">거대한 이름값이 평판으로 둔갑하는 착시를 막기 위해, 외형적 덩치와 내면의 책임을 완벽히 분리하여 기업의 묵직한 가치만을 투명하게 진단합니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">GOV</span><span class="dx-title">공공기관</span></div>
      <p class="dx-body">역할이 전혀 다른 기관들을 한 줄로 세우는 획일화를 벗어나, 궤를 같이하는 기능군 내에서 묵묵히 쌓아온 공공의 헌신과 책임만을 정밀하게 묻습니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">UNI</span><span class="dx-title">대학</span></div>
      <p class="dx-body">과거의 정적인 결과값으로 획일적인 서열을 만들지 않습니다. 역동적인 성장의 추이와 현장의 생생한 목소리를 융합해 대학의 진짜 명성을 짚어냅니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">ENT</span><span class="dx-title">공인</span></div>
      <p class="dx-body">스포트라이트가 만들어낸 순간적인 유명세에 기대지 않습니다. 단발성 이슈를 단호히 걷어내고 대중의 마음속에 묵직하게 뿌리내린 진짜 신뢰만을 차분하게 기록합니다.</p>
    </div>
  </div>
</section>

<div class="about-figure about-figure-split">
  <img src="img/about_ripple.jpg" alt="평판의 파동" loading="lazy">
  <div class="about-figure-overlay">
    <div class="about-figure-title">Absolute Independence</div>
    <div class="about-figure-lead">절대적 독립성 원칙</div>
  </div>
</div>

<section class="section">
  <div class="wrap">
    <p class="about-body" style="margin-bottom:28px">이러한 혁신은 <b>자본과 타협하지 않는 굳건한 뼈대</b> 위에서만 가능합니다.</p>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag" style="font-size:15px">물리적 분리</span></div>
      <p class="dx-body">데이터를 다루는 분석 조직은 비즈니스의 이해관계로부터 완전히 독립된 섬과 같습니다. 보고 체계와 의사결정 라인을 영구적으로 분리하여, 오직 팩트와 통계적 근거만으로 평가의 순수성을 묵묵히 지켜나갑니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag" style="font-size:15px">자본의 무개입</span></div>
      <p class="dx-body">객관성은 구조를 분리하는 것에서 시작됩니다. 데이터를 다루는 분석 조직은 광고나 영업 조직과 완전히 절연되어, 오직 데이터가 가리키는 진실만을 독립적으로 바라봅니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag" style="font-size:15px">선제적 공시</span></div>
      <p class="dx-body">공정함의 증명은 숨김없는 고백에서 시작됩니다. 복잡한 비즈니스 역학 관계가 평가에 영향을 미치지 않도록, 이해상충 소지가 있는 지점들은 언제나 투명하게 선제 공시합니다.</p>
    </div>
    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag" style="font-size:15px">진단 의견의 선행</span></div>
      <p class="dx-body">BRIDGE 지수는 맹목적인 정답을 강요하는 순위표가 아닌 객관적인 &lsquo;통계적 진단 의견&rsquo;입니다. 최종 결과를 단편적으로 제시하기 전에, 어떠한 방법론과 근거로 이 신호들이 추출되었는지 그 검증의 과정을 세상에 먼저 투명하게 엽니다.</p>
    </div>
  </div>
</section>

<section class="section tint">
  <div class="wrap">
    <div class="about-sec-head">
      <h2 class="about-h2">우리가 하지 않는 일</h2>
      <p class="about-h2-sub">What We Do Not Do</p>
    </div>
    <ul class="about-donot">
      <li>법적, 도의적, 투자적 가치 판단의 영역을 침범하지 않습니다.</li>
      <li>개별 기업, 인물, 기관의 사적인 요청이나 압력으로 순위를 임의 조정하지 않습니다.</li>
      <li>대중 내면의 맹목적 신뢰나 시장 가치 자체를 직접 측정했다고 오만하게 포장하지 않습니다.</li>
      <li>&lsquo;결과가 불리하다&rsquo;는 단순한 불만으로 점수를 변경하는 일은 원천적으로 불가능합니다.</li>
    </ul>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="about-sec-head">
      <h2 class="about-h2">서비스 체계</h2>
      <p class="about-h2-sub">Service Architecture</p>
    </div>
    <div class="about-arch">
      <div class="about-arch-row"><div class="about-arch-k">운영 주체</div><div class="about-arch-n">SignalBridge</div><div class="about-arch-d">서비스 운영, 계약, 데이터 거버넌스 수호</div></div>
      <div class="about-arch-row"><div class="about-arch-k">핵심 엔진</div><div class="about-arch-n">BRIDGE Framework</div><div class="about-arch-d">6축(B&middot;R&middot;I&middot;D&middot;G&middot;E) 평가 철학과 공통 산식의 근간</div></div>
      <div class="about-arch-row"><div class="about-arch-k">공개 모듈</div><div class="about-arch-n">CPR &middot; GOV &middot; UNI &middot; ENT</div><div class="about-arch-d">프레임워크 기반 4대 생태계별 평판지수</div></div>
      <div class="about-arch-row"><div class="about-arch-k">솔루션</div><div class="about-arch-n">BRIDGE-D vs V</div><div class="about-arch-d">공익 목적의 무료 공개형(D)과 내부 자료 결합 확장형(V)</div></div>
    </div>
    <p class="about-contact">문의 &nbsp;·&nbsp; <a href="contact.html" style="color:var(--gold);">문의 | 이의제기</a></p>
  </div>
</section>
''' + footer("about")
with open(f"{OUT}/about.html","w",encoding="utf-8") as f: f.write(about_html)

print("pages written:", os.listdir(OUT))

# ---------- 데이터 추출 (DATA EXTRACTION): cross-domain light explanation ----------
# PILOT's original content is now absorbed into the CPR/STAR/GOV/UNI pages themselves
# (real names, N/R grade). This page is the light, on-site explanation of HOW BRIDGE
# extracts and reasons about data across all four domains; the detailed proprietary
# methodology (the actual know-how) lives in the white paper §21-24, not here.
import importlib
importlib.reload(build_pilot)
data_extraction_html = head("BRIDGE — 데이터 추출 방법론", "BRIDGE가 CPR·GOV·UNI·ENT 네 영역에서 무엇을 근거로 어떻게 평판 신호를 추출하는지에 대한 요약입니다.") + base_header("데이터 추출") + '''
<header class="list-hero-photo hero-data-extraction">
  <div class="wrap">
    <h1>데이터 추출</h1>
    <p class="list-note">기업(CPR), 공공(GOV), 대학(UNI), 공인(ENT)이라는 각기 다른 네 개의 생태계에서 BRIDGE가 어떠한 근거와 논리로 유의미한 평판 신호를 추출하는지 명확히 밝힙니다. 발생 기전이 전혀 다른 평판들을 단일한 지표로 재단하는 것은 필연적으로 데이터의 왜곡을 낳습니다. 우리는 이러한 오류를 원천 차단하기 위해 각 영역이 지닌 고유한 특성을 분석하고, 데이터 수집부터 가중치 산정까지 완전히 차별화된 맞춤형 추출 알고리즘을 구축했습니다.</p>
  </div>
</header>
<section class="section">
  <div class="wrap">
    <div class="dx-common">
      <h2 class="about-h2">공통 원칙</h2>
      <ul class="about-donot dx-plus">
        <li>대상선정(누구를 평가할 것인가)과 평판측정(그 대상이 몇 점인가)을 분리합니다.</li>
        <li>모든 점수에는 근거자료(Evidence Card)와 신뢰등급(A~D, N/R)을 함께 표시합니다.</li>
        <li>산정방식을 비공개로 두는 외부 지수의 점수·순위는 근거자료로 인용하지 않습니다.</li>
      </ul>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">CPR</span><span class="dx-title">기업 | 위상적 분리와 로버스트 정제</span></div>
      <p class="dx-body">기업의 경제적 규모와 실질적인 평판을 혼동하지 않기 위해, 시가총액과 매출 등 객관적 지표로 평가 대상을 먼저 확정하는 철저한 분리 원칙을 적용합니다. 이후 수집된 데이터는 엄격한 교차 검증을 거쳐 통계적 편향과 극단적인 노이즈를 걷어내며, 시간의 흐름과 정보의 신뢰도까지 통제하는 5가지 복합 가중치 알고리즘을 거치게 됩니다. 이처럼 까다로운 정제 과정을 통과한 진짜 데이터만이 6개의 핵심 평판 축(B·R·I·D·G·E)에 정밀하게 맵핑되어 거대 기업의 이름값에 가려지지 않은 투명한 가치를 비춰줍니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 공시 데이터 1차 집계인 MCNA와 심층 추출망 BRIDGE DB를 활용하며, 확고한 외부 평가는 비변동성 데이터의 2기 엔진 자체 DB를 통해 산출됩니다.</div>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">GOV</span><span class="dx-title">공공기관 | 제한적 비교와 매체 편중 제어</span></div>
      <p class="dx-body">각기 다른 무게의 책임을 진 공공기관들을 무의미한 통합 서열표로 묶지 않고, 역할의 궤를 같이하는 기관 사이에서만 유의미한 평판 척도를 산출합니다. 찰나의 여론이나 특정 정보망의 과도한 쏠림 현상에 휩쓸리지 않도록, 폭넓은 신호의 다양성을 점수화하여 공공 평판의 묵직한 중심을 잡습니다. 나아가 기관이 묵묵히 쌓아온 본연의 가치가 소수의 단편적인 논란에 훼손되지 않도록, 텍스트 이면의 주체를 추적하는 귀속 규칙을 적용해 흔들림 없는 객관적 데이터만을 투명하게 분리합니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 공공기관 현황 1차 집계망인 AGK와 BRIDGE DB를 교차시키며, 기관 경영평가 등은 비변동성 데이터의 2기 엔진 자체 DB 안에서 독립 관리됩니다.</div>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">UNI</span><span class="dx-title">대학 | 서사 지표 추출과 발화자 계층화</span></div>
      <p class="dx-body">취업률과 논문 건수에 의존하던 기존의 획일적인 서열화 방식에서 벗어나, 평판 측정의 새로운 기준을 제시합니다. 단편적인 결과(Outcome) 대신 &lsquo;경쟁률의 증감&rsquo;과 같은 서사적 변화(Narrative)를 핵심 지표로 측정하여, 소수 알려진 대학에 쏠리던 평가의 편향성을 원천 차단합니다. 나아가 발화 주체를 예비 수험생, 재학생, 졸업생으로 세밀하게 층화(Stratification)하여, 각 교육 수요자 그룹이 실질적으로 체감하는 입체적인 평판을 완성합니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 대학 공시 1차 집계망인 AGK와 BRIDGE DB를 거쳐 목소리를 텍스트화하며, 평가의 뼈대는 비변동성 데이터의 2기 엔진 자체 DB가 지탱합니다.</div>
    </div>

    <div class="dx-domain">
      <div class="dx-head"><span class="dx-tag">ENT</span><span class="dx-title">공인 | 감성 분해와 결측의 허용</span></div>
      <p class="dx-body">대중적인 유명세가 곧 특정 브랜드와의 적합성을 의미하지는 않기에, 대중적 인지도(STAR-P)와 실질적 브랜드 적합성(STAR-F)을 철저하게 분리하여 진단합니다. 텍스트 이면의 뉘앙스를 세밀하게 해체하는 감성 분석과 시간의 흐름에 따라 영향력을 제어하는 가중치 함수를 통해, 찰나의 &lsquo;반짝 이슈&rsquo;와 단단한 &lsquo;구조적 신뢰&rsquo;를 뚜렷하게 갈라냅니다. 특히 검증할 수 있는 적합성 데이터가 부족할 경우 억지로 점수를 채워 넣지 않고 과감히 공란으로 남겨두어, 불확실한 데이터를 아는 척하지 않는 투명성의 원칙을 지킵니다.</p>
      <div class="dx-routing"><span class="dx-routing-k">SIGNAL ROUTING</span> 공개 보도 집계망 ABAJN과 BRIDGE DB를 통해 뉴스의 거품을 걷어내며, 기저의 절대 지표들은 비변동성 데이터의 2기 엔진 자체 DB로 굳건히 제어합니다.</div>
    </div>
  </div>
</section>
''' + footer("index")
with open(f"{OUT}/data-extraction.html","w",encoding="utf-8") as f: f.write(data_extraction_html)
print("data-extraction.html written")
