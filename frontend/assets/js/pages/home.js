import { STOCKS } from '../config.js';
import { api } from '../api.js';
import { $, esc, fmt, renderHeader } from '../ui.js';

renderHeader('index.html');

// letreiro
$('#tape').innerHTML = [...STOCKS, ...STOCKS].map((s) => (
  `<span><strong>${s.ticker}</strong><span>${s.name}</span><span style="color:#3A3F37">/</span><span>próximo pregão: alta ou baixa?</span></span>`
)).join('');

// barras da janela LSTM
$('#seq').innerHTML = Array.from({ length: 60 }, (_, i) => {
  const h = 28 + ((Math.sin(i * 1.7) + Math.sin(i * 0.43) + 2) / 4) * 72;
  return `<span style="height:${h.toFixed(0)}%;animation-delay:${(i * 0.05).toFixed(2)}s"></span>`;
}).join('');

// ilustração do hero (linha decorativa, não é dado real)
(function heroChart() {
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const pts = [];
  let p = 190;
  for (let i = 0; i < 54; i++) {
    p = Math.max(70, Math.min(255, p + (rnd() - 0.56) * 16));
    pts.push([i * (440 / 53), p]);
  }
  const line = pts.map((q, i) => `${i ? 'L' : 'M'}${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(' ');
  const [lx, ly] = pts[pts.length - 1];
  const tx = 530, ty = ly - 46;
  $('#hero-chart').innerHTML = `
  <svg viewBox="0 0 560 300" style="width:100%;height:auto" role="img" aria-label="Ilustração: linha de preço terminando num cone de previsão para o próximo pregão">
    <defs><linearGradient id="hg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#B9F18C" stop-opacity=".22"/><stop offset="1" stop-color="#B9F18C" stop-opacity="0"/></linearGradient></defs>
    <g stroke="#22261F"><line x1="0" y1="60" x2="560" y2="60"/><line x1="0" y1="130" x2="560" y2="130"/><line x1="0" y1="200" x2="560" y2="200"/><line x1="0" y1="270" x2="560" y2="270"/></g>
    <rect x="140" y="20" width="300" height="262" fill="#8FB8FF" fill-opacity=".06" stroke="#8FB8FF" stroke-opacity=".35" stroke-dasharray="4 5"/>
    <text x="148" y="38" fill="#8FB8FF" font-family="IBM Plex Mono, monospace" font-size="11">lookback = 60</text>
    <path d="${line} L440 300 L0 300 Z" fill="url(#hg)" class="fade-in"/>
    <path d="${line}" pathLength="1" fill="none" stroke="#ECE8DD" stroke-width="2.2" stroke-linejoin="round" class="draw"/>
    <polygon points="${lx},${ly} ${tx},${ty - 30} ${tx},${ty + 30}" fill="#B9F18C" fill-opacity=".16" class="fade-late"/>
    <path d="M${lx} ${ly} L${tx} ${ty}" pathLength="1" fill="none" stroke="#B9F18C" stroke-width="2" class="draw-late"/>
    <circle cx="${lx}" cy="${ly}" r="5" fill="#ECE8DD"/>
    <circle cx="${lx}" cy="${ly}" r="5" fill="#ECE8DD" class="pulse"/>
  </svg>`;
})();

// cards das ações (com último fechamento real, se a API responder)
const grid = $('#stock-grid');
const arrow = '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M5 13L13 5M6 5h7v7" fill="none" stroke="#ECE8DD" stroke-width="1.6" stroke-linecap="round"/></svg>';
grid.innerHTML = STOCKS.map((s) => `
  <a class="stock-card" href="grafico.html?ticker=${s.ticker}" data-tk="${s.ticker}">
    <div class="top"><span>id_stock ${s.id}</span>${arrow}</div>
    <div style="display:flex;flex-direction:column;gap:6px">
      <span class="tk">${s.ticker}</span>
      <span class="nm">${esc(s.name)}</span>
      <span class="px" data-px></span>
      <svg class="spark" viewBox="0 0 200 36" preserveAspectRatio="none" aria-hidden="true" data-spark></svg>
    </div>
  </a>`).join('');

STOCKS.forEach(async (s) => {
  try {
    const data = await api.history(s.ticker);
    // a API serializa os Numeric do SQLAlchemy como string
    const h = data.History.slice(-60).map((x) => ({ ...x, close: Number(x.close) }));
    if (h.length < 2) return;
    const last = h[h.length - 1], prev = h[h.length - 2];
    const chg = (last.close / prev.close - 1) * 100;
    const card = grid.querySelector(`[data-tk="${s.ticker}"]`);
    card.querySelector('[data-px]').innerHTML = `<span>${fmt.money(last.close)}</span><span class="${chg >= 0 ? 'up' : 'down'}">${chg >= 0 ? '▲ +' : '▼ '}${chg.toFixed(2)}%</span><span class="faint">${fmt.short(last.recorded_at)}</span>`;
    const closes = h.map((x) => x.close);
    const mn = Math.min(...closes), mx = Math.max(...closes);
    const d = closes.map((c, i) => `${i ? 'L' : 'M'}${(i * 200 / (closes.length - 1)).toFixed(1)} ${(32 - ((c - mn) / (mx - mn || 1)) * 28).toFixed(1)}`).join(' ');
    card.querySelector('[data-spark]').innerHTML = `<path d="${d}" pathLength="1" fill="none" stroke="${chg >= 0 ? '#B9F18C' : '#FF7A45'}" stroke-width="1.6" class="draw" vector-effect="non-scaling-stroke"/>`;
  } catch {
    /* sem API: os cards ficam só com nome e ticker */
  }
});
