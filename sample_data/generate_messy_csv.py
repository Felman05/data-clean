"""Generates sample_data/messy_employees.csv with intentional data quality issues."""
import random
import pandas as pd
from pathlib import Path

random.seed(42)

departments = ["Sales", "sales", "SALES", "Engineering", "HR", "Marketing", "marketing"]
statuses = ["Active", "active", "ACTIVE", "Inactive", None]
date_formats = [
    "2021-03-15", "03/15/2021", "15-03-2021", "March 15 2021", "2020-07-04",
    "07/04/2020", "2019-11-30", "30/11/2019", "Nov 30 2019",
]

rows = []
for i in range(1, 201):
    salary = random.choices(
        [random.randint(25000, 180000), None, -500, 9999999],
        weights=[80, 10, 5, 5],
        k=1,
    )[0]
    dept = random.choice(departments)
    if random.random() < 0.05:
        dept = None
    hire = random.choice(date_formats)
    if random.random() < 0.04:
        hire = "not-a-date"
    status = random.choice(statuses)
    name = f"  Employee_{i}  " if random.random() < 0.2 else f"Employee_{i}"
    email = (
        f"emp{i}@company.com" if random.random() > 0.06
        else random.choice(["not-an-email", None, "missing@"])
    )
    rows.append({
        "employee_id": i,
        "name": name,
        "department": dept,
        "salary": salary,
        "hire_date": hire,
        "status": status,
        "email": email,
        "years_experience": random.choices(
            [random.randint(0, 35), None, -2, -5],
            weights=[80, 10, 5, 5],
            k=1,
        )[0],
    })

# Inject 15 exact duplicates
for _ in range(15):
    rows.append(random.choice(rows[:200]))

df = pd.DataFrame(rows)
out = Path(__file__).parent / "messy_employees.csv"
df.to_csv(out, index=False)
print(f"Generated {len(df)} rows -> {out}")
