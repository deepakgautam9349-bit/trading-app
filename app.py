import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# पेज सेटअप
st.set_page_config(page_title="📊 ट्रेडिंग ऐप", layout="wide")

# टाइटल
st.title("📊 ट्रेडिंग बैकटेस्टिंग ऐप")

# साइडबार
with st.sidebar:
    st.header("⚙️ सेटिंग्स")
    symbol = st.text_input("स्टॉक सिंबल", value="AAPL").upper()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("शुरुआत", datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("अंत", datetime.now())
    
    sma_short = st.number_input("Short SMA", value=50, min_value=5, max_value=200, step=5)
    sma_long = st.number_input("Long SMA", value=200, min_value=20, max_value=300, step=5)
    
    run_btn = st.button("🚀 बैकटेस्ट", type="primary", use_container_width=True)

# डेटा फेच करने का फंक्शन
@st.cache_data
def fetch_data(symbol, start, end):
    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        if df.empty:
            return None
        return df
    except Exception as e:
        st.error(f"❌ एरर: {e}")
        return None

# बैकटेस्ट लॉजिक
if run_btn:
    if not symbol:
        st.warning("⚠️ कृपया स्टॉक सिंबल डालें!")
    elif start_date >= end_date:
        st.warning("⚠️ शुरुआत तारीख अंत से पहले होनी चाहिए!")
    else:
        with st.spinner("📥 डेटा लोड हो रहा है..."):
            df = fetch_data(symbol, start_date, end_date)
        
        # ✅ डेटा चेक करो
        if df is None or df.empty:
            st.error(f"❌ {symbol} के लिए डेटा नहीं मिला! सही सिंबल डालें (जैसे AAPL, TSLA, RELIANCE.NS)")
        else:
            # Indicators
            df['SMA_Short'] = df['Close'].rolling(window=sma_short).mean()
            df['SMA_Long'] = df['Close'].rolling(window=sma_long).mean()
            df['Signal'] = 0
            df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1
            df.loc[df['SMA_Short'] < df['SMA_Long'], 'Signal'] = -1
            df['Position'] = df['Signal'].diff()
            
            # ✅ मेट्रिक्स (सिर्फ तभी जब डेटा हो)
            if len(df) > 1:
                total_return = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                volatility = df['Close'].pct_change().std() * 100
                sharpe = (df['Close'].pct_change().mean() / df['Close'].pct_change().std()) * np.sqrt(252)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("📈 कुल रिटर्न", f"{total_return:.2f}%")
                col2.metric("📊 वोलैटिलिटी", f"{volatility:.2f}%")
                col3.metric("⚡ शार्प रेश्यो", f"{sharpe:.2f}" if not np.isnan(sharpe) else "N/A")
            else:
                st.warning("⚠️ पर्याप्त डेटा नहीं है!")
                st.stop()
            
            # चार्ट
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               row_heights=[0.7, 0.3],
                               vertical_spacing=0.1)
            
            # Price & SMA
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], 
                                    name='Price', line=dict(color='white')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Short'], 
                                    name=f'SMA {sma_short}', line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Long'], 
                                    name=f'SMA {sma_long}', line=dict(color='blue')), row=1, col=1)
            
            # बाय/सेल सिग्नल
            buy_signals = df[df['Position'] == 2]
            sell_signals = df[df['Position'] == -2]
            
            if not buy_signals.empty:
                fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'],
                                        mode='markers', marker=dict(symbol='triangle-up', 
                                        size=12, color='green'), name='Buy'), row=1, col=1)
            if not sell_signals.empty:
                fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'],
                                        mode='markers', marker=dict(symbol='triangle-down', 
                                        size=12, color='red'), name='Sell'), row=1, col=1)
            
            # वॉल्यूम
            colors = ['green' if row['Close'] >= row['Open'] else 'red' for _, row in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], 
                                marker_color=colors, name='Volume'), row=2, col=1)
            
            fig.update_layout(height=600, template='plotly_dark', 
                             hovermode='x unified')
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # डेटा टेबल
            with st.expander("📋 डेटा देखें"):
                st.dataframe(df.tail(20))
            
            # CSV डाउनलोड
            csv = df.to_csv().encode('utf-8')
            st.download_button("📥 CSV डाउनलोड करें", data=csv,
                              file_name=f"{symbol}_data.csv", mime="text/csv")

# फुटर
st.markdown("---")
st.caption("🚀 Streamlit + yfinance + Plotly के साथ बनाया गया")
