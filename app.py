import streamlit as st
import pandas as.set_page_config(layout="wide")import pandas as pd

def color_pnl(val):
    if pd.isna(val):
        return ""
    if val > 0:
        return "background-color: #C6EFCE; color: black"
    elif val < 0:
        return "background-color: #FFC7CE; color: black"
    else:
        return ""

st.title("📊 Trading Dashboard (Excel Replica)")

file = st.file_uploader("Upload Trading CSV", type=["csv"])

if file:

    calc, stats, pnl_pivot, ret_pivot, occ, excel = main.process_csv(file)

    st.subheader("📈 Equity Curve")
    st.line_chart(calc.set_index("Entry Date")["Cumm Profit"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "Calculated",
        "PnL Pivot",
        "Returns Pivot",
        "Stats"
    ])

    # ✅ CALCULATED TABLE
    with tab1:
        st.dataframe(
            calc.style.applymap(
                color_pnl,
                subset=["Net PnL", "% Returns", "Cumm Profit"]
            ),
            use_container_width=True
        )

    # ✅ PNL HEATMAP
    with tab2:
        st.dataframe(
            pnl_pivot.style.background_gradient(cmap="RdYlGn"),
            use_container_width=True
        )

    # ✅ RETURNS HEATMAP
    with tab3:
        st.dataframe(
            ret_pivot.style.background_gradient(cmap="RdYlGn"),
            use_container_width=True
        )

    # ✅ STATS
    with tab4:
        st.dataframe(
            stats.style.applymap(
                color_pnl,
                subset=["Net PnL", "Avg Profit", "Avg Loss"]
            )
        )
        st.dataframe(occ.style.bar(color="#5fba7d"))

    st.download_button("📥 Download Excel", excel, "trading_output.xlsx")
import main

