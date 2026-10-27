"""Testes offline da integração manual; modelos e notas são fictícios.

Executar: python scripts/test_manual_requirements.py
As entradas e saídas ficam em uma pasta temporária. Não acessa rede ou Neo4j.
"""

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from hardware_catalog import MANUAL_COLUMNS, read_catalog
from hardware_matcher import normalize_name, read_aliases
from hardware_review import collect_review
from process_requirements import process_requirements


class ManualRequirementsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gamecompass-requirements-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalog_path = self.root / "manual.csv"
        self.aliases_path = self.root / "aliases.json"
        models = [
            ("CPU", "CPU fictícia A", "300"),
            ("CPU", "CPU fictícia pendente", ""),
            ("GPU", "GPU fictícia A", "500"),
            ("GPU", "GPU fictícia B", "400"),
            ("GPU", "GPU fictícia pendente", ""),
        ]
        with self.catalog_path.open("w", encoding="utf-8", newline="") as handle:
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
            for row in read_catalog(self.catalog_path, catalog_format="manual")
        }
        self.aliases_path.write_text(json.dumps([
            {"component_type": "CPU", "alias": "CPU A", "canonical_name": "CPU fictícia A"},
            {"component_type": "GPU", "alias": "GPU A", "canonical_name": "GPU fictícia A"},
            {"component_type": "GPU", "alias": "GPU P", "canonical_name": "GPU fictícia pendente"},
        ]), encoding="utf-8")
        self.aliases = read_aliases(self.aliases_path, self.catalog)

    def html(self, gpu="GPU A", cpu="CPU A", ram="Memória: 8192 MB de RAM"):
        return f"<strong>Mínimos:</strong><br>Processador: {cpu}<br>{ram}<br>Placa de vídeo: {gpu}"

    def document(self, **kwargs):
        return process_requirements(
            self.html(**kwargs), self.catalog, self.aliases, catalog_format="manual",
        )

    def save(self, document, name="requirements.json"):
        path = self.root / name
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        return path

    def cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(Path(__file__).with_name(script)), *map(str, args)],
            capture_output=True, text=True, check=False,
        )

    def process_cli(self, *args):
        return self.cli(
            "process_requirements.py", "--format", "manual",
            "--catalog", self.catalog_path, "--aliases", self.aliases_path, *args,
        )

    def test_resolved_manual_requirements_keep_version_and_thresholds(self):
        result = self.document(gpu="GPU A ou GPU fictícia B")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["requirements"], {"ram_gb": 8, "cpu_score": 300, "gpu_score": 400})
        self.assertEqual(result["catalog_format"], "manual")
        self.assertEqual(result["score_version"], "manual_v1")
        self.assertEqual(result["issues"], [])
        self.assertNotIn("passmark_score", json.dumps(result))

    def test_known_gpu_without_score_keeps_identity_and_partial_results(self):
        result = self.document(gpu="GPU P")
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["requirements"], {"ram_gb": 8, "cpu_score": 300, "gpu_score": None})
        alternative = result["hardware"]["GPU"]["alternatives"][0]
        self.assertEqual(alternative["status"], "matched")
        self.assertEqual(alternative["name"], "GPU fictícia pendente")
        self.assertEqual(result["issues"], ["GPU: há alternativas sem classificação de desempenho."])

    def test_unknown_gpu_is_reported_as_unidentified(self):
        result = self.document(gpu="GPU desconhecida")
        self.assertIsNone(result["requirements"]["gpu_score"])
        self.assertEqual(result["issues"], ["GPU: há alternativas não identificadas."])

    def test_pending_and_unknown_alternatives_have_distinct_issues(self):
        result = self.document(gpu="GPU P ou GPU desconhecida")
        self.assertEqual(len(result["issues"]), 2)
        self.assertIsNone(result["hardware"]["GPU"]["required_score"])

    def test_pending_cpu_does_not_erase_valid_gpu_score(self):
        result = self.document(cpu="CPU fictícia pendente")
        self.assertIsNone(result["requirements"]["cpu_score"])
        self.assertEqual(result["requirements"]["gpu_score"], 500)
        self.assertIn("CPU: há alternativas sem classificação de desempenho.", result["issues"])

    def test_missing_ram_is_pending_not_zero(self):
        result = self.document(ram="")
        self.assertEqual(result["status"], "needs_review")
        self.assertIsNone(result["requirements"]["ram_gb"])
        self.assertIn("RAM: campo ausente.", result["issues"])

    def test_empty_alternative_preserves_other_fields(self):
        result = self.document(cpu="CPU A ou ")
        self.assertEqual(result["status"], "needs_review")
        self.assertIsNone(result["hardware"]["CPU"])
        self.assertEqual(result["requirements"]["gpu_score"], 500)

    def test_resolved_review_has_no_pending_items(self):
        result = collect_review([self.save(self.document())])
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["pending_models"], [])
        self.assertEqual(result["pending_classifications"], [])
        self.assertEqual(result["score_version"], "manual_v1")

    def test_pending_classifications_group_canonical_model_and_keep_aliases(self):
        first = self.save(self.document(gpu="GPU P"), "one.json")
        second = self.save(self.document(gpu="GPU fictícia pendente"), "two.json")
        result = collect_review([first, second])
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["pending_models"], [])
        self.assertEqual(len(result["pending_classifications"]), 1)
        item = result["pending_classifications"][0]
        self.assertEqual(item["name"], "GPU fictícia pendente")
        self.assertEqual(item["queries"], ["GPU P", "GPU fictícia pendente"])
        self.assertEqual(item["sources"], [str(first), str(second)])

    def test_unknown_models_stay_in_pending_models(self):
        result = collect_review([self.save(self.document(gpu="GPU desconhecida"))])
        self.assertEqual(result["pending_models"][0]["query"], "GPU desconhecida")
        self.assertEqual(result["pending_classifications"], [])

    def test_review_keeps_both_kinds_of_pending_item(self):
        result = collect_review([self.save(self.document(gpu="GPU P ou GPU desconhecida"))])
        self.assertEqual(len(result["pending_models"]), 1)
        self.assertEqual(len(result["pending_classifications"]), 1)
        self.assertEqual(len(result["document_issues"][0]["issues"]), 2)

    def test_review_rejects_mixed_formats(self):
        manual = self.save(self.document(), "manual.json")
        legacy = self.save({"status": "needs_review", "issues": ["Campos ausentes."], "hardware": {"CPU": None, "GPU": None}}, "legacy.json")
        with self.assertRaisesRegex(ValueError, "misture"):
            collect_review([manual, legacy])

    def test_review_rejects_missing_or_incompatible_version_metadata(self):
        for location in ("root", "block", "alternative", "missing_format"):
            with self.subTest(location=location):
                data = self.document()
                if location == "root":
                    data["score_version"] = "manual_v2"
                elif location == "block":
                    data["hardware"]["GPU"]["score_version"] = "manual_v2"
                elif location == "alternative":
                    data["hardware"]["GPU"]["alternatives"][0]["score_version"] = "manual_v2"
                else:
                    del data["catalog_format"]
                with self.assertRaises(ValueError):
                    collect_review([self.save(data)])

    def test_review_rejects_incoherent_classification(self):
        for patch in ({"score_status": "classified"}, {"performance_score": 0}, {"performance_score": True}, {"passmark_score": 500}):
            with self.subTest(patch=patch):
                data = self.document(gpu="GPU P")
                data["hardware"]["GPU"]["alternatives"][0].update(patch)
                with self.assertRaises(ValueError):
                    collect_review([self.save(data)])

    def test_cli_process_and_review_keep_source_hashes(self):
        raw = self.root / "raw.html"
        raw.write_text(self.html(gpu="GPU P"), encoding="utf-8")
        output = self.root / "processed.json"
        result = self.process_cli("--input", raw, "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(output.read_text(encoding="utf-8"))
        for field, path in (("input_sha256", raw), ("catalog_sha256", self.catalog_path), ("aliases_sha256", self.aliases_path)):
            self.assertEqual(data["source"][field], hashlib.sha256(path.read_bytes()).hexdigest())
        review_path = self.root / "review.json"
        review = self.cli("hardware_review.py", "--input", output, "--output", review_path)
        self.assertEqual(review.returncode, 0, review.stderr)
        self.assertEqual(json.loads(review_path.read_text())["pending_classifications"][0]["name"], "GPU fictícia pendente")

    def test_cli_cannot_overwrite_raw_catalog_or_aliases(self):
        raw = self.root / "raw.html"
        raw.write_text(self.html(), encoding="utf-8")
        for target in (raw, self.catalog_path, self.aliases_path):
            with self.subTest(target=target):
                previous = target.read_bytes()
                result = self.process_cli("--input", raw, "--output", target)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(target.read_bytes(), previous)

    def test_invalid_catalog_preserves_existing_processed_output(self):
        output = self.root / "previous.json"
        output.write_bytes(b"previous result\n")
        self.catalog_path.write_text(self.catalog_path.read_text().replace("manual_v1", "manual_v2"), encoding="utf-8")
        result = self.process_cli("--text", self.html(), "--output", output)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_bytes(), b"previous result\n")

    def test_invalid_document_preserves_previous_review_output(self):
        invalid = self.root / "invalid.json"
        invalid.write_text("[]", encoding="utf-8")
        output = self.root / "previous.json"
        output.write_bytes(b"previous review\n")
        result = self.cli("hardware_review.py", "--input", invalid, "--output", output)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_bytes(), b"previous review\n")

    def test_legacy_default_contract_is_preserved(self):
        legacy = {
            ("CPU", "cpu a"): {"name": "CPU A", "passmark_score": 1234},
            ("GPU", "gpu a"): {"name": "GPU A", "passmark_score": 2345},
        }
        data = process_requirements(self.html(), legacy, {})
        self.assertEqual(data["requirements"], {"ram_gb": 8, "cpu_score": 1234, "gpu_score": 2345})
        self.assertNotIn("score_version", data)
        review = collect_review([self.save(data)])
        self.assertEqual(review["status"], "resolved")
        self.assertNotIn("pending_classifications", review)

    def test_review_cli_rejects_repeated_inputs(self):
        source = self.save(self.document())
        output = self.root / "review.json"
        result = self.cli("hardware_review.py", "--input", source, source, "--output", output)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
