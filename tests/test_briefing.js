const fs = require('fs');
const assert = require('assert');

const html = fs.readFileSync('site/briefing.html', 'utf8');
const js = fs.readFileSync('site/briefing.js', 'utf8');
const css = fs.readFileSync('site/briefing.css', 'utf8');
const data = JSON.parse(fs.readFileSync('site/data/latest.json', 'utf8'));
const brandShell = fs.readFileSync('tools/apply_brand_shell.py', 'utf8');

for (let i = 1; i <= 6; i += 1) {
  assert(html.includes(`data-stage="${i}"`), `missing stage navigation ${i}`);
  assert(html.includes(`data-stage-panel="${i}"`), `missing stage panel ${i}`);
}

['SIGNAL GUIDE', 'FIELD PULSE', 'POSITION READ', 'RELATIONSHIP INTELLIGENCE', 'PUBLICITY BRIEF', 'REPORT EDITION'].forEach((label) => {
  assert(html.includes(label), `missing stage label: ${label}`);
});

for (const field of ['CPR', 'GOV', 'ENT', 'UNI']) {
  const rows = data.rankings.filter((item) => item.domain === field && item.ranking_type === 'T100');
  assert(rows.length >= 3 && rows.length <= 100, `${field} briefing source must expose a usable T100 range`);
}

assert(js.includes("const FIELDS=['CPR','GOV','UNI','ENT']"), 'briefing must accept all four fields');
assert(js.includes("LANGUAGES=['한국어','영어']"), 'briefing must expose Korean and English only');
assert(js.includes('function buildEnglishPrintReport()'), 'English print report generator missing');
assert(js.includes("if(IS_ENGLISH){buildEnglishPrintReport();return;}"), 'English report routing missing');
assert(css.includes('.print-language-en') && css.includes('.language-en'), 'English report typography contract missing');
assert(js.includes('completeRange'), 'briefing must enforce contiguous ranks');
assert(js.includes("new Set(ids).size!==3"), 'briefing must reject duplicate targets');
assert(js.includes("if(entities.some((entity)=>!entity))"), 'briefing must reject unknown target IDs');
[
  '발견 반응력','인지도 정체성','도달 경험 전환','발견 행동 전환','확산 지속성',
  '반응 정체성 결속','반응 경험 일치','반응 행동 전환','반응 관계 유지','약속 경험 일치',
  '정체성 행동 동력','정체성 지속성','경험 행동 전환','경험 신뢰 축적','행동 관계 지속'
].forEach((label)=>assert(js.includes(label), `missing BRIDGE pair interpretation: ${label}`));
assert(html.includes('id="positionNarrative"'), 'position explanation layer missing');
assert(html.includes('id="pairGrid"'), '15-pair DSSE interpretation surface missing');
assert(js.includes("['08 · 다음 관측과 실무 제안'"), 'PUBLICITY eight-block explanation missing');
assert(js.includes('활용 제안.'), 'practical implication generation missing');
assert(!js.includes('if(entities.length!==3){const preferred='), 'invalid selections must not be silently replaced');
assert(js.includes("e.axis_status[a]!=='reference'"), 'reference axes must be excluded');
assert(html.includes('근거 신뢰등급') && html.includes('평판등급이 아니라'), 'trust-grade boundary missing');
assert(html.includes('활동량은 긍정 평판이 아니며'), 'activity interpretation boundary missing');
assert(!html.includes('ENT T100 3위를 기록했다'), 'stale hard-coded rank must not remain');
assert(css.includes('@media(max-width:720px)'), 'mobile responsive contract missing');
assert(html.includes('id="previewPdf"') && html.includes('id="savePdf"') && html.includes('id="printReport"'), 'report edition preview, save and print controls missing');
assert(html.includes('id="exitPdfPreview"') && js.includes('setPdfPreview'), 'full-report preview mode missing');
assert(html.includes('id="pdfMobileToolbar"') && html.includes('id="pdfMobilePageStatus"'), 'mobile report reader toolbar missing');
assert(js.includes('updateMobilePreviewPage') && js.includes("getBoundingClientRect().top"), 'mobile report page-position indicator missing');
assert(js.includes('class="print-table-scroll"') && css.includes('표를 좌우로 밀어 전체 열 보기'), 'mobile report tables must scroll instead of collapsing columns');
assert(css.includes('BRIDGE MOBILE REPORT VIEW v7.2') && css.includes('min-height:calc(100svh - 92px)'), 'mobile-native report cover reflow missing');
assert(css.includes('column-count:1') && css.includes('grid-template-columns:repeat(2,minmax(0,1fr))'), 'mobile report prose and six-axis reflow missing');
assert(js.includes('requestAnimationFrame') && js.includes('window.scrollTo'), 'stage navigation must move to the next stage heading');
assert(css.includes('background:#172534') && css.includes('.stage-pager button:hover'), 'stage pager contrast treatment missing');
assert(html.includes('DUAL READING') && html.includes('data-reading="easy"') && html.includes('data-reading="professional"'), 'easy/professional reading switch missing');
assert(html.includes('id="positionEasyRead"') && html.includes('id="relationshipEasyRead"') && html.includes('id="publicityEasyRead"'), 'easy reading surfaces missing');
assert(js.includes("classList.toggle('easy-reading'"), 'dual reading interaction missing');
assert(js.includes('실제 활동이 전혀 없었다는 뜻은 아닙니다') || js.includes('활동량도 움직임의 크기일 뿐'), 'safe activity explanation missing');
assert(css.includes('.easy-read-card') && css.includes('.reading-mode'), 'dual reading responsive styles missing');
assert(html.includes('CONTEXT MAP · INTEGRATED'), 'the former context step must be integrated into SIGNAL GUIDE');
assert(html.includes('id="fieldPulseList"') && html.includes('CUMULATIVE PERFORMANCE · CURRENT VIEW'), 'field-specific cumulative TOP 20 step missing');
assert(js.includes('function renderFieldPulse()') && js.includes('.slice(0,20)'), 'current field TOP 20 generator missing');
assert(js.includes('const lines=[') && js.includes('fieldPulseNarrative'), 'seven-line field interpretation missing');
assert(html.includes('id="positionLifestyle"') && html.includes('id="relationshipLifestyle"') && html.includes('id="publicityB2B"'), 'infotainment and B2B explanation surfaces missing');
assert(
  js.includes('function buildPrintReport()') &&
  js.includes("total=reportMode==='basic'?8:29") &&
  js.includes("String(number).padStart(2,'0')} / ${total}"),
  'BASIC 8-page and STANDARD 29-page report edition generators missing'
);
assert(js.includes("footer=number===1?'':"), 'cover must omit the report footer');
assert(js.includes('PUBLICITY BRIEF · EXTERNAL EDITION 1/2') && js.includes('PUBLICITY BRIEF · EXTERNAL EDITION 2/2'), 'PUBLICITY must be split instead of shrinking body copy');
assert(css.includes('font-size:11pt!important') && css.includes('line-height:1.74!important'), 'PDF body typography must remain 11pt with report line spacing');
assert(css.includes('background:var(--report-tangerine)') && css.includes('--report-tangerine:#d6aa42'), 'page 2+ footer must use the cover tangerine field');
assert(
  html.includes('data-report-mode="basic"') &&
  html.includes('data-report-mode="standard"') &&
  js.includes("query.get('briefing')==='basic'") &&
  js.includes("searchParams.set('briefing','basic')") &&
  js.includes('applyBasicMode'),
  'BASIC/STANDARD briefing scope switch missing'
);
assert(html.includes('id="activityNarrative"'), 'expanded activity-versus-reputation explanation missing');
assert(js.includes('rankStory=[') && js.includes('rankStory.map'), 'expanded POSITION READ story missing');
assert(js.includes('activityStory=[') && js.includes('activityStory.map'), 'expanded activity interpretation story missing');
['axisReading','entityNarrative','comparisonNarrative'].forEach((name) => {
  assert(js.includes(`function ${name}(`), `${name} data-driven PDF narrative missing`);
});
assert(js.includes("['B','R','I'].map((x)=>axisReading(pick,x))") && js.includes("['D','G','E'].map((x)=>axisReading(pick,x))"), 'MY PICK six-axis PDF commentary missing');
assert(js.includes("entityNarrative(a,'COMPARE A')") && js.includes("entityNarrative(b,'COMPARE B')"), 'independent comparison narratives missing');
assert(js.includes('...activityStory.slice(0,9)'), 'full activity/reputation PDF explanation missing');
assert(css.includes('.print-narrative-full') && css.includes('.print-entity-detail'), 'dense report typography contract missing');
assert(js.includes('function printReading(') && css.includes('.print-reading'), 'print visual explanation layer missing');
assert(js.includes("openReportOutput('pdf')") && js.includes("openReportOutput('print')"), 'PDF and print actions must be independently wired');
assert(css.includes('@page{size:A4 portrait') && css.includes('.print-cover') && css.includes('.print-sheet:before'), 'A4 branded print system missing');
assert(js.includes('CONTENTS · STANDARD EDITION') && js.includes('EXECUTIVE SIGNAL'), 'cover-two contents and executive signal pages missing');
assert(html.includes('briefing.js?v=20261101-bilingual5'), 'English briefing control cache must be current');
assert(js.includes('showStage(stage);'), 'English briefing must refresh pager labels after translation');
assert(js.includes("const journeyLabels=['INDEX & CONTEXT','FIELD PULSE','POSITION','RELATIONSHIP','EXTERNAL BRIEF','PDF REPORT']"), 'English journey labels must drive the pager');
assert(js.includes("IS_ENGLISH?'← Previous':'← 이전 단계'"), 'English stage pager must not fall back to Korean');
assert(js.includes('CUMULATIVE PERFORMANCE · CURRENT VIEW') && js.includes('DISTRIBUTION · DOT PLOT'), 'current-view and T100 distribution pages missing');
assert(js.includes('PAIR READING · PRIORITY 3') && js.includes('ACTION PRIORITIES'), 'pair interpretation and action-priority pages missing');
assert(js.includes('METHOD · NOTICE · NEXT'), 'method, notice and next-question record page missing');
assert(!js.includes('<footer class="print-sheet-footer"><span>${id}</span>'), 'long report identifier must not repeat in the footer');
assert(css.includes('--report-brown:#40251d') && css.includes('.print-cover-split'), 'dark-brown and gold report design system missing');
assert(css.includes('.print-type-publicity') && css.includes('.print-type-method'), 'page-type density system missing');
assert(brandShell.includes("style.css?v=20261031-bilingual1"), 'daily rebuild must preserve the bilingual stylesheet version');
assert(brandShell.includes("i18n.js?v=20261101-bilingual3"), 'daily rebuild must preserve the bilingual interface layer');

console.log('Six-stage BRIDGE briefing contract passed.');

