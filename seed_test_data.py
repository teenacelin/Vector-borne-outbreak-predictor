import sqlite3
import random
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'cleaned', 'vector_predictor.db')

def seed_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM predictions")
    cursor.execute("DELETE FROM features")
    cursor.execute("DELETE FROM dengue_cases")
    cursor.execute("DELETE FROM locations")

    # 1. Add Locations
    locations = [
        ('Brazil', 'AM', 'Amazonas', 'Manaus', '-3.1190', '-60.0217'),
        ('Brazil', 'AC', 'Acre', 'Rio Branco', '-9.9750', '-67.8249'),
        ('Brazil', 'PE', 'Pernambuco', 'Recife', '-8.0476', '-34.8770')
    ]
    
    for loc in locations:
        cursor.execute("INSERT INTO locations (country, state_code, state_name, municipality, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)", loc)
    
    # 2. Add Dengue Cases (for Seasonal Chart)
    for loc_id in [1, 2, 3]:
        for month in range(1, 13):
            cases = random.randint(50, 500) if month in [1, 2, 3, 4] else random.randint(10, 100)
            cursor.execute("INSERT INTO dengue_cases (location_id, year, month, cases) VALUES (?, 2024, ?, ?)", (loc_id, month, cases))

    # 3. Add Features (for Climate Chart & Hotspots)
    base_date = datetime.date(2024, 1, 1)
    for loc_id in [1, 2, 3]:
        for week in range(20):
            d = base_date + datetime.timedelta(weeks=week)
            cases = random.randint(50, 300) + (week * 10) # Increasing trend
            rain = random.uniform(50, 200)
            temp = random.uniform(25, 32)
            
            cursor.execute('''
                INSERT INTO features (location_id, date, dengue_rolling_4, rainfall_1, temperature_1, rainfall_anomaly, temperature_anomaly) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (loc_id, d.isoformat(), cases, rain, temp, random.uniform(-20, 50), random.uniform(-1, 2)))

    # 4. Add Predictions (for Map & Actions Table)
    pred_date = (base_date + datetime.timedelta(weeks=19)).isoformat()
    for loc_id, risk, prob in [(1, 'VERY HIGH', 0.88), (2, 'HIGH', 0.76), (3, 'MODERATE', 0.45)]:
        cursor.execute('''
            INSERT INTO predictions (location_id, prediction_date, disease, risk_probability, risk_level) 
            VALUES (?, ?, 'dengue', ?, ?)
        ''', (loc_id, pred_date, prob, risk))

    conn.commit()
    conn.close()
    print("Test data seeded successfully into SQLite.")

if __name__ == '__main__':
    seed_db()
