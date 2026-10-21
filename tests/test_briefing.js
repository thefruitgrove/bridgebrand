const fs = require('fs');
const assert = require('assert');

const html = fs.readFileSync('site/briefing.html', 'utf8');
const js = fs.readFileSync('site/briefing.js', 'utf8');
const css = fs.readFileSync('site/briefing.css', 'utf8');
const data = JSON.parse(fs.readFileSync('site/data/latest.json', 'utf8'));

for (let i = 1; i <= 6; i += 1) {
  assert(html.includes(`data-stage="${i}"`), `missing stage navigation ${i}`);
  assert(html.includes(`data-stage-panel="${i}"`), `missing stage panel ${i}`);
}

['SIGNAL GUIDE', 'CONTEXT MAP', 'POSITION READ', 'RELATIONSHIP INTELLIGENCE', 'PUBLICITY BRIEF', 'REPORT EDITION'].forEach((label) => {
  assert(html.includes(label), `missing stage label: ${label}`);
});

for (const field of ['CPR', 'GOV', 'ENT', 'UNI']) {
  const rows = data.rankings.filter((item) => item.domain === field && item.ranking_type === 'T100');
  assert(rows.length >= 3 && rows.length <= 100, `${field} briefing source must expose a usable T100 range`);
}

assert(js.includes("const FIELDS=['CPR','GOV','UNI','ENT']"), 'briefing must accept all four fields');
assert(js.includes('completeRange'), 'briefing must enforce contiguous ranks');
assert(js.includes("new Set(ids).size!==3"), 'briefing must reject duplicate targets');
assert(js.includes("if(entities.some((entity)=>!entity))"), 'briefing must reject unknown target IDs');
assert(!js.includes('if(entities.length!==3){const preferred='), 'invalid selections must not be silently replaced');
assert(js.includes("e.axis_status[a]!=='reference'"), 'reference axes must be excluded');
assert(html.includes('근거 신뢰등급') && html.includes('평판등급이 아니라'), 'trust-grade boundary missing');
assert(html.includes('활동량은 긍정 평판이 아니며'), 'activity interpretation boundary missing');
assert(!html.includes('ENT T100 3위를 기록했다'), 'stale hard-coded rank must not remain');
assert(css.includes('@media(max-width:720px)'), 'mobile responsive contract missing');
assert(html.includes('id="savePdf"') && html.includes('id="printReport"'), 'report edition save and print controls missing');

console.log('Six-stage BRIDGE briefing contract passed.');
