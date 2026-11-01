"""Regressões offline da ampliação: coletas reutilizadas e fichas antigas.

As respostas geradas aqui são fixtures, sem representar uma coleta Steam real.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from extract_steam_requirements import extract_os_text, extract_snapshot, separate_legacy_levels
from fetch_games import main as fetch_main
from fetch_steam import save_snapshot
from game_catalog import ROOT, read_selection
from hardware_catalog import read_catalog
from hardware_matcher import match_hardware, normalize_name, read_aliases
from process_requirements import process_requirements
from regex_parser import clean_html, extract_hardware_text, extract_ram_gb
from requirements_curation import apply_curation, read_curation
from reuse_snapshots import reuse_snapshots
import update_catalog


class SnapshotReuseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source, self.target = self.root / "old", self.root / "new"
        self.selection = self.root / "selection.json"
        self.selection.write_text(json.dumps({"schema_version": "steam_games_v1", "tag_vocabulary": ["Fantasia"],
            "games": [{"id": appid, "tags": ["Fantasia"], "curation_notes": "Fixture inventada."}
                      for appid in ("101", "202")]}))
        self.save(self.source, "101")
        (self.source / "collection.json").write_text('{"fixture": true}')

    def save(self, root, appid, *, language="portuguese"):
        raw = json.dumps({appid: {"success": True, "data": {"steam_appid": int(appid),
            "name": f"Fixture {appid}", "type": "game", "is_free": True,
            "platforms": {"windows": True, "mac": False, "linux": False}, "genres": [{"description": "Indie"}],
            "pc_requirements": {"minimum": "OS: Windows 10<br>Memory: 4 GB RAM"}}}}).encode()
        metadata = {"appid": appid, "title": f"Fixture {appid}", "response_sha256": hashlib.sha256(raw).hexdigest(),
            "collected_at": "2026-10-01T10:00:00Z", "source_url": "https://store.steampowered.com/api/appdetails?appids=" + appid,
            "country": "br", "language": language}
        save_snapshot(root / appid, raw, metadata)
        return raw, metadata

    def reuse(self):
        return reuse_snapshots(self.source, self.target, self.selection)

    def test_copy_keeps_original_bytes_dates_and_records_provenance(self):
        before = {name: (self.source / "101" / name).read_bytes() for name in ("appdetails.json", "metadata.json")}
        self.assertEqual(self.reuse(), 1)
        for name, raw in before.items():
            self.assertEqual((self.target / "101" / name).read_bytes(), raw)
            self.assertEqual((self.source / "101" / name).read_bytes(), raw)
        manifest = json.loads((self.target / "collection.json").read_text())
        self.assertEqual(manifest["appids"], ["101", "202"])
        self.assertEqual(manifest["reuse_sources"][0]["appids"], ["101"])
        self.assertEqual(manifest["reuse_sources"][0]["source_manifest_sha256"],
                         hashlib.sha256((self.source / "collection.json").read_bytes()).hexdigest())

    def test_retry_does_not_overwrite_or_duplicate_history(self):
        self.reuse()
        manifest = (self.target / "collection.json").read_bytes()
        self.assertEqual(self.reuse(), 0)
        self.assertEqual((self.target / "collection.json").read_bytes(), manifest)

    def test_fetch_requests_only_missing_games_and_keeps_reuse_provenance(self):
        self.reuse()
        raw, metadata = self.save(self.root / "fixture", "202")
        with patch("fetch_games.fetch_app", return_value=(raw, metadata)) as fetch, patch("fetch_games.time.sleep"):
            self.assertEqual(fetch_main(["--selection", str(self.selection), "--output-dir", str(self.target), "--resume"]), 0)
        fetch.assert_called_once_with("202", language="portuguese")
        manifest = json.loads((self.target / "collection.json").read_text())
        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["reuse_sources"][0]["appids"], ["101"])
        self.assertEqual(extract_snapshot(self.target / "202")["id"], "202")

    def test_preflight_corruption_publishes_nothing(self):
        self.save(self.source, "202")
        (self.source / "202/appdetails.json").write_bytes(b"corrupted fixture")
        with self.assertRaisesRegex(ValueError, "Hash divergente"):
            self.reuse()
        self.assertFalse(self.target.exists())

    def test_existing_corrupt_destination_is_not_replaced(self):
        self.reuse()
        (self.target / "101/appdetails.json").write_bytes(b"bad fixture")
        with self.assertRaisesRegex(ValueError, "Hash divergente"):
            self.reuse()
        self.assertEqual((self.target / "101/appdetails.json").read_bytes(), b"bad fixture")

    def test_region_language_and_appid_must_match(self):
        for key, value in (("language", "english"), ("country", "us"), ("appid", "202")):
            path = self.source / "101/metadata.json"
            original = path.read_bytes()
            data = json.loads(original)
            data[key] = value
            path.write_text(json.dumps(data))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.reuse()
            self.assertFalse(self.target.exists())
            path.write_bytes(original)

    def test_overlapping_roots_are_rejected(self):
        for target in (self.source, self.source / "nested", self.root):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "sobreposição"):
                reuse_snapshots(self.source, target, self.selection)

    def test_destination_without_manifest_is_preserved(self):
        self.target.mkdir()
        marker = self.target / "keep.txt"
        marker.write_text("keep")
        with self.assertRaisesRegex(ValueError, "manifesto"):
            self.reuse()
        self.assertEqual(marker.read_text(), "keep")

    def test_incompatible_selection_cannot_change_existing_lot(self):
        self.reuse()
        manifest = (self.target / "collection.json").read_bytes()
        data = json.loads(self.selection.read_text())
        data["games"].pop()
        self.selection.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "AppIDs"):
            self.reuse()
        self.assertEqual((self.target / "collection.json").read_bytes(), manifest)

    def test_updater_requires_fetch_and_protects_previous_snapshot_directory(self):
        base = ["--selection", str(self.selection), "--snapshot-dir", str(self.target),
                "--reuse-snapshot-dir", str(self.source), "--processed-dir", str(self.root / "processed")]
        with patch.object(update_catalog, "fetch_main") as fetch, patch.object(update_catalog, "load_hardware_main") as load:
            self.assertEqual(update_catalog.main(base), 1)
            self.assertEqual(update_catalog.main([*base, "--fetch", "--load", "--processed-dir", str(self.source)]), 1)
        fetch.assert_not_called()
        load.assert_not_called()
        self.assertFalse(self.target.exists())

    def test_incomplete_new_lot_keeps_old_raw_and_does_not_write_processed_or_database(self):
        before = (self.source / "101/appdetails.json").read_bytes()
        args = ["--selection", str(self.selection), "--snapshot-dir", str(self.target),
                "--reuse-snapshot-dir", str(self.source), "--processed-dir", str(self.root / "processed"),
                "--fetch", "--load", "--attempts", "1"]
        with patch.object(update_catalog, "fetch_main", return_value=2), \
             patch.object(update_catalog, "load_hardware_main") as hardware, \
             patch.object(update_catalog, "load_games_main") as games:
            self.assertEqual(update_catalog.main(args), 1)
        hardware.assert_not_called()
        games.assert_not_called()
        self.assertEqual((self.source / "101/appdetails.json").read_bytes(), before)
        self.assertEqual((self.target / "101/appdetails.json").read_bytes(), before)
        self.assertFalse((self.root / "processed").exists())


class LegacyAndHardwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = read_catalog(ROOT / "data/catalog/hardware_manual_v1.csv", catalog_format="manual")
        cls.index = {(r["component_type"], normalize_name(r["name"])): r for r in rows}
        cls.aliases = read_aliases(ROOT / "data/catalog/hardware_aliases.json", cls.index)
        cls.rules = read_curation(ROOT / "data/catalog/requirements_curation.json", cls.index)

    def test_explicit_legacy_levels_keep_distinct_ram_cpu_gpu_and_os(self):
        # Fixture semelhante ao formato antigo, com quantidades diferentes para
        # demonstrar que os recomendados não são copiados dos mínimos.
        raw = {"minimum": "<b>Mínimo:</b> Processador a 1.7 GHz, 512MB de RAM, placa gráfica DirectX 8.1, Windows 7/Vista/XP"
               "<br><b>Recomendado:</b> Processador Pentium 4, 2GB de RAM, placa gráfica DirectX 9, Windows 10"}
        before = deepcopy(raw)
        levels = separate_legacy_levels(raw)
        self.assertEqual(raw, before)
        self.assertEqual(extract_ram_gb(levels["minimum"]), 1)
        self.assertEqual(extract_ram_gb(levels["recommended"]), 2)
        self.assertEqual(extract_hardware_text(levels["minimum"], "CPU"), "Processador a 1.7 GHz")
        self.assertEqual(extract_hardware_text(levels["recommended"], "GPU"), "placa gráfica DirectX 9")
        self.assertEqual(extract_os_text(clean_html(levels["recommended"])), "Windows 10")

    def test_two_unsplit_levels_are_not_silently_used_as_minimum(self):
        with self.assertRaises(ValueError):
            extract_ram_gb("Minimum: Processor 2 GHz, 1 GB RAM<br>Recommended: Processor 3 GHz, 4 GB RAM")

    def test_existing_recommended_field_is_never_overwritten(self):
        raw = {"minimum": "Minimum: Processor 2 GHz, 1 GB RAM<br>Recommended: Processor 3 GHz, 4 GB RAM",
               "recommended": "Memory: 8 GB RAM"}
        self.assertEqual(separate_legacy_levels(raw), raw)

    def test_storage_and_graphics_memory_do_not_fill_missing_ram(self):
        for text in ("Graphics: GTX 750 1GB<br>Storage: 8 GB", "Minimum: Processor 2 GHz, graphics card 4 GB, Windows 10",
                     "Minimum: Storage 8 GB, 4 GB RAM, Windows 10"):
            with self.subTest(text=text):
                self.assertIsNone(extract_ram_gb(text))

    def test_memory_variants_remain_distinct(self):
        def find(name):
            return match_hardware(name, "GPU", self.index, self.aliases, catalog_format="manual")
        a, b = find("NVIDIA GeForce RTX 3050 6GB"), find("NVIDIA GeForce RTX 3050 8GB")
        self.assertEqual((a["performance_score"], b["performance_score"]), (150, 200))
        self.assertEqual(find("NVIDIA GeForce RTX 3050 4GB")["status"], "not_found")
        self.assertNotEqual(find("NVIDIA GeForce GT 1030 DDR4 2GB")["performance_score"],
                            find("NVIDIA GeForce GT 1030 GDDR5 2GB")["performance_score"])

    def test_missing_ram_remains_pending_after_hardware_curation(self):
        html = "OS: Windows 10<br>Processor: SSE2 instruction set support<br>Graphics: Graphics card with DX10 (shader model 4.0) capabilities."
        original = process_requirements(html, self.index, self.aliases, catalog_format="manual")
        result = apply_curation(original, "1135690", "Windows", "minimum", self.rules, self.index, self.aliases)
        self.assertIsNone(result["requirements"]["ram_gb"])
        self.assertIsNotNone(result["requirements"]["cpu_score"])
        self.assertEqual(result["status"], "needs_review")

    def test_missing_gpu_is_not_inferred_from_directx_or_curated_cpu(self):
        html = "OS: Windows 10<br>Processor: 3.0 GHz processor<br>Memory: 4 GB RAM<br>DirectX: Version 9.0c"
        original = process_requirements(html, self.index, self.aliases, catalog_format="manual")
        result = apply_curation(original, "253230", "Windows", "minimum", self.rules, self.index, self.aliases)
        self.assertIsNone(result["requirements"]["gpu_score"])
        self.assertEqual(result["status"], "needs_review")

    def test_new_legacy_rules_do_not_apply_to_changed_or_other_game_text(self):
        html = "OS: Windows 10<br>Processor: Quad Core 9 GHz<br>Memory: 4 GB RAM<br>Graphics: NVIDIA GTX 750"
        original = process_requirements(html, self.index, self.aliases, catalog_format="manual")
        for appid in ("418530", "999999"):
            result = apply_curation(original, appid, "Windows", "minimum", self.rules, self.index, self.aliases)
            self.assertIsNone(result["requirements"]["cpu_score"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
