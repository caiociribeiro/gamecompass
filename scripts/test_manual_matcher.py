"""Testes offline do matching manual; todos os modelos e notas são fictícios.

Executar: python scripts/test_manual_matcher.py
Os arquivos de teste ficam em uma pasta temporária. Não há acesso ao Neo4j.
"""

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from hardware_catalog import MANUAL_COLUMNS, read_catalog
from hardware_matcher import match_alternatives, match_hardware, normalize_name, read_aliases


class ManualMatcherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gamecompass-matcher-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.csv_path = self.root / "manual.csv"
        self.aliases_path = self.root / "aliases.json"
        models = [
            ("GPU", "GPU fictícia 6GB", "500"),
            ("GPU", "GPU fictícia 3GB", "400"),
            ("GPU", "GPU fictícia pendente", ""),
            ("CPU", "CPU fictícia", "300"),
        ]
        with self.csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS)
            writer.writeheader()
            for kind, name, score in models:
                writer.writerow({
                    "component_type": kind, "name": name,
                    "performance_score": score, "score_version": "manual_v1",
                    "source_url": "https://example.org/fixture",
                    "collected_at": "2026-10-27T00:00:00Z",
                    "notes": "Fixture fictícia; não representa benchmark real.",
                })
        self.catalog = {
            (row["component_type"], normalize_name(row["name"])): row
            for row in read_catalog(self.csv_path, catalog_format="manual")
        }
        self.aliases_path.write_text(json.dumps([{
            "component_type": "GPU", "alias": "GPU A",
            "canonical_name": "GPU fictícia 6GB",
        }]), encoding="utf-8")
        self.aliases = read_aliases(self.aliases_path, self.catalog)

    def single(self, name, kind="GPU"):
        return match_hardware(name, kind, self.catalog, self.aliases, catalog_format="manual")

    def alternatives(self, text, kind="GPU"):
        return match_alternatives(text, kind, self.catalog, self.aliases, catalog_format="manual")

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(Path(__file__).with_name("hardware_matcher.py")), *map(str, args)],
            capture_output=True, text=True, check=False,
        )

    def test_exact_model_has_manual_score_and_version(self):
        result = self.single("GPU fictícia 6GB")
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["performance_score"], 500)
        self.assertEqual(result["score_version"], "manual_v1")
        self.assertEqual(result["score_status"], "classified")
        self.assertNotIn("passmark_score", result)

    def test_alias_preserves_canonical_model(self):
        result = self.single("GPU A")
        self.assertEqual(result["name"], "GPU fictícia 6GB")
        self.assertEqual(result["method"], "alias")
        self.assertEqual(result["performance_score"], 500)

    def test_spaces_and_case_are_normalized(self):
        self.assertEqual(self.single("  gpu   FICTÍCIA 6gb  ")["performance_score"], 500)

    def test_memory_variants_are_distinct(self):
        self.assertEqual(self.single("GPU fictícia 3GB")["performance_score"], 400)
        self.assertEqual(self.single("GPU fictícia 8GB")["status"], "not_found")

    def test_types_are_kept_separate(self):
        self.assertEqual(self.single("GPU fictícia 6GB", "CPU")["status"], "not_found")
        self.assertEqual(self.single("CPU fictícia", "CPU")["performance_score"], 300)

    def test_known_unclassified_model_keeps_identity(self):
        result = self.single("GPU fictícia pendente")
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["score_status"], "pending")
        self.assertEqual(result["name"], "GPU fictícia pendente")
        self.assertIsNone(result["performance_score"])

    def test_unknown_model_is_not_classified(self):
        result = self.single("Modelo desconhecido")
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["score_status"], "not_found")
        for field in ("name", "performance_score", "score_version", "method"):
            self.assertIsNone(result[field])

    def test_resolved_alternatives_use_lowest_score(self):
        result = self.alternatives("GPU A ou GPU fictícia 3GB")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["required_score"], 400)
        self.assertEqual(result["score_version"], "manual_v1")
        self.assertEqual(len(result["alternatives"]), 2)

    def test_pending_alternative_blocks_threshold(self):
        result = self.alternatives("GPU A or GPU fictícia pendente")
        self.assertEqual(result["status"], "needs_review")
        self.assertIsNone(result["required_score"])

    def test_unknown_alternative_blocks_threshold(self):
        result = self.alternatives("GPU A ou Modelo desconhecido")
        self.assertEqual(result["status"], "needs_review")
        self.assertIsNone(result["required_score"])

    def test_empty_alternative_is_rejected(self):
        with self.assertRaises(ValueError):
            self.alternatives("GPU A ou ")

    def test_incompatible_score_version_is_rejected(self):
        key = ("GPU", normalize_name("GPU fictícia 3GB"))
        self.catalog[key]["score_version"] = "manual_v2"
        with self.assertRaisesRegex(ValueError, "score_version"):
            self.alternatives("GPU A ou GPU fictícia 3GB")

    def test_invalid_manual_scores_are_rejected(self):
        key = ("GPU", normalize_name("GPU fictícia 6GB"))
        for invalid in (0, -1, True, "500", 500.0):
            with self.subTest(score=invalid):
                self.catalog[key]["performance_score"] = invalid
                with self.assertRaises(ValueError):
                    self.single("GPU A")

    def test_legacy_functions_keep_previous_contract(self):
        legacy = {
            ("GPU", "gpu legada a"): {"name": "GPU legada A", "passmark_score": 1234},
            ("GPU", "gpu legada b"): {"name": "GPU legada B", "passmark_score": 2345},
        }
        result = match_hardware("GPU legada A", "GPU", legacy, {})
        self.assertEqual(result["passmark_score"], 1234)
        self.assertNotIn("performance_score", result)
        self.assertEqual(match_alternatives("GPU legada A or GPU legada B", "GPU", legacy, {})["required_score"], 1234)

    def test_cli_reads_validated_manual_catalog_and_aliases(self):
        result = self.cli(
            "--format", "manual", "--catalog", self.csv_path,
            "--aliases", self.aliases_path, "--type", "GPU",
            "--name", "GPU A ou GPU fictícia 3GB", "--alternatives",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["required_score"], 400)
        self.assertEqual(json.loads(result.stdout)["score_version"], "manual_v1")

    def test_cli_rejects_legacy_header_in_manual_mode(self):
        legacy = self.root / "legacy.csv"
        legacy.write_text("component_type,name,passmark_score,benchmark,source_url,collected_at\n", encoding="utf-8")
        result = self.cli("--format", "manual", "--catalog", legacy, "--type", "GPU", "--name", "GPU A")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Cabeçalho", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
