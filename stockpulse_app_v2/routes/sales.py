from datetime import datetime

from flask import Blueprint, request, jsonify

from db import get_db, query_all, query_one, execute
from auth_helpers import require_login

sales_bp = Blueprint("sales", __name__)


@sales_bp.route("/api/sales", methods=["GET", "POST"])
def sales():
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401
    conn = get_db()
    try:
        if request.method == "GET":
            rows = query_all(conn, """
                SELECT sales.id, sales.sale_date AS date, sales.qty, sales.revenue,
                       products.name AS product_name, products.id AS product_id
                FROM sales JOIN products ON products.id = sales.product_id
                ORDER BY sales.sale_date DESC, sales.id DESC LIMIT 200
            """)
            return jsonify(rows)

        data = request.get_json(force=True)
        product_id = int(data["product_id"])
        qty = int(data["qty"])
        prod = query_one(conn, "SELECT * FROM products WHERE id=%s", (product_id,))
        if prod is None:
            return jsonify({"error": "Product not found"}), 404
        if qty > prod["stock"]:
            return jsonify({"error": f"Only {prod['stock']} in stock"}), 400
        revenue = qty * prod["price"]
        today = datetime.now().date().isoformat()
        execute(conn, "UPDATE products SET stock = stock - %s WHERE id=%s", (qty, product_id))
        sale_id = execute(
            conn,
            "INSERT INTO sales (sale_date, product_id, qty, revenue) VALUES (%s,%s,%s,%s)",
            (today, product_id, qty, revenue),
        )
        return jsonify({"id": sale_id, "date": today, "product_id": product_id,
                         "product_name": prod["name"], "qty": qty, "revenue": revenue}), 201
    finally:
        conn.close()
