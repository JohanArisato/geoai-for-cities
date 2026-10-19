# Record Heat, Record Demand: Can GeoAI Predict Where the Grid Strains?

Code and data for Part 3 of *GeoAI for Cities* by Jhoven (Johan) Fernandez (working paper, October 2026).
Read it at https://johanarisato.github.io/geoai-for-cities/#part-3

## Question
Where does summer electricity demand climb in New York and San Diego, what explains it, and can a model
built in one place predict another?

## Data (all public)
- New York: NYSERDA Utility Energy Registry, Con Edison residential ZIP data, 2024–2025 (`data/raw/coned_zip_summary.csv`)
- San Diego: SDG&E Energy Data Request Program, residential ZIP data, 2018–2019 (`data/raw/sdge_zip_summary_2018_2019.csv`)
- New York housing: NYC MapPLUTO 26v2 (`data/raw/pluto_zip_housing.csv`)
- City comparison: EIA Form 861M, 2024–2025 (`data/raw/eia861m_city_utilities.csv`)
- Heat, canopy and poverty for New York: Part 2 (github.com/JohanArisato/who-gets-the-shade)
- Boundaries: NYC Health Dept. geography files; Census ZIP areas (OpenDataDE); Natural Earth coastline

`code/00_browser_pulls.md` explains how each raw summary was pulled. Only per-ZIP and per-utility
summaries were saved, not full raw API responses; each pull can be repeated from the public source.

## Code
| Script | What it does |
|---|---|
| 01_zip_to_uhf.py | ZIP → neighborhood crosswalk (New York) |
| 03_ny_results.py | Neighborhood-level results for New York |
| 04_sd_geo.py | San Diego ZIP distance to the coast |
| 05_zip_models.py | ZIP-level models and prediction tests, both cities |
| 06_maps.py, 09_interactive_maps.py | Maps for the web page |
| 07_site_integrate.py | Adds Part 3 to the site |
| 08_robustness.py | Robustness checks (grouped CV, per-borough tests, canopy sensitivity, September comparison) |

Paths in the scripts point to the author's working folders; adjust them to run locally.

## Main limits
Monthly or quarterly totals, not hourly peaks; residential accounts, not households; San Diego uses 2019 only;
area-level associations, not causal effects. See section 9 of the post.
