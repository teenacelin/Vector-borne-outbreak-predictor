import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cleaned', 'vector_predictor.db')

def fetch_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Join malaria cases with precipitation on location + year + month
    # Use LEFT JOIN so we keep malaria rows even if no climate match
    query = """
    SELECT 
        l.location_id, l.municipality, l.state_name,
        m.year, m.month,
        COALESCE(m.cases, 0) as malaria_cases,
        p.rainfall_mm,
        t.temperature_c,
        i.population,
        i.urban_density,
        i.sanitation_index
    FROM locations l
    INNER JOIN malaria_cases m ON l.location_id = m.location_id
    LEFT JOIN precipitation p ON l.location_id = p.location_id AND m.year = p.year AND m.month = p.month
    LEFT JOIN temperature t ON l.location_id = t.location_id AND m.year = t.year AND m.month = t.month
    LEFT JOIN infrastructure i ON l.location_id = i.location_id
    WHERE m.year IS NOT NULL
    ORDER BY l.location_id, m.year, m.month
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def create_features(df):
    if df.empty:
        return df
        
    df = df.sort_values(by=['location_id', 'year', 'month'])
    
    # Fill missing climate with per-location median (better than 0)
    df['rainfall_mm'] = df.groupby('location_id')['rainfall_mm'].transform(
        lambda x: x.fillna(x.median()) if x.notna().any() else x.fillna(0)
    )
    df['temperature_c'] = df.groupby('location_id')['temperature_c'].transform(
        lambda x: x.fillna(x.median()) if x.notna().any() else x.fillna(0)
    )
    # Final fallback: fill remaining NaN with 0
    df['rainfall_mm'] = df['rainfall_mm'].fillna(0)
    df['temperature_c'] = df['temperature_c'].fillna(0)
    
    # Infrastructure fallbacks
    df['population'] = df['population'].fillna(10000)
    df['urban_density'] = df['urban_density'].fillna(50.0)
    df['sanitation_index'] = df['sanitation_index'].fillna(0.5)
    
    # Calculate lags per municipality (monthly)
    df['malaria_lag_1'] = df.groupby('location_id')['malaria_cases'].shift(1)
    df['malaria_lag_4'] = df.groupby('location_id')['malaria_cases'].shift(4)
    
    df['rainfall_1'] = df.groupby('location_id')['rainfall_mm'].shift(1)
    df['rainfall_2'] = df.groupby('location_id')['rainfall_mm'].shift(2)
    
    df['temperature_1'] = df.groupby('location_id')['temperature_c'].shift(1)
    df['temperature_2'] = df.groupby('location_id')['temperature_c'].shift(2)
    
    # Calculate historical means for anomalies
    hist_rain = df.groupby(['location_id', 'month'])['rainfall_mm'].transform('mean')
    hist_temp = df.groupby(['location_id', 'month'])['temperature_c'].transform('mean')
    
    df['rainfall_anomaly'] = df['rainfall_mm'] - hist_rain
    df['temperature_anomaly'] = df['temperature_c'] - hist_temp
    
    # Outbreak target: top 10% of cases per location
    p90 = df.groupby('location_id')['malaria_cases'].transform(lambda x: x.quantile(0.90))
    p90 = p90.fillna(0)
    df['outbreak_target'] = (df['malaria_cases'] > p90).astype(int)
    
    # Drop NaNs resulting from shifts (first few rows per location)
    df = df.dropna(subset=['malaria_lag_1', 'malaria_lag_4', 'rainfall_1', 'rainfall_2', 'temperature_1', 'temperature_2'])
    return df

def save_features(df):
    if df.empty:
        print("No features to save.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM features")
    
    inserted = 0
    for _, row in df.iterrows():
        date_str = f"{int(row['year'])}-{int(row['month']):02d}-01"
        
        cursor.execute('''
            INSERT INTO features (
                location_id, date, malaria_lag_1, malaria_lag_4, 
                rainfall_1, rainfall_2, temperature_1, temperature_2, 
                rainfall_anomaly, temperature_anomaly, population, urban_density, sanitation_index, outbreak_target, dengue_rolling_4
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(row['location_id']), date_str, 
            float(row['malaria_lag_1']), float(row['malaria_lag_4']), 
            float(row['rainfall_1']), float(row['rainfall_2']), 
            float(row['temperature_1']), float(row['temperature_2']), 
            float(row['rainfall_anomaly']), float(row['temperature_anomaly']), 
            int(row['population']), float(row['urban_density']), float(row['sanitation_index']),
            int(row['outbreak_target']), int(row['malaria_cases'])
        ))
        inserted += 1
        
    conn.commit()
    conn.close()
    print(f"Successfully generated and saved {inserted} feature records.")

if __name__ == "__main__":
    print("Fetching raw data from database...")
    raw_df = fetch_data()
    print(f"Fetched {len(raw_df)} raw records.")
    print(f"  - Rows with rainfall data: {raw_df['rainfall_mm'].notna().sum()}")
    print(f"  - Rows with temperature data: {raw_df['temperature_c'].notna().sum()}")
    print("Engineering features (filling climate gaps with median imputation)...")
    features_df = create_features(raw_df)
    print(f"  - Features after lag calculation: {len(features_df)}")
    print("Saving features to database...")
    save_features(features_df)
