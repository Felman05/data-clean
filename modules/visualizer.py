"""Plotly chart builders for the Dashboard section."""
from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str | None = None,
    title: str = "",
    color_col: str | None = None,
    aggregation: str = "none",
) -> go.Figure:
    """
    Build a Plotly figure.

    chart_type: 'bar', 'line', 'pie', 'scatter', 'histogram'
    aggregation: 'none', 'sum', 'mean', 'count' — applied to y_col grouped by x_col before plotting.
    Returns a Plotly Figure with height=400.
    """
    plot_df = df.copy()

    if aggregation != "none" and y_col:
        if aggregation == "count":
            plot_df = plot_df.groupby(x_col).size().reset_index(name=y_col)
        elif aggregation == "sum":
            plot_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
        elif aggregation == "mean":
            plot_df = plot_df.groupby(x_col)[y_col].mean().reset_index()

    kwargs: dict[str, Any] = {"title": title or f"{chart_type.title()} of {x_col}"}

    if chart_type == "bar":
        fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col, **kwargs)
    elif chart_type == "line":
        fig = px.line(plot_df, x=x_col, y=y_col, color=color_col, **kwargs)
    elif chart_type == "pie":
        fig = px.pie(plot_df, names=x_col, values=y_col, **kwargs)
    elif chart_type == "scatter":
        fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col, **kwargs)
    elif chart_type == "histogram":
        fig = px.histogram(plot_df, x=x_col, color=color_col, **kwargs)
    else:
        raise ValueError(f"Unknown chart_type: {chart_type!r}")

    fig.update_layout(height=400)
    return fig
