# Design Spec: Dashboard Redesign + Download Button
**Date:** 2026-05-15  
**Project:** Refine Data Studio (FEDM BAT403 Semestral Project)

---

## 1. Motivation

The current Dashboard is a manual chart builder — the user must configure every chart from scratch. For a graded demo where the professor evaluates visualization capability, an auto-generated overview is more convincing and immediately informative. Additionally, the system has no way to export the cleaned dataset, which is the primary output of a data cleaning tool.

## 2. Scope

Two changes, both confined to `app.py`:

1. **Download button** — added to `_render_compare()` and top of `_render_dashboard()`
2. **Dashboard redesign** — `_render_dashboard()` replaced with tabbed layout

No changes to any `modules/` files, database schema, or other sections.

---

## 3. Change 1 — Download Cleaned CSV

### Location
- Primary: **Compare section** (`_render_compare()`), below the side-by-side tables
- Secondary: **Dashboard section** (`_render_dashboard()`), above the KPI cards

### Behavior
- Uses `st.download_button()` with `cleaned_df.to_csv(index=False).encode("utf-8")`
- Filename: `cleaned_<original_filename>` (e.g. `cleaned_employees.csv`)
- Falls back to `cleaned_data.csv` if original filename is not in session state
- Only rendered when `cleaned_df` is not None

---

## 4. Change 2 — Dashboard Redesign

### Layout
```
┌─────────────────────────────────────────────────────┐
│  KPI Cards Row (always visible, 5 cards)            │
├──────────────────────┬──────────────────────────────┤
│  Tab: Overview       │  Tab: Custom Charts           │
│  (auto-generated)    │  (existing builder, unchanged)│
└──────────────────────┴──────────────────────────────┘
```

### 4.1 KPI Cards

Five metric cards rendered using `st.metric()` in a 5-column layout:

| Card | Value | Delta shown |
|------|-------|-------------|
| Rows | `len(cleaned_df)` | `len(cleaned_df) - len(original_df)` (negative = rows removed) |
| Missing Filled | sum of `rows_affected` in log where `action == "fill_missing"` | — |
| Duplicates Removed | sum of `rows_affected` in log where `action == "drop_duplicates"` | — |
| Actions Applied | `len(cleaning_log)` | — |
| Data Quality | `round((cleaned_df.notna().sum().sum() / cleaned_df.size) * 100, 1)` as `"X%"` | — |

If `cleaning_log` is empty (dataset not yet cleaned), the middle three cards show `0`.

### 4.2 Overview Tab — Auto-Generated Charts

Charts are generated automatically based on column types detected in `cleaned_df`. Generated using the existing `build_chart()` from `modules/visualizer.py`.

**Chart generation rules (in order):**

1. **Histogram** — first numeric column found → `build_chart(df, "histogram", col)`
2. **Bar chart** — first categorical/object column found, top 10 values by frequency → `build_chart(df, "bar", col, y_col, aggregation="count")`
3. **Line chart** — if a datetime column AND a numeric column both exist → `build_chart(df, "line", date_col, numeric_col)`
4. **Scatter** — if 2+ numeric columns exist → `build_chart(df, "scatter", num_col_1, num_col_2)`
5. **Pie** — first categorical column with ≤ 8 unique values → `build_chart(df, "pie", col, y_col, aggregation="count")`

Charts are laid out 2-per-row using `st.columns(2)`. If fewer than 2 charts can be generated (e.g. dataset has only one column), a single-column layout is used. If no charts can be generated, a friendly message is shown: "No suitable columns found for auto-charts. Use the Custom Charts tab to build manually."

### 4.3 Custom Charts Tab

Identical to the current `_render_dashboard()` implementation — the form and chart list are moved into this tab unchanged. Session state key `"charts"` is preserved.

---

## 5. Session State

No new session state keys are needed. Existing keys used:
- `cleaned_df` — source data for all dashboard rendering
- `original_df` — used for Rows delta in KPI cards
- `cleaning_log` — used to compute Missing Filled and Duplicates Removed counts
- `uploaded_filename` — used to construct download filename
- `charts` — existing key, now scoped to Custom Charts tab

---

## 6. Limitations (for documentation / demo Q&A)

- Auto-charts pick the **first** matching column; there is no user control over which column is used in the Overview tab (that's what the Custom Charts tab is for)
- Download produces CSV only; Excel export is not supported
- KPI deltas reflect session memory only — if the page is refreshed without re-uploading, values reset to 0

---

## 7. Files Changed

| File | Change |
|------|--------|
| `app.py` | `_render_compare()`: add download button; `_render_dashboard()`: full replacement with tabbed layout + KPI cards |
| `.gitignore` | Add `.superpowers/` (already done) |
