import random
from datetime import datetime, timedelta

import pymysql
import pymysql.cursors

from config import DB_CONFIG

SEED_USERS = [
    ("admin@shop.com", "admin123", "admin"),
    ("staff@shop.com", "staff123", "staff"),
]

SEED_PRODUCTS = [
    ("Amul Butter 500g", "DA-B5", "Dairy", 290, 240, 22, 10),
    ("Basmati Rice 5kg", "GR-BR5", "Groceries", 650, 480, 45, 10),
    ("Britannia Marie Gold", "SN-BMG", "Snacks", 30, 21, 90, 15),
    ("Coca Cola 1.25L", "BV-CC1", "Beverages", 75, 55, 55, 20),
    ("Colgate Toothpaste 200g", "PC-CT2", "Personal Care", 145, 110, 50, 15),
    ("Dark Fantasy Choco Fills", "SN-DFC", "Snacks", 90, 68, 4, 10),
    ("Dove Soap 100g", "PC-DS1", "Personal Care", 62, 45, 80, 20),
    ("Head & Shoulders Shampoo 340ml", "PC-HS3", "Personal Care", 340, 265, 12, 10),
    ("Lays Classic 52g", "SN-LC5", "Snacks", 20, 13, 200, 30),
    ("Milk 1L Full Cream", "DA-M1", "Dairy", 68, 55, 120, 20),
    ("Nescafe Classic 100g", "BV-NC1", "Beverages", 320, 245, 25, 10),
    ("Paneer 200g", "DA-P2", "Dairy", 95, 72, 6, 15),
    ("Sunflower Oil 1L", "GR-SO1", "Groceries", 180, 140, 60, 15),
    ("Toor Dal 1kg", "GR-TD1", "Groceries", 165, 130, 3, 10),
    ("Tropicana Orange 1L", "BV-T01", "Beverages", 120, 90, 18, 10),
    ("Whole Wheat Flour 10kg", "GR-WF10", "Groceries", 480, 360, 8, 10),
]


def _connect(with_database=True):
    kwargs = dict(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )
    if with_database:
        kwargs["database"] = DB_CONFIG["database"]
    return pymysql.connect(**kwargs)


def get_db():
    """Return a live MySQL connection scoped to the stockpulse database."""
    return _connect(with_database=True)


def query_all(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def query_one(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(conn, sql, params=None):
    """Run an INSERT/UPDATE/DELETE, commit, and return lastrowid (for INSERTs)."""
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid


def executemany(conn, sql, seq_of_params):
    with conn.cursor() as cur:
        cur.executemany(sql, seq_of_params)
        conn.commit()


def init_db():
    """Create the database (if missing), tables, and seed data. Safe to call every run."""
    # Step 1: make sure the database itself exists.
    bootstrap = _connect(with_database=False)
    try:
        with bootstrap.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        bootstrap.commit()
    finally:
        bootstrap.close()

    # Step 2: connect to the actual database and create tables.
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(150) NOT NULL,
                    sku VARCHAR(30) UNIQUE NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    price DOUBLE NOT NULL,
                    cost DOUBLE NOT NULL,
                    stock INT NOT NULL,
                    threshold_qty INT NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'staff'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    sale_date VARCHAR(10) NOT NULL,
                    product_id INT NOT NULL,
                    qty INT NOT NULL,
                    revenue DOUBLE NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    INDEX idx_sales_date (sale_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS restocks (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    restock_date VARCHAR(10) NOT NULL,
                    product_id INT NOT NULL,
                    qty INT NOT NULL,
                    note VARCHAR(255),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        conn.commit()

        # Seed users.
        if query_one(conn, "SELECT COUNT(*) AS c FROM users")["c"] == 0:
            executemany(
                conn,
                "INSERT INTO users (email, password, role) VALUES (%s,%s,%s)",
                SEED_USERS,
            )

        # Seed products.
        if query_one(conn, "SELECT COUNT(*) AS c FROM products")["c"] == 0:
            executemany(
                conn,
                "INSERT INTO products (name, sku, category, price, cost, stock, threshold_qty) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                SEED_PRODUCTS,
            )

        # Seed ~30 days of sales history.
        if query_one(conn, "SELECT COUNT(*) AS c FROM sales")["c"] == 0:
            products = query_all(conn, "SELECT id, price FROM products")
            product_ids = [p["id"] for p in products]
            prices = {p["id"]: p["price"] for p in products}
            today = datetime.now().date()
            rows = []
            for d in range(29, -1, -1):
                day = today - timedelta(days=d)
                orders = 3 + random.randint(0, 5)
                if d <= 1:
                    orders += 4
                if d in (11, 12):
                    orders += 5
                for _ in range(orders):
                    pid = random.choice(product_ids)
                    qty = random.randint(1, 4)
                    rows.append((day.isoformat(), pid, qty, qty * prices[pid]))
            executemany(
                conn,
                "INSERT INTO sales (sale_date, product_id, qty, revenue) VALUES (%s,%s,%s,%s)",
                rows,
            )
    finally:
        conn.close()
