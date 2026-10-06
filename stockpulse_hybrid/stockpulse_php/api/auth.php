<?php
// ============================================
// StockPulse — Auth Endpoints
// ============================================

function login(): void {
    $data = jsonInput();
    $email = strtolower(trim($data['email'] ?? ''));
    $password = $data['password'] ?? '';

    $pdo = getDB();
    $stmt = $pdo->prepare("SELECT * FROM users WHERE LOWER(email) = ? AND password = ?");
    $stmt->execute([$email, $password]);
    $user = $stmt->fetch();

    if ($user) {
        $_SESSION['logged_in'] = true;
        $_SESSION['email'] = $user['email'];
        $_SESSION['role'] = $user['role'];
        echo json_encode(['ok' => true, 'email' => $user['email'], 'role' => $user['role']]);
    } else {
        http_response_code(401);
        echo json_encode(['ok' => false, 'error' => 'Incorrect email or password.']);
    }
}

function logout(): void {
    $_SESSION = [];
    session_destroy();
    echo json_encode(['ok' => true]);
}

function me(): void {
    if (!isLoggedIn()) {
        echo json_encode(['logged_in' => false]);
        return;
    }
    echo json_encode([
        'logged_in' => true,
        'email' => $_SESSION['email'],
        'role' => $_SESSION['role'],
    ]);
}
