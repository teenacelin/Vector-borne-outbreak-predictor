import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'vector_predictor.db')
MALARIA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'sivep_malaria_2025.xls')

def ingest_malaria():
    print(f"Loading malaria data from {MALARIA_FILE}...")
    # It's actually a CSV despite the .xls extension
    df = pd.read_csv(MALARIA_FILE, encoding='latin1', on_bad_lines='skip')
    
    # We want to aggregate by municipality, year, month
    print("Aggregating case data...")
    # Use dt_sinto_year, dt_sinto_month
    df = df.dropna(subset=['mun_infe_nome', 'dt_sinto_year', 'dt_sinto_month'])
    
    agg = df.groupby(['mun_infe_nome', 'dt_sinto_year', 'dt_sinto_month']).size().reset_index(name='cases')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM malaria_cases")
    
    # We need to map mun_infe_nome to location_id
    # We will do a simple string match, ignoring accents/encoding for this MVP
    cursor.execute("SELECT location_id, municipality FROM locations")
    locs = cursor.fetchall()
    
    # Very basic normalization to improve matching
    import unicodedata
    def normalize(s):
        if not isinstance(s, str): return ""
        s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
        return s.lower().replace(' ', '')
        
    loc_map = {normalize(m): lid for loc_id, m in locs for lid in [loc_id]}
    
    inserted = 0
    for _, row in agg.iterrows():
        mun = normalize(row['mun_infe_nome'])
        if mun in loc_map:
            loc_id = loc_map[mun]
            cursor.execute('''
                INSERT INTO malaria_cases (location_id, year, month, cases, source)
                VALUES (?, ?, ?, ?, 'SIVEP-Malaria')
            ''', (loc_id, int(row['dt_sinto_year']), int(row['dt_sinto_month']), int(row['cases'])))
            inserted += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted} monthly aggregated malaria records.")

if __name__ == '__main__':
    ingest_malaria()
