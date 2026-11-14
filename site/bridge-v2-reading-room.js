/* BRIDGEBRAND reading-room picture direction only.
   The six stages, reports, ranks and underlying published JSON remain under
   briefing.js; this file never reads/writes index scores or account data. */
(() => {
  'use strict';
  const photo = document.getElementById('bridgePulsePhoto');
  if (!photo) return;
  const domain = new URLSearchParams(location.search).get('field');
  const images = {
    CPR: { src: 'img/hero_cpr.jpg', label: '기업 분야의 관계 환경을 표현한 편집 이미지' },
    GOV: { src: 'img/hero_gov.jpg', label: '공공 분야의 관계 환경을 표현한 편집 이미지' },
    UNI: { src: 'img/hero_uni.jpg', label: '대학 분야의 관계 환경을 표현한 편집 이미지' },
    ENT: { src: 'img/hero_star.jpg', label: '인물 분야의 관계 환경을 표현한 편집 이미지' }
  };
  const selected = images[domain] || images.CPR;
  photo.src = selected.src;
  photo.alt = selected.label;
  const caption = document.getElementById('bridgePulsePhotoCaption');
  if (caption) caption.textContent = 'EDITORIAL FIELD STUDY / ' + (images[domain] ? domain : 'BRIDGE');
})();
