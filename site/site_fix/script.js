(function(){
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
    el.innerHTML='VOL. 01 — WEEK '+week+'<br>SEOUL · '+String(d).padStart(2,'0')+' '+months[m-1]+' '+y;
  })();
  // Published Supabase snapshot. A valid daily snapshot rebuilds the public
  // T100 list in score/rank order; static HTML is fallback only.
  (function loadBridgeDailySnapshot(){
    var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    var domain = page === 'cpr.html' ? 'CPR' : page === 'gov.html' ? 'GOV' :
      page === 'uni.html' ? 'UNI' : page === 'star.html' ? 'ENT' : null;
    fetch('data/latest.json', {cache:'no-store'}).then(function(res){
      if(!res.ok) throw new Error('snapshot unavailable');
      return res.json();
    }).then(function(payload){
      var rows = (payload.rankings || []).filter(function(r){ return r.ranking_type === 'T100'; });
      rows.sort(function(a,b){ return Number(a.rank)-Number(b.rank) || Number(b.score)-Number(a.score); });
      function esc(v){ var d=document.createElement('div'); d.textContent=String(v==null?'':v); return d.innerHTML; }
      function change(rec){
        var d=Number(rec.rank_change||0), cls=d>0?'wow-up':d<0?'wow-down':'wow-flat';
        return '<span class="wow '+cls+'">'+(d>0?'▲ '+d:d<0?'▼ '+Math.abs(d):'— 0')+'</span>';
      }
      function rankRow(rec){
        var n=Number(rec.rank), top=n<=3?' top3':'';
        return '<div class="rk-row rk-clickable live-row'+top+'" data-entity="'+esc(rec.name)+'" data-region="'+esc(rec.domain)+'" data-type="T100" data-live-date="'+esc(payload.asOfDate||'')+'" tabindex="0" role="button">'+
          '<div class="rk-num">'+String(n).padStart(2,'0')+'</div>'+
          '<div class="rk-name"><div class="nm">'+esc(rec.name)+'</div><div class="sub">'+esc(rec.external_id)+' · '+esc(rec.category||'')+' · '+esc(rec.subcategory||'T100')+'</div></div>'+
          '<div class="rk-market">'+esc(rec.subcategory||rec.domain)+'</div>'+
          '<div class="rk-dims"><span class="dm">실측 공개적격 · '+esc(payload.asOfDate||'')+'</span></div>'+
          '<div class="rk-score">'+Number(rec.score).toFixed(1)+'</div>'+
          '<div class="rk-wow">'+change(rec)+'</div>'+
          '<div class="rk-trust"><span class="trust-badge grade-'+esc(rec.trust_grade)+'">'+esc(rec.trust_grade)+'</span></div></div>';
      }
      if(domain){
        var live=rows.filter(function(r){return r.domain===domain;});
        window.BRIDGE_PILOT_CASES = window.BRIDGE_PILOT_CASES || {};
        live.forEach(function(rec){
          window.BRIDGE_PILOT_CASES[rec.name] = {
            dims:rec.axis_scores||{B:null,R:null,I:null,D:null,G:null,E:null}, score:rec.score,
            daily_index:rec.daily_index, weekly_index:rec.weekly_index,
            activity_points:rec.activity_points, cumulative_performance:rec.cumulative_performance,
            v3_score:rec.weighted_index, trust:rec.trust_grade, method:'live',
            history:rec.last_week_index==null?[]:[{score:rec.last_week_index}]
          };
        });
        var prefix=domain==='ENT'?'star':domain.toLowerCase(), panel=document.getElementById(prefix+'-t100');
        if(panel){ panel.innerHTML=live.map(rankRow).join(''); panel.setAttribute('data-shown','1000'); }
        if(panel && window.openBridgeModal){
          panel.querySelectorAll('.rk-clickable').forEach(function(row){
            row.addEventListener('click',function(){ window.openBridgeModal(row.dataset.entity,row.dataset.region,row.dataset.type); });
            row.addEventListener('keydown',function(e){ if(e.key==='Enter'||e.key===' '){e.preventDefault();row.click();} });
          });
        }
        var btn=document.querySelector('.seg-btn[data-target="'+prefix+'-t100"] span');
        if(btn) btn.textContent=live.length+'/100';
        if(panel){
          var note=document.createElement('div'); note.className='live-snapshot-note';
          note.textContent='실측 공개 '+live.length+' / 100 · '+(payload.asOfDate||'')+' · 공개적격 전 대상 표시';
          panel.parentNode.insertBefore(note,panel);
        }
      }
      // 주식시황형 LIVE 바: CPR 1~10, ENT 1~10, GOV 1~10,
      // CPR 11~20, ENT 11~20, GOV 11~20. 각 영역 50위까지만 사용한다.
      var track=document.getElementById('tickerTrack');
      if(track){
        function take(d,a,b){return rows.filter(function(r){return r.domain===d&&Number(r.rank)>=a&&Number(r.rank)<=b&&Number(r.rank)<=50;});}
        var seq=[].concat(take('CPR',1,10),take('ENT',1,10),take('GOV',1,10),take('CPR',11,20),take('ENT',11,20),take('GOV',11,20));
        var html=seq.map(function(r){var d=Number(r.rank_change||0);return '<span><b>'+esc(r.domain)+'</b>'+esc(r.name)+' <span class="t-score">'+Number(r.score).toFixed(1)+'</span> <i class="'+(d>0?'t-up':d<0?'t-down':'t-flat')+'">'+(d>0?'+'+d:d)+'</i></span>';}).join('');
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
            var deltaText=delta>0?'▲ '+delta:delta<0?'▼ '+Math.abs(delta):'— 0';
            return '<li><span class="t5-nm">'+esc(r.name)+'</span><span class="t5-sc">'+Number(r.score).toFixed(1)+'</span><span class="'+deltaClass+'">'+deltaText+'</span></li>';
          }).join('') : '<li class="t5-empty">오늘 공개 기준 충족 대상 없음</li>';
          return '<a class="t5-block" href="'+heroLinks[d]+'"><div class="t5-head">'+d+' <span class="t5-more">TOP 5 →</span></div><ol class="t5-list">'+items+'</ol></a>';
        }).join('');
        heroTop.setAttribute('data-live-date',payload.asOfDate||'');
      }
      // THIS WEEK의 네 영역 목록도 같은 스냅샷으로 교체한다.
      document.querySelectorAll('.twr-col').forEach(function(col){
        var h=col.querySelector('.twr-head'), list=col.querySelector('.twr-list'); if(!h||!list)return;
        var d=(h.textContent.trim().match(/^(CPR|GOV|UNI|ENT)/)||[])[1]; if(!d)return;
        var live=rows.filter(function(r){return r.domain===d;}).slice(0,15);
        list.innerHTML=live.map(function(r){return '<li class="twr-item '+(Number(r.rank)<=3?'twr-top3':'')+'"><span class="twr-rank">'+r.rank+'</span><span class="twr-name">'+esc(r.name)+'</span><span class="twr-score">'+Number(r.score).toFixed(1)+'</span></li>';}).join('');
      });
    }).catch(function(){
      // Never replace the last deployed snapshot with zeroes after a failed run.
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

  // ---- Segmented ranking tabs (CPR/STAR/GOV pages) ----
  var segBtns = document.querySelectorAll('.seg-btn');
  segBtns.forEach(function(btn){
    btn.addEventListener('click', function(){
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
  function buildRadarSVG(vals, missing){
    var cx=160, cy=160, maxR=120;
    missing = missing || [];
    var rings = [0.33, 0.66, 1.0].map(function(f){
      return '<polygon points="' + polygonPoints([f*100,f*100,f*100,f*100,f*100,f*100], cx, cy, maxR) + '" fill="none" stroke="#DEDAD1" stroke-width="1"/>';
    }).join('');
    // 결측 축은 레이더 꼭짓점을 작게(흐리게) — 찌그러짐 완화
    var dataPoly = '<polygon points="' + polygonPoints(vals, cx, cy, maxR) + '" fill="rgba(169,136,79,0.22)" stroke="#a9884f" stroke-width="2"/>';
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
  function openBridgeModal(name, region, type){
    if(!modalOverlay) return;
    var flagEl = document.getElementById('bridgeModalFlag');
    var evList = document.getElementById('bridgeEvidenceList');
    var scoreNote = document.getElementById('bmScoreNote') || {};
    var periodLbl = document.getElementById('bmPeriodLabel') || {};
    var wowLbl = document.getElementById('bmWowLabel') || {};
    var cumLbl = document.getElementById('bmCumLabel') || {};
    var pilot = PILOT_CASES[name];
    document.getElementById('bridgeModalTitle').textContent = name;
    if(pilot){
      document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · BRIDGE 관측 결과 · 신뢰 ' + (pilot.trust || 'N/R');
      flagEl.textContent = '검증 가능한 공개자료를 바탕으로 산출한 관측 결과입니다. 미확인 영역은 N/R로 표시됩니다.';
      flagEl.style.background = '#e8f3ee';
      flagEl.style.color = '#1d5c42';
      flagEl.style.borderColor = '#2e7d5a';
      var svg = document.getElementById('bridgeRadar');
      var missingAxes = ['B','R','I','D','G','E'].filter(function(k){ return pilot.dims[k] === null || pilot.dims[k] === undefined; });
      // 결측 축은 0 대신 중앙 근처(8)로 — 찌그러짐 완화, 라벨은 흐리게
      var vals = ['B','R','I','D','G','E'].map(function(k){ var v=pilot.dims[k]; return (v === null || v === undefined) ? 8 : v; });
      svg.innerHTML = buildRadarSVG(vals, missingAxes);
      ['B','R','I','D','G','E'].forEach(function(k){
        var v = pilot.dims[k];
        document.getElementById('bm'+k).textContent = (v === null || v === undefined) ? 'N/R' : v;
      });
      // 공개 지표: 내부 산식과 원천변수는 노출하지 않고 결과와 의미만 제공한다.
      var dailyIndex = pilot.daily_index;
      var weeklyIndex = (pilot.weekly_index != null) ? pilot.weekly_index : pilot.score;
      document.getElementById('bmIndexPoint').textContent = (dailyIndex != null ? dailyIndex : 'N/R');
      document.getElementById('bmWeekly').textContent = (weeklyIndex != null ? weeklyIndex : 'N/R');
      document.getElementById('bmActivity').textContent = (pilot.activity_points != null ? pilot.activity_points + 'P' : 'N/R');
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
        var weeksN = pilot.history.length + 1;
        var allScores = pilot.history.map(function(h){return h.score;}).concat([weeklyIndex]);
        var histSum = allScores.reduce(function(a,b){return a+b;}, 0);
        var histAvg = Math.round((histSum / weeksN) * 10) / 10;
        var cumulativeValue = pilot.cumulative_performance != null ? pilot.cumulative_performance : histAvg;
        document.getElementById('bmCumulative').innerHTML = '<span class=\'cum-unit\'>평균</span> <span class=\'cum-num\'>' + cumulativeValue + '</span><span class=\'cum-tail\'> · ' + weeksN + '주</span>';
      } else {
        // 전주 데이터 아직 없음 — 이번 주가 첫 기록
        document.getElementById('bmLastWeek').textContent = '—';
        document.getElementById('bmWow').textContent = '— (첫 주)';
        var firstCumulative = pilot.cumulative_performance != null ? pilot.cumulative_performance : weeklyIndex;
        document.getElementById('bmCumulative').innerHTML = '<span class=\'cum-unit\'>평균</span> <span class=\'cum-num\'>' + firstCumulative + '</span><span class=\'cum-tail\'> · 1주</span>';
      }
      var isNonVolatile = pilot.method === '비변동성';
      scoreNote.textContent = '여론의 소음이 아닌, 검증된 공식 데이터와 실제 관측값만으로 구성된 지수입니다. 유효한 근거가 확보된 축만 투명하게 계산하며, 아직 확인되지 않은 데이터는 투명성을 위해 N/A로 남겨두었습니다.';
      var evItems = document.getElementById('bridgeEvidenceItems');
      var dims = pilot.dims || {};
      var evLines = [];
      var publicAxis = {B:'도달',R:'반응',I:'정체성',D:'경험',G:'행동유발',E:'책임·지속'};
      Object.keys(publicAxis).forEach(function(k){
        if(dims[k] !== null && dims[k] !== undefined){
          evLines.push('<div class="evidence-item"><b>' + k + ' · ' + publicAxis[k] + '</b> 유효 신호가 확인되었습니다.</div>');
        }
      });
      if(!evLines.length){
        evLines.push('<div class="evidence-item">유효 근거가 확보된 축을 기준으로 산출되었습니다.</div>');
      }
      evItems.innerHTML = evLines.join('');
      var limItems = document.getElementById('bridgeLimitationItems');
      var lim = [];
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
      evList.style.display = 'block';
    } else {
      // [2026-10] 예시 제거 — 미산출 대상은 N/R로 정직하게 표기
      document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · BRIDGE 모형 다이어그램';
      flagEl.textContent = '현재 공개 기준(유효 축 2개 이상)을 충족하지 못해 미산출(N/R) 상태입니다. 데이터가 확보되면 자동 산출됩니다.';
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
      document.getElementById('bmCumulative').textContent = 'N/R';
      scoreNote.textContent = '';
      evList.style.display = 'none';
    }
    modalOverlay.classList.add('open');
  }
  function closeBridgeModal(){ if(modalOverlay) modalOverlay.classList.remove('open'); }
  window.openBridgeModal = openBridgeModal;
  document.querySelectorAll('.rk-clickable').forEach(function(row){
    row.addEventListener('click', function(){
      openBridgeModal(row.dataset.entity, row.dataset.region, row.dataset.type);
    });
    row.addEventListener('keydown', function(e){
      if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); row.click(); }
    });
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

