// Endereço da API FastAPI. Rode o backend com:
//   cd backend && uvicorn main:app --reload
// Usa o mesmo host em que a página foi aberta (localhost, IP da rede etc.),
// assim funciona também quando o site é acessado de outro computador.
export const API_BASE = `${location.protocol}//${location.hostname || '127.0.0.1'}:8000`;

// ids da tabela `stocks` (ordem do scripts/seed_history.py)
export const STOCKS = [
  { id: 1, ticker: 'AAPL', name: 'Apple' },
  { id: 2, ticker: 'MSFT', name: 'Microsoft' },
  { id: 3, ticker: 'GOOGL', name: 'Alphabet' },
  { id: 4, ticker: 'AMZN', name: 'Amazon' },
  { id: 5, ticker: 'NVDA', name: 'NVIDIA' },
];

export const stockByTicker = (t) => STOCKS.find((s) => s.ticker === t);
export const stockById = (id) => STOCKS.find((s) => s.id === Number(id));
