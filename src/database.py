# This file puts the clean prices into a small SQL database.
# The database lives only in the memory of the computer, so no file is ever saved on the disk.

# bring in sqlite3, the small database that already comes inside Python
import sqlite3

# the SQL command that makes the empty table, where one fund together with one date can appear only once
CREATE_TABLE_SQL = "CREATE TABLE prices (date TEXT, ticker TEXT, price REAL, PRIMARY KEY (ticker, date))"


# This function makes a new database, copies the clean table into it, and gives the open database back.
def store_prices(prices):
    # make a database that lives only in the memory of the computer
    connection = sqlite3.connect(":memory:")
    # create the empty table inside that database
    connection.execute(CREATE_TABLE_SQL)
    # copy every row of the clean pandas table into the database table
    prices.to_sql("prices", connection, if_exists="append", index=False)
    # give the open database back to the part of the program that called this function
    return connection
