import sqlite3
import pandas as pd
import os

DB_PATH = 'data/cleaned/vector_predictor.db'
OUT_DIR = 'data/powerbi_export'

os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

# Export Predictions
df_predictions = pd.read_sql_query("SELECT p.*, l.municipality, l.state_name, l.latitude, l.longitude FROM predictions p JOIN locations l ON p.location_id = l.location_id", conn)
df_predictions.to_csv(f"{OUT_DIR}/predictions_export.csv", index=False)

# Export Features & Climate
df_features = pd.read_sql_query("SELECT f.*, l.municipality, l.state_name FROM features f JOIN locations l ON f.location_id = l.location_id", conn)
df_features.to_csv(f"{OUT_DIR}/features_export.csv", index=False)

# Export Historical Disease
df_disease = pd.read_sql_query("SELECT m.*, l.municipality, l.state_name FROM malaria_cases m JOIN locations l ON m.location_id = l.location_id", conn)
df_disease.to_csv(f"{OUT_DIR}/historical_disease_export.csv", index=False)

conn.close()
print(f"Data successfully exported to {OUT_DIR} for Power BI!")
