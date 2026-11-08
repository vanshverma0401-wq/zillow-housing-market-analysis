"""Synthetic source-publication checks; no Zillow data or cell execution required."""
from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_notebook_evidence.py"
SPEC = importlib.util.spec_from_file_location("export_notebook_evidence", SCRIPT)
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6e9sAAAAASUVORK5CYII="


def fixture() -> dict:
    cells = [{"cell_type": "code", "metadata": {"private": "private-cell-metadata"},
              "execution_count": 23, "source": [f"# original source cell {index}\n"],
              "outputs": [{"output_type": "display_data", "data": {"text/html": "<script>PRIVATE_OUTPUT</script>"}, "metadata": {}}]}
             for index in range(70)]
    for index in exporter.REPLACEMENTS:
        cells[index].update({"cell_type": "markdown", "source": ["ORIGINAL_UNVERIFIED_RECOMMENDATION\n"]})
        cells[index].pop("outputs")
        cells[index].pop("execution_count")
    cells[0]["source"] = ["![institution](institution_logo.png)\n"]
    cells[10]["source"] = ['raise RuntimeError("MUST NOT EXECUTE")\n']
    for index, definitions in exporter.FIGURES.items():
        cells[index]["outputs"] = [{"output_type": "display_data", "data": {
            "image/png": PNG, "text/html": "<script>PRIVATE_OUTPUT</script>"},
            "metadata": {"private": "private-output-metadata"}} for _ in definitions]
    for index in range(62, 70):
        cells[index]["source"] = ["PRIVATE_ROI_PROMISE password='private-value' /Users/private/project\n"]
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"private_path": "/Users/private/project", "widgets": "PRIVATE_WIDGET_STATE"}}


class ExportTests(unittest.TestCase):
    def test_strips_outputs_metadata_and_profit_sections_without_executing_code(self):
        source = fixture()
        payloads, inventory = exporter.build_payloads(json.dumps(source).encode())
        public = json.loads(payloads["notebooks/zillow_home_value_analysis.ipynb"])
        text = json.dumps(public)
        for private in ["PRIVATE_OUTPUT", "PRIVATE_WIDGET_STATE", "PRIVATE_ROI_PROMISE",
                        "/Users/private", "private-cell-metadata", "institution_logo.png"]:
            self.assertNotIn(private, text)
        self.assertIn("MUST NOT EXECUTE", text)
        for cell in public["cells"]:
            self.assertEqual(cell["metadata"], {})
            if cell["cell_type"] == "code":
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])
        self.assertEqual(inventory["omitted_source_cell_indices"], list(range(62, 70)))
        self.assertFalse(inventory["execution_performed"])

    def test_retained_code_is_exact_and_review_warnings_are_explicit(self):
        source = fixture()
        payloads, inventory = exporter.build_payloads(json.dumps(source).encode())
        public = json.loads(payloads["notebooks/zillow_home_value_analysis.ipynb"])
        for mapping in inventory["cell_mapping"]:
            index = mapping["source_cell_index"]
            if index not in exporter.REPLACEMENTS:
                self.assertEqual(exporter.source_text(public["cells"][mapping["public_cell_index"]]),
                                 exporter.source_text(source["cells"][index]))
        text = json.dumps(public)
        for phrase in ["separate long-form sales dataframe", "ratio, not a number of days",
                       "random 80/20 row split", "24 calendar months", "byte-for-byte submission identity"]:
            self.assertIn(phrase, text)

    def test_saved_pngs_are_byte_exact_and_risky_figures_are_classified(self):
        payloads, inventory = exporter.build_payloads(json.dumps(fixture()).encode())
        manifest = json.loads(payloads["technical/figure_manifest.json"])
        self.assertEqual((inventory["published_png_count"], manifest["figure_count"]), (16, 16))
        for figure in manifest["figures"]:
            self.assertEqual(payloads[figure["asset"]], base64.b64decode(PNG))
            self.assertEqual((figure["width"], figure["height"]), (1, 1))
            self.assertNotIn(figure["source_cell_index"], [65, 68])
            self.assertFalse(figure["validated_finding"])
            self.assertEqual(figure["data_attribution"], "Data Provided by Zillow Group")
        legacy = [f for f in manifest["figures"] if f["source_cell_index"] == 49]
        self.assertEqual(len(legacy), 3)
        self.assertTrue(all(f["evidence_class"] == "legacy_alignment_and_units_diagnostic" for f in legacy))

    def test_source_private_patterns_and_active_markup_fail_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for unsafe in ["'/Users/private/input.csv'", "'<script>unsafe()</script>'", "api_key='private-value'"]:
                notebook = fixture()
                notebook["cells"][10]["source"] = [unsafe]
                source = root / "input.ipynb"
                source.write_text(json.dumps(notebook))
                output = root / "published"
                with self.assertRaises(exporter.ExportError):
                    exporter.export_evidence(source, output)
                self.assertFalse(output.exists())

    def test_source_bytes_preserved_and_destination_alias_cannot_overwrite_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input.ipynb"
            source.write_text(json.dumps(fixture()))
            original = source.read_bytes()
            output = root / "published"
            exporter.export_evidence(source, output)
            self.assertEqual(source.read_bytes(), original)
            alias = root / "collision"
            (alias / "notebooks").mkdir(parents=True)
            (alias / "notebooks/zillow_home_value_analysis.ipynb").symlink_to(source)
            with self.assertRaisesRegex(exporter.ExportError, "overwrite"):
                exporter.export_evidence(source, alias)
            self.assertEqual(source.read_bytes(), original)

    def test_invalid_or_excessive_notebooks_and_pngs_are_rejected(self):
        with self.assertRaises(exporter.ExportError):
            exporter.build_payloads(b"{broken")
        notebook = fixture()
        notebook["cells"].pop()
        with self.assertRaisesRegex(exporter.ExportError, "70-cell"):
            exporter.build_payloads(json.dumps(notebook).encode())
        with patch.object(exporter, "MAX_NOTEBOOK_BYTES", 10):
            with self.assertRaisesRegex(exporter.ExportError, "size limit"):
                exporter.build_payloads(json.dumps(fixture()).encode())
        notebook = fixture()
        notebook["cells"][32]["outputs"][0]["data"]["image/png"] = "not base64"
        with self.assertRaises(exporter.ExportError):
            exporter.build_payloads(json.dumps(notebook).encode())


if __name__ == "__main__":
    unittest.main()
