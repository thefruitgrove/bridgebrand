/* BRIDGEBRAND 2.0 public experience. Reads published JSON; never mutates the index. */
(function(){
 'use strict';
 const $=id=>document.getElementById(id);
 const input=$('v2SearchInput'),form=$('v2SearchForm'),results=$('v2SearchResults'),status=$('v2SearchStatus');
 const fieldLabels={CPR:'기업',GOV:'정부·지자체',UNI:'대학교',ENT:'광고모델·인물'};
 let entries=[],focused=null,asOfDate='';
 const menu=$('v2MenuToggle'),mobile=$('v2MobileMenu');
 menu.addEventListener('click',()=>{const next=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(next));menu.setAttribute('aria-label',next?'메뉴 닫기':'메뉴 열기');mobile.hidden=!next;});
 mobile.addEventListener('click',event=>{if(event.target.closest('a')){mobile.hidden=true;menu.setAttribute('aria-expanded','false');}});
 const collator=new Intl.Collator('ko');
 const normalized=value=>String(value||'').normalize('NFKC').toLocaleLowerCase('ko').replace(/\s+/g,'');
 function route(row){
   const q=new URLSearchParams({field:row.domain,pick:row.external_id});
   window.location.assign('intelligence.html?'+q.toString()+'#trioBeta');
 }
 function match(query){
   const q=normalized(query);
   if(!q)return [];
   return entries.filter(x=>normalized(x.name).includes(q)||normalized(x.external_id).includes(q)).slice(0,8);
 }
 function renderSuggestions(){
   const term=input.value.trim();const matches=match(term);
   results.replaceChildren();focused=null;
   if(!matches.length){
      results.hidden=true;input.setAttribute('aria-expanded','false');
      if(term)status.textContent=entries.length?'검색 결과가 없습니다. 이름을 다시 입력해 주세요.':'공개 데이터를 확인하는 중입니다.';
      return;
   }
   for(const row of matches){
     const button=document.createElement('button');button.type='button';button.setAttribute('role','option');button.setAttribute('aria-selected','false');
     const name=document.createElement('strong');name.textContent=row.name;
     const detail=document.createElement('span');detail.textContent=fieldLabels[row.domain]+' · '+row.rank+'위';
     button.append(name,detail);button.addEventListener('click',()=>route(row));results.append(button);
   }
   results.hidden=false;input.setAttribute('aria-expanded','true');status.textContent=matches.length+'개 검색 결과 · 항목을 선택하면 Intelligence로 이동합니다.';
 }
 input.addEventListener('input',renderSuggestions);
 input.addEventListener('keydown',event=>{
   if(event.key==='Escape'){results.hidden=true;input.setAttribute('aria-expanded','false');return;}
   if(event.key==='ArrowDown'&&!results.hidden){event.preventDefault();const first=results.querySelector('button');if(first)first.focus();}
 });
 results.addEventListener('keydown',event=>{if(event.key==='Escape'){results.hidden=true;input.focus();}if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();const buttons=[...results.querySelectorAll('button')];const i=buttons.indexOf(document.activeElement);const next=buttons[i+(event.key==='ArrowDown'?1:-1)];if(next)next.focus();else input.focus();}});
 document.addEventListener('pointerdown',event=>{if(!form.contains(event.target)){results.hidden=true;input.setAttribute('aria-expanded','false');}});
 form.addEventListener('submit',event=>{
   event.preventDefault();
   if(!entries.length){status.textContent='공개 자료를 아직 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.';return;}
   const query=normalized(input.value);
   const exact=entries.find(x=>normalized(x.name)===query||normalized(x.external_id)===query);
   if(exact){route(exact);return;}
   const matches=match(query);
   if(matches.length===1){route(matches[0]);return;}
   renderSuggestions();if(matches.length>1)status.textContent='여러 대상이 검색됐습니다. 정확한 대상을 하나 선택해 주세요.';
 });
 const cards=$('v2SignalCards');
 function card(label,title,body,href,lead){
    const art=document.createElement('article');art.className='v2-feature'+(lead?' v2-feature-lead':'');
    const kicker=document.createElement('p');kicker.className='v2-feature-label';kicker.textContent=label;
    const heading=document.createElement('h3');heading.textContent=title;
    const description=document.createElement('p');description.textContent=body;
    const link=document.createElement('a');link.href=href;link.className='v2-feature-link';link.textContent='지수 자세히 보기 ↗';
    art.append(kicker,heading,description,link);return art;
 }
 async function start(){
   try{
      const response=await fetch('data/latest.json',{cache:'no-store'});
      if(!response.ok)throw new Error('HTTP '+response.status);
      const data=await response.json();
      if(data.dataStatus!=='published'||data.recordCount!==400||!Array.isArray(data.rankings)||data.rankings.length!==400)throw new Error('Incomplete published snapshot');
      if(!/^\d{4}-\d{2}-\d{2}$/.test(data.asOfDate||''))throw new Error('Invalid publication date');
      const ids=new Set(data.rankings.map(x=>x.domain+'|'+x.external_id));
      if(ids.size!==400)throw new Error('Duplicate subject in published rankings');
      asOfDate=data.asOfDate;
      entries=data.rankings.filter(x=>['CPR','GOV','UNI','ENT'].includes(x.domain)&&x.ranking_type==='T100'&&x.name&&x.external_id).sort((a,b)=>collator.compare(a.name,b.name));
      if(entries.length!==400)throw new Error('Incomplete field coverage');
      $('v2DataDate').textContent=asOfDate+' 기준 · 400개 공개 평가 대상';
      status.textContent=asOfDate+' 기준 · 400개 평가 대상 검색 가능';
      const movers=entries.filter(x=>typeof x.score_change==='number'&&Number.isFinite(x.score_change)&&x.score_change!==0).sort((a,b)=>Math.abs(b.score_change)-Math.abs(a.score_change));
      const mover=movers[0];
      const desc=mover?fieldLabels[mover.domain]+' · '+(mover.score_change>0?'+':'')+mover.score_change.toFixed(2)+'점 변화 · 순위와 점수 변화는 같은 의미가 아닙니다.':'실제 공개 지수의 변화와 관측범위를 확인합니다.';
      const fieldTop=entries.filter(x=>x.domain==='CPR').sort((a,b)=>a.rank-b.rank)[0];
      const featureA=card('THE MOVEMENT / '+asOfDate,mover?mover.name+'의 평판지수 변화':'이번 주 평가 흐름',desc,mover?({CPR:'cpr',GOV:'gov',UNI:'uni',ENT:'star'}[mover.domain]+'.html'):'this-week.html',true);
      const featureB=card('BRIDGE INDEX / PUBLIC DATA',fieldTop?'기업 분야 '+fieldTop.rank+'위 · '+fieldTop.name:'네 분야의 현재 위치','네 분야는 각각의 평가대상군 안에서 비교합니다. 분야 간 점수의 직접적인 우열 비교는 하지 않습니다.','cpr.html',false);
      cards.replaceChildren(featureA,featureB);
   }catch(err){
      console.warn('BRIDGE 2.0 live-data readiness:',err);
      $('v2DataDate').textContent='공개 지수 확인이 필요합니다';
      status.textContent='현재 실시간 목록 연결을 확인할 수 없습니다. 분야별 지수 페이지를 이용해 주세요.';
      cards.replaceChildren(
       card('THE MOVEMENT','이번 주 평가 흐름','데이터 연결을 확인 중입니다. 실제 점수와 순위는 공개 지수에서 확인해 주세요.','this-week.html',true),
       card('BRIDGE INDEX','네 분야의 평판','기업·정부·대학·인물의 공개 평가를 확인할 수 있습니다.','cpr.html',false)
      );
   }
 }
 start();
})();