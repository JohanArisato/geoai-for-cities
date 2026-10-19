# How the raw data were pulled (run in a browser console, October 19, 2026)

The data portals are not reachable from the analysis server, so each pull ran in a browser and
saved a per-ZIP summary to `data/raw/`. Each step can be repeated from the public sources.

## New York: data/raw/coned_zip_summary.csv
Source: NYSERDA Utility Energy Registry, Monthly ZIP Code Energy Use (data.ny.gov, dataset g2x3-izm4),
utility "Consolidated Edison", data_class "electricity".
- Fields: "Residential Consumption (R)" (MWh, with number_of_accounts) and "ICAP Capacity Tag (R)" (MW).
- Coverage: July 2023 to June 2026.
- Per ZIP and year (2024, 2025):
  - summer = mean of Jun, Jul, Aug kWh per account
  - shoulder = mean of Apr, May, Oct kWh per account
  - icap25_kw = mean of 2025 monthly capacity tag × 1000 / accounts
- max_month_ratio = largest monthly kWh/account ÷ median month. It flags a Nov–Dec 2023 spike in a
  few ZIPs; those months are not used.

## San Diego: data/raw/sdge_zip_summary_2018_2019.csv
Source: SDG&E Energy Data Request Program (energydata.sdge.com), files SDGE-ELEC-{2018,2019}-Q{2,3,4}.csv.
- Rows: CustomerClass R (residential).
- Measures: summer = mean Jun–Aug kWh per customer; shoulder = mean Apr, May, Oct; sep19 = September 2019.
- Why 2019: July residential customers in these files were 1.32 million in 2019–2020, 1.22 million in 2021
  and 0.34–0.58 million from 2022 on. The drop coincides with the launch of community choice energy
  programs, so later files appear to cover only part of the customer base. That reading is an inference,
  not stated by SDG&E.

## New York housing: data/raw/pluto_zip_housing.csv
Source: NYC MapPLUTO 26v2 (data.cityofnewyork.us, dataset 64uk-42ks).
- Built from lots with unitsres > 0.
- sqft_per_unit = sum(resarea) / sum(unitsres).
- pct_units_1_2_family = residential units in buildings with 1–2 units / all residential units.

## Federal city comparison: data/raw/eia861m_city_utilities.csv
Source: Form EIA-861M, sales to ultimate customers (eia.gov/electricity/data/eia861m), files
sales_ult_cust_2024.xlsx and sales_ult_cust_2025.xlsx (2025 preliminary), read in the browser with SheetJS.
- Utilities: Consolidated Edison Co-NY Inc, Los Angeles Department of Water & Power, Commonwealth Edison Co,
  Arizona Public Service Co, Salt River Project, San Diego Gas & Electric Co.
- Per utility and year:
  - summer = mean Jun–Aug residential MWh × 1000 / customers
  - shoulder = mean Apr, May, Oct, computed the same way
  - price_x10 = annual residential revenue (thousand $) / MWh; multiply by 10 for cents per kWh
- Houston does not appear as a utility in this file.

## Note on raw files
Only the per-ZIP and per-utility summaries above were saved; the full raw API responses were not.
Each pull can be repeated from the public sources with the steps described here.
