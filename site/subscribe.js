(function(){
'use strict';

var BRIEFINGS={
 basic:{id:'basic',name:'BASIC 기본 브리핑',short:'BASIC',limit:1,pages:'15–20페이지',sample:'briefing.html?field=ENT&pick=STAR-091&compareA=STAR-056&compareB=STAR-100&language=한국어&briefing=basic&sample=ent-20261103',description:'한 대상의 핵심지표·순위·여섯 축·활동량·근거 상태와 다음 관측 질문을 정리합니다.'},
 standard:{id:'standard',name:'STANDARD 일반 브리핑',short:'STANDARD',limit:3,pages:'21–33페이지',sample:'briefing.html?field=ENT&pick=STAR-091&compareA=STAR-056&compareB=STAR-100&language=한국어&sample=ent-20261103',description:'중심 대상과 비교 대상 둘의 관계 구조와 근거 차이를 분석하고 PUBLICITY까지 제공합니다.'},
 special:{id:'special',name:'SPECIAL 스페셜 브리핑',short:'SPECIAL',limit:3,pages:'최소 35페이지',sample:'subscription-sample.html?edition=special',description:'STANDARD 전체에 3일 흐름, 이전 2주 PUBLICITY, 대안 해석과 전략 선택지를 확장합니다.'}
};
var FIELD_LABEL={ENT:'공인·아티스트',CPR:'기업·브랜드',UNI:'대학',GOV:'정부·공공기관'};
var state={step:0,briefing:null,field:'',targets:[],delivery:'',language:'한국어'};
var catalog={ENT:[],CPR:[],UNI:[],GOV:[]},catalogStatus='loading';
var stage=document.getElementById('subscribeStage');
var progress=[].slice.call(document.querySelectorAll('#subProgress li'));
var initialParams=new URLSearchParams(location.search);
var isEnglish=initialParams.get('lang')==='en'||(!initialParams.get('lang')&&localStorage.getItem('bridge-ui-language')==='en');

function esc(value){return String(value||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function head(no,title,desc){return '<div class="subscribe-step-head"><small>STEP '+no+' OF 4</small><h2>'+title+'</h2><p>'+desc+'</p></div>';}
function back(){return state.step?'<button type="button" class="sub-back" data-action="back">← 이전 단계</button>':'';}
function setStep(step){state.step=step;progress.forEach(function(item,index){item.classList.toggle('active',index===step);item.classList.toggle('done',index<step);});render();updateSummary();document.getElementById('serviceConfigurator').scrollIntoView({behavior:'smooth',block:'start'});}
function currentPrice(){
 if(!state.briefing)return null;
 var basic=state.briefing.id==='basic';
 return state.delivery==='subscription'?
  (basic?{krw:'6,000원',usd:'약 $4.5',detail:'주 2회(화·금) · 4주 기준 총 8회',unit:'월 단위 결제'}:{krw:'10,000원',usd:'약 $7.5',detail:'주 3회(화·목·토) · 4주 기준 총 12회',unit:'월 단위 결제'}):
  (basic?{krw:'1,000원',usd:'약 $0.8',detail:'선택 시점의 정식 보고서 1회',unit:'1회 기준'}:{krw:'1,500원',usd:'약 $1.2',detail:'선택 시점의 정식 보고서 1회',unit:'1회 기준'});
}
function validTargets(){var values=state.targets.slice(0,state.briefing?state.briefing.limit:0).filter(Boolean);return state.briefing&&values.length===state.briefing.limit&&new Set(values).size===values.length;}
function loadCatalog(){fetch('data/latest.json',{cache:'no-store'}).then(function(response){if(!response.ok)throw new Error('T100 공개 데이터를 불러오지 못했습니다.');return response.json();}).then(function(data){Object.keys(catalog).forEach(function(field){var rows=(data.rankings||[]).filter(function(row){return row.domain===field&&row.ranking_type==='T100';});var date=[].concat(rows.map(function(row){return row.as_of_date||'';})).sort().pop();catalog[field]=rows.filter(function(row){return row.as_of_date===date;}).sort(function(a,b){return Number(a.rank)-Number(b.rank);});});catalogStatus='ready';render();}).catch(function(){catalogStatus='error';render();});}

function renderBriefingStep(){
 return head('01','어떤 분석이 필요하십니까?','상품 이름보다 분석할 대상의 수와 필요한 설명의 깊이를 먼저 선택하세요.')+
 '<div class="sub-briefing-grid">'+
 '<article class="sub-briefing-choice '+(state.briefing&&state.briefing.id==='basic'?'selected':'')+'"><small>BASIC · 15–20 PAGES</small><h3>하나를 빠르게 이해하기</h3><p>한 대상의 현재 위치와 관계 구조를 필요한 정보 중심으로 읽습니다.</p><button type="button" data-briefing="basic">BASIC 선택 →</button></article>'+
 '<article class="sub-briefing-choice comparison '+(state.briefing&&state.briefing.id!=='basic'?'selected':'')+'"><small>STANDARD · SPECIAL BRIEFING</small><h3>세 대상을 비교하고 깊게 분석하기</h3><p>같은 분야의 중심 대상 하나와 비교 대상 둘을 동일한 조건에서 읽습니다.</p><div class="sub-depth-actions"><button type="button" data-briefing="standard"><b>STANDARD</b><span>관계 구조와 PUBLICITY</span></button><button type="button" data-briefing="special"><b>SPECIAL</b><span>시간 흐름과 전략까지 확장</span></button></div></article></div>';
}
function targetInputs(){
 if(!state.briefing)return '';
 var labels=state.briefing.limit===1?['MY PICK']:['MY PICK','COMPARE A','COMPARE B'];
 var rows=catalog[state.field]||[];
 if(catalogStatus==='loading')return '<div class="sub-data-status">최신 '+state.field+' T100을 불러오고 있습니다.</div>';
 if(catalogStatus==='error'||!rows.length)return '<div class="sub-data-status error">최신 T100을 확인할 수 없어 대상 선택을 잠시 중단했습니다.</div>';
 return '<div class="sub-target-list">'+labels.map(function(label,index){return '<label><span>'+label+'</span><select data-target="'+index+'"><option value="">'+(index===0?'주요 분석 대상 선택':'비교 대상 '+index+' 선택')+'</option>'+rows.map(function(row){var name=String(row.name||'');return '<option value="'+esc(name)+'" '+(state.targets[index]===name?'selected':'')+'>'+String(row.rank).padStart(2,'0')+' · '+esc(name)+'</option>';}).join('')+'</select></label>';}).join('')+'</div><p class="sub-target-rule">최신 공개 T100 안의 서로 다른 대상만 선택할 수 있습니다. 입력 목록은 매일 공개 데이터와 함께 갱신됩니다.</p>';
}
function renderScopeStep(){
 return head('02','분야와 대상을 선택하세요.','한 보고서에서는 한 분야의 T100만 사용합니다. 서로 다른 분야의 대상은 직접 비교하지 않습니다.')+
 '<div class="sub-field-grid">'+['ENT','CPR','UNI','GOV'].map(function(field){return '<button type="button" data-field="'+field+'" class="'+(state.field===field?'selected':'')+'"><b>'+field+'</b><span>'+FIELD_LABEL[field]+'</span></button>';}).join('')+'</div>'+
 (state.field?'<div class="sub-target-block visible"><p><b>'+state.field+' T100</b> 안에서 '+(state.briefing.limit===1?'분석 대상 하나':'중심 대상 하나와 비교 대상 둘')+'를 선택하세요.</p>'+targetInputs()+'</div>':'<p class="sub-field-prompt">먼저 CPR·GOV·UNI·ENT 중 한 분야를 선택하세요.</p>')+
 '<div class="sub-actions">'+back()+'<button type="button" data-action="next" '+(!validTargets()?'disabled':'')+'>제공 방식 선택 →</button></div>';
}
function renderDeliveryStep(){
 var basic=state.briefing&&state.briefing.id==='basic';
 return head('03','어떻게 받아보시겠습니까?','보고서의 분석 기준은 유지하고, 필요한 시점에 한 번 받거나 같은 대상을 정기적으로 관측할 수 있습니다.')+
 '<div class="sub-price-label">SERVICE FEE · 이용요금</div><div class="sub-choice-grid sub-delivery-grid"><button type="button" data-delivery="once" class="'+(state.delivery==='once'?'selected':'')+'"><b>ONE-TIME</b><strong>한 번 분석받기</strong><span>선택 시점의 정식 보고서</span><em>'+(basic?'1,000원':'1,500원')+'</em><small>'+(basic?'약 $0.8':'약 $1.2')+' · 환율 변동 가능</small></button><button type="button" data-delivery="subscription" class="'+(state.delivery==='subscription'?'selected':'')+'"><b>CONTINUOUS</b><strong>정기적으로 관측하기</strong><span>같은 대상을 반복 관측</span><em>'+(basic?'6,000원':'10,000원')+'</em><small>'+(basic?'주 2회(화·금) · 4주 8회 · 약 $4.5':'주 3회(화·목·토) · 4주 12회 · 약 $7.5')+'</small></button></div><p class="sub-price-note">정기 관측은 한 달 단위 결제 기준이며, 달러 환산액은 결제 시점 환율에 따라 달라질 수 있습니다.</p>'+
 '<fieldset class="sub-language-field"><legend>제공 언어</legend><div class="sub-language-grid"><button type="button" data-language="한국어" class="'+(state.language==='한국어'?'selected':'')+'">한국어</button><button type="button" data-language="English" class="'+(state.language==='English'?'selected':'')+'">English</button></div><p>영문판에서도 T100 대상명은 한글 원본을 유지합니다.</p></fieldset>'+
 '<div class="sub-actions">'+back()+'<button type="button" data-action="next" '+(!state.delivery||!state.language?'disabled':'')+'>구성 확인 →</button></div>';
}
function renderReviewStep(){
 var briefing=state.briefing;
 var price=currentPrice();
 return head('04','선택한 분석 구성을 확인하세요.','현재는 신청 전 미리보기 단계입니다. 회원가입·결제·실제 전달 기능은 최종 운영 단계에서 연결됩니다.')+
 '<div class="sub-final"><span>'+briefing.pages+'</span><h3>'+briefing.name+'</h3><p>'+briefing.description+'</p><ul><li><b>분야</b>'+esc(state.field+' · '+FIELD_LABEL[state.field])+'</li><li><b>대상</b>'+esc(state.targets.slice(0,briefing.limit).filter(Boolean).join(' · '))+'</li><li><b>제공</b>'+(state.delivery==='once'?'한 번 분석':'정기 관측')+'</li><li><b>언어</b>'+esc(state.language)+'</li></ul><div class="sub-review-price"><small>SERVICE FEE</small><strong>'+price.krw+'</strong><span>'+price.usd+' · '+price.detail+' · '+price.unit+'</span></div></div><div class="sub-notice"><b>해석 기준</b><p>같은 분야·같은 기준일·같은 공개 범위에서 비교하며, 관측되지 않은 원인을 임의로 만들지 않습니다. SPECIAL은 더 많은 자료를 사용하지만 근거의 한계를 넘는 결론을 뜻하지 않습니다.</p></div><div class="sub-actions">'+back()+'<button type="button" data-action="complete">이 구성 저장하기 →</button></div>';
}
function render(){
 if(state.step===0)stage.innerHTML=renderBriefingStep();
 else if(state.step===1)stage.innerHTML=renderScopeStep();
 else if(state.step===2)stage.innerHTML=renderDeliveryStep();
 else stage.innerHTML=renderReviewStep();
 translateStage();
}
function translateStage(){
 if(!isEnglish)return;
 var map={
  '어떤 분석이 필요하십니까?':'What kind of analysis do you need?','상품 이름보다 분석할 대상의 수와 필요한 설명의 깊이를 먼저 선택하세요.':'Choose the number of subjects and analytical depth before learning plan names.',
  '하나를 빠르게 이해하기':'Understand one subject quickly','한 대상의 현재 위치와 관계 구조를 필요한 정보 중심으로 읽습니다.':'Read one subject’s current position and relationship structure in a focused report.','BASIC 선택 →':'Choose BASIC →',
  '세 대상을 비교하고 깊게 분석하기':'Compare three subjects in depth','같은 분야의 중심 대상 하나와 비교 대상 둘을 동일한 조건에서 읽습니다.':'Read one primary subject and two comparison subjects in the same field under identical conditions.','관계 구조와 PUBLICITY':'Relationship structure and PUBLICITY','시간 흐름과 전략까지 확장':'Extend to time flow and strategy',
  '분야와 대상을 선택하세요.':'Choose a field and subjects.','한 보고서에서는 한 분야의 T100만 사용합니다. 서로 다른 분야의 대상은 직접 비교하지 않습니다.':'Each report uses one field’s T100 only. Subjects from different fields are never compared directly.','공인·아티스트':'Public figures · artists','기업·브랜드':'Companies · brands','대학':'Universities','정부·공공기관':'Government · public institutions','먼저 CPR·GOV·UNI·ENT 중 한 분야를 선택하세요.':'Choose one field: CPR, GOV, UNI or ENT.','제공 방식 선택 →':'Choose delivery →',
  '어떻게 받아보시겠습니까?':'How would you like to receive it?','보고서의 분석 기준은 유지하고, 필요한 시점에 한 번 받거나 같은 대상을 정기적으로 관측할 수 있습니다.':'Keep the same analytical standard and receive one report or observe the same subjects regularly.','한 번 분석받기':'One-time analysis','선택 시점의 정식 보고서':'A formal report at the selected point in time','정기적으로 관측하기':'Regular observation','같은 대상을 반복 관측':'Repeated observation of the same subjects','제공 언어':'Delivery language','영문판에서도 T100 대상명은 한글 원본을 유지합니다.':'T100 subject names remain in their original Korean in the English edition.','← 이전 단계':'← Previous','구성 확인 →':'Review configuration →',
  '선택한 분석 구성을 확인하세요.':'Review your analysis configuration.','현재는 신청 전 미리보기 단계입니다. 회원가입·결제·실제 전달 기능은 최종 운영 단계에서 연결됩니다.':'This is a pre-application preview. Account, payment and delivery will be connected in the final operating stage.','한 번 분석':'One-time analysis','정기 관측':'Regular observation','분야':'Field','대상':'Subjects','제공':'Delivery','언어':'Language','해석 기준':'Interpretive standard','같은 분야·같은 기준일·같은 공개 범위에서 비교하며, 관측되지 않은 원인을 임의로 만들지 않습니다. SPECIAL은 더 많은 자료를 사용하지만 근거의 한계를 넘는 결론을 뜻하지 않습니다.':'Comparison uses the same field, reference date and public-data scope. Unobserved causes are not invented. SPECIAL uses more material, but does not claim beyond the evidence.','이 구성 저장하기 →':'Save this configuration →'
 };
 var walker=document.createTreeWalker(stage,NodeFilter.SHOW_TEXT);var node;
 while((node=walker.nextNode())){var value=node.nodeValue.trim();if(map[value])node.nodeValue=node.nodeValue.replace(value,map[value]);else if(/ T100 안에서 /.test(value))node.nodeValue=value.replace(' 안에서 분석 대상 하나를 입력하세요.',' — enter one subject.').replace(' 안에서 중심 대상 하나와 비교 대상 둘을 입력하세요.',' — enter one primary subject and two comparison subjects.');}
 stage.querySelectorAll('input[data-target]').forEach(function(input,index){input.placeholder=index===0?'Primary subject':'Comparison subject '+index;});
}
function updateSummary(){
 var briefing=state.briefing;
 var englishName=briefing?({basic:'BASIC Briefing',standard:'STANDARD Briefing',special:'SPECIAL Briefing'}[briefing.id]):'Choose an analysis path';
 document.getElementById('subSummaryName').textContent=isEnglish?englishName:(briefing?briefing.name:'분석 방식을 선택하세요');
 document.getElementById('subSummaryMode').textContent=briefing?briefing.short+' · '+(isEnglish?({basic:'15–20 pages',standard:'21–33 pages',special:'minimum 35 pages'}[briefing.id]):briefing.pages):'—';
 document.getElementById('subSummaryField').textContent=state.field?state.field+' · '+FIELD_LABEL[state.field]:'—';
 document.getElementById('subSummaryTargets').textContent=state.targets.slice(0,briefing?briefing.limit:0).filter(Boolean).join(', ')||'—';
 document.getElementById('subSummaryDeliveryMode').textContent=state.delivery==='once'?(isEnglish?'One-time analysis':'한 번 분석'):state.delivery==='subscription'?(isEnglish?'Regular observation':'정기 관측'):'—';
 document.getElementById('subSummaryLanguage').textContent=state.language||'—';
 var englishDescription=briefing?({basic:'One subject’s key indicators, rank, six dimensions, activity, evidence status and next observation questions.',standard:'Relationship structures and evidence differences across three subjects, including PUBLICITY.',special:'STANDARD plus a three-day flow, the previous two weeks of PUBLICITY, alternative readings and strategic options.'}[briefing.id]):'The selected scope and deliverables will appear here.';
 document.getElementById('subSummaryDelivery').textContent=isEnglish?englishDescription:(briefing?briefing.description:'선택한 분석의 범위와 결과물이 표시됩니다.');
 var sample=document.getElementById('summarySampleLink');sample.href=briefing?briefing.sample:'subscription-sample.html?edition=basic';sample.textContent=briefing?briefing.short+(isEnglish?' sample →':' 샘플 보기 →'):(isEnglish?'View a briefing sample →':'브리핑 샘플 보기 →');
}
function selectBriefing(id){state.briefing=BRIEFINGS[id];state.targets=state.targets.slice(0,state.briefing.limit);setStep(1);}
function complete(){
 var saved={briefing:state.briefing.id,field:state.field,targets:state.targets.slice(0,state.briefing.limit).filter(Boolean),delivery:state.delivery,language:state.language,savedAt:new Date().toISOString()};
 localStorage.setItem('bridge-service-draft',JSON.stringify(saved));
 var price=currentPrice();document.getElementById('subscribeDialogPlan').innerHTML='<b>'+esc(state.briefing.name)+'</b><span>'+esc(state.field+' · '+saved.targets.join(' · ')+' · '+(state.delivery==='once'?'한 번 분석':'정기 관측')+' · '+state.language)+'</span><strong>'+price.krw+' <small>'+price.usd+'</small></strong><em>'+price.detail+'</em>';
 document.getElementById('subscribeDialogSample').href=state.briefing.sample;
 document.getElementById('subscribeDialog').hidden=false;document.body.style.overflow='hidden';
}

stage.addEventListener('click',function(event){
 var button=event.target.closest('button');if(!button)return;
 if(button.dataset.briefing)selectBriefing(button.dataset.briefing);
 else if(button.dataset.field){state.field=button.dataset.field;state.targets=[];render();updateSummary();}
 else if(button.dataset.delivery){state.delivery=button.dataset.delivery;render();updateSummary();}
 else if(button.dataset.language){state.language=button.dataset.language;render();updateSummary();}
 else if(button.dataset.action==='back')setStep(Math.max(0,state.step-1));
 else if(button.dataset.action==='next')setStep(state.step+1);
 else if(button.dataset.action==='complete')complete();
});
stage.addEventListener('change',function(event){if(event.target.dataset.target===undefined)return;state.targets[Number(event.target.dataset.target)]=event.target.value;render();updateSummary();});
document.querySelectorAll('[data-start-briefing]').forEach(function(link){link.addEventListener('click',function(){selectBriefing(link.dataset.startBriefing==='basic'?'basic':'standard');});});
document.getElementById('subscribeDialogClose').addEventListener('click',function(){document.getElementById('subscribeDialog').hidden=true;document.body.style.overflow='';});

var initialBriefing=initialParams.get('briefing')||initialParams.get('edition');if(BRIEFINGS[initialBriefing])state.briefing=BRIEFINGS[initialBriefing];
var initialField=initialParams.get('field');if(FIELD_LABEL[initialField])state.field=initialField;
state.targets=(initialParams.get('targets')||'').split(',').map(function(value){return value.trim();}).filter(Boolean);
if(state.briefing&&state.field)state.step=1;
render();updateSummary();loadCatalog();
})();
