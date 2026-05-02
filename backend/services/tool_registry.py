from typing import Any
import json
import logging
from backend.storage import Storage
from backend.services.analytics import get_dashboard_analytics
from backend.services.budget_engine import get_global_budget_summary
from backend.models.predict import predict_next_expense, build_daily_expense_series
from backend.services.guardrails import validate_tool_args

logger = logging.getLogger(__name__)

# Define the OpenAI-compatible tool schemas
# We include JSON schemas corresponding to the Pydantic models in guardrails.py
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "Get the user's recent transactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "range": {
                        "type": "string",
                        "description": "The time range to get transactions for, e.g., '30d', 'all'"
                    }
                },
                "required": ["range"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Get the user's current account balance and high-level dashboard analytics (total income, expense, savings).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_spending_risk",
            "description": "Use the internal machine learning ensemble to predict the user's next expected expense and elevate risk thresholds.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_spending",
            "description": "Summarize the user's spending against their budget.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def execute_get_transactions(args: dict) -> dict:
    df = Storage.get_transactions()
    if df.empty:
        return {"status": "success", "data": "No transactions found."}
    
    # Simple mock processing roughly matching range
    return {"status": "success", "data": df.tail(10).to_dict(orient="records")}

def execute_get_balance(args: dict) -> dict:
    analytics = get_dashboard_analytics()
    return {"status": "success", "data": analytics}

def execute_detect_spending_risk(args: dict) -> dict:
    df = Storage.get_transactions()
    if df.empty:
        return {"status": "error", "message": "No transaction data available for prediction"}
    daily_series = build_daily_expense_series(df)
    prediction = predict_next_expense(daily_series)
    return {"status": "success", "data": prediction}

def execute_summarize_spending(args: dict) -> dict:
    summary = get_global_budget_summary()
    return {"status": "success", "data": summary}


TOOL_EXECUTORS = {
    "get_transactions": execute_get_transactions,
    "get_balance": execute_get_balance,
    "detect_spending_risk": execute_detect_spending_risk,
    "summarize_spending": execute_summarize_spending
}

def dispatch_tool(tool_name: str, raw_args_str: str) -> str:
    """Executes a tool after validating arguments via Pydantic guardrails."""
    try:
        args = json.loads(raw_args_str) if raw_args_str else {}
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Arguments must be a valid JSON string"})

    is_valid, payload_or_err = validate_tool_args(tool_name, args)
    if not is_valid:
        return json.dumps({"status": "error", "message": payload_or_err})
    
    executor = TOOL_EXECUTORS.get(tool_name)
    if not executor:
        return json.dumps({"status": "error", "message": f"Tool {tool_name} not implemented."})
    
    try:
        result = executor(args)
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error executing {tool_name}: {e}")
        return json.dumps({"status": "error", "message": str(e)})

