const fs = require('fs');
const assert = require('assert');

const html = fs.readFileSync('site/intelligence.html', 'utf8');
const js = fs.readFileSync('site/intelligence.js', 'utf8');
const data = JSON.parse(fs.readFileSync('site/data/latest.json', 'utf8'));

['trioPick1', 'trioPick2', 'trioPick3', 'trioSnapshotMeta', 'serviceBuilder'].forEach((id) => {
  assert(html.includes(`id="${id}"`), `missing UI element: ${id}`);
});

assert(js.includes("const FIELDS = ['CPR', 'GOV', 'UNI', 'ENT']"), 'discovery must support all four fields');
assert(js.includes('new Set(ids).size!==3'), 'duplicate target protection missing');
assert(js.includes('state.entries.length < 3') && js.includes('state.entries.length > 100'), 'published T100 range guard missing');
assert(js.includes('completeRange'), 'contiguous rank guard missing');
assert(js.includes('syncSelectAvailability'), 'cross-select duplicate prevention missing');
assert(html.includes('intelligence.html?field=CPR#trioBeta'), 'CPR discovery route missing');
assert(html.includes('intelligence.html?field=GOV#trioBeta'), 'GOV discovery route missing');
assert(js.includes("['PULSE',3") && js.includes("['INSIGHT',5") && js.includes("['INTELLIGENCE',10"), 'subscription target limits missing');
assert(js.includes("['SNAPSHOT',1") && js.includes("['DEEP DIVE',1"), 'one-time packages missing');
assert(js.includes("['ENTERPRISE T100',100"), 'enterprise package missing');

for (const field of ['CPR', 'GOV', 'ENT', 'UNI']) {
  const rows = data.rankings.filter((row) => row.domain === field && row.ranking_type === 'T100');
  assert(rows.length >= 3 && rows.length <= 100, `${field} must expose a usable published T100 range`);
  assert.strictEqual(new Set(rows.map((row) => row.external_id)).size, rows.length, `${field} target IDs must be unique`);
  assert.strictEqual(new Set(rows.map((row) => row.rank)).size, rows.length, `${field} ranks must be unique`);
  assert.strictEqual(new Set(rows.map((row) => row.as_of_date)).size, 1, `${field} targets must share one observation date`);
  rows.sort((a,b) => a.rank-b.rank).forEach((row,index) => assert.strictEqual(row.rank,index+1,`${field} ranks must be contiguous`));
}

console.log('BRIDGE TRIO and service-builder contract passed.');
