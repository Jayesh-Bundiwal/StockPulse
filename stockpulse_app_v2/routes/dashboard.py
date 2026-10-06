from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

from db import get_db, query_all, query_one
from auth_helpers import require_login

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard")
def dashboard():
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401
    days_window = int(request.args.get("days", 30))
    days_window = max(1, min(days_window, 365))
    conn = get_db()
    try:
        today = datetime.now().date()
        cutoff = (today - timedelta(days=days_window - 1)).isoformat()

        total_revenue = query_one(
            conn, "SELECT COALESCE(SUM(revenue),0) AS v FROM sales WHERE sale_date>=%s", (cutoff,)
        )["v"]
        orders_total = query_one(
            conn, "SELECT COUNT(*) AS v FROM sales WHERE sale_date>=%s", (cutoff,)
        )["v"]
        today_row = query_one(
            conn, "SELECT COALESCE(SUM(revenue),0) AS rev, COUNT(*) AS cnt FROM sales WHERE sale_date=%s",
            (today.isoformat(),)
        )
        today_revenue, today_count = today_row["rev"], today_row["cnt"]
        inv_row = query_one(
            conn, "SELECT COALESCE(SUM(stock*cost),0) AS val, COALESCE(SUM(stock),0) AS units, COUNT(*) AS skus FROM products"
        )
        inventory_value, total_units, sku_count = inv_row["val"], inv_row["units"], inv_row["skus"]
        low_stock_rows = query_all(
            conn,
            "SELECT id, name, sku, category, price, cost, stock, threshold_qty AS threshold FROM products "
            "WHERE stock <= threshold_qty ORDER BY (stock / threshold_qty) ASC"
        )

        revenue_by_day = []
        for d in range(days_window - 1, -1, -1):
            day = (today - timedelta(days=d)).isoformat()
            rev = query_one(conn, "SELECT COALESCE(SUM(revenue),0) AS v FROM sales WHERE sale_date=%s", (day,))["v"]
            revenue_by_day.append({"date": day, "revenue": rev})

        top_products = query_all(conn, """
            SELECT products.name AS name, COALESCE(SUM(CASE WHEN sales.sale_date>=%s THEN sales.revenue END),0) AS revenue
            FROM products LEFT JOIN sales ON sales.product_id = products.id
            GROUP BY products.id, products.name ORDER BY revenue DESC LIMIT 5
        """, (cutoff,))

        category_revenue = query_all(conn, """
            SELECT products.category AS category, COALESCE(SUM(CASE WHEN sales.sale_date>=%s THEN sales.revenue END),0) AS revenue
            FROM products LEFT JOIN sales ON sales.product_id = products.id
            GROUP BY products.category ORDER BY revenue DESC
        """, (cutoff,))

        return jsonify({
            "days_window": days_window,
            "total_revenue": total_revenue,
            "orders_total": orders_total,
            "today_revenue": today_revenue,
            "today_count": today_count,
            "inventory_value": inventory_value,
            "total_units": total_units,
            "sku_count": sku_count,
            "low_stock": len(low_stock_rows),
            "low_stock_products": low_stock_rows,
            "revenue_by_day": revenue_by_day,
            "top_products": top_products,
            "category_revenue": category_revenue,
        })
    finally:
        conn.close()
