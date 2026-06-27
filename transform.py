import pandas as pd

def transform(clean_df: pd.DataFrame) -> dict:
    print("[transform] Computing aggregates...")

    if "revenue" not in clean_df.columns:
        raise ValueError("[transform] Missing 'revenue' column - run clean.py first")

    # Aggregate revenue by category

    revenue_by_category = (
        clean_df.groupby("category")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    revenue_by_category.columns = ["category", "total_revenue"]

    # Aggregate Monthly totals

    clean_df["year_month"] = clean_df["date"].dt.to_period("M").astype(str)
    monthly_totals = (
        clean_df.groupby("year_month")
        .agg(
            total_revenue=("revenue", "sum"),
            order_count=("order_id", "nunique"),
            total_quantity=("quantity", "sum")
        )
        .sort_index()
        .reset_index()
    )

    # Sort Top products by revenue

    # Grouping by product, sum revenue, takes the top 5

    top_products = (
        clean_df.groupby("product")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    top_products.columns = ["product", "total_revenue"]

    # Build the status breakdown

    status_breakdown = (
        clean_df.groupby("status")
        .agg(
            order_count=("order_id", "count"),
            total_revenue=("revenue", "sum")
        )
        .sort_values("total_revenue", ascending=False)
        .reset_index()
    )

    # Build customer summary

    customer_summary = (
        clean_df.groupby("customer_id")
        .agg(
            total_spend=("revenue", "sum"),
            order_count=("order_id", "nunique"),
            avg_order_value=("revenue", "mean")
        )
        .sort_values("total_spend", ascending=False)
        .reset_index()
    )

    print(f"[transform] Computed 5 aggregates from {len(clean_df)} clean rows")

    return {
        "revenue_by_category": revenue_by_catagory,
        "monthly_totals": monthly_totals,
        "top_products": top_products,
        "status_breakdown": status_breakdown,
        "customer_summary": customer_summary
    }
