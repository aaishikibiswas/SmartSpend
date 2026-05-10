from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Any

try:
    import pandas as pd
except Exception:  # pragma: no cover - pandas is present in the app runtime
    pd = None


def to_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        return value if isfinite(value) else 0
    if hasattr(value, "item"):
        try:
            return to_json_safe(value.item())
        except Exception:
            pass
    if pd is not None:
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
    return value
