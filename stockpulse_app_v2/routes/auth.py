from flask import Blueprint, request, jsonify, session

from db import get_db, query_one

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    conn = get_db()
    try:
        user = query_one(
            conn, "SELECT * FROM users WHERE LOWER(email)=%s AND password=%s", (email, password)
        )
    finally:
        conn.close()
    if user:
        session["logged_in"] = True
        session["email"] = user["email"]
        session["role"] = user["role"]
        return jsonify({"ok": True, "email": user["email"], "role": user["role"]})
    return jsonify({"ok": False, "error": "Incorrect email or password."}), 401


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/api/me")
def me():
    if not session.get("logged_in"):
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "email": session.get("email"), "role": session.get("role")})
