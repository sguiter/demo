import streamlit as st
import requests
import pandas as pd

# --- Page Configuration (must be first Streamlit command) ---
st.set_page_config(
    page_title="Home - DEMO",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Original Application Code ---
def original_app(page):
    if page == "Home":
        st.title("🏛️ DEMO")
        st.write(
            """
            Welcome to DEMO!  
            This platform provides financial data, downloadable models, and financial analysis tools.
            
            (Summary of app functionality coming soon...)
            """
        )
    elif page == "Historicals":
        st.title("Historicals")
        st.write("Historical data view.")
    elif page == "DCF":
        st.title("DCF")
        st.write("Discounted Cash Flow tool.")
    elif page == "How To":
        st.title("How To")
        st.write("Instructions and guides.")
    elif page == "About US":
        st.title("About US")
        st.write("Information about us.")


def get_cik_from_ticker(ticker):
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "Your Name your.email@example.com", "Accept": "application/json"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    for item in data.values():
        if item["ticker"].lower() == ticker.lower():
            return str(item["cik_str"]).zfill(10)
    return None


def get_xbrl_metrics(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": "Your Name your.email@example.com"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    facts = resp.json().get("facts", {}).get("us-gaap", {})
    metrics = {}
    for tag, content in facts.items():
        usd_entries = content.get("units", {}).get("USD", [])
        if not usd_entries:
            continue
        entry = max(usd_entries, key=lambda x: x.get("end", ""))
        val = entry.get("val")
        end_date = entry.get("end")
        if val is None:
            continue
        try:
            display_val = f"{int(val):,}"
        except Exception:
            display_val = str(val)
        metrics[tag] = {"Value": display_val, "Date": end_date}
    return metrics


def edgar_parser_tab():
    st.header("10-K Parser")
    # Input and fetch
    ticker = st.text_input("Enter stock ticker", key="ticker_input")
    if st.button("Fetch 10-K Metrics", key="fetch_button"):
        if not ticker:
            st.error("Please enter a ticker symbol.")
        else:
            try:
                cik = get_cik_from_ticker(ticker)
                if not cik:
                    st.error("Invalid ticker or CIK not found.")
                    return
                metrics = get_xbrl_metrics(cik)
                if not metrics:
                    st.warning("No USD metrics available for this company.")
                    return
                # Store DataFrame in session state
                df = pd.DataFrame.from_dict(metrics, orient="index")
                df.index.name = "Metric"
                df.sort_index(inplace=True)
                st.session_state['metrics_df'] = df
                st.session_state['favorites'] = []
            except requests.HTTPError as e:
                st.error(f"Error fetching metrics: {e}")

    # Display after fetch
    if 'metrics_df' in st.session_state:
        df = st.session_state['metrics_df']
        st.write(f"Showing {len(df)} metrics for {ticker.upper()}.")
        # Multiselect with persistence
        st.subheader("Search and Favorite Metrics")
        favorites = st.multiselect(
            "Search or select metrics to favorite:",
            options=df.index.tolist(),
            default=st.session_state.get('favorites', [])
        )
        # Update session state favorites
        st.session_state['favorites'] = favorites
        if favorites:
            st.write("### Favorite Metrics")
            fav_df = df.loc[favorites]
            st.dataframe(fav_df)
            fav_csv = fav_df.to_csv().encode('utf-8')
            st.download_button(
                "Download Favorite Metrics CSV",
                fav_csv,
                file_name=f"{ticker}_favorite_metrics.csv",
                mime="text/csv"
            )
        else:
            st.info("Select metrics above to mark as favorites.")
        st.subheader("All Retrieved Metrics")
        st.dataframe(df)


def main():
    st.sidebar.title("Navigation")
    menu_items = ["Home", "Historicals", "DCF", "How To", "About US", "10-K Parser"]
    page = st.sidebar.selectbox("Go to", menu_items)
    if page == "10-K Parser":
        edgar_parser_tab()
    else:
        original_app(page)

if __name__ == "__main__":
    main()
