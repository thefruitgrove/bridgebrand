(function () {
  'use strict';
  const AXES = ['B', 'R', 'I', 'D', 'G', 'E'];
  const AXIS_NAMES = { B: '도달', R: '반응', I: '정체성', D: '경험', G: '행동유발', E: '책임·지속' };
  const AXIS_TYPES = {
    B: ['발견 확장형', '공중에게 발견되는 폭이 상대적으로 선명합니다.'],
    R: ['반응 응집형', '관측된 반응의 밀도와 방향이 관계의 중심을 이룹니다.'],
    I: ['정체성 각인형', '반복해서 기억되는 이미지와 정체성 신호가 두드러집니다.'],
    D: ['경험 접점형', '공중이 실제로 마주하는 경험 신호가 관계를 이끕니다.'],
    G: ['행동 전환형', '관심이 참여와 행동으로 이어지는 신호가 선명합니다.'],
    E: ['신뢰 지속형', '책임과 지속에 관한 신호가 관계 구조의 중심입니다.']
  };
  const COLORS = ['#d5ae63', '#77a8d6', '#d47f84'];
  const state = { entries: [], selected: [], mode: 'subscription', pkg: 'PULSE', field: 'ENT', language: '한국어' };
  const packages = {
    subscription: [
      ['PULSE', 3, '주 3회 · 월 스페셜, 수·금 기본'],
      ['INSIGHT', 5, '주 3회 · 월 스페셜, 수·금 일반'],
      ['CONTINUUM', 5, '주 7회 · 월 스페셜, 화~일 일반'],
      ['INTELLIGENCE', 10, '주 3회 · 월·수·금 스페셜'],
      ['SIGNATURE', 10, '주 7회 · 월~일 스페셜']
    ],
    'one-time': [['SNAPSHOT', 1, '1회 · 일반 브리핑'], ['DEEP DIVE', 1, '1회 · 스페셜 브리핑']],
    enterprise: [['ENTERPRISE T100', 100, 'T100 범위·주기·언어 맞춤 설계']]
  };
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>'"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));
  const validAxis = (e, axis) => e.axis_status && e.axis_status[axis] !== 'reference' && Number.isFinite(Number(e.axis_scores && e.axis_scores[axis]));

  fetch('data/latest.json', { cache: 'no-store' }).then((r) => {
    if (!r.ok) throw new Error('공개 데이터를 불러오지 못했습니다.');
    return r.json();
  }).then((data) => {
    state.entries = (data.rankings || []).filter((x) => x.domain === 'ENT' && x.ranking_type === 'T100').sort((a, b) => a.rank - b.rank);
    buildSelects();
  }).catch((err) => {
    $('trioError').hidden = false;
    $('trioError').textContent = err.message + ' 잠시 후 다시 확인해 주세요.';
    $('trioRun').disabled = true;
  });

  function buildSelects() {
    const preferred = ['리센느', '임영웅', '김지원'];
    const defaults = preferred.map((name) => state.entries.find((e) => e.name === name)).filter(Boolean);
    while (defaults.length < 3 && state.entries[defaults.length]) defaults.push(state.entries[defaults.length]);
    ['trioPick1', 'trioPick2', 'trioPick3'].forEach((id, i) => {
      const select = $(id);
      select.innerHTML = state.entries.map((e) => `<option value="${esc(e.external_id)}">${e.rank}. ${esc(e.name)} · ${esc(e.category)}</option>`).join('');
      if (defaults[i]) select.value = defaults[i].external_id;
    });
  }

  $('trioRun').addEventListener('click', () => {
    const ids = ['trioPick1', 'trioPick2', 'trioPick3'].map((id) => $(id).value);
    if (new Set(ids).size !== 3) {
      $('trioError').hidden = false;
      $('trioError').textContent = '서로 다른 세 대상을 선택해 주세요.';
      return;
    }
    $('trioError').hidden = true;
    state.selected = ids.map((id) => state.entries.find((e) => e.external_id === id)).filter(Boolean);
    renderComparison();
  });

  function renderComparison() {
    if (state.selected.length !== 3) return;
    const result = $('trioResult');
    result.hidden = false;
    $('trioDate').textContent = `${state.selected[0].as_of_date} · ENT T100 · 동일 공개 범위`;
    $('trioSummary').innerHTML = state.selected.map((e, i) => {
      const type = relationshipType(e);
      return `<article style="--trio-color:${COLORS[i]}"><small>${i === 0 ? 'MY PICK' : `COMPARE ${i === 1 ? 'A' : 'B'}`}</small><h3>${esc(e.name)}</h3><div><strong>${Number(e.daily_index).toFixed(2)}</strong><span>오늘의 관계 평판 수준</span></div><p>ENT T100 ${e.rank} · 근거 신뢰등급 ${esc(e.trust_grade)}<br>산출 범위 ${e.axes_available}/6축 · ${esc(type[0])}</p></article>`;
    }).join('');
    renderRadar();
    renderGaps();
    $('trioTypes').innerHTML = state.selected.map((e, i) => {
      const type = relationshipType(e);
      return `<div><i style="background:${COLORS[i]}"></i><p><b>${esc(e.name)} · ${esc(type[0])}</b><span>${esc(type[1])}</span></p></div>`;
    }).join('');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function relationshipType(e) {
    const candidates = AXES.filter((a) => validAxis(e, a)).sort((a, b) => Number(e.axis_scores[b]) - Number(e.axis_scores[a]));
    return candidates.length ? AXIS_TYPES[candidates[0]] : ['관측 대기형', '현재 비교 가능한 대상별 축 근거가 충분하지 않습니다.'];
  }

  function point(axisIndex, value, radius, cx, cy) {
    const angle = -Math.PI / 2 + axisIndex * Math.PI / 3;
    const r = radius * value / 100;
    return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r];
  }

  function renderRadar() {
    const svg = $('trioRadar'), cx = 260, cy = 205, radius = 150;
    let html = '';
    [20, 40, 60, 80, 100].forEach((level) => {
      const pts = AXES.map((_, i) => point(i, level, radius, cx, cy).join(',')).join(' ');
      html += `<polygon points="${pts}" fill="none" stroke="rgba(255,255,255,.14)" stroke-width="1"/>`;
    });
    AXES.forEach((a, i) => {
      const end = point(i, 100, radius, cx, cy), label = point(i, 117, radius, cx, cy);
      html += `<line x1="${cx}" y1="${cy}" x2="${end[0]}" y2="${end[1]}" stroke="rgba(255,255,255,.12)"/><text x="${label[0]}" y="${label[1]}" text-anchor="middle" dominant-baseline="middle"><tspan font-weight="800">${a}</tspan><tspan x="${label[0]}" dy="16">${AXIS_NAMES[a]}</tspan></text>`;
    });
    state.selected.forEach((e, idx) => {
      const points = AXES.map((a, i) => validAxis(e, a) ? point(i, Number(e.axis_scores[a]), radius, cx, cy) : null);
      const closed = points.every(Boolean);
      if (closed) html += `<polygon points="${points.map((p) => p.join(',')).join(' ')}" fill="${COLORS[idx]}22" stroke="${COLORS[idx]}" stroke-width="3"/>`;
      else points.forEach((p, i) => { const n = points[(i + 1) % 6]; if (p && n) html += `<line x1="${p[0]}" y1="${p[1]}" x2="${n[0]}" y2="${n[1]}" stroke="${COLORS[idx]}" stroke-width="3"/>`; });
      points.forEach((p) => { if (p) html += `<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="${COLORS[idx]}"/>`; });
    });
    svg.innerHTML = html;
  }

  function renderGaps() {
    const gaps = AXES.map((axis) => {
      const vals = state.selected.filter((e) => validAxis(e, axis)).map((e) => ({ name: e.name, value: Number(e.axis_scores[axis]) }));
      if (vals.length < 2) return null;
      vals.sort((a, b) => b.value - a.value);
      return { axis, gap: vals[0].value - vals[vals.length - 1].value, high: vals[0], low: vals[vals.length - 1], count: vals.length };
    }).filter(Boolean).sort((a, b) => b.gap - a.gap).slice(0, 2);
    $('trioGaps').innerHTML = gaps.length ? gaps.map((g) => `<div class="trio-gap"><b>${g.axis} · ${AXIS_NAMES[g.axis]}</b><strong>${g.gap.toFixed(1)}p 차이</strong><p>${esc(g.high.name)} ${g.high.value.toFixed(1)} ↔ ${esc(g.low.name)} ${g.low.value.toFixed(1)}${g.count < 3 ? ' · 비교 가능 2개 대상' : ''}</p></div>`).join('') : '<p>현재 세 대상에서 서로 비교 가능한 축 근거가 충분하지 않습니다.</p>';
  }

  $('trioShare').addEventListener('click', () => {
    if (!state.selected.length) return;
    const canvas = document.createElement('canvas'); canvas.width = 1200; canvas.height = 630;
    const c = canvas.getContext('2d'); c.fillStyle = '#0d141d'; c.fillRect(0, 0, 1200, 630);
    c.fillStyle = '#d5ae63'; c.font = '700 24px sans-serif'; c.fillText('BRIDGE TRIO · ENT BETA', 70, 75);
    c.fillStyle = '#f4f1ea'; c.font = '700 54px serif'; c.fillText('세 개의 관계 신호를 발견하다.', 70, 145);
    state.selected.forEach((e, i) => { const x = 70 + i * 370; c.fillStyle = COLORS[i]; c.fillRect(x, 210, 8, 250); c.fillStyle = '#f4f1ea'; c.font = '700 34px sans-serif'; c.fillText(e.name, x + 28, 255); c.font = '700 62px serif'; c.fillText(Number(e.daily_index).toFixed(2), x + 28, 340); c.fillStyle = '#aeb7c0'; c.font = '22px sans-serif'; c.fillText(relationshipType(e)[0], x + 28, 390); c.fillText(`산출 ${e.axes_available}/6축 · 신뢰 ${e.trust_grade}`, x + 28, 430); });
    c.fillStyle = '#87919a'; c.font = '18px sans-serif'; c.fillText('인기투표가 아닌 동일 날짜 공개자료 기반 관계 구조 비교 · bridgebrand.co.kr', 70, 570);
    canvas.toBlob((blob) => {
      const file = new File([blob], 'bridge-trio-ent.png', { type: 'image/png' });
      if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) navigator.share({ title: 'BRIDGE TRIO', files: [file] }).catch(() => {});
      else { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = file.name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000); }
    }, 'image/png');
  });

  function bindSingleChoice(id, key) {
    $(id).addEventListener('click', (ev) => { const b = ev.target.closest('button[data-value]'); if (!b) return; [...$(id).querySelectorAll('button')].forEach((x) => x.classList.remove('active')); b.classList.add('active'); state[key] = b.dataset.value; if (key === 'mode') { state.pkg = packages[state.mode][0][0]; renderPackages(); } renderReview(); });
  }
  bindSingleChoice('modeOptions', 'mode'); bindSingleChoice('fieldOptions', 'field'); bindSingleChoice('languageOptions', 'language');

  function renderPackages() {
    $('packageOptions').innerHTML = packages[state.mode].map((p) => `<button type="button" data-value="${p[0]}" class="${p[0] === state.pkg ? 'active' : ''}"><b>BRIDGE ${p[0]}</b><span>${p[2]}</span></button>`).join('');
    renderTargetInputs();
  }
  $('packageOptions').addEventListener('click', (ev) => { const b = ev.target.closest('button[data-value]'); if (!b) return; state.pkg = b.dataset.value; renderPackages(); renderReview(); });

  function currentPackage() { return packages[state.mode].find((p) => p[0] === state.pkg) || packages[state.mode][0]; }
  function renderTargetInputs() {
    const max = currentPackage()[1], shown = max === 100 ? 1 : max;
    $('targetLimit').textContent = max === 100 ? '대상 범위 협의' : `최대 ${max}개`;
    $('builderTargets').innerHTML = Array.from({ length: shown }, (_, i) => `<input type="text" maxlength="50" placeholder="${i + 1}. 대상명${i === 0 ? ' (필수)' : ''}" aria-label="분석 대상 ${i + 1}">`).join('');
    $('builderTargets').addEventListener('input', renderReview);
  }
  function renderReview() {
    const p = currentPackage(), modeLabel = state.mode === 'subscription' ? '정기 관측' : state.mode === 'one-time' ? '단건 분석' : '맞춤 분석 문의';
    const targets = [...$('builderTargets').querySelectorAll('input')].map((i) => i.value.trim()).filter(Boolean);
    $('reviewPackage').textContent = `BRIDGE ${p[0]}`; $('reviewMode').textContent = modeLabel; $('reviewField').textContent = state.field; $('reviewTargets').textContent = targets.length ? targets.join(', ') : '입력 대기'; $('reviewLanguage').textContent = state.language; $('reviewDetail').textContent = p[2];
    const q = new URLSearchParams({ service: `BRIDGE ${p[0]}`, mode: modeLabel, field: state.field, targets: targets.join(', '), language: state.language });
    $('intelContact').href = `contact.html?${q.toString()}`;
  }
  renderPackages(); renderReview();
})();
