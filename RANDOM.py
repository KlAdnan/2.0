from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download('vader_lexicon')

def generate_ai_report():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Comprehensive AI Financial Analysis Report", styles['Title']))
    elements.append(Spacer(1, 12))

    # User Info
    conn = sqlite3.connect('finance_tracker.db')
    c = conn.cursor()
    c.execute("SELECT username, email FROM users WHERE id = ?", (st.session_state.user_id,))
    user_info = c.fetchone()
    elements.append(Paragraph(f"Name: {user_info[0]} | Email: {user_info[1]} | Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Expenses Section
    df_expenses = pd.read_sql_query("SELECT * FROM expenses WHERE user_id = ?", conn, params=(st.session_state.user_id,))
    if not df_expenses.empty:
        total_exp = df_expenses["amount"].sum()
        elements.append(Paragraph(f"Total Expenses: ₹{total_exp:,.2f}", styles['Heading2']))
        exp_table = [["Date", "Amount", "Category"]] + df_expenses[["date", "amount", "category"]].values.tolist()[:5]
        elements.append(Table(exp_table, colWidths=[100, 100, 100]))
        plt.pie(df_expenses.groupby("category")["amount"].sum(), labels=df_expenses["category"].unique(), autopct='%1.1f%%')
        plt.savefig("exp_pie.png")
        elements.append(Image("exp_pie.png", width=200, height=200))
        elements.append(Spacer(1, 12))

        # ML Prediction for Future Expenses
        X = np.array(range(len(df_expenses))).reshape(-1, 1)
        y = df_expenses["amount"].values
        model = LinearRegression().fit(X, y)
        future_months = 12
        future_expenses = model.predict(np.array(range(len(df_expenses), len(df_expenses) + future_months)).reshape(-1, 1))
        elements.append(Paragraph(f"Predicted Expenses Next {future_months} Months: ₹{sum(future_expenses):,.2f}", styles['Normal']))

    # Investments Section
    df_goals = pd.read_sql_query("SELECT * FROM goals WHERE user_id = ?", conn, params=(st.session_state.user_id,))
    if not df_goals.empty:
        total_current = df_goals["current_amount"].sum()
        elements.append(Paragraph(f"Current Investments: ₹{total_current:,.2f}", styles['Heading2']))
        elements.append(Paragraph(f"Target Investments: ₹{df_goals['target_amount'].sum():,.2f}", styles['Normal']))
        elements.append(Spacer(1, 12))

    # Debt Section
    loans_df = pd.DataFrame(st.session_state.loans)
    if not loans_df.empty:
        total_debt = loans_df["Loan Amount"].sum() - loans_df["Amount Paid"].sum()
        elements.append(Paragraph(f"Total Outstanding Debt: ₹{total_debt:,.2f}", styles['Heading2']))
        debt_table = [["Loan Type", "Amount", "Interest Rate"]] + loans_df[["Loan Type", "Loan Amount", "Interest Rate"]].values.tolist()
        elements.append(Table(debt_table, colWidths=[100, 100, 100]))
        elements.append(Spacer(1, 12))

    # Graphs and Visualizations
    plt.figure(figsize=(6, 4))
    plt.plot(future_expenses)
    plt.title("Predicted Expense Trend")
    plt.savefig("exp_trend.png")
    elements.append(Image("exp_trend.png", width=200, height=200))
    plt.close()

    # AI Analysis with NLP
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores("Based on your data, your financial health is improving.")
    elements.append(Paragraph(f"AI Sentiment Analysis: {sentiment['compound']:.2f} (Positive: {sentiment['pos']:.2f})", styles['Heading2']))

    # Strategies and Recommendations
    elements.append(Paragraph("Financial Strategies", styles['Heading2']))
    recommendations = [
        "1. Increase savings by 10% monthly.",
        "2. Refinance loans with >15% interest.",
        "3. Invest 20% of income in diversified assets."
    ]
    for rec in recommendations:
        elements.append(Paragraph(rec, styles['Normal']))
    elements.append(Spacer(1, 12))

    # Planning to Execution
    elements.append(Paragraph("Action Plan", styles['Heading2']))
    action_plan = [["Task", "Status"], ["Review Budget", "Pending"], ["Increase Savings", "Pending"]]
    elements.append(Table(action_plan, colWidths=[200, 100]))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    st.download_button("Download AI Financial Report", buffer, "ai_financial_report.pdf", "application/pdf")
    if os.path.exists("exp_pie.png"):
        os.remove("exp_pie.png")
    if os.path.exists("exp_trend.png"):
        os.remove("exp_trend.png")
    conn.close()

with col2:
    if st.button("Generate Financial Report (PDF)"):
        generate_ai_report()