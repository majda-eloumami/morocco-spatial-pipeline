# =============================================================================
# Morocco Spatial Pipeline — Script 02: Descriptive Analysis
# Author: Majda El Oumami
# GitHub: github.com/majda-eloumami
#
# Description:
#   Summary statistics, urban/rural comparison, correlation analysis,
#   and exploratory visualizations for the FINAL_MOROCCO_2024 dataset.
#
# Inputs  (data/processed/):
#   - FINAL_MOROCCO_2024.geojson       ← from Script 01
#
# Outputs (outputs/):
#   - DESCRIPTIVE_STATISTICS.xlsx
#
# Outputs (figures/):
#   - 01_activity_gap_distribution.png
#   - 02_scatter_plots.png
#   - 03_correlation_heatmap.png
#   - 04_choropleth_maps.png
# =============================================================================

# ===== 0. ENVIRONMENT SETUP ==================================================

import os
import sys

IN_COLAB = 'google.colab' in sys.modules

if IN_COLAB:
    from google.colab import drive
    drive.mount('/content/drive')
    BASE_DIR = "/content/drive/MyDrive/morocco-spatial-pipeline"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
FIGURES_DIR   = os.path.join(BASE_DIR, "figures")
OUTPUTS_DIR   = os.path.join(BASE_DIR, "outputs")

for d in [FIGURES_DIR, OUTPUTS_DIR]:
    os.makedirs(d, exist_ok=True)

print(f"Environment : {'Google Colab' if IN_COLAB else 'Local'}")
print(f"Base dir    : {BASE_DIR}")

# ===== 1. IMPORTS ============================================================

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

print("✓ Packages loaded")

# ===== 2. LOAD DATA ==========================================================

print("\n=== Loading Data ===")

gdf = gpd.read_file(os.path.join(PROCESSED_DIR, "FINAL_MOROCCO_2024.geojson"))
print(f"✓ Dataset loaded: {len(gdf)} communes")

# ===== 3. VARIABLE LISTS =====================================================

KEY_VARS   = ['activity_gap', 'unemployment', 'illiteracy',
              'electricity', 'water', 'household_size', 'pop_total']
OUTCOME    = 'activity_gap'
REGRESSORS = ['illiteracy', 'secondary_edu', 'higher_edu', 'unemployment',
              'urban', 'household_size', 'working_age_pop', 'married_pct']

# ===== 4. OVERALL SUMMARY ====================================================

print("\n=== Overall Summary ===")

n_total = len(gdf)
n_urban = (gdf['urban'] == 1).sum()
n_rural = (gdf['urban'] == 0).sum()
pop_tot = gdf['pop_total'].sum()
pop_urb = gdf[gdf['urban'] == 1]['pop_total'].sum()
pop_rur = gdf[gdf['urban'] == 0]['pop_total'].sum()

print(f"  Total communes   : {n_total:,}")
print(f"  Urban communes   : {n_urban:,} ({n_urban/n_total*100:.1f}%)")
print(f"  Rural communes   : {n_rural:,} ({n_rural/n_total*100:.1f}%)")
print(f"  Total population : {pop_tot:,.0f}")
print(f"  Urban population : {pop_urb:,.0f} ({pop_urb/pop_tot*100:.1f}%)")
print(f"  Rural population : {pop_rur:,.0f} ({pop_rur/pop_tot*100:.1f}%)")

# ===== 5. DESCRIPTIVE STATISTICS =============================================

print("\n=== Descriptive Statistics ===")

desc_stats = gdf[KEY_VARS].describe().T.round(3)
print(desc_stats)

# ===== 6. URBAN VS RURAL COMPARISON ==========================================

print("\n=== Urban vs Rural Comparison ===")

comparison_vars = ['activity_gap', 'unemployment', 'illiteracy',
                   'electricity', 'water', 'household_size']

comparison_results = []
for var in comparison_vars:
    urban_vals = gdf[gdf['urban'] == 1][var].dropna()
    rural_vals = gdf[gdf['urban'] == 0][var].dropna()
    t_stat, p_val = stats.ttest_ind(urban_vals, rural_vals)
    comparison_results.append({
        'Variable'   : var,
        'Urban_Mean' : round(urban_vals.mean(), 3),
        'Rural_Mean' : round(rural_vals.mean(), 3),
        'Difference' : round(urban_vals.mean() - rural_vals.mean(), 3),
        'T_Stat'     : round(t_stat, 3),
        'P_Value'    : round(p_val, 6),
        'Sig'        : '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else ''
    })

comparison_df = pd.DataFrame(comparison_results)
print(comparison_df.to_string(index=False))

# ===== 7. CORRELATION WITH ACTIVITY GAP ======================================

print("\n=== Correlation with Activity Gap ===")

corr_vars = ['activity_gap', 'unemployment', 'illiteracy', 'electricity',
             'water', 'household_size', 'urban', 'pop_total',
             'working_age_pop', 'married_pct', 'distance_to_road',
             'secondary_edu', 'higher_edu']

existing_corr = [v for v in corr_vars if v in gdf.columns]
corr_gap      = gdf[existing_corr].corr()[OUTCOME].sort_values(ascending=False)
print(corr_gap.round(3))

# ===== 8. SAVE SUMMARY TABLES ================================================

print("\n=== Saving Summary Tables ===")

with pd.ExcelWriter(os.path.join(OUTPUTS_DIR, "DESCRIPTIVE_STATISTICS.xlsx"),
                    engine='openpyxl') as writer:
    desc_stats.to_excel(writer, sheet_name='Overall_Summary')
    comparison_df.to_excel(writer, sheet_name='Urban_vs_Rural', index=False)
    corr_gap.to_frame().to_excel(writer, sheet_name='Correlations')

print("✓ DESCRIPTIVE_STATISTICS.xlsx saved")

# ===== 9. FIGURE 1: ACTIVITY GAP DISTRIBUTION ================================

print("\n=== Creating Figures ===")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
axes[0].hist(gdf['activity_gap'].dropna(), bins=50,
             edgecolor='white', alpha=0.8, color='#2e86c1')
axes[0].axvline(gdf['activity_gap'].mean(), color='#c0392b',
                linestyle='--', linewidth=2,
                label=f"Mean: {gdf['activity_gap'].mean():.1f} pp")
axes[0].set_title('Distribution of Activity Gap', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Activity Gap (pp)')
axes[0].set_ylabel('Number of Communes')
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)

# Boxplot by urban/rural
urban_data = gdf[gdf['urban'] == 1]['activity_gap'].dropna()
rural_data = gdf[gdf['urban'] == 0]['activity_gap'].dropna()
bp = axes[1].boxplot([urban_data, rural_data], labels=['Urban', 'Rural'],
                      patch_artist=True, widths=0.5)
for patch, color in zip(bp['boxes'], ['#2e86c1', '#117a65']):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[1].set_title('Activity Gap: Urban vs Rural', fontsize=13, fontweight='bold')
axes[1].set_ylabel('Activity Gap (pp)')
axes[1].grid(axis='y', alpha=0.3)

plt.suptitle('Gender Activity Gap — Morocco 2024 Census', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '01_activity_gap_distribution.png'),
            dpi=200, bbox_inches='tight')
plt.show()
print("✓ Figure 1 saved")

# ===== 10. FIGURE 2: SCATTER PLOTS ===========================================

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()

scatter_pairs = [
    ('unemployment',   'Unemployment Rate (%)', '#c0392b'),
    ('illiteracy',     'Illiteracy Rate (%)',   '#884ea0'),
    ('electricity',    'Electricity Access (%)', '#117a65'),
    ('water',          'Water Access (%)',       '#2e86c1'),
    ('household_size', 'Household Size',         '#d4ac0d'),
    ('married_pct',    'Married Population (%)', '#1a5276'),
]

for i, (xvar, xlabel, color) in enumerate(scatter_pairs):
    if xvar not in gdf.columns:
        continue
    clean = gdf[[xvar, OUTCOME]].dropna()
    axes[i].scatter(clean[xvar], clean[OUTCOME], alpha=0.4, color=color, s=15)
    m, b   = np.polyfit(clean[xvar], clean[OUTCOME], 1)
    x_line = np.linspace(clean[xvar].min(), clean[xvar].max(), 100)
    axes[i].plot(x_line, m * x_line + b, color='black', linewidth=1.5)
    axes[i].set_title(f'Activity Gap vs {xlabel}', fontsize=11, fontweight='bold')
    axes[i].set_xlabel(xlabel)
    axes[i].set_ylabel('Activity Gap (pp)')
    axes[i].grid(alpha=0.3)

plt.suptitle('Activity Gap vs Key Predictors', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '02_scatter_plots.png'),
            dpi=200, bbox_inches='tight')
plt.show()
print("✓ Figure 2 saved")

# ===== 11. FIGURE 3: CORRELATION HEATMAP =====================================

corr_subset_vars = [v for v in ['activity_gap', 'unemployment', 'illiteracy',
                                 'electricity', 'water', 'urban', 'household_size',
                                 'working_age_pop', 'married_pct']
                    if v in gdf.columns]

corr_matrix = gdf[corr_subset_vars].corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, square=True, ax=ax,
            cbar_kws={'shrink': 0.8}, linewidths=0.5)
ax.set_title('Correlation Matrix — Key Variables', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '03_correlation_heatmap.png'),
            dpi=200, bbox_inches='tight')
plt.show()
print("✓ Figure 3 saved")

# ===== 12. FIGURE 4: CHOROPLETH MAPS =========================================

fig, axes = plt.subplots(2, 2, figsize=(18, 16))

map_specs = [
    ('activity_gap', 'Activity Gap (pp)',       'RdYlGn_r'),
    ('unemployment', 'Unemployment Rate (%)',    'YlOrRd'),
    ('illiteracy',   'Illiteracy Rate (%)',      'YlOrBr'),
    ('urban',        'Urban (1) / Rural (0)',    'Set2'),
]

for ax, (col, title, cmap) in zip(axes.flatten(), map_specs):
    gdf.plot(
        column       = col,
        cmap         = cmap,
        edgecolor    = 'black',
        linewidth    = 0.08,
        legend       = True,
        ax           = ax,
        missing_kwds = {'color': 'lightgrey', 'label': 'No data'},
        legend_kwds  = {'shrink': 0.7}
    )
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.axis('off')

plt.suptitle('Spatial Distribution — Morocco 2024 Census', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, '04_choropleth_maps.png'),
            dpi=200, bbox_inches='tight')
plt.show()
print("✓ Figure 4 saved")

# ===== 13. FINAL SUMMARY =====================================================

print("\n" + "=" * 60)
print("SCRIPT 02 COMPLETE")
print("=" * 60)
print(f"  Activity gap mean  : {gdf['activity_gap'].mean():.1f} pp")
print(f"  Urban mean         : {gdf[gdf['urban']==1]['activity_gap'].mean():.1f} pp")
print(f"  Rural mean         : {gdf[gdf['urban']==0]['activity_gap'].mean():.1f} pp")
print("\n→ Next: run 03_spatial_analysis.py")
