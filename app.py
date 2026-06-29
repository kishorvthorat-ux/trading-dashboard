import streamlit as st
import pandas as pd
import main

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="Trading Dashboard", layout="wide")

st.title("📊 Trading Dashboard (Excel Replica)")

# ---------------- COLOR FUNCTION ----------------
def color_pnl(val):
    if pd.isna(val):
        return ""
    if val > 0:
        return "background-color: #C6EFCE; color: black"
    elif val < 0:
        return "background-color: #FFC7CE; color: black"
    else:
        return ""

# ---------------- FILE UPLOAD ----------------
file = st.file_uploader("Upload Trading CSV", type=["csv"])

# ---------------- MAIN LOGIC ----------------
if file is not None:

    calc, stats, pnl_pivot, ret_pivot, occ, excel = main.process_csv(file)

    # ---------------- DOWNLOAD ----------------
    st.download_button(
        "📥 Download Excel Report",
        excel,
        file_name="trading_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------- KPI ROW ----------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Net PnL", round(stats["Net PnL"][0], 2))
    col2.metric("Trades", int(stats["Total Trades"][0]))
    col3.metric("Win Rate", round(stats["Strike Rate"][0] * 100, 2))
    col4.metric("Profit Factor", round(stats["Profit Factor"][0], 2))

    st.divider()

    # ---------------- EQUITY CHART ----------------
    st.subheader("📈 Equity Curve")
    st.line_chart(calc.set_index("Entry Date")["Cumm Profit"])

    # ---------------- TABS ----------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "Calculated",
        "PnL Pivot",
        "Returns Pivot",
        "Stats"
    ])

    # ✅ CALCULATED TABLE WITH COLOR
    with tab1:
        styled_calc = calc.style.map(
            color_pnl,
            subset=["Net PnL", "% Returns", "Cumm Profit"]
        )
        st.dataframe(styled_calc, use_container_width=True)

    # ✅ PNL PIVOT (SAFE HEATMAP)
    with tab2:
        try:
            st.dataframe(
                pnl_pivot.style.background_gradient(cmap="RdYlGn"),
                use_container_width=True
            )
        except:
            # fallback if matplotlib missing
            st.dataframe(pnl_pivot, use_container_width=True)

    # ✅ RETURNS PIVOT (SAFE HEATMAP)
    with tab3:
        try:
            st.dataframe(
                ret_pivot.style.background_gradient(cmap="RdYlGn"),
                use_container_width=True
            )
        except:
            st.dataframe(ret_pivot, use_container_width=True)

    # ✅ STATS + OCCURRENCE
    with tab4:

        styled_stats = stats.style.map(
            color_pnl,
            subset=["Net PnL", "Avg Profit", "Avg Loss"]
        )

        st.subheader("📊 Strategy Stats")
        st.dataframe(styled_stats, use_container_width=True)

        st.subheader("📉 Trade Distribution")
        st.dataframe(
            occ.style.bar(color="#5fba7d", subset=["Count"]),
            use_container_width=True
        )

# ---------------- EMPTY STATE ----------------
else:
    st.info("👆 Upload your trading CSV file to view the dashboard")

    st.markdown("""
    ### ✅ What you will get:
    - 📊 Full trade analysis (like Excel)
    - 📈 Equity curve
    - 📅 Monthly & Quarterly pivots
    - 🎯 Win/Loss statistics
    - 📥 Downloadable Excel report
    """)
