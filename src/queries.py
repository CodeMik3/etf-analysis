# This file holds the three questions that we ask the database with SQL.
# All three use a window function, which means: stay on this row, but look at the other rows around it.

# bring in pandas, the library that works with tables of data
import pandas as pd

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


# This function runs all three questions on the open database and gives back three pandas tables.
def run_queries(connection):
    # run the first question and keep the answer in a pandas table
    daily_return_table = pd.read_sql_query(DAILY_RETURN_SQL, connection)
    # run the second question and keep the answer in a pandas table
    growth_table = pd.read_sql_query(GROWTH_SQL, connection)
    # run the third question and keep the answer in a pandas table
    drawdown_table = pd.read_sql_query(DRAWDOWN_SQL, connection)
    # give the three tables back together
    return daily_return_table, growth_table, drawdown_table
