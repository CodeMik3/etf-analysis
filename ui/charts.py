# This file builds the five charts.
# Each function takes a table of numbers and gives back a finished chart that the page can show.

# bring in altair, the drawing library that already comes inside Streamlit
import altair as alt
# bring in pandas, because the charts need real dates and weekly points
import pandas as pd
# bring in our own look, so every chart uses the same colours
from ui.theme import CHART_COLOURS, style_chart


# This function draws the value of 10000 dollars over time, with the name of each fund at the end of its line.
def growth_chart(growth_table):
    # turn the growth answer into a wide table, with one column for each fund
    growth_wide = growth_table.pivot(index="date", columns="ticker", values="growth")
    # change the text dates in the row labels into real dates, so the chart draws time in the right way
    growth_wide.index = pd.to_datetime(growth_wide.index)
    # keep only the last day of every week, because 8 funds times 3000 days is too many points for the browser to draw quickly
    growth_weekly = growth_wide.resample("W").last()
    # change the wide table back into a long table, because altair draws from long tables
    growth_long = growth_weekly.reset_index().melt(id_vars="date", var_name="ticker", value_name="growth")
    # keep only the very last week of each fund, so we can write the name of the fund at the end of its line
    growth_last_week = growth_long.sort_values("date").groupby("ticker", as_index=False).last()
    # draw one coloured line for each fund, with dollars on the side and years at the bottom
    growth_lines = alt.Chart(growth_long).mark_line(strokeWidth=2.5).encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("growth:Q", title=None, axis=alt.Axis(format="$,.0f")),
        color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
        tooltip=["date:T", "ticker:N", alt.Tooltip("growth:Q", format="$,.0f")],
    )
    # write the name of the fund in its own colour at the end of its line, so no legend is needed
    growth_names = alt.Chart(growth_last_week).mark_text(align="left", dx=7, fontSize=12, fontWeight="bold").encode(
        x=alt.X("date:T"),
        y=alt.Y("growth:Q"),
        text=alt.Text("ticker:N"),
        color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
    )
    # put the lines and the names on top of each other, and leave room on the right for the names
    chart = (growth_lines + growth_names).properties(height=380, padding={"left": 5, "top": 5, "right": 55, "bottom": 5})
    # give the chart back in the dark style of the page
    return style_chart(chart)


# This function draws one small chart for every fund, showing how far it was below its own best price.
def drawdown_chart(drawdown_table):
    # turn the drawdown answer into a wide table, with one column for each fund
    drawdown_wide = drawdown_table.pivot(index="date", columns="ticker", values="drawdown")
    # change the text dates in the row labels into real dates
    drawdown_wide.index = pd.to_datetime(drawdown_wide.index)
    # keep the lowest number of every week, so the chart stays fast but still shows the deepest fall
    drawdown_weekly = drawdown_wide.resample("W").min()
    # change the wide table back into a long table, because altair draws from long tables
    drawdown_long = drawdown_weekly.reset_index().melt(id_vars="date", var_name="ticker", value_name="drawdown")
    # draw a filled shape under the line, with percent on the side, and make each little chart small
    drawdown_area = alt.Chart(drawdown_long).mark_area(opacity=0.45, line={"strokeWidth": 1.4}).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%Y", labelFontSize=9, tickCount=4)),
        y=alt.Y("drawdown:Q", title=None, axis=alt.Axis(format="%")),
        color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
        tooltip=["date:T", "ticker:N", alt.Tooltip("drawdown:Q", format=".1%")],
    ).properties(width=250, height=150)
    # repeat that little chart once for every fund, and put four of them in each row
    chart = drawdown_area.facet(facet=alt.Facet("ticker:N", title=None), columns=4)
    # give the chart back in the dark style of the page
    return style_chart(chart)


# This function draws one dot for every fund: the risk from left to right and the growth from bottom to top.
def risk_chart(summary):
    # draw one full colour dot for each fund
    risk_dots = alt.Chart(summary).mark_circle(size=180).encode(
        x=alt.X("volatility:Q", title="Risk (volatility per year)", axis=alt.Axis(format="%")),
        y=alt.Y("cagr:Q", title="Growth per year", axis=alt.Axis(format="%")),
        color=alt.Color("ticker:N", legend=None, scale=alt.Scale(scheme=CHART_COLOURS)),
        tooltip=["ticker:N", alt.Tooltip("volatility:Q", format=".1%"), alt.Tooltip("cagr:Q", format=".1%")],
    )
    # write the name of the fund just above and to the right of its dot
    risk_names = risk_dots.mark_text(align="left", dx=10, dy=-10, fontSize=12, fontWeight="bold").encode(text=alt.Text("ticker:N"))
    # put the dots and the names on top of each other
    chart = (risk_dots + risk_names).properties(height=380, padding={"left": 5, "top": 5, "right": 45, "bottom": 5})
    # give the chart back in the dark style of the page
    return style_chart(chart)


# This function draws the correlation table as coloured squares with the number written inside.
def correlation_chart(correlation):
    # change the square correlation table into a long table with one row for every pair of funds
    correlation_long = correlation.reset_index().melt(id_vars="ticker", var_name="other_ticker", value_name="correlation")
    # the side and the bottom of this chart, written once because the squares and the numbers must sit in exactly the same place
    correlation_x = alt.X("other_ticker:N", title=None, sort=list(correlation.columns), scale=alt.Scale(paddingInner=0.03))
    correlation_y = alt.Y("ticker:N", title=None, sort=list(correlation.index), scale=alt.Scale(paddingInner=0.03))
    # draw one full colour square for every pair, where a stronger blue means the two funds move together more
    correlation_squares = alt.Chart(correlation_long).mark_rect(cornerRadius=4).encode(
        x=correlation_x,
        y=correlation_y,
        color=alt.Color("correlation:Q", scale=alt.Scale(scheme="blues", domain=[0, 1]), legend=None),
        tooltip=["ticker:N", "other_ticker:N", alt.Tooltip("correlation:Q", format=".2f")],
    )
    # write the number inside each square, in white letters on the strong blues and in black letters on the pale blues
    correlation_numbers = alt.Chart(correlation_long).mark_text(fontSize=12, fontWeight="bold").encode(
        x=correlation_x,
        y=correlation_y,
        text=alt.Text("correlation:Q", format=".2f"),
        color=alt.condition("datum.correlation > 0.55", alt.value("#ffffff"), alt.value("#10131c")),
    )
    # put the numbers on top of the squares
    chart = (correlation_squares + correlation_numbers).properties(height=380)
    # give the chart back in the dark style of the page
    return style_chart(chart)


# This function draws the growth of every fund in every calendar year, blue for a gain and red for a loss.
def yearly_chart(yearly_returns):
    # the side and the bottom of this chart, written once because the squares and the numbers must sit in exactly the same place
    yearly_x = alt.X("year:N", title=None, axis=alt.Axis(orient="top", labelAngle=0), scale=alt.Scale(paddingInner=0.03))
    yearly_y = alt.Y("ticker:N", title=None, sort=sorted(yearly_returns["ticker"].unique()), scale=alt.Scale(paddingInner=0.03))
    # draw one full colour square for every fund and every year
    yearly_squares = alt.Chart(yearly_returns).mark_rect(cornerRadius=4).encode(
        x=yearly_x,
        y=yearly_y,
        color=alt.Color("yearly_return:Q", scale=alt.Scale(scheme="redblue", domainMid=0), legend=None),
        tooltip=["ticker:N", "year:N", alt.Tooltip("yearly_return:Q", format=".1%")],
    )
    # write the growth inside each square, in white letters on the strong colours and in black letters on the pale ones
    yearly_numbers = alt.Chart(yearly_returns).mark_text(fontSize=12, fontWeight="bold").encode(
        x=yearly_x,
        y=yearly_y,
        text=alt.Text("yearly_return:Q", format=".0%"),
        color=alt.condition("abs(datum.yearly_return) > 0.20", alt.value("#ffffff"), alt.value("#10131c")),
    )
    # put the numbers on top of the squares
    chart = (yearly_squares + yearly_numbers).properties(height=330)
    # give the chart back in the dark style of the page
    return style_chart(chart)
