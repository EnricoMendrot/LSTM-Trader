// Gráfico de preço em SVG puro: linha ou candles, volume, projeção D+1 e crosshair.
import { fmt } from './ui.js';

const UP = '#B9F18C';
const DOWN = '#FF7A45';
const VB_W = 960;
const VB_H = 400;
const PLOT_W = 830;     // largura da área histórica
const LEFT = 12;
const TOP = 14;
const PLOT_H = 296;     // altura da área de preço
const VOL_BASE = 376;   // base das barras de volume
const VOL_H = 40;
const PROJ_X = 906;     // x do ponto previsto (coluna D+1)

/**
 * @param {HTMLElement} host
 * @param {{date:Date,o:number,h:number,l:number,c:number,v:number}[]} bars
 * @param {{mode?:'line'|'candles', prediction?:{up:boolean, final:number, conf:number, label:string}}} opts
 */
export function renderPriceChart(host, bars, { mode = 'line', prediction = null } = {}) {
  const n = bars.length;
  if (n < 2) { host.innerHTML = ''; return; }

  const last = bars[n - 1];
  let mn = Infinity, mx = -Infinity, vmax = 0;
  for (const b of bars) { mn = Math.min(mn, b.l); mx = Math.max(mx, b.h); vmax = Math.max(vmax, b.v); }

  // preço-alvo apenas visual: distância proporcional à força do sinal
  let tPrice = null;
  if (prediction) {
    const strength = 0.008 + Math.abs(prediction.final - 0.5) * 0.08;
    tPrice = last.c * (1 + (prediction.up ? strength : -strength));
    mn = Math.min(mn, tPrice); mx = Math.max(mx, tPrice);
  }
  const pad = (mx - mn) * 0.1 || 1;
  mn -= pad; mx += pad;

  const X = (i) => LEFT + i * (PLOT_W / (n - 1));
  const Y = (v) => TOP + ((mx - v) / (mx - mn)) * PLOT_H;
  const cw = Math.max(1.2, (PLOT_W / n) * 0.62);
  const f1 = (v) => v.toFixed(1);

  // grade
  let grid = '';
  for (let g = 0; g < 5; g++) {
    const v = mx - (mx - mn) * (g / 4);
    const y = Y(v);
    grid += `<line x1="0" x2="852" y1="${f1(y)}" y2="${f1(y)}" stroke="#22261F"/>`
      + `<text x="4" y="${f1(y - 5)}" fill="#6F7269" font-family="IBM Plex Mono, monospace" font-size="11">${v.toFixed(2)}</text>`;
  }

  // volume
  let vols = '';
  for (let i = 0; i < n; i++) {
    const b = bars[i];
    const h = (b.v / vmax) * VOL_H;
    vols += `<rect x="${f1(X(i) - cw / 2)}" y="${f1(VOL_BASE - h)}" width="${f1(cw)}" height="${f1(h)}" fill="${b.c >= b.o ? UP : DOWN}" fill-opacity=".45" class="grow"/>`;
  }

  // série
  let series = '';
  if (mode === 'candles') {
    for (let i = 0; i < n; i++) {
      const b = bars[i];
      const c = b.c >= b.o ? UP : DOWN;
      const top = Y(Math.max(b.o, b.c));
      const bot = Y(Math.min(b.o, b.c));
      series += `<line x1="${f1(X(i))}" x2="${f1(X(i))}" y1="${f1(Y(b.h))}" y2="${f1(Y(b.l))}" stroke="${c}"/>`
        + `<rect x="${f1(X(i) - cw / 2)}" y="${f1(top)}" width="${f1(cw)}" height="${f1(Math.max(1, bot - top))}" fill="${c}" class="grow"/>`;
    }
  } else {
    const line = bars.map((b, i) => `${i ? 'L' : 'M'}${f1(X(i))} ${f1(Y(b.c))}`).join(' ');
    series = `<path d="${line} L${f1(X(n - 1))} 326 L${LEFT} 326 Z" fill="url(#lt-area)" class="fade-in"/>`
      + `<path d="${line}" pathLength="1" fill="none" stroke="#ECE8DD" stroke-width="2" stroke-linejoin="round" class="draw"/>`;
  }

  // projeção
  const lX = X(n - 1), lY = Y(last.c);
  let proj = '';
  if (prediction) {
    const col = prediction.up ? UP : DOWN;
    const tY = Y(tPrice);
    const spread = 18 + (1 - prediction.conf) * 90;
    proj = `<polygon points="${f1(lX)},${f1(lY)} ${PROJ_X},${f1(tY - spread)} ${PROJ_X},${f1(tY + spread)}" fill="${col}" fill-opacity=".2" class="fade-late"/>`
      + `<path d="M${f1(lX)} ${f1(lY)} L${PROJ_X} ${f1(tY)}" pathLength="1" fill="none" stroke="${col}" stroke-width="2.2" class="draw-late"/>`
      + `<circle cx="${PROJ_X}" cy="${f1(tY)}" r="5" fill="${col}" class="fade-late"/>`
      + `<text x="${PROJ_X}" y="${f1(Math.max(44, tY - spread - 10))}" text-anchor="middle" fill="${col}" font-family="IBM Plex Mono, monospace" font-size="12" font-weight="600" class="fade-late">${prediction.up ? 'ALTA' : 'BAIXA'}</text>`;
  }

  // rótulos do eixo x
  let xl = '';
  for (const f of [0, 0.25, 0.5, 0.75, 1]) {
    const i = Math.round(f * (n - 1));
    const x = Math.min(820, Math.max(28, X(i)));
    xl += `<text x="${f1(x)}" y="396" fill="#6F7269" font-family="IBM Plex Mono, monospace" font-size="11" text-anchor="middle">${fmt.short(bars[i].date)}</text>`;
  }

  host.innerHTML = `
  <div class="chart-wrap" style="position:relative">
    <svg viewBox="0 0 ${VB_W} ${VB_H}" style="width:100%;height:auto" role="img" aria-label="Gráfico de preço${prediction ? ' com previsão para o próximo pregão' : ''}">
      <defs><linearGradient id="lt-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ECE8DD" stop-opacity=".16"/><stop offset="1" stop-color="#ECE8DD" stop-opacity="0"/></linearGradient></defs>
      <rect x="852" y="10" width="108" height="316" fill="#1A1D18"/>
      <text x="${PROJ_X}" y="30" text-anchor="middle" fill="#9A9C92" font-family="IBM Plex Mono, monospace" font-size="11">D+1</text>
      ${grid}${vols}${series}${proj}
      <circle cx="${f1(lX)}" cy="${f1(lY)}" r="4.5" fill="#ECE8DD"/>
      <circle cx="${f1(lX)}" cy="${f1(lY)}" r="4.5" fill="#ECE8DD" class="pulse"/>
      ${xl}
      <g class="xh" style="display:none;pointer-events:none">
        <line class="xh-v" y1="10" y2="376" stroke="#6F7269" stroke-dasharray="3 4"/>
        <circle class="xh-d" r="4" fill="#0F110E" stroke="#ECE8DD" stroke-width="2"/>
      </g>
      <rect class="hit" x="0" y="0" width="852" height="${VB_H}" fill="transparent"/>
    </svg>
    <div class="tip" role="status" style="position:absolute;top:8px;display:none;pointer-events:none;background:#0F110E;border:1px solid #3A3F37;border-radius:12px;padding:10px 12px;font-family:var(--mono);font-size:12px;line-height:1.6;white-space:nowrap"></div>
  </div>`;

  // crosshair
  const svg = host.querySelector('svg');
  const hit = host.querySelector('.hit');
  const xh = host.querySelector('.xh');
  const v = host.querySelector('.xh-v');
  const d = host.querySelector('.xh-d');
  const tip = host.querySelector('.tip');

  const move = (ev) => {
    const r = svg.getBoundingClientRect();
    const px = ((ev.clientX - r.left) / r.width) * VB_W;
    const i = Math.max(0, Math.min(n - 1, Math.round(((px - LEFT) / PLOT_W) * (n - 1))));
    const b = bars[i];
    const x = X(i), y = Y(b.c);
    xh.style.display = '';
    v.setAttribute('x1', x); v.setAttribute('x2', x);
    d.setAttribute('cx', x); d.setAttribute('cy', y);
    const chg = i > 0 ? (b.c / bars[i - 1].c - 1) * 100 : 0;
    tip.innerHTML = `<div style="color:#9A9C92">${fmt.date(b.date)}</div>`
      + `<div>F ${b.c.toFixed(2)} <span style="color:${chg >= 0 ? UP : DOWN}">${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%</span></div>`
      + `<div style="color:#9A9C92">A ${b.o.toFixed(2)} · Mx ${b.h.toFixed(2)} · Mn ${b.l.toFixed(2)}</div>`;
    tip.style.display = 'block';
    const left = (x / VB_W) * r.width;
    tip.style.left = (left > r.width / 2 ? left - tip.offsetWidth - 14 : left + 14) + 'px';
  };
  hit.addEventListener('pointermove', move);
  hit.addEventListener('pointerleave', () => { xh.style.display = 'none'; tip.style.display = 'none'; });
}

// Anel de probabilidade (P(alta))
export function ring(value, color, size = 132) {
  const r = 52, C = 2 * Math.PI * r;
  return `<svg width="${size}" height="${size}" viewBox="0 0 132 132" role="img" aria-label="Probabilidade de alta ${(value * 100).toFixed(1)}%">
    <circle cx="66" cy="66" r="${r}" fill="none" stroke="#262A24" stroke-width="12"/>
    <circle cx="66" cy="66" r="${r}" fill="none" stroke="${color}" stroke-width="12" stroke-linecap="round"
      stroke-dasharray="${(value * C).toFixed(1)} ${C.toFixed(1)}" transform="rotate(-90 66 66)" class="ring-arc"/>
    <line x1="66" y1="8" x2="66" y2="20" stroke="#6F7269" stroke-width="2"/>
    <text x="66" y="66" text-anchor="middle" fill="#ECE8DD" font-family="IBM Plex Mono, monospace" font-size="26" font-weight="600">${Math.round(value * 100)}%</text>
    <text x="66" y="88" text-anchor="middle" fill="#9A9C92" font-family="IBM Plex Mono, monospace" font-size="11">P(alta)</text>
  </svg>`;
}
