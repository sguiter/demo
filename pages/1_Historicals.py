import streamlit as st
import pandas as pd

from streamlit_app.helpers.API_helpers import get_financial_statement
from streamlit_app.helpers.excel_helpers import create_excel_file

def transform_income_statement(df):
    df = df.set_index('date')
    df = df.drop(columns=[
        'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'acceptedDate',
        'calendarYear', 'period', 'link', 'finalLink'
    ], errors='ignore')
    df = df.transpose()
    df = df[df.columns[::-1]]  # Flip columns oldest -> newest
    return df

def transform_balance_sheet(df):
    df = df.set_index('date')
    df = df.drop(columns=[
        'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'acceptedDate',
        'calendarYear', 'period', 'link', 'finalLink'
    ], errors='ignore')
    df = df.transpose()
    df = df[df.columns[::-1]]  # Flip columns oldest -> newest
    return df

def transform_cash_flow(df):
    df = df.set_index('date')
    df = df.drop(columns=[
        'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'acceptedDate',
        'calendarYear', 'period', 'link', 'finalLink'
    ], errors='ignore')
    df = df.transpose()
    df = df[df.columns[::-1]]  # Flip columns oldest -> newest
    return df

# Historical Financials Page
st.title("📜 Historical Financials")

ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT)")

if st.button("Download Financials"):
    if ticker:
        # ADDING SPINNER HERE ✅
        with st.spinner('Loading financial data...'):
            income_df = get_financial_statement(ticker, "income-statement")
            balance_df = get_financial_statement(ticker, "balance-sheet-statement")
            cashflow_df = get_financial_statement(ticker, "cash-flow-statement")

        if income_df is not None and balance_df is not None and cashflow_df is not None:
            # Transform the pulled financials
            income_df = transform_income_statement(income_df)
            balance_df = transform_balance_sheet(balance_df)
            cashflow_df = transform_cash_flow(cashflow_df)

            st.success(f"Showing financials for {ticker.upper()}")

            st.subheader("Income Statement")
            st.dataframe(income_df)

            st.subheader("Balance Sheet")
            st.dataframe(balance_df)

            st.subheader("Cash Flow Statement")
            st.dataframe(cashflow_df)

            excel_file = create_excel_file(income_df, balance_df, cashflow_df)

            st.download_button(
                label="📥 Download Financials as Excel",
                data=excel_file,
                file_name=f"{ticker.upper()}_financials.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Failed to fetch one or more financial statements.")
    else:
        st.warning("Please enter a valid ticker.")

