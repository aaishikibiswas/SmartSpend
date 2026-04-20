from __future__ import annotations

import io
import json
import math
import os
from datetime import date
from typing import Any

import pandas as pd
import pdfplumber
import pytesseract
import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fpdf import FPDF
from langdetect import LangDetectException, detect
from PIL import Image
from pydantic import BaseModel, Field


app = FastAPI(title="Expense Analyzer API", version="1.0.0")

DEFAULT_ALLOWED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


def get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    if not raw.strip():
        return DEFAULT_ALLOWED_ORIGINS
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


ALLOWED_ORIGINS = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


CATEGORY_KEYWORDS = {
    "Food": ["zomato", "swiggy", "food", "restaurant", "foodpanda"],
    "Shopping": ["flipkart", "amazon", "myntra"],
    "Transport": ["uber", "ola", "cab", "fuel", "petrol"],
    "Utilities": ["bill", "electricity", "recharge", "jio", "airtel", "water", "gas", "phone recharge"],
    "Income": ["salary", "credit", "refund", "deposit", "cashback"],
    "Cash": ["atm", "cash", "withdrawal"],
    "Rent": ["rent", "landlord", "housing"],
    "Entertainment": ["movie", "netflix", "hotstar", "cinema", "spotify", "ticket"],
    "Subscriptions": ["subscription", "spotify", "youtube", "prime", "disney", "membership"],
    "Health": ["pharmacy", "hospital", "doctor", "medicine"],
    "Education": ["school", "college", "course", "fees"],
}

CATEGORY_EMOJI = {
    "Food": "🍔",
    "Shopping": "🛍️",
    "Transport": "🚕",
    "Utilities": "🔌",
    "Income": "💼",
    "Cash": "🏧",
    "Rent": "🏠",
    "Entertainment": "🎮",
    "Subscriptions": "📱",
    "Health": "🏥",
    "Education": "📚",
    "Regional": "🌐",
    "Other": "🔍",
}


class Goal(BaseModel):
    name: str
    target_amount: float
    target_date: date


class BillReminder(BaseModel):
    name: str
    amount: float
    due_day: int = Field(ge=1, le=31)


class Transaction(BaseModel):
    date: str
    description: str
    debit: float = 0
    credit: float = 0
    balance: float = 0
    category: str | None = None


class DashboardFilters(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    categories: list[str] = Field(default_factory=lambda: ["All"])
    projection_months: int = 6


class DashboardRequest(BaseModel):
    transactions: list[Transaction]
    monthly_budget: float = 10000
    weekly_budget_amount: float = 2500
    financial_goals: list[Goal] = Field(default_factory=list)
    bill_reminders: list[BillReminder] = Field(default_factory=list)
    category_budgets: dict[str, dict[str, float]] = Field(default_factory=dict)
    filters: DashboardFilters = Field(default_factory=DashboardFilters)


class ExportRequest(BaseModel):
    transactions: list[Transaction]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    api_key: str
    model_name: str
    temperature: float = 0.7
    transactions: list[Transaction]
    monthly_budget: float = 10000
    weekly_budget_amount: float = 2500
    financial_goals: list[Goal] = Field(default_factory=list)
    bill_reminders: list[BillReminder] = Field(default_factory=list)
    category_budgets: dict[str, dict[str, float]] = Field(default_factory=dict)
    chat_history: list[ChatMessage] = Field(default_factory=list)


class SuggestionsRequest(ChatRequest):
    pass


def category_label(name: str) -> str:
    return f"{CATEGORY_EMOJI.get(name, '🔍')} {name}"


def detect_category(description: str) -> str:
    value = (description or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in value for keyword in keywords):
            return category_label(category)
    try:
        lang = detect(value)
        if lang in {"hi", "bn", "or"}:
            return category_label("Regional")
    except LangDetectException:
        pass
    return category_label("Other")


def parse_number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "nan", "None"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def month_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%B %Y")


def transaction_to_record(tx: Transaction) -> dict[str, Any]:
    return {
        "Date": tx.date,
        "Description": tx.description,
        "Debit": tx.debit,
        "Credit": tx.credit,
        "Balance": tx.balance,
        "Category": tx.category or detect_category(tx.description),
    }


def normalize_transactions(transactions: list[Transaction]) -> pd.DataFrame:
    if not transactions:
        return pd.DataFrame(columns=["Date", "Description", "Debit", "Credit", "Balance", "Category", "Month", "Day"])
    df = pd.DataFrame([transaction_to_record(tx) for tx in transactions])
    return normalize_dataframe(df)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Date", "Description", "Debit", "Credit", "Balance", "Category", "Month", "Day"])

    rename_map = {col: col.strip().title() for col in df.columns}
    df = df.rename(columns=rename_map).copy()

    for col in ["Description", "Debit", "Credit", "Balance"]:
        if col not in df.columns:
            df[col] = "" if col == "Description" else 0

    if "Date" not in df.columns:
        raise HTTPException(status_code=400, detail="Uploaded data must include a Date column.")

    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"]).copy()
    if df.empty:
        return pd.DataFrame(columns=["Date", "Description", "Debit", "Credit", "Balance", "Category", "Month", "Day"])

    for column in ["Debit", "Credit", "Balance"]:
        df[column] = df[column].apply(parse_number)

    df["Description"] = df["Description"].fillna("").astype(str)
    if "Category" not in df.columns:
        df["Category"] = df["Description"].apply(detect_category)
    else:
        df["Category"] = df["Category"].fillna("").astype(str)
        df["Category"] = df.apply(
            lambda row: row["Category"] if row["Category"].strip() else detect_category(row["Description"]),
            axis=1,
        )

    df["Month"] = df["Date"].apply(month_label)
    df["Day"] = df["Date"].dt.strftime("%Y-%m-%d")
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)
    return df


def parse_text_to_df(text: str) -> pd.DataFrame:
    lines = text.strip().splitlines()
    rows: list[list[Any]] = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        try:
            line_date = parts[0]
            balance = parse_number(parts[-1])
            credit = parse_number(parts[-2])
            debit = parse_number(parts[-3])
            desc = " ".join(parts[1:-3])
            rows.append([line_date, desc, debit, credit, balance])
        except Exception:
            continue
    return pd.DataFrame(rows, columns=["Date", "Description", "Debit", "Credit", "Balance"])


def extract_text_from_image(file_bytes: bytes) -> str:
    return pytesseract.image_to_string(Image.open(io.BytesIO(file_bytes)))


def parse_uploaded_file(filename: str, file_bytes: bytes) -> pd.DataFrame:
    suffix = filename.split(".")[-1].lower()
    if suffix == "csv":
        return pd.read_csv(io.BytesIO(file_bytes))
    if suffix == "pdf":
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
        return parse_text_to_df(text)
    if suffix in {"png", "jpg", "jpeg"}:
        return parse_text_to_df(extract_text_from_image(file_bytes))
    raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, CSV, PNG, JPG, or JPEG.")


def format_currency(value: float) -> str:
    return f"₹{value:,.2f}"


def safe_pct(numerator: float, denominator: float) -> float:
    return (numerator / denominator) * 100 if denominator else 0.0


def records_from_df(df: pd.DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    if limit is not None:
        df = df.head(limit)
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "date": row["Date"].strftime("%Y-%m-%d"),
                "description": row["Description"],
                "debit": round(float(row["Debit"]), 2),
                "credit": round(float(row["Credit"]), 2),
                "balance": round(float(row["Balance"]), 2),
                "category": row["Category"],
            }
        )
    return rows


def chart_series_from_group(grouped: pd.Series) -> list[dict[str, Any]]:
    return [{"label": str(label), "value": round(float(value), 2)} for label, value in grouped.items()]


def build_dashboard(payload: DashboardRequest) -> dict[str, Any]:
    df = normalize_transactions(payload.transactions)
    if df.empty:
        return {"has_data": False}

    filters = payload.filters
    filtered = df.copy()
    if filters.start_date:
        filtered = filtered[filtered["Date"] >= pd.to_datetime(filters.start_date)]
    if filters.end_date:
        filtered = filtered[filtered["Date"] <= pd.to_datetime(filters.end_date)]
    if filters.categories and "All" not in filters.categories:
        filtered = filtered[filtered["Category"].isin(filters.categories)]

    today = pd.Timestamp.now().normalize()
    current_month_str = month_label(today)
    week_start = today.to_period("W").start_time
    week_end = today.to_period("W").end_time

    total_income = float(filtered["Credit"].sum())
    total_expense = float(filtered["Debit"].sum())
    total_savings = total_income - total_expense

    top_category_series = filtered.groupby("Category")["Debit"].sum().sort_values(ascending=False)
    top_category = top_category_series.index[0] if not top_category_series.empty else "N/A"
    top_category_value = float(top_category_series.iloc[0]) if not top_category_series.empty else 0.0

    total_expenses_current_month = float(filtered["Debit"].sum())
    total_expenses_current_week = float(
        filtered[(filtered["Date"] >= week_start) & (filtered["Date"] <= week_end)]["Debit"].sum()
    )
    df_current_month = filtered[filtered["Month"] == current_month_str]
    df_last_week = df[df["Date"] >= (pd.Timestamp.now() - pd.Timedelta(weeks=1))]

    alerts: list[dict[str, str]] = []

    food_week = float(df_last_week[df_last_week["Category"] == category_label("Food")]["Debit"].sum())
    transport_week = float(df_last_week[df_last_week["Category"] == category_label("Transport")]["Debit"].sum())
    if not df_last_week.empty:
        if food_week > 1000:
            alerts.append({"type": "info", "section": "Spending Tips", "message": f"You spent {format_currency(food_week)} on food this week. Consider cooking at home to save more."})
        if transport_week > 800:
            alerts.append({"type": "info", "section": "Spending Tips", "message": f"Transport spending reached {format_currency(transport_week)} this week. Public transport or carpooling could help."})
        if food_week <= 1000 and transport_week <= 800:
            alerts.append({"type": "success", "section": "Spending Tips", "message": "You managed food and transport spending well this week."})
    else:
        alerts.append({"type": "info", "section": "Spending Tips", "message": "No recent transactions yet for tailored spending tips."})

    monthly_budget_used = safe_pct(total_expenses_current_month, payload.monthly_budget)
    weekly_budget_used = safe_pct(total_expenses_current_week, payload.weekly_budget_amount)

    if payload.monthly_budget > 0:
        level = "error" if monthly_budget_used >= 100 else "warning" if monthly_budget_used >= 80 else "info"
        message = f"Monthly spending is {format_currency(total_expenses_current_month)} of {format_currency(payload.monthly_budget)} ({monthly_budget_used:.1f}%)."
        alerts.append({"type": level, "section": "Budget Breach Alerts", "message": message})
    else:
        alerts.append({"type": "info", "section": "Budget Breach Alerts", "message": "Set a monthly budget to receive monthly alerts."})

    if payload.weekly_budget_amount > 0:
        level = "error" if weekly_budget_used >= 100 else "warning" if weekly_budget_used >= 80 else "info"
        message = f"Weekly spending is {format_currency(total_expenses_current_week)} of {format_currency(payload.weekly_budget_amount)} ({weekly_budget_used:.1f}%)."
        alerts.append({"type": level, "section": "Budget Breach Alerts", "message": message})
    else:
        alerts.append({"type": "info", "section": "Budget Breach Alerts", "message": "Set a weekly budget to receive weekly alerts."})

    if payload.category_budgets and not df_current_month.empty:
        for category, frequencies in payload.category_budgets.items():
            category_expense = float(df_current_month[df_current_month["Category"] == category]["Debit"].sum())
            for frequency, amount in frequencies.items():
                if amount <= 0:
                    continue
                if frequency == "monthly":
                    used = safe_pct(category_expense, amount)
                    if used >= 100:
                        alerts.append({"type": "error", "section": "Category Budget Alerts", "message": f"{category} spending reached {format_currency(category_expense)} against a {format_currency(amount)} monthly budget."})
                    elif used >= 80:
                        alerts.append({"type": "warning", "section": "Category Budget Alerts", "message": f"{category} spending is at {used:.1f}% of its monthly budget."})
    else:
        alerts.append({"type": "info", "section": "Category Budget Alerts", "message": "Set category budgets to receive category-level alerts."})

    avg_transaction = float(filtered["Debit"].mean()) if not math.isnan(float(filtered["Debit"].mean())) else 0.0
    high_transaction_threshold = max(avg_transaction * 2, 5000)
    high_transactions = filtered[filtered["Debit"] > high_transaction_threshold].copy()
    if not high_transactions.empty:
        for _, row in high_transactions.head(3).iterrows():
            alerts.append({"type": "warning", "section": "High Transaction Detection", "message": f"{format_currency(float(row['Debit']))} spent on {row['Description']} ({row['Date'].strftime('%Y-%m-%d')})."})
    else:
        alerts.append({"type": "info", "section": "High Transaction Detection", "message": "No unusually high transactions detected."})

    duplicate_messages: list[dict[str, str]] = []
    df_sorted = filtered.sort_values(by=["Description", "Debit", "Date"]).reset_index(drop=True)
    seen_pairs: set[tuple[Any, ...]] = set()
    for index in range(len(df_sorted) - 1):
        row1 = df_sorted.iloc[index]
        row2 = df_sorted.iloc[index + 1]
        if (
            row1["Description"] == row2["Description"]
            and row1["Debit"] == row2["Debit"]
            and row1["Debit"] > 0
            and abs((row1["Date"] - row2["Date"]).days) <= 1
        ):
            pair_key = tuple(sorted(((row1["Day"], row1["Debit"], row1["Description"]), (row2["Day"], row2["Debit"], row2["Description"]))))
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                duplicate_messages.append(
                    {
                        "type": "warning",
                        "section": "Duplicate Transaction Warning",
                        "message": f"Potential duplicate: {row1['Description']} for {format_currency(float(row1['Debit']))} on {row1['Date'].strftime('%Y-%m-%d')} and {row2['Date'].strftime('%Y-%m-%d')}.",
                    }
                )
    alerts.extend(duplicate_messages or [{"type": "info", "section": "Duplicate Transaction Warning", "message": "No potential duplicate transactions detected."}])

    total_savings_so_far = float(df["Credit"].sum() - df["Debit"].sum())
    goals = []
    for goal in payload.financial_goals:
        achieved = min(total_savings_so_far, goal.target_amount)
        remaining_days = (goal.target_date - date.today()).days
        goals.append(
            {
                "name": goal.name,
                "target_amount": goal.target_amount,
                "achieved": round(max(0.0, achieved), 2),
                "remaining": round(max(0.0, goal.target_amount - total_savings_so_far), 2),
                "progress_percent": round(safe_pct(achieved, goal.target_amount), 1),
                "remaining_days": remaining_days,
                "is_achieved": total_savings_so_far >= goal.target_amount,
            }
        )

    upcoming_bills = []
    today_date = date.today()
    for bill in payload.bill_reminders:
        due_day = min(bill.due_day, 28 if today_date.month == 2 else 30 if today_date.month in {4, 6, 9, 11} else 31)
        due_date = today_date.replace(day=due_day)
        if due_date < today_date:
            if today_date.month == 12:
                next_month = today_date.replace(year=today_date.year + 1, month=1, day=1)
            else:
                next_month = today_date.replace(month=today_date.month + 1, day=1)
            month_last_day = (pd.Timestamp(next_month) + pd.offsets.MonthEnd(0)).day
            due_date = next_month.replace(day=min(bill.due_day, int(month_last_day)))
        days_until_due = (due_date - today_date).days
        if 0 <= days_until_due <= 30:
            upcoming_bills.append(
                {
                    "name": bill.name,
                    "amount": bill.amount,
                    "days_until_due": days_until_due,
                    "due_date": due_date.isoformat(),
                }
            )

    monthly_summary = df.groupby("Month").agg(Total_Credit=("Credit", "sum"), Total_Debit=("Debit", "sum")).reset_index()
    projection = None
    if len(monthly_summary) >= 2:
        avg_monthly_income = float(monthly_summary["Total_Credit"].mean())
        avg_monthly_expense = float(monthly_summary["Total_Debit"].mean())
        avg_monthly_net = avg_monthly_income - avg_monthly_expense
        current_total_savings = total_savings_so_far
        projected_savings = current_total_savings + (avg_monthly_net * filters.projection_months)
        projection = {
            "avg_monthly_income": round(avg_monthly_income, 2),
            "avg_monthly_expense": round(avg_monthly_expense, 2),
            "avg_monthly_net": round(avg_monthly_net, 2),
            "projection_months": filters.projection_months,
            "projected_savings": round(projected_savings, 2),
            "history_months": len(monthly_summary),
        }

    expense_breakdown = filtered.groupby("Category")["Debit"].sum().sort_values(ascending=False).head(5)
    daily_expense = filtered.groupby("Day")["Debit"].sum().reset_index()
    report_overview = [
        {"label": "Income", "value": round(float(filtered["Credit"].sum()), 2)},
        {"label": "Expense", "value": round(float(filtered["Debit"].sum()), 2)},
        {"label": "Savings", "value": round(max(0.0, total_savings), 2)},
    ]

    return {
        "has_data": True,
        "available_categories": sorted(df["Category"].dropna().unique().tolist()),
        "metrics": {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "total_savings": round(total_savings, 2),
            "savings_rate": round(safe_pct(total_savings, total_income), 1),
            "top_category": top_category,
            "top_category_value": round(top_category_value, 2),
        },
        "alerts": alerts,
        "budget_trackers": {
            "monthly_budget": payload.monthly_budget,
            "monthly_used": round(total_expenses_current_month, 2),
            "monthly_remaining": round(payload.monthly_budget - total_expenses_current_month, 2),
            "monthly_percent": round(monthly_budget_used, 1),
            "weekly_budget": payload.weekly_budget_amount,
            "weekly_used": round(total_expenses_current_week, 2),
            "weekly_remaining": round(payload.weekly_budget_amount - total_expenses_current_week, 2),
            "weekly_percent": round(weekly_budget_used, 1),
        },
        "goals": goals,
        "upcoming_bills": upcoming_bills,
        "projection": projection,
        "charts": {
            "expense_breakdown": chart_series_from_group(expense_breakdown),
            "report_overview": report_overview,
            "daily_expense": [{"label": item["Day"], "value": round(float(item["Debit"]), 2)} for item in daily_expense.to_dict(orient="records")],
        },
        "recent_transactions": records_from_df(filtered, 15),
        "filtered_transactions": records_from_df(filtered),
        "summary": {
            "total_spent": round(float(df["Debit"].sum()), 2),
            "total_received": round(float(df["Credit"].sum()), 2),
            "final_balance": round(float(df["Balance"].iloc[-1]) if not df["Balance"].empty else 0.0, 2),
        },
    }


def build_pdf(summary: dict[str, float]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Expense Summary Report", ln=1, align="C")
    for key, value in summary.items():
        pdf.cell(200, 10, txt=f"{key}: Rs. {value:,.2f}", ln=1)
    return bytes(pdf.output(dest="S"))


def ai_context(request_data: ChatRequest) -> str:
    df = normalize_transactions(request_data.transactions)
    if df.empty:
        return "No financial data available. Ask the user to upload a bank statement for a more detailed analysis."

    top_category = df.groupby("Category")["Debit"].sum().sort_values(ascending=False)
    top_category_name = top_category.index[0] if not top_category.empty else "N/A"
    summary_context = f"""
Financial Summary:
- Total Income: {format_currency(float(df['Credit'].sum()))}
- Total Expenses: {format_currency(float(df['Debit'].sum()))}
- Total Savings: {format_currency(float(df['Credit'].sum() - df['Debit'].sum()))}
- Most Spending Category: {top_category_name}
- Monthly Budget Set: {format_currency(request_data.monthly_budget)}
- Weekly Budget Set: {format_currency(request_data.weekly_budget_amount)}
- Current Monthly Expenses: {format_currency(float(df[df['Month'] == month_label(pd.Timestamp.now())]['Debit'].sum()))}
- Current Weekly Expenses: {format_currency(float(df[(df['Date'] >= pd.Timestamp.now().to_period('W').start_time) & (df['Date'] <= pd.Timestamp.now().to_period('W').end_time)]['Debit'].sum()))}
- Financial Goals: {json.dumps([goal.model_dump() for goal in request_data.financial_goals], default=str)}
- Bill Reminders: {json.dumps([bill.model_dump() for bill in request_data.bill_reminders], default=str)}
- Category Budgets: {json.dumps(request_data.category_budgets, default=str)}
"""
    return f"{summary_context}\nRecent Transaction Data (first 50 rows):\n{df.head(50).to_string(index=False)}"


def call_openrouter(request_data: ChatRequest, smart_mode: bool = False) -> str:
    context = ai_context(request_data)
    system_message = (
        "You are a helpful financial advisor for an Expense Analyzer app. Use the data to provide practical advice. "
        "Mention relevant app features when helpful: dashboard overview, alerts, budgets, goals, bill reminders, projections, charts, reports, transaction entry, and category budgets."
    )
    user_message = f"Financial data:\n{context}\n\nQuestion: {request_data.question}\nAnswer clearly and concisely."
    if smart_mode:
        system_message = (
            "You are a proactive financial advisor for an Expense Analyzer app. "
            "Return 3-5 actionable recommendations. Explain why each recommendation matters and which app feature helps the user act on it."
        )
        user_message = f"Financial data:\n{context}\n\nProvide 3-5 smart financial suggestions tailored to the user."

    messages = [{"role": "system", "content": system_message}]
    for message in request_data.chat_history[-8:]:
        if message.role in {"user", "assistant"}:
            messages.append({"role": message.role, "content": message.content})
    messages.append({"role": "user", "content": user_message})

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {request_data.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Expense Analyzer",
        },
        json={
            "model": request_data.model_name,
            "temperature": request_data.temperature,
            "max_tokens": 600,
            "messages": messages,
        },
        timeout=60,
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an unexpected response.") from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/parse/upload")
async def parse_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    df = normalize_dataframe(parse_uploaded_file(file.filename or "upload.csv", content))
    return {
        "transactions": records_from_df(df),
        "available_categories": sorted(df["Category"].dropna().unique().tolist()) if not df.empty else [],
    }


@app.post("/api/dashboard/analyze")
def analyze_dashboard(payload: DashboardRequest) -> dict[str, Any]:
    return build_dashboard(payload)


@app.post("/api/export/csv")
def export_csv(payload: ExportRequest) -> StreamingResponse:
    df = normalize_transactions(payload.transactions)
    csv_bytes = df[["Date", "Description", "Debit", "Credit", "Balance", "Category"]].assign(
        Date=lambda data: data["Date"].dt.strftime("%Y-%m-%d")
    ).to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="expenses.csv"'},
    )


@app.post("/api/export/pdf")
def export_pdf(payload: ExportRequest) -> Response:
    df = normalize_transactions(payload.transactions)
    summary = {
        "Total Spent": float(df["Debit"].sum()),
        "Total Received": float(df["Credit"].sum()),
        "Final Balance": float(df["Balance"].iloc[-1]) if not df["Balance"].empty else 0.0,
    }
    return Response(
        content=build_pdf(summary),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="summary_report.pdf"'},
    )


@app.post("/api/ai/chat")
def ai_chat(payload: ChatRequest) -> dict[str, str]:
    return {"answer": call_openrouter(payload, smart_mode=False)}


@app.post("/api/ai/suggestions")
def ai_suggestions(payload: SuggestionsRequest) -> dict[str, str]:
    return {"answer": call_openrouter(payload, smart_mode=True)}
