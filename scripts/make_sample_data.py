# This script makes the file sample_data/prices.csv.
# The app reads that file when Yahoo Finance does not answer, so the page still works without the internet.
# Run it from the project folder with:  python scripts/make_sample_data.py

# bring in os, to build the path of the file we write
import os
# bring in sys, so we can add the project folder to the import path
import sys
# bring in yfinance, the library that downloads prices from Yahoo Finance
import yfinance as yf
# bring in pandas, the library that works with tables of data
import pandas as pd

# work out where the project folder is, which is one step above this script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# add the project folder to the import path, so that "from src import config" works
sys.path.insert(0, PROJECT_ROOT)

# bring in our own settings, so the sample uses the same funds and the same start date as the app
from src import config


# This function downloads the prices and writes them as a simple csv file with three columns.
def main():
    # say what is happening, because the download takes a few seconds
    print("Downloading prices for:", ", ".join(config.FUNDS))
    # ask Yahoo Finance for the prices of all the funds, from the start date until today
    raw = yf.download(config.FUNDS, start=config.START_DATE, auto_adjust=True, progress=False)
    # keep only the "Close" part, which is the price at the end of each day
    close = raw["Close"].reset_index()
    # change the wide table into a long table, with one row for each fund on each day
    prices = close.melt(id_vars="Date", var_name="ticker", value_name="price")
    # rename the column "Date" to "date", so every column name is lower case
    prices = prices.rename(columns={"Date": "date"})
    # remove the rows with no price, because a fund may be younger than the start date
    prices = prices.dropna(subset=["price"])
    # write the date as simple text that looks like 2026-10-27
    prices["date"] = pd.to_datetime(prices["date"]).dt.strftime("%Y-%m-%d")
    # keep four numbers after the point, which is enough and keeps the file small
    prices["price"] = prices["price"].round(4)
    # sort the rows by fund and then by date
    prices = prices.sort_values(["ticker", "date"])
    # make sure the folder exists before we write into it
    os.makedirs(os.path.dirname(config.BACKUP_PRICES_PATH), exist_ok=True)
    # write the file without the row numbers
    prices.to_csv(config.BACKUP_PRICES_PATH, index=False)
    # say how many rows were written and where they went
    print("Wrote", len(prices), "rows to", config.BACKUP_PRICES_PATH)


# only run the download when this file is started on purpose, not when something imports it
if __name__ == "__main__":
    main()
