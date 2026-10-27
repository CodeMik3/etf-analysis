# These tests check the three SQL window functions on a tiny table where the right answer can be worked out by hand.
# The prices of VTI are 100, 110, 99, 105 and the prices of BND are 70 on every day.
# Run them with: pytest

# bring in pandas, to build small tables by hand
import pandas as pd
# bring in pytest, which gives us the approx helper for comparing decimal numbers
import pytest
# bring in the parts that we want to test
from src.database import store_prices
from src.queries import run_queries


# This function builds the tiny price table and puts it into a database in memory.
def make_small_database():
    prices = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"] * 2,
            "ticker": ["VTI", "VTI", "VTI", "VTI", "BND", "BND", "BND", "BND"],
            "price": [100.0, 110.0, 99.0, 105.0, 70.0, 70.0, 70.0, 70.0],
        }
    )
    return store_prices(prices)


# the first day of a fund has no day before it, so its daily return must be empty
def test_first_day_has_no_daily_return():
    daily_return_table, _, _ = run_queries(make_small_database())
    first_row_of_vti = daily_return_table[daily_return_table["ticker"] == "VTI"].iloc[0]
    assert pd.isna(first_row_of_vti["daily_return"])


# 110 after 100 is a rise of ten percent, and 99 after 110 is a fall of ten percent
def test_daily_return_uses_the_day_before():
    daily_return_table, _, _ = run_queries(make_small_database())
    vti = daily_return_table[daily_return_table["ticker"] == "VTI"].reset_index(drop=True)
    assert vti["daily_return"][1] == pytest.approx(0.10)
    assert vti["daily_return"][2] == pytest.approx(-0.10)


# each fund must use only its own prices, so BND never borrows the first price of VTI
def test_partition_by_keeps_the_funds_apart():
    _, growth_table, _ = run_queries(make_small_database())
    bnd = growth_table[growth_table["ticker"] == "BND"]
    assert list(bnd["growth"]) == [10000.0, 10000.0, 10000.0, 10000.0]


# 10000 dollars at a price of 100 becomes 11000 dollars when the price reaches 110
def test_growth_is_measured_from_the_first_price():
    _, growth_table, _ = run_queries(make_small_database())
    vti = growth_table[growth_table["ticker"] == "VTI"].reset_index(drop=True)
    assert vti["growth"][0] == pytest.approx(10000.0)
    assert vti["growth"][1] == pytest.approx(11000.0)
    assert vti["growth"][3] == pytest.approx(10500.0)


# the drawdown is zero on a new best price, and negative once the price falls below the best price
def test_drawdown_is_measured_from_the_best_price_so_far():
    _, _, drawdown_table = run_queries(make_small_database())
    vti = drawdown_table[drawdown_table["ticker"] == "VTI"].reset_index(drop=True)
    assert vti["drawdown"][0] == pytest.approx(0.0)
    assert vti["drawdown"][1] == pytest.approx(0.0)
    assert vti["drawdown"][2] == pytest.approx(99.0 / 110.0 - 1)
    assert vti["drawdown"][3] == pytest.approx(105.0 / 110.0 - 1)


# the drawdown must never be a positive number, because a price cannot be above its own best price
def test_drawdown_is_never_positive():
    _, _, drawdown_table = run_queries(make_small_database())
    assert (drawdown_table["drawdown"] <= 0).all()


# the last day of VTI is 105 while its best price was 110, so the running maximum must not look into the future
def test_running_maximum_does_not_look_ahead():
    prices = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-01-02", "2020-01-03"],
            "ticker": ["VTI", "VTI", "VTI"],
            "price": [100.0, 90.0, 200.0],
        }
    )
    _, _, drawdown_table = run_queries(store_prices(prices))
    # on the second day the best price so far is still 100, not the 200 that comes later
    assert drawdown_table["drawdown"][1] == pytest.approx(-0.10)
    # on the last day the price itself is the new best price, so the drawdown is zero
    assert drawdown_table["drawdown"][2] == pytest.approx(0.0)
