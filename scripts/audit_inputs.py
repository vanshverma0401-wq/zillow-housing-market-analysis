#!/usr/bin/env python3
"""New November 2026 input audit; not the original 2025 project implementation.

Inspect literal read_csv calls with AST and inventory available CSV snapshots.
No notebook code, model, formula, download, or metric aggregation is executed.
Only CSV basenames resolved inside the supplied data directory are read.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Sequence

DATE_HEADER = re.compile(r"\d{4}-\d{2}-\d{2}")
CSV_BASENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _.,()\-]*\.csv", re.I)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_date_header(value: str) -> bool:
    if not DATE_HEADER.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def required_inputs(notebook: dict) -> dict:
    """Inspect code-cell syntax without evaluating expressions or comments.

    IPython magic/shell lines are blanked to allow ordinary Python cells to
    parse. Unparseable cells and dynamic read_csv arguments are reported.
    Literal path prefixes are discarded; they never choose a read location.
    """
    calls: list[str] = []
    dynamic_calls = 0
    ignored_literals = 0
    stripped_paths = 0
    skipped_magic_lines = 0
    parse_failures: list[dict] = []
    for number, cell in enumerate(notebook.get("cells", []), 1):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else source
        if not isinstance(text, str):
            raise ValueError("Code-cell source must be text")
        normalized = []
        for line in text.splitlines():
            if line.lstrip().startswith(("%", "!", "?")):
                skipped_magic_lines += 1
                normalized.append("")
            else:
                normalized.append(line)
        try:
            tree = ast.parse("\n".join(normalized))
        except SyntaxError as error:
            parse_failures.append({"cell_number": number,
                                   "line_number": error.lineno,
                                   "error_kind": "SyntaxError"})
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            is_reader = (isinstance(node.func, ast.Attribute) and node.func.attr == "read_csv") or (
                isinstance(node.func, ast.Name) and node.func.id == "read_csv")
            if not is_reader:
                continue
            argument = node.args[0] if node.args else next(
                (k.value for k in node.keywords if k.arg == "filepath_or_buffer"), None)
            if not isinstance(argument, ast.Constant) or not isinstance(argument.value, str):
                dynamic_calls += 1
                continue
            value = argument.value
            if "://" in value:
                ignored_literals += 1
                continue
            normalized_path = value.replace("\\", "/")
            basename = PurePosixPath(normalized_path).name
            if not CSV_BASENAME.fullmatch(basename):
                ignored_literals += 1
                continue
            stripped_paths += int(normalized_path != basename)
            calls.append(basename)
    frequencies = Counter(calls)
    return {
        "literal_csv_call_count": len(calls),
        "distinct_required_csv_count": len(frequencies),
        "required_files": sorted(frequencies),
        "calls_by_filename": dict(sorted(frequencies.items())),
        "dynamic_read_csv_call_count": dynamic_calls,
        "ignored_nonlocal_or_non_csv_literal_count": ignored_literals,
        "literal_path_prefixes_discarded": stripped_paths,
        "ipython_magic_or_shell_lines_omitted": skipped_magic_lines,
        "unparsed_code_cells": parse_failures,
        "commented_calls_counted": False,
        "static_scope": "Literal call syntax only; reachability and runtime branches are not evaluated.",
    }


def csv_profile(path: Path) -> tuple[dict, set[str], set[str]]:
    """Count structures and missing cells, emitting no region or metric rows."""
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames
        if not headers or len(headers) != len(set(headers)):
            raise ValueError("Missing or duplicate CSV headers")
        dates = sorted(name for name in headers if is_date_header(name))
        metadata = [name for name in headers if name not in dates]
        row_count = 0
        region_ids: set[str] = set()
        repeated_ids = 0
        missing_ids = 0
        missing_date_cells = 0
        types: Counter[str] = Counter()
        for row in reader:
            if None in row or any(row.get(name) is None for name in headers):
                raise ValueError("CSV row width differs from its header")
            row_count += 1
            if "RegionID" in headers:
                identifier = row["RegionID"].strip()
                if identifier:
                    repeated_ids += int(identifier in region_ids)
                    region_ids.add(identifier)
                else:
                    missing_ids += 1
            if "RegionType" in headers:
                types[row["RegionType"].strip() or "(missing)"] += 1
            missing_date_cells += sum(not row[name].strip() for name in dates)
    profile = {
        "filename": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "row_count": row_count,
        "column_count": len(headers),
        "metadata_fields": metadata,
        "date_column_count": len(dates),
        "first_date_column": dates[0] if dates else None,
        "last_date_column": dates[-1] if dates else None,
        "empty_date_cell_count": missing_date_cells,
        "region_id_field_present": "RegionID" in headers,
        "distinct_nonempty_region_ids": len(region_ids) if "RegionID" in headers else None,
        "duplicate_region_id_occurrences": repeated_ids if "RegionID" in headers else None,
        "missing_region_id_rows": missing_ids if "RegionID" in headers else None,
        "region_type_counts": dict(sorted(types.items())),
        "national_country_row_count": types.get("country", 0) if "RegionType" in headers else None,
        "numeric_metrics_aggregated": False,
    }
    return profile, region_ids, set(dates)


def audit_inputs(notebook_path: Path, data_dir: Path) -> dict:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8-sig"))
    if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
        raise ValueError("Expected a notebook with a cells list")
    requirements = required_inputs(notebook)
    root = data_dir.resolve()
    if not root.is_dir():
        raise ValueError("Data directory does not exist")
    available: list[dict] = []
    missing: list[str] = []
    blocked: list[str] = []
    region_sets: list[set[str]] = []
    date_sets: list[set[str]] = []
    for name in requirements["required_files"]:
        candidate = root / name
        if candidate.resolve().parent != root:
            blocked.append(name)
            continue
        if not candidate.is_file():
            missing.append(name)
            continue
        profile, identifiers, dates = csv_profile(candidate)
        available.append(profile)
        if profile["region_id_field_present"]:
            region_sets.append(identifiers)
        date_sets.append(dates)
    common_dates = set.intersection(*date_sets) if date_sets else set()
    identical_content: dict[str, list[str]] = {}
    for profile in available:
        identical_content.setdefault(profile["sha256"], []).append(profile["filename"])
    return {
        "inventory_format": 1,
        "tooling_introduced": "2026-11-08",
        "tooling_scope": "New static input audit, separate from the original 2025 project code.",
        "source_notebook_sha256": sha256(notebook_path),
        "notebook_code_executed": False,
        "models_replayed": False,
        "downloads_performed": False,
        "data_read_scope": "CSV basenames resolved only inside the supplied data directory; symlinks outside it are blocked.",
        "requirements": requirements,
        "available_required_file_count": len(available),
        "missing_required_file_count": len(missing),
        "missing_required_files": missing,
        "blocked_outside_data_directory": blocked,
        "available_files": available,
        "distinct_available_content_hash_count": len(identical_content),
        "byte_identical_available_file_groups": sorted(
            sorted(names) for names in identical_content.values() if len(names) > 1),
        "common_region_id_count_across_available_id_tables": len(set.intersection(*region_sets)) if region_sets else None,
        "common_date_columns_across_available_files": {
            "count": len(common_dates),
            "first": min(common_dates) if common_dates else None,
            "last": max(common_dates) if common_dates else None,
        },
        "interpretation": [
            "Region counts include country and MSA rows where present; no national/metro metric averaging is performed.",
            "Shared column or identifier counts do not prove complete nonmissing observations or valid joins.",
            "Byte-identical filenames are identified without changing or combining their records.",
            "The CSVs do not record an acquisition or provider-release timestamp in their metadata columns.",
            "Current provider downloads may revise history or extend dates and need not match these retained snapshot hashes.",
            "Missing files are listed without being fetched; this audit does not establish an end-to-end replay.",
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    sources = {args.notebook.resolve()}
    if args.data_dir.is_dir():
        sources.update(p.resolve() for p in args.data_dir.iterdir()
                       if p.is_file() and p.suffix.lower() == ".csv")
    if output in sources or args.output.suffix.lower() == ".csv":
        parser.error("Output must differ from the notebook and every source CSV")
    try:
        result = audit_inputs(args.notebook, args.data_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, UnicodeError, csv.Error) as error:
        parser.exit(1, f"Input audit failed: {type(error).__name__}\n")
    print(f"Inventoried {result['available_required_file_count']} available and {result['missing_required_file_count']} missing CSV inputs; no project code executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
