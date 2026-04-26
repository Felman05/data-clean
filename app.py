"""Main Streamlit application — Data Cleaning and Analytics System (BAT403)."""
import streamlit as st
import pandas as pd
from pathlib import Path

from modules.db import test_connection, get_session
from modules.repository import insert_dataset, insert_dataset_columns

st.set_page_config(page_title="FEDM Data Cleaner", layout="wide", page_icon="🧹")

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
    st.title("🧹 FEDM Data Cleaner")
    st.caption("BAT403 — Enterprise Data Management")

    ok, db_msg = test_connection()
    if ok:
        st.success(db_msg)
    else:
        st.warning(db_msg)

    st.divider()
    sections = ["Upload", "Profile", "Clean", "Compare", "Insights", "Dashboard"]
    for sec in sections:
        if st.button(sec, use_container_width=True, key=f"nav_{sec}"):
            st.session_state["section"] = sec

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

def _render_upload() -> None:
    st.header("📂 Upload Dataset")
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
        st.subheader("Preview")
        st.dataframe(
            st.session_state["original_df"],
            use_container_width=True,
            height=400,
        )


def _render_profile() -> None:
    st.header("📊 Data Profile")
    if st.session_state["original_df"] is None:
        st.info("Upload a dataset first.")
        return
    st.info("Profile section — coming in Task 5.")


def _render_clean() -> None:
    st.header("🧼 Data Cleaning")
    if st.session_state["cleaned_df"] is None:
        st.info("Upload a dataset first.")
        return
    st.info("Cleaning section — coming in Task 6.")


def _render_compare() -> None:
    st.header("🔍 Before vs After")
    if st.session_state["original_df"] is None:
        st.info("Upload a dataset first.")
        return
    st.info("Comparison section — coming in Task 7.")


def _render_insights() -> None:
    st.header("💡 Insights")
    if st.session_state["cleaned_df"] is None:
        st.info("Upload a dataset first.")
        return
    st.info("Insights section — coming in Task 8.")


def _render_dashboard() -> None:
    st.header("📈 Dashboard")
    if st.session_state["cleaned_df"] is None:
        st.info("Upload a dataset first.")
        return
    st.info("Dashboard section — coming in Task 9.")


def _replay_actions(df: pd.DataFrame, log: list[dict]) -> pd.DataFrame:
    """Replay a cleaning log on df. Stub — full implementation in Task 6."""
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
