# Zillow Home Value Analysis Final Project

A **Python data-analysis and machine-learning case study** combining Zillow
housing indicators across metropolitan, neighborhood, city, county and state
levels. The team prepared and joined time-indexed datasets, explored housing
markets, visualized geographic patterns and built an XGBoost regression prototype.

Complete 2025 academic final project by **Jake Holley, Miranda Dahl and Vansh Verma**.

**[Read the complete final project](FINAL_PROJECT.md) · [Explore the original notebook](notebooks/zillow_home_value_analysis.ipynb) · [Browse all 18 figures](FIGURE_GALLERY.md)**

![Original home-value trends for selected top- and bottom-ranked metropolitan groups](assets/figures/home-value-trends.png)

*Original saved chart from Question 1. Groups reflect the team's historical
home-value-growth procedure; these are ZHVI typical-home-value indices and not
current investment recommendations. Data Provided by Zillow Group.*

## New evaluation extension

The [calendar-safe benchmark](REPLAY_EXTENSION.md) adds a runnable, tested metro
baseline with exact calendar joins, train-only scaling and a purged chronological
split. A bounded 50-metro historical run compares fixed Ridge against persistence;
it is separate from the preserved neighborhood XGBoost and financial scenarios.

## Skills demonstrated

| Skill area | Evidence in this project |
| --- | --- |
| **Python, Pandas and NumPy data preparation** | [CSV ingestion, wide-to-long reshaping, multi-key joins and group aggregations](FINAL_PROJECT.md#source-cell-16) |
| **Exploratory data analysis and visualization** | [Housing, rent, inventory and sales comparisons](FIGURE_GALLERY.md) using Matplotlib and Seaborn |
| **Geospatial analysis with GeoPandas** | [State-level map code and saved maps](FINAL_PROJECT.md#source-cell-49); the original duration proxy has documented alignment and unit limitations |
| **Feature engineering and data formats** | [Geographic joins and lagged trend features](FINAL_PROJECT.md#source-cell-53), with CSV and Parquet staging |
| **Machine-learning preprocessing with scikit-learn** | [Median imputation, categorical encoding, scaling and a ColumnTransformer pipeline](FINAL_PROJECT.md#source-cell-57) |
| **Supervised learning with XGBoost regression** | [Original training code, saved diagnostic and feature importance](FINAL_PROJECT.md#source-cell-57); prospective time-series performance remains unvalidated |

## Open the complete final project

- **[Read the full final project](FINAL_PROJECT.md)** — all six questions, original explanations, code, saved outputs and all 18 figures in one GitHub page.
- **[Open the original final notebook](notebooks/zillow_home_value_analysis.ipynb)** — byte-identical to the final notebook recovered from the shared team folder.
- **[Browse all 18 figures](FIGURE_GALLERY.md)** — includes the original ROI and monthly-income scenario charts.

**Data Provided by Zillow Group**

## What the final project contains

| Section | Original project scope |
| --- | --- |
| Data preparation | CSV loading, cleaning, wide-to-long reshaping, geographic joins and feature preparation |
| Question 1 | Which US real-estate markets are doing best? |
| Question 2 | Are sale prices and inventory listings going up or down overall? |
| Question 3 | Should I invest now? Where is the best opportunity? |
| Question 4 | How long does real estate stay on the market before it rents or sells? |
| Model | Preprocessing pipeline, XGBoost training, saved evaluation and feature importance |
| Question 5 | Expected profits and return-on-investment scenarios in selected markets |
| Question 6 | Expected monthly-income scenarios in selected markets |

The notebook and readable report preserve the team's original 2025 analysis,
including its final scenario sections. Later review observations are kept in
[Methods and limitations](METHODS_AND_LIMITATIONS.md), rather than replacing or
removing the original project content. Original projections are historical
classroom outputs; they have not been independently revalidated.

All 18 saved charts are included. A separate original illustrative image,
`oak_grove.png`, was not present in the recovered files; its original reference
is retained and marked in the readable report.

## Verified project artifacts

| Artifact | Verified content |
| --- | --- |
| Complete final notebook | 70 original cells, 46 code cells, all saved outputs and 18 PNG figures |
| Original source identity | SHA-256 `740cf88030647d5e840cc39f58b87a07a6ba1ec985a93417e6c330749189bfb6`; shared-folder and retained copies match |
| Readable final report | Every source cell represented, with original narrative, collapsible code and saved outputs |
| Figure gallery | All 18 original PNGs, including the last two scenario figures |
| Referenced header image | Original `st_thomas.jpg` restored so the notebook header renders |
| Required CSV inputs | All 16 filenames recovered privately; 15 distinct content hashes |

The complete final notebook supersedes the earlier shortened publication copy.
No source cells, conclusions or scenario figures are omitted from the final
notebook. The readable report only remaps local image references for GitHub display
and adds attribution and navigation outside the original content.

## Technical work

The team used Python, Pandas, NumPy, Matplotlib, Seaborn, GeoPandas, Parquet,
scikit-learn preprocessing and XGBoost. The source covers metro exploration,
national housing indicators, state maps, neighborhood-level feature engineering
and a fitted value-modeling prototype.

Supporting evidence:

- [Notebook and source inventory](technical/notebook_inventory.json)
- [Final report mapping](technical/final_report_manifest.json)
- [Figure fingerprints](technical/figure_manifest.json)
- [Input inventory](technical/input_inventory.json)
- [Source reconciliation](technical/source_reconciliation.json)
- [Technical evidence](technical/TECHNICAL_EVIDENCE.md)

## Reproduction status

The November 8 publication restored the completed historical project and its
saved results without a new original-notebook execution or retraining. A separate
[November 10 extension](REPLAY_EXTENSION.md) now includes a bounded real-input
metro benchmark, pinned environment, aggregate results and contract tests. Raw Zillow CSVs
remain private; the public input manifest records their names, schemas and hashes.
The environment and external Census boundary files still need verification for a
fresh replay. [requirements-notebook.txt](requirements-notebook.txt) lists imports,
not an original environment lock.

Install [requirements-replay.txt](requirements-replay.txt) in an isolated Python
3.12 environment, then check both audit utilities and new replay contracts without
running the original model:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

See [review notes](METHODS_AND_LIMITATIONS.md) for the known dataframe-alignment,
metric-label and time-series evaluation issues. These notes are separate from the
complete original final-project artifacts.

## Sources and attribution

**Data Provided by Zillow Group.** Official [housing data](https://www.zillow.com/research/data/),
[ZHVI methodology](https://www.zillow.com/research/zhvi-methodology/) and
[ZORI methodology](https://www.zillow.com/research/methodology-zori-repeat-rent/).
See [data attribution and usage](DATA_AND_USAGE.md) for source and asset boundaries.
