"use strict";
// 후보 화면과 움직이는 카드가 같은 금박 장식과 이름 표기를 사용한다.
(() => {
  let sequence = 0;
  const curl = '<path d="M5 31V5h26M9 26V9h17M11 20c10 0 4-11 12-11s7 10 1 10c-6 0-1-5-5-5s-3 12-8 12M5 31c3-6 9-3 10-1"/><circle cx="5" cy="5" r="2" fill="currentColor" stroke="none"/>';
  function margins() {
    return ['bl','br'].map(position => `<svg class="gilt-margin ${position}" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width=".85" aria-hidden="true">${curl}</svg>`).join('');
  }
  function overlay() {
    const id = `gilt-foil-${++sequence}`;
    // 별·동전 등 카드의 상징과 혼동하지 않도록 덩굴과 가는 선만 겹친다.
    const corner = '<path d="M13 81V24Q13 13 24 13H69M21 68V31Q21 21 31 21H56M14 55c20-2 4-34 25-34 20 0 20 21 6 21-12 0-7-12-1-12M27 53c-2-8 7-17 14-12 7 6-1 17-9 14M13 80c5-15 18-16 23-12 7 5 1 14-6 8M43 14c-5 11 7 13 17 8"/><path d="M13 49c-9-9-7-18 0-23 7 8 7 15 0 23ZM41 14c8-8 17-7 24 0-8 6-16 7-24 0Z" fill="currentColor" fill-opacity=".6" stroke="none"/>';
    const corners = [`<g>${corner}</g>`,`<g transform="translate(600 0) scale(-1 1)">${corner}</g>`,`<g transform="translate(0 900) scale(1 -1)">${corner}</g>`,`<g transform="translate(600 900) scale(-1 -1)">${corner}</g>`].join('');
    return `<svg class="gilt-art-overlay" viewBox="0 0 600 900" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffe4a0"/><stop offset=".32" stop-color="#ae833c"/><stop offset=".56" stop-color="#efd195"/><stop offset="1" stop-color="#bd944c"/></linearGradient></defs><g fill="none" stroke="#49351a" stroke-opacity=".38" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="7" width="586" height="886" rx="3"/></g><g fill="none" stroke="url(#${id})" color="#e6c67e" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="7" width="586" height="886" rx="3"/>${corners}</g></svg>`;
  }
  function title(value) {
    return value.toLowerCase().replace(/\b\w/g, c => c.toUpperCase()).replace(/\bOf\b/g, 'of');
  }
  function back(src) {
    return `<div class="gilt-back-print" aria-hidden="true"><div class="gilt-back-half"><img src="${src}" alt=""></div><div class="gilt-back-half"><img src="${src}" alt=""></div></div>`;
  }
  window.LEMON_GILT = Object.freeze({ margins, overlay, title, back });
})();
