import sqlite3
import geopandas as gpd
import xarray as xr
from rasterstats import zonal_stats
from affine import Affine
import numpy as np
import os
import json
import datetime
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'vector_predictor.db')
CHIRPS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'chirps-v2.0.2025.days_p25.nc')

def get_locations_gdf():
    print("Fetching locations from DB...")
    conn = sqlite3.connect(DB_PATH, timeout=60)
    # Only fetch a few for testing if needed, or all 5572
    df = pd.read_sql_query("SELECT location_id, geometry FROM locations WHERE geometry IS NOT NULL", conn)
    conn.close()
    
    from shapely.geometry import shape
    df['geometry'] = df['geometry'].apply(lambda x: shape(json.loads(x)))
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf

def process_chirps():
    if not os.path.exists(CHIRPS_PATH):
        print(f"CHIRPS file not found at {CHIRPS_PATH}")
        return
        
    gdf = get_locations_gdf()
    
    print(f"Opening {CHIRPS_PATH}...")
    ds = xr.open_dataset(CHIRPS_PATH)
    
    # We will resample daily data to monthly sum for simplicity in the dashboard
    print("Resampling daily precipitation to monthly sums...")
    monthly_precip = ds['precip'].resample(time='1ME').sum()
    
    lats = monthly_precip.latitude.values
    lons = monthly_precip.longitude.values
    
    # Calculate affine transform from coords
    pixel_size_x = lons[1] - lons[0]
    pixel_size_y = lats[1] - lats[0]
    # Assuming standard orientation: top-left corner
    transform = Affine.translation(lons[0] - pixel_size_x/2, lats[0] - pixel_size_y/2) * Affine.scale(pixel_size_x, pixel_size_y)
    
    conn = sqlite3.connect(DB_PATH, timeout=60)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM precipitation WHERE source='CHIRPS v2.0 NC'")
    
    inserted = 0
    # Process each month
    for time_idx in range(len(monthly_precip.time)):
        date_val = pd.to_datetime(monthly_precip.time.values[time_idx])
        year = date_val.year
        month = date_val.month
        
        print(f"Processing raster for {year}-{month:02d}...")
        
        # Get 2D numpy array for this month. Notice xarray coords might be inverted for rasterstats
        # rasterstats expects origin at top-left.
        # If latitude is increasing (e.g. -49 to 49), we need to flip it.
        data_array = monthly_precip.isel(time=time_idx).values
        
        if lats[0] < lats[-1]:
            # Flip Y axis
            data_array = np.flipud(data_array)
            top_lat = lats[-1] + pixel_size_y/2
            transform = Affine.translation(lons[0] - pixel_size_x/2, top_lat) * Affine.scale(pixel_size_x, -pixel_size_y)
            
        stats = zonal_stats(gdf, data_array, affine=transform, stats=['mean'], nodata=-9999, all_touched=True)
        
        for idx, stat in enumerate(stats):
            mean_val = stat['mean']
            if mean_val is not None and not np.isnan(mean_val):
                loc_id = int(gdf.iloc[idx]['location_id'])
                obs_date = f"{year}-{month:02d}-01"
                
                cursor.execute('''
                    INSERT INTO precipitation (location_id, observation_date, year, month, rainfall_mm, source)
                    VALUES (?, ?, ?, ?, ?, 'CHIRPS v2.0 NC')
                ''', (loc_id, obs_date, year, month, float(mean_val)))
                inserted += 1
                
        # Commit per month to save memory
        conn.commit()

    conn.close()
    print(f"Successfully processed CHIRPS and inserted {inserted} monthly precipitation records.")

if __name__ == '__main__':
    process_chirps()
