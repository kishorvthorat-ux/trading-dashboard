import pandas as pd
import numpy as np
import io

def process_csv(file):
    df = pd.read_csv(file)

    # Convert datetime
    df['Date and time'] = pd.to_datetime(df['Date and time'])

    # Sort
    df = df.sort_values(['Trade number', 'Date and time'])

    # Split entry / exit
    entries = df[df['Type'].str.contains("Entry")].copy()
    exits = df[df['Type'].str.contains("Exit")].copy()

    entries = entries.rename(columns={
        'Type': 'Entry Type',
        'Date and time': 'Entry Date',
        'Signal': 'Entry Signal',
        'Price USD': 'Entry Price'
    })

    exits = exits.rename(columns={
        'Type': 'Exit Type',
        'Date and time': 'Exit Date',
        'Signal': 'Exit Signal',
        'Price USD': 'Exit Price'
    })

    calc = pd.merge(entries, exits, on='Trade number')

    # ===============================
    # CALCULATIONS
    # ===============================
    calc['Points'] = calc['Exit Price'] - calc['Entry Price']
    calc['Gross PnL'] = calc['Points'] * 30
    calc['Turnover'] = calc['Entry Price'] * 30
    calc['Brokerage'] = calc['Turnover'] * 0.0005
    calc['Net PnL'] = calc['Gross PnL'] - calc['Brokerage']

    calc['Equity'] = 100000 + calc['Net PnL'].cumsum()
    calc['Return %'] = (calc['Points'] / calc['Entry Price']) * 100

    # ===============================
    # STATS
    # ===============================
    wins = (calc['Net PnL'] > 0).sum()
    losses = (calc['Net PnL'] < 0).sum()

    stats = pd.DataFrame([{
        "Total Trades": len(calc),
        "Wins": wins,
        "Losses": losses,
        "Strike Rate": wins / len(calc) if len(calc) else 0,
        "Net PnL": calc['Net PnL'].sum()
    }])

    # ===============================
    # WRITE EXCEL IN MEMORY
    # ===============================
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        calc.to_excel(writer, sheet_name="Calculated", index=False)
        stats.to_excel(writer, sheet_name="Stats", index=False)

    output.seek(0)

    return calc, stats, output
