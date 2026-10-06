<?php
// ============================================
// StockPulse — Python Analytics Service Client
// ============================================
// This is the bridge between the two halves of the app:
//   - PHP  = database (fetches raw rows out of MySQL)
//   - Python = data manipulation (turns those rows into KPIs/aggregates with Pandas)
//
// callAnalyticsService() sends raw rows PHP already queried to the Python
// service as JSON over HTTP (both run on localhost) and returns its
// computed JSON response. Python never touches MySQL directly — it only
// ever sees the data PHP hands it.

require_once __DIR__ . '/config.php';

/**
 * POSTs $payload as JSON to $endpoint on the Python analytics service
 * and returns the decoded JSON response as an array.
 * Stops the request with a clear error if the Python service is
 * unreachable or returns an error, same style as getDB()'s error handling.
 */
function callAnalyticsService(string $endpoint, array $payload): array {
    $url = rtrim(PYTHON_SERVICE_URL, '/') . $endpoint;

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'X-Internal-Key: ' . INTERNAL_SERVICE_KEY,
        ],
        CURLOPT_POSTFIELDS     => json_encode($payload),
        CURLOPT_TIMEOUT        => 10,
    ]);
    $body = curl_exec($ch);
    $curlErr = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($body === false || $curlErr) {
        http_response_code(502);
        echo json_encode([
            'error' => 'Could not reach the Python analytics service at ' . $url . '. ' .
                       'Is it running? Start it with: cd python_service && python analytics_service.py. ' .
                       'Details: ' . $curlErr
        ]);
        exit;
    }

    $decoded = json_decode($body, true);
    if ($httpCode >= 400 || !is_array($decoded)) {
        http_response_code($httpCode >= 400 ? $httpCode : 500);
        echo $body !== '' ? $body : json_encode(['error' => 'Analytics service returned an invalid response']);
        exit;
    }

    return $decoded;
}
