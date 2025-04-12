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
import numpy_financial as npf  # Added for SWP calculations
import numpy_financial as npf


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
if 'theme' not in st.session_state:
    st.session_state.theme = "light"
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

# Loan types with icons and default interest rates
loan_types = {
    "Personal Loan": {"icon": "cash", "interest_rate": 15},
    "Credit Card Loan": {"icon": "credit-card", "interest_rate": 45},
    "Education Loan": {"icon": "book", "interest_rate": 10},
    "App Loan": {"icon": "app-indicator", "interest_rate": 30},
    "Home Loan": {"icon": "house", "interest_rate": 8},
    "Car Loan": {"icon": "car-front", "interest_rate": 9},
    "Business Loan": {"icon": "briefcase", "interest_rate": 12},
    "Gold Loan": {"icon": "gem", "interest_rate": 10},
    "Agricultural Loan": {"icon": "flower1", "interest_rate": 7},
    "Consumer Durable Loan": {"icon": "cart-fill", "interest_rate": 18},
    "Loan Against Property": {"icon": "building", "interest_rate": 11},
    "Loans Against Securities": {"icon": "shield-lock", "interest_rate": 9},
    "Payday Loan": {"icon": "calendar", "interest_rate": 50},
    "Two-Wheeler Loan": {"icon": "bicycle", "interest_rate": 12},
    "Government-Backed Loan": {"icon": "bank", "interest_rate": 6},
    "Other": {"icon": "question-circle", "interest_rate": 10}
}

# ============ THEME IMPLEMENTATION ============
def load_css():
    css = """
    <style>
    @import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.2/font/bootstrap-icons.css");
    .stApp {
        background-color: %s;
        color: %s;
    }
    .main .block-container {
        padding: 1rem;
        border-radius: 0.5rem;
        max-width: 100%%;
    }
    h1, h2, h3, h4, h5, h6 {
        color: %s;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem;
        padding: 10px 20px;
        background-color: %s;
        color: %s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00704A;
        color: white;
    }
    .stButton>button {
        border-radius: 0.5rem;
        background-color: #00704A;
        color: white;
        transition: transform 0.2s, background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #C6A969;
        color: #1E3932;
        transform: scale(1.05);
    }
    .stExpander {
        border-radius: 0.5rem;
        border: 1px solid %s;
    }
    div[data-testid="stForm"] {
        border-radius: 0.5rem;
        border: 1px solid %s;
        padding: 1rem;
        background-color: %s;
    }
    div[data-testid="stMetric"] {
        background-color: %s;
        border-radius: 0.5rem;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%%;
        background-color: #00704A;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 70px;
        z-index: 1000;
        display: flex;
        align-items: center;
        font-size: 14px;
        background-color: %s;
        border-radius: 20px;
        padding: 5px 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.2s;
    }
    .theme-toggle:hover {
        transform: scale(1.05);
    }
    .theme-toggle img {
        width: 25px;
        height: 25px;
        margin-right: 5px;
    }
    .stDataFrame, .stTable, .stSelectbox, .stNumberInput, .stDateInput, .stTextInput, .stTextArea {
        background-color: %s;
        color: %s;
        border-radius: 0.5rem;
    }
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            font-size: 14px;
        }
        .stButton>button {
            padding: 8px 16px;
            font-size: 14px;
        }
    }
    </style>
    """
    if st.session_state.dark_mode:
        return css % ('#1E1E1E', '#E0E0E0', '#C6A969', '#2D2D2D', '#E0E0E0', '#444444', '#444444', '#2D2D2D', '#2D2D2D', '#2D2D2D', '#2D2D2D', '#E0E0E0')
    else:
        return css % ('#F7F7F7', '#1E3932', '#00704A', 'white', '#1E3932', '#e6e6e6', '#e6e6e6', 'white', 'white', 'white', 'white', '#1E3932')

def theme_toggle():
    light_icon = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNGRkMxMDciIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1zdW4iPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjQiLz48cGF0aCBkPSJNMTIgMnY0Ii8+PHBhdGggZD0iTTEyIDE4djQiLz48cGF0aCBkPSJNNC45MyA0LjkzIDcuNzYgNy43NiIvPjxwYXRoIGQ9Ik0xNi4yNCAxNi4yNCAxOS4wNyAxOS4wNyIvPjxwYXRoIGQ9Ik0yIDEyaDQiLz48cGF0aCBkPSJNMTggMTJoNCIvPjxwYXRoIGQ9Ik00LjkzIDE5LjA3IDcuNzYgMTYuMjQiLz48cGF0aCBkPSJNMTYuMjQgNy43NiAxOS4wNyA0LjkzIi8+PC9zdmc+"
    dark_icon = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjY2ZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1tb29uIj48cGF0aCBkPSJNMTIgM2MuMTMyIDIuMjItMS41MzggNC4xNTUtMy43NDggNC4xNTVhNi4yMSA2LjIxIDAgMCAxLTIuMzMtLjQ1M2MuMTM5IDMuNTYyIDMuMDQ5IDYuNDI4IDYuNjM0IDYuNDI0IDMuNjggMCA2LjY2Ny0yLjk3MyA2LjY2Ny0yLjY0QzE1LjIyNyAzLjE1MyAxNi4xNjggMCAxMi4xMDIgMGMtLjE2OCAwLS4zMzYuMDA1LS41MDIuMDE1QzEyLjAwMSAuMDEgMTIgMy4wMyAxMiA2LjAzIDEyIDYuMDMgMTIgNnYgNi4wMyA2LjA0Yy0uMDAxIDMuMDA0IDIuNDM2IDUuNDIgNS40OTggNS40MiA0LjE0IDAgNy41MDgtMy4zNjggNy41MDgtNy41MDhWMmMwLS4xNjgtLjAwNS0uMzM2LS4wMTUtLjUwMkwyMS45ODUgNi4wMTZD"
    icon = dark_icon if st.session_state.dark_mode else light_icon
    label = "Switch to Light Mode" if st.session_state.dark_mode else "Switch to Dark Mode"
    toggle_html = f"""
    <div class="theme-toggle" onclick="toggleTheme()">
        <img src="{icon}" alt="Theme Icon" />
        <span>{label}</span>
    </div>
    <script>
    function toggleTheme() {{
        fetch('/?theme=' + (document.querySelector('.stApp').classList.contains('dark') ? 'light' : 'dark'), {{
            method: 'GET'
        }}).then(() => {{
            window.location.reload();
        }});
    }}
    </script>
    """
    return toggle_html

def currency_switcher():
    currencies = {
        "INR": "https://flagcdn.com/w40/in.png",
        "USD": "https://flagcdn.com/w40/us.png",
        "AED": "https://flagcdn.com/w40/ae.png",
        "SAR": "https://flagcdn.com/w40/sa.png",
        "CAD": "https://flagcdn.com/w40/ca.png",
        "QAR": "https://flagcdn.com/w40/qa.png",
        "CNY": "https://flagcdn.com/w40/cn.png"
    }
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_currency = st.selectbox("Select Currency", list(currencies.keys()), key="currency_select")
    with col2:
        st.image(currencies[selected_currency], width=40)
    st.session_state.currency = selected_currency
    return selected_currency

def handle_theme_from_url():
    query_params = st.query_params
    if 'theme' in query_params:
        theme_param = query_params['theme']
        if theme_param == 'dark' and not st.session_state.dark_mode:
            st.session_state.dark_mode = True
        elif theme_param == 'light' and st.session_state.dark_mode:
            st.session_state.dark_mode = False
    st.markdown(load_css(), unsafe_allow_html=True)
    st.markdown(theme_toggle(), unsafe_allow_html=True)

# ============ COLOR SCHEME ============
if st.session_state.dark_mode:
    COLORS = {
        'primary': '#00704A',
        'secondary': '#27251F',
        'accent': '#C6A969',
        'background': '#1E1E1E',
        'text_dark': '#E0E0E0',
        'text_light': '#FFFFFF',
        'success': '#006241',
        'warning': '#CBA258',
        'error': '#DC3545',
    }
else:
    COLORS = {
        'primary': '#00704A',
        'secondary': '#27251F',
        'accent': '#C6A969',
        'background': '#F7F7F7',
        'text_dark': '#1E3932',
        'text_light': '#FFFFFF',
        'success': '#006241',
        'warning': '#CBA258',
        'error': '#DC3545',
    }

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, amount REAL, category TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL, target_date TEXT, priority TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans
                 (id INTEGER PRIMARY KEY, user_id INTEGER, loan_type TEXT, principal REAL, interest_rate REAL, tenure_months INTEGER, start_date TEXT, outstanding_balance REAL, monthly_payment REAL, description TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ============ AUTHENTICATION ============
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
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
        conn.commit()
        return True, "Registration successful! Please login."
    except sqlite3.IntegrityError:
        return False, "Email or username already exists!"
    finally:
        conn.close()

def auth_page():
    st.markdown("<h1 style='text-align: center;'>AI Financial Planner</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login")
            if submit:
                if login_user(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username", key="reg_username")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Choose Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
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
        options=["Dashboard", "Expenses", "Investments", "Analysis", "Debt Management", "Settings"],
        icons=["house", "wallet", "graph-up", "clipboard-data", "credit-card", "gear"],
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
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Monthly Savings", value="₹25,000", delta="↑ 8%")
    with col2:
        st.metric(label="Investments", value="₹1,50,000", delta="↑ 12%")
    with col3:
        st.metric(label="Expenses", value="₹45,000", delta="5%")
    with col4:
        st.metric(label="Net Worth", value="₹5,00,000", delta="↑ 15%")
    st.markdown("### Market Overview")
    try:
        symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'WIPRO.NS']
        market_data = pd.DataFrame()
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1d')
            if not hist.empty:
                market_data.loc[symbol, 'Price'] = hist['Close'].iloc[-1]
                market_data.loc[symbol, 'Change'] = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                market_data.loc[symbol, 'Change %'] = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
        st.dataframe(market_data.style.format({'Price': '₹{:,.2f}', 'Change': '₹{:,.2f}', 'Change %': '{:,.2f}%'}))
        st.markdown("### Market Trends (Last Month)")
        fig = go.Figure()
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1mo')
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name=symbol, mode='lines'))
        fig.update_layout(title='Stock Performance', xaxis_title='Date', yaxis_title='Price (₹)', height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Unable to fetch market data. Please check your internet connection.")

# ============ EXPENSE TRACKER ============
def expense_tracker():
    st.markdown("<h1 style='text-align: center;'>Smart Expense Tracker</h1>", unsafe_allow_html=True)
    with st.expander("Add New Expense", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            expense_date = st.date_input("Date", datetime.now(), key="exp_date")
            expense_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, value=None, key="exp_amount")
        with col2:
            default_categories = ["Needs", "Wants", "Investment", "Bills", "Entertainment", "Health", "Other"]
            expense_category = st.selectbox("Category", default_categories, key="exp_category")
            if expense_category == "Other":
                expense_category = st.text_input("Specify Category", key="exp_other_category")
        with col3:
            expense_description = st.text_area("Description", height=100, key="exp_description")
        if st.button("Add Expense", key="add_expense"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute(
                    "INSERT INTO expenses (user_id, date, amount, category, description) VALUES (?, ?, ?, ?, ?)",
                    (st.session_state.user_id, expense_date.strftime("%Y-%m-%d"), expense_amount, expense_category, expense_description)
                )
                conn.commit()
                conn.close()
                st.success("Expense added successfully!")
            else:
                st.error("User not authenticated. Please log in.")
    if st.session_state.user_id:
        conn = sqlite3.connect('finance_tracker.db')
        df_expenses = pd.read_sql_query("SELECT date, amount, category, description FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        if not df_expenses.empty:
            st.markdown("### Expense Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                total_expenses = df_expenses["amount"].sum()
                st.metric("Total Expenses", f"{st.session_state.currency} {total_expenses:,.2f}")
            with col2:
                avg_daily = df_expenses.groupby("date")["amount"].sum().mean()
                st.metric("Average Daily Expense", f"{avg_daily:,.2f}")
            with col3:
                most_common_category = df_expenses["category"].mode()[0]
                st.metric("Most Common Category", most_common_category)
            st.markdown("### Expense Analysis")
            fig = px.pie(df_expenses, values="amount", names="category", title="Expense Distribution by Category")
            st.plotly_chart(fig)
            df_expenses["date"] = pd.to_datetime(df_expenses["date"])
            daily_expenses = df_expenses.groupby("date")["amount"].sum().reset_index()
            fig = px.line(daily_expenses, x="date", y="amount", title="Daily Expense Trend", labels={"amount": "Amount (₹)", "date": "Date"})
            st.plotly_chart(fig)
        else:
            st.info("No expenses have been added yet.")
    else:
        st.error("User not authenticated. Please log in.")

# ============ INVESTMENT PLANNER ============
def investment_planner():
    st.markdown("<h1 style='text-align: center;'>Investment Planner</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Investment Calculator", "Portfolio Allocation", "Goal Tracker", "Retirement Planning"])
    with tab1:
        st.markdown("### Investment Calculator")
        calc_type = st.radio("Select Calculator Type", ["SIP", "Lump Sum"], key="calc_type")
        if calc_type == "SIP":
            initial_investment = 0
            monthly_investment = st.number_input("Monthly Investment (₹)", min_value=100, value=None, key="sip_monthly")
            period_unit = st.selectbox("Investment Period Unit", ["Years", "Months"], key="sip_period_unit")
            if period_unit == "Years":
                years = st.number_input("Investment Period (Years)", min_value=1, max_value=40, value=None, key="sip_years")
                months = years * 12 if years else 0
            else:
                months = st.number_input("Investment Period (Months)", min_value=1, value=None, key="sip_months")
                years = months / 12 if months else 0
            expected_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=30.0, value=None, key="sip_return")
        else:
            initial_investment = st.number_input("Lump Sum Investment (₹)", min_value=1000, value=None, key="lump_sum")
            monthly_investment = 0
            period_unit = st.selectbox("Investment Period Unit", ["Years", "Months"], key="lump_period_unit")
            if period_unit == "Years":
                years = st.number_input("Investment Period (Years)", min_value=1, max_value=40, value=None, key="lump_years")
                months = years * 12 if years else 0
            else:
                months = st.number_input("Investment Period (Months)", min_value=1, value=None, key="lump_months")
                years = months / 12 if months else 0
            expected_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=30.0, value=None, key="lump_return")
        inflation_rate = st.slider("Assumed Inflation Rate (%)", 2.9, 8.9, 4.5, key="inflation_rate")
        holding_period = st.selectbox("Holding Period", ["Less than 12 months", "More than 12 months"], key="holding_period")
        if all([initial_investment or monthly_investment, expected_return, years or months]):
            monthly_rate = expected_return / (12 * 100)
            if calc_type == "SIP":
                real_return = (1 + monthly_rate) / (1 + inflation_rate / 1200) - 1
                future_value = monthly_investment * ((pow(1 + real_return, months) - 1) / real_return) * (1 + real_return)
                total_investment = monthly_investment * months
            else:
                real_return = (1 + expected_return / 100) / (1 + inflation_rate / 100) - 1
                future_value = initial_investment * pow(1 + real_return, years)
                total_investment = initial_investment
            total_returns = future_value - total_investment
            inflation_adjusted_value = future_value / pow(1 + inflation_rate / 100, years)
            tax_rate = 0.20 if holding_period == "Less than 12 months" else 0.125
            tax_amount = total_returns * tax_rate
            after_tax_returns = total_returns - tax_amount
            st.markdown("### Investment Projections")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Initial Investment", f"₹{total_investment:,.2f}")
            col2.metric("Total Returns", f"₹{total_returns:,.2f}", help="Gross return before inflation & taxes")
            col3.metric("Inflation-Adjusted Value", f"₹{inflation_adjusted_value:,.2f}", delta=f"-₹{(future_value - inflation_adjusted_value):,.2f}", delta_color="inverse")
            col4.metric("After-Tax Returns", f"₹{after_tax_returns:,.2f}", delta=f"-₹{tax_amount:,.2f}", delta_color="inverse")
            st.markdown("### Investment Growth Projection")
            period_range = np.arange(0, (years if period_unit == "Years" else months) + 1)
            x_axis_label = 'Years' if period_unit == "Years" else 'Months'
            if calc_type == "SIP":
                growth_values = [monthly_investment * ((pow(1 + monthly_rate, period) - 1) / monthly_rate) * (1 + monthly_rate) for period in period_range]
                fig = go.Figure(go.Scatter(x=period_range, y=growth_values, mode='lines', name='Investment Growth'))
                fig.update_layout(title=f'{calc_type} Investment Growth', xaxis_title=x_axis_label, yaxis_title='Amount (₹)', height=400)
                st.plotly_chart(fig)
    with tab2:
        st.markdown("### Portfolio Allocation")
        age = st.number_input("Your Age", min_value=18, max_value=100, value=None, key="port_age")
        risk_profile = st.selectbox("Risk Profile", ["Conservative", "Moderate", "Aggressive"], key="risk_profile")
        if age:
            equity_percent = max(20, min(80, 100 - age))
            if risk_profile == "Conservative":
                equity_percent = max(20, equity_percent - 10)
            elif risk_profile == "Aggressive":
                equity_percent = min(80, equity_percent + 10)
            debt_percent = 100 - equity_percent
            large_cap, mid_cap, small_cap = equity_percent * 0.60, equity_percent * 0.25, equity_percent * 0.15
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure(data=[go.Pie(labels=['Equity', 'Debt'], values=[equity_percent, debt_percent], hole=.3)])
                fig.update_layout(title="Broad Asset Allocation")
                st.plotly_chart(fig)
            with col2:
                fig = go.Figure(data=[go.Pie(labels=['Large Cap', 'Mid Cap', 'Small Cap'], values=[large_cap, mid_cap, small_cap], hole=.3)])
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
        with st.expander("Add New Goal", expanded=True):
            with st.form("new_goal"):
                goal_name = st.text_input("Goal Name", key="goal_name")
                goal_amount = st.number_input("Target Amount (₹)", min_value=0.0, value=None, key="goal_amount")
                goal_date = st.date_input("Target Date", key="goal_date")
                priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="goal_priority")
                current_amount = st.number_input("Current Amount (₹)", min_value=0.0, value=None, key="goal_current")
                submitted = st.form_submit_button("Add Goal")
                if submitted and all([goal_name, goal_amount, current_amount is not None]):
                    conn = sqlite3.connect('finance_tracker.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO goals (user_id, name, target_amount, current_amount, target_date, priority) VALUES (?, ?, ?, ?, ?, ?)",
                              (st.session_state.user_id, goal_name, goal_amount, current_amount, goal_date.strftime("%Y-%m-%d"), priority))
                    conn.commit()
                    conn.close()
                    st.success("Goal added successfully!")
        conn = sqlite3.connect('finance_tracker.db')
        df_goals = pd.read_sql_query("SELECT name, target_amount, current_amount, target_date, priority FROM goals WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        if not df_goals.empty:
            st.markdown("### Your Financial Goals")
            for _, goal in df_goals.iterrows():
                progress = (goal['current_amount'] / goal['target_amount']) * 100
                st.markdown(f"<h4>{goal['name']} ({goal['priority']} Priority)</h4>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.progress(progress / 100)
                    st.markdown(f"Progress: {progress:.1f}%")
                with col2:
                    st.markdown(f"Target: ₹{goal['target_amount']:,.2f}<br>Current: ₹{goal['current_amount']:,.2f}<br>Target Date: {goal['target_date']}", unsafe_allow_html=True)
                target_date = datetime.strptime(goal['target_date'], "%Y-%m-%d")
                months_remaining = (target_date - datetime.now()).days / 30
                if months_remaining > 0:
                    monthly_needed = (goal['target_amount'] - goal['current_amount']) / months_remaining
                    st.info(f"Monthly savings needed: ₹{monthly_needed:,.2f}")
    with tab4:
        st.markdown("### Retirement Planning with SWP")
        col1, col2 = st.columns(2)
        with col1:
            current_age = st.number_input("Current Age", min_value=18, max_value=100, value=None, key="retire_current_age")
            retirement_age = st.number_input("Retirement Age", min_value=(current_age or 18)+1, max_value=100, value=None, key="retire_age")
            life_expectancy = st.number_input("Life Expectancy", min_value=(retirement_age or 19)+1, max_value=120, value=None, key="life_expectancy")
        with col2:
            current_savings = st.number_input("Current Retirement Savings (₹)", min_value=0.0, value=None, key="retire_savings")
            monthly_investment = st.number_input("Monthly Investment (₹)", min_value=0.0, value=None, key="retire_monthly")
            pre_return = st.number_input("Expected Annual Return Pre-Retirement (%)", min_value=0.0, value=None, key="pre_return")
            post_return = st.number_input("Expected Annual Return Post-Retirement (%)", min_value=0.0, value=None, key="post_return")
            inflation_rate = st.number_input("Inflation Rate (%)", min_value=0.0, value=None, key="retire_inflation")
        if st.button("Calculate Retirement Plan", key="calc_retirement") and all([current_age, retirement_age, life_expectancy, current_savings is not None, monthly_investment is not None, pre_return, post_return, inflation_rate]):
            years_to_retirement = retirement_age - current_age
            years_in_retirement = life_expectancy - retirement_age
            fv_savings = current_savings * (1 + pre_return/100)**years_to_retirement
            monthly_rate_pre = pre_return / (12 * 100)
            fv_investments = monthly_investment * (((1 + monthly_rate_pre)**(12*years_to_retirement) - 1) / monthly_rate_pre) * (1 + monthly_rate_pre)
            corpus = fv_savings + fv_investments
            monthly_rate_post = post_return / (12 * 100)
            monthly_withdrawal = npf.pmt(monthly_rate_post, years_in_retirement*12, -corpus, 0)
            st.success(f"Projected Retirement Corpus: ₹{corpus:,.2f}")
            st.success(f"Monthly Withdrawal Amount (SWP): ₹{monthly_withdrawal:,.2f}")

# ============ ADVANCED ANALYTICS ============
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
            fig = px.line(monthly_expenses, x=monthly_expenses.index, y='amount', title='Monthly Expense Trend', labels={'amount': 'Amount (₹)', 'date': 'Month'})
            st.plotly_chart(fig)
            col1, col2 = st.columns(2)
            with col1:
                category_expenses = df_expenses.groupby('category')['amount'].sum()
                fig = px.pie(values=category_expenses.values, names=category_expenses.index, title='Expense Distribution by Category')
                st.plotly_chart(fig)
            with col2:
                df_expenses['weekday'] = df_expenses['date'].dt.day_name()
                weekly_expenses = df_expenses.groupby('weekday')['amount'].mean()
                fig = px.bar(x=weekly_expenses.index, y=weekly_expenses.values, title='Average Daily Spending by Weekday', labels={'x': 'Day', 'y': 'Average Amount (₹)'})
                st.plotly_chart(fig)
            total_monthly = df_expenses.groupby(df_expenses['date'].dt.strftime('%Y-%m'))['amount'].sum()
            avg_monthly, std_monthly = total_monthly.mean(), total_monthly.std()
            insights = []
            if total_monthly.iloc[-1] > avg_monthly + std_monthly:
                insights.append("Your spending this month is higher than usual.")
            elif total_monthly.iloc[-1] < avg_monthly - std_monthly:
                insights.append("Your spending this month is lower than usual.")
            for category in df_expenses['category'].unique():
                cat_data = df_expenses[df_expenses['category'] == category]
                cat_monthly = cat_data.groupby(cat_data['date'].dt.strftime('%Y-%m'))['amount'].sum()
                if len(cat_monthly) > 1 and cat_monthly.iloc[-1] > cat_monthly.iloc[:-1].mean() * 1.2:
                    insights.append(f"{category} expenses have increased significantly.")
            for insight in insights:
                st.info(insight)
    with tab2:
        st.markdown("### Investment Performance Analysis")
        investment_data = pd.DataFrame({
            'Date': pd.date_range(start='2023-01-01', periods=12, freq='ME'),
            'Equity': np.random.normal(12000, 2000, 12).cumsum(),
            'Debt': np.random.normal(8000, 1000, 12).cumsum(),
            'Gold': np.random.normal(5000, 500, 12).cumsum()
        })
        fig = px.line(investment_data, x='Date', y=['Equity', 'Debt', 'Gold'], title='Portfolio Performance Over Time')
        st.plotly_chart(fig)
        current_allocation = {'Asset': ['Equity', 'Debt', 'Gold'], 'Amount': [investment_data['Equity'].iloc[-1], investment_data['Debt'].iloc[-1], investment_data['Gold'].iloc[-1]]}
        df_allocation = pd.DataFrame(current_allocation)
        fig = px.pie(df_allocation, values='Amount', names='Asset', title='Current Asset Allocation')
        st.plotly_chart(fig)
        st.markdown("### Performance Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_value = df_allocation['Amount'].sum()
            st.metric("Total Portfolio Value", f"₹{total_value:,.2f}")
        with col2:
            investment_sum = sum([investment_data[col].iloc[0] for col in ['Equity', 'Debt', 'Gold']])
            returns = (total_value - investment_sum) / investment_sum * 100 if investment_sum > 0 else 0
            st.metric("Total Returns", f"{returns:.1f}%")
        with col3:
            monthly_return = returns / 12
            st.metric("Average Monthly Return", f"{monthly_return:.1f}%")
    with tab3:
        st.markdown("### Financial Health Score")
        col1, col2 = st.columns(2)
        with col1:
            monthly_income = st.number_input("Monthly Income (₹)", min_value=0.0, value=None, key="health_income")
            monthly_expenses = st.number_input("Monthly Expenses (₹)", min_value=0.0, value=None, key="health_expenses")
            emergency_fund = st.number_input("Emergency Fund (₹)", min_value=0.0, value=None, key="health_fund")
        with col2:
            total_investments = st.number_input("Total Investments (₹)", min_value=0.0, value=None, key="health_invest")
            total_debt = st.number_input("Total Debt (₹)", min_value=0.0, value=None, key="health_debt")
        if all([monthly_income, monthly_expenses, emergency_fund, total_investments, total_debt is not None]):
            savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100 if monthly_income > 0 else 0
            emergency_fund_months = emergency_fund / monthly_expenses if monthly_expenses > 0 else 0
            debt_to_income = (total_debt / (monthly_income * 12)) * 100 if monthly_income > 0 else 0
            investment_ratio = (total_investments / (monthly_income * 12)) * 100 if monthly_income > 0 else 0
            score = min(25, savings_rate / 2) + min(25, emergency_fund_months * 12.5) + min(25, 25 * (1 - debt_to_income/100)) + min(25, investment_ratio / 4)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Financial Health Score"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': COLORS['primary']}, 'steps': [{'range': [0, 33], 'color': "lightgray"}, {'range': [33, 66], 'color': "gray"}, {'range': [66, 100], 'color': COLORS['accent']}]}
            ))
            st.plotly_chart(fig)
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
            st.markdown("### Personalized Recommendations")
            recommendations = []
            if savings_rate < 20:
                recommendations.append("Create a budget to increase your savings rate to at least 20%")
            if emergency_fund_months < 6:
                recommendations.append(f"Build emergency fund by saving ₹{(6*monthly_expenses - emergency_fund):,.2f} more")
            if debt_to_income >= 30:
                recommendations.append("Focus on debt reduction before increasing investments")
            if investment_ratio < 50:
                recommendations.append("Consider increasing your investment allocation")
            for rec in recommendations:
                st.markdown(f"- {rec}")

# ============ DEBT MANAGEMENT ============
def debt_management():
    st.markdown("<h1 style='text-align: center;'>Debt Management</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Loan Entry", "Debt Strategy", "Debt Payoff Calculator"])
    with tab1:
        st.markdown("### Add New Loan")
        with st.form("new_loan"):
            loan_type_options = [f"<i class='bi bi-{loan_types[lt]['icon']}'></i> {lt}" for lt in loan_types.keys()]
            loan_type = st.selectbox("Loan Type", loan_type_options, format_func=lambda x: x, key="loan_type")
            loan_type = loan_type.split('> ')[1]  # Extract the loan type name
            if loan_type == "Other":
                loan_type = st.text_input("Specify Loan Type", key="other_loan_type")
            principal = st.number_input("Principal Amount (₹)", min_value=0.0, step=1000.0, value=None, key="loan_principal")
            interest_rate = st.slider("Interest Rate (%)", min_value=1.0, max_value=100.0, value=float(loan_types[loan_type]["interest_rate"]), step=0.1, key="loan_interest")
            tenure_months = st.number_input("Tenure (Months)", min_value=1, step=1, value=None, key="loan_tenure")
            start_date = st.date_input("Start Date", value=datetime.now(), key="loan_start_date")
            monthly_payment = st.number_input("Monthly Payment (₹)", min_value=0.0, step=100.0, value=None, key="loan_monthly")
            description = st.text_area("Description", key="loan_description")
            submitted = st.form_submit_button("Add Loan")
            if submitted and all([principal, tenure_months, monthly_payment is not None]):
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("INSERT INTO loans (user_id, loan_type, principal, interest_rate, tenure_months, start_date, outstanding_balance, monthly_payment, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (st.session_state.user_id, loan_type, principal, interest_rate, tenure_months, start_date.strftime("%Y-%m-%d"), principal, monthly_payment, description))
                conn.commit()
                conn.close()
                st.success("Loan added successfully!")
        st.markdown("### Existing Loans")
        conn = sqlite3.connect('finance_tracker.db')
        df_loans = pd.read_sql_query("SELECT * FROM loans WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        if not df_loans.empty:
            edited_df = st.data_editor(df_loans, hide_index=True, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, key="loan_table")
            if st.button("Delete Selected", key="delete_selected"):
                selected_ids = edited_df[edited_df['Select']]['id'].tolist()
                if selected_ids:
                    st.session_state.confirm_delete = True
                else:
                    st.warning("No loans selected for deletion.")
            if st.session_state.confirm_delete:
                st.warning("Are you sure you want to delete the selected loans?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, delete", key="confirm_yes"):
                        conn = sqlite3.connect('finance_tracker.db')
                        c = conn.cursor()
                        c.execute(f"DELETE FROM loans WHERE id IN ({','.join('?'*len(selected_ids))})", selected_ids)
                        conn.commit()
                        conn.close()
                        st.success("Selected loans deleted!")
                        st.session_state.confirm_delete = False
                        st.rerun()
                with col2:
                    if st.button("Cancel", key="confirm_cancel"):
                        st.session_state.confirm_delete = False
                        st.rerun()
            csv = df_loans.to_csv(index=False)
            st.download_button(label="Download Loans as CSV", data=csv, file_name="loans.csv", mime="text/csv", key="download_loans")
        else:
            st.info("No loans added yet.")
    with tab2:
        st.markdown("### Debt Strategy")
        if not df_loans.empty:
            total_debt = df_loans['outstanding_balance'].sum()
            total_monthly_payment = df_loans['monthly_payment'].sum()
            st.metric("Total Outstanding Debt", f"₹{total_debt:,.2f}")
            st.metric("Total Monthly Payment", f"₹{total_monthly_payment:,.2f}")
            st.markdown("#### Debt Snowball vs Avalanche")
            snowball = df_loans.sort_values('outstanding_balance').iloc[0]
            avalanche = df_loans.sort_values('interest_rate', ascending=False).iloc[0]
            st.info(f"**Snowball Method**: Pay off {snowball['loan_type']} first (Lowest Balance: ₹{snowball['outstanding_balance']:,.2f})")
            st.info(f"**Avalanche Method**: Pay off {avalanche['loan_type']} first (Highest Interest: {avalanche['interest_rate']:.2f}%)")
            st.markdown("#### Debt-to-Income Ratio")
            monthly_income = st.number_input("Monthly Income (₹)", min_value=0.0, value=None, key="dti_income")
            if monthly_income:
                dti = (total_monthly_payment / monthly_income) * 100
                st.metric("Debt-to-Income Ratio", f"{dti:.2f}%", help="Ideal: Below 36%")
                if dti > 36:
                    st.warning("High DTI - Consider reducing debt or increasing income.")
        else:
            st.info("No loans to analyze.")
    with tab3:
        st.markdown("### Debt Payoff Calculator")
        total_debt = st.number_input("Total Debt (₹)", min_value=0.0, value=None, key="calc_total_debt")
        avg_interest_rate = st.number_input("Average Interest Rate (%)", min_value=0.0, value=None, key="calc_interest")
        monthly_payment = st.number_input("Monthly Payment (₹)", min_value=0.0, value=None, key="calc_monthly")
        if st.button("Calculate Payoff Time", key="calc_payoff") and all([total_debt, avg_interest_rate, monthly_payment]):
            monthly_rate = avg_interest_rate / (12 * 100)
            months = npf.nper(monthly_rate, -monthly_payment, total_debt) if monthly_payment > total_debt * monthly_rate else float('inf')
            if months != float('inf'):
                years = months / 12
                st.success(f"Payoff Time: {months:.1f} months (~{years:.1f} years)")
                total_interest = (monthly_payment * months) - total_debt
                st.info(f"Total Interest Paid: ₹{total_interest:,.2f}")
            else:
                st.error("Monthly payment too low to cover interest.")

# ============ SETTINGS PAGE ============
def settings_page():
    st.markdown("<h1 style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)
    st.markdown("### Profile Settings")
    col1, col2 = st.columns(2)
    with col1:
        conn = sqlite3.connect('finance_tracker.db')
        c = conn.cursor()
        c.execute("SELECT username, email FROM users WHERE id = ?", (st.session_state.user_id,))
        user_info = c.fetchone()
        conn.close()
        if user_info:
            username, email = user_info
            st.text_input("Username", value=username, disabled=True, key="profile_username")
            st.text_input("Email", value=email, disabled=True, key="profile_email")
    with col2:
        st.markdown("### Theme Settings")
        dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
    st.markdown("### Notification Settings")
    st.checkbox("Email Alerts for Unusual Expenses", value=True, key="notif_expenses")
    st.checkbox("Monthly Report", value=True, key="notif_report")
    st.checkbox("Investment Alerts", value=True, key="notif_invest")
    st.markdown("### Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Data", key="export_data"):
            conn = sqlite3.connect('finance_tracker.db')
            df_expenses = pd.read_sql_query("SELECT date, amount, category, description FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
            csv = df_expenses.to_csv(index=False)
            st.download_button(label="Download CSV", data=csv, file_name="my_financial_data.csv", mime="text/csv", key="download_csv")
            conn.close()
    with col2:
        if st.button("Delete Account", key="delete_account"):
            st.warning("This will permanently delete your account and all data!")
            if st.button("Confirm Delete", key="confirm_delete_account"):
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("DELETE FROM expenses WHERE user_id = ?", (st.session_state.user_id,))
                c.execute("DELETE FROM goals WHERE user_id = ?", (st.session_state.user_id,))
                c.execute("DELETE FROM loans WHERE user_id = ?", (st.session_state.user_id,))
                c.execute("DELETE FROM users WHERE id = ?", (st.session_state.user_id,))
                conn.commit()
                conn.close()
                st.session_state.clear()
                st.success("Account deleted successfully!")
                st.rerun()

# ============ MAIN APP ============
def main():
    # Add Bootstrap Icons CDN
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.2/font/bootstrap-icons.css">', unsafe_allow_html=True)
    handle_theme_from_url()
    st.markdown(f"""
    <div class="header-container" style="top: 30px;">
        <div style="position: relative; z-index: 9999;">{theme_toggle()}</div>
        {currency_switcher()}
    </div>
    """, unsafe_allow_html=True)
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
        elif selected == "Debt Management":
            debt_management()
        elif selected == "Settings":
            settings_page()
        st.markdown("""
        <div class='footer'>
            Developed by Muhammed Adnan | Contact: kladnan321@gmail.com
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()