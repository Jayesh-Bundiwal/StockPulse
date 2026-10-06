<?php
// ============================================
// StockPulse — Product Endpoints
// ============================================

const PRODUCT_SELECT = "SELECT id, name, sku, category, price, cost, stock, threshold_qty AS threshold FROM products";

function products(string $method): void {
    requireLogin();
    $pdo = getDB();

    if ($method === 'GET') {
        $rows = $pdo->query(PRODUCT_SELECT . " ORDER BY name")->fetchAll();
        echo json_encode($rows);
        return;
    }

    // POST — add a new product (admin only)
    requireAdmin('Only admin accounts can add products');
    $d = jsonInput();
    $stmt = $pdo->prepare("INSERT INTO products (name, sku, category, price, cost, stock, threshold_qty) VALUES (?,?,?,?,?,?,?)");
    $stmt->execute([
        $d['name'], $d['sku'], $d['category'],
        (float)$d['price'], (float)$d['cost'], (int)$d['stock'], (int)$d['threshold'],
    ]);
    $id = $pdo->lastInsertId();
    $stmt2 = $pdo->prepare(PRODUCT_SELECT . " WHERE id = ?");
    $stmt2->execute([$id]);
    http_response_code(201);
    echo json_encode($stmt2->fetch());
}

function productDetail(int $id, string $method): void {
    requireLogin();
    requireAdmin('Only admin accounts can edit or delete products');
    $pdo = getDB();

    if ($method === 'DELETE') {
        $stmt = $pdo->prepare("DELETE FROM products WHERE id = ?");
        $stmt->execute([$id]);
        echo json_encode(['ok' => true]);
        return;
    }

    // PUT — update
    $d = jsonInput();
    $stmt = $pdo->prepare("UPDATE products SET name=?, sku=?, category=?, price=?, cost=?, stock=?, threshold_qty=? WHERE id=?");
    $stmt->execute([
        $d['name'], $d['sku'], $d['category'],
        (float)$d['price'], (float)$d['cost'], (int)$d['stock'], (int)$d['threshold'], $id,
    ]);
    $stmt2 = $pdo->prepare(PRODUCT_SELECT . " WHERE id = ?");
    $stmt2->execute([$id]);
    echo json_encode($stmt2->fetch());
}

function productsBulk(): void {
    requireAdmin('Only admin accounts can import products');
    $pdo = getDB();
    $rows = jsonInput()['products'] ?? [];

    $inserted = 0;
    $updated = 0;
    $errors = [];

    foreach ($rows as $r) {
        try {
            $name = trim($r['name']);
            $sku = trim($r['sku']);
            $category = trim($r['category'] ?? 'Groceries') ?: 'Groceries';
            $price = (float)($r['price'] ?? 0);
            $cost = (float)($r['cost'] ?? 0);
            $stock = (int)($r['stock'] ?? 0);
            $threshold = (int)($r['threshold'] ?? 10);

            $check = $pdo->prepare("SELECT id FROM products WHERE sku = ?");
            $check->execute([$sku]);

            if ($check->fetch()) {
                $upd = $pdo->prepare("UPDATE products SET name=?, category=?, price=?, cost=?, stock=?, threshold_qty=? WHERE sku=?");
                $upd->execute([$name, $category, $price, $cost, $stock, $threshold, $sku]);
                $updated++;
            } else {
                $ins = $pdo->prepare("INSERT INTO products (name, sku, category, price, cost, stock, threshold_qty) VALUES (?,?,?,?,?,?,?)");
                $ins->execute([$name, $sku, $category, $price, $cost, $stock, $threshold]);
                $inserted++;
            }
        } catch (Exception $e) {
            $errors[] = $e->getMessage();
        }
    }

    echo json_encode(['inserted' => $inserted, 'updated' => $updated, 'errors' => $errors]);
}
