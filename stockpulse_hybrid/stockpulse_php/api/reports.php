<?php
// ============================================
// StockPulse — Reports Endpoint
// ============================================
// PHP's job here: authenticate the request, connect to MySQL, and fetch
// the raw products + sales rows.
// Python's job: group by category and compute units/revenue/margin using
// Pandas. See python_service/analytics_service.py -> compute_reports().

function reports(): void {
    requireLogin();
    $pdo = getDB();

    $daysWindow = (int)($_GET['days'] ?? 30);
    $daysWindow = max(1, min($daysWindow, 3650));

    $products = $pdo->query("
        SELECT id, name, sku, category, price, cost, stock, threshold_qty FROM products
    ")->fetchAll();

    $sales = $pdo->query("
        SELECT id, sale_date, product_id, qty, revenue FROM sales
    ")->fetchAll();

    $result = callAnalyticsService('/compute/reports', [
        'days_window' => $daysWindow,
        'products'    => $products,
        'sales'       => $sales,
    ]);

    echo json_encode($result);
}
