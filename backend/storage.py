import hashlib
import json
import secrets
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


transactions_db: List[Dict[str, Any]] = []

goals_db: List[Dict[str, Any]] = [
    {"id": 1, "name": "MacBook Pro M3", "target": 125000, "achieved": 65000, "daysLeft": 124, "color": "bg-[#8B5CF6]"},
    {"id": 2, "name": "Emergency Fund", "target": 500000, "achieved": 458000, "daysLeft": 15, "color": "bg-emerald-400"},
]

bills_db: List[Dict[str, Any]] = [
    {"id": 1, "name": "Internet (Fiber)", "due": "Due Today", "amount": 2400, "icon": "Wifi", "color": "red"},
    {"id": 2, "name": "Electricity", "due": "Due in 4 days", "amount": 4120, "icon": "Zap", "color": "blue"},
]

subscriptions_db: List[Dict[str, Any]] = []

emis_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Car Loan",
        "total_amount": 420000,
        "monthly_emi": 12850,
        "remaining_months": 19,
        "interest_rate": 9.2,
        "due_date": "2026-04-18",
    }
]

alerts_db: List[Dict[str, Any]] = []
suppressed_subscriptions_db: set[str] = set()
suppressed_emis_db: set[str] = set()

users_db: List[Dict[str, Any]] = []
sessions_db: Dict[str, int] = {}

budget_config = {
    "monthly": 50000,
    "weekly": 11500,
    "auto_distribute": False,
    "categories": {
        "Housing": {"amount": 20000, "frequency": "Monthly"},
        "Food": {"amount": 12000, "frequency": "Monthly"},
        "Transport": {"amount": 5000, "frequency": "Monthly"},
        "Entertainment": {"amount": 8000, "frequency": "Monthly"},
    },
}

DEFAULT_GOALS = deepcopy(goals_db)
DEFAULT_BILLS = deepcopy(bills_db)
DEFAULT_SUBSCRIPTIONS = deepcopy(subscriptions_db)
DEFAULT_EMIS = deepcopy(emis_db)
DEFAULT_BUDGET_CONFIG = deepcopy(budget_config)


class Storage:
    TRANSACTIONS_PATH = DATA_DIR / "transactions.json"
    GOALS_PATH = DATA_DIR / "goals.json"
    BILLS_PATH = DATA_DIR / "bills.json"
    SUBSCRIPTIONS_PATH = DATA_DIR / "subscriptions.json"
    EMIS_PATH = DATA_DIR / "emis.json"
    ALERTS_PATH = DATA_DIR / "alerts.json"
    USERS_PATH = DATA_DIR / "users.json"
    SESSIONS_PATH = DATA_DIR / "sessions.json"
    BUDGET_PATH = DATA_DIR / "budget.json"
    SUPPRESSED_SUBSCRIPTIONS_PATH = DATA_DIR / "suppressed_subscriptions.json"
    SUPPRESSED_EMIS_PATH = DATA_DIR / "suppressed_emis.json"

    @staticmethod
    def _save_transactions() -> None:
        _write_json(Storage.TRANSACTIONS_PATH, transactions_db)

    @staticmethod
    def _save_goals() -> None:
        _write_json(Storage.GOALS_PATH, goals_db)

    @staticmethod
    def _save_bills() -> None:
        _write_json(Storage.BILLS_PATH, bills_db)

    @staticmethod
    def _save_subscriptions() -> None:
        _write_json(Storage.SUBSCRIPTIONS_PATH, subscriptions_db)

    @staticmethod
    def _save_emis() -> None:
        _write_json(Storage.EMIS_PATH, emis_db)

    @staticmethod
    def _save_alerts() -> None:
        _write_json(Storage.ALERTS_PATH, alerts_db)

    @staticmethod
    def _save_users() -> None:
        _write_json(Storage.USERS_PATH, users_db)

    @staticmethod
    def _save_sessions() -> None:
        _write_json(Storage.SESSIONS_PATH, sessions_db)

    @staticmethod
    def _save_budget() -> None:
        _write_json(Storage.BUDGET_PATH, budget_config)

    @staticmethod
    def _save_suppressed() -> None:
        _write_json(Storage.SUPPRESSED_SUBSCRIPTIONS_PATH, sorted(suppressed_subscriptions_db))
        _write_json(Storage.SUPPRESSED_EMIS_PATH, sorted(suppressed_emis_db))

    @staticmethod
    def initialize() -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        transactions_db.clear()
        transactions_db.extend(_read_json(Storage.TRANSACTIONS_PATH, []))

        goals_db.clear()
        goals_db.extend(_read_json(Storage.GOALS_PATH, deepcopy(DEFAULT_GOALS)))

        bills_db.clear()
        bills_db.extend(_read_json(Storage.BILLS_PATH, deepcopy(DEFAULT_BILLS)))

        subscriptions_db.clear()
        subscriptions_db.extend(_read_json(Storage.SUBSCRIPTIONS_PATH, deepcopy(DEFAULT_SUBSCRIPTIONS)))

        emis_db.clear()
        emis_db.extend(_read_json(Storage.EMIS_PATH, deepcopy(DEFAULT_EMIS)))

        alerts_db.clear()
        alerts_db.extend(_read_json(Storage.ALERTS_PATH, []))

        users_db.clear()
        users_db.extend(_read_json(Storage.USERS_PATH, []))

        sessions_db.clear()
        sessions_db.update({str(key): int(value) for key, value in _read_json(Storage.SESSIONS_PATH, {}).items()})

        budget_loaded = _read_json(Storage.BUDGET_PATH, deepcopy(DEFAULT_BUDGET_CONFIG))
        budget_config.clear()
        budget_config.update(budget_loaded)
        budget_config.setdefault("monthly", DEFAULT_BUDGET_CONFIG["monthly"])
        budget_config.setdefault("weekly", DEFAULT_BUDGET_CONFIG["weekly"])
        budget_config.setdefault("auto_distribute", DEFAULT_BUDGET_CONFIG["auto_distribute"])
        budget_config.setdefault("categories", deepcopy(DEFAULT_BUDGET_CONFIG["categories"]))

        suppressed_subscriptions_db.clear()
        suppressed_subscriptions_db.update({str(item).strip().lower() for item in _read_json(Storage.SUPPRESSED_SUBSCRIPTIONS_PATH, [])})

        suppressed_emis_db.clear()
        suppressed_emis_db.update({str(item).strip().lower() for item in _read_json(Storage.SUPPRESSED_EMIS_PATH, [])})

    @staticmethod
    def get_transactions() -> pd.DataFrame:
        if not transactions_db:
            return pd.DataFrame(columns=["id", "date", "merchant", "category", "amount", "type", "language"])
        return pd.DataFrame(transactions_db)

    @staticmethod
    def replace_transactions(new_txs: List[Dict[str, Any]]):
        transactions_db.clear()
        Storage.add_transactions(new_txs)

    @staticmethod
    def add_transactions(new_txs: List[Dict[str, Any]]):
        start_id = max([tx["id"] for tx in transactions_db], default=0) + 1
        for i, tx in enumerate(new_txs):
            row = dict(tx)
            row["id"] = start_id + i
            transactions_db.append(row)
        Storage._save_transactions()

    @staticmethod
    def add_transaction(tx: Dict[str, Any]):
        Storage.add_transactions([tx])

    @staticmethod
    def reset_alerts():
        alerts_db.clear()
        Storage._save_alerts()

    @staticmethod
    def add_alert(alert: Dict[str, Any]):
        next_alert = dict(alert)
        next_alert["id"] = max([a["id"] for a in alerts_db], default=0) + 1
        alerts_db.insert(0, next_alert)
        Storage._save_alerts()

    @staticmethod
    def get_alerts() -> List[Dict[str, Any]]:
        return [dict(item) for item in alerts_db]

    @staticmethod
    def get_budget_config() -> Dict[str, Any]:
        categories = {}
        for name, value in budget_config["categories"].items():
            if isinstance(value, dict):
                categories[name] = {
                    "amount": int(value.get("amount", 0)),
                    "frequency": value.get("frequency", "Monthly"),
                }
            else:
                categories[name] = {
                    "amount": int(value),
                    "frequency": "Monthly",
                }
        return {
            "monthly": budget_config["monthly"],
            "weekly": budget_config["weekly"],
            "auto_distribute": bool(budget_config.get("auto_distribute", False)),
            "categories": categories,
        }

    @staticmethod
    def update_budget_config(config: Dict[str, Any]):
        budget_config["monthly"] = int(config.get("monthly", budget_config["monthly"]))
        budget_config["weekly"] = int(config.get("weekly", budget_config["weekly"]))
        budget_config["auto_distribute"] = bool(config.get("auto_distribute", budget_config.get("auto_distribute", False)))
        categories = config.get("categories", budget_config["categories"])
        normalized_categories = {}
        for name, value in categories.items():
            if not str(name).strip():
                continue
            if isinstance(value, dict):
                amount = int(value.get("amount", 0))
                frequency = value.get("frequency", "Monthly")
            else:
                amount = int(value)
                frequency = "Monthly"
            if amount >= 0:
                normalized_categories[str(name)] = {
                    "amount": amount,
                    "frequency": frequency,
                }
        budget_config["categories"] = normalized_categories
        Storage._save_budget()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()

    @staticmethod
    def create_user(full_name: str, email: str, password: str) -> Dict[str, Any]:
        normalized_email = email.strip().lower()
        if any(user["email"] == normalized_email for user in users_db):
            raise ValueError("An account with this email already exists.")

        salt = secrets.token_hex(8)
        user = {
            "id": max([user["id"] for user in users_db], default=0) + 1,
            "full_name": full_name.strip(),
            "email": normalized_email,
            "plan": "Pro Plan",
            "avatar_seed": normalized_email.replace("@", "-"),
            "password_hash": Storage._hash_password(password, salt),
            "password_salt": salt,
        }
        users_db.append(user)
        Storage._save_users()
        return {key: value for key, value in user.items() if key not in {"password_hash", "password_salt"}}

    @staticmethod
    def authenticate_user(email: str, password: str) -> Dict[str, Any] | None:
        normalized_email = email.strip().lower()
        for user in users_db:
            if user["email"] != normalized_email:
                continue
            expected_hash = Storage._hash_password(password, user["password_salt"])
            if secrets.compare_digest(expected_hash, user["password_hash"]):
                return {key: value for key, value in user.items() if key not in {"password_hash", "password_salt"}}
        return None

    @staticmethod
    def create_session(user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        sessions_db[token] = user_id
        Storage._save_sessions()
        return token

    @staticmethod
    def get_user_by_session(token: str | None) -> Dict[str, Any] | None:
        if not token:
            return None
        user_id = sessions_db.get(token)
        if user_id is None:
            return None
        for user in users_db:
            if user["id"] == user_id:
                return {key: value for key, value in user.items() if key not in {"password_hash", "password_salt"}}
        return None

    @staticmethod
    def delete_session(token: str | None):
        if token:
            sessions_db.pop(token, None)
            Storage._save_sessions()

    @staticmethod
    def update_user(user_id: int, updates: Dict[str, Any]) -> Dict[str, Any] | None:
        allowed_fields = {"full_name", "plan", "avatar_seed"}
        for user in users_db:
            if user["id"] != user_id:
                continue
            for key, value in updates.items():
                if key in allowed_fields and isinstance(value, str) and value.strip():
                    user[key] = value.strip()
            Storage._save_users()
            return {key: value for key, value in user.items() if key not in {"password_hash", "password_salt"}}
        return None

    @staticmethod
    def get_emis() -> List[Dict[str, Any]]:
        return [dict(item) for item in emis_db]

    @staticmethod
    def get_subscriptions() -> List[Dict[str, Any]]:
        return [dict(item) for item in subscriptions_db]

    @staticmethod
    def add_subscription(subscription: Dict[str, Any]) -> Dict[str, Any]:
        next_item = dict(subscription)
        next_item["id"] = max([int(item.get("id", 0)) for item in subscriptions_db], default=0) + 1
        subscriptions_db.append(next_item)
        Storage._save_subscriptions()
        return dict(next_item)

    @staticmethod
    def remove_subscription(name: str) -> bool:
        normalized = str(name).strip().lower()
        filtered = [item for item in subscriptions_db if str(item.get("name", "")).strip().lower() != normalized and str(item.get("id")) != str(name)]
        removed = len(filtered) != len(subscriptions_db)
        subscriptions_db.clear()
        subscriptions_db.extend(filtered)
        if removed:
            Storage._save_subscriptions()
            return True
        return False

    @staticmethod
    def add_emi(emi: Dict[str, Any]) -> Dict[str, Any]:
        next_item = dict(emi)
        next_item["id"] = max([item["id"] for item in emis_db], default=0) + 1
        emis_db.append(next_item)
        Storage._save_emis()
        return dict(next_item)

    @staticmethod
    def remove_emi(identifier: str) -> bool:
        filtered = [
            item
            for item in emis_db
            if str(item.get("id")) != str(identifier) and str(item.get("name", "")).strip().lower() != str(identifier).strip().lower()
        ]
        removed = len(filtered) != len(emis_db)
        emis_db.clear()
        emis_db.extend(filtered)
        if removed:
            Storage._save_emis()
            return True
        suppressed_emis_db.add(str(identifier).strip().lower())
        Storage._save_suppressed()
        return False

    @staticmethod
    def get_suppressed_subscriptions() -> set[str]:
        return set(suppressed_subscriptions_db)

    @staticmethod
    def suppress_subscription(name: str) -> None:
        if str(name).strip():
            suppressed_subscriptions_db.add(str(name).strip().lower())
            Storage._save_suppressed()

    @staticmethod
    def get_suppressed_emis() -> set[str]:
        return set(suppressed_emis_db)

    @staticmethod
    def get_bills() -> List[Dict[str, Any]]:
        return [dict(item) for item in bills_db]

    @staticmethod
    def add_bill(bill: Dict[str, Any]) -> Dict[str, Any]:
        next_bill = dict(bill)
        next_bill["id"] = max([b["id"] for b in bills_db], default=0) + 1
        bills_db.append(next_bill)
        Storage._save_bills()
        return dict(next_bill)

    @staticmethod
    def remove_bill(identifier: str) -> bool:
        filtered = [
            item
            for item in bills_db
            if str(item.get("id")) != str(identifier) and str(item.get("name", "")).strip().lower() != str(identifier).strip().lower()
        ]
        removed = len(filtered) != len(bills_db)
        bills_db.clear()
        bills_db.extend(filtered)
        if removed:
            Storage._save_bills()
        return removed

    @staticmethod
    def replace_bills(items: List[Dict[str, Any]]) -> None:
        bills_db.clear()
        bills_db.extend(items)
        Storage._save_bills()


Storage.initialize()
if not users_db:
    Storage.create_user("Adaline Chen", "adaline@smartspend.ai", "SmartSpend@123")
Storage._save_budget()
Storage._save_goals()
Storage._save_bills()
Storage._save_subscriptions()
Storage._save_emis()
Storage._save_transactions()
Storage._save_alerts()
Storage._save_users()
Storage._save_sessions()
Storage._save_suppressed()
