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
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
import io
import os
import requests

# Currency symbols
currency_symbols = {
    "INR": "₹", "USD": "$", "AED": "د.إ", "SAR": "ر.س", "CAD": "$", "QAR": "ر.ق", "CNY": "¥"
}

# Fetch exchange rates
if 'exchange_rates' not in st.session_state:
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/INR")
        data = response.json()
        st.session_state.exchange_rates = data['rates']
    except:
        st.warning("Failed to fetch exchange rates. Using fallback rates.")
        st.session_state.exchange_rates = {"USD": 0.012, "AED": 0.044, "INR": 1.0}

def convert_amount(amount, from_currency="INR", to_currency=None):
    if to_currency is None:
        to_currency = st.session_state.currency
    if from_currency == to_currency:
        return amount
    if from_currency == "INR" and to_currency in st.session_state.exchange_rates:
        rate = st.session_state.exchange_rates[to_currency]
        return amount * rate
    else:
        st.error(f"Unable to fetch exchange rate from {from_currency} to {to_currency}")
        return amount

# Page config
st.set_page_config(
    page_title="AI Financial Planner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'theme' not in st.session_state:
    st.session_state.theme = "light"
if 'loans' not in st.session_state:
    st.session_state.loans = []
if 'currency' not in st.session_state:
    st.session_state.currency = "INR"
if 'selected_index' not in st.session_state:
    st.session_state.selected_index = 0
if 'show_search' not in st.session_state:
    st.session_state.show_search = False

# Theme CSS
def load_css():
    light_theme = """
    <style>
    .stApp {
        background-color: #F7F7F7;
        color: #1E3932;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #00704A;
        animation: fadeIn 1s ease-in;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        animation: slideIn 0.5s ease-out;
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
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .stExpander, div[data-testid="stForm"] {
        border-radius: 0.5rem;
        border: 1px solid #e6e6e6;
        transition: transform 0.3s ease;
    }
    .stExpander:hover, div[data-testid="stForm"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 0.5rem;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .theme-toggle {
        position: fixed;
        top: 40px;
        right: 20px;
        z-index: 9999;
        display: flex;
        align-items: center;
        font-size: 16px;
        background-color: #FFFFFF;
        border-radius: 25px;
        padding: 8px 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .theme-toggle:hover {
        transform: scale(1.05);
        box-shadow: 0 0 10px rgba(0, 112, 74, 0.5);
    }
    .theme-toggle img {
        width: 25px;
        height: 25px;
        margin-right: 5px;
    }
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #00704A;
        color: white;
        text-align: center;
        padding: 10px;
        animation: slideUp 0.8s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideUp {
        from { transform: translateY(100%); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    </style>
    """
    dark_theme = """
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #C6A969;
        animation: fadeIn 1s ease-in;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        animation: slideIn 0.5s ease-out;
    }
    .stButton>button {
        background-color: #C6A969;
        color: #1E3932;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .stExpander, div[data-testid="stForm"] {
        border-radius: 0.5rem;
        border: 1px solid #444444;
        transition: transform 0.3s ease;
    }
    .stExpander:hover, div[data-testid="stForm"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetric"] {
        background-color: #2D2D2D;
        border-radius: 0.5rem;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .theme-toggle {
        position: fixed;
        top: 40px;
        right: 20px;
        z-index: 9999;
        display: flex;
        align-items: center;
        font-size: 16px;
        background-color: #2D2D2D;
        border-radius: 25px;
        padding: 8px 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .theme-toggle:hover {
        transform: scale(1.05);
        box-shadow: 0 0 10px rgba(198, 169, 105, 0.5);
    }
    .theme-toggle img {
        width: 25px;
        height: 25px;
        margin-right: 5px;
    }
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #C6A969;
        color: #1E3932;
        text-align: center;
        padding: 10px;
        animation: slideUp 0.8s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideUp {
        from { transform: translateY(100%); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    </style>
    """
    return light_theme if st.session_state.theme == "light" else dark_theme

# Theme toggle
def theme_toggle():
    light_icon = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNGRkMxMDciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI0Ii8+PHBhdGggZD0iTTEyIDJ2NCIvPjxwYXRoIGQ9Ik0xMiAxOHY0Ii8+PHBhdGggZD0iTTQuOTMgNC45MyA3Ljc2IDcuNzYiLz48cGF0aCBkPSJNMTYuMjQgMTYuMjQgMTkuMDcgMTkuMDciLz48cGF0aCBkPSJNMiAxMmg0Ii8+PHBhdGggZD0iTTE4IDEyaDQiLz48cGF0aCBkPSJNNC45MyAxOS4wNyA3Ljc2IDE2LjI0Ii8+PHBhdGggZD0iTTE2LjI0IDcuNzYgMTkuMDcgNC45MyIvPjwvc3ZnPg=="
    dark_icon = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI4IDI4IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjY2ZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMTIgM0E2LjY2NyA2LjY2NyAwIDAgMCAyMSAyMUE2LjY2NyA2LjY2NyAwIDAgMCAxMiAzWm0wIDE4YTkgOSAwIDAgMSAwLTE4IDkgOSAwIDAgMSAwIDE4WiIvPjwvc3ZnPg=="
    themes = ["light", "dark"]
    current_theme_idx = themes.index(st.session_state.theme)
    next_theme_idx = (current_theme_idx + 1) % len(themes)
    next_theme = themes[next_theme_idx]
    icon = light_icon if st.session_state.theme == "light" else dark_icon
    label = st.session_state.theme.capitalize()
    toggle_html = f"""
    <div class="theme-toggle" onclick="toggleTheme('{next_theme}')">
        <img src="{icon}" alt="Theme Icon" />
        <span>{label}</span>
    </div>
    <script>
        function toggleTheme(nextTheme) {{
            window.parent.postMessage({{type: 'themeChange', theme: nextTheme}}, '*');
        }}
    </script>
    """
    return toggle_html

def currency_switcher():
    currencies = {
        "India INR": "https://flagcdn.com/w40/in.png",
        "USA USD": "https://flagcdn.com/w40/us.png",
        "UAE AED": "https://flagcdn.com/w40/ae.png",
        "Saudi SAR": "https://flagcdn.com/w40/sa.png",
        "Canada CAD": "https://flagcdn.com/w40/ca.png",
        "Qatar QAR": "https://flagcdn.com/w40/qa.png",
        "China CNY": "https://flagcdn.com/w40/cn.png"
    }
    selected_currency = st.selectbox("Select Currency", list(currencies.keys()))
    st.session_state.currency = selected_currency.split()[1]
    st.image(currencies[selected_currency], width=40)
    return selected_currency

def handle_theme_from_url():
    query_params = st.query_params
    if 'theme' in query_params:
        theme_param = query_params['theme']
        if theme_param in ['light', 'dark']:
            st.session_state.theme = theme_param
            st.session_state.dark_mode = (theme_param == 'dark')
    st.markdown(load_css(), unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, amount REAL, category TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, loan_type TEXT, principal REAL, interest_rate REAL, 
                  tenure_months INTEGER, start_date TEXT, outstanding_balance REAL, emi_amount REAL, 
                  monthly_payment REAL, description TEXT, amount_paid REAL DEFAULT 0.0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL, 
                  target_date TEXT, priority TEXT)''')
    conn.commit()
    conn.close()

def migrate_db():
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    try:
        c.execute("SELECT emi_amount FROM loans LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE loans ADD COLUMN emi_amount REAL")
        conn.commit()
    conn.close()

# Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, hashed_password))
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

# Authentication page
def auth_page():
    st.markdown("""
    <style>
    .login-container {
        background: #f0f2f6;
        padding: 3rem;
        border-radius: 1rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        animation: fadeInUp 1s ease-out;
    }
    .login-title {
        color: #00704A;
        font-size: 3rem;
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeIn 1s ease-in;
    }
    .stTextInput > div > input {
        background-color: white;
        border: 1px solid #e6e6e6;
        color: #1E3932;
        padding: 0.8rem;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stTextInput > div > input:focus {
        border-color: #00704A;
        box-shadow: 0 0 10px rgba(0, 112, 74, 0.5);
    }
    .stButton>button {
        background: #00704A;
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 0.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0, 112, 74, 0.5);
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(50px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-container">
        <h1 class="login-title">Unlock Your Financial Future</h1>
        <p style="text-align: center; color: #1E3932; margin-bottom: 2rem;">
            AI-Powered Financial Insights
        </p>
    </div>
    """, unsafe_allow_html=True)

    components.html("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
    <div id="coin-container" style="width: 100%; height: 200px;"></div>
    <script>
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 200, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ alpha: true });
        renderer.setSize(window.innerWidth * 0.8, 200);
        document.getElementById('coin-container').appendChild(renderer.domElement);
        const geometry = new THREE.CylinderGeometry(50, 50, 10, 32);
        const material = new THREE.MeshPhongMaterial({ color: 0x00704A });
        const coin = new THREE.Mesh(geometry, material);
        scene.add(coin);
        const light = new THREE.PointLight(0xffffff, 1, 100);
        light.position.set(50, 50, 50);
        scene.add(light);
        camera.position.z = 100;
        function animate() {
            requestAnimationFrame(animate);
            coin.rotation.x += 0.05;
            coin.rotation.y += 0.05;
            renderer.render(scene, camera);
        }
        animate();
    </script>
    """, height=200)

    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login")
            if submit:
                if login_user(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username", placeholder="Pick a unique username")
            new_email = st.text_input("Email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            submit = st.form_submit_button("Register")
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters!")
                else:
                    success, message = register_user(new_username, new_email, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# Navigation
def create_navigation():
    return option_menu(
        menu_title=None,
        options=["Dashboard", "Expenses", "Investments", "Analysis", "Debt Management", "Settings"],
        icons=["house", "wallet", "graph-up", "clipboard-data", "credit-card", "gear"],
        menu_icon="cast",
        default_index=st.session_state.selected_index,
        orientation="horizontal",
        styles={
            "container": {"padding": "10px", "background-color": "#00704A"},
            "icon": {"color": "white", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "color": "white", "padding": "10px 20px"},
            "nav-link-selected": {"background-color": "#C6A969"},
        }
    )

# Dashboard
def dashboard():
    st.markdown("<h1 style='text-align: center;'>Financial Dashboard</h1>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Monthly Savings", f"{currency_symbols[st.session_state.currency]} {convert_amount(25000):,.2f}", "8%")
    with col2:
        st.metric("Investments", f"{currency_symbols[st.session_state.currency]} {convert_amount(150000):,.2f}", "12%")
    with col3:
        st.metric("Expenses", f"{currency_symbols[st.session_state.currency]} {convert_amount(45000):,.2f}", "5%")
    with col4:
        st.metric("Net Worth", f"{currency_symbols[st.session_state.currency]} {convert_amount(500000):,.2f}", "15%")
    
    st.markdown("### Market Overview")
    try:
        symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS']
        market_data = pd.DataFrame()
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1d')
            if not hist.empty:
                market_data.loc[symbol, 'Price'] = hist['Close'].iloc[-1]
                market_data.loc[symbol, 'Change'] = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                market_data.loc[symbol, 'Change %'] = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
        st.dataframe(market_data.style.format({'Price': f"{currency_symbols[st.session_state.currency]} {{:,.2f}}", 'Change': f"{currency_symbols[st.session_state.currency]} {{:,.2f}}", 'Change %': '{:,.2f}%'}))
        
        st.markdown("### Market Trends (Last Month)")
        fig = go.Figure()
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1mo')
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name=symbol, mode='lines'))
        fig.update_layout(title='Stock Performance', xaxis_title='Date', yaxis_title=f"Price ({currency_symbols[st.session_state.currency]})", height=400)
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("Unable to fetch market data.")

# Expense Tracker
def expense_tracker():
    st.markdown("<h1 style='text-align: center;'>Smart Expense Tracker</h1>", unsafe_allow_html=True)
    with st.expander("Add New Expense", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            expense_date = st.date_input("Date", datetime.now())
            expense_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        with col2:
            categories = ["Needs", "Wants", "Investment", "Bills", "Entertainment", "Health", "Other"]
            expense_category = st.selectbox("Category", categories)
            if expense_category == "Other":
                expense_category = st.text_input("Specify Category")
        with col3:
            expense_description = st.text_area("Description", height=100)
        if st.button("Add Expense"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("INSERT INTO expenses (user_id, date, amount, category, description) VALUES (?, ?, ?, ?, ?)",
                         (st.session_state.user_id, expense_date.strftime("%Y-%m-%d"), expense_amount, expense_category, expense_description))
                conn.commit()
                conn.close()
                st.success("Expense added successfully!")
            else:
                st.error("Please log in.")
    
    if st.session_state.user_id:
        conn = sqlite3.connect('finance_tracker.db')
        df_expenses = pd.read_sql_query("SELECT date, amount, category, description FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        if not df_expenses.empty:
            st.markdown("### Expense Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                total_expenses = df_expenses["amount"].sum()
                st.metric("Total Expenses", f"{currency_symbols[st.session_state.currency]} {convert_amount(total_expenses):,.2f}")
            with col2:
                avg_daily = df_expenses.groupby("date")["amount"].sum().mean()
                st.metric("Average Daily", f"{currency_symbols[st.session_state.currency]} {convert_amount(avg_daily):,.2f}")
            with col3:
                most_common = df_expenses["category"].mode()[0]
                st.metric("Top Category", most_common)
            
            st.markdown("### Expense Analysis")
            fig = px.pie(df_expenses, values="amount", names="category", title="Expense Distribution")
            st.plotly_chart(fig)
            df_expenses["date"] = pd.to_datetime(df_expenses["date"])
            daily_expenses = df_expenses.groupby("date")["amount"].sum().reset_index()
            daily_expenses["amount_converted"] = daily_expenses["amount"].apply(convert_amount)
            fig = px.line(daily_expenses, x="date", y="amount_converted", title="Daily Expense Trend", labels={"amount_converted": f"Amount ({currency_symbols[st.session_state.currency]})"})
            st.plotly_chart(fig)
        else:
            st.info("No expenses added yet.")

# Investment Planner
def investment_planner():
    st.markdown("<h1 style='text-align: center;'>Investment Planner</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Calculator", "Portfolio", "Goals", "Retirement"])
    with tab1:
        st.markdown("### Investment Calculator")
        calc_type = st.radio("Type", ["SIP", "Lump Sum"])
        if calc_type == "SIP":
            monthly_investment = st.number_input("Monthly Investment (₹)", min_value=100, value=5000)
            years = st.number_input("Years", min_value=1, max_value=40, value=10)
            expected_return = st.number_input("Annual Return (%)", min_value=1.0, max_value=30.0, value=12.0)
            months = years * 12
            monthly_rate = expected_return / (12 * 100)
            future_value = monthly_investment * ((pow(1 + monthly_rate, months) - 1) / monthly_rate) * (1 + monthly_rate)
            total_investment = monthly_investment * months
        else:
            initial_investment = st.number_input("Lump Sum (₹)", min_value=1000, value=50000)
            years = st.number_input("Years", min_value=1, max_value=40, value=10)
            expected_return = st.number_input("Annual Return (%)", min_value=1.0, max_value=30.0, value=12.0)
            future_value = initial_investment * pow(1 + expected_return / 100, years)
            total_investment = initial_investment
        total_returns = future_value - total_investment
        st.markdown("### Projections")
        col1, col2 = st.columns(2)
        col1.metric("Invested Amount", f"₹{total_investment:,.2f}")
        col2.metric("Total Returns", f"₹{total_returns:,.2f}")
    with tab2:
        st.markdown("### Portfolio Allocation")
        age = st.number_input("Age", min_value=18, max_value=100, value=30)
        equity_percent = max(20, min(80, 100 - age))
        debt_percent = 100 - equity_percent
        fig = go.Figure(data=[go.Pie(labels=['Equity', 'Debt'], values=[equity_percent, debt_percent], hole=.3)])
        fig.update_layout(title="Asset Allocation")
        st.plotly_chart(fig)
    with tab3:
        st.markdown("### Goal Tracker")
        st.write("Goal tracking to be implemented.")
    with tab4:
        st.markdown("### Retirement Planning")
        current_age = st.number_input("Current Age", min_value=18, max_value=100, value=30)
        retirement_age = st.number_input("Retirement Age", min_value=current_age + 1, max_value=100, value=60)
        monthly_saving = st.number_input("Monthly Savings (₹)", min_value=0, value=20000)
        expected_return = st.number_input("Annual Return (%)", min_value=1.0, max_value=20.0, value=8.0)
        years_to_retire = retirement_age - current_age
        monthly_rate = expected_return / 12 / 100
        future_value = monthly_saving * ((pow(1 + monthly_rate, years_to_retire * 12) - 1) / monthly_rate) * (1 + monthly_rate)
        st.metric("Retirement Corpus", f"₹{future_value:,.2f}")
        st.markdown("### Systematic Withdrawal Plan (SWP)")
        initial_corpus = st.number_input("Initial Corpus (₹)", min_value=10000, value=int(future_value), key="swp_corpus")
        withdrawal_amount = st.number_input("Monthly Withdrawal (₹)", min_value=1000, value=20000, key="swp_withdrawal")
        swp_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=20.0, value=8.0, key="swp_expected_return")
        tenure_years = st.number_input("Tenure (Years)", min_value=1, max_value=40, value=10, key="swp_tenure")
        monthly_rate = swp_return / 12 / 100
        months = tenure_years * 12
        remaining_corpus = initial_corpus
        swp_data = []
        for month in range(months):
            interest = remaining_corpus * monthly_rate
            remaining_corpus += interest - withdrawal_amount
            swp_data.append({"Month": month + 1, "Corpus Value": max(0, remaining_corpus)})
            if remaining_corpus <= 0:
                break
        swp_df = pd.DataFrame(swp_data)
        st.line_chart(swp_df.set_index("Month"))
        st.write(f"SWP Duration: {len(swp_data)} months")

# Advanced Analytics
def advanced_analytics():
    st.markdown("<h1 style='text-align: center;'>Advanced Analytics</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Expense Analysis", "Investment Analysis", "Financial Health"])
    with tab1:
        st.markdown("### Expense Pattern Analysis")
        conn = sqlite3.connect('finance_tracker.db')
        df_expenses = pd.read_sql_query("SELECT date, amount, category FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        if not df_expenses.empty:
            df_expenses['date'] = pd.to_datetime(df_expenses['date'])
            monthly_expenses = df_expenses.groupby(df_expenses['date'].dt.strftime('%Y-%m'))[['amount']].sum()
            fig = px.line(monthly_expenses, x=monthly_expenses.index, y='amount', title='Monthly Expense Trend')
            st.plotly_chart(fig)
    with tab2:
        st.markdown("### Investment Performance")
        st.write("Investment analysis to be implemented.")
    with tab3:
        st.markdown("### Financial Health")
        monthly_income = st.number_input("Monthly Income (₹)", min_value=0, value=50000)
        monthly_expenses = st.number_input("Monthly Expenses (₹)", min_value=0, value=30000)
        savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100 if monthly_income > 0 else 0
        st.metric("Savings Rate", f"{savings_rate:.1f}%")

# Debt Management
def load_loans_from_db():
    if st.session_state.user_id:
        conn = sqlite3.connect('finance_tracker.db')
        c = conn.cursor()
        c.execute("SELECT id, loan_type, principal, emi_amount, amount_paid, interest_rate, tenure_months FROM loans WHERE user_id = ?", (st.session_state.user_id,))
        loans = c.fetchall()
        conn.close()
        st.session_state.loans = [{"id": loan[0], "Loan Type": loan[1], "Loan Amount": loan[2], "EMI Amount": loan[3], "Amount Paid": loan[4], "Interest Rate": loan[5], "Tenure (Months)": loan[6]} for loan in loans]

def debt_management():
    load_loans_from_db()
    st.markdown("<h1 style='text-align: center;'>Debt Management</h1>", unsafe_allow_html=True)
    st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">', unsafe_allow_html=True)
    loan_types = {
        "Personal Loan": {"icon": "cash", "interest_rate": 15.0},
        "Credit Card Loan": {"icon": "credit-card", "interest_rate": 45.0},
        "Education Loan": {"icon": "book", "interest_rate": 10.0},
        "Home Loan": {"icon": "house", "interest_rate": 8.0},
    }
    tab1, tab2 = st.tabs(["Loan Entry & Editing", "Debt Strategy"])
    with tab1:
        st.markdown("### Add New Loan")
        loan_type = option_menu("Select Loan Type:", list(loan_types.keys()), icons=[loan_types[lt]["icon"] for lt in loan_types], menu_icon="list", default_index=0, styles={"nav-link-selected": {"background-color": "#00704A"}})
        default_interest = loan_types[loan_type]["interest_rate"]
        col1, col2, col3 = st.columns(3)
        with col1:
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0.0, step=1000.0)
        with col2:
            emi_amount = st.number_input("EMI Amount (₹)", min_value=0.0, step=100.0)
        with col3:
            amount_paid = st.number_input("Amount Paid (₹)", min_value=0.0, step=1000.0)
        tenure_months = st.number_input("Tenure (Months)", min_value=1, step=1)
        interest_rate = st.slider("Interest Rate (%)", 1.0, 100.0, float(default_interest), step=0.1)
        if st.button("Submit"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("INSERT INTO loans (user_id, loan_type, principal, emi_amount, amount_paid, interest_rate, tenure_months) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (st.session_state.user_id, loan_type, loan_amount, emi_amount, amount_paid, interest_rate, tenure_months))
                conn.commit()
                conn.close()
                st.session_state.loans.append({"id": c.lastrowid, "Loan Type": loan_type, "Loan Amount": loan_amount, "EMI Amount": emi_amount, "Amount Paid": amount_paid, "Interest Rate": interest_rate, "Tenure (Months)": tenure_months})
                st.rerun()
        
        if st.session_state.loans:
            st.markdown("### Loan Overview")
            df = pd.DataFrame(st.session_state.loans)
            df["Outstanding Balance"] = df["Loan Amount"] - df["Amount Paid"]
            for i, loan in df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{loan['Loan Type']} - {currency_symbols[st.session_state.currency]} {convert_amount(loan['Outstanding Balance']):,.2f} @ {loan['Interest Rate']}%")
                with col2:
                    if st.button("Edit", key=f"edit_{i}"):
                        st.session_state.edit_loan_idx = i
                with col3:
                    if st.button("Delete", key=f"delete_{i}"):
                        conn = sqlite3.connect('finance_tracker.db')
                        c = conn.cursor()
                        c.execute("DELETE FROM loans WHERE id = ?", (loan['id'],))
                        conn.commit()
                        conn.close()
                        st.session_state.loans.pop(i)
                        st.rerun()
            if "edit_loan_idx" in st.session_state:
                idx = st.session_state.edit_loan_idx
                loan = st.session_state.loans[idx]
                with st.form(f"edit_form_{idx}"):
                    new_amount = st.number_input("Loan Amount", value=float(loan["Loan Amount"]))
                    new_emi = st.number_input("EMI Amount", value=float(loan["EMI Amount"]))
                    new_paid = st.number_input("Amount Paid", value=float(loan["Amount Paid"]))
                    new_rate = st.slider("Interest Rate (%)", 1.0, 100.0, float(loan["Interest Rate"]))
                    new_tenure = st.number_input("Tenure (Months)", value=int(loan["Tenure (Months)"]))
                    if st.form_submit_button("Update"):
                        conn = sqlite3.connect('finance_tracker.db')
                        c = conn.cursor()
                        c.execute("UPDATE loans SET principal = ?, emi_amount = ?, amount_paid = ?, interest_rate = ?, tenure_months = ? WHERE id = ?",
                                 (new_amount, new_emi, new_paid, new_rate, new_tenure, loan['id']))
                        conn.commit()
                        conn.close()
                        st.session_state.loans[idx].update({"Loan Amount": new_amount, "EMI Amount": new_emi, "Amount Paid": new_paid, "Interest Rate": new_rate, "Tenure (Months)": new_tenure})
                        del st.session_state.edit_loan_idx
                        st.rerun()
    with tab2:
        st.markdown("### Debt Strategy")
        if st.session_state.loans:
            monthly_budget = st.number_input("Monthly Budget (₹)", min_value=0.0, value=10000.0)
            loans_df = pd.DataFrame(st.session_state.loans)
            loans_df["Outstanding Balance"] = loans_df["Loan Amount"] - loans_df["Amount Paid"]
            total_budget = monthly_budget
            repayment_plan = []
            remaining_balance = loans_df["Outstanding Balance"].sum()
            months = 0
            while remaining_balance > 0 and months < 1200:
                month_budget = total_budget
                for idx, loan in loans_df.iterrows():
                    if month_budget >= loan["EMI Amount"] and loan["Outstanding Balance"] > 0:
                        payment = min(loan["EMI Amount"], loan["Outstanding Balance"])
                        loans_df.at[idx, "Outstanding Balance"] = max(0, loan["Outstanding Balance"] - payment)
                        month_budget -= payment
                remaining_balance = loans_df["Outstanding Balance"].sum()
                repayment_plan.append({"Month": months, "Remaining Balance": remaining_balance})
                months += 1
                if remaining_balance <= 0:
                    break
            repayment_df = pd.DataFrame(repayment_plan)
            st.success(f"Debt-free in {months} months")
            fig = go.Figure(go.Scatter(x=repayment_df["Month"], y=repayment_df["Remaining Balance"], mode="lines", name="Balance"))
            fig.update_layout(title="Debt Repayment", xaxis_title="Months", yaxis_title=f"Balance ({currency_symbols[st.session_state.currency]})")
            st.plotly_chart(fig)

# Settings Page
def settings_page():
    st.markdown("<h1 style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)
    st.markdown("### Profile Settings")
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    c.execute("SELECT username, email FROM users WHERE id = ?", (st.session_state.user_id,))
    user_info = c.fetchone()
    conn.close()
    if user_info:
        st.text_input("Username", value=user_info[0], disabled=True)
        st.text_input("Email", value=user_info[1], disabled=True)
    
    st.markdown("### Notification Settings")
    st.checkbox("Email Alerts for Unusual Expenses", value=True)
    st.checkbox("Monthly Report", value=True)
    
    st.markdown("### Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Data as CSV"):
            conn = sqlite3.connect('finance_tracker.db')
            df_expenses = pd.read_sql_query("SELECT * FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
            csv = df_expenses.to_csv(index=False)
            st.download_button("Download CSV", csv, "expenses_data.csv", "text/csv")
            conn.close()
    with col2:
        if st.button("Generate Financial Report (PDF)"):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph("Personal Financial Report", styles['Title']))
            elements.append(Spacer(1, 12))
            conn = sqlite3.connect('finance_tracker.db')
            c = conn.cursor()
            c.execute("SELECT username, email FROM users WHERE id = ?", (st.session_state.user_id,))
            user_info = c.fetchone()
            elements.append(Paragraph(f"Name: {user_info[0]} | Email: {user_info[1]} | Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            elements.append(Spacer(1, 12))
            df_expenses = pd.read_sql_query("SELECT * FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
            total_expenses = df_expenses["amount"].sum()
            elements.append(Paragraph("Executive Summary", styles['Heading2']))
            loans_df = pd.DataFrame(st.session_state.loans)
            total_debt = loans_df["Outstanding Balance"].sum() if not loans_df.empty else 0
            total_investments = 0
            net_worth = total_investments - total_debt
            elements.append(Paragraph(f"Total Expenses: ₹{total_expenses:,.2f}", styles['Normal']))
            elements.append(Paragraph(f"Total Debt: ₹{total_debt:,.2f}", styles['Normal']))
            elements.append(Paragraph(f"Total Investments: ₹{total_investments:,.2f}", styles['Normal']))
            elements.append(Paragraph(f"Net Worth: ₹{net_worth:,.2f}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Expense Analysis", styles['Heading2']))
            exp_table = [["Date", "Amount", "Category"]] + df_expenses[["date", "amount", "category"]].values.tolist()[:10]
            elements.append(Table(exp_table, colWidths=[100, 100, 100]))
            plt.pie(df_expenses.groupby("category")["amount"].sum(), labels=df_expenses["category"].unique(), autopct='%1.1f%%')
            plt.savefig("exp_pie.png")
            elements.append(Image("exp_pie.png", width=200, height=200))
            doc.build(elements)
            buffer.seek(0)
            st.download_button("Download PDF Report", buffer, "financial_report.pdf", "application/pdf")
            conn.close()

# Main app
def main():
    init_db()
    migrate_db()
    handle_theme_from_url()
    st.markdown(theme_toggle(), unsafe_allow_html=True)
    components.html("""
    <script>
        window.addEventListener('message', function(event) {
            if (event.data.type === 'themeChange') {
                const url = new URL(window.location);
                url.searchParams.set('theme', event.data.theme);
                window.location.href = url.toString();
            }
        });
    </script>
    """, height=0)
    
    with st.sidebar:
        currency_switcher()
    
    if not st.session_state.authenticated:
        auth_page()
    else:
        if st.button("🔍"):
            st.session_state.show_search = not st.session_state.show_search
        if st.session_state.show_search:
            sections = ["Dashboard", "Expenses", "Investments", "Analysis", "Debt Management", "Settings"]
            selected_section = st.selectbox("Choose a section", sections)
            if selected_section:
                st.session_state.selected_index = sections.index(selected_section)
                st.session_state.show_search = False
                st.rerun()
        
        selected = create_navigation()
        if selected == "Dashboard":
            dashboard()
        elif selected == "Expenses":
            expense_tracker()
        elif selected == "Investments":
            investment_planner()
        elif selected == "Analysis":
            advanced_analytics()
        elif selected == "Debt Management":
            debt_management()
        elif selected == "Settings":
            settings_page()
        st.markdown("<div class='footer'>Developed by Muhammed Adnan | Contact: kladnan321@gmail.com</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()