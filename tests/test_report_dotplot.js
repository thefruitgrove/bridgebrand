'use strict';
// Offline visual-data QA: selected entity must appear in the 29-page STANDARD
// score distribution even when outside the top 20. No network/DB writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'site', 'briefing.js'), 'utf8');
const start = source.indexOf('function printDotPlot(rows,pick){');
const end = source.indexOf('\nfunction printProse(', start);
assert.ok(start > 0 && end > start, 'dot plot source function was not found');
const context = vm.createContext({num: (v, digits = 1) => Number(v).toFixed(digits)});
vm.runInContext(source.slice(start, end), context);
const rows = Array.from({length: 100}, (_, i) => ({
  external_id: 'e' + (i + 1),
  name: '대상 ' + String(i + 1).padStart(3, '0'),
  rank: i + 1,
  daily_index: 100 - i * 0.36,
}));
for (const rank of [1, 10, 19, 20, 21, 50, 95, 100]) {
  const pick = rows[rank - 1];
  const html = context.printDotPlot(rows, pick);
  const names = [...html.matchAll(/<span>대상 (\d{3})<\/span>/g)].map(m => Number(m[1]));
  assert.ok(names.includes(rank), 'selected rank ' + rank + ' missing from distribution');
  assert.equal((html.match(/class="is-pick"/g) || []).length, 1, 'selected rank ' + rank + ' must have one highlighted dot');
  assert.ok(names.length <= 20, 'render should not overflow 20 rows');
  assert.ok(names.includes(1), 'always show a top ranking reference');
  assert.match(html, /print-dotplot-note/, 'visible range must be explained');
  if (rank > 20) {
    assert.ok(!names.includes(20), 'do not silently claim to show entire top 20 when selection is lower');
    assert.match(html, /표시되지 않은 순위는 생략/, 'omitted ranks must be disclosed');
  } else {
    assert.equal(names.length, 20, 'show top 20 for selected rank within top 20');
  }
}
console.log('STANDARD dot-plot selected-rank scenarios: 8 passed');
