# Dashboard Redesign + Download Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Download Cleaned CSV button to the Compare section and redesign the Dashboard section with always-visible KPI cards plus a tabbed layout (Overview with auto-generated charts, Custom Charts with the existing builder).

**Architecture:** All changes are confined to `app.py`. `_render_compare()` gets a download button appended. `_render_dashboard()` is replaced with a new version that renders KPI metrics, then delegates to two new helper functions — `_render_auto_charts()` for the Overview tab and `_render_custom_chart_builder()` for the Custom Charts tab (which contains the existing builder code verbatim).

**Tech Stack:** Streamlit (`st.metric`, `st.tabs`, `st.download_button`), pandas, Plotly via the existing `build_chart()` from `modules/visualizer.py`.

---

## File Map

| File | Change |
|------|--------|
| `app.py:705–758` | `_render_compare()` — append download button after styled diff table |
| `app.py:823–885` | `_render_dashboard()` — full replacement with KPI + tabs |
| `app.py` (new, before `_render_dashboard`) | Add `_render_auto_charts(df)` helper |
| `app.py` (new, before `_render_dashboard`) | Add `_render_custom_chart_builder(df)` helper |

---

## Task 1: Download Button in Compare Section

**Files:**
- Modify: `app.py:757-758` (append after the styled dataframe `st.dataframe` call)

- [ ] **Step 1: Add the download button block inside `_render_compare()`**

  Open `app.py`. Find the end of `_render_compare()` — it ends at the `st.dataframe(styled, ...)` call around line 758. Append this block immediately after it (still inside the function, after the `if shared_cols` block):

  ```python
      # ── Download ──────────────────────────────────────────────────────────
      st.divider()
      fname = st.session_state.get("uploaded_filename") or "data.csv"
      download_name = f"cleaned_{Path(fname).stem}.csv"
      st.download_button(
          label="⬇️ Download Cleaned CSV",
          data=clean.to_csv(index=False).encode("utf-8"),
          file_name=download_name,
          mime="text/csv",
      )
  ```

  Note: `Path` is already imported at the top of `app.py` (`from pathlib import Path`).

- [ ] **Step 2: Verify visually**

  Run `streamlit run app.py`, upload `sample_data/messy_employees.csv`, navigate to **Compare**. Confirm the "⬇️ Download Cleaned CSV" button appears below the diff table. Click it — a file named `cleaned_messy_employees.csv` should download.

- [ ] **Step 3: Commit**

  ```bash
  git add app.py
  git commit -m "feat: add Download Cleaned CSV button to Compare section"
  ```

---

## Task 2: Add Helper Functions Before `_render_dashboard`

**Files:**
- Modify: `app.py` — insert two new functions immediately before `def _render_dashboard()`

- [ ] **Step 1: Insert `_render_auto_charts` before `_render_dashboard`**

  Find the line `def _render_dashboard() -> None:` (around line 823). Insert the following function **immediately before** it:

  ```python
  def _render_auto_charts(df: pd.DataFrame) -> None:
      num_cols = df.select_dtypes(include="number").columns.tolist()
      cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
      date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

      charts = []

      if num_cols:
          charts.append(build_chart(df, "histogram", num_cols[0],
                                    title=f"Distribution of {num_cols[0]}"))

      if cat_cols:
          col = cat_cols[0]
          top10 = df[col].value_counts().head(10).reset_index()
          top10.columns = [col, "count"]
          charts.append(build_chart(top10, "bar", col, "count",
                                    title=f"Top 10 — {col}"))

      if date_cols and num_cols:
          sorted_df = df.sort_values(date_cols[0])
          charts.append(build_chart(sorted_df, "line", date_cols[0], num_cols[0],
                                    title=f"{num_cols[0]} over time"))

      if len(num_cols) >= 2:
          charts.append(build_chart(df, "scatter", num_cols[0], num_cols[1],
                                    title=f"{num_cols[0]} vs {num_cols[1]}"))

      pie_col = next((c for c in cat_cols if df[c].nunique() <= 8), None)
      if pie_col:
          pie_data = df[pie_col].value_counts().reset_index()
          pie_data.columns = [pie_col, "count"]
          charts.append(build_chart(pie_data, "pie", pie_col, "count",
                                    title=f"{pie_col} breakdown"))

      if not charts:
          st.info("No suitable columns found for auto-charts. Use the Custom Charts tab to build manually.")
          return

      for i in range(0, len(charts), 2):
          left, right = st.columns(2)
          left.plotly_chart(charts[i], use_container_width=True)
          if i + 1 < len(charts):
              right.plotly_chart(charts[i + 1], use_container_width=True)
  ```

- [ ] **Step 2: Insert `_render_custom_chart_builder` immediately after `_render_auto_charts`**

  Insert this function after `_render_auto_charts` and before `_render_dashboard`:

  ```python
  def _render_custom_chart_builder(df: pd.DataFrame) -> None:
      all_cols = df.columns.tolist()

      st.subheader("Add Chart")
      with st.form("add_chart_form"):
          fc1, fc2, fc3 = st.columns(3)
          chart_type = fc1.selectbox("Chart type", ["bar", "line", "pie", "scatter", "histogram"])
          x_col = fc2.selectbox("X column", all_cols)
          y_col = fc3.selectbox("Y column (optional for histogram/pie)",
                                ["(none)"] + df.select_dtypes(include="number").columns.tolist())
          fc4, fc5, fc6 = st.columns(3)
          agg = fc4.selectbox("Aggregation", ["none", "sum", "mean", "count"])
          color_col = fc5.selectbox("Color by (optional)", ["(none)"] + all_cols)
          title = fc6.text_input("Chart title (optional)")
          submitted = st.form_submit_button("Add Chart")

      if submitted:
          y = y_col if y_col != "(none)" else None
          color = color_col if color_col != "(none)" else None
          try:
              fig = build_chart(df, chart_type, x_col, y, title, color, agg)
              chart_cfg = {
                  "chart_type": chart_type, "x_col": x_col, "y_col": y,
                  "color_col": color, "agg": agg, "title": title,
              }
              st.session_state["charts"].append({"fig": fig, "cfg": chart_cfg})
          except Exception as exc:
              st.error(f"Chart error: {exc}")

      for i, chart_item in enumerate(st.session_state["charts"]):
          with st.container():
              st.plotly_chart(chart_item["fig"], use_container_width=True)
              col_save, col_remove = st.columns([1, 1])
              with col_save:
                  if st.button("💾 Save to DB", key=f"save_chart_{i}"):
                      did = st.session_state.get("dataset_id")
                      if not did:
                          st.warning("Upload must be persisted to DB first.")
                      else:
                          try:
                              cfg = chart_item["cfg"]
                              session = get_session()
                              insert_chart(
                                  session, did,
                                  chart_type=cfg["chart_type"],
                                  x_column=cfg["x_col"],
                                  y_column=cfg.get("y_col"),
                                  config={k: v for k, v in cfg.items()},
                              )
                              session.close()
                              st.success("Chart saved to database.")
                          except Exception as exc:
                              st.error(f"DB error: {exc}")
              with col_remove:
                  if st.button("🗑 Remove", key=f"remove_chart_{i}"):
                      st.session_state["charts"].pop(i)
                      st.rerun()
              st.divider()
  ```

- [ ] **Step 3: No commit yet** — `_render_dashboard` still calls neither helper; commit after Task 3.

---

## Task 3: Replace `_render_dashboard` Body

**Files:**
- Modify: `app.py:823–885` — replace the entire body of `_render_dashboard()`

- [ ] **Step 1: Replace `_render_dashboard` with the new version**

  Delete everything from `def _render_dashboard() -> None:` through its closing line (the final `st.divider()` inside the chart loop, around line 885). Replace with:

  ```python
  def _render_dashboard() -> None:
      _section_header("Dashboard", "Dataset overview and interactive charts")
      df = st.session_state["cleaned_df"]
      orig = st.session_state["original_df"]
      if df is None:
          st.info("Upload a dataset first.")
          return

      fname = st.session_state.get("uploaded_filename") or "data.csv"
      download_name = f"cleaned_{Path(fname).stem}.csv"
      st.download_button(
          label="⬇️ Download Cleaned CSV",
          data=df.to_csv(index=False).encode("utf-8"),
          file_name=download_name,
          mime="text/csv",
      )

      st.divider()

      log = st.session_state["cleaning_log"]
      orig_rows = len(orig) if orig is not None else len(df)
      row_delta = len(df) - orig_rows
      imputed = sum(e["rows_affected"] for e in log if e["action"] == "fill_missing")
      dupes_dropped = sum(e["rows_affected"] for e in log if e["action"] == "drop_duplicates")
      quality = round((df.notna().sum().sum() / df.size) * 100, 1) if df.size > 0 else 0.0

      k1, k2, k3, k4, k5 = st.columns(5)
      k1.metric("Rows", len(df), delta=row_delta if row_delta != 0 else None, delta_color="inverse")
      k2.metric("Missing Filled", imputed)
      k3.metric("Duplicates Removed", dupes_dropped)
      k4.metric("Actions Applied", len(log))
      k5.metric("Data Quality", f"{quality}%")

      st.divider()

      tab_overview, tab_custom = st.tabs(["Overview", "Custom Charts"])
      with tab_overview:
          _render_auto_charts(df)
      with tab_custom:
          _render_custom_chart_builder(df)
  ```

- [ ] **Step 2: Verify visually**

  With `streamlit run app.py` running, upload `sample_data/messy_employees.csv`, run **Auto-Clean** in the Clean section, then navigate to **Dashboard**. Confirm:
  - Download button appears at top
  - 5 KPI cards show correct values (rows, filled, dupes, actions, quality %)
  - "Overview" tab shows auto-generated charts (histogram, bar, scatter at minimum for the employees dataset)
  - "Custom Charts" tab shows the existing form and works as before

- [ ] **Step 3: Commit**

  ```bash
  git add app.py
  git commit -m "feat: redesign Dashboard with KPI cards, auto-charts, and tabbed layout"
  ```

---

## Self-Review

**Spec coverage:**
- ✅ Download button in Compare section (Task 1)
- ✅ Download button in Dashboard section (Task 3, top of function)
- ✅ KPI cards: Rows (with delta), Missing Filled, Duplicates Removed, Actions Applied, Data Quality (Task 3)
- ✅ Overview tab with auto-charts: histogram, bar, line, scatter, pie based on column types (Task 2 `_render_auto_charts`)
- ✅ Custom Charts tab: existing builder preserved verbatim (Task 2 `_render_custom_chart_builder`)
- ✅ Filename uses `uploaded_filename` session key with fallback

**Placeholder scan:** None found.

**Type consistency:**
- `_render_auto_charts(df: pd.DataFrame)` — called in Task 3 as `_render_auto_charts(df)` ✅
- `_render_custom_chart_builder(df: pd.DataFrame)` — called in Task 3 as `_render_custom_chart_builder(df)` ✅
- `build_chart()` signatures match `modules/visualizer.py` ✅
- `st.session_state["charts"]` — already initialized in `_DEFAULTS` ✅
