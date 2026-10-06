# StockPulse — Inventory & Sales Analytics Dashboard (PHP + MySQL edition)

A full-stack, real-time inventory and sales analytics dashboard.

- **Backend:** PHP (plain PHP, no framework — just files you can read top to bottom)
- **Database:** MySQL
- **Frontend:** HTML/CSS/JavaScript + Chart.js (unchanged from earlier versions — same look, same features)
- **Features:** role-based login (Admin/Staff), dashboard KPIs & charts with a 7/30/90-day
  range switch, notification bell for low stock, product catalog (CRUD) with CSV bulk import,
  sales logging, a Purchases/Restock log, inventory stock adjustment, and category reports
  with CSV export.

## Why PHP instead of Flask?

Same app, same database schema, same features — just written in PHP instead of Python, since
that's the stack you're more comfortable reading and explaining. Nothing about how the app
*works* changed; only the language it's written in.

---

## Project structure

```
stockpulse_php/
├── config.php          Your MySQL credentials — edit this first
├── db.php              One function: getDB() — opens the MySQL connection
├── setup.php           Run once — creates the database, tables, and sample data
├── auth_helpers.php     Login/role check helper functions
├── router.php            Only used by the PHP built-in dev server (see below)
├── api/
│   ├── index.php         Routes each request to the right handler (like a switchboard)
│   ├── auth.php           login / logout / me
│   ├── products.php       Product CRUD + CSV bulk import
│   ├── sales.php          Log a sale, list sales
│   ├── restocks.php       Log a restock, list restocks
│   ├── inventory.php      Adjust stock
│   ├── dashboard.php      KPIs, charts, low-stock alerts
│   └── reports.php        Category revenue/margin report
└── public/
    └── index.html         The frontend (loads in your browser)
```

Every PHP file is short and does one job — `api/sales.php` only knows about sales,
`api/products.php` only knows about products, and so on. `api/index.php` is the only file
that "routes" a request to the right place, similar to how a receptionist directs visitors
to the right office.

---

## 1. Requirements

- **PHP 8.0+** with the `pdo_mysql` extension (this comes bundled with PHP by default on
  most installs — XAMPP/WAMP/MAMP all include it)
- **MySQL Server 8.0+**

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

## 4. Start the app

```
php -S localhost:8000 -t public router.php
```

This starts PHP's built-in development server. Breaking that command down:
- `-S localhost:8000` — serve on your computer, port 8000
- `-t public` — serve static files (the frontend) from the `public/` folder
- `router.php` — a small script that sends anything starting with `/api/` to the PHP backend,
  and lets everything else load normally as a static file

Open **http://localhost:8000** in your browser.

---

## 5. Log in

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

Useful for screenshots in your project report:

```
mysql -u root -p
USE stockpulse;
SHOW TABLES;
SELECT * FROM products LIMIT 5;
```

---

## 8. Resetting the data

```
mysql -u root -p -e "DROP DATABASE stockpulse;"
php setup.php
```

---

## How a request flows through the app (useful for your report)

1. Browser loads `public/index.html`, which calls e.g. `fetch('/api/products')`.
2. PHP's dev server sees the path starts with `/api/` and hands it to `router.php`.
3. `router.php` includes `api/index.php`.
4. `api/index.php` matches the URL + HTTP method (`GET /products`) to a function —
   `products('GET')` inside `api/products.php`.
5. That function calls `getDB()` (from `db.php`) to get a MySQL connection, runs a query,
   and prints the result as JSON with `echo json_encode(...)`.
6. The browser receives the JSON and updates the page.

This request → route → handler → database → JSON response flow is the same pattern used by
almost every web backend, regardless of language — worth describing in your Implementation
chapter's "Business Logic" section.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not connect to MySQL database` | Check `DB_USER`/`DB_PASSWORD` in `config.php` match your actual MySQL login. Make sure MySQL is running. |
| `php: command not found` | PHP isn't installed or isn't on your PATH — see step 1. |
| `Class "PDO" not found` | Your PHP install is missing the `pdo_mysql` extension. On Ubuntu: `sudo apt install php-mysql`. |
| Blank page / nothing loads | Make sure you ran the server with `-t public router.php` exactly as shown — without `router.php`, `/api/` requests won't be routed. |
| `Address already in use` on port 8000 | Something else is using that port. Use a different one: `php -S localhost:8080 -t public router.php`, then visit `http://localhost:8080`. |
| Changes to PHP files don't show up | PHP's built-in server reloads each file on every request automatically — just refresh your browser. No restart needed unless you edited `router.php` or `config.php`. |
