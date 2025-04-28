import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter

from streamlit_app.helpers.API_helpers import get_financial_statement

# -------------------------
# Helper Functions
# -------------------------

def transform_income_statement(df):
    df = df.set_index('date')
    df = df.drop(columns=[
        'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'acceptedDate',
        'calendarYear', 'period', 'link', 'finalLink'
    ], errors='ignore')
    df = df.transpose()
    df = df[df.columns[::-1]]
    return df

def transform_balance_sheet(df):
    df = df.set_index('date')
    df = df.drop(columns=[
        'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'acceptedDate',
        'calendarYear', 'period', 'link', 'finalLink'
    ], errors='ignore')
    df = df.transpose()
    df = df[df.columns[::-1]]
    return df

def transform_cash_flow(df):
    df = df.set_index('date')
    df = df.drop(columns=[
        'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'acceptedDate',
        'calendarYear', 'period', 'link', 'finalLink'
    ], errors='ignore')
    df = df.transpose()
    df = df[df.columns[::-1]]
    return df

def pull_historical_data(ticker):
    income_statement = get_financial_statement(ticker, "income-statement")
    balance_sheet = get_financial_statement(ticker, "balance-sheet-statement")
    cash_flow = get_financial_statement(ticker, "cash-flow-statement")

    income_statement = transform_income_statement(income_statement)
    balance_sheet = transform_balance_sheet(balance_sheet)
    cash_flow = transform_cash_flow(cash_flow)

    return income_statement, balance_sheet, cash_flow

# -------------------------
# Streamlit Inputs
# -------------------------

st.title("💸 Discounted Cash Flow (DCF) Calculator")

# Ticker input
ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT)")

# Forecast horizon
forecast_years = st.slider("How many years would you like to forecast?", min_value=1, max_value=10, value=5)

# Financial assumptions
st.subheader("Financial Assumptions")
revenue_growth = st.number_input("Revenue Growth Rate (%)", value=8.0) / 100
gross_margin = st.number_input("Gross Margin (%)", value=60.0) / 100
operating_costs_percent = st.number_input("Operating Costs (% of Revenue)", value=30.0) / 100
tax_rate = st.number_input("Tax Rate (%)", value=21.0) / 100
da_percent = st.number_input("D&A (% of Revenue)", value=3.0) / 100
capex_percent = st.number_input("CapEx (% of Revenue)", value=5.0) / 100

# -------------------------
# Main Build Button
# -------------------------

if st.button("Build DCF Model"):
    if ticker:
        with st.spinner("Building your DCF model..."):
            income_df, balance_df, cashflow_df = pull_historical_data(ticker)

            # Create Excel Workbook
            wb = Workbook()
            wb.remove(wb.active)

            # Create Historical Sheets
            def create_historical_sheet(wb, df, sheet_name):
                ws = wb.create_sheet(title=sheet_name)
                for r in dataframe_to_rows(df, index=True, header=True):
                    ws.append(r)

            create_historical_sheet(wb, income_df, "Income Statement")
            create_historical_sheet(wb, balance_df, "Balance Sheet")
            create_historical_sheet(wb, cashflow_df, "Cash Flow Statement")

            # Create Assumptions Sheet
            assumptions_ws = wb.create_sheet(title="Assumptions")
            assumptions_ws.append(["Input", "Value"])
            assumptions_ws.append(["Revenue Growth Rate (%)", revenue_growth])
            assumptions_ws.append(["Gross Margin (%)", gross_margin])
            assumptions_ws.append(["Operating Costs (% of Revenue)", operating_costs_percent])
            assumptions_ws.append(["Tax Rate (%)", tax_rate])
            assumptions_ws.append(["D&A (% of Revenue)", da_percent])
            assumptions_ws.append(["CapEx (% of Revenue)", capex_percent])

            # Create DCF Forecast Sheet
            forecast_ws = wb.create_sheet(title="DCF Forecast")

            lines = [
                "Revenue", "COGS", "Gross Profit", "Gross Margin %",
                "Operating Costs", "Operating Income", "Operating Margin %",
                "Income Tax", "Net Income", "Net Income Margin %", "Free Cash Flow"
            ]

            years = list(income_df.columns) + [f"Forecast {i+1}" for i in range(forecast_years)]
            forecast_ws.append(["Variable"] + years)

            row_mapping = {}
            for line in lines:
                forecast_ws.append([line] + [""] * len(years))
                row_mapping[line] = forecast_ws.max_row

            # 🔥 Correctly find real rows
            lookup_rows = {
                "revenue": None,
                "costOfRevenue": None,
                "grossProfit": None,
                "operatingIncome": None,
                "incomeTaxExpense": None,
                "netIncome": None
            }

            # Find correct row numbers
            for row_idx, row in enumerate(income_df.index, start=3):
                name = str(row).strip()
                if name in lookup_rows:
                    lookup_rows[name] = row_idx

            # Fill Historical Data
            for idx, year in enumerate(income_df.columns):
                col_letter = get_column_letter(idx + 2)

                # Revenue
                forecast_ws[f"{col_letter}{row_mapping['Revenue']}"] = f"='Income Statement'!{col_letter}{lookup_rows['revenue']}"
                # COGS
                forecast_ws[f"{col_letter}{row_mapping['COGS']}"] = f"='Income Statement'!{col_letter}{lookup_rows['costOfRevenue']}"
                # Gross Profit
                forecast_ws[f"{col_letter}{row_mapping['Gross Profit']}"] = f"='Income Statement'!{col_letter}{lookup_rows['grossProfit']}"
                # Gross Margin %
                forecast_ws[f"{col_letter}{row_mapping['Gross Margin %']}"] = f"={col_letter}{row_mapping['Gross Profit']}/{col_letter}{row_mapping['Revenue']}"
                # Operating Income
                forecast_ws[f"{col_letter}{row_mapping['Operating Income']}"] = f"='Income Statement'!{col_letter}{lookup_rows['operatingIncome']}"
                # Operating Margin %
                forecast_ws[f"{col_letter}{row_mapping['Operating Margin %']}"] = f"={col_letter}{row_mapping['Operating Income']}/{col_letter}{row_mapping['Revenue']}"
                # Income Tax
                forecast_ws[f"{col_letter}{row_mapping['Income Tax']}"] = f"='Income Statement'!{col_letter}{lookup_rows['incomeTaxExpense']}"
                # Net Income
                forecast_ws[f"{col_letter}{row_mapping['Net Income']}"] = f"='Income Statement'!{col_letter}{lookup_rows['netIncome']}"
                # Net Income Margin %
                forecast_ws[f"{col_letter}{row_mapping['Net Income Margin %']}"] = f"={col_letter}{row_mapping['Net Income']}/{col_letter}{row_mapping['Revenue']}"

            # Fill Forecast Formulas
            for i in range(forecast_years):
                idx = len(income_df.columns) + i
                col_letter = get_column_letter(idx + 2)
                prev_col = get_column_letter(idx + 1)

                forecast_ws[f"{col_letter}{row_mapping['Revenue']}"] = f"={prev_col}{row_mapping['Revenue']}*(1+Assumptions!B2)"
                forecast_ws[f"{col_letter}{row_mapping['COGS']}"] = f"={col_letter}{row_mapping['Revenue']}*(1-Assumptions!B3)"
                forecast_ws[f"{col_letter}{row_mapping['Gross Profit']}"] = f"={col_letter}{row_mapping['Revenue']}-{col_letter}{row_mapping['COGS']}"
                forecast_ws[f"{col_letter}{row_mapping['Operating Costs']}"] = f"={col_letter}{row_mapping['Revenue']}*Assumptions!B4"
                forecast_ws[f"{col_letter}{row_mapping['Operating Income']}"] = f"={col_letter}{row_mapping['Gross Profit']}-{col_letter}{row_mapping['Operating Costs']}"
                forecast_ws[f"{col_letter}{row_mapping['Income Tax']}"] = f"={col_letter}{row_mapping['Operating Income']}*Assumptions!B5"
                forecast_ws[f"{col_letter}{row_mapping['Net Income']}"] = f"={col_letter}{row_mapping['Operating Income']}-{col_letter}{row_mapping['Income Tax']}"
                forecast_ws[f"{col_letter}{row_mapping['Free Cash Flow']}"] = f"={col_letter}{row_mapping['Net Income']}+(Assumptions!B6*{col_letter}{row_mapping['Revenue']})-(Assumptions!B7*{col_letter}{row_mapping['Revenue']})"
            # Save and Streamlit Download
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            st.success(f"DCF Model for {ticker.upper()} built successfully!")

            st.download_button(
                label="📥 Download DCF Excel File",
                data=output,
                file_name=f"{ticker.upper()}_DCF_Model.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.warning("Please enter a valid ticker.")
