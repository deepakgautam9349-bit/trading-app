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
    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        return df
    except:
        return pd.DataFrame()

if run:
    if not symbol:
        st.warning("Please enter a valid symbol!")
        st.stop()
    
    with st.spinner("Loading data..."):
        df = load_data(symbol, start, end)
    
    if len(df) == 0:
        st.error(f"No data found for {symbol}!")
        st.stop()
    
    # Calculate indicators
    df['SMA1'] = df['Close'].rolling(sma1).mean()
    df['SMA2'] = df['Close'].rolling(sma2).mean()
    df['Signal'] = 0
    df.loc[df['SMA1'] > df['SMA2'], 'Signal'] = 1
    df.loc[df['SMA1'] < df['SMA2'], 'Signal'] = -1
    df['Position'] = df['Signal'].diff()
    
    # ✅ SIMPLE AND CLEAN METRICS
    returns = df['Close'].pct_change().dropna()
    total_return = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
    volatility = returns.std() * 100
    sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() != 0 else 0
    
    # Show Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📈 Return", f"{total_return:.2f}%")
    col2.metric("📊 Volatility", f"{volatility:.2f}%")
    col3.metric("⚡ Sharpe", f"{sharpe_ratio:.2f}")
    
    # Price Chart
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price', line=dict(color='white')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA1'], name=f'SMA {sma1}', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA2'], name=f'SMA {sma2}', line=dict(color='blue')))
    
    buy_signals = df[df['Position'] == 2]
    sell_signals = df[df['Position'] == -2]
    
    if not buy_signals.empty:
        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'), name='Buy'))
    if not sell_signals.empty:
        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='Sell'))
    
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='gray'))
    fig.update_layout(height=500, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Raw Data"):
        st.dataframe(df.tail(20))
