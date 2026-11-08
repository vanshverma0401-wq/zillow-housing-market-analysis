# Methods and limitations

**Data Provided by Zillow Group**

## Original evidence and publication edits

The final notebook was recovered from the authenticated shared team folder on
November 8, 2026. It matches the retained local final version byte-for-byte.
The title, three collaborators and feedback-named charts corroborate project
identity. No available Canvas submission attachment establishes exact submission
byte identity.

The public copy retains original code through source cell 61 unchanged. It strips
all original outputs, execution counts and private notebook/cell metadata;
removes the institutional-logo reference; replaces unsupported recommendation
narratives; inserts review warnings; and omits source cells 62-69 containing
profit/income scenarios and conclusions. The precise source-to-public cell mapping
is recorded in [notebook_inventory.json](technical/notebook_inventory.json).

## Metric definitions

ZHVI represents typical home values rather than prices only for homes that sold.
It should not be relabeled as median transaction price. The notebook's national
median-sale-price figure instead loads a separate sale-price series. See
[ZHVI methodology](https://www.zillow.com/research/zhvi-methodology/).

ZORI tracks asking-rent changes and is not a record of rent collected by an
investor. Rental-index movement does not establish realized property income.
See [ZORI methodology](https://www.zillow.com/research/methodology-zori-repeat-rent/).

The pending-days input concerns the interval to pending status, not the entire
listing-to-closing process or a measured time to rent a property. Inventory and
sales counts are different measures; their ratio is not automatically days.
Definitions are available on the [provider's data page](https://www.zillow.com/research/data/).

## Data preparation and coverage

The metro workflow identifies date columns, forward-fills selected series,
filters rows for missing observations, reshapes wide series into long records and
joins on region/state/date. These choices affect the retained geography and time
coverage. Other source cells use national aggregate rows and separate weekly
series; they should not be confused with averages across all metros.

The input audit found all 16 distinct required CSV filenames. Two filenames,
`msa_values.csv` and the metro ZHVI input, have identical content, leaving 15
unique hashes. Input availability is not evidence that keys are unique after
every transformation, that joins are valid, or that every retained observation is
nonmissing. Date ranges differ between series. File fingerprints identify the
recovered snapshots, not a provider-release or acquisition timestamp.

## Legacy market-duration issue

In source cell 49 the numerator comes from `df_q4['Inventory']`, while the
denominator uses `df['SalesCount']`. An earlier loop leaves `df` bound to the
separate long-form sales dataframe. Pandas division aligns those objects by row
index rather than the merged region/date keys; that is not the intended join.
The unchanged source is annotated rather than silently repaired.

The three associated saved figures inherit this alignment/selection issue. The
comparison chart also places an inventory/sales ratio alongside a days measure
under a shared days label. These are archived diagnostics, not validated
fastest/slowest-market findings. The actual pending-days measure also does not
measure rental duration.

## Other visual-label issues

The source images are preserved unchanged. The sales-count and inventory trend
panels reuse a Home Value y-axis label. The national sales-count chart repeats the
inventory chart title. Captions identify the source fields and distinguish those
label errors from the actual intended measures.

## Historical model

The source constructs seasonal sine/cosine features, geographic value differences
and 12/24/36-row trends. It fits an XGBoost regressor using a scikit-learn pipeline
with categorical encoding, imputation and numeric scaling. The model targets a
future difference in log neighborhood value, which is recomposed into values for
the historical diagnostic plot.

Evaluation uses a random 80/20 row split across repeated neighborhoods and dates.
This is not an out-of-time or spatial holdout. Nearby training/test observations
and overlapping target horizons can produce optimistic results for prospective
forecasting. The target uses a 24-row shift after filtering; without confirming a
complete monthly sequence, that is not guaranteed to be a two-calendar-year
horizon. Row-based lag features have the same timing qualification.

Saved score annotations and feature importances are historical diagnostics only.
No independent replay, chronological backtest, baseline comparison or uncertainty
calibration was performed during publication. Feature importance is not a causal
explanation. No forecasting-accuracy headline or profit promise is supported by
these figures.

## Runtime and interpretation boundary

The 16 published figures are saved outputs from the original notebook, not new
results. No notebook cells were executed to export them. All required CSV names
were recovered privately, but the Census state-boundary resource and the complete
runtime environment remain unverified. The public package does not contain raw
provider data or a deployable trained model.

This is an academic historical analysis. It does not establish current market
rankings, realized investment returns, rental income, causal market drivers or a
property acquisition recommendation.
