import { api, auth } from '../api.js';
import { $, $$, esc } from '../ui.js';

const next = new URLSearchParams(location.search).get('next');
// só aceita destinos locais (evita redirecionamento aberto)
const target = next && /^[a-z]+\.html$/.test(next) ? next : 'grafico.html';

let mode = 'login';

const COPY = {
  login: {
    title: 'Bem-vindo de volta', sub: 'Use o e-mail e a senha cadastrados.', cta: 'Entrar',
    route: 'POST /auth/login', note: 'access_token válido por 30 min · refresh_token por 7 dias (GET /auth/refresh).',
  },
  create: {
    title: 'Criar conta', sub: 'Nome, e-mail e senha. Só isso.', cta: 'Criar conta',
    route: 'POST /auth/create', note: 'Senha guardada com bcrypt. E-mail já cadastrado retorna erro.',
  },
};

function setMode(m) {
  mode = m;
  const c = COPY[m];
  $$('.seg').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.mode === m)));
  $('#name-field').hidden = m !== 'create';
  $('#title').textContent = c.title;
  $('#sub').textContent = c.sub;
  $('#submit').textContent = c.cta;
  $('#route').textContent = c.route;
  $('#route-note').textContent = c.note;
  $('#password').autocomplete = m === 'create' ? 'new-password' : 'current-password';
  $('#msg').innerHTML = '';
}
$$('.seg').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.mode)));

function message(text, ok = false) {
  $('#msg').innerHTML = `<div class="notice ${ok ? 'ok' : 'error'}" role="${ok ? 'status' : 'alert'}">${esc(text)}</div>`;
}

$('#form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = $('#name').value.trim();
  const email = $('#email').value.trim();
  const password = $('#password').value;

  if (mode === 'create' && !name) return message('Informe seu nome.');
  if (!/^\S+@\S+\.\S+$/.test(email)) return message('Informe um e-mail válido.');
  if (password.length < 6) return message('A senha precisa ter pelo menos 6 caracteres.');

  const btn = $('#submit');
  btn.disabled = true;
  btn.textContent = mode === 'create' ? 'Criando conta…' : 'Entrando…';
  try {
    if (mode === 'create') await api.createUser(name, email, password);
    const tokens = await api.login(email, password);
    auth.save(tokens, email);
    message(mode === 'create' ? 'Conta criada! Redirecionando…' : 'Tudo certo! Redirecionando…', true);
    setTimeout(() => location.assign(target), 500);
  } catch (err) {
    const map = {
      'Invalid email or password': 'E-mail ou senha incorretos.',
      'Email already registered': 'Este e-mail já está cadastrado. Tente entrar.',
    };
    message(map[err.message] || err.message);
    btn.disabled = false;
    btn.textContent = COPY[mode].cta;
  }
});

// linhas animadas do painel esquerdo
const cols = ['#B9F18C', '#8FB8FF', '#FFB547', '#ECE8DD'];
$('#lines').innerHTML = cols.map((c, k) => {
  let s = 101 + k * 37;
  const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  let y = 180 + k * 40;
  let d = `M0 ${y.toFixed(1)}`;
  for (let i = 1; i <= 40; i++) {
    y = Math.max(60, Math.min(380, y + (rnd() - 0.52) * 26));
    d += ` L${i * 15} ${y.toFixed(1)}`;
  }
  return `<path d="${d}" pathLength="1" fill="none" stroke="${c}" stroke-width="1.6" stroke-opacity="${k ? 0.22 : 0.55}" vector-effect="non-scaling-stroke" class="ln" style="animation-delay:${k * 0.8}s"/>`;
}).join('');

if (auth.isLogged()) message(`Você já está conectado como ${auth.email() || 'usuário'}.`, true);
