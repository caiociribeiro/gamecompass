"""Coletas podem reutilizar os mesmos AppIDs após uma revisão editorial."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fetch_games import main
from fetch_steam import save_snapshot


class FetchResumeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.selection = self.root / "selection.json"
        self.lot = self.root / "raw"
        self.selection.write_text(json.dumps({"schema_version": "steam_games_v1", "tag_vocabulary": ["Fantasia"],
            "games": [{"id": "101", "tags": ["Fantasia"], "curation_notes": "Fixture."}]}))
        self.digest = hashlib.sha256(self.selection.read_bytes()).hexdigest()
        raw = json.dumps({"101": {"success": True, "data": {"steam_appid": 101, "name": "Jogo fixture",
            "platforms": {"windows": True, "mac": False, "linux": False}, "pc_requirements": []}}}).encode()
        save_snapshot(self.lot / "101", raw, {"appid": "101", "title": "Jogo fixture",
            "response_sha256": hashlib.sha256(raw).hexdigest(), "collected_at": "2026-10-31T00:00:00Z",
            "source_url": "https://store.steampowered.com/api/appdetails?appids=101&cc=br&l=portuguese",
            "country": "br", "language": "portuguese"})
        self.manifest = self.lot / "collection.json"
        self.manifest.write_text(json.dumps({"selection_sha256": self.digest, "status": "ok", "games": 1, "issues": []}))
        self.args = ["--selection", str(self.selection), "--output-dir", str(self.lot), "--resume"]

    def edit_selection(self):
        selection = json.loads(self.selection.read_text())
        selection["games"][0].update(editorial_genres=["Roguelike"], genre_curation_notes="Revisão editorial fixture.")
        self.selection.write_text(json.dumps(selection))

    def test_legacy_complete_lot_accepts_editorial_changes_without_network_or_raw_changes(self):
        self.edit_selection()
        raw = (self.lot / "101/appdetails.json").read_bytes()
        metadata = (self.lot / "101/metadata.json").read_bytes()
        with patch("fetch_games.fetch_app") as fetch:
            self.assertEqual(main(self.args), 0)
        fetch.assert_not_called()
        current = json.loads(self.manifest.read_text())
        self.assertEqual(current["appids"], ["101"])
        self.assertEqual(current["collection_selection_sha256"], self.digest)
        self.assertEqual(current["selection_sha256"], hashlib.sha256(self.selection.read_bytes()).hexdigest())
        self.assertEqual((self.lot / "101/appdetails.json").read_bytes(), raw)
        self.assertEqual((self.lot / "101/metadata.json").read_bytes(), metadata)

    def test_partial_manifest_with_explicit_ids_accepts_editorial_changes(self):
        self.manifest.write_text(json.dumps({"selection_sha256": self.digest, "status": "partial", "appids": ["101"]}))
        self.edit_selection()
        with patch("fetch_games.fetch_app") as fetch:
            self.assertEqual(main(self.args), 0)
        fetch.assert_not_called()

    def test_changed_appids_preserve_manifest_and_do_not_make_requests(self):
        selected = json.loads(self.selection.read_text())
        selected["games"][0]["id"] = "202"
        self.selection.write_text(json.dumps(selected))
        before = self.manifest.read_bytes()
        with patch("fetch_games.fetch_app") as fetch:
            self.assertEqual(main(self.args), 1)
        fetch.assert_not_called()
        self.assertEqual(self.manifest.read_bytes(), before)
        self.assertFalse((self.lot / "202").exists())

    def test_snapshot_from_another_language_is_not_reused(self):
        path = self.lot / "101/metadata.json"
        metadata = json.loads(path.read_text())
        metadata["language"] = "english"
        path.write_text(json.dumps(metadata))
        before = self.manifest.read_bytes()
        with patch("fetch_games.fetch_app") as fetch:
            self.assertEqual(main(self.args), 1)
        fetch.assert_not_called()
        self.assertEqual(self.manifest.read_bytes(), before)

    def test_corrupt_snapshot_is_not_silently_replaced(self):
        with (self.lot / "101/appdetails.json").open("ab") as f: f.write(b"x")
        with patch("fetch_games.fetch_app") as fetch:
            self.assertEqual(main(self.args), 1)
        fetch.assert_not_called()

    def test_invalid_manifest_hash_does_not_become_collection_provenance(self):
        self.manifest.write_text(json.dumps({"selection_sha256": "invalid", "status": "ok", "games": 1}))
        with patch("fetch_games.fetch_app") as fetch:
            self.assertEqual(main(self.args), 1)
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
