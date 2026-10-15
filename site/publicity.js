(function(){
'use strict';
var cfg=window.BRIDGE_PUBLICITY_CONFIG||{},articles=[],fallback=false;
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function day(d){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(d);}
function week(d){var x=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate()));x.setUTCDate(x.getUTCDate()+3-(x.getUTCDay()+6)%7);var y=x.getUTCFullYear(),f=new Date(Date.UTC(y,0,4));return y+'-W'+String(1+Math.round((x-f)/604800000)).padStart(2,'0');}
function monday(w){var p=w.split('-W'),d=new Date(Date.UTC(Number(p[0]),0,4));d.setUTCDate(d.getUTCDate()-(d.getUTCDay()+6)%7+(Number(p[1])-1)*7);return d;}
function label(a){return 'WEEK '+Number(a.issue_week.split('W')[1])+' — '+(a.slot==='OVERALL'?'OVERALL ANALYSIS':a.slot+' '+a.domain)+' PUBLICITY';}
function dateText(value){return new Date(value).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',month:'long',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false});}
function issueList(){
  var now=new Date(),kst=new Date(day(now)+'T00:00:00Z');if(kst.getUTCDay()===1)kst.setUTCDate(kst.getUTCDate()-1);
  var weeks=Array.from(new Set(articles.map(function(a){return a.issue_week;}).concat([week(kst)]))).sort().reverse();
  document.getElementById('pubIssues').innerHTML=weeks.map(function(w){
    var start=monday(w),slots=[];['WED','FRI'].forEach(function(s){['CPR','GOV','UNI','ENT'].forEach(function(d){slots.push({slot:s,domain:d});});});slots.push({slot:'OVERALL',domain:'ALL'});
    return '<section class="pub-issue"><div class="pub-week"><h3>WEEK '+Number(w.split('W')[1])+'</h3><span>'+w.split('-')[0]+' · 9 EDITIONS</span></div>'+slots.map(function(s,i){
      var a=articles.find(function(x){return x.issue_week===w&&x.slot===s.slot&&x.domain===s.domain&&!x.is_example;})||articles.find(function(x){return x.issue_week===w&&x.slot===s.slot&&x.domain===s.domain&&x.is_example;});
      var release=new Date(start);release.setUTCDate(start.getUTCDate()+(s.slot==='WED'?2:s.slot==='FRI'?4:7));var due=release.toISOString().slice(0,10)+'T12:00:00+09:00';
      var placeholder=new Date(due)<new Date('2026-10-16T00:00:00+09:00')?'정식 발행 전 회차':new Date(due)>now?'발행 예정':'발행 확인 중';
      var identity={issue_week:w,slot:s.slot,domain:s.domain};
      return '<'+(a?'a href="publicity-article.html?id='+encodeURIComponent(a.id)+'"':'div')+' class="pub-row'+(a?'':' pending')+'"><span class="pub-no">'+String(i+1).padStart(2,'0')+'</span><div><span class="pub-row-label">'+esc(label(identity))+'</span><span class="pub-row-title">'+esc(a?a.payload.title:placeholder)+(a&&a.is_example?'<span class="pub-example">SAMPLE</span>':'')+'</span></div><div class="pub-row-meta">'+esc(a&&a.is_example?'10월 14일 자료 · 예시':dateText(a?a.scheduled_at:due))+'<br>'+(a?'READ THE SIGNAL →':'SEOUL · KST')+'</div></'+(a?'a':'div')+'>';
    }).join('')+'</section>';
  }).join('');
}
function radar(profile){
 var names=['B','R','I','D','G','E'],angles=names.map(function(_,i){return (-90+i*60)*Math.PI/180;}),cx=135,cy=130,r=88;
 function points(vals){return vals.map(function(v,i){return [cx+Math.cos(angles[i])*r*v/100,cy+Math.sin(angles[i])*r*v/100];});}
 var pts=points(names.map(function(a){return Number(profile.axes[a])||0;}));
 var svg=[33,66,100].map(function(v){return '<polygon points="'+points(names.map(function(){return v;})).map(function(p){return p.join(',');}).join(' ')+'" fill="none" stroke="#d6d0c0"/>';}).join('');
 svg+='<polygon points="'+pts.map(function(p){return p.join(',');}).join(' ')+'" fill="#ad8d551b" stroke="none"/>';
 pts.forEach(function(p,i){var n=(i+1)%6,ref=profile.states[names[i]]==='reference'||profile.states[names[n]]==='reference';svg+='<line x1="'+p[0]+'" y1="'+p[1]+'" x2="'+pts[n][0]+'" y2="'+pts[n][1]+'" stroke="'+(ref?'#a2a4a0':'#a0824a')+'" stroke-width="2"'+(ref?' stroke-dasharray="4,4"':'')+'/>';});
 names.forEach(function(a,i){svg+='<text x="'+(cx+Math.cos(angles[i])*(r+20))+'" y="'+(cy+Math.sin(angles[i])*(r+20))+'" text-anchor="middle" dominant-baseline="middle" font-size="10" fill="#6e6b61">'+a+' '+esc(profile.axes[a])+'</text>';});
 return '<div class="pub-profile"><b>'+esc(profile.name)+'</b><svg viewBox="0 0 270 260" role="img" aria-label="'+esc(profile.name)+' 여섯 축 프로필">'+svg+'</svg><p>실선: 관측·유지 / 점선: 참조<br>참조값은 대상 평가가 아닙니다.</p></div>';
}
function renderArticle(id){
 var a=articles.find(function(x){return x.id===id;});document.getElementById('pubBoard').hidden=true;document.getElementById('pubArticle').hidden=false;
 var node=document.getElementById('pubArticleContent');
 if(!a){node.innerHTML='<h2>아직 공개되지 않은 분석입니다.</h2><p>예약 시각 이전이거나 공개 상태를 확인할 수 없습니다. 잠시 후 다시 확인해 주세요.</p>';return;}
 var p=a.payload;document.title=p.title+' | BRIDGE PUBLICITY';
 document.getElementById('pubIntro').textContent='순위 너머의 관계, 근거 위의 해석.';
 var table=p.table||[],overall=a.domain==='ALL';
 var th=overall?['영역','공개 대상','관측일 수']:['일별 순위','대상','Daily','Weekly*','당주 활동 P','신뢰'];
 var rows=table.map(function(r){return '<tr>'+(overall?[r.domain,r.eligible,r.observation_days]:[r.rank,r.name,r.daily,r.weekly,r.activity,r.trust]).map(function(v){return '<td>'+esc(v==null?'—':v)+'</td>';}).join('')+'</tr>';}).join('');
 node.innerHTML='<div class="pub-article-label">'+esc(label(a))+(a.is_example?' · SAMPLE':'')+'</div><h2>'+esc(p.title)+'</h2><p class="pub-deck">'+esc(p.standfirst)+'</p><div class="pub-byline">시그널브릿지 · BRIDGE PUBLICITY<br>분석 대상: '+esc(p.data_from)+' — '+esc(p.data_through)+' · '+esc(p.methodology_version)+'<br>'+(a.is_example?'예시 게시: ':'공개 기준: ')+esc(dateText(a.scheduled_at))+' KST'+(new Date(a.prepared_at).getTime()>new Date(a.scheduled_at).getTime()+60000&&!a.is_example?' · 준비 완료 후 지연 공개':'')+'</div>'+
 (p.revision_note?'<p class="pub-data-caption">'+esc(p.revision_note)+'</p>':'')+'<div class="pub-table-wrap"><table class="pub-table"><thead><tr>'+th.map(function(t){return '<th scope="col">'+t+'</th>';}).join('')+'</tr></thead><tbody>'+rows+'</tbody></table></div><p class="pub-data-caption">'+(overall?'영역별 집계이며 분야 사이의 점수 우열 비교가 아닙니다.':'* Weekly는 자료 마감일까지의 잠정 주간 수준입니다. 표의 순위는 Daily 기준이며, 활동 P는 당주 총량입니다.')+'</p>'+
 '<div class="pub-profiles">'+(p.profiles||[]).map(radar).join('')+'</div>'+
 (p.sections||[]).map(function(s){return '<section><h3>'+esc(s.heading)+'</h3>'+s.paragraphs.map(function(t){return '<p>'+esc(t)+'</p>';}).join('')+'</section>';}).join('')+
 '<aside class="pub-limit"><p><b>이 분석을 읽는 기준</b></p><ul>'+(p.limitations||[]).map(function(x){return '<li>'+esc(x)+'</li>';}).join('')+'</ul><p>작성 시점의 입력본을 고정해 보관합니다. 이후 점수 갱신이 이 기사의 수치를 바꾸지 않습니다.<br>입력 식별: '+esc(a.snapshot_hash.slice(0,16))+'</p></aside><div class="pub-share"><button id="pubCopy" type="button">기사 주소 복사</button><span id="pubCopyStatus" role="status"></span></div>';
 document.getElementById('pubCopy').onclick=function(){navigator.clipboard.writeText(location.href).then(function(){document.getElementById('pubCopyStatus').textContent='복사했습니다.';}).catch(function(){document.getElementById('pubCopyStatus').textContent='주소창의 링크를 복사해 주세요.';});};
}
function render(){var id=new URLSearchParams(location.search).get('id');if(id)renderArticle(id);else issueList();document.getElementById('pubStatus').textContent=fallback?'연결 지연으로 예시만 표시합니다. 정식 발행 상태는 다시 확인해 주세요.':'매주 수·금 영역별 4편 · 다음 주 월요일 종합 1편. 예약 기사는 공개 시각 이후에 열립니다.';}
function load(){var headers={apikey:cfg.key};if(cfg.key&&cfg.key.indexOf('eyJ')===0)headers.Authorization='Bearer '+cfg.key;
 return fetch(cfg.url+'/rest/v1/bridge_publicity_articles?select=id,issue_week,slot,domain,scheduled_at,is_example,payload,snapshot_hash,prepared_at&order=scheduled_at.desc&limit=240',{headers:headers,cache:'no-store'}).then(function(r){if(!r.ok)throw new Error('publicity unavailable');return r.json();}).then(function(rows){if(!Array.isArray(rows))throw new Error('invalid response');articles=rows;fallback=false;render();}).catch(function(){return fetch('data/publicity-example.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw new Error('example unavailable');return r.json();}).then(function(data){articles=data.articles||[];fallback=true;render();}).catch(function(){document.getElementById('pubStatus').textContent='분석 기사 연결을 확인하지 못했습니다. 잠시 후 다시 확인해 주세요.';});});}
load();setInterval(function(){if(!document.hidden)load();},60000);
})();
