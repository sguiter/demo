# theme_utils.py
import streamlit as st

TEAM_COLORS = {
    "Default":      {"primary": "#e10600", "bg": "#000000", "secondary": "#1d1d1f", "text": "#ffffff"},
    "Ferrari":      {"primary": "#d40000", "bg": "#330000", "secondary": "#660000", "text": "#fff200"},
    "Mercedes":     {"primary": "#00d2be", "bg": "#202020", "secondary": "#004146", "text": "#B2DFDB"},
    "Red Bull":     {"primary": "#1e41ff", "bg": "#121F45", "secondary": "#e20034", "text": "#FFC906"},
    "McLaren":      {"primary": "#47C7FC", "bg": "#333333", "secondary": "#ff8000", "text": "#ffffff"},
    "Alpine":       {"primary": "#FD4BC7", "bg": "#0090ff", "secondary": "#d29bae", "text": "#ffffff"},
    "Williams":     {"primary": "#041e42", "bg": "#4e86de", "secondary": "#ffffff", "text": "#182166"},
    "Racing Bulls": {"primary": "#0090ff", "bg": "#101355", "secondary": "#e20034", "text": "#ffffff"},
    "Haas":         {"primary": "#555759", "bg": "#000000", "secondary": "#c9413a", "text": "#ffffff"},
    "Aston Martin": {"primary": "#006F62", "bg": "#1C1C1C", "secondary": "#467c78", "text": "#ffffff"},
    "Kick Sauber":  {"primary": "#0A0A0A", "bg": "#000105", "secondary": "#90da51", "text": "#ffffff"},
}

def apply_theme():
    """
    Injects the theme CSS based on st.session_state["team_theme"].
    - Initializes session_state["team_theme"] to "Default" if missing.
    - Rebuilds and injects the CSS on every run (no caching).
    """
    # 1) Ensure we have a theme selected
    if "team_theme" not in st.session_state:
        st.session_state.team_theme = "Default"

    # 2) Grab the right color palette
    colors = TEAM_COLORS.get(
        st.session_state.get("team_theme", "Default"),
        TEAM_COLORS["Default"]
    )

    # 3) Build & inject the CSS un‑cached
    css = f"""
    <style>
      /* App background */
      div[data-testid="stAppViewContainer"],
      div[data-testid="stBlock"] {{
        background-color: {colors['bg']} !important;
      }}

      /* Text colors */
      body, p, label, span {{
        color: {colors['text']} !important;
      }}

      /* Custom title classes */
      .title-center {{
        color: {colors['primary']} !important;
      }}
      .subtitle-center {{
        color: {colors['text']} !important;
      }}

      /* Buttons */
      .stButton > button {{
        background-color: {colors['primary']} !important;
        color: {colors['text']} !important;
      }}
      .stButton > button:hover {{
        background-color: {colors['secondary']} !important;
      }}

      /* Sidebar */
      div[data-testid="stSidebar"], section[data-testid="stSidebar"] {{
        background-color: {colors['secondary']} !important;
      }}
      section[data-testid="stSidebar"] * {{
        color: {colors['text']} !important;
      }}

      /* Selectboxes */
      .stSelectbox > div,
      .stSelectbox label {{
        background-color: {colors['bg']} !important;
        color: {colors['text']} !important;
      }}

      /* Hide default header */
      header[data-testid="stHeader"] {{
        display: none;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
