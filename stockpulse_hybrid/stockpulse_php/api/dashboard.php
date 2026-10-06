<?php
// ============================================
// StockPulse — Dashboard Endpoint
// ============================================
// PHP's job here: authenticate the request, connect to MySQL, and fetch
// the raw products + sales rows.
// Python's job: turn those raw rows into KPIs, the revenue trend, top
// products, and category split, using Pandas. See
// python_service/analytics_service.py -> compute_dashboard().

function dashboard(): void {
    requireLogin();
    $pdo = getDB();

    $daysWindow = (int)($_GET['days'] ?? 30);
    $daysWindow = max(1, min($daysWindow, 365));

    $products = $pdo->query("
        SELECT id, name, sku, category, price, cost, stock, threshold_qty FROM products
    ")->fetchAll();

    $sales = $pdo->query("
        SELECT id, sale_date, product_id, qty, revenue FROM sales
    ")->fetchAll();

    $result = callAnalyticsService('/compute/dashboard', [
        'days_window' => $daysWindow,
        'today'       => (new DateTime())->format('Y-m-d'),
        'products'    => $products,
        'sales'       => $sales,
    ]);

    echo json_encode($result);
}
