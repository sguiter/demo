import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Home - DCF Generator", 
    page_icon="🤑", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Page Title
st.title("🤑 DCF Generator")

# Introduction and Purpose
st.header("What is the DCF Generator?")
st.write(
    """
    The **Discounted Cash Flow (DCF) Generator** is a powerful tool designed to help individuals, investors, and businesses make informed financial decisions.
    
    By using this tool, you can calculate the intrinsic value of a company based on its future cash flows. The DCF method is widely used in financial analysis to estimate the value of an investment or business, especially for long-term valuation purposes.
    """
)

# Introduction and Purpose
st.header("Why D.E.M.O?")
st.write(
    """
-----Discounted Estimation & Modeling Organizer-----

Discounted: Refers to the core Discounted Cash Flow (DCF) methodology used in the tool.

Estimation: Reflects the process of estimating the intrinsic value of a company based on projected cash flows.

Modeling: Indicates the tool's ability to create financial models, which are essential to DCF analysis.

Organizer: Highlights the tool’s ability to organize and structure financial data, making it easy to perform and present DCF calculations.
    """
)

# Who Would Benefit
st.header("Who Can Benefit from This Tool?")
st.write(
    """
    This tool is ideal for:
    - **Investors**: Whether you're a retail investor or a professional, the DCF Generator can help you assess whether a company's stock is under- or overvalued.
    - **Financial Analysts**: Analysts can use this tool to quickly generate models and present results for investment decision-making.
    - **Business Owners**: If you're a business owner looking to understand your company's valuation, this tool will allow you to estimate your business’s worth based on cash flows.
    - **Students**: Perfect for finance and business students who want to practice financial modeling and learn about valuation techniques.
    """
)

# Key Features
st.header("Key Features of the DCF Generator")
st.write(
    """
    - **Flexible Inputs**: Customize the forecast period, discount rate, and growth rate.
    - **Easy-to-Use Interface**: No prior financial modeling experience needed.
    - **Real-Time Calculations**: Instant feedback on your inputs, with dynamic outputs for the DCF calculation.
    - **Downloadable Models**: Once the DCF is calculated, download your results in Excel format for further analysis or reporting.
    - **Accurate and Reliable**: Uses industry-standard financial methods for accurate company valuation.
    """
)

# Additional Information
st.header("Why Use the DCF Generator?")
st.write(
    """
    - **Time-Saving**: Instead of manually setting up DCF models, this tool automates calculations and offers easy-to-understand visualizations.
    - **Decision Support**: The DCF model provides crucial insight into the future cash flow potential of a company, helping investors make more informed decisions.
    - **Transparent Assumptions**: Users can clearly see and adjust key assumptions like growth rate and discount rate, providing transparency in the financial models.
    """
)

# Closing Remark
st.write("Feel free to explore the features and begin your financial analysis with the DCF Generator!")

