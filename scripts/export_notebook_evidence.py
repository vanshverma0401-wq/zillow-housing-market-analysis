#!/usr/bin/env python3
"""New November 2026 static export utility for the 2025 team notebook.

This project-specific exporter reads notebook JSON and saved PNG payloads only.
It never executes cells, refreshes data, trains a model or writes to its input.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import struct

MAX_NOTEBOOK_BYTES = 16 * 1024 * 1024
MAX_IMAGE_BYTES = 4 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SENSITIVE = re.compile(
    r"/(?:Users|home|Volumes)/|[A-Za-z]:\\|\\\\|"
    r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|"
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-proj-[A-Za-z0-9]{10,})|"
    r"(?i:password|api[_ -]?key|access[_ -]?token|secret)\s*=\s*['\"][^'\"]+",
    re.I,
)
ACTIVE_HTML = re.compile(r"<\s*(?:script|iframe|object|embed)\b|javascript:|\bon(?:load|error)\s*=", re.I)

# Source-cell coordinates are stable in the retained 70-cell FINAL_NOTEBOOK.
FIGURES = {
    32: [("home-value-trends", "Top and bottom selected metros: home-value trends")],
    33: [("rent-index-trends", "Top and bottom selected metros: rent-index trends")],
    34: [("sales-count-trends", "Top and bottom selected metros: sales-count trends")],
    35: [("inventory-trends", "Top and bottom selected metros: inventory trends")],
    38: [("national-for-sale-inventory", "United States for-sale inventory")],
    39: [("national-sales-count", "United States sales count; original chart title repeats the inventory title")],
    40: [("national-median-sale-price", "United States Median Sales Price of Homes")],
    41: [("national-mean-sale-price", "United States Mean Sales Price of Homes")],
    42: [("national-above-list-share", "United States Percent of Homes Sold Above Listing Price")],
    43: [("national-below-list-share", "United States Percent of Homes Sold Below Listing Price")],
    46: [("state-market-index-heatmap", "Index Rating Trends by State Over R12")],
    49: [
        ("legacy-market-duration-comparison", "Legacy time-on-market comparison; alignment and unit limitations"),
        ("legacy-state-time-proxy", "Average Time-on-Market Proxy by State; legacy alignment limitation"),
        ("legacy-state-mean-doz", "Average Mean DoZ by State; legacy selection limitation"),
    ],
    59: [("historical-model-diagnostic", "Historical actual-versus-predicted diagnostic from random row split")],
    61: [("historical-feature-importance", "Historical XGBoost feature importance")],
}

REVIEW_NOTE = """# Zillow Home Value Analysis source review

Original 2025 collaborative project: **Jake Holley, Miranda Dahl and Vansh Verma**.

This public source copy was prepared from the final notebook recovered from the
authenticated shared team folder on November 8, 2026. Its bytes match the retained
local final notebook. Its title, team and named charts corroborate the project
identified in the course feedback; no Canvas submission attachment was available
to establish byte-for-byte submission identity. No cell was executed during this export.

All original outputs, execution counts and private notebook metadata are removed.
Original code through source cell 61 is retained unchanged, including documented
limitations. Institutional branding, unverified recommendation text and the final
ROI/profit/income sections are omitted or replaced. See the repository methods,
source inventory and figure captions before interpreting this historical code.
"""

REPLACEMENTS = {
    0: "# SEIS 631 Final Project - Zillow Home Value Analysis\n\nJake Holley, Miranda Dahl, Vansh Verma\n",
    36: "### Historical market-trend section\n\nThe preceding saved comparisons describe the selected historical data and its ranking procedure. They do not establish current market performance, causal drivers or an investment recommendation.\n",
    44: "### Historical national-indicator section\n\nThe preceding code summarizes historical inventory, sale-count and price-series snapshots. Narrative numerical claims have not been freshly recomputed, and these figures are not current market evidence.\n",
    47: "### Historical state market-index section\n\nThe saved state heatmap is descriptive source evidence. It does not establish that a particular time or place is suitable for buying property.\n",
    50: "### Legacy market-duration interpretation\n\nThe preceding historical figures inherit the documented dataframe-index alignment and ratio-versus-days limitations. They are not validated comparisons of sale or rental duration and should not support market rankings.\n",
    51: "# Historical neighborhood value model\n\nThe following retained model source is separate from the omitted profit/income recommendation sections.\n",
}

WARNINGS = {
    49: """### Review warning before legacy source cell 49

The denominator uses `df['SalesCount']`, while the numerator uses `df_q4`.
An earlier loop leaves `df` bound to the separate long-form sales dataframe;
pandas aligns the division by row index, not the merged region/date keys.
This source is preserved without silently fixing that issue. Inventory divided
by sales is a ratio, not a number of days, although the original comparison plot
uses a days label. The three saved figures are historical diagnostics, not
validated market-duration findings.
""",
    57: """### Review warning before historical model training

The retained model uses a random 80/20 row split across repeated neighborhoods
and dates. It is not an out-of-time or spatial validation. The future target uses
a 24-row shift after filtering observations; 24 rows are not guaranteed to mean
24 calendar months. Saved performance and feature-importance images are
historical diagnostics, not independently validated forecasting performance.
""",
}


class ExportError(ValueError):
    """The selected notebook is malformed or unsafe for this source export."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_text(cell: dict) -> str:
    source = cell.get("source", [])
    if isinstance(source, str):
        return source
    if isinstance(source, list) and all(isinstance(line, str) for line in source):
        return "".join(source)
    raise ExportError("Invalid cell source")


def markdown(text: str, identifier: str) -> dict:
    return {"cell_type": "markdown", "id": identifier, "metadata": {},
            "source": text.splitlines(keepends=True)}


def build_payloads(raw: bytes) -> tuple[dict[str, bytes], dict]:
    if len(raw) > MAX_NOTEBOOK_BYTES:
        raise ExportError("Notebook exceeds the size limit")
    try:
        original = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ExportError("Invalid notebook JSON") from exc
    cells = original.get("cells") if isinstance(original, dict) else None
    if not isinstance(cells, list) or len(cells) != 70 or not all(isinstance(c, dict) for c in cells):
        raise ExportError("Expected the retained 70-cell final-notebook structure")
    public_cells = [markdown(REVIEW_NOTE, "publication-review")]
    mapping = []
    for index, cell in enumerate(cells[:62]):
        kind = cell.get("cell_type")
        if kind not in {"markdown", "code"}:
            raise ExportError("Unexpected retained cell type")
        text = REPLACEMENTS.get(index, source_text(cell))
        if SENSITIVE.search(text) or ACTIVE_HTML.search(text):
            raise ExportError(f"Unsafe source pattern in retained cell {index}")
        if index in WARNINGS:
            public_cells.append(markdown(WARNINGS[index], f"review-warning-{index}"))
        public_index = len(public_cells)
        cleaned = {"cell_type": kind, "id": f"source-cell-{index:03d}",
                   "metadata": {}, "source": text.splitlines(keepends=True)}
        if kind == "code":
            cleaned.update({"execution_count": None, "outputs": []})
        public_cells.append(cleaned)
        mapping.append({"source_cell_index": index, "public_cell_index": public_index,
                        "cell_type": kind, "source_replaced": index in REPLACEMENTS})
    notebook = {"cells": public_cells,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                             "language_info": {"name": "python"}},
                "nbformat": 4, "nbformat_minor": 5}
    notebook_raw = (json.dumps(notebook, indent=1, ensure_ascii=False) + "\n").encode()
    payloads = {"notebooks/zillow_home_value_analysis.ipynb": notebook_raw}
    figures = []
    for index, specifications in FIGURES.items():
        outputs = cells[index].get("outputs", [])
        images = [(j, o.get("data", {}).get("image/png")) for j, o in enumerate(outputs)
                  if isinstance(o, dict) and "image/png" in o.get("data", {})]
        if len(images) != len(specifications):
            raise ExportError(f"Unexpected saved PNG count in cell {index}")
        for (output_index, encoded), (filename, title) in zip(images, specifications):
            if isinstance(encoded, list):
                encoded = "".join(encoded)
            if not isinstance(encoded, str):
                raise ExportError("Invalid saved PNG payload")
            try:
                png = base64.b64decode("".join(encoded.split()), validate=True)
            except ValueError as exc:
                raise ExportError("Invalid saved PNG base64") from exc
            if len(png) > MAX_IMAGE_BYTES or not png.startswith(PNG_SIGNATURE) or len(png) < 24:
                raise ExportError("Invalid or excessive saved PNG")
            width, height = struct.unpack(">II", png[16:24])
            asset = "assets/figures/" + filename + ".png"
            payloads[asset] = png
            category = "legacy_alignment_and_units_diagnostic" if index == 49 else (
                "historical_random_split_model_diagnostic" if index in {59, 61} else "historical_descriptive_snapshot")
            figures.append({"source_cell_index": index, "source_output_index": output_index,
                            "asset": asset, "title": title, "width": width, "height": height,
                            "sha256": sha256(png), "source_notebook_sha256": sha256(raw),
                            "evidence_class": category, "freshly_recomputed": False,
                            "validated_finding": False,
                            "data_attribution": "Data Provided by Zillow Group"})
    inventory = {
        "export_tool_added": "2026-11-08", "original_project_year": 2025,
        "project_authors": ["Jake Holley", "Miranda Dahl", "Vansh Verma"],
        "source_provenance": "Authenticated shared team folder recovered November 8, 2026; byte-identical to the retained local final notebook.",
        "shared_team_source_reconciled_date": "2026-11-08",
        "source_notebook_sha256": sha256(raw), "source_cell_count": 70,
        "source_code_cell_count": sum(c.get("cell_type") == "code" for c in cells),
        "public_cell_count": len(public_cells), "retained_source_cell_indices": list(range(62)),
        "omitted_source_cell_indices": list(range(62, 70)),
        "omission_reason": "Unvalidated ROI, profit, income and recommendation sections omitted.",
        "replaced_markdown_source_cells": sorted(REPLACEMENTS),
        "warnings_before_source_cells": sorted(WARNINGS), "cell_mapping": mapping,
        "public_notebook_sha256": sha256(notebook_raw), "published_png_count": len(figures),
        "source_png_count": sum("image/png" in o.get("data", {}) for c in cells for o in c.get("outputs", []) if isinstance(o, dict)),
        "execution_performed": False, "raw_datasets_published_by_exporter": False,
        "submission_identity": "Title, team and named charts corroborate course-feedback project; byte-identical submitted attachment not established.",
        "removed": ["all original outputs", "execution counts", "notebook and cell metadata", "institutional logo reference", "unverified recommendation narratives", "ROI/profit/income sections"],
        "code_policy": "Retained code is unchanged; documented historical issues are not silently fixed.",
    }
    manifest = {"source_notebook_sha256": sha256(raw), "figure_count": len(figures),
                "omitted_png_source_cells": [65, 68],
                "note": "Byte-identical saved PNGs; historical source evidence, not a fresh notebook execution.",
                "figures": figures}
    payloads["technical/notebook_inventory.json"] = (json.dumps(inventory, indent=2) + "\n").encode()
    payloads["technical/figure_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return payloads, inventory


def export_evidence(source: Path, output: Path) -> dict:
    raw = source.read_bytes()
    payloads, inventory = build_payloads(raw)
    if any((output / name).resolve() == source.resolve() for name in payloads):
        raise ExportError("Output would overwrite the source notebook")
    for name, content in payloads.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_notebook", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        inventory = export_evidence(args.source_notebook, args.output_dir)
    except (ExportError, OSError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")
    print(f"Exported {inventory['published_png_count']} historical figures without executing cells.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
