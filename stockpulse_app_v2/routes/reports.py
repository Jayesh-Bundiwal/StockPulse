from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

from db import get_db, query_all
from auth_helpers import require_login

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/api/reports")
def reports():
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401
    days_window = int(request.args.get("days", 30))
    days_window = max(1, min(days_window, 3650))
    cutoff = (datetime.now().date() - timedelta(days=days_window - 1)).isoformat()
    conn = get_db()
    try:
        rows = query_all(conn, """
            SELECT products.category AS category,
                   COALESCE(SUM(CASE WHEN sales.sale_date>=%s THEN sales.qty END),0) AS units,
                   COALESCE(SUM(CASE WHEN sales.sale_date>=%s THEN sales.revenue END),0) AS revenue,
                   COALESCE(SUM(CASE WHEN sales.sale_date>=%s THEN sales.qty*products.cost END),0) AS cost
            FROM products LEFT JOIN sales ON sales.product_id = products.id
            GROUP BY products.category ORDER BY revenue DESC
        """, (cutoff, cutoff, cutoff))
        result = []
        for r in rows:
            margin = ((r["revenue"] - r["cost"]) / r["revenue"] * 100) if r["revenue"] > 0 else 0
            result.append({"category": r["category"], "units": r["units"], "revenue": r["revenue"], "margin": margin})
        return jsonify(result)
    finally:
        conn.close()
