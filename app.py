import os
import re
import hmac
import io
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from sklearn.ensemble import IsolationForest
except ImportError:
    IsolationForest = None


# ---------------------------------------------------------
# FinSight - personal finance dashboard
# Run with: py -m streamlit run app.py
# Demo login: admin / ChangeMe123!
# ---------------------------------------------------------

st.set_page_config(
    page_title="FinSight | Personal Finance",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Palette
NAVY = "#17243A"
NAVY_2 = "#263650"
GREEN = "#A8C995"
GREEN_LIGHT = "#EAF2E4"
BG = "#F5F7FA"
WHITE = "#FFFFFF"
TEXT = "#202B3C"
MUTED = "#718096"
BORDER = "#E3E8EF"
RED = "#D65A65"
BLUE = "#6689C6"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
        color: {TEXT};
    }}
    .stApp {{ background: {BG}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 1.35rem; padding-bottom: 2.5rem; max-width: 1450px; }}
    h1, h2, h3 {{ font-family: 'Manrope', sans-serif !important; color: {NAVY} !important; }}
    h1 {{ font-weight: 800 !important; letter-spacing: -1px; }}
    h2 {{ font-weight: 750 !important; letter-spacing: -0.5px; }}
    h3 {{ font-weight: 700 !important; }}

    /* Buttons: visible text, high contrast, clear hover/focus state */
    div.stButton > button, div.stFormSubmitButton > button,
    div[data-testid="stDownloadButton"] > button {{
        background: {NAVY} !important;
        color: #FFFFFF !important;
        border: 1px solid {NAVY} !important;
        border-radius: 10px !important;
        min-height: 43px;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(23,36,58,.10);
        transition: all .18s ease-in-out;
    }}
    div.stButton > button p, div.stFormSubmitButton > button p,
    div[data-testid="stDownloadButton"] > button p {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}
    div.stButton > button:hover, div.stFormSubmitButton > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {{
        background: {NAVY_2} !important;
        color: #FFFFFF !important;
        border-color: {GREEN} !important;
        transform: translateY(-1px);
    }}
    div.stButton > button:focus, div.stFormSubmitButton > button:focus {{
        outline: 3px solid {GREEN} !important;
        outline-offset: 2px;
    }}

    /* Top navigation radio styled as clear, clickable tabs */
    div[role="radiogroup"] {{
        gap: 8px !important;
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 8px;
        width: fit-content;
        max-width: 100%;
        flex-wrap: wrap;
    }}
    div[role="radiogroup"] label {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 9px;
        padding: 8px 13px;
        margin: 0 !important;
        cursor: pointer !important;
        color: {NAVY} !important;
        font-weight: 700 !important;
    }}
    div[role="radiogroup"] label p {{
        color: {NAVY} !important;
        font-weight: 700 !important;
    }}
    div[role="radiogroup"] label:has(input:checked) {{
        background: {NAVY} !important;
        border-color: {NAVY} !important;
    }}
    div[role="radiogroup"] label:has(input:checked) p {{
        color: #FFFFFF !important;
    }}
    div[role="radiogroup"] label:hover {{
        background: {GREEN_LIGHT} !important;
        border-color: {GREEN} !important;
    }}

    /* Cards */
    .brand-row {{ display:flex; align-items:center; gap:12px; margin-bottom: 8px; }}
    .brand-mark {{
        width:44px; height:44px; display:flex; align-items:center; justify-content:center;
        border-radius:14px; background:{NAVY}; color:{GREEN}; font-size:25px; font-weight:800;
    }}
    .brand-name {{ font-family:'Manrope',sans-serif; font-size:24px; font-weight:800; color:{NAVY}; line-height:1.05; }}
    .brand-sub {{ color:{MUTED}; font-size:12px; margin-top:4px; }}
    .hero {{
        background: linear-gradient(120deg, {NAVY} 0%, {NAVY_2} 100%);
        border-radius: 22px; padding: 27px 30px; color: white; margin: 12px 0 20px;
        box-shadow: 0 12px 28px rgba(23,36,58,.12);
    }}
    .hero-kicker {{ color:{GREEN}; font-size:12px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; }}
    .hero-title {{ color:white; font-family:'Manrope',sans-serif; font-size:30px; font-weight:800; margin:8px 0 6px; }}
    .hero-text {{ color:#D8E0EA; font-size:14px; }}
    .metric-card {{
        background:{WHITE}; border:1px solid {BORDER}; border-radius:16px;
        padding:18px 19px; min-height:116px; box-shadow:0 4px 15px rgba(31,48,72,.035);
    }}
    .metric-label {{ color:{MUTED}; font-size:12px; font-weight:700; letter-spacing:.4px; text-transform:uppercase; }}
    .metric-value {{ color:{NAVY}; font-family:'Manrope',sans-serif; font-size:25px; font-weight:800; margin-top:9px; }}
    .metric-note {{ color:{MUTED}; font-size:12px; margin-top:4px; }}
    .section-head {{ margin: 20px 0 10px; }}
    .section-sub {{ color:{MUTED}; margin-top:-5px; margin-bottom:14px; font-size:13px; }}
    .info-card {{ background:{WHITE}; border:1px solid {BORDER}; border-radius:16px; padding:18px; }}
    .small-muted {{ color:{MUTED}; font-size:12px; }}
    .login-wrap {{ max-width:470px; margin: 3rem auto 0; }}
    .login-panel {{ background:{WHITE}; border:1px solid {BORDER}; border-radius:22px; padding:28px; box-shadow:0 15px 40px rgba(23,36,58,.08); }}
    [data-testid="stFileUploader"] {{
        background:{WHITE}; border:1px dashed #9AAABD; border-radius:14px; padding:12px;
        position:relative; z-index:1; color:{NAVY};
    }}
    [data-testid="stFileUploader"] section {{ background:{WHITE}; }}
    [data-testid="stFileUploader"] button {{
        background:{NAVY} !important; color:#FFFFFF !important;
        border:1px solid {NAVY} !important; border-radius:8px !important;
        font-weight:700 !important; cursor:pointer !important;
    }}
    [data-testid="stFileUploader"] button p {{ color:#FFFFFF !important; }}
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span {{ color:{TEXT}; }}
    [data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; overflow:hidden; }}
    hr {{ border-color:{BORDER}; }}
    /* Simple high-contrast horizontal menu */
    div[role="radiogroup"] {{ width:100%; display:flex; gap:8px; flex-wrap:wrap; background:transparent; border:0; padding:0; }}
    div[role="radiogroup"] label {{ flex:1 1 auto; justify-content:center; text-align:center; min-height:44px; background:#FFFFFF; border:1px solid {BORDER}; border-radius:10px; padding:10px 14px; color:{NAVY} !important; }}
    div[role="radiogroup"] label p {{ color:{NAVY} !important; font-weight:700 !important; }}
    div[role="radiogroup"] label:has(input:checked) {{ background:{NAVY} !important; border-color:{NAVY} !important; }}
    div[role="radiogroup"] label:has(input:checked) p {{ color:#FFFFFF !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value):
    try:
        return "₹{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "₹0.00"


def brand():
    st.markdown(
        f"""
        <div class="brand-row">
          <div class="brand-mark">◈</div>
          <div>
            <div class="brand-name">FinSight</div>
            <div class="brand-sub">PERSONAL FINANCE INTELLIGENCE</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def login_page():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    brand()
    st.markdown(
        f"""
        <div class="login-panel">
          <div style="color:{GREEN if False else NAVY};font-size:12px;font-weight:800;letter-spacing:1.4px;">WELCOME BACK</div>
          <div style="font-family:Manrope,sans-serif;color:{NAVY};font-size:29px;font-weight:800;margin:7px 0;">Your money, in focus.</div>
          <div style="color:{MUTED};font-size:14px;margin-bottom:18px;">Sign in to explore your spending and cash flow.</div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        expected_user = os.getenv("FINSIGHT_USERNAME", "admin")
        expected_password = os.getenv("FINSIGHT_PASSWORD", "ChangeMe123!")
        if hmac.compare_digest(username.strip(), expected_user) and hmac.compare_digest(password, expected_password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username.strip()
            st.rerun()
        else:
            st.error("Incorrect username or password. Check spelling and capital letters.")
    st.markdown(
        f'<div class="small-muted" style="margin:14px 0 0;">Local demo login: <b>admin</b> / <b>ChangeMe123!</b></div></div></div>',
        unsafe_allow_html=True,
    )


def categorize(description):
    d = str(description).lower()
    rules = {
        "Groceries": ["zepto", "bigbasket", "grocery", "supermarket", "reliance fresh", "vegetable", "fruit"],
        "Food & Dining": ["swiggy", "zomato", "restaurant", "hotel", "cafe", "food", "bakery"],
        "Transport": ["uber", "ola", "rapido", "metro", "petrol", "fuel", "irctc", "redbus", "bus", "train"],
        "Shopping": ["amazon", "flipkart", "myntra", "meesho", "shopping", "store"],
        "Bills & Recharge": ["airtel", "jio", "vi ", "recharge", "electricity", "eb bill", "broadband", "water bill"],
        "Healthcare": ["hospital", "medical", "pharmacy", "clinic", "doctor", "apollo"],
        "Education": ["college", "school", "course", "udemy", "coursera", "exam", "books"],
        "Entertainment": ["netflix", "spotify", "movie", "cinema", "hotstar", "prime video"],
        "Transfers": ["upi", "transfer", "sent to", "paid to", "received from", "imps", "neft", "rtgs"],
    }
    for category, keywords in rules.items():
        if any(word in d for word in keywords):
            return category
    return "Others"


def parse_pdf(uploaded_file):
    if pdfplumber is None:
        st.error("PDF support needs pdfplumber. Install it with: py -m pip install pdfplumber")
        return pd.DataFrame()
    rows = []
    try:
        uploaded_file.seek(0)
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as exc:
        st.error(f"Could not read this PDF: {exc}")
        return pd.DataFrame()

    # Handles transaction-like lines with a date and one or more amounts.
    date_pattern = re.compile(
        r"(?P<date>\d{1,2}\s*[A-Za-z]{3,9}\s*,?\s*\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
    )
    amount_pattern = re.compile(r"(?:₹|Rs\.?\s*)?([\d,]+\.\d{2})")
    for line in text.splitlines():
        line = " ".join(line.split())
        dm = date_pattern.search(line)
        am = list(amount_pattern.finditer(line))
        if not dm or not am:
            continue
        date_text = dm.group("date").replace(",", "").strip()
        parsed_date = pd.to_datetime(date_text, errors="coerce", dayfirst=True)
        if pd.isna(parsed_date):
            continue
        # Ignore lines with too little information and obvious summaries.
        description = (line[:dm.start()] + " " + line[dm.end():am[-1].start()]).strip(" -|:")
        if len(description) < 2:
            description = line[dm.end():am[-1].start()].strip(" -|:")
        if not description or any(x in description.lower() for x in ["opening balance", "closing balance", "statement period"]):
            continue
        amount = float(am[-1].group(1).replace(",", ""))
        lower = line.lower()
        if any(x in lower for x in ["received from", "receivedfrom", "credit", "credited", "deposit"]):
            typ = "Income"
        elif any(x in lower for x in ["paid to", "paidto", "sent to", "sentto", "debit", "debited", "withdrawal"]):
            typ = "Expense"
        else:
            # Bank statement lines are most often debits when no clear credit marker exists.
            typ = "Expense"
        rows.append({"Date": parsed_date, "Description": description, "Amount": amount, "Type": typ})

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates().sort_values("Date").reset_index(drop=True)
        df["Category"] = df["Description"].apply(categorize)
    return df


def normalize_data(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Date", "Description", "Amount", "Type", "Category"])
    df = df.copy()
    # Normalize common column names from CSV uploads.
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace("_", " ")
        if key in ["date", "transaction date", "txn date"]:
            rename[col] = "Date"
        elif key in ["description", "details", "narration", "merchant", "particulars"]:
            rename[col] = "Description"
        elif key in ["amount", "transaction amount", "value"]:
            rename[col] = "Amount"
        elif key in ["type", "transaction type", "debit credit", "income expense"]:
            rename[col] = "Type"
        elif key in ["category", "expense category"]:
            rename[col] = "Category"
    df = df.rename(columns=rename)
    if "Date" not in df.columns or "Amount" not in df.columns:
        return pd.DataFrame(columns=["Date", "Description", "Amount", "Type", "Category"])
    if "Description" not in df.columns:
        df["Description"] = "Transaction"
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
    df["Amount"] = (
        df["Amount"].astype(str).str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False).str.replace("Rs.", "", regex=False).str.strip()
    )
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").abs()
    df = df.dropna(subset=["Date", "Amount"])
    if "Type" not in df.columns:
        df["Type"] = "Expense"
    df["Type"] = df["Type"].astype(str).str.strip().str.title()
    df["Type"] = df["Type"].replace({
        "Credit": "Income", "Cr": "Income", "Received": "Income",
        "Debit": "Expense", "Dr": "Expense", "Spent": "Expense"
    })
    df.loc[~df["Type"].isin(["Income", "Expense"]), "Type"] = "Expense"
    if "Category" not in df.columns:
        df["Category"] = df["Description"].apply(categorize)
    df["Category"] = df["Category"].fillna("").astype(str)
    df.loc[df["Category"].str.strip() == "", "Category"] = df.loc[
        df["Category"].str.strip() == "", "Description"
    ].apply(categorize)
    return df[["Date", "Description", "Amount", "Type", "Category"]].sort_values("Date").reset_index(drop=True)


def metric(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def get_totals(df):
    income = df.loc[df["Type"] == "Income", "Amount"].sum()
    expense = df.loc[df["Type"] == "Expense", "Amount"].sum()
    return income, expense, income - expense


def chart_layout(fig, height=330):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=35, b=8),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        font=dict(family="DM Sans", color=TEXT, size=12),
        title_font=dict(family="Manrope", size=16, color=NAVY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDER)
    fig.update_yaxes(gridcolor="#EDF0F4", zerolinecolor=BORDER)
    return fig



def detect_subscriptions(df):
    """Find likely recurring subscription merchants from descriptions."""
    if df.empty:
        return pd.DataFrame(columns=["Merchant", "Transactions", "Total", "Last payment", "Category"])
    keywords = ["netflix", "spotify", "hotstar", "prime video", "amazon prime",
                "youtube premium", "google", "apple", "adobe", "canva", "subscription",
                "membership", "ott", "jio cinema"]
    exp = df[df["Type"] == "Expense"].copy()
    exp["Description"] = exp["Description"].astype(str)
    exp = exp[exp["Description"].str.lower().apply(lambda x: any(k in x for k in keywords))]
    if exp.empty:
        return pd.DataFrame(columns=["Merchant", "Transactions", "Total", "Last payment", "Category"])
    result = exp.groupby("Description").agg(
        Transactions=("Amount", "size"),
        Total=("Amount", "sum"),
        Last_payment=("Date", "max"),
        Category=("Category", "first")
    ).reset_index().rename(columns={"Description": "Merchant", "Last_payment": "Last payment"})
    return result.sort_values("Total", ascending=False)


def unusual_transactions(df):
    if df.empty or IsolationForest is None:
        return pd.DataFrame()
    exp = df[df["Type"] == "Expense"].copy()
    if len(exp) < 8:
        return pd.DataFrame()
    model = IsolationForest(contamination=0.08, random_state=42)
    exp["Anomaly"] = model.fit_predict(exp[["Amount"]])
    return exp[exp["Anomaly"] == -1].sort_values("Amount", ascending=False)


def goals_page(df):
    st.title("Goal-based Spending")
    st.caption("Tell FinSight your savings target and get a practical plan based on your own spending.")
    if df.empty:
        st.info("Upload your bank statement on Overview first. Your transactions will be available here automatically.")
        return

    goal_name = st.text_input("What are you saving for?", value="My ₹10,000 savings goal", key="goal_name")
    c1, c2 = st.columns(2)
    with c1:
        goal_amount = st.number_input("Savings target (₹)", min_value=500.0, value=10000.0, step=500.0, key="goal_amount")
        months = st.selectbox("When do you want to reach it?", [1, 2, 3, 4, 6, 12], index=2, format_func=lambda x: f"Within {x} month{'s' if x != 1 else ''}", key="goal_months")
    with c2:
        current_savings = st.number_input("Already saved for this goal (₹)", min_value=0.0, value=0.0, step=500.0, key="goal_saved")
        remaining = max(0.0, float(goal_amount) - float(current_savings))
        monthly_target = remaining / months
        st.metric("Still to save", money(remaining))
        st.metric("Savings needed each month", money(monthly_target))
        st.progress(min(1.0, current_savings / goal_amount))

    expenses = df[df["Type"] == "Expense"].copy()
    if expenses.empty:
        st.info("No expense transactions were found to create a spending-reduction plan.")
        return

    # Use monthly average by category so targets remain useful across statement lengths.
    expenses["Month"] = expenses["Date"].dt.to_period("M")
    month_count = max(1, expenses["Month"].nunique())
    category_monthly = (expenses.groupby("Category")["Amount"].sum() / month_count).sort_values(ascending=False)
    st.markdown("### Your personalised savings plan")
    st.markdown(
        f"<div style='background:#17243A;border-radius:16px;padding:18px 20px;margin:8px 0 16px;'>"
        f"<div style='color:#A8C995;font-size:12px;font-weight:700;text-transform:uppercase;'>TARGET PLAN</div>"
        f"<div style='color:white;font-size:25px;font-weight:800;margin:5px 0;'>{money(monthly_target)} to save each month</div>"
        f"<div style='color:#E1E8F0;'>Goal: {goal_name or 'Savings goal'} · Deadline: {months} month(s) · Remaining: {money(remaining)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("FinSight compares your average monthly spending by category and estimates where you could cut back. Suggested cuts are optional—protect essential bills, food, healthcare, education, and necessary travel.")

    suggestions = []
    remaining_monthly = monthly_target
    # Suggest up to a 25% reduction from the largest categories first, prioritising flexible spend.
    flexible_first = ["Food & Dining", "Shopping", "Entertainment", "Others", "Groceries", "Transport", "Bills & Recharge"]
    ordered = sorted(category_monthly.items(), key=lambda item: (flexible_first.index(item[0]) if item[0] in flexible_first else len(flexible_first), -item[1]))
    for category, avg_amount in ordered:
        if remaining_monthly <= 0:
            break
        cap = float(avg_amount) * (0.25 if category in ["Food & Dining", "Shopping", "Entertainment", "Others"] else 0.15)
        cut = min(cap, remaining_monthly)
        if cut >= 1:
            suggestions.append({"Category": category, "Estimated monthly spend": round(float(avg_amount), 2), "Suggested reduction": round(cut, 2), "New target spend": round(max(0, float(avg_amount)-cut), 2)})
            remaining_monthly -= cut

    if suggestions:
        plan = pd.DataFrame(suggestions)
        plan["Estimated monthly spend"] = plan["Estimated monthly spend"].map(money)
        plan["Suggested reduction"] = plan["Suggested reduction"].map(money)
        plan["New target spend"] = plan["New target spend"].map(money)
        st.dataframe(plan, hide_index=True, use_container_width=True)
        suggested_total = sum(x["Suggested reduction"] for x in suggestions)
        st.success(f"Suggested potential savings: {money(suggested_total)} per month.")
        if remaining_monthly > 0:
            st.warning(f"The target needs another {money(remaining_monthly)} per month beyond these suggested cuts. Consider a longer timeline or a smaller goal rather than cutting essential expenses.")
    else:
        st.warning("There is not enough category spending in this statement to suggest reductions. Try a longer timeline or check whether your statement includes all expenses.")

    st.markdown("#### Your average monthly spending by category")
    cat_view = category_monthly.rename("Average monthly spend").reset_index().sort_values("Average monthly spend", ascending=False)
    cat_view["Average monthly spend"] = cat_view["Average monthly spend"].map(money)
    st.dataframe(cat_view, hide_index=True, use_container_width=True)
    st.caption("Keep essential bills, medication, education, and necessary travel protected. Review the suggested reductions and choose only the ones realistic for you.")


def subscriptions_page(df):
    st.title("Subscription tracker")
    st.caption("Flags likely subscriptions based on words in transaction descriptions. Verify these suggestions.")
    subs = detect_subscriptions(df)
    if subs.empty:
        st.info("No likely subscriptions detected yet. Transactions containing names such as Netflix, Spotify, Prime Video, Hotstar, Canva or 'subscription' will appear here.")
        if not df.empty:
            st.markdown("#### Expense descriptions to review")
            st.dataframe(df[df["Type"] == "Expense"][["Date", "Description", "Amount", "Category"]].sort_values("Date", ascending=False).head(15), hide_index=True, use_container_width=True)
        return
    st.metric("Likely subscription merchants", len(subs))
    st.dataframe(subs, hide_index=True, use_container_width=True)
    st.caption("This tracker uses statement text, not bank-authorized subscription cancellation. Repeated merchant names are suggestions, not proof of a recurring payment.")


def coach_reply(question, df):
    """A small local finance chatbot; responses are generated from uploaded transaction data."""
    q = question.lower().strip()
    if df.empty:
        return "Please upload and analyse a bank statement first. Then I can answer using the transactions in that statement."
    income, expense, balance = get_totals(df)
    expenses = df[df["Type"] == "Expense"].copy()
    if any(word in q for word in ["balance", "left", "remaining money", "net"]):
        return f"Your recorded income is {money(income)}, expenses are {money(expense)}, and net balance is {money(balance)}. This is calculated only from transactions successfully extracted from your uploaded statement."
    if any(word in q for word in ["income", "earned", "received"]):
        return f"Your recorded income total is {money(income)} across {len(df[df['Type'] == 'Income'])} income transaction(s). Please verify that all credit entries were extracted correctly."
    if any(word in q for word in ["expense", "spent", "spending", "where"]):
        if expenses.empty:
            return "I couldn't find expense transactions in this statement. Please check the imported transaction types."
        cats = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        top = cats.head(3)
        details = "; ".join(f"{name}: {money(value)}" for name, value in top.items())
        return f"Your total recorded expenses are {money(expense)}. Your highest-spending categories are: {details}. Start by checking optional purchases and repeat payments in the largest categories; don't cut essential spending without considering your needs."
    if any(word in q for word in ["save", "saving", "goal", "10000", "10k"]):
        if expenses.empty:
            return "I need expense transactions to suggest realistic savings. Upload a statement containing your spending first."
        cats = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        first = cats.index[0]
        return f"For a ₹10,000 goal, first choose a deadline. For example, over 3 months you need about ₹3,334 each month. Your largest category in this statement is {first} ({money(cats.iloc[0])} over the uploaded period). Review the Goal-based Spending page for a category-by-category reduction plan."
    if any(word in q for word in ["subscription", "netflix", "spotify", "recurring"]):
        subs = detect_subscriptions(df)
        if subs.empty:
            return "I couldn't confidently identify subscriptions from the descriptions. Open Subscription Tracker and review recurring-looking merchant names; bank statement text may not clearly label every subscription."
        names = ", ".join(subs["Merchant"].astype(str).head(5).tolist())
        return f"I found these likely subscription-related descriptions: {names}. Please verify they are recurring and still useful before cancelling anything."
    if any(word in q for word in ["unusual", "large transaction", "fraud", "suspicious"]):
        flagged = unusual_transactions(df)
        if flagged.empty:
            return "There are not enough expense transactions for the anomaly model, or no transactions were flagged. A flag is only a prompt to review—not proof of fraud."
        rows = flagged.head(3)
        details = "; ".join(f"{r['Description']} ({money(r['Amount'])})" for _, r in rows.iterrows())
        return f"The model flagged these amounts for review: {details}. Check the date and merchant against your own records; unusual does not automatically mean fraudulent."
    return (f"Here's your snapshot: income {money(income)}, expenses {money(expense)}, net balance {money(balance)}. "
            "You can ask me things like ‘Where am I spending the most?’, ‘How can I save ₹10,000?’, ‘What is my balance?’, or ‘Show subscriptions’. I use simple local rules and your uploaded data; I am not connected to a live bank or an external AI model.")


def coach_page(df):
    st.title("AI Finance Coach")
    st.caption("Ask a question about your uploaded transactions. The local coach uses your statement data.")

    if "coach_chat" not in st.session_state:
        st.session_state["coach_chat"] = []

    if df.empty:
        st.warning("Upload and analyse your statement on the Overview page first.")
    else:
        income, expense, balance = get_totals(df)
        c1, c2, c3 = st.columns(3)
        with c1:
            metric("Income", money(income))
        with c2:
            metric("Expenses", money(expense))
        with c3:
            metric("Net balance", money(balance))

    # Prominent chatbot panel
    st.markdown(
        """
        <div style="background:#17243A;border-radius:16px;padding:20px;margin:18px 0 12px;">
          <div style="font-size:23px;font-weight:800;color:#FFFFFF;">💬 Chat with FinSight</div>
          <div style="font-size:14px;color:#E1E8F0;margin-top:6px;">
            Ask me where your money goes, how to reduce expenses, or how to reach a savings goal.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Quick questions — click one to get an answer:**")
    quick_questions = [
        "Where am I spending the most?",
        "How can I save ₹10,000?",
        "What is my balance?",
        "Show subscriptions",
    ]
    qcols = st.columns(2)
    for i, q in enumerate(quick_questions):
        with qcols[i % 2]:
            if st.button(q, key=f"coach_quick_{i}", use_container_width=True):
                st.session_state["coach_chat"].append({"role": "user", "content": q})
                st.session_state["coach_chat"].append({"role": "assistant", "content": coach_reply(q, df)})

    st.markdown("### Conversation")
    if not st.session_state["coach_chat"]:
        st.info("Your conversation will appear here. Type a question below and press Send message.")
    else:
        for message in st.session_state["coach_chat"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with st.form("coach_send_form", clear_on_submit=True):
        question = st.text_input(
            "Type your question here",
            placeholder="Example: How can I reduce my food spending?",
            key="coach_question_input",
        )
        sent = st.form_submit_button("Send message ➤", use_container_width=True)

    if sent:
        if not question.strip():
            st.warning("Please type a question before sending.")
        else:
            st.session_state["coach_chat"].append({"role": "user", "content": question.strip()})
            st.session_state["coach_chat"].append({"role": "assistant", "content": coach_reply(question.strip(), df)})
            st.rerun()

    if st.session_state["coach_chat"]:
        if st.button("Clear conversation", key="coach_clear_conversation"):
            st.session_state["coach_chat"] = []
            st.rerun()

    st.caption("Note: this is a local rule-based chatbot, not a connected external generative AI service.")


def overview_page(df):
    st.markdown(
        """
        <div class="hero">
          <div class="hero-kicker">YOUR FINANCIAL SNAPSHOT</div>
          <div class="hero-title">Make every rupee count.</div>
          <div class="hero-text">Understand your cash flow, discover spending patterns, and stay in control.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Upload or replace your bank statement")
    st.caption("Choose a PDF or CSV and click Analyse. Your dashboard, charts and insights will update automatically below.")
    uploaded = st.file_uploader("Choose bank statement (PDF or CSV)", type=["pdf", "csv"], key="overview_upload")
    if uploaded is not None and st.button("Upload and analyse statement", key="overview_process", use_container_width=True):
        with st.spinner("Reading your statement..."):
            if uploaded.name.lower().endswith(".pdf"):
                parsed = parse_pdf(uploaded)
            else:
                try:
                    parsed = normalize_data(pd.read_csv(uploaded))
                except Exception as exc:
                    st.error(f"Could not read the CSV: {exc}")
                    parsed = pd.DataFrame()
            parsed = normalize_data(parsed)
            if parsed.empty:
                st.error("No transactions could be detected. Try a CSV with Date, Description, Amount, and Type columns.")
            else:
                st.session_state["transactions_df"] = parsed
                st.success(f"Loaded {len(parsed)} transactions. All dashboard details are updated below.")
                st.rerun()
    if df.empty:
        st.info("Upload a statement above to display income, expenses, charts, unusual spending, goals, coach suggestions and subscription tracking.")
        return
    income, expense, balance = get_totals(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric("Total income", money(income), "All uploaded transactions")
    with c2: metric("Total expenses", money(expense), "All uploaded transactions")
    with c3: metric("Net balance", money(balance), "Income minus expenses")
    with c4: metric("Transactions", f"{len(df):,}", "Cleaned transaction records")

    monthly = df.assign(Month=df["Date"].dt.to_period("M").astype(str)).groupby(["Month", "Type"])["Amount"].sum().reset_index()
    st.markdown('<div class="section-head">Cash flow over time</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Compare monthly income with monthly expenses.</div>', unsafe_allow_html=True)
    fig = px.bar(monthly, x="Month", y="Amount", color="Type", barmode="group",
                 color_discrete_map={"Income": GREEN, "Expense": NAVY_2})
    st.plotly_chart(chart_layout(fig, 350), use_container_width=True)

    left, right = st.columns(2)
    expenses = df[df["Type"] == "Expense"]
    with left:
        st.markdown('<div class="section-head">Where your money goes</div>', unsafe_allow_html=True)
        if expenses.empty:
            st.info("No expense transactions found.")
        else:
            cat = expenses.groupby("Category", as_index=False)["Amount"].sum().sort_values("Amount", ascending=False)
            fig = px.pie(cat, names="Category", values="Amount", hole=.62)
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(chart_layout(fig, 340), use_container_width=True)
    with right:
        st.markdown('<div class="section-head">Recent transactions</div>', unsafe_allow_html=True)
        recent = df.sort_values("Date", ascending=False).head(7).copy()
        recent["Date"] = recent["Date"].dt.strftime("%d %b %Y")
        recent["Amount"] = recent.apply(lambda r: ("+" if r["Type"] == "Income" else "−") + money(r["Amount"]), axis=1)
        st.dataframe(recent[["Date", "Description", "Category", "Type", "Amount"]], hide_index=True, use_container_width=True)

    # Show all key insights on Overview immediately after a statement is uploaded.
    st.markdown("---")
    st.markdown("## More insights from your statement")
    tab1, tab2, tab3, tab4 = st.tabs(["Spending patterns", "Monthly analysis", "Unusual spending", "Subscription tracker"])
    with tab1:
        if expenses.empty:
            st.info("No expense transactions found.")
        else:
            category_totals = expenses.groupby("Category", as_index=False)["Amount"].sum().sort_values("Amount", ascending=False)
            st.plotly_chart(chart_layout(px.bar(category_totals, x="Category", y="Amount", color="Category",
                                                title="Spending by category"), 360), use_container_width=True)
    with tab2:
        st.plotly_chart(chart_layout(px.line(monthly, x="Month", y="Amount", color="Type", markers=True,
                                             title="Monthly income and expenses"), 360), use_container_width=True)
    with tab3:
        flagged = unusual_transactions(df)
        if flagged.empty:
            st.info("No unusual transactions were flagged, or there are not enough expense transactions for anomaly detection.")
        else:
            st.warning("These transactions differ from the amount pattern and should be reviewed. A flag does not mean fraud.")
            st.dataframe(flagged[["Date", "Description", "Amount", "Category"]], hide_index=True, use_container_width=True)
    with tab4:
        subs = detect_subscriptions(df)
        if subs.empty:
            st.info("No likely subscription charges detected from description keywords. Check the Subscription Tracker menu for more details.")
        else:
            st.dataframe(subs, hide_index=True, use_container_width=True)


def analytics_page(df):
    st.title("Analytics")
    st.caption("Explore spending patterns and monthly changes.")
    if df.empty:
        st.info("Upload a statement first.")
        return
    expenses = df[df["Type"] == "Expense"].copy()
    a, b = st.columns(2)
    with a:
        st.markdown("#### Expense categories")
        if expenses.empty:
            st.info("No expenses found.")
        else:
            cat = expenses.groupby("Category", as_index=False)["Amount"].sum().sort_values("Amount", ascending=True)
            fig = px.bar(cat, x="Amount", y="Category", orientation="h", text_auto=".2s",
                         color_discrete_sequence=[NAVY_2])
            st.plotly_chart(chart_layout(fig, max(320, 35 * len(cat))), use_container_width=True)
    with b:
        st.markdown("#### Monthly savings")
        temp = df.assign(Month=df["Date"].dt.to_period("M").astype(str))
        pivot = temp.pivot_table(index="Month", columns="Type", values="Amount", aggfunc="sum", fill_value=0).reset_index()
        if "Income" not in pivot: pivot["Income"] = 0
        if "Expense" not in pivot: pivot["Expense"] = 0
        pivot["Net balance"] = pivot["Income"] - pivot["Expense"]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=pivot["Month"], y=pivot["Income"], name="Income", marker_color=GREEN))
        fig.add_trace(go.Bar(x=pivot["Month"], y=pivot["Expense"], name="Expense", marker_color=NAVY_2))
        fig.add_trace(go.Scatter(x=pivot["Month"], y=pivot["Net balance"], name="Net balance", mode="lines+markers", line=dict(color=BLUE, width=3)))
        fig.update_layout(barmode="group")
        st.plotly_chart(chart_layout(fig, 350), use_container_width=True)
    st.markdown("#### Monthly breakdown")
    monthly = df.assign(Month=df["Date"].dt.to_period("M").astype(str)).pivot_table(
        index="Month", columns="Type", values="Amount", aggfunc="sum", fill_value=0
    ).reset_index()
    if "Income" not in monthly: monthly["Income"] = 0
    if "Expense" not in monthly: monthly["Expense"] = 0
    monthly["Net balance"] = monthly["Income"] - monthly["Expense"]
    st.dataframe(monthly, hide_index=True, use_container_width=True)


def transactions_page(df):
    st.title("Transactions")
    st.caption("Search, filter, and export your transaction history.")
    if df.empty:
        st.info("No transactions loaded yet. Upload a PDF or CSV from Statements.")
        return
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search = st.text_input("Search description or category", placeholder="e.g. groceries, UPI, transport")
    with c2:
        kind = st.selectbox("Transaction type", ["All", "Income", "Expense"])
    with c3:
        categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
        category = st.selectbox("Category", categories)
    filtered = df.copy()
    if search.strip():
        filtered = filtered[
            filtered["Description"].astype(str).str.contains(search, case=False, na=False)
            | filtered["Category"].astype(str).str.contains(search, case=False, na=False)
        ]
    if kind != "All":
        filtered = filtered[filtered["Type"] == kind]
    if category != "All":
        filtered = filtered[filtered["Category"] == category]
    st.caption(f"{len(filtered):,} transaction(s)")
    view = filtered.sort_values("Date", ascending=False).copy()
    view["Date"] = view["Date"].dt.strftime("%d %b %Y")
    st.dataframe(view, hide_index=True, use_container_width=True)
    st.download_button(
        "Download filtered transactions (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="finsight_transactions.csv",
        mime="text/csv",
        use_container_width=False,
    )


def insights_page(df):
    st.title("AI Insights")
    st.caption("Rule-based summaries and optional machine-learning anomaly detection.")
    if df.empty:
        st.info("Upload a statement first.")
        return
    income, expense, balance = get_totals(df)
    expense_df = df[df["Type"] == "Expense"]
    if expense > income:
        st.warning(f"Your expenses are {money(expense - income)} higher than your recorded income for this dataset.")
    else:
        st.success(f"Your recorded income exceeds expenses by {money(balance)}.")
    if not expense_df.empty:
        cat = expense_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        st.markdown("#### Spending summary")
        st.write(f"Your highest spending category is **{cat.index[0]}** at **{money(cat.iloc[0])}**.")
        month_totals = expense_df.assign(Month=expense_df["Date"].dt.to_period("M").astype(str)).groupby("Month")["Amount"].sum()
        if len(month_totals) >= 2:
            change = month_totals.iloc[-1] - month_totals.iloc[-2]
            if change > 0:
                st.write(f"Expenses rose by **{money(change)}** compared with the previous month.")
            else:
                st.write(f"Expenses fell by **{money(abs(change))}** compared with the previous month.")
    st.markdown("#### Unusual transaction detection")
    if IsolationForest is None:
        st.info("Install scikit-learn to enable anomaly detection: py -m pip install scikit-learn")
        return
    if len(expense_df) < 8:
        st.info("At least 8 expense transactions are needed to run anomaly detection.")
        return
    features = expense_df[["Amount"]].copy()
    model = IsolationForest(contamination=0.08, random_state=42)
    model.fit(features)
    expense_df = expense_df.copy()
    expense_df["Anomaly"] = model.predict(features)
    unusual = expense_df[expense_df["Anomaly"] == -1].sort_values("Amount", ascending=False)
    if unusual.empty:
        st.success("No unusual transactions were flagged in this dataset.")
    else:
        st.warning(f"{len(unusual)} transaction(s) were flagged for review. This does not necessarily mean they are fraudulent.")
        unusual["Date"] = unusual["Date"].dt.strftime("%d %b %Y")
        st.dataframe(unusual[["Date", "Description", "Amount", "Category"]], hide_index=True, use_container_width=True)


def statements_page():
    st.title("Statements")
    st.caption("Upload a bank statement PDF or transaction CSV. Your imported data stays available while this app session is active.")

    st.markdown("### 1. Choose your statement")
    st.write("Select **Browse files** below, then choose a PDF or CSV from your computer. You can also drag and drop the file into the upload area.")

    # Keep the uploader outside raw HTML wrappers. Wrapping Streamlit widgets
    # in hand-written opening/closing div tags can break the page DOM and clicks.
    uploaded = st.file_uploader(
        "Choose a PDF or CSV file",
        type=["pdf", "csv"],
        key="statement_upload",
        help="Supported formats: PDF bank statements and CSV transaction files.",
        label_visibility="visible",
    )

    if uploaded is not None:
        st.success(f"Selected file: {uploaded.name}")
        st.markdown("### 2. Import transactions")
        if st.button("Process statement", key="process_statement", type="primary", use_container_width=True):
            with st.spinner("Reading your statement..."):
                if uploaded.name.lower().endswith(".pdf"):
                    parsed = parse_pdf(uploaded)
                else:
                    try:
                        uploaded.seek(0)
                        parsed = normalize_data(pd.read_csv(uploaded))
                    except Exception as exc:
                        st.error(f"Could not read the CSV: {exc}")
                        parsed = pd.DataFrame()
                parsed = normalize_data(parsed)
                if parsed.empty:
                    st.error("No transactions were detected. For CSV, include Date, Description, Amount, and Type columns. For PDF, use a statement with selectable text.")
                else:
                    st.session_state["transactions_df"] = parsed
                    st.success(f"Successfully loaded {len(parsed)} transactions.")
                    st.rerun()

    current = st.session_state.get("transactions_df", pd.DataFrame())
    if not current.empty:
        st.markdown("---")
        st.markdown("### Current dataset")
        inc, exp, bal = get_totals(current)
        c1, c2, c3 = st.columns(3)
        with c1:
            metric("Income", money(inc))
        with c2:
            metric("Expenses", money(exp))
        with c3:
            metric("Net balance", money(bal))
        if st.button("Clear loaded data", key="clear_data"):
            st.session_state["transactions_df"] = pd.DataFrame()
            st.rerun()


# Initialize state before creating any widget that uses the key.
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "transactions_df" not in st.session_state:
    st.session_state["transactions_df"] = pd.DataFrame()
if "main_navigation" not in st.session_state:
    st.session_state["main_navigation"] = "Overview"

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

# Header and simplified navigation: only the sections requested.
header_left, header_right = st.columns([3, 1])
with header_left:
    brand()
with header_right:
    st.markdown(
        f'<div style="text-align:right;padding-top:8px;color:{MUTED};font-size:13px;">Signed in as <b style="color:{NAVY}">{st.session_state.get("username", "User")}</b></div>',
        unsafe_allow_html=True,
    )

menu_items = [
    "Overview",
    "Unusual Spending Patterns",
    "Goal-based Spending",
    "AI Finance Coach",
    "Subscription Tracker",
]
if st.session_state.get("main_navigation") not in menu_items:
    st.session_state["main_navigation"] = "Overview"

navigation = st.selectbox(
    "Navigate to",
    menu_items,
    key="main_navigation",
    label_visibility="visible",
)

st.markdown("---")
data = normalize_data(st.session_state["transactions_df"])

if navigation == "Overview":
    overview_page(data)
elif navigation == "Unusual Spending Patterns":
    st.title("Unusual Spending Patterns")
    st.caption("Machine-learning flags are suggestions for review, not proof of fraud.")
    if data.empty:
        st.info("Upload your statement on Overview first. This section will then use the same data automatically.")
    else:
        flagged = unusual_transactions(data)
        if flagged.empty:
            st.info("No flagged transactions, or there are not enough expenses for anomaly detection.")
        else:
            st.warning("Review these unusual amounts. A flag does not mean a transaction is fraudulent.")
            st.dataframe(flagged[["Date", "Description", "Amount", "Category"]], hide_index=True, use_container_width=True)
elif navigation == "Goal-based Spending":
    goals_page(data)
elif navigation == "AI Finance Coach":
    coach_page(data)
elif navigation == "Subscription Tracker":
    subscriptions_page(data)

st.markdown(
    f'<div style="text-align:center;color:{MUTED};font-size:11px;padding:28px 0 0;">FinSight · Personal Finance Intelligence · Your data stays in this app session</div>',
    unsafe_allow_html=True,
)
