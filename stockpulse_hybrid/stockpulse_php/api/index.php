<?php
// ============================================
// StockPulse — API Router
// ============================================
// Matches the request path + method to a handler function.
// This plays the same role Flask's @app.route() decorators played
// in the Python version — just written out explicitly.

session_start();
header('Content-Type: application/json');

require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../auth_helpers.php';
require_once __DIR__ . '/../analytics_client.php';
require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/products.php';
require_once __DIR__ . '/sales.php';
require_once __DIR__ . '/restocks.php';
require_once __DIR__ . '/inventory.php';
require_once __DIR__ . '/dashboard.php';
require_once __DIR__ . '/reports.php';

$uri    = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path   = preg_replace('#^/api#', '', $uri); // strip leading /api
$method = $_SERVER['REQUEST_METHOD'];

if ($path === '' || $path === '/') {
    http_response_code(404);
    echo json_encode(['error' => 'No endpoint specified']);
    exit;
}

// ---- Auth ----
if ($path === '/login' && $method === 'POST')  { login(); exit; }
if ($path === '/logout' && $method === 'POST') { logout(); exit; }
if ($path === '/me' && $method === 'GET')      { me(); exit; }

// ---- Products ----
if ($path === '/products' && ($method === 'GET' || $method === 'POST')) { products($method); exit; }
if ($path === '/products/bulk' && $method === 'POST') { productsBulk(); exit; }
if (preg_match('#^/products/(\d+)$#', $path, $m) && ($method === 'PUT' || $method === 'DELETE')) {
    productDetail((int)$m[1], $method); exit;
}

// ---- Sales ----
if ($path === '/sales' && ($method === 'GET' || $method === 'POST')) { sales($method); exit; }

// ---- Restocks (Purchases) ----
if ($path === '/restocks' && ($method === 'GET' || $method === 'POST')) { restocks($method); exit; }

// ---- Inventory ----
if (preg_match('#^/inventory/(\d+)/adjust$#', $path, $m) && $method === 'POST') {
    adjustInventory((int)$m[1]); exit;
}

// ---- Dashboard & Reports ----
if ($path === '/dashboard' && $method === 'GET') { dashboard(); exit; }
if ($path === '/reports' && $method === 'GET')   { reports(); exit; }

http_response_code(404);
echo json_encode(['error' => 'Endpoint not found: ' . $method . ' ' . $path]);
