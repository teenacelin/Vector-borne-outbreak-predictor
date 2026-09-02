<?php
// api/get_dashboard_data.php
require_once 'config.php';

$response = [
    'overview' => [],
    'map_data' => [],
    'municipality_stats' => [],
    'climate_disease_trends' => [],
    'model_performance' => []
];

try {
    // 1. Overview KPIs
    $stmt = $pdo->query("SELECT COUNT(*) as tracked_municipalities FROM locations");
    $overview = $stmt->fetch();
    
    $stmt = $pdo->query("SELECT COUNT(*) as high_risk_count FROM predictions WHERE risk_level IN ('HIGH', 'VERY HIGH') AND prediction_date = (SELECT MAX(prediction_date) FROM predictions)");
    $high_risk = $stmt->fetch();
    
    $response['overview']['trackedMunicipalities'] = $overview['tracked_municipalities'] ?? 0;
    $response['overview']['highRiskMunicipalities'] = $high_risk['high_risk_count'] ?? 0;

    // 2. Map Data
    $stmt = $pdo->query("
        SELECT l.location_id, l.municipality, l.state_code, l.latitude, l.longitude, p.risk_probability, p.risk_level
        FROM locations l
        JOIN predictions p ON l.location_id = p.location_id
        WHERE p.prediction_date = (SELECT MAX(prediction_date) FROM predictions)
    ");
    $response['map_data'] = $stmt->fetchAll();

    // 3. Municipality Stats (Hotspots & Growth)
    $stmt = $pdo->query("
        SELECT l.municipality, f.dengue_rolling_4 as cases, f.rainfall_anomaly, f.temperature_anomaly
        FROM locations l
        JOIN features f ON l.location_id = f.location_id
        WHERE f.date = (SELECT MAX(date) FROM features)
        ORDER BY f.dengue_rolling_4 DESC
        LIMIT 10
    ");
    $response['municipality_stats']['hotspots'] = $stmt->fetchAll();
    
    // Actions table data
    $stmt = $pdo->query("
        SELECT l.municipality, p.risk_level, p.risk_probability 
        FROM locations l
        JOIN predictions p ON l.location_id = p.location_id
        WHERE p.prediction_date = (SELECT MAX(prediction_date) FROM predictions)
        ORDER BY p.risk_probability DESC
        LIMIT 10
    ");
    $response['municipality_stats']['actions'] = $stmt->fetchAll();

    // 4. Climate & Disease Trends
    $stmt = $pdo->query("
        SELECT f.date, AVG(f.temperature_1) as avg_temp, AVG(f.rainfall_1) as avg_rain, SUM(f.dengue_rolling_4) as total_cases
        FROM features f
        GROUP BY f.date
        ORDER BY f.date ASC
    ");
    $response['climate_disease_trends'] = $stmt->fetchAll();
    
    // Seasonal Risk
    $stmt = $pdo->query("
        SELECT month, SUM(cases) as total_cases
        FROM malaria_cases
        GROUP BY month
        ORDER BY month ASC
    ");
    $response['seasonal_risk'] = $stmt->fetchAll();

    // 5. Model Performance (Dynamically read real metrics from XGBoost output)
    $metrics_file = __DIR__ . '/../public/metrics.json';
    if (file_exists($metrics_file)) {
        $metrics_json = file_get_contents($metrics_file);
        $response['model_performance'] = json_decode($metrics_json, true);
    } else {
        $response['model_performance'] = [
            'precision' => 0,
            'recall' => 0,
            'f1_score' => 0,
            'pr_auc' => 0
        ];
    }

} catch (\PDOException $e) {
    echo json_encode(['error' => 'Database query failed: ' . $e->getMessage()]);
    exit;
}

echo json_encode($response);
?>
