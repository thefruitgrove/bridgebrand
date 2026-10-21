const fs = require('fs');
const assert = require('assert');

const html = fs.readFileSync('site/intelligence.html', 'utf8');
const js = fs.readFileSync('site/intelligence.js', 'utf8');
const data = JSON.parse(fs.readFileSync('site/data/latest.json', 'utf8'));

['trioPick1', 'trioPick2', 'trioPick3', 'trioRadar', 'trioGaps', 'trioTypes', 'serviceBuilder'].forEach((id) => {
  assert(html.includes(`id="${id}"`), `missing UI element: ${id}`);
});

assert(js.includes('new Set(ids).size !== 3'), 'duplicate target protection missing');
assert(js.includes("e.axis_status[axis] !== 'reference'"), 'reference-axis exclusion missing');
assert(js.includes("['PULSE', 3") && js.includes("['INSIGHT', 5") && js.includes("['INTELLIGENCE', 10"), 'subscription target limits missing');
assert(js.includes("['SNAPSHOT', 1") && js.includes("['DEEP DIVE', 1"), 'one-time packages missing');
assert(js.includes("['ENTERPRISE T100', 100"), 'enterprise package missing');

const selected = ['리센느', '임영웅', '김지원'].map((name) => data.rankings.find((row) => row.domain === 'ENT' && row.name === name));
assert(selected.every(Boolean), 'default ENT comparison targets missing from public data');
assert(new Set(selected.map((row) => row.as_of_date)).size === 1, 'default targets must share one observation date');
assert(selected.every((row) => row.axes_available > 0), 'default targets need comparable axes');

console.log('BRIDGE TRIO and service-builder contract passed.');
