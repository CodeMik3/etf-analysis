# This file decides how the page looks: the dark glass style of the page, and the colours of the charts.
# It holds no numbers about money, only looks.

# bring in Streamlit, because the style is put on the page with a Streamlit command
import streamlit as st

# the colours of the eight lines and dots, and the three greys that the charts use for text, grid lines and axis lines
CHART_COLOURS = "tableau10"
TEXT_GREY = "#d9d9d9"
GRID_GREY = "rgba(255, 255, 255, 0.10)"
AXIS_GREY = "rgba(255, 255, 255, 0.28)"

# The long text below is CSS, not Python. CSS is the language that tells the browser how the page should look.
# Every rule says: pick a part of the page, then change its colour, its corners, or its blur.
LIQUID_GLASS_CSS = """
<style>

/* the whole page: soft grey lights on a black sheet, and the lights do not move, so nothing gets slow */
.stApp {
    background:
        radial-gradient(1100px 760px at 8% 0%, rgba(255, 255, 255, 0.16), transparent 60%),
        radial-gradient(900px 680px at 95% 12%, rgba(255, 255, 255, 0.10), transparent 60%),
        radial-gradient(1000px 820px at 50% 108%, rgba(255, 255, 255, 0.08), transparent 60%),
        linear-gradient(165deg, #000000 0%, #141414 55%, #000000 100%);
    background-attachment: fixed;
}

/* the thin bar at the very top of the page: see-through with a light blur */
[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

/* the sidebar: one tall sheet of frosted glass */
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.07) !important;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border-right: 1px solid rgba(255, 255, 255, 0.12);
}

/* the boxes inside the sidebar must stay see-through, or they would hide the glass */
[data-testid="stSidebar"] > div {
    background: transparent !important;
}

/* the main column: one big piece of glass that holds all the results, with only a small gap on the left and the right */
.stMainBlockContainer {
    max-width: 100%;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    padding-top: 3rem;
    margin-left: 1rem;
    margin-right: 1rem;
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(22px) saturate(160%);
    -webkit-backdrop-filter: blur(22px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 28px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.60), inset 0 1px 0 rgba(255, 255, 255, 0.32);
}

/* the tables, the charts and the messages: smaller pieces of glass inside the big one */
[data-testid="stDataFrame"],
[data-testid="stVegaLiteChart"],
[data-testid="stAlertContainer"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 20px;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.50),
        inset 0 -1px 0 rgba(255, 255, 255, 0.18),
        0 10px 34px rgba(0, 0, 0, 0.45);
    overflow: hidden;
}

/* the boxes in the sidebar where you choose the funds, the date and the safe return */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] {
    background: rgba(255, 255, 255, 0.10) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 14px !important;
}

/* the small labels of the funds that you picked: only the corners are changed here, because the colour comes from config.toml */
[data-testid="stMultiSelectTagsContainer"] div {
    border-radius: 11px;
}

/* the titles get a soft white light behind the letters */
.stApp h1, .stApp h2, .stApp h3 {
    color: #ffffff;
    text-shadow: 0 2px 22px rgba(255, 255, 255, 0.30);
}

</style>
"""


# This function must run before anything else is drawn.
# It names the browser tab, lets the page use the whole screen, and puts the glass style on the page.
def configure_page():
    # give the page a name in the browser tab, and let the content use the whole width of the screen
    st.set_page_config(page_title="Vanguard ETF Analysis", page_icon="📈", layout="wide")
    # put the CSS on the page, and allow HTML so that the browser reads it as a style and not as text
    st.markdown(LIQUID_GLASS_CSS, unsafe_allow_html=True)


# This function gives every chart the same dark look, so we do not have to repeat these lines five times.
# It takes a finished chart, changes the colours of the text and the lines around it, and gives the chart back.
def style_chart(chart):
    # make the area behind the chart see-through, so the glass of the page shows through it
    chart = chart.configure(background="transparent")
    # remove the box around the drawing area
    chart = chart.configure_view(strokeWidth=0, fill=None)
    # make the numbers, the titles and the thin grid lines light grey instead of black
    chart = chart.configure_axis(
        labelColor=TEXT_GREY,
        titleColor=TEXT_GREY,
        gridColor=GRID_GREY,
        domainColor=AXIS_GREY,
        tickColor=AXIS_GREY,
        labelFontSize=12,
        titleFontSize=12,
    )
    # make the small title above each little chart white and bold
    chart = chart.configure_header(labelColor="#ffffff", titleColor="#ffffff", labelFontWeight="bold")
    # give the chart back to the part of the program that called this function
    return chart
