# LSTM-Trader · Frontend

Interface web do LSTM-Trader em HTML, CSS e JavaScript puro (ES modules), sem etapa de build.

## Telas

| Arquivo | Tela | Rotas da API |
|---|---|---|
| `index.html` | Projeto: explicação do pipeline, da LSTM, do XGBoost e do ensemble | `GET /dashboard/history/{ticker}` (último fechamento nos cards) |
| `grafico.html` | Gráfico por ação (linha/candles, volume, períodos 1M–5A, projeção D+1) + card de previsão | `GET /dashboard/history/{ticker}`, `POST /predict/{id_stock}` |
| `previsoes.html` | Comparação LSTM × XGBoost × ensemble nas 5 ações + histórico | `POST /predict/{id_stock}` |
| `login.html` | Entrar / criar conta | `POST /auth/login`, `POST /auth/create`, `GET /auth/refresh` |

## Como rodar

1. Suba o backend (porta 8000):
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
2. Sirva a pasta `frontend/` na porta **5500** (a liberada no CORS do `main.py`):
   - VS Code: botão **Go Live** da extensão Live Server, com `frontend/` como raiz; ou
   - `python -m http.server 5500 --bind 127.0.0.1` dentro de `frontend/`.
3. Abra `http://127.0.0.1:5500/index.html`.

> Abrir os `.html` direto pelo explorador de arquivos (`file://`) não funciona: os módulos JS precisam de um servidor.

O endereço da API fica em `assets/js/config.js` (`API_BASE`).

## Estrutura

```
frontend/
├── index.html · grafico.html · previsoes.html · login.html
└── assets/
    ├── css/  styles.css (tokens e componentes) · home.css · app.css
    └── js/
        ├── config.js   URL da API e ids das ações
        ├── api.js      cliente HTTP, JWT (access + refresh) e histórico local de previsões
        ├── ui.js       header, formatação, utilitários
        ├── chart.js    gráfico de preço em SVG e anel de probabilidade
        └── pages/      um script por tela
```

## Observações

- Os tokens ficam no `localStorage`. Em `401`, o cliente tenta `GET /auth/refresh` uma vez antes de pedir login de novo.
- A API ainda não tem rota para listar a tabela `predictions`. Por enquanto o histórico da tela Previsões mostra as previsões feitas neste navegador. Com uma rota como `GET /predict/history`, basta trocar `predictionLog.all()` em `api.js`.
- A projeção D+1 no gráfico é visual: a direção e a largura do cone vêm de `final_forecast` e `confidence_score`, mas o modelo não prevê preço.
