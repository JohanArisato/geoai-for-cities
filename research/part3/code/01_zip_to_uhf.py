"""Crosswalk from ZIP code areas (MODZCTA 2010) to the 42 UHF neighborhoods used in Part 2.
Area-weighted: each ZIP's share of land falling in each UHF neighborhood.
Source: github.com/nycehs/NYC_geography (MODZCTA_2010_WGS1984.geo.json, UHF42.geo.json)."""
import geopandas as gpd, pandas as pd
from pathlib import Path
G = Path('/home/claude/nycgeo'); OUT = Path(__file__).resolve().parents[1] / 'data'
z = gpd.read_file(G / 'MODZCTA_2010_WGS1984.geo.json').to_crs(2263)
u = gpd.read_file(G / 'UHF42.geo.json').to_crs(2263)
u['uhf'] = pd.to_numeric(u['GEOCODE'], errors='coerce'); u = u.dropna(subset=['uhf']); u['uhf'] = u.uhf.astype(int)
u = u[u.uhf > 0]  # code 0 = airports and large parks, not a neighborhood
zc = [c for c in z.columns if c.upper() in ('MODZCTA', 'ZCTA', 'ZIPCODE', 'ZIP')][0]
z['zip'] = z[zc].astype(str).str[:5]
z = z[z.zip != '99999']  # placeholder polygon (parks)
z['zip_area'] = z.area
x = gpd.overlay(z[['zip', 'zip_area', 'geometry']], u[['uhf', 'GEONAME', 'BOROUGH', 'geometry']], how='intersection')
x['share'] = x.area / x.zip_area
x = x[x.share > 0.01].copy()
x['share'] = x.share / x.groupby('zip').share.transform('sum')
x[['zip', 'uhf', 'GEONAME', 'BOROUGH', 'share']].sort_values(['zip', 'share'], ascending=[True, False]).to_csv(OUT / 'zip_to_uhf42.csv', index=False)
print('ZIP areas:', z.zip.nunique(), '| matched:', x.zip.nunique(), '| neighborhoods:', x.uhf.nunique())
print('ZIPs split across 2+ neighborhoods:', (x.groupby('zip').size() > 1).sum())
