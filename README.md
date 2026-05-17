# Morocco Spatial Data Pipeline — HCP 2024 Census

> **A reusable spatial data pipeline that merges Morocco's 2024 Census with commune-level boundaries into a single, analysis-ready GeoJSON.**

This repository builds a clean, fully documented commune-level spatial dataset for Morocco using the 2024 HCP Census. The output GeoJSON can be plugged directly into any spatial econometrics, data science, or mapping project no preprocessing needed.

---

## Objective

The 2024 HCP Census provides rich socioeconomic indicators at the commune level (~1,500 units) but ships as two separate files: a shapefile of commune boundaries and a tabular Excel extract. They share no clean common identifier. This pipeline solves that matching problem using a three-stage strategy and delivers a single spatial file ready for research.

**Output:** one `FINAL_MOROCCO_2024.geojson` covering ~1,500 communes with 30+ socioeconomic variables, English-named, geometry-validated, and accompanied by a Queen contiguity spatial weights matrix.

---

## Input Data

| File | Source | Format | Description |
|---|---|---|---|
| `2024_Census.xlsx` | HCP Morocco (2024 Census) | Excel | Commune-level indicators by sex |
| `populaion_commune.zip` | HCP Morocco | Shapefile (zipped) | Commune polygon boundaries |
| `gadm41_MAR_4.shp` | GADM 4.1 | Shapefile (auto-downloaded) | Used for spatial gap-filling only |

> Place the first two files in `data/raw/`. GADM is downloaded automatically on first run.

---

## Output Files

| File | Location | Description |
|---|---|---|
| `FINAL_MOROCCO_2024.geojson` | `data/processed/` | Full spatial dataset and geometry + all variables |
| `FINAL_MOROCCO_2024.csv` | `data/processed/` | Same dataset without geometry (for tabular analysis) |
| `CODEBOOK.csv` | `outputs/` | Variable dictionary: short name ↔ original French name |

---

## Pipeline Steps

| Step | Script Section | Description |
|---|---|---|
| 1 | Load data | Read Census Excel + HCP shapefile |
| 2 | Name cleaning | Strip administrative prefixes from commune names |
| 3 | Direct merge | Match HCP polygons to Census rows by name (~90%+) |
| 4 | GADM download | Auto-download GADM Level-4 Morocco boundaries |
| 5 | Centroid join | Spatial join for polygons with no name match |
| 6 | Intersects fallback | Secondary spatial join for remaining gaps |
| 7 | Median imputation | Province-median fill for last residuals |
| 8 | Scope filter | Remove Western Sahara communes |
| 9 | Variable creation | Compute gender gap variables (activity, unemployment, illiteracy) |
| 10 | Rename | Translate all variable names to English short names |
| 11 | Export | Save GeoJSON, CSV, and codebook |

---

## Variables in the Final Dataset

| Category | Variables |
|---|---|
| Identifiers | `commune_code`, `province_code`, `region_code`, `commune_name_fr` |
| Population | `pop_total`, `pop_male`, `pop_female`, `log_pop` |
| Labour market | `activity_rate`, `activity_rate_male`, `activity_rate_female`, `activity_gap` |
| Unemployment | `unemployment`, `unemployment_male`, `unemployment_female`, `unemployment_gap` |
| Education | `illiteracy`, `secondary_edu`, `higher_edu` + gender breakdowns |
| Infrastructure | `electricity`, `water`, `distance_to_road` |
| Demographics | `urban`, `household_size`, `working_age_pop`, `married_pct` + gender breakdowns |
| Gender gaps | `activity_gap`, `unemployment_gap`, `illiteracy_gap` |
| Pipeline | `data_source` (HCP_matched / GADM_fill) |

Full definitions in `outputs/CODEBOOK.csv`.

---

## Folder Structure

```
morocco-spatial-pipeline/
├── scripts/
│   └── 01_data_cleaning.py       ← Full pipeline (single script)
├── data/
│   ├── raw/                      ← Input files (not tracked by git)
│   │   ├── 2024_Census.xlsx
│   │   └── populaion_commune.zip
│   └── processed/                ← Generated outputs
│       ├── FINAL_MOROCCO_2024.geojson
│       └── FINAL_MOROCCO_2024.csv
├── figures/                      ← Auto-generated maps (future scripts)
├── outputs/
│   └── CODEBOOK.csv
├── README.md
└── .gitignore
```

---

## How to Reproduce

### Requirements

```bash
pip install geopandas pandas numpy matplotlib openpyxl requests
```

### Steps

1. Place `2024_Census.xlsx` and `populaion_commune.zip` in `data/raw/`
2. Run:

```bash
cd morocco-spatial-pipeline
python scripts/01_data_cleaning.py
```

Works locally and in Google Colab — environment is detected automatically. GADM is downloaded and cached on first run.

---

## Tools & Packages

| Tool | Purpose |
|---|---|
| GeoPandas | Spatial data loading, joining, and export |
| pandas / NumPy | Data wrangling and variable construction |
| requests | GADM auto-download |
| matplotlib | Diagnostic plots |

---

## Possible Research Uses

This dataset is ready to use as is for any commune-level study in Morocco:

- Spatial econometrics (SAR, SEM, SDM models)
- Gender inequality mapping
- Infrastructure and poverty analysis
- Urban-rural comparisons
- Clustering and regionalization studies

---

## 👩‍💻 Author

**Majda El Oumami**
GitHub: [github.com/majda-eloumami](https://github.com/majda-eloumami)
2024–2025
