(function () {
  'use strict';
  const FIELDS = ['CPR', 'GOV', 'UNI', 'ENT'];
  const params = new URLSearchParams(location.search);
  const initialField = FIELDS.includes(params.get('field')) ? params.get('field') : 'ENT';
  const state = { entries: [], field: initialField, language: '한국어', mode: 'subscription', pkg: 'PULSE' };
  const packages = {
    subscription: [['PULSE',3,'주 3회 · 월 스페셜, 수·금 기본'],['INSIGHT',5,'주 3회 · 월 스페셜, 수·금 일반'],['CONTINUUM',5,'주 7회 · 월 스페셜, 화~일 일반'],['INTELLIGENCE',10,'주 3회 · 월·수·금 스페셜'],['SIGNATURE',10,'주 7회 · 월~일 스페셜']],
    'one-time': [['SNAPSHOT',1,'1회 · 일반 브리핑'],['DEEP DIVE',1,'1회 · 스페셜 브리핑']],
    enterprise: [['ENTERPRISE T100',100,'T100 범위·주기·언어 맞춤 설계']]
  };
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  $('discoveryField').textContent = `00 / ${state.field} BETA`;
  document.querySelectorAll('[data-field-link]').forEach((card) => card.classList.toggle('active', card.dataset.fieldLink === state.field));

  fetch('data/latest.json', { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('공개 데이터를 불러오지 못했습니다.'); return r.json(); }).then((data) => {
    state.entries = (data.rankings || []).filter((x) => x.domain === state.field && x.ranking_type === 'T100').sort((a,b) => a.rank-b.rank);
    if (state.entries.length < 3) throw new Error(`${state.field} T100에서 비교 가능한 대상이 충분하지 않습니다.`);
    buildSelects();
  }).catch((err) => { $('trioError').hidden = false; $('trioError').textContent = `${err.message} 잠시 후 다시 확인해 주세요.`; $('trioRun').disabled = true; });

  function buildSelects() {
    const preferred = state.field === 'ENT' ? ['리센느','아이브','르세라핌'] : [];
    const defaults = preferred.map((name) => state.entries.find((e) => e.name === name)).filter(Boolean);
    state.entries.forEach((entry) => { if (defaults.length < 3 && !defaults.includes(entry)) defaults.push(entry); });
    ['trioPick1','trioPick2','trioPick3'].forEach((id,i) => { const select=$(id); select.innerHTML=state.entries.map((e)=>`<option value="${esc(e.external_id)}">${e.rank}. ${esc(e.name)}${e.category?` · ${esc(e.category)}`:''}</option>`).join(''); select.value=defaults[i].external_id; });
  }
  $('discoveryLanguages').addEventListener('click', (event) => { const button=event.target.closest('button[data-language]'); if(!button)return; $('discoveryLanguages').querySelectorAll('button').forEach((b)=>b.classList.remove('active')); button.classList.add('active'); state.language=button.dataset.language; });
  $('trioRun').addEventListener('click', () => {
    const ids=['trioPick1','trioPick2','trioPick3'].map((id)=>$(id).value);
    if(new Set(ids).size!==3){$('trioError').hidden=false;$('trioError').textContent='서로 다른 세 대상을 선택해 주세요.';return;}
    $('trioError').hidden=true;
    const query=new URLSearchParams({field:state.field,pick:ids[0],compareA:ids[1],compareB:ids[2],language:state.language,trial:'free'});
    location.href=`briefing.html?${query.toString()}`;
  });

  function bindSingleChoice(id,key){$(id).addEventListener('click',(ev)=>{const b=ev.target.closest('button[data-value]');if(!b)return;$(id).querySelectorAll('button').forEach((x)=>x.classList.remove('active'));b.classList.add('active');state[key]=b.dataset.value;if(key==='mode'){state.pkg=packages[state.mode][0][0];renderPackages();}renderReview();});}
  bindSingleChoice('modeOptions','mode');bindSingleChoice('fieldOptions','field');bindSingleChoice('languageOptions','language');
  function currentPackage(){return packages[state.mode].find((p)=>p[0]===state.pkg)||packages[state.mode][0];}
  function renderPackages(){$('packageOptions').innerHTML=packages[state.mode].map((p)=>`<button type="button" data-value="${p[0]}" class="${p[0]===state.pkg?'active':''}"><b>BRIDGE ${p[0]}</b><span>${p[2]}</span></button>`).join('');renderTargetInputs();}
  $('packageOptions').addEventListener('click',(ev)=>{const b=ev.target.closest('button[data-value]');if(!b)return;state.pkg=b.dataset.value;renderPackages();renderReview();});
  function renderTargetInputs(){const max=currentPackage()[1],shown=max===100?1:max;$('targetLimit').textContent=max===100?'대상 범위 협의':`최대 ${max}개`;$('builderTargets').innerHTML=Array.from({length:shown},(_,i)=>`<input type="text" maxlength="50" placeholder="${i+1}. 대상명${i===0?' (필수)':''}" aria-label="분석 대상 ${i+1}">`).join('');$('builderTargets').addEventListener('input',renderReview);}
  function renderReview(){const p=currentPackage(),modeLabel=state.mode==='subscription'?'정기 관측':state.mode==='one-time'?'단건 분석':'맞춤 분석 문의';const targets=[...$('builderTargets').querySelectorAll('input')].map((i)=>i.value.trim()).filter(Boolean);$('reviewPackage').textContent=`BRIDGE ${p[0]}`;$('reviewMode').textContent=modeLabel;$('reviewField').textContent=state.field;$('reviewTargets').textContent=targets.length?targets.join(', '):'입력 대기';$('reviewLanguage').textContent=state.language;$('reviewDetail').textContent=p[2];const q=new URLSearchParams({plan:p[0],mode:state.mode==='one-time'?'once':state.mode,field:state.field,targets:targets.join(', '),language:state.language});$('intelContact').href=`subscribe.html?${q.toString()}`;}
  renderPackages();renderReview();
})();
