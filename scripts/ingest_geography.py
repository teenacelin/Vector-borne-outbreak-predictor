import sqlite3
import geopandas as gpd
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'vector_predictor.db')
SHP_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'geography', 'gadm41_BRA_2.shp')

def ingest():
    if not os.path.exists(SHP_PATH):
        print(f"File not found: {SHP_PATH}")
        return

    print(f"Loading shapefile from {SHP_PATH}...")
    gdf = gpd.read_file(SHP_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing locations to prevent duplicates
    # NOTE: This will fail if foreign keys are enforced and data exists in other tables
    # For testing, we are ignoring foreign keys or assuming tables are cleared.
    cursor.execute("DELETE FROM locations")
    
    print("Processing and inserting municipalities...")
    inserted = 0
    for _, row in gdf.iterrows():
        country = row.get('COUNTRY', 'Brazil')
        state_name = row.get('NAME_1', '')
        municipality = row.get('NAME_2', '')
        
        # Calculate centroids for easy mapping
        centroid = row.geometry.centroid
        lat = centroid.y
        lon = centroid.x
        
        geom_json = json.dumps(row.geometry.__geo_interface__)
        
        cursor.execute('''
            INSERT INTO locations (country, state_name, municipality, latitude, longitude, geometry)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (country, state_name, municipality, lat, lon, geom_json))
        inserted += 1
        
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted} locations.")

if __name__ == '__main__':
    ingest()
