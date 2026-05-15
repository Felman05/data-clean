"""Main Streamlit application — Refine Data Studio."""
import streamlit as st
import pandas as pd
from pathlib import Path

from modules.db import test_connection, get_session
from modules.profiler import profile_dataframe
import plotly.express as px
from modules.insights import generate_insights, correlation_matrix
from modules.visualizer import build_chart
from modules.repository import (
    insert_dataset, insert_dataset_columns,
    insert_cleaning_action, delete_last_cleaning_action, delete_all_cleaning_actions,
    insert_insight, insert_chart,
)
from modules.cleaner import (
    fill_missing, drop_duplicates, convert_type,
    standardize_text, standardize_dates, filter_invalid, auto_clean,
)

st.set_page_config(page_title="Refine — Data Studio", layout="wide", page_icon="◈")

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=Syne:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ──────────────────────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background: #F1F4FB; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; border-bottom: none; height: 0; }
.stDeployButton { display: none !important; }

/* ── Sidebar ───────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0C1524 !important;
    border-right: 1px solid #17253A;
    min-width: 220px !important;
    max-width: 220px !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0; }
[data-testid="stSidebarContent"] { padding: 0; }

/* sidebar nav buttons */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    color: #64748B !important;
    text-align: left !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    border-radius: 8px !important;
    padding: 0.55rem 1rem !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.12) !important;
    color: #A5B4FC !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:focus {
    box-shadow: none !important;
    outline: none !important;
}

/* ── Main content area ─────────────────────────────────────────────────────── */
.main .block-container {
    padding: 2.5rem 3rem 3rem 3rem;
    max-width: 1440px;
}

/* ── Typography ────────────────────────────────────────────────────────────── */
h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
    color: #0F172A !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 0.25rem !important;
    line-height: 1.2 !important;
}
h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    color: #1E293B !important;
    letter-spacing: -0.02em !important;
}
h2 { font-size: 1.1rem !important; }
h3 { font-size: 1rem !important; }
p, li, label, .stMarkdown { color: #334155; font-size: 0.9rem; }

/* ── Metric cards ──────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: white;
    padding: 1.1rem 1.4rem 1.1rem 1.2rem;
    border-radius: 12px;
    border: 1px solid #E8EDF5;
    border-left: 3px solid #6366F1;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05), 0 4px 20px rgba(15,23,42,0.03);
}
[data-testid="stMetricLabel"] > div {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: #94A3B8 !important;
}
[data-testid="stMetricValue"] > div {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -0.02em !important;
}

/* ── Buttons (main) ────────────────────────────────────────────────────────── */
.main .stButton > button {
    background: #6366F1 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 0.45rem 1.2rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(99,102,241,0.3) !important;
}
.main .stButton > button:hover {
    background: #4F46E5 !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.4) !important;
    transform: translateY(-1px) !important;
}
.main .stButton > button:active { transform: translateY(0) !important; }

/* ── Tabs ──────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 2px solid #E2E8F0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #64748B;
    padding: 0.65rem 1.1rem;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #6366F1 !important;
    border-bottom: 2px solid #6366F1 !important;
    background: transparent !important;
}

/* ── Inputs ────────────────────────────────────────────────────────────────── */
.stSelectbox label, .stMultiselect label, .stTextInput label,
.stTextArea label, .stSlider label, .stRadio label, .stNumberInput label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-baseweb="select"] > div,
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background: white !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.875rem !important;
    color: #1E293B !important;
}

/* ── File uploader ─────────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: white;
    border: 2px dashed #CBD5E1;
    border-radius: 12px;
    transition: border-color 0.2s ease;
}
[data-testid="stFileUploader"]:hover { border-color: #6366F1; }
[data-testid="stFileUploadDropzone"] {
    background: white !important;
    border-radius: 12px;
}

/* ── Expanders ─────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: white;
    border: 1px solid #E8EDF5 !important;
    border-radius: 10px !important;
    margin-bottom: 0.4rem;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}
.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    color: #1E293B !important;
    font-size: 0.875rem !important;
}

/* ── DataFrames ────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #E8EDF5;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05);
}

/* ── Alerts ────────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.875rem !important;
}

/* ── Form ──────────────────────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: white;
    border: 1px solid #E8EDF5;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}

/* ── Divider ───────────────────────────────────────────────────────────────── */
hr { border-color: #E8EDF5 !important; margin: 1.5rem 0 !important; }

/* ── Code ──────────────────────────────────────────────────────────────────── */
code, pre { font-family: 'JetBrains Mono', monospace !important; font-size: 0.82rem !important; }

/* ── Info/success chips in sidebar ────────────────────────────────────────── */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    font-size: 0.75rem !important;
    padding: 0.4rem 0.7rem !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "original_df": None,
    "cleaned_df": None,
    "cleaning_log": [],
    "dataset_id": None,
    "uploaded_filename": None,
    "section": "Upload",
    "charts": [],
}
for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand logo
    st.markdown("""
    <div style="padding:1.8rem 1.2rem 1.4rem 1.2rem; border-bottom:1px solid #17253A; margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:3px;">
            <div style="width:30px;height:30px;background:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;color:white;font-weight:900;flex-shrink:0;">◈</div>
            <span style="font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:800;color:#F1F5F9;letter-spacing:-0.03em;">Refine</span>
        </div>
        <span style="font-size:0.68rem;color:#334155;letter-spacing:0.08em;text-transform:uppercase;font-weight:600;padding-left:40px;">Data Studio</span>
    </div>
    """, unsafe_allow_html=True)

    # DB status indicator
    ok, db_msg = test_connection()
    if ok:
        st.markdown("""<div style="margin:0 1rem 1rem 1rem;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:7px;padding:6px 10px;font-size:0.72rem;font-weight:600;color:#10B981;letter-spacing:0.02em;">● DB Connected</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="margin:0 1rem 1rem 1rem;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);border-radius:7px;padding:6px 10px;font-size:0.72rem;font-weight:600;color:#F59E0B;letter-spacing:0.02em;">● DB Offline</div>""", unsafe_allow_html=True)

    # Navigation
    st.markdown('<div style="padding:0 0.6rem;">', unsafe_allow_html=True)
    nav_items = [
        ("Upload",    "↑", "Upload"),
        ("Profile",   "◎", "Profile"),
        ("Clean",     "✦", "Clean"),
        ("Compare",   "⊟", "Compare"),
        ("Insights",  "◈", "Insights"),
        ("Dashboard", "▦", "Dashboard"),
    ]
    current = st.session_state["section"]
    for sec, icon, label in nav_items:
        is_active = sec == current
        if is_active:
            st.markdown(f"""<div style="background:rgba(99,102,241,0.15);border-radius:8px;padding:0.55rem 1rem;margin-bottom:2px;font-family:'DM Sans',sans-serif;font-size:0.88rem;font-weight:600;color:#A5B4FC;letter-spacing:0.01em;">{icon}&nbsp;&nbsp;{label}</div>""", unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", use_container_width=True, key=f"nav_{sec}"):
            st.session_state["section"] = sec
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Upload helpers ────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_PATH = Path("sample_data/messy_employees.csv")


def _load_file(uploaded_file) -> pd.DataFrame:
    """Read an UploadedFile object into a DataFrame."""
    if uploaded_file.name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, engine="openpyxl")
    return pd.read_csv(uploaded_file)


def _persist_upload(df: pd.DataFrame, filename: str, file_type: str) -> int:
    """Save dataset + columns metadata to DB. Returns dataset_id."""
    session = get_session()
    try:
        dataset_id = insert_dataset(
            session,
            name=Path(filename).stem,
            original_filename=filename,
            file_type=file_type,
            row_count=len(df),
            column_count=len(df.columns),
        )
        cols = [
            {
                "column_name": col,
                "detected_dtype": str(df[col].dtype),
                "missing_count": int(df[col].isna().sum()),
                "unique_count": int(df[col].nunique()),
                "column_order": i,
            }
            for i, col in enumerate(df.columns)
        ]
        insert_dataset_columns(session, dataset_id, cols)
    finally:
        session.close()
    return dataset_id


# ── Section renderers ─────────────────────────────────────────────────────────

def _apply_action(new_df: pd.DataFrame, log_entry: dict) -> None:
    """Update session state and persist the cleaning action to DB."""
    st.session_state["cleaned_df"] = new_df
    st.session_state["cleaning_log"].append(log_entry)
    did = st.session_state.get("dataset_id")
    if did:
        try:
            session = get_session()
            insert_cleaning_action(
                session,
                dataset_id=did,
                action_type=log_entry["action"],
                target_column=log_entry["column"] if log_entry["column"] != "—" else None,
                parameters=log_entry.get("params", {}),
                rows_affected=log_entry["rows_affected"],
            )
            session.close()
        except Exception:
            pass  # DB unavailable — in-memory state still valid


def _section_header(title: str, subtitle: str) -> None:
    st.markdown(f"""
    <div style="margin-bottom:2rem;padding-bottom:1rem;border-bottom:1px solid #E8EDF5;">
        <h1 style="margin:0 0 4px 0;">{title}</h1>
        <p style="margin:0;font-size:0.85rem;color:#94A3B8;font-weight:400;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)



def _render_upload() -> None:
    _section_header("Upload", "Import a CSV or Excel file to get started")
    col_a, col_b = st.columns([3, 1])

    with col_a:
        uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

    with col_b:
        st.write("")
        st.write("")
        if st.button("Load sample messy dataset", use_container_width=True):
            if SAMPLE_PATH.exists():
                df = pd.read_csv(SAMPLE_PATH)
                st.session_state["original_df"] = df
                st.session_state["cleaned_df"] = df.copy()
                st.session_state["cleaning_log"] = []
                st.session_state["uploaded_filename"] = "messy_employees.csv"
                with st.spinner("Saving to database…"):
                    try:
                        did = _persist_upload(df, "messy_employees.csv", "csv")
                        st.session_state["dataset_id"] = did
                    except Exception as exc:
                        st.warning(f"DB save skipped: {exc}")
                st.success(f"Sample dataset loaded: {len(df)} rows × {len(df.columns)} columns")
            else:
                st.error("sample_data/messy_employees.csv not found — run generate_messy_csv.py first.")

    if uploaded is not None:
        file_type = "xlsx" if uploaded.name.endswith(".xlsx") else "csv"
        with st.spinner("Reading file…"):
            try:
                df = _load_file(uploaded)
                save_path = UPLOAD_DIR / uploaded.name
                save_path.write_bytes(uploaded.getvalue())
                st.session_state["original_df"] = df
                st.session_state["cleaned_df"] = df.copy()
                st.session_state["cleaning_log"] = []
                st.session_state["uploaded_filename"] = uploaded.name
                try:
                    did = _persist_upload(df, str(save_path), file_type)
                    st.session_state["dataset_id"] = did
                except Exception as exc:
                    st.warning(f"DB save skipped: {exc}")
                    st.session_state["dataset_id"] = None
                st.success(f"Loaded **{uploaded.name}**: {len(df)} rows × {len(df.columns)} columns")
            except Exception as exc:
                st.error(f"Could not read file: {exc}")

    if st.session_state["original_df"] is not None:
        st.markdown('<p style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.5rem;">Preview</p>', unsafe_allow_html=True)
        st.dataframe(
            st.session_state["original_df"],
            use_container_width=True,
            height=420,
        )


def _render_profile() -> None:
    _section_header("Profile", "Statistical overview of your dataset")
    df = st.session_state["original_df"]
    if df is None:
        st.info("Upload a dataset first.")
        return

    with st.spinner("Profiling data…"):
        profile = profile_dataframe(df)

    ov = profile["overview"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{ov['rows']:,}")
    c2.metric("Columns", ov["columns"])
    c3.metric("Memory", f"{ov['memory_bytes'] / 1024:.1f} KB")
    c4.metric("Duplicate Rows", ov["duplicate_rows"])

    st.subheader("Column Details")
    for col_profile in profile["columns"]:
        with st.expander(f"**{col_profile['name']}** — {col_profile['dtype']}"):
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Missing", f"{col_profile['missing_count']} ({col_profile['missing_pct']}%)")
            mc2.metric("Unique", col_profile["unique_count"])
            mc3.metric("Dtype", col_profile["dtype"])

            if "mean" in col_profile:
                nc1, nc2, nc3, nc4, nc5 = st.columns(5)
                nc1.metric("Mean", col_profile["mean"])
                nc2.metric("Median", col_profile["median"])
                nc3.metric("Min", col_profile["min"])
                nc4.metric("Max", col_profile["max"])
                nc5.metric("Std Dev", col_profile["std"])
            elif "top_values" in col_profile:
                top_df = pd.DataFrame(col_profile["top_values"])
                st.table(top_df.rename(columns={"value": "Value", "count": "Count"}))


def _render_clean() -> None:
    _section_header("Clean", "Apply transformations to fix quality issues")
    df = st.session_state["cleaned_df"]
    if df is None:
        st.info("Upload a dataset first.")
        return

    # ── Auto-Clean button (top of page) ────────────────────────────────────────
    with st.container():
        st.subheader("🚀 Auto-Clean")
        st.caption("Automatically apply intelligent cleaning to your entire dataset")
        col_ac1, col_ac2 = st.columns([2, 1])
        with col_ac2:
            if st.button("Run Auto-Clean", use_container_width=True, type="primary"):
                with st.spinner("Auto-cleaning dataset…"):
                    try:
                        cleaned_df, logs = auto_clean(df)
                        st.session_state["cleaned_df"] = cleaned_df
                        st.session_state["cleaning_log"].extend(logs)
                        
                        # Persist to database
                        did = st.session_state.get("dataset_id")
                        if did:
                            try:
                                session = get_session()
                                for log in logs:
                                    insert_cleaning_action(
                                        session,
                                        dataset_id=did,
                                        action_type=log["action"],
                                        target_column=log["column"] if log["column"] != "—" else None,
                                        parameters=log.get("params", {}),
                                        rows_affected=log["rows_affected"],
                                    )
                                session.close()
                            except Exception:
                                pass
                        
                        # Show summary
                        total_rows_affected = sum(log["rows_affected"] for log in logs)
                        st.success(f"✓ Auto-clean complete! {len(logs)} actions applied, {total_rows_affected} rows affected.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error: {exc}")
        
        with col_ac1:
            with st.expander("What does auto-clean do?"):
                st.markdown("""
                **Auto-Clean performs the following steps:**
                1. **Remove duplicates** — Exact row duplicates
                2. **Fill missing values** — Median for numeric, mode for categorical
                3. **Standardize text** — Trim whitespace, convert to lowercase
                4. **Standardize dates** — Detect date columns and convert to ISO format (YYYY-MM-DD)
                5. **One-shot operation** — No manual decisions needed!
                """)
    
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Missing Values", "Duplicates", "Type Conversion",
        "Text & Dates", "Invalid Data Filter",
    ])

    # ── Tab 1: Missing values ──────────────────────────────────────────────
    with tab1:
        st.subheader("Handle Missing Values")
        col = st.selectbox("Column", df.columns, key="mv_col")
        missing_n = int(df[col].isna().sum())
        st.info(f"{missing_n} missing values in **{col}**")
        method = st.selectbox(
            "Method",
            ["drop_row", "drop_column", "mean", "median", "mode", "custom", "ffill", "bfill"],
            key="mv_method",
        )
        custom_val = None
        if method == "custom":
            custom_val = st.text_input("Custom fill value", key="mv_custom")
        if st.button("Apply", key="mv_apply"):
            if missing_n == 0:
                st.warning("No missing values in this column.")
            else:
                with st.spinner("Applying…"):
                    try:
                        new_df, log = fill_missing(df, col, method, custom_val)
                        _apply_action(new_df, log)
                        st.success(f"Done — {log['rows_affected']} values affected.")
                    except Exception as exc:
                        st.error(f"Error: {exc}")

    # ── Tab 2: Duplicates ──────────────────────────────────────────────────
    with tab2:
        st.subheader("Remove Duplicates")
        dup_count = int(df.duplicated().sum())
        st.info(f"{dup_count} duplicate rows detected")
        subset_cols = st.multiselect("Consider only these columns (leave empty = all)", df.columns, key="dup_subset")
        keep = st.radio("Keep", ["first", "last", "none"], key="dup_keep")
        keep_val: str | bool = keep if keep != "none" else False
        if st.button("Remove Duplicates", key="dup_apply"):
            with st.spinner("Removing…"):
                try:
                    sub = subset_cols if subset_cols else None
                    new_df, log = drop_duplicates(df, sub, keep_val)
                    _apply_action(new_df, log)
                    st.success(f"Removed {log['rows_affected']} duplicate rows.")
                except Exception as exc:
                    st.error(f"Error: {exc}")

    # ── Tab 3: Type conversion ─────────────────────────────────────────────
    with tab3:
        st.subheader("Convert Column Type")
        tc_col = st.selectbox("Column", df.columns, key="tc_col")
        st.caption(f"Current dtype: **{df[tc_col].dtype}**")
        tc_type = st.selectbox("Target type", ["numeric", "datetime", "string", "category", "boolean"], key="tc_type")
        tc_fmt = None
        if tc_type == "datetime":
            tc_fmt = st.text_input("Date format hint (optional, e.g. %d/%m/%Y)", key="tc_fmt") or None
        if st.button("Convert", key="tc_apply"):
            with st.spinner("Converting…"):
                try:
                    new_df, log = convert_type(df, tc_col, tc_type, tc_fmt)
                    _apply_action(new_df, log)
                    new_dtype = new_df[tc_col].dtype if tc_col in new_df.columns else "dropped"
                    st.success(f"Converted **{tc_col}** → {new_dtype}. {log['rows_affected']} values coerced to NaN.")
                except Exception as exc:
                    st.error(f"Error: {exc}")

    # ── Tab 4: Text & Dates ────────────────────────────────────────────────
    with tab4:
        st.subheader("Text Standardization")
        obj_cols = df.select_dtypes(include="object").columns.tolist()
        txt_col = st.selectbox("Column", obj_cols if obj_cols else df.columns.tolist(), key="txt_col")
        ops = st.multiselect("Operations (applied in order)", ["trim", "lowercase", "uppercase", "titlecase"], key="txt_ops")
        if st.button("Apply Text Ops", key="txt_apply"):
            if not ops:
                st.warning("Select at least one operation.")
            else:
                with st.spinner("Standardizing text…"):
                    try:
                        new_df, log = standardize_text(df, txt_col, ops)
                        _apply_action(new_df, log)
                        st.success(f"Applied {ops} to **{txt_col}**.")
                    except Exception as exc:
                        st.error(f"Error: {exc}")

        st.divider()
        st.subheader("Date Standardization")
        date_col = st.selectbox("Date column", df.columns, key="date_col")
        date_fmt = st.text_input("Output format", value="%Y-%m-%d", key="date_fmt")
        if st.button("Standardize Dates", key="date_apply"):
            with st.spinner("Parsing dates…"):
                try:
                    new_df, log = standardize_dates(df, date_col, date_fmt)
                    _apply_action(new_df, log)
                    st.success(f"Standardized {log['rows_affected']} date values in **{date_col}**.")
                except Exception as exc:
                    st.error(f"Error: {exc}")

    # ── Tab 5: Invalid data filter ─────────────────────────────────────────
    with tab5:
        st.subheader("Filter Invalid Values")
        fi_col = st.selectbox("Column", df.columns, key="fi_col")
        rule = st.selectbox("Rule type", ["numeric_range", "regex_match", "allowed_values"], key="fi_rule")
        min_v = max_v = regex_p = allowed_v = None
        if rule == "numeric_range":
            c1, c2 = st.columns(2)
            min_v = c1.number_input("Min (inclusive)", key="fi_min", value=0.0)
            max_v = c2.number_input("Max (inclusive)", key="fi_max", value=999999.0)
        elif rule == "regex_match":
            regex_p = st.text_input("Regex pattern (rows NOT matching are removed)", key="fi_regex")
        elif rule == "allowed_values":
            raw = st.text_area("Allowed values (one per line)", key="fi_allowed")
            allowed_v = [v.strip() for v in raw.splitlines() if v.strip()] if raw else None
        if st.button("Apply Filter", key="fi_apply"):
            with st.spinner("Filtering…"):
                try:
                    new_df, log = filter_invalid(df, fi_col, rule, min_v, max_v, regex_p, allowed_v)
                    _apply_action(new_df, log)
                    st.success(f"Removed {log['rows_affected']} invalid rows from **{fi_col}**.")
                except Exception as exc:
                    st.error(f"Error: {exc}")

    # ── Cleaning log + Undo/Reset ──────────────────────────────────────────
    st.divider()
    st.subheader("Cleaning Log")
    log = st.session_state["cleaning_log"]
    if not log:
        st.caption("No actions applied yet.")
    else:
        log_df = pd.DataFrame(log)[["action", "column", "rows_affected"]]
        log_df.index = range(1, len(log_df) + 1)
        st.dataframe(log_df, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("↩ Undo Last Action", use_container_width=True):
            if not log:
                st.warning("Nothing to undo.")
            else:
                orig = st.session_state["original_df"].copy()
                new_log = log[:-1]
                replayed = _replay_actions(orig, new_log)
                st.session_state["cleaned_df"] = replayed
                st.session_state["cleaning_log"] = new_log
                did = st.session_state.get("dataset_id")
                if did:
                    try:
                        s = get_session()
                        delete_last_cleaning_action(s, did)
                        s.close()
                    except Exception:
                        pass
                st.success("Last action undone.")
                st.rerun()

    with c2:
        if st.button("🔄 Reset to Original", use_container_width=True):
            st.session_state["cleaned_df"] = st.session_state["original_df"].copy()
            st.session_state["cleaning_log"] = []
            did = st.session_state.get("dataset_id")
            if did:
                try:
                    s = get_session()
                    delete_all_cleaning_actions(s, did)
                    s.close()
                except Exception:
                    pass
            st.success("Reset to original dataset.")
            st.rerun()


def _render_compare() -> None:
    _section_header("Compare", "Side-by-side diff of original vs cleaned data")
    orig = st.session_state["original_df"]
    clean = st.session_state["cleaned_df"]
    if orig is None or clean is None:
        st.info("Upload a dataset first.")
        return

    orig_rows, clean_rows = len(orig), len(clean)
    orig_cols, clean_cols = len(orig.columns), len(clean.columns)
    removed_rows = orig_rows - clean_rows
    removed_cols = orig_cols - clean_cols

    log = st.session_state["cleaning_log"]
    imputed = sum(e["rows_affected"] for e in log if e["action"] == "fill_missing")
    dupes_dropped = sum(e["rows_affected"] for e in log if e["action"] == "drop_duplicates")

    st.info(
        f"**Summary:** {removed_rows} rows removed · "
        f"{imputed} values imputed · "
        f"{dupes_dropped} duplicates dropped · "
        f"{removed_cols} columns removed"
    )

    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Original ({orig_rows} rows × {orig_cols} cols)")
        st.dataframe(orig, use_container_width=True, height=400)
    with c2:
        st.subheader(f"Cleaned ({clean_rows} rows × {clean_cols} cols)")
        st.dataframe(clean, use_container_width=True, height=400)

    # Highlight cells that changed (shared columns only, first 500 rows for perf)
    shared_cols = [c for c in clean.columns if c in orig.columns]
    if shared_cols and len(clean) > 0:
        st.subheader("Changed Cells (first 500 rows, shared columns)")
        orig_sub = orig[shared_cols].head(500).reset_index(drop=True)
        clean_sub = clean[shared_cols].head(500).reset_index(drop=True)
        min_rows = min(len(orig_sub), len(clean_sub))
        orig_sub = orig_sub.iloc[:min_rows]
        clean_sub = clean_sub.iloc[:min_rows]

        def _highlight(row):
            orig_row = orig_sub.iloc[row.name] if row.name < len(orig_sub) else None
            styles = []
            for col in row.index:
                if orig_row is not None and str(row[col]) != str(orig_row[col]):
                    styles.append("background-color: #d4edda")
                else:
                    styles.append("")
            return styles

        styled = clean_sub.style.apply(_highlight, axis=1)
        st.dataframe(styled, use_container_width=True, height=400)

    # ── Download ──────────────────────────────────────────────────────────
    st.divider()
    fname = st.session_state.get("uploaded_filename") or "data.csv"
    download_name = f"cleaned_{Path(fname).stem}.csv"
    st.download_button(
        label="⬇️ Download Cleaned CSV",
        data=clean.to_csv(index=False).encode("utf-8"),
        file_name=download_name,
        mime="text/csv",
        key="compare_download_csv",
    )


def _render_insights() -> None:
    _section_header("Insights", "Auto-generated statistics and correlations")
    df = st.session_state["cleaned_df"]
    if df is None:
        st.info("Upload a dataset first.")
        return

    col_options = df.columns.tolist()
    selected = st.multiselect("Columns to analyse", col_options, default=col_options[:4], key="ins_cols")
    top_n = st.slider("Top N frequent values (categorical)", 3, 20, 5, key="ins_topn")

    if not selected:
        st.warning("Select at least one column.")
        return

    with st.spinner("Generating insights…"):
        insights = generate_insights(df, selected, top_n)

    if not insights:
        st.info("No insights generated for the selected columns.")
        return

    st.subheader("Auto-Generated Bullets")
    for ins in insights:
        st.markdown(f"- {ins['description']}")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(num_cols) >= 2:
        st.subheader("Correlation Heatmap")
        corr = correlation_matrix(df)
        fig = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            title="Numeric Column Correlations",
            aspect="auto",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    if st.button("💾 Save insights to database", key="ins_save"):
        did = st.session_state.get("dataset_id")
        if not did:
            st.warning("No dataset_id — upload was not persisted to DB.")
        else:
            try:
                session = get_session()
                for ins in insights:
                    insert_insight(
                        session,
                        dataset_id=did,
                        insight_type=ins["type"],
                        target_column=ins["column"] if "×" not in ins["column"] else None,
                        description=ins["description"],
                        value_numeric=ins.get("value_numeric"),
                    )
                session.close()
                st.success(f"Saved {len(insights)} insights to database.")
            except Exception as exc:
                st.error(f"DB error: {exc}")


def _render_dashboard() -> None:
    _section_header("Dashboard", "Build interactive charts from your cleaned data")
    df = st.session_state["cleaned_df"]
    if df is None:
        st.info("Upload a dataset first.")
        return

    all_cols = df.columns.tolist()

    st.subheader("Add Chart")
    with st.form("add_chart_form"):
        fc1, fc2, fc3 = st.columns(3)
        chart_type = fc1.selectbox("Chart type", ["bar", "line", "pie", "scatter", "histogram"])
        x_col = fc2.selectbox("X column", all_cols)
        y_col = fc3.selectbox("Y column (optional for histogram/pie)", ["(none)"] + df.select_dtypes(include="number").columns.tolist())
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
                if st.button(f"💾 Save to DB", key=f"save_chart_{i}"):
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
                if st.button(f"🗑 Remove", key=f"remove_chart_{i}"):
                    st.session_state["charts"].pop(i)
                    st.rerun()
            st.divider()


def _replay_actions(df: pd.DataFrame, log: list[dict]) -> pd.DataFrame:
    """Replay a cleaning log list on df, returning the resulting DataFrame."""
    action_map = {
        "fill_missing": lambda df, e: fill_missing(df, e["column"], e["params"]["method"], e["params"].get("custom_value"))[0],
        "drop_duplicates": lambda df, e: drop_duplicates(df, e["params"].get("subset"), e["params"].get("keep", "first"))[0],
        "convert_type": lambda df, e: convert_type(df, e["column"], e["params"]["target_type"], e["params"].get("datetime_format"))[0],
        "standardize_text": lambda df, e: standardize_text(df, e["column"], e["params"]["operations"])[0],
        "standardize_dates": lambda df, e: standardize_dates(df, e["column"], e["params"].get("output_format", "%Y-%m-%d"))[0],
        "filter_invalid": lambda df, e: filter_invalid(
            df, e["column"], e["params"]["rule_type"],
            e["params"].get("min_val"), e["params"].get("max_val"),
            e["params"].get("regex_pattern"), e["params"].get("allowed_values"),
        )[0],
    }
    for entry in log:
        handler = action_map.get(entry["action"])
        if handler:
            try:
                df = handler(df, entry)
            except Exception:
                pass
    return df


# ── Section router ────────────────────────────────────────────────────────────
section = st.session_state["section"]

try:
    if section == "Upload":
        _render_upload()
    elif section == "Profile":
        _render_profile()
    elif section == "Clean":
        _render_clean()
    elif section == "Compare":
        _render_compare()
    elif section == "Insights":
        _render_insights()
    elif section == "Dashboard":
        _render_dashboard()
except Exception as exc:
    st.error(f"Unexpected error in **{section}**: {exc}")
    st.caption("Try resetting to original or re-uploading your file.")
