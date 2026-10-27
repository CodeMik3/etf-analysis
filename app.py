# This app studies a few Vanguard ETFs, which are baskets of shares that you can buy like one share.
# It downloads the daily prices from Yahoo Finance, cleans them, keeps them in a small SQL database, and asks the database three questions.
# At the end it shows one table and three charts, so you can compare how much each fund grew and how much risk it took.


# STEP 0: IMPORT THE TOOLS AND WRITE THE SETTINGS

# bring in Streamlit, the library that turns Python code into a web page
import streamlit as st
# bring in yfinance, the library that downloads prices from Yahoo Finance
import yfinance as yf
# bring in pandas, the library that works with tables of data
import pandas as pd
# bring in altair, the drawing library that already comes inside Streamlit, which lets us choose how the charts look
import altair as alt
# bring in sqlite3, the small database that already comes inside Python
import sqlite3
# bring in os, which lets us ask if a file exists on the computer
import os
# bring in datetime, which lets us work with dates
import datetime

# the list of funds that the user can choose from
FUNDS = ["VTI", "VOO", "VGT", "VYM", "VXUS", "VWO", "BND", "VNQ"]
# the first date that we ask Yahoo Finance about
START_DATE = "2015-01-01"
# the yearly return of a very safe investment, written in percent
DEFAULT_SAFE_RETURN_PERCENT = 2.0
# the number of days in one year when the stock market is open
TRADING_DAYS = 252


# STEP 0B: MAKE THE PAGE LOOK LIKE LIQUID GLASS

# give the page a name in the browser tab, and let the content use the whole width of the screen
st.set_page_config(page_title="Vanguard ETF Analysis", page_icon="📈", layout="wide")

# The long text below is CSS, not Python. CSS is the language that tells the browser how the page should look.
# Every rule says: pick a part of the page, then change its colour, its corners, or its blur.
LIQUID_GLASS_CSS = """
<style>

/* the whole page: soft grey lights on a black sheet, and the lights do not move, so nothing gets slow */
.stApp {
    background:
        radial-gradient(1100px 760px at 8% 0%, rgba(255, 255, 255, 0.16), transparent 60%),
        radial-gradient(900px 680px at 95% 12%, rgba(255, 255, 255, 0.10), transparent 60%),
        radial-gradient(1000px 820px at 50% 108%, rgba(255, 255, 255, 0.08), transparent 60%),
        linear-gradient(165deg, #000000 0%, #141414 55%, #000000 100%);
    background-attachment: fixed;
}

/* the thin bar at the very top of the page: see-through with a light blur */
[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

/* the sidebar: one tall sheet of frosted glass */
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.07) !important;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border-right: 1px solid rgba(255, 255, 255, 0.12);
}

/* the boxes inside the sidebar must stay see-through, or they would hide the glass */
[data-testid="stSidebar"] > div {
    background: transparent !important;
}

/* the main column: one big piece of glass that holds all the results, with only a small gap on the left and the right */
.stMainBlockContainer {
    max-width: 100%;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    padding-top: 3rem;
    margin-left: 1rem;
    margin-right: 1rem;
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(22px) saturate(160%);
    -webkit-backdrop-filter: blur(22px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 28px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.60), inset 0 1px 0 rgba(255, 255, 255, 0.32);
}

/* the tables, the charts and the messages: smaller pieces of glass inside the big one */
[data-testid="stDataFrame"],
[data-testid="stVegaLiteChart"],
[data-testid="stAlertContainer"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 20px;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.50),
        inset 0 -1px 0 rgba(255, 255, 255, 0.18),
        0 10px 34px rgba(0, 0, 0, 0.45);
    overflow: hidden;
}

/* the boxes in the sidebar where you choose the funds, the date and the safe return */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] {
    background: rgba(255, 255, 255, 0.10) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 14px !important;
}

/* the small labels of the funds that you picked: only the corners are changed here, because the colour comes from config.toml */
[data-testid="stMultiSelectTagsContainer"] div {
    border-radius: 11px;
}

/* the titles get a soft white light behind the letters */
.stApp h1, .stApp h2, .stApp h3 {
    color: #ffffff;
    text-shadow: 0 2px 22px rgba(255, 255, 255, 0.30);
}

</style>
"""

# put the CSS on the page, and allow HTML so that the browser reads it as a style and not as text
st.markdown(LIQUID_GLASS_CSS, unsafe_allow_html=True)


# STEP 0C: ASK THE USER THREE QUESTIONS IN THE SIDEBAR

# write a small title at the top of the sidebar
st.sidebar.header("Your choices")
# let the user pick one or more funds, and start with all of them picked
chosen_funds = st.sidebar.multiselect("Funds", FUNDS, default=FUNDS)
# let the user pick the first date, and allow any date between 2012 and today
start_date = st.sidebar.date_input(
    "Start date",
    value=pd.to_datetime(START_DATE).date(),
    min_value=datetime.date(2012, 1, 1),
    max_value=datetime.date.today(),
)
# let the user say how much a very safe investment earns in one year
safe_return_percent = st.sidebar.number_input(
    "Safe return (% per year)",
    min_value=0.0,
    max_value=10.0,
    step=0.1,
    value=DEFAULT_SAFE_RETURN_PERCENT,
)
# change the percent into a decimal number, because the Sharpe ratio needs a decimal
risk_free_rate = safe_return_percent / 100

# if the user removed every fund, there is nothing to study
if len(chosen_funds) == 0:
    # show a yellow message that asks for at least one fund
    st.warning("Please choose at least one fund in the sidebar.")
    # stop the program here, so the rest of the page does not run
    st.stop()


# STEP 1: DOWNLOAD THE PRICES

# This function downloads the closing prices of the chosen funds and gives back one long table.
# The line above it keeps the answer for one day (86400 seconds), so the page does not download the same prices again and again.
@st.cache_data(ttl=86400)
def download_prices(funds, start):
    # ask Yahoo Finance for the prices of all the chosen funds, from the start date until today
    raw = yf.download(list(funds), start=str(start), auto_adjust=True, progress=False)
    # keep only the "Close" part, which is the price at the end of each day
    close = raw["Close"]
    # if the user picked only one fund, the answer is one column of numbers, not a table
    if isinstance(close, pd.Series):
        # to_frame changes that one column of numbers into a small table
        close = close.to_frame()
    # move the dates out of the row labels and into a normal column called "Date"
    close = close.reset_index()
    # change the wide table into a long table, with one row for each fund on each day
    long_table = close.melt(id_vars="Date", var_name="ticker", value_name="price")
    # rename the column "Date" to "date", so every column name is lower case
    long_table = long_table.rename(columns={"Date": "date"})
    # give the long table back to the part of the program that called this function
    return long_table


# start with an empty table, so we can check later if the download worked
prices = pd.DataFrame()
# remember with True or False if Yahoo Finance answered us
download_worked = False
# try the download, and catch any problem, so that the page does not crash
try:
    # call the function, and pass the funds as a tuple, because the saved answer needs a tuple
    prices = download_prices(tuple(chosen_funds), start_date)
    # an empty answer is also a failure, so we make an error on purpose
    if prices.empty:
        # raise means "stop here and jump to the except part below"
        raise ValueError("Yahoo Finance sent back no rows.")
    # if the program is still here, the download worked
    download_worked = True
except Exception:
    # any problem at all means that we must use the backup file
    download_worked = False

# if Yahoo Finance did not answer, look for the saved file on the computer
if download_worked == False:
    # check if a file called prices.csv sits next to this program
    if os.path.exists("prices.csv"):
        # read the saved file, which has the columns date, ticker and price
        prices = pd.read_csv("prices.csv")
        # keep only the rows of the funds that the user chose
        prices = prices[prices["ticker"].isin(chosen_funds)]
        # keep only the rows on the start date or after the start date
        prices = prices[pd.to_datetime(prices["date"]) >= pd.to_datetime(start_date)]
        # tell the user that these numbers come from the saved file
        st.info("Yahoo did not answer, so this page uses the saved prices.csv file.")
    else:
        # without Yahoo Finance and without a backup file there is nothing to show
        st.error("Could not download prices from Yahoo, and there is no prices.csv backup. Please try again later.")
        # stop the program here
        st.stop()


# STEP 2: CLEAN THE PRICES

# count the rows before the cleaning, so we can tell the user how many rows we removed
rows_before = len(prices)
# remove every row where the price is missing
prices = prices.dropna(subset=["price"])
# remove every row where the price is zero or less, because such a price is wrong
prices = prices[prices["price"] > 0]
# remove rows that say the same thing twice about one fund on one day
prices = prices.drop_duplicates(subset=["date", "ticker"])
# change the date into simple text that looks like 2026-10-23
prices["date"] = pd.to_datetime(prices["date"]).dt.strftime("%Y-%m-%d")
# sort the table by fund and then by date, and give the rows new row numbers
prices = prices.sort_values(["ticker", "date"]).reset_index(drop=True)
# count the rows after the cleaning
rows_after = len(prices)

# if almost nothing is left, the numbers would not mean anything
if rows_after < 30:
    # show a red message that asks for an earlier start date
    st.error("Not enough data for these choices. Try an earlier start date.")
    # stop the program here
    st.stop()


# STEP 3: STORE THE PRICES IN SQL

# make a database that lives only in the memory of the computer, so no file is saved
connection = sqlite3.connect(":memory:")
# create an empty table, where one fund together with one date can appear only once
connection.execute("CREATE TABLE prices (date TEXT, ticker TEXT, price REAL, PRIMARY KEY (ticker, date))")
# copy every row of the clean pandas table into the database table
prices.to_sql("prices", connection, if_exists="append", index=False)


# STEP 4: ASK QUESTIONS WITH SQL

# this question asks how much the price changed from one day to the next day
DAILY_RETURN_SQL = """
SELECT
    -- the day of the price
    date,
    -- the short name of the fund
    ticker,
    -- LAG takes the price of the day before inside the same fund, so this line is the change of one day
    price / LAG(price) OVER (PARTITION BY ticker ORDER BY date) - 1 AS daily_return
FROM prices
-- keep the days of one fund together and in time order
ORDER BY ticker, date
"""

# this question asks what 10000 dollars would be worth on every day
GROWTH_SQL = """
SELECT
    -- the day of the price
    date,
    -- the short name of the fund
    ticker,
    -- FIRST_VALUE is the very first price of the fund, so this line shows the value of 10000 dollars later
    10000 * price / FIRST_VALUE(price) OVER (PARTITION BY ticker ORDER BY date) AS growth
FROM prices
-- keep the days of one fund together and in time order
ORDER BY ticker, date
"""

# this question asks how far the price is below the best price of the fund until that day
DRAWDOWN_SQL = """
SELECT
    -- the day of the price
    date,
    -- the short name of the fund
    ticker,
    -- MAX from the first row until this row is the best price so far, so this number is zero or negative
    price / MAX(price) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - 1 AS drawdown
FROM prices
-- keep the days of one fund together and in time order
ORDER BY ticker, date
"""

# run the first question and keep the answer in a pandas table
daily_return_table = pd.read_sql_query(DAILY_RETURN_SQL, connection)
# run the second question and keep the answer in a pandas table
growth_table = pd.read_sql_query(GROWTH_SQL, connection)
# run the third question and keep the answer in a pandas table
drawdown_table = pd.read_sql_query(DRAWDOWN_SQL, connection)

# make an empty list, where we will put one small answer for each fund
summary_rows = []
# go through the funds one by one, in alphabetical order
for one_ticker in sorted(prices["ticker"].unique()):
    # keep only the price rows of this one fund
    fund_prices = prices[prices["ticker"] == one_ticker]
    # keep only the daily changes of this one fund, and remove the empty first value
    fund_returns = daily_return_table[daily_return_table["ticker"] == one_ticker]["daily_return"].dropna()
    # keep only the drawdown numbers of this one fund
    fund_drawdowns = drawdown_table[drawdown_table["ticker"] == one_ticker]["drawdown"]
    # read the first date of this fund as a real date
    first_date = pd.to_datetime(fund_prices["date"].iloc[0])
    # read the last date of this fund as a real date
    last_date = pd.to_datetime(fund_prices["date"].iloc[-1])
    # count how many days there are between the first date and the last date
    days = (last_date - first_date).days
    # read the first price of this fund
    first_price = fund_prices["price"].iloc[0]
    # read the last price of this fund
    last_price = fund_prices["price"].iloc[-1]
    # the yearly growth: how much the price grew in one year on average
    cagr = (last_price / first_price) ** (365.25 / days) - 1
    # the volatility: how much the daily changes jump around, counted for one whole year
    volatility = fund_returns.std() * (TRADING_DAYS ** 0.5)
    # the Sharpe ratio: the growth above the safe return, divided by the risk
    sharpe = (fund_returns.mean() * TRADING_DAYS - risk_free_rate) / volatility
    # the biggest fall: the lowest drawdown number of this fund
    max_drawdown = fund_drawdowns.min()
    # put the name and the five numbers of this fund into one small dictionary
    one_row = {
        "ticker": one_ticker,
        "cagr": cagr,
        "volatility": volatility,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
    }
    # add this small dictionary to the list
    summary_rows.append(one_row)

# change the list of small dictionaries into one table with one row for each fund
summary = pd.DataFrame(summary_rows)

# turn the daily changes into a wide table, with the dates as rows and one column for each fund
returns_wide = daily_return_table.pivot(index="date", columns="ticker", values="daily_return")
# measure how much the funds move together, and keep two numbers after the point
correlation = returns_wide.corr().round(2)

# make a copy of the daily changes without the empty first value of each fund
yearly_steps = daily_return_table.dropna(subset=["daily_return"]).copy()
# take the first four letters of the date, which are the year
yearly_steps["year"] = yearly_steps["date"].str[:4]
# turn a change like 0.01 into a growth number like 1.01, because growth numbers can be multiplied
yearly_steps["growth_factor"] = 1 + yearly_steps["daily_return"]
# multiply all the growth numbers of one fund inside one year, which gives the growth of that whole year
yearly_returns = yearly_steps.groupby(["ticker", "year"], as_index=False)["growth_factor"].prod()
# take away the 1 again, so that 1.12 becomes 0.12, which means twelve percent
yearly_returns["yearly_return"] = yearly_returns["growth_factor"] - 1


# STEP 5: SHOW THE ANSWERS

# the colours of the eight lines and dots, and the three greys that the charts use for text, grid lines and axis lines
CHART_COLOURS = "tableau10"
TEXT_GREY = "#d9d9d9"
GRID_GREY = "rgba(255, 255, 255, 0.10)"
AXIS_GREY = "rgba(255, 255, 255, 0.28)"


# This function gives every chart the same dark glass look, so we do not have to repeat these lines five times.
# It takes a finished chart, changes the colours of the text and the lines around it, and gives the chart back.
def style_chart(chart):
    # make the area behind the chart see-through, so the glass of the page shows through it
    chart = chart.configure(background="transparent")
    # remove the box around the drawing area
    chart = chart.configure_view(strokeWidth=0, fill=None)
    # make the numbers, the titles and the thin grid lines light grey instead of black
    chart = chart.configure_axis(
        labelColor=TEXT_GREY,
        titleColor=TEXT_GREY,
        gridColor=GRID_GREY,
        domainColor=AXIS_GREY,
        tickColor=AXIS_GREY,
        labelFontSize=12,
        titleFontSize=12,
    )
    # make the small title above each little chart white and bold
    chart = chart.configure_header(labelColor="#ffffff", titleColor="#ffffff", labelFontWeight="bold")
    # give the chart back to the part of the program that called this function
    return chart


# the big title of the page
st.title("Vanguard ETF Analysis")
# two sentences that say what this page is about
st.write(
    "This page compares Vanguard ETFs with real prices from Yahoo Finance. "
    "It shows how much money each fund made and how much risk it took."
)
# a small grey line with the cleaning numbers and the safe return
st.caption(
    "Rows before cleaning: " + str(rows_before)
    + ". Rows after cleaning: " + str(rows_after)
    + ". Safe return used: " + str(safe_return_percent) + "% per year."
)

# the small title of this part
st.subheader("Summary")
# explain in simple words what the reader sees
st.caption("What this shows: one line for every fund, with its growth and its risk since the start date.")
# make a copy of the summary table, because we change only the copy for the screen
summary_display = summary.copy()
# change the yearly growth into percent, and keep two numbers after the point
summary_display["cagr"] = (summary_display["cagr"] * 100).round(2)
# change the volatility into percent, and keep two numbers after the point
summary_display["volatility"] = (summary_display["volatility"] * 100).round(2)
# change the biggest fall into percent, and keep two numbers after the point
summary_display["max_drawdown"] = (summary_display["max_drawdown"] * 100).round(2)
# keep two numbers after the point for the Sharpe ratio
summary_display["sharpe"] = summary_display["sharpe"].round(2)
# give the columns names that a normal person can read
summary_display = summary_display.rename(columns={
    "ticker": "Fund",
    "cagr": "Yearly growth (%)",
    "volatility": "Volatility (%)",
    "sharpe": "Sharpe ratio",
    "max_drawdown": "Max drawdown (%)",
})
# show the table and hide the row numbers
st.dataframe(summary_display, hide_index=True)
# explain every column in easy words
st.caption(
    "Fund is the short name of the ETF. "
    "Yearly growth is the average growth in one year. "
    "Volatility says how much the price jumps up and down, and a bigger number means more risk. "
    "Sharpe ratio is the growth above the safe return for each piece of risk, and bigger is better. "
    "Max drawdown is the biggest fall from a high price to a later low price."
)

# the small title of this part
st.subheader("Growth of 10,000")
# explain in simple words what the reader sees
st.caption("What this shows: what 10,000 dollars would be worth on every day, if you had bought the fund on the start date. The chart draws one point for each week, so it stays fast.")
# turn the growth answer into a wide table, with one column for each fund
growth_wide = growth_table.pivot(index="date", columns="ticker", values="growth")
# change the text dates in the row labels into real dates, so the chart draws time in the right way
growth_wide.index = pd.to_datetime(growth_wide.index)
# keep only the last day of every week, because 8 funds times 3000 days is too many points for the browser to draw quickly
growth_weekly = growth_wide.resample("W").last()
# change the wide table back into a long table, because altair draws from long tables
growth_long = growth_weekly.reset_index().melt(id_vars="date", var_name="ticker", value_name="growth")
# keep only the very last week of each fund, so we can write the name of the fund at the end of its line
growth_last_week = growth_long.sort_values("date").groupby("ticker", as_index=False).last()
# draw one coloured line for each fund, with dollars on the side and years at the bottom
growth_lines = alt.Chart(growth_long).mark_line(strokeWidth=2.5).encode(
    x=alt.X("date:T", title=None),
    y=alt.Y("growth:Q", title=None, axis=alt.Axis(format="$,.0f")),
    color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
    tooltip=["date:T", "ticker:N", alt.Tooltip("growth:Q", format="$,.0f")],
)
# write the name of the fund in its own colour at the end of its line, so no legend is needed
growth_names = alt.Chart(growth_last_week).mark_text(align="left", dx=7, fontSize=12, fontWeight="bold").encode(
    x=alt.X("date:T"),
    y=alt.Y("growth:Q"),
    text=alt.Text("ticker:N"),
    color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
)
# put the lines and the names on top of each other, and leave room on the right for the names
growth_chart = (growth_lines + growth_names).properties(height=380, padding={"left": 5, "top": 5, "right": 55, "bottom": 5})
# show the finished chart in the dark glass style
st.altair_chart(style_chart(growth_chart), theme=None, width="stretch")

# the small title of this part
st.subheader("Drawdown")
# explain in simple words what the reader sees
st.caption("What this shows: how far below its own best price each fund was on every day, and zero means a new best price. The chart draws the worst day of each week, so it stays fast.")
# turn the drawdown answer into a wide table, with one column for each fund
drawdown_wide = drawdown_table.pivot(index="date", columns="ticker", values="drawdown")
# change the text dates in the row labels into real dates
drawdown_wide.index = pd.to_datetime(drawdown_wide.index)
# keep the lowest number of every week, so the chart stays fast but still shows the deepest fall
drawdown_weekly = drawdown_wide.resample("W").min()
# change the wide table back into a long table, because altair draws from long tables
drawdown_long = drawdown_weekly.reset_index().melt(id_vars="date", var_name="ticker", value_name="drawdown")
# draw a filled shape under the line, with percent on the side, and make each little chart small
drawdown_area = alt.Chart(drawdown_long).mark_area(opacity=0.45, line={"strokeWidth": 1.4}).encode(
    x=alt.X("date:T", title=None, axis=alt.Axis(format="%Y", labelFontSize=9, tickCount=4)),
    y=alt.Y("drawdown:Q", title=None, axis=alt.Axis(format="%")),
    color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
    tooltip=["date:T", "ticker:N", alt.Tooltip("drawdown:Q", format=".1%")],
).properties(width=250, height=150)
# repeat that little chart once for every fund, and put four of them in each row
drawdown_chart = drawdown_area.facet(facet=alt.Facet("ticker:N", title=None), columns=4)
# show the finished chart in the dark glass style
st.altair_chart(style_chart(drawdown_chart), theme=None, width="stretch")

# the small title of this part
st.subheader("Risk and return")
# explain in simple words what the reader sees
st.caption("What this shows: each fund is one dot, dots on the right took more risk, and dots higher up grew more.")
# draw one full colour dot for each fund, with the risk from left to right and the growth from bottom to top
risk_dots = alt.Chart(summary).mark_circle(size=180).encode(
    x=alt.X("volatility:Q", title="Risk (volatility per year)", axis=alt.Axis(format="%")),
    y=alt.Y("cagr:Q", title="Growth per year", axis=alt.Axis(format="%")),
    color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
    tooltip=["ticker:N", alt.Tooltip("volatility:Q", format=".1%"), alt.Tooltip("cagr:Q", format=".1%")],
)
# write the name of the fund just above and to the right of its dot
risk_names = risk_dots.mark_text(align="left", dx=10, dy=-10, fontSize=12, fontWeight="bold").encode(text=alt.Text("ticker:N"))
# put the dots and the names on top of each other
risk_chart = (risk_dots + risk_names).properties(height=380, padding={"left": 5, "top": 5, "right": 45, "bottom": 5})
# show the finished chart in the dark glass style
st.altair_chart(style_chart(risk_chart), theme=None, width="stretch")

# the small title of this part
st.subheader("Correlation")
# explain in simple words what the reader sees
st.caption("What this shows: how often two funds move in the same direction on the same day.")
# change the square correlation table into a long table with one row for every pair of funds
correlation_long = correlation.reset_index().melt(id_vars="ticker", var_name="other_ticker", value_name="correlation")
# the side and the bottom of this chart, written once because the squares and the numbers must sit in exactly the same place
correlation_x = alt.X("other_ticker:N", title=None, sort=list(correlation.columns), scale=alt.Scale(paddingInner=0.03))
correlation_y = alt.Y("ticker:N", title=None, sort=list(correlation.index), scale=alt.Scale(paddingInner=0.03))
# draw one full colour square for every pair, where a stronger blue means the two funds move together more
correlation_squares = alt.Chart(correlation_long).mark_rect(cornerRadius=4).encode(
    x=correlation_x,
    y=correlation_y,
    color=alt.Color("correlation:Q", scale=alt.Scale(scheme="blues", domain=[0, 1]), legend=None),
    tooltip=["ticker:N", "other_ticker:N", alt.Tooltip("correlation:Q", format=".2f")],
)
# write the number inside each square, in white letters on the strong blues and in black letters on the pale blues
correlation_numbers = alt.Chart(correlation_long).mark_text(fontSize=12, fontWeight="bold").encode(
    x=correlation_x,
    y=correlation_y,
    text=alt.Text("correlation:Q", format=".2f"),
    color=alt.condition("datum.correlation > 0.55", alt.value("#ffffff"), alt.value("#10131c")),
)
# put the numbers on top of the squares
correlation_chart = (correlation_squares + correlation_numbers).properties(height=380)
# show the finished chart in the dark glass style
st.altair_chart(style_chart(correlation_chart), theme=None, width="stretch")
# explain the three important numbers
st.caption(
    "A number near 1 means that the two funds almost always move the same way. "
    "A number near 0 means that they move without a clear link. "
    "A number near -1 means that one goes up when the other goes down."
)

# the small title of this part
st.subheader("Year by year")
# explain in simple words what the reader sees
st.caption("What this shows: the growth of each fund in each year. Blue means the fund went up, and red means it went down.")
# the side and the bottom of this chart, written once because the squares and the numbers must sit in exactly the same place
yearly_x = alt.X("year:N", title=None, axis=alt.Axis(orient="top", labelAngle=0), scale=alt.Scale(paddingInner=0.03))
yearly_y = alt.Y("ticker:N", title=None, sort=sorted(yearly_returns["ticker"].unique()), scale=alt.Scale(paddingInner=0.03))
# draw one full colour square for every fund and every year, with blue for a gain and red for a loss
yearly_squares = alt.Chart(yearly_returns).mark_rect(cornerRadius=4).encode(
    x=yearly_x,
    y=yearly_y,
    color=alt.Color("yearly_return:Q", scale=alt.Scale(scheme="redblue", domainMid=0), legend=None),
    tooltip=["ticker:N", "year:N", alt.Tooltip("yearly_return:Q", format=".1%")],
)
# write the growth inside each square, in white letters on the strong colours and in black letters on the pale ones
yearly_numbers = alt.Chart(yearly_returns).mark_text(fontSize=12, fontWeight="bold").encode(
    x=yearly_x,
    y=yearly_y,
    text=alt.Text("yearly_return:Q", format=".0%"),
    color=alt.condition("abs(datum.yearly_return) > 0.20", alt.value("#ffffff"), alt.value("#10131c")),
)
# put the numbers on top of the squares
yearly_chart = (yearly_squares + yearly_numbers).properties(height=330)
# show the finished chart in the dark glass style
st.altair_chart(style_chart(yearly_chart), theme=None, width="stretch")
# warn the reader that the first year and the last year are not whole years
st.caption("The first year starts on your start date and the last year stops today, so those two years are shorter than the others.")
