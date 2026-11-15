/* Execute shipped functions offline; no fetch, storage writes or payment. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const cells={};
const node=()=>({innerHTML:'',textContent:'',style:{},classList:{toggle(){}},addEventListener(){},scrollIntoView(){}});
const document={body:{style:{}},getElementById(id){return cells[id]||(cells[id]=node());},querySelectorAll(){return [];}};
const context={document,window:{},URLSearchParams,location:{search:''},localStorage:{getItem(){return null;},setItem(){throw Error('unexpected storage write');}},fetch(){throw Error('unexpected network');}};
vm.createContext(context);
let source=fs.readFileSync('site/subscribe.js','utf8');
assert(source.includes('render();updateSummary();loadCatalog();'),'bootstrap boundary changed; inspect before testing');
source=source.replace('render();updateSummary();loadCatalog();',
  'window.serviceTest={state,BRIEFINGS,validTargets,renderDeliveryStep,selectBriefing};');
vm.runInContext(source,context);
const api=context.window.serviceTest;
assert(api,'shipped service API extraction failed');
api.selectBriefing('basic');assert.equal(api.state.step,1);assert.equal(api.state.briefing.limit,1);
api.state.targets=['A'];assert.equal(api.validTargets(),true);
api.selectBriefing('standard');assert.equal(api.state.briefing.limit,3);
api.state.targets=['A','A','B'];assert.equal(api.validTargets(),false,'duplicate targets must be rejected');
api.state.targets=['A','B'];assert.equal(api.validTargets(),false,'partial comparison must be rejected');
api.state.targets=['A','B','C'];assert.equal(api.validTargets(),true);
const delivery=api.renderDeliveryStep();
for(const value of ['once','subscription'])assert(delivery.includes('data-delivery="'+value+'"'),'delivery mode missing');
for(const value of ['한국어','English'])assert(delivery.includes('data-language="'+value+'"'),'language missing');
assert(!delivery.includes('data-language="일본어"')&&!delivery.includes('data-language="중국어"'));
assert.equal(api.BRIEFINGS.special.limit,3);
console.log('Service builder runtime passed: BASIC, comparison, duplicates, partial targets, delivery and languages.');
