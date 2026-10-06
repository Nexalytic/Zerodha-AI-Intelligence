# Zerodha AI Intelligence

An experimental, local-only stock-market and portfolio intelligence dashboard. It includes portfolio overview/import, risk and allocation views, markets, news research, watchlists, calculators, activity, and an AI analyst. Alpha Vantage is integrated for on-demand stock quote lookups; Groq provides portfolio analysis and web-search-grounded market/news answers (free tier available).

This is an unofficial demo and is not affiliated with or endorsed by Zerodha. It has no email authentication, no multi-user access control, and no production security review. Keep it on your own computer; do not expose it to the internet or use it for trading decisions. Initial portfolio prices are illustrative until replaced by your CSV or provider quote.

## Market data limits

Alpha Vantage `GLOBAL_QUOTE` accepts one symbol per request. The app caches results and requests quotes only when you click **Get quote**. Free keys are currently limited to 25 requests per day and typically five requests per minute; the local backend enforces both limits. Bare symbols in this India-focused demo map to the documented `.BSE` ticker suffix; add an explicit suffix where needed. Alpha Vantage documents realtime and 15-minute delayed entitlements for US data, while global quote responses default to end-of-day outside those entitlements. This is not tick-by-tick streaming. Confirm symbol availability and data entitlement on Alpha Vantage before relying on the result.

## Requirements

- Node.js 20 or newer and npm
- Python 3.11 or newer
- Alpha Vantage API key for quote lookups
- Groq API key (free) for AI analysis and grounded news/search answers

## Run on Windows (PowerShell)

Open this folder in VS Code. Use two terminals.

### Terminal 1 - backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python -m uvicorn app.main:app --reload --port 8000
```

Set `ALPHA_VANTAGE_API_KEY` and `GROQ_API_KEY` in `backend/.env`. Keys stay on the backend and are excluded from Git. You can leave them blank to inspect the clearly labeled local demo; quote requests and AI market research will show setup messages.

### Terminal 2 - frontend

From the project root (not the `backend` folder):

```powershell
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). No login or email OTP is used.

## Get the API keys

1. **Alpha Vantage:** Claim an API key at [Alpha Vantage Support](https://www.alphavantage.co/support/#api-key). Put it in `ALPHA_VANTAGE_API_KEY` in `backend/.env`. This app sends single-symbol `GLOBAL_QUOTE` requests; it does not expose the key in browser code. See the [official quote documentation](https://www.alphavantage.co/documentation/#latestprice).
2. **Groq:** Create a free key at [console.groq.com/keys](https://console.groq.com/keys), then put it in `GROQ_API_KEY` in `backend/.env`.

## Demo data and limitations

The starter positions are illustrative examples, not real recommendations or account data. Upload a CSV with symbol, quantity, average price and current price columns to replace them. The portfolio, watchlist, quote cache, and Alpha Vantage daily usage counter are stored in the local SQLite file `backend/zerodha-demo.db`. There is one shared local demo workspace, with no login boundary. No orders are created or sent. Do not deploy this demo publicly.
