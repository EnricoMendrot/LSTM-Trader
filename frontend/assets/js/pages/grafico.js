import { STOCKS, stockByTicker } from '../config.js';
import { api, auth, predictionLog } from '../api.js';
import { $, esc, fmt, parseDate, isUp, renderHeader, errorNotice } from '../ui.js';
import { renderPriceChart, ring } from '../chart.js';

renderHeader('grafico.html');

const RANGES = [['1M', 22], ['3M', 66], ['6M', 126], ['1A', 252], ['5A', 1260]];
const MODES = [['line', 'Linha'], ['candles', 'Candles']];

const params = new URLSearchParams(location.search);
const state = {
  ticker: stockByTicker(params.get('ticker'))?.ticker || 'NVDA',
  range: '3M',
  mode: 'line',
  bars: null,          // histórico completo da ação atual
  loadingPredict: false,
  predictError: null,
};
const cache = new Map();

// ---------- abas ----------
function renderTabs() {
  $('#tabs').innerHTML = STOCKS.map((s) => {
    const p = predictionLog.latest(s.id);
    const sub = p
      ? `<span class="sub" style="${s.ticker === state.ticker ? '' : `color:${isUp(p) ? 'var(--up)' : 'var(--down)'}`}">${isUp(p) ? '▲ alta' : '▼ baixa'} ${fmt.pct(p.final_forecast)}</span>`
      : `<span class="sub">${esc(s.name)}</span>`;
    return `<button class="ticker-tab" role="tab" type="button" aria-selected="${s.ticker === state.ticker}" data-tk="${s.ticker}"><span class="tk">${s.ticker}</span>${sub}</button>`;
  }).join('');
}
$('#tabs').addEventListener('click', (e) => {
  const b = e.target.closest('[data-tk]');
  if (!b || b.dataset.tk === state.ticker) return;
  state.ticker = b.dataset.tk;
  state.predictError = null;
  history.replaceState(null, '', `?ticker=${state.ticker}`);
  load();
});

// ---------- controles ----------
function renderControls() {
  $('#ranges').innerHTML = RANGES.map(([k]) => `<button class="pill" type="button" aria-pressed="${k === state.range}" data-range="${k}">${k}</button>`).join('');
  $('#modes').innerHTML = MODES.map(([k, l]) => `<button class="pill" type="button" aria-pressed="${k === state.mode}" data-mode="${k}">${l}</button>`).join('');
}
$('#ranges').addEventListener('click', (e) => {
  const b = e.target.closest('[data-range]');
  if (b) { state.range = b.dataset.range; renderControls(); renderChart(); }
});
$('#modes').addEventListener('click', (e) => {
  const b = e.target.closest('[data-mode]');
  if (b) { state.mode = b.dataset.mode; renderControls(); renderChart(); }
});

// ---------- dados ----------
async function fetchBars(ticker) {
  if (cache.has(ticker)) return cache.get(ticker);
  const data = await api.history(ticker);
  const bars = data.History
    .map((h) => ({ date: parseDate(h.recorded_at), o: +h.open_price, h: +h.price_high, l: +h.price_low, c: +h.close, v: +h.volume }))
    .sort((a, b) => a.date - b.date);
  const result = { company: data['Company Name'], bars };
  cache.set(ticker, result);
  return result;
}

async function load() {
  const stock = stockByTicker(state.ticker);
  renderTabs();
  $('#stock-title').textContent = stock.ticker;
  $('#stock-name').textContent = stock.name;
  $('#last-close').textContent = '';
  $('#last-chg').textContent = '';
  $('#chart').innerHTML = '<div class="skeleton" style="aspect-ratio:960/400"></div>';
  $('#table-title').textContent = `Últimos pregões · ${stock.ticker}`;
  renderPredict();
  try {
    const { company, bars } = await fetchBars(stock.ticker);
    if (stock.ticker !== state.ticker) return; // trocou de aba no meio
    state.bars = bars;
    $('#stock-name').textContent = `${company} · NASDAQ`;
    renderChart();
    renderTable();
  } catch (err) {
    state.bars = null;
    $('#chart').innerHTML = errorNotice(err);
    $('#kpis').innerHTML = '';
    $('#rows').innerHTML = '';
  }
}

// ---------- gráfico ----------
function currentPrediction() {
  const p = predictionLog.latest(stockByTicker(state.ticker).id);
  if (!p) return null;
  return { up: isUp(p), final: p.final_forecast, conf: p.confidence_score, target: p.target_date };
}

function renderChart() {
  if (!state.bars) return;
  const n = RANGES.find(([k]) => k === state.range)[1];
  const bars = state.bars.slice(-n);
  const last = bars[bars.length - 1];
  const prev = bars[bars.length - 2] || last;
  const chg = (last.c / prev.c - 1) * 100;

  $('#last-close').textContent = fmt.money(last.c);
  const chgEl = $('#last-chg');
  chgEl.textContent = `${chg >= 0 ? '▲ +' : '▼ '}${chg.toFixed(2)}%`;
  chgEl.className = `mono ${chg >= 0 ? 'up' : 'down'}`;

  const pred = currentPrediction();
  renderPriceChart($('#chart'), bars, { mode: state.mode, prediction: pred });

  const lg = $('#legend-proj');
  lg.hidden = !pred;
  if (pred) {
    $('#legend-proj-sw').style.borderTopColor = pred.up ? 'var(--up)' : 'var(--down)';
    $('#legend-proj-txt').textContent = `previsão D+1 (${fmt.date(pred.target)})`;
  }

  const hi = Math.max(...bars.map((b) => b.h));
  const lo = Math.min(...bars.map((b) => b.l));
  $('#kpis').innerHTML = [
    ['Abertura', fmt.money(last.o)],
    ['Máx. do período', fmt.money(hi)],
    ['Mín. do período', fmt.money(lo)],
    ['Volume', fmt.vol(last.v)],
  ].map(([l, v]) => `<div class="stat"><span class="label">${l}</span><span class="value">${v}</span></div>`).join('');
  $('#src').textContent = `Último pregão na base: ${fmt.date(last.date)} · GET /dashboard/history/${state.ticker}`;
}

function renderTable() {
  $('#rows').innerHTML = state.bars.slice(-8).reverse().map((b) => `
    <tr>
      <td class="muted">${fmt.date(b.date)}</td>
      <td>${b.o.toFixed(2)}</td><td>${b.h.toFixed(2)}</td><td>${b.l.toFixed(2)}</td>
      <td class="${b.c >= b.o ? 'up' : 'down'}">${b.c.toFixed(2)}</td>
      <td class="muted">${fmt.vol(b.v)}</td>
    </tr>`).join('');
}

// ---------- card de previsão ----------
function renderPredict() {
  const stock = stockByTicker(state.ticker);
  const card = $('#predict');
  const p = predictionLog.latest(stock.id);
  const logged = auth.isLogged();

  const button = state.loadingPredict
    ? '<div class="loading-bar"><span style="position:relative">Rodando LSTM + XGBoost…</span></div>'
    : logged
      ? `<button class="btn btn-solid btn-block" type="button" data-run>${p ? 'Gerar nova previsão' : 'Gerar previsão'}</button>`
      : '<a class="btn btn-solid btn-block" href="login.html?next=grafico.html">Entrar para gerar previsão</a>';
  const err = state.predictError ? errorNotice(state.predictError) : '';
  const foot = `<p class="mono faint" style="font-size:12px">POST /predict/${stock.id}${p ? ` · executado em ${fmt.dateTime(p.forecast_date)}` : ''}</p>`;

  if (!p) {
    card.style.borderColor = '';
    card.innerHTML = `
      <div class="head"><span class="eyebrow">Previsão · ${stock.ticker}</span><span>v1.0</span></div>
      <div class="empty-state">
        <h3>Nenhuma previsão ainda</h3>
        <p>Rode o ensemble para estimar se ${stock.ticker} fecha em alta ou baixa no próximo pregão.</p>
      </div>
      ${err}${button}${foot}`;
    return;
  }

  const up = isUp(p);
  const col = up ? 'var(--up)' : 'var(--down)';
  const hex = up ? '#B9F18C' : '#FF7A45';
  const bar = (label, v, c) => `
    <div class="prob-bar">
      <div class="row"><span><span style="width:8px;height:8px;border-radius:2px;background:${c}"></span>${label}</span><span class="mono">${fmt.num(v)}</span></div>
      <div class="track"><div class="fill-x" style="width:${(v * 100).toFixed(1)}%;background:${c}"></div></div>
    </div>`;

  card.style.borderColor = col;
  card.innerHTML = `
    <div class="head"><span class="eyebrow">Previsão · ${fmt.date(p.target_date)}</span><span>v1.0</span></div>
    <div class="verdict">
      ${ring(p.final_forecast, hex)}
      <div class="verdict-text">
        <span class="verdict-word" style="color:${col}">${up ? 'ALTA' : 'BAIXA'}</span>
        <p>O ensemble estima que o próximo fechamento fique ${up ? 'acima' : 'abaixo'} do atual.</p>
      </div>
    </div>
    <div class="prob-bars">
      ${bar('LSTM', p.prob_lstm, 'var(--lstm)')}
      ${bar('XGBoost', p.prob_xgb, 'var(--xgb)')}
      ${bar('Confiança', p.confidence_score, 'var(--text)')}
    </div>
    ${err}${button}${foot}`;
}

$('#predict').addEventListener('click', async (e) => {
  if (!e.target.closest('[data-run]') || state.loadingPredict) return;
  const stock = stockByTicker(state.ticker);
  state.loadingPredict = true;
  state.predictError = null;
  renderPredict();
  try {
    await api.predict(stock.id);
  } catch (err) {
    state.predictError = err;
    if (err.status === 401) renderHeader('grafico.html');
  } finally {
    state.loadingPredict = false;
    if (stock.ticker === state.ticker) {
      renderPredict();
      renderChart();
    }
    renderTabs();
  }
});

renderControls();
load();
