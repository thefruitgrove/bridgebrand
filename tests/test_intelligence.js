const fs = require('fs');
const assert = require('assert');

const html = fs.readFileSync('site/intelligence.html', 'utf8');
const js = fs.readFileSync('site/intelligence.js', 'utf8');
const subscribeHtml = fs.readFileSync('site/subscribe.html', 'utf8');
const subscribeJs = fs.readFileSync('site/subscribe.js', 'utf8');
const briefingHtml = fs.readFileSync('site/briefing.html', 'utf8');
const briefingJs = fs.readFileSync('site/briefing.js', 'utf8');
const i18nJs = fs.readFileSync('site/i18n.js', 'utf8');
const data = JSON.parse(fs.readFileSync('site/data/latest.json', 'utf8'));

['trioPick1', 'trioPick2', 'trioPick3', 'trioSnapshotMeta', 'serviceBuilder'].forEach((id) => {
  assert(html.includes(`id="${id}"`), `missing UI element: ${id}`);
});

assert(js.includes("const FIELDS = ['CPR', 'GOV', 'UNI', 'ENT']"), 'discovery must support all four fields');
assert(js.includes('new Set(ids).size!==3'), 'duplicate target protection missing');
assert(js.includes('state.entries.length < 3') && js.includes('state.entries.length > 100'), 'published T100 range guard missing');
assert(js.includes('completeRange'), 'contiguous rank guard missing');
assert(js.includes('syncSelectAvailability'), 'cross-select duplicate prevention missing');
assert(js.includes("'00 / BRIDGE 6단계 브리핑 체험'"), 'generic six-stage trial label missing');
assert(js.includes('MY PICK을 선택하세요') && js.includes("select.value=''"), 'selectors must begin blank');
assert(html.includes('intelligence.html?field=CPR#trioBeta'), 'CPR discovery route missing');
assert(html.includes('intelligence.html?field=GOV#trioBeta'), 'GOV discovery route missing');
assert(js.includes("['PULSE',3") && js.includes("['INSIGHT',5") && js.includes("['INTELLIGENCE',10"), 'subscription target limits missing');
assert(js.includes("['SNAPSHOT',1") && js.includes("['DEEP DIVE',1"), 'one-time packages missing');
assert(js.includes("['ENTERPRISE T100',100"), 'enterprise package missing');
assert(html.includes('subscribe.html#serviceOverview'), 'subscription entry route missing');
['briefing','subscription','scope','one-time'].forEach((name) => {
  assert(subscribeHtml.includes(`data-service-panel="${name}"`), `missing subscription overview: ${name}`);
  assert(subscribeHtml.includes(`data-service-content="${name}"`), `missing subscription content: ${name}`);
});
['방식','서비스','분야','대상','언어','확인'].forEach((label) => assert(subscribeHtml.includes(`<li>${label}</li>`) || subscribeHtml.includes(`<li class="active">${label}</li>`), `missing configurator step: ${label}`));
assert(subscribeJs.includes('showOverview'), 'subscription overview navigation missing');
assert(briefingHtml.includes('id="trialConversion"'), 'final-stage conversion panel missing');
assert(briefingHtml.includes('ONE-TIME BRIEFING'), 'one-time briefing label missing');
assert(briefingJs.includes("$('trialConversion').hidden=stage!==6"), 'conversion panel must appear only at report stage');
assert(subscribeJs.includes("['한국어','영어 글로벌 에디션']"), 'subscription languages must be Korean and English only');
assert(!subscribeHtml.includes('일본어') && !subscribeHtml.includes('중국어'), 'Japanese and Chinese options must be removed');
assert(i18nJs.includes("const PUBLICITY=new Set(['publicity.html','publicity-article.html'])"), 'PUBLICITY must remain outside the bilingual conversion scope');
assert(i18nJs.includes('T100 entity names, scores and source records are deliberately preserved'), 'T100 Korean-name preservation contract missing');
assert(i18nJs.includes("const path=rawPath.includes('.')?rawPath:`${rawPath||'index'}.html`"), 'extensionless production routes must resolve to page translation keys');
assert(i18nJs.includes('function applyStructuredEnglish()'), 'nested hero and service structures need selector-based English translation');
assert(i18nJs.includes("setText('#trioRun','Start comparison →')"), 'English discovery action missing');
assert(i18nJs.includes("if(path==='subscribe.html')"), 'English subscription structure translation missing');

for (const field of ['CPR', 'GOV', 'ENT', 'UNI']) {
  const rows = data.rankings.filter((row) => row.domain === field && row.ranking_type === 'T100');
  assert(rows.length >= 3 && rows.length <= 100, `${field} must expose a usable published T100 range`);
  assert.strictEqual(new Set(rows.map((row) => row.external_id)).size, rows.length, `${field} target IDs must be unique`);
  assert.strictEqual(new Set(rows.map((row) => row.rank)).size, rows.length, `${field} ranks must be unique`);
  assert.strictEqual(new Set(rows.map((row) => row.as_of_date)).size, 1, `${field} targets must share one observation date`);
  rows.sort((a,b) => a.rank-b.rank).forEach((row,index) => assert.strictEqual(row.rank,index+1,`${field} ranks must be contiguous`));
}

console.log('BRIDGE TRIO and service-builder contract passed.');
