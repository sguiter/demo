import streamlit as st

# Set page configuration
st.set_page_config(page_title="How to Use - DCF Generator", page_icon="📚", layout="wide")

# Title of the Page
st.title("📚 How to Use the DCF Generator")

# Introduction to the Page
st.markdown("""
Welcome to the **DCF Generator** how-to guide. This page will walk you through the steps to use the tool and generate a discounted cash flow (DCF) model. 

The **Discounted Cash Flow (DCF)** method is an essential valuation tool used by investors, analysts, and businesses to estimate the value of a company based on projected cash flows. With this tool, you can easily calculate the intrinsic value of a company by adjusting various assumptions and parameters.
""")

# Step-by-step Instructions
st.header("Step-by-Step Instructions")

st.subheader("1. Enter the Stock Ticker")
st.write(
    """
    The first step is to input the stock ticker of the company you're interested in analyzing. For example, if you're analyzing **Apple**, enter `AAPL`. If you're analyzing **Microsoft**, enter `MSFT`. 
    
    - Go to the input box labeled **"Enter a stock ticker"**.
    - Type the stock ticker symbol and press enter.
    - The tool will fetch the company's financial statements (income statement, balance sheet, and cash flow) for the selected ticker.
    """
)

st.subheader("2. Review the Historical Financial Statements")
st.write(
    """
    After entering the ticker, the tool will pull the **historical financial data** for the company. This includes:
    
    - **Income Statement**
    - **Balance Sheet**
    - **Cash Flow Statement**
    
    You can view these financial statements in tabular format. If the data is available, the tables will show the latest data for each statement.
    """
)

st.subheader("3. Set Assumptions & Inputs")
st.write(
    """
    After reviewing the historical data, you can adjust assumptions and inputs for the model. The DCF Generator will automatically calculate the following parameters:
    
    - **Forecast Period (years)**: How many years of forecasted data you want to generate (typically 5 to 10 years).
    - **Long-Term Growth Rate (%)**: This represents the long-term growth assumption for the company’s revenue after the forecast period.
    - **Revenue YoY Growth (%)**: The year-on-year revenue growth rate for each of the forecast years.
    - **Gross Margin (%), Operating Margin (%), Tax Rate (%)**: You can adjust these based on historical values or input your own assumptions.
    - **D&A (% of Revenue), CapEx (% of Revenue), Other Income/Expense (% of Revenue), Interest Expense (% of Revenue)**: These values are based on historical data or can be manually adjusted.
    - **Discount Rate (%)**: This rate is used to discount future cash flows back to their present value.
    
    Once the assumptions are set, click on the **Next** button to proceed.
    """
)

st.subheader("4. Generate the DCF Model")
st.write(
    """
    After setting the assumptions, click on **"Generate DCF"** to calculate the discounted cash flow (DCF) model. The tool will automatically:
    
    - Calculate **Free Cash Flow** based on your inputs.
    - Calculate the **Discounted Cash Flow** for each year of the forecast period.
    - Calculate the **Terminal Value**.
    - Calculate the **Enterprise Value** and **Share Price**.
    
    The results will be displayed in an **Excel file** that you can download for further analysis.
    """
)

st.subheader("5. Download the DCF Excel Model")
st.write(
    """
    Once the model is generated, you will see a **Download button** labeled **"Download DCF Excel File"**. 
    Click the button to download the model, which includes the following sheets:
    
    - **Historical Financial Statements**
    - **Assumptions**
    - **DCF Forecast**
    
    The Excel file will contain all the calculated values, including Free Cash Flow, Enterprise Value, Terminal Value, and Share Price.
    """
)

# Conclusion
st.header("You're Ready to Start!")
st.write(
    """
    That's it! You can now use the DCF Generator to estimate the intrinsic value of any company based on its financial data. If you have any further questions or need help, feel free to reach out to us!
    """
)

st.markdown("""
### Disclaimer:
The tool provides estimates based on user inputs and historical data. Please ensure you review the assumptions thoroughly before making any investment decisions.
""")
