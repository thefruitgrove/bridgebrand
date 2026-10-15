"""Static shell; released article data is fetched through time-gated RLS."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build_publicity(head,header,footer):
    body='''<link rel="stylesheet" href="publicity.css?v=20261015-1">
<main class="pub-shell">
  <section class="pub-cover">
    <a class="pub-back" href="index.html">BRIDGE / SIGNALBRIDGE</a>
    <div class="pub-kicker">THE INTERPRETATION OF SIGNALS</div>
    <h1 id="pubHeading">Publicity<span>.</span></h1>
    <p class="pub-intro" id="pubIntro">순위 너머의 관계를 읽다.<br>브랜드의 현재 위치, 강점과 제약, 변화의 방향을 이야기합니다.</p>
    <div class="pub-schedule">WED & FRI 12:00 · MON OVERALL 12:00 <span>SEOUL TIME</span></div>
  </section>
  <section id="pubBoard" class="pub-board" aria-label="주차별 PUBLICITY 기사">
    <div class="pub-board-head"><h2>THE WEEKLY EDITIONS</h2><p>네 영역, 두 번의 관측, 한 주의 해석.</p></div>
    <p id="pubStatus" role="status">공개된 분석 기사를 불러오고 있습니다.</p>
    <div id="pubIssues"></div>
  </section>
  <article id="pubArticle" class="pub-article" hidden>
    <a class="pub-index-link" href="publicity.html">← ALL PUBLICITY</a>
    <div id="pubArticleContent"></div>
  </article>
  <div class="pub-note">PUBLICITY는 공개자료에서 관측한 관계와 신호를 해석합니다. 순위는 모든 가치를 판정하지 않으며, 관측 공백은 부정 평가와 다릅니다.</div>
</main>
<script src="publicity-config.js?v=1" defer></script><script src="publicity.js?v=20261015-1" defer></script>'''
    shell=head('BRIDGE — PUBLICITY')+header('PUBLICITY')+body+footer('index')
    for name in ('publicity.html','publicity-article.html'):(ROOT/'site'/name).write_text(shell)
