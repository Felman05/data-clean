"""Data profiling functions — compute per-column and overall statistics."""
from typing import Any
import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute a full profile of a DataFrame.

    Returns a dict with:
      - overview: {rows, columns, memory_bytes, duplicate_rows}
      - columns: list of per-column dicts (see _profile_column)
    """
    return {
        "overview": {
            "rows": len(df),
            "columns": len(df.columns),
            "memory_bytes": int(df.memory_usage(deep=True).sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        },
        "columns": [_profile_column(df, col) for col in df.columns],
    }


def _profile_column(df: pd.DataFrame, col: str) -> dict[str, Any]:
    """Return a profile dict for one column."""
    series = df[col]
    missing = int(series.isna().sum())
    total = len(series)
    result: dict[str, Any] = {
        "name": col,
        "dtype": str(series.dtype),
        "missing_count": missing,
        "missing_pct": round(missing / total * 100, 2) if total else 0.0,
        "unique_count": int(series.nunique()),
    }
    if pd.api.types.is_numeric_dtype(series):
        desc = series.describe()
        result.update({
            "mean": round(float(desc["mean"]), 4) if "mean" in desc else None,
            "median": round(float(series.median()), 4),
            "min": float(desc["min"]) if "min" in desc else None,
            "max": float(desc["max"]) if "max" in desc else None,
            "std": round(float(desc["std"]), 4) if "std" in desc else None,
        })
    else:
        top5 = series.value_counts().head(5)
        result["top_values"] = [
            {"value": str(v), "count": int(c)} for v, c in top5.items()
        ]
    return result
