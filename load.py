import sqlite3
import pandas as pd
from pathlib import Path

def load(clean_df: pd.DataFrame, aggregates:dict, db_path: str = "sales.db") -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[load] Writing to SQLite: {db_path}")

    with sqlite3.connect(db_path) as conn:
        # Clean orders (the full cleaned dataset)
        clean_df.to_sql(
            name="clean_orders",
            con=conn,
            if_exists="replace",
            index=False
        )
        print(f"[load] Wrote {len(clean_df)} rows to 'clean_orders'")
        for name, df in aggregates.items():
            df.to_sql(
                name=name,
                con=conn,
                if_exists="replace",
                index=False
            )
            print(f"[load] Wrote {len(df)} rows to '{name}'")
    print(f"[load] Done. Database saved to {db_path}")


def query_db(db_path: str, sql: str) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql, conn)