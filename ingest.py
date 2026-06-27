import pandas as pd

def load_csv(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, dtype=str)
    df.columns = df.columns.str.strip()
    print(f"[ingest Loaded {df.shape[0]} rows, {df.shape[1]} columns from '{filepath}'")
    return df

