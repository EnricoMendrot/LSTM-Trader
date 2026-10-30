import { STOCKS, stockById } from '../config.js';
import { api, auth, predictionLog } from '../api.js';
import { $, esc, fmt, isUp, renderHeader, errorNotice } from '../ui.js';

renderHeader('previsoes.html');

const SORTS = [['conf', 'Confiança'], ['prob', 'P(alta)'], ['ticker', 'Ticker']];
const state = { sort: 'conf', filter: 'Todas', running: false, current: null, error: null };

const latestAll = () => STOCKS.map((s) => ({ stock: s, p: predictionLog.latest(s.id) }));

// ---------- botão principal ----------
function renderRun() {
  const slot = $('#run-slot');
  if (!auth.isLogged()) {
    slot.innerHTML = '<a class="btn btn-solid" href="login.html?next=previsoes.html">Entrar para prever</a>';
    return;
  }
  slot.innerHTML = state.running
    ? `<button class="btn btn-busy" type="button" disabled aria-live="polite"><svg class="spin" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="26 12"/></svg>Prevendo ${esc(state.current)}…</button>`
    : '<button class="btn btn-solid" type="button" data-run>Prever as 5 ações</button>';
}

$('#run-slot').addEventListener('click', async (e) => {
  if (!e.target.closest('[data-run]') || state.running) return;
  state.running = true;
  state.error = null;
  $('#alert').innerHTML = '';
  for (const s of STOCKS) {
    state.current = s.ticker;
    renderRun();
    renderDumbbell();
    try {
      await api.predict(s.id);
    } catch (err) {
      state.error = err;
      break;
    }
    renderAll();
  }
  state.running = false;
  state.current = null;
  if (state.error) {
    $('#alert').innerHTML = errorNotice(state.error);
    if (state.error.status === 401) renderHeader('previsoes.html');
  }
  renderAll();
});

// ---------- resumo ----------
function renderSummary() {
  const done = latestAll().filter((x) => x.p);
  const target = done.map((x) => x.p.target_date).sort().pop();
  $('#target-line').textContent = target ? `Alvo · próximo pregão · ${fmt.date(target)}` : 'Alvo · próximo pregão';

  if (!done.length) {
    $('#summary').innerHTML = `<div class="stat" style="grid-column:1/-1"><span class="label">Ainda não há previsões neste navegador.</span><span class="value" style="font-family:var(--font);font-size:16px;color:var(--text-2)">Clique em “Prever as 5 ações” para rodar o ensemble em todas.</span></div>`;
    return;
  }
  const ups = done.filter((x) => isUp(x.p)).length;
  const avg = done.reduce((a, x) => a + x.p.confidence_score, 0) / done.length;
  const byConf = [...done].sort((a, b) => b.p.confidence_score - a.p.confidence_score);
  const best = byConf[0], worst = byConf[byConf.length - 1];
  const tile = (l, v, s, c = 'var(--text)') => `<div class="stat"><span class="label">${l}</span><span class="big" style="color:${c}">${v}</span><span class="mono muted" style="font-size:12px">${s}</span></div>`;
  $('#summary').innerHTML = [
    tile('Sinal de alta', `${ups} / ${done.length}`, `${done.length - ups} com sinal de baixa`, 'var(--up)'),
    tile('Confiança média', fmt.num(avg), '1 − |pLSTM − pXGB|'),
    tile('Mais consenso', best.stock.ticker, `confiança ${fmt.num(best.p.confidence_score)}`),
    tile('Mais divergência', worst.stock.ticker, `confiança ${fmt.num(worst.p.confidence_score)}`, 'var(--xgb)'),
  ].join('');
}

// ---------- dumbbell ----------
function renderSorts() {
  $('#sorts').innerHTML = SORTS.map(([k, l]) => `<button class="pill" type="button" aria-pressed="${k === state.sort}" data-sort="${k}">${l}</button>`).join('');
}
$('#sorts').addEventListener('click', (e) => {
  const b = e.target.closest('[data-sort]');
  if (b) { state.sort = b.dataset.sort; renderSorts(); renderDumbbell(); }
});

function renderDumbbell() {
  const rows = latestAll();
  const key = {
    conf: (x) => (x.p ? -x.p.confidence_score : 9),
    prob: (x) => (x.p ? -x.p.final_forecast : 9),
    ticker: (x) => x.stock.ticker,
  }[state.sort];
  rows.sort((a, b) => (key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : 0));

  $('#dumbbell').innerHTML = rows.map(({ stock, p }, i) => {
    const busy = state.running && state.current === stock.ticker ? '<div class="busy"></div>' : '';
    const name = `<a class="db-name" href="grafico.html?ticker=${stock.ticker}"><span class="tk">${stock.ticker}</span><span class="nm">${esc(stock.name)}</span></a>`;
    if (!p) {
      return `<div class="db-grid db-row" style="animation-delay:${i * 0.07}s">${name}
        <div class="db-track"><div class="axis"></div><div class="mid"></div><div class="pending">sem previsão</div>${busy}</div>
        <div class="db-out"><span class="mono faint" style="font-size:13px">—</span></div></div>`;
    }
    const up = isUp(p);
    const c = up ? 'var(--up)' : 'var(--down)';
    const lo = Math.min(p.prob_lstm, p.prob_xgb) * 100;
    const hi = Math.max(p.prob_lstm, p.prob_xgb) * 100;
    const f = p.final_forecast * 100;
    const strength = Math.abs(f - 50);
    return `<div class="db-grid db-row" style="animation-delay:${i * 0.07}s">${name}
      <div class="db-track">
        <div class="axis"></div><div class="mid"></div>
        <div class="strength" style="background:${c};left:${up ? 50 : 50 - strength}%;width:${strength}%"></div>
        <div class="link" style="left:${lo}%;width:${hi - lo}%"></div>
        <div class="dot" style="left:${p.prob_lstm * 100}%;background:var(--lstm)" title="LSTM ${fmt.num(p.prob_lstm)}"></div>
        <div class="dot" style="left:${p.prob_xgb * 100}%;background:var(--xgb)" title="XGBoost ${fmt.num(p.prob_xgb)}"></div>
        <div class="diamond" style="left:${f}%" title="Ensemble ${fmt.num(p.final_forecast)}"></div>
        ${busy}
      </div>
      <div class="db-out">
        <span class="tag" style="background:${c}">${up ? '▲ ALTA' : '▼ BAIXA'} ${fmt.pct(p.final_forecast)}</span>
        <div class="conf"><div class="track"><div class="fill-x" style="width:${p.confidence_score * 100}%"></div></div><span>${fmt.num(p.confidence_score)}</span></div>
      </div></div>`;
  }).join('');
}

// ---------- histórico ----------
function renderFilters() {
  $('#filters').innerHTML = ['Todas', ...STOCKS.map((s) => s.ticker)]
    .map((k) => `<button class="pill" type="button" aria-pressed="${k === state.filter}" data-f="${k}">${k}</button>`).join('');
}
$('#filters').addEventListener('click', (e) => {
  const b = e.target.closest('[data-f]');
  if (b) { state.filter = b.dataset.f; renderFilters(); renderHistory(); }
});

function renderHistory() {
  const list = predictionLog.all().filter((p) => state.filter === 'Todas' || stockById(p.id_stock)?.ticker === state.filter);
  if (!list.length) {
    $('#hist').innerHTML = '<tr><td colspan="8" class="muted" style="text-align:left;padding:24px">Nenhuma previsão registrada.</td></tr>';
    return;
  }
  $('#hist').innerHTML = list.map((p) => {
    const up = isUp(p);
    return `<tr>
      <td class="muted">${fmt.dateTime(p.forecast_date)}</td>
      <td class="left muted">${fmt.date(p.target_date)}</td>
      <td class="left" style="font-weight:600">${stockById(p.id_stock)?.ticker ?? p.id_stock}</td>
      <td style="color:var(--lstm)">${fmt.num(p.prob_lstm, 4)}</td>
      <td style="color:var(--xgb)">${fmt.num(p.prob_xgb, 4)}</td>
      <td>${fmt.num(p.final_forecast, 4)}</td>
      <td>${fmt.num(p.confidence_score, 4)}</td>
      <td class="${up ? 'up' : 'down'}">${p.direction ?? (up ? 'alta' : 'baixa')}</td>
    </tr>`;
  }).join('');
}

function renderAll() {
  renderRun();
  renderSummary();
  renderDumbbell();
  renderHistory();
}

renderSorts();
renderFilters();
renderAll();
