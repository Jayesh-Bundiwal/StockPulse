from flask import Blueprint, request, jsonify

from db import get_db, query_all, query_one, execute
from auth_helpers import require_login, require_admin

products_bp = Blueprint("products", __name__)

SELECT_PRODUCT = "SELECT id, name, sku, category, price, cost, stock, threshold_qty AS threshold FROM products"


@products_bp.route("/api/products", methods=["GET", "POST"])
def products():
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401
    conn = get_db()
    try:
        if request.method == "GET":
            rows = query_all(conn, SELECT_PRODUCT + " ORDER BY name")
            return jsonify(rows)

        if not require_admin():
            return jsonify({"error": "Only admin accounts can add products"}), 403

        data = request.get_json(force=True)
        new_id = execute(
            conn,
            "INSERT INTO products (name, sku, category, price, cost, stock, threshold_qty) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (data["name"], data["sku"], data["category"], float(data["price"]), float(data["cost"]),
             int(data["stock"]), int(data["threshold"])),
        )
        row = query_one(conn, SELECT_PRODUCT + " WHERE id=%s", (new_id,))
        return jsonify(row), 201
    finally:
        conn.close()


@products_bp.route("/api/products/bulk", methods=["POST"])
def products_bulk():
    if not require_admin():
        return jsonify({"error": "Only admin accounts can import products"}), 403
    rows_in = request.get_json(force=True).get("products", [])
    conn = get_db()
    try:
        inserted, updated, errors = 0, 0, []
        for r in rows_in:
            try:
                name = r["name"].strip()
                sku = r["sku"].strip()
                category = (r.get("category") or "Groceries").strip() or "Groceries"
                price = float(r.get("price", 0))
                cost = float(r.get("cost", 0))
                stock = int(r.get("stock", 0))
                threshold = int(r.get("threshold", 10))
                existing = query_one(conn, "SELECT id FROM products WHERE sku=%s", (sku,))
                if existing:
                    execute(
                        conn,
                        "UPDATE products SET name=%s, category=%s, price=%s, cost=%s, stock=%s, threshold_qty=%s WHERE sku=%s",
                        (name, category, price, cost, stock, threshold, sku),
                    )
                    updated += 1
                else:
                    execute(
                        conn,
                        "INSERT INTO products (name, sku, category, price, cost, stock, threshold_qty) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (name, sku, category, price, cost, stock, threshold),
                    )
                    inserted += 1
            except Exception as e:
                errors.append(str(e))
        return jsonify({"inserted": inserted, "updated": updated, "errors": errors})
    finally:
        conn.close()


@products_bp.route("/api/products/<int:product_id>", methods=["PUT", "DELETE"])
def product_detail(product_id):
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401
    if not require_admin():
        return jsonify({"error": "Only admin accounts can edit or delete products"}), 403
    conn = get_db()
    try:
        if request.method == "DELETE":
            execute(conn, "DELETE FROM products WHERE id=%s", (product_id,))
            return jsonify({"ok": True})

        data = request.get_json(force=True)
        execute(
            conn,
            "UPDATE products SET name=%s, sku=%s, category=%s, price=%s, cost=%s, stock=%s, threshold_qty=%s WHERE id=%s",
            (data["name"], data["sku"], data["category"], float(data["price"]), float(data["cost"]),
             int(data["stock"]), int(data["threshold"]), product_id),
        )
        row = query_one(conn, SELECT_PRODUCT + " WHERE id=%s", (product_id,))
        return jsonify(row)
    finally:
        conn.close()
