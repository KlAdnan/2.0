import streamlit as st
import sqlite3
import pandas as pd

def sync_loans_with_db():
    """
    Synchronizes the loans data between the database and session state.
    Loads all loans for the current user from the database into st.session_state.loans.
    """
    if not st.session_state.user_id:
        return
    
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    
    # Get all loans for the current user
    c.execute("""
        SELECT id, loan_type, principal, interest_rate, tenure_months, 
               emi_amount, amount_paid, start_date, description
        FROM loans 
        WHERE user_id = ?
    """, (st.session_state.user_id,))
    
    loans = c.fetchall()
    conn.close()
    
    # Clear existing loans in session state
    st.session_state.loans = []
    
    # Add each loan to session state with proper column names
    for loan in loans:
        loan_id, loan_type, principal, interest_rate, tenure_months, emi_amount, amount_paid, start_date, description = loan
        
        # Format the loan data with the expected column names
        loan_data = {
            "id": loan_id,
            "Loan Type": loan_type,
            "Loan Amount": principal,
            "Interest Rate": interest_rate,
            "Tenure (Months)": tenure_months,
            "EMI Amount": emi_amount if emi_amount is not None else 0.0,
            "Amount Paid": amount_paid if amount_paid is not None else 0.0,
            "Start Date": start_date,
            "Description": description
        }
        
        st.session_state.loans.append(loan_data)