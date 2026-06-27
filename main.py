import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="📊 Trading App", layout="wide")

# Title
st.title("📊 ट्रेडिंग बैकटेस्टिंग ऐप")

# Sidebar
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    symbol = st.text_input("स्टॉक सिंबल", "BTC-USD").upper()
    start = st.date_input("शुरुआत", datetime.now() - timedelta(days=365))
    end = st.date_input("अंत", datetime.now())
    sma1 = st.slider("Short SMA", 5, 100, 20)
    sma2 = st.slider("Long SMA", 20, 200, 50)
    run = st.button("🚀 बैकटेस्ट", type="primary")

# Data function
@st.cache_data
def load_data(symbol, start, end):
    return yf.download(symbol, start=start, end=end, progress=False)

# Main logic
if run:
    if not symbol:
        st.warning("⚠️ स्टॉक सिंबल डालें!")
        st.stop()
    
    with st.spinner("📥 डेटा लोड हो रहा..."):
        df = load_data(symbol, start, end)
    
    if df.empty:
        st.error(f"❌ {symbol} का डेटा नहीं मिला!")
        st.stop()
    
    # Calculate indicators
    df['SMA1'] = df['Close'].rolling(sma1).mean()
    df['SMA2'] = df['Close'].rolling(sma2).mean()
    df['Signal'] = 0
    df.loc[df['SMA1'] > df['SMA2'], 'Signal'] = 1
    df.loc[df['SMA1'] < df['SMA2'], 'Signal'] = -1
    df['Position'] = df['Signal'].diff()
    
    # Find trades
    trades = []
    entry_price = None
    entry_date = None
    
    for i in range(len(df)):
        if df['Position'].iloc[i] == 2:
            entry_price = df['Close'].iloc[i]
            entry_date = df.index[i]
        elif df['Position'].iloc[i] == -2 and entry_price is not None:
            exit_price = df['Close'].iloc[i]
            profit_pct = ((exit_price - entry_price) / entry_price) * 100
            trades.append({
                'Entry Date': entry_date,
                'Entry Price': round(entry_price, 2),
                'Exit Date': df.index[i],
                'Exit Price': round(exit_price, 2),
                'Profit %': round(profit_pct, 2)
            })
            entry_price = None
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    ret = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
    col1.metric("📈 रिटर्न", f"{ret:.2f}%")
    col2.metric("🔄 ट्रेड्स", len(trades))
    if trades:
        win = len([t for t in trades if t['Profit %'] > 0])
        col3.metric("✅ जीत %", f"{(win/len(trades)*100):.1f}%")
        avg = sum([t['Profit %'] for t in trades]) / len(trades)
        col4.metric("💰 औसत", f"{avg:.2f}%")
    else:
        col3.metric("✅ जीत %", "0%")
        col4.metric("💰 औसत", "0%")
    
    # Show trades
    if trades:
        st.subheader("📋 ट्रेड हिस्ट्री")
        st.dataframe(pd.DataFrame(trades), use_container_width=True)
        
        # Profit chart
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=[f"#{i+1}" for i in range(len(trades))],
            y=[t['Profit %'] for t in trades],
            marker_color=['green' if t['Profit %'] > 0 else 'red' for t in trades]
        ))
        fig2.update_layout(title="📊 हर ट्रेड का Profit/Loss", height=300, template='plotly_dark')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("ℹ️ कोई ट्रेड सिग्नल नहीं!")
    
    # Price chart
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA1'], name=f'SMA{sma1}', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA2'], name=f'SMA{sma2}', line=dict(color='blue')))
    
    buy = df[df['Position'] == 2]
    sell = df[df['Position'] == -2]
    if not buy.empty:
        fig.add_trace(go.Scatter(x=buy.index, y=buy['Close'], mode='markers',
                                marker=dict(symbol='triangle-up', size=12, color='green'), name='Buy'))
    if not sell.empty:
        fig.add_trace(go.Scatter(x=sell.index, y=sell['Close'], mode='markers',
                                marker=dict(symbol='triangle-down', size=12, color='red'), name='Sell'))
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='gray'))
    
    fig.update_layout(height=500, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)
