# This file draws the three questions in the sidebar and reads back what the user chose.

# bring in Streamlit, the library that turns Python code into a web page
import streamlit as st
# bring in pandas, because we turn the start date text into a real date
import pandas as pd
# bring in datetime, which lets us work with dates
import datetime
# bring in our own settings, so the sidebar shows the funds and the numbers from one place
from src import config


# This function draws the sidebar and gives back four things that the rest of the page needs:
# the chosen funds, the start date, the safe return in percent, and the same safe return as a decimal.
def choose_settings():
    # write a small title at the top of the sidebar
    st.sidebar.header("Your choices")
    # let the user pick one or more funds, and start with all of them picked
    chosen_funds = st.sidebar.multiselect("Funds", config.FUNDS, default=config.FUNDS)
    # let the user pick the first date, and allow any date between 2012 and today
    start_date = st.sidebar.date_input(
        "Start date",
        value=pd.to_datetime(config.START_DATE).date(),
        min_value=pd.to_datetime(config.EARLIEST_DATE).date(),
        max_value=datetime.date.today(),
    )
    # let the user say how much a very safe investment earns in one year
    safe_return_percent = st.sidebar.number_input(
        "Safe return (% per year)",
        min_value=0.0,
        max_value=10.0,
        step=0.1,
        value=config.DEFAULT_SAFE_RETURN_PERCENT,
    )
    # change the percent into a decimal number, because the Sharpe ratio needs a decimal
    risk_free_rate = safe_return_percent / 100
    # give the four answers back together
    return chosen_funds, start_date, safe_return_percent, risk_free_rate
