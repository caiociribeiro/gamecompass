"""Fixtures identificadas para validação, integridade e preservação de saídas."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from fetch_steam import save_snapshot
from game_catalog import ROOT, build_catalog, read_selection, validate_catalog
from load_games import prepare_payload, main as load_main
from process_games import main as process_main


class GameCatalogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.selection = self.root / "selection.json"
        self.selection.write_text(json.dumps({"schema_version": "steam_games_v1", "tag_vocabulary": ["Fantasia"],
            "games": [{"id": "101", "tags": ["Fantasia"], "curation_notes": "Fixture editorial inventada."}]}))
        self.catalog = ROOT / "data/catalog/hardware_manual_v1.csv"
        self.aliases = ROOT / "data/catalog/hardware_aliases.json"
        self.snapshots = self.root / "raw"
        self.raw_data = {"steam_appid": 101, "name": "Jogo fixture 101", "type": "game", "is_free": False,
            "price_overview": {"currency": "BRL", "final": 1099, "final_formatted": "R$ 10,99"},
            "genres": [{"description": "RPG"}, {"description": "RPG"}],
            "platforms": {"windows": True, "mac": False, "linux": False},
            "pc_requirements": {level: "OS: Windows 10<br>Processor: AMD Ryzen 5 3600<br>Memory: 8 GB RAM<br>Graphics: NVIDIA GeForce RTX 5070 12GB" for level in ("minimum", "recommended")}}
        self.save()

    def save(self, data=None):
        target = self.snapshots / "101"
        if target.exists():
            import shutil
            shutil.rmtree(target)
        raw = json.dumps({"101": {"success": True, "data": data or self.raw_data}}).encode()
        save_snapshot(target, raw, {"appid": "101", "title": (data or self.raw_data)["name"],
            "response_sha256": hashlib.sha256(raw).hexdigest(), "collected_at": "2026-10-30T00:00:00+00:00",
            "source_url": "https://store.steampowered.com/api/appdetails?appids=101&cc=br&l=portuguese",
            "country": "br", "language": "portuguese"})

    def build(self):
        return build_catalog(self.snapshots, self.selection, self.catalog, self.aliases)

    def test_build_preserves_identity_tags_price_and_separate_platforms(self):
        game = self.build()["games"][0]
        self.assertEqual(game["id"], "101")
        self.assertEqual(game["genres"], ["RPG"])
        self.assertEqual(game["themes"], ["Fantasia"])
        self.assertEqual(game["price"], 10.99)
        self.assertEqual(game["min_ram_gb"], 8)
        self.assertEqual(game["min_cpu_score"], 100)
        self.assertEqual(game["min_gpu_score"], 550)
        self.assertIsNone(game["platforms"]["Linux"]["minimum"])
        self.assertFalse(game["platforms"]["Linux"]["native_support"])

    def test_missing_requirements_stay_null(self):
        self.raw_data["pc_requirements"] = {}
        self.save()
        game = self.build()["games"][0]
        self.assertIsNone(game["min_cpu_score"])
        self.assertIsNone(game["rec_ram_gb"])
        self.assertEqual(game["status"], "needs_review")

    def test_unidentified_model_keeps_other_results(self):
        self.raw_data["pc_requirements"]["minimum"] = self.raw_data["pc_requirements"]["minimum"].replace("AMD Ryzen 5 3600", "CPU fixture desconhecida")
        self.save()
        game = self.build()["games"][0]
        self.assertIsNone(game["min_cpu_score"])
        self.assertEqual(game["min_gpu_score"], 550)

    def test_missing_price_is_not_free(self):
        del self.raw_data["price_overview"]
        self.save()
        self.assertIsNone(self.build()["games"][0]["price"])

    def test_free_game_has_numeric_zero_price(self):
        self.raw_data["is_free"] = True
        self.save()
        self.assertEqual(self.build()["games"][0]["price"], 0.0)

    def test_tampered_snapshot_is_rejected(self):
        with (self.snapshots / "101/appdetails.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ValueError, "Hash"):
            self.build()

    def test_dlc_is_not_loaded_as_base_game(self):
        self.raw_data["type"] = "dlc"
        self.save()
        with self.assertRaisesRegex(ValueError, "jogo base"):
            self.build()

    def test_unreviewed_tags_and_duplicate_ids_are_rejected(self):
        source = json.loads(self.selection.read_text())
        for change in ("tag", "duplicate"):
            value = deepcopy(source)
            if change == "tag": value["games"][0]["tags"] = ["Tag desconhecida"]
            else: value["games"].append(value["games"][0])
            self.selection.write_text(json.dumps(value))
            with self.assertRaises(ValueError): read_selection(self.selection)

    def test_invalid_scores_and_mixed_versions_are_rejected(self):
        original = self.build()
        for value in (-1, 0, True, 1.5, 2**63):
            data = deepcopy(original)
            data["games"][0]["min_cpu_score"] = value
            with self.assertRaises(ValueError): validate_catalog(data)
        data = deepcopy(original)
        data["score_version"] = "passmark"
        with self.assertRaises(ValueError): validate_catalog(data)

    def test_nested_and_flat_requirements_cannot_disagree(self):
        data = self.build()
        data["games"][0]["platforms"]["Windows"]["minimum"]["requirements"]["cpu_score"] = 999
        with self.assertRaisesRegex(ValueError, "divergem"):
            prepare_payload(data)

    def test_payload_uses_only_contract_labels_and_keeps_audit_json(self):
        rows = prepare_payload(self.build())
        self.assertEqual(rows[0]["tags"], ["Fantasia"])
        self.assertEqual(rows[0]["properties"]["min_cpu_score"], 100)
        self.assertEqual(json.loads(rows[0]["properties"]["catalog_json"])["id"], "101")
        self.assertNotIn("passmark_score", rows[0]["properties"])

    def test_processing_failure_keeps_previous_output(self):
        output = self.root / "processed.json"
        output.write_text("previous")
        with (self.snapshots / "101/appdetails.json").open("ab") as stream: stream.write(b"x")
        self.assertEqual(process_main(["--snapshot-dir", str(self.snapshots), "--selection", str(self.selection), "--output", str(output)]), 1)
        self.assertEqual(output.read_text(), "previous")

    def test_processing_cannot_overwrite_raw_or_selection(self):
        for output in (self.selection, self.snapshots / "101/appdetails.json"):
            before = output.read_bytes()
            self.assertEqual(process_main(["--snapshot-dir", str(self.snapshots), "--selection", str(self.selection), "--output", str(output)]), 1)
            self.assertEqual(output.read_bytes(), before)

    def test_load_dry_run_needs_no_database_and_rejects_stale_catalog(self):
        output = self.root / "processed.json"
        output.write_text(json.dumps(self.build()))
        self.assertEqual(load_main(["--input", str(output), "--dry-run"]), 0)
        data = json.loads(output.read_text())
        data["catalog_sha256"] = "0" * 64
        output.write_text(json.dumps(data))
        self.assertEqual(load_main(["--input", str(output), "--dry-run"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
