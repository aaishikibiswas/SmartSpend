import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
from langdetect import detect
from fpdf import FPDF
from deep_translator import GoogleTranslator
import re
import requests
import json
import gradio as gr

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

# --- Page config ---
st.set_page_config(page_title="Expense Analyzer", layout="wide", initial_sidebar_state="collapsed")

# --- Inject Custom CSS ---
st.markdown("""
<style>
:root {
    --page-bg-start: #b8aaf8;
    --page-bg-end: #9f91f0;
    --surface: rgba(255, 255, 255, 0.92);
    --surface-strong: #ffffff;
    --surface-soft: #f6f4ff;
    --stroke: #e7e1fb;
    --text: #1f1b2e;
    --muted: #7f7897;
    --primary: #7f6af7;
    --primary-deep: #6552e8;
    --success: #2fa36c;
    --danger: #e16b6b;
    --warning: #e3a93a;
    --shadow: 0 18px 50px rgba(90, 67, 194, 0.12);
}

.stApp {
    background: linear-gradient(135deg, var(--page-bg-start), var(--page-bg-end));
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="collapsedControl"] {
    opacity: 1;
}

[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.92);
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.dashboard-shell {
    background: var(--surface);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 34px;
    padding: 1.25rem;
    box-shadow: 0 28px 70px rgba(69, 50, 158, 0.16);
    backdrop-filter: blur(14px);
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.1rem;
}

.brand-pill, .profile-pill, .soft-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.65rem;
    background: rgba(255,255,255,0.9);
    border: 1px solid var(--stroke);
    border-radius: 999px;
    padding: 0.6rem 0.95rem;
    box-shadow: 0 10px 30px rgba(120, 96, 231, 0.08);
}

.brand-mark {
    width: 36px;
    height: 36px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: 700;
    background: radial-gradient(circle at top left, #14111d, #5d45ec);
}

.profile-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #d6cbff, #f4efff);
    color: var(--primary-deep);
    font-weight: 700;
}

.hero-banner {
    background: linear-gradient(135deg, rgba(127,106,247,0.14), rgba(255,255,255,0.72));
    border: 1px solid var(--stroke);
    border-radius: 28px;
    padding: 1.3rem 1.4rem;
    margin-bottom: 1rem;
}

.hero-title {
    color: var(--text);
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
    margin: 0 0 0.3rem 0;
}

.hero-subtitle, .section-subtitle, .muted-text {
    color: var(--muted);
}

.panel-card {
    background: rgba(255,255,255,0.88);
    border: 1px solid var(--stroke);
    border-radius: 26px;
    padding: 1rem 1rem 0.6rem 1rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.metric-html-card {
    background: var(--surface-strong);
    border: 1px solid var(--stroke);
    border-radius: 24px;
    padding: 1rem 1rem 0.95rem 1rem;
    box-shadow: var(--shadow);
    min-height: 136px;
}

.metric-html-label {
    color: var(--text);
    font-size: 0.98rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
}

.metric-html-value {
    color: #181428;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.7rem;
}

.metric-html-delta {
    display: inline-block;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 0.28rem 0.55rem;
    border-radius: 999px;
}

.delta-positive {
    color: var(--success);
    background: rgba(47, 163, 108, 0.1);
}

.delta-negative {
    color: var(--danger);
    background: rgba(225, 107, 107, 0.12);
}

.section-head {
    margin-bottom: 0.5rem;
}

.section-title {
    color: var(--text);
    font-size: 1.1rem;
    font-weight: 750;
    margin: 0;
}

.mini-note {
    color: var(--muted);
    font-size: 0.88rem;
}

div[data-testid="stMetric"] {
    background: var(--surface-strong);
    border: 1px solid var(--stroke);
    border-radius: 22px;
    padding: 1rem;
    box-shadow: var(--shadow);
}

div[data-testid="stMetric"] label {
    color: var(--muted) !important;
}

div[data-testid="stMetricValue"] {
    color: var(--text);
}

div[data-testid="stExpander"] {
    border: 1px solid var(--stroke);
    border-radius: 20px;
    background: rgba(255,255,255,0.86);
}

.stButton > button,
.stDownloadButton > button,
button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), var(--primary-deep)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 0.62rem 1.15rem !important;
    font-weight: 600 !important;
    box-shadow: 0 12px 25px rgba(127, 106, 247, 0.28);
}

.stButton > button:hover,
.stDownloadButton > button:hover,
button[kind="primary"]:hover {
    transform: translateY(-1px);
    filter: brightness(1.02);
}

.stSelectbox > div > div,
.stNumberInput > div > div,
.stDateInput > div > div,
.stTextInput > div > div,
.stTextArea textarea,
.stMultiSelect > div > div,
.stFileUploader > div,
.stChatInput textarea {
    border-radius: 18px !important;
    border: 1px solid var(--stroke) !important;
    background: rgba(255,255,255,0.88) !important;
}

.stRadio [role="radiogroup"] {
    padding: 0.35rem;
    border-radius: 18px;
    background: var(--surface-soft);
    border: 1px solid var(--stroke);
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--primary), #9b8cff);
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--stroke);
    border-radius: 22px;
    overflow: hidden;
}

.stAlert {
    border-radius: 18px;
    border: 1px solid var(--stroke);
}

.hint-card {
    background: linear-gradient(135deg, rgba(127,106,247,0.15), rgba(255,255,255,0.75));
    border: 1px solid var(--stroke);
    border-radius: 24px;
    padding: 1.1rem 1.15rem;
}
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'financial_goals' not in st.session_state:
    st.session_state.financial_goals = []
if 'bill_reminders' not in st.session_state:
    st.session_state.bill_reminders = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": "Hi! I'm your expense advisor. How can I help you with your finances today?"}]
# Initialize df in session state to ensure it's accessible globally for the chatbot
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'ai_suggestions' not in st.session_state: # New state for AI suggestions
    st.session_state.ai_suggestions = ""
# Initialize budget variables in session state
if 'monthly_budget' not in st.session_state:
    st.session_state.monthly_budget = 10000 # Default value, matches sidebar input
if 'weekly_budget_amount' not in st.session_state:
    st.session_state.weekly_budget_amount = 2500 # Default value, matches sidebar input
if 'category_budgets' not in st.session_state: # Initialize category budgets
    st.session_state.category_budgets = {}

# --- Language Selection ---
# Keep language selection in sidebar if preferred, or move to main content
lang_option = st.sidebar.selectbox("🌐 Choose Language", ["English", "Hindi", "Bengali", "Odia"])
lang_codes = {"English": "en", "Hindi": "hi", "Bengali": "bn", "Odia": "or"}
selected_lang_code = lang_codes.get(lang_option, "en")

def translate(text):
    try:
        return GoogleTranslator(source='auto', target=selected_lang_code).translate(text)
    except:
        return text

# --- Sidebar Inputs (Moved some to left column, keeping API Key and Model here) ---
# --- Chatbot Settings (Keep API key and model selection here for global access) ---
st.sidebar.markdown("### AI Chatbot Settings")
api_key = st.sidebar.text_input(
    "Enter OpenRouter API Key:",
    type="password",
    help="Get your key from https://openrouter.ai/keys",
    key="api_key_input"
)

model = st.sidebar.selectbox(
    "Choose AI Model:",
    [
        "anthropic/claude-3-opus",
        "anthropic/claude-3-sonnet",
        "openai/gpt-4-turbo-preview",
        "google/gemini-pro",
        "meta-llama/llama-3-70b-instruct"
    ],
    index=1,
    key="model_selectbox"
)

temperature = st.sidebar.slider("AI Temperature:", 0.0, 1.0, 0.7, key="temp_slider")

if st.sidebar.button("Clear Chat History", key="clear_chat_history_button"):
    st.session_state.chat_messages = [{"role": "assistant", "content": "Hi! I'm your expense advisor. How can I help you with your finances today?"}]
    st.session_state.ai_suggestions = "" # Clear suggestions too
    st.rerun()

st.sidebar.markdown("---")

# --- Category Keywords (Remains the same) ---
category_keywords = {
    "🍔 Food": ["zomato", "swiggy", "food", "restaurant"],
    "🛍️ Shopping": ["flipkart", "amazon", "myntra"],
    "🚕 Transport": ["uber", "ola", "cab", "fuel", "petrol"],
    "🔌 Utilities": ["bill", "electricity", "recharge", "jio", "airtel", "water", "gas"],
    "💼 Income": ["salary", "credit", "refund", "deposit"],
    "🏧 Cash": ["atm", "cash", "withdrawal"],
    "🏠 Rent": ["rent", "landlord", "housing"],
    "🎮 Entertainment": ["movie", "netflix", "hotstar", "cinema", "spotify", "ticket"],
    "📱 Subscriptions": ["subscription", "spotify", "youtube", "prime", "disney", "membership"],
    "🏥 Health": ["pharmacy", "hospital", "doctor", "medicine"],
    "📚 Education": ["school", "college", "course", "fees"]
}

def categorize(desc):
    desc = desc.lower()
    for category, keywords in category_keywords.items():
        if any(k in desc for k in keywords):
            return category
    lang = detect(desc)
    return "🌐 Regional" if lang in ["hi", "bn", "or"] else "🔍 Other"

# --- Parsing Functions (Remain the same) ---
def extract_text_from_image(image_file):
    return pytesseract.image_to_string(Image.open(image_file))

def parse_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
    return parse_text_to_df(text)

def parse_text_to_df(text):
    lines = text.strip().split('\n')
    rows = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5:
            try:
                date = parts[0]
                # Try to parse credit/debit/balance from the end, then description
                # This part is highly dependent on PDF/OCR format, may need refinement
                balance = float(parts[-1].replace(',', ''))
                credit_str = parts[-2]
                debit_str = parts[-3]
                desc = " ".join(parts[1:-3]) # Description is everything between date and debit/credit

                # Handle cases where credit/debit might be non-numeric (e.g., '-')
                try:
                    credit = float(credit_str.replace(',', ''))
                except ValueError:
                    credit = 0.0

                try:
                    debit = float(debit_str.replace(',', ''))
                except ValueError:
                    debit = 0.0

                rows.append([date, desc, debit, credit, balance])
            except Exception as e:
                # st.warning(f"Skipping line due to parsing error: {line} - {e}") # For debugging
                continue
    return pd.DataFrame(rows, columns=["Date", "Description", "Debit", "Credit", "Balance"])

def export_pdf_report(summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Expense Summary Report", ln=1, align='C')
    for key, value in summary.items():
        key = key.replace("₹", "Rs.") # FPDF doesn't render rupees symbol well
        pdf.cell(200, 10, txt=f"{key}: Rs. {value:,.2f}", ln=1)
    return pdf.output(dest='S').encode('latin1', errors='replace')


def money(value):
    return f"₹{value:,.2f}"


def metric_delta_class(value):
    return "delta-negative" if value < 0 else "delta-positive"


def section_title(title, subtitle=""):
    subtitle_html = f"<div class='section-subtitle'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title, value, delta_text, delta_value=1):
    st.markdown(
        f"""
        <div class="metric-html-card">
            <div class="metric-html-label">{title}</div>
            <div class="metric-html-value">{value}</div>
            <span class="metric-html-delta {metric_delta_class(delta_value)}">{delta_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plot(fig, height=320):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(246,244,255,0.65)",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color="#3a3450"),
        title=dict(font=dict(size=18, color="#221d33")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, linecolor="#ddd5fb", tickfont=dict(color="#6f6787"))
    fig.update_yaxes(showgrid=True, gridcolor="#ebe6ff", zeroline=False, tickfont=dict(color="#6f6787"))
    return fig


# --- Dashboard Shell ---
st.markdown(
    """
    <div class="dashboard-shell">
        <div class="topbar">
            <div class="brand-pill">
                <div class="brand-mark">F</div>
                <div>
                    <div style="font-weight:800;color:#1f1b2e;">FinSet</div>
                    <div class="mini-note">Smart expense control</div>
                </div>
            </div>
            <div class="profile-pill">
                <div class="profile-avatar">A</div>
                <div>
                    <div style="font-weight:700;color:#1f1b2e;">Adaline Lively</div>
                    <div class="mini-note">expense dashboard</div>
                </div>
            </div>
        </div>
        <div class="hero-banner">
            <div class="hero-title">Welcome back to your financial cockpit</div>
            <div class="hero-subtitle">Same logic, cleaner dashboard. Upload statements, monitor budgets, track goals, and ask the AI assistant for guidance.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Define 3-Column Layout ---
left_col, center_col, right_col = st.columns([1.05, 2.45, 1.2], gap="large")

# --- LEFT COLUMN: Upload & Financial Settings ---
with left_col:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    section_title("Upload & Settings", "Everything on the left works the same, just in a cleaner control panel.")
    st.markdown('<div class="soft-chip">Finance controls</div>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown("### " + translate("Upload Data"))
    uploaded_file = st.file_uploader(translate("Upload your bank statement"), type=["pdf", "csv", "png", "jpg", "jpeg"])

    st.markdown("---") # Separator for clarity

    st.markdown("### " + translate("Financial Settings"))
    # Link sidebar inputs to session state variables
    monthly_budget = st.number_input(translate("Set Monthly Budget (in ₹)"), min_value=0, value=st.session_state.monthly_budget, key="monthly_budget_input_col")
    st.session_state.monthly_budget = monthly_budget # Update session state when input changes

    weekly_budget_amount = st.number_input(translate("Set Weekly Budget (in ₹)"), min_value=0, value=st.session_state.weekly_budget_amount, key="weekly_budget_input_col")
    st.session_state.weekly_budget_amount = weekly_budget_amount # Update session state when input changes

    st.markdown("---") # Separator for clarity

    st.markdown("### " + translate("Add New Transaction"))
    with st.form("new_transaction_form", clear_on_submit=True):
        trans_date = st.date_input(translate("Date"), value="today", key="trans_date_input")
        trans_desc = st.text_input(translate("Description"), key="trans_desc_input")
        trans_amount = st.number_input(translate("Amount (in ₹)"), min_value=0.0, value=0.0, format="%.2f", key="trans_amount_input")
        trans_type = st.radio(translate("Type"), ["Debit", "Credit"], key="trans_type_input")
        
        # Get categories dynamically from existing data or a default list
        all_categories = list(category_keywords.keys()) + ["🔍 Other"]
        trans_category = st.selectbox(translate("Category"), all_categories, key="trans_category_input")

        add_trans_button = st.form_submit_button(translate("Add Transaction"))
        if add_trans_button:
            if trans_desc and trans_amount > 0:
                new_row = {
                    "Date": pd.to_datetime(trans_date),
                    "Description": trans_desc,
                    "Debit": trans_amount if trans_type == "Debit" else 0.0,
                    "Credit": trans_amount if trans_type == "Credit" else 0.0,
                    "Balance": 0.0, # Balance will be recalculated or can be ignored for single entry
                    "Category": trans_category,
                    "Month": pd.to_datetime(trans_date).strftime('%B %Y'),
                    "Day": pd.to_datetime(trans_date).date()
                }
                # Append new transaction to the DataFrame in session state
                new_df_row = pd.DataFrame([new_row])
                st.session_state.df = pd.concat([st.session_state.df, new_df_row], ignore_index=True)
                st.session_state.df.sort_values("Date", ascending=False, inplace=True) # Re-sort
                st.success(translate("Transaction added successfully!"))
                st.rerun() # Rerun to update dashboard with new data
            else:
                st.error(translate("Please enter a valid description and amount for the transaction."))
    st.markdown("---")

    st.markdown("### " + translate("Manage Financial Goals"))

    with st.form("new_goal_form_col"):
        goal_name = st.text_input(translate("Goal Name (e.g., Vacation, Gadget)"), key="goal_name_input_col")
        goal_target_amount = st.number_input(translate("Target Amount (in ₹)"), min_value=0.0, value=0.0, format="%.2f", key="goal_target_amount_input_col")
        goal_target_date = st.date_input(translate("Target Date"), min_value=pd.Timestamp.now().date(), key="goal_target_date_input_col")

        # Removed the 'key' argument from st.form_submit_button
        add_goal_button = st.form_submit_button(translate("Add Goal")) 
        if add_goal_button:
            if goal_name and goal_target_amount > 0:
                st.session_state.financial_goals.append({
                    "name": goal_name,
                    "target_amount": goal_target_amount,
                    "target_date": goal_target_date,
                    "achieved": 0.0 # Will be updated dynamically
                })
                st.success(translate(f"Goal '{goal_name}' added!"))
            else:
                st.error(translate("Please enter a valid goal name and target amount."))

    # Display current goals in left column
    if st.session_state.financial_goals:
        st.markdown("#### " + translate("Your Current Goals"))
        for i, goal in enumerate(st.session_state.financial_goals):
            st.text(f"🎯 {goal['name']}: ₹{goal['target_amount']:,.0f} by {goal['target_date'].strftime('%Y-%m-%d')}")
            if st.button(translate("Remove Goal"), key=f"remove_goal_col_{i}"):
                st.session_state.financial_goals.pop(i)
                st.success(translate("Goal removed."))
                st.rerun() # Rerun to update the list

    st.markdown("---") # Separator for clarity
    st.markdown("### " + translate("Manage Bill Reminders"))

    with st.form("new_bill_form_col"):
        bill_name = st.text_input(translate("Bill Name (e.g., Electricity, Rent)"), key="bill_name_input_col")
        bill_amount = st.number_input(translate("Amount (in ₹)"), min_value=0.0, value=0.0, format="%.2f", key="bill_amount_input_form_col")
        bill_due_day = st.slider(translate("Due Day of Month"), 1, 31, 1, key="bill_day_input_form_col")

        # Removed the 'key' argument from st.form_submit_button
        add_bill_button = st.form_submit_button(translate("Add Bill")) 
        if add_bill_button:
            if bill_name and bill_amount > 0:
                st.session_state.bill_reminders.append({
                    "name": bill_name,
                    "amount": bill_amount,
                    "due_day": bill_due_day
                })
                st.success(translate(f"Bill '{bill_name}' added!"))
            else:
                st.error(translate("Please enter a valid bill name and amount."))

    # Display current bills in left column
    if st.session_state.bill_reminders:
        st.markdown("#### " + translate("Your Recurring Bills"))
        today_day = pd.Timestamp.now().day
        for i, bill in enumerate(st.session_state.bill_reminders):
            st.text(f"🧾 {bill['name']}: ₹{bill['amount']:,.0f} (Day {bill['due_day']})")
            if bill['due_day'] == today_day:
                st.warning(translate(f"🔔 {bill['name']} is due today!"))
            elif bill['due_day'] > today_day and bill['due_day'] <= today_day + 7: # Within next 7 days
                 st.info(translate(f"Upcoming: {bill['name']} on day {bill['due_day']}"))

            if st.button(translate("Remove Bill"), key=f"remove_bill_col_{i}"):
                st.session_state.bill_reminders.pop(i)
                st.success(translate("Bill reminder removed."))
                st.rerun()

    st.markdown("---")

    st.markdown("### " + translate("Manage Category Budgets"))
    # Dynamically create budget options for each category present in data or default list
    all_active_categories = list(st.session_state.df['Category'].unique()) if not st.session_state.df.empty else list(category_keywords.keys()) + ["🔍 Other"]
    all_active_categories = sorted(list(set(all_active_categories))) # Ensure unique and sorted

    # New form for setting category budgets
    with st.form("category_budget_form"):
        selected_category_for_budget = st.selectbox(
            translate("Select Category"),
            options=all_active_categories,
            key="selected_category_for_budget"
        )
        budget_frequency = st.selectbox(
            translate("Budget Frequency"),
            options=["Monthly", "Weekly", "Yearly"],
            key="budget_frequency_input"
        )
        
        # Get current budget for the selected category and frequency
        current_selected_cat_budget = st.session_state.category_budgets.get(selected_category_for_budget, {}).get(budget_frequency.lower(), 0.0)
        
        new_category_budget_amount = st.number_input(
            translate(f"Set Budget for {selected_category_for_budget} ({budget_frequency}, ₹)"),
            min_value=0.0,
            value=current_selected_cat_budget,
            format="%.2f",
            key="new_category_budget_amount"
        )
        set_category_budget_button = st.form_submit_button(translate("Set Category Budget"))
        if set_category_budget_button:
            if selected_category_for_budget not in st.session_state.category_budgets:
                st.session_state.category_budgets[selected_category_for_budget] = {}
            st.session_state.category_budgets[selected_category_for_budget][budget_frequency.lower()] = new_category_budget_amount
            st.success(translate(f"Budget for {selected_category_for_budget} ({budget_frequency}) set to ₹{new_category_budget_amount:,.2f}!"))
            st.rerun() # Rerun to update alerts if needed

    # Display current category budgets
    if st.session_state.category_budgets:
        st.markdown("#### " + translate("Current Category Budgets"))
        for category, frequencies in st.session_state.category_budgets.items():
            st.markdown(f"**{category}:**")
            for freq, amount in frequencies.items():
                if amount > 0:
                    st.text(f"  - {freq.capitalize()}: ₹{amount:,.2f}")
    st.markdown("---")
    st.markdown("</div>", unsafe_allow_html=True)


# --- Parsing and Data Processing (remains largely the same, but now within the main logic flow) ---
if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1].lower()
    try:
        temp_df = pd.DataFrame() # Use a temporary df for parsing
        if file_type == "pdf":
            temp_df = parse_pdf(uploaded_file)
        elif file_type == "csv":
            temp_df = pd.read_csv(uploaded_file)
        elif file_type in ["png", "jpg", "jpeg"]:
            temp_df = parse_text_to_df(extract_text_from_image(uploaded_file))

        if not temp_df.empty:
            # Ensure columns are numeric, coercing errors will turn invalid values into NaN
            temp_df['Credit'] = pd.to_numeric(temp_df['Credit'], errors='coerce').fillna(0)
            temp_df['Debit'] = pd.to_numeric(temp_df['Debit'], errors='coerce').fillna(0)
            temp_df['Balance'] = pd.to_numeric(temp_df['Balance'], errors='coerce').fillna(0)
            temp_df['Category'] = temp_df['Description'].apply(categorize)
            temp_df['Date'] = pd.to_datetime(temp_df['Date'], dayfirst=True, errors='coerce')
            temp_df.dropna(subset=['Date'], inplace=True) # Drop rows where date parsing failed
            temp_df['Month'] = temp_df['Date'].dt.strftime('%B %Y')
            temp_df['Day'] = temp_df['Date'].dt.date
            temp_df.sort_values("Date", ascending=False, inplace=True)
            
            # Store the processed DataFrame in session state
            st.session_state.df = temp_df.copy()
            
        else:
            center_col.error(translate("Could not parse data from the uploaded file. Please check the format or try a different file."))
            st.session_state.df = pd.DataFrame() # Clear df if parsing fails
    except Exception as e:
        center_col.error(translate(f"An error occurred while processing the file: {e}"))
        center_col.info(translate("Please ensure your PDF/Image is clear and structured, or use a CSV file."))
        st.session_state.df = pd.DataFrame() # Clear df on error


# --- CENTER COLUMN: Main Financial Dashboard ---
with center_col:
    df = st.session_state.df

    if not df.empty:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title("Overview", "A cleaner summary of the same financial calculations already in your app.")
        # --- Custom Filters ---
        with st.expander("🔍 Filter Transactions (Date Range + Category)"):
            start_date_filter = st.date_input("Start Date", pd.to_datetime(df["Date"].min()))
            end_date_filter = st.date_input("End Date", pd.to_datetime(df["Date"].max()))
            category_options = sorted(df["Category"].dropna().unique().tolist())
            selected_categories = st.multiselect("Filter by Category", ["All"] + category_options, default=["All"])

            # Apply filters
            df_filtered = df[
                (df["Date"] >= pd.to_datetime(start_date_filter)) &
                (df["Date"] <= pd.to_datetime(end_date_filter))
            ]

            if "All" not in selected_categories:
                df_filtered = df_filtered[df_filtered["Category"].isin(selected_categories)]
            else:
                df_filtered = df.copy()

        # Set fallback budget values
        monthly_budget = st.session_state.monthly_budget
        weekly_budget_amount = st.session_state.weekly_budget_amount

        # --- Key Metrics ---
        section_title(translate("Dashboard Overview"), "This month snapshot with the same totals, just presented like the reference design.")

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        total_income_value = df_filtered['Credit'].sum()
        total_expense_value = df_filtered['Debit'].sum()
        with col1:
            render_metric_card(translate("Total Income"), money(total_income_value), "Cash in", 1)
        with col2:
            render_metric_card(translate("Total Expense"), money(total_expense_value), "Cash out", -1)
        savings = df_filtered['Credit'].sum() - df_filtered['Debit'].sum()
        savings_delta = f"{(savings / df_filtered['Credit'].sum()) * 100:.1f}% saved" if df_filtered['Credit'].sum() > 0 else "0.0% saved"
        with col3:
            render_metric_card(translate("Total Savings"), money(savings), savings_delta, savings)

        top_category_series = df_filtered.groupby("Category")["Debit"].sum().sort_values(ascending=False)
        if not top_category_series.empty:
            top_category = top_category_series.index[0]
            top_value = top_category_series.values[0]
            with col4:
                render_metric_card(translate("Most Spending"), top_category, money(top_value), -1)
        else:
            with col4:
                render_metric_card(translate("Most Spending"), translate("N/A"), translate("No expenses"), 1)

        st.markdown("</div>", unsafe_allow_html=True)

        # Define this to avoid NameError later
        total_expenses_current_month = df_filtered['Debit'].sum()

        # Calculate total expenses for the current week
        current_week_start = pd.Timestamp.now().to_period('W').start_time
        current_week_end = pd.Timestamp.now().to_period('W').end_time
        total_expenses_current_week_val = df_filtered[(df_filtered['Date'] >= current_week_start) & (df_filtered['Date'] <= current_week_end)]['Debit'].sum()

        # Filter DataFrame for the current month for category budget alerts
        current_month_str = pd.Timestamp.now().strftime('%B %Y')
        df_current_month = df_filtered[df_filtered['Month'] == current_month_str]


        # --- Smart Insights & Alerts ---
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title(translate("Smart Insights & Alerts"), "Helpful warnings, duplicate detection, and spending tips.")
        with st.expander(translate("View Smart Alerts & Suggestions")):
            # 1. Spending Tips
            st.markdown("#### " + translate("Spending Tips"))
            df_last_week = df[df['Date'] >= (pd.Timestamp.now() - pd.Timedelta(weeks=1))].copy()
            if not df_last_week.empty:
                food_spending_this_week = df_last_week[df_last_week['Category'] == "🍔 Food"]['Debit'].sum()
                if food_spending_this_week > 1000: # Example threshold
                    st.info(translate(f"💡 You spent ₹{food_spending_this_week:,.2f} on Food this week – consider cooking at home to save!"))

                transport_spending_this_week = df_last_week[df_last_week['Category'] == "🚕 Transport"]['Debit'].sum()
                if transport_spending_this_week > 800: # Example threshold
                    st.info(translate(f"💡 Your transport expenses are ₹{transport_spending_this_week:,.2f} this week. Explore public transport or carpooling options."))
                
                if food_spending_this_week <= 1000 and transport_spending_this_week <= 800:
                    st.success(translate("Good job on managing your spending in key categories this week!"))
            else:
                st.info(translate("No recent transactions to generate specific spending tips yet."))

            st.markdown("---")
            # 2. Budget Breach Alerts
            st.markdown("#### " + translate("Budget Breach Alerts"))
            if monthly_budget > 0:
                budget_percentage_used = (total_expenses_current_month / monthly_budget) * 100
                if budget_percentage_used >= 100:
                    st.error(translate(f"🚨 Your total expenses for this month (₹{total_expenses_current_month:,.2f}) have exceeded your budget of ₹{monthly_budget:,.2f}!"))
                elif budget_percentage_used >= 80:
                    st.warning(translate(f"⚠️ You've used {budget_percentage_used:.1f}% of your monthly budget (₹{total_expenses_current_month:,.2f} of ₹{monthly_budget:,.2f}). Watch your spending!"))
                else:
                    st.info(translate("Your monthly spending is within budget. Keep it up!"))
            else:
                st.info(translate("Set a monthly budget in the sidebar to receive budget breach alerts."))

            if weekly_budget_amount > 0:
                weekly_budget_percentage_used = (total_expenses_current_week_val / weekly_budget_amount) * 100
                if weekly_budget_percentage_used >= 100:
                    st.error(translate(f"🚨 Your total expenses for this week (₹{total_expenses_current_week_val:,.2f}) have exceeded your weekly budget of ₹{weekly_budget_amount:,.2f}!"))
                elif weekly_budget_percentage_used >= 80:
                    st.warning(translate(f"⚠️ You've used {weekly_budget_percentage_used:.1f}% of your weekly budget (₹{total_expenses_current_week_val:,.2f} of ₹{weekly_budget_amount:,.2f})."))
                else:
                    st.info(translate("Your weekly spending is well within budget."))
            else:
                st.info(translate("Set a weekly budget in the sidebar for weekly alerts."))

            # Category Budget Alerts
            st.markdown("#### " + translate("Category Budget Alerts"))
            if st.session_state.category_budgets and not df_current_month.empty:
                for category, frequencies in st.session_state.category_budgets.items():
                    category_expenses = df_current_month[df_current_month['Category'] == category]['Debit'].sum()
                    for freq, budget_amount in frequencies.items():
                        if budget_amount > 0:
                            if freq == "monthly":
                                budget_used_percent = (category_expenses / budget_amount) * 100
                                if budget_used_percent >= 100:
                                    st.error(translate(f"🚨 {category} expenses (₹{category_expenses:,.2f}) have exceeded your monthly budget of ₹{budget_amount:,.2f}!"))
                                elif budget_used_percent >= 80:
                                    st.warning(translate(f"⚠️ {category} expenses are {budget_used_percent:.1f}% of your monthly budget (₹{category_expenses:,.2f} of ₹{budget_amount:,.2f})."))
                            # Add weekly/yearly logic if needed based on `freq`
            else:
                st.info(translate("Set category-specific budgets to receive alerts."))


            st.markdown("---")
            # 3. High Transaction Detection
            st.markdown("#### " + translate("High Transaction Detection"))
            avg_transaction_amount = df['Debit'].mean()
            high_transaction_threshold = max(avg_transaction_amount * 2, 5000) # Threshold: 2x avg or fixed 5000
            high_transactions = df[df['Debit'] > high_transaction_threshold].copy()
            if not high_transactions.empty:
                st.warning(translate("💸 Detected unusually high transactions:"))
                for index, row in high_transactions.head(3).iterrows(): # Show top 3 highest
                    st.write(translate(f"- On {row['Date'].strftime('%Y-%m-%d')}: ₹{row['Debit']:,.2f} for '{row['Description']}' ({row['Category']})"))
            else:
                st.info(translate("No unusually high transactions detected recently."))

            st.markdown("---")
            # 4. Duplicate Transaction Warning
            st.markdown("#### " + translate("Duplicate Transaction Warning"))
            df_sorted = df.sort_values(by=['Description', 'Debit', 'Date'])
            potential_duplicates = []
            # Iterate through sorted DataFrame to find possible duplicates within a day
            for i in range(len(df_sorted) - 1):
                row1 = df_sorted.iloc[i]
                row2 = df_sorted.iloc[i+1]
                # Check for same description and amount within a 1-day window
                if row1['Description'] == row2['Description'] and \
                   row1['Debit'] == row2['Debit'] and \
                   abs((row1['Date'] - row2['Date']).days) <= 1 and row1['Debit'] > 0: # Only check for debits > 0
                    potential_duplicates.append((row1, row2))

            if potential_duplicates:
                st.warning(translate("⛔ Potentially duplicate transactions detected:"))
                # Display unique pairs of duplicates
                seen_duplicates = set()
                for d1, d2 in potential_duplicates:
                    # Create a unique key for the pair to avoid repeating
                    pair_key = tuple(sorted(((d1['Date'], d1['Debit'], d1['Description']), (d2['Date'], d2['Debit'], d2['Description']))))
                    if pair_key not in seen_duplicates:
                        st.write(translate(f"- Transaction: '{d1['Description']}' for ₹{d1['Debit']:,.2f} on {d1['Date'].strftime('%Y-%m-%d')} and {d2['Date'].strftime('%Y-%m-%d')}"))
                        seen_duplicates.add(pair_key)
            else:
                st.info(translate("No potential duplicate transactions detected."))
        
        st.markdown("</div>", unsafe_allow_html=True)


        # --- Budgeting Section ---
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title(translate("Monthly Budget Tracker"), "Track how much room is left in your monthly plan.")
        st.info(f"{translate('Your current monthly budget is')} ₹{monthly_budget:,.2f}")

        budget_col1, budget_col2 = st.columns(2)
        with budget_col1:
            st.metric(translate("Expenses This Month"), f"₹{total_expenses_current_month:,.2f}")
        with budget_col2:
            remaining_budget = monthly_budget - total_expenses_current_month
            # Determine delta color based on remaining budget
            delta_color = "inverse" if remaining_budget < 0 else "normal"
            delta_text = f"{translate('Over budget by')} ₹{-remaining_budget:,.2f}" if remaining_budget < 0 else f"{translate('Remaining')}"
            st.metric(translate("Remaining Budget"), f"₹{remaining_budget:,.2f}", delta=delta_text, delta_color=delta_color)

        # Progress bar for budget
        budget_percentage_used = (total_expenses_current_month / monthly_budget) * 100 if monthly_budget > 0 else 0
        
        st.markdown(f"**{translate('Budget Used')}: {budget_percentage_used:.1f}%**")
        if budget_percentage_used >= 100:
            st.progress(1.0, text=translate("Budget Exceeded!"))
        elif budget_percentage_used >= 80:
            st.progress(budget_percentage_used / 100, text=translate("Approaching Budget Limit!"))
        else:
            st.progress(budget_percentage_used / 100)

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Weekly Budget Tracker ---
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title(translate("Weekly Budget Tracker"), "A smaller sprint view of spending control.")
        st.info(f"{translate('Your current weekly budget is')} ₹{weekly_budget_amount:,.2f}")
        
        col_week1, col_week2 = st.columns(2)
        with col_week1:
            st.metric(translate("Expenses This Week"), f"₹{total_expenses_current_week_val:,.2f}")
        with col_week2:
            remaining_weekly_budget = weekly_budget_amount - total_expenses_current_week_val
            delta_color_week = "inverse" if remaining_weekly_budget < 0 else "normal"
            delta_text_week = f"{translate('Over budget by')} ₹{-remaining_weekly_budget:,.2f}" if remaining_weekly_budget < 0 else f"{translate('Remaining')}"
            st.metric(translate("Remaining Weekly Budget"), f"₹{remaining_weekly_budget:,.2f}", delta=delta_text_week, delta_color=delta_color_week)

        weekly_budget_percentage_used = (total_expenses_current_week_val / weekly_budget_amount) * 100 if weekly_budget_amount > 0 else 0

        st.markdown(f"**{translate('Weekly Budget Used')}: {weekly_budget_percentage_used:.1f}%**")
        if weekly_budget_percentage_used >= 100:
            st.progress(1.0, text=translate("Weekly Budget Exceeded!"))
        elif weekly_budget_percentage_used >= 80:
            st.progress(weekly_budget_percentage_used / 100, text=translate("Approaching Weekly Budget Limit!"))
        else:
            st.progress(weekly_budget_percentage_used / 100)
        
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Multiple Financial Goals Tracker ---
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title(translate("Multiple Financial Goals Tracker"), "See how today’s savings connect to your future plans.")
        if st.session_state.financial_goals:
            total_savings_so_far = df['Credit'].sum() - df['Debit'].sum() # Overall savings
            
            for i, goal in enumerate(st.session_state.financial_goals):
                st.markdown(f"#### 🎯 {goal['name']}")
                col_goal1, col_goal2, col_goal3 = st.columns(3)
                with col_goal1:
                    st.metric(translate("Target"), f"₹{goal['target_amount']:,.2f}")
                with col_goal2:
                    # Cap achieved savings at target amount for display
                    display_achieved = min(total_savings_so_far, goal['target_amount'])
                    st.metric(translate("Achieved"), f"₹{display_achieved:,.2f}")
                with col_goal3:
                    remaining_days = (goal['target_date'] - pd.Timestamp.now().date()).days
                    if remaining_days >= 0:
                        st.metric(translate("Days Left"), f"{remaining_days} {translate('days')}")
                    else:
                        st.metric(translate("Status"), translate("Overdue! ⏱️"), delta_color="inverse")

                progress_percent = (display_achieved / goal['target_amount']) * 100 if goal['target_amount'] > 0 else 0
                
                if total_savings_so_far >= goal['target_amount']:
                    st.progress(1.0, text=translate("Goal Achieved! 🎉"))
                    st.balloons()
                else:
                    st.progress(progress_percent / 100, text=f"{progress_percent:.1f}% {translate('Achieved')}")
                    st.info(translate(f"You need to save ₹{goal['target_amount'] - total_savings_so_far:,.2f} more to reach your goal."))
                st.markdown("---") # Separator between goals
        else:
            st.info(translate("Define your financial goals in the left column to track them here!"))

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Upcoming Bill Reminders ---
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title(translate("Upcoming Bill Reminders"), "Bills that need attention soon.")
        if st.session_state.bill_reminders:
            st.markdown(f"**{translate('Current Date')}: {pd.Timestamp.now().strftime('%Y-%m-%d')}**")
            today_date = pd.Timestamp.now().date()
            upcoming_bills_found = False
            for bill in st.session_state.bill_reminders:
                # Calculate next due date for this month or next
                due_date_this_month = today_date.replace(day=bill['due_day'])
                if due_date_this_month < today_date:
                    # If due day has passed this month, consider next month
                    if today_date.month == 12:
                        due_date_this_month = due_date_this_month.replace(year=today_date.year + 1, month=1)
                    else:
                        due_date_this_month = due_date_this_month.replace(month=today_date.month + 1)
                
                days_until_due = (due_date_this_month - today_date).days

                if 0 <= days_until_due <= 30: # Show bills due within the next 30 days
                    upcoming_bills_found = True
                    bill_col1, bill_col2, bill_col3 = st.columns([2,1,1])
                    with bill_col1:
                        st.write(f"**{bill['name']}**")
                    with bill_col2:
                        st.write(f"₹{bill['amount']:,.2f}")
                    with bill_col3:
                        if days_until_due == 0:
                            st.error(translate("Due Today!"))
                        elif days_until_due <= 7:
                            st.warning(translate(f"Due in {days_until_due} days"))
                        else:
                            st.info(translate(f"Due in {days_until_due} days"))
            if not upcoming_bills_found:
                st.info(translate("No upcoming bills due in the next 30 days."))
        else:
            st.info(translate("Add recurring bills in the left column to get reminders."))

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Projected Savings ---
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title(translate("Projected Savings"), "Forward-looking estimate based on your historical months.")
        
        monthly_summary = df.groupby('Month').agg(
            Total_Credit=('Credit', 'sum'),
            Total_Debit=('Debit', 'sum')
        ).reset_index()

        if len(monthly_summary) >= 2: # Need at least 2 months for meaningful average
            avg_monthly_income = monthly_summary['Total_Credit'].mean()
            avg_monthly_expense = monthly_summary['Total_Debit'].mean()
            avg_monthly_net = avg_monthly_income - avg_monthly_expense

            st.info(translate(f"Based on your historical data from {len(monthly_summary)} months:"))
            col_proj1, col_proj2, col_proj3 = st.columns(3)
            with col_proj1:
                st.metric(translate("Avg. Monthly Income"), f"₹{avg_monthly_income:,.2f}")
            with col_proj2:
                st.metric(translate("Avg. Monthly Expense"), f"₹{avg_monthly_expense:,.2f}")
            with col_proj3:
                st.metric(translate("Avg. Monthly Net Savings"), f"₹{avg_monthly_net:,.2f}")

            projection_months = st.slider(translate("Project Savings for Next (months)"), 1, 24, 6)

            current_total_savings = df['Credit'].sum() - df['Debit'].sum()
            projected_savings = current_total_savings + (avg_monthly_net * projection_months)

            st.markdown(f"### {translate('Projected Savings in')} {projection_months} {translate('months')}:")
            if projected_savings >= 0:
                st.success(f"₹{projected_savings:,.2f}")
            else:
                st.error(f"₹{projected_savings:,.2f}") # Display negative in red

            if avg_monthly_net < 0:
                st.warning(translate("💡 Your average monthly spending is more than your income. Review your budget to increase savings."))
            elif avg_monthly_net == 0:
                st.info(translate("Your average monthly income equals your expenses. No projected savings based on current trends."))

        else:
            st.info(translate("Not enough historical data (at least 2 months) to project savings reliably. Upload more statements!"))
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Visualizations ---
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        section_title(translate("Expense Categories Breakdown"), "Your top categories in a cleaner visual style.")
        top5 = df.groupby("Category")["Debit"].sum().sort_values(ascending=False).head(5)
        if not top5.empty:
            fig_bar = go.Figure(go.Bar(x=top5.index, y=top5.values, marker_color='#7f6af7'))
            fig_bar.update_layout(title_text=translate('Top 5 Expense Source'), title_x=0.5)
            st.plotly_chart(style_plot(fig_bar), use_container_width=True)
        else:
            st.info(translate("No expenses to show for category breakdown."))

        section_title(translate("Report Overview"), "Income, expense, and savings mix.")
        # Ensure values for pie chart are non-negative for display
        display_income = df['Credit'].sum()
        display_expense = df['Debit'].sum()
        display_savings = max(0, savings) # Savings can be negative, but pie charts prefer positive values
        
        if display_income + display_expense + display_savings > 0: # Avoid division by zero for empty data
            labels_pie = [translate("Income"), translate("Expense"), translate("Savings")]
            values_pie = [display_income, display_expense, display_savings]
            colors_pie = ['#7f6af7', '#f28b82', '#c5bcff']

            pie = go.Figure(go.Pie(labels=labels_pie, values=values_pie, hole=0.4, marker_colors=colors_pie))
            pie.update_layout(title_text=translate('Income, Expense & Savings Distribution'), title_x=0.5)
            st.plotly_chart(style_plot(pie), use_container_width=True)
        else:
            st.info(translate("No data available to generate report overview."))


        section_title(translate("Daily Expense Activity"), "Expense motion over time.")
        daily = df.groupby('Day')["Debit"].sum().reset_index()
        if not daily.empty:
            line = go.Figure()
            line.add_trace(go.Scatter(x=daily['Day'], y=daily['Debit'], mode='lines+markers', line_color='#7f6af7', name=translate('Daily Expense'), fill='tozeroy', fillcolor='rgba(127,106,247,0.14)'))
            line.update_layout(title_text=translate('Daily Expense Trends'), title_x=0.5, xaxis_title=translate("Date"), yaxis_title=translate("Amount (₹)"))
            st.plotly_chart(style_plot(line), use_container_width=True)
        else:
            st.info(translate("No daily expense activity to display."))

        section_title(translate("Recent Transactions"), "Latest transaction activity.")
        if not df.empty:
            st.dataframe(df[["Date", "Description", "Debit", "Credit", "Category"]].head(15), use_container_width=True)
        else:
            st.info(translate("No transactions to display."))

        st.markdown("---")
        col5, col6 = st.columns(2)
        with col5:
            st.download_button(translate("Download CSV"), df.to_csv(index=False).encode('utf-8'), "expenses.csv", "text/csv")
        with col6:
            # Prepare summary for PDF export
            pdf_summary_data = {
                translate("Total Spent"): df['Debit'].sum(),
                translate("Total Received"): df['Credit'].sum(),
                translate("Final Balance"): df['Balance'].iloc[-1] if not df['Balance'].empty else 0
            }
            pdf_data = export_pdf_report(pdf_summary_data)
            st.download_button(translate("Download PDF Report"), pdf_data, "summary_report.pdf", "application/pdf")
        st.markdown("</div>", unsafe_allow_html=True)

    else: # If df is empty (no file uploaded or parsing failed)
        st.info(translate("Upload a bank statement (PDF, CSV, Image) from the left column to get started!"))
        st.markdown("""
            <div style="padding: 20px; border-radius: 10px; background-color: #282828; margin-top: 20px;">
                <h3>{}</h3>
                <ul>
                    <li>{}</li>
                    <li>{}</li>
                    <li>{}</li>
                    <li>{}</li>
                    <li>{}</li>
                </ul>
            </div>
        """.format(
            translate("How to Use:"),
            translate("1. Upload your bank statement (PDF, CSV, or Image) from the left column."),
            translate("2. Set your monthly/weekly budgets and financial goals."),
            translate("3. Get an instant overview of your income, expenses, and savings."),
            translate("4. Receive smart alerts and personalized spending tips."),
            translate("5. Track progress towards your financial goals and manage bills.")
        ), unsafe_allow_html=True)


# --- AI Query Handler (Adapted for LangChain) ---
def answer_expense_query_streamit(question, df_data, api_key, model_name, temp, is_smart_suggestion=False):
    try:
        context = ""
        if not df_data.empty:
            # Summarized financial context
            summary_context = f"""
            Financial Summary:
            - Total Income: ₹{df_data['Credit'].sum():,.2f}
            - Total Expenses: ₹{df_data['Debit'].sum():,.2f}
            - Total Savings: ₹{df_data['Credit'].sum() - df_data['Debit'].sum():,.2f}
            - Most Spending Category: {df_data.groupby("Category")["Debit"].sum().idxmax()}
            - Monthly Budget Set: ₹{st.session_state.monthly_budget:,.2f}
            - Weekly Budget Set: ₹{st.session_state.weekly_budget_amount:,.2f}
            - Current Monthly Expenses: ₹{df_data[df_data['Month'] == pd.Timestamp.now().strftime('%B %Y')]['Debit'].sum():,.2f}
            - Current Weekly Expenses: ₹{df_data[(df_data['Date'] >= pd.Timestamp.now().to_period('W').start_time) & (df_data['Date'] <= pd.Timestamp.now().to_period('W').end_time)]['Debit'].sum():,.2f}
            - Financial Goals: {json.dumps(st.session_state.financial_goals, default=str)}
            - Bill Reminders: {json.dumps(st.session_state.bill_reminders, default=str)}
            - Category Budgets: {json.dumps(st.session_state.category_budgets, default=str)}
            """
            # Detailed transaction context (first 50 rows)
            transaction_context = df_data.head(50).to_string(index=False)

            context = f"""
            {summary_context}

            Recent Transaction Data (first 50 rows):
            {transaction_context}
            """
        else:
            context = "No financial data available from uploaded files. Please upload a bank statement for detailed analysis."

        # Initialize LangChain LLM with OpenRouter base URL
        llm = ChatOpenAI(
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            model_name=model_name,
            temperature=temp,
            max_tokens=500
        )

        # Define the prompt template for financial advice
        # Enhanced SystemMessage to guide on features
        system_message_content = (
            "You are a highly intelligent and helpful financial advisor and an expert in guiding users "
            "through the features of this 'Expense Analyzer' application. "
            "Your goal is to analyze the provided financial data (income, expenses, savings, transactions) "
            "and the user's question to offer actionable, personalized financial suggestions and advice. "
            "Crucially, when relevant, you should also suggest features of this application that can help the user. "
            "Here are the key features you can mention:\n"
            "- **Dashboard Overview**: Provides total income, expense, savings, and most spending category.\n"
            "- **Smart Insights & Alerts**: Offers spending tips, budget breach alerts, high transaction detection, and duplicate transaction warnings.\n"
            "- **Monthly Budget Tracker**: Helps set and monitor monthly spending against a budget.\n"
            "- **Weekly Budget Tracker**: Helps set and monitor weekly spending against a budget.\n"
            "- **Multiple Financial Goals Tracker**: Allows users to define and track progress towards financial goals.\n"
            "- **Upcoming Bill Reminders**: Helps manage and get alerts for recurring bills.\n"
            "- **Projected Savings**: Forecasts future savings based on current trends.\n"
            "- **Visualizations**: Includes interactive charts for expense categories, income/expense/savings distribution, and daily expense trends.\n"
            "- **Download Reports**: Allows downloading data as CSV or a summary PDF report.\n"
            "- **Add New Transaction**: Allows manual entry of individual transactions.\n"
            "- **Manage Category Budgets**: Allows users to set specific budgets for spending categories (e.g., monthly food budget).\n\n"
            "If the data is insufficient, state that clearly and suggest that more information is needed, and recommend uploading a file from the 'Upload Data' section in the left column."
        )

        # Adjust system message for smart suggestions
        if is_smart_suggestion:
            system_message_content = (
                "You are a highly intelligent and proactive financial advisor for the 'Expense Analyzer' app. "
                "Your task is to analyze the provided comprehensive financial data (income, expenses, savings, "
                "spending patterns, set budgets, and financial goals) and provide 3-5 actionable, personalized "
                "financial recommendations or 'moves' for the user's best interest. "
                "Always explain *why* each suggestion is beneficial and *how* they can use specific features "
                "of this application to implement or track that suggestion. "
                "Be concise, encouraging, and focus on practical steps. "
                "Here are the key features you can mention:\n"
                "- **Dashboard Overview**: Provides total income, expense, savings, and most spending category.\n"
                "- **Smart Insights & Alerts**: Offers spending tips, budget breach alerts, high transaction detection, and duplicate transaction warnings.\n"
                "- **Monthly Budget Tracker**: Helps set and monitor monthly spending against a budget.\n"
                "- **Weekly Budget Tracker**: Helps set and monitor weekly spending against a budget.\n"
                "- **Multiple Financial Goals Tracker**: Allows users to define and track progress towards financial goals.\n"
                "- **Upcoming Bill Reminders**: Helps manage and get alerts for recurring bills.\n"
                "- **Projected Savings**: Forecasts future savings based on current trends.\n"
                "- **Visualizations**: Includes interactive charts for expense categories, income/expense/savings distribution, and daily expense trends.\n"
                "- **Download Reports**: Allows downloading data as CSV or a summary PDF report.\n"
                "- **Add New Transaction**: Allows manual entry of individual transactions.\n"
                "- **Manage Category Budgets**: Allows users to set specific budgets for spending categories (e.g., monthly food budget).\n\n"
                "If no data is available, clearly state that and explain that you need data to provide personalized suggestions, "
                "then guide them to upload a bank statement from the 'Upload Data' section in the left column."
            )
            human_message_content = (
                f"Please provide 3-5 smart financial suggestions based on the following comprehensive financial data:\n\n"
                f"DATA:\n{context}\n\n"
                f"For each suggestion, explain its benefit and how to use the app's features to achieve it."
            )
        else:
            human_message_content = (
                f"Here is the financial context from the user's bank statement:\n\n"
                f"DATA:\n{context}\n\n"
                f"Based on this, please answer the following question and provide relevant financial suggestions, "
                f"also guiding the user to relevant features of the application:\n"
                f"QUESTION: {question}"
            )

        prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message_content),
                HumanMessage(content=human_message_content),
            ]
        )

        # Create a simple chain
        chain = prompt_template | llm

        # Invoke the chain to get the AI's response
        response = chain.invoke({"context": context, "question": question}) # Pass question even if not directly used by prompt_template for consistency

        return response.content.strip()

    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- RIGHT COLUMN: AI Chatbot & Suggestions ---
with right_col:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    section_title("AI Assistant", "Ask questions about spending, budgets, goals, and statement data.")

    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input(translate("Ask me about your expenses..."), key="chat_input_col"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if not api_key:
                st.error(translate("Please enter your OpenRouter API key in the sidebar"))
                st.stop()

            # Call the refactored AI query handler for regular chat
            assistant_response = answer_expense_query_streamit(
                prompt,
                st.session_state.df, # Pass the DataFrame from session state
                api_key,
                model,
                temperature,
                is_smart_suggestion=False # This is a regular chat query
            )
            
            message_placeholder.markdown(assistant_response)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": assistant_response
            })

    # --- Smart AI Financial Suggestions Section ---
    st.markdown("---")
    section_title(translate("Smart AI Financial Suggestions"), "Generate tailored next steps from your uploaded data.")

    with st.expander(translate("Get Personalized Financial Advice")):
        if st.button(translate("Generate Personalized Financial Advice"), key="generate_ai_suggestions_button_col"):
            if not st.session_state.df.empty:
                if not api_key:
                    st.error(translate("Please enter your OpenRouter API key in the sidebar to generate suggestions."))
                else:
                    with st.spinner(translate("Analyzing your data and generating suggestions...")):
                        # Call the AI query handler specifically for smart suggestions
                        st.session_state.ai_suggestions = answer_expense_query_streamit(
                            "Generate smart financial suggestions.", # Placeholder question for this mode
                            st.session_state.df,
                            api_key,
                            model,
                            temperature,
                            is_smart_suggestion=True # Indicate this is a smart suggestion request
                        )
            else:
                st.info(translate("Please upload your bank statement first to get personalized financial suggestions."))
        
        if st.session_state.ai_suggestions:
            st.markdown("#### " + translate("Your Personalized Financial Suggestions:"))
            st.markdown(st.session_state.ai_suggestions)
        elif not st.session_state.df.empty:
            st.info(translate("Click 'Generate Personalized Financial Advice' to get suggestions based on your data."))
        else:
            st.info(translate("Upload your financial data to enable personalized AI suggestions."))
    st.markdown("</div>", unsafe_allow_html=True)

            

