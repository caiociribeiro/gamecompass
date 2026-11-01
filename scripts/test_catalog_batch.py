"""Testes offline de curadoria, atualização em lote e requisitos problemáticos.

As respostas Steam e o banco são substituídos por fixtures identificadas.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fetch_steam import save_snapshot
from game_catalog import ROOT, build_catalog, validate_catalog
from hardware_catalog import read_catalog
from hardware_matcher import match_hardware, normalize_name, read_aliases, split_alternatives
from load_games import main as load_main
from process_requirements import process_requirements
from regex_parser import extract_ram_gb
from requirements_curation import FORMAT, apply_curation, read_curation, validate_curated_block
import update_catalog


class CatalogBatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.csv = ROOT / "data/catalog/hardware_manual_v1.csv"
        self.aliases_path = ROOT / "data/catalog/hardware_aliases.json"
        self.index = {(r["component_type"], normalize_name(r["name"])): r
            for r in read_catalog(self.csv, catalog_format="manual")}
        self.aliases = read_aliases(self.aliases_path, self.index)
        self.html = ("OS: Windows 10<br>Processor: Intel i5+<br>Memory: 8 GB RAM"
                     "<br>Graphics: NVIDIA GeForce GTX 1060 6GB")
        self.rule = {"id": "999001", "platform": "Windows", "level": "minimum", "component_type": "CPU",
            "expected_query": "Intel i5+", "reference_models": ["Intel Core i5-2400"],
            "source_url": "https://store.steampowered.com/app/999001/",
            "reviewed_at": "2026-10-31T12:00:00Z", "notes": "Referência inventada para testar o mecanismo."}
        self.curation = self.root / "curation.json"
        self.save_rule()
        self.selection = self.root / "selection.json"
        self.selection.write_text(json.dumps({"schema_version": "steam_games_v1", "tag_vocabulary": ["Fantasia"],
            "games": [{"id": "999001", "tags": ["Fantasia"], "curation_notes": "Fixture inventada."}]}))
        self.raw_dir = self.root / "raw"
        raw = json.dumps({"999001": {"success": True, "data": {
            "steam_appid": 999001, "name": "Jogo fixture de teste", "type": "game", "is_free": True,
            "genres": [{"description": "RPG"}], "platforms": {"windows": True, "mac": False, "linux": False},
            "pc_requirements": {"minimum": self.html}}}}).encode()
        save_snapshot(self.raw_dir / "999001", raw, {"appid": "999001", "title": "Jogo fixture de teste",
            "response_sha256": hashlib.sha256(raw).hexdigest(), "collected_at": "2026-10-31T12:00:00Z",
            "source_url": "https://store.steampowered.com/api/appdetails?appids=999001&cc=br&l=portuguese",
            "country": "br", "language": "portuguese"})

    def save_rule(self):
        self.curation.write_text(json.dumps({"schema_version": FORMAT, "rules": [self.rule]}))

    def block(self):
        return process_requirements(self.html, self.index, self.aliases, catalog_format="manual")

    def apply(self, block=None, **kwargs):
        return apply_curation(block or self.block(), kwargs.get("appid", "999001"),
            kwargs.get("platform", "Windows"), kwargs.get("level", "minimum"),
            read_curation(self.curation, self.index), kwargs.get("catalog", self.index), self.aliases)

    def build(self):
        return build_catalog(self.raw_dir, self.selection, self.csv, self.aliases_path, self.curation)

    def args(self):
        return ["--snapshot-dir", str(self.raw_dir), "--selection", str(self.selection),
            "--catalog", str(self.csv), "--aliases", str(self.aliases_path),
            "--curation", str(self.curation), "--processed-dir", str(self.root / "processed")]

    def test_manual_reference_preserves_original_text_unknown_and_other_fields(self):
        original = self.block()
        result = self.apply(original)
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["text"], original["text"])
        self.assertIsNone(original["requirements"]["cpu_score"])
        self.assertEqual(result["original_requirements"], original["requirements"])
        self.assertEqual(result["original_hardware"]["CPU"], original["hardware"]["CPU"])
        self.assertEqual(result["requirements"]["gpu_score"], original["requirements"]["gpu_score"])
        self.assertEqual(result["curation"][0]["original_query"], "Intel i5+")
        validate_curated_block(result, self.index)

    def test_curated_field_uses_current_database_scores(self):
        current = deepcopy(self.index)
        current[("CPU", normalize_name("Intel Core i5-2400"))]["performance_score"] = 987
        self.assertEqual(self.apply(catalog=current)["requirements"]["cpu_score"], 987)

    def test_unknown_or_unclassified_reference_cannot_use_csv_score(self):
        for missing in (True, False):
            current = deepcopy(self.index)
            key = ("CPU", normalize_name("Intel Core i5-2400"))
            if missing: del current[key]
            else: current[key]["performance_score"] = None
            result = self.apply(catalog=current)
            self.assertIsNone(result["requirements"]["cpu_score"])
            self.assertNotIn("curation", result)
            self.assertEqual(result["status"], "needs_review")

    def test_rule_does_not_cross_game_platform_or_requirement_level(self):
        for other in ({"appid": "999002"}, {"platform": "Linux"}, {"level": "recommended"}):
            self.assertIsNone(self.apply(**other)["requirements"]["cpu_score"])

    def test_changed_source_stays_pending_instead_of_applying_old_estimate(self):
        block = process_requirements(self.html.replace("Intel i5+", "CPU nova desconhecida"),
                                     self.index, self.aliases, catalog_format="manual")
        result = self.apply(block)
        self.assertIsNone(result["requirements"]["cpu_score"])
        self.assertTrue(any("texto mudou" in issue for issue in result["issues"]))

    def test_exact_identification_takes_priority_over_manual_rule(self):
        self.rule["expected_query"] = "Intel Core i5-2500"
        self.save_rule()
        block = process_requirements(self.html.replace("Intel i5+", "Intel Core i5-2500"),
                                     self.index, self.aliases, catalog_format="manual")
        result = self.apply(block)
        self.assertNotIn("curation", result)
        self.assertEqual(result["requirements"], block["requirements"])

    def test_curated_result_cannot_change_score_without_changing_reference(self):
        result = self.apply()
        result["requirements"]["cpu_score"] += 1
        with self.assertRaisesRegex(ValueError, "diverge"):
            validate_curated_block(result, self.index)

    def test_invalid_curation_models_and_metadata_are_rejected(self):
        original = deepcopy(self.rule)
        for key, value in [("reference_models", ["CPU inexistente"]), ("reference_models", []),
                           ("source_url", "javascript:alert(1)"), ("reviewed_at", "2026-10-31"),
                           ("component_type", "RAM"), ("notes", "")]:
            self.rule = {**original, key: value}
            self.save_rule()
            with self.assertRaises(ValueError): read_curation(self.curation, self.index)

    def test_duplicate_field_rules_are_rejected(self):
        self.curation.write_text(json.dumps({"schema_version": FORMAT, "rules": [self.rule, self.rule]}))
        with self.assertRaisesRegex(ValueError, "repetida"):
            read_curation(self.curation, self.index)

    def test_pipeline_and_loader_keep_curation_hash_and_original_requirements(self):
        data = self.build()
        block = data["games"][0]["platforms"]["Windows"]["minimum"]
        self.assertEqual(data["curation_sha256"], hashlib.sha256(self.curation.read_bytes()).hexdigest())
        self.assertIsNone(block["original_requirements"]["cpu_score"])
        self.assertEqual(data["games"][0]["min_cpu_score"], block["requirements"]["cpu_score"])
        self.assertIsNone(data["games"][0]["rec_cpu_score"])
        validate_catalog(data)
        source = self.root / "games.json"
        source.write_text(json.dumps(data))
        args = ["--input", str(source), "--catalog", str(self.csv), "--aliases", str(self.aliases_path),
                "--curation", str(self.curation), "--dry-run"]
        self.assertEqual(load_main(args), 0)
        self.rule["notes"] += " Revisão posterior."
        self.save_rule()
        self.assertEqual(load_main(args), 1)

    def test_offline_batch_processes_without_loading_database(self):
        with patch.object(update_catalog, "load_hardware_main") as hardware:
            self.assertEqual(update_catalog.main(self.args()), 0)
        hardware.assert_not_called()
        self.assertTrue((self.root / "processed/games_manual_v1.json").is_file())
        self.assertEqual((self.root / "processed/hardware_manual_v1.csv").stat().st_mode & 0o444, 0o444)

    def test_load_flag_validates_games_before_loading_hardware_and_games(self):
        events = []
        with patch.object(update_catalog, "load_games_main", side_effect=lambda argv: events.append("validate" if "--dry-run" in argv else "games") or 0), \
             patch.object(update_catalog, "load_hardware_main", side_effect=lambda argv: events.append("hardware") or 0):
            self.assertEqual(update_catalog.main([*self.args(), "--load"]), 0)
        self.assertEqual(events, ["validate", "hardware", "games"])

    def test_partial_collection_is_resumed_and_valid_snapshots_are_reused(self):
        with patch.object(update_catalog, "fetch_main", side_effect=[2, 0]) as fetch, \
             patch.object(update_catalog.time, "sleep"):
            self.assertEqual(update_catalog.main([*self.args(), "--fetch"]), 0)
        self.assertEqual(fetch.call_count, 2)
        self.assertTrue(all("--resume" in call.args[0] for call in fetch.call_args_list))

    def test_failed_collection_stops_before_processing_or_database_writes(self):
        with patch.object(update_catalog, "fetch_main", return_value=2), \
             patch.object(update_catalog.time, "sleep"), \
             patch.object(update_catalog, "load_hardware_main") as hardware:
            self.assertEqual(update_catalog.main([*self.args(), "--fetch", "--load", "--attempts", "1"]), 1)
        hardware.assert_not_called()
        self.assertFalse((self.root / "processed/games_manual_v1.json").exists())

    def test_invalid_snapshot_preserves_outputs_and_does_not_load_database(self):
        output = self.root / "processed"
        output.mkdir()
        for name in ("games_manual_v1.json", "hardware_manual_v1.csv"):
            (output / name).write_text("preserve")
        with (self.raw_dir / "999001/appdetails.json").open("ab") as f: f.write(b"x")
        with patch.object(update_catalog, "load_hardware_main") as hardware:
            self.assertEqual(update_catalog.main([*self.args(), "--load"]), 1)
        hardware.assert_not_called()
        for name in ("games_manual_v1.json", "hardware_manual_v1.csv"):
            self.assertEqual((output / name).read_text(), "preserve")

    def test_hardware_failure_stops_the_game_load(self):
        with patch.object(update_catalog, "load_games_main", return_value=0) as games, \
             patch.object(update_catalog, "load_hardware_main", return_value=1):
            self.assertEqual(update_catalog.main([*self.args(), "--load"]), 1)
        games.assert_called_once()
        self.assertIn("--dry-run", games.call_args.args[0])

    def test_batch_outputs_cannot_overwrite_catalog_or_raw(self):
        for output in (self.csv.parent, self.raw_dir):
            with patch.object(update_catalog, "load_hardware_main") as hardware:
                self.assertEqual(update_catalog.main([*self.args(), "--processed-dir", str(output)]), 1)
            hardware.assert_not_called()

    def test_vram_lists_fullwidth_slash_and_pipe_preserve_each_variant(self):
        self.assertEqual(split_alternatives("1GB ATI Radeon HD 5770, 1GB NVIDIA GeForce GTX 460"),
                         ["1GB ATI Radeon HD 5770", "1GB NVIDIA GeForce GTX 460"])
        self.assertEqual(split_alternatives("AMD Ryzen 3 1200／Intel Core i3-6300 | Intel Core i3-4130"),
                         ["AMD Ryzen 3 1200", "Intel Core i3-6300", "Intel Core i3-4130"])
        self.assertEqual(split_alternatives("GTX 1060 3/6GB"), ["GTX 1060 3/6GB"])

    def test_format_cleanup_keeps_identity_without_approving_generic_frequency(self):
        found = match_hardware("Intel® Core™ i5-2500 @3.3 GHz", "CPU", self.index, self.aliases, catalog_format="manual")
        self.assertEqual(found["name"], "Intel Core i5-2500")
        for query in ("2.0 GHz", "Intel i5+", "Intel Core i3"):
            self.assertEqual(match_hardware(query, "CPU", self.index, self.aliases, catalog_format="manual")["status"], "not_found")
        for query in ("GeForce GTX 1060 3/6GB", "Intel Arc A770"):
            self.assertEqual(match_hardware(query, "GPU", self.index, self.aliases, catalog_format="manual")["status"], "not_found")

    def test_ram_ddr_description_is_accepted_without_reading_gpu_memory(self):
        self.assertEqual(extract_ram_gb("Memory: 4 GB RAM DDR3<br>Graphics: GPU 8GB"), 4)
        self.assertIsNone(extract_ram_gb("Graphics: GPU 8GB DDR5"))
        with self.assertRaises(ValueError): extract_ram_gb("Memory: 4GB or 8GB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
