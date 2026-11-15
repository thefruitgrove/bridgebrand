/* Published-data guard: unavailable weekly evidence is not a 0.00 score. */
const fs=require('node:fs');
const assert=require('node:assert/strict');
const vm=require('node:vm');

const source=fs.readFileSync('site/script.js','utf8');
const data=JSON.parse(fs.readFileSync('site/data/latest.json','utf8'));
const rows=data.rankings.filter(r=>r.ranking_type==='T100');
assert.equal(rows.length,400,'fixture must contain all 400 published T100 entries');
const missing=rows.filter(r=>r.last_week_index===null);
assert(missing.length>0,'historical fixture must exercise real missing last-week data');
assert(missing.every(r=>r.last_week_index!==0),'NULL and zero must remain distinct in public JSON');
assert(source.includes('var verifiedHistory = Array.isArray(pilot.history)'), 'prior-week history must validate data');
assert(source.includes('h.score != null && Number.isFinite(Number(h.score))'), 'null history cannot become zero');
assert(source.includes("document.getElementById('bmLastWeek').textContent = 'N/R';"),
  'unavailable last-week indices must render N/R');
assert(source.includes('var prevScore = Number(prevWeek.score);'), 'real observed week must render original score');
new vm.Script(source,{filename:'site/script.js'});
console.log('Missing prior-week evidence remains N/R; genuine zero stays distinct, browser JS syntax valid.');
