import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

st.set_page_config(page_title="Advanced Buy/Sell Signals", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4255; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Advanced Signal Dashboard")
st.caption("Strategy: EMA 50 + RSI 14 + SuperTrend (10, 3)")

st.sidebar.header("Market Selection")
asset_mapping = {
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Gold (USD)": "GC=F",
    "Crude Oil": "CL=F",
    "Silver": "SI=F"
}

selected_label = st.sidebar.selectbox("Choose Asset", list(asset_mapping.keys()))
symbol = asset_mapping[selected_label]
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"], index=1)

@st.cache_data(ttl=60)
def get_market_data(ticker, tf):
    df = yf.download(ticker, period="1mo", interval=tf)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

try:
    df = get_market_data(symbol, timeframe)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    st_df = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)
    df['ST'] = st_df['SUPERTd_7_3.0'] 
    
    last_row = df.iloc[-1]
    curr_price = float(last_row['Close'])
    curr_rsi = float(last_row['RSI'])
    curr_st = int(last_row['ST'])
    curr_ema = float(last_row['EMA50'])
    
    buy_cond = (curr_price > curr_ema) and (curr_rsi > 50) and (curr_st == 1)
    sell_cond = (curr_price < curr_ema) and (curr_rsi < 45) and (curr_st == -1)

    m1, m2, m3 = st.columns(3)
    m1.metric("Current Price", f"{curr_price:,.2f}")
    m2.metric("RSI (14)", f"{curr_rsi:,.2f}")
    
    if buy_cond:
        m3.markdown("<h2 style='color:#28a745; margin:0;'>STRONG BUY</h2>", unsafe_allow_html=True)
    elif sell_cond:
        m3.markdown("<h2 style='color:#dc3545; margin:0;'>STRONG SELL</h2>", unsafe_allow_html=True)
    else:
        m3.markdown("<h2 style='color:#ffc107; margin:0;'>NEUTRAL / WAIT</h2>", unsafe_allow_html=True)

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price')])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='orange', width=2), name='Trend (EMA 50)'))
    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
except Exception as e:
    st.warning("Loading data...")
