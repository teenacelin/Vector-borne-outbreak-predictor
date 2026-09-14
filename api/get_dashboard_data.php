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
    // Filters
    $state = $_GET['state'] ?? 'ALL';
    $risk = $_GET['risk'] ?? 'ALL';
    $start_date = $_GET['start_date'] ?? null;
    $end_date = $_GET['end_date'] ?? null;

    $where_pred = ["p.prediction_date = (SELECT MAX(prediction_date) FROM predictions)"];
    $where_feat = ["f.date = (SELECT MAX(date) FROM features)"];
    $where_feat_trend = ["1=1"];
    $where_malaria = ["1=1"];
    
    $params_pred = [];
    $params_feat = [];
    $params_feat_trend = [];
    $params_malaria = [];
    
    if ($state !== 'ALL') {
        $where_pred[] = 'l.state_name = ?';
        $params_pred[] = $state;
        
        $where_feat[] = 'l.state_name = ?';
        $params_feat[] = $state;
        
        $where_feat_trend[] = "location_id IN (SELECT location_id FROM locations WHERE state_name = ?)";
        $params_feat_trend[] = $state;
        
        $where_malaria[] = "location_id IN (SELECT location_id FROM locations WHERE state_name = ?)";
        $params_malaria[] = $state;
    }
    
    if ($risk !== 'ALL') {
        $where_pred[] = 'p.risk_level = ?';
        $params_pred[] = $risk;
    }
    
    if ($start_date) {
        $where_feat_trend[] = "f.date >= ?";
        $params_feat_trend[] = $start_date;
    }
    
    if ($end_date) {
        $where_feat_trend[] = "f.date <= ?";
        $params_feat_trend[] = $end_date;
    }

    $where_pred_sql = implode(' AND ', $where_pred);
    $where_feat_sql = implode(' AND ', $where_feat);
    $where_feat_trend_sql = implode(' AND ', $where_feat_trend);
    $where_malaria_sql = implode(' AND ', $where_malaria);

    // 1. Overview KPIs
    // Tracked municipalities (filtered by state if needed)
    $stmt = $pdo->prepare("SELECT COUNT(*) as tracked_municipalities FROM locations " . ($state !== 'ALL' ? "WHERE state_name = ?" : ""));
    $stmt->execute($state !== 'ALL' ? [$state] : []);
    $overview = $stmt->fetch();
    
    // High risk count (respecting filters)
    $high_risk_cond = ["p.risk_level IN ('HIGH', 'VERY HIGH')"];
    $high_risk_params = [];
    if ($state !== 'ALL') {
        $high_risk_cond[] = 'l.state_name = ?';
        $high_risk_params[] = $state;
    }
    $high_risk_sql = implode(' AND ', $high_risk_cond);
    
    $stmt = $pdo->prepare("SELECT COUNT(*) as high_risk_count FROM predictions p JOIN locations l ON p.location_id = l.location_id WHERE p.prediction_date = (SELECT MAX(prediction_date) FROM predictions) AND " . $high_risk_sql);
    $stmt->execute($high_risk_params);
    $high_risk = $stmt->fetch();
    
    $response['overview']['trackedMunicipalities'] = $overview['tracked_municipalities'] ?? 0;
    $response['overview']['highRiskMunicipalities'] = $high_risk['high_risk_count'] ?? 0;

    // 2. Map Data
    $stmt = $pdo->prepare("
        SELECT l.location_id, l.municipality, l.state_name, l.latitude, l.longitude, l.geometry, p.risk_probability, p.risk_level
        FROM locations l
        JOIN predictions p ON l.location_id = p.location_id
        WHERE {$where_pred_sql}
    ");
    $stmt->execute($params_pred);
    $response['map_data'] = $stmt->fetchAll();

    // 3. Municipality Stats (Hotspots & Growth)
    $stmt = $pdo->prepare("
        SELECT l.municipality, f.malaria_cases_current as cases, f.rainfall_anomaly, f.temperature_anomaly
        FROM locations l
        JOIN features f ON l.location_id = f.location_id
        WHERE {$where_feat_sql}
        ORDER BY f.malaria_cases_current DESC
        LIMIT 10
    ");
    $stmt->execute($params_feat);
    $response['municipality_stats']['hotspots'] = $stmt->fetchAll();
    
    // Actions table data
    $stmt = $pdo->prepare("
        SELECT l.municipality, p.risk_level, p.risk_probability 
        FROM locations l
        JOIN predictions p ON l.location_id = p.location_id
        WHERE {$where_pred_sql}
        ORDER BY p.risk_probability DESC
        LIMIT 10
    ");
    $stmt->execute($params_pred);
    $response['municipality_stats']['actions'] = $stmt->fetchAll();

    // 4. Climate & Disease Trends
    $stmt = $pdo->prepare("
        SELECT f.date, AVG(f.temperature_1) as avg_temp, AVG(f.rainfall_1) as avg_rain, SUM(f.malaria_cases_current) as total_cases
        FROM features f
        WHERE {$where_feat_trend_sql}
        GROUP BY f.date
        ORDER BY f.date ASC
    ");
    $stmt->execute($params_feat_trend);
    $response['climate_disease_trends'] = $stmt->fetchAll();
    
    // Seasonal Risk
    $stmt = $pdo->prepare("
        SELECT month, SUM(cases) as total_cases
        FROM malaria_cases
        WHERE {$where_malaria_sql}
        GROUP BY month
        ORDER BY month ASC
    ");
    $stmt->execute($params_malaria);
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
