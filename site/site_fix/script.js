(function(){
  // Apply the approved wordmark without changing the dimensions or alignment
  // of any existing SIGNALBRIDGE logo slot.
  (function installSignalBridgeWordmarks(){
    Array.prototype.forEach.call(document.querySelectorAll('.logo'), function(slot){
      if(slot.dataset.brandWordmark === '1' || slot.textContent.trim() !== 'SIGNALBRIDGE') return;
      var box=slot.getBoundingClientRect();
      if(!box.width || !box.height) return;
      slot.style.setProperty('--brand-slot-width', box.width.toFixed(2)+'px');
      slot.style.setProperty('--brand-slot-height', box.height.toFixed(2)+'px');
      slot.classList.add('brand-logo-slot');
      slot.dataset.brandWordmark='1';
      slot.textContent='';
      var img=document.createElement('img');
      img.className='brand-wordmark-image';
      img.src='assets/signalbridge-wordmark.svg?v=20261018-1';
      img.alt='SIGNALBRIDGE';
      slot.appendChild(img);
    });
  })();

  // PUBLICITY is a primary mobile destination: THIS WEEK → PUBLICITY → CPR.
  (function normalizeMobilePublicity(){
    var menu=document.getElementById('mobileMenu');
    if(!menu) return;
    Array.prototype.forEach.call(menu.querySelectorAll('a.mm-util'), function(link){
      if(link.textContent.trim()==='PUBLICITY') link.remove();
    });
    var groups=Array.prototype.slice.call(menu.querySelectorAll('.mm-group'));
    var hasPrimary=groups.some(function(group){
      var first=group.querySelector('a');
      return first && first.textContent.trim()==='PUBLICITY';
    });
    if(hasPrimary) return;
    var thisWeek=groups.find(function(group){
      var first=group.querySelector('a');
      return first && first.textContent.trim()==='THIS WEEK';
    });
    if(!thisWeek) return;
    var group=document.createElement('div');
    group.className='mm-group';
    group.innerHTML='<a href="publicity.html">PUBLICITY</a>';
    thisWeek.insertAdjacentElement('afterend', group);
  })();

  function scopeMessage(status){
    return {baseline_pending:'새 기준의 비교 자료 축적 중',scope_expanded:'근거 범위 확대 · 변화 해석 주의',scope_reduced:'근거 범위 축소 · 비교 제한',scope_changed:'근거 구성 변경 · 비교 제한',methodology_changed:'산출 기준 변경 · 직접 비교 제한',legacy_unverified:'이전 기준 · 비교 검토 필요'}[status] || '비교 조건 확인 필요';
  }
  function snapshotDiagnosis(rec){
    if(rec.comparison_status !== 'same_scope') return scopeMessage(rec.comparison_status);
    if(rec.last_week_index == null || rec.weekly_index == null) return '평판 관측 · 비교 데이터 축적 중';
    return Number(rec.weekly_index)>Number(rec.last_week_index)?'최근 평판 수준이 전주를 웃돕니다.':Number(rec.weekly_index)<Number(rec.last_week_index)?'최근 평판 수준이 전주를 밑돕니다.':'전주 평판 수준을 유지하고 있습니다.';
  }
  function selectModalCase(name, region, snapshotDate){
    var domain=region==='STAR'?'ENT':region;
    if(snapshotDate) return (window.BRIDGE_DATED_CASES||{})[domain+'|'+name+'|'+snapshotDate] || null;
    return (window.BRIDGE_LIVE_CASES||{})[domain+'|'+name] || (window.BRIDGE_PILOT_CASES||{})[name];
  }
  // Load the current presentation layer explicitly. This also prevents a
  // long-lived edge/browser cache from keeping the former two-column board.
  (function refreshPresentationLayer(){
    var fresh=document.createElement('link');
    fresh.rel='stylesheet';
    fresh.href='style.css?v=20261018-brand2';
    document.head.appendChild(fresh);
  })();
  // The masthead is a Seoul service clock, not a stale build timestamp.
  // Data recency remains separately disclosed by each snapshot's asOfDate.
  (function updateSeoulMasthead(){
    var el=document.getElementById('heroSeoulClock');
    if(!el) return;
    var parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
    var p={}; parts.forEach(function(x){p[x.type]=x.value;});
    var y=Number(p.year), m=Number(p.month), d=Number(p.day);
    var utc=new Date(Date.UTC(y,m-1,d));
    var day=(utc.getUTCDay()+6)%7;
    utc.setUTCDate(utc.getUTCDate()-day+3);
    var firstThu=new Date(Date.UTC(utc.getUTCFullYear(),0,4));
    var week=1+Math.round((utc-firstThu)/604800000);
    var months=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    el.innerHTML='<span>VOL. 02 — WEEK '+week+'</span><span>SEOUL · '+String(d).padStart(2,'0')+' '+months[m-1]+' '+y+'</span>';
  })();
  // Published Supabase snapshot. A valid daily snapshot rebuilds the public
  // T100 list in score/rank order; static HTML is fallback only.
  (function loadBridgeDailySnapshot(){
    var page = (location.pathname.split('/').pop() || 'index').toLowerCase().replace(/\.html$/, '');
    var domain = page === 'cpr' ? 'CPR' : page === 'gov' ? 'GOV' :
      page === 'uni' ? 'UNI' : page === 'star' ? 'ENT' : null;
    fetch('data/latest.json', {cache:'no-store'}).then(function(res){
      if(!res.ok) throw new Error('snapshot unavailable');
      return res.json();
    }).then(function(payload){
      if(payload.dataStatus!=='published'||!Array.isArray(payload.rankings)||!payload.rankings.length) throw new Error('invalid published snapshot');
      var snapshotKeys={};
      payload.rankings.forEach(function(rec){
        var key=rec.domain+'|'+rec.ranking_type+'|'+rec.external_id;
        if(snapshotKeys[key]||rec.score==null||!Number.isFinite(Number(rec.score))||Number(rec.score)<0||Number(rec.score)>100||rec.as_of_date!==payload.asOfDate) throw new Error('inconsistent snapshot');
        snapshotKeys[key]=true;
      });
      var rows = (payload.rankings || []).filter(function(r){ return r.ranking_type === 'T100'; });
      rows.sort(function(a,b){ return Number(a.rank)-Number(b.rank) || Number(b.score)-Number(a.score); });
      function esc(v){ var d=document.createElement('div'); d.textContent=String(v==null?'':v); return d.innerHTML; }
      function change(rec){
        if(rec.previous_rank==null) return '<span class="wow wow-flat">비교대기</span>';
        var d=Number(rec.rank_change||0), cls=d>0?'wow-up':d<0?'wow-down':'wow-flat';
        return '<span class="wow '+cls+'">'+(d>0?'▲ '+d:d<0?'▼ '+Math.abs(d):'— 0')+'</span>';
      }
      function rankRow(rec, snapshotDate){
        var n=Number(rec.rank), top=n<=3?' top3':'';
        var displayedDate=snapshotDate||rec.as_of_date||payload.asOfDate||'';
        return '<div class="rk-row rk-clickable live-row'+top+'" data-entity="'+esc(rec.name)+'" data-region="'+esc(rec.domain)+'" data-type="T100" data-live-date="'+esc(displayedDate)+'" tabindex="0" role="button">'+
          '<div class="rk-num">'+String(n).padStart(2,'0')+'</div>'+
          '<div class="rk-name"><div class="nm">'+esc(rec.name)+'</div><div class="sub">'+esc(rec.external_id)+' · '+esc(rec.category||'')+' · '+esc(rec.subcategory||'T100')+'</div></div>'+
          '<div class="rk-market">'+esc(rec.subcategory||rec.domain)+'</div><div class="rk-diagnosis">'+esc(snapshotDiagnosis(rec))+'</div>'+
          '<div class="rk-dims"><span class="dm">공개 관측 · '+esc(displayedDate)+'</span></div>'+
          '<div class="rk-score">'+Number(rec.score).toFixed(1)+'</div>'+
          '<div class="rk-wow">'+change(rec)+'</div>'+
          '<div class="rk-trust"><span class="trust-badge grade-'+esc(rec.trust_grade)+'">'+esc(rec.trust_grade)+'</span></div></div>';
      }
      function renderDomainRows(domainRows, snapshotDate){
        if(!domain) return;
        domainRows.sort(function(a,b){return Number(a.rank)-Number(b.rank)||Number(b.score)-Number(a.score);});
        domainRows.forEach(function(rec){
          var selectedCase = {
            dims:rec.axis_scores||{B:null,R:null,I:null,D:null,G:null,E:null}, score:rec.score,
            axis_status:rec.axis_status,axis_evidence_dates:rec.axis_evidence_dates,
            observed_days:rec.observed_days,collection_ok_days:rec.collection_ok_days,
            reference_axes_count:rec.reference_axes_count,comparison_status:rec.comparison_status,
            weekly_axis_states:rec.weekly_axis_states,weekly_axis_coverage:rec.weekly_axis_coverage,
            weekly_collection_complete:rec.weekly_collection_complete,
            weekly_reference_axes:rec.weekly_reference_axes,weekly_failed_axes:rec.weekly_failed_axes,
            daily_index:rec.daily_index, weekly_index:rec.weekly_index,
            activity_points:rec.activity_points, cumulative_performance:rec.cumulative_performance,
            four_week_average:rec.four_week_average, cumulative_activity:rec.cumulative_activity,
            observed_weeks:rec.observed_weeks, stability:rec.stability,
            v3_score:rec.weighted_index, trust:rec.trust_grade, method:'live',
            snapshot_date:snapshotDate||rec.as_of_date, last_week_index:rec.last_week_index, wow_delta:rec.wow_delta,
            history:rec.last_week_index==null?[]:[{score:rec.last_week_index}]
          };
          window.BRIDGE_PILOT_CASES[rec.name]=selectedCase;
          window.BRIDGE_DATED_CASES=window.BRIDGE_DATED_CASES||{};
          window.BRIDGE_DATED_CASES[domain+'|'+rec.name+'|'+selectedCase.snapshot_date]=selectedCase;
        });
        var prefix=domain==='ENT'?'star':domain.toLowerCase(), panel=document.getElementById(prefix+'-t100');
        if(panel){ panel.innerHTML=domainRows.map(function(rec){return rankRow(rec,snapshotDate);}).join(''); panel.setAttribute('data-shown','1000'); }
        var btn=document.querySelector('.seg-btn[data-target="'+prefix+'-t100"] span');
        if(btn) btn.textContent=domainRows.length+'/100';
        var note=document.querySelector('.live-snapshot-note');
        if(!note && panel){ note=document.createElement('div'); note.className='live-snapshot-note'; panel.parentNode.insertBefore(note,panel); }
        if(note) note.textContent='공개 적격 '+domainRows.length+' / 100 · '+(snapshotDate||'')+' · 공개적격 전 대상 표시';

        // The left rail is the always-visible T100. Cohort panels on the
        // right are independently re-ranked from the same live snapshot.
        var cohortMap={
          CPR:[['bc50',['BC50','BC70']],['bb50',['BB50','BB30']]],
          GOV:[['m40','GM40'],['c60','GC60']],
          UNI:[['u60','U60'],['c40','C40']],
          ENT:[['am45','AM40'],['aw45','AW40'],['an10','AN20']]
        };
        (cohortMap[domain]||[]).forEach(function(pair){
          var target=document.getElementById(prefix+'-'+pair[0]); if(!target)return;
          var cohortCodes=Array.isArray(pair[1])?pair[1]:[pair[1]];
          var subset=domainRows.filter(function(r){return cohortCodes.indexOf(String(r.subcategory||'').toUpperCase())>=0;});
          subset.sort(function(a,b){return Number(b.score)-Number(a.score)||String(a.name).localeCompare(String(b.name),'ko');});
          subset=subset.map(function(r,i){var copy=Object.assign({},r);copy.rank=i+1;copy.previous_rank=null;copy.rank_change=null;return copy;});
          target.innerHTML=subset.map(function(r){return rankRow(r,snapshotDate);}).join('');
          target.classList.remove('hidden');
        });
      }
      window.BRIDGE_LIVE_CASES=window.BRIDGE_LIVE_CASES||{};
      rows.forEach(function(rec){
        window.BRIDGE_LIVE_CASES[rec.domain+'|'+rec.name]={
          dims:rec.axis_scores||{},axis_status:rec.axis_status||{},axis_evidence_dates:rec.axis_evidence_dates||{},
          score:rec.score,daily_index:rec.daily_index,weekly_index:rec.weekly_index,
          activity_points:rec.activity_points,cumulative_performance:rec.cumulative_performance,
          four_week_average:rec.four_week_average,cumulative_activity:rec.cumulative_activity,
          observed_weeks:rec.observed_weeks,observed_days:rec.observed_days,collection_ok_days:rec.collection_ok_days,
          reference_axes_count:rec.reference_axes_count,comparison_status:rec.comparison_status,
          stability:rec.stability,v3_score:rec.weighted_index,trust:rec.trust_grade,method:'live',
          history:rec.last_week_index==null?[]:[{score:rec.last_week_index}]
        };
      });
      if(domain){
        var live=rows.filter(function(r){return r.domain===domain;});
        window.BRIDGE_PILOT_CASES = window.BRIDGE_PILOT_CASES || {};
        renderDomainRows(live,payload.asOfDate||'');
        window.BRIDGE_RENDER_PERIOD=function(start,end){
          if(!window.BRIDGE_HISTORY) return null;
          var archive=(window.BRIDGE_HISTORY&&window.BRIDGE_HISTORY.rankings)||[];
          var candidates=archive.filter(function(r){return r.domain===domain&&r.as_of_date>=start&&r.as_of_date<=end;});
          if(!candidates.length){ renderDomainRows([],start+' ~ '+end); return false; }
          var latestDate=candidates.reduce(function(a,r){return r.as_of_date>a?r.as_of_date:a;},'');
          renderDomainRows(candidates.filter(function(r){return r.as_of_date===latestDate;}),latestDate);
          return true;
        };
        fetch('data/history.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw new Error('archive unavailable');return r.json();}).then(function(h){window.BRIDGE_HISTORY=h;}).catch(function(){});
      }
      // Without a valid weekly baseline, show actual evidence, never a fabricated delta.
      function tickerEvidence(r){
        var states=r.axis_status||{},scores=r.axis_scores||{};
        var axes=Object.keys(states).filter(function(a){return (states[a]==='observed'||states[a]==='maintained')&&typeof scores[a]==='number'&&Number.isFinite(scores[a]);});
        axes.sort(function(a,b){return scores[b]-scores[a]||a.localeCompare(b);});
        return axes.length?esc(axes[0])+' '+scores[axes[0]].toFixed(1)+' · 유효 '+axes.length+'축':'활동 '+Number(r.activity_points||0).toFixed(1)+'P';
      }
      // 주식시황형 LIVE 바: CPR 1~10, ENT 1~10, GOV 1~10,
      // CPR 11~20, ENT 11~20, GOV 11~20. 각 영역 50위까지만 사용한다.
      var track=document.getElementById('tickerTrack');
      if(track){
        function take(d,a,b){return rows.filter(function(r){return r.domain===d&&Number(r.rank)>=a&&Number(r.rank)<=b&&Number(r.rank)<=50;});}
        var seq=[];
        for(var start=1;start<=50;start+=10){seq=seq.concat(take('CPR',start,start+9),take('ENT',start,start+9),take('GOV',start,start+9));}
        var html=seq.map(function(r){var valid=r.comparison_status==='same_scope'&&r.last_week_index!=null&&r.wow_delta!=null,d=valid?Number(r.wow_delta):null;return '<span><b>'+esc(r.domain)+'</b>'+esc(r.name)+' <span class="t-score">'+Number(r.score).toFixed(1)+'</span> <i class="'+(d>0?'t-up':d<0?'t-down':'t-flat')+'">'+(d===null?tickerEvidence(r):'주간 '+(d>0?'+':'')+d.toFixed(1))+'</i></span>';}).join('');
        track.innerHTML=html+html;
      }
      // HOME hero TOP 5: the original markup is only a no-JS fallback.
      // Replace all four cards from the same published snapshot used by the
      // ticker and ranking pages so the landing page can never show stale data.
      var heroTop=document.querySelector('.hero-top5');
      if(heroTop){
        var heroLinks={CPR:'cpr.html',GOV:'gov.html',UNI:'uni.html',ENT:'star.html'};
        heroTop.innerHTML=['CPR','GOV','UNI','ENT'].map(function(d){
          var top=rows.filter(function(r){return r.domain===d;}).slice(0,5);
          var items=top.length ? top.map(function(r){
            var delta=Number(r.rank_change||0);
            var deltaClass=delta>0?'t5-up':delta<0?'t5-down':'t5-flat';
            var deltaText=r.previous_rank==null?'비교대기':delta>0?'▲ '+delta:delta<0?'▼ '+Math.abs(delta):'— 0';
            return '<li><span class="t5-nm">'+esc(r.name)+'</span><span class="t5-sc">'+Number(r.score).toFixed(1)+'</span><span class="'+deltaClass+'">'+deltaText+'</span></li>';
          }).join('') : '<li class="t5-empty">오늘 공개 기준 충족 대상 없음</li>';
          return '<a class="t5-block" href="'+heroLinks[d]+'"><div class="t5-head">'+d+' <span class="t5-more">TOP 5 →</span></div><ol class="t5-list">'+items+'</ol></a>';
        }).join('');
        heroTop.setAttribute('data-live-date',payload.asOfDate||'');
      }
      // THIS WEEK의 네 영역 TOP 20도 같은 스냅샷으로 교체한다.
      var weekNote=document.querySelector('.tw-latest');
      if(weekNote)weekNote.textContent=(payload.asOfDate||'')+' 기준 · 영역별 일별 순위 TOP 20';
      document.querySelectorAll('.twr-col').forEach(function(col){
        var h=col.querySelector('.twr-head'), list=col.querySelector('.twr-list'); if(!h||!list)return;
        var d=(h.textContent.trim().match(/^(CPR|GOV|UNI|ENT)/)||[])[1]; if(!d)return;
        var live=rows.filter(function(r){return r.domain===d;}).slice(0,20);
        list.innerHTML=live.map(function(r){
          var delta=Number(r.rank_change||0), cls=delta>0?'twr-up':delta<0?'twr-down':'twr-flat';
          var deltaText=r.previous_rank==null?'비교대기':delta>0?'▲'+delta:delta<0?'▼'+Math.abs(delta):'—';
          var tags=snapshotDiagnosis(r);
          return '<li class="twr-item '+(Number(r.rank)<=3?'twr-top3':'')+'"><span class="twr-rank">'+r.rank+'</span><span class="twr-name"><b>'+esc(r.name)+'</b><small>'+esc(tags||'현재 평판 수준 관측')+'</small></span><span class="twr-score">'+Number(r.score).toFixed(1)+'<i class="'+cls+'">'+deltaText+'</i></span></li>';
        }).join('');
      });
    }).catch(function(){
      // Never replace the last deployed snapshot with zeroes after a failed run.
      var notice=document.createElement('div');
      notice.className='live-snapshot-note';
      notice.setAttribute('role','status');
      notice.textContent='최신 공개 데이터 연결을 확인하지 못했습니다. 현재 표시는 배포 시 저장된 자료이며 최신 결과와 다를 수 있습니다.';
      var main=document.querySelector('main')||document.body;
      main.insertBefore(notice,main.firstChild);
    });
  })();

  // ---- LIVE ticker: pause on hover, and a manual play/pause button ----
  var track = document.getElementById('tickerTrack');
  var toggleBtn = document.getElementById('tickerToggle');
  var viewport = track ? track.parentElement : null;
  var paused = false;

  function setPaused(p){
    paused = p;
    if(track) track.classList.toggle('paused', paused);
    if(toggleBtn) toggleBtn.textContent = paused ? 'PAUSED ▶' : 'LIVE ⏸';
  }
  if(viewport){
    viewport.addEventListener('mouseenter', function(){ if(track) track.classList.add('paused'); });
    viewport.addEventListener('mouseleave', function(){ if(track && !paused) track.classList.remove('paused'); });
  }
  if(toggleBtn){
    toggleBtn.addEventListener('click', function(){ setPaused(!paused); });
  }

  // ---- Nav dropdown: hover (desktop, via CSS) + click toggle (touch/keyboard) ----
  var dropItems = document.querySelectorAll('.nav-item.has-drop');
  dropItems.forEach(function(item){
    var link = item.querySelector('a');
    link.addEventListener('click', function(e){
      // On touch devices, first tap opens the submenu instead of navigating
      if(window.matchMedia('(hover: none)').matches){
        if(!item.classList.contains('open')){
          e.preventDefault();
          dropItems.forEach(function(i){ if(i !== item) i.classList.remove('open'); });
          item.classList.add('open');
        }
        // second tap on an already-open item navigates normally
      }
    });
  });
  document.addEventListener('click', function(e){
    dropItems.forEach(function(item){
      if(!item.contains(e.target)) item.classList.remove('open');
    });
  });

  // ---- Mobile menu ----
  var navToggle = document.querySelector('.nav-toggle');
  var mobileMenu = document.getElementById('mobileMenu');
  var mmClose = document.getElementById('mmClose');
  function openMobile(){ if(mobileMenu) mobileMenu.classList.add('open'); }
  function closeMobile(){ if(mobileMenu) mobileMenu.classList.remove('open'); }
  if(navToggle) navToggle.addEventListener('click', openMobile);
  if(mmClose) mmClose.addEventListener('click', closeMobile);
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') closeMobile();
  });
  if(mobileMenu){
    mobileMenu.addEventListener('click', function(e){
      if(e.target === mobileMenu) closeMobile();
    });
  }

  // ---- Ranking workspace: T100 master rail + always-visible cohorts ----
  document.querySelectorAll('.ranking-workspace').forEach(function(workspace){
    var control=workspace.querySelector('.seg-control');
    var panels=workspace.querySelector('.ranking-panels');
    if(!control||!panels)return;
    var boards=document.createElement('div'); boards.className='ranking-card-boards'; panels.appendChild(boards);
    var buttons=Array.from(control.querySelectorAll('.seg-btn'));
    var panelList=Array.from(panels.querySelectorAll('.rk-panel'));
    panelList.forEach(function(panel,index){
      panel.classList.remove('hidden');
      var label=buttons[index] ? buttons[index].textContent.trim() : '';
      var h=document.createElement('div'); h.className='ranking-panel-head';
      h.innerHTML='<b>'+label.replace(/\d+\/?\d*$/,'').trim()+'</b><span>매일 05:15 KST 갱신</span>';
      panel.parentNode.insertBefore(h,panel);
      var shell=document.createElement('section'); shell.className=index===0?'ranking-master':'ranking-cohort';

      h.parentNode.insertBefore(shell,h); shell.appendChild(h); shell.appendChild(panel);
      if(index>0)boards.appendChild(shell);
    });
    control.classList.add('ranking-summary-strip');
  });

  // Legacy tab events remain for deep links, but the dashboard itself keeps
  // all panels visible. A hash scrolls to the relevant cohort.
  var segBtns = document.querySelectorAll('.seg-btn');
  segBtns.forEach(function(btn){
    btn.addEventListener('click', function(){
      if(btn.closest('.ranking-workspace')){
        var visible=document.getElementById(btn.dataset.target);
        if(visible){ visible.closest('section').scrollIntoView({behavior:'smooth',block:'start'}); }
        return;
      }
      var target = btn.dataset.target;
      var group = btn.parentElement;
      group.querySelectorAll('.seg-btn').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      var panelsContainer = group.parentElement;
      panelsContainer.querySelectorAll('.rk-panel').forEach(function(p){ p.classList.add('hidden'); });
      var targetPanel = document.getElementById(target);
      if(targetPanel) targetPanel.classList.remove('hidden');
    });
  });

  // ---- Deep-link support: #t100 / #bc70 etc. activates the matching tab on load ----
  if(location.hash){
    var key = location.hash.replace('#','');
    var btn = document.querySelector('.seg-btn[data-target$="-' + key + '"]');
    if(btn) btn.click();
  }

  // ---- BRIDGE sample diagram modal (UNI demo): deterministic illustrative axis values ----
  function hashSeed(str){
    var h = 0;
    for(var i=0;i<str.length;i++){ h = (h*31 + str.charCodeAt(i)) >>> 0; }
    return h;
  }
  function polygonPoints(vals, cx, cy, maxR){
    var angles = [-90, -30, 30, 90, 150, 210]; // 6 axes, starting at top
    return vals.map(function(v, i){
      var r = (v/100) * maxR;
      var rad = angles[i] * Math.PI/180;
      var x = cx + r*Math.cos(rad);
      var y = cy + r*Math.sin(rad);
      return x.toFixed(1) + ',' + y.toFixed(1);
    }).join(' ');
  }
  function buildRadarSVG(vals, missing, references){
    var cx=160, cy=160, maxR=120;
    missing = missing || [];
    references = references || [];
    var rings = [0.33, 0.66, 1.0].map(function(f){
      return '<polygon points="' + polygonPoints([f*100,f*100,f*100,f*100,f*100,f*100], cx, cy, maxR) + '" fill="none" stroke="#DEDAD1" stroke-width="1"/>';
    }).join('');
    // 결측 축은 레이더 꼭짓점을 작게(흐리게) — 찌그러짐 완화
    var points=polygonPoints(vals,cx,cy,maxR).split(' ');
    var axisNames=['B','R','I','D','G','E'];
    var dataPoly = '<polygon points="'+points.join(' ')+'" fill="rgba(169,136,79,0.12)" stroke="none"/>';
    dataPoly+=points.map(function(point,i){
      var next=(i+1)%6, dashed=references.indexOf(axisNames[i])>=0||references.indexOf(axisNames[next])>=0;
      return '<polyline points="'+point+' '+points[next]+'" fill="none" stroke="'+(dashed?'#999':'#a9884f')+'" stroke-width="2"'+(dashed?' stroke-dasharray="5,4"':'')+'/>';
    }).join('');
    dataPoly+=points.map(function(point,i){
      if(references.indexOf(axisNames[i])<0)return '';
      var xy=point.split(',');
      return '<circle cx="'+xy[0]+'" cy="'+xy[1]+'" r="4" fill="white" stroke="#999"><title>'+axisNames[i]+' · 참조 기준 · 대상 평가값 아님</title></circle>';
    }).join('');
    var labels = ['B','R','I','D','G','E'];
    var angles = [-90,-30,30,90,150,210];
    var labelEls = labels.map(function(l, i){
      var rad = angles[i]*Math.PI/180;
      var x = cx + (maxR+20)*Math.cos(rad);
      var y = cy + (maxR+20)*Math.sin(rad);
      var isM = missing.indexOf(l) >= 0;
      var col = isM ? '#c9c4b8' : '#161513';   // 결측 축 라벨 흐리게
      return '<text x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" text-anchor="middle" dominant-baseline="middle" font-size="15" font-weight="700" fill="'+col+'">'+l+'</text>';
    }).join('');
    // 결측 축 꼭짓점에 작은 점선 표식
    var missDots = labels.map(function(l,i){
      if(missing.indexOf(l)<0) return '';
      var rad = angles[i]*Math.PI/180;
      var x = cx + (maxR*0.12)*Math.cos(rad);
      var y = cy + (maxR*0.12)*Math.sin(rad);
      return '<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="3" fill="none" stroke="#c9c4b8" stroke-width="1" stroke-dasharray="2,2"/>';
    }).join('');
    return rings + dataPoly + missDots + labelEls;
  }

  var modalOverlay = document.getElementById('bridgeModalOverlay');
  var modalClose = document.getElementById('bridgeModalClose');
  var PILOT_CASES = window.BRIDGE_PILOT_CASES || {};
  function openBridgeModal(name, region, type, snapshotDate){
    if(!modalOverlay) return;
    var flagEl = document.getElementById('bridgeModalFlag');
    var evList = document.getElementById('bridgeEvidenceList');
    var scoreNote = document.getElementById('bmScoreNote') || {};
    var periodLbl = document.getElementById('bmPeriodLabel') || {};
    var wowLbl = document.getElementById('bmWowLabel') || {};
    var cumLbl = document.getElementById('bmCumLabel') || {};
    var pilot = selectModalCase(name,region,snapshotDate);
    document.getElementById('bridgeModalTitle').textContent = name;
    var intelligenceLink=document.getElementById('bridgeModalIntelligence');
    if(!intelligenceLink){
      intelligenceLink=document.createElement('a');
      intelligenceLink.id='bridgeModalIntelligence';
      intelligenceLink.className='modal-intelligence-link';
      intelligenceLink.textContent='이 대상을 더 깊게 분석하기';
      var modalScore=document.querySelector('.bridge-modal-score');
      if(modalScore&&modalScore.parentNode)modalScore.parentNode.insertBefore(intelligenceLink,modalScore.nextSibling);
    }
    intelligenceLink.href='intelligence.html?field='+encodeURIComponent(region)+'&target='+encodeURIComponent(name);
    if(pilot){
      document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · '+(pilot.snapshot_date||snapshotDate||'현재 공개본')+' · 근거 신뢰등급 ' + (pilot.trust || 'N/R') + ' · 평판등급이 아님';
      flagEl.textContent = 'BRIDGE 축의 상태 프로필입니다. 참조값 50은 대상의 실제 평가점수가 아니며 종합지수와 순위 계산에서 제외됩니다.';
      flagEl.style.background = '#e8f3ee';
      flagEl.style.color = '#1d5c42';
      flagEl.style.borderColor = '#2e7d5a';
      var svg = document.getElementById('bridgeRadar');
      var missingAxes = ['B','R','I','D','G','E'].filter(function(k){ return pilot.dims[k] === null || pilot.dims[k] === undefined; });
      // 결측 축은 0 대신 중앙 근처(8)로 — 찌그러짐 완화, 라벨은 흐리게
      var vals = ['B','R','I','D','G','E'].map(function(k){ var v=pilot.dims[k]; return (v === null || v === undefined) ? 8 : v; });
      var referenceAxes=['B','R','I','D','G','E'].filter(function(k){return (pilot.axis_status||{})[k]==='reference';});
      svg.innerHTML = buildRadarSVG(vals, missingAxes, referenceAxes);
      ['B','R','I','D','G','E'].forEach(function(k){
        var v = pilot.dims[k];
        var state=(pilot.axis_status||{})[k];
        var label={observed:'관측',maintained:'유지',estimated:'추정',reference:'참조'}[state]||'';
        var cell=document.getElementById('bm'+k);
        cell.textContent=(v===null||v===undefined?'N/R':v)+(label?' · '+label:'');
        cell.title=state==='reference'?'대상 실측 없음 · 시각적 참조 기준 · 순위 제외':((pilot.axis_evidence_dates||{})[k]||'근거 기준일 확인 필요');
        cell.classList.toggle('axis-reference',state==='reference');
      });
      var currentStates=pilot.axis_status||{};
      var availableCount=['B','R','I','D','G','E'].filter(function(k){return currentStates[k]==='observed'||currentStates[k]==='maintained';}).length;
      var observedCount=['B','R','I','D','G','E'].filter(function(k){return currentStates[k]==='observed';}).length;
      var maintainedCount=['B','R','I','D','G','E'].filter(function(k){return currentStates[k]==='maintained';}).length;
      var referenceCount=['B','R','I','D','G','E'].filter(function(k){return currentStates[k]==='reference';}).length;
      function setMetricSub(id,text){
        var el=document.getElementById(id), row=el&&typeof el.closest==='function'?el.closest('.bmscore-row'):null, sub=row&&typeof row.querySelector==='function'?row.querySelector('.bmscore-sub'):null;
        if(sub)sub.textContent=text;
      }
      setMetricSub('bmIndexPoint','오늘의 관측 가능한 관계 평판 수준');
      setMetricSub('bmWeekly','월요일부터 현재까지 일별지수의 근거 신뢰도 가중평균');
      setMetricSub('bmLastWeek','직전 월~일 일별지수의 근거 신뢰도 가중평균');
      setMetricSub('bmWow','이번 주와 직전 완료 주간 대표지수의 차이');
      setMetricSub('bmFourWeek','최근 최대 4개 주간 대표지수 평균');
      setMetricSub('bmV3Score',availableCount===6?'여섯 축을 모두 가중 반영한 당일 종합지수':'관측·유지 '+availableCount+'/6축을 가중 반영한 당일 종합지수');
      setMetricSub('bmActivity','이번 주 검증·중복 제거된 사건 활동량');
      setMetricSub('bmCumulativeActivity','운영 관측기간의 검증된 사건 활동량 누계');
      setMetricSub('bmCumulative','관측된 주간 대표지수의 누적 평균');
      setMetricSub('bmStability','최근 주간 대표지수 변동의 안정성');
      // 공개 지표: 내부 산식과 원천변수는 노출하지 않고 결과와 의미만 제공한다.
      var dailyIndex = pilot.daily_index;
      var weeklyIndex = (pilot.weekly_index != null) ? pilot.weekly_index : pilot.score;
      document.getElementById('bmIndexPoint').textContent = (dailyIndex != null ? dailyIndex : 'N/R');
      document.getElementById('bmWeekly').textContent = (weeklyIndex != null ? weeklyIndex : 'N/R');
      document.getElementById('bmActivity').textContent = (pilot.activity_points != null ? pilot.activity_points + 'P' : 'N/R');
      document.getElementById('bmFourWeek').textContent = (pilot.four_week_average != null ? pilot.four_week_average : 'N/R');
      document.getElementById('bmCumulativeActivity').textContent = (pilot.cumulative_activity != null ? pilot.cumulative_activity + 'P' : 'N/R');
      document.getElementById('bmStability').textContent = (pilot.stability != null ? pilot.stability : 'N/R');
      var _v3el = document.getElementById('bmV3Score');
      if(_v3el){ _v3el.textContent = (pilot.v3_score != null ? pilot.v3_score : '—'); }
      if(pilot.history && pilot.history.length){
        var prevWeek = pilot.history[pilot.history.length - 1];
        var prevScore = prevWeek.score;
        var realWow = Math.round((weeklyIndex - prevScore) * 10) / 10;
        var arrow2 = realWow > 0 ? '▲' : (realWow < 0 ? '▼' : '—');
        // 2) 전주 지표
        document.getElementById('bmLastWeek').textContent = (prevScore != null ? prevScore : '—');
        // 3) WoW (실측 표기 제거)
        document.getElementById('bmWow').textContent = arrow2 + ' ' + Math.abs(realWow);
        // 장기 성과는 기간 합계가 아니라 비교 가능한 기간평균으로 표시한다.
        var weeksN = pilot.observed_weeks || (pilot.history.length + 1);
        var allScores = pilot.history.map(function(h){return h.score;}).concat([weeklyIndex]);
        var histSum = allScores.reduce(function(a,b){return a+b;}, 0);
        var histAvg = Math.round((histSum / weeksN) * 10) / 10;
        var cumulativeValue = pilot.cumulative_performance != null ? pilot.cumulative_performance : histAvg;
        document.getElementById('bmCumulative').innerHTML = '<span class=\'cum-unit\'>평균</span> <span class=\'cum-num\'>' + cumulativeValue + '</span><span class=\'cum-tail\'> · 관측 ' + weeksN + '주</span>';
      } else {
        // 전주 데이터 아직 없음 — 이번 주가 첫 기록
        document.getElementById('bmLastWeek').textContent = '—';
        document.getElementById('bmWow').textContent = '— (첫 주)';
        var firstCumulative = pilot.cumulative_performance != null ? pilot.cumulative_performance : weeklyIndex;
        document.getElementById('bmCumulative').innerHTML = '<span class=\'cum-unit\'>평균</span> <span class=\'cum-num\'>' + firstCumulative + '</span><span class=\'cum-tail\'> · 관측 ' + (pilot.observed_weeks || 1) + '주</span>';
      }
      if(pilot.comparison_status !== 'same_scope'){
        document.getElementById('bmWow').textContent='— · '+scopeMessage(pilot.comparison_status);
      }
      var isNonVolatile = pilot.method === '비변동성';
      scoreNote.textContent = '산출 범위 '+availableCount+'/6축 · 관측 '+observedCount+' · 유지 '+maintainedCount+' · 참조 '+referenceCount+'. 평판 수준은 가중평균으로, 활동은 총량으로 읽으며 참조 축은 종합지수와 순위에 반영하지 않습니다.';
      if(pilot.observed_days!=null)scoreNote.textContent+=' 이번 주 평가 가능 '+pilot.observed_days+'일 · 수집 정상 '+(pilot.collection_ok_days==null?'확인 중':pilot.collection_ok_days+'일')+'.';
      if(pilot.comparison_status&&pilot.comparison_status!=='same_scope')scoreNote.textContent+=' 비교 상태: '+({baseline_pending:'새 기준의 비교 자료 축적 중',scope_expanded:'근거 범위 확대',scope_reduced:'근거 범위 축소',scope_changed:'근거 구성 변경',methodology_changed:'산출 기준 변경',legacy_unverified:'이전 기준 · 비교 검토 필요'}[pilot.comparison_status]||'비교 검토 필요')+'.';
      var evItems = document.getElementById('bridgeEvidenceItems');
      var dims = pilot.dims || {};
      var evLines = [];
      var publicAxis = {B:'도달',R:'반응',I:'정체성',D:'경험',G:'행동유발',E:'책임·지속'};
      Object.keys(publicAxis).forEach(function(k){
        if(dims[k] !== null && dims[k] !== undefined && (pilot.axis_status||{})[k]!=='reference'){
          evLines.push('<div class="evidence-item"><b>' + k + ' · ' + publicAxis[k] + '</b> 유효 신호가 확인되었습니다.</div>');
        }
      });
      if(!evLines.length){
        evLines.push('<div class="evidence-item">유효 근거가 확보된 축을 기준으로 산출되었습니다.</div>');
      }
      evItems.innerHTML = evLines.join('');
      var limItems = document.getElementById('bridgeLimitationItems');
      var lim = [];
      if(pilot.reference_axes_count)lim.push('<li>참조 축 '+pilot.reference_axes_count+'개는 대상별 평가 결과가 아니며 순위 산출에서 제외됩니다.</li>');
      // 미산출 축 안내
      var missing = ['B','R','I','D','G','E'].filter(function(k){ return dims[k] === null || dims[k] === undefined; });
      var axisKo = {B:'B',R:'R',I:'I',D:'D',G:'G',E:'E'};
      if(missing.length){
        lim.push('<li>데이터 부족으로 현재 미산출된 영역(' + missing.map(function(k){return axisKo[k];}).join('·') + '축)은 공식 데이터 갱신 시점에 교정·추가됩니다.</li>');
      }
      // 잠정 대입 등 돌발상황(수정 이력이 있으면)
      if(pilot.has_revision){
        lim.push('<li>일부 지표는 데이터 갱신 과정에서 보정된 잠정 수치가 포함될 수 있습니다.</li>');
      }
      if(!lim.length){
        lim.push('<li>현재 확보된 근거 범위 내에서 산출되었으며, 데이터가 추가되면 정직하게 갱신됩니다.</li>');
      }
      limItems.innerHTML = lim.join('');
      var legend=document.getElementById('bridgeAxisStateLegend');
      if(!legend){
        legend=document.createElement('div');
        legend.id='bridgeAxisStateLegend';
        legend.className='axis-state-legend';
        evList.appendChild(legend);
      }
      legend.innerHTML='<div class="axis-state-summary">산출 범위 <b>'+availableCount+'/6축</b> · 관측 '+observedCount+' · 유지 '+maintainedCount+' · 참조 '+referenceCount+'</div>'+
        '<div class="axis-state-row"><b>관측</b><span>유효 근거로 해당 날짜의 축 값을 산출</span><em>반영</em></div>'+
        '<div class="axis-state-row"><b>유지</b><span>유효기간 안의 이전 근거를 규칙에 따라 재확인</span><em>반영</em></div>'+
        '<div class="axis-state-row"><b>참조</b><span>대상별 유효 평가값이 없어 중립 기준선만 표시</span><em>제외</em></div>'+
        '<p>참조값 50은 대상의 실제 평가점수가 아닙니다.</p>';
      evList.style.display = 'block';
    } else {
      // [2026-10] 예시 제거 — 미산출 대상은 N/R로 정직하게 표기
      document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · BRIDGE 모형 다이어그램';
      flagEl.textContent = snapshotDate?'선택한 날짜의 공개 상세 자료를 확인할 수 없습니다. 최신 자료로 대체하지 않습니다.':'공개 상세 근거를 확인할 수 없습니다. 유효 축·출처·신뢰도 등 공개 조건을 충족한 자료만 표시합니다.';
      flagEl.style.background = '';
      flagEl.style.color = '';
      flagEl.style.borderColor = '';
      var svg2 = document.getElementById('bridgeRadar');
      svg2.innerHTML = buildRadarSVG([0,0,0,0,0,0]);
      ['B','R','I','D','G','E'].forEach(function(k){
        document.getElementById('bm'+k).textContent = 'N/R';
      });
      document.getElementById('bmIndexPoint').textContent = 'N/R';
      document.getElementById('bmWeekly').textContent = 'N/R';
      document.getElementById('bmLastWeek').textContent = 'N/R';
      document.getElementById('bmWow').textContent = 'N/R';
      document.getElementById('bmV3Score').textContent = 'N/R';
      document.getElementById('bmActivity').textContent = 'N/R';
      document.getElementById('bmFourWeek').textContent = 'N/R';
      document.getElementById('bmCumulativeActivity').textContent = 'N/R';
      document.getElementById('bmStability').textContent = 'N/R';
      document.getElementById('bmCumulative').textContent = 'N/R';
      scoreNote.textContent = '';
      evList.style.display = 'none';
    }
    modalOverlay.classList.add('open');
  }

  /* One quiet service entry per ranking page; mobile uses a reachable bottom action. */
  if(typeof document.querySelector==='function'&&document.querySelector('.ranking-panels')&&!document.querySelector('.intelligence-rail')){
    var rail=document.createElement('a');
    rail.className='intelligence-rail';rail.href='intelligence.html';
    rail.setAttribute('aria-label','BRIDGE 분석 서비스 보기');rail.innerHTML='<span>BRIDGE INTELLIGENCE</span>';
    document.body.appendChild(rail);
    var mobileCta=document.createElement('a');
    mobileCta.className='intelligence-mobile-cta';mobileCta.href='intelligence.html';
    mobileCta.textContent='BRIDGE 분석 서비스 보기 →';document.body.appendChild(mobileCta);
    document.body.classList.add('has-intelligence-mobile');
  }
  function closeBridgeModal(){ if(modalOverlay) modalOverlay.classList.remove('open'); }
  window.openBridgeModal = openBridgeModal;
  // Delegation keeps every live row interactive after the 05:15 snapshot
  // replaces T100 and cohort markup asynchronously.
  document.addEventListener('click', function(e){
    var row=e.target.closest('.rk-clickable');
    if(row) openBridgeModal(row.dataset.entity, row.dataset.region, row.dataset.type, row.dataset.liveDate);
  });
  document.addEventListener('keydown', function(e){
    var row=e.target.closest && e.target.closest('.rk-clickable');
    if(row && (e.key === 'Enter' || e.key === ' ')){
      e.preventDefault(); openBridgeModal(row.dataset.entity, row.dataset.region, row.dataset.type, row.dataset.liveDate);
    }
  });
  if(modalClose) modalClose.addEventListener('click', closeBridgeModal);
  if(modalOverlay) modalOverlay.addEventListener('click', function(e){ if(e.target === modalOverlay) closeBridgeModal(); });
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeBridgeModal(); });

  // ---- Period selector (Week/Month/Quarter/Half/Year) ----
  document.querySelectorAll('.period-selector').forEach(function(sel){
    var periods;
    try { periods = JSON.parse(sel.dataset.periods); } catch(e){ return; }
    var tabs = sel.querySelectorAll('.period-unit');
    var rangeSelect = sel.querySelector('.period-range');
    function fmtRange(pair){ return pair[0] === pair[1] ? pair[0] : (pair[0] + ' ~ ' + pair[1]); }
    function populate(unit){
      var list = periods[unit] || [];
      rangeSelect.innerHTML = list.map(function(p, i){
        return '<option value="' + i + '">' + fmtRange(p) + '</option>';
      }).join('');
      if(list.length) rangeSelect.selectedIndex = list.length - 1; // default to most recent
      var status=sel.querySelector('.period-status');
      if(status) status.textContent=list.length ? '기간 선택 가능' : 'N/R';
    }
    tabs.forEach(function(tab){
      tab.addEventListener('click', function(){
        tabs.forEach(function(t){ t.classList.remove('active'); });
        tab.classList.add('active');
        populate(tab.dataset.unit);
      });
    });
    var defaultUnit = sel.dataset.defaultUnit || 'week';
    populate(defaultUnit);
    rangeSelect.addEventListener('change', function(){
      var status=sel.querySelector('.period-status');
      var unit=sel.querySelector('.period-unit.active');
      var list=periods[unit?unit.dataset.unit:(sel.dataset.defaultUnit||'week')]||[];
      var pair=list[Number(rangeSelect.value)];
      var ok=pair&&window.BRIDGE_RENDER_PERIOD?window.BRIDGE_RENDER_PERIOD(pair[0],pair[1]):false;
      if(status) status.textContent=ok===null?'기간 이력을 불러오는 중입니다. 잠시 후 다시 선택해 주세요.':ok?'선택 기간 안의 마지막 공개일 스냅샷':'해당 기간 N/R';
    });
  });

})();


/* ===== [2026-09 신설] 검색 + 정렬 (동료 피드백 반영) ===== */
(function(){
  function rowsIn(page){
    // 해당 페이지의 활성 패널 내 rk-row 수집
    return Array.from(document.querySelectorAll('.rk-panel'))
      .filter(function(p){ return p.id && p.id.indexOf(page+'-')===0; });
  }
  function scoreOf(row){
    var el=row.querySelector('.rk-score'); if(!el) return -1;
    var v=parseFloat(el.textContent.replace(/[^\d.]/g,'')); return isNaN(v)?-1:v;
  }
  function nameOf(row){ return (row.getAttribute('data-entity')||'').trim(); }

  // 검색
  document.querySelectorAll('.rk-search').forEach(function(inp){
    inp.addEventListener('input', function(){
      var page=inp.getAttribute('data-page');
      var q=inp.value.trim().toLowerCase();
      rowsIn(page).forEach(function(panel){
        panel.querySelectorAll('[data-entity]').forEach(function(row){
          var hit = nameOf(row).toLowerCase().indexOf(q)>=0;
          row.setAttribute('data-search-hidden', (q==='' || hit) ? '0' : '1');
        });
      });
      if(window.__bridgeRepage) window.__bridgeRepage(page);
    });
  });

  // 정렬
  document.querySelectorAll('.rk-sort-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      var page=btn.getAttribute('data-page');
      var mode=btn.getAttribute('data-sort');
      // 버튼 활성표시 (같은 페이지 내)
      document.querySelectorAll('.rk-sort-btn[data-page="'+page+'"]').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      rowsIn(page).forEach(function(panel){
        var rows=Array.from(panel.querySelectorAll('[data-entity]'));
        if(rows.length<2) return;
        if(mode==='default'){
          rows.sort(function(a,b){ return (parseInt(a.getAttribute('data-idx')||0)) - (parseInt(b.getAttribute('data-idx')||0)); });
        } else if(mode==='score'){
          rows.sort(function(a,b){ return scoreOf(b)-scoreOf(a); }); // 높은 점수 먼저(N/R=-1은 뒤로)
        } else if(mode==='name'){
          rows.sort(function(a,b){ return nameOf(a).localeCompare(nameOf(b),'ko'); });
        }
        rows.forEach(function(r){ panel.appendChild(r); });
      });
      if(window.__bridgeRepage) window.__bridgeRepage(page);
    });
  });
})();

(function(){
  document.querySelectorAll('.rk-panel').forEach(function(panel){
    Array.from(panel.querySelectorAll('[data-entity]')).forEach(function(row,i){
      if(!row.getAttribute('data-idx')) row.setAttribute('data-idx', i);
    });
  });
})();


/* ===== [2026-09] 페이지네이션 + 검색/정렬 연동 (동료 피드백 ④) ===== */
(function(){
  var PAGE_SIZE = 20;

  function visibleRows(panel){
    // 검색으로 display:none 처리되지 않은 행만 대상
    return Array.from(panel.querySelectorAll('[data-entity]'))
      .filter(function(r){ return r.getAttribute('data-search-hidden')!=='1'; });
  }

  function applyPaging(panel){
    if(panel.classList.contains('hidden')) return;
    var rows = visibleRows(panel);
    var shown = parseInt(panel.getAttribute('data-shown')||PAGE_SIZE, 10);
    rows.forEach(function(r,i){
      // 검색으로 숨긴 건 그대로 숨김, 그 외에는 페이지 범위만 표시
      if(r.getAttribute('data-search-hidden')==='1'){ r.style.display='none'; return; }
      r.style.display = (i < shown) ? '' : 'none';
    });
    // 기존 더보기 버튼 제거
    var old = panel.querySelector('.rk-more-wrap'); if(old) old.remove();
    if(rows.length > shown){
      var wrap=document.createElement('div'); wrap.className='rk-more-wrap';
      var btn=document.createElement('button'); btn.className='rk-more-btn';
      btn.textContent='더 보기';
      var cnt=document.createElement('span'); cnt.className='rk-more-count';
      cnt.textContent='('+shown+' / '+rows.length+')';
      btn.addEventListener('click', function(){
        panel.setAttribute('data-shown', Math.min(shown+PAGE_SIZE, rows.length));
        applyPaging(panel);
      });
      wrap.appendChild(btn); wrap.appendChild(cnt);
      panel.appendChild(wrap);
    }
  }

  // 전역 훅: 검색/정렬 후 호출
  window.__bridgeRepage = function(page){
    document.querySelectorAll('.rk-panel').forEach(function(panel){
      if(page && panel.id.indexOf(page+'-')!==0) return;
      panel.setAttribute('data-shown', PAGE_SIZE); // 검색·정렬 시 첫 페이지로 리셋
      applyPaging(panel);
    });
  };

  // 초기 적용
  document.querySelectorAll('.rk-panel').forEach(function(panel){
    panel.setAttribute('data-shown', PAGE_SIZE);
    applyPaging(panel);
  });

  // 탭 전환 시에도 적용 (seg-btn 클릭 후 패널이 보이게 되면)
  document.querySelectorAll('.seg-btn').forEach(function(b){
    b.addEventListener('click', function(){ setTimeout(function(){ window.__bridgeRepage(); }, 30); });
  });
})();


/* [2026-09 수정] 모바일도 탭=모달(벤다이어그램)로 통일 — 펼침 로직 제거 */

/* Preserve equal alignment after generated-page rebuilds. */
(function alignHomeActions(){
  var mobile=window.matchMedia('(max-width:650px)').matches;
  document.querySelectorAll('#hero-cinematic .hero-actions .btn').forEach(function(el){
    el.style.setProperty('align-items','center','important');
    el.style.setProperty('justify-content','center','important');
    el.style.setProperty('text-align','center','important');
    el.style.setProperty('height',mobile?'48px':'50px','important');
    el.style.setProperty('line-height','1','important');
  });
})();

