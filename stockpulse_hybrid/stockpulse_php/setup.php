<?php
// ============================================
// StockPulse — One-time Database Setup
// ============================================
// Run this ONCE before using the app:
//   php setup.php
// (or open http://localhost:8000/setup.php in a browser)
//
// It creates the "stockpulse" database if it doesn't exist, creates all
// four tables, and seeds 16 sample products, 2 demo user accounts, and
// ~30 days of sample sales history. Safe to run again — it checks for
// existing data before inserting anything.

require_once __DIR__ . '/config.php';

echo "Connecting to MySQL at " . DB_HOST . ":" . DB_PORT . " ...\n";

try {
    $bootstrap = new PDO("mysql:host=" . DB_HOST . ";port=" . DB_PORT, DB_USER, DB_PASSWORD, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    ]);
} catch (PDOException $e) {
    die("Could not connect to MySQL server. Check DB_USER / DB_PASSWORD in config.php.\nDetails: " . $e->getMessage() . "\n");
}

$bootstrap->exec("CREATE DATABASE IF NOT EXISTS `" . DB_NAME . "` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
echo "Database \"" . DB_NAME . "\" ready.\n";

require_once __DIR__ . '/db.php';
$pdo = getDB();

$pdo->exec("
    CREATE TABLE IF NOT EXISTS products (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(150) NOT NULL,
        sku VARCHAR(30) UNIQUE NOT NULL,
        category VARCHAR(50) NOT NULL,
        price DOUBLE NOT NULL,
        cost DOUBLE NOT NULL,
        stock INT NOT NULL,
        threshold_qty INT NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
");

$pdo->exec("
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(120) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'staff'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
");

$pdo->exec("
    CREATE TABLE IF NOT EXISTS sales (
        id INT PRIMARY KEY AUTO_INCREMENT,
        sale_date VARCHAR(10) NOT NULL,
        product_id INT NOT NULL,
        qty INT NOT NULL,
        revenue DOUBLE NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        INDEX idx_sales_date (sale_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
");

$pdo->exec("
    CREATE TABLE IF NOT EXISTS restocks (
        id INT PRIMARY KEY AUTO_INCREMENT,
        restock_date VARCHAR(10) NOT NULL,
        product_id INT NOT NULL,
        qty INT NOT NULL,
        note VARCHAR(255),
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
");
echo "Tables created (or already existed).\n";

// ---- Seed users ----
$count = $pdo->query("SELECT COUNT(*) FROM users")->fetchColumn();
if ($count == 0) {
    $stmt = $pdo->prepare("INSERT INTO users (email, password, role) VALUES (?, ?, ?)");
    $stmt->execute(['admin@shop.com', 'admin123', 'admin']);
    $stmt->execute(['staff@shop.com', 'staff123', 'staff']);
    echo "Seeded 2 demo users (admin@shop.com / staff@shop.com).\n";
} else {
    echo "Users table already has data — skipped seeding.\n";
}

// ---- Seed products ----
$count = $pdo->query("SELECT COUNT(*) FROM products")->fetchColumn();
if ($count == 0) {
    $products = [
        ["Amul Butter 500g", "DA-B5", "Dairy", 290, 240, 22, 10],
        ["Basmati Rice 5kg", "GR-BR5", "Groceries", 650, 480, 45, 10],
        ["Britannia Marie Gold", "SN-BMG", "Snacks", 30, 21, 90, 15],
        ["Coca Cola 1.25L", "BV-CC1", "Beverages", 75, 55, 55, 20],
        ["Colgate Toothpaste 200g", "PC-CT2", "Personal Care", 145, 110, 50, 15],
        ["Dark Fantasy Choco Fills", "SN-DFC", "Snacks", 90, 68, 4, 10],
        ["Dove Soap 100g", "PC-DS1", "Personal Care", 62, 45, 80, 20],
        ["Head & Shoulders Shampoo 340ml", "PC-HS3", "Personal Care", 340, 265, 12, 10],
        ["Lays Classic 52g", "SN-LC5", "Snacks", 20, 13, 200, 30],
        ["Milk 1L Full Cream", "DA-M1", "Dairy", 68, 55, 120, 20],
        ["Nescafe Classic 100g", "BV-NC1", "Beverages", 320, 245, 25, 10],
        ["Paneer 200g", "DA-P2", "Dairy", 95, 72, 6, 15],
        ["Sunflower Oil 1L", "GR-SO1", "Groceries", 180, 140, 60, 15],
        ["Toor Dal 1kg", "GR-TD1", "Groceries", 165, 130, 3, 10],
        ["Tropicana Orange 1L", "BV-T01", "Beverages", 120, 90, 18, 10],
        ["Whole Wheat Flour 10kg", "GR-WF10", "Groceries", 480, 360, 8, 10],
    ];
    $stmt = $pdo->prepare("INSERT INTO products (name, sku, category, price, cost, stock, threshold_qty) VALUES (?,?,?,?,?,?,?)");
    foreach ($products as $p) {
        $stmt->execute($p);
    }
    echo "Seeded " . count($products) . " sample products.\n";
} else {
    echo "Products table already has data — skipped seeding.\n";
}

// ---- Seed ~30 days of sales history ----
$count = $pdo->query("SELECT COUNT(*) FROM sales")->fetchColumn();
if ($count == 0) {
    $rows = $pdo->query("SELECT id, price FROM products")->fetchAll();
    if (count($rows) > 0) {
        $stmt = $pdo->prepare("INSERT INTO sales (sale_date, product_id, qty, revenue) VALUES (?,?,?,?)");
        $today = new DateTime();
        for ($d = 29; $d >= 0; $d--) {
            $day = (clone $today)->modify("-$d days")->format('Y-m-d');
            $orders = 3 + random_int(0, 5);
            if ($d <= 1) $orders += 4;
            if ($d == 11 || $d == 12) $orders += 5;
            for ($i = 0; $i < $orders; $i++) {
                $p = $rows[array_rand($rows)];
                $qty = random_int(1, 4);
                $stmt->execute([$day, $p['id'], $qty, $qty * $p['price']]);
            }
        }
        echo "Seeded ~30 days of sample sales history.\n";
    }
} else {
    echo "Sales table already has data — skipped seeding.\n";
}

echo "\nSetup complete! Start the app with:\n";
echo "  php -S localhost:8000 -t public router.php\n";
echo "Then open http://localhost:8000 and log in with admin@shop.com / admin123\n";
