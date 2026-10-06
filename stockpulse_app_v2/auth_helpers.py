from flask import session


def require_login():
    return session.get("logged_in") is True


def current_role():
    return session.get("role")


def require_admin():
    return require_login() and current_role() == "admin"
