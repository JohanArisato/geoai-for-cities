"""San Diego ZIP geography: centroid and distance to the Pacific coast.
ZIP polygons: github.com/OpenDataDE/State-zip-code-GeoJSON (2010 Census ZCTAs).
Coastline: Natural Earth 10m (github.com/nvkelso/natural-earth-vector)."""
import geopandas as gpd, pandas as pd
from shapely.geometry import box
from pathlib import Path
R = Path(__file__).resolve().parents[1]
s = pd.read_csv(R/'data/raw/sdge_zip_summary_2018_2019.csv', dtype={'zip': str})
z = gpd.read_file('/home/claude/zipgeo/ca_california_zip_codes_geo.min.json')
zc = [c for c in z.columns if 'ZCTA' in c.upper() or c.upper().startswith('ZIP')][0]
z['zip'] = z[zc].astype(str).str[:5]
z = z[z.zip.isin(s.zip)].to_crs(32611)
coast = gpd.read_file('/home/claude/ne/geojson/ne_10m_coastline.geojson')
coast = coast[coast.intersects(box(-118.5, 32.4, -116.8, 33.8))].to_crs(32611)
cl = coast.geometry.union_all()
z['dist_coast_km'] = z.geometry.centroid.distance(cl) / 1000
z['area_km2'] = z.area / 1e6
c = z.geometry.centroid.to_crs(4326); z['lon'], z['lat'] = c.x, c.y
z[['zip', 'dist_coast_km', 'area_km2', 'lon', 'lat']].to_csv(R/'data/sd_zip_geo.csv', index=False)
z[['zip', 'geometry']].to_crs(4326).to_file(R/'data/sd_zips.geojson', driver='GeoJSON')
print(len(z), 'of', len(s), 'ZIPs located; missing:', sorted(set(s.zip) - set(z.zip)))
print(z.dist_coast_km.describe().round(1).to_string())
