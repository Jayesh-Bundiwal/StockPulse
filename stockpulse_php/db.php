<?php
// ============================================
// StockPulse — Database Connection Helper
// ============================================
require_once __DIR__ . '/config.php';

/**
 * Returns a single shared PDO connection to the stockpulse database.
 * Connecting is cheap in PHP (a fresh connection per request is normal
 * — unlike Flask, there's no long-running process to keep it open in).
 */
function getDB(): PDO {
    static $pdo = null;
    if ($pdo !== null) {
        return $pdo;
    }
    try {
        $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
        $pdo = new PDO($dsn, DB_USER, DB_PASSWORD, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    } catch (PDOException $e) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode([
            'error' => 'Could not connect to MySQL database "' . DB_NAME . '". ' .
                       'Did you run setup.php first, and are your credentials in config.php correct? ' .
                       'Details: ' . $e->getMessage()
        ]);
        exit;
    }
    return $pdo;
}
