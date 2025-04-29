import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Border, Side, Alignment

from streamlit_app.helpers.API_helpers import get_financial_statement
from streamlit_app.helpers.base_formatting import formatting_page


# -------------------------
# Constants
# -------------------------

RATIO_ITEMS = {
    "grossProfitRatio",
    "ebitdaratio",
    "operatingIncomeRatio",
    "incomeBeforeTaxRatio",
    "netIncomeRatio",
    "eps",
    "epsdiluted",
}

SEPARATOR_BORDER = Border(
    top=Side(style="thin", color="000000"),
    bottom=Side(style="thin", color="000000"),
)

# Fixed width (characters) for numeric year columns to avoid oversized gaps
YEAR_COL_WIDTH = 14


# -------------------------
# Helper Functions
# -------------------------

def _drop_meta_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_to_drop = [
        "symbol",
        "reportedCurrency",
        "cik",
        "fillingDate",
        "acceptedDate",
        "calendarYear",
        "period",
        "link",
        "finalLink",
    ]
    df = df.set_index("date").drop(columns=cols_to_drop, errors="ignore").transpose()
    return df[df.columns[::-1]]  # chronological order (oldest → newest)


def transform_income_statement(df: pd.DataFrame) -> pd.DataFrame:
    return _drop_meta_columns(df)


def transform_balance_sheet(df: pd.DataFrame) -> pd.DataFrame:
    return _drop_meta_columns(df)


def transform_cash_flow(df: pd.DataFrame) -> pd.DataFrame:
    return _drop_meta_columns(df)


def pull_historical_data(ticker: str):
    inc = get_financial_statement(ticker, "income-statement")
    bal = get_financial_statement(ticker, "balance-sheet-statement")
    cf = get_financial_statement(ticker, "cash-flow-statement")
    return (
        transform_income_statement(inc),
        transform_balance_sheet(bal),
        transform_cash_flow(cf),
    )


def create_historical_combined_sheet(wb: Workbook, dfs, titles):
    ws = wb.create_sheet("Historical")
    start_row = 1

    for df, title in zip(dfs, titles):
        ws.cell(row=start_row, column=1, value=title)
        for col_idx in range(1, df.shape[1] + 2):
            ws.cell(row=start_row, column=col_idx).border = SEPARATOR_BORDER

        for r_idx, row in enumerate(dataframe_to_rows(df, index=True, header=True), start=start_row + 1):
            for c_idx, val in enumerate(row, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                if r_idx > start_row + 1 and row[0] in RATIO_ITEMS:
                    cell.font = Font(bold=True, name=cell.font.name, size=cell.font.size)

        start_row += df.shape[0] + 1 + 5


# -------------------------
# Streamlit UI
# -------------------------

st.title("💸 Discounted Cash Flow (DCF) Calculator")

ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT)")
forecast_years = st.slider("How many years to forecast?", 1, 10, 5)

st.subheader("Financial Assumptions")
revenue_growth = st.number_input("Revenue Growth Rate (%)", 8.0) / 100
gross_margin = st.number_input("Gross Margin (%)", 60.0) / 100
operating_costs_percent = st.number_input("Operating Costs (% of Revenue)", 30.0) / 100
tax_rate = st.number_input("Tax Rate (%)", 21.0) / 100
da_percent = st.number_input("D&A (% of Revenue)", 3.0) / 100
capex_percent = st.number_input("CapEx (% of Revenue)", 5.0) / 100

if st.button("Build DCF Model"):
    if not ticker:
        st.warning("Please enter a valid ticker.")
    else:
        with st.spinner("Building your DCF model..."):
            # -------------------------
            # Pull & transform statements
            # -------------------------
            inc_df, bal_df, cf_df = pull_historical_data(ticker)
            inc_df.columns = pd.to_datetime(inc_df.columns).date
            bal_df.columns = pd.to_datetime(bal_df.columns).date
            cf_df.columns = pd.to_datetime(cf_df.columns).date

            for df in (inc_df, bal_df, cf_df):
                non_ratio_mask = [idx not in RATIO_ITEMS for idx in df.index]
                df.loc[non_ratio_mask] = df.loc[non_ratio_mask] / 1_000_000

            # -------------------------
            # Build Workbook
            # -------------------------
            wb = Workbook()
            wb.remove(wb.active)

            create_historical_combined_sheet(
                wb,
                dfs=[inc_df, bal_df, cf_df],
                titles=["Income Statement", "Balance Sheet", "Statement of Cash Flows"],
            )

            # Assumptions
            asum = wb.create_sheet("Assumptions")
            asum.append(["Input", "Value"])
            asum.append(["Revenue Growth Rate (%)", revenue_growth])
            asum.append(["Gross Margin (%)", gross_margin])
            asum.append(["Operating Costs (% of Revenue)", operating_costs_percent])
            asum.append(["Tax Rate (%)", tax_rate])
            asum.append(["D&A (% of Revenue)", da_percent])
            asum.append(["CapEx (% of Revenue)", capex_percent])

            for cell in asum["B"][1:]:
                cell.number_format = "0.00%"

            for col in ["A", "B"]:
                max_len = 0
                for cell in asum[col]:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
                    display = (
                        f"{cell.value:.2%}" if (col == "B" and isinstance(cell.value, (int, float))) else str(cell.value)
                    )
                    max_len = max(max_len, len(display))
                asum.column_dimensions[col].width = max_len + 3

            # -------------------------
            # DCF Forecast
            # -------------------------
            forecast_ws = wb.create_sheet("DCF Forecast")

            lines = [
                "Revenue",
                "COGS",
                "Gross Profit",
                "Gross Margin %",
                "Operating Costs",
                "Operating Income",
                "Operating Margin %",
                "Income Tax",
                "Net Income",
                "Net Income Margin %",
                "Free Cash Flow",
            ]

            hist_years = inc_df.columns.tolist()
            last_hist_year = hist_years[-1].year
            fcast_years = [last_hist_year + i + 1 for i in range(forecast_years)]
            years = hist_years + fcast_years

            # Header row
            forecast_ws.append(["Variable"] + years)

            # Bold **all** year headers (historical + forecast)
            for col_idx in range(2, 2 + len(years)):
                hdr_cell = forecast_ws.cell(row=1, column=col_idx)
                hdr_cell.font = Font(bold=True, name=hdr_cell.font.name, size=hdr_cell.font.size)

            # Append line labels
            row_map = {}
            for label in lines:
                forecast_ws.append([label] + [""] * len(years))
                row_map[label] = forecast_ws.max_row

            # Historical look-ups
            for col_idx in range(2, 2 + len(hist_years)):
                col_letter = get_column_letter(col_idx)
                forecast_ws[f"{col_letter}{row_map['Revenue']}"] = f"='Historical'!{col_letter}4"

                lookup = {
                    "COGS": "costOfRevenue",
                    "Gross Profit": "grossProfit",
                    "Operating Income": "operatingIncome",
                    "Income Tax": "incomeTaxExpense",
                    "Net Income": "netIncome",
                }
                for var, key in lookup.items():
                    hist_row = next(r for r, v in enumerate(inc_df.index, start=3) if v == key)
                    forecast_ws[f"{col_letter}{row_map[var]}"] = f"='Historical'!{col_letter}{hist_row}"

                forecast_ws[f"{col_letter}{row_map['Gross Margin %']}"] = (
                    f"={col_letter}{row_map['Gross Profit']}/{col_letter}{row_map['Revenue']}"
                )
                forecast_ws[f"{col_letter}{row_map['Operating Margin %']}"] = (
                    f"={col_letter}{row_map['Operating Income']}/{col_letter}{row_map['Revenue']}"
                )
                forecast_ws[f"{col_letter}{row_map['Net Income Margin %']}"] = (
                    f"={col_letter}{row_map['Net Income']}/{col_letter}{row_map['Revenue']}"
                )

            # Forecast formulas
            for i in range(forecast_years):
                col_idx = 2 + len(hist_years) + i
                col_letter = get_column_letter(col_idx)
                prev_col = get_column_letter(col_idx - 1)

                forecast_ws[f"{col_letter}{row_map['Revenue']}"] = f"={prev_col}{row_map['Revenue']}*(1+Assumptions!B2)"
                forecast_ws[f"{col_letter}{row_map['COGS']}"] = f"={col_letter}{row_map['Revenue']}*(1-Assumptions!B3)"
                forecast_ws[f"{col_letter}{row_map['Gross Profit']}"] = (
                    f"={col_letter}{row_map['Revenue']}-{col_letter}{row_map['COGS']}"
                )
                forecast_ws[f"{col_letter}{row_map['Operating Costs']}"] = (
                    f"={col_letter}{row_map['Revenue']}*Assumptions!B4"
                )
                forecast_ws[f"{col_letter}{row_map['Operating Income']}"] = (
                    f"={col_letter}{row_map['Gross Profit']}-{col_letter}{row_map['Operating Costs']}"
                )
                forecast_ws[f"{col_letter}{row_map['Income Tax']}"] = (
                    f"={col_letter}{row_map['Operating Income']}*Assumptions!B5"
                )
                forecast_ws[f"{col_letter}{row_map['Net Income']}"] = (
                    f"={col_letter}{row_map['Operating Income']}-{col_letter}{row_map['Income Tax']}"
                )
                forecast_ws[f"{col_letter}{row_map['Free Cash Flow']}"] = (
                    f"={col_letter}{row_map['Net Income']}+"
                    f"(Assumptions!B6*{col_letter}{row_map['Revenue']})-"
                    f"(Assumptions!B7*{col_letter}{row_map['Revenue']})"
                )

            # -------------------------
            # Formatting for all sheets
            # -------------------------
            for sheet in wb.worksheets:
                formatting_page(sheet)

                for col_idx in range(1, sheet.max_column + 1):
                    letter = get_column_letter(col_idx)

                    # Fixed width for numeric year columns on DCF Forecast
                    if sheet.title == "DCF Forecast" and col_idx >= 2:
                        sheet.column_dimensions[letter].width = YEAR_COL_WIDTH
                    else:
                        values = [
                            str(c.value).rstrip()
                            for c in sheet[letter]
                            if c.value is not None
                        ]
                        sheet.column_dimensions[letter].width = (max(map(len, values)) + 1) if values else 1

                    for cell in sheet[letter]:
                        cell.alignment = Alignment(horizontal="left", vertical=cell.alignment.vertical)

            # -------------------------
            # Bold forecast VALUES
            # -------------------------
            num_hist = len(hist_years)
            for col_idx in range(2 + num_hist, 2 + num_hist + forecast_years):
                for row_idx in range(2, forecast_ws.max_row + 1):
                    cell = forecast_ws.cell(row=row_idx, column=col_idx)
                    cell.font = Font(bold=True, name=cell.font.name, size=cell.font.size)

            # -------------------------
            # Streamlit download
            # -------------------------
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            st.success(f"DCF Model for {ticker.upper()} built successfully!")
            st.download_button(
                "📥 Download DCF Excel File",
                data=buffer,
                file_name=f"{ticker.upper()}_DCF_Model.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
