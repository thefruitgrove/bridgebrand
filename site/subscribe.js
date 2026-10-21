(function(){
'use strict';
var plans={
 subscription:[
  {id:'PULSE',name:'BRIDGE PULSE',limit:3,cycle:'주 3회',brief:'월 스페셜 · 수·금 기본',desc:'핵심 변화를 효율적으로 확인하는 입문형 정기 관측'},
  {id:'INSIGHT',name:'BRIDGE INSIGHT',limit:5,cycle:'주 3회',brief:'월 스페셜 · 수·금 일반',desc:'관계 평판의 구조와 변화를 정기적으로 해석'},
  {id:'CONTINUUM',name:'BRIDGE CONTINUUM',limit:5,cycle:'주 7회',brief:'월 스페셜 · 화~일 일반',desc:'매일 변화를 놓치지 않는 연속 모니터링'},
  {id:'INTELLIGENCE',name:'BRIDGE INTELLIGENCE',limit:10,cycle:'주 3회',brief:'월·수·금 스페셜',desc:'주요 관측일마다 제공하는 고급 심층 분석'},
  {id:'SIGNATURE',name:'BRIDGE SIGNATURE',limit:10,cycle:'주 7회',brief:'월~일 스페셜',desc:'상시 의사결정을 위한 최상위 연속 분석'}
 ],
 once:[
  {id:'SNAPSHOT',name:'BRIDGE SNAPSHOT',limit:1,cycle:'1회',brief:'일반 브리핑',desc:'선택 시점의 관계 구조를 한 번에 확인'},
  {id:'DEEP_DIVE',name:'BRIDGE DEEP DIVE',limit:1,cycle:'1회',brief:'스페셜 브리핑',desc:'사건과 변화 원인을 시각 자료와 함께 심층 분석'}
 ],
 enterprise:[{id:'ENTERPRISE',name:'BRIDGE ENTERPRISE T100',limit:100,cycle:'맞춤',brief:'범위·주기·언어 협의',desc:'T100 전체 또는 조직 목적에 맞춘 별도 설계'}]
};
var state={step:0,mode:'',plan:null,field:new Set(),targets:[],language:''};
var stage=document.getElementById('subscribeStage'),progress=[].slice.call(document.querySelectorAll('#subProgress li'));
var initialParams=new URLSearchParams(location.search),fieldParam=initialParams.get('field');
function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function setStep(n){state.step=n;progress.forEach(function(x,i){x.classList.toggle('active',i===n);x.classList.toggle('done',i<n);});render();updateSummary();window.scrollTo({top:0,behavior:'smooth'});}
function head(no,title,desc){return '<div class="subscribe-step-head"><small>STEP '+no+' OF 6</small><h2>'+title+'</h2><p>'+desc+'</p></div>';}
function back(){return state.step?'<button type="button" class="sub-back" data-action="back">← 이전 단계</button>':'';}
function render(){
 if(state.step===0)stage.innerHTML=head('01','어떤 방식으로 분석받으시겠습니까?','정기적으로 변화를 관측하거나, 필요한 시점에 한 번 분석받을 수 있습니다.')+'<div class="sub-choice-grid"><button data-mode="subscription"><b>REGULAR OBSERVATION</b><strong>정기적으로 관측하기</strong><span>주 3회 또는 주 7회</span></button><button data-mode="once"><b>ONE-TIME ANALYSIS</b><strong>한 번 분석받기</strong><span>일반 또는 스페셜 브리핑</span></button><button data-mode="enterprise"><b>CUSTOM SCOPE</b><strong>T100 맞춤 분석</strong><span>범위와 목적 별도 설계</span></button></div>';
 else if(state.step===1)stage.innerHTML=head('02','서비스를 선택하세요.','보고 주기와 분석 깊이에 따라 구성됩니다.')+'<div class="sub-plan-grid">'+plans[state.mode].map(function(p){return '<button data-plan="'+p.id+'"><small>'+p.cycle+'</small><b>'+p.name+'</b><span>'+p.brief+'</span><p>'+p.desc+'</p><em>대상 '+(p.limit===100?'T100':p.limit+'개')+'</em></button>';}).join('')+'</div>'+back();
 else if(state.step===2)stage.innerHTML=head('03','관측 분야를 선택하세요.','분야별 관계 환경을 섞지 않고 각각의 기준으로 분석합니다.')+'<div class="sub-field-grid">'+['ENT','CPR','UNI','GOV'].map(function(f){return '<button data-field="'+f+'" class="'+(state.field.has(f)?'selected':'')+'"><b>'+f+'</b><span>'+({ENT:'공인·아티스트',CPR:'기업·브랜드',UNI:'대학',GOV:'정부·공공기관'}[f])+'</span></button>';}).join('')+'</div><div class="sub-actions">'+back()+'<button data-action="next" '+(!state.field.size?'disabled':'')+'>대상 선택하기 →</button></div>';
 else if(state.step===3){var lim=state.plan.limit===100?10:state.plan.limit;stage.innerHTML=head('04','분석 대상을 입력하세요.',state.plan.limit===100?'T100 맞춤 범위는 담당 확인 단계에서 확정합니다.':'최대 '+lim+'개 대상을 선택할 수 있습니다.')+'<div class="sub-target-list">'+Array.from({length:lim},function(_,i){return '<label><span>'+(i===0?'MAIN SUBJECT':'SUBJECT '+(i+1))+'</span><input type="text" maxlength="50" data-target="'+i+'" value="'+esc(state.targets[i])+'" placeholder="'+(i===0?'주요 분석 대상':'추가 분석 대상')+'"></label>';}).join('')+'</div><div class="sub-actions">'+back()+'<button data-action="next" '+(!(state.targets[0]||'').trim()?'disabled':'')+'>언어 선택하기 →</button></div>';}
 else if(state.step===4)stage.innerHTML=head('05','제공 언어를 선택하세요.','글로벌 에디션은 번역과 현지 독자의 문맥을 함께 반영합니다.')+'<div class="sub-language-grid">'+['한국어','영어 글로벌 에디션','일본어 글로벌 에디션','중국어 글로벌 에디션'].map(function(l){return '<button data-language="'+l+'" class="'+(state.language===l?'selected':'')+'">'+l+'</button>';}).join('')+'</div><div class="sub-actions">'+back()+'<button data-action="next" '+(!state.language?'disabled':'')+'>구성 확인하기 →</button></div>';
 else stage.innerHTML=head('06','선택한 서비스 구성을 확인하세요.','아래 구성은 회원가입 전 미리보기이며 실제 신청이나 결제가 발생하지 않습니다.')+'<div class="sub-final"><span>'+state.plan.cycle+'</span><h3>'+state.plan.name+'</h3><p>'+state.plan.brief+' · '+state.plan.desc+'</p><ul><li><b>분야</b>'+esc(Array.from(state.field).join(' · '))+'</li><li><b>대상</b>'+esc(state.targets.filter(Boolean).join(' · '))+'</li><li><b>언어</b>'+esc(state.language)+'</li><li><b>공통 제공</b>선택 분야 주간 흐름 · 퍼블리시티 · PDF 보고서</li></ul></div><div class="sub-notice"><b>현재 단계 안내</b><p>회원가입, 개인정보 동의, 결제와 실제 보고서 전달 기능은 아직 연결되지 않았습니다. 선택 완료 후 샘플 보고서를 확인할 수 있습니다.</p></div><div class="sub-actions">'+back()+'<button data-action="complete">이 구성 선택 완료 →</button></div>';
}
function updateSummary(){var p=state.plan;document.getElementById('subSummaryName').textContent=p?p.name:'선택을 시작하세요';document.getElementById('subSummaryMode').textContent=state.mode==='subscription'?'정기 관측':state.mode==='once'?'단건 분석':state.mode==='enterprise'?'T100 맞춤':'—';document.getElementById('subSummaryField').textContent=state.field.size?Array.from(state.field).join(' · '):'—';document.getElementById('subSummaryTargets').textContent=state.targets.filter(Boolean).join(', ')||'—';document.getElementById('subSummaryLanguage').textContent=state.language||'—';document.getElementById('subSummaryDelivery').textContent=p?(p.cycle+' · '+p.brief+' · 대상 '+(p.limit===100?'T100':p.limit+'개')):'선택한 서비스의 제공 구성이 표시됩니다.';}
stage.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;if(b.dataset.mode){state.mode=b.dataset.mode;state.plan=null;setStep(1);}else if(b.dataset.plan){state.plan=plans[state.mode].find(function(p){return p.id===b.dataset.plan;});state.field=new Set(fieldParam&&['ENT','CPR','UNI','GOV'].includes(fieldParam)?[fieldParam]:[]);state.targets=[];setStep(2);}else if(b.dataset.field){state.field.has(b.dataset.field)?state.field.delete(b.dataset.field):state.field.add(b.dataset.field);render();updateSummary();}else if(b.dataset.language){state.language=b.dataset.language;render();updateSummary();}else if(b.dataset.action==='back')setStep(Math.max(0,state.step-1));else if(b.dataset.action==='next')setStep(state.step+1);else if(b.dataset.action==='complete')complete();});
stage.addEventListener('input',function(e){if(e.target.dataset.target===undefined)return;state.targets[Number(e.target.dataset.target)]=e.target.value;var next=stage.querySelector('[data-action="next"]');if(next)next.disabled=!(state.targets[0]||'').trim();updateSummary();});
function complete(){var saved={mode:state.mode,plan:state.plan.name,field:Array.from(state.field),targets:state.targets.filter(Boolean),language:state.language,savedAt:new Date().toISOString()};localStorage.setItem('bridge-service-draft',JSON.stringify(saved));document.getElementById('subscribeDialogPlan').innerHTML='<b>'+esc(saved.plan)+'</b><span>'+esc(saved.field.join(' · '))+' · '+esc(saved.targets.join(' · '))+' · '+esc(saved.language)+'</span>';document.getElementById('subscribeDialog').hidden=false;document.body.style.overflow='hidden';}
document.getElementById('subscribeDialogClose').addEventListener('click',function(){document.getElementById('subscribeDialog').hidden=true;document.body.style.overflow='';});
var initialMode=initialParams.get('mode'),initialPlan=(initialParams.get('plan')||'').replace(/\s+/g,'_');
if(initialPlan==='ENTERPRISE_T100')initialPlan='ENTERPRISE';
if(plans[initialMode]){
 state.mode=initialMode;
 state.plan=plans[initialMode].find(function(p){return p.id===initialPlan;})||plans[initialMode][0];
 if(fieldParam&&['ENT','CPR','UNI','GOV'].includes(fieldParam))state.field.add(fieldParam);
 state.targets=(initialParams.get('targets')||'').split(',').map(function(x){return x.trim();}).filter(Boolean);
 state.language=initialParams.get('language')||'';
 state.step=state.field.size?3:2;
}
render();updateSummary();
})();
