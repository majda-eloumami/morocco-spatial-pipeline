# 🗺️ Morocco Spatial Data Pipeline — HCP 2024 Census

> **A reusable spatial data pipeline that merges Morocco's 2024 Census with commune-level boundaries into a single, analysis-ready GeoJSON.**

This repository builds a clean, fully documented commune-level spatial dataset for Morocco using the 2024 HCP Census. The output GeoJSON can be plugged directly into any spatial econometrics, data science, or mapping project — no preprocessing needed.

---

## 🎯 Objective

The 2024 HCP Census provides rich socioeconomic indicators at the commune level (~1,500 units) but ships as two separate files: a shapefile of commune boundaries and a tabular Excel extract. They share no clean common identifier. This pipeline solves that matching problem using a three-stage strategy and delivers a single spatial file ready for research.

**Output:** one `FINAL_MOROCCO_2024.geojson` covering ~1,500 communes with 30+ socioeconomic variables, English-named and geometry-validated, plus a full descriptive analysis with summary statistics, urban/rural comparisons, and choropleth maps.

---

## 📦 Input Data

| File | Source | Format | Description |
|---|---|---|---|
| `2024_Census.xlsx` | HCP Morocco (2024 Census) | Excel | Commune-level indicators by sex |
| `populaion_commune.zip` | HCP Morocco | Shapefile (zipped) | Commune polygon boundaries |
| `gadm41_MAR_4.shp` | GADM 4.1 | Shapefile (auto-downloaded) | Used for spatial gap-filling only |

> Place the first two files in `data/raw/`. GADM is downloaded automatically on first run.

---

## 📤 Output Files

| File | Location | Description |
|---|---|---|
| `FINAL_MOROCCO_2024.geojson` | `data/processed/` | Full spatial dataset — geometry + all variables |
| `FINAL_MOROCCO_2024.csv` | `data/processed/` | Same dataset without geometry (for tabular analysis) |
| `CODEBOOK.csv` | `outputs/` | Variable dictionary: short name ↔ original French name |
| `DESCRIPTIVE_STATISTICS.xlsx` | `outputs/` | Summary stats, urban/rural comparison, correlations |
| `01_activity_gap_distribution.png` | `figures/` | Histogram + boxplot of activity gap |
| `02_scatter_plots.png` | `figures/` | Activity gap vs key predictors |
| `03_correlation_heatmap.png` | `figures/` | Correlation matrix heatmap |
| `04_choropleth_maps.png` | `figures/` | Spatial distribution maps across communes |

---

## 🔬 Pipeline

### Script 01 — `01_data_cleaning.py` (Data Creation)

| Step | Description |
|---|---|
| 1 | Load Census Excel + HCP shapefile |
| 2 | Strip administrative prefixes from commune names |
| 3 | Direct name merge: HCP polygons ↔ Census rows (~90%+) |
| 4 | Auto-download GADM Level-4 Morocco boundaries |
| 5 | Centroid-based spatial join for unmatched polygons |
| 6 | Intersects fallback for remaining gaps |
| 7 | Province-median imputation for last residuals |
| 8 | Remove Western Sahara communes |
| 9 | Compute gender gap variables (activity, unemployment, illiteracy) |
| 10 | Rename all variables to English short names |
| 11 | Export GeoJSON, CSV, and codebook |

### Script 02 — `02_descriptive_analysis.py` (Descriptive Analysis)

| Step | Description |
|---|---|
| 1 | Load GeoJSON from Script 01 |
| 2 | Overall summary (communes, population, urban/rural split) |
| 3 | Descriptive statistics table (mean, std, min, max) |
| 4 | Urban vs rural comparison with t-tests |
| 5 | Correlation analysis with activity gap |
| 6 | Figure 1: Activity gap distribution + urban/rural boxplot |
| 7 | Figure 2: Scatter plots vs key predictors |
| 8 | Figure 3: Correlation heatmap |
| 9 | Figure 4: Choropleth maps across communes |
| 10 | Export summary tables to Excel |

---

## 📊 Variables in the Final Dataset

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

## 📁 Folder Structure

```
morocco-spatial-pipeline/
├── scripts/
│   ├── 01_data_cleaning.py           ← Data merging & cleaning pipeline
│   └── 02_descriptive_analysis.py    ← Summary stats & visualizations
├── data/
│   ├── raw/                          ← Input files
│   │   ├── 2024_Census.xlsx
│   │   └── populaion_commune.zip
│   └── processed/                    ← Generated outputs
│       ├── FINAL_MOROCCO_2024.geojson
│       └── FINAL_MOROCCO_2024.csv
├── figures/                          ← Auto-generated maps & plots
│   ├── 01_activity_gap_distribution.png
│   ├── 02_scatter_plots.png
│   ├── 03_correlation_heatmap.png
│   └── 04_choropleth_maps.png
├── outputs/
│   ├── CODEBOOK.csv
│   └── DESCRIPTIVE_STATISTICS.xlsx
├── README.md
└── .gitignore
```

---

## ▶️ How to Reproduce

### Requirements

```bash
pip install geopandas pandas numpy matplotlib seaborn scipy openpyxl requests esda libpysal
```

### Steps

1. Place `2024_Census.xlsx` and `populaion_commune.zip` in `data/raw/`
2. Run Script 01 — data cleaning:

```bash
cd morocco-spatial-pipeline
python scripts/01_data_cleaning.py
```

3. Run Script 02 — descriptive analysis:

```bash
python scripts/02_descriptive_analysis.py
```

Works locally and in Google Colab — environment is detected automatically. GADM is downloaded and cached on first run.

---

## 🛠️ Tools & Packages

| Tool | Purpose |
|---|---|
| GeoPandas | Spatial data loading, joining, and export |
| pandas / NumPy | Data wrangling and variable construction |
| requests | GADM auto-download |
| matplotlib / seaborn | Figures and choropleth maps |
| scipy | T-tests for urban/rural comparison |
| esda / libpysal | Spatial autocorrelation (Script 03, coming soon) |

---

## 🔮 Possible Research Uses

This dataset is ready to use as-is for any commune-level study in Morocco:

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
