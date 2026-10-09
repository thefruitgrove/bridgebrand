(function(){
  // Published Supabase snapshot overlay. The generated HTML remains a safe
  // fallback, while a valid daily snapshot replaces visible rank fields.
  (function loadBridgeDailySnapshot(){
    var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    var domain = page === 'cpr.html' ? 'CPR' : page === 'gov.html' ? 'GOV' :
      page === 'uni.html' ? 'UNI' : page === 'star.html' ? 'ENT' : null;
    fetch('data/latest.json', {cache:'no-store'}).then(function(res){
      if(!res.ok) throw new Error('snapshot unavailable');
      return res.json();
    }).then(function(payload){
      var rows = (payload.rankings || []).filter(function(r){ return r.ranking_type === 'T100'; });
      var byKey = {};
      rows.forEach(function(r){ byKey[r.domain + '|' + r.name] = r; });
      if(domain){
        document.querySelectorAll('.rk-row').forEach(function(el){
          var nameEl = el.querySelector('.nm');
          if(!nameEl) return;
          var rec = byKey[domain + '|' + nameEl.textContent.trim()];
          if(!rec) return;
          var rankEl = el.querySelector('.rk-num');
          var scoreEl = el.querySelector('.rk-score');
          var wowEl = el.querySelector('.rk-wow');
          var trustEl = el.querySelector('.rk-trust');
          if(rankEl) rankEl.textContent = String(rec.rank).padStart(2, '0');
          if(scoreEl) scoreEl.textContent = Number(rec.score).toFixed(1);
          if(wowEl){
            var d = Number(rec.rank_change || 0);
            wowEl.textContent = d > 0 ? '▲ ' + d : d < 0 ? '▼ ' + Math.abs(d) : '— 0';
          }
          if(trustEl) trustEl.innerHTML = '<span class="trust-badge grade-' + rec.trust_grade + '">' + rec.trust_grade + '</span>';
          el.setAttribute('data-live-date', payload.asOfDate || '');
        });
      }
      document.querySelectorAll('#tickerTrack > span').forEach(function(el){
        var tagEl = el.querySelector('b');
        if(!tagEl) return;
        var tag = tagEl.textContent.trim();
        var name = '';
        el.childNodes.forEach(function(node){ if(node.nodeType === 3 && !name) name = node.textContent.trim(); });
        var rec = byKey[tag + '|' + name];
        if(!rec) return;
        var score = el.querySelector('.t-score, .t-flat');
        if(score){ score.className = 't-score'; score.textContent = Number(rec.score).toFixed(1); }
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
  function seededAxisValues(name){
    var seed = hashSeed(name);
    var vals = [];
    ['B','R','I','D','G','E'].forEach(function(k, idx){
      var v = 45 + ((seed >> (idx*4)) % 50); // 45~94 range, deterministic per name+axis
      vals.push(v);
    });
    return vals;
  }
  // ---- 36-week series (BETA 2026 전체 구간, Week 1~36): deterministic per name+week,
  // never real data — used only to demonstrate the WoW/누적 포인트 UI mechanics.
  function seededAxisValuesForWeek(name, week){
    var seed = hashSeed(name + '-w' + week);
    var vals = [];
    ['B','R','I','D','G','E'].forEach(function(k, idx){
      var v = 45 + ((seed >> (idx*4)) % 50);
      vals.push(v);
    });
    return vals;
  }
  function weeklyIndexPoint(name, week){
    var vals = seededAxisValuesForWeek(name, week);
    return vals.reduce(function(a,b){ return a+b; }, 0) / vals.length;
  }
  function seededSeries36(name){
    var series = [];
    for(var w=1; w<=36; w++){ series.push(weeklyIndexPoint(name, w)); }
    return series;
  }
  function cumulativeStats(name){
    var series = seededSeries36(name);
    var sum = series.reduce(function(a,b){ return a+b; }, 0);
    var avg = sum / series.length;
    var wow = series[35] - series[34]; // Week36 - Week35
    return {
      week36: series[35].toFixed(1),
      wow: Math.round(wow*10)/10,
      sum: sum.toFixed(1),
      avg: avg.toFixed(1),
      weeks: series.length
    };
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
      document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · BRIDGE 실측 파일럿 결과 (신뢰등급 C, 제한적)';
      flagEl.textContent = '실측 파일럿 — 실제 뉴스 근거 5건 기반 계산값입니다. 무작위 예시가 아닙니다. 단, 표본이 극소해 신뢰등급 C(제한적)입니다.';
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
      // [2026-10] 5단 지표 — 예시 표현 제거, 전주·누적 실측 표기
      document.getElementById('bmIndexPoint').textContent = pilot.score;
      var _v3el = document.getElementById('bmV3Score');
      if(_v3el){ _v3el.textContent = (pilot.v3_score != null ? pilot.v3_score : '—'); }
      if(pilot.history && pilot.history.length){
        var prevWeek = pilot.history[pilot.history.length - 1];
        var prevScore = prevWeek.score;
        var realWow = Math.round((pilot.score - prevScore) * 10) / 10;
        var arrow2 = realWow > 0 ? '▲' : (realWow < 0 ? '▼' : '—');
        // 2) 전주 지표
        document.getElementById('bmLastWeek').textContent = (prevScore != null ? prevScore : '—');
        // 3) WoW (실측 표기 제거)
        document.getElementById('bmWow').textContent = arrow2 + ' ' + Math.abs(realWow);
        // 5) 누적 (실측→주간수 표기)
        var weeksN = pilot.history.length + 1;
        var allScores = pilot.history.map(function(h){return h.score;}).concat([pilot.score]);
        var histSum = allScores.reduce(function(a,b){return a+b;}, 0);
        var histAvg = Math.round((histSum / weeksN) * 10) / 10;
        document.getElementById('bmCumulative').innerHTML = '<span class=\'cum-unit\'>합계</span> <span class=\'cum-num\'>' + histSum.toFixed(1) + '</span><span class=\'cum-sep\'>/</span><span class=\'cum-unit\'>평균</span> <span class=\'cum-num\'>' + histAvg + '</span><span class=\'cum-tail\'>(' + weeksN + '주간)</span>';
      } else {
        // 전주 데이터 아직 없음 — 이번 주가 첫 기록
        document.getElementById('bmLastWeek').textContent = '—';
        document.getElementById('bmWow').textContent = '— (첫 주)';
        document.getElementById('bmCumulative').innerHTML = '<span class=\'cum-unit\'>합계</span> <span class=\'cum-num\'>' + pilot.score + '</span><span class=\'cum-sep\'>/</span><span class=\'cum-unit\'>평균</span> <span class=\'cum-num\'>' + pilot.score + '</span><span class=\'cum-tail\'>(1주간)</span>';
      }
      var isNonVolatile = pilot.method === '비변동성';
      scoreNote.textContent = '여론의 소음이 아닌, 검증된 공식 데이터와 실제 관측값만으로 구성된 지수입니다. 유효한 근거가 확보된 축만 투명하게 계산하며, 아직 확인되지 않은 데이터는 투명성을 위해 N/A로 남겨두었습니다.';
      var evItems = document.getElementById('bridgeEvidenceItems');
      var dims = pilot.dims || {};
      var evLines = [];
      // 비변동성(공시·규모) 축이 있으면 요약
      var nonvolAxes = [];
      if(dims.B !== null && dims.B !== undefined) nonvolAxes.push('도달(B)');
      if(dims.E !== null && dims.E !== undefined) nonvolAxes.push('책임·지속(E)');
      if(nonvolAxes.length){
        evLines.push('<div class="evidence-item"><b>[비변동성]</b> 공식 공시·규모 데이터를 ' + nonvolAxes.join('·') + ' 축에 반영</div>');
      }
      // 변동성(반응/사건) 축
      if(dims.R !== null && dims.R !== undefined){
        var rTxt = (dims.R >= 100) ? '최근 탐색 기간 내 유의미한 위기·논란 신호 미발견' : '최근 탐색 기간 내 관측된 반응·사건을 반영';
        evLines.push('<div class="evidence-item"><b>[변동성]</b> ' + rTxt + '</div>');
      }
      if(dims.G !== null && dims.G !== undefined){
        evLines.push('<div class="evidence-item"><b>[변동성]</b> 전년 대비 행동 변화(경쟁률·이용 등)를 행동유발(G) 축에 반영</div>');
      }
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
      if(pilot.revision_note){
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
      document.getElementById('bmLastWeek').textContent = 'N/R';
      document.getElementById('bmWow').textContent = 'N/R';
      document.getElementById('bmV3Score').textContent = 'N/R';
      document.getElementById('bmCumulative').textContent = 'N/R';
      scoreNote.textContent = '';
      evList.style.display = 'none';
    }
    modalOverlay.classList.add('open');
  }
  function closeBridgeModal(){ if(modalOverlay) modalOverlay.classList.remove('open'); }
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

  // ---- Format-example toggle: fills score/WoW/trust cells with clearly-marked
  // illustrative values (never real). Reuses the same seeded-value logic as the
  // BRIDGE sample diagram modal, so a row's inline example matches its modal example.
  function seededScoreAndGrade(name){
    var cum = cumulativeStats(name);
    var vals = seededAxisValuesForWeek(name, 36);
    var avg = parseFloat(cum.week36);
    var grade = avg >= 85 ? 'A' : avg >= 70 ? 'B' : avg >= 55 ? 'C' : 'D';
    return { score: cum.week36, delta: cum.wow, grade: grade, dims: vals };
  }
  // [2026-10] 형식 예시 토글 제거 — 항상 실제 데이터 표시

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
