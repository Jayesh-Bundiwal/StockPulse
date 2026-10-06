<?php
// ============================================
// StockPulse — Sales Endpoints
// ============================================

function sales(string $method): void {
    requireLogin();
    $pdo = getDB();

    if ($method === 'GET') {
        $rows = $pdo->query("
            SELECT sales.id, sales.sale_date AS date, sales.qty, sales.revenue,
                   products.name AS product_name, products.id AS product_id
            FROM sales JOIN products ON products.id = sales.product_id
            ORDER BY sales.sale_date DESC, sales.id DESC LIMIT 200
        ")->fetchAll();
        echo json_encode($rows);
        return;
    }

    // POST — log a sale
    $d = jsonInput();
    $productId = (int)$d['product_id'];
    $qty = (int)$d['qty'];

    $stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
    $stmt->execute([$productId]);
    $product = $stmt->fetch();

    if (!$product) {
        http_response_code(404);
        echo json_encode(['error' => 'Product not found']);
        return;
    }
    if ($qty > $product['stock']) {
        http_response_code(400);
        echo json_encode(['error' => "Only {$product['stock']} in stock"]);
        return;
    }

    $revenue = $qty * $product['price'];
    $today = date('Y-m-d');

    $pdo->prepare("UPDATE products SET stock = stock - ? WHERE id = ?")->execute([$qty, $productId]);
    $ins = $pdo->prepare("INSERT INTO sales (sale_date, product_id, qty, revenue) VALUES (?,?,?,?)");
    $ins->execute([$today, $productId, $qty, $revenue]);

    http_response_code(201);
    echo json_encode([
        'id' => $pdo->lastInsertId(), 'date' => $today, 'product_id' => $productId,
        'product_name' => $product['name'], 'qty' => $qty, 'revenue' => $revenue,
    ]);
}
