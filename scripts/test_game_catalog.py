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
from review_game_requirements import main as review_main, review_catalog


class GameCatalogTests(unittest.TestCase):
    def test_editorial_genres_extend_steam_genres_with_separate_provenance(self):
        selected = json.loads(self.selection.read_text())
        selected["games"][0].update(editorial_genres=["Roguelike"], genre_curation_notes="Classificação de teste.")
        self.selection.write_text(json.dumps(selected))
        data = self.build()
        game = data["games"][0]
        self.assertEqual(game["genres"], ["RPG", "Roguelike"])
        self.assertEqual(game["genre_source"]["steam"], ["RPG"])
        self.assertEqual(game["genre_source"]["editorial"], ["Roguelike"])
        self.assertIn("Roguelike", prepare_payload(data)[0]["genres"])

    def test_invalid_or_unexplained_editorial_genres_are_rejected(self):
        original = json.loads(self.selection.read_text())
        for genres, note in [(["Categoria desconhecida"], "nota"), (["Puzzle", "Puzzle"], "nota"),
                             (["Puzzle"], ""), ("Puzzle", "nota"), ([True], "nota")]:
            selected = deepcopy(original)
            selected["games"][0].update(editorial_genres=genres, genre_curation_notes=note)
            self.selection.write_text(json.dumps(selected))
            with self.assertRaises(ValueError): read_selection(self.selection)

    def test_processed_genres_cannot_disagree_with_their_sources(self):
        data = self.build()
        data["games"][0]["genre_source"]["editorial"] = ["Puzzle"]
        with self.assertRaisesRegex(ValueError, "Origem"):
            prepare_payload(data)

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

    def test_portuguese_os_and_fractional_ram_survive_the_full_pipeline(self):
        self.raw_data["pc_requirements"]["minimum"] = (
            self.raw_data["pc_requirements"]["minimum"]
            .replace("OS: Windows 10", "Sistema Operativo *: Windows 11")
            .replace("8 GB RAM", "2.5 GB RAM")
        )
        self.save()
        game = self.build()["games"][0]
        self.assertEqual(game["platforms"]["Windows"]["minimum"]["os_text"], "Windows 11")
        self.assertEqual(game["min_ram_gb"], 3)
        self.assertFalse(any("SO ausente" in issue for issue in game["issues"]))

    def test_new_spelling_aliases_keep_the_canonical_models_and_scores(self):
        self.raw_data["pc_requirements"]["minimum"] = (
            "Sistema Operativo: Windows 10<br>Processor: Intel Core i7 8700K"
            "<br>Memory: 8 GB RAM<br>Graphics: Intel Arc A580 (8GB+ of VRAM)"
        )
        self.save()
        minimum = self.build()["games"][0]["platforms"]["Windows"]["minimum"]
        self.assertEqual(minimum["status"], "resolved")
        self.assertEqual(minimum["hardware"]["CPU"]["alternatives"][0]["name"], "Intel Core i7-8700K")
        self.assertEqual(minimum["hardware"]["GPU"]["alternatives"][0]["name"], "Intel Arc A580 8GB")
        self.assertEqual(minimum["requirements"]["cpu_score"], 100)
        self.assertEqual(minimum["requirements"]["gpu_score"], 300)

    def test_unidentified_model_keeps_other_results(self):
        self.raw_data["pc_requirements"]["minimum"] = self.raw_data["pc_requirements"]["minimum"].replace("AMD Ryzen 5 3600", "CPU fixture desconhecida")
        self.save()
        game = self.build()["games"][0]
        self.assertIsNone(game["min_cpu_score"])
        self.assertEqual(game["min_gpu_score"], 550)

    def test_known_or_alternative_survives_without_fabricating_unknown_vram(self):
        self.raw_data["pc_requirements"]["recommended"] = (
            "OS: Windows 10<br>Processor: Intel Core i7-8700<br>Memory: 16 GB RAM"
            "<br>Graphics: NVIDIA GeForce 1080 Ti or AMD Radeon RX 5700 XT or INTEL Arc A770"
        )
        self.save()
        data = self.build()
        block = data["games"][0]["platforms"]["Windows"]["recommended"]
        self.assertIsNone(block["requirements"]["gpu_score"])
        alternatives = block["hardware"]["GPU"]["alternatives"]
        self.assertEqual([a["performance_score"] for a in alternatives], [300, 300, None])
        self.assertIsNone(alternatives[-1]["name"])
        report = review_catalog(data)
        self.assertEqual(report["summary"]["recommended"]["has_known_alternative"], 1)

    def test_boilerplate_only_recommended_is_absent_instead_of_an_empty_checklist(self):
        self.raw_data["pc_requirements"]["recommended"] = (
            "<strong>Recomendados:</strong><br>Requer um sistema operativo e processador de 64 bits"
        )
        self.save()
        data = self.build()
        self.assertIsNone(data["games"][0]["platforms"]["Windows"]["recommended"])
        self.assertEqual(review_catalog(data)["summary"]["recommended"]["not_provided"], 1)

    def test_review_distinguishes_generic_frequency_from_a_classified_model(self):
        self.raw_data["pc_requirements"]["minimum"] = (
            "OS: Windows 10<br>Processor: 2.0 GHz<br>Memory: 4 GB RAM<br>Graphics: Intel HD 4000"
        )
        self.raw_data["pc_requirements"]["recommended"] = ""
        self.save()
        report = review_catalog(self.build())
        self.assertEqual(report["summary"]["requiring_curation"], 1)
        self.assertEqual(report["pending_queries"][0]["query"], "2.0 GHz")

    def test_review_cli_keeps_the_input_hash_and_level_counts(self):
        source = self.root / "processed.json"
        source.write_text(json.dumps(self.build()), encoding="utf-8")
        output = self.root / "review.json"
        self.assertEqual(review_main(["--input", str(source), "--output", str(output)]), 0)
        report = json.loads(output.read_text())
        self.assertEqual(report["source"]["input_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(report["summary"]["minimum"]["resolved"], 1)
        self.assertEqual(report["summary"]["with_comparison_basis"], 1)

    def test_review_cli_preserves_previous_output_when_input_is_invalid(self):
        source = self.root / "invalid.json"
        source.write_text('{"schema_version":"invalid"}')
        output = self.root / "previous-review.json"
        output.write_text('{"previous":"preserve"}')
        original = output.read_bytes()
        self.assertEqual(review_main(["--input", str(source), "--output", str(output)]), 1)
        self.assertEqual(output.read_bytes(), original)

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
