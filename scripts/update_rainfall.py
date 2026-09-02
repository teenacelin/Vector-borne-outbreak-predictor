import sqlite3
import os
import sys
import datetime
import argparse

# Add parent directory to path to import data_pipeline modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_pipeline.spatial.zonal_stats import calculate_zonal_stats, geometries_to_gdf

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'vector_predictor.db')

def fetch_locations():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT location_id, geometry FROM locations WHERE geometry IS NOT NULL")
    locations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return locations

def update_rainfall(raster_path, year, month, week=None, source="CHIRPS v3"):
    """
    Process a rainfall raster and update the database.
    """
    if not os.path.exists(raster_path):
        print(f"Error: Raster file not found at {raster_path}")
        return

    print("Fetching locations from database...")
    locations = fetch_locations()
    if not locations:
        print("No locations with geometry found in the database.")
        return

    print("Converting to GeoDataFrame...")
    gdf = geometries_to_gdf(locations)

    print(f"Calculating mean rainfall per municipality from {raster_path}...")
    mean_rainfall = calculate_zonal_stats(raster_path, gdf, stat='mean')

    print("Updating database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Observation date defaults to 1st of month if week is not specified, just as an anchor
    obs_date = datetime.date(year, month, 1).isoformat()

    inserted = 0
    for idx, row in gdf.iterrows():
        val = mean_rainfall[idx]
        if val is not None:
            cursor.execute('''
                INSERT INTO precipitation (location_id, observation_date, year, month, week, rainfall_mm, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['location_id'], obs_date, year, month, week, val, source))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted} rainfall records.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process CHIRPS rainfall raster and load to DB.")
    parser.add_argument("--raster", required=True, help="Path to the GeoTIFF raster file")
    parser.add_argument("--year", type=int, required=True, help="Year of the observation")
    parser.add_argument("--month", type=int, required=True, help="Month of the observation")
    parser.add_argument("--week", type=int, default=None, help="Week of the observation (optional)")
    parser.add_argument("--source", default="CHIRPS v3", help="Data source description")
    
    args = parser.parse_args()
    update_rainfall(args.raster, args.year, args.month, args.week, args.source)
