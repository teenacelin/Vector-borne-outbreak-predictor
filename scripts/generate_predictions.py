import sqlite3
import pandas as pd
import pickle
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'vector_predictor.db')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'saved_models', 'xgboost_v1.pkl')

def get_risk_level(prob):
    if prob < 0.30: return "LOW"
    elif prob < 0.60: return "MODERATE"
    elif prob < 0.80: return "HIGH"
    else: return "VERY HIGH"

def generate():
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Please train the model first.")
        return
        
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    conn = sqlite3.connect(DB_PATH)
    
    # Fetch the most recent feature row per location
    query = """
    SELECT *
    FROM features
    WHERE date = (SELECT MAX(date) FROM features)
    """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("No recent features found.")
        conn.close()
        return

    features = [
        'malaria_lag_1', 'malaria_lag_4', 'rainfall_1', 'rainfall_2', 
        'temperature_1', 'temperature_2', 'rainfall_anomaly', 'temperature_anomaly',
        'population', 'urban_density', 'sanitation_index'
    ]
    
    X = df[features]
    
    print("Generating predictions...")
    probs = model.predict_proba(X)[:, 1]
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions")
    
    prediction_date = datetime.date.today().isoformat()
    # Target date is roughly 4 weeks ahead
    target_date = (datetime.date.today() + datetime.timedelta(weeks=4)).isoformat()
    
    inserted = 0
    for idx, row in df.iterrows():
        prob = probs[idx]
        level = get_risk_level(prob)
        
        cursor.execute('''
            INSERT INTO predictions (
                location_id, prediction_date, target_date, disease, 
                risk_probability, risk_level, model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (row['location_id'], prediction_date, target_date, 'malaria', float(prob), level, 'xgboost_v1'))
        inserted += 1
        
    conn.commit()
    conn.close()
    
    print(f"Successfully generated and stored {inserted} predictions.")

if __name__ == "__main__":
    generate()
