import json

# Load the JSON data
with open('10K_scraper/nyse_stocks.json', 'r') as file:
    data = json.load(file)

# Print the type and structure of the data to confirm it's a dictionary
print(f"Data type: {type(data)}")
print(f"Data structure: {data}")

# Extract the tickers from the dictionary
tickers = [item['ACT Symbol'] for item in data]

# Save the tickers to a text file
with open('10K_scraper/company_tickers.txt', 'w') as output_file:
    for ticker in tickers:
        output_file.write(ticker + '\n')

print("Tickers have been saved to 'company_tickers.txt'")

# Open the text file and calculate the number of lines
with open('10K_scraper/company_tickers.txt', 'r') as file:
    lines = file.readlines()  # Read all lines in the file
    num_lines = len(lines)  # Get the number of lines
    print(f"The number of lines in the file is: {num_lines}")