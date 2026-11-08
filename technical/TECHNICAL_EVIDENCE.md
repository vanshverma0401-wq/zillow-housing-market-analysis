# Complete final project evidence

**Data Provided by Zillow Group**

The canonical [final notebook](../notebooks/zillow_home_value_analysis.ipynb) is now
byte-identical to the authenticated shared-team `FINAL_NOTEBOOK.ipynb`:
`740cf88030647d5e840cc39f58b87a07a6ba1ec985a93417e6c330749189bfb6`.
It contains all 70 cells, 46 code cells, saved outputs and 18 original PNGs.
No source sections, conclusions, ROI scenarios or monthly-income figures are omitted.

The original Markdown also references a separate `oak_grove.png` illustration.
That file was absent from the recovered source materials and scoped local search;
its original reference is retained with an adjacent availability note. This does
not affect the 18 embedded chart outputs, all of which are present.

The [readable final project](../FINAL_PROJECT.md) represents every source cell and
output in order, using collapsible code and separate image assets. Only relative
image references are remapped for GitHub. Its mapping is recorded in
[final_report_manifest.json](final_report_manifest.json).

## Source reconciliation

The shared-folder and retained local notebooks match byte-for-byte. The title,
three collaborators and named figures match the course feedback, although no
available Canvas attachment established submitted-file byte identity.
See [source reconciliation](source_reconciliation.json) and
[notebook inventory](notebook_inventory.json).

All 16 required CSV filenames are available privately. Their schemas, dates and
hashes are recorded in [input_inventory.json](input_inventory.json); there are 15
distinct hashes. The original header image was also recovered from the shared
project materials and is present beside the notebook and in the report assets.

## Preservation checks

- Canonical notebook SHA-256 equals the original shared source.
- All source cells and saved outputs are preserved.
- All 18 figure exports match the original PNG payloads.
- Original team names and all six questions are present.
- No notebook code was executed or model retrained during publication.
- Actual credentials, private paths and contact identifiers were absent from the full source audit.

The [figure manifest](figure_manifest.json) supplies source-cell/output coordinates,
asset hashes and historical evidence classifications. The
[complete gallery](../FIGURE_GALLERY.md) shows every figure.

## Review notes and tests

[Methods and limitations](../METHODS_AND_LIMITATIONS.md) documents the existing
alignment, label, horizon and evaluation issues separately from the final artifact.
Original numerical annotations and scenario text are preserved as historical work,
not advertised as independently verified outcomes.

The export, input-audit and report-rendering utilities are new November 2026
portfolio tooling. Their focused tests verify content preservation and tool
boundaries. Test success does not establish original model quality or a clean
end-to-end notebook execution.
