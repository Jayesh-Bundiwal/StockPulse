<?php
// ============================================
// StockPulse — Inventory Adjustment Endpoint
// ============================================

function adjustInventory(int $productId): void {
    requireLogin();
    $pdo = getDB();

    $delta = (int)(jsonInput()['delta'] ?? 0);

    $stmt = $pdo->prepare("SELECT stock FROM products WHERE id = ?");
    $stmt->execute([$productId]);
    $row = $stmt->fetch();

    if (!$row) {
        http_response_code(404);
        echo json_encode(['error' => 'Product not found']);
        return;
    }

    $newStock = max(0, $row['stock'] + $delta);
    $pdo->prepare("UPDATE products SET stock = ? WHERE id = ?")->execute([$newStock, $productId]);

    echo json_encode(['id' => $productId, 'stock' => $newStock]);
}
