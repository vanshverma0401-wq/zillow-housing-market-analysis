# Technical evidence and provenance

**Data Provided by Zillow Group**

## Source identity

The shared-team `FINAL_NOTEBOOK.ipynb` was recovered through the authenticated
project folder on November 8, 2026. Its SHA-256 is
`740cf88030647d5e840cc39f58b87a07a6ba1ec985a93417e6c330749189bfb6`.
It is byte-identical to the retained local final notebook. Its title, three authors
and named figures match the project described in course feedback. No available
Canvas attachment establishes byte-for-byte identity to the submitted file.

The original contains 70 cells, 46 code cells and 18 saved PNGs. The public source
contains 65 cells, including 43 retained original code cells and added review
notes. It is a documented publication copy, not an unchanged original submission.
See [notebook inventory](notebook_inventory.json).

See [source reconciliation](source_reconciliation.json) for the source identity and publication scope.

## Evidence classes

| Class | What it establishes | What it does not establish |
| --- | --- | --- |
| Original source code | Transformations, model configuration and analytical workflow were present | Clean-kernel execution or prospective forecast validity |
| Saved PNG outputs | Historical figures existed in the retained notebook | Fresh recomputation, corrected labels or validated numerical findings |
| Shared-source hash match | Recovered and retained versions are identical | Exact Canvas submission attachment identity |
| Input inventory | All 16 named CSV inputs are available privately, with schemas and hashes | Valid joins, complete values, metric correctness or a successful notebook replay |
| Synthetic audit tests | Export/privacy/input-inventory behavior on focused fixtures | Original model quality or financial results |

## Source publication edits

[The exporter](../scripts/export_notebook_evidence.py) creates the reviewed
[notebook](../notebooks/zillow_home_value_analysis.ipynb) and records every retained
source-cell index, replacement and omission. It strips outputs, execution counts,
metadata and the institutional-logo reference. It inserts warnings before the
legacy market-duration and model-training cells and excludes the last eight source
cells containing ROI/profit/income scenarios and recommendation text.

Sixteen PNGs are exported byte-for-byte from saved payloads; the ROI and net-income
images are omitted. [The figure manifest](figure_manifest.json) records each
source-cell/output coordinate, asset hash, size, attribution and evidence class.
The [gallery](../FIGURE_GALLERY.md) places interpretation limits next to every view.

## Input recovery

[The input audit](../scripts/audit_inputs.py) statically discovers literal CSV
reads and inspects only filenames resolved inside an authorized input directory.
It does not execute the notebook, download files or train the model. The checked
[manifest](input_inventory.json) records 16 available required names, zero missing
names and 15 distinct content hashes.

The external state-boundary file and original environment are not validated by
that CSV audit. The public source can naturally have a different notebook hash
from the retained original because publication edits are deliberate.

## New tooling and remaining work

Both helpers and their synthetic tests are November 2026 portfolio tooling,
separate from the original team implementation. Fourteen focused tests cover
source-output stripping, private-pattern rejection, source immutability,
input-discovery boundaries, schema inventory and safe output paths.

A controlled future replay should verify the geospatial inputs and environment,
repair the market-duration denominator using explicit matching keys, confirm
calendar horizons, use chronological evaluation with suitable separation and
compare with meaningful baselines. None of those steps is claimed complete here.
