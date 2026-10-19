"""Robustness checks requested in review: grouped cross-validation (New York, by neighborhood),
per-borough held-out scores, San Diego extrapolation vs. spatial-block tests, September sensitivity,
canopy sensitivity, and accounts per housing unit."""
import json, numpy as np, pandas as pd, statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, cross_val_predict
from sklearn.metrics import r2_score
from sklearn.cluster import KMeans
from pathlib import Path
R = Path(__file__).resolve().parents[1]; out = {}
rf = lambda: RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0)
d = pd.read_csv(R/'data/ny_zip_results.csv', dtype={'zip': str})
HS = ['surf_temp_f', 'canopy_pct', 'poverty_pct']; HO = ['sqft_per_unit', 'pct_units_1_2_family']
for lab, X in [('heat_shade', HS), ('housing', HO), ('both', HO + HS)]:
    y = d.peak_kw.values
    out[f'ny_peak_{lab}_grouped_by_neighborhood'] = round(float(r2_score(y, cross_val_predict(rf(), d[X].values, y, groups=d.uhf, cv=GroupKFold(5)))), 2)
    p = cross_val_predict(rf(), d[X].values, y, groups=d.BOROUGH, cv=LeaveOneGroupOut())
    out[f'ny_peak_{lab}_by_borough'] = {b: round(float(r2_score(y[m], p[m])), 2) for b in sorted(d.BOROUGH.unique()) for m in [d.BOROUGH.values == b]}
X = HO + HS
for lab, extra in [('base', []), ('no_surface_temp', None), ('borough_fe', 'fe'), ('no_staten_island', 'nosi')]:
    g = d[d.BOROUGH != 'Staten Island'] if extra == 'nosi' else d
    cols = [c for c in X if not (extra is None and c == 'surf_temp_f')]
    M = g[cols]
    if extra == 'fe': M = pd.concat([M, pd.get_dummies(g.BOROUGH, drop_first=True, dtype=float)], axis=1)
    res = {}
    for t in ['peak_kw', 'cooling_kwh']:
        f = sm.WLS(g[t], sm.add_constant(M), weights=g.accts25).fit(cov_type='cluster', cov_kwds={'groups': g.uhf})
        res[t] = {'per_10pts': round(float(f.params['canopy_pct'] * 10), 3), 'p': round(float(f.pvalues['canopy_pct']), 3)}
    out[f'canopy_{lab}'] = res
h = pd.read_csv(R/'data/raw/pluto_zip_housing.csv', dtype={'zip': str})
a = d.merge(h[['zip', 'res_units']], on='zip', suffixes=('', '_p'))
a['acct_per_unit'] = a.accts25 / a.res_units_p if 'res_units_p' in a else a.accts25 / a.res_units
q = a.pct_units_1_2_family
out['accounts_per_housing_unit'] = {'apartments': round(float(a.accts25[q < 10].sum() / a.res_units[q < 10].sum()), 2), 'houses': round(float(a.accts25[q >= 50].sum() / a.res_units[q >= 50].sum()), 2)}
s = pd.read_csv(R/'data/sd_zip_results.csv', dtype={'zip': str})
s['sep_inc'] = s.sep19_kwh - s.shoulder19_kwh
bands = [('coast', s.dist_coast_km < 5), ('inland30', s.dist_coast_km >= 30)]
w = lambda c, m: float(np.average(s[c][m], weights=s.custs_jul19[m]))
out['sd_sept_vs_junaug'] = {k: {'jun_aug': round(w('cooling_kwh', m)), 'september': round(w('sep_inc', m))} for k, m in bands}
tr, te = s[s.dist_coast_km < 10], s[s.dist_coast_km >= 10]
lin = LinearRegression().fit(tr[['dist_coast_km']], tr.cooling_kwh)
out['sd_linear_raw_distance_extrapolation'] = {'r2': round(float(r2_score(te.cooling_kwh, lin.predict(te[['dist_coast_km']]))), 2), 'pred_mean': round(float(lin.predict(te[['dist_coast_km']]).mean())), 'actual_mean': round(float(te.cooling_kwh.mean())), 'train_max_km': round(float(tr.dist_coast_km.max()), 1)}
blk = KMeans(6, n_init=10, random_state=0).fit_predict(s[['lon', 'lat']])
Xs = np.log1p(s[['dist_coast_km']].values)
out['sd_spatial_block_cv'] = {'forest': round(float(r2_score(s.cooling_kwh, cross_val_predict(rf(), Xs, s.cooling_kwh, groups=blk, cv=LeaveOneGroupOut()))), 2),
                              'linear': round(float(r2_score(s.cooling_kwh, cross_val_predict(LinearRegression(), Xs, s.cooling_kwh, groups=blk, cv=LeaveOneGroupOut()))), 2)}
out['sd_2018_vs_2019_corr'] = {'pearson': round(float((s.summer18_kwh - s.shoulder18_kwh).corr(s.cooling_kwh)), 2), 'spearman': round(float((s.summer18_kwh - s.shoulder18_kwh).corr(s.cooling_kwh, method='spearman')), 2)}
(R/'data/robustness.json').write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
