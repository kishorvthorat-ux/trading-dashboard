import pandas as pd
import numpy as np
import io

def process_csv(file):

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    if "Price" in df.columns:
        df.rename(columns={"Price": "Price USD"}, inplace=True)

    df['Date and time'] = pd.to_datetime(df['Date and time'])

    # ---------------- ENTRY / EXIT ----------------
    entries = df[df['Type'].str.contains("Entry", na=False)].copy()
    exits = df[df['Type'].str.contains("Exit", na=False)].copy()

    entries = entries.rename(columns={
        'Date and time': 'Entry Date',
        'Signal': 'Entry Signal',
        'Price USD': 'Entry Price'
    })

    exits = exits.rename(columns={
        'Date and time': 'Exit Date',
        'Signal': 'Exit Signal',
        'Price USD': 'Exit Price'
    })

    calc = pd.merge(entries, exits, on='Trade number')

    # ---------------- CALCULATIONS ----------------
    calc['Days'] = (calc['Exit Date'] - calc['Entry Date']).dt.days

    calc['Points'] = calc['Exit Price'] - calc['Entry Price']
    calc['Gross PnL'] = calc['Points'] * 30

    calc['Turnover'] = calc['Entry Price'] * 30
    calc['Brokerage'] = calc['Turnover'] * 0.0005

    calc['Net PnL'] = calc['Gross PnL'] - calc['Brokerage']

    calc['% Returns'] = (calc['Points'] / calc['Entry Price']) * 100
    calc['Margin 20%'] = calc['Turnover'] * 0.2

    # ---------------- RESULT ----------------
    calc['Count'] = np.where(calc['Net PnL'] > 0, 1, -1)

    # ---------------- EQUITY / SCALING ----------------
    base_capital = 100000
    calc['Cumm Profit'] = calc['Net PnL'].cumsum()
    calc['Equity'] = base_capital + calc['Cumm Profit']

    calc['Lots'] = (calc['Equity'] / calc['Margin 20%']).fillna(1)
    calc['Lots'] = calc['Lots'].astype(int).replace(0, 1)

    calc['Amount'] = calc['Lots'] * calc['Margin 20%']
    calc['Cumm Position Size'] = calc['Amount'].cumsum()

    # ---------------- TIME FEATURES ----------------
    calc['Weekday'] = calc['Entry Date'].dt.day_name()
    calc['Day'] = calc['Entry Date'].dt.day

    calc['Day Type'] = np.where(calc['Day'] <= 10, 'Start',
                        np.where(calc['Day'] <= 20, 'Middle', 'End'))

    calc['Week Count'] = calc['Entry Date'].dt.isocalendar().week

    calc['PivotYear'] = calc['Entry Date'].dt.year
    calc['PivotMonth'] = calc['Entry Date'].dt.strftime('%b')
    calc['PivotQuarter'] = calc['Entry Date'].dt.to_period('Q').astype(str)

    # ---------------- STATS ----------------
    wins = calc[calc['Net PnL'] > 0]
    losses = calc[calc['Net PnL'] < 0]

    total_trades = len(calc)

    avg_profit = wins['Net PnL'].mean()
    avg_loss = losses['Net PnL'].mean()

    profit_factor = abs(wins['Net PnL'].sum() / losses['Net PnL'].sum())

    expectancy = (len(wins)/total_trades)*avg_profit + \
                 (len(losses)/total_trades)*avg_loss

    stats = pd.DataFrame([{
        "Total Trades": total_trades,
        "Wins": len(wins),
        "Losses": len(losses),
        "Strike Rate": len(wins)/total_trades,
        "Net PnL": calc['Net PnL'].sum(),
        "Avg Profit": avg_profit,
        "Avg Loss": avg_loss,
        "Profit Factor": profit_factor,
        "Expectancy": expectancy
    }])

    # ---------------- OCCURRENCE ----------------
    occurrence = calc['Count'].value_counts().sort_index().reset_index()
    occurrence.columns = ['Outcome', 'Count']

    # ---------------- PIVOTS ----------------
    pivot_pnl = pd.pivot_table(
        calc, values='Net PnL',
        index='PivotYear',
        columns='PivotMonth',
        aggfunc='sum',
        fill_value=0
    )

    pivot_returns = pd.pivot_table(
        calc, values='% Returns',
        index='PivotYear',
        columns='PivotMonth',
        aggfunc='sum',
        fill_value=0
    )

    # Add totals
    pivot_pnl['Total'] = pivot_pnl.sum(axis=1)
    pivot_returns['Total'] = pivot_returns.sum(axis=1)

    pivot_pnl.loc['Grand Total'] = pivot_pnl.sum()
    pivot_returns.loc['Grand Total'] = pivot_returns.sum()

# ---------------- EXCEL OUTPUT ----------------
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        # Write data
        calc.to_excel(writer, sheet_name="Calculated", index=False)
        stats.to_excel(writer, sheet_name="Stats", index=False)
        occurrence.to_excel(writer, sheet_name="Occurrence", index=False)
        pivot_pnl.to_excel(writer, sheet_name="PnL Pivot")
        pivot_returns.to_excel(writer, sheet_name="Returns Pivot")

        workbook = writer.book

        # ---------------- FORMATS ----------------
        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center'
        })

        border_format = workbook.add_format({'border': 1})

        currency_fmt = workbook.add_format({
            'num_format': '₹#,##0',
            'border': 1
        })

        percent_fmt = workbook.add_format({
            'num_format': '0.00%',
            'border': 1
        })

        green = workbook.add_format({'bg_color': '#C6EFCE'})
        red = workbook.add_format({'bg_color': '#FFC7CE'})

        # ---------------- CALCULATED ----------------
        ws = writer.sheets['Calculated']

        ws.freeze_panes(1, 0)

        for col_num, col_name in enumerate(calc.columns):
            ws.write(0, col_num, col_name, header_format)
            ws.set_column(col_num, col_num, 18)

        # Currency columns
        for col in ["Net PnL", "Gross PnL", "Turnover", "Brokerage", "Cumm Profit"]:
            if col in calc.columns:
                idx = calc.columns.get_loc(col)
                ws.set_column(idx, idx, 18, currency_fmt)

        # Percent column
        if "% Returns" in calc.columns:
            idx = calc.columns.get_loc("% Returns")
            ws.set_column(idx, idx, 18, percent_fmt)

        # Conditional colors
        for col in ["Net PnL", "% Returns", "Cumm Profit"]:
            if col in calc.columns:
                idx = calc.columns.get_loc(col)

                ws.conditional_format(
                    1, idx, len(calc), idx,
                    {'type': 'cell', 'criteria': '>', 'value': 0, 'format': green}
                )

                ws.conditional_format(
                    1, idx, len(calc), idx,
                    {'type': 'cell', 'criteria': '<', 'value': 0, 'format': red}
                )

        # ---------------- PIVOTS ----------------
        pivot_ws = writer.sheets['PnL Pivot']
        pivot_ws.freeze_panes(1, 1)

        pivot_ws.conditional_format(
            1, 1,
            pivot_pnl.shape[0],
            pivot_pnl.shape[1],
            {
                'type': '3_color_scale',
                'min_color': '#F8696B',
                'mid_color': '#FFEB84',
                'max_color': '#63BE7B'
            }
        )

        ret_ws = writer.sheets['Returns Pivot']
        ret_ws.freeze_panes(1, 1)

        ret_ws.conditional_format(
            1, 1,
            pivot_returns.shape[0],
            pivot_returns.shape[1],
            {
                'type': '3_color_scale',
                'min_color': '#F8696B',
                'mid_color': '#FFEB84',
                'max_color': '#63BE7B'
            }
        )

    output.seek(0)

    return calc, stats, pivot_pnl, pivot_returns, occurrence, output
    
    output.seek(0)

    return calc, stats, pivot_pnl, pivot_returns, occurrence, output
