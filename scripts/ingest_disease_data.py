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
    df = df.dropna(subset=['mun_infe_code', 'dt_sinto_year', 'dt_sinto_month'])
    
    agg = df.groupby(['mun_infe_code', 'dt_sinto_year', 'dt_sinto_month']).size().reset_index(name='cases')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM malaria_cases")
    
    # We will match mun_infe_code to ibge_code
    cursor.execute("SELECT location_id, ibge_code FROM locations")
    locs = cursor.fetchall()
        
    loc_map = {str(ibge).strip(): lid for lid, ibge in locs if ibge}
    
    inserted = 0
    unmatched_rows = 0
    
    for _, row in agg.iterrows():
        # mun_infe_code is often a float in pandas, convert to int then string
        try:
            mun_code = str(int(row['mun_infe_code']))
        except ValueError:
            mun_code = str(row['mun_infe_code']).strip()
            
        if mun_code in loc_map:
            loc_id = loc_map[mun_code]
            cursor.execute('''
                INSERT INTO malaria_cases (location_id, year, month, cases, source)
                VALUES (?, ?, ?, ?, 'SIVEP-Malaria')
            ''', (loc_id, int(row['dt_sinto_year']), int(row['dt_sinto_month']), int(row['cases'])))
            inserted += 1
        else:
            # 6-digit codes (SIVEP) usually match 7-digit IBGE without the last check digit
            # Let's try matching the first 6 digits
            matched = False
            for loc_ibge, lid in loc_map.items():
                if loc_ibge.startswith(mun_code[:6]):
                    loc_id = lid
                    cursor.execute('''
                        INSERT INTO malaria_cases (location_id, year, month, cases, source)
                        VALUES (?, ?, ?, ?, 'SIVEP-Malaria')
                    ''', (loc_id, int(row['dt_sinto_year']), int(row['dt_sinto_month']), int(row['cases'])))
                    inserted += 1
                    matched = True
                    break
            if not matched:
                unmatched_rows += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted} monthly aggregated malaria records.")
    if unmatched_rows > 0:
        print(f"Warning: {unmatched_rows} source rows could not be matched to any IBGE code.")

if __name__ == '__main__':
    ingest_malaria()
