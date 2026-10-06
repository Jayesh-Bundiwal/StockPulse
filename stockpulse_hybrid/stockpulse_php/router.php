<?php
// ============================================
// StockPulse — Dev Server Router
// ============================================
// This file is only used by PHP's built-in development server:
//   php -S localhost:8000 -t public router.php
//
// It sends any request starting with /api/ to api/index.php.
// Everything else (index.html, css, js, images) is served normally
// from the public/ folder by the built-in server itself.

$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if (strpos($uri, '/api/') === 0) {
    require __DIR__ . '/api/index.php';
    return true;
}

return false; // let the built-in server serve the static file from public/
