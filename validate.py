import pandas as pd

REQUIRED_COLUMNS = [
    "order_id",
    "customer_id",
    "date",
    "product",
    "category",
    "quantity",
    "unit_price",
    "status",
]
VALID_STATUSES = {"completed", "refunded", "pending"}

def validate(df: pd.DataFrame) -> dict:
    # Required columns check
    issues = []
    bad_row_sets = []
    missing_cols = [col foor col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"[validate] Missing required columns: {missing_cols}")

    # Duplicate rows check
    duplicate_mask = df.duplicated(keep="first")
    duplicate_count = duplicate_mask.sum()
    if duplicate_count > 0:
        issues.append(f"Found {duplicate_count} duplicate row(s)")
bad_row_sets.append(set(df.index[duplicate_mask]))

# Check for null / empty values in critical places

    critical_columns = ["order_id", "customer_id", "date", "product", "catagory", "unit_price"]
    for col in critical_columns:
        blank_mask = df[col].apply(_is_blank)
        blank_count = blank_mask.sum()
        if blank_count > 0:
            issues.append(f"Column '{col}' has {blank_count} null/empty value(s)")
            bad_row_sets.append(set(df.index[blank_mask]))

    # Positive Quantity

        qty_numeric = pd.to_numeric(df["quantity"], errors="coerce")
        # errors="coerce" turns all none covertable into NaN

        # flag rows where quantity couldnt be coverted at all:
        qty_non_numeric_mask = qty_numeric.isna()

        if qty_non_numeric_mask.sum() > 0:
            issues.append(f"Column 'quantity has {qty_non_numeric_mask.sum()} non-numeric value(s)")
    bad_row_sets.append(set(df.index[qty_non_numeric_mask]))

        qty_invalid_mask = qty_numeric <= 0
        if qty_invalid_mask.sum() > 0:
            issues.append(f"Column 'quantity has {qty_invalid_mask.sum()} zero or negative value(s)")
    bad_row_sets.append(set(df.index[qty_invalid_mask]))

            # Check unit_price is positive

            price_numeric = pd.to_numeric(df["unit_price"], error="coerce")

            price_non_numeric_mask = price_numeric.isna()
            if price_non_numeric_mask.sum() > 0:
                issues.append(f"Column 'unit_price' has {price_non_numeric_mask.sum()} non-numeric value(s)")
                bad_row_sets.append(set())

            # Check status is acceptable value

            bad_status_mask = ~df["status"].str.lower().isin(VALID_STATUSES)
            if bad_status_mask.sum() > 0:
                issues.append(
                    f"Column 'status' has {bad_status_mask.sum()} invalid value(s): " f"{df.loc[bad_status_mask, 'status'].unique().tolist()}"
                )
            bad_row_sets.append(set(df.index[bad_status_mask]))

            all_bad_rows = set()
            for row_set in bad_row_sets:
                all_bad_rows.update(row_set)

                bad_rows_index = pd.Index(sorted(all_bad_rows))

                passed = len(issues) == 0

                print(f"\n[validate] {'PASSED' if passed else 'ISSUES FOUND'}")
                print(f"[validate] Total rows checked: {len(df)}")
                print(f"[validate] Rows with issues: {len(bad_row_index)}")
                if issues:
                    for issue in issues:
                        print(f"{issue}")

                return {
                    "passed": passed,
                    "issues": issues,
                    "bad_rows": bad_rows_index
                }
    def _is_blank(value) -> bool:
        if pd.isna(value):
            return True

        return str(value).strip() == ""
