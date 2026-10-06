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
