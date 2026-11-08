"""Synthetic tests for the new November 2026 input inventory utility."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_inputs", ROOT / "scripts" / "audit_inputs.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def notebook(*code: str) -> dict:
    return {"cells": [{"cell_type": "code", "source": text} for text in code], "nbformat": 4}


class SyntaxTests(unittest.TestCase):
    def test_comments_are_ignored_and_repeated_calls_count_separately(self):
        result = audit.required_inputs(notebook(
            "# pd.read_csv('comment.csv')\na=pd.read_csv('one.csv')\nb=pd.read_csv('one.csv')",
            "read_csv(filepath_or_buffer='two.csv')\ntext=\"pd.read_csv('not_a_call.csv')\""))
        self.assertEqual(result["literal_csv_call_count"], 3)
        self.assertEqual(result["distinct_required_csv_count"], 2)
        self.assertEqual(result["calls_by_filename"], {"one.csv": 2, "two.csv": 1})

    def test_magics_dynamic_calls_and_unparseable_cells_are_reported(self):
        result = audit.required_inputs(notebook(
            "%matplotlib inline\n!pip install hypothetical\npd.read_csv('one.csv')\npd.read_csv(variable)",
            "this is invalid python ?"))
        self.assertEqual(result["required_files"], ["one.csv"])
        self.assertEqual(result["ipython_magic_or_shell_lines_omitted"], 2)
        self.assertEqual(result["dynamic_read_csv_call_count"], 1)
        self.assertEqual(result["unparsed_code_cells"][0]["cell_number"], 2)

    def test_literal_paths_do_not_select_external_locations_or_emit_paths(self):
        result = audit.required_inputs(notebook(
            "pd.read_csv('/Users/synthetic/private/one.csv')\npd.read_csv('../two.csv')\n"
            "pd.read_csv('https://example.invalid/private.csv')"))
        self.assertEqual(result["required_files"], ["one.csv", "two.csv"])
        self.assertEqual(result["literal_path_prefixes_discarded"], 2)
        self.assertEqual(result["ignored_nonlocal_or_non_csv_literal_count"], 1)
        self.assertNotIn("/Users/", json.dumps(result))
        self.assertNotIn("https://", json.dumps(result))


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.nb = self.root / "original.ipynb"
        self.nb.write_text(json.dumps(notebook("pd.read_csv('available.csv')\npd.read_csv('missing.csv')")))
        (self.data / "available.csv").write_text(
            "RegionID,RegionName,RegionType,2024-01-31,2024-02-29,2024-02-30,2024_notes\n"
            "1,Country,country,10,,bad,notes\n"
            "2,Metro,msa,20,21,bad,notes\n"
            "2,Repeated ID,msa,22,23,bad,notes\n")

    def test_profiles_use_valid_iso_dates_and_stable_ids_without_metric_averages(self):
        result = audit.audit_inputs(self.nb, self.data)
        self.assertEqual(result["available_required_file_count"], 1)
        self.assertEqual(result["missing_required_files"], ["missing.csv"])
        profile = result["available_files"][0]
        self.assertEqual(profile["row_count"], 3)
        self.assertEqual(profile["date_column_count"], 2)
        self.assertEqual(profile["first_date_column"], "2024-01-31")
        self.assertEqual(profile["empty_date_cell_count"], 1)
        self.assertIn("2024-02-30", profile["metadata_fields"])
        self.assertEqual(profile["distinct_nonempty_region_ids"], 2)
        self.assertEqual(profile["duplicate_region_id_occurrences"], 1)
        self.assertEqual(profile["region_type_counts"], {"country": 1, "msa": 2})
        self.assertEqual(profile["national_country_row_count"], 1)
        self.assertFalse(profile["numeric_metrics_aggregated"])

    def test_symlink_outside_data_directory_is_blocked_without_reading_it(self):
        outside = self.root / "missing.csv"
        outside.write_text("not a usable CSV")
        (self.data / "missing.csv").symlink_to(outside)
        result = audit.audit_inputs(self.nb, self.data)
        self.assertEqual(result["blocked_outside_data_directory"], ["missing.csv"])
        self.assertEqual(result["missing_required_file_count"], 0)

    def test_identical_contents_under_distinct_names_are_reported_without_collapsing_inputs(self):
        source = self.data / "available.csv"
        alias = self.data / "same_content.csv"
        alias.write_bytes(source.read_bytes())
        self.nb.write_text(json.dumps(notebook(
            "pd.read_csv('available.csv')\npd.read_csv('same_content.csv')")))
        result = audit.audit_inputs(self.nb, self.data)
        self.assertEqual(result["available_required_file_count"], 2)
        self.assertEqual(result["distinct_available_content_hash_count"], 1)
        self.assertEqual(result["byte_identical_available_file_groups"],
                         [["available.csv", "same_content.csv"]])
        self.assertEqual([f["row_count"] for f in result["available_files"]], [3, 3])

    def test_output_collision_with_notebook_any_csv_and_symlink_is_rejected(self):
        extra = self.data / "not_referenced.csv"
        extra.write_text("user data that must not be overwritten")
        alias = self.root / "alias.json"
        alias.symlink_to(extra)
        for target in [self.nb, self.data / "available.csv", extra, alias]:
            before_nb, before_extra = self.nb.read_bytes(), extra.read_bytes()
            with self.assertRaises(SystemExit) as raised:
                audit.main([str(self.nb), "--data-dir", str(self.data), "--output", str(target)])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(self.nb.read_bytes(), before_nb)
            self.assertEqual(extra.read_bytes(), before_extra)

    def test_cli_preserves_sources_and_emits_no_paths_or_raw_region_records(self):
        original_nb = self.nb.read_bytes()
        csv_path = self.data / "available.csv"
        original_csv = csv_path.read_bytes()
        destination = self.root / "inventory.json"
        self.assertEqual(audit.main([str(self.nb), "--data-dir", str(self.data), "--output", str(destination)]), 0)
        self.assertEqual(self.nb.read_bytes(), original_nb)
        self.assertEqual(csv_path.read_bytes(), original_csv)
        text = destination.read_text()
        self.assertNotIn(str(self.root), text)
        self.assertNotIn("Repeated ID", text)
        self.assertNotIn("RegionName\": \"", text)
        self.assertFalse(json.loads(text)["models_replayed"])


if __name__ == "__main__":
    unittest.main()
