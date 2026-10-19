"""Inline SVG choropleth maps for the draft page (ZIP level).
NY: Con Edison capacity tag (kW of summer peak per household), 2025. SD: extra summer kWh per household, 2019."""
import geopandas as gpd, pandas as pd, numpy as np, html, json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
def svg(gdf, col, fmt, unit, label, W=560, tol=None):
    g = gdf.copy()
    minx, miny, maxx, maxy = g.total_bounds; s = W / (maxx - minx); H = (maxy - miny) * s
    if tol: g['geometry'] = g.geometry.simplify(tol, preserve_topology=True)
    v = g[col].dropna(); br = list(np.quantile(v, [0, .2, .4, .6, .8, 1]))
    def cls(x):
        if pd.isna(x): return 'qn'
        return 'q%d' % min(4, int(np.searchsorted(br[1:-1], x, side='right')))
    def path(geom):
        polys = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
        d = []
        for p in polys:
            for ring in [p.exterior] + list(p.interiors):
                pts = [f'{(x - minx) * s:.1f},{(maxy - y) * s:.1f}' for x, y in ring.coords]
                d.append('M' + 'L'.join(pts) + 'Z')
        return ''.join(d)
    out = [f'<svg class="map" viewBox="0 0 {W} {H:.0f}" role="img" aria-label="{html.escape(label)}">']
    for _, r in g.iterrows():
        val = 'no data' if pd.isna(r[col]) else fmt(r[col]) + ' ' + unit
        out.append(f'<path class="{cls(r[col])}" d="{path(r.geometry)}"><title>ZIP {r.zip}: {val}</title></path>')
    out.append('</svg>')
    legend = '<ol class="mlegend">' + ''.join(f'<li><i class="q{i}"></i>{fmt(br[i])}–{fmt(br[i+1])}</li>' for i in range(5)) + '<li><i class="qn"></i>No data</li></ol>'
    return ''.join(out), legend
# New York
z = gpd.read_file('/home/claude/nycgeo/MODZCTA_2010_WGS1984.geo.json').to_crs(2263)
zc = [c for c in z.columns if c.upper() in ('MODZCTA', 'ZCTA', 'ZIPCODE', 'ZIP')][0]
z['zip'] = z[zc].astype(str).str[:5]; z = z[z.zip != '99999']
ny = pd.read_csv(R/'data/ny_zip_results.csv', dtype={'zip': str})[['zip', 'peak_kw', 'cooling_kwh']]
z = z.merge(ny, on='zip', how='left')
ny_svg, ny_leg = svg(z, 'peak_kw', lambda x: f'{x:.2f}', 'kW', 'Map of New York City ZIP codes shaded by share of summer peak per household; highest on Staten Island and in eastern Queens, lowest in Manhattan, the Bronx and northern Brooklyn.', tol=250)
# San Diego
sz = gpd.read_file(R/'data/sd_zips.geojson').to_crs(32611)
sd = pd.read_csv(R/'data/sd_zip_results.csv', dtype={'zip': str})[['zip', 'cooling_kwh']]
sz = sz.merge(sd, on='zip', how='inner')
sd_svg, sd_leg = svg(sz, 'cooling_kwh', lambda x: f'{x:.0f}', 'kWh', 'Map of San Diego County ZIP codes shaded by extra summer electricity per household; lowest along the coast, rising steadily inland.', tol=150)
(R/'data/maps.json').write_text(json.dumps({'ny_svg': ny_svg, 'ny_leg': ny_leg, 'sd_svg': sd_svg, 'sd_leg': sd_leg}))
print(len(ny_svg), len(sd_svg)); print(ny_leg); print(sd_leg)
