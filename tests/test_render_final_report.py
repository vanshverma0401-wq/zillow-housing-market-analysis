"""Synthetic checks for complete, non-executing final-report rendering."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_final_report.py"
SPEC = importlib.util.spec_from_file_location("render_final_report", SCRIPT)
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def fixture():
    image = b"synthetic-png-payload"
    notebook = {"cells": [
        {"cell_type": "markdown", "source": ["![st_thomas](st_thomas.jpg)\n", "# Original final question six\nOriginal conclusion 35%.\n"]},
        {"cell_type": "code", "source": ["raise RuntimeError('MUST NEVER EXECUTE')\n", "print('original source')\n"],
         "outputs": [{"output_type": "stream", "text": ["Saved result: 7\n"]}]},
        {"cell_type": "code", "source": ["plot()\n"], "outputs": [{"output_type": "display_data", "data": {
            "image/png": base64.b64encode(image).decode(), "text/plain": ["<Figure with one axis>"]}}]},
    ]}
    raw = json.dumps(notebook).encode()
    figures = {"source_notebook_sha256": hashlib.sha256(raw).hexdigest(), "figures": [{
        "source_cell_index": 2, "source_output_index": 0, "asset": "assets/figures/example.png",
        "sha256": hashlib.sha256(image).hexdigest()}]}
    return raw, figures


class FinalReportTests(unittest.TestCase):
    def test_every_cell_narrative_source_and_saved_output_is_preserved_without_execution(self):
        raw, figures = fixture()
        markdown, manifest = report.build_report(raw, figures, "assets/st_thomas.jpg")
        self.assertIn("Original conclusion 35%.", markdown)
        self.assertIn("raise RuntimeError('MUST NEVER EXECUTE')", markdown)
        self.assertIn("Saved result: 7", markdown)
        self.assertIn("<Figure with one axis>", markdown)
        self.assertIn("assets/figures/example.png", markdown)
        self.assertEqual(manifest["rendered_cell_count"], 3)
        self.assertEqual(manifest["saved_output_count"], 2)
        self.assertEqual(manifest["saved_png_count"], 1)
        self.assertFalse(manifest["notebook_executed"])
        self.assertFalse(manifest["narrative_or_code_omitted"])
        self.assertIn("![st_thomas](assets/st_thomas.jpg)", markdown)
        self.assertEqual([c["source_text_unchanged"] for c in manifest["cells"]], [False, True, True])
        self.assertEqual(manifest["missing_original_markdown_assets"], [])

    def test_unsupplied_original_image_references_are_preserved_and_declared(self):
        raw, figures = fixture()
        notebook = json.loads(raw)
        oak_source = "Original neighborhood discussion.\n\n![oak_grove](oak_grove.png)\n\nOriginal conclusion."
        notebook["cells"].append({"cell_type": "markdown", "source": [oak_source]})
        changed = json.dumps(notebook).encode()
        figures["source_notebook_sha256"] = hashlib.sha256(changed).hexdigest()
        markdown, manifest = report.build_report(changed, figures)
        self.assertIn("![st_thomas](st_thomas.jpg)", markdown)
        self.assertIn(oak_source, markdown)
        self.assertTrue(all(c["source_text_unchanged"] for c in manifest["cells"]))
        missing = manifest["missing_original_markdown_assets"]
        self.assertEqual([m["asset"] for m in missing], ["st_thomas.jpg", "oak_grove.png"])
        self.assertTrue(all(m["original_reference_preserved"] for m in missing))
        self.assertIn("Publication note (outside the original source)", markdown)
        self.assertIn("not supplied in the recovered project folder", markdown)
        self.assertFalse(manifest["narrative_or_code_omitted"])
        self.assertEqual(manifest["formatting_exceptions"], [])

    def test_source_and_image_fingerprints_prevent_incorrect_figure_substitution(self):
        raw, figures = fixture()
        figures["source_notebook_sha256"] = "incorrect"
        with self.assertRaisesRegex(report.ReportError, "different source"):
            report.build_report(raw, figures)
        raw, figures = fixture()
        figures["figures"][0]["sha256"] = "incorrect"
        with self.assertRaisesRegex(report.ReportError, "Figure fingerprint"):
            report.build_report(raw, figures)

    def test_unsafe_paths_active_markup_and_unknown_mime_fail_before_writing(self):
        raw, figures = fixture()
        figures["figures"][0]["asset"] = "../private.png"
        with self.assertRaisesRegex(report.ReportError, "Unsafe figure path"):
            report.build_report(raw, figures)
        for bad in ["/Users/private/record.txt", "<script>alert(1)</script>"]:
            notebook = json.loads(raw)
            notebook["cells"][0]["source"] = [bad]
            changed = json.dumps(notebook).encode()
            figures["source_notebook_sha256"] = hashlib.sha256(changed).hexdigest()
            figures["figures"][0]["asset"] = "assets/figures/example.png"
            with self.assertRaisesRegex(report.ReportError, "Unsafe source"):
                report.build_report(changed, figures)
        notebook = json.loads(raw)
        notebook["cells"][2]["outputs"][0]["data"]["text/html"] = "<table></table>"
        changed = json.dumps(notebook).encode()
        figures["source_notebook_sha256"] = hashlib.sha256(changed).hexdigest()
        with self.assertRaisesRegex(report.ReportError, "Unexpected saved output MIME"):
            report.build_report(changed, figures)

    def test_cli_cannot_overwrite_input_or_figure_manifest_even_through_symlink(self):
        raw, figures = fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, figure_file = root / "source.ipynb", root / "figures.json"
            source.write_bytes(raw)
            figure_file.write_text(json.dumps(figures))
            alias = root / "alias.ipynb"
            alias.symlink_to(source)
            for output in [source, figure_file, alias]:
                with self.assertRaises(SystemExit):
                    report.main([str(source), "--figure-manifest", str(figure_file), "--output", str(output),
                                 "--manifest-output", str(root / "report.json")])
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(json.loads(figure_file.read_text()), figures)

    def test_fences_cannot_be_closed_by_original_backticks(self):
        value = "print('```')\n"
        rendered = report.fenced(value, "python")
        self.assertTrue(rendered.startswith("````python\n"))
        self.assertTrue(rendered.endswith("````\n"))
        self.assertIn(value, rendered)


if __name__ == "__main__":
    unittest.main()
