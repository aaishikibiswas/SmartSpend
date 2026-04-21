from __future__ import annotations

import io
import json
import math
import os
import secrets
import time
from datetime import date
from typing import Any

import pandas as pd
import pdfplumber
import pytesseract
import requests
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fpdf import FPDF
from langdetect import LangDetectException, detect
from PIL import Image
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo.collection import ReturnDocument


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


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    plan: str | None = None


class AuthStore:
    def __init__(self) -> None:
        self.mongodb_uri = os.getenv("MONGODB_URI", "").strip()
        self.mongo_mode = bool(self.mongodb_uri)
        self.users_file = os.getenv("USERS_FILE", "users_store.json")
        self.sessions_file = os.getenv("SESSIONS_FILE", "sessions_store.json")
        self.session_ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24 * 7)))
        self.password_salt = os.getenv("AUTH_PASSWORD_SALT", "smartspend-default-salt")

        if self.mongo_mode:
            try:
                client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
                db_name = os.getenv("MONGODB_DB", "smartspend")
                self.db = client[db_name]
                self.users_col = self.db["users"]
                self.sessions_col = self.db["sessions"]
                # Force an early connectivity check; fallback if unreachable.
                self.db.command("ping")
                self.users_col.create_index("email", unique=True)
                self.users_col.create_index("id", unique=True)
                self.sessions_col.create_index("token", unique=True)
                self.sessions_col.create_index("expires_at")
            except Exception:
                # Keep service alive even if Mongo is temporarily misconfigured/unreachable.
                self.mongo_mode = False
                self._ensure_local_files()
        else:
            self._ensure_local_files()

    def _ensure_local_files(self) -> None:
        for path in (self.users_file, self.sessions_file):
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump([], handle)

    def _hash_password(self, password: str) -> str:
        import hashlib

        return hashlib.sha256(f"{self.password_salt}:{password}".encode("utf-8")).hexdigest()

    def _public_user(self, user_record: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(user_record["id"]),
            "full_name": str(user_record.get("full_name", "")),
            "email": str(user_record.get("email", "")),
            "plan": str(user_record.get("plan", "Starter")),
            "avatar_seed": str(user_record.get("avatar_seed", "user")),
        }

    def _load_local(self, path: str) -> list[dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save_local(self, path: str, data: list[dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

    def register(self, full_name: str, email: str, password: str) -> dict[str, Any]:
        normalized_email = email.strip().lower()
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

        avatar_seed = normalized_email.split("@")[0] or "user"
        now_ts = int(time.time())
        password_hash = self._hash_password(password)

        if self.mongo_mode:
            user_id = int(time.time() * 1000)
            user_record = {
                "id": user_id,
                "full_name": full_name.strip(),
                "email": normalized_email,
                "password_hash": password_hash,
                "plan": "Starter",
                "avatar_seed": avatar_seed,
                "created_at": now_ts,
            }
            try:
                self.users_col.insert_one(user_record)
            except DuplicateKeyError as exc:
                raise HTTPException(status_code=409, detail="Email already registered.") from exc
            return self._public_user(user_record)

        users = self._load_local(self.users_file)
        if any(str(user.get("email", "")).lower() == normalized_email for user in users):
            raise HTTPException(status_code=409, detail="Email already registered.")
        user_id = max([int(user.get("id", 0)) for user in users] + [0]) + 1
        user_record = {
            "id": user_id,
            "full_name": full_name.strip(),
            "email": normalized_email,
            "password_hash": password_hash,
            "plan": "Starter",
            "avatar_seed": avatar_seed,
            "created_at": now_ts,
        }
        users.append(user_record)
        self._save_local(self.users_file, users)
        return self._public_user(user_record)

    def login(self, email: str, password: str) -> dict[str, Any]:
        normalized_email = email.strip().lower()
        password_hash = self._hash_password(password)

        if self.mongo_mode:
            user = self.users_col.find_one({"email": normalized_email})
            if not user or user.get("password_hash") != password_hash:
                raise HTTPException(status_code=401, detail="Invalid email or password.")
            return self._public_user(user)

        users = self._load_local(self.users_file)
        for user in users:
            if str(user.get("email", "")).lower() == normalized_email and user.get("password_hash") == password_hash:
                return self._public_user(user)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        now_ts = int(time.time())
        expires_at = now_ts + self.session_ttl_seconds

        if self.mongo_mode:
            self.sessions_col.insert_one(
                {
                    "token": token,
                    "user_id": int(user_id),
                    "created_at": now_ts,
                    "expires_at": expires_at,
                }
            )
            return token

        sessions = self._load_local(self.sessions_file)
        sessions.append(
            {
                "token": token,
                "user_id": int(user_id),
                "created_at": now_ts,
                "expires_at": expires_at,
            }
        )
        self._save_local(self.sessions_file, sessions)
        return token

    def _find_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        if self.mongo_mode:
            user = self.users_col.find_one({"id": int(user_id)})
            return self._public_user(user) if user else None
        users = self._load_local(self.users_file)
        for user in users:
            if int(user.get("id", 0)) == int(user_id):
                return self._public_user(user)
        return None

    def get_user_by_token(self, token: str) -> dict[str, Any]:
        now_ts = int(time.time())
        if self.mongo_mode:
            session = self.sessions_col.find_one({"token": token})
            if not session or int(session.get("expires_at", 0)) < now_ts:
                if session:
                    self.sessions_col.delete_one({"token": token})
                raise HTTPException(status_code=401, detail="Session expired or invalid.")
            user = self._find_user_by_id(int(session["user_id"]))
            if not user:
                raise HTTPException(status_code=401, detail="Session user not found.")
            return user

        sessions = self._load_local(self.sessions_file)
        valid_sessions = [s for s in sessions if int(s.get("expires_at", 0)) >= now_ts]
        if len(valid_sessions) != len(sessions):
            self._save_local(self.sessions_file, valid_sessions)
        for session in valid_sessions:
            if session.get("token") == token:
                user = self._find_user_by_id(int(session["user_id"]))
                if not user:
                    raise HTTPException(status_code=401, detail="Session user not found.")
                return user
        raise HTTPException(status_code=401, detail="Session expired or invalid.")

    def update_user(self, user_id: int, full_name: str | None, plan: str | None) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        if full_name is not None and full_name.strip():
            updates["full_name"] = full_name.strip()
        if plan is not None and plan.strip():
            updates["plan"] = plan.strip()

        if not updates:
            user = self._find_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found.")
            return user

        if self.mongo_mode:
            result = self.users_col.find_one_and_update(
                {"id": int(user_id)},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
            )
            if not result:
                raise HTTPException(status_code=404, detail="User not found.")
            return self._public_user(result)

        users = self._load_local(self.users_file)
        for user in users:
            if int(user.get("id", 0)) == int(user_id):
                user.update(updates)
                self._save_local(self.users_file, users)
                return self._public_user(user)
        raise HTTPException(status_code=404, detail="User not found.")

    def delete_session(self, token: str) -> None:
        if self.mongo_mode:
            self.sessions_col.delete_many({"token": token})
            return
        sessions = self._load_local(self.sessions_file)
        sessions = [session for session in sessions if session.get("token") != token]
        self._save_local(self.sessions_file, sessions)


auth_store = AuthStore()


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme.")
    token = authorization.replace("Bearer ", "", 1).strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token missing.")
    return token


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


@app.post("/auth/register")
def auth_register(payload: RegisterRequest) -> dict[str, Any]:
    user = auth_store.register(payload.full_name, payload.email, payload.password)
    session_token = auth_store.create_session(int(user["id"]))
    return {
        "status": 200,
        "data": {
            "user": user,
            "sessionToken": session_token,
        },
        "message": "Registration successful.",
    }


@app.post("/auth/login")
def auth_login(payload: LoginRequest) -> dict[str, Any]:
    user = auth_store.login(payload.email, payload.password)
    session_token = auth_store.create_session(int(user["id"]))
    return {
        "status": 200,
        "data": {
            "user": user,
            "sessionToken": session_token,
        },
        "message": "Login successful.",
    }


@app.get("/auth/me")
def auth_me(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    user = auth_store.get_user_by_token(token)
    return {
        "status": 200,
        "data": user,
    }


@app.put("/auth/me")
def auth_update_me(payload: ProfileUpdateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    user = auth_store.get_user_by_token(token)
    updated = auth_store.update_user(int(user["id"]), payload.full_name, payload.plan)
    return {
        "status": 200,
        "data": updated,
        "message": "Profile updated.",
    }


@app.post("/auth/logout")
def auth_logout(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    auth_store.delete_session(token)
    return {
        "status": 200,
        "data": {"success": True},
    }


# ---- SmartSpend compatibility layer for Next.js routes ----
_demo_transactions: list[dict[str, Any]] = [
    {"id": 1, "merchant": "Salary Credit", "category": "Income", "date": "2026-04-01", "amount": 84530.0, "type": "credit"},
    {"id": 2, "merchant": "Rent", "category": "Rent", "date": "2026-04-03", "amount": 18000.0, "type": "debit"},
    {"id": 3, "merchant": "Internet Fiber", "category": "Utilities", "date": "2026-04-08", "amount": 2400.0, "type": "debit"},
    {"id": 4, "merchant": "Groceries", "category": "Food", "date": "2026-04-10", "amount": 5200.0, "type": "debit"},
    {"id": 5, "merchant": "Transport", "category": "Transport", "date": "2026-04-12", "amount": 2337.0, "type": "debit"},
]
_demo_alerts: list[dict[str, Any]] = [
    {"id": 1, "type": "warning", "title": "High fixed expense ratio", "message": "Fixed commitments are above 60% of total spend."},
    {"id": 2, "type": "info", "title": "Bill due soon", "message": "Internet bill is due today."},
]
_demo_goals: list[dict[str, Any]] = [
    {"id": 1, "name": "Emergency Fund", "target": 300000.0, "achieved": 185603.0, "daysLeft": 180, "color": "#7B6CF6"},
]
_demo_bills: list[dict[str, Any]] = [
    {"id": 1, "name": "Internet (Fiber)", "amount": 2400.0, "due": "Due Today", "icon": "bolt", "color": "red"},
    {"id": 2, "name": "Electricity", "amount": 4120.0, "due": "Due in 4 days", "icon": "bolt", "color": "blue"},
]
_demo_subscriptions: list[dict[str, Any]] = [
    {"id": 1, "name": "Uber One", "frequency": "monthly", "monthly_cost": 399.0, "yearly_cost": 4788.0, "last_charge_date": "2026-04-01", "next_due_date": "2026-05-01", "source": "auto"},
]
_demo_emi_items: list[dict[str, Any]] = [
    {"id": 1, "name": "Car Loan", "total_amount": 240000.0, "monthly_emi": 12850.0, "remaining_months": 19, "interest_rate": 9.2, "due_date": "2026-05-18", "source": "auto"},
]
_demo_budget_global: dict[str, Any] = {
    "monthly_budget": 35000.0,
    "weekly_budget": 9000.0,
    "spent_amount": 27937.0,
    "remaining_amount": 7063.0,
    "usage_percent": 79.82,
    "daily_allowance": 378.0,
    "auto_distribute": True,
    "status": "on-track",
}
_demo_budget_categories: list[dict[str, Any]] = [
    {"name": "Food", "allocated_amount": 8000.0, "frequency": "monthly", "spent_amount": 5200.0, "remaining_amount": 2800.0, "usage_percent": 65.0, "status": "on-track", "monthly_equivalent": 8000.0},
    {"name": "Transport", "allocated_amount": 4000.0, "frequency": "monthly", "spent_amount": 2337.0, "remaining_amount": 1663.0, "usage_percent": 58.4, "status": "on-track", "monthly_equivalent": 4000.0},
]


def _ok(data: Any, message: str | None = None, status: int = 200) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status, "data": data}
    if message:
        payload["message"] = message
    return payload


def _metrics_from_transactions() -> dict[str, Any]:
    income = sum(float(item["amount"]) for item in _demo_transactions if item["type"] == "credit")
    expense = sum(float(item["amount"]) for item in _demo_transactions if item["type"] == "debit")
    net_savings = income - expense
    subscription_load = sum(float(item["monthly_cost"]) for item in _demo_subscriptions)
    emi_load = sum(float(item["monthly_emi"]) for item in _demo_emi_items)
    fixed_total = sum(float(item["amount"]) for item in _demo_transactions if item["type"] == "debit" and item["category"] in {"Rent", "Utilities", "EMI", "Subscription", "Bills"})
    variable_total = max(0.0, expense - fixed_total)
    fixed_percent = (fixed_total / expense * 100.0) if expense else 0.0
    variable_percent = (variable_total / expense * 100.0) if expense else 0.0
    net_worth = max(0.0, net_savings * 4) - (sum(float(item["monthly_emi"]) * float(item["remaining_months"]) for item in _demo_emi_items))

    return {
        "totalIncome": round(income, 2),
        "totalExpense": round(expense, 2),
        "netSavings": round(net_savings, 2),
        "totalBalance": round(net_savings + 120000.0, 2),
        "savingsRatio": round((net_savings / income * 100.0) if income else 0.0, 2),
        "volatility": 18.4,
        "healthScore": 69,
        "budgetUsagePercent": round(_demo_budget_global["usage_percent"], 2),
        "remainingBudget": round(_demo_budget_global["remaining_amount"], 2),
        "dailyAllowance": round(_demo_budget_global["daily_allowance"], 2),
        "burnRate": round(expense / 30.0, 2),
        "savingsGrowth": 7.4,
        "lifestyleInflation": 4.8,
        "runwayMonths": 6.9,
        "financialPersonality": "Stable Planner",
        "subscriptionLoad": round(subscription_load, 2),
        "monthlyEmiLoad": round(emi_load, 2),
        "netWorth": round(net_worth, 2),
        "assets": round(max(0.0, net_worth + 250000.0), 2),
        "liabilities": round(max(0.0, 250000.0 - net_worth), 2),
        "fixedExpensePercent": round(fixed_percent, 2),
        "variableExpensePercent": round(variable_percent, 2),
        "projectedOutflow": round(expense + subscription_load + emi_load, 2),
        "creditScore": {
            "score": 712,
            "category": "Good",
            "range": {"min": 300, "max": 900},
            "indicators": {"spending_stability": "Moderate", "savings_ratio": "Healthy", "risk_level": "Medium"},
            "feature_contributions": {"savings_ratio": 80, "volatility": -25, "anomalies": -10, "expense_income_ratio": -18},
            "explainability": {"top_positive_driver": "savings_ratio", "top_negative_driver": "expense_income_ratio"},
            "suggestions": ["Increase monthly auto-savings by 10%", "Reduce variable spend by Rs.1500"],
            "disclaimer": "Based on system-generated financial behavior. Not an official credit score.",
        },
        "trends": {"balanceTrend": 4.1, "incomeTrend": 2.2, "expenseTrend": -1.3, "savingsTrend": 5.8},
    }


@app.get("/dashboard/")
def dashboard_compat() -> dict[str, Any]:
    metrics = _metrics_from_transactions()
    data = {
        "metrics": metrics,
        "budgeting": {"global": _demo_budget_global, "categories": _demo_budget_categories, "feedback": ["Budget usage is under control.", "You can allocate more to emergency fund."]},
        "goalSuggestion": {"recommendedContribution": 5099.0, "message": "Move Rs.5,099 toward your top goal this month."},
        "categoryBreakdown": [
            {"name": "Rent", "amount": 18000.0},
            {"name": "Food", "amount": 5200.0},
            {"name": "Utilities", "amount": 2400.0},
            {"name": "Transport", "amount": 2337.0},
        ],
        "subscriptions": _demo_subscriptions,
        "emi": {"items": _demo_emi_items, "monthly_load": round(sum(float(item["monthly_emi"]) for item in _demo_emi_items), 2), "remaining_liability": round(sum(float(item["monthly_emi"]) * float(item["remaining_months"]) for item in _demo_emi_items), 2)},
        "expenseSplit": {
            "fixed_total": 20400.0,
            "variable_total": 7537.0,
            "fixed_percent": metrics["fixedExpensePercent"],
            "variable_percent": metrics["variableExpensePercent"],
            "breakdown": [{"name": "Fixed", "amount": 20400.0}, {"name": "Variable", "amount": 7537.0}],
        },
        "networth": {"assets": metrics["assets"], "liabilities": metrics["liabilities"], "net_worth": metrics["netWorth"]},
        "cashflow": {"upcoming_payments": [{"name": "Internet", "date": "2026-04-22", "amount": 2400.0, "type": "bill"}], "monthly_outflow_projection": metrics["projectedOutflow"]},
        "priorities": [{"level": "HIGH", "title": "Build emergency buffer", "message": "Allocate at least 15% of monthly income to emergency fund."}],
        "bills": _demo_bills,
        "recentTransactions": _demo_transactions[:8],
        "allTransactions": _demo_transactions,
    }
    return _ok(data)


@app.get("/alerts/")
def alerts_compat() -> dict[str, Any]:
    return _ok(_demo_alerts)


@app.get("/goals/")
def goals_compat() -> dict[str, Any]:
    return _ok(_demo_goals)


@app.get("/bills/")
def bills_compat() -> dict[str, Any]:
    return _ok(_demo_bills)


@app.post("/bills/")
def bills_add_compat(payload: dict[str, Any]) -> dict[str, Any]:
    next_id = max([int(item.get("id", 0)) for item in _demo_bills] + [0]) + 1
    item = {
        "id": next_id,
        "name": str(payload.get("name", "New Bill")),
        "amount": float(payload.get("amount", 0)),
        "due": str(payload.get("due", "Due in 7 days")),
        "icon": str(payload.get("icon", "bolt")),
        "color": str(payload.get("color", "blue")),
    }
    _demo_bills.append(item)
    return _ok(item, "Bill added.")


@app.delete("/bills/{identifier}")
def bills_delete_compat(identifier: str) -> dict[str, Any]:
    global _demo_bills
    _demo_bills = [item for item in _demo_bills if str(item.get("id")) != identifier and str(item.get("name")) != identifier]
    return _ok({"removed": identifier})


@app.post("/transactions/")
def transactions_add_compat(payload: dict[str, Any]) -> dict[str, Any]:
    next_id = max([int(item.get("id", 0)) for item in _demo_transactions] + [0]) + 1
    item = {
        "id": next_id,
        "merchant": str(payload.get("merchant", "Manual Entry")),
        "category": str(payload.get("category", "Others")),
        "date": str(payload.get("date", date.today().isoformat())),
        "amount": float(payload.get("amount", 0)),
        "type": str(payload.get("type", "debit")),
    }
    _demo_transactions.insert(0, item)
    return _ok(item, "Transaction added.")


@app.post("/upload/")
async def upload_compat(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    count = 0
    if file.filename:
        try:
            df = normalize_dataframe(parse_uploaded_file(file.filename, content))
            count = int(len(df.index))
            for _, row in df.head(20).iterrows():
                _demo_transactions.append(
                    {
                        "id": max([int(item.get("id", 0)) for item in _demo_transactions] + [0]) + 1,
                        "merchant": str(row["Description"])[:80] or "Imported",
                        "category": str(row["Category"]).replace("ðŸ” ", "") if isinstance(row["Category"], str) else "Others",
                        "date": row["Date"].strftime("%Y-%m-%d"),
                        "amount": float(row["Debit"] if row["Debit"] > 0 else row["Credit"]),
                        "type": "debit" if float(row["Debit"]) > 0 else "credit",
                    }
                )
        except Exception:
            count = 0
    return _ok({"success": True, "extractedTransactionsCount": count, "message": "Statement processed."})


@app.post("/assistant/query")
def assistant_query_compat(payload: dict[str, Any]) -> dict[str, Any]:
    q = str(payload.get("question", "")).strip()
    metrics = _metrics_from_transactions()
    answer = (
        f"From your current data: income is Rs{metrics['totalIncome']:,.0f}, expenses are Rs{metrics['totalExpense']:,.0f}, "
        f"net savings are Rs{metrics['netSavings']:,.2f}. Start by reducing variable spend by 5-10% and automate savings."
    )
    if q:
        answer += f" You asked: '{q}'. Focus first on bills, recurring subscriptions, and your emergency fund."
    return _ok({"answer": answer, "suggestions": ["What is my next predicted expense?", "Which category am I spending the most on?"]})


@app.get("/subscriptions/")
def subscriptions_get_compat() -> dict[str, Any]:
    return _ok(_demo_subscriptions)


@app.post("/subscriptions/")
def subscriptions_add_compat(payload: dict[str, Any]) -> dict[str, Any]:
    next_id = max([int(item.get("id", 0)) for item in _demo_subscriptions] + [0]) + 1
    monthly = float(payload.get("monthly_cost", 0))
    item = {
        "id": next_id,
        "name": str(payload.get("name", "New Subscription")),
        "frequency": str(payload.get("frequency", "monthly")),
        "monthly_cost": monthly,
        "yearly_cost": round(monthly * 12, 2),
        "last_charge_date": str(payload.get("last_charge_date", date.today().isoformat())),
        "next_due_date": str(payload.get("next_due_date", date.today().isoformat())),
        "source": "manual",
    }
    _demo_subscriptions.append(item)
    return _ok(item, "Subscription added.")


@app.delete("/subscriptions/{name}")
def subscriptions_delete_compat(name: str) -> dict[str, Any]:
    global _demo_subscriptions
    _demo_subscriptions = [item for item in _demo_subscriptions if str(item.get("name")).lower() != name.lower()]
    return _ok({"removed": name})


@app.get("/emi/")
def emi_get_compat() -> dict[str, Any]:
    return _ok(
        {
            "items": _demo_emi_items,
            "monthly_load": round(sum(float(item["monthly_emi"]) for item in _demo_emi_items), 2),
            "remaining_liability": round(sum(float(item["monthly_emi"]) * float(item["remaining_months"]) for item in _demo_emi_items), 2),
        }
    )


@app.post("/emi/")
def emi_add_compat(payload: dict[str, Any]) -> dict[str, Any]:
    next_id = max([int(item.get("id", 0)) for item in _demo_emi_items] + [0]) + 1
    item = {
        "id": next_id,
        "name": str(payload.get("name", "New EMI")),
        "total_amount": float(payload.get("total_amount", 0)),
        "monthly_emi": float(payload.get("monthly_emi", 0)),
        "remaining_months": int(payload.get("remaining_months", 0)),
        "interest_rate": float(payload.get("interest_rate", 0)),
        "due_date": str(payload.get("due_date", date.today().isoformat())),
        "source": "manual",
    }
    _demo_emi_items.append(item)
    return _ok(item, "EMI added.")


@app.delete("/emi/{identifier}")
def emi_delete_compat(identifier: str) -> dict[str, Any]:
    global _demo_emi_items
    _demo_emi_items = [item for item in _demo_emi_items if str(item.get("id")) != identifier and str(item.get("name")) != identifier]
    return _ok({"removed": identifier})


@app.get("/expense-split/")
def expense_split_compat() -> dict[str, Any]:
    metrics = _metrics_from_transactions()
    return _ok({"fixed_total": 20400.0, "variable_total": 7537.0, "fixed_percent": metrics["fixedExpensePercent"], "variable_percent": metrics["variableExpensePercent"], "breakdown": [{"name": "Fixed", "amount": 20400.0}, {"name": "Variable", "amount": 7537.0}]})


@app.get("/networth/")
def networth_compat() -> dict[str, Any]:
    metrics = _metrics_from_transactions()
    return _ok({"assets": metrics["assets"], "liabilities": metrics["liabilities"], "net_worth": metrics["netWorth"]})


@app.get("/cashflow/")
def cashflow_compat() -> dict[str, Any]:
    metrics = _metrics_from_transactions()
    return _ok({"upcoming_payments": [{"name": "Internet", "date": "2026-04-22", "amount": 2400.0, "type": "bill"}], "monthly_outflow_projection": metrics["projectedOutflow"]})


@app.get("/priorities/")
def priorities_compat() -> dict[str, Any]:
    return _ok([{"level": "HIGH", "title": "Build emergency buffer", "message": "Allocate 15% of monthly income to emergency fund."}])


@app.post("/predict/")
def predict_compat(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ok({"forecast": {"peakAlert": {"day": "2026-04-28", "amount": 9200.0}, "series": [3200, 4100, 3700, 5200, 6200, 5800, 6400]}, "next_expense_prediction": {"predicted_expense": 1083.72, "risk_level": "Medium", "budget_usage_percent": 79.8, "recurring_load": 13249.0}})


@app.post("/simulate/")
def simulate_compat(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics_from_transactions()
    income_adj = float(payload.get("income_adjustment", 0))
    expense_adj = float(payload.get("expense_adjustment", 0))
    months = int(payload.get("months", 6))
    new_income = metrics["totalIncome"] + income_adj
    new_expense = metrics["totalExpense"] + expense_adj
    monthly_savings = new_income - new_expense
    return _ok(
        {
            "new_income": round(new_income, 2),
            "new_expense": round(new_expense, 2),
            "monthly_savings": round(monthly_savings, 2),
            "projected_savings": round(monthly_savings * months, 2),
            "risk_level": "Low" if monthly_savings > 0 else "High",
            "expense_split": {"fixed_total": 20400.0, "variable_total": max(0.0, new_expense - 20400.0), "fixed_percent": (20400.0 / new_expense * 100.0) if new_expense else 0.0, "variable_percent": max(0.0, 100.0 - ((20400.0 / new_expense * 100.0) if new_expense else 0.0)), "breakdown": [{"name": "Fixed", "amount": 20400.0}, {"name": "Variable", "amount": max(0.0, new_expense - 20400.0)}]},
            "updated_metrics": _metrics_from_transactions(),
            "networth": {"assets": metrics["assets"], "liabilities": metrics["liabilities"], "net_worth": metrics["netWorth"]},
            "cashflow": {"upcoming_payments": [{"name": "Internet", "date": "2026-04-22", "amount": 2400.0, "type": "bill"}], "monthly_outflow_projection": round(new_expense, 2)},
            "priorities": [{"level": "MEDIUM", "title": "Control variable spend", "message": "Keep discretionary expenses under target."}],
            "months": months,
        }
    )


@app.get("/budget/global/")
def budget_global_get_compat() -> dict[str, Any]:
    return _ok(_demo_budget_global)


@app.put("/budget/global/")
def budget_global_update_compat(payload: dict[str, Any]) -> dict[str, Any]:
    _demo_budget_global.update({k: payload[k] for k in ("monthly_budget", "weekly_budget", "auto_distribute") if k in payload})
    return _ok({"global": _demo_budget_global, "categories": _demo_budget_categories, "feedback": ["Global budget updated."], "alerts": _demo_alerts})


@app.get("/budget/category/")
def budget_category_get_compat() -> dict[str, Any]:
    return _ok(_demo_budget_categories)


@app.post("/budget/category/")
def budget_category_upsert_compat(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    amount = float(payload.get("amount", 0))
    frequency = str(payload.get("frequency", "monthly"))
    if not name:
        raise HTTPException(status_code=400, detail="Category name required.")
    existing = next((item for item in _demo_budget_categories if item["name"].lower() == name.lower()), None)
    if existing:
        existing["allocated_amount"] = amount
        existing["frequency"] = frequency
        existing["monthly_equivalent"] = amount
        category = existing
    else:
        category = {"name": name, "allocated_amount": amount, "frequency": frequency, "spent_amount": 0.0, "remaining_amount": amount, "usage_percent": 0.0, "status": "on-track", "monthly_equivalent": amount}
        _demo_budget_categories.append(category)
    return _ok({"category": category, "categories": _demo_budget_categories, "feedback": ["Category budget saved."], "alerts": _demo_alerts})


@app.delete("/budget/category/{name}")
def budget_category_delete_compat(name: str) -> dict[str, Any]:
    global _demo_budget_categories
    _demo_budget_categories = [item for item in _demo_budget_categories if item["name"].lower() != name.lower()]
    return _ok({"categories": _demo_budget_categories, "feedback": ["Category removed."], "alerts": _demo_alerts})


@app.post("/decision/")
def decision_compat(payload: dict[str, Any]) -> dict[str, Any]:
    price = float(payload.get("price", 0))
    remaining = max(0.0, float(_demo_budget_global.get("remaining_amount", 0)) - price)
    status = "Affordable" if remaining >= 0 else "Risky"
    return _ok(
        {
            "item_name": str(payload.get("item_name", "Item")),
            "category": "General",
            "price": price,
            "affordability": "Within budget" if remaining >= 0 else "Over budget",
            "status": status,
            "budget_impact_percent": (price / float(_demo_budget_global.get("monthly_budget", 1))) * 100.0,
            "current_risk_level": "Medium",
            "new_risk_level": "High" if remaining < 0 else "Medium",
            "remaining_global_budget": remaining,
            "remaining_category_budget": remaining,
            "recommendation": "Proceed cautiously." if remaining >= 0 else "Delay purchase.",
        }
    )
