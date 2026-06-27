import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="📊 Trading App", layout="wide")
st.title("📊 Crypto Trading Backtest")

with st.sidebar:
    st.header("⚙️ Settings")
    symbol = st.text_input("Symbol (e.g., BTC-USD)", "BTC-USD").upper()
    start = st.date_input("Start", datetime.now() - timedelta(days=365))
    end = st.date_input("End", datetime.now())
    sma1 = st.slider("Short SMA", 5, 100, 20)
    sma2 = st.slider("Long SMA", 20, 200, 50)
    run = st.button("🚀 RUN BACKTEST", type="primary")

@st.cache_data
def load_data(symbol, start, end):
    return yf.download(symbol, start=start, end=end, progress=False)

if run:
    with st.spinner("Loading..."):
        df = load_data(symbol, start, end)
    
    if df.empty:
        st.error("No data found for this symbol!")
        st.stop()
    
    # Simple Strategy
    df['S1'] = df['Close'].rolling(sma1).mean()
    df['S2'] = df['Close'].rolling(sma2).mean()
    df['Signal'] = 0
    df.loc[df['S1'] > df['S2'], 'Signal'] = 1
    df.loc[df['S1'] < df['S2'], 'Signal'] = -1
    df['Pos'] = df['Signal'].diff()
    
    # Show Metrics (इस बार "col" सही है!)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Return", f"{((df['Close'].iloc[-1]/df['Close'].iloc[0]-1)*100):.2f}%")
    c2.metric("Volatility", f"{df['Close'].pct_change().std()*100:.2f}%")
    c3.metric("Sharpe", f"{((df['Close'].pct_change().mean()/df['Close'].pct_change().std())*252**0.5):.2f}")
    
    # Chart
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['S1'], name=f'SMA{sma1}', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['S2'], name=f'SMA{sma2}', line=dict(color='blue')))
    
    buy = df[df['Pos'] == 2]
    sell = df[df['Pos'] == -2]
    if not buy.empty:
        fig.add_trace(go.Scatter(x=buy.index, y=buy['Close'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'), name='Buy'))
    if not sell.empty:
        fig.add_trace(go.Scatter(x=sell.index, y=sell['Close'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='Sell'))
    
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='gray'))
    fig.update_layout(height=500, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)
