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
    symbol = st.text_input("स्टॉक सिंबल", value="AAPL").upper()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("शुरुआत", datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("अंत", datetime.now())
    
    sma_short = st.number_input("Short SMA", value=20, min_value=5, max_value=200, step=5)
    sma_long = st.number_input("Long SMA", value=50, min_value=20, max_value=300, step=5)
    
    run_btn = st.button("🚀 बैकटेस्ट", type="primary", use_container_width=True)

@st.cache_data
def fetch_data(symbol, start, end):
    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        return df
    except:
        return None

if run_btn:
    if not symbol:
        st.warning("⚠️ स्टॉक सिंबल डालें!")
    elif start_date >= end_date:
        st.warning("⚠️ सही तारीख डालें!")
    else:
        with st.spinner("📥 डेटा लोड हो रहा..."):
            df = fetch_data(symbol, start_date, end_date)
        
        if df is None or df.empty:
            st.error(f"❌ {symbol} का डेटा नहीं मिला!")
        else:
            # SMA Calculate
            df['SMA_Short'] = df['Close'].rolling(sma_short).mean()
            df['SMA_Long'] = df['Close'].rolling(sma_long).mean()
            df['Signal'] = 0
            df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1
            df.loc[df['SMA_Short'] < df['SMA_Long'], 'Signal'] = -1
            df['Position'] = df['Signal'].diff()
            
            # ✅ Metrics - सबसे सरल तरीका
            try:
                returns = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                vol = df['Close'].pct_change().std() * 100
                sharpe = (df['Close'].pct_change().mean() / df['Close'].pct_change().std()) * np.sqrt(252) if df['Close'].pct_change().std() != 0 else 0
                
                # ✅ 3 columns में दिखाओ
                c1, c2, c3 = st.columns(3)
                c1.metric("📈 रिटर्न", f"{returns:.2f}%")
                c2.metric("📊 वोलैटिलिटी", f"{vol:.2f}%")
                c3.metric("⚡ शार्प", f"{sharpe:.2f}")
            except:
                st.warning("⚠️ मेट्रिक्स नहीं निकाल पाए!")
            
            # ✅ Chart - सरल और साफ
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price', line=dict(color='white')))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Short'], name=f'SMA {sma_short}', line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Long'], name=f'SMA {sma_long}', line=dict(color='blue')))
            
            buy = df[df['Position'] == 2]
            sell = df[df['Position'] == -2]
            
            if not buy.empty:
                fig.add_trace(go.Scatter(x=buy.index, y=buy['Close'], mode='markers', 
                                        marker=dict(symbol='triangle-up', size=12, color='green'), name='Buy'))
            if not sell.empty:
                fig.add_trace(go.Scatter(x=sell.index, y=sell['Close'], mode='markers', 
                                        marker=dict(symbol='triangle-down', size=12, color='red'), name='Sell'))
            
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='gray'))
            
            fig.update_layout(height=600, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📋 डेटा"):
                st.dataframe(df.tail(20))
