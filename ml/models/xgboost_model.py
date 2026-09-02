import sqlite3
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import pickle
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cleaned', 'vector_predictor.db')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'xgboost_v1.pkl')

def load_data():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM features"
    df = pd.read_sql_query(query, conn, parse_dates=['date'])
    conn.close()
    return df

def train_model():
    df = load_data()
    if df.empty:
        print("No features available for training.")
        return

    df['year'] = df['date'].dt.year

    features = [
        'malaria_lag_1', 'malaria_lag_4', 'rainfall_1', 'rainfall_2', 
        'temperature_1', 'temperature_2', 'rainfall_anomaly', 'temperature_anomaly',
        'population', 'urban_density', 'sanitation_index'
    ]
    target = 'outbreak_target'

    # Time-series split. Adjust split_year based on available data.
    # We'll use 2023 for demonstration.
    split_year = 2023
    
    train = df[df['year'] < split_year]
    test = df[df['year'] >= split_year]

    # Fallback if year < 2023 doesn't exist in data
    if train.empty or test.empty:
        print(f"Time-series split at year {split_year} failed. Trying 80/20 sequential split.")
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]

    if train.empty or test.empty:
        print("Dataset too small for training.")
        return

    X_train = train[features]
    y_train = train[target]
    X_test = test[features]
    y_test = test[target]

    print("Training XGBoost model...")
    # Calculate scale_pos_weight to balance classes
    pos_cases = y_train.sum()
    neg_cases = len(y_train) - pos_cases
    scale_weight = neg_cases / pos_cases if pos_cases > 0 else 1

    model = xgb.XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        random_state=42,
        eval_metric='logloss',
        scale_pos_weight=scale_weight
    )
    
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    print("--- Model Evaluation ---")
    precision = precision_score(y_test, preds, zero_division=0)
    recall = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    try:
        roc_auc = roc_auc_score(y_test, probs)
    except ValueError:
        roc_auc = 0.0
        
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1 Score: {f1:.3f}")
    print(f"ROC-AUC: {roc_auc:.3f}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    # Save metrics to DB or temp file so the dashboard can read REAL metrics
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # We will just write a small JSON file for the dashboard to read, or we can create a metrics table
    # A temp file is easier:
    metrics = {
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'pr_auc': float(roc_auc)
    }
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'metrics.json'), 'w') as f:
        json.dump(metrics, f)
        
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    import json
    train_model()
