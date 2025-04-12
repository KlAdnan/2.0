import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import yfinance as yf
from streamlit_option_menu import option_menu
import sqlite3
import hashlib

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="AI Financial Planner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ SESSION STATE ============
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'theme' not in st.session_state:     # Initialize 'theme' in session state
    st.session_state.theme = "light"     # Default to "light" theme

# ============ THEME IMPLEMENTATION ============
def load_css():
    # Define CSS for both light and dark themes
    light_theme = """
    <style>
    .stApp {
        background-color: #F7F7F7;
        color: #1E3932;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        border-radius: 0.5rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #00704A;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem;
        padding: 10px 20px;
        background-color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00704A;
        color: white;
    }
    .stButton>button {
        border-radius: 0.5rem;
        background-color: #00704A;
        color: white;
    }
    .stButton>button:hover {
        background-color: #C6A969;
        color: #1E3932;
    }
    .stExpander {
        border-radius: 0.5rem;
        border: 1px solid #e6e6e6;
    }
    div[data-testid="stForm"] {
        border-radius: 0.5rem;
        border: 1px solid #e6e6e6;
        padding: 1rem;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 0.5rem;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #00704A;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-radius: 0;
    }
    /* Theme toggle button */
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 70px;
        z-index: 1000;
        display: flex;
        align-items: center;
        font-size: 14px;
        background-color: white;
        border-radius: 20px;
        padding: 5px 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        cursor: pointer;
    }
    .theme-toggle img {
        width: 25px;
        height: 25px;
        margin-right: 5px;
    }
    </style>
    """
    
    dark_theme = """
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        border-radius: 0.5rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #C6A969;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem;
        padding: 10px 20px;
        background-color: #2D2D2D;
        color: #E0E0E0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00704A;
        color: white;
    }
    .stButton>button {
        border-radius: 0.5rem;
        background-color: #00704A;
        color: white;
    }
    .stButton>button:hover {
        background-color: #C6A969;
        color: #1E3932;
    }
    .stExpander {
        border-radius: 0.5rem;
        border: 1px solid #444444;
    }
    div[data-testid="stForm"] {
        border-radius: 0.5rem;
        border: 1px solid #444444;
        padding: 1rem;
        background-color: #2D2D2D;
    }
    div[data-testid="stMetric"] {
        background-color: #2D2D2D;
        border-radius: 0.5rem;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        color: #E0E0E0;
    }
    div[data-testid="stMetric"] label {
        color: #C6A969;
    }
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #00704A;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-radius: 0;
    }
    /* Theme toggle button */
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 70px;
        z-index: 1000;
        display: flex;
        align-items: center;
        font-size: 14px;
        background-color: #2D2D2D;
        color: #E0E0E0;
        border-radius: 20px;
        padding: 5px 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        cursor: pointer;
    }
    .theme-toggle img {
        width: 25px;
        height: 25px;
        margin-right: 5px;
    }
    /* Additional dark theme elements */
    .stDataFrame, .stTable {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border-radius: 0.5rem;
    }
    .stSelectbox, .stNumberInput, .stDateInput, .stTextInput, .stTextArea {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border-radius: 0.5rem;
    }
    </style>
    """

    royal_theme = """
    <style>
    .stApp {
        background-color: #0A1747;
        color: #E3F2FD;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        border-radius: 0.5rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FFD700;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem;
        padding: 10px 20px;
        background-color: #122164;
        color: #E3F2FD;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1A237E;
        color: #FFD700;
    }
    .stButton>button {
        border-radius: 0.5rem;
        background-color: #1A237E;
        color: #FFD700;
    }
    .stButton>button:hover {
        background-color: #3949AB;
        color: #E3F2FD;
    }
    .stExpander {
        border-radius: 0.5rem;
        border: 1px solid #3949AB;
    }
    div[data-testid="stForm"] {
        border-radius: 0.5rem;
        border: 1px solid #3949AB;
        padding: 1rem;
        background-color: #122164;
        color: #E3F2FD;
    }
    div[data-testid="stMetric"] {
        background-color: #122164;
        border-radius: 0.5rem;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        color: #E3F2FD;
    }
    div[data-testid="stMetric"] label {
        color: #FFD700;
    }
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #1A237E;
        color: #FFD700;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-radius: 0;
    }
    /* Theme toggle button */
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 70px;
        z-index: 1000;
        display: flex;
        align-items: center;
        font-size: 14px;
        background-color: #122164;
        color: #E3F2FD;
        border-radius: 20px;
        padding: 5px 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        cursor: pointer;
    }
    .theme-toggle img {
        width: 25px;
        height: 25px;
        margin-right: 5px;
    }
    /* Additional royal theme elements */
    .stDataFrame, .stTable {
        background-color: #122164;
        color: #E3F2FD;
        border-radius: 0.5rem;
    }
    .stSelectbox, .stNumberInput, .stDateInput, .stTextInput, .stTextArea {
        background-color: #122164;
        color: #E3F2FD;
        border-radius: 0.5rem;
    }
    </style>
    """
    
    # Return the appropriate theme based on session state
    if st.session_state.dark_mode:
        return dark_theme
    elif st.session_state.theme == "royal":
        return royal_theme
    else:
        return light_theme

def theme_toggle():
    # Create base64 encoded images for light/dark mode icons
    light_icon = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNGRkMxMDciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1zdW4iPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjQiLz48cGF0aCBkPSJNMTIgMnY0Ii8+PHBhdGggZD0iTTEyIDE4djQiLz48cGF0aCBkPSJNNC45MyA0LjkzIDcuNzYgNy43NiIvPjxwYXRoIGQ9Ik0xNi4yNCAxNi4yNCAxOS4wNyAxOS4wNyIvPjxwYXRoIGQ9Ik0yIDEyaDQiLz48cGF0aCBkPSJNMTggMTJoNCIvPjxwYXRoIGQ9Ik00LjkzIDE5LjA3IDcuNzYgMTYuMjQiLz48cGF0aCBkPSJNMTYuMjQgNy43NiAxOS4wNyA0LjkzIi8+PC9zdmc+"
    dark_icon = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjY2ZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1tb29uIj48cGF0aCBkPSJNMTIgM2MuMTMyIDIuMjItMS41MzggNC4xNTUtMy43NDggNC4xNTVhNi4yMSA2LjIxIDAgMCAxLTIuMzMtLjQ1M2MuMTM5IDMuNTYyIDMuMDQ5IDYuNDI4IDYuNjM0IDYuNDI0IDMuNjggMCA2LjY2Ny0yLjk3MyA2LjY2Ny0yLjY0QzE1LjIyNyAzLjE1MyAxNi4xNjggMCAxMi4xMDIgMGMtLjE2OCAwLS4zMzYuMDA1LS41MDIuMDE1QzEyLjAwMSAuMDEgMTIgMy4wMyAxMiA2LjAzIDEyIDYuMDMgMTIgNnYgNi4wMyA2LjA0Yy0uMDAxIDMuMDA0IDIuNDM2IDUuNDIgNS40OTggNS40MiA0LjE0IDAgNy41MDgtMy4zNjggNy41MDgtNy41MDhWMmMwLS4xNjgtLjAwNS0uMzM2LS4wMTUtLjUwMkwyMS45ODUgNi4wMTZD"
    royal_icon = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmQ3MDAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS10cm9uZSI+PHBhdGggZD0iTTEyIDUuMjUiLz48cGF0aCBkPSJNMTIgMTguNXY2LjUiLz48cGF0aCBkPSJNLjkyOCA1LjY4OCA1LjI4MSA2LjMwOSIvPjxwYXRoIGQ9IjE4LjcwNyAxOC4zMDIgMTguNTA3IDE3LjY4MSIvPjxwYXRoIGQ9IjQuOTI4IDE4LjMwMiA1LjI4MSAxNy42ODMiLz48cGF0aCBkPSIxOC43MDcgNS42ODggMTguNTA3IDYuMzA5Ii8+PHBhdGggZD0iNSAxMmguNSIvPjxwYXRoIGQ9IjE4LjUgMTJoLjUiLz48cGF0aCBkPSIxMi42ODggNi4zMDkgMTMuMzA5IDUuNjg4Ii8+PHBhdGggZD0iMTAuNjkxIDE3LjY0MyAxMC4zMzggMTguMzA2Ii8+PHBhdGggZD0iMTIuNjg4IDE3LjY0MyAxMy4zMDkgMTguMzA2Ii8+PHBhdGggZD0iMTAuNjkxIDYuMzA5IDEwLjMzOCA1LjY4OCIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjMiLz48L3N2Zz4="

    # Choose icon based on current theme
    if st.session_state.dark_mode:
        icon = dark_icon
        label = "Switch to Light Mode"
    elif st.session_state.theme == "royal":
        icon = royal_icon
        label = "Switch to Light Mode"
    else:
        icon = light_icon
        label = "Switch to Dark Mode"

    # Create the toggle button HTML
    toggle_html = f"""
    <div class="theme-toggle" onclick="toggleTheme()">
        <img src="{icon}" alt="Theme Icon" />
        <span>{label}</span>
    </div>
    <script>
        // ... (Your existing JavaScript code) ... 
    </script>
    """
    return toggle_html
  

def currency_switcher():
    currencies = {
        "🇮🇳 INR": "https://flagcdn.com/w40/in.png",
        "🇺🇸 USD": "https://flagcdn.com/w40/us.png",
        "🇦🇪 AED": "https://flagcdn.com/w40/ae.png",
        "🇸🇦 SAR": "https://flagcdn.com/w40/sa.png",
        "🇨🇦 CAD": "https://flagcdn.com/w40/ca.png",
        "🇶🇦 QAR": "https://flagcdn.com/w40/qa.png",
        "🇨🇳 CNY": "https://flagcdn.com/w40/cn.png"
    }

    selected_currency = st.selectbox(
        "Select Currency", list(currencies.keys())
    )
    st.session_state.currency = selected_currency.split()[1]  # Store currency code

    # Display the selected flag
    st.image(currencies[selected_currency], width=40)

    return selected_currency  # Return the selected value to display


# Handle theme switching via URL parameter
def handle_theme_from_url():
    # Get query parameters using st.query_params
    query_params = st.query_params

    # Check if theme parameter exists
    if 'theme' in query_params:
        theme_param = query_params['theme'][0]
        if theme_param == 'dark' and not st.session_state.dark_mode:
            st.session_state.dark_mode = True
        elif theme_param == 'light' and st.session_state.dark_mode:
            st.session_state.dark_mode = False

    # Apply CSS based on current theme
    theme_css = load_css()
    toggle_html = theme_toggle()  # Get the toggle button HTML
    
    # Inject the CSS and theme toggle button
    st.markdown(theme_css, unsafe_allow_html=True)
    st.markdown(toggle_html, unsafe_allow_html=True)

# ============ COLOR SCHEME ============
if st.session_state.dark_mode:
    COLORS = {
        'primary': '#00704A',     # Starbucks Green
        'secondary': '#27251F',   # Dark Gray
        'accent': '#C6A969',      # Gold
        'background': '#1E1E1E',  # Dark Background
        'text_dark': '#E0E0E0',   # Light Text for Dark Mode
        'text_light': '#FFFFFF',  # White Text
        'success': '#006241',     # Dark Green
        'warning': '#CBA258',     # Light Gold
        'error': '#DC3545',       # Red
    }
else:
    COLORS = {
        'primary': '#00704A',     # Starbucks Green
        'secondary': '#27251F',   # Dark Gray
        'accent': '#C6A969',      # Gold
        'background': '#F7F7F7',  # Light Background
        'text_dark': '#1E3932',   # Dark Green Text
        'text_light': '#FFFFFF',  # White Text
        'success': '#006241',     # Dark Green
        'warning': '#CBA258',     # Light Gold
        'error': '#DC3545',       # Red
    }

# ============ CUSTOM CSS ============
st.markdown(f"""
    <style>
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
    }}
    
    .footer {{
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #00704A;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }}
    
    .stApp {{
        background-color: {COLORS['background']};
    }}
    
    h1, h2, h3 {{
        color: {COLORS['primary']};
    }}

    .header-container {{
        position: fixed; /* Stay in place */
        top: 10px;
        right: 10px;
        display: flex;   /* Enable flexbox for alignment */
        align-items: center; /* Align items vertically */
        z-index: 9999; /* Ensure it stays on top */
    }}
    </style>
""", unsafe_allow_html=True)


# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    
    # Users table (simplified)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  username TEXT UNIQUE,
                  email TEXT UNIQUE,
                  password TEXT)''')
    
    # Expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  date TEXT,
                  amount REAL,
                  category TEXT,
                  description TEXT)''')
    
    # Investment goals table
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  name TEXT,
                  target_amount REAL,
                  current_amount REAL,
                  target_date TEXT,
                  priority TEXT)''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# ============ AUTHENTICATION ============
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT id FROM users WHERE email=? AND password=?", 
              (email, hashed_password))
    result = c.fetchone()
    conn.close()
    if result:
        st.session_state.user_id = result[0]
        st.session_state.authenticated = True
        return True
    return False

def register_user(username, email, password):
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    try:
        hashed_password = hash_password(password)
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                 (username, email, hashed_password))
        conn.commit()
        return True, "Registration successful! Please login."
    except sqlite3.IntegrityError:
        return False, "Email or username already exists!"
    finally:
        conn.close()

def auth_page():
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='color: #00704A; margin-bottom: 2rem;'>AI Financial Planner</h1>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if login_user(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long!")
                else:
                    success, message = register_user(new_username, new_email, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# ============ NAVIGATION ============
def create_navigation():
    return option_menu(
        menu_title=None,
        options=["Dashboard", "Expenses", "Investments", "Analysis", "Settings"],
        icons=["house", "wallet", "graph-up", "clipboard-data", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
    "container": {"padding": "10px!important", "background-color": COLORS['primary']},
    "icon": {"color": COLORS['text_light'], "font-size": "20px"},
    "nav-link": {
        "font-size": "16px",
        "text-align": "center",
        "margin": "5px",
        "padding": "10px 20px",
        "--hover-color": COLORS['accent'],
        "color": COLORS['text_light']
    },
    "nav-link-selected": {"background-color": COLORS['accent']},
}

    )

# ============ DASHBOARD ============
def dashboard():
    st.markdown("<h1 style='text-align: center;'>Financial Dashboard</h1>", unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Monthly Savings",
            value="₹25,000",
            delta="↑ 8%"
        )
    
    with col2:
        st.metric(
            label="Investments",
            value="₹1,50,000",
            delta="↑ 12%"
        )
    
    with col3:
        st.metric(
            label="Expenses",
            value="₹45,000",
            delta="5%"
        )
    
    with col4:
        st.metric(
            label="Net Worth",
            value="₹5,00,000",
            delta="↑ 15%"
        )
    
    # Market Overview
    st.markdown("### Market Overview")
    
    # Define symbols for Indian and US markets
    indian_symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'WIPRO.NS']
    us_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    # Combine symbols for display
    all_symbols = indian_symbols + us_symbols
    market_data = pd.DataFrame()
    
    for symbol in all_symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1d')
            if not hist.empty:
                market_data.loc[symbol, 'Price'] = hist['Close'].iloc[-1]
                market_data.loc[symbol, 'Change'] = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                market_data.loc[symbol, 'Change %'] = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                market_data.loc[symbol, 'Market'] = 'Indian' if symbol in indian_symbols else 'US'
        except Exception as e:
            st.warning(f"Could not fetch data for {symbol}: {str(e)}")
            continue
    
    if not market_data.empty:
        st.markdown("#### Real-Time Market Data")
        st.dataframe(market_data.style.format({
            'Price': '{:,.2f}',
            'Change': '{:,.2f}',
            'Change %': '{:,.2f}%'
        }))
        
        # Market Trends Chart for Indian Market
        st.markdown("#### Indian Market Trends (Last Month)")
        fig_indian = go.Figure()
        for symbol in indian_symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period='1mo')
                if not hist.empty:
                    fig_indian.add_trace(go.Scatter(x=hist.index, y=hist['Close'],
                                                    name=symbol, mode='lines'))
            except Exception as e:
                st.warning(f"Could not fetch historical data for {symbol}: {str(e)}")
                continue
        
        fig_indian.update_layout(
            title='Indian Stock Performance',
            xaxis_title='Date',
            yaxis_title='Price (₹)',
            height=400
        )
        st.plotly_chart(fig_indian, use_container_width=True)
        
        # Market Trends Chart for US Market
        st.markdown("#### US Market Trends (Last Month)")
        fig_us = go.Figure()
        for symbol in us_symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period='1mo')
                if not hist.empty:
                    fig_us.add_trace(go.Scatter(x=hist.index, y=hist['Close'],
                                                name=symbol, mode='lines'))
            except Exception as e:
                st.warning(f"Could not fetch historical data for {symbol}: {str(e)}")
                continue
        
        fig_us.update_layout(
            title='US Stock Performance',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            height=400
        )
        st.plotly_chart(fig_us, use_container_width=True)
    else:
        st.error("Unable to fetch market data for any symbols. Please check your internet connection or try again later.")

# ============ EXPENSE TRACKER ============
def expense_tracker():
    st.markdown("<h1 style='text-align: center;'>Smart Expense Tracker</h1>", unsafe_allow_html=True)

    # --- Add New Expense ---
    with st.expander("Add New Expense", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            expense_date = st.date_input("Date", datetime.now())
            expense_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)

        with col2:
            default_categories = ["Needs", "Wants", "Investments", "Savings", "Entertainment", "Health", "Other"]
            expense_category = st.selectbox("Category", default_categories)
            if expense_category == "Other":
                expense_category = st.text_input("Specify Category")

        with col3:
            expense_description = st.text_area("Description", height=100)

        if st.button("Add Expense"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO expenses (user_id, date, amount, category, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        st.session_state.user_id,
                        expense_date.strftime("%Y-%m-%d"),
                        expense_amount,
                        expense_category,
                        expense_description,
                    ),
                )
                conn.commit()
                conn.close()
                st.success("Expense added successfully!")
            else:
                st.error("User not authenticated. Please log in.")

    # --- Expense Analysis ---
    if st.session_state.user_id:
        conn = sqlite3.connect('finance_tracker.db')
        df_expenses = pd.read_sql_query(
            """
            SELECT date, amount, category, description
            FROM expenses
            WHERE user_id = ?
            """,
            conn,
            params=(st.session_state.user_id,),
        )
        conn.close()

        if not df_expenses.empty:
            df_expenses["date"] = pd.to_datetime(df_expenses["date"])

            # --- Day-End Table (Latest Day) ---
            st.markdown("### Latest Day Expenses")
            latest_date = df_expenses["date"].max().strftime("%Y-%m-%d")
            st.markdown(f"**Date: {latest_date}**")
            
            latest_day_expenses = df_expenses[df_expenses["date"] == latest_date]
            
            day_table = pd.DataFrame(columns=["Category", "Description", "Needs (₹)", "Wants (₹)", "Investments (₹)", "Savings (₹)", "Total (₹)"])
            for _, row in latest_day_expenses.iterrows():
                new_row = {
                    "Category": row["category"],
                    "Description": row["description"],
                    "Needs (₹)": row["amount"] if row["category"] == "Needs" else 0,
                    "Wants (₹)": row["amount"] if row["category"] == "Wants" else 0,
                    "Investments (₹)": row["amount"] if row["category"] == "Investments" else 0,
                    "Savings (₹)": row["amount"] if row["category"] == "Savings" else 0,
                    "Total (₹)": row["amount"]
                }
                day_table = pd.concat([day_table, pd.DataFrame([new_row])], ignore_index=True)
            
            st.dataframe(day_table.style.format({
                "Needs (₹)": "{:,.2f}",
                "Wants (₹)": "{:,.2f}",
                "Investments (₹)": "{:,.2f}",
                "Savings (₹)": "{:,.2f}",
                "Total (₹)": "{:,.2f}"
            }))
            
            # Download button for day-end table
            csv_day = day_table.to_csv(index=False)
            st.download_button(
                label="Download Latest Day Expenses as CSV",
                data=csv_day,
                file_name=f"expenses_{latest_date}.csv",
                mime="text/csv"
            )

            # --- Month-End Table (Current Month) ---
            st.markdown("### Current Month Expenses")
            current_month = datetime.now().strftime("%Y-%m")
            st.markdown(f"**Month: {current_month}**")
            
            df_expenses["month"] = df_expenses["date"].dt.strftime("%Y-%m")
            current_month_expenses = df_expenses[df_expenses["month"] == current_month]
            
            month_table = pd.DataFrame(columns=["Month", "Needs (₹)", "Wants (₹)", "Investments (₹)", "Savings (₹)", "Total (₹)"])
            if not current_month_expenses.empty:
                month_row = {
                    "Month": current_month,
                    "Needs (₹)": current_month_expenses[current_month_expenses["category"] == "Needs"]["amount"].sum(),
                    "Wants (₹)": current_month_expenses[current_month_expenses["category"] == "Wants"]["amount"].sum(),
                    "Investments (₹)": current_month_expenses[current_month_expenses["category"] == "Investments"]["amount"].sum(),
                    "Savings (₹)": current_month_expenses[current_month_expenses["category"] == "Savings"]["amount"].sum(),
                    "Total (₹)": current_month_expenses["amount"].sum()
                }
                month_table = pd.concat([month_table, pd.DataFrame([month_row])], ignore_index=True)
            
            st.dataframe(month_table.style.format({
                "Needs (₹)": "{:,.2f}",
                "Wants (₹)": "{:,.2f}",
                "Investments (₹)": "{:,.2f}",
                "Savings (₹)": "{:,.2f}",
                "Total (₹)": "{:,.2f}"
            }))
            
            # Download button for month-end table
            csv_month = month_table.to_csv(index=False)
            st.download_button(
                label="Download Current Month Expenses as CSV",
                data=csv_month,
                file_name=f"expenses_{current_month}.csv",
                mime="text/csv"
            )

            # --- Summary Statistics ---
            st.markdown("### Expense Summary")
            col1, col2, col3 = st.columns(3)

            with col1:
                total_expenses = df_expenses["amount"].sum()
                st.metric(
                    "Total Expenses",
                    f"{st.session_state.currency} {total_expenses:,.2f}"
                )

            with col2:
                avg_daily = df_expenses.groupby("date")["amount"].sum().mean()
                st.metric("Average Daily Expense", f"{avg_daily:,.2f}")

            with col3:
                most_common_category = df_expenses["category"].mode()[0]
                st.metric("Most Common Category", most_common_category)

            # --- Visualizations ---
            st.markdown("### Expense Analysis")

            # Category-wise Pie Chart
            fig = px.pie(
                df_expenses,
                values="amount",
                names="category",
                title="Expense Distribution by Category"
            )
            st.plotly_chart(fig)

            # Daily Expense Trend
            daily_expenses = (
                df_expenses.groupby("date")["amount"].sum().reset_index()
            )

            fig = px.line(
                daily_expenses,
                x="date",
                y="amount",
                title="Daily Expense Trend",
                labels={"amount": "Amount (₹)", "date": "Date"},
            )
            st.plotly_chart(fig)
        else:
            st.info("No expenses have been added yet.")
    else:
        st.error("User not authenticated. Please log in.")


# ============ INVESTMENT PLANNER ============
def investment_planner():
    st.markdown("<h1 style='text-align: center;'>Investment Planner</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Investment Calculator", "Portfolio Allocation", "Goal Tracker"])

    with tab1:
        st.markdown("### Investment Calculator")
        calc_type = st.radio("Select Calculator Type", ["SIP", "Lump Sum"])

        # --- Input Fields ---
        if calc_type == "SIP":
            initial_investment = 0
            monthly_investment = st.number_input("Monthly Investment (₹)", min_value=100, value=5000)
            period_unit = st.selectbox("Investment Period Unit", ["Years", "Months"])
            if period_unit == "Years":
                years = st.number_input("Investment Period (Years)", min_value=1, max_value=40, value=10)
                months = years * 12  # Calculate months from years
            else:  # Months
                months = st.number_input("Investment Period (Months)", min_value=1, value=120)
                years = months / 12  # Calculate years from months
            expected_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=30.0, value=12.0)
        else:  # Lump Sum
            initial_investment = st.number_input("Lump Sum Investment (₹)", min_value=1000, value=50000)
            monthly_investment = 0  # For Lump Sum, no monthly investment
            period_unit = st.selectbox("Investment Period Unit", ["Years", "Months"])
            if period_unit == "Years":
                years = st.number_input("Investment Period (Years)", min_value=1, max_value=40, value=10)
                months = years * 12
            else:
                months = st.number_input("Investment Period (Months)", min_value=1, value=120)
                years = months / 12
            expected_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=30.0, value=12.0)

        # --- Common Input Fields ---
        inflation_rate = st.slider("Assumed Inflation Rate (%)", 2.9, 8.9, 4.5)
        holding_period = st.selectbox("Holding Period", ["Less than 12 months", "More than 12 months"])

        # --- Calculations (Matching Groww Calculator Logic) ---
        monthly_rate = expected_return / (12 * 100)

        if calc_type == "SIP":
            # SIP Future Value: FV = P * (((1 + r)^n - 1) / r) * (1 + r)
            future_value = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
            total_investment = monthly_investment * months
        else:  # Lump Sum
            # Lump Sum Future Value: FV = P * (1 + r)^n
            future_value = initial_investment * (1 + expected_return / 100) ** years
            total_investment = initial_investment

        total_returns = future_value - total_investment

        # --- Inflation Adjustment ---
        inflation_adjusted_value = future_value / (1 + inflation_rate / 100) ** years

        # --- Tax Calculation ---
        if holding_period == "Less than 12 months":
            tax_rate = 0.20  # STCG - 20%
            taxable_amount = total_returns
            tax_amount = taxable_amount * tax_rate
        else:
            tax_rate = 0.125  # LTCG - 12.5%
            annual_exemption = 125000 * years
            taxable_amount = max(0, total_returns - annual_exemption)
            tax_amount = taxable_amount * tax_rate

        after_tax_returns = total_returns - tax_amount

        # --- Display Results ---
        st.markdown("### Investment Projections")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Investment", f"₹{total_investment:,.2f}")
        col2.metric("Total Returns", f"₹{total_returns:,.2f}", help="Gross return before inflation & taxes")
        col3.metric(
            "Inflation-Adjusted Value",
            f"₹{inflation_adjusted_value:,.2f}",
            delta=f"-₹{(future_value - inflation_adjusted_value):,.2f}",
            delta_color="inverse",
            help=f"Future value adjusted for {inflation_rate:.2f}% annual inflation"
        )
        col4.metric(
            "After-Tax Returns",
            f"₹{after_tax_returns:,.2f}",
            delta=f"-₹{tax_amount:,.2f}",
            delta_color="inverse",
            help=f"Returns after deducting {tax_rate * 100:.2f}% tax on taxable gains"
        )

        # --- Growth Visualization ---
        st.markdown("### Investment Growth Projection")
        if period_unit == "Years":
            period_range = np.arange(0, years + 1)
            x_axis_label = 'Years'
        else:  # Months
            period_range = np.arange(0, months + 1)
            x_axis_label = 'Months'

        growth_values = []
        if calc_type == "SIP":
            for period in range(int(months) + 1):
                value = monthly_investment * (((1 + monthly_rate) ** period - 1) / monthly_rate) * (1 + monthly_rate) if period > 0 else 0
                growth_values.append(value)
        else:  # Lump Sum
            for period in period_range:
                value = initial_investment * (1 + expected_return / 100) ** period
                growth_values.append(value)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=period_range, y=growth_values, mode='lines', name='Investment Growth'))
        fig.update_layout(
            title=f'{calc_type} Investment Growth',
            xaxis_title=x_axis_label,
            yaxis_title='Amount (₹)',
            height=400
        )
        st.plotly_chart(fig)

    with tab2:
        st.markdown("### Portfolio Allocation")
        age = st.number_input("Your Age", min_value=18, max_value=100, value=30)
        risk_profile = st.selectbox("Risk Profile",
                                     ["Conservative", "Moderate", "Aggressive"])

        # Calculate allocations based on age and risk profile
        equity_percent = max(20, min(80, 100 - age))

        if risk_profile == "Conservative":
            equity_percent = max(20, equity_percent - 10)
        elif risk_profile == "Aggressive":
            equity_percent = min(80, equity_percent + 10)

        debt_percent = 100 - equity_percent

        # Equity breakdown
        large_cap = equity_percent * 0.60
        mid_cap = equity_percent * 0.25
        small_cap = equity_percent * 0.15

        col1, col2 = st.columns(2)

        with col1:
            # Broad Asset Allocation
            fig = go.Figure(data=[go.Pie(
                labels=['Equity', 'Debt'],
                values=[equity_percent, debt_percent],
                hole=.3
            )])
            fig.update_layout(title="Broad Asset Allocation")
            st.plotly_chart(fig)

        with col2:
            # Equity Breakdown
            fig = go.Figure(data=[go.Pie(
                labels=['Large Cap', 'Mid Cap', 'Small Cap'],
                values=[large_cap, mid_cap, small_cap],
                hole=.3
            )])
            fig.update_layout(title="Equity Breakdown")
            st.plotly_chart(fig)

        st.markdown(f"""
        ### Recommended Allocation

        **Broad Asset Allocation:**
        - Equity: {equity_percent:.1f}%
        - Debt: {debt_percent:.1f}%

        **Equity Breakdown:**
        - Large Cap: {large_cap:.1f}%
        - Mid Cap: {mid_cap:.1f}%
        - Small Cap: {small_cap:.1f}%
        """)

    with tab3:
        st.markdown("### Goal Tracker")

        # Add New Goal
        with st.expander("Add New Goal", expanded=True):
            with st.form("new_goal"):
                goal_name = st.text_input("Goal Name")
                goal_amount = st.number_input("Target Amount (₹)", min_value=0)
                goal_date = st.date_input("Target Date")
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                current_amount = st.number_input("Current Amount (₹)", min_value=0)

                submitted = st.form_submit_button("Add Goal")
                if submitted:
                    conn = sqlite3.connect('finance_tracker.db')
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO goals (user_id, name, target_amount, current_amount,
                                           target_date, priority)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (st.session_state.user_id, goal_name, goal_amount,
                          current_amount, goal_date.strftime("%Y-%m-%d"), priority))
                    conn.commit()
                    conn.close()
                    st.success("Goal added successfully!")

        # Display Goals
        conn = sqlite3.connect('finance_tracker.db')
        df_goals = pd.read_sql_query("""
            SELECT name, target_amount, current_amount, target_date, priority
            FROM goals
            WHERE user_id = ?
        """, conn, params=(st.session_state.user_id,))
        conn.close()

        if not df_goals.empty:
            st.markdown("### Your Financial Goals")

            for _, goal in df_goals.iterrows():
                progress = (goal['current_amount'] / goal['target_amount']) * 100

                st.markdown(f"""
                <div style='padding: 1rem; background-color: white; border-radius: 0.5rem;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 1rem 0;'>
                    <h4>{goal['name']} ({goal['priority']} Priority)</h4>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                with col1:
                    st.progress(progress / 100)
                    st.markdown(f"Progress: {progress:.1f}%")

                with col2:
                    st.markdown(f"""
                    Target: ₹{goal['target_amount']:,.2f}
                    Current: ₹{goal['current_amount']:,.2f}
                    Target Date: {goal['target_date']}
                    """)

                # Calculate monthly savings needed
                target_date = datetime.strptime(goal['target_date'], "%Y-%m-%d")
                months_remaining = (target_date - datetime.now()).days / 30
                if months_remaining > 0:
                    monthly_needed = (goal['target_amount'] - goal['current_amount']) / months_remaining
                    st.info(f"You need to save ₹{monthly_needed:,.2f} monthly to reach your goal")


# ============ ADVANCED ANALYTICS ============
def advanced_analytics():
    st.markdown("<h1 style='text-align: center;'>Advanced Analytics</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Expense Analysis", "Investment Analysis", "Financial Health"])
    
    with tab1:
        st.markdown("### Expense Pattern Analysis")
        
        # Get expense data
        conn = sqlite3.connect('finance_tracker.db')
        df_expenses = pd.read_sql_query("""
            SELECT date, amount, category 
            FROM expenses 
            WHERE user_id = ?
        """, conn, params=(st.session_state.user_id,))
        conn.close()
        
        if not df_expenses.empty:
            df_expenses['date'] = pd.to_datetime(df_expenses['date'])
            
            # Monthly Trend
            monthly_expenses = df_expenses.groupby(df_expenses['date'].dt.strftime('%Y-%m'))[['amount']].sum()
            
            fig = px.line(monthly_expenses, x=monthly_expenses.index, y='amount',
                         title='Monthly Expense Trend',
                         labels={'amount': 'Amount (₹)', 'date': 'Month'})
            st.plotly_chart(fig)
            
            # Category Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Category Distribution
                category_expenses = df_expenses.groupby('category')['amount'].sum()
                fig = px.pie(values=category_expenses.values,
                           names=category_expenses.index,
                           title='Expense Distribution by Category')
                st.plotly_chart(fig)
            
            with col2:
                # Weekly Pattern
                df_expenses['weekday'] = df_expenses['date'].dt.day_name()
                weekly_expenses = df_expenses.groupby('weekday')['amount'].mean()
                
                fig = px.bar(x=weekly_expenses.index,
                           y=weekly_expenses.values,
                           title='Average Daily Spending by Weekday',
                           labels={'x': 'Day', 'y': 'Average Amount (₹)'})
                st.plotly_chart(fig)
            
            # Calculate metrics
            total_monthly = df_expenses.groupby(df_expenses['date'].dt.strftime('%Y-%m'))['amount'].sum()
            avg_monthly = total_monthly.mean()
            std_monthly = total_monthly.std()
            
            # Generate insights
            insights = []
            
            if total_monthly.iloc[-1] > avg_monthly + std_monthly:
                insights.append("📈 Your spending this month is higher than usual.")
            elif total_monthly.iloc[-1] < avg_monthly - std_monthly:
                insights.append("📉 Your spending this month is lower than usual.")
            
            # Category-specific insights
            for category in df_expenses['category'].unique():
                cat_data = df_expenses[df_expenses['category'] == category]
                cat_monthly = cat_data.groupby(cat_data['date'].dt.strftime('%Y-%m'))['amount'].sum()
                
                if len(cat_monthly) > 1 and cat_monthly.iloc[-1] > cat_monthly.iloc[:-1].mean() * 1.2:
                    insights.append(f"⚠️ {category} expenses have increased significantly.")
            
            for insight in insights:
                st.info(insight)
    
    with tab2:
        st.markdown("### Investment Performance Analysis")
        
        # Sample investment data (replace with actual data)
        investment_data = pd.DataFrame({
            'Date': pd.date_range(start='2023-01-01', periods=12, freq='ME'),
            'Equity': np.random.normal(12000, 2000, 12).cumsum(),
            'Debt': np.random.normal(8000, 1000, 12).cumsum(),
            'Gold': np.random.normal(5000, 500, 12).cumsum()
        })
        
                # Portfolio Performance
        fig = px.line(investment_data, x='Date',
                     y=['Equity', 'Debt', 'Gold'],
                     title='Portfolio Performance Over Time')
        st.plotly_chart(fig)
        
        # Asset Allocation
        current_allocation = {
            'Asset': ['Equity', 'Debt', 'Gold'],
            'Amount': [investment_data['Equity'].iloc[-1],
                      investment_data['Debt'].iloc[-1],
                      investment_data['Gold'].iloc[-1]]
        }
        df_allocation = pd.DataFrame(current_allocation)
        
        fig = px.pie(df_allocation, values='Amount', names='Asset',
                    title='Current Asset Allocation')
        st.plotly_chart(fig)
        
        # Performance Metrics
        st.markdown("### Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_value = df_allocation['Amount'].sum()
            st.metric("Total Portfolio Value", f"₹{total_value:,.2f}")
            
        with col2:
            # Safety check to ensure we're only working with numeric data
            if 'Date' in investment_data.columns:
                investment_data_numeric = investment_data.drop(columns=['Date'])
            else:
                investment_data_numeric = investment_data
                
            # Get the first row as a Series and filter out non-numeric values
            first_row = investment_data_numeric.iloc[0]
            # Instead of select_dtypes, manually filter numeric values
            numeric_values = [value for value in first_row if isinstance(value, (int, float))]
            investment_sum = sum(numeric_values) if numeric_values else 0
            
            # Calculate returns
            returns = (total_value - investment_sum) / investment_sum * 100 if investment_sum > 0 else 0
            st.metric("Total Returns", f"{returns:.1f}%")
        
        with col3:
            monthly_return = returns / 12
            st.metric("Average Monthly Return", f"{monthly_return:.1f}%")

    with tab3:
        st.markdown("### Financial Health Score")
        
        # Get user inputs
        col1, col2 = st.columns(2)
        
        with col1:
            monthly_income = st.number_input("Monthly Income (₹)", min_value=0, value=50000)
            monthly_expenses = st.number_input("Monthly Expenses (₹)", min_value=0, value=30000)
            emergency_fund = st.number_input("Emergency Fund (₹)", min_value=0, value=100000)
        
        with col2:
            total_investments = st.number_input("Total Investments (₹)", min_value=0, value=200000)
            total_debt = st.number_input("Total Debt (₹)", min_value=0, value=0)

        
        # Calculate ratios
        savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100 if monthly_income > 0 else 0
        emergency_fund_months = emergency_fund / monthly_expenses if monthly_expenses > 0 else 0
        debt_to_income = (total_debt / (monthly_income * 12)) * 100 if monthly_income > 0 else 0
        investment_ratio = (total_investments / (monthly_income * 12)) * 100 if monthly_income > 0 else 0
        
        # Calculate health score
        score = 0
        score += min(25, savings_rate / 2)  # Max 25 points for savings
        score += min(25, emergency_fund_months * 12.5)  # Max 25 points for emergency fund
        score += min(25, 25 * (1 - debt_to_income/100))  # Max 25 points for low debt
        score += min(25, investment_ratio / 4)  # Max 25 points for investments
        
        # Display score gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Financial Health Score"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': COLORS['primary']},
                'steps': [
                    {'range': [0, 33], 'color': "lightgray"},
                    {'range': [33, 66], 'color': "gray"},
                    {'range': [66, 100], 'color': COLORS['accent']}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        st.plotly_chart(fig)
        
        # Analysis and Recommendations
        st.markdown("### Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Strengths")
            if savings_rate >= 20:
                st.success(f"Strong savings rate: {savings_rate:.1f}%")
            if emergency_fund_months >= 6:
                st.success(f"Adequate emergency fund: {emergency_fund_months:.1f} months")
            if debt_to_income < 30:
                st.success(f"Healthy debt levels: {debt_to_income:.1f}%")
            if investment_ratio >= 50:
                st.success(f"Good investment ratio: {investment_ratio:.1f}%")
        
        with col2:
            st.markdown("#### Areas for Improvement")
            if savings_rate < 20:
                st.warning(f"Work on increasing savings rate: {savings_rate:.1f}%")
            if emergency_fund_months < 6:
                st.warning(f"Build emergency fund: Currently {emergency_fund_months:.1f} months")
            if debt_to_income >= 30:
                st.warning(f"High debt-to-income ratio: {debt_to_income:.1f}%")
            if investment_ratio < 50:
                st.warning(f"Increase investments: Currently {investment_ratio:.1f}%")
        
        # Recommendations
        st.markdown("### Personalized Recommendations")
        recommendations = []
        
        if savings_rate < 20:
            recommendations.append("• Create a budget to increase your savings rate to at least 20%")
        if emergency_fund_months < 6:
            recommendations.append(f"• Build emergency fund by saving ₹{(6*monthly_expenses - emergency_fund):,.2f} more")
        if debt_to_income >= 30:
            recommendations.append("• Focus on debt reduction before increasing investments")
        if investment_ratio < 50:
            recommendations.append("• Consider increasing your investment allocation")
        
        for rec in recommendations:
            st.markdown(rec)

# ============ SETTINGS PAGE ============
def settings_page():
    st.markdown("<h1 style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)
    
    # Profile Settings
    st.markdown("### Profile Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get user info
        conn = sqlite3.connect('finance_tracker.db')
        c = conn.cursor()
        c.execute("SELECT username, email FROM users WHERE id = ?", 
                 (st.session_state.user_id,))
        user_info = c.fetchone()
        conn.close()
        
        if user_info:
            username, email = user_info
            st.text_input("Username", value=username, disabled=True)
            st.text_input("Email", value=email, disabled=True)
    
    with col2:
        # Theme Settings
        st.markdown("### Theme Settings")
        dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
    
    # Notification Settings
    st.markdown("### Notification Settings")
    st.checkbox("Email Alerts for Unusual Expenses", value=True)
    st.checkbox("Monthly Report", value=True)
    st.checkbox("Investment Alerts", value=True)
    
    # Data Management
    st.markdown("### Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Data"):
            # Get user's data
            conn = sqlite3.connect('finance_tracker.db')
            df_expenses = pd.read_sql_query("""
                SELECT date, amount, category, description 
                FROM expenses 
                WHERE user_id = ?
            """, conn, params=(st.session_state.user_id,))
            
            # Convert to CSV
            csv = df_expenses.to_csv(index=False)
            
            # Create download button
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="my_financial_data.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Delete Account"):
            st.warning("⚠️ This will permanently delete your account and all associated data!")
            if st.button("Confirm Delete"):
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                # Delete user's data
                c.execute("DELETE FROM expenses WHERE user_id = ?", 
                         (st.session_state.user_id,))
                c.execute("DELETE FROM goals WHERE user_id = ?", 
                         (st.session_state.user_id,))
                c.execute("DELETE FROM users WHERE id = ?", 
                         (st.session_state.user_id,))
                conn.commit()
                conn.close()
                
                # Clear session state
                st.session_state.clear()
                st.success("Account deleted successfully!")
                st.rerun()

# ============ MAIN APP ============
def main():
    # Apply theme
    handle_theme_from_url()
       
    # Add theme switcher to the header
    theme_switcher_html = theme_toggle()
    st.markdown(
        f"""
        <div class="header-container"> 
            <div style="position: relative; z-index: 9999;">{theme_switcher_html}</div> 
            {currency_switcher()} 
        </div>
        """,
        unsafe_allow_html=True,
    )

    
    if not st.session_state.authenticated:
        auth_page()
    else:
        selected = create_navigation()
        
        if selected == "Dashboard":
            dashboard()
        elif selected == "Expenses":
            expense_tracker()
        elif selected == "Investments":
            investment_planner()
        elif selected == "Analysis":
            advanced_analytics()
        elif selected == "Settings":
            settings_page()
            
        # Add footer here
        st.markdown("""
            <div class='footer'>
                Developed by Muhammed Adnan | Contact: kladnan321@gmail.com
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()