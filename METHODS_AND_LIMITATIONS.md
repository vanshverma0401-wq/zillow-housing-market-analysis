# Review notes and limitations

**Data Provided by Zillow Group**

These November 2026 review notes accompany the **complete original 2025 final
project**. They do not replace its narrative or remove any of its questions,
calculations, conclusions or figures. Read the original work in
[FINAL_PROJECT.md](FINAL_PROJECT.md) or the
[complete notebook](notebooks/zillow_home_value_analysis.ipynb).

## Original project and source identity

The shared-team final notebook was recovered on November 8, 2026 and matches the
retained local copy byte-for-byte. The public notebook now preserves all 70 cells,
46 code cells, original saved outputs and 18 PNGs, including Questions 5 and 6.
Its SHA-256 matches the recovered source exactly. The referenced header photograph
is also supplied separately so its original relative image link works.

The project title, team names and feedback-named charts match the course feedback.
An available Canvas attachment did not establish exact submitted-file byte identity;
the verified byte identity is to the shared team's final notebook.

## Metric definitions

ZHVI measures typical home values, not median prices solely for homes that sold.
The national median-sale-price plot uses a separate weekly transaction-price input.
ZORI is an asking-rent index, not collected rental income. The pending-duration
series concerns listing-to-pending time, not time to rent or the full period to
closing. Definitions: [Zillow Research data](https://www.zillow.com/research/data/),
[ZHVI](https://www.zillow.com/research/zhvi-methodology/) and
[ZORI](https://www.zillow.com/research/methodology-zori-repeat-rent/).

## Data and input inventory

All 16 distinct CSV filenames referenced by the notebook are retained privately.
There are 15 distinct content hashes because `msa_values.csv` equals the metro
ZHVI input. Historical date ranges and missing values differ across series.
Availability does not establish valid joins, complete observations or a successful
clean-kernel replay. National aggregates and metro rows should be treated separately.
Current provider downloads may revise past values and need not match these snapshots.

## Legacy market-duration issue

In original source cell 49, `df_q4['Inventory']` is divided by
`df['SalesCount'] + 1`. An earlier loop leaves `df` bound to the separate long-form
sales dataframe. Pandas aligns by row index rather than the intended region/date
keys. The three corresponding saved views inherit that alignment or selection issue.
An inventory/sales ratio also is not a days measure, despite the shared original
chart label. The full original code and images are preserved; this issue has not
been silently repaired or claimed as a validated market-duration result.

## Original label issues

The sales-count and inventory trend panels retain a Home Value axis label.
The national sales-count figure repeats the inventory chart title. The gallery
captions distinguish these original labels from the intended data fields.

## Model evaluation

The original source fits an XGBoost model within a scikit-learn preprocessing
pipeline. Evaluation uses a random 80/20 row split across repeated neighborhoods
and dates. It is not an out-of-time or spatial holdout. Nearby observations and
overlapping target horizons can make prospective performance appear optimistic.

The target uses a 24-row shift after filtering, which is not guaranteed to equal
24 calendar months. The same timing qualification applies to row-based lag features.
Saved metrics, plots and feature importance are original historical diagnostics;
no new chronological backtest, baseline comparison or uncertainty calibration has
been performed here. Feature importance is not a causal explanation.

## Original ROI and monthly-income scenarios

Questions 5 and 6, their original assumptions, narrative and two saved charts are
included in full. They are classroom scenario calculations based on the original
model and cost assumptions. The figures do not establish realized returns or income,
and no independent replay or validation of those projections was performed during
publication. These qualifications accompany the original work instead of omitting it.

## New tooling and remaining work

The audit/export/report-rendering utilities are November 2026 portfolio tools,
separate from the original 2025 implementation. Their tests verify preservation,
privacy boundaries, file mappings and inventory behavior; they do not validate
the original model or financial outcomes.

A future controlled replay should configure the original inputs and environment,
verify the Census boundaries, correct the dataframe alignment and labels, confirm
calendar horizons and evaluate chronologically against meaningful baselines.
No such fresh end-to-end run is claimed by this publication update.
