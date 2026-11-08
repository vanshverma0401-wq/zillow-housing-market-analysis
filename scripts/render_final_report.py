#!/usr/bin/env python3
"""Render the complete 2025 final notebook as a GitHub-readable report.

Added for the November 2026 publication review. Reads saved notebook JSON and
figure metadata only; never executes notebook cells or retrains a model.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

MAX_NOTEBOOK_BYTES = 16 * 1024 * 1024
SENSITIVE = re.compile(r"/(?:Users|home|Volumes)/|[A-Za-z]:\\|\\\\|"
                       r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|"
                       r"\bgh[pousr]_[A-Za-z0-9]{20,}|\bsk-proj-[A-Za-z0-9_-]{20,}", re.I)
ACTIVE_HTML = re.compile(r"<\s*(?:script|iframe|object|embed)\b|javascript\s*:", re.I)
ASSET_PATH = re.compile(r"assets/figures/[a-z0-9-]+\.png")
HEADER_PHOTO_REFERENCE = re.compile(r"!\[st_thomas\]\(st_thomas\.jpg\)")
OAK_GROVE_REFERENCE = re.compile(r"!\[oak_grove\]\(oak_grove\.png\)")


class ReportError(ValueError):
    pass


def text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return "".join(value)
    raise ReportError("Expected notebook text")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fenced(value: str, language: str = "") -> str:
    length = max([2, *(len(m.group()) for m in re.finditer(r"`+", value))]) + 1
    fence = "`" * length
    return f"{fence}{language}\n{value}" + ("" if value.endswith("\n") else "\n") + f"{fence}\n"


def build_report(raw: bytes, figures: dict, header_photo_asset: str | None = None) -> tuple[str, dict]:
    if len(raw) > MAX_NOTEBOOK_BYTES:
        raise ReportError("Notebook exceeds the read limit")
    try:
        notebook = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise ReportError("Invalid notebook JSON") from error
    cells = notebook.get("cells") if isinstance(notebook, dict) else None
    if not isinstance(cells, list) or not all(isinstance(c, dict) for c in cells):
        raise ReportError("Expected notebook cells")
    entries = figures.get("figures") if isinstance(figures, dict) else None
    if not isinstance(entries, list):
        raise ReportError("Expected a figure manifest")
    if figures.get("source_notebook_sha256") != sha(raw):
        raise ReportError("Figure manifest belongs to a different source notebook")
    mapping: dict[tuple[int, int], dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not ASSET_PATH.fullmatch(entry.get("asset", "")):
            raise ReportError("Unsafe figure path")
        key = (entry.get("source_cell_index"), entry.get("source_output_index"))
        if key in mapping:
            raise ReportError("Duplicate figure coordinate")
        mapping[key] = entry
    if header_photo_asset is not None and not re.fullmatch(r"(?:assets|notebooks)/[A-Za-z0-9_.-]+\.jpg", header_photo_asset):
        raise ReportError("Unsafe header photograph path")

    parts = [
        "# Complete Final Project Zillow Home Value Analysis\n",
        "**Jake Holley, Miranda Dahl and Vansh Verma — 2025 academic final project.**\n",
        "The complete original notebook narrative, code and saved outputs are reproduced below in their original order. These are historical project results, not a fresh execution. Original assumptions, conclusions and scenario outputs are preserved. Later technical review notes are kept separately in [Methods and limitations](METHODS_AND_LIMITATIONS.md).\n",
        "[Complete original notebook](notebooks/zillow_home_value_analysis.ipynb) · [All figure files](FIGURE_GALLERY.md)\n",
        "**Data Provided by Zillow Group**\n",
        "---\n",
    ]
    cell_map = []
    output_map = []
    exceptions = []
    missing_assets = []
    png_count = 0
    stream_count = 0
    for index, cell in enumerate(cells):
        kind = cell.get("cell_type")
        source = text(cell.get("source", []))
        if SENSITIVE.search(source) or ACTIVE_HTML.search(source):
            raise ReportError(f"Unsafe source content in cell {index}")
        rendered = source
        cell_missing_assets = []
        if kind == "markdown" and HEADER_PHOTO_REFERENCE.search(source):
            if header_photo_asset:
                rendered = HEADER_PHOTO_REFERENCE.sub(f"![st_thomas]({header_photo_asset})", source)
                exceptions.append({"source_cell_index": index, "formatting_change": "Relative header photograph reference rebased for the root Markdown report."})
            else:
                cell_missing_assets.append({"asset": "st_thomas.jpg", "reason": "The original header photograph was not supplied to this report rendering."})
        if kind == "markdown" and OAK_GROVE_REFERENCE.search(source):
            cell_missing_assets.append({"asset": "oak_grove.png", "reason": "This original illustrative asset was not supplied in the recovered project folder."})
        parts.append(f'<a id="source-cell-{index}"></a>\n')
        if kind == "markdown":
            parts.append(rendered + ("" if rendered.endswith("\n") else "\n"))
        elif kind == "code":
            parts += [f"<details>\n<summary>Source code — original cell {index + 1}</summary>\n", fenced(source, "python"), "</details>\n"]
        else:
            raise ReportError(f"Unsupported cell type {kind}")
        for missing in cell_missing_assets:
            note_anchor = f"publication-note-{index}-{len(missing_assets)}"
            parts += [f'<a id="{note_anchor}"></a>\n',
                      f"> **Publication note (outside the original source):** {missing['reason']} Its original `{missing['asset']}` reference is preserved above. No replacement image was fabricated. The complete final project includes all {len(entries)} embedded charts.\n"]
            missing_assets.append({"source_cell_index": index, **missing,
                                   "original_reference_preserved": True,
                                   "report_note_anchor": note_anchor})
        cell_map.append({"source_cell_index": index, "cell_type": kind,
                         "source_text_sha256": sha(source.encode()),
                         "rendered_source_text_sha256": sha(rendered.encode()),
                         "source_text_unchanged": rendered == source,
                         "report_anchor": f"source-cell-{index}"})
        for number, output in enumerate(cell.get("outputs", [])):
            if not isinstance(output, dict):
                raise ReportError("Invalid saved output")
            coordinate = (index, number)
            anchor = f"source-output-{index}-{number}"
            parts.append(f'<a id="{anchor}"></a>\n')
            rendered_mimes = []
            output_type = output.get("output_type")
            if output_type == "stream":
                value = text(output.get("text", []))
                if SENSITIVE.search(value) or ACTIVE_HTML.search(value):
                    raise ReportError("Unsafe saved stream")
                parts += ["Saved text output:\n", fenced(value)]
                stream_count += 1
                rendered_mimes.append("stream")
            elif output_type in {"display_data", "execute_result"}:
                data = output.get("data", {})
                if not isinstance(data, dict) or set(data) - {"image/png", "text/plain"}:
                    raise ReportError("Unexpected saved output MIME; review before publication")
                if "image/png" in data:
                    entry = mapping.get(coordinate)
                    if entry is None:
                        raise ReportError(f"Missing figure coordinate {coordinate}")
                    try:
                        png = base64.b64decode("".join(text(data["image/png"]).split()), validate=True)
                    except ValueError as error:
                        raise ReportError("Invalid saved image data") from error
                    if sha(png) != entry.get("sha256"):
                        raise ReportError("Figure fingerprint differs from the saved notebook image")
                    parts += [f"![Original saved figure — cell {index + 1}, output {number + 1}]({entry['asset']})\n",
                              f"*Original saved output, source cell {index}, output {number}. Data Provided by Zillow Group.*\n"]
                    png_count += 1
                    rendered_mimes.append("image/png")
                if "text/plain" in data:
                    value = text(data["text/plain"])
                    if SENSITIVE.search(value) or ACTIVE_HTML.search(value):
                        raise ReportError("Unsafe saved plain-text output")
                    parts += ["<details>\n<summary>Original saved output description</summary>\n", fenced(value), "</details>\n"]
                    rendered_mimes.append("text/plain")
            else:
                raise ReportError(f"Unsupported saved output type {output_type}")
            output_map.append({"source_cell_index": index, "source_output_index": number,
                               "output_type": output_type, "represented_mime_types": rendered_mimes,
                               "report_anchor": anchor})
    report = "\n".join(parts).rstrip() + "\n"
    manifest = {"generated_date": "2026-11-08", "original_project_year": 2025,
                "source_notebook_sha256": sha(raw), "report_sha256": sha(report.encode()),
                "source_cell_count": len(cells), "rendered_cell_count": len(cell_map),
                "source_code_cell_count": sum(c.get("cell_type") == "code" for c in cells),
                "source_markdown_cell_count": sum(c.get("cell_type") == "markdown" for c in cells),
                "saved_png_count": png_count, "saved_stream_count": stream_count,
                "saved_output_count": len(output_map), "notebook_executed": False,
                "narrative_or_code_omitted": False, "formatting_exceptions": exceptions,
                "missing_original_markdown_assets": missing_assets,
                "cells": cell_map, "outputs": output_map}
    return report, manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--figure-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--header-photo-asset", "--logo-asset", dest="header_photo_asset",
                        help="Repository-relative path to the recovered original header photograph")
    args = parser.parse_args(argv)
    sources = {args.notebook.resolve(), args.figure_manifest.resolve()}
    if args.output.resolve() in sources or args.manifest_output.resolve() in sources or args.output.resolve() == args.manifest_output.resolve():
        parser.error("Outputs must differ from sources and from each other")
    try:
        report, manifest = build_report(args.notebook.read_bytes(), json.loads(args.figure_manifest.read_text()), args.header_photo_asset)
        for destination in [args.output, args.manifest_output]:
            destination.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        args.manifest_output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except (ReportError, OSError, ValueError) as error:
        parser.exit(1, f"Report export failed: {error}\n")
    print(f"Rendered {manifest['rendered_cell_count']} cells and {manifest['saved_png_count']} saved figures without executing the notebook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
