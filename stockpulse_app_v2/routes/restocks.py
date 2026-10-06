from datetime import datetime

from flask import Blueprint, request, jsonify

from db import get_db, query_all, query_one, execute
from auth_helpers import require_login

restocks_bp = Blueprint("restocks", __name__)


@restocks_bp.route("/api/restocks", methods=["GET", "POST"])
def restocks():
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401
    conn = get_db()
    try:
        if request.method == "GET":
            rows = query_all(conn, """
                SELECT restocks.id, restocks.restock_date AS date, restocks.qty, restocks.note,
                       products.name AS product_name, products.id AS product_id
                FROM restocks JOIN products ON products.id = restocks.product_id
                ORDER BY restocks.restock_date DESC, restocks.id DESC LIMIT 200
            """)
            return jsonify(rows)

        data = request.get_json(force=True)
        product_id = int(data["product_id"])
        qty = int(data["qty"])
        note = (data.get("note") or "").strip()
        prod = query_one(conn, "SELECT * FROM products WHERE id=%s", (product_id,))
        if prod is None:
            return jsonify({"error": "Product not found"}), 404
        if qty <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
        today = datetime.now().date().isoformat()
        execute(conn, "UPDATE products SET stock = stock + %s WHERE id=%s", (qty, product_id))
        restock_id = execute(
            conn,
            "INSERT INTO restocks (restock_date, product_id, qty, note) VALUES (%s,%s,%s,%s)",
            (today, product_id, qty, note),
        )
        return jsonify({"id": restock_id, "date": today, "product_id": product_id,
                         "product_name": prod["name"], "qty": qty, "note": note}), 201
    finally:
        conn.close()
