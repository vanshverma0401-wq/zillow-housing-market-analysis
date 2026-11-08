"""Complete-final-project export checks; no notebook cells are executed."""
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
    cells = [{"cell_type": "code", "metadata": {"original": "original-cell-metadata"},
              "execution_count": 23, "source": [f"# original source cell {index}\n"],
              "outputs": []} for index in range(70)]
    cells[0] = {"cell_type": "markdown", "metadata": {"original": True},
                "source": ["![institution](institution_logo.png)\n", "# Complete original project\n"]}
    cells[10]["source"] = ['raise RuntimeError("MUST NOT EXECUTE")\n']
    cells[55]["outputs"] = [{"output_type": "stream", "name": "stdout", "text": ["Original saved diagnostic\n"]}]
    for index, definitions in exporter.FIGURES.items():
        cells[index]["outputs"] = [{"output_type": "display_data", "data": {
            "image/png": PNG, "text/plain": "<Figure size 1x1 with 1 Axes>"},
            "metadata": {"original": "original-output-metadata"}} for _ in definitions]
    cells[65]["source"] = ["# Original classroom ROI scenario code\n"]
    cells[66] = {"cell_type": "markdown", "metadata": {}, "source": ["ORIGINAL_ROI_CONCLUSION\n"]}
    cells[68]["source"] = ["# Original classroom monthly-income scenario code\n"]
    cells[69] = {"cell_type": "markdown", "metadata": {}, "source": ["ORIGINAL_INCOME_CONCLUSION\n"]}
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"language_info": {"name": "python", "version": "3.12.4"},
                         "original": "original-notebook-metadata"}}


class ExportTests(unittest.TestCase):
    def test_complete_notebook_bytes_and_all_saved_outputs_are_preserved_without_execution(self):
        source = fixture()
        raw = (json.dumps(source, indent=3) + "\n").encode()
        payloads, inventory = exporter.build_payloads(raw)
        self.assertEqual(payloads["notebooks/zillow_home_value_analysis.ipynb"], raw)
        public = json.loads(payloads["notebooks/zillow_home_value_analysis.ipynb"])
        self.assertEqual(public, source)
        self.assertEqual(inventory["public_cell_count"], 70)
        self.assertTrue(inventory["all_original_outputs_preserved"])
        self.assertTrue(inventory["all_original_metadata_preserved"])
        self.assertFalse(inventory["execution_performed"])
        self.assertIn("MUST NOT EXECUTE", json.dumps(public))
        self.assertFalse(inventory["matches_verified_shared_source_hash"])

    def test_every_cell_and_original_conclusion_is_retained_with_no_inserted_review(self):
        source = fixture()
        payloads, inventory = exporter.build_payloads(json.dumps(source).encode())
        public = json.loads(payloads["notebooks/zillow_home_value_analysis.ipynb"])
        self.assertEqual(inventory["omitted_source_cell_indices"], [])
        self.assertEqual(inventory["replaced_markdown_source_cells"], [])
        self.assertEqual(inventory["warnings_before_source_cells"], [])
        for mapping in inventory["cell_mapping"]:
            index = mapping["source_cell_index"]
            self.assertEqual(mapping["public_cell_index"], index)
            self.assertEqual(public["cells"][index], source["cells"][index])
        text = json.dumps(public)
        for retained in ["ORIGINAL_ROI_CONCLUSION", "ORIGINAL_INCOME_CONCLUSION", "institution_logo.png"]:
            self.assertIn(retained, text)

    def test_all_eighteen_saved_pngs_are_byte_exact_and_scenarios_are_labelled(self):
        payloads, inventory = exporter.build_payloads(json.dumps(fixture()).encode())
        manifest = json.loads(payloads["technical/figure_manifest.json"])
        self.assertEqual((inventory["published_png_count"], manifest["figure_count"]), (18, 18))
        self.assertEqual(manifest["omitted_png_source_cells"], [])
        for figure in manifest["figures"]:
            self.assertEqual(payloads[figure["asset"]], base64.b64decode(PNG))
            self.assertEqual((figure["width"], figure["height"]), (1, 1))
            self.assertFalse(figure["validated_finding"])
            self.assertEqual(figure["data_attribution"], "Data Provided by Zillow Group")
        scenarios = [f for f in manifest["figures"] if f["source_cell_index"] in {65, 68}]
        self.assertEqual(len(scenarios), 2)
        self.assertTrue(all(f["evidence_class"] == "historical_unvalidated_classroom_scenario" for f in scenarios))

    def test_private_content_and_active_html_anywhere_are_rejected_before_output(self):
        mutations = [
            lambda d: d["cells"][10].update(source=["'/Users/private/input.csv'"]),
            lambda d: d["metadata"].update(path="/Users/private/project"),
            lambda d: d["cells"][55]["outputs"][0].update(text=["person@example.com"]),
            lambda d: d["cells"][32]["outputs"][0]["data"].update({"text/html": "<script>unsafe()</script>"}),
            lambda d: d["cells"][68].update(source=["api_key='private-value'"]),
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for mutate in mutations:
                notebook = fixture()
                mutate(notebook)
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
            self.assertEqual((output / "notebooks/zillow_home_value_analysis.ipynb").read_bytes(), original)
            alias = root / "collision"
            (alias / "notebooks").mkdir(parents=True)
            (alias / "notebooks/zillow_home_value_analysis.ipynb").symlink_to(source)
            with self.assertRaisesRegex(exporter.ExportError, "overwrite"):
                exporter.export_evidence(source, alias)
            self.assertEqual(source.read_bytes(), original)

    def test_invalid_or_excessive_notebooks_and_unmapped_pngs_are_rejected(self):
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
        notebook = fixture()
        notebook["cells"][1]["outputs"] = [{"data": {"image/png": PNG}}]
        with self.assertRaisesRegex(exporter.ExportError, "outside the complete figure map"):
            exporter.build_payloads(json.dumps(notebook).encode())


if __name__ == "__main__":
    unittest.main()
