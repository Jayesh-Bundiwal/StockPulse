<?php
// ============================================
// StockPulse — Auth Helper Functions
// ============================================

function isLoggedIn(): bool {
    return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
}

function currentRole(): ?string {
    return $_SESSION['role'] ?? null;
}

function isAdmin(): bool {
    return isLoggedIn() && currentRole() === 'admin';
}

/** Sends a 401 JSON response and stops execution if not logged in. */
function requireLogin(): void {
    if (!isLoggedIn()) {
        http_response_code(401);
        echo json_encode(['error' => 'Not authenticated']);
        exit;
    }
}

/** Sends a 403 JSON response and stops execution if not an admin. */
function requireAdmin(string $message = 'Admin access required'): void {
    requireLogin();
    if (!isAdmin()) {
        http_response_code(403);
        echo json_encode(['error' => $message]);
        exit;
    }
}

/** Reads and JSON-decodes the request body. Returns an empty array if invalid/empty. */
function jsonInput(): array {
    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
}
