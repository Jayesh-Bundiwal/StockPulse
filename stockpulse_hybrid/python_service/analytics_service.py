"""
StockPulse — Python Analytics Microservice
============================================
This is the "data manipulation" half of StockPulse.

PHP (stockpulse_php/) owns the database: it connects to MySQL, runs the
queries, and hands the raw product/sale rows to this service as JSON.
This service never touches MySQL directly — it only receives rows,
crunches them with Pandas, and returns the computed result as JSON.

Two endpoints, one per PHP caller:
  POST /compute/dashboard  <- api/dashboard.php
  POST /compute/reports    <- api/reports.php

Run:
    pip install -r requirements.txt
    python analytics_service.py
Listens on http://127.0.0.1:5001 (localhost only — this is an internal
service, not meant to be reached directly from the browser).
"""
from datetime import datetime, timedelta

import os
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)

# Must match INTERNAL_SERVICE_KEY in stockpulse_php/config.php.
# Simple shared-secret check: only the PHP app (server-to-server, on the
# same machine) is meant to call this service.
INTERNAL_SERVICE_KEY = os.getenv("STOCKPULSE_INTERNAL_KEY")
# For local development only: fall back to a default if the env var is not set.
if INTERNAL_SERVICE_KEY is None:
    INTERNAL_SERVICE_KEY = "stockpulse-internal-key-change-me"


@app.before_request
def check_internal_key():
    if request.headers.get("X-Internal-Key") != INTERNAL_SERVICE_KEY:
        return jsonify({"error": "Forbidden — missing/invalid internal service key"}), 403


def _frames(payload: dict):
    """Turn the raw JSON rows PHP sent into pandas DataFrames with the right dtypes."""
    products = pd.DataFrame(payload.get("products", []))
    sales = pd.DataFrame(payload.get("sales", []))

    if not products.empty:
        products["price"] = products["price"].astype(float)
        products["cost"] = products["cost"].astype(float)
        products["stock"] = products["stock"].astype(int)
        products["threshold_qty"] = products["threshold_qty"].astype(int)

    if not sales.empty:
        sales["sale_date"] = pd.to_datetime(sales["sale_date"]).dt.normalize()
        sales["qty"] = sales["qty"].astype(int)
        sales["revenue"] = sales["revenue"].astype(float)

    return products, sales


@app.route("/compute/dashboard", methods=["POST"])
def compute_dashboard():
    payload = request.get_json(force=True) or {}
    days_window = max(1, min(int(payload.get("days_window", 30)), 365))
    today = pd.to_datetime(payload.get("today") or datetime.now().strftime("%Y-%m-%d")).normalize()
    cutoff = today - timedelta(days=days_window - 1)

    products, sales = _frames(payload)
    in_window = sales[sales["sale_date"] >= cutoff] if not sales.empty else sales

    total_revenue = float(in_window["revenue"].sum()) if not in_window.empty else 0.0
    orders_total = int(len(in_window))

    today_rows = sales[sales["sale_date"] == today] if not sales.empty else sales
    today_revenue = float(today_rows["revenue"].sum()) if not today_rows.empty else 0.0
    today_count = int(len(today_rows))

    if not products.empty:
        inventory_value = float((products["stock"] * products["cost"]).sum())
        total_units = int(products["stock"].sum())
        sku_count = int(len(products))

        low_stock = products[products["stock"] <= products["threshold_qty"]].copy()
        # Avoid division-by-zero when threshold_qty is 0: compute ratio only where threshold > 0
        safe = low_stock["threshold_qty"] > 0
        low_stock.loc[safe, "ratio"] = low_stock.loc[safe, "stock"].div(low_stock.loc[safe, "threshold_qty"])
        low_stock.loc[~safe, "ratio"] = 0.0
        low_stock = low_stock.sort_values("ratio").drop(columns=["ratio"])
        low_stock = low_stock.rename(columns={"threshold_qty": "threshold"})
        low_stock_products = low_stock.to_dict("records")
    else:
        inventory_value, total_units, sku_count, low_stock_products = 0.0, 0, 0, []

    # Revenue by day across the whole window, zero-filled for days with no sales
    daily = (
        in_window.groupby(in_window["sale_date"].dt.strftime("%Y-%m-%d"))["revenue"].sum()
        if not in_window.empty else pd.Series(dtype=float)
    )
    revenue_by_day = []
    for i in range(days_window - 1, -1, -1):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        revenue_by_day.append({"date": day, "revenue": float(daily.get(day, 0.0))})

    # Top products & category revenue — every product/category included, zero-filled
    if not products.empty:
        rev_by_product = (
            in_window.groupby("product_id")["revenue"].sum()
            if not in_window.empty else pd.Series(dtype=float)
        )
        merged = products.copy()
        merged["revenue"] = merged["id"].map(rev_by_product).fillna(0.0).astype(float)

        top_products = (
            merged.sort_values("revenue", ascending=False)
            .head(5)[["name", "revenue"]]
            .to_dict("records")
        )
        category_revenue = (
            merged.groupby("category")["revenue"].sum()
            .sort_values(ascending=False)
            .reset_index()
            .to_dict("records")
        )
    else:
        top_products, category_revenue = [], []

    return jsonify({
        "days_window": days_window,
        "total_revenue": total_revenue,
        "orders_total": orders_total,
        "today_revenue": today_revenue,
        "today_count": today_count,
        "inventory_value": inventory_value,
        "total_units": total_units,
        "sku_count": sku_count,
        "low_stock": len(low_stock_products),
        "low_stock_products": low_stock_products,
        "revenue_by_day": revenue_by_day,
        "top_products": top_products,
        "category_revenue": category_revenue,
    })


@app.route("/compute/reports", methods=["POST"])
def compute_reports():
    payload = request.get_json(force=True) or {}
    days_window = max(1, min(int(payload.get("days_window", 30)), 3650))
    today = pd.to_datetime(payload.get("today") or datetime.now().strftime("%Y-%m-%d")).normalize()
    cutoff = today - timedelta(days=days_window - 1)

    products, sales = _frames(payload)
    if products.empty:
        return jsonify([])

    in_window = sales[sales["sale_date"] >= cutoff] if not sales.empty else sales

    if not in_window.empty:
        merged = in_window.merge(
            products[["id", "category", "cost"]],
            left_on="product_id", right_on="id", how="left",
        )
        merged["line_cost"] = merged["qty"] * merged["cost"]
        grouped = merged.groupby("category").agg(
            units=("qty", "sum"), revenue=("revenue", "sum"), cost=("line_cost", "sum")
        )
    else:
        grouped = pd.DataFrame(columns=["units", "revenue", "cost"])

    # Every category present, even ones with zero sales in the window
    all_categories = products["category"].unique()
    grouped = grouped.reindex(all_categories, fill_value=0)

    result = []
    for category, row in grouped.sort_values("revenue", ascending=False).iterrows():
        revenue = float(row["revenue"])
        cost = float(row["cost"])
        margin = (revenue - cost) / revenue * 100 if revenue > 0 else 0.0
        result.append({
            "category": category,
            "units": int(row["units"]),
            "revenue": revenue,
            "margin": margin,
        })
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
