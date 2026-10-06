<?php
// ============================================
// StockPulse — Purchases / Restock Endpoints
// ============================================

function restocks(string $method): void {
    requireLogin();
    $pdo = getDB();

    if ($method === 'GET') {
        $rows = $pdo->query("
            SELECT restocks.id, restocks.restock_date AS date, restocks.qty, restocks.note,
                   products.name AS product_name, products.id AS product_id
            FROM restocks JOIN products ON products.id = restocks.product_id
            ORDER BY restocks.restock_date DESC, restocks.id DESC LIMIT 200
        ")->fetchAll();
        echo json_encode($rows);
        return;
    }

    // POST — record a restock
    $d = jsonInput();
    $productId = (int)$d['product_id'];
    $qty = (int)$d['qty'];
    $note = trim($d['note'] ?? '');

    $stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
    $stmt->execute([$productId]);
    $product = $stmt->fetch();

    if (!$product) {
        http_response_code(404);
        echo json_encode(['error' => 'Product not found']);
        return;
    }
    if ($qty <= 0) {
        http_response_code(400);
        echo json_encode(['error' => 'Quantity must be positive']);
        return;
    }

    $today = date('Y-m-d');
    $pdo->prepare("UPDATE products SET stock = stock + ? WHERE id = ?")->execute([$qty, $productId]);
    $ins = $pdo->prepare("INSERT INTO restocks (restock_date, product_id, qty, note) VALUES (?,?,?,?)");
    $ins->execute([$today, $productId, $qty, $note]);

    http_response_code(201);
    echo json_encode([
        'id' => $pdo->lastInsertId(), 'date' => $today, 'product_id' => $productId,
        'product_name' => $product['name'], 'qty' => $qty, 'note' => $note,
    ]);
}
