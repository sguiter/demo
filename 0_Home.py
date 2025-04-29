import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Home - DEMO",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---

def get_cik_from_ticker(ticker):
    """
    Convert stock ticker to SEC CIK using official SEC mapping.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {
        "User-Agent": "Your Name your.email@example.com",
        "Accept": "application/json"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    for item in data.values():
        if item["ticker"].lower() == ticker.lower():
            return str(item["cik_str"]).zfill(10)
    return None

@st.cache_data

def get_historical_revenue(cik, tags=["SalesRevenueNet", "Revenues"], years=5):
    """
    Retrieve the last `years` fiscal-year revenues from XBRL Company Facts.
    """
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": "Your Name your.email@example.com"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    facts = resp.json().get("facts", {}).get("us-gaap", {})
    rev = {}
    for tag in tags:
        entries = facts.get(tag, {}).get("units", {}).get("USD", [])
        annual = [e for e in entries if e.get("fp") == "FY"]
        for e in annual:
            year, val = e.get("fy"), e.get("val")
            if year and val is not None:
                rev[year] = val
        if rev:
            break
    df = pd.DataFrame.from_dict(rev, orient='index', columns=['Revenue']) if rev else pd.DataFrame()
    df.index.name = 'Year'
    df.sort_index(inplace=True)
    return df.tail(years)


def compute_cagr(df):
    """
    Compute CAGR from first to last entry in DataFrame.
    """
    if df.shape[0] < 2:
        return None
    years = df.index.to_list()
    start, end = df.iloc[0, 0], df.iloc[-1, 0]
    period = years[-1] - years[0]
    if start > 0 and period > 0:
        return (end / start) ** (1 / period) - 1
    return None

@st.cache_data

def get_xbrl_metrics(cik):
    """
    Return a DataFrame of all USD-denominated XBRL metrics with Value and Date.
    """
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": "Your Name your.email@example.com"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    facts = resp.json().get("facts", {}).get("us-gaap", {})
    data = {}
    for tag, content in facts.items():
        entries = content.get("units", {}).get("USD", [])
        if not entries:
            continue
        latest = max(entries, key=lambda x: x.get('end', ''))
        val, date = latest.get('val'), latest.get('end')
        if val is not None:
            data[tag] = {'Value': val, 'Date': date}
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index.name = 'Metric'
    return df

@st.cache_data

def compute_wacc(cik, tax_rate, rf_rate, equity_risk_premium):
    """
    Calculate WACC using CAPM for cost of equity and interest/divided debt for cost of debt.
    """
    df = get_xbrl_metrics(cik)
    # Cost of Equity (CAPM)
    if 'Beta' in df.index:
        try:
            beta = float(df.at['Beta', 'Value'])
            coe = rf_rate + beta * equity_risk_premium
        except Exception:
            coe = None
    else:
        coe = None
    # Cost of Debt
    if 'InterestExpense' in df.index:
        try:
            interest = float(df.at['InterestExpense', 'Value'])
        except Exception:
            interest = 0.0
    else:
        interest = 0.0
    debt_cur = float(df.at['DebtCurrent', 'Value']) if 'DebtCurrent' in df.index else 0.0
    debt_lt = float(df.at['LongTermDebtNoncurrent', 'Value']) if 'LongTermDebtNoncurrent' in df.index else 0.0
    total_debt = debt_cur + debt_lt
    cod = (interest / total_debt) if total_debt > 0 else None
    # Capital Structure
    if 'StockholdersEquity' in df.index:
        try:
            equity_val = float(df.at['StockholdersEquity', 'Value'])
        except Exception:
            return None
    else:
        return None
    total_val = equity_val + total_debt
    if total_val <= 0:
        return None
    w_e = equity_val / total_val
    w_d = total_debt / total_val
    if coe is None or cod is None:
        return None
    return w_e * coe + w_d * cod * (1 - tax_rate)

# --- Original App Pages ---

def original_app(page):
    if page == 'Home':
        st.title('🏛️ DEMO')
        st.write('Welcome to DEMO! This platform provides financial analysis tools.')
    elif page == 'Historicals':
        st.title('Historicals')
        st.write('Historical data and charts.')
    elif page == 'How To':
        st.title('How To')
        st.write('User guides and documentation.')
    elif page == 'About US':
        st.title('About US')
        st.write('Information about the developer.')

# --- DCF Tab ---

def dcf_tab():
    st.title('Discounted Cash Flow (DCF) Calculator')
    ticker = st.text_input('Enter a stock ticker:', key='dcf_ticker')
    years = st.slider('Forecast Years', 1, 10, 5)

    # Scenario Assumptions
    scenario_names = ['Base', 'Upside', 'Downside']
    tabs = st.tabs(scenario_names)
    scenarios = {}
    defaults = dict(growth=8, gm=60, oc=30, tax=21, da=3, cap=5)
    for name, tab in zip(scenario_names, tabs):
        with tab:
            scenarios[name] = {
                'growth': st.number_input(f'Revenue Growth % ({name})', value=defaults['growth'], key=f'g_{name}'),
                'gm': st.number_input(f'Gross Margin % ({name})', value=defaults['gm'], key=f'gm_{name}'),
                'oc': st.number_input(f'Operating Cost % ({name})', value=defaults['oc'], key=f'oc_{name}'),
                'tax': st.number_input(f'Tax Rate % ({name})', value=defaults['tax'], key=f'tax_{name}'),
                'da': st.number_input(f'D&A % ({name})', value=defaults['da'], key=f'da_{name}'),
                'cap': st.number_input(f'CapEx % ({name})', value=defaults['cap'], key=f'cap_{name}')
            }
    rf_rate = st.number_input('Risk-Free Rate %', value=3.0, key='rf') / 100
    erp = st.number_input('Equity Risk Premium %', value=5.0, key='erp') / 100

    if st.button('Build DCF & Sensitivity'):
        if not ticker:
            st.error('Please enter a ticker symbol.')
            return
        cik = get_cik_from_ticker(ticker)
        rev_df = get_historical_revenue(cik)
        cagr = compute_cagr(rev_df) or 0

        # Scenario NPVs
        npvs = {}
        for name, ass in scenarios.items():
            last_rev = rev_df.iloc[-1, 0]
            val = last_rev * ((1 + ass['growth'] / 100) ** years) * (ass['gm'] / 100)
            npvs[name] = val
        df_npvs = pd.Series(npvs, name='NPV').to_frame()
        st.subheader('Scenario Valuations')
        st.table(df_npvs)

        # Tornado Sensitivity ±10%
        base_ass = scenarios['Base']
        sens = {}
        for key, val in base_ass.items():
            for delta in [-0.1, 0.1]:
                ass = base_ass.copy()
                ass[key] = val * (1 + delta)
                last_rev = rev_df.iloc[-1, 0]
                s_val = last_rev * ((1 + ass['growth'] / 100) ** years) * (ass['gm'] / 100)
                sens[f'{key} {int(delta*100)}%'] = s_val
        df_sens = pd.Series(sens, name='NPV').to_frame()
        df_sens['Delta'] = df_sens['NPV'] - df_npvs.loc['Base', 'NPV']
        df_sens = df_sens.reindex(df_sens['Delta'].abs().sort_values(ascending=False).index)
        st.subheader('Sensitivity Tornado Chart')
        fig, ax = plt.subplots()
        ax.barh(df_sens.index, df_sens['Delta'])
        ax.set_xlabel('NPV Change')
        st.pyplot(fig)

        # WACC Calculation
        wacc = compute_wacc(cik, scenarios['Base']['tax'] / 100, rf_rate, erp)
        st.metric('5-Year Revenue CAGR', f'{cagr:.2%}')
        if wacc is not None:
            st.metric('WACC', f'{wacc:.2%}')
        else:
            st.warning('WACC could not be calculated.')

# --- 10-K Parser Tab ---

def edgar_parser_tab():
    st.title('10-K Key Metrics from XBRL')
    ticker = st.text_input('Enter stock ticker:', key='parser_ticker')
    if st.button('Fetch 10-K Metrics'):
        if not ticker:
            st.error('Please enter a ticker symbol.')
            return
        cik = get_cik_from_ticker(ticker)
        df = get_xbrl_metrics(cik)
        st.dataframe(df)

# --- Main Navigation ---

def main():
    st.sidebar.title('Navigation')
    pages = ['Home', 'Historicals', 'DCF', 'How To', 'About US', '10-K Parser']
    choice = st.sidebar.selectbox('Go to', pages)
    if choice == 'DCF':
        dcf_tab()
    elif choice == '10-K Parser':
        edgar_parser_tab()
    else:
        original_app(choice)

if __name__ == '__main__':
    main()