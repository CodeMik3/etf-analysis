# These tests check the numbers in the summary table, the correlation table and the yearly growth.
# Run them with: pytest

# bring in pandas, to build small tables by hand
import pandas as pd
# bring in pytest, which gives us the approx helper for comparing decimal numbers
import pytest
# bring in the parts that we want to test
from src.database import store_prices
from src.queries import run_queries
from src.metrics import build_summary, build_correlation, build_yearly_returns


# This function builds one fund whose price doubles in exactly one year, with a day in the middle.
def make_one_year_of_prices():
    return pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-07-01", "2021-01-01"],
            "ticker": ["VTI", "VTI", "VTI"],
            "price": [100.0, 150.0, 200.0],
        }
    )


# a price that doubles in about one year is a yearly growth of about one hundred percent
def test_yearly_growth_of_a_price_that_doubles():
    prices = make_one_year_of_prices()
    daily_return_table, _, drawdown_table = run_queries(store_prices(prices))
    summary = build_summary(prices, daily_return_table, drawdown_table, 0.0)
    assert summary["cagr"][0] == pytest.approx(1.0, abs=0.01)


# the worst drawdown of a price that only goes up must be zero
def test_max_drawdown_of_a_price_that_only_rises():
    prices = make_one_year_of_prices()
    daily_return_table, _, drawdown_table = run_queries(store_prices(prices))
    summary = build_summary(prices, daily_return_table, drawdown_table, 0.0)
    assert summary["max_drawdown"][0] == pytest.approx(0.0)


# the summary must have exactly one row for each fund, named in the column ticker
def test_summary_has_one_row_for_each_fund():
    prices = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-01-02"] * 3,
            "ticker": ["VTI", "VTI", "VOO", "VOO", "BND", "BND"],
            "price": [100.0, 101.0, 300.0, 303.0, 70.0, 70.7],
        }
    )
    daily_return_table, _, drawdown_table = run_queries(store_prices(prices))
    summary = build_summary(prices, daily_return_table, drawdown_table, 0.02)
    assert len(summary) == 3
    assert sorted(summary["ticker"]) == ["BND", "VOO", "VTI"]


# a bigger safe return must make the Sharpe ratio smaller, because the safe return is taken away from the growth
def test_a_higher_safe_return_lowers_the_sharpe_ratio():
    prices = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"],
            "ticker": ["VTI", "VTI", "VTI", "VTI"],
            "price": [100.0, 102.0, 101.0, 104.0],
        }
    )
    daily_return_table, _, drawdown_table = run_queries(store_prices(prices))
    low_safe_return = build_summary(prices, daily_return_table, drawdown_table, 0.00)
    high_safe_return = build_summary(prices, daily_return_table, drawdown_table, 0.05)
    assert high_safe_return["sharpe"][0] < low_safe_return["sharpe"][0]


# two funds that move exactly the same way must have a correlation of 1.
# The prices must go up and then down, because a fund that changes by the same amount every day has no
# movement to compare and the correlation of two flat lines cannot be worked out at all.
def test_two_funds_that_move_together_have_correlation_one():
    prices = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-01-02", "2020-01-03"] * 2,
            "ticker": ["VTI", "VTI", "VTI", "VOO", "VOO", "VOO"],
            "price": [100.0, 110.0, 99.0, 200.0, 220.0, 198.0],
        }
    )
    daily_return_table, _, _ = run_queries(store_prices(prices))
    correlation = build_correlation(daily_return_table)
    assert correlation.loc["VTI", "VOO"] == pytest.approx(1.0)


# every fund must always have a correlation of 1 with itself
def test_a_fund_correlates_perfectly_with_itself():
    prices = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-01-02", "2020-01-03"],
            "ticker": ["VTI", "VTI", "VTI"],
            "price": [100.0, 110.0, 99.0],
        }
    )
    daily_return_table, _, _ = run_queries(store_prices(prices))
    correlation = build_correlation(daily_return_table)
    assert correlation.loc["VTI", "VTI"] == pytest.approx(1.0)


# the yearly growth must multiply the daily changes inside one year, and must split the years apart
def test_yearly_growth_is_counted_for_each_year_on_its_own():
    prices = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-12-31", "2021-12-31"],
            "ticker": ["VTI", "VTI", "VTI"],
            "price": [100.0, 120.0, 60.0],
        }
    )
    daily_return_table, _, _ = run_queries(store_prices(prices))
    yearly_returns = build_yearly_returns(daily_return_table)
    year_2020 = yearly_returns[yearly_returns["year"] == "2020"]["yearly_return"].iloc[0]
    year_2021 = yearly_returns[yearly_returns["year"] == "2021"]["yearly_return"].iloc[0]
    # 100 grows to 120 inside 2020, which is a rise of twenty percent
    assert year_2020 == pytest.approx(0.20)
    # 120 falls to 60 inside 2021, which is a fall of fifty percent
    assert year_2021 == pytest.approx(-0.50)
