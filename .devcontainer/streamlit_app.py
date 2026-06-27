import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="📊 Trading App", layout="wide")
st.title("📊 ट्रेडिंग बैकटेस्टिंग ऐप")

with st.sidebar:
    st.header("⚙️ SETTINGS")
    symbol = st.text_input("Stock Symbol", "BTC-USD").upper()
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    end_date = st.date_input("End Date", datetime.now())
    sma_short = st.slider("Short SMA", 5, 100, 20)
    sma_long = st.slider("Long SMA", 20, 200, 50)
    run_button = st.button("🚀 RUN BACKTEST", type="primary")

@st.cache_data
def get_data(symbol, start, end):
    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        return df
    except:
        return pd.DataFrame()

if run_button:
    if not symbol:
        st.warning("⚠️ Please enter a stock symbol!")
        st.stop()
    
    with st.spinner("📥 Loading data..."):
        df = get_data(symbol, start_date, end_date)
    
    if df.empty:
        st.error(f"❌ No data found for {symbol}!")
        st.stop()
    
    df['SMA_Short'] = df['Close'].rolling(sma_short).mean()
    df['SMA_Long'] = df['Close'].rolling(sma_long).mean()
    df['Signal'] = 0
    df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1
    df.loc[df['SMA_Short'] < df['SMA_Long'], 'Signal'] = -1
    df['Position'] = df['Signal'].diff()
    
    trades = []
    entry_price = 0
    entry_date = None
    in_trade = False
    
    for i in range(len(df)):
        if df['Position'].iloc[i] == 2 and not in_trade:
            entry_price = df['Close'].iloc[i]
            entry_date = df.index[i]
            in_trade = True
        elif df['Position'].iloc[i] == -2 and in_trade:
            exit_price = df['Close'].iloc[i]
            profit_pct = ((exit_price - entry_price) / entry_price) * 100
            trades.append({
                'Entry Date': entry_date,
                'Entry Price': round(entry_price, 2),
                'Exit Date': df.index[i],
                'Exit Price': round(exit_price, 2),
                'Profit %': round(profit_pct, 2)
            })
            in_trade = False
    
    # ✅ यहाँ "col1" है, "coll" नहीं!
    col1, col2, col3, col4 = st.columns(4)
    
    total_return = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
    col1.metric("📈 Total Return", f"{total_return:.2f}%")
    col2.metric("🔄 Total Trades", len(trades))
    
    if trades:
        win_trades = len([t for t in trades if t['Profit %'] > 0])
        win_rate = (win_trades / len(trades)) * 100
        avg_profit = sum([t['Profit %'] for t in trades]) / len(trades)
        col3.metric("✅ Win Rate", f"{win_rate:.1f}%")
        col4.metric("💰 Avg Profit", f"{avg_profit:.2f}%")
    else:
        col3.metric("✅ Win Rate", "0%")
        col4.metric("💰 Avg Profit", "0%")
    
    if trades:
        st.subheader("📋 Trade History")
        st.dataframe(pd.DataFrame(trades), use_container_width=True)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=[f"#{i+1}" for i in range(len(trades))],
            y=[t['Profit %'] for t in trades],
            marker_color=['green' if t['Profit %'] > 0 else 'red' for t in trades]
        ))
        fig2.update_layout(title="📊 Profit/Loss per Trade", height=300, template='plotly_dark')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("ℹ️ No trading signals generated!")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price', line=dict(color='white')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Short'], name=f'SMA {sma_short}', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Long'], name=f'SMA {sma_long}', line=dict(color='blue')))
    
    buy_signals = df[df['Position'] == 2]
    sell_signals = df[df['Position'] == -2]
    
    if not buy_signals.empty:
        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers',
                                marker=dict(symbol='triangle-up', size=12, color='green'), name='Buy'))
    if not sell_signals.empty:
        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers',
                                marker=dict(symbol='triangle-down', size=12, color='red'), name='Sell'))
    
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='gray'))
    fig.update_layout(height=500, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 View Raw Data"):
        st.dataframe(df.tail(20))
