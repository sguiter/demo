# streamlit_app/helpers/api_helpers.py

import requests
import pandas as pd

FMP_API_KEY = "UvcEht6tbVGEdX8ER7wbvHv1Schl9wkI"
# UvcEht6tbVGEdX8ER7wbvHv1Schl9wkI
# VL9QgBf3OKJ4NaSmoQJDXUDhwCmMmVEq5nI

def get_financial_statement(ticker, statement_type):
    url = f"https://financialmodelingprep.com/api/v3/{statement_type}/{ticker.upper()}?limit=5&apikey={FMP_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        return df
    else:
        return None