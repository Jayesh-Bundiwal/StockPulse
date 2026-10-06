<?php
// ============================================
// StockPulse — Database Configuration
// ============================================
// Edit these values to match your own MySQL setup.
// If you just installed MySQL and haven't changed anything,
// DB_USER is usually "root" and DB_PASSWORD is whatever you
// set during installation (or blank, if you didn't set one).

define('DB_HOST', 'localhost');
define('DB_PORT', '3306');
define('DB_USER', 'root');
define('DB_PASSWORD', '');       // <-- put your MySQL root password here
define('DB_NAME', 'stockpulse');

// Used to secure PHP session cookies. Change this to any random string.
define('SESSION_SECRET', 'stockpulse-dev-secret-change-me');

// ============================================
// Python Analytics Service (Dashboard & Reports)
// ============================================
// PHP still does the database work (queries products/sales out of MySQL).
// It then hands those raw rows to this separate Python (Flask + Pandas)
// service, which does the data manipulation and hands back computed
// KPIs/aggregates. Start it separately with:
//   cd python_service && pip install -r requirements.txt && python analytics_service.py
define('PYTHON_SERVICE_URL', 'http://127.0.0.1:5001');

// A shared secret so the Python service only accepts requests from this
// PHP app (server-to-server, both on localhost) — not from the public internet.
// Must match INTERNAL_SERVICE_KEY in python_service/analytics_service.py.
define('INTERNAL_SERVICE_KEY', 'stockpulse-internal-key-change-me');
