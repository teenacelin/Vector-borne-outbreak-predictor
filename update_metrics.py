import pickle
import json

with open('ml/saved_models/xgboost_v1.pkl', 'rb') as f:
    model = pickle.load(f)

importances = model.feature_importances_
features = ['temperature_1', 'rainfall_1', 'temperature_2', 'rainfall_2', 'malaria_lag_4', 'malaria_lag_8', 'malaria_rolling_6', 'temperature_anomaly', 'population', 'urban_density', 'sanitation_index']

feature_importances = {f: float(i) for f, i in zip(features, importances)}

with open('public/metrics.json', 'r') as f:
    metrics = json.load(f)

metrics['feature_importances'] = feature_importances

with open('public/metrics.json', 'w') as f:
    json.dump(metrics, f)

print("Updated metrics.json with feature importances")
