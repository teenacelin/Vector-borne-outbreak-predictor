import geopandas as gpd
from rasterstats import zonal_stats
import json

def calculate_zonal_stats(raster_path, polygons_gdf, stat='mean'):
    """
    Calculate zonal statistics from a raster based on polygon boundaries.
    
    Args:
        raster_path (str): Path to the GeoTIFF raster file.
        polygons_gdf (GeoDataFrame): GeoPandas DataFrame containing polygons.
        stat (str): Statistic to calculate ('mean', 'max', 'min', 'sum').
        
    Returns:
        list: A list of the calculated statistics corresponding to each polygon.
    """
    # Ensure geometry is available
    if not isinstance(polygons_gdf, gpd.GeoDataFrame):
        raise ValueError("polygons_gdf must be a GeoPandas GeoDataFrame")

    # Use rasterstats to calculate the statistic
    # Using 'all_touched=True' is generally better for small polygons compared to pixel size
    stats = zonal_stats(polygons_gdf, raster_path, stats=[stat], all_touched=True)
    
    # Extract the requested stat value
    results = [s[stat] for s in stats]
    return results

def geometries_to_gdf(locations):
    """
    Convert a list of database location records (with GeoJSON geometry) to a GeoDataFrame.
    
    Args:
        locations (list of dict): e.g. [{'location_id': 1, 'geometry': '{...}'}]
        
    Returns:
        GeoDataFrame
    """
    import pandas as pd
    from shapely.geometry import shape

    df = pd.DataFrame(locations)
    
    # Convert string GeoJSON geometry to Shapely objects
    # Assuming 'geometry' column contains valid GeoJSON strings
    df['geometry'] = df['geometry'].apply(lambda x: shape(json.loads(x)) if x else None)
    
    # Drop rows without geometry
    df = df.dropna(subset=['geometry'])
    
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    # Assuming standard WGS84 for CHIRPS/CHIRTS and GADM
    gdf.set_crs(epsg=4326, inplace=True)
    
    return gdf
