'use strict';
/* BRIDGE Evidence / WHAT NEXT regression test.
 * Run: node tests/test_evidence_action_rules.js
 * No external dependencies and no database writes.
 */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const js=fs.readFileSync(path.join(root,'site/briefing.js'),'utf8');
const start=js.indexOf('/* Evidence-aware next-check ordering');
const end=js.indexOf('function activityMeaning(e)',start);
assert(start>=0&&end>start,'Expected evidence action helpers not found');
const context={
 AXES:['B','R','I','D','G','E'],
 AXIS_NAME:{B:'도달',R:'반응',I:'정체성',D:'경험',G:'행동유발',E:'책임·지속'},
 hasNumber:v=>v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v)),
 num:(v,d=2)=>Number.isFinite(Number(v))?Number(v).toFixed(d):'N/R',
 valid:(e,a)=>Boolean(e&&e.axis_status&&['observed','maintained'].includes(e.axis_status[a])&&e.axis_scores&&e.axis_scores[a]!==null&&e.axis_scores[a]!==undefined&&e.axis_scores[a]!==''&&Number.isFinite(Number(e.axis_scores[a]))),
 escEvidence:v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))
};
vm.createContext(context);
vm.runInContext(js.slice(start,end),context,{timeout:1000});
const {actionCheckItems,actionCheckSummary,actionCheckHtml}=context;
const snapshot=JSON.parse(fs.readFileSync(path.join(root,'site/data/latest.json'),'utf8'));
assert(Array.isArray(snapshot.rankings)&&snapshot.rankings.length>0,'Missing published snapshot fixture');
const order={reference:0,maintained:1,observed:2};
for(const row of snapshot.rankings){
 const items=actionCheckItems(row);
 const summary=actionCheckSummary(row);
 assert.equal(items.length,6,row.external_id);
 assert.equal(summary.length,3,row.external_id);
 for(let i=1;i<items.length;i++)assert(order[items[i-1].group]<=order[items[i].group],row.external_id);
 assert(summary.every(x=>/^[BRIDGE]$/.test(x.axis)),row.external_id);
 assert(!actionCheckHtml(row).includes('undefined'),row.external_id);
}
const probe={
 axis_status:{B:'observed',R:'reference',I:'maintained',D:'observed',G:'observed',E:'observed'},
 axis_scores:{B:80,R:50,I:10,D:40,G:70,E:75},
 axis_evidence_dates:{B:'<script>bad()</script>',I:'2026-11-08'}
};
assert.equal(actionCheckItems(probe)[0].axis,'R');
assert.equal(actionCheckItems(probe)[1].axis,'I');
assert.equal(actionCheckItems(probe)[2].axis,'D');
assert(!actionCheckHtml(probe,6).includes('<script>'),'Unescaped evidence text');
console.log('BRIDGE WHAT NEXT evidence checks passed: '+snapshot.rankings.length+' published entities');
