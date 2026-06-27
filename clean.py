import pandas as pd

# Accepting the dictionary output from validate.py
# Creating a new data frame from the changes made

def clean(df: pd.DataFrame, validation_report:dict) -> pd.DataFrame:

    # create a clean copy
    clean_df = df.copy()
    rows_before = len(clean_df)
    print(f"[clean] Starting with {rows_before} rows")

    dupes = clean_df.duplicated(keep="first")
    dup_count = dupes.sum()
    if dup_count > 0:
        clean_df = clean_df[~dupes]
        print(f"[clean] Dropped {dup_count} duplicate row(s)")

        # Drop rows with blank critical fields

        critical_cols = ["product", "category", "unit_price"]
        for col in critical_cols:
            blank_mask = clean_df[col].apply(_is_blank)
            blank_count = blank_mask.sum()
            if blank_count > 0:
                clean_df = clean_df[~blank_mask]
                print(f"[clean] Dropped {blank_count} row(s) with blank '{col}'")

                # Drop rows with unparseable dates

                date_parsed = pd.to_datetime(clean_df["date"], errors="coerce")
                bad_date_mask = date_parsed.isna()
                bad_date_count = bad_date_mask.sum()
                if bad_date_count > 0:
                    clean_df = clean_df[~bad_date_mask]
                    print(f"[clean] Dropped {bad_date_count} row(s) with unparseable date")

                    # Drop rows with invalid quantity

                    qty_numeric = pd.to_numeric(clean_df["quantity"], errors="coerce")
                    bad_qty_mask = qty_numeric.isna() | (qty_numeric <= 0)
                    bad_qty_count = bad_qty_mask.sum()
                    if bad_qty_count > 0:
                        clean_df = clean_df[~bad_qty_mask]
                        print(f"[clean] Dropped {bad_qty_count} row(s) with invalid quantity")

                        #Normalize text fields

                        clean_df["category"] = clean_df["category"].str.lower().str.strip()
                        clean_df["status"] = clean_df["status"] = clean_df["product"].str.lower().str.strip()
                        clean_df["product"] = clean_df["product"] = clean_df["product"].str.lower().str.strip()
                        print("[clean] Normalized category, status, and product casing")

                        # Convert types

                        # All values are valid by this point

                        clean_df["date"] = pd.to_datetime(clean_df["date"])
                        clean_df["quantity"] = clean_df["quantity"].astype(int)
                        clean_df["unit_price"] = clean_df["unit_price"].astype(float)
                        print("[clean] Coverted types: date > datetime, quantity > int, unit_price > float")

                        # Compute revenue so we don't need to in transform.py

                        clean_df["revenue"] = clean_df["quantity"] * clean_df["unit_price"]
                        print("[clean] Computed revecnue column")

                        rows_after = len(clean_df)
                        dropped = rows_before - rows_after
                        print(f"[clean] Finished: {rows_after} rows remain ({dropped} dropped total)")

                        return clean_df
                    def _is_blank(value) -> bool:
                        if pd.isna(value):
                            return True
                        return str(value).strip() == ""
                        



