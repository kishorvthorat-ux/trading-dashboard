import streamlit as st
import pandas as pd
import plotly.express as px
from main import process_csv

st.set_page_config(layout="wide")

st.title("📊 Trading Analyzer Dashboard")

# ===============================
# FILE UPLOAD
# ===============================
uploaded_file = st.file_uploader("Upload Trading CSV", type=["csv"])

if uploaded_file:

    # Process file
    calc, stats, excel_file = process_csv(uploaded_file)

    # ===============================
    # KPI DISPLAY
    # ===============================
    st.subheader("📌 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Trades", int(stats['Total Trades'][0]))
    col2.metric("Wins", int(stats['Wins'][0]))
    col3.metric("Losses", int(stats['Losses'][0]))
    col4.metric("Net PnL", round(stats['Net PnL'][0], 2))

    # ===============================
    # EQUITY CURVE
    # ===============================
    st.subheader("📈 Equity Curve")

    fig_equity = px.line(calc, y="Equity", title="Equity Growth")
    st.plotly_chart(fig_equity, use_container_width=True)

    # ===============================
    # PNL DISTRIBUTION
    # ===============================
    st.subheader("📊 PnL Distribution")

    fig_hist = px.histogram(calc, x="Net PnL", nbins=30)
    st.plotly_chart(fig_hist, use_container_width=True)

    # ===============================
    # WIN / LOSS PIE
    # ===============================
    st.subheader("🟢 Win vs 🔴 Loss")

    calc['Result'] = calc['Net PnL'].apply(lambda x: "Win" if x > 0 else "Loss")

    fig_pie = px.pie(calc, names="Result")
    st.plotly_chart(fig_pie)

    # ===============================
    # MONTHLY PNL
    # ===============================
    st.subheader("📅 Monthly Performance")

    calc['Month'] = calc['Entry Date'].dt.to_period('M').astype(str)
    monthly = calc.groupby('Month')['Net PnL'].sum().reset_index()

    fig_month = px.bar(monthly, x='Month', y='Net PnL')
    st.plotly_chart(fig_month, use_container_width=True)

    # ===============================
    # DATA PREVIEW
    # ===============================
    st.subheader("📄 Calculated Data Preview")
    st.dataframe(calc.head(20))

    # ===============================
    # DOWNLOAD EXCEL
    # ===============================
    st.download_button(
        label="📥 Download Excel Report",
        data=excel_file,
        file_name="trading_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Upload a CSV file to start analysis")
