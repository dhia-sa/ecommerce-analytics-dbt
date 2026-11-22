"""
Export a small, read-only copy of the tables the dashboard needs into
dashboard/data/dashboard.duckdb, so the hosted dashboard (Streamlit Community
Cloud) can run without the raw CSVs or a full dbt build.

Run from the project root after `dbt build`, then commit the file:
    python scripts/export_dashboard_db.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT / "ecommerce.duckdb"
TARGET_DB = ROOT / "dashboard" / "data" / "dashboard.duckdb"

# table -> select list (only the columns dashboard/app.py queries)
TABLES = {
    "core.fct_orders": (
        "order_date, is_valid_order, item_count, items_value, is_late_delivery, review_score"
    ),
    "analytics.mart_monthly_sales": "*",
    "analytics.mart_delivery_performance": "*",
    "analytics.mart_customer_rfm": "*",
    "analytics.mart_cohort_retention": "*",
    "analytics.mart_seller_performance": "*",
}


def main() -> None:
    if not SOURCE_DB.exists():
        raise SystemExit(f"{SOURCE_DB} not found: run `dbt build` first.")

    TARGET_DB.parent.mkdir(parents=True, exist_ok=True)
    TARGET_DB.unlink(missing_ok=True)

    con = duckdb.connect(str(TARGET_DB))
    con.execute(f"attach '{SOURCE_DB.as_posix()}' as src (read_only)")
    for table, columns in TABLES.items():
        schema = table.split(".")[0]
        con.execute(f"create schema if not exists {schema}")
        con.execute(f"create table {table} as select {columns} from src.{table}")
        rows = con.execute(f"select count(*) from {table}").fetchall()[0][0]
        print(f"{table:<40} {rows:>8,} rows")
    con.execute("detach src")
    con.execute("checkpoint")
    con.close()

    print(f"Wrote {TARGET_DB.relative_to(ROOT)} ({TARGET_DB.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
