# ============================================================
# ADVANCED NSE STOCK RESEARCH DASHBOARD
# ============================================================

import requests
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

from ta.trend import SMAIndicator
from ta.trend import EMAIndicator
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NSE Dashboard",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

body{
    background:#0f172a;
}

.main-card{
    background:#111827;
    padding:20px;
    border-radius:18px;
    border:1px solid #374151;
    margin-bottom:15px;
}

.metric-title{
    color:#9CA3AF;
    font-size:14px;
    margin-bottom:8px;
}

.metric-value{
    color:white;
    font-size:24px;
    font-weight:bold;
}

.section-title{
    font-size:30px;
    font-weight:bold;
    margin-top:30px;
    margin-bottom:20px;
}

.company-title{
    font-size:42px;
    font-weight:bold;
    margin-top:20px;
    margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# NSE SESSION
# ============================================================

session = requests.Session()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    )
}

session.headers.update(HEADERS)

try:

    session.get(
        "https://www.nseindia.com",
        timeout=10
    )

except:
    pass

# ============================================================
# FORMATTERS
# ============================================================

def indian_format(number):

    try:

        return f"{float(number):,.2f}"

    except:

        return number

# ============================================================
# SHORT FORMAT
# ============================================================

def short_number(value):

    try:

        if value is None:
            return "N/A"

        value = float(value)

        if np.isnan(value):
            return "N/A"

        abs_value = abs(value)

        if abs_value >= 10000000:

            return (
                f"₹ {indian_format(value / 10000000)} Cr"
            )

        elif abs_value >= 100000:

            return (
                f"₹ {indian_format(value / 100000)} L"
            )

        elif abs_value >= 1000:

            return (
                f"₹ {indian_format(value / 1000)} K"
            )

        return f"₹ {indian_format(value)}"

    except:

        return value

# ============================================================
# PERCENT FORMAT
# ============================================================

def percent_format(value):

    try:

        if value is None:
            return "N/A"

        if np.isnan(value):
            return "N/A"

        return f"{value * 100:.2f}%"

    except:

        return value

# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(v):

    if v is None:
        return "N/A"

    try:

        if np.isnan(v):
            return "N/A"

    except:
        pass

    return v

# ============================================================
# STOCK OBJECT
# ============================================================

@st.cache_resource
def get_stock_object(ticker):

    return yf.Ticker(f"{ticker}.NS")

# ============================================================
# FUNDAMENTALS
# ============================================================

@st.cache_data(ttl=3600)
def get_fundamentals(ticker):

    stock = get_stock_object(ticker)

    return stock.info

# ============================================================
# LIVE PRICE
# ============================================================

@st.cache_data(ttl=5)
def get_live_price(ticker):

    try:

        url = (
            "https://www.nseindia.com/api/"
            f"quote-equity?symbol={ticker}"
        )

        response = session.get(
            url,
            timeout=10
        )

        data = response.json()

        return data.get(
            "priceInfo",
            {}
        )

    except:

        return {}

# ============================================================
# HISTORY
# ============================================================

@st.cache_data(ttl=1800)
def get_history(
    ticker,
    period,
    interval
):

    stock = get_stock_object(ticker)

    hist = stock.history(
        period=period,
        interval=interval,
        auto_adjust=False
    )

    return hist

# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def add_technical_indicators(df):

    if len(df) < 20:

        return df

    try:

        df["SMA20"] = SMAIndicator(
            close=df["Close"],
            window=20
        ).sma_indicator()

        df["EMA20"] = EMAIndicator(
            close=df["Close"],
            window=20
        ).ema_indicator()

        df["RSI"] = RSIIndicator(
            close=df["Close"],
            window=14
        ).rsi()

        macd = MACD(df["Close"])

        df["MACD"] = macd.macd()

        df["MACD_SIGNAL"] = macd.macd_signal()

        bb = BollingerBands(df["Close"])

        df["BB_HIGH"] = bb.bollinger_hband()

        df["BB_LOW"] = bb.bollinger_lband()

    except:
        pass

    return df

# ============================================================
# AI SCORE
# ============================================================

def ai_score(info):

    score = 50

    try:

        roe = info.get("returnOnEquity")

        if roe and roe > 0.15:
            score += 15

        margins = info.get("profitMargins")

        if margins and margins > 0.10:
            score += 15

        debt = info.get("debtToEquity")

        if debt and debt < 1:
            score += 10

        growth = info.get("revenueGrowth")

        if growth and growth > 0.10:
            score += 10

    except:
        pass

    return min(score, 100)

# ============================================================
# AI SIGNAL
# ============================================================

def ai_signal(score):

    if score >= 80:
        return "STRONG BUY"

    elif score >= 65:
        return "BUY"

    elif score >= 50:
        return "HOLD"

    return "SELL"

# ============================================================
# TITLE
# ============================================================

st.title("NSE Stock Research Dashboard")

st.markdown("""
Supports:

✅ Multi Stock Comparison  
✅ Live NSE Prices  
✅ Technical Indicators  
✅ Candlestick Charts  
✅ RSI / MACD  
✅ Bollinger Bands  
✅ AI Buy/Sell Signal  
✅ Company Officers  
✅ Financial Analysis  
✅ Raw Financial Data  
""")

# ============================================================
# FORM
# ============================================================

with st.form("ticker_form"):

    tickers_input = st.text_input(
        "Enter NSE Tickers (comma separated)",
        value=""
    )

    analyze = st.form_submit_button(
        "Analyze Stocks"
    )

# ============================================================
# SESSION
# ============================================================

if analyze:

    st.session_state["tickers"] = [

        t.strip().upper()

        for t in tickers_input.split(",")

        if t.strip()
    ]

# ============================================================
# MAIN
# ============================================================

if "tickers" in st.session_state:

    comparison_rows = []

    tickers = st.session_state["tickers"]

    for ticker in tickers:

        st.markdown("---")

        # ====================================================
        # FUNDAMENTALS
        # ====================================================

        try:

            fundamentals_key = (
                f"{ticker}_fundamentals"
            )

            if fundamentals_key not in st.session_state:

                st.session_state[
                    fundamentals_key
                ] = get_fundamentals(ticker)

            info = st.session_state[
                fundamentals_key
            ]

        except Exception as e:

            st.error(
                f"{ticker}: {e}"
            )

            continue

        company_name = info.get(
            "longName",
            ticker
        )

        # ====================================================
        # LIVE PRICE
        # ====================================================

        live_price_data = get_live_price(ticker)

        current_price = live_price_data.get(
            "lastPrice",
            info.get("currentPrice")
        )

        # ====================================================
        # SCORE
        # ====================================================

        score = ai_score(info)

        signal = ai_signal(score)

        # ====================================================
        # TITLE
        # ====================================================

        st.markdown(f"""
        <div class="company-title">
            {company_name}
        </div>
        """, unsafe_allow_html=True)

        # ====================================================
        # TOP CARDS
        # ====================================================

        cols = st.columns(5)
        quote_type = safe_value(info.get("quoteType"))
        cards = [

            (
                "Investment Score",
                f"{score}/100"
            ),

            (
                "Recommendation",
                signal
            ),

            (
                "LIVE Stock Price",
                f"₹ {indian_format(current_price)}"
            ),

            (
                "Market Capitalization",
                short_number(
                    info.get("marketCap")
                )
            ),
            (
                "Quote Type",
                info.get("quoteType")
            )
            
        ]

        for col, (title, value) in zip(
            cols,
            cards
        ):

            with col:

                st.markdown(f"""
                <div class="main-card">
                    <div class="metric-title">
                        {title}
                    </div>
                    <div class="metric-value">
                        {value}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ====================================================
        # TIMEFRAME
        # ====================================================

        t1, t2, t3 = st.columns(3)

        with t1:

            timeframe = st.selectbox(

                f"Select Timeframe - {ticker}",

                [
                    "1 Day",
                    "1 Week",
                    "1 Month",
                    "3 Months",
                    "6 Months",
                    "1 Year"
                ],

                index=5,

                key=f"timeframe_{ticker}"
            )

        with t2:

            chart_type = st.selectbox(

                f"Chart Type - {ticker}",

                [
                    "Candlestick",
                    "Line Chart"
                ],

                key=f"chart_{ticker}"
            )

        with t3:

            selected_indicators = st.multiselect(

                f"Indicators - {ticker}",

                [
                    "SMA 20",
                    "EMA 20",
                    "RSI",
                    "MACD",
                    "Bollinger Bands",
                    "Volume"
                ],

                default=[
                    "SMA 20",
                    "EMA 20"
                ],

                key=f"indicator_{ticker}"
            )

        # ====================================================
        # PERIOD MAP
        # ====================================================

        if timeframe == "1 Day":

            period = "1d"
            interval = "5m"

        elif timeframe == "1 Week":

            period = "5d"
            interval = "15m"

        elif timeframe == "1 Month":

            period = "1mo"
            interval = "1h"

        elif timeframe == "3 Months":

            period = "3mo"
            interval = "1d"

        elif timeframe == "6 Months":

            period = "6mo"
            interval = "1d"

        else:

            period = "1y"
            interval = "1d"

        # ====================================================
        # HISTORY
        # ====================================================

        history_key = (
            f"{ticker}_{period}_{interval}"
        )

        try:

            if history_key not in st.session_state:

                st.session_state[
                    history_key
                ] = get_history(
                    ticker,
                    period,
                    interval
                )

            hist = st.session_state[
                history_key
            ]

        except Exception as e:

            st.error(
                f"History Error: {e}"
            )

            continue

        # ====================================================
        # EMPTY CHECK
        # ====================================================

        if hist is None or hist.empty:

            st.warning(
                f"No historical data for {ticker}"
            )

            continue

        # ====================================================
        # DATETIME
        # ====================================================

        if not isinstance(
            hist.index,
            pd.DatetimeIndex
        ):

            hist.index = pd.to_datetime(
                hist.index
            )

        # ====================================================
        # REMOVE WEEKENDS
        # ====================================================

        hist = hist[
            hist.index.weekday < 5
        ]

        # ====================================================
        # REMOVE AFTER HOURS
        # ====================================================

        if interval in [

            "5m",
            "15m",
            "30m",
            "60m",
            "1h"
        ]:

            try:

                hist = hist.between_time(
                    "09:15",
                    "15:30"
                )

            except:
                pass

        # ====================================================
        # REMOVE HOLIDAYS
        # ====================================================

        if "Volume" in hist.columns:

            hist = hist[
                hist["Volume"] > 0
            ]

        # ====================================================
        # SORT
        # ====================================================

        hist = hist.sort_index()

        # ====================================================
        # REMOVE DUPLICATES
        # ====================================================

        hist = hist[
            ~hist.index.duplicated()
        ]

        # ====================================================
        # EMPTY CHECK
        # ====================================================

        if hist.empty:

            st.warning(
                f"No valid candles for {ticker}"
            )

            continue

        # ====================================================
        # TECHNICALS
        # ====================================================

        hist = add_technical_indicators(hist)

        hist = hist.dropna(how="all")

        if hist.empty:

            st.warning(
                f"Indicators unavailable for {ticker}"
            )

            continue

        latest = hist.iloc[-1]

        # ====================================================
        # TECHNICAL CARDS
        # ====================================================

        st.markdown("""
        <div class="section-title">
            Technical Analysis
        </div>
        """, unsafe_allow_html=True)

        tech_cols = st.columns(4)

        tech_cards = [

            (
                "RSI",
                round(
                    latest.get("RSI", 0),
                    2
                )
            ),

            (
                "MACD",
                round(
                    latest.get("MACD", 0),
                    2
                )
            ),

            (
                "20 EMA",
                round(
                    latest.get("EMA20", 0),
                    2
                )
            ),

            (
                "20 SMA",
                round(
                    latest.get("SMA20", 0),
                    2
                )
            )
        ]

        for col, (title, value) in zip(
            tech_cols,
            tech_cards
        ):

            with col:

                st.markdown(f"""
                <div class="main-card">
                    <div class="metric-title">
                        {title}
                    </div>
                    <div class="metric-value">
                        {value}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ====================================================
        # CHART
        # ====================================================

        st.markdown("""
        <div class="section-title">
            Interactive Technical Chart
        </div>
        """, unsafe_allow_html=True)

        fig = go.Figure()

        if chart_type == "Candlestick":

            fig.add_trace(

                go.Candlestick(

                    x=hist.index,

                    open=hist["Open"],

                    high=hist["High"],

                    low=hist["Low"],

                    close=hist["Close"],

                    name="Candlestick"
                )
            )

        else:

            fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["Close"],

                    mode="lines",

                    name="Close"
                )
            )

        # ====================================================
        # SMA
        # ====================================================

        if "SMA 20" in selected_indicators:

            fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["SMA20"],

                    mode="lines",

                    name="SMA20"
                )
            )

        # ====================================================
        # EMA
        # ====================================================

        if "EMA 20" in selected_indicators:

            fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["EMA20"],

                    mode="lines",

                    name="EMA20"
                )
            )

        # ====================================================
        # BB
        # ====================================================

        if "Bollinger Bands" in selected_indicators:

            fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["BB_HIGH"],

                    mode="lines",

                    name="BB HIGH"
                )
            )

            fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["BB_LOW"],

                    mode="lines",

                    name="BB LOW"
                )
            )

        # ====================================================
        # VOLUME
        # ====================================================

        if "Volume" in selected_indicators:

            fig.add_trace(

                go.Bar(

                    x=hist.index,

                    y=hist["Volume"],

                    name="Volume",

                    opacity=0.3,

                    yaxis="y2"
                )
            )

        # ====================================================
        # RANGE BREAKS
        # ====================================================

        rangebreaks = [

            dict(
                bounds=["sat", "mon"]
            )
        ]

        if interval in [

            "5m",
            "15m",
            "30m",
            "60m",
            "1h"
        ]:

            rangebreaks.append(

                dict(
                    bounds=[15.5, 9.25],
                    pattern="hour"
                )
            )

        fig.update_xaxes(

            rangebreaks=rangebreaks
        )

        # ====================================================
        # CHART LAYOUT
        # ====================================================

        fig.update_layout(

            template="plotly_dark",

            height=700,

            hovermode="x unified",

            xaxis_rangeslider_visible=False,

            yaxis=dict(
                title="Price"
            ),

            yaxis2=dict(

                title="Volume",

                overlaying="y",

                side="right",

                showgrid=False
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ====================================================
        # RSI CHART
        # ====================================================

        if "RSI" in selected_indicators:

            st.markdown("""
            <div class="section-title">
                RSI Indicator
            </div>
            """, unsafe_allow_html=True)

            rsi_fig = go.Figure()

            rsi_fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["RSI"],

                    mode="lines",

                    name="RSI"
                )
            )

            rsi_fig.add_hline(
                y=70,
                line_dash="dash"
            )

            rsi_fig.add_hline(
                y=30,
                line_dash="dash"
            )

            rsi_fig.update_layout(

                template="plotly_dark",

                height=300
            )

            st.plotly_chart(
                rsi_fig,
                use_container_width=True
            )

        # ====================================================
        # MACD CHART
        # ====================================================

        if "MACD" in selected_indicators:

            st.markdown("""
            <div class="section-title">
                MACD Indicator
            </div>
            """, unsafe_allow_html=True)

            macd_fig = go.Figure()

            macd_fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["MACD"],

                    mode="lines",

                    name="MACD"
                )
            )

            macd_fig.add_trace(

                go.Scatter(

                    x=hist.index,

                    y=hist["MACD_SIGNAL"],

                    mode="lines",

                    name="Signal"
                )
            )

            macd_fig.update_layout(

                template="plotly_dark",

                height=300
            )

            st.plotly_chart(
                macd_fig,
                use_container_width=True
            )

        # ====================================================
        # COMPANY OFFICERS
        # ====================================================

        st.markdown("""
        <div class="section-title">
            Company Officers
        </div>
        """, unsafe_allow_html=True)

        officers = info.get(
            "companyOfficers",
            []
        )

        officer_rows = []

        for officer in officers:

            pay = officer.get("totalPay")

            if pay:

                pay = (
                    f"{pay / 10000000:.2f} Cr"
                )

            officer_rows.append({

                "Name":
                    officer.get("name"),

                "Title":
                    officer.get("title"),

                "Salary":
                    pay,

                "Fiscal Year":
                    officer.get("fiscalYear")
            })

        if officer_rows:

            officer_df = pd.DataFrame(
                officer_rows
            )

            st.dataframe(
                officer_df,
                use_container_width=True
            )

        # ====================================================
        # RAW DATA
        # ====================================================

        st.markdown("""
        <div class="section-title">
            Complete Financial Data
        </div>
        """, unsafe_allow_html=True)

        try:

            full_df = pd.DataFrame(

                list(info.items()),

                columns=[
                    "Attribute",
                    "Value"
                ]
            )

            def raw_formatter(v):

                try:

                    if isinstance(v, (int, float)):

                        if abs(v) > 100000:

                            return short_number(v)

                        return indian_format(v)

                    return v

                except:

                    return v

            full_df["Value"] = full_df[
                "Value"
            ].apply(raw_formatter)

            search_term = st.text_input(

                f"Search Attribute - {ticker}",

                key=f"search_{ticker}"
            )

            if search_term:

                filtered_df = full_df[

                    full_df["Attribute"]

                    .astype(str)

                    .str.contains(

                        search_term,

                        case=False,

                        na=False
                    )
                ]

                st.dataframe(

                    filtered_df,

                    use_container_width=True,

                    height=600
                )

            else:

                st.dataframe(

                    full_df,

                    use_container_width=True,

                    height=600
                )

        except Exception as e:

            st.error(
                f"{ticker}: {e}"
            )

        # ====================================================
        # COMPARISON
        # ====================================================

        comparison_rows.append({

            "Ticker":
                ticker,

            "Company":
                company_name,

            "AI Score":
                score,

            "Signal":
                signal,

            "LIVE Price":
                current_price,

            "Market Cap":
                info.get("marketCap"),

            "PE":
                info.get("trailingPE"),

            "ROE":
                info.get("returnOnEquity"),

            "Revenue Growth":
                info.get("revenueGrowth")
        })

    # ========================================================
    # MULTI STOCK COMPARISON
    # ========================================================

    if len(comparison_rows) > 1:

        st.markdown("""
        <div class="section-title">
            Multi Stock Comparison
        </div>
        """, unsafe_allow_html=True)

        comparison_df = pd.DataFrame(
            comparison_rows
        )

        st.dataframe(
            comparison_df,
            use_container_width=True,
            height=500
        )
