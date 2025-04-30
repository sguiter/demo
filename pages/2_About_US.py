import streamlit as st
from PIL import Image

# Set page configuration
st.set_page_config(page_title="About the Team", page_icon="👥", layout="wide")

# Page Title
st.title("👥 Meet the Team")

# Introduction to the Team
st.write(
    """
    This project was made possible by the hard work and collaboration of four dedicated individuals. Below you can find information about each of the team members and their contributions to the project.
    """
)

# Create 2 rows and 2 columns layout for each team member
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

# First Row (Person 1 and Person 2)
with row1_col1:
    # Open and rotate the first image 90 degrees
    img1 = Image.open(r"C:\Users\gwapi\OneDrive\Pictures\Camera Roll\20241202_170744.jpg")  # Replace with actual image path
    img1_rotated = img1.rotate(-90, expand=True)
    st.image(img1_rotated, width=250)
    st.subheader("Aiden Beeskow")
    st.write("""
        "The Resident Accountant"
        - **Responsibilities**: Aiden was responsible for overseeing the technical development of ticker lookup feature but was ultimately shelved by executive decision.
        - **Skills**: Using only the downloads folder, hiding revenue, lowering your tax, and rizzing from a distance.
        - **Fun Fact**: Aiden can't do land sports but is optimized for aquatic performance.
        - **LinkedIn**: [Aiden Beeskow](https://www.linkedin.com/in/aiden-beeskow-62326a253/)
    """)

with row1_col2:
    # Open and rotate the second image 90 degrees
    img2 = Image.open(r"C:\Users\gwapi\OneDrive\Pictures\Camera Roll\20241202_171333.jpg")  # Replace with actual image path
    img2_rotated = img2.rotate(-90, expand=True)
    st.image(img2_rotated, width=250)
    st.subheader("Sam Brooks")
    st.write("""
        "Big Money Brooks"
        - **Responsibilities**: Sam lost his sanity trying to beautify the exported Excel file, ensuring that the financial data was presented in a clear and professional manner.
        - **Skills**: Application of AI and machine learning, programming, and other nerd things unknown to the common man.
        - **Fun Fact**: Sam rolls logs in water and plays D&D on the weekends in a secret lair.
        - **LinkedIn**: [Samuel Brooks](https://www.linkedin.com/in/samuel-brooks-59730a1b1/)
    """)

# Second Row (Person 3 and Person 4)
with row2_col1:
    st.image(r"C:\Users\gwapi\OneDrive\Pictures\Camera Roll\SG.jpg", width=250)  # Replace with actual image path
    st.subheader("Sophia Guiter")
    st.write("""
        "Zoey Survior"
        - **Responsibilities**: Sophia lost sleep trying to  make the DCF Generator to work. She designed the user interface, ensuring that the tool was intuitive, visually appealing, and easy to navigate while producing an accurate model.
        - **Skills**: UX/UI design, Streamlit, Financial Analysis, and basically everything a CFA is supposed to know.
        - **Fun Fact**: Sophia found an amazing sunny beach with temperatures 75 degrees and more in Iowa!.
        - **LinkedIn**: [Sophia Guiter](https://www.linkedin.com/in/sophia-guiter/)
    """)

with row2_col2:
    st.image(r"C:\Users\gwapi\OneDrive\Pictures\Camera Roll\IO.jpg", width=250)  # Replace with actual image path
    st.subheader("Ian Ortega")
    st.write("""
        "The Quant" 
        - **Responsibilities**: Ian was expected to make this whole damn chatbot thing work. 
        - **Skills**: Looking smart, pretending to know what he's doing, and getting Sam demoted.
        - **Fun Fact**: Can play careless whisper on the saxophone and take your mom for a date.
        - **LinkedIn**: [Ian Ortega](https://www.linkedin.com/in/iannicholas-ortega/)
    """)

# Closing Note
st.write("""
    Thank you to Hunter Sandidge and Marquette University for the support and resources provided during this project. We just want to make money off of this for REAL!
""")
