/* Run the production presentation functions with a minimal DOM. No network. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('site/script.js','utf8');
function take(name,next){
  const start=source.indexOf('  function '+name+'(');
  const end=source.indexOf('\n  function '+next+'(',start);
  assert(start>=0&&end>start,'production function boundaries');
  return source.slice(start,end);
}
const cells={};
const document={getElementById(id){return cells[id]||(cells[id]={textContent:'',innerHTML:'',style:{},classList:{toggle(){},add(){},remove(){}}});}};
const context={window:{},document,modalOverlay:{classList:{add(){}}}};
vm.createContext(context);
vm.runInContext(take('scopeMessage','snapshotDiagnosis')+take('snapshotDiagnosis','selectModalCase'),context);
const selection=source.slice(source.indexOf('  function selectModalCase('),source.indexOf('  // Load the current presentation'));
vm.runInContext(selection,context);
vm.runInContext(take('polygonPoints','buildRadarSVG')+source.slice(source.indexOf('  function buildRadarSVG('),source.indexOf('\n  var modalOverlay')),context);
vm.runInContext(take('openBridgeModal','closeBridgeModal'),context);
const values={B:60,R:50,I:80,D:75,G:50,E:50};
const past={dims:values,axis_status:{B:'observed',R:'reference',I:'observed',D:'observed',G:'reference',E:'reference'},reference_axes_count:3,daily_index:61,weekly_index:63,score:61,last_week_index:50,comparison_status:'scope_expanded',history:[{score:50}],snapshot_date:'2026-10-14',trust:'C'};
context.window.BRIDGE_DATED_CASES={'CPR|기업A|2026-10-14':past};
context.window.BRIDGE_LIVE_CASES={'CPR|기업A':{...past,daily_index:99}};
context.openBridgeModal('기업A','CPR','T100','2026-10-14');
assert.equal(cells.bmIndexPoint.textContent,61,'selected historical date must not use current score 99');
assert.match(cells.bridgeModalSub.textContent,/2026-10-14/);
assert.match(cells.bmWow.textContent,/근거 범위 확대/,'scope change must block improvement delta');
assert.match(cells.bridgeRadar.innerHTML,/stroke-dasharray="5,4"/,'reference edges must be distinct');
assert.match(cells.bridgeRadar.innerHTML,/대상 평가값 아님/);
assert(!context.snapshotDiagnosis({...past,weekly_index:90}).includes('웃돕니다'),'scope expansion must not claim improvement');
assert.match(context.snapshotDiagnosis({...past,comparison_status:'same_scope',last_week_index:0,weekly_index:0}),/유지/,'zero is a valid value');
context.openBridgeModal('기업A','CPR','T100','2026-09-01');
assert.equal(cells.bmIndexPoint.textContent,'N/R','missing historical record must not fall back to current');
assert.match(cells.bridgeModalFlag.textContent,/최신 자료로 대체하지 않습니다/);
console.log('Presentation regressions passed: dated modal, missing history, scope-limited comparisons, reference radar, zero values.');
