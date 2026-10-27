# Architecture

## Folder map

```
app.py                      the page itself: the story from top to bottom, and nothing else
src/
  config.py                 every setting in one place: funds, dates, trading days, file paths
  data_loader.py            Yahoo Finance download (cached 24h) and the offline csv fallback
  cleaning.py               removes missing, impossible and duplicate rows, then sorts
  database.py               builds the in-memory SQLite database and loads the clean rows
  queries.py                the three SQL window-function queries, and a helper that runs them
  metrics.py                summary table, correlation table, calendar-year returns
ui/
  theme.py                  page config, the CSS, and the shared Altair styling
  sidebar.py                the three inputs, returned as plain values
  charts.py                 the five charts, each a function from a table to a finished chart
tests/                      pytest suite, no network needed
scripts/make_sample_data.py regenerates sample_data/prices.csv
sample_data/prices.csv      offline fallback prices
.streamlit/config.toml      theme colours (dark base, chip colour, text colour)
```

## Flow

```
ui.sidebar          what the user chose
      |
src.data_loader     Yahoo Finance, or sample_data/prices.csv if Yahoo is down
      |
src.cleaning        drop bad rows, normalise dates, sort
      |
src.database        in-memory SQLite, PRIMARY KEY (ticker, date)
      |
src.queries         daily return / growth / drawdown, via SQL window functions
      |
src.metrics         summary, correlation, yearly returns (pandas)
      |
ui.charts           five Altair charts
      |
app.py              writes it all to the page
```

## Design notes

**Why SQLite at all, when pandas could do it.** The three calculations are per-group and
order-dependent, which is exactly what SQL window functions are for. `PARTITION BY ticker` is also a
safety rail: one fund's maths cannot leak into another's.

**Why the drawdown query needs `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.** Without that
frame, `MAX(price)` would be the highest price of the whole period, including days that had not
happened yet. The frame restricts it to days already seen, so the running peak never looks ahead.

**Why the charts resample to weekly.** Eight funds over ten years is roughly 24,000 daily points per
chart, and two line charts made the browser sluggish. The growth chart keeps each week's last value
and the drawdown chart keeps each week's lowest value, so the deepest falls are never smoothed away.
Every number in the summary table still comes from the full daily data.

**Why the sidebar returns plain values.** `ui.sidebar.choose_settings()` hands back ordinary Python
values rather than reading Streamlit state elsewhere, so `src/` never imports the UI and the whole
`src/` package can be tested without a browser or a running server.

**Why `primaryColor` in `.streamlit/config.toml` must stay dark.** Streamlit draws the selected-fund
chips with the theme's primary colour as the background and hard-coded white text. A light primary
colour makes the fund names invisible.
