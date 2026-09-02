import sqlite3
import geopandas as gpd
import xarray as xr
from rasterstats import zonal_stats
from affine import Affine
import numpy as np
import os
import json
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'vector_predictor.db')
ERA5_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'data_stream-moda.nc')

def get_locations_gdf():
    print("Fetching locations from DB...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT location_id, geometry FROM locations WHERE geometry IS NOT NULL", conn)
    conn.close()
    
    from shapely.geometry import shape
    df['geometry'] = df['geometry'].apply(lambda x: shape(json.loads(x)))
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf

def process_temperature():
    if not os.path.exists(ERA5_PATH):
        print(f"Temperature NetCDF not found at {ERA5_PATH}")
        return
        
    gdf = get_locations_gdf()
    
    print(f"Opening {ERA5_PATH}...")
    ds = xr.open_dataset(ERA5_PATH)
    
    monthly_temp = ds['t2m']
    
    lats = monthly_temp.latitude.values
    lons = monthly_temp.longitude.values
    
    pixel_size_x = lons[1] - lons[0]
    pixel_size_y = lats[1] - lats[0]
    transform = Affine.translation(lons[0] - pixel_size_x/2, lats[0] - pixel_size_y/2) * Affine.scale(pixel_size_x, pixel_size_y)
    
    conn = sqlite3.connect(DB_PATH, timeout=60)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM temperature WHERE source='ERA5 NC'")
    
    inserted = 0
    
    for time_idx in range(len(monthly_temp.valid_time)):
        date_val = pd.to_datetime(monthly_temp.valid_time.values[time_idx])
        year = date_val.year
        month = date_val.month
        
        print(f"Processing raster for {year}-{month:02d}...")
        
        data_array = monthly_temp.isel(valid_time=time_idx).values
        
        if lats[0] < lats[-1]:
            data_array = np.flipud(data_array)
            top_lat = lats[-1] + pixel_size_y/2
            transform = Affine.translation(lons[0] - pixel_size_x/2, top_lat) * Affine.scale(pixel_size_x, -pixel_size_y)
            
        stats = zonal_stats(gdf, data_array, affine=transform, stats=['mean'], nodata=-9999, all_touched=True)
        
        for idx, stat in enumerate(stats):
            mean_val = stat['mean']
            if mean_val is not None and not np.isnan(mean_val):
                # Convert Kelvin to Celsius
                temp_c = mean_val - 273.15
                
                loc_id = int(gdf.iloc[idx]['location_id'])
                obs_date = f"{year}-{month:02d}-01"
                
                cursor.execute('''
                    INSERT INTO temperature (location_id, observation_date, year, month, temperature_c, source)
                    VALUES (?, ?, ?, ?, ?, 'ERA5 NC')
                ''', (loc_id, obs_date, year, month, float(temp_c)))
                inserted += 1
                
        conn.commit()

    conn.close()
    print(f"Successfully processed Temperature and inserted {inserted} monthly records.")

if __name__ == '__main__':
    process_temperature()
