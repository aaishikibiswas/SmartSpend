import hashlib
import secrets
from typing import Any, Dict, List
import pandas as pd
import os
import logging
import time
import functools
import threading
from contextvars import ContextVar

try:
    from pymongo import MongoClient as PyMongoClient
except Exception:
    PyMongoClient = None

try:
    import mongomock
except Exception:
    mongomock = None

logger = logging.getLogger("smartspend.storage")
mongo_degraded_until = 0.0
current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)
local_transactions_buffer: Dict[int, List[Dict[str, Any]]] = {}
local_tx_next_id = 1_000_000

# ---------------------------------------------------------------------------
# Request-scoped transaction cache (TTL = 5 seconds)
# ---------------------------------------------------------------------------
_tx_cache_lock = threading.Lock()
_tx_cache_by_user: Dict[int, tuple[pd.DataFrame, float]] = {}
_TX_CACHE_TTL = 5.0  # seconds


def set_current_user_id(user_id: int | None):
    return current_user_id.set(user_id)


def reset_current_user_id(token) -> None:
    current_user_id.reset(token)


def get_current_user_id(required: bool = True) -> int | None:
    user_id = current_user_id.get()
    if user_id is None and required:
        raise PermissionError("Authentication required.")
    return user_id


def _owner_filter(extra: Dict[str, Any] | None = None, user_id: int | None = None) -> Dict[str, Any]:
    owner_id = user_id if user_id is not None else get_current_user_id()
    query: Dict[str, Any] = {"userId": owner_id}
    if extra:
        query.update(extra)
    return query


def _with_owner(doc: Dict[str, Any], user_id: int | None = None) -> Dict[str, Any]:
    owner_id = user_id if user_id is not None else get_current_user_id()
    row = dict(doc)
    row["userId"] = owner_id
    return row


def _get_cached_transactions(user_id: int) -> pd.DataFrame | None:
    with _tx_cache_lock:
        cached = _tx_cache_by_user.get(user_id)
        if cached is not None:
            df, ts = cached
            if (time.time() - ts) < _TX_CACHE_TTL:
                return df
    return None


def _set_cached_transactions(user_id: int, df: pd.DataFrame) -> None:
    with _tx_cache_lock:
        _tx_cache_by_user[user_id] = (df, time.time())


def invalidate_transaction_cache(user_id: int | None = None) -> None:
    """Call this after any write to transactions so next read is fresh."""
    with _tx_cache_lock:
        if user_id is None:
            _tx_cache_by_user.clear()
        else:
            _tx_cache_by_user.pop(user_id, None)


def _is_mongo_degraded() -> bool:
    return time.time() < mongo_degraded_until


def _mark_mongo_degraded(seconds: float = 30.0) -> None:
    global mongo_degraded_until
    mongo_degraded_until = max(mongo_degraded_until, time.time() + seconds)


def _empty_transactions_df() -> pd.DataFrame:
    return pd.DataFrame(columns=["id", "date", "merchant", "category", "amount", "type", "language"])


def _buffer_transactions(new_txs: List[Dict[str, Any]], user_id: int) -> None:
    global local_tx_next_id
    user_buffer = local_transactions_buffer.setdefault(user_id, [])
    for tx in new_txs:
        row = _with_owner(tx, user_id)
        if "id" not in row:
            row["id"] = local_tx_next_id
            local_tx_next_id += 1
        user_buffer.append(row)


def _build_mongo_client():
    mongo_uri = os.getenv(
        "MONGODB_URI",
        "mongodb+srv://aaishikibiswas_db_user:aki9090@cluster0.hc1jgeu.mongodb.net/?appName=Cluster0",
    )
    safe_uri = mongo_uri.split("@")[-1] if "@" in mongo_uri else mongo_uri

    if PyMongoClient is not None:
        try:
            client = PyMongoClient(mongo_uri)
            client.admin.command("ping")
            logger.info("Connected to MongoDB at %s", safe_uri)
            return client
        except Exception:
            logger.warning("MongoDB is not reachable at %s; falling back to in-memory storage.", safe_uri)

    if mongomock is not None:
        logger.warning("Using in-memory mongomock storage for local development.")
        return mongomock.MongoClient()

    raise RuntimeError(
        "MongoDB is not reachable and mongomock is not installed. "
        "Install/start MongoDB, or run `pip install mongomock` for local in-memory fallback."
    )

mongo_client = _build_mongo_client()
db = mongo_client["smartspend"]

# Initialization of default data
DEFAULT_GOALS = [
    {"id": 1, "name": "MacBook Pro M3", "target": 125000, "achieved": 65000, "daysLeft": 124, "color": "bg-[#8B5CF6]"},
    {"id": 2, "name": "Emergency Fund", "target": 500000, "achieved": 458000, "daysLeft": 15, "color": "bg-emerald-400"},
]

DEFAULT_BILLS = [
    {"id": 1, "name": "Internet (Fiber)", "due": "Due Today", "amount": 2400, "icon": "Wifi", "color": "red"},
    {"id": 2, "name": "Electricity", "due": "Due in 4 days", "amount": 4120, "icon": "Zap", "color": "blue"},
]

DEFAULT_EMIS = [
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

DEFAULT_BUDGET_CONFIG = {
    "type": "global",
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

def _clean_id(doc):
    if doc and "_id" in doc:
        del doc["_id"]
    return doc


# Legacy module compatibility: several services still import these globals.
goals_db: List[Dict[str, Any]] = []
bills_db: List[Dict[str, Any]] = []
alerts_db: List[Dict[str, Any]] = []


def _refresh_legacy_views() -> None:
    global goals_db, bills_db, alerts_db
    user_id = get_current_user_id(required=False)
    query = {"userId": user_id} if user_id is not None else {"userId": {"$exists": False}}
    goals_db = [_clean_id(dict(doc)) for doc in db.goals.find(query, {"_id": 0})]
    bills_db = [_clean_id(dict(doc)) for doc in db.bills.find(query, {"_id": 0})]
    alerts_db = [_clean_id(dict(doc)) for doc in db.alerts.find(query, {"_id": 0})]

class Storage:
    @staticmethod
    def initialize() -> None:
        if db.users.count_documents({}) == 0:
            user = Storage.create_user("Adaline Chen", "adaline@smartspend.ai", "SmartSpend@123")
            default_user_id = user["id"]
        else:
            first_user = db.users.find_one(sort=[("id", 1)])
            default_user_id = first_user["id"] if first_user else 1

        for collection_name in [
            "transactions",
            "goals",
            "bills",
            "emis",
            "budget",
            "alerts",
            "subscriptions",
            "suppressed_subscriptions",
            "suppressed_emis",
            "uploaded_statements",
            "wallet",
            "simulator",
            "preferences",
            "ai_insights",
        ]:
            getattr(db, collection_name).update_many(
                {"userId": {"$exists": False}},
                {"$set": {"userId": default_user_id}},
            )

        if db.goals.count_documents({"userId": default_user_id}) == 0:
            db.goals.insert_many([_with_owner(goal, default_user_id) for goal in DEFAULT_GOALS])
        if db.bills.count_documents({"userId": default_user_id}) == 0:
            db.bills.insert_many([_with_owner(bill, default_user_id) for bill in DEFAULT_BILLS])
        if db.emis.count_documents({"userId": default_user_id}) == 0:
            db.emis.insert_many([_with_owner(emi, default_user_id) for emi in DEFAULT_EMIS])
        if db.budget.count_documents({"type": "global", "userId": default_user_id}) == 0:
            db.budget.insert_one(_with_owner(DEFAULT_BUDGET_CONFIG, default_user_id))
        _refresh_legacy_views()

    @staticmethod
    def get_transactions() -> pd.DataFrame:
        user_id = get_current_user_id()
        cached = _get_cached_transactions(user_id)
        if cached is not None:
            return cached
        if _is_mongo_degraded():
            rows = local_transactions_buffer.get(user_id, [])
            df = pd.DataFrame(rows) if rows else _empty_transactions_df()
            _set_cached_transactions(user_id, df)
            return df
        try:
            txs = list(db.transactions.find(_owner_filter(user_id=user_id), {"_id": 0}))
            if local_transactions_buffer.get(user_id):
                txs.extend(local_transactions_buffer[user_id])
            df = pd.DataFrame(txs) if txs else _empty_transactions_df()
            _set_cached_transactions(user_id, df)
            return df
        except Exception as exc:
            import traceback
            traceback.print_exc()
            _mark_mongo_degraded()
            logger.error("Failed to load transactions from MongoDB, returning empty dataframe: %s: %s", type(exc).__name__, exc)
            rows = local_transactions_buffer.get(user_id, [])
            df = pd.DataFrame(rows) if rows else _empty_transactions_df()
            _set_cached_transactions(user_id, df)
            return df

    @staticmethod
    def replace_transactions(new_txs: List[Dict[str, Any]]):
        user_id = get_current_user_id()
        invalidate_transaction_cache(user_id)
        if _is_mongo_degraded():
            local_transactions_buffer[user_id] = []
            if new_txs:
                _buffer_transactions(new_txs, user_id)
            return
        try:
            db.transactions.delete_many(_owner_filter(user_id=user_id))
            local_transactions_buffer[user_id] = []
            if new_txs:
                Storage.add_transactions(new_txs)
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to replace transactions in MongoDB, buffering locally: %s: %s", type(exc).__name__, exc)
            local_transactions_buffer[user_id] = []
            if new_txs:
                _buffer_transactions(new_txs, user_id)

    @staticmethod
    def add_transactions(new_txs: List[Dict[str, Any]]):
        if not new_txs: return
        user_id = get_current_user_id()
        invalidate_transaction_cache(user_id)
        if _is_mongo_degraded():
            _buffer_transactions(new_txs, user_id)
            return
        try:
            max_tx = db.transactions.find_one(_owner_filter(user_id=user_id), sort=[("id", -1)])
            start_id = max_tx["id"] + 1 if max_tx and "id" in max_tx else 1
            docs = []
            for i, tx in enumerate(new_txs):
                row = _with_owner(tx, user_id)
                row["id"] = start_id + i
                docs.append(row)
            db.transactions.insert_many(docs)
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to add transactions to MongoDB, buffering locally: %s: %s", type(exc).__name__, exc)
            _buffer_transactions(new_txs, user_id)

    @staticmethod
    def add_transaction(tx: Dict[str, Any]):
        Storage.add_transactions([tx])

    @staticmethod
    def reset_alerts():
        db.alerts.delete_many(_owner_filter())
        _refresh_legacy_views()

    @staticmethod
    def sync_alerts(new_alerts: List[Dict[str, Any]]):
        if _is_mongo_degraded():
            return
        try:
            user_id = get_current_user_id()
            existing = list(db.alerts.find(_owner_filter(user_id=user_id), {"_id": 0}))
            existing_map = {f"{a['title']}::{a['message']}": a for a in existing}
            
            db.alerts.delete_many(_owner_filter(user_id=user_id))
            if not new_alerts:
                _refresh_legacy_views()
                return

            max_id = max((a.get("id", 0) for a in existing), default=0)
            
            new_count = sum(1 for a in new_alerts if f"{a['title']}::{a['message']}" not in existing_map)
            current_new_id = max_id + new_count
            
            docs_to_insert = []
            new_alerts_returned = []
            
            for alert in new_alerts:
                key = f"{alert['title']}::{alert['message']}"
                doc = dict(alert)
                doc["userId"] = user_id
                if key in existing_map:
                    doc["id"] = existing_map[key]["id"]
                else:
                    doc["id"] = current_new_id
                    current_new_id -= 1
                    new_alerts_returned.append(doc)
                docs_to_insert.append(doc)
                
            if docs_to_insert:
                db.alerts.insert_many(docs_to_insert)
            _refresh_legacy_views()
            
            for a in new_alerts_returned:
                if "_id" in a:
                    del a["_id"]
            
            return new_alerts_returned
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to sync alerts in MongoDB: %s: %s", type(exc).__name__, exc)
            return []

    @staticmethod
    def add_alert(alert: Dict[str, Any]):
        user_id = get_current_user_id()
        max_alert = db.alerts.find_one(_owner_filter(user_id=user_id), sort=[("id", -1)])
        next_id = max_alert["id"] + 1 if max_alert and "id" in max_alert else 1
        doc = _with_owner(alert, user_id)
        doc["id"] = next_id
        db.alerts.insert_one(doc)
        _refresh_legacy_views()

    @staticmethod
    def get_alerts() -> List[Dict[str, Any]]:
        if _is_mongo_degraded():
            return []
        try:
            return [_clean_id(doc) for doc in db.alerts.find(_owner_filter(), sort=[("id", -1)])]
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to load alerts from MongoDB, returning empty list: %s: %s", type(exc).__name__, exc)
            return []

    @staticmethod
    def get_budget_config() -> Dict[str, Any]:
        if _is_mongo_degraded():
            config = DEFAULT_BUDGET_CONFIG
        else:
            try:
                config = db.budget.find_one(_owner_filter({"type": "global"})) or _with_owner(DEFAULT_BUDGET_CONFIG)
            except Exception as exc:
                _mark_mongo_degraded()
                logger.error("Failed to load budget config from MongoDB, using defaults: %s: %s", type(exc).__name__, exc)
                config = DEFAULT_BUDGET_CONFIG
        categories = {}
        for name, value in config.get("categories", {}).items():
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
            "monthly": config.get("monthly", 50000),
            "weekly": config.get("weekly", 11500),
            "auto_distribute": bool(config.get("auto_distribute", False)),
            "categories": categories,
        }

    @staticmethod
    def update_budget_config(config: Dict[str, Any]):
        current = Storage.get_budget_config()
        monthly = int(config.get("monthly", current["monthly"]))
        weekly = int(config.get("weekly", current["weekly"]))
        auto_distribute = bool(config.get("auto_distribute", current["auto_distribute"]))
        categories = config.get("categories", current["categories"])
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
        db.budget.update_one(
            _owner_filter({"type": "global"}),
            {"$set": {
                "monthly": monthly,
                "weekly": weekly,
                "auto_distribute": auto_distribute,
                "categories": normalized_categories,
                "userId": get_current_user_id(),
            }},
            upsert=True
        )

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()

    @staticmethod
    def create_user(full_name: str, email: str, password: str) -> Dict[str, Any]:
        normalized_email = email.strip().lower()
        if db.users.find_one({"email": normalized_email}):
            raise ValueError("An account with this email already exists.")

        salt = secrets.token_hex(8)
        max_user = db.users.find_one(sort=[("id", -1)])
        next_id = max_user["id"] + 1 if max_user and "id" in max_user else 1

        user = {
            "id": next_id,
            "full_name": full_name.strip(),
            "email": normalized_email,
            "plan": "Pro Plan",
            "avatar_seed": normalized_email.replace("@", "-"),
            "preferred_currency": "INR",
            "timezone": "Asia/Kolkata",
            "city": "Kolkata",
            "occupation": "Financial Planner",
            "password_hash": Storage._hash_password(password, salt),
            "password_salt": salt,
        }
        db.users.insert_one(user)
        return _clean_id({key: value for key, value in user.items() if key not in {"password_hash", "password_salt", "_id"}})

    @staticmethod
    def get_first_user_id() -> int | None:
        user = db.users.find_one(sort=[("id", 1)])
        return int(user["id"]) if user and "id" in user else None

    @staticmethod
    def authenticate_user(email: str, password: str) -> Dict[str, Any] | None:
        normalized_email = email.strip().lower()
        user = db.users.find_one({"email": normalized_email})
        if not user:
            return None
        expected_hash = Storage._hash_password(password, user["password_salt"])
        if secrets.compare_digest(expected_hash, user["password_hash"]):
            return _clean_id({key: value for key, value in user.items() if key not in {"password_hash", "password_salt", "_id"}})
        return None

    @staticmethod
    def create_session(user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        db.sessions.insert_one({"token": token, "user_id": user_id})
        return token

    @staticmethod
    def get_user_by_session(token: str | None) -> Dict[str, Any] | None:
        if not token:
            return None
        session = db.sessions.find_one({"token": token})
        if not session:
            return None
        user = db.users.find_one({"id": session["user_id"]})
        if user:
            return _clean_id({key: value for key, value in user.items() if key not in {"password_hash", "password_salt", "_id"}})
        return None

    @staticmethod
    def delete_session(token: str | None):
        if token:
            db.sessions.delete_one({"token": token})

    @staticmethod
    def update_user(user_id: int, updates: Dict[str, Any]) -> Dict[str, Any] | None:
        allowed_fields = {"full_name", "plan", "avatar_seed", "preferred_currency", "timezone", "city", "occupation"}
        valid_updates = {}
        for key, value in updates.items():
            if key in allowed_fields and isinstance(value, str) and value.strip():
                valid_updates[key] = value.strip()
        
        if valid_updates:
            db.users.update_one({"id": user_id}, {"$set": valid_updates})
        
        user = db.users.find_one({"id": user_id})
        if user:
            return _clean_id({key: value for key, value in user.items() if key not in {"password_hash", "password_salt", "_id"}})
        return None

    @staticmethod
    def get_emis() -> List[Dict[str, Any]]:
        if _is_mongo_degraded():
            return []
        try:
            return [_clean_id(doc) for doc in db.emis.find(_owner_filter(), {"_id": 0})]
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to load EMIs from MongoDB, returning empty list: %s: %s", type(exc).__name__, exc)
            return []

    @staticmethod
    def get_subscriptions() -> List[Dict[str, Any]]:
        if _is_mongo_degraded():
            return []
        try:
            return [_clean_id(doc) for doc in db.subscriptions.find(_owner_filter(), {"_id": 0})]
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to load subscriptions from MongoDB, returning empty list: %s: %s", type(exc).__name__, exc)
            return []

    @staticmethod
    def add_subscription(subscription: Dict[str, Any]) -> Dict[str, Any]:
        user_id = get_current_user_id()
        max_sub = db.subscriptions.find_one(_owner_filter(user_id=user_id), sort=[("id", -1)])
        next_id = max_sub["id"] + 1 if max_sub and "id" in max_sub else 1
        doc = _with_owner(subscription, user_id)
        doc["id"] = next_id
        db.subscriptions.insert_one(doc)
        return _clean_id(doc)

    @staticmethod
    def remove_subscription(name: str) -> bool:
        normalized = str(name).strip().lower()
        try:
            id_val = int(name)
            result = db.subscriptions.delete_one(_owner_filter({"$or": [{"id": id_val}, {"name": {"$regex": f"^{normalized}$", "$options": "i"}}]}))
        except ValueError:
            result = db.subscriptions.delete_one(_owner_filter({"name": {"$regex": f"^{normalized}$", "$options": "i"}}))
        return result.deleted_count > 0

    @staticmethod
    def add_emi(emi: Dict[str, Any]) -> Dict[str, Any]:
        user_id = get_current_user_id()
        max_emi = db.emis.find_one(_owner_filter(user_id=user_id), sort=[("id", -1)])
        next_id = max_emi["id"] + 1 if max_emi and "id" in max_emi else 1
        doc = _with_owner(emi, user_id)
        doc["id"] = next_id
        db.emis.insert_one(doc)
        return _clean_id(doc)

    @staticmethod
    def remove_emi(identifier: str) -> bool:
        normalized = str(identifier).strip().lower()
        try:
            id_val = int(identifier)
            result = db.emis.delete_one(_owner_filter({"$or": [{"id": id_val}, {"name": {"$regex": f"^{normalized}$", "$options": "i"}}]}))
        except ValueError:
            result = db.emis.delete_one(_owner_filter({"name": {"$regex": f"^{normalized}$", "$options": "i"}}))
            
        if result.deleted_count > 0:
            return True
        Storage.suppress_emi(str(identifier))
        return False

    @staticmethod
    def get_suppressed_subscriptions() -> set[str]:
        if _is_mongo_degraded():
            return set()
        try:
            return {doc["name"] for doc in db.suppressed_subscriptions.find(_owner_filter())}
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to load suppressed subscriptions, returning empty set: %s: %s", type(exc).__name__, exc)
            return set()

    @staticmethod
    def suppress_subscription(name: str) -> None:
        if str(name).strip():
            db.suppressed_subscriptions.update_one(
                _owner_filter({"name": str(name).strip().lower()}),
                {"$set": {"name": str(name).strip().lower(), "userId": get_current_user_id()}},
                upsert=True
            )

    @staticmethod
    def get_suppressed_emis() -> set[str]:
        if _is_mongo_degraded():
            return set()
        try:
            return {doc["name"] for doc in db.suppressed_emis.find(_owner_filter())}
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to load suppressed EMIs, returning empty set: %s: %s", type(exc).__name__, exc)
            return set()

    @staticmethod
    def suppress_emi(name: str) -> None:
        if str(name).strip():
            db.suppressed_emis.update_one(
                _owner_filter({"name": str(name).strip().lower()}),
                {"$set": {"name": str(name).strip().lower(), "userId": get_current_user_id()}},
                upsert=True
            )

    @staticmethod
    def get_bills() -> List[Dict[str, Any]]:
        if _is_mongo_degraded():
            return []
        try:
            return [_clean_id(doc) for doc in db.bills.find(_owner_filter(), {"_id": 0})]
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to load bills from MongoDB, returning empty list: %s: %s", type(exc).__name__, exc)
            return []

    @staticmethod
    def add_bill(bill: Dict[str, Any]) -> Dict[str, Any]:
        user_id = get_current_user_id()
        max_bill = db.bills.find_one(_owner_filter(user_id=user_id), sort=[("id", -1)])
        next_id = max_bill["id"] + 1 if max_bill and "id" in max_bill else 1
        doc = _with_owner(bill, user_id)
        doc["id"] = next_id
        db.bills.insert_one(doc)
        _refresh_legacy_views()
        return _clean_id(doc)

    @staticmethod
    def remove_bill(identifier: str) -> bool:
        normalized = str(identifier).strip().lower()
        try:
            id_val = int(identifier)
            result = db.bills.delete_one(_owner_filter({"$or": [{"id": id_val}, {"name": {"$regex": f"^{normalized}$", "$options": "i"}}]}))
        except ValueError:
            result = db.bills.delete_one(_owner_filter({"name": {"$regex": f"^{normalized}$", "$options": "i"}}))
        deleted = result.deleted_count > 0
        if deleted:
            _refresh_legacy_views()
        return deleted

    @staticmethod
    def replace_bills(items: List[Dict[str, Any]]) -> None:
        user_id = get_current_user_id()
        db.bills.delete_many(_owner_filter(user_id=user_id))
        if items:
            docs = []
            for item in items:
                docs.append(_with_owner(item, user_id))
            db.bills.insert_many(docs)
        _refresh_legacy_views()

    @staticmethod
    def get_goals() -> List[Dict[str, Any]]:
        if _is_mongo_degraded():
            return []
        try:
            return [_clean_id(doc) for doc in db.goals.find(_owner_filter(), {"_id": 0})]
        except Exception as exc:
            _mark_mongo_degraded()
            logger.error("Failed to load goals from MongoDB, returning empty list: %s: %s", type(exc).__name__, exc)
            return []

    @staticmethod
    def add_goal(goal: Dict[str, Any]) -> Dict[str, Any]:
        user_id = get_current_user_id()
        max_goal = db.goals.find_one(_owner_filter(user_id=user_id), sort=[("id", -1)])
        next_id = max_goal["id"] + 1 if max_goal and "id" in max_goal else 1
        doc = _with_owner(goal, user_id)
        doc["id"] = next_id
        db.goals.insert_one(doc)
        _refresh_legacy_views()
        return _clean_id(doc)

    @staticmethod
    def add_uploaded_statement(file_info: Dict[str, Any]) -> None:
        db.uploaded_statements.insert_one(_with_owner(file_info))

Storage.initialize()
