import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Load the JSON data (use the correct path for your file)
with open('10K_scraper/company_tickers.json', 'r') as file:
    data = json.load(file)

# Get the current year (2024) to filter filings
current_year = "2024"

# Function to get the latest 10-K filing URL for a given CIK
def get_10k_filing_url(cik):
    # Construct the URL for the company's EDGAR filings page
    print(cik)
    edgar_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/"
    print(edgar_url)
    
    # Send a GET request to fetch the company's filings page
    response = requests.get(edgar_url)
    
    if response.status_code == 200:
        print(f"Successfully fetched filings for CIK: {cik}")
        
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for all <a> tags containing links to filings
        links = soup.find_all('a', href=True)
        
        # Find 10-K filings from 2024
        for link in links:
            if '10-K' in link['href'] and current_year in link['href']:
                # Extract the accession number and filing date from the link
                href = link['href']
                parts = href.split('/')
                
                # Extract parts from the URL
                accession_number = parts[-2]
                filing_date = parts[-1].split('-')[1][:8]  # Extracting the date part (e.g., 20240928)
                
                # Construct the full URL to the 10-K filing (HTML format)
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{accession_number}-{filing_date}.htm"
                return filing_url
    else:
        print(f"Failed to fetch filings for CIK: {cik} (Status Code: {response.status_code})")
    return None

# Function to download the 10-K filing
def download_10k_filing(filing_url, ticker):
    response = requests.get(filing_url)
    if response.status_code == 200:
        filename = f"10K_{ticker}_2024.htm"
        with open(filename, 'wb') as f:
            f.write(response.content)
            print(f"Downloaded {filename}")
    else:
        print(f"Failed to download filing for {ticker}")

# Loop through the companies in the JSON file and download their 2024 10-K filings
for item in data.values():
    ticker = item['ticker']
    cik = item['cik_str']
    
    # Get the 10-K filing URL for the company
    filing_url = get_10k_filing_url(cik)
    
    if filing_url:
        # Download the 10-K filing
        download_10k_filing(filing_url, ticker)
