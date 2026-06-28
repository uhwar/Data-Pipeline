import sys
from pathlib import Path

from ingest import load_csv
from validate import validate
from clean import clean
from transform import transform
from load import load

def run_pipeline(csv_path: str = "raw_sales_data.csv", db_path: str = "sales.db") -> dict:
    print("*=" * 15)
    print("SALES DATA PIPELINE")
    print("*=" * 15)

    # Ingest Phase
    print("Stage 1: Ingest")
    raw_df = load_csv(csv_path)
    rows_ingested = len(raw_df)
    print("rows ingested: ", rows_ingested)

    # Validate Phase
    print("Stage 2: Validate")
    try:
        report = validate(raw_df)
    except ValueError as e:
        print(f"[pipeline] VALIDATION FAILED, cannot continue: {e}")
        sys.exit(1)
    issues_found = len(report["issues"])
    bad_rows_count = len(report["bad_rows"])

    print("Stage 3: Clean")
    clean_df = clean(raw_df, report)
    rows_clean = len(clean_df)
    rows_dropped = rows_ingested - rows_clean

    # Transform Phase
    print("Stage 4: Transform")
    aggregates = transform(clean_df)
    aggregate_count = len(aggregates)

    # Load Phase
    print("Stage 5: Load")
    load(clean_df, aggregates, db_path)

    # Summary Build
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  CSV file:          {csv_path}")
    print(f"  Database file:     {db_path}")
    print(f"  Rows ingested:     {rows_ingested}")
    print(f"  Issues found:      {issues_found}")
    print(f"  Bad rows flagged:  {bad_rows_count}")
    print(f"  Rows dropped:      {rows_dropped}")
    print(f"  Rows cleaned:      {rows_clean}")
    print(f"  Aggregates built:  {aggregate_count}")
    print(f"  Tables in SQLite:  {aggregate_count + 1} (clean_orders + {aggregate_count} aggregates)")
    print("=" * 60)

    return {
        "csv_path": csv_path,
        "db_path": db_path,
        "rows_ingested": rows_ingested,
        "issues_found": issues_found,
        "bad_rows_flagged": bad_rows_count,
        "rows_dropped": rows_dropped,
        "rows_clean": rows_clean,
        "aggregates_built": aggregate_count,
        "tables_created": aggregate_count + 1,
    }

if __name__ == "__main__":
    run_pipeline()