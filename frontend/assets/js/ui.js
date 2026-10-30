import { auth } from './api.js';

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

// ---------- formatação ----------
export const fmt = {
  money: (v) => '$' + Number(v).toFixed(2),
  num: (v, d = 2) => Number(v).toFixed(d),
  pct: (v, d = 0) => (Number(v) * 100).toFixed(d) + '%',
  vol: (v) => (Number(v) / 1e6).toFixed(1) + ' mi',
  date(d) {
    const x = d instanceof Date ? d : parseDate(d);
    return x.toLocaleDateString('pt-BR');
  },
  short(d) {
    const x = d instanceof Date ? d : parseDate(d);
    return x.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  },
  dateTime(d) {
    return new Date(d).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  },
};

// "2026-06-26T00:00:00" ou "2026-06-26" → Date local (sem deslocar o dia pelo fuso)
export function parseDate(s) {
  const [y, m, d] = String(s).slice(0, 10).split('-').map(Number);
  return new Date(y, m - 1, d);
}

export const isUp = (p) => (p.direction ? p.direction === 'alta' : p.final_forecast > 0.5);

// ---------- header ----------
const LOGO = `<svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><rect x="1" y="1" width="28" height="28" rx="7" fill="none" stroke="#ECE8DD" stroke-width="1.6"/><polyline points="6,20 11,14 15,17 22,8" fill="none" stroke="#B9F18C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="22" cy="8" r="2.4" fill="#B9F18C"/></svg>`;

export function renderHeader(active) {
  const el = $('#site-header');
  if (!el) return;
  const links = [
    ['index.html', 'Projeto'],
    ['grafico.html', 'Gráficos'],
    ['previsoes.html', 'Previsões'],
  ];
  const email = auth.email();
  const user = auth.isLogged()
    ? `<div class="user-area"><span class="avatar" aria-hidden="true">${esc((email || '?')[0])}</span><span>${esc(email || 'Conectado')}</span><button class="link-btn" type="button" data-logout>Sair</button></div>`
    : `<a class="btn btn-ghost" href="login.html" style="min-height:44px">Entrar</a>`;

  el.className = 'site-header';
  el.innerHTML = `
    <a class="brand" href="index.html">${LOGO}<span>LSTM—TRADER</span></a>
    <nav class="nav" aria-label="Principal">
      ${links.map(([href, label]) => `<a href="${href}"${href === active ? ' aria-current="page"' : ''}>${label}</a>`).join('')}
    </nav>
    ${user}`;

  $('[data-logout]', el)?.addEventListener('click', () => {
    auth.logout();
    location.reload();
  });
}

export function errorNotice(err) {
  return `<div class="notice error" role="alert"><strong>${esc(err.message)}</strong>${
    err.status === 0 ? '<br>Inicie o backend com <code>cd backend &amp;&amp; uvicorn main:app --reload</code> e recarregue a página.' : ''
  }</div>`;
}
