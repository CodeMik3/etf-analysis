# This app studies a few Vanguard ETFs, which are baskets of shares that you can buy like one share.
# It downloads the daily prices from Yahoo Finance, cleans them, keeps them in a small SQL database, and asks the database three questions.
# At the end it shows one table and five charts, so you can compare how much each fund grew and how much risk it took.
#
# This file only tells the story from top to bottom. The real work lives in two folders:
# the folder src holds the numbers and the SQL, and the folder ui holds everything you see.

# bring in Streamlit, the library that turns Python code into a web page
import streamlit as st
# bring in our own settings
from src import config
# bring in the part that gets the prices from Yahoo Finance or from the saved file
from src.data_loader import load_prices
# bring in the part that throws away the wrong rows
from src.cleaning import clean_prices
# bring in the part that puts the clean rows into a small SQL database
from src.database import store_prices
# bring in the part that asks the database the three questions
from src.queries import run_queries
# bring in the part that turns the answers into the numbers we show
from src.metrics import build_summary, build_correlation, build_yearly_returns
# bring in the look of the page
from ui.theme import configure_page
# bring in the three questions in the sidebar
from ui.sidebar import choose_settings
# bring in the five charts
from ui.charts import growth_chart, drawdown_chart, risk_chart, correlation_chart, yearly_chart


# STEP 0: MAKE THE PAGE LOOK RIGHT AND ASK THE USER WHAT TO SHOW

# name the browser tab, use the whole width of the screen, and put the dark glass style on the page
configure_page()
# draw the sidebar and read back what the user chose
chosen_funds, start_date, safe_return_percent, risk_free_rate = choose_settings()

# if the user removed every fund, there is nothing to study
if len(chosen_funds) == 0:
    # show a yellow message that asks for at least one fund
    st.warning("Please choose at least one fund in the sidebar.")
    # stop the program here, so the rest of the page does not run
    st.stop()


# STEP 1: GET THE PRICES

# ask for the prices, and also ask where they came from
prices, price_source = load_prices(chosen_funds, start_date)

# if the saved file was used, say so, because the numbers may be a few days old
if price_source == "backup":
    # show a blue message that explains where the prices come from
    st.info("Yahoo did not answer, so this page uses the saved prices.csv file.")

# if there are no prices at all, there is nothing to show
if price_source == "nothing":
    # show a red message and ask the user to try again later
    st.error("Could not download prices from Yahoo, and there is no prices.csv backup. Please try again later.")
    # stop the program here
    st.stop()


# STEP 2: CLEAN THE PRICES

# count the rows before the cleaning, so we can tell the user how many rows we removed
rows_before = len(prices)
# throw away the rows that are missing, wrong or repeated, and sort the rest
prices = clean_prices(prices)
# count the rows after the cleaning
rows_after = len(prices)

# if almost nothing is left, the numbers would not mean anything
if rows_after < config.MINIMUM_ROWS:
    # show a red message that asks for an earlier start date
    st.error("Not enough data for these choices. Try an earlier start date.")
    # stop the program here
    st.stop()


# STEP 3: STORE THE PRICES IN SQL AND ASK THE THREE QUESTIONS

# put the clean prices into a database that lives only in the memory of the computer
connection = store_prices(prices)
# ask the three questions and keep the three answers
daily_return_table, growth_table, drawdown_table = run_queries(connection)


# STEP 4: TURN THE ANSWERS INTO NUMBERS

# build the table with one row for every fund
summary = build_summary(prices, daily_return_table, drawdown_table, risk_free_rate)
# build the table that shows which funds move together
correlation = build_correlation(daily_return_table)
# build the table with the growth of every single year
yearly_returns = build_yearly_returns(daily_return_table)


# STEP 5: SHOW THE ANSWERS

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
# draw the chart of the growth over time
st.altair_chart(growth_chart(growth_table), theme=None, width="stretch")

# the small title of this part
st.subheader("Drawdown")
# explain in simple words what the reader sees
st.caption("What this shows: how far below its own best price each fund was on every day, and zero means a new best price. The chart draws the worst day of each week, so it stays fast.")
# draw one small chart for every fund
st.altair_chart(drawdown_chart(drawdown_table), theme=None, width="stretch")

# the small title of this part
st.subheader("Risk and return")
# explain in simple words what the reader sees
st.caption("What this shows: each fund is one dot, dots on the right took more risk, and dots higher up grew more.")
# draw the dots
st.altair_chart(risk_chart(summary), theme=None, width="stretch")

# the small title of this part
st.subheader("Correlation")
# explain in simple words what the reader sees
st.caption("What this shows: how often two funds move in the same direction on the same day.")
# draw the coloured squares with the numbers inside
st.altair_chart(correlation_chart(correlation), theme=None, width="stretch")
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
# draw one coloured square for every fund and every year
st.altair_chart(yearly_chart(yearly_returns), theme=None, width="stretch")
# warn the reader that the first year and the last year are not whole years
st.caption("The first year starts on your start date and the last year stops today, so those two years are shorter than the others.")
