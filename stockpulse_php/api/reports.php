<?php
// ============================================
// StockPulse — Reports Endpoint
// ============================================

function reports(): void {
    requireLogin();
    $pdo = getDB();

    $daysWindow = (int)($_GET['days'] ?? 30);
    $daysWindow = max(1, min($daysWindow, 3650));
    $cutoff = (new DateTime())->modify('-' . ($daysWindow - 1) . ' days')->format('Y-m-d');

    $stmt = $pdo->prepare("
        SELECT products.category AS category,
               COALESCE(SUM(CASE WHEN sales.sale_date >= ? THEN sales.qty END),0) AS units,
               COALESCE(SUM(CASE WHEN sales.sale_date >= ? THEN sales.revenue END),0) AS revenue,
               COALESCE(SUM(CASE WHEN sales.sale_date >= ? THEN sales.qty*products.cost END),0) AS cost
        FROM products LEFT JOIN sales ON sales.product_id = products.id
        GROUP BY products.category ORDER BY revenue DESC
    ");
    $stmt->execute([$cutoff, $cutoff, $cutoff]);
    $rows = $stmt->fetchAll();

    $result = [];
    foreach ($rows as $r) {
        $revenue = (float)$r['revenue'];
        $cost = (float)$r['cost'];
        $margin = $revenue > 0 ? (($revenue - $cost) / $revenue * 100) : 0;
        $result[] = [
            'category' => $r['category'],
            'units' => (int)$r['units'],
            'revenue' => $revenue,
            'margin' => $margin,
        ];
    }
    echo json_encode($result);
}
