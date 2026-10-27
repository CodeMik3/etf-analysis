# This file turns the three SQL answers into the numbers that the page shows.
# It makes the summary table, the correlation table and the growth of every single year.

# bring in pandas, the library that works with tables of data
import pandas as pd
# bring in our own settings, so we know how many days a trading year has
from src import config


# This function builds the summary table, with one row for every fund.
# It needs the clean prices, the daily changes, the drawdowns, and the safe return as a decimal.
def build_summary(prices, daily_return_table, drawdown_table, risk_free_rate):
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
        volatility = fund_returns.std() * (config.TRADING_DAYS ** 0.5)
        # the Sharpe ratio: the growth above the safe return, divided by the risk
        sharpe = (fund_returns.mean() * config.TRADING_DAYS - risk_free_rate) / volatility
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
    return pd.DataFrame(summary_rows)


# This function measures how much the funds move together on the same day.
def build_correlation(daily_return_table):
    # turn the daily changes into a wide table, with the dates as rows and one column for each fund
    returns_wide = daily_return_table.pivot(index="date", columns="ticker", values="daily_return")
    # measure how much the funds move together, and keep two numbers after the point
    return returns_wide.corr().round(2)


# This function works out how much each fund grew in each calendar year.
def build_yearly_returns(daily_return_table):
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
    # give the finished table back
    return yearly_returns
