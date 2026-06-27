import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="📊 ट्रेडिंग ऐप", layout="wide")
st.title("📊 ट्रेडिंग बैकटेस्टिंग ऐप")

with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    symbol = st.text_input("स्टॉक सिंबल", "BTC-USD").upper()
    start_date = st.date_input("शुरुआत", datetime.now() - timedelta(days=365))
    end_date = st.date_input("अंत", datetime.now())
    sma_short = st.number_input("Short SMA", value=20, min_value=5, max_value=200, step=5)
    sma_long = st.number_input("Long SMA", value=50, min_value=5, max_value=300, step=5)
    run = st.button("🚀 बैकटेस्ट", type="primary")

@st.cache_data
def get_data(symbol, start, end):
    return yf.download(symbol, start=start, end=end, progress=False)

if run:
    if not symbol:
        st.warning("⚠️ स्टॉक सिंबल डालें!")
    else:
        with st.spinner("📥 डेटा लोड हो रहा..."):
            df = get_data(symbol, start_date, end_date)
        
        if df.empty:
            st.error(f"❌ {symbol} का डेटा नहीं मिला!")
            st.stop()
        
        df['SMA1'] = df['Close'].rolling(sma_short).mean()
        df['SMA2'] = df['Close'].rolling(sma_long).mean()
        df['Signal'] = 0
        df.loc[df['SMA1'] > df['SMA2'], 'Signal'] = 1
        df.loc[df['SMA1'] < df['SMA2'], 'Signal'] = -1
        df['Position'] = df['Signal'].diff()
        
        trades = []
        entry = None
        entry_date = None
        in_trade = False
        
        for i in range(len(df)):
            if df['Position'].iloc[i] == 2 and not in_trade:
                entry = df['Close'].iloc[i]
                entry_date = df.index[i]
                in_trade = True
            elif df['Position'].iloc[i] == -2 and in_trade:
                exit_price = df['Close'].iloc[i]
                profit = ((exit_price - entry) / entry) * 100
                trades.append({
                    'Entry Date': entry_date,
                    'Entry Price': round(entry, 2),
                    'Exit Date': df.index[i],
                    'Exit Price': round(exit_price, 2),
                    'Profit %': round(profit, 2)
                })
                in_trade = False
        
        c1, c2, c3 = st.columns(3)
        total_return = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
        c1.metric("📈 कुल रिटर्न", f"{total_return:.2f}%")
        c2.metric("🔄 कुल ट्रेड्स", len(trades))
        
        win = len([t for t in trades if t['Profit %'] > 0]) if trades else 0
        c3.metric("✅ जीत %", f"{(win/len(trades)*100):.1f}%" if trades else "0%")
        
        if trades:
            st.subheader("📋 ट्रेड हिस्ट्री")
            df_trades = pd.DataFrame(trades)
            st.dataframe(df_trades, use_container_width=True)
            
            fig2 = go.Figure()
            profits = [t['Profit %'] for t in trades]
            colors = ['green' if p > 0 else 'red' for p in profits]
            fig2.add_trace(go.Bar(x=[f"#{i+1}" for i in range(len(trades))], 
                                 y=profits, marker_color=colors))
            fig2.update_layout(title="📊 हर ट्रेड का Profit/Loss", height=350, template='plotly_dark')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("ℹ️ कोई ट्रेड सिग्नल नहीं आया!")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA1'], name=f'SMA {sma_short}', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA2'], name=f'SMA {sma_long}', line=dict(color='blue')))
        
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
