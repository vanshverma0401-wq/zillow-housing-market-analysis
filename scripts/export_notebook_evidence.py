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
    65: [("original-roi-scenario", "Original classroom ROI scenario; unvalidated")],
    68: [("original-net-income-scenario", "Original classroom monthly-income scenario; unvalidated")],
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


def inspect_text(value: object, location: str = "notebook") -> None:
    """Reject actual private/active content while keeping the original bytes.

    PNG base64 strings are decoded and bounded separately. Notebook code and
    formulas are inspected as text only; nothing is evaluated or executed.
    """
    if isinstance(value, dict):
        for key, child in value.items():
            if key != "image/png":
                inspect_text(child, location + "." + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            inspect_text(child, f"{location}[{index}]")
    elif isinstance(value, str):
        if SENSITIVE.search(value) or ACTIVE_HTML.search(value):
            raise ExportError(f"Unsafe private or active content at {location}")


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
    for cell in cells:
        if cell.get("cell_type") not in {"markdown", "code"}:
            raise ExportError("Unexpected cell type")
        source_text(cell)
        if cell.get("cell_type") == "code" and not isinstance(cell.get("outputs", []), list):
            raise ExportError("Invalid code-cell outputs")
    inspect_text(original)
    # Complete final-project restoration: preserve source, narrative, metadata,
    # saved figures, text outputs and execution counts byte-for-byte.
    payloads = {"notebooks/zillow_home_value_analysis.ipynb": raw}
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
                "historical_random_split_model_diagnostic" if index in {59, 61} else (
                    "historical_unvalidated_classroom_scenario" if index in {65, 68} else "historical_descriptive_snapshot"))
            figures.append({"source_cell_index": index, "source_output_index": output_index,
                            "asset": asset, "title": title, "width": width, "height": height,
                            "sha256": sha256(png), "source_notebook_sha256": sha256(raw),
                            "evidence_class": category, "freshly_recomputed": False,
                            "validated_finding": False,
                            "data_attribution": "Data Provided by Zillow Group"})
    source_png_count = sum("image/png" in o.get("data", {}) for c in cells
                           for o in c.get("outputs", []) if isinstance(o, dict))
    if source_png_count != len(figures):
        raise ExportError("Unexpected saved PNG outside the complete figure map")
    known_source = sha256(raw) == "740cf88030647d5e840cc39f58b87a07a6ba1ec985a93417e6c330749189bfb6"
    inventory = {
        "export_tool_added": "2026-11-08", "original_project_year": 2025,
        "project_authors": ["Jake Holley", "Miranda Dahl", "Vansh Verma"],
        "source_provenance": (
            "Authenticated shared team folder recovered November 8, 2026; byte-identical to the retained local final notebook."
            if known_source else "Input provided to static exporter; external provenance not established by this utility."),
        "shared_team_source_reconciled_date": "2026-11-08" if known_source else None,
        "matches_verified_shared_source_hash": known_source,
        "publication_mode": "complete_final_project",
        "source_notebook_sha256": sha256(raw), "source_cell_count": len(cells),
        "source_code_cell_count": sum(c.get("cell_type") == "code" for c in cells),
        "public_cell_count": len(cells),
        "public_code_cell_count": sum(c.get("cell_type") == "code" for c in cells),
        "retained_source_cell_indices": list(range(len(cells))),
        "omitted_source_cell_indices": [], "omission_reason": None,
        "replaced_markdown_source_cells": [], "warnings_before_source_cells": [],
        "cell_mapping": [{"source_cell_index": i, "public_cell_index": i,
                          "cell_type": cell["cell_type"], "source_replaced": False}
                         for i, cell in enumerate(cells)],
        "public_notebook_sha256": sha256(raw),
        "byte_identical_to_source": True, "all_original_outputs_preserved": True,
        "all_original_metadata_preserved": True,
        "published_png_count": len(figures), "source_png_count": source_png_count,
        "execution_performed": False, "raw_datasets_published_by_exporter": False,
        "privacy_screen": "Source, saved text outputs and metadata screened; no private or active content found. PNGs exported without interpretation or execution.",
        "submission_identity": "Title, team and named charts corroborate course-feedback project; byte-identical submitted attachment not established.",
        "removed": [],
        "code_policy": "The complete final notebook is preserved byte-for-byte. Current review notes remain separate from the original project.",
    }
    manifest = {"source_notebook_sha256": sha256(raw), "figure_count": len(figures),
                "omitted_png_source_cells": [],
                "note": "All eighteen original saved PNGs are included byte-for-byte. Historical scenarios and model diagnostics are not a fresh notebook execution or validated investment outcome.",
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
