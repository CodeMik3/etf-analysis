# This file holds every setting of the app in one place.
# If you want to change a fund, a date or a number, you change it here and nowhere else.

# bring in os, which lets us build file paths that work on Windows, on Mac and on Linux
import os

# the folder that holds the whole project, worked out from the place of this file
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the saved price file that the app reads when Yahoo Finance does not answer
BACKUP_PRICES_PATH = os.path.join(PROJECT_ROOT, "sample_data", "prices.csv")

# the list of funds that the user can choose from
FUNDS = ["VTI", "VOO", "VGT", "VYM", "VXUS", "VWO", "BND", "VNQ"]
# the first date that we ask Yahoo Finance about
START_DATE = "2015-01-01"
# the oldest date that the user is allowed to choose
EARLIEST_DATE = "2012-01-01"
# the yearly return of a very safe investment, written in percent
DEFAULT_SAFE_RETURN_PERCENT = 2.0
# the number of days in one year when the stock market is open
TRADING_DAYS = 252
# how many rows must be left after the cleaning, or the app stops and asks for an earlier start date
MINIMUM_ROWS = 30
