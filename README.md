# FEDM Data Cleaning and Analytics System

BAT403 — Foundations of Enterprise Data Management  
Semestral Project

## Requirements

- Python 3.11+
- XAMPP with MySQL running on port 3306

## Installation

1. Clone or copy this project folder.
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and set your MySQL credentials (defaults work for XAMPP with no root password).

## Database Setup (phpMyAdmin)

1. Open http://localhost/phpmyadmin
2. Click **Import** in the top navigation bar.
3. Click **Choose File** → select `database/schema.sql`
4. Click **Go**.
5. The `fedm_system` database and all 5 tables will be created.
6. *(Optional)* Repeat for `database/seed.sql` to load demo rows.

## Running the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Generating the Sample Dataset

If `sample_data/messy_employees.csv` is missing:

```bash
python sample_data/generate_messy_csv.py
```

## Project Structure

```
fedm-proj/
├── app.py                  Main Streamlit application
├── modules/
│   ├── profiler.py         Data profiling
│   ├── cleaner.py          Cleaning engine (6 methods)
│   ├── insights.py         Insight generation
│   ├── visualizer.py       Plotly chart builders
│   ├── db.py               SQLAlchemy engine + connection test
│   └── repository.py       CRUD for all DB tables
├── database/
│   ├── schema.sql          CREATE DATABASE + tables
│   └── seed.sql            Demo rows
├── sample_data/
│   ├── generate_messy_csv.py
│   └── messy_employees.csv
├── storage/uploads/        Uploaded files (auto-created)
├── .env.example            Environment variable template
├── requirements.txt
└── README.md
```

## Workflow

**Upload → Profile → Clean → Compare → Insights → Dashboard**

Use the sidebar to navigate between sections. Cleaning state persists across navigation via `st.session_state`.

## Database Tables

| Table | Purpose |
|-------|---------|
| `datasets` | One row per uploaded file |
| `dataset_columns` | Per-column metadata for each dataset |
| `cleaning_actions` | Every cleaning operation, in order (supports undo/replay) |
| `insights` | Saved plain-English insight bullets |
| `dashboard_charts` | Saved chart configurations |

## Cleaning Methods

| Tab | Operations |
|-----|-----------|
| Missing Values | drop row, drop column, fill mean/median/mode/custom, forward fill, backward fill |
| Duplicates | subset-aware detection and removal |
| Type Conversion | numeric, datetime, string, category, boolean |
| Text & Dates | trim, lowercase/uppercase/titlecase, ISO date normalization |
| Invalid Data Filter | numeric range, regex match, allowed values list |
"# data-clean" 
