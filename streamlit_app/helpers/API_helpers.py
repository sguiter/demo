# streamlit_app/helpers/api_helpers.py

import requests
import pandas as pd
from config import FMP_API_KEY

def get_financial_statement(ticker, statement_type):
    url = f"https://financialmodelingprep.com/api/v3/{statement_type}/{ticker.upper()}?limit=5&apikey={FMP_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        return df
    else:
        return None
