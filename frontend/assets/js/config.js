// Endereço da API FastAPI. Rode o backend com:
//   cd backend && uvicorn main:app --reload
export const API_BASE = 'http://127.0.0.1:8000';

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
