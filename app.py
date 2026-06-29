import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 Trading Dashboard")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    calc = pd.read_excel(uploaded_file, sheet_name="Calculated")
    stats = pd.read_excel(uploaded_file, sheet_name="Stats")

    st.write(stats)

    fig = px.line(calc, y="Equity", title="Equity Curve")
    st.plotly_chart(fig, use_container_width=True)
