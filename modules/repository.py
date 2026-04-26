"""CRUD functions for every table. No raw SQL should appear outside this module."""
import json
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text


# ── datasets ─────────────────────────────────────────────────────────────────

def insert_dataset(
    session: Session,
    name: str,
    original_filename: str,
    file_type: str,
    row_count: int,
    column_count: int,
) -> int:
    """Insert a datasets row and return the new id."""
    result = session.execute(
        text(
            "INSERT INTO datasets (name, original_filename, file_type, row_count, column_count, uploaded_at) "
            "VALUES (:name, :original_filename, :file_type, :row_count, :column_count, :uploaded_at)"
        ),
        {
            "name": name,
            "original_filename": original_filename,
            "file_type": file_type,
            "row_count": row_count,
            "column_count": column_count,
            "uploaded_at": datetime.now(),
        },
    )
    session.commit()
    return result.lastrowid


def get_dataset(session: Session, dataset_id: int) -> dict | None:
    row = session.execute(
        text("SELECT * FROM datasets WHERE id = :id"), {"id": dataset_id}
    ).mappings().fetchone()
    return dict(row) if row else None


def list_datasets(session: Session) -> list[dict]:
    rows = session.execute(
        text("SELECT * FROM datasets ORDER BY uploaded_at DESC")
    ).mappings().fetchall()
    return [dict(r) for r in rows]


# ── dataset_columns ───────────────────────────────────────────────────────────

def insert_dataset_columns(
    session: Session,
    dataset_id: int,
    columns: list[dict],
) -> None:
    """Bulk-insert dataset_columns rows. Each dict: {column_name, detected_dtype, missing_count, unique_count, column_order}"""
    for col in columns:
        session.execute(
            text(
                "INSERT INTO dataset_columns "
                "(dataset_id, column_name, detected_dtype, missing_count, unique_count, column_order) "
                "VALUES (:dataset_id, :column_name, :detected_dtype, :missing_count, :unique_count, :column_order)"
            ),
            {**col, "dataset_id": dataset_id},
        )
    session.commit()


# ── cleaning_actions ──────────────────────────────────────────────────────────

def insert_cleaning_action(
    session: Session,
    dataset_id: int,
    action_type: str,
    target_column: str | None,
    parameters: dict,
    rows_affected: int,
) -> int:
    """Insert a cleaning_actions row with sequence_order = current_max + 1. Returns new id."""
    row = session.execute(
        text(
            "SELECT COALESCE(MAX(sequence_order), 0) + 1 AS next_seq "
            "FROM cleaning_actions WHERE dataset_id = :did"
        ),
        {"did": dataset_id},
    ).fetchone()
    next_seq = row[0]
    result = session.execute(
        text(
            "INSERT INTO cleaning_actions "
            "(dataset_id, action_type, target_column, parameters, rows_affected, sequence_order, applied_at) "
            "VALUES (:dataset_id, :action_type, :target_column, :parameters, :rows_affected, :sequence_order, :applied_at)"
        ),
        {
            "dataset_id": dataset_id,
            "action_type": action_type,
            "target_column": target_column,
            "parameters": json.dumps(parameters),
            "rows_affected": rows_affected,
            "sequence_order": next_seq,
            "applied_at": datetime.now(),
        },
    )
    session.commit()
    return result.lastrowid


def delete_last_cleaning_action(session: Session, dataset_id: int) -> bool:
    """Delete the highest-sequence_order cleaning_action row. Returns True if one was deleted."""
    row = session.execute(
        text(
            "SELECT id FROM cleaning_actions WHERE dataset_id = :did "
            "ORDER BY sequence_order DESC LIMIT 1"
        ),
        {"did": dataset_id},
    ).fetchone()
    if not row:
        return False
    session.execute(text("DELETE FROM cleaning_actions WHERE id = :id"), {"id": row[0]})
    session.commit()
    return True


def delete_all_cleaning_actions(session: Session, dataset_id: int) -> None:
    """Delete all cleaning_actions for a dataset (reset to original)."""
    session.execute(
        text("DELETE FROM cleaning_actions WHERE dataset_id = :did"), {"did": dataset_id}
    )
    session.commit()


def list_cleaning_actions(session: Session, dataset_id: int) -> list[dict]:
    rows = session.execute(
        text(
            "SELECT * FROM cleaning_actions WHERE dataset_id = :did "
            "ORDER BY sequence_order ASC"
        ),
        {"did": dataset_id},
    ).mappings().fetchall()
    return [dict(r) for r in rows]


# ── insights ──────────────────────────────────────────────────────────────────

def insert_insight(
    session: Session,
    dataset_id: int,
    insight_type: str,
    target_column: str | None,
    description: str,
    value_numeric: float | None,
) -> int:
    result = session.execute(
        text(
            "INSERT INTO insights "
            "(dataset_id, insight_type, target_column, description, value_numeric, generated_at) "
            "VALUES (:dataset_id, :insight_type, :target_column, :description, :value_numeric, :generated_at)"
        ),
        {
            "dataset_id": dataset_id,
            "insight_type": insight_type,
            "target_column": target_column,
            "description": description,
            "value_numeric": value_numeric,
            "generated_at": datetime.now(),
        },
    )
    session.commit()
    return result.lastrowid


def list_insights(session: Session, dataset_id: int) -> list[dict]:
    rows = session.execute(
        text("SELECT * FROM insights WHERE dataset_id = :did ORDER BY generated_at DESC"),
        {"did": dataset_id},
    ).mappings().fetchall()
    return [dict(r) for r in rows]


# ── dashboard_charts ──────────────────────────────────────────────────────────

def insert_chart(
    session: Session,
    dataset_id: int,
    chart_type: str,
    x_column: str,
    y_column: str | None,
    config: dict,
) -> int:
    result = session.execute(
        text(
            "INSERT INTO dashboard_charts "
            "(dataset_id, chart_type, x_column, y_column, config, created_at) "
            "VALUES (:dataset_id, :chart_type, :x_column, :y_column, :config, :created_at)"
        ),
        {
            "dataset_id": dataset_id,
            "chart_type": chart_type,
            "x_column": x_column,
            "y_column": y_column,
            "config": json.dumps(config),
            "created_at": datetime.now(),
        },
    )
    session.commit()
    return result.lastrowid


def list_charts(session: Session, dataset_id: int) -> list[dict]:
    rows = session.execute(
        text("SELECT * FROM dashboard_charts WHERE dataset_id = :did ORDER BY created_at DESC"),
        {"did": dataset_id},
    ).mappings().fetchall()
    return [dict(r) for r in rows]
