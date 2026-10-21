const fs = require('fs');
const assert = require('assert');

const html = fs.readFileSync('site/intelligence.html', 'utf8');
const js = fs.readFileSync('site/intelligence.js', 'utf8');
const data = JSON.parse(fs.readFileSync('site/data/latest.json', 'utf8'));

['trioPick1', 'trioPick2', 'trioPick3', 'trioSnapshotMeta', 'serviceBuilder'].forEach((id) => {
  assert(html.includes(`id="${id}"`), `missing UI element: ${id}`);
});

assert(js.includes("const FIELDS = ['UNI', 'ENT']"), 'phase-one discovery must be limited to UNI and ENT');
assert(js.includes('new Set(ids).size!==3'), 'duplicate target protection missing');
assert(js.includes('state.entries.length !== 100'), 'complete T100 snapshot guard missing');
assert(js.includes('syncSelectAvailability'), 'cross-select duplicate prevention missing');
assert(html.includes('data-field-link="CPR" aria-disabled="true"'), 'CPR must remain closed in phase one');
assert(html.includes('data-field-link="GOV" aria-disabled="true"'), 'GOV must remain closed in phase one');
assert(js.includes("['PULSE',3") && js.includes("['INSIGHT',5") && js.includes("['INTELLIGENCE',10"), 'subscription target limits missing');
assert(js.includes("['SNAPSHOT',1") && js.includes("['DEEP DIVE',1"), 'one-time packages missing');
assert(js.includes("['ENTERPRISE T100',100"), 'enterprise package missing');

for (const field of ['ENT', 'UNI']) {
  const rows = data.rankings.filter((row) => row.domain === field && row.ranking_type === 'T100');
  assert.strictEqual(rows.length, 100, `${field} must expose exactly 100 T100 targets`);
  assert.strictEqual(new Set(rows.map((row) => row.external_id)).size, 100, `${field} target IDs must be unique`);
  assert.strictEqual(new Set(rows.map((row) => row.rank)).size, 100, `${field} ranks must be unique`);
  assert.strictEqual(new Set(rows.map((row) => row.as_of_date)).size, 1, `${field} targets must share one observation date`);
}

console.log('BRIDGE TRIO and service-builder contract passed.');
