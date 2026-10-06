from flask import Blueprint, request, jsonify

from db import get_db, query_one, execute
from auth_helpers import require_login

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/api/inventory/<int:product_id>/adjust", methods=["POST"])
def adjust_inventory(product_id):
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401
    delta = int(request.get_json(force=True).get("delta", 0))
    conn = get_db()
    try:
        row = query_one(conn, "SELECT stock FROM products WHERE id=%s", (product_id,))
        if row is None:
            return jsonify({"error": "Product not found"}), 404
        new_stock = max(0, row["stock"] + delta)
        execute(conn, "UPDATE products SET stock=%s WHERE id=%s", (new_stock, product_id))
        return jsonify({"id": product_id, "stock": new_stock})
    finally:
        conn.close()
