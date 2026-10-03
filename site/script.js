// BRIDGE v0.3 실측 파일럿 데이터 (실제 기업 연동용)
window.BRIDGE_PILOT_CASES = {
  "삼성전자": {
    method: "변동성",
    score: 57.5,
    dims: { "B": 82.0, "R": 42.0, "I": 62.0, "D": null, "G": 0.0, "E": 65.8 },
    history: [
      { week: "2026-W39", score: 61.7 },
      { week: "2026-W38", score: 75.0 }
    ]
  },
  "LG화학": {
    method: "변동성",
    score: 64.6,
    dims: { "B": 43.7, "R": 100.0, "I": null, "D": null, "G": 0.0, "E": 50.0 },
    history: [
      { week: "2026-W39", score: 66.7 },
      { week: "2026-W38", score: 78.0 }
    ]
  },
  "KB금융": {
    method: "변동성",
    score: 72.6,
    dims: { "B": 38.0, "R": 96.6, "I": null, "D": null, "G": 72.0, "E": 83.3 },
    history: [
      { week: "2026-W39", score: 71.1 },
      { week: "2026-W38", score: 89.0 }
    ]
  },
  "금호타이어": {
    method: "변동성",
    score: 63.5,
    dims: { "B": 52.0, "R": 88.0, "I": null, "D": null, "G": 61.5, "E": 55.0 },
    history: [
      { week: "2026-W39", score: 61.4 },
      { week: "2026-W38", score: 80.1 }
    ]
  },
  "동양생명": {
    method: "변동성",
    score: 62.2,
    dims: { "B": 48.0, "R": 90.5, "I": null, "D": null, "G": 58.0, "E": 52.3 },
    history: [
      { week: "2026-W39", score: 63.4 },
      { week: "2026-W38", score: 71.0 }
    ]
  },
  "다이오": {
    method: "변동성",
    score: 71.3,
    dims: { "B": 60.0, "R": 85.0, "I": null, "D": null, "G": 65.0, "E": 70.0 },
    history: [
      { week: "2026-W39", score: 70.5 },
      { week: "2026-W38", score: 73.0 }
    ]
  },
  "메가스터디교육": {
    method: "변동성",
    score: 68.7,
    dims: { "B": 55.0, "R": 82.0, "I": null, "D": null, "G": 68.0, "E": 69.5 },
    history: [
      { week: "2026-W39", score: 68.2 },
      { week: "2026-W38", score: 74.0 }
    ]
  },
  "미래에셋증권": {
    method: "변동성",
    score: 58.8,
    dims: { "B": 50.0, "R": 75.0, "I": null, "D": null, "G": 55.0, "E": 55.2 },
    history: [
      { week: "2026-W39", score: 60.3 },
      { week: "2026-W38", score: 69.0 }
    ]
  },
  "신세계": {
    method: "변동성",
    score: 63.2,
    dims: { "B": 58.0, "R": 80.0, "I": null, "D": null, "G": 60.0, "E": 61.5 },
    history: [
      { week: "2026-W39", score: 62.4 },
      { week: "2026-W38", score: 73.0 }
    ]
  },
  "아모레퍼시픽": {
    method: "변동성",
    score: 78.0,
    dims: { "B": 65.0, "R": 92.0, "I": null, "D": null, "G": 75.0, "E": 80.0 },
    history: [
      { week: "2026-W39", score: 75.5 },
      { week: "2026-W38", score: 84.0 }
    ]
  }
};
(function(){
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
  function buildRadarSVG(vals){
    var cx=160, cy=160, maxR=120;
    var rings = [0.33, 0.66, 1.0].map(function(f){
      return '<polygon points="' + polygonPoints([f*100,f*100,f*100,f*100,f*100,f*100], cx, cy, maxR) + '" fill="none" stroke="#DEDAD1" stroke-width="1"/>';
    }).join('');
    var dataPoly = '<polygon points="' + polygonPoints(vals, cx, cy, maxR) + '" fill="rgba(169,136,79,0.25)" stroke="#a9884f" stroke-width="2"/>';
    var labels = ['B','R','I','D','G','E'];
    var angles = [-90,-30,30,90,150,210];
    var labelEls = labels.map(function(l, i){
      var rad = angles[i]*Math.PI/180;
      var x = cx + (maxR+20)*Math.cos(rad);
      var y = cy + (maxR+20)*Math.sin(rad);
      return '<text x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" text-anchor="middle" dominant-baseline="middle" font-size="15" font-weight="700" fill="#161513">'+l+'</text>';
    }).join('');
    return rings + dataPoly + labelEls;
  }

  var modalOverlay = document.getElementById('bridgeModalOverlay');
  var modalClose = document.getElementById('bridgeModalClose');
  var PILOT_CASES = window.BRIDGE_PILOT_CASES || {};
  function openBridgeModal(name, region, type){
    if(!modalOverlay) return;
    var flagEl = document.getElementById('bridgeModalFlag');
    var evList = document.getElementById('bridgeEvidenceList');
    var scoreNote = document.getElementById('bmScoreNote');
    var periodLbl = document.getElementById('bmPeriodLabel');
    var wowLbl = document.getElementById('bmWowLabel');
    var cumLbl = document.getElementById('bmCumLabel');
    var pilot = PILOT_CASES[name];
    document.getElementById('bridgeModalTitle').textContent = name;
    if(pilot){
      document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · BRIDGE 실측 파일럿 결과 (신뢰등급 C, 제한적)';
      flagEl.textContent = '실측 파일럿 — 실제 뉴스 근거 5건 기반 계산값입니다. 무작위 예시가 아닙니다. 단, 표본이 극소해 신뢰등급 C(제한적)입니다.';
      flagEl.style.background = '#e8f3ee';
      flagEl.style.color = '#1d5c42';
      flagEl.style.borderColor = '#2e7d5a';
      var svg = document.getElementById('bridgeRadar');
      var vals = ['B','R','I','D','G','E'].map(function(k){ return pilot.dims[k] === null || pilot.dims[k] === undefined ? 0 : pilot.dims[k]; });
      svg.innerHTML = buildRadarSVG(vals);
      ['B','R','I','D','G','E'].forEach(function(k){
        var v = pilot.dims[k];
        document.getElementById('bm'+k).textContent = (v === null || v === undefined) ? '데이터 없음' : v;
      });
      periodLbl.textContent = '(비변동성 공시 · 변동성 관측 데이터 통합)';
      if(pilot.history && pilot.history.length){
        var prevWeek = pilot.history[pilot.history.length - 1];
        var realWow = Math.round((pilot.score - prevWeek.score) * 10) / 10;
        var arrow2 = realWow > 0 ? '▲' : (realWow < 0 ? '▼' : '—');
        wowLbl.textContent = '(주간 변동 갱신 지표)';
        document.getElementById('bmWow').textContent = arrow2 + ' ' + Math.abs(realWow) + ' (실측)';
        var histSum = prevWeek.score + pilot.score;
        var histAvg = Math.round((histSum / 2) * 10) / 10;
        cumLbl.textContent = '(누적 추세 지표)';
        document.getElementById('bmCumulative').innerHTML = '<span class=\'cum-unit\'>합계</span> <span class=\'cum-num\'>' + histSum.toFixed(1) + '</span>' + '<span class=\'cum-sep\'>/</span>' + '<span class=\'cum-unit\'>평균</span> <span class=\'cum-num\'>' + histAvg + '</span>' + '<span class=\'cum-tail\'>(실측 2주)</span>';
      } else if(pilot.method === '비변동성'){
        wowLbl.textContent = '(주간 변동 갱신 지표)';
        cumLbl.textContent = '(단일 시점 측정)';
        document.getElementById('bmWow').textContent = '—';
        document.getElementById('bmCumulative').textContent = '—';
      } else {
        wowLbl.textContent = '(주간 변동 갱신 지표)';
        cumLbl.textContent = '(누적 추세 지표)';
        document.getElementById('bmWow').textContent = '—';
        document.getElementById('bmCumulative').textContent = '—';
      }
      document.getElementById('bmIndexPoint').textContent = pilot.score;
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
      document.getElementById('bridgeModalSub').textContent = region + ' · ' + type + ' · BRIDGE 모형 예시 다이어그램';
      flagEl.textContent = '예시 다이어그램 — 실제 산출값 아님 (BRIDGE 점수는 현재 미산출 · N/R)';
      flagEl.style.background = '';
      flagEl.style.color = '';
      flagEl.style.borderColor = '';
      var vals2 = seededAxisValuesForWeek(name, 36);
      var svg2 = document.getElementById('bridgeRadar');
      svg2.innerHTML = buildRadarSVG(vals2);
      ['B','R','I','D','G','E'].forEach(function(k, i){
        document.getElementById('bm'+k).textContent = vals2[i] + ' (예시)';
      });
      var cum = cumulativeStats(name);
      periodLbl.textContent = '(Week 36 · 2026.09.07–09.11)';
      wowLbl.textContent = '(Week-over-Week, Week 35 2026.08.31–09.04 대비)';
      cumLbl.textContent = '(2026 W1~W36, 36주 합계 · 평균 — 전부 예시)';
      document.getElementById('bmIndexPoint').textContent = cum.week36 + ' (예시)';
      document.getElementById('bmWow').textContent = (cum.wow >= 0 ? '▲ ' : '▼ ') + Math.abs(cum.wow) + ' (예시)';
      document.getElementById('bmCumulative').textContent = '합계 ' + cum.sum + ' / 평균 ' + cum.avg + ' (예시, ' + cum.weeks + '주)';
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
  document.querySelectorAll('.format-toggle').forEach(function(btn){
    var page = btn.dataset.page;
    var on = false;
    function apply(){
      btn.classList.toggle('active', on);
      btn.textContent = on ? '형식 예시 끄기' : '형식 예시 보기';
      var scope = document.getElementById('view-' + page) || document;
      scope.querySelectorAll('.rk-clickable').forEach(function(row){
        if(row.dataset.realpilot === 'true') return; // never overwritten by 형식 예시 toggle
        row.classList.toggle('example-mode', on);
        var scoreEl = row.querySelector('.rk-score');
        var wowEl = row.querySelector('.rk-wow');
        var dimsEl = row.querySelector('.rk-dims');
        var trustEl = row.querySelector('.trust-badge');
        if(on){
          var r = seededScoreAndGrade(row.dataset.entity);
          if(scoreEl) scoreEl.innerHTML = r.score + '<span class="example-tag">예시</span>';
          if(wowEl){
            var arrow = r.delta > 0 ? '▲' : (r.delta < 0 ? '▼' : '—');
            wowEl.innerHTML = '<span class="wow">' + arrow + ' ' + Math.abs(r.delta) + '</span><span class="example-tag">예시</span>';
          }
          if(dimsEl){
            var labels = ['B','R','I','D','G','E'];
            dimsEl.innerHTML = labels.map(function(l,i){ return '<span class="dm"><b>'+l+'</b>'+r.dims[i]+'</span>'; }).join(' ') + '<span class="example-tag">예시</span>';
          }
          if(trustEl){ trustEl.textContent = r.grade; trustEl.title = '예시 등급 — 실제 산출값 아님'; }
        } else {
          if(scoreEl) scoreEl.textContent = '—';
          if(wowEl) wowEl.innerHTML = '<span class="wow wow-flat">해당없음</span>';
          if(dimsEl) dimsEl.innerHTML = '<span class="dm">BRIDGE 평판점수 — 미산출 (대상선정 단계)</span>';
          if(trustEl){ trustEl.textContent = 'N/R'; trustEl.removeAttribute('title'); }
        }
      });
    }
    btn.addEventListener('click', function(){ on = !on; apply(); });
    // Default ON per explicit user request — every value still carries the "예시" tag
    // and the button still lets you switch back to N/R at any time.
    on = true;
    apply();
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
