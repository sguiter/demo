# streamlit_app/helpers/excel_helpers.py

import io
import pandas as pd

def create_excel_file(income_df, balance_df, cashflow_df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        income_df.to_excel(writer, sheet_name='Income Statement', index=False)
        balance_df.to_excel(writer, sheet_name='Balance Sheet', index=False)
        cashflow_df.to_excel(writer, sheet_name='Cash Flow Statement', index=False)
    buffer.seek(0)
    return buffer
