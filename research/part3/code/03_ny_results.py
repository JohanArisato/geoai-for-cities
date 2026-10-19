"""New York results. Inputs: data/raw/coned_zip_summary.csv (built in-browser from the NYSERDA
Utility Energy Registry API, dataset g2x3-izm4, Con Edison, 'Residential Consumption (R)' and
'ICAP Capacity Tag (R)'; see code/00_browser_pulls.md) and Part 2's neighborhood data."""
import json, numpy as np, pandas as pd, statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, LeaveOneGroupOut, cross_val_predict
from sklearn.metrics import r2_score
from pathlib import Path
R = Path(__file__).resolve().parents[1]
z = pd.read_csv(R/'data/raw/coned_zip_summary.csv', dtype={'zip': str})
for y in ('24', '25'):
    z[f'cool{y}'] = z[f'summer{y}_kwh'] - z[f'shoulder{y}_kwh']
z['cooling_kwh'] = z[['cool24', 'cool25']].mean(axis=1)      # extra kWh per household per summer month
z['summer_kwh'] = z[['summer24_kwh', 'summer25_kwh']].mean(axis=1)
z['shoulder_kwh'] = z[['shoulder24_kwh', 'shoulder25_kwh']].mean(axis=1)
z['peak_kw'] = z.icap25_kw                                    # household share of summer peak (capacity tag), kW
z = z.dropna(subset=['cooling_kwh', 'peak_kw'])
xw = pd.read_csv(R/'data/zip_to_uhf42.csv', dtype={'zip': str})
m = z.merge(xw, on='zip'); m['w'] = m.accts25 * m.share
agg = lambda c: m.groupby('uhf').apply(lambda g: np.average(g[c], weights=g.w))
u = pd.DataFrame({c: agg(c) for c in ['cooling_kwh', 'summer_kwh', 'shoulder_kwh', 'peak_kw']})
u['households'] = m.groupby('uhf').w.sum().round()
p2 = pd.read_csv('/home/claude/shade-study/data/uhf42_shade.csv').rename(columns={'geo_join_id': 'uhf'})
d = p2.merge(u, left_on='uhf', right_index=True)
out = {'zips_used': int(z.zip.nunique()), 'zips_matched': int(m.zip.nunique()), 'neighborhoods': int(len(d)),
       'households': int(d.households.sum())}
cw = lambda c: float(np.average(d[c], weights=d.households))
out['citywide'] = {k: round(cw(k), 1) for k in ['summer_kwh', 'shoulder_kwh', 'cooling_kwh']} | {'peak_kw': round(cw('peak_kw'), 3)}
out['citywide']['summer_vs_shoulder_pct'] = round(100 * (out['citywide']['summer_kwh'] / out['citywide']['shoulder_kwh'] - 1), 1)
X = ['surf_temp_f', 'canopy_pct', 'poverty_pct']
out['corr'] = {t: {v: round(float(d[t].corr(d[v])), 2) for v in X + ['heat_ed_rate']} for t in ['cooling_kwh', 'peak_kw']}
for t in ['cooling_kwh', 'peak_kw']:
    f = sm.OLS(d[t], sm.add_constant(d[X])).fit(cov_type='HC1')
    out[f'ols_{t}'] = {'r2': round(float(f.rsquared), 3), **{k: {'b': round(float(f.params[k]), 3), 'p': round(float(f.pvalues[k]), 4)} for k in X}}
    fb = sm.OLS(d[t], sm.add_constant(d[X + ['BOROUGH']].pipe(pd.get_dummies, columns=['BOROUGH'], drop_first=True, dtype=float))).fit(cov_type='HC1')
    out[f'ols_{t}_boro_fe'] = {'r2': round(float(fb.rsquared), 3), **{k: {'b': round(float(fb.params[k]), 3), 'p': round(float(fb.pvalues[k]), 4)} for k in X}}
feats = ['surf_temp_f', 'canopy_pct', 'veg_pct', 'poverty_pct']
for t in ['cooling_kwh', 'peak_kw']:
    Xf, y = d[feats].values, d[t].values
    for name, mdl in [('linear', LinearRegression()), ('forest', RandomForestRegressor(n_estimators=500, min_samples_leaf=3, random_state=0))]:
        rk = [r2_score(y, cross_val_predict(mdl, Xf, y, cv=KFold(5, shuffle=True, random_state=s))) for s in range(20)]
        lb = r2_score(y, cross_val_predict(mdl, Xf, y, groups=d.BOROUGH, cv=LeaveOneGroupOut()))
        out[f'{t}_{name}_r2_random'] = round(float(np.mean(rk)), 2); out[f'{t}_{name}_r2_borough'] = round(float(lb), 2)
d = d.sort_values('cooling_kwh', ascending=False)
out['top5_cooling'] = d[['GEONAME', 'BOROUGH', 'cooling_kwh', 'peak_kw', 'canopy_pct', 'poverty_pct']].head(5).round(2).values.tolist()
out['bottom5_cooling'] = d[['GEONAME', 'BOROUGH', 'cooling_kwh', 'peak_kw', 'canopy_pct', 'poverty_pct']].tail(5).round(2).values.tolist()
out['by_borough'] = d.groupby('BOROUGH').apply(lambda g: {'cooling_kwh': round(float(np.average(g.cooling_kwh, weights=g.households)), 1), 'peak_kw': round(float(np.average(g.peak_kw, weights=g.households)), 3)}).to_dict()
d.to_csv(R/'data/ny_uhf42_results.csv', index=False)
(R/'data/ny_results.json').write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
