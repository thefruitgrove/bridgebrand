(function(){
'use strict';
const NAMES=['리센느','아이브','르세라핌'];
const AXES=['B','R','I','D','G','E'];
const AXIS_NAME={B:'도달',R:'반응',I:'정체성',D:'경험',G:'행동유발',E:'책임·지속'};
const COLORS=['#c69c3c','#71899e','#a9787e'];
const RANGE=['01–06','07–10','11–12','13–19','20','21'];
let stage=1, entities=[];
const $=(id)=>document.getElementById(id);
const num=(v,d=2)=>Number(v).toFixed(d);
const signed=(v)=>`${Number(v)>=0?'▲':'▼'} ${Math.abs(Number(v)).toFixed(2)}`;
const dateKo=(iso)=>{const [y,m,d]=String(iso).split('-').map(Number);return `${y}년 ${m}월 ${d}일`;};
const valid=(e,a)=>e&&e.axis_status&&e.axis_status[a]!=='reference'&&Number.isFinite(Number(e.axis_scores&&e.axis_scores[a]));

document.querySelectorAll('[data-stage], [data-go-stage]').forEach((button)=>button.addEventListener('click',()=>showStage(Number(button.dataset.stage||button.dataset.goStage))));
$('prevStage').addEventListener('click',()=>showStage(stage-1));
$('nextStage').addEventListener('click',()=>showStage(stage+1));

function showStage(next){
  if(next<1||next>6)return;
  stage=next;
  document.querySelectorAll('[data-stage-panel]').forEach((panel)=>{const on=Number(panel.dataset.stagePanel)===stage;panel.hidden=!on;panel.classList.toggle('active',on);});
  document.querySelectorAll('#journeyTrack [data-stage]').forEach((button)=>button.classList.toggle('active',Number(button.dataset.stage)===stage));
  $('progressText').textContent=`${String(stage).padStart(2,'0')} / 06 · ${document.querySelector(`#journeyTrack [data-stage="${stage}"] em`).textContent}`;
  $('progressBar').style.width=`${stage/6*100}%`;
  $('chapterRange').textContent=RANGE[stage-1];
  $('pagerLabel').textContent=`${String(stage).padStart(2,'0')} / 06`;
  $('prevStage').disabled=stage===1;
  $('nextStage').disabled=stage===6;
  $('prevStage').textContent=stage===1?'← 이전 단계':`← ${document.querySelector(`#journeyTrack [data-stage="${stage-1}"] span`).lastChild.textContent.trim()}`;
  $('nextStage').textContent=stage===6?'보고서 완료':`${document.querySelector(`#journeyTrack [data-stage="${stage+1}"] span`).lastChild.textContent.trim()} →`;
  document.querySelector('.journey-nav').scrollIntoView({behavior:'smooth',block:'start'});
}

fetch('data/latest.json',{cache:'no-store'}).then((r)=>{if(!r.ok)throw new Error('공개 데이터를 불러오지 못했습니다.');return r.json();}).then((data)=>{
  const all=(data.rankings||[]).filter((x)=>x.domain==='ENT'&&x.ranking_type==='T100');
  entities=NAMES.map((name)=>all.find((x)=>x.name===name)).filter(Boolean);
  if(entities.length!==3)throw new Error('동일 스냅샷의 세 대상 데이터가 완전하지 않습니다.');
  render();
}).catch((error)=>{
  $('coverStats').innerHTML=`<span>${error.message}</span>`;
});

function render(){
  const r=entities[0];
  $('coverStats').innerHTML=`<span>ENT T100 <strong>${r.rank}위</strong></span><span>DAILY <strong>${num(r.daily_index)}</strong></span><span>WEEKLY <strong>${num(r.weekly_index)}</strong></span><span>근거 신뢰등급 <strong>${r.trust_grade}</strong> · 평판등급 아님</span>`;
  const metrics=[
    ['BRIDGE DAILY INDEX',num(r.daily_index),'오늘의 관측 가능한 관계 평판 수준'],
    ['BRIDGE WEEKLY INDEX',num(r.weekly_index),'월요일부터 현재까지 일별지수의 근거 신뢰도 가중평균'],
    ['LAST WEEK INDEX',num(r.last_week_index),'직전 월~일 일별지수의 근거 신뢰도 가중평균'],
    ['WoW Δ',signed(r.wow_delta),'이번 주 대표지수와 직전 완료 주간 대표지수의 차이'],
    ['4-WEEK AVERAGE',num(r.four_week_average),'최근 최대 4개 주간 대표지수 평균'],
    ['ACTIVITY POINTS',`${Math.round(r.activity_points)}P`,'이번 주 검증·중복 제거된 사건 활동량'],
    ['CUMULATIVE ACTIVITY',`${Math.round(r.cumulative_activity)}P`,'운영 관측기간의 검증된 사건 활동량 누계'],
    ['STABILITY',r.stability==null?'N/R':num(r.stability),'완료 주간 이력이 부족하면 산출하지 않음']
  ];
  $('metricList').innerHTML=metrics.map((m)=>`<div class="metric-row"><b>${m[0]}</b><strong>${m[1]}</strong><span>${m[2]}</span></div>`).join('');
  $('positionRows').innerHTML=entities.map((e,i)=>`<tr><td>${e.name}${i===0?' · MY PICK':''}</td><td>${e.rank}위</td><td>${num(e.daily_index)}</td><td class="${Number(e.score_change)>=0?'delta-up':'delta-down'}">${signed(e.score_change)}</td><td>${num(e.weekly_index)}</td><td class="${Number(e.wow_delta)>=0?'delta-up':'delta-down'}">${signed(e.wow_delta)}</td></tr>`).join('');
  $('rankChangeCopy').textContent=`리센느는 전일 대비 ${Math.abs(Number(r.score_change)).toFixed(2)}점 ${Number(r.score_change)>=0?'상승':'하락'}했지만 순위는 ${r.previous_rank}위에서 ${r.rank}위로 ${r.rank_change>0?'상승':'변화'}했습니다.`;
  $('entitySummary').innerHTML=entities.map((e,i)=>{const top=topAxis(e),low=lowAxis(e);return `<article><small>${i===0?'MY PICK':`COMPARE ${i===1?'A':'B'}`}</small><h4>${e.name}</h4><strong>${num(e.daily_index)}</strong><p>ENT T100 ${e.rank}위 · 신뢰 ${e.trust_grade}<br>강한 축 ${top} · 낮은 축 ${low}</p></article>`;}).join('');
  renderBars(r,$('resceneBars'),COLORS[0]);
  $('compareBriefs').innerHTML=entities.slice(1).map((e,i)=>`<article><small>COMPARE ${i===0?'A':'B'}</small><h4>${e.name}</h4><strong>${num(e.daily_index)}</strong><p>${compareNarrative(e)}</p><div class="mini-axis">강한 축 ${topAxis(e)} · 낮은 축 ${lowAxis(e)}</div></article>`).join('');
  renderRadar();renderGaps();renderActivity();renderPublicity();
}
function topAxis(e){return AXES.filter((a)=>valid(e,a)).sort((a,b)=>Number(e.axis_scores[b])-Number(e.axis_scores[a]))[0]||'—';}
function lowAxis(e){return AXES.filter((a)=>valid(e,a)).sort((a,b)=>Number(e.axis_scores[a])-Number(e.axis_scores[b]))[0]||'—';}
function compareNarrative(e){
  if(e.name==='아이브')return `도달 ${num(e.axis_scores.B,1)}과 반응 ${num(e.axis_scores.R,1)}이 강하고 활동량은 ${Math.round(e.activity_points)}P로 세 대상 중 가장 큽니다. 높은 활동이 행동유발과 경험으로 전환되는지가 다음 질문입니다.`;
  return `반응 ${num(e.axis_scores.R,1)}과 책임·지속 ${num(e.axis_scores.E,1)}이 강합니다. 기존 관계의 지속 기반이 실제 경험과 새로운 행동으로 확장되는지가 다음 질문입니다.`;
}
function renderBars(e,target,color){target.innerHTML=AXES.map((a)=>`<div class="axis-bar"><span>${a} · ${AXIS_NAME[a]}</span><div class="axis-bar-track"><i style="width:${valid(e,a)?Number(e.axis_scores[a]):0}%;background:${color}"></i></div><strong>${valid(e,a)?num(e.axis_scores[a],1):'참조'}</strong></div>`).join('');}
function point(i,value,r,cx,cy){const angle=-Math.PI/2+i*Math.PI/3,rr=r*value/100;return[cx+Math.cos(angle)*rr,cy+Math.sin(angle)*rr];}
function renderRadar(){
  const svg=$('briefingRadar'),cx=260,cy=205,r=150;let h='';
  [20,40,60,80,100].forEach((level)=>{h+=`<polygon points="${AXES.map((_,i)=>point(i,level,r,cx,cy).join(',')).join(' ')}" fill="none" stroke="rgba(255,255,255,.14)"/>`;});
  AXES.forEach((a,i)=>{const end=point(i,100,r,cx,cy),label=point(i,117,r,cx,cy);h+=`<line x1="${cx}" y1="${cy}" x2="${end[0]}" y2="${end[1]}" stroke="rgba(255,255,255,.12)"/><text x="${label[0]}" y="${label[1]}" text-anchor="middle"><tspan font-weight="800">${a}</tspan><tspan x="${label[0]}" dy="15">${AXIS_NAME[a]}</tspan></text>`;});
  entities.forEach((e,n)=>{const pts=AXES.map((a,i)=>valid(e,a)?point(i,Number(e.axis_scores[a]),r,cx,cy):null);if(pts.every(Boolean))h+=`<polygon points="${pts.map((p)=>p.join(',')).join(' ')}" fill="${COLORS[n]}22" stroke="${COLORS[n]}" stroke-width="3"/>`;pts.forEach((p)=>{if(p)h+=`<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="${COLORS[n]}"/>`;});});svg.innerHTML=h;
}
function renderGaps(){const gaps=AXES.map((a)=>{const vals=entities.filter((e)=>valid(e,a)).map((e)=>({name:e.name,v:Number(e.axis_scores[a])})).sort((x,y)=>y.v-x.v);return vals.length<2?null:{a,g:vals[0].v-vals.at(-1).v,hi:vals[0],lo:vals.at(-1)};}).filter(Boolean).sort((x,y)=>y.g-x.g).slice(0,3);$('briefingGaps').innerHTML=gaps.map((x)=>`<div class="gap-card"><b>${x.a} · ${AXIS_NAME[x.a]}</b><strong>${num(x.g,1)}p 차이</strong><span>${x.hi.name} ${num(x.hi.v,1)} ↔ ${x.lo.name} ${num(x.lo.v,1)}</span></div>`).join('');}
function renderActivity(){const max=Math.max(...entities.map((e)=>Number(e.activity_points)||0));$('activityCompare').innerHTML=entities.map((e)=>`<div class="activity-row"><span>${e.name}</span><div class="activity-track"><i style="width:${max?Number(e.activity_points)/max*100:0}%"></i></div><strong>${Math.round(e.activity_points)}P</strong></div>`).join('');}
function renderPublicity(){
  const [r,i,l]=entities;
  $('publicityHeadline').textContent=`리센느 ${num(r.daily_index)}으로 비교 우위…아이브는 활동량, 르세라핌은 지속 기반에서 다른 강점`;
  $('publicityStandfirst').textContent=`${dateKo(r.as_of_date)} ENT T100에서 리센느는 강한 반응과 선명한 정체성을 바탕으로 세 대상 중 가장 높은 관계 평판 수준을 보였다.`;
  $('publicityBody').innerHTML=`<p>시그널브릿지 BRIDGE 브랜드평판지수 INDEX 관측에서 리센느는 당일 ${num(r.daily_index)}으로 ENT T100 ${r.rank}위를 기록했다. 비교 대상인 아이브는 ${num(i.daily_index)}, 르세라핌은 ${num(l.daily_index)}로 나타났다. 이번 결과는 같은 날짜와 공개자료 범위에서 세 대상의 상대적 관계 구조를 비교한 것이다.</p><p>리센느의 현재 위치를 만든 핵심은 반응과 정체성이다. 두 축은 각각 ${num(r.axis_scores.R,1)}과 ${num(r.axis_scores.I,1)}으로 나타났고 행동유발도 ${num(r.axis_scores.G,1)}로 뒤를 받쳤다. 공중의 관심이 단순 노출에서 끝나지 않고 특정 이미지와 후속 행동으로 연결되는 구조다.</p><p>다만 경험은 ${num(r.axis_scores.D,1)}, 책임·지속은 ${num(r.axis_scores.E,1)}으로 상대적으로 낮았다. 이를 부정적인 판정으로 해석해서는 안 된다. 현재의 빠른 관심과 정체성이 반복 경험과 장기 신뢰로 전환되는 과정은 후속 관측이 필요하다.</p><p>아이브는 도달 ${num(i.axis_scores.B,1)}과 반응 ${num(i.axis_scores.R,1)}이 강했고 주간 활동량은 ${Math.round(i.activity_points)}P로 세 대상 중 가장 많았다. 르세라핌은 반응 ${num(l.axis_scores.R,1)}과 책임·지속 ${num(l.axis_scores.E,1)}이 강했다. 세 대상은 같은 범주에 있지만 서로 다른 경로로 관계 평판을 형성하고 있다.</p><p>리센느의 현재 우위는 모든 가치와 능력에서 앞선다는 뜻이 아니다. BRIDGE가 다음에 확인할 질문은 분명하다. 지금의 선명한 기억이 실제 경험과 지속 가능한 신뢰로 이어질 수 있는가.</p>`;
}
showStage(1);
})();
