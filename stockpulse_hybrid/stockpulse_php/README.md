# StockPulse — Inventory & Sales Analytics Dashboard (PHP + Python hybrid edition)

A full-stack, real-time inventory and sales analytics dashboard.

- **Database layer:** PHP (plain PHP, no framework) — owns the MySQL connection, runs every
  query, and handles auth, products, sales, restocks, and inventory exactly as a normal PHP
  CRUD backend would.
- **Data manipulation layer:** Python (Flask + Pandas) — a small internal microservice that
  takes the raw rows PHP fetched and turns them into dashboard KPIs, the revenue trend, top
  products, category splits, and the category revenue/margin report.
- **Database:** MySQL
- **Frontend:** HTML/CSS/JavaScript + Chart.js (unchanged — same look, same features, same
  `/api/...` URLs; it has no idea Python is involved)
- **Features:** role-based login (Admin/Staff), dashboard KPIs & charts with a 7/30/90-day
  range switch, notification bell for low stock, product catalog (CRUD) with CSV bulk import,
  sales logging, a Purchases/Restock log, inventory stock adjustment, and category reports
  with CSV export.

## Why two backends?

Everything that's straightforward reading/writing of rows (login, products, sales, restocks,
inventory adjustments) stays in PHP — there's no real "manipulation" happening, just CRUD.

The Dashboard and Reports endpoints are different: they aggregate, group, and compute (revenue
trends, top-5 products, category margins). That's genuine data manipulation, so it's done in
Python with Pandas instead of hand-written SQL aggregation.

**How a Dashboard/Reports request flows now:**
1. Browser calls `GET /api/dashboard` — exactly as before.
2. `api/dashboard.php` checks the session is logged in, then runs two plain `SELECT * FROM
   products` / `SELECT * FROM sales` queries against MySQL. That's PHP's entire job here —
   fetch the raw rows.
3. PHP POSTs those raw rows as JSON to the Python service running on `http://127.0.0.1:5001`
   (see `analytics_client.php`).
4. `python_service/analytics_service.py` loads the rows into Pandas DataFrames, computes the
   KPIs/aggregates/margins, and returns them as JSON.
5. PHP relays that JSON straight back to the browser.

The two services talk over plain HTTP on localhost, using a shared secret header
(`X-Internal-Key`) so the Python service only accepts requests from this PHP app — it's not
meant to be reachable directly from a browser.

Every other endpoint (`/api/login`, `/api/products`, `/api/sales`, `/api/restocks`,
`/api/inventory/...`) is untouched PHP, same as before.

---

## Project structure

```
stockpulse/
├── stockpulse_php/
│   ├── config.php            Your MySQL credentials + Python service URL — edit this first
│   ├── db.php                One function: getDB() — opens the MySQL connection
│   ├── analytics_client.php  Sends raw rows to the Python service, returns its JSON
│   ├── setup.php             Run once — creates the database, tables, and sample data
│   ├── auth_helpers.php      Login/role check helper functions
│   ├── router.php            Only used by the PHP built-in dev server (see below)
│   ├── api/
│   │   ├── index.php         Routes each request to the right handler (like a switchboard)
│   │   ├── auth.php          login / logout / me
│   │   ├── products.php      Product CRUD + CSV bulk import
│   │   ├── sales.php         Log a sale, list sales
│   │   ├── restocks.php      Log a restock, list restocks
│   │   ├── inventory.php     Adjust stock
│   │   ├── dashboard.php     Fetches raw rows, hands off to Python, relays the result
│   │   └── reports.php       Fetches raw rows, hands off to Python, relays the result
│   └── public/
│       └── index.html        The frontend (loads in your browser)
└── python_service/
    ├── analytics_service.py  Flask app: /compute/dashboard and /compute/reports (Pandas)
    └── requirements.txt      flask, pandas
```

Every PHP file is short and does one job — `api/sales.php` only knows about sales,
`api/products.php` only knows about products, and so on. `api/index.php` is the only file
that "routes" a request to the right place, similar to how a receptionist directs visitors
to the right office. `api/dashboard.php` and `api/reports.php` are the only two that talk to
Python — everything else is pure PHP + MySQL.

---

## 1. Requirements

- **PHP 8.0+** with the `pdo_mysql` and `curl` extensions (both come bundled with PHP by
  default on most installs — XAMPP/WAMP/MAMP all include them)
- **MySQL Server 8.0+**
- **Python 3.9+** with `pip` (for the Dashboard/Reports analytics service)

### Easiest option: XAMPP (bundles both PHP and MySQL together)

If you don't already have PHP and MySQL installed separately, download **XAMPP**
(https://www.apachefriends.org/) — it installs PHP, MySQL, and a control panel in one go,
for Windows/Mac/Linux. Start the MySQL service from the XAMPP control panel, then follow
step 3 onward using the `php` command from the XAMPP install (or add it to your PATH).

### Or install them separately

- **Windows:** https://windows.php.net/download/ (PHP) + https://dev.mysql.com/downloads/installer/ (MySQL)
- **Mac:** `brew install php mysql` then `brew services start mysql`
- **Linux (Ubuntu/Debian):** `sudo apt install php-cli php-mysql mysql-server` then `sudo service mysql start`

Confirm PHP is installed:
```
php -v
```

---

## 2. Unzip the project and set your MySQL credentials

Open `config.php` in any text editor and fill in your MySQL username/password:

```php
define('DB_USER', 'root');
define('DB_PASSWORD', '');   // <-- your MySQL root password goes here
```

If you just installed MySQL and never set a root password, leave `DB_PASSWORD` blank.

---

## 3. Run the one-time setup

Open a terminal in the project folder and run:

```
php setup.php
```

You should see output like:
```
Database "stockpulse" ready.
Tables created (or already existed).
Seeded 2 demo users (admin@shop.com / staff@shop.com).
Seeded 16 sample products.
Seeded ~30 days of sample sales history.
Setup complete!
```

This creates the `stockpulse` database and all 4 tables automatically — you don't need to
write or run any SQL by hand. It's safe to run again later (it won't duplicate data).

---

## 4. Install and start the Python analytics service

In a **separate terminal**, from the project root:

```
cd python_service
pip install -r requirements.txt
python analytics_service.py
```

You should see `Running on http://127.0.0.1:5001`. Leave this terminal running — it's what
computes the Dashboard KPIs and Reports for the PHP app. If it's not running, `/api/dashboard`
and `/api/reports` will return a clear "Could not reach the Python analytics service" error
instead of crashing silently.

---

## 5. Start the PHP app

Back in your first terminal, from the `stockpulse_php/` folder:

```
php -S localhost:8000 -t public router.php
```

This starts PHP's built-in development server. Breaking that command down:
- `-S localhost:8000` — serve on your computer, port 8000
- `-t public` — serve static files (the frontend) from the `public/` folder
- `router.php` — a small script that sends anything starting with `/api/` to the PHP backend,
  and lets everything else load normally as a static file

Open **http://localhost:8000** in your browser. You now have two servers running:
`localhost:8000` (PHP, the app you actually browse to) and `127.0.0.1:5001` (Python, called
internally by PHP — you never visit this one in a browser).

---

## 6. Log in

- **Admin** — `admin@shop.com` / `admin123` (full access)
- **Staff** — `staff@shop.com` / `staff123` (can log sales & adjust stock, cannot add/edit/delete products)

---

## 7. Using the app

- **Dashboard** — KPIs, revenue trend (7/30/90-day switch), top products, category split,
  low-stock notification bell.
- **Products** — search, filter, add/edit/delete (admin only), CSV bulk import (admin only).
- **Sales** — log a sale.
- **Purchases** — record stock arriving from a supplier.
- **Inventory** — adjust stock with `-`/`+`/`+10`, or type an exact number and click "Set".
- **Reports** — category revenue/margin breakdown + CSV export.

---

## 8. Verifying your data in MySQL directly

Useful for screenshots in your project report:

```
mysql -u root -p
USE stockpulse;
SHOW TABLES;
SELECT * FROM products LIMIT 5;
```

---

## 9. Resetting the data

```
mysql -u root -p -e "DROP DATABASE stockpulse;"
php setup.php
```

---

## How a request flows through the app (useful for your report)

**A simple CRUD request** (products, sales, restocks, inventory, login) — pure PHP:
1. Browser loads `public/index.html`, which calls e.g. `fetch('/api/products')`.
2. PHP's dev server sees the path starts with `/api/` and hands it to `router.php`.
3. `router.php` includes `api/index.php`.
4. `api/index.php` matches the URL + HTTP method (`GET /products`) to a function —
   `products('GET')` inside `api/products.php`.
5. That function calls `getDB()` (from `db.php`) to get a MySQL connection, runs a query,
   and prints the result as JSON with `echo json_encode(...)`.
6. The browser receives the JSON and updates the page.

**A Dashboard/Reports request** — PHP for the database, Python for the manipulation:
1. Browser calls `fetch('/api/dashboard?days=30')`.
2. `api/index.php` routes it to `dashboard()` in `api/dashboard.php`, same as any other route.
3. `dashboard()` calls `getDB()`, runs two plain queries (`SELECT * FROM products`,
   `SELECT * FROM sales`) — no aggregation happens in SQL.
4. `dashboard()` calls `callAnalyticsService('/compute/dashboard', [...])`
   (`analytics_client.php`), which POSTs those raw rows as JSON to the Python service at
   `http://127.0.0.1:5001`.
5. `analytics_service.py` loads the rows into Pandas DataFrames, computes total revenue,
   the revenue-by-day trend, top 5 products, category split, and low-stock list, and
   returns them as JSON.
6. PHP receives that JSON and echoes it straight back to the browser.

This request → route → handler → database → (→ Python → Pandas →) → JSON response flow is
worth describing in your Implementation chapter's "Business Logic" section — it's a good
example of separating concerns: PHP for data access, Python for data manipulation.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not connect to MySQL database` | Check `DB_USER`/`DB_PASSWORD` in `config.php` match your actual MySQL login. Make sure MySQL is running. |
| `Could not reach the Python analytics service` (on Dashboard/Reports only) | The Python service isn't running. Open a terminal, `cd python_service`, and run `python analytics_service.py`. Leave it running alongside the PHP server. |
| `php: command not found` | PHP isn't installed or isn't on your PATH — see step 1. |
| `Class "PDO" not found` | Your PHP install is missing the `pdo_mysql` extension. On Ubuntu: `sudo apt install php-mysql`. |
| `curl error` / cURL not found | Your PHP install is missing the `curl` extension. On Ubuntu: `sudo apt install php-curl`, then restart the PHP server. |
| `ModuleNotFoundError: No module named 'flask'` or `'pandas'` | Run `pip install -r requirements.txt` inside `python_service/` before starting the service. |
| Blank page / nothing loads | Make sure you ran the server with `-t public router.php` exactly as shown — without `router.php`, `/api/` requests won't be routed. |
| `Address already in use` on port 8000 | Something else is using that port. Use a different one: `php -S localhost:8080 -t public router.php`, then visit `http://localhost:8080`. |
| `Address already in use` on port 5001 | Something else is using that port, or the Python service is already running elsewhere. Stop the other process, or edit the port in `analytics_service.py`'s `app.run(...)` line and in `PYTHON_SERVICE_URL` in `config.php` to match. |
| Changes to PHP files don't show up | PHP's built-in server reloads each file on every request automatically — just refresh your browser. No restart needed unless you edited `router.php` or `config.php`. |
| Changes to `analytics_service.py` don't show up | Stop the Python service (Ctrl+C) and restart it — Flask's dev server auto-reloads on save, but a manual restart guarantees it. |
