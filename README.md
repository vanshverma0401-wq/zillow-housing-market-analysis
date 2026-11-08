# Zillow Home Value Analysis Final Project

Complete 2025 academic final project by **Jake Holley, Miranda Dahl and Vansh Verma**.

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

This publication restores the completed historical project and its saved results.
It does not claim a new notebook execution or model retraining. Raw Zillow CSVs
remain private; the public input manifest records their names, schemas and hashes.
The environment and external Census boundary files still need verification for a
fresh replay. [requirements-notebook.txt](requirements-notebook.txt) lists imports,
not an original environment lock.

New November 2026 audit utilities can be checked without running the original model:

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
