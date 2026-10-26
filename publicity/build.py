"""Static shell; released article data is fetched through time-gated RLS."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build_publicity(head,header,footer):
    body='''<link rel="stylesheet" href="publicity.css?v=20261015-3">
<main class="pub-shell">
  <section class="pub-cover">
    <a class="pub-back" href="index.html">BRIDGE / SIGNALBRIDGE</a>
    <div class="pub-kicker">THE INTERPRETATION OF SIGNALS</div>
    <h1 id="pubHeading">Publicity<span>.</span></h1>
    <p class="pub-intro" id="pubIntro">순위로 시선을 열고, 여섯 축으로 이유를 설명합니다.<br>점수·활동량·근거 범위를 구분해 이번 회차에서 확인된 변화와 다음 질문을 전합니다.</p>
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
  <div class="pub-note">PUBLICITY는 공개자료에서 확인된 결과를 기사 형식으로 설명합니다. 순위는 같은 분야와 공개 범위 안의 상대적 위치이며, 활동량은 긍정 평판과 같지 않습니다. 관측되지 않은 축과 수집 실패도 낮은 점수로 바꾸지 않습니다.</div>
</main>
<script src="publicity-config.js?v=1" defer></script><script src="publicity.js?v=20261016-5" defer></script>'''
    shell=head('BRIDGE — PUBLICITY')+header('PUBLICITY')+body+footer('index')
    for name in ('publicity.html','publicity-article.html'):(ROOT/'site'/name).write_text(shell)
