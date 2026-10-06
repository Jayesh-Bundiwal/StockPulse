# StockPulse — Inventory & Sales Analytics Dashboard (v2 — MySQL edition)

A full-stack, real-time inventory and sales analytics dashboard.

- **Backend:** Python + Flask, organized into modules (routes, config, database layer)
- **Database:** **MySQL** (upgraded from the earlier SQLite version)
- **Frontend:** HTML/CSS/JavaScript + Chart.js (served by Flask, no separate build step)
- **Features:** role-based login (Admin/Staff), dashboard KPIs & charts with a 7/30/90-day
  range switch, notification bell for low stock, product catalog (CRUD) with CSV bulk import,
  sales logging, a Purchases/Restock log, inventory stock adjustment, and category reports
  with CSV export.

## What changed from the SQLite version

```
Before (v1)                      After (v2)
------------------------------    ------------------------------
app.py (everything, ~470 lines)  app.py               (Flask app + blueprint registration)
                                  config.py            (DB settings)
                                  db.py                (MySQL connection + schema + seed data)
                                  auth_helpers.py       (login/role helper functions)
                                  routes/
                                    auth.py             (login, logout, session check)
                                    products.py          (CRUD + CSV bulk import)
                                    sales.py             (sales log)
                                    restocks.py          (purchases/restock log)
                                    inventory.py         (stock adjust)
                                    dashboard.py          (KPIs, charts, low-stock)
                                    reports.py            (category breakdown)
sqlite3 (file-based)              MySQL (real database server)
```

The frontend (`static/index.html`) is unchanged — the API still returns the exact same JSON
shape, so nothing on the UI side needed to change.

---

## 1. Requirements

- **Python 3.9+**
- **MySQL Server 8.0+** (this is the new requirement — the SQLite version needed nothing
  extra; MySQL needs an actual database server running on your machine)

### Installing MySQL

- **Windows:** download MySQL Installer from https://dev.mysql.com/downloads/installer/ —
  choose "MySQL Server" during setup, and remember the **root password** you set.
- **Mac:** `brew install mysql` then `brew services start mysql`
- **Linux (Ubuntu/Debian):** `sudo apt install mysql-server` then `sudo service mysql start`

After installing, confirm it's running:
```
mysql -u root -p
```
(enter the root password you set). If you get a `mysql>` prompt, it's working — type `exit`
to leave.

---

## 2. Unzip the project

```
stockpulse_app/
├── app.py
├── config.py
├── db.py
├── auth_helpers.py
├── requirements.txt
├── README.md
├── routes/
│   ├── auth.py
│   ├── products.py
│   ├── sales.py
│   ├── restocks.py
│   ├── inventory.py
│   ├── dashboard.py
│   └── reports.py
└── static/
    └── index.html
```

---

## 3. Set your MySQL credentials

The app reads database credentials from environment variables (defaults assume a local
`root` user with **no password**, which usually isn't your case — set these first):

- **Windows (cmd):**
  ```
  set DB_USER=root
  set DB_PASSWORD=your_mysql_root_password
  ```
- **Mac/Linux:**
  ```
  export DB_USER=root
  export DB_PASSWORD=your_mysql_root_password
  ```

You don't need to create the `stockpulse` database yourself — the app creates it
automatically on first run (`CREATE DATABASE IF NOT EXISTS`).

*(Optional — you can also override `DB_HOST`, `DB_PORT`, and `DB_NAME` the same way if
your setup differs from the defaults: `localhost`, `3306`, `stockpulse`.)*

---

## 4. Install dependencies

Open a terminal in the project folder:

```
python -m venv venv
```
Activate it — **Windows:** `venv\Scripts\activate` · **Mac/Linux:** `source venv/bin/activate`

```
pip install -r requirements.txt
```

This installs Flask and PyMySQL (the MySQL driver).

---

## 5. Run the application

Make sure your MySQL server is running (step 1), then, in the **same terminal** where you
set the `DB_PASSWORD` environment variable (step 3):

```
python app.py
```

First run creates the `stockpulse` database, all four tables, and seeds 16 sample products
plus ~30 days of sample sales — automatically, no manual SQL needed.

Open **http://127.0.0.1:5000** and log in:

- **Admin** — `admin@shop.com` / `admin123` (full access)
- **Staff** — `staff@shop.com` / `staff123` (can log sales & adjust stock, cannot add/edit/delete products)

---

## 6. Using the app

- **Dashboard** — KPIs, revenue trend (7/30/90-day switch), top products, category split,
  low-stock notification bell.
- **Products** — search, filter, add/edit/delete (admin only), CSV bulk import (admin only).
- **Sales** — log a sale.
- **Purchases** — record stock arriving from a supplier.
- **Inventory** — adjust stock with `-`/`+`/`+10`, or type an exact number and click "Set".
- **Reports** — category revenue/margin breakdown + CSV export.

---

## 7. Verifying your data in MySQL directly

If you want to see the raw tables (useful for your project report / DB screenshots):

```
mysql -u root -p
USE stockpulse;
SHOW TABLES;
SELECT * FROM products LIMIT 5;
```

---

## 8. Resetting the data

To start over with fresh seed data, drop the database and let the app recreate it:

```
mysql -u root -p -e "DROP DATABASE stockpulse;"
```
Then run `python app.py` again.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Access denied for user 'root'@'localhost'` | Your `DB_PASSWORD` env var doesn't match your actual MySQL root password. Reset it: `mysql -u root -p` then `ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';` |
| `Can't connect to MySQL server` | MySQL isn't running. Start it (`brew services start mysql`, `sudo service mysql start`, or via Windows Services). |
| `ModuleNotFoundError: No module named 'pymysql'` | Run `pip install -r requirements.txt` again — make sure your virtual environment is activated. |
| Works, but env vars seem ignored on Windows | `set` only applies to the current terminal session — if you open a new terminal, set them again before running `python app.py`. |
| Want a permanent fix instead of `set`/`export` every time | Set the variables in your OS's system environment variables panel instead. |

---

## Project structure reference (for your report)

This modular layout — Flask blueprints per feature area, a dedicated `config.py` for
settings, and a `db.py` data-access layer — is the kind of structure worth describing in
your Implementation chapter (Business Logic / Form & Report Layouts sections), and the
MySQL schema (4 tables: `products`, `sales`, `users`, `restocks`, with foreign keys) is a
direct match for a Database/ER diagram in your Design chapter.
