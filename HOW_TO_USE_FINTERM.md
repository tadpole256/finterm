# How To Use Finterm (Simple Guide)

This guide is written for non-technical users.

## What this app is

Finterm is a personal market research terminal you run on your own computer.

- It helps you track watchlists, charts, notes, alerts, screening, and portfolio context.
- It can use free live market data (Alpha Vantage) or local mock data.
- It is not a live brokerage execution platform.

## Before you start

This guide is for macOS.

You need:
- Terminal app (already on Mac)
- Internet connection
- About 10-15 minutes for first setup

## One-time setup (first time only)

1. Open Terminal.
2. Go to the project folder:

```bash
cd /Users/tadpole256/Documents/GitHub/finterm
```

3. Install local database services:

```bash
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
```

4. Create the local database:

```bash
createdb finterm
```

5. Install app dependencies:

```bash
npm install
cd apps/api && python3 -m pip install -r requirements-dev.txt && cd ../..
```

6. Create local config files:

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

7. Get a free Alpha Vantage API key:

- Open [Alpha Vantage API Key Page](https://www.alphavantage.co/support/#api-key)
- Sign up and copy your key

8. Put your key into both env files:

Open `.env` and `apps/api/.env`, then set:

```bash
MARKET_DATA_PROVIDER=alpha_vantage
ALPHA_VANTAGE_API_KEY=your_real_key_here
ALPHA_VANTAGE_BASE_URL=https://www.alphavantage.co/query
```

9. Prepare database tables and sample data:

```bash
npm run db:migrate
npm run db:seed
```

10. Start the app:

```bash
npm run dev
```

11. Open your browser to:

- Web app: `http://localhost:3000`
- API docs (optional): `http://localhost:8000/docs`

Keep the Terminal window open while using the app.

Notes:
- Alpha Vantage free data is delayed (not true real-time).
- If you refresh too often, Alpha Vantage can temporarily throttle requests.

## Daily start (after first setup)

Each day, do:

```bash
cd /Users/tadpole256/Documents/GitHub/finterm
brew services start postgresql@16
brew services start redis
npm run dev
```

Then open `http://localhost:3000`.

## Daily stop

In the terminal where the app is running, press:

- `Control + C`

## What to click first (easy flow)

1. **Home**: quick market snapshot and active signals.
2. **Watchlists**: add symbols you care about.
3. **Security page**: click a symbol to view chart + context.
4. **Research**: save notes/thesis in plain language.
5. **Screener**: filter market candidates.
6. **Alerts**: add simple thresholds and reminders.
7. **Journal**: record trade decisions and outcomes.

## Common problems and quick fixes

### "Connection refused" or database errors

Run:

```bash
brew services start postgresql@16
createdb finterm
npm run db:migrate
npm run db:seed
```

### "brew: command not found"

Install Homebrew first:

- https://brew.sh

Then repeat setup.

### App page won’t load

Make sure `npm run dev` is still running in Terminal.

## Optional: run background worker

If you want scheduled local jobs:

```bash
npm run dev:worker
```

Run this in a second terminal window.

## Important note

This local MVP is designed for research workflow and decision support.
Treat outputs as informational, not financial advice.
