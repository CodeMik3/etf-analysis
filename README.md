# Vanguard ETF Analysis

A small web app that compares eight Vanguard ETFs using real market data. It downloads daily prices,
cleans them, stores them in an in-memory SQL database, answers three questions with SQL window
functions, and presents the results as a dashboard.

Live data comes from Yahoo Finance and is adjusted for dividends and splits, so the returns shown are
total returns rather than price-only.

## What it shows

| Section | Question it answers |
|---|---|
| Summary | Yearly growth, volatility, Sharpe ratio and worst fall, one row per fund |
| Growth of 10,000 | What $10,000 invested on the start date would be worth on any later day |
| Drawdown | How far below its own previous high each fund sat, as eight small panels |
| Risk and return | Each fund as one point: risk across, growth up |
| Correlation | How closely any two funds move on the same day |
| Year by year | Each fund's return in each calendar year as a heatmap, blue for a gain and red for a loss |

Three sidebar controls drive everything: which funds to include, the start date, and the risk-free
rate used by the Sharpe ratio.

## How it works

```
Yahoo Finance  ->  clean in pandas  ->  SQLite (in memory)  ->  3 SQL queries  ->  Altair charts
```

1. **Download** — `yfinance` returns a wide table (one column per fund), which is reshaped into a long
   table of `date, ticker, price`. The result is cached for 24 hours. If Yahoo is unreachable, the app
   falls back to a local `prices.csv` if one exists.
2. **Clean** — drop missing prices, drop prices of zero or less, drop duplicate fund/day rows,
   normalise dates to `YYYY-MM-DD`, sort. The app reports how many rows survived.
3. **Store** — rows go into an in-memory SQLite database with `PRIMARY KEY (ticker, date)`. Nothing is
   written to disk.
4. **Query** — three SQL window functions do the analysis:

   | Query | Core expression | Purpose |
   |---|---|---|
   | Daily return | `price / LAG(price) OVER (PARTITION BY ticker ORDER BY date) - 1` | Day-over-day change |
   | Growth | `10000 * price / FIRST_VALUE(price) OVER (...)` | Value of a fixed initial investment |
   | Drawdown | `price / MAX(price) OVER (... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - 1` | Distance below the running peak |

   `PARTITION BY ticker` keeps each fund's maths independent. The `ROWS BETWEEN` frame on the drawdown
   query restricts `MAX` to days already seen, so the running peak never looks into the future.

5. **Present** — metrics are computed in pandas from the query results, then drawn with Altair. The two
   time-series charts are resampled to weekly points so the browser stays responsive with ~24,000 daily
   rows behind them; every reported statistic still uses the full daily data.

## Running it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Tech

Python, Streamlit, pandas, yfinance, Altair, and the `sqlite3` module from the standard library.
Styling is a CSS block in `app.py` plus a theme file in `.streamlit/config.toml`.
