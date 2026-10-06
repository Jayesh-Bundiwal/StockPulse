<?php
// ============================================
// StockPulse — Dashboard Endpoint
// ============================================

function dashboard(): void {
    requireLogin();
    $pdo = getDB();

    $daysWindow = (int)($_GET['days'] ?? 30);
    $daysWindow = max(1, min($daysWindow, 365));

    $today = new DateTime();
    $cutoff = (clone $today)->modify('-' . ($daysWindow - 1) . ' days')->format('Y-m-d');
    $todayStr = $today->format('Y-m-d');

    $stmt = $pdo->prepare("SELECT COALESCE(SUM(revenue),0) AS v FROM sales WHERE sale_date >= ?");
    $stmt->execute([$cutoff]);
    $totalRevenue = (float)$stmt->fetch()['v'];

    $stmt = $pdo->prepare("SELECT COUNT(*) AS v FROM sales WHERE sale_date >= ?");
    $stmt->execute([$cutoff]);
    $ordersTotal = (int)$stmt->fetch()['v'];

    $stmt = $pdo->prepare("SELECT COALESCE(SUM(revenue),0) AS rev, COUNT(*) AS cnt FROM sales WHERE sale_date = ?");
    $stmt->execute([$todayStr]);
    $todayRow = $stmt->fetch();
    $todayRevenue = (float)$todayRow['rev'];
    $todayCount = (int)$todayRow['cnt'];

    $invRow = $pdo->query("SELECT COALESCE(SUM(stock*cost),0) AS val, COALESCE(SUM(stock),0) AS units, COUNT(*) AS skus FROM products")->fetch();
    $inventoryValue = (float)$invRow['val'];
    $totalUnits = (int)$invRow['units'];
    $skuCount = (int)$invRow['skus'];

    $lowStockRows = $pdo->query("
        SELECT id, name, sku, category, price, cost, stock, threshold_qty AS threshold
        FROM products WHERE stock <= threshold_qty ORDER BY (stock / threshold_qty) ASC
    ")->fetchAll();

    $revenueByDay = [];
    $stmt = $pdo->prepare("SELECT COALESCE(SUM(revenue),0) AS v FROM sales WHERE sale_date = ?");
    for ($d = $daysWindow - 1; $d >= 0; $d--) {
        $day = (clone $today)->modify("-$d days")->format('Y-m-d');
        $stmt->execute([$day]);
        $revenueByDay[] = ['date' => $day, 'revenue' => (float)$stmt->fetch()['v']];
    }

    $stmt = $pdo->prepare("
        SELECT products.name AS name,
               COALESCE(SUM(CASE WHEN sales.sale_date >= ? THEN sales.revenue END),0) AS revenue
        FROM products LEFT JOIN sales ON sales.product_id = products.id
        GROUP BY products.id, products.name ORDER BY revenue DESC LIMIT 5
    ");
    $stmt->execute([$cutoff]);
    $topProducts = $stmt->fetchAll();
    foreach ($topProducts as &$tp) { $tp['revenue'] = (float)$tp['revenue']; }

    $stmt = $pdo->prepare("
        SELECT products.category AS category,
               COALESCE(SUM(CASE WHEN sales.sale_date >= ? THEN sales.revenue END),0) AS revenue
        FROM products LEFT JOIN sales ON sales.product_id = products.id
        GROUP BY products.category ORDER BY revenue DESC
    ");
    $stmt->execute([$cutoff]);
    $categoryRevenue = $stmt->fetchAll();
    foreach ($categoryRevenue as &$cr) { $cr['revenue'] = (float)$cr['revenue']; }

    echo json_encode([
        'days_window' => $daysWindow,
        'total_revenue' => $totalRevenue,
        'orders_total' => $ordersTotal,
        'today_revenue' => $todayRevenue,
        'today_count' => $todayCount,
        'inventory_value' => $inventoryValue,
        'total_units' => $totalUnits,
        'sku_count' => $skuCount,
        'low_stock' => count($lowStockRows),
        'low_stock_products' => $lowStockRows,
        'revenue_by_day' => $revenueByDay,
        'top_products' => $topProducts,
        'category_revenue' => $categoryRevenue,
    ]);
}
