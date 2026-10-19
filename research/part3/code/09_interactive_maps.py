"""Interactive ZIP maps for Part 3: hover/tap details, measure switcher, clickable legend, ZIP search,
case-study buttons. Writes data/interactive_maps.json with HTML fragments, CSS and JS."""
import geopandas as gpd, pandas as pd, numpy as np, json, html
from pathlib import Path
R = Path(__file__).resolve().parents[1]
P_NY, P_SD = 0.3566, 0.4363   # 2024 EIA average residential prices, $/kWh
def paths(g, W=560, tol=None):
    minx, miny, maxx, maxy = g.total_bounds; s = W / (maxx - minx); H = (maxy - miny) * s
    if tol: g = g.assign(geometry=g.geometry.simplify(tol, preserve_topology=True))
    out = []
    for _, r in g.iterrows():
        polys = [r.geometry] if r.geometry.geom_type == 'Polygon' else list(r.geometry.geoms)
        d = ''.join('M' + 'L'.join(f'{(x-minx)*s:.1f},{(maxy-y)*s:.1f}' for x, y in ring.coords) + 'Z'
                    for p in polys for ring in [p.exterior] + list(p.interiors))
        out.append((r.zip, d))
    return out, W, H
# ---------- New York
z = gpd.read_file('/home/claude/nycgeo/MODZCTA_2010_WGS1984.geo.json').to_crs(2263)
zc = [c for c in z.columns if c.upper() in ('MODZCTA', 'ZCTA', 'ZIPCODE', 'ZIP')][0]
z['zip'] = z[zc].astype(str).str[:5]; z = z[z.zip != '99999']
ny = pd.read_csv(R/'data/ny_zip_results.csv', dtype={'zip': str})
xw = pd.read_csv(R/'data/zip_to_uhf42.csv', dtype={'zip': str}).sort_values('share', ascending=False).drop_duplicates('zip')
ny = ny.merge(xw[['zip', 'GEONAME']], on='zip', how='left')
nyd = {r.zip: {'n': f'{r.GEONAME}, {r.BOROUGH}', 'peak': round(r.peak_kw, 2), 'cool': round(r.cooling_kwh), 'fam': round(r.pct_units_1_2_family),
               'sqft': int(r.sqft_per_unit), 'can': round(r.canopy_pct, 1), 'pov': round(r.poverty_pct, 1), 'acc': int(r.accts25),
               'usd': round(r.cooling_kwh * 3 * P_NY)} for r in ny.itertuples()}
ny_paths, nyW, nyH = paths(z, tol=250)
# ---------- San Diego
sz = gpd.read_file(R/'data/sd_zips.geojson').to_crs(32611)
sd = pd.read_csv(R/'data/sd_zip_results.csv', dtype={'zip': str})
sd['sep_inc'] = sd.sep19_kwh - sd.shoulder19_kwh
sz = sz[sz.zip.isin(sd.zip)]
sdd = {r.zip: {'cool': round(r.cooling_kwh), 'sep': round(r.sep_inc), 'dist': round(r.dist_coast_km, 1), 'sum': round(r.summer19_kwh),
               'sho': round(r.shoulder19_kwh), 'acc': int(r.custs_jul19), 'usd': round(r.cooling_kwh * 3 * P_SD)} for r in sd.itertuples()}
sd_paths, sdW, sdH = paths(sz, tol=150)
CASES = {
 'sd': [
  ('92107', 'Ocean Beach', 'On the water, 0.9 km from the shore. Summer adds just 14 kWh a month per account, about $18 a summer, among the smallest increases in the county.'),
  ('92037', 'La Jolla', 'Also on the coast, but with bigger homes: these accounts use about 1.6 times as much power as Ocean Beach’s even outside summer, yet summer still adds only 34 kWh a month. Size raises the baseline; the ocean keeps the summer jump small.'),
  ('92020', 'El Cajon', 'About 19 km inland. Summer adds 130 kWh a month per account, roughly $170 a summer, nine times Ocean Beach’s increase.'),
  ('92040', 'Lakeside', 'About 34 km inland. Summer adds 266 kWh a month, about $348 a summer, one of the largest increases in the county. September is higher still, at 374 kWh.'),
 ],
 'ny': [
  ('10307', 'Tottenville, Staten Island', 'The highest peak allocation in the city: 3.38 kW per account, nearly three times Manhattan’s typical level. 95% of homes are in 1–2 family houses averaging about 1,530 sq ft. Summer adds 544 kWh a month, roughly $580 a summer.'),
  ('11362', 'Little Neck, Queens', 'A mix of houses and apartments at the city’s eastern edge, with some of its heaviest tree canopy. 2.39 kW per account; summer adds 261 kWh a month, about $280 a summer.'),
  ('10025', 'Upper West Side, Manhattan', 'Dense apartment buildings with no 1–2 family homes. 1.11 kW per account; summer adds 144 kWh a month, about $154 a summer.'),
  ('10467', 'Fordham–Bronx Park, Bronx', 'One of the poorest areas in the study (32.6% in poverty, fifth-highest of 42 neighborhoods), yet among the lowest tenth of ZIP codes for peak allocation: 1.02 kW. Small apartments explain part of that; the data cannot tell how many households go without air conditioning.'),
 ]}
def fmt_attr(x): return html.escape(json.dumps(x, separators=(',', ':')), quote=True)
def block(cid, title, pths, W, H, data, metrics, cases, label):
    p = ''.join(f'<path data-z="{zp}" d="{d}"></path>' for zp, d in pths)
    btns = ''.join(f'<button type="button" class="im-m" data-m="{k}" aria-pressed="{"true" if i == 0 else "false"}">{html.escape(m["short"])}</button>' for i, (k, m) in enumerate(metrics.items()))
    cbtn = ''.join(f'<button type="button" class="im-case" data-z="{zp}"><b>{i+1}</b>{html.escape(nm)}</button>' for i, (zp, nm, _) in enumerate(cases))
    cards = ''.join(f'<li id="{cid}-c{i+1}"><h4><span>{i+1}</span>{html.escape(nm)} <small>ZIP {zp}</small></h4><p>{html.escape(t)}</p><button type="button" class="im-show" data-z="{zp}">Show on map</button></li>' for i, (zp, nm, t) in enumerate(cases))
    zips = sorted(data)
    return f'''<div class="im" id="{cid}" data-d="{fmt_attr(data)}" data-m="{fmt_attr(metrics)}">
      <div class="im-bar"><div class="im-ms" role="group" aria-label="Measure shown on the map">{btns}</div>
        <label class="im-find"><span>Find a ZIP</span><input type="text" inputmode="numeric" maxlength="5" list="{cid}-zips" id="{cid}-find" placeholder="e.g. {cases[0][0]}"></label>
        <datalist id="{cid}-zips">{''.join(f'<option value="{zz}">' for zz in zips)}</datalist></div>
      <div class="im-stage"><svg class="im-svg" viewBox="0 0 {W} {H:.0f}" role="img" aria-label="{html.escape(label)}">{p}</svg>
        <div class="im-info" aria-live="polite"><p class="im-hint">Hover or tap a ZIP code, or pick a case study below.</p></div></div>
      <div class="im-legend"><p class="im-lt"></p><ol></ol><p class="im-ln">Tap a legend color to highlight those ZIP codes.</p></div>
      <div class="im-cases" role="group" aria-label="Case studies">{cbtn}</div>
      <ol class="im-cards">{cards}</ol>
    </div>'''
NYM = {'peak': {'short': 'Peak share', 'title': 'Share of Con Edison’s summer peak, kW per account (2025)', 'unit': 'kW', 'dec': 2},
       'cool': {'short': 'Summer increase', 'title': 'Extra summer electricity, kWh per account per month (2024–25)', 'unit': 'kWh', 'dec': 0},
       'fam': {'short': 'Houses', 'title': 'Homes in 1–2 family buildings, % of units', 'unit': '%', 'dec': 0},
       'can': {'short': 'Tree canopy', 'title': 'Tree canopy, % of land (neighborhood, 2014)', 'unit': '%', 'dec': 0}}
SDM = {'cool': {'short': 'Jun–Aug increase', 'title': 'Extra summer electricity, kWh per account per month, June–August (2019)', 'unit': 'kWh', 'dec': 0},
       'sep': {'short': 'September increase', 'title': 'Extra electricity in September, kWh per account (2019)', 'unit': 'kWh', 'dec': 0},
       'dist': {'short': 'Distance to coast', 'title': 'Distance from ZIP center to the coast, km', 'unit': 'km', 'dec': 0}}
out = {
 'sd': block('im-sd', 'San Diego', sd_paths, sdW, sdH, sdd, SDM, CASES['sd'], 'Interactive map of San Diego County ZIP codes; extra summer electricity rises from the coast inland.'),
 'ny': block('im-ny', 'New York', ny_paths, nyW, nyH, nyd, NYM, CASES['ny'], 'Interactive map of New York City ZIP codes; peak share is highest on Staten Island and in eastern Queens.'),
}
out['css'] = '''
.im{display:grid;gap:12px;background:var(--paper);border:1px solid var(--rule);padding:14px;min-width:0}
.im-bar{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:end;justify-content:space-between}
.im-ms{display:flex;flex-wrap:wrap;gap:6px}
.im-m{font:inherit;font-size:.85rem;font-weight:600;padding:7px 12px;min-height:36px;border:1px solid var(--rule);background:var(--bg);color:var(--ink-2);cursor:pointer;border-radius:999px}
.im-m[aria-pressed="true"]{background:var(--moss);border-color:var(--moss);color:var(--paper)}
.im-find{display:grid;gap:3px;font-size:.78rem;color:var(--ink-2)}
.im-find input{font:inherit;font-size:16px;width:8.5em;padding:6px 10px;border:1px solid var(--rule);background:var(--bg);color:var(--ink)}
.im-stage{display:grid;grid-template-columns:minmax(0,1fr) 15rem;gap:14px;align-items:start}
.im-svg{width:100%;height:auto;max-height:560px;display:block;touch-action:manipulation}
.im-svg path{fill:var(--mn);stroke:var(--paper);stroke-width:.6;stroke-linejoin:round;cursor:pointer;transition:opacity .15s}
.im-svg path.c0{fill:var(--m0)}.im-svg path.c1{fill:var(--m1)}.im-svg path.c2{fill:var(--m2)}.im-svg path.c3{fill:var(--m3)}.im-svg path.c4{fill:var(--m4)}
.im-svg.dim path:not(.hl){opacity:.18}
.im-svg path.sel{stroke:var(--clay);stroke-width:2.5}
.im-svg path:hover{stroke:var(--ink);stroke-width:1.6}
.im-info{border-left:3px solid var(--clay);padding:4px 0 4px 12px;font-size:.88rem;line-height:1.45;display:grid;gap:4px;min-width:0}
.im-info h4{margin:0;font-size:1rem}
.im-info dl{margin:4px 0 0;display:grid;grid-template-columns:auto auto;gap:3px 10px}
.im-info dt{color:var(--ink-2)}.im-info dd{margin:0;text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.im-hint{color:var(--ink-2);margin:0}
.im-legend{display:grid;gap:6px}
.im-lt{font-size:.85rem;font-weight:600;margin:0}
.im-legend ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.im-legend button{font:inherit;font-size:.8rem;display:flex;align-items:center;gap:6px;padding:5px 9px;min-height:32px;border:1px solid var(--rule);background:var(--bg);color:var(--ink);cursor:pointer;font-variant-numeric:tabular-nums}
.im-legend button[aria-pressed="true"]{border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}
.im-legend i{width:14px;height:14px;display:inline-block}
.im-ln{font-size:.75rem;color:var(--ink-2);margin:0}
.im-cases{display:flex;flex-wrap:wrap;gap:6px}
.im-case,.im-show{font:inherit;font-size:.85rem;padding:6px 11px;min-height:36px;border:1px solid var(--clay);background:transparent;color:var(--clay);cursor:pointer;display:flex;gap:6px;align-items:center}
.im-case b{display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--clay);color:var(--paper);font-size:.75rem}
.im-case[aria-pressed="true"]{background:var(--clay);color:var(--paper)}
.im-case[aria-pressed="true"] b{background:var(--paper);color:var(--clay)}
.im-cards{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.im-cards li{border-top:3px solid var(--clay);background:var(--bg);padding:10px 12px;display:grid;gap:6px;align-content:start;min-width:0}
.im-cards h4{margin:0;font-size:.95rem;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.im-cards h4 span{color:var(--clay)}
.im-cards small{font-weight:500;color:var(--ink-2)}
.im-cards p{margin:0;font-size:.88rem;line-height:1.5;color:var(--ink-2)}
.im-show{justify-self:start;padding:4px 10px;min-height:32px;font-size:.8rem}
.im button:focus-visible,.im input:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
@media (max-width:720px){.im-stage{grid-template-columns:1fr}.im-cards{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){.im-svg path{transition:none}}
'''
out['js'] = r'''<script>
(function(){
 document.querySelectorAll('.im').forEach(function(root){
  var D=JSON.parse(root.dataset.d), M=JSON.parse(root.dataset.m), keys=Object.keys(M);
  var svg=root.querySelector('.im-svg'), info=root.querySelector('.im-info'), leg=root.querySelector('.im-legend ol'), lt=root.querySelector('.im-lt');
  var paths=[].slice.call(svg.querySelectorAll('path')), cur=keys[0], breaks=[], sel=null, hl=null, isNY=root.id==='im-ny';
  function u(x){return x==='%'?'%':' '+x;}
  function f(v,d){return v==null?'no data':Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
  function q(a,p){var i=(a.length-1)*p, lo=Math.floor(i), hi=Math.ceil(i);return a[lo]+(a[hi]-a[lo])*(i-lo);}
  function cls(v){if(v==null)return -1;for(var k=0;k<4;k++){if(v<breaks[k+1])return k;}return 4;}
  function median(k){var a=Object.values(D).map(function(o){return o[k];}).filter(function(v){return v!=null;}).sort(function(a,b){return a-b;});return q(a,.5);}
  function draw(){
   var vals=Object.values(D).map(function(o){return o[cur];}).filter(function(v){return v!=null;}).sort(function(a,b){return a-b;});
   breaks=[0,.2,.4,.6,.8,1].map(function(p){return q(vals,p);});
   paths.forEach(function(p){var o=D[p.dataset.z];var c=o?cls(o[cur]):-1;p.setAttribute('class',(c<0?'':'c'+c)+(p.dataset.z===sel?' sel':'')+(hl!==null&&c===hl?' hl':''));});
   var m=M[cur], d=m.dec; lt.textContent=m.title;
   leg.innerHTML='';
   for(var i=0;i<5;i++){var li=document.createElement('li'),b=document.createElement('button');b.type='button';b.dataset.c=i;b.setAttribute('aria-pressed',hl===i?'true':'false');
    b.innerHTML='<i style="background:var(--m'+i+')"></i>'+f(breaks[i],d)+'–'+f(breaks[i+1],d)+u(m.unit);li.appendChild(b);leg.appendChild(li);}
   var li=document.createElement('li');li.innerHTML='<button type="button" disabled><i style="background:var(--mn)"></i>No data</button>';leg.appendChild(li);
   svg.classList.toggle('dim',hl!==null);
  }
  function show(z){
   var o=D[z];
   if(!o){info.innerHTML='<h4>ZIP '+z+'</h4><p class="im-hint">No data for this ZIP code (fewer than 500 accounts or an incomplete summer).</p>';return;}
   var rows;
   if(isNY) rows=[['Neighborhood',o.n],['Peak share',f(o.peak,2)+' kW'],['Summer increase',f(o.cool,0)+' kWh/mo'],['Extra cost per summer','$'+f(o.usd,0)],['Homes in 1–2 family buildings',f(o.fam,0)+'%'],['Avg home size',f(o.sqft,0)+' sq ft'],['Tree canopy (neighborhood)',f(o.can,1)+'%'],['Poverty (neighborhood)',f(o.pov,1)+'%'],['Residential accounts',f(o.acc,0)]];
   else rows=[['Distance to coast',f(o.dist,1)+' km'],['Summer increase (Jun–Aug)',f(o.cool,0)+' kWh/mo'],['September increase',f(o.sep,0)+' kWh'],['Extra cost per summer','$'+f(o.usd,0)],['Summer use',f(o.sum,0)+' kWh/mo'],['Spring and fall use',f(o.sho,0)+' kWh/mo'],['Residential accounts',f(o.acc,0)]];
   var med=median(cur), v=o[cur], diff=v==null?'':(v>=med?'Above':'Below')+' the city’s middle ZIP code ('+f(med,M[cur].dec)+u(M[cur].unit)+') on this measure.';
   info.innerHTML='<h4>ZIP '+z+'</h4><dl>'+rows.map(function(r){return '<dt>'+r[0]+'</dt><dd>'+r[1]+'</dd>';}).join('')+'</dl><p class="im-hint">'+diff+'</p>';
  }
  function select(z){sel=z;show(z);draw();
   root.querySelectorAll('.im-case').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.z===z?'true':'false');});}
  root.querySelectorAll('.im-m').forEach(function(b){b.addEventListener('click',function(){cur=b.dataset.m;hl=null;
   root.querySelectorAll('.im-m').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});draw();if(sel)show(sel);});});
  leg.addEventListener('click',function(e){var b=e.target.closest('button[data-c]');if(!b)return;var c=+b.dataset.c;hl=(hl===c)?null:c;draw();});
  svg.addEventListener('mouseover',function(e){var p=e.target.closest('path');if(p)show(p.dataset.z);});
  svg.addEventListener('mouseleave',function(){if(sel)show(sel);});
  svg.addEventListener('click',function(e){var p=e.target.closest('path');if(p)select(p.dataset.z);});
  root.querySelectorAll('.im-case,.im-show').forEach(function(b){b.addEventListener('click',function(){select(b.dataset.z);if(b.classList.contains('im-show'))svg.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});});
  var inp=root.querySelector('.im-find input');inp.addEventListener('input',function(){var z=inp.value.trim();if(/^\d{5}$/.test(z)){if(paths.some(function(p){return p.dataset.z===z;}))select(z);else info.innerHTML='<h4>ZIP '+z+'</h4><p class="im-hint">That ZIP code is not on this map.</p>';}});
  draw();
 });
})();
</script>'''
(R/'data/interactive_maps.json').write_text(json.dumps(out))
print({k: len(v) for k, v in out.items()})
