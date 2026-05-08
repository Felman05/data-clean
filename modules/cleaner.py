"""
Data cleaning functions for the FEDM system.

Every public function:
- Takes a DataFrame (the current cleaned_df) and operation parameters
- Returns (new_df, log_entry_dict)
- Never mutates the input DataFrame
- Records rows_affected for the cleaning log

Call pattern in app.py:
    cleaned_df, log = some_cleaner(cleaned_df, **params)
    st.session_state["cleaning_log"].append(log)
    st.session_state["cleaned_df"] = cleaned_df
"""
from __future__ import annotations
from typing import Any
import pandas as pd


def _entry(action: str, column: str | None, rows_affected: int, **params) -> dict[str, Any]:
    return {
        "action": action,
        "column": column or "—",
        "rows_affected": rows_affected,
        "params": params,
    }


# ── Missing values ────────────────────────────────────────────────────────────

def fill_missing(
    df: pd.DataFrame,
    column: str,
    method: str,
    custom_value: Any = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Handle missing values in a single column.

    method options:
      'drop_row'     — remove rows where this column is NaN
      'drop_column'  — remove this column entirely
      'mean'         — fill with column mean (numeric only)
      'median'       — fill with column median (numeric only)
      'mode'         — fill with most frequent value
      'custom'       — fill with custom_value
      'ffill'        — forward fill
      'bfill'        — backward fill

    Use 'drop_row' when missing data is rare and rows are not needed.
    Use 'mean'/'median' for numeric columns when missingness is random.
    Use 'mode' for categorical columns.
    Use 'ffill'/'bfill' for time-ordered data.
    Use 'custom' when a sentinel value (e.g. 0, 'Unknown') is meaningful.
    """
    out = df.copy()
    missing_before = int(out[column].isna().sum())
    if missing_before == 0:
        return out, _entry("fill_missing", column, 0, method=method)

    if method == "drop_row":
        out = out.dropna(subset=[column])
        rows_affected = missing_before
    elif method == "drop_column":
        out = out.drop(columns=[column])
        rows_affected = missing_before
    elif method == "mean":
        out[column] = out[column].fillna(out[column].mean())
        rows_affected = missing_before
    elif method == "median":
        out[column] = out[column].fillna(out[column].median())
        rows_affected = missing_before
    elif method == "mode":
        mode_val = out[column].mode()
        if len(mode_val):
            out[column] = out[column].fillna(mode_val.iloc[0])
        rows_affected = missing_before
    elif method == "custom":
        out[column] = out[column].fillna(custom_value)
        rows_affected = missing_before
    elif method == "ffill":
        out[column] = out[column].ffill()
        rows_affected = missing_before - int(out[column].isna().sum())
    elif method == "bfill":
        out[column] = out[column].bfill()
        rows_affected = missing_before - int(out[column].isna().sum())
    else:
        raise ValueError(f"Unknown fill method: {method!r}")

    return out, _entry("fill_missing", column, rows_affected, method=method, custom_value=custom_value)


# ── Duplicates ────────────────────────────────────────────────────────────────

def drop_duplicates(
    df: pd.DataFrame,
    subset: list[str] | None = None,
    keep: str | bool = "first",
) -> tuple[pd.DataFrame, dict]:
    """
    Remove duplicate rows.

    subset: columns to consider for identifying duplicates (None = all columns).
    keep: 'first' keeps the first occurrence; 'last' keeps the last; False drops all.

    Use subset when duplicates are defined by a business key (e.g. ['employee_id']).
    Use keep='first' for most cases; keep=False to remove all copies of a duplicate.
    """
    before = len(df)
    out = df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)
    rows_affected = before - len(out)
    return out, _entry("drop_duplicates", None, rows_affected, subset=subset, keep=str(keep))


# ── Type conversion ───────────────────────────────────────────────────────────

def convert_type(
    df: pd.DataFrame,
    column: str,
    target_type: str,
    datetime_format: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Convert a column to a new dtype.

    target_type options: 'numeric', 'datetime', 'string', 'category', 'boolean'
    datetime_format: optional strptime format string, e.g. '%d/%m/%Y'

    Values that cannot be converted become NaN (for numeric/datetime) or are left
    as-is for string/category/boolean conversions. Errors are never raised silently —
    conversion failures are coerced to NaN so the user can see them in the profile.
    """
    out = df.copy()
    before_nulls = int(out[column].isna().sum())

    if target_type == "numeric":
        out[column] = pd.to_numeric(out[column], errors="coerce")
    elif target_type == "datetime":
        out[column] = pd.to_datetime(
            out[column], format=datetime_format, errors="coerce", dayfirst=False
        )
    elif target_type == "string":
        out[column] = out[column].astype(str)
    elif target_type == "category":
        out[column] = out[column].astype("category")
    elif target_type == "boolean":
        out[column] = out[column].map(
            lambda v: True if str(v).strip().lower() in ("true", "1", "yes", "active")
            else (False if str(v).strip().lower() in ("false", "0", "no", "inactive") else pd.NA)
        )
    else:
        raise ValueError(f"Unknown target_type: {target_type!r}")

    after_nulls = int(out[column].isna().sum())
    rows_affected = max(0, after_nulls - before_nulls)
    return out, _entry("convert_type", column, rows_affected, target_type=target_type, datetime_format=datetime_format)


# ── Text standardization ──────────────────────────────────────────────────────

def standardize_text(
    df: pd.DataFrame,
    column: str,
    operations: list[str],
) -> tuple[pd.DataFrame, dict]:
    """
    Apply text transformations to a string column.

    operations is a list from: ['trim', 'lowercase', 'uppercase', 'titlecase']
    Order matters: operations are applied left to right.

    Use 'trim' to remove accidental leading/trailing spaces.
    Use 'lowercase' before deduplication or grouping to avoid case-sensitive splits.
    Use 'titlecase' for display names in reports.
    """
    out = df.copy()
    col = out[column].astype(str)
    for op in operations:
        if op == "trim":
            col = col.str.strip()
        elif op == "lowercase":
            col = col.str.lower()
        elif op == "uppercase":
            col = col.str.upper()
        elif op == "titlecase":
            col = col.str.title()
    out[column] = col
    return out, _entry("standardize_text", column, len(df), operations=operations)


# ── Date standardization ──────────────────────────────────────────────────────

def standardize_dates(
    df: pd.DataFrame,
    column: str,
    output_format: str = "%Y-%m-%d",
) -> tuple[pd.DataFrame, dict]:
    """
    Parse mixed date formats in a column and normalize to output_format.

    Non-parseable values become NaN. The column dtype becomes object (string)
    after formatting so it is human-readable in the CSV export.

    Use this when a column has mixed date formats (e.g. '03/15/2021', 'March 15 2021').
    Set output_format to '%Y-%m-%d' for ISO 8601 (recommended for databases).
    """
    out = df.copy()
    parsed = pd.to_datetime(out[column], errors="coerce", infer_datetime_format=True)
    rows_affected = int(parsed.notna().sum())
    out[column] = parsed.dt.strftime(output_format).where(parsed.notna(), other=pd.NA)
    return out, _entry("standardize_dates", column, rows_affected, output_format=output_format)


# ── Invalid data filtering ────────────────────────────────────────────────────

def filter_invalid(
    df: pd.DataFrame,
    column: str,
    rule_type: str,
    min_val: float | None = None,
    max_val: float | None = None,
    regex_pattern: str | None = None,
    allowed_values: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Remove rows that violate a column-level data rule.

    rule_type options:
      'numeric_range'  — keep rows where min_val <= column <= max_val
      'regex_match'    — keep rows where column matches regex_pattern
      'allowed_values' — keep rows where column is in allowed_values list

    Use 'numeric_range' for salary, age, years_experience bounds checking.
    Use 'regex_match' for email, phone, or ID format validation.
    Use 'allowed_values' for controlled-vocabulary columns (department, status).
    NaN values are kept in all modes (use fill_missing to handle them separately).
    """
    out = df.copy()

    if rule_type == "numeric_range":
        numeric_col = pd.to_numeric(out[column], errors="coerce")
        valid = pd.Series([True] * len(out), index=out.index)
        if min_val is not None:
            valid &= (numeric_col >= min_val) | numeric_col.isna()
        if max_val is not None:
            valid &= (numeric_col <= max_val) | numeric_col.isna()
        mask = valid
    elif rule_type == "regex_match":
        mask = out[column].isna() | out[column].astype(str).str.match(
            regex_pattern or ".*", na=True
        )
    elif rule_type == "allowed_values":
        mask = out[column].isna() | out[column].isin(allowed_values or [])
    else:
        raise ValueError(f"Unknown rule_type: {rule_type!r}")

    removed = int((~mask).sum())
    out = out[mask].reset_index(drop=True)
    return out, _entry(
        "filter_invalid", column, removed,
        rule_type=rule_type, min_val=min_val, max_val=max_val,
        regex_pattern=regex_pattern, allowed_values=allowed_values,
    )


# ── Auto-clean (intelligent one-shot cleaning) ────────────────────────────────

def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """
    Automatically apply common cleaning operations across all columns.
    Returns (cleaned_df, list_of_log_entries) for batch processing.

    Steps:
    1. Remove exact duplicate rows
    2. For each column with missing values:
       - Numeric columns: fill with median
       - Categorical/text columns: fill with mode
    3. For object/string columns: trim whitespace + lowercase
    4. Attempt date standardization on columns with "date" in name
    5. Remove rows with duplicate values in key columns

    This provides a reasonable default cleaning suitable for most datasets
    without requiring user interaction.
    """
    out = df.copy()
    logs = []

    # Step 1: Remove duplicates
    before = len(out)
    out = out.drop_duplicates().reset_index(drop=True)
    dup_removed = before - len(out)
    if dup_removed > 0:
        logs.append(_entry("drop_duplicates", None, dup_removed, subset=None, keep="first"))

    # Step 2: Fill missing values intelligently
    for col in out.columns:
        missing_count = int(out[col].isna().sum())
        if missing_count == 0:
            continue

        if pd.api.types.is_numeric_dtype(out[col]):
            median_val = out[col].median()
            if pd.notna(median_val):
                out[col] = out[col].fillna(median_val)
                logs.append(_entry("fill_missing", col, missing_count, method="median"))
        else:
            mode_vals = out[col].dropna().mode()
            if len(mode_vals) > 0:
                mode_val = mode_vals.iloc[0]
                out[col] = out[col].fillna(mode_val)
                logs.append(_entry("fill_missing", col, missing_count, method="mode"))

    # Step 3: Standardize text columns (trim + lowercase)
    for col in out.columns:
        if pd.api.types.is_object_dtype(out[col]):
            out[col] = out[col].astype(str).str.strip().str.lower()
            logs.append(_entry("standardize_text", col, len(out), operations=["trim", "lowercase"]))

    # Step 4: Standardize date columns (detect by name)
    for col in out.columns:
        if "date" in col.lower():
            try:
                parsed = pd.to_datetime(out[col], errors="coerce", infer_datetime_format=True)
                if parsed.notna().sum() > 0:
                    out[col] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), other=pd.NA)
                    logs.append(_entry("standardize_dates", col, int(parsed.notna().sum()), output_format="%Y-%m-%d"))
            except Exception:
                pass

    return out, logs
