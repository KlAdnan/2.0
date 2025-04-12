import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from datetime import datetime
import sqlite3
import hashlib

# Check for required packages
try:
    from streamlit_option_menu import option_menu
except ImportError:
    st.error("Please install streamlit-option-menu via `pip install streamlit-option-menu`")
    st.stop()

# Page Config
st.set_page_config(
    page_title="AI Financial Planner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session State Initialization
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'loans' not in st.session_state:
    st.session_state.loans = []

# Loan Types with Icons and Default Interest Rates
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
    "Government-Backed Loan": {"icon": "bank", "interest_rate": 6}
}

# Theme CSS
def load_css():
    css = """
    <style>
    @import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.2/font/bootstrap-icons.css");
    .stApp {
        background-color: %s;
        color: %s;
    }
    h1, h2, h3 { color: %s; animation: slideIn 0.5s ease-in-out; }
    .stButton>button {
        background-color: #28a745;
        color: white;
        border-radius: 5px;
        transition: transform 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #218838;
        transform: scale(1.05);
    }
    .stExpander {
        border: 1px solid #ccc;
        border-radius: 5px;
        animation: fadeIn 0.5s ease-in-out;
    }
    .stExpander:hover {
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .theme-toggle {
        position: fixed;
        top: 60px;
        right: 10px;
        z-index: 1000;
        background-color: %s;
        padding: 5px 10px;
        border-radius: 20px;
        cursor: pointer;
        transition: transform 0.2s ease;
    }
    .theme-toggle:hover {
        transform: scale(1.05);
    }
    .theme-toggle i { font-size: 20px; margin-right: 5px; }
    .stDataFrame { animation: fadeIn 0.5s ease-in-out; }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    </style>
    """
    if st.session_state.dark_mode:
        return css % ('#1E1E1E', '#E0E0E0', '#C6A969', '#2D2D2D')
    else:
        return css % ('#F7F7F7', '#1E3932', '#00704A', 'white')

# Theme Toggle
def theme_toggle():
    icon = "bi-moon" if st.session_state.dark_mode else "bi-sun"
    label = "Switch to Light Mode" if st.session_state.dark_mode else "Switch to Dark Mode"
    toggle_html = f"""
    <div class="theme-toggle" onclick="document.getElementById('theme_switch').click()">
        <i class="bi {icon}"></i>{label}
    </div>
    """
    if st.button("Toggle Theme", key="theme_switch", help="Switch between light and dark mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    return toggle_html

# Database Setup
def init_db():
    with sqlite3.connect('finance_tracker.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS expenses
                     (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, category TEXT, description TEXT, needs REAL, wants REAL, investments REAL, savings REAL, total REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS goals
                     (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL, target_date TEXT)''')
        conn.commit()

init_db()

# Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email, password):
    with sqlite3.connect('finance_tracker.db') as conn:
        c = conn.cursor()
        hashed_password = hash_password(password)
        c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, hashed_password))
        result = c.fetchone()
        if result:
            st.session_state.user_id = result[0]
            st.session_state.authenticated = True
            return True
    return False

def register_user(username, email, password):
    with sqlite3.connect('finance_tracker.db') as conn:
        c = conn.cursor()
        try:
            hashed_password = hash_password(password)
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
            conn.commit()
            return True, "Registration successful! Please login."
        except sqlite3.IntegrityError:
            return False, "Email or username already exists!"

def auth_page():
    st.title("AI Financial Planner")
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
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Register"):
                if password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters!")
                else:
                    success, message = register_user(username, email, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# Navigation
def create_navigation():
    return option_menu(
        menu_title=None,
        options=["Dashboard", "Expenses", "Investments", "Debt Management"],
        icons=["house", "wallet", "graph-up", "credit-card"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "10px", "background-color": "#00704A"},
            "icon": {"color": "white", "font-size": "20px"},
            "nav-link": {"color": "white", "text-align": "center"},
            "nav-link-selected": {"background-color": "#C6A969"}
        }
    )

# Dashboard
def dashboard():
    st.markdown("<h1>Financial Dashboard</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Monthly Savings", "₹25,000")
    with col2:
        st.metric("Expenses", "₹45,000")

# Expense Tracker
def expense_tracker():
    st.markdown("<h1>Smart Expense Tracker</h1>", unsafe_allow_html=True)
    with st.expander("Add New Expense", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("Date", datetime.now())
            category = st.selectbox("Category", ["Needs", "Wants", "Investments", "Savings"])
        with col2:
            description = st.text_input("Description")
        with col3:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        if st.button("Add Expense"):
            if st.session_state.user_id:
                with sqlite3.connect('finance_tracker.db') as conn:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO expenses (user_id, date, category, description, needs, wants, investments, savings, total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (st.session_state.user_id, date.strftime("%Y-%m-%d"), category, description,
                         amount if category == "Needs" else 0,
                         amount if category == "Wants" else 0,
                         amount if category == "Investments" else 0,
                         amount if category == "Savings" else 0,
                         amount)
                    )
                    conn.commit()
                st.success("Expense added!")
            else:
                st.error("Please log in.")
    if st.session_state.user_id:
        with sqlite3.connect('finance_tracker.db') as conn:
            df = pd.read_sql_query("SELECT date, category, description, needs, wants, investments, savings, total FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        if not df.empty:
            st.markdown("<h2>Your Expenses</h2>", unsafe_allow_html=True)
            st.dataframe(df.style.format({
                "needs": "₹{:.2f}",
                "wants": "₹{:.2f}",
                "investments": "₹{:.2f}",
                "savings": "₹{:.2f}",
                "total": "₹{:.2f}"
            }))

# Investment Planner
def investment_planner():
    st.markdown("<h1>Investment Planner</h1>", unsafe_allow_html=True)
    with st.expander("Add New Goal", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Goal Name")
            target_amount = st.number_input("Target Amount (₹)", min_value=0.0)
        with col2:
            current_amount = st.number_input("Current Amount (₹)", min_value=0.0)
        with col3:
            target_date = st.date_input("Target Date")
        if st.button("Add Goal"):
            if st.session_state.user_id:
                with sqlite3.connect('finance_tracker.db') as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO goals (user_id, name, target_amount, current_amount, target_date) VALUES (?, ?, ?, ?, ?)",
                              (st.session_state.user_id, name, target_amount, current_amount, target_date.strftime("%Y-%m-%d")))
                    conn.commit()
                st.success("Goal added!")
    if st.session_state.user_id:
        with sqlite3.connect('finance_tracker.db') as conn:
            df = pd.read_sql_query("SELECT name, target_amount, current_amount, target_date FROM goals WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        if not df.empty:
            st.dataframe(df)

# Debt Management (Your Provided Code)
def debt_management():
    st.markdown("<h1>Debt Management</h1>", unsafe_allow_html=True)
    with st.expander("Add New Loan", expanded=True):
        loan_type = option_menu(
            "Select Loan Type:",
            options=list(loan_types.keys()),
            icons=[loan_types[lt]["icon"] for lt in loan_types],
            menu_icon="list",
            default_index=0,
            key="loan_type"
        )
        default_interest = loan_types[loan_type]["interest_rate"]
        col1, col2, col3 = st.columns(3)
        with col1:
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=1000, key="loan_amount")
        with col2:
            emi_amount = st.number_input("EMI Amount (₹)", min_value=0, step=100, key="emi_amount")
        with col3:
            amount_paid = st.number_input("Amount Paid (₹)", min_value=0, step=1000, key="amount_paid")
        col4, col5 = st.columns(2)
        with col4:
            tenure_years = st.number_input("Tenure Years", min_value=0, step=1, key="tenure_years")
        with col5:
            tenure_months = st.number_input("Tenure Months", min_value=0, max_value=11, step=1, key="tenure_months")
        interest_rate = st.slider(
            "Interest Rate (%)",
            1.0, 100.0,
            value=float(default_interest),
            step=0.1,
            key=f"interest_rate_{loan_type}"
        )
        if st.button("Submit"):
            if tenure_years > 0 and tenure_months > 0:
                tenure = f"{tenure_years} years {tenure_months} months"
            elif tenure_years > 0:
                tenure = f"{tenure_years} years"
            elif tenure_months > 0:
                tenure = f"{tenure_months} months"
            else:
                tenure = "0 months"
            st.session_state.loans.append({
                "Loan Type": loan_type,
                "Loan Amount": loan_amount,
                "EMI Amount": emi_amount,
                "Amount Paid": amount_paid,
                "Interest Rate": interest_rate,
                "Tenure": tenure
            })
            st.success("Loan details submitted successfully!")
    if st.session_state.loans:
        st.subheader("Entered Loans")
        df = pd.DataFrame(st.session_state.loans)
        st.dataframe(df.style.format({
            "Loan Amount": "₹{:.2f}",
            "EMI Amount": "₹{:.2f}",
            "Amount Paid": "₹{:.2f}",
            "Interest Rate": "{:.1f}%"
        }))
        st.subheader("Interest Rate Distribution")
        fig, ax = plt.subplots()
        ax.pie(df["Interest Rate"], labels=df["Loan Type"], autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax.axis("equal")
        st.pyplot(fig)

# Main App
def main():
    st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.2/font/bootstrap-icons.css">', unsafe_allow_html=True)
    st.markdown(load_css(), unsafe_allow_html=True)
    st.markdown(theme_toggle(), unsafe_allow_html=True)
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
        elif selected == "Debt Management":
            debt_management()

if __name__ == "__main__":
    main()