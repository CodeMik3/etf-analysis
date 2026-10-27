# This file gets the prices.
# It first asks Yahoo Finance, and if Yahoo does not answer it reads the saved file in the sample_data folder.

# bring in Streamlit, because the download is saved for one day with a Streamlit tool
import streamlit as st
# bring in yfinance, the library that downloads prices from Yahoo Finance
import yfinance as yf
# bring in pandas, the library that works with tables of data
import pandas as pd
# bring in os, which lets us ask if a file exists on the computer
import os
# bring in our own settings, so we know where the saved file is
from src import config


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


# This function reads the saved price file and keeps only the rows that the user asked for.
# If there is no saved file, it gives back an empty table.
def read_backup_prices(funds, start):
    # if the saved file is not on the computer, there is nothing to read
    if not os.path.exists(config.BACKUP_PRICES_PATH):
        # give back an empty table, which tells the caller that there is no backup
        return pd.DataFrame()
    # read the saved file, which has the columns date, ticker and price
    prices = pd.read_csv(config.BACKUP_PRICES_PATH)
    # keep only the rows of the funds that the user chose
    prices = prices[prices["ticker"].isin(list(funds))]
    # keep only the rows on the start date or after the start date
    prices = prices[pd.to_datetime(prices["date"]) >= pd.to_datetime(start)]
    # give the rows back
    return prices


# This function is the one the page calls.
# It gives back two things: the price table, and a word that says where the prices came from.
# The word is "yahoo", or "backup" when the saved file was used, or "nothing" when there are no prices at all.
def load_prices(funds, start):
    # try the download, and catch any problem, so that the page does not crash
    try:
        # call the download, and pass the funds as a tuple, because the saved answer needs a tuple
        prices = download_prices(tuple(funds), start)
        # an empty answer is also a failure, so we make an error on purpose
        if prices.empty:
            # raise means "stop here and jump to the except part below"
            raise ValueError("Yahoo Finance sent back no rows.")
        # if the program is still here, the download worked
        return prices, "yahoo"
    except Exception:
        # Yahoo did not answer, so try the saved file instead
        backup = read_backup_prices(funds, start)
        # if the saved file gave us rows, use them
        if len(backup) > 0:
            # say that these prices come from the saved file
            return backup, "backup"
        # there is no Yahoo answer and no saved file either
        return pd.DataFrame(), "nothing"
