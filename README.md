# Vanguard ETF Analysis

A web app that compares eight Vanguard ETFs using real market data. It downloads daily prices, cleans
them, stores them in an in-memory SQL database, answers three questions with SQL window functions, and
presents the results as a dashboard.

Prices come from Yahoo Finance adjusted for dividends and splits, so the figures are total returns
rather than price-only. If Yahoo is unreachable the app falls back to a bundled CSV, so it always runs.

**Python · Streamlit · pandas · Altair · SQLite · yfinance**

## What it shows

| Section | Question it answers |
|---|---|
| Summary | Yearly growth, volatility, Sharpe ratio and worst fall, one row per fund |
| Growth of 10,000 | What $10,000 invested on the start date would be worth on any later day |
| Drawdown | How far below its own previous high each fund sat, as eight small panels |
| Risk and return | Each fund as one point: risk across, growth up |
| Correlation | How closely any two funds move on the same day |
| Year by year | Each fund's return in each calendar year, blue for a gain and red for a loss |

Three sidebar controls drive everything: which funds to include, the start date, and the risk-free rate
used by the Sharpe ratio.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

```bash
pip install -r requirements-dev.txt   # adds pytest
pytest                                # 20 tests, no network needed
python scripts/make_sample_data.py    # refresh the offline fallback prices
```

## Project layout

```
app.py                        the page: the story from top to bottom
src/
  config.py                   every setting in one place
  data_loader.py              Yahoo download (cached 24h) + offline CSV fallback
  cleaning.py                 removes missing, impossible and duplicate rows
  database.py                 in-memory SQLite
  queries.py                  the three SQL window-function queries
  metrics.py                  summary, correlation, calendar-year returns
ui/
  theme.py                    page config, CSS, shared chart styling
  sidebar.py                  the three inputs
  charts.py                   the five charts
tests/                        pytest suite
scripts/make_sample_data.py   regenerates the fallback CSV
sample_data/prices.csv        offline fallback prices
docs/architecture.md          how the pieces fit together, and why
```

`src/` never imports from `ui/`, so all of the analysis can be tested without a browser.

## How it works

```
Yahoo Finance -> clean in pandas -> SQLite (in memory) -> 3 SQL queries -> pandas metrics -> Altair charts
```

The analysis rests on three SQL window functions:

| Query | Core expression | Purpose |
|---|---|---|
| Daily return | `price / LAG(price) OVER (PARTITION BY ticker ORDER BY date) - 1` | Day-over-day change |
| Growth | `10000 * price / FIRST_VALUE(price) OVER (...)` | Value of a fixed initial investment |
| Drawdown | `price / MAX(price) OVER (... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - 1` | Distance below the running peak |

`PARTITION BY ticker` keeps each fund's maths independent. The `ROWS BETWEEN` frame on the drawdown
query limits `MAX` to days already seen, so the running peak never looks into the future.

The two time-series charts are resampled to weekly points — the growth chart keeps each week's last
value, the drawdown chart keeps each week's lowest — so the browser stays responsive with ~24,000 daily
rows behind them. Every reported statistic still uses the full daily data.

More detail, including why each decision was made, is in [docs/architecture.md](docs/architecture.md).
