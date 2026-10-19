"""ZIP-level tests. New York: does housing (home size, share of 1-2 family homes) explain summer demand
better than heat and shade? San Diego: does distance from the coast explain it?
Housing: NYC PLUTO 26v2 aggregated by ZIP (data/raw/pluto_zip_housing.csv)."""
import json, numpy as np, pandas as pd, statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, LeaveOneGroupOut, cross_val_predict
from sklearn.metrics import r2_score
from pathlib import Path
R = Path(__file__).resolve().parents[1]; out = {}
def cv(X, y, groups=None, seeds=20):
    res = {}
    for name, mdl in [('linear', LinearRegression()), ('forest', RandomForestRegressor(n_estimators=400, min_samples_leaf=3, random_state=0))]:
        res[name + '_random'] = round(float(np.mean([r2_score(y, cross_val_predict(mdl, X, y, cv=KFold(5, shuffle=True, random_state=s))) for s in range(seeds)])), 2)
        if groups is not None:
            res[name + '_heldout'] = round(float(r2_score(y, cross_val_predict(mdl, X, y, groups=groups, cv=LeaveOneGroupOut()))), 2)
    return res
# ---- New York
z = pd.read_csv(R/'data/raw/coned_zip_summary.csv', dtype={'zip': str})
z['cooling_kwh'] = ((z.summer24_kwh - z.shoulder24_kwh) + (z.summer25_kwh - z.shoulder25_kwh)) / 2
z['peak_kw'] = z.icap25_kw
h = pd.read_csv(R/'data/raw/pluto_zip_housing.csv', dtype={'zip': str})
xw = pd.read_csv(R/'data/zip_to_uhf42.csv', dtype={'zip': str}).sort_values('share', ascending=False).drop_duplicates('zip')
p2 = pd.read_csv('/home/claude/shade-study/data/uhf42_shade.csv').rename(columns={'geo_join_id': 'uhf'})
d = z.merge(h, on='zip').merge(xw[['zip', 'uhf', 'BOROUGH']], on='zip').merge(p2[['uhf', 'surf_temp_f', 'canopy_pct', 'poverty_pct']], on='uhf')
d = d.dropna(subset=['cooling_kwh', 'peak_kw']); d = d[d.accts25 >= 500]
out['ny_n_zips'] = int(len(d))
out['ny_corr'] = {t: {v: round(float(d[t].corr(d[v])), 2) for v in ['sqft_per_unit', 'pct_units_1_2_family', 'surf_temp_f', 'canopy_pct', 'poverty_pct']} for t in ['cooling_kwh', 'peak_kw']}
for t in ['cooling_kwh', 'peak_kw']:
    for label, X in [('heat_shade', ['surf_temp_f', 'canopy_pct', 'poverty_pct']),
                     ('housing', ['sqft_per_unit', 'pct_units_1_2_family']),
                     ('both', ['sqft_per_unit', 'pct_units_1_2_family', 'surf_temp_f', 'canopy_pct', 'poverty_pct'])]:
        f = sm.WLS(d[t], sm.add_constant(d[X]), weights=d.accts25).fit(cov_type='cluster', cov_kwds={'groups': d.uhf})  # canopy, heat, poverty vary by neighborhood
        out[f'ny_{t}_{label}'] = {'r2': round(float(f.rsquared), 2), **{k: {'b': round(float(f.params[k]), 3), 'p': round(float(f.pvalues[k]), 4)} for k in X}}
        out[f'ny_{t}_{label}_cv'] = cv(d[X].values, d[t].values, groups=d.BOROUGH.values)
q = d.pct_units_1_2_family
out['ny_by_housing'] = {lab: {'zips': int(s.sum()), 'cooling_kwh': round(float(np.average(d.cooling_kwh[s], weights=d.accts25[s])), 0), 'peak_kw': round(float(np.average(d.peak_kw[s], weights=d.accts25[s])), 2)}
                        for lab, s in [('mostly apartments (<10% in 1-2 family homes)', q < 10), ('mixed (10-50%)', (q >= 10) & (q < 50)), ('mostly houses (50%+)', q >= 50)]}
d.to_csv(R/'data/ny_zip_results.csv', index=False)
# ---- San Diego (2019, full customer base; San Diego County ZIPs only)
s = pd.read_csv(R/'data/raw/sdge_zip_summary_2018_2019.csv', dtype={'zip': str}).merge(pd.read_csv(R/'data/sd_zip_geo.csv', dtype={'zip': str}), on='zip')
s = s[~s.zip.str.startswith('926')]
s['cooling_kwh'] = s.summer19_kwh - s.shoulder19_kwh
s = s[(s.custs_jul19 >= 500)]
out['sd_n_zips'] = int(len(s)); out['sd_customers'] = int(s.custs_jul19.sum())
cw = lambda c, g=s: float(np.average(g[c], weights=g.custs_jul19))
out['sd_citywide'] = {'summer_kwh': round(cw('summer19_kwh'), 0), 'shoulder_kwh': round(cw('shoulder19_kwh'), 0), 'cooling_kwh': round(cw('cooling_kwh'), 0)}
out['sd_citywide']['summer_vs_shoulder_pct'] = round(100 * (out['sd_citywide']['summer_kwh'] / out['sd_citywide']['shoulder_kwh'] - 1), 0)
out['sd_corr_dist'] = round(float(s.cooling_kwh.corr(s.dist_coast_km)), 2)
out['sd_corr_logdist'] = round(float(s.cooling_kwh.corr(np.log1p(s.dist_coast_km))), 2)
bands = [('coast (under 5 km)', s.dist_coast_km < 5), ('5-15 km', (s.dist_coast_km >= 5) & (s.dist_coast_km < 15)), ('15-30 km', (s.dist_coast_km >= 15) & (s.dist_coast_km < 30)), ('inland (30 km+)', s.dist_coast_km >= 30)]
out['sd_by_distance'] = {lab: {'zips': int(m.sum()), 'customers': int(s.custs_jul19[m].sum()), 'summer_kwh': round(cw('summer19_kwh', s[m]), 0), 'shoulder_kwh': round(cw('shoulder19_kwh', s[m]), 0), 'cooling_kwh': round(cw('cooling_kwh', s[m]), 0)} for lab, m in bands if m.sum()}
f = sm.WLS(s.cooling_kwh, sm.add_constant(np.log1p(s[['dist_coast_km']])), weights=s.custs_jul19).fit(cov_type='HC1')
out['sd_wls_logdist'] = {'r2': round(float(f.rsquared), 2), 'b': round(float(f.params['dist_coast_km']), 1), 'p': round(float(f.pvalues['dist_coast_km']), 5)}
# coast -> inland transfer: train on ZIPs within 10 km, predict the rest
tr, te = s[s.dist_coast_km < 10], s[s.dist_coast_km >= 10]
X = lambda g: np.log1p(g[['dist_coast_km']].values)
lin = LinearRegression().fit(X(tr), tr.cooling_kwh)
rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=3, random_state=0).fit(X(tr), tr.cooling_kwh)
out['sd_coast_to_inland'] = {'train_zips': int(len(tr)), 'test_zips': int(len(te)),
    'linear_r2': round(float(r2_score(te.cooling_kwh, lin.predict(X(te)))), 2), 'forest_r2': round(float(r2_score(te.cooling_kwh, rf.predict(X(te)))), 2),
    'forest_pred_mean': round(float(rf.predict(X(te)).mean()), 0), 'actual_mean': round(float(te.cooling_kwh.mean()), 0)}
out['sd_2018_check_corr'] = round(float((s.summer18_kwh - s.shoulder18_kwh).corr(s.cooling_kwh)), 2)
s.to_csv(R/'data/sd_zip_results.csv', index=False)
(R/'data/zip_results.json').write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
