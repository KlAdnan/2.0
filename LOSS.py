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
from reportlab.lib import colors
import io
import os

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
if 'loans' not in st.session_state:
    st.session_state.loans = []
if 'currency' not in st.session_state:
    st.session_state.currency = "INR"

# ============ THEME SWITCHER ============
def theme_switcher():
    themes = {
        "Light": "light",
        "Dark": "dark"
    }
    selected_theme = st.sidebar.selectbox("Theme", list(themes.keys()))
    st.session_state.theme = themes[selected_theme]
    return selected_theme

# ============ CURRENCY SWITCHER ============
def currency_switcher():
    currencies = {
        "INR": "₹",
        "USD": "$",
        "AED": "AED",
        "SAR": "SAR",
        "CAD": "CAD",
        "QAR": "QAR",
        "CNY": "CNY"
    }
    selected_currency = st.sidebar.selectbox("Currency", list(currencies.keys()))
    st.session_state.currency = selected_currency
    return currencies[selected_currency]

# ============ LOAD CSS ============
def load_css():
    base_css = """
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css">
    <style>
    .stApp {
        transition: all 0.3s ease;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Arial', sans-serif;
        transition: color 0.3s ease;
    }
    .stButton>button {
        border-radius: 0.5rem;
        padding: 10px 20px;
        transition: transform 0.2s ease, background-color 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    .stExpander {
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stExpander:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }
    i.bi {
        font-size: 1.2em;
        margin-right: 5px;
        vertical-align: middle;
    }
    </style>
    """
    
    light_theme = base_css + """
    <style>
    .stApp {
        background: linear-gradient(135deg, #F7F7F7, #E0E0E0);
        color: #1E3932;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #00704A;
    }
    .stButton>button {
        background-color: #00704A;
        color: white;
    }
    .stButton>button:hover {
        background-color: #C6A969;
    }
    </style>
    """
    
    dark_theme = base_css + """
    <style>
    .stApp {
        background: linear-gradient(135deg, #1E1E1E, #2D2D2D);
        color: #E0E0E0;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #C6A969;
    }
    .stButton>button {
        background-color: #00704A;
        color: white;
    }
    .stButton>button:hover {
        background-color: #C6A969;
    }
    i.bi {
        color: #E0E0E0;
    }
    </style>
    """
    
    if st.session_state.theme == "dark":
        return dark_theme
    else:
        return light_theme

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, amount REAL, category TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans
                 (id INTEGER PRIMARY KEY, user_id INTEGER, loan_type TEXT, principal REAL, interest_rate REAL, 
                  tenure INTEGER, start_date TEXT, outstanding_balance REAL, monthly_payment REAL, 
                  description TEXT, amount_paid REAL DEFAULT 0.0, emi_amount REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL, 
                  target_date TEXT, priority TEXT)''')
    conn.commit()
    conn.close()

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
    st.markdown("<h1 class='fade-in' style='text-align: center;'>AI Financial Planner</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
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
            if st.form_submit_button("Register"):
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

# ============ NAVIGATION ============
def create_navigation():
    return option_menu(
        menu_title=None,
        options=["Dashboard", "Expenses", "Investments", "Analysis", "Debt Management", "Settings"],
        icons=["house", "wallet", "graph-up", "clipboard-data", "credit-card", "gear"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "10px", "background": "linear-gradient(90deg, #00704A, #004d35)"},
            "icon": {"color": "#FFFFFF", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "padding": "10px 20px",
                "color": "#FFFFFF",
                "position": "relative",
                "transition": "color 0.3s ease"
            },
            "nav-link-selected": {"background-color": "#C6A969", "color": "#1E3932"},
        }
    )

# ============ DASHBOARD ============
def dashboard():
    st.markdown("<h1 class='fade-in' style='text-align: center;'>Financial Dashboard</h1>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Monthly Savings", value=f"{st.session_state.currency} 25,000", delta="↑ 8%")
    with col2:
        st.metric(label="Investments", value=f"{st.session_state.currency} 1,50,000", delta="↑ 12%")
    with col3:
        st.metric(label="Expenses", value=f"{st.session_state.currency} 45,000", delta="5%")
    with col4:
        st.metric(label="Net Worth", value=f"{st.session_state.currency} 5,00,000", delta="↑ 15%")
    
    st.markdown("### Market Overview")
    try:
        # Indian Market
        indian_symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'WIPRO.NS']
        indian_data = pd.DataFrame()
        for symbol in indian_symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1d')
            if not hist.empty:
                indian_data.loc[symbol, 'Price'] = hist['Close'].iloc[-1]
                indian_data.loc[symbol, 'Change'] = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                indian_data.loc[symbol, 'Change %'] = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
        st.markdown("**Indian Market**")
        st.dataframe(indian_data.style.format({'Price': f'{st.session_state.currency}{{:,.2f}}', 'Change': f'{st.session_state.currency}{{:,.2f}}', 'Change %': '{:,.2f}%'}))
        
        # US Market
        us_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        us_data = pd.DataFrame()
        for symbol in us_symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1d')
            if not hist.empty:
                us_data.loc[symbol, 'Price'] = hist['Close'].iloc[-1]
                us_data.loc[symbol, 'Change'] = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
                us_data.loc[symbol, 'Change %'] = ((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
        st.markdown("**US Market**")
        st.dataframe(us_data.style.format({'Price': f'{st.session_state.currency}{{:,.2f}}', 'Change': f'{st.session_state.currency}{{:,.2f}}', 'Change %': '{:,.2f}%'}))
        
        st.markdown("### Market Trends (Last Month)")
        fig = go.Figure()
        for symbol in indian_symbols + us_symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1mo')
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name=symbol, mode='lines'))
        fig.update_layout(title='Stock Performance', xaxis_title='Date', yaxis_title='Price', height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Unable to fetch market data. Please check your internet connection or try again later.")

# ============ EXPENSE TRACKER ============
def expense_tracker():
    st.markdown("<h1 class='fade-in' style='text-align: center;'>Expense Tracker</h1>", unsafe_allow_html=True)
    with st.expander("Add New Expense", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            expense_date = st.date_input("Date", datetime.now())
            expense_amount = st.number_input("Amount", min_value=0.0, step=100.0)
        with col2:
            default_categories = ["Needs", "Wants", "Investment", "Bills", "Entertainment", "Health", "Other"]
            expense_category = st.selectbox("Category", default_categories)
            if expense_category == "Other":
                expense_category = st.text_input("Specify Category")
        with col3:
            expense_description = st.text_area("Description", height=100)
        if st.button("Add Expense"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("""INSERT INTO expenses (user_id, date, amount, category, description) VALUES (?, ?, ?, ?, ?)""",
                         (st.session_state.user_id, expense_date.strftime("%Y-%m-%d"), expense_amount, expense_category, expense_description))
                conn.commit()
                conn.close()
                st.success("Expense added successfully!")
            else:
                st.error("User not authenticated. Please log in.")
    
    if st.session_state.user_id:
        conn = sqlite3.connect('finance_tracker.db')
        df_expenses = pd.read_sql_query("""SELECT date, amount, category, description FROM expenses WHERE user_id = ?""", conn, params=(st.session_state.user_id,))
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
            fig = px.pie(df_expenses, values="amount", names="category", title="Expense Distribution")
            st.plotly_chart(fig)
            df_expenses["date"] = pd.to_datetime(df_expenses["date"])
            daily_expenses = df_expenses.groupby("date")["amount"].sum().reset_index()
            fig = px.line(daily_expenses, x="date", y="amount", title="Daily Expense Trend", labels={"amount": f"Amount ({st.session_state.currency})", "date": "Date"})
            st.plotly_chart(fig)
        else:
            st.info("No expenses added yet.")
    else:
        st.error("User not authenticated. Please log in.")

# ============ INVESTMENT PLANNER ============
def investment_planner():
    st.markdown("<h1 class='fade-in' style='text-align: center;'>Investment Planner</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Investment Calculator", "Portfolio Allocation", "Goal Tracker", "Retirement Planning", "SWP Calculator"])
    
    with tab1:
        st.markdown("### Investment Calculator")
        calc_type = st.radio("Select Calculator Type", ["SIP", "Lump Sum"])
        if calc_type == "SIP":
            initial_investment = 0
            monthly_investment = st.number_input("Monthly Investment", min_value=100, value=5000)
        else:
            initial_investment = st.number_input("Lump Sum Investment", min_value=1000, value=50000)
            monthly_investment = 0
        
        period_unit = st.selectbox("Investment Period Unit", ["Years", "Months"])
        if period_unit == "Years":
            years = st.number_input("Investment Period (Years)", min_value=1, max_value=40, value=10)
            months = years * 12
        else:
            months = st.number_input("Investment Period (Months)", min_value=1, value=120)
            years = months / 12
        
        expected_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=30.0, value=12.0)
        inflation_rate = st.slider("Assumed Inflation Rate (%)", 2.0, 10.0, 4.5)
        holding_period = st.selectbox("Holding Period", ["Less than 12 months", "More than 12 months"])
        
        # Calculations aligned with Groww
        monthly_rate = expected_return / 1200  # Monthly rate from annual percentage
        if calc_type == "SIP":
            future_value = monthly_investment * ((pow(1 + monthly_rate, months) - 1) / monthly_rate) * (1 + monthly_rate)
            total_investment = monthly_investment * months
        else:
            future_value = initial_investment * pow(1 + monthly_rate, months)
            total_investment = initial_investment
        
        # Inflation adjustment
        inflation_adjusted_value = future_value / pow(1 + inflation_rate / 100, years)
        
        # Tax calculation
        total_returns = future_value - total_investment
        if holding_period == "Less than 12 months":
            tax_rate = 0.20  # Short-term capital gains tax
            tax_amount = total_returns * tax_rate
        else:
            taxable_gain = max(0, total_returns - 125000)  # Long-term gains above ₹1.25 lakh
            tax_rate = 0.125  # Long-term capital gains tax
            tax_amount = taxable_gain * tax_rate
        after_tax_returns = total_returns - tax_amount
        after_tax_future_value = total_investment + after_tax_returns
        
        st.markdown("### Investment Projections")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Invested Amount", f"{st.session_state.currency} {total_investment:,.2f}")
        col2.metric("Future Value", f"{st.session_state.currency} {future_value:,.2f}")
        col3.metric("Inflation-Adjusted Value", f"{st.session_state.currency} {inflation_adjusted_value:,.2f}")
        col4.metric("After-Tax Future Value", f"{st.session_state.currency} {after_tax_future_value:,.2f}")
        
        st.markdown("### Growth Projection")
        period_range = np.arange(0, years + 1) if period_unit == "Years" else np.arange(0, months + 1)
        x_label = "Years" if period_unit == "Years" else "Months"
        growth_values = [monthly_investment * ((pow(1 + monthly_rate, p) - 1) / monthly_rate) * (1 + monthly_rate) if calc_type == "SIP" else initial_investment * pow(1 + monthly_rate, p) for p in period_range]
        fig = go.Figure(go.Scatter(x=period_range, y=growth_values, mode='lines', name='Growth'))
        fig.update_layout(title=f'{calc_type} Growth', xaxis_title=x_label, yaxis_title=f'Amount ({st.session_state.currency})', height=400)
        st.plotly_chart(fig)

    with tab2:
        st.markdown("### Portfolio Allocation")
        age = st.number_input("Your Age", min_value=18, max_value=100, value=30)
        risk_profile = st.selectbox("Risk Profile", ["Conservative", "Moderate", "Aggressive"])
        equity_percent = max(20, min(80, 100 - age))
        if risk_profile == "Conservative":
            equity_percent -= 10
        elif risk_profile == "Aggressive":
            equity_percent += 10
        debt_percent = 100 - equity_percent
        large_cap, mid_cap, small_cap = equity_percent * 0.60, equity_percent * 0.25, equity_percent * 0.15
        
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(data=[go.Pie(labels=['Equity', 'Debt'], values=[equity_percent, debt_percent], hole=.3)])
            fig.update_layout(title="Asset Allocation")
            st.plotly_chart(fig)
        with col2:
            fig = go.Figure(data=[go.Pie(labels=['Large Cap', 'Mid Cap', 'Small Cap'], values=[large_cap, mid_cap, small_cap], hole=.3)])
            fig.update_layout(title="Equity Breakdown")
            st.plotly_chart(fig)
        
        st.markdown(f"**Recommended Allocation:** Equity: {equity_percent:.1f}%, Debt: {debt_percent:.1f}%\nEquity Breakdown: Large Cap: {large_cap:.1f}%, Mid Cap: {mid_cap:.1f}%, Small Cap: {small_cap:.1f}%")

    with tab3:
        st.markdown("### Goal Tracker")
        with st.form("new_goal"):
            goal_name = st.text_input("Goal Name")
            goal_amount = st.number_input("Target Amount", min_value=0)
            goal_date = st.date_input("Target Date")
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            current_amount = st.number_input("Current Amount", min_value=0)
            if st.form_submit_button("Add Goal"):
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
            for _, goal in df_goals.iterrows():
                progress = (goal['current_amount'] / goal['target_amount']) * 100
                st.markdown(f"<h4>{goal['name']} ({goal['priority']})</h4>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.progress(progress / 100)
                    st.markdown(f"Progress: {progress:.1f}%")
                with col2:
                    st.markdown(f"Target: {st.session_state.currency} {goal['target_amount']:,.2f}\nCurrent: {st.session_state.currency} {goal['current_amount']:,.2f}\nDate: {goal['target_date']}")
                target_date = datetime.strptime(goal['target_date'], "%Y-%m-%d")
                months_left = max(1, (target_date - datetime.now()).days / 30)
                monthly_needed = (goal['target_amount'] - goal['current_amount']) / months_left
                st.info(f"Save {st.session_state.currency} {monthly_needed:,.2f}/month to reach goal")

    with tab4:
        st.markdown("### Retirement Planning")
        current_age = st.number_input("Current Age", min_value=18, max_value=100, value=30)
        retirement_age = st.number_input("Retirement Age", min_value=current_age, max_value=100, value=60)
        life_expectancy = st.number_input("Life Expectancy", min_value=retirement_age, max_value=120, value=85)
        monthly_expenses = st.number_input("Expected Monthly Expenses Post-Retirement", min_value=0, value=50000)
        expected_return = st.number_input("Expected Annual Return Post-Retirement (%)", min_value=1.0, max_value=15.0, value=7.0)
        inflation_rate = st.slider("Assumed Inflation Rate (%)", 2.0, 10.0, 4.5)
        
        years_to_retire = retirement_age - current_age
        retirement_years = life_expectancy - retirement_age
        
        # Adjust expenses for inflation
        future_monthly_expenses = monthly_expenses * pow(1 + inflation_rate / 100, years_to_retire)
        
        # Calculate required corpus
        monthly_rate = expected_return / 1200
        corpus_needed = future_monthly_expenses * (1 - pow(1 + monthly_rate, -retirement_years * 12)) / monthly_rate
        
        st.markdown(f"**Required Retirement Corpus:** {st.session_state.currency} {corpus_needed:,.2f}")
        
        # Calculate monthly investment needed
        if years_to_retire > 0:
            pre_retirement_return = st.number_input("Expected Annual Return Pre-Retirement (%)", min_value=1.0, max_value=20.0, value=12.0)
            pre_monthly_rate = pre_retirement_return / 1200
            monthly_investment_needed = corpus_needed / (((pow(1 + pre_monthly_rate, years_to_retire * 12) - 1) / pre_monthly_rate) * (1 + pre_monthly_rate))
            st.markdown(f"**Monthly Investment Needed (SIP):** {st.session_state.currency} {monthly_investment_needed:,.2f}")
        else:
            st.markdown("You are already at retirement age.")

    with tab5:
        st.markdown("### SWP Calculator")
        corpus = st.number_input("Corpus Amount", min_value=0, value=1000000)
        withdrawal_rate = st.number_input("Annual Withdrawal Rate (%)", min_value=1.0, max_value=20.0, value=4.0)
        expected_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=15.0, value=7.0)
        withdrawal_period = st.number_input("Withdrawal Period (Years)", min_value=1, max_value=50, value=20)
        
        annual_withdrawal = corpus * (withdrawal_rate / 100)
        monthly_withdrawal = annual_withdrawal / 12
        
        # Calculate future value after withdrawals
        monthly_rate = expected_return / 1200
        future_value = corpus * pow(1 + monthly_rate, withdrawal_period * 12) - monthly_withdrawal * ((pow(1 + monthly_rate, withdrawal_period * 12) - 1) / monthly_rate)
        
        st.markdown(f"**Monthly Withdrawal:** {st.session_state.currency} {monthly_withdrawal:,.2f}")
        st.markdown(f"**Corpus After {withdrawal_period} Years:** {st.session_state.currency} {future_value:,.2f}")
        
        # Plot SWP depletion
        months = withdrawal_period * 12
        corpus_values = [corpus]
        for i in range(1, months + 1):
            new_corpus = corpus_values[-1] * (1 + monthly_rate) - monthly_withdrawal
            corpus_values.append(max(0, new_corpus))
        fig = go.Figure(go.Scatter(x=list(range(months + 1)), y=corpus_values, mode='lines', name='Corpus'))
        fig.update_layout(title='SWP Corpus Depletion', xaxis_title='Months', yaxis_title=f'Corpus ({st.session_state.currency})')
        st.plotly_chart(fig)

# ============ ADVANCED ANALYTICS ============
def advanced_analytics():
    st.markdown("<h1 class='fade-in' style='text-align: center;'>Advanced Analytics</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Expense Analysis", "Investment Analysis", "Financial Health"])
    
    with tab1:
        conn = sqlite3.connect('finance_tracker.db')
        df_expenses = pd.read_sql_query("SELECT date, amount, category FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        if not df_expenses.empty:
            df_expenses['date'] = pd.to_datetime(df_expenses['date'])
            monthly_expenses = df_expenses.groupby(df_expenses['date'].dt.strftime('%Y-%m'))['amount'].sum()
            fig = px.line(monthly_expenses, x=monthly_expenses.index, y='amount', title='Monthly Expense Trend')
            st.plotly_chart(fig)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(df_expenses, values='amount', names='category', title='Expense Distribution')
                st.plotly_chart(fig)
            with col2:
                df_expenses['weekday'] = df_expenses['date'].dt.day_name()
                weekly_expenses = df_expenses.groupby('weekday')['amount'].mean()
                fig = px.bar(weekly_expenses, x=weekly_expenses.index, y=weekly_expenses.values, title='Avg Daily Spending by Weekday')
                st.plotly_chart(fig)
            
            total_monthly = monthly_expenses.mean()
            std_monthly = monthly_expenses.std()
            if monthly_expenses.iloc[-1] > total_monthly + std_monthly:
                st.info("📈 Spending this month is higher than usual.")
            elif monthly_expenses.iloc[-1] < total_monthly - std_monthly:
                st.info("📉 Spending this month is lower than usual.")
    
    with tab2:
        investment_data = pd.DataFrame({
            'Date': pd.date_range(start='2023-01-01', periods=12, freq='ME'),
            'Equity': np.random.normal(12000, 2000, 12).cumsum(),
            'Debt': np.random.normal(8000, 1000, 12).cumsum(),
            'Gold': np.random.normal(5000, 500, 12).cumsum()
        })
        fig = px.line(investment_data, x='Date', y=['Equity', 'Debt', 'Gold'], title='Portfolio Performance')
        st.plotly_chart(fig)
        
        current_allocation = {'Asset': ['Equity', 'Debt', 'Gold'], 'Amount': [investment_data[col].iloc[-1] for col in ['Equity', 'Debt', 'Gold']]}
        fig = px.pie(pd.DataFrame(current_allocation), values='Amount', names='Asset', title='Current Allocation')
        st.plotly_chart(fig)
        
        total_value = sum(current_allocation['Amount'])
        initial_value = investment_data.iloc[0][['Equity', 'Debt', 'Gold']].sum()
        returns = ((total_value - initial_value) / initial_value * 100) if initial_value > 0 else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Portfolio Value", f"{st.session_state.currency} {total_value:,.2f}")
        col2.metric("Total Returns", f"{returns:.1f}%")
        col3.metric("Monthly Return", f"{returns / 12:.1f}%")
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            monthly_income = st.number_input("Monthly Income", min_value=0, value=50000)
            monthly_expenses = st.number_input("Monthly Expenses", min_value=0, value=30000)
            emergency_fund = st.number_input("Emergency Fund", min_value=0, value=100000)
        with col2:
            total_investments = st.number_input("Total Investments", min_value=0, value=200000)
            total_debt = st.number_input("Total Debt", min_value=0, value=0)
        
        savings_rate = ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0
        emergency_months = emergency_fund / monthly_expenses if monthly_expenses > 0 else 0
        debt_to_income = (total_debt / (monthly_income * 12) * 100) if monthly_income > 0 else 0
        investment_ratio = (total_investments / (monthly_income * 12) * 100) if monthly_income > 0 else 0
        
        score = min(25, savings_rate / 2) + min(25, emergency_months * 12.5) + min(25, 25 * (1 - debt_to_income / 100)) + min(25, investment_ratio / 4)
        fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text': "Financial Health Score"}, gauge={'axis': {'range': [0, 100]}}))
        st.plotly_chart(fig)

# ============ DEBT MANAGEMENT ============
def sync_loans_with_db():
    if st.session_state.user_id:
        conn = sqlite3.connect('finance_tracker.db')
        loans_df = pd.read_sql_query("SELECT * FROM loans WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        st.session_state.loans = loans_df.to_dict('records')
    else:
        st.session_state.loans = []

def debt_management():
    st.markdown("<h1 class='fade-in' style='text-align: center;'>Debt Management</h1>", unsafe_allow_html=True)
    loan_types = {
        "Personal Loan": {"icon": "cash", "interest_rate": 15.0},
        "Credit Card Loan": {"icon": "credit-card", "interest_rate": 45.0},
        "Education Loan": {"icon": "book", "interest_rate": 10.0},
        "Home Loan": {"icon": "house", "interest_rate": 8.0},
        "Car Loan": {"icon": "car-front", "interest_rate": 9.0},
        "Business Loan": {"icon": "briefcase", "interest_rate": 12.0},
        "Gold Loan": {"icon": "gem", "interest_rate": 10.0},
        "Agricultural Loan": {"icon": "flower1", "interest_rate": 7.0},
        "Consumer Durable Loan": {"icon": "cart-fill", "interest_rate": 18.0},
        "Loan Against Property": {"icon": "building", "interest_rate": 11.0},
        "Loans Against Securities": {"icon": "shield-lock", "interest_rate": 9.0},
        "Payday Loan": {"icon": "calendar", "interest_rate": 50.0},
        "Two-Wheeler Loan": {"icon": "bicycle", "interest_rate": 12.0},
        "Government-Backed Loan": {"icon": "bank", "interest_rate": 6.0}
    }
    tab1, tab2 = st.tabs(["Loan Entry & Editing", "Debt Strategy"])
    
    with tab1:
        loan_type = st.selectbox("Loan Type:", [f"{loan_types[k]['icon']} {k}" for k in loan_types.keys()])
        selected_loan_type = loan_type.split(" ", 1)[1]  # Extract loan type without icon
        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input("Loan Amount", min_value=0.0, step=1000.0)
            emi_amount = st.number_input("EMI Amount", min_value=0.0, step=100.0)
        with col2:
            amount_paid = st.number_input("Amount Paid", min_value=0.0, step=1000.0)
            tenure = st.number_input("Tenure (Months)", min_value=0, step=1)
        interest_rate = st.slider("Interest Rate (%)", 1.0, 100.0, float(loan_types[selected_loan_type]["interest_rate"]))
        
        if st.button("Submit"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("INSERT INTO loans (user_id, loan_type, principal, emi_amount, amount_paid, interest_rate, tenure) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (st.session_state.user_id, selected_loan_type, loan_amount, emi_amount, amount_paid, interest_rate, tenure))
                conn.commit()
                conn.close()
                sync_loans_with_db()
                st.success("Loan added!")
        
        if st.session_state.loans:
            df = pd.DataFrame(st.session_state.loans)
            df["Outstanding"] = df["principal"] - df["amount_paid"]
            df["Loan Type"] = df["loan_type"].apply(lambda x: f'<i class="{loan_types[x]["icon"]}"></i> {x}')
            st.write(df[["Loan Type", "principal", "emi_amount", "amount_paid", "interest_rate", "tenure", "Outstanding"]].to_html(escape=False), unsafe_allow_html=True)
            
            loan_idx = st.selectbox("Edit/Delete Loan:", df.index, format_func=lambda x: f"{df.loc[x, 'Loan Type']} - {st.session_state.currency} {df.loc[x, 'principal']:,.2f}")
            with st.form(f"edit_loan_{loan_idx}"):
                current_type = df.loc[loan_idx, "loan_type"]
                new_type = st.selectbox("Loan Type", list(loan_types.keys()), index=list(loan_types.keys()).index(current_type))
                new_amount = st.number_input("Amount", value=float(df.loc[loan_idx, "principal"]))
                new_emi = st.number_input("EMI", value=float(df.loc[loan_idx, "emi_amount"]))
                new_paid = st.number_input("Paid", value=float(df.loc[loan_idx, "amount_paid"]))
                new_rate = st.number_input("Rate (%)", value=float(df.loc[loan_idx, "interest_rate"]))
                new_tenure = st.number_input("Tenure", value=int(df.loc[loan_idx, "tenure"]))
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update"):
                        conn = sqlite3.connect('finance_tracker.db')
                        c = conn.cursor()
                        c.execute("UPDATE loans SET loan_type=?, principal=?, emi_amount=?, amount_paid=?, interest_rate=?, tenure=? WHERE id=?",
                                 (new_type, new_amount, new_emi, new_paid, new_rate, new_tenure, df.loc[loan_idx, 'id']))
                        conn.commit()
                        conn.close()
                        sync_loans_with_db()
                        st.success("Loan updated!")
                with col2:
                    if st.form_submit_button("Delete"):
                        conn = sqlite3.connect('finance_tracker.db')
                        c = conn.cursor()
                        c.execute("DELETE FROM loans WHERE id=?", (df.loc[loan_idx, 'id'],))
                        conn.commit()
                        conn.close()
                        sync_loans_with_db()
                        st.success("Loan deleted!")
    
    with tab2:
        if st.session_state.loans:
            monthly_budget = st.number_input("Monthly Budget", min_value=0.0, value=10000.0)
            strategy = st.selectbox("Strategy", ["Debt Avalanche", "Debt Snowball"])
            df = pd.DataFrame(st.session_state.loans)
            df["Outstanding"] = df["principal"] - df["amount_paid"]
            df["Monthly Interest"] = (df["Outstanding"] * (df["interest_rate"] / 100)) / 12
            df = df.sort_values("interest_rate" if "Avalanche" in strategy else "Outstanding", ascending=False)
            
            total_budget = monthly_budget
            repayment_plan, months, interest_paid = [], 0, 0
            temp_df = df.copy()
            while temp_df["Outstanding"].sum() > 0 and months < 1200:
                month_budget = total_budget
                month_interest = temp_df["Monthly Interest"].sum()
                interest_paid += month_interest
                for idx, loan in temp_df.iterrows():
                    if month_budget >= loan["emi_amount"] and loan["Outstanding"] > 0:
                        payment = min(loan["emi_amount"], loan["Outstanding"] + loan["Monthly Interest"])
                        temp_df.at[idx, "Outstanding"] = max(0, loan["Outstanding"] + loan["Monthly Interest"] - payment)
                        month_budget -= payment
                temp_df["Monthly Interest"] = (temp_df["Outstanding"] * (temp_df["interest_rate"] / 100)) / 12
                repayment_plan.append({"Month": months, "Balance": temp_df["Outstanding"].sum()})
                months += 1
            
            if months < 1200:
                debt_free_date = datetime.now() + pd.offsets.MonthEnd(months)
                st.success(f"Debt-free by {debt_free_date.strftime('%B %Y')} ({months} months)")
                st.metric("Interest Paid", f"{st.session_state.currency} {interest_paid:,.2f}")
                fig = go.Figure(go.Scatter(x=[r["Month"] for r in repayment_plan], y=[r["Balance"] for r in repayment_plan], mode="lines"))
                fig.update_layout(title="Debt Repayment", xaxis_title="Months", yaxis_title=f"Balance ({st.session_state.currency})")
                st.plotly_chart(fig)

# ============ SETTINGS ============
def settings_page():
    st.markdown("<h1 class='fade-in' style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)
    if st.session_state.user_id:
        conn = sqlite3.connect('finance_tracker.db')
        c = conn.cursor()
        c.execute("SELECT username, email FROM users WHERE id = ?", (st.session_state.user_id,))
        user_data = c.fetchone()
        conn.close()
        
        with st.form("update_account"):
            new_username = st.text_input("Username", value=user_data[0])
            new_email = st.text_input("Email", value=user_data[1])
            if st.form_submit_button("Update"):
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", (new_username, new_email, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("Account updated!")
        
        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Change Password"):
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("SELECT password FROM users WHERE id = ?", (st.session_state.user_id,))
                if hash_password(current_password) == c.fetchone()[0]:
                    if new_password == confirm_password:
                        c.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(new_password), st.session_state.user_id))
                        conn.commit()
                        st.success("Password changed!")
                    else:
                        st.error("Passwords do not match!")
                else:
                    st.error("Incorrect current password!")
                conn.close()
    else:
        st.error("Please log in to access settings.")

# ============ MAIN APP ============
def main():
    init_db()
    theme_switcher()
    currency_switcher()
    st.markdown(f"""
        <div class="header-container fade-in">
            {load_css()}
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
        st.markdown("<div class='footer fade-in'>Developed by Your Name | Contact: your_email@example.com</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()