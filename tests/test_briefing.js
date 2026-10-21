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

['리센느', '아이브', '르세라핌'].forEach((name) => {
  const row = data.rankings.find((item) => item.domain === 'ENT' && item.ranking_type === 'T100' && item.name === name);
  assert(row, `missing public ENT target: ${name}`);
  assert(row.axes_available === 6, `sample target must have 6 comparable axes: ${name}`);
});

assert(js.includes("x.domain==='ENT'&&x.ranking_type==='T100'"), 'briefing must use ENT T100 public data');
assert(js.includes("e.axis_status[a]!=='reference'"), 'reference axes must be excluded');
assert(html.includes('근거 신뢰등급') && html.includes('평판등급이 아니라'), 'trust-grade boundary missing');
assert(html.includes('활동량은 긍정 평판이 아니며'), 'activity interpretation boundary missing');
assert(css.includes('@media(max-width:720px)'), 'mobile responsive contract missing');
assert(html.includes('assets/reports/BRIDGE_ENT_GENERAL_BRIEFING_리센느_20261021.pdf'), 'report edition PDF link missing');

console.log('Six-stage BRIDGE briefing contract passed.');
