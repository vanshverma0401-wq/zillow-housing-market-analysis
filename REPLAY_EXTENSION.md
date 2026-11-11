# Post-submission calendar-safe housing benchmark

**Added November 10, 2026. Data Provided by Zillow Group.** This is a separate,
bounded metro-level benchmark and keyed inventory/sales reconciliation. It
preserves the complete original 2025 team notebook, its 18 figures and ROI/income
scenarios. It does not rerun or overwrite the original neighborhood XGBoost model.

The extension demonstrates **Pandas key validation, calendar-aware feature
engineering, purged chronological evaluation, train-only preprocessing,
regression baselines, reproducible CLIs and automated tests**.

## Source identity

The shared-team final notebook was rechecked November 10, 2026 and remains
SHA-256 `740cf88030647d5e840cc39f58b87a07a6ba1ec985a93417e6c330749189bfb6`.
This establishes byte identity to the shared final notebook, not to a downloadable
Canvas submission attachment. The fresh course-page review showed project title,
authors and feedback; exact Canvas attachment byte identity remains unestablished.
Private URLs, local paths and source CSVs are not published.

The new benchmark uses three retained historical input snapshots:

| Input | SHA-256 |
| --- | --- |
| Metro ZHVI | `721f78a04459583c5d675e9a23b359e571680ac5a5d0e2128c06ac20dba837ac` |
| Metro for-sale inventory | `e1d76f872d7e821823eb5fe6c58f02ead0b9235d67b91913cf5399559988f00b` |
| Metro sales count | `624ed073eba4f43d7cf5baf92189ad9747b147b835e06bed6d57c29a6659915a` |

See [input inventory](technical/input_inventory.json) for exact filenames and
[data attribution and usage](DATA_AND_USAGE.md) before obtaining permitted inputs.
Current downloads may revise historical values and yield different results.

## Correct contracts, separate scope

| Original limitation | Extension behavior | What it does not establish |
| --- | --- | --- |
| Inventory divided by unrelated dataframe rows | One-to-one outer join on RegionID and month; duplicate keys rejected; unmatched/missing/zero/invalid rows remain explicit | A days-on-market statistic |
| Denominator uses sales + 1 | Exact inventory/monthly-sales ratio; zero sales is unavailable, not artificially smoothed | Listing-to-pending duration |
| 24-row shift after filtering | Future value looked up by the same region and **exactly 24 calendar months**; missing months stay missing | Point-in-time source vintages |
| Row-based feature lags | Exact 12- and 24-month same-region lookups | Availability before the actual publication lag of each input |
| Random split of repeated time observations | Train target dates strictly before the first test origin; horizon-crossing rows purged | Unseen-geography generalization |
| No simple independent baseline | Fixed Ridge compared with unchanged current value | Validation of the original XGBoost or ROI scenarios |

## Bounded evaluation design

Use the first 50 numeric metro RegionIDs (country aggregate excluded). This is a
transparent deterministic **convenience cohort**, not a representative random
sample. Keep positive finite ZHVI; derive log current value and trailing
12-/24-month log returns. Predict the 24-month future log return. All predictors
are computed from the current or earlier observation month; no target appears
in the feature matrix. The snapshots themselves are revised histories rather
than vintage-correct real-time information.

The chronological cutoff is January 31, 2021. Training targets must occur before
that date. Fit StandardScaler and a fixed Ridge (`alpha=1`) on training only.
There was no parameter search, test tuning or validation-based selection.

| Row disposition | Count |
| --- | ---: |
| Retained positive ZHVI observations | 12,359 |
| Missing exact lag/future or other unusable feature/target | 2,471 |
| Eligible complete observations | 9,888 |
| Training | 7,344 |
| Purged pre-cutoff origins whose targets cross the cutoff | 1,196 |
| Test | 1,348 |

Training origins run January 2002–December 2018; the latest training target is
December 2020. Test origins run January 2021–March 2023, with future targets
through March 2025. No training target reaches the first test origin. A
unit test checks this purge condition directly.

## Actual bounded result

[Aggregate machine-readable report](technical/replay/metro_benchmark_2026-11-10.json)
records exact dates, counts, model settings, input hashes and environment.

| Metric, 1,348 test rows | Unchanged-value baseline | Fixed Ridge |
| --- | ---: | ---: |
| Mean absolute error, ZHVI amount units | 24,849.52 | 13,357.26 |
| Median absolute percentage error | 9.90% | 4.65% |
| Root mean squared log error | 0.126 | 0.070 |

Ridge outperforms persistence on **this cohort and historical snapshot**. Same
metros occur in both periods; monthly 24-month targets overlap and errors are
dependent. There is no independent confidence interval, geography holdout,
vintage-safe forecasting claim or investment-return conclusion. The scores are
not directly comparable to the original neighborhood XGBoost diagnostics.

Inventory/sales reconciliation yields **425 comparable region-months**, 3,825
with inventory but no sales row, and 605 with sales but no inventory row. These
coverage differences are retained explicitly. The median comparable ratio is
2.62 inventory units per monthly sale; it is **not 2.62 days**. This ratio is a
separate descriptive check and is not a predictor in the price benchmark.

## Run with permitted local snapshots

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-replay.txt
python -m unittest discover -s tests -v
python -m replay.housing --help
python -m replay.housing --prices /path/to/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv --inventory /path/to/Metro_invt_fs_uc_sfrcondo_sm_month.csv --sales /path/to/Metro_sales_count_now_uc_sfrcondo_month.csv --output technical/replay/local_metro_report.json --max-regions 50 --test-start 2021-01-31
```

The CLI reads local data and writes aggregate JSON without uploading records. Output paths that alias a source CSV, including
symlinks, are rejected before reading or writing the input.
The Python 3.12.14 environment is pinned in [requirements-replay.txt](requirements-replay.txt).
CI uses synthetic fixtures and the original export/inventory tests; it does not
fetch provider data or rerun the real-input benchmark.

Tests cover missing calendar months, region isolation, duplicate-key rejection,
keyed reconciliation, zero/nonfinite handling, past-only lags, train-only scaling
and horizon purging. Exact filenames, schemas and hashes support a permitted
local replay; the original notebook environment and external Census boundary
inputs remain separate. The original [methods notes](METHODS_AND_LIMITATIONS.md)
continue to apply to the preserved classroom results.

Implementation reference: scikit-learn's
[Pipeline](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html).
