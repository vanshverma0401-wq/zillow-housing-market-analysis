# Data attribution and publication boundary

**Data Provided by Zillow Group**

## Primary sources

The historical project uses Zillow Research housing-market and geographic
home-value series. Provider documentation:

- [Housing data and downloads](https://www.zillow.com/research/data/)
- [Zillow Home Value Index methodology](https://www.zillow.com/research/zhvi-methodology/)
- [Zillow Observed Rent Index methodology](https://www.zillow.com/research/methodology-zori-repeat-rent/)
- [Zillow terms of use](https://www.zillow.com/corporate/terms-of-use/)

ZHVI, rent indices, sale prices, listing counts and pending-duration series are
separate metrics. The public captions identify their intended roles rather than
presenting them as interchangeable property-level outcomes.

## Retained snapshot evidence

All 16 distinct CSV filenames referenced by the retained notebook were recovered
from the shared team project materials and inspected privately. Their basenames,
sizes, hashes, schema summaries and date coverage appear in
[input_inventory.json](technical/input_inventory.json). There are 15 distinct
content hashes because the MSA-value and metro-ZHVI files are identical.

Current provider downloads may extend dates or revise past values. They need not
match the recovered 2025-project snapshot. No acquisition or provider-release
timestamp was established from the CSV metadata.

## What is public

- A reviewed notebook source copy, with original outputs and private metadata removed.
- Sixteen attributed historical figures exported from saved notebook PNG payloads.
- Source and input fingerprints, structural metadata and documented publication edits.
- New static audit utilities and synthetic tests, added in November 2026.

## What remains private

Raw Zillow CSVs, shared-folder account URLs, course feedback, institutional logos,
private notebook versions and the omitted profit/income sections are not
redistributed. No explicit raw-data rehosting license was established in this
review; no MIT or other open-data license is asserted for those provider files.
The provider links above are the starting point for obtaining and reviewing data
under their applicable conditions.

## Team and other materials

The original academic work is credited to **Jake Holley, Miranda Dahl and Vansh
Verma**. No sole-authorship claim or new per-person contribution split is created.
The new audit helpers are separate from the original 2025 analysis. Publication of
the case study does not transfer ownership of Zillow's data, vendor software,
third-party geographic resources or institutional branding.

The original map code references a Census state-boundary file. That external
resource was not revalidated or rehosted during this publication audit. No
endorsement by Zillow, the university or another provider is claimed.
