# =============================================================================
# Morocco Labour Market — Script 01: Data Creation & Cleaning
# Author: Majda El Oumami
# GitHub: github.com/majda-eloumami
#
# Description:
#   Merges HCP commune boundaries with 2024 Census data using direct name
#   matching and GADM spatial join for gap filling. Creates gender gap
#   variables and saves the final analysis-ready dataset.
#
# Inputs  (data/raw/):
#   - 2024_Census.xlsx
#   - populaion_commune.zip
#
# Outputs (data/processed/):
#   - FINAL_MOROCCO_2024.geojson
#   - FINAL_MOROCCO_2024.csv
#   - spatial_weights_queen.pkl
#
# Outputs (outputs/):
#   - CODEBOOK.csv
# =============================================================================

# ===== 0. ENVIRONMENT SETUP ==================================================

import os
import sys

IN_COLAB = 'google.colab' in sys.modules

if IN_COLAB:
    os.system("pip install geopandas libpysal esda spreg -q")
    from google.colab import drive
    drive.mount('/content/drive')
    BASE_DIR      = "/content/drive/MyDrive/morocco-labour-cleaning"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR       = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
FIGURES_DIR   = os.path.join(BASE_DIR, "figures")
OUTPUTS_DIR   = os.path.join(BASE_DIR, "outputs")

for d in [RAW_DIR, PROCESSED_DIR, FIGURES_DIR, OUTPUTS_DIR]:
    os.makedirs(d, exist_ok=True)

print(f"Environment : {'Google Colab' if IN_COLAB else 'Local'}")
print(f"Base dir    : {BASE_DIR}")
print(f"Raw data    : {RAW_DIR}")
print(f"Processed   : {PROCESSED_DIR}")

# ===== 1. IMPORTS ============================================================

import geopandas as gpd
import pandas as pd
import numpy as np
import re
import zipfile
import requests
import matplotlib.pyplot as plt

print("\n✓ Packages loaded")

# ===== 2. LOAD CENSUS DATA ===================================================

print("\n=== Loading Census Data ===")

census = pd.read_excel(os.path.join(RAW_DIR, "2024_Census.xlsx"))
census['census_clean'] = census['Libelle Français'].str.lower().str.strip()

print(f"✓ Census loaded: {len(census)} communes")

# ===== 3. LOAD HCP SHAPEFILE =================================================

print("\n=== Loading HCP Commune Boundaries ===")

zip_path     = os.path.join(RAW_DIR, "populaion_commune.zip")
extract_path = os.path.join(RAW_DIR, "hcp_communes_2024")

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

shp_files = [f for f in os.listdir(extract_path) if f.endswith('.shp')]
hcp_all   = gpd.read_file(os.path.join(extract_path, shp_files[0]))

print(f"✓ HCP loaded: {len(hcp_all)} polygons")

# ===== 4. CLEAN HCP COMMUNE NAMES ============================================

print("\n=== Cleaning HCP Commune Names ===")

def clean_hcp_name(name):
    """Strip administrative prefixes from commune names for matching."""
    if pd.isna(name):
        return None
    name = str(name).lower().strip()
    name = re.sub(r"^commune\s+d[e'u]?\s*", '', name)
    name = re.sub(r"^commune\s+des\s+",     '', name)
    name = re.sub(r"^commune\s+",           '', name)
    name = re.sub(r"^méchouar\s+(de\s+)?",  '', name)
    name = re.sub(r"^ensemble\s+du\s+territoire.*$", '', name)
    name = name.strip()
    return name if name else None

hcp_all['nom_clean'] = hcp_all['nom'].apply(clean_hcp_name)
hcp_all['nom_clean'] = hcp_all['nom_clean'].str.replace('*', '', regex=False).str.strip()
hcp_all.loc[hcp_all['nom_clean'] == 'casablanca', 'nom_clean'] = 'méchouar-kasba'

print(f"  With names    : {hcp_all['nom_clean'].notna().sum()}")
print(f"  Without names : {hcp_all['nom_clean'].isna().sum()}")

# ===== 5. DIRECT MERGE: HCP + CENSUS =========================================

print("\n=== Step 1: Direct Name Matching ===")

hcp_named = hcp_all[hcp_all['nom_clean'].notna()].copy()

hcp_with_census = hcp_named.merge(
    census,
    left_on  = 'nom_clean',
    right_on = 'census_clean',
    how      = 'left',
    indicator= True
)

direct_matched   = hcp_with_census[hcp_with_census['_merge'] == 'both'].copy()
direct_unmatched = hcp_with_census[hcp_with_census['_merge'] == 'left_only'].copy()

# Drop duplicates keeping first match
direct_matched = direct_matched.drop_duplicates(subset='Code_Commu', keep='first')

print(f"  Direct matches  : {len(direct_matched)}")
print(f"  Named unmatched : {len(direct_unmatched)}")

# ===== 6. GADM DOWNLOAD & GAP FILLING ========================================

print("\n=== Step 2: GADM Download for Gap Filling ===")

gadm_path = os.path.join(RAW_DIR, "morocco_gadm")

if not os.path.exists(os.path.join(gadm_path, "gadm41_MAR_4.shp")):
    print("  Downloading GADM Morocco shapefile...")
    url      = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_MAR_shp.zip"
    response = requests.get(url, stream=True)
    zip_gadm = os.path.join(RAW_DIR, "morocco_gadm.zip")
    with open(zip_gadm, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    with zipfile.ZipFile(zip_gadm, "r") as zip_ref:
        zip_ref.extractall(gadm_path)
    print("  ✓ GADM downloaded")
else:
    print("  ✓ GADM already cached locally")

gadm_morocco           = gpd.read_file(os.path.join(gadm_path, "gadm41_MAR_4.shp"))
gadm_morocco['gadm_clean'] = gadm_morocco['NAME_4'].str.lower().str.strip()

gadm_with_census = gadm_morocco.merge(
    census,
    left_on  = 'gadm_clean',
    right_on = 'census_clean',
    how      = 'left',
    indicator= True
)
gadm_matched = gadm_with_census[gadm_with_census['_merge'] == 'both'].copy()
print(f"  ✓ GADM matched to census: {len(gadm_matched)}")

# ===== 7. SPATIAL JOIN: FILL NO-NAME POLYGONS ================================

print("\n=== Step 3: Spatial Join for No-Name Polygons ===")

hcp_no_name = hcp_all[hcp_all['nom_clean'].isna()].copy()
print(f"  No-name polygons to fill: {len(hcp_no_name)}")

# Fix geometries
hcp_no_name['geometry']          = hcp_no_name.geometry.buffer(0)
gadm_matched_fixed               = gadm_matched.to_crs(hcp_no_name.crs).copy()
gadm_matched_fixed['geometry']   = gadm_matched_fixed.geometry.buffer(0)

# Centroid-based spatial join
hcp_no_name_proj = hcp_no_name.to_crs('EPSG:26191')
hcp_no_name      = hcp_no_name.copy()
hcp_no_name['centroid'] = hcp_no_name_proj.geometry.centroid.to_crs(hcp_no_name.crs)

centroids_gdf = gpd.GeoDataFrame(
    hcp_no_name[['Code_Commu']],
    geometry = hcp_no_name['centroid'],
    crs      = hcp_no_name.crs
)

census_cols     = [c for c in census.columns if c != 'census_clean']
gadm_cols_exist = ['geometry'] + [c for c in census_cols if c in gadm_matched.columns]

centroid_join = gpd.sjoin(
    centroids_gdf,
    gadm_matched_fixed[gadm_cols_exist],
    how       = 'left',
    predicate = 'within'
)

# Fallback: intersects for remaining unmatched
still_empty = centroid_join[centroid_join['Libelle Français'].isna()]['Code_Commu'].tolist()

if len(still_empty) > 0:
    still_geom      = hcp_no_name[hcp_no_name['Code_Commu'].isin(still_empty)][['geometry', 'Code_Commu']]
    intersects_join = gpd.sjoin(still_geom, gadm_matched_fixed[gadm_cols_exist],
                                how='left', predicate='intersects')
    for idx, row in intersects_join.iterrows():
        mask = centroid_join['Code_Commu'] == row['Code_Commu']
        for col in gadm_cols_exist:
            if col != 'geometry' and pd.notna(row.get(col)):
                centroid_join.loc[mask, col] = row[col]

centroid_join = centroid_join.drop_duplicates(subset='Code_Commu', keep='first')
print(f"  ✓ Filled: {centroid_join['Libelle Français'].notna().sum()}/{len(hcp_no_name)}")

# Merge back to original geometries
fill_cols = [c for c in centroid_join.columns
             if c not in ['geometry', 'index_right', 'centroid']]

no_name_with_data = hcp_no_name[['geometry', 'Code_Commu']].merge(
    centroid_join[fill_cols], on='Code_Commu', how='left'
)
no_name_with_data = gpd.GeoDataFrame(no_name_with_data, geometry='geometry',
                                      crs=hcp_no_name.crs)
no_name_with_data['data_source'] = 'GADM_fill'

# ===== 8. COMBINE ALL DATA ===================================================

print("\n=== Step 4: Combining All Data ===")

direct_matched['data_source'] = 'HCP_matched'

common_cols    = list(set(direct_matched.columns) & set(no_name_with_data.columns))
final_complete = gpd.GeoDataFrame(
    pd.concat([
        direct_matched[common_cols].reset_index(drop=True),
        no_name_with_data[common_cols].reset_index(drop=True)
    ], ignore_index=True),
    geometry = 'geometry',
    crs      = hcp_all.crs
)

# Fill last missing with province median
last_missing = final_complete[final_complete['Libelle Français'].isna()]
for idx, row in last_missing.iterrows():
    code     = row['Code_Commu']
    province = code.split('.')[1] if pd.notna(code) else None
    if province:
        same_province = final_complete[
            final_complete['Code_Commu'].str.contains(f'.{province}.', na=False) &
            final_complete['Libelle Français'].notna()
        ]
        if len(same_province) > 0:
            for col in census.columns:
                if col in final_complete.columns and col not in ['Libelle Français', 'Libelle Arabe', 'census_clean']:
                    if pd.api.types.is_numeric_dtype(final_complete[col]):
                        final_complete.loc[idx, col] = same_province[col].median()
            final_complete.loc[idx, 'Libelle Français'] = f"Unknown_{code}"
            final_complete.loc[idx, 'census_clean']     = f"unknown_{code}"

print(f"✓ Total communes : {len(final_complete)}")
print(f"  HCP matched    : {(final_complete['data_source'] == 'HCP_matched').sum()}")
print(f"  GADM filled    : {(final_complete['data_source'] == 'GADM_fill').sum()}")
print(f"  Coverage       : {final_complete['Libelle Français'].notna().sum()/len(final_complete)*100:.1f}%")

# ===== 9. REMOVE WESTERN SAHARA ==============================================

print("\n=== Step 5: Removing Western Sahara Communes ===")

ws_names = {'mijik', 'zoug', 'aghouinite', 'lagouira'}
mask_ws  = final_complete['Libelle Français'].str.lower().str.strip().isin(ws_names)

print(f"  Removing {mask_ws.sum()} Western Sahara communes")

final_complete = final_complete.loc[~mask_ws].copy().reset_index(drop=True)

print(f"✓ After removal : {len(final_complete)} communes")

# ===== 10. CREATE GENDER GAP VARIABLES =======================================

print("\n=== Step 6: Creating Gender Gap Variables ===")

final_complete['activity_gap'] = (
    final_complete["Taux d'activité des 15 ans et plus (%): Masculins"] -
    final_complete["Taux d'activité des 15 ans et plus (%): Féminins"]
)
final_complete['unemployment_gap'] = (
    final_complete['Taux de chômage (%): Masculins'] -
    final_complete['Taux de chômage (%): Féminins']
)
final_complete['illiteracy_gap'] = (
    final_complete["Taux d'analphabétisme des 10 ans et plus (%): Masculins"] -
    final_complete["Taux d'analphabétisme des 10 ans et plus (%): Féminins"]
)
final_complete['pop_total'] = (
    final_complete['Population municipale (Effectif): Masculins'] +
    final_complete['Population municipale (Effectif): Féminins']
)
final_complete['unemployment'] = (
    final_complete['Taux de chômage (%): Masculins'] +
    final_complete['Taux de chômage (%): Féminins']
) / 2
final_complete['illiteracy'] = (
    final_complete["Taux d'analphabétisme des 10 ans et plus (%): Masculins"] +
    final_complete["Taux d'analphabétisme des 10 ans et plus (%): Féminins"]
) / 2

print("✓ Gap variables created: activity_gap, unemployment_gap, illiteracy_gap")

# ===== 11. RENAME VARIABLES TO ENGLISH =======================================

print("\n=== Step 7: Renaming Variables to English ===")

rename_dict = {
    'Code_Commu'   : 'commune_code',
    'Code_Provi'   : 'province_code',
    'CODE_REGIO'   : 'region_code',
    'Libelle Français' : 'commune_name_fr',
    'Libelle Arabe'    : 'commune_name_ar',
    'census_clean'     : 'commune_name_clean',
    'activity_gap'     : 'activity_gap',
    'unemployment_gap' : 'unemployment_gap',
    'illiteracy_gap'   : 'illiteracy_gap',
    'pop_total'        : 'pop_total',
    'Population municipale (Effectif): Masculins' : 'pop_male',
    'Population municipale (Effectif): Féminins'  : 'pop_female',
    "Taux d'activité des 15 ans et plus (%): Ensemble"   : 'activity_rate',
    "Taux d'activité des 15 ans et plus (%): Masculins"  : 'activity_rate_male',
    "Taux d'activité des 15 ans et plus (%): Féminins"   : 'activity_rate_female',
    'unemployment'                                  : 'unemployment',
    'Taux de chômage (%): Ensemble'                 : 'unemployment_census',
    'Taux de chômage (%): Masculins'                : 'unemployment_male',
    'Taux de chômage (%): Féminins'                 : 'unemployment_female',
    'illiteracy'                                    : 'illiteracy',
    "Taux d'analphabétisme des 10 ans et plus (%): Ensemble"  : 'illiteracy_census',
    "Taux d'analphabétisme des 10 ans et plus (%): Masculins" : 'illiteracy_male',
    "Taux d'analphabétisme des 10 ans et plus (%): Féminins"  : 'illiteracy_female',
    "Population selon le niveau d'études_Secondaire qualifiant (%): Ensemble"  : 'secondary_edu',
    "Population selon le niveau d'études_Secondaire qualifiant (%): Masculins" : 'secondary_edu_male',
    "Population selon le niveau d'études_Secondaire qualifiant (%): Féminins"  : 'secondary_edu_female',
    "Population selon le niveau d'études_Supérieur (%): Ensemble"  : 'higher_edu',
    "Population selon le niveau d'études_Supérieur (%): Masculins" : 'higher_edu_male',
    "Population selon le niveau d'études_Supérieur (%): Féminins"  : 'higher_edu_female',
    'Électricité (%): Ensemble'  : 'electricity',
    'Eau courante (%): Ensemble' : 'water',
    "Conditions d'habitat: Distance moyenne des logements à la route goudronnée - R (km)" : 'distance_to_road',
    'Urbain '                    : 'urban',
    'Taille moyenne des ménages (Nombre): Ensemble'             : 'household_size',
    'Proportion de la population âgée de 15 à 59 ans (%): Ensemble'  : 'working_age_pop',
    'Proportion de la population âgée de 15 à 59 ans (%): Masculins' : 'working_age_pop_male',
    'Proportion de la population âgée de 15 à 59 ans (%): Féminins'  : 'working_age_pop_female',
    'Proportion des mariés agés de 15ans et plus(%): Ensemble'   : 'married_pct',
    'Proportion des mariés agés de 15ans et plus(%): Masculins'  : 'married_pct_male',
    'Proportion des mariés agés de 15ans et plus(%): Féminins'   : 'married_pct_female',
    'data_source' : 'data_source',
    'nom'         : 'hcp_name_fr',
    'nom_arabe'   : 'hcp_name_ar',
    'nom_clean'   : 'hcp_name_clean',
}

existing_renames = {k: v for k, v in rename_dict.items() if k in final_complete.columns}
final_complete   = final_complete.rename(columns=existing_renames)

# Log-transform population
final_complete['log_pop'] = np.log(final_complete['pop_total'].replace(0, np.nan))

print(f"✓ Renamed {len(existing_renames)} variables")

# ===== 12. FIX GEOMETRIES ====================================================

print("\n=== Step 8: Fixing Geometries ===")

final_complete['geometry'] = final_complete.geometry.buffer(0)
print(f"  Valid geometries: {final_complete.geometry.is_valid.sum()}/{len(final_complete)}")

# ===== 13. SAVE OUTPUTS ======================================================

print("\n=== Step 9: Saving Outputs ===")

# GeoJSON
geojson_path = os.path.join(PROCESSED_DIR, "FINAL_MOROCCO_2024.geojson")
final_complete.to_file(geojson_path, driver='GeoJSON')
print(f"✓ {geojson_path}")

# CSV (no geometry)
csv_path = os.path.join(PROCESSED_DIR, "FINAL_MOROCCO_2024.csv")
final_complete.drop(columns='geometry').to_csv(csv_path, index=False)
print(f"✓ {csv_path}")

# Codebook
codebook = pd.DataFrame([
    {'variable': short, 'original_name': orig}
    for orig, short in existing_renames.items()
])
codebook.to_csv(os.path.join(OUTPUTS_DIR, "CODEBOOK.csv"), index=False)
print(f"✓ CODEBOOK.csv")

# ===== 14. FINAL SUMMARY =====================================================

print("\n" + "=" * 60)
print("SCRIPT 01 COMPLETE")
print("=" * 60)
print(f"  Total communes : {len(final_complete)}")
print(f"  Coverage       : {final_complete['commune_name_fr'].notna().sum()/len(final_complete)*100:.1f}%")
print(f"  Activity gap μ : {final_complete['activity_gap'].mean():.1f} pp")
print(f"  Urban communes : {(final_complete['urban']==1).sum()}")
print(f"  Rural communes : {(final_complete['urban']==0).sum()}")
print("\n→ Next: run 02_descriptive_analysis.py")
