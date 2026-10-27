# These tests check that the cleaning step really throws away the bad rows.
# Run them with: pytest

# bring in pandas, to build small tables by hand
import pandas as pd
# bring in the function that we want to test
from src.cleaning import clean_prices


# This function builds a tiny messy table that has one example of every problem.
def make_messy_prices():
    # three good rows, one missing price, one price of zero, one negative price, and one repeated row
    return pd.DataFrame(
        {
            "date": ["2020-01-03", "2020-01-02", "2020-01-02", "2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09"],
            "ticker": ["VTI", "VTI", "VTI", "VTI", "VTI", "VTI", "VTI"],
            "price": [102.0, 100.0, 100.0, None, 0.0, -5.0, 105.0],
        }
    )


# a row with no price must be removed
def test_missing_price_is_removed():
    clean = clean_prices(make_messy_prices())
    assert "2020-01-06" not in list(clean["date"])


# a price of zero and a price below zero are both impossible, so both must be removed
def test_zero_and_negative_prices_are_removed():
    clean = clean_prices(make_messy_prices())
    assert (clean["price"] > 0).all()
    # seven rows go in, and four of them are bad: the missing one, the zero, the negative one and the repeat
    assert len(clean) == 3


# the same fund on the same day must appear only once
def test_duplicate_day_is_removed():
    clean = clean_prices(make_messy_prices())
    only_second_of_january = clean[clean["date"] == "2020-01-02"]
    assert len(only_second_of_january) == 1


# the rows must come out sorted by fund and then by date
def test_rows_are_sorted_by_ticker_then_date():
    messy = pd.DataFrame(
        {
            "date": ["2020-01-02", "2020-01-01", "2020-01-02", "2020-01-01"],
            "ticker": ["VOO", "VTI", "VTI", "VOO"],
            "price": [300.0, 150.0, 151.0, 299.0],
        }
    )
    clean = clean_prices(messy)
    assert list(clean["ticker"]) == ["VOO", "VOO", "VTI", "VTI"]
    assert list(clean["date"]) == ["2020-01-01", "2020-01-02", "2020-01-01", "2020-01-02"]


# dates that arrive in different shapes must all come out as text like 2020-01-02
def test_dates_become_plain_text():
    messy = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-02 16:00:00"), "2020/01/03"],
            "ticker": ["VTI", "VTI"],
            "price": [100.0, 101.0],
        }
    )
    clean = clean_prices(messy)
    assert list(clean["date"]) == ["2020-01-02", "2020-01-03"]


# the table that goes in must not be changed by the cleaning
def test_original_table_is_not_changed():
    messy = make_messy_prices()
    rows_before = len(messy)
    clean_prices(messy)
    assert len(messy) == rows_before
