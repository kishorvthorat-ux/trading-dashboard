import pandas as pd
import numpy as np
import io

def process_csv(file):
    df = pd.read_csv(file)

    # ✅ Clean column names
    df.columns = df.columns.str.strip()

    # ✅ Ensure datetime
    df['Date and time'] = pd.to_datetime(df['Date and time'])

    # ✅ Sort CORRECTLY (critical for your file)
    df = df.sort_values(by=['Trade number', 'Date and time'])

    # ✅ Split Entry / Exit
    entries = df[df['Type'].str.contains("Entry", case=False, na=False)].copy()
    exits = df[df['Type'].str.contains("Exit", case=False, na=False)].copy()

    # ✅ Rename columns
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

    # ✅ Keep ONLY required columns (avoids _x _y issue)
    entries = entries[['Trade number', 'Entry Type', 'Entry Date', 'Entry Signal', 'Entry Price']]
    exits = exits[['Trade number', 'Exit Type', 'Exit Date', 'Exit Signal', 'Exit Price']]

    # ✅ Merge
    calc = pd.merge(entries, exits, on='Trade number', how='inner')

    # ✅ SAFETY CHECK (very important)
    if 'Entry Price' not in calc.columns or 'Exit Price' not in calc.columns:
        raise ValueError("Entry/Exit columns missing after merge")

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
    # EXCEL OUTPUT
    # ===============================
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        calc.to_excel(writer, sheet_name="Calculated", index=False)
        stats.to_excel(writer, sheet_name="Stats", index=False)

    output.seek(0)

    return calc, stats, output
