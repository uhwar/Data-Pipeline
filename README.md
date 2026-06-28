# Sales Data Pipeline

A modular ETL pipeline that reads raw sales data from a CSV file, validates and cleans it, builds business-ready aggregates, and writes everything to a SQLite database. Built with Python, pandas, and SQLite.

> **ETL** stands for Extract, Transform, Load — the industry-standard pattern for moving raw data into a usable format. Most production data pipelines (at companies like Stripe, Shopify, or any analytics team) follow this same three-phase structure. This project is a clean, minimal implementation of that pattern.

---

## What Goes In

The pipeline reads a single CSV file: `raw_sales_data.csv`. Think of a CSV as a spreadsheet saved as plain text — each row is one order, each column is a field about that order.

Here is what each row looks like and what each field means:

| Column | Type | Example | What it means |
|---|---|---|---|
| `order_id` | text | `ORD-001` | Unique ID for each purchase |
| `customer_id` | text | `CUST-042` | Who bought it |
| `date` | text | `2024-03-15` | When the purchase happened |
| `product` | text | `Wireless Headphones` | What was sold |
| `category` | text | `Electronics` | Product group |
| `quantity` | number | `2` | How many units |
| `unit_price` | number | `49.99` | Price per unit |
| `status` | text | `completed` | Order outcome |

**Valid statuses** are `completed`, `pending`, and `refunded`. Anything else is flagged as invalid.

A realistic raw file looks like this — messy, with blank cells, typos, and duplicates mixed in:

```
order_id,customer_id,date,product,category,quantity,unit_price,status
ORD-001,CUST-042,2024-03-15,Wireless Headphones,Electronics,2,49.99,completed
ORD-002,CUST-017,2024-03-15,Running Shoes,Apparel,1,89.99,pending
ORD-001,CUST-042,2024-03-15,Wireless Headphones,Electronics,2,49.99,completed  ← duplicate
ORD-003,CUST-088,,Yoga Mat,Fitness,-1,29.99,completed                           ← missing date, bad qty
ORD-004,CUST-011,2024-03-16,Coffee Maker,Kitchen,1,,shipped                     ← missing price, bad status
```

The pipeline's job is to turn that noise into clean, trustworthy data.

---

## How the Pipeline Works

```
raw_sales_data.csv
        │
        ▼
  ┌─────────────┐
  │  1. ingest  │  Read the CSV into memory
  └──────┬──────┘
         │
         ▼
  ┌──────────────┐
  │  2. validate │  Scan for issues, build a report
  └──────┬───────┘
         │
         ▼
  ┌────────────┐
  │  3. clean  │  Drop bad rows, fix types, add revenue
  └──────┬─────┘
         │
         ▼
  ┌─────────────────┐
  │  4. transform   │  Aggregate into summary tables
  └──────┬──────────┘
         │
         ▼
  ┌────────────┐
  │  5. load   │  Write everything to SQLite
  └──────┬─────┘
         │
         ▼
      sales.db
```

Each stage is a separate Python file with one job. They pass data to each other through function calls in `main.py`.

---

## File Reference

### `ingest.py` — Read the CSV

Reads the CSV file and loads it into a **DataFrame** (think of a DataFrame as an in-memory table — like a spreadsheet you can query with code). All values are loaded as plain strings so nothing gets silently converted before validation.

**Key function:** `load_csv(filepath)`

```python
# Reads the file, strips whitespace from column names, returns a DataFrame
def load_csv(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, dtype=str)
    df.columns = df.columns.str.strip()
    return df
```

`dtype=str` is important — it forces pandas to read everything as text. Without it, pandas might silently convert `"ORD-001"` to `NaN` if it looks like a number.

---

### `validate.py` — Find Problems

Scans the raw DataFrame for anything that would cause downstream errors. It does not fix anything — it just reports what it found. The result is a **validation report**: a Python dictionary containing a list of issues and the row indices (positions) of every bad row.

**Key function:** `validate(df)` → returns `{"passed": bool, "issues": list, "bad_rows": Index}`

```python
# Check that all required columns actually exist
missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

# Flag any row where a critical field is blank or null
for col in critical_columns:
    blank_mask = df[col].apply(_is_blank)   # returns True/False per row
    if blank_mask.sum() > 0:
        issues.append(f"Column '{col}' has {blank_mask.sum()} null/empty value(s)")
```

**What it checks:**
- All 8 required columns are present
- No blank/null values in critical fields (`order_id`, `customer_id`, `date`, `product`, `category`, `unit_price`)
- `quantity` is numeric and greater than zero
- `unit_price` is numeric
- `status` is one of `completed`, `pending`, or `refunded`
- No duplicate rows

**Helper function:** `_is_blank(value)` — returns `True` if a value is `None`, `NaN`, or an empty/whitespace string. Imported by `clean.py` to avoid duplication.

---

### `clean.py` — Fix the Data

Takes the raw DataFrame and the validation report, then returns a clean copy with bad rows removed and types corrected. It also adds a `revenue` column computed from `quantity × unit_price` so `transform.py` doesn't have to.

**Key function:** `clean(df, validation_report)` → returns a clean `pd.DataFrame`

```python
# Drop exact duplicate rows
clean_df = clean_df[~clean_df.duplicated(keep="first")]

# Drop rows where a critical field is blank
for col in ["product", "category", "unit_price"]:
    blank_mask = clean_df[col].apply(_is_blank)
    clean_df = clean_df[~blank_mask]

# Normalize text so "Electronics" and "electronics" don't count as two categories
clean_df["category"] = clean_df["category"].str.lower().str.strip()

# Convert columns to their proper types
clean_df["date"]       = pd.to_datetime(clean_df["date"])
clean_df["quantity"]   = clean_df["quantity"].astype(int)
clean_df["unit_price"] = clean_df["unit_price"].astype(float)

# Add revenue so transform.py doesn't have to recompute it
clean_df["revenue"] = clean_df["quantity"] * clean_df["unit_price"]
```

The `~` operator before a mask means "NOT this" — `~blank_mask` keeps every row where `_is_blank` returned `False`.

---

### `transform.py` — Build Summaries

Takes the clean DataFrame and produces five aggregate tables — pre-summarized views of the data that are ready to query. Instead of returning a single DataFrame, it returns a **dictionary** where each key is a table name and each value is a DataFrame.

**Key function:** `transform(clean_df)` → returns `dict[str, pd.DataFrame]`

```python
# Total revenue per product category, highest first
revenue_by_category = (
    clean_df.groupby("category")["revenue"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

# Monthly totals: revenue, order count, and units sold
clean_df["year_month"] = clean_df["date"].dt.to_period("M").astype(str)
monthly_totals = (
    clean_df.groupby("year_month")
    .agg(
        total_revenue=("revenue", "sum"),
        order_count=("order_id", "nunique"),
        total_quantity=("quantity", "sum")
    )
    .reset_index()
)
```

`groupby` is the pandas equivalent of `GROUP BY` in SQL — it splits the data into groups and lets you run calculations on each group. `.agg()` lets you run multiple calculations at once.

**The five aggregates produced:**

| Table | Groups by | Calculates |
|---|---|---|
| `revenue_by_category` | category | total revenue |
| `monthly_totals` | year + month | revenue, orders, units |
| `top_products` | product | revenue (top 5 only) |
| `status_breakdown` | status | order count, revenue |
| `customer_summary` | customer | total spend, orders, avg order value |

---

### `load.py` — Write to SQLite

Takes the clean DataFrame and the aggregates dictionary and writes them all to a SQLite database file. SQLite is a file-based database — the entire database lives in a single `.db` file on disk. No server required.

**Key functions:** `load(clean_df, aggregates, db_path)` and `query_db(db_path, sql)`

```python
with sqlite3.connect(db_path) as conn:
    # Write the full cleaned dataset as one table
    clean_df.to_sql(name="clean_orders", con=conn, if_exists="replace", index=False)

    # Write each aggregate as its own table
    for name, df in aggregates.items():
        df.to_sql(name=name, con=conn, if_exists="replace", index=False)
```

`if_exists="replace"` means the table gets dropped and recreated every run — so re-running the pipeline with a new CSV always produces fresh results.

`query_db` is a convenience function for reading the database after the pipeline runs:

```python
# Example: query the database directly
from load import query_db

results = query_db("sales.db", "SELECT * FROM revenue_by_category LIMIT 5")
print(results)
```

---

### `main.py` — The Orchestrator

Calls all five stages in order and prints a summary report when done. This is the only file you run directly.

```python
python main.py
```

You can also call `run_pipeline()` with custom paths:

```python
from main import run_pipeline

result = run_pipeline(csv_path="my_data.csv", db_path="output.db")
```

`run_pipeline()` returns a dictionary with the final counts so other scripts can consume the results programmatically.

---

## What Comes Out

After a successful run, the pipeline creates `sales.db` with **6 tables**:

```
sales.db
├── clean_orders         ← the full cleaned dataset (~187 rows after cleaning 200 raw)
├── revenue_by_category  ← total revenue grouped by product category
├── monthly_totals       ← revenue + order counts by month
├── top_products         ← top 5 products by revenue
├── status_breakdown     ← completed vs. pending vs. refunded breakdown
└── customer_summary     ← per-customer spend, order count, and avg order value
```

### `clean_orders` — the base table

This is the cleaned version of your raw CSV, with types corrected and a `revenue` column added:

| Column | Type | Notes |
|---|---|---|
| `order_id` | TEXT | |
| `customer_id` | TEXT | |
| `date` | DATETIME | parsed from string |
| `product` | TEXT | lowercased |
| `category` | TEXT | lowercased |
| `quantity` | INTEGER | validated > 0 |
| `unit_price` | REAL | validated numeric |
| `status` | TEXT | lowercased |
| `revenue` | REAL | quantity × unit_price |

### Example queries

```sql
-- Total revenue by category
SELECT * FROM revenue_by_category;

-- Best month by revenue
SELECT * FROM monthly_totals ORDER BY total_revenue DESC LIMIT 1;

-- Top 5 customers by spend
SELECT customer_id, total_spend FROM customer_summary LIMIT 5;

-- Refunded orders and their value
SELECT * FROM status_breakdown WHERE status = 'refunded';
```

You can run these with any SQLite viewer (DB Browser for SQLite is free and works well), or use the built-in `query_db()` function from `load.py`.

---

## What You Can Do With This

This pipeline is a foundation. Some natural next steps:

- **Swap in real data** — replace `raw_sales_data.csv` with an export from Shopify, WooCommerce, or any e-commerce platform that exports orders as CSV
- **Add a visualization layer** — connect `sales.db` to a tool like Streamlit or matplotlib to build charts from the aggregate tables
- **Schedule it** — wrap `main.py` in a cron job or GitHub Action to run automatically on new data
- **Extend the transforms** — add more aggregate tables in `transform.py` (weekly instead of monthly, regional breakdowns, return rate calculations)
- **Swap the database** — `pandas.to_sql()` works with PostgreSQL and MySQL too; swap the `sqlite3.connect()` call for a SQLAlchemy engine

---

## Requirements

```
pandas
```

Python's standard library handles SQLite (`sqlite3` is built in). No other dependencies.

```bash
pip install pandas
python main.py
```

---

## Project Structure

```
Data-Pipeline/
├── main.py              # entry point — run this
├── ingest.py            # stage 1: read CSV
├── validate.py          # stage 2: find problems
├── clean.py             # stage 3: fix and type-cast
├── transform.py         # stage 4: build aggregates
├── load.py              # stage 5: write to SQLite
└── raw_sales_data.csv   # sample input data (200 rows)
```
