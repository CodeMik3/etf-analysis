# This file cleans the price table.
# It throws away the rows that are wrong or repeated, and it puts the rest in a clear order.

# bring in pandas, the library that works with tables of data
import pandas as pd


# This function takes a raw price table and gives back a clean copy of it.
# The steps always happen in this order: missing prices, wrong prices, repeated rows, dates, sorting.
def clean_prices(prices):
    # work on a copy, so that the table that came in is not changed
    clean = prices.copy()
    # remove every row where the price is missing
    clean = clean.dropna(subset=["price"])
    # remove every row where the price is zero or less, because such a price is wrong
    clean = clean[clean["price"] > 0]
    # remove rows that say the same thing twice about one fund on one day
    clean = clean.drop_duplicates(subset=["date", "ticker"])
    # change the date into simple text that looks like 2026-10-27
    clean["date"] = pd.to_datetime(clean["date"]).dt.strftime("%Y-%m-%d")
    # sort the table by fund and then by date, and give the rows new row numbers
    clean = clean.sort_values(["ticker", "date"]).reset_index(drop=True)
    # give the clean table back to the part of the program that called this function
    return clean
