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
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import os
from streamlit.components.v1 import html

# Starbucks Premium Theme Colors
COLORS = {
    'primary': '#00704A',     # Starbucks Green
    'secondary': '#1E3932',   # Dark Green
    'accent': '#C6A969',      # Warm Gold
    'background': '#F5F5DC',  # Off-White
    'text_dark': '#1E3932',   # Dark Green Text
    'text_light': '#FFFFFF',  # White Text
    'success': '#006241',     # Deep Green
    'warning': '#CBA258',     # Light Gold
    'error': '#DC3545',       # Red
}

# Enhanced 3D Earth Animation with Interactive Features
earth_html = """
<div id="earth-container" style="width: 100%; height: 500px; position: relative; z-index: 1;"></div>
<div class="background-icons">
    <i class="icon icon-dollar bi bi-currency-dollar"></i>
    <i class="icon icon-chart bi bi-bar-chart"></i>
    <i class="icon icon-piggy bi bi-piggy-bank"></i>
    <i class="icon icon-wallet bi bi-wallet2"></i>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.134.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.134.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
    let scene, camera, renderer, earth, controls;
    let financialPoints = [];
    const financialData = [
        { name: "Loans", message: "Managing loans can be challenging. Our AI can help you strategize." },
        { name: "Investments", message: "Not sure where to invest? Let AI guide your decisions." },
        { name: "Expenses", message: "Track and categorize your expenses effortlessly." },
        { name: "Savings", message: "Set and achieve your savings goals with personalized plans." },
        { name: "Budgeting", message: "Create a budget that works for you with AI insights." }
    ];
    function init() {
        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        renderer = new THREE.WebGLRenderer({ alpha: true });
        renderer.setSize(window.innerWidth * 0.8, 500);
        document.getElementById('earth-container').appendChild(renderer.domElement);
        const geometry = new THREE.SphereGeometry(5, 32, 32);
        const texture = new THREE.TextureLoader().load('https://i.imgur.com/9C9e9xE.jpg');
        const material = new THREE.MeshBasicMaterial({ map: texture });
        earth = new THREE.Mesh(geometry, material);
        scene.add(earth);
        financialData.forEach((data, index) => {
            const pointGeometry = new THREE.SphereGeometry(0.2, 16, 16);
            const pointMaterial = new THREE.MeshBasicMaterial({ color: 0xffd700 });
            const point = new THREE.Mesh(pointGeometry, pointMaterial);
            const angle = (index / financialData.length) * Math.PI * 2;
            point.position.set(
                7 * Math.cos(angle),
                0,
                7 * Math.sin(angle)
            );
            point.userData = data;
            scene.add(point);
            financialPoints.push(point);
        });
        camera.position.z = 15;
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        const light = new THREE.AmbientLight(0x404040, 2);
        scene.add(light);
        const logoGeometry = new THREE.PlaneGeometry(2, 1);
        const logoTexture = new THREE.TextureLoader().load('https://via.placeholder.com/200x100.png?text=Your+Logo');
        const logoMaterial = new THREE.MeshBasicMaterial({ map: logoTexture, transparent: true });
        const logo = new THREE.Mesh(logoGeometry, logoMaterial);
        logo.position.set(0, 5, 0);
        scene.add(logo);
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        function onMouseClick(event) {
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(financialPoints);
            if (intersects.length > 0) {
                const data = intersects[0].object.userData;
                alert(`${data.name}: ${data.message}`);
            }
        }
        window.addEventListener('click', onMouseClick);
        function animate() {
            requestAnimationFrame(animate);
            earth.rotation.y += 0.002;
            financialPoints.forEach((point, index) => {
                const time = Date.now() * 0.001;
                const angle = (index / financialData.length) * Math.PI * 2 + time;
                point.position.set(
                    7 * Math.cos(angle),
                    0,
                    7 * Math.sin(angle)
                );
            });
            controls.update();
            renderer.render(scene, camera);
        }
        animate();
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth * 0.8, 500);
        });
    }
    init();
</script>
"""

# Page Config for Mobile-Friendly Layout
st.set_page_config(
    page_title="AI Financial Planner",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Session State
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'theme' not in st.session_state:
    st.session_state.theme = "starbucks"
if 'loans' not in st.session_state:
    st.session_state.loans = []

# Custom CSS for Starbucks Premium Theme and Mobile Optimization
st.markdown(f"""
    <style>
    .stApp {{
        background: url('https://i.imgur.com/9C9e9xE.jpg') no-repeat center center fixed;
        background-size: cover;
        color: {COLORS['text_dark']};
        font-family: 'Arial', sans-serif;
        padding: 10px;
    }}
    .main .block-container {{
        padding: 10px;
        max-width: 100%;
        margin: 0 auto;
    }}
    h1, h2, h3 {{
        color: {COLORS['primary']};
        text-align: center;
        font-weight: bold;
    }}
    .stButton>button {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_light']};
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 16px;
    }}
    .stButton>button:hover {{
        background-color: {COLORS['accent']};
        color: {COLORS['text_dark']};
    }}
    .stExpander {{
        border-radius: 10px;
        border: 2px solid {COLORS['secondary']};
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {COLORS['background']};
        border-radius: 10px;
        padding: 10px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_light']};
    }}
    .login-button {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        background-color: {COLORS['accent']};
        color: {COLORS['text_dark']};
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    .login-button:hover {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_light']};
        transform: scale(1.1);
    }}
    #login-modal {{
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.8);
    }}
    .login-content {{
        background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']});
        margin: 15% auto;
        padding: 20px;
        border-radius: 10px;
        width: 70%;
        color: {COLORS['text_light']};
        text-align: center;
    }}
    .login-content h1 {{
        color: {COLORS['accent']};
        margin-bottom: 20px;
    }}
    .login-content p {{
        font-size: 18px;
        margin-bottom: 20px;
    }}
    .background-icons {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    }}
    .icon {{
        position: absolute;
        opacity: 0.1;
        font-size: 50px;
        color: {COLORS['accent']};
    }}
    .icon-dollar {{
        top: 20%;
        left: 10%;
    }}
    .icon-chart {{
        top: 40%;
        right: 15%;
    }}
    .icon-piggy {{
        bottom: 30%;
        left: 20%;
    }}
    .icon-wallet {{
        bottom: 10%;
        right: 25%;
    }}
    @media (max-width: 768px) {{
        .main .block-container {{
            padding: 5px;
        }}
        h1 {{
            font-size: 24px;
        }}
        .stButton>button {{
            font-size: 14px;
            padding: 8px 16px;
        }}
        #earth-container {{
            height: 300px;
        }}
    }}
    </style>
""", unsafe_allow_html=True)

# Database Setup
def init_db():
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, amount REAL, category TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, user_id INTEGER, loan_type TEXT, principal REAL, interest_rate REAL, tenure INTEGER, start_date TEXT, outstanding_balance REAL, monthly_payment REAL, description TEXT, amount_paid REAL DEFAULT 0.0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL, target_date TEXT, priority TEXT)''')
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
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
        conn.commit()
        return True, "Registration successful! Please login."
    except sqlite3.IntegrityError:
        return False, "Email or username already exists!"
    finally:
        conn.close()

def auth_page():
    st.markdown(f"""
        <div style='text-align: center; padding: 20px; background: rgba(245, 245, 220, 0.9); border-radius: 15px;'>
            <h1 style='color: {COLORS['primary']}; margin-bottom: 20px;'>Unlock Your Financial Future</h1>
            <p style='color: {COLORS['text_dark']}; font-size: 18px;'>Step into a world of financial mastery. Login to explore the unseen potential of your wealth.</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email...")
            password = st.text_input("Password", type="password", placeholder="Enter your secret key...")
            submit = st.form_submit_button("Enter the Journey")
            if submit:
                if login_user(email, password):
                    st.success("Welcome to your financial odyssey!")
                    st.rerun()
                else:
                    st.error("The gates are locked. Check your credentials.")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Your Alias")
            new_email = st.text_input("Email")
            new_password = st.text_input("Create Your Secret Key", type="password")
            confirm_password = st.text_input("Confirm Secret Key", type="password")
            submit = st.form_submit_button("Begin Your Quest")
            if submit:
                if new_password != confirm_password:
                    st.error("The keys don't match!")
                elif len(new_password) < 6:
                    st.error("Your key must be stronger (6+ characters)!")
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
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "10px", "background-color": COLORS['primary']},
            "icon": {"color": COLORS['text_light'], "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "5px", "padding": "10px", "--hover-color": COLORS['accent'], "color": COLORS['text_light']},
            "nav-link-selected": {"background-color": COLORS['accent']},
        }
    )

# Dashboard
def dashboard():
    st.markdown(f"<h1 style='color: {COLORS['primary']}'>AI Financial Tracker</h1>", unsafe_allow_html=True)
    html(earth_html, height=500)
    st.markdown(f"""
        <div style='background: rgba(245, 245, 220, 0.9); padding: 20px; border-radius: 15px; text-align: center;'>
            <h2 style='color: {COLORS['primary']}'>Take Control of Your Finances</h2>
            <p style='color: {COLORS['text_dark']}'>Navigate the unknown with confidence. Conquer loans, master investments, and visualize your wealth.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Savings Goal", "₹25,000", "↑ 8%")
    with col2:
        st.metric("Net Worth", "₹5,00,000", "↑ 15%")

# Expense Tracker
def expense_tracker():
    st.markdown(f"<h1 style='color: {COLORS['primary']}'>Smart Expense Tracker</h1>", unsafe_allow_html=True)
    with st.expander("Add New Expense"):
        col1, col2 = st.columns(2)
        with col1:
            expense_date = st.date_input("Date")
            expense_amount = st.number_input("Amount (₹)", min_value=0.0)
        with col2:
            expense_category = st.selectbox("Category", ["Needs", "Wants", "Bills"])
            expense_description = st.text_area("Description")
        if st.button("Add Expense"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("INSERT INTO expenses (user_id, date, amount, category, description) VALUES (?, ?, ?, ?, ?)", 
                         (st.session_state.user_id, expense_date.strftime("%Y-%m-%d"), expense_amount, expense_category, expense_description))
                conn.commit()
                conn.close()
                st.success("Expense added!")
            else:
                st.error("Login required.")

# Investment Planner
def investment_planner():
    st.markdown(f"<h1 style='color: {COLORS['primary']}'>Investment Planner</h1>", unsafe_allow_html=True)
    with st.expander("Calculate Investment"):
        monthly_investment = st.number_input("Monthly Investment (₹)", min_value=100)
        years = st.number_input("Years", min_value=1)
        return_rate = st.slider("Return Rate (%)", 1.0, 30.0, 12.0)
        if st.button("Calculate"):
            future_value = monthly_investment * 12 * years * (1 + return_rate/100)
            st.metric("Future Value", f"₹{future_value:,.2f}")

# Advanced Analytics
def advanced_analytics():
    st.markdown(f"<h1 style='color: {COLORS['primary']}'>Advanced Analytics</h1>", unsafe_allow_html=True)
    st.write("Analyze your financial data here.")

# Debt Management
def debt_management():
    st.markdown(f"<h1 style='color: {COLORS['primary']}'>Debt Management</h1>", unsafe_allow_html=True)
    with st.expander("Add Loan"):
        loan_amount = st.number_input("Loan Amount (₹)", min_value=0.0)
        interest_rate = st.slider("Interest Rate (%)", 1.0, 50.0, 10.0)
        if st.button("Add Loan"):
            if st.session_state.user_id:
                conn = sqlite3.connect('finance_tracker.db')
                c = conn.cursor()
                c.execute("INSERT INTO loans (user_id, loan_type, principal, interest_rate) VALUES (?, ?, ?, ?)", 
                         (st.session_state.user_id, "Personal", loan_amount, interest_rate))
                conn.commit()
                conn.close()
                st.success("Loan added!")
            else:
                st.error("Login required.")

# Settings
def settings_page():
    st.markdown(f"<h1 style='color: {COLORS['primary']}'>Settings</h1>", unsafe_allow_html=True)
    st.toggle("Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")
    if st.button("Export Data"):
        conn = sqlite3.connect('finance_tracker.db')
        df = pd.read_sql_query("SELECT * FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
        conn.close()
        st.download_button("Download CSV", df.to_csv(), "expenses.csv", "text/csv")

# Main App
def main():
    init_db()
    st.markdown(f"<div style='position: relative; min-height: 100vh;'>", unsafe_allow_html=True)
    if not st.session_state.authenticated:
        st.markdown(f"""
            <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;'>
                {auth_page.__doc__}
            </div>
            <div class='login-button' onclick='document.getElementById("login-modal").style.display="block"'>💰</div>
            <div id='login-modal' style='display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4);'>
                <div class='login-content'>
                    <h1>Unlock Your Financial Future</h1>
                    <p>Discover the power of AI-driven financial planning. Log in to explore your personalized dashboard.</p>
                    {auth_page()}
                    <button onclick='document.getElementById("login-modal").style.display="none"'>Close</button>
                </div>
            </div>
        """, unsafe_allow_html=True)
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
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()