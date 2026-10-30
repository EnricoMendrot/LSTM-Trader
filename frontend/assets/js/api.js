import { API_BASE } from './config.js';

const KEYS = { access: 'lt_access', refresh: 'lt_refresh', email: 'lt_email', preds: 'lt_predictions' };

const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage indisponível */ } },
  del(k) { try { localStorage.removeItem(k); } catch { /* idem */ } },
};

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

// ---------- sessão ----------
export const auth = {
  isLogged: () => Boolean(store.get(KEYS.access)),
  email: () => store.get(KEYS.email),
  save({ access_token, refresh_token }, email) {
    store.set(KEYS.access, access_token);
    if (refresh_token) store.set(KEYS.refresh, refresh_token);
    if (email) store.set(KEYS.email, email);
  },
  logout() { [KEYS.access, KEYS.refresh, KEYS.email].forEach(store.del); },
};

async function raw(path, { method = 'GET', body, token } = {}) {
  const headers = { Accept: 'application/json' };
  if (body) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(API_BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError(`Não foi possível conectar à API em ${API_BASE}. O backend está rodando?`, 0);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : res.statusText;
    throw new ApiError(detail || 'Erro na requisição', res.status);
  }
  return data;
}

// Requisição autenticada: em 401 tenta renovar o token uma vez (GET /auth/refresh)
async function authed(path, opts = {}) {
  const token = store.get(KEYS.access);
  if (!token) throw new ApiError('Faça login para continuar.', 401);
  try {
    return await raw(path, { ...opts, token });
  } catch (err) {
    const refresh = store.get(KEYS.refresh);
    if (err.status !== 401 || !refresh) throw err;
    try {
      const fresh = await raw('/auth/refresh', { token: refresh });
      auth.save(fresh);
    } catch {
      auth.logout();
      throw new ApiError('Sua sessão expirou. Entre novamente.', 401);
    }
    return raw(path, { ...opts, token: store.get(KEYS.access) });
  }
}

// ---------- endpoints ----------
export const api = {
  login: (email, password) => raw('/auth/login', { method: 'POST', body: { email, password } }),
  createUser: (name, email, password) => raw('/auth/create', { method: 'POST', body: { name, email, password } }),

  // { Ticker, "Company Name", History: [{ recorded_at, close, open_price, price_high, price_low, volume }] }
  history: (ticker) => raw(`/dashboard/history/${encodeURIComponent(ticker)}`),

  // { id_stock, prob_xgb, prob_lstm, direction, final_forecast, confidence_score, target_date }
  async predict(idStock) {
    const result = await authed(`/predict/${idStock}`, { method: 'POST' });
    predictionLog.add(result);
    return result;
  },
};

// ---------- histórico local de previsões ----------
// O backend grava cada previsão na tabela `predictions`, mas ainda não expõe
// uma rota de listagem. Enquanto isso, guardamos as respostas neste navegador.
export const predictionLog = {
  all() {
    try { return JSON.parse(store.get(KEYS.preds) || '[]'); } catch { return []; }
  },
  add(p) {
    const list = this.all();
    list.unshift({ ...p, forecast_date: new Date().toISOString() });
    store.set(KEYS.preds, JSON.stringify(list.slice(0, 200)));
  },
  latest(idStock) {
    return this.all().find((p) => Number(p.id_stock) === Number(idStock)) || null;
  },
};
