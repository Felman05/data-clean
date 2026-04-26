"""Insight generation — returns plain-English bullets and structured data."""
from typing import Any
import pandas as pd


def generate_insights(df: pd.DataFrame, columns: list[str], top_n: int = 5) -> list[dict[str, Any]]:
    """
    Generate a list of insight dicts for selected columns.

    Each dict has: {type, column, description, value_numeric}
    type values: 'summary_stat', 'top_value', 'correlation'
    """
    insights: list[dict] = []

    for col in columns:
        series = df[col].dropna()
        if series.empty:
            continue
        if pd.api.types.is_numeric_dtype(series):
            insights += _numeric_insights(series, col)
        else:
            insights += _categorical_insights(series, col, top_n)

    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(num_cols) >= 2:
        insights += _correlation_insights(df[num_cols])

    return insights


def _numeric_insights(series: pd.Series, col: str) -> list[dict]:
    mn, mx, avg, med = series.min(), series.max(), series.mean(), series.median()
    return [
        {
            "type": "summary_stat",
            "column": col,
            "description": (
                f"{col} ranges from {mn:,.2f} to {mx:,.2f} "
                f"with an average of {avg:,.2f} and median {med:,.2f}."
            ),
            "value_numeric": float(avg),
        }
    ]


def _categorical_insights(series: pd.Series, col: str, top_n: int) -> list[dict]:
    vc = series.value_counts()
    results = []
    for i, (val, count) in enumerate(vc.head(top_n).items()):
        pct = round(int(count) / len(series) * 100, 1)
        if i == 0:
            desc = f"'{val}' is the most common {col}, appearing in {pct}% of rows ({int(count):,} times)."
        else:
            desc = f"'{val}' appears {int(count):,} times ({pct}% of {col} values)."
        results.append({
            "type": "top_value",
            "column": col,
            "description": desc,
            "value_numeric": float(pct),
        })
    return results


def _correlation_insights(num_df: pd.DataFrame) -> list[dict]:
    """Find pairs with |correlation| >= 0.5 and emit a plain-English bullet."""
    corr = num_df.corr()
    results = []
    cols = corr.columns.tolist()
    for i, c1 in enumerate(cols):
        for c2 in cols[i + 1:]:
            val = corr.loc[c1, c2]
            if abs(val) >= 0.5:
                direction = "positively" if val > 0 else "negatively"
                strength = "strongly" if abs(val) >= 0.75 else "moderately"
                results.append({
                    "type": "correlation",
                    "column": f"{c1} × {c2}",
                    "description": f"{c1} and {c2} are {strength} {direction} correlated (r = {val:.2f}).",
                    "value_numeric": round(float(val), 4),
                })
    return results


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return the correlation matrix for all numeric columns."""
    return df.select_dtypes(include="number").corr()
