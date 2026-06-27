import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Trading App", layout="wide")

st.title("📊 ट्रेडिंग बैकटेस्टिंग ऐप")

with st.sidebar:
    symbol = st.text_input("स्टॉक सिंबल", "AAPL").upper()
    start = st.date_input("शुरुआत", datetime.now() - timedelta(days=365))
    end = st.date_input("अंत", datetime.now())
    sma1 = st.number_input("Short SMA", 50)
    sma2 = st.number_input("Long SMA", 200)
    run = st.button("🚀 बैकटेस्ट")

@st.cache_data
def get_data(symbol, start, end):
    return yf.download(symbol, start=start, end=end, progress=False)

if run:
    with st.spinner("डेटा लोड हो रहा..."):
        df = get_data(symbol, start, end)
    
    if not df.empty:
        df['SMA1'] = df['Close'].rolling(sma1).mean()
        df['SMA2'] = df['Close'].rolling(sma2).mean()
        df['Signal'] = np.where(df['SMA1'] > df['SMA2'], 1, -1)
        df['Position'] = df['Signal'].diff()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📈 रिटर्न", f"{((df['Close'].iloc[-1]/df['Close'].iloc[0]-1)*100):.2f}%")
        col2.metric("💰 वोलैटिलिटी", f"{df['Close'].pct_change().std()*100:.2f}%")
        col3.metric("📊 शार्प", f"{((df['Close'].pct_change().mean()/df['Close'].pct_change().std())*np.sqrt(252)):.2f}")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA1'], name=f'SMA{sma1}'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA2'], name=f'SMA{sma2}'), row=1, col=1)
        buy = df[df['Position'] == 2]
        sell = df[df['Position'] == -2]
        fig.add_trace(go.Scatter(x=buy.index, y=buy['Close'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'), name='Buy'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell.index, y=sell['Close'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='Sell'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume'), row=2, col=1)
        fig.update_layout(height=600, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 डेटा"):
            st.dataframe(df.tail(20))
    else:
        st.error("❌ डेटा नहीं मिला!")