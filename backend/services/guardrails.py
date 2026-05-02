from typing import Any, Optional
from pydantic import BaseModel, Field

class GetTransactionsParams(BaseModel):
    range: str = Field(description="The time range to get transactions for, e.g., '30d', 'all'")

class GetBalanceParams(BaseModel):
    pass  # No parameters needed

class DetectSpendingRiskParams(BaseModel):
    pass  # Parameters will be implicitly derived from user session context on the backend

class SummarizeSpendingParams(BaseModel):
    pass

def validate_tool_args(tool_name: str, args: dict) -> tuple[bool, Any]:
    """Validates unparsed JSON args coming from the LLM against Pydantic schemas."""
    schemas = {
        "get_transactions": GetTransactionsParams,
        "get_balance": GetBalanceParams,
        "detect_spending_risk": DetectSpendingRiskParams,
        "summarize_spending": SummarizeSpendingParams,
    }
    schema_cls = schemas.get(tool_name)
    if not schema_cls:
        return False, f"Unknown tool: {tool_name}"
    
    try:
        validated = schema_cls(**args)
        return True, validated
    except Exception as e:
        return False, f"Validation error for {tool_name}: {str(e)}"
