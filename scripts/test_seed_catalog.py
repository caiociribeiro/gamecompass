"""Carga automática do catálogo (serviço catalog do Compose), sem Neo4j: o banco é simulado."""
import json
import unittest
from unittest.mock import patch

import seed_catalog

DATA = json.loads(seed_catalog.GAMES.read_text(encoding="utf-8-sig"))
IDS = [game["id"] for game in DATA["games"]]
HASHES = [DATA.get(key) for key in seed_catalog.HASHES]


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def data(self):
        return self.rows

    def single(self):
        return self.rows[0]


class FakeDatabase:
    """Responde às consultas do seed_catalog a partir de listas simples."""

    def __init__(self, games, parts, stale=0, interacted_stale=0):
        self.games, self.parts, self.stale, self.interacted_stale = games, parts, stale, interacted_stale
        self.queries = []

    def run(self, query, **params):
        self.queries.append(query)
        if "RETURN g.id AS id" in query:
            return FakeResult(self.games)
        if "labels(h)[0] AS kind" in query:
            return FakeResult(self.parts)
        if "DETACH DELETE" in query:
            removed, self.stale = self.stale - self.interacted_stale, self.interacted_stale
            return FakeResult([{"n": removed}])
        if "NOT g.id IN $ids RETURN count(g)" in query:
            return FakeResult([{"n": self.stale}])
        raise AssertionError("Consulta inesperada: " + query)

    def session(self, **kwargs):
        return self

    def verify_connectivity(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def complete_parts():
    kinds = {"CPU": "CPU", "GPU": "GPU"}
    return [{"kind": kinds[row["component_type"]], "name": row["name"], "score": row["performance_score"]}
            for row in DATA["hardware"]]


def run(database):
    with patch.dict("os.environ", {"NEO4J_PASSWORD": "teste"}), \
            patch.object(seed_catalog.GraphDatabase, "driver", return_value=database), \
            patch.object(seed_catalog, "load_hardware_main", return_value=0) as hardware, \
            patch.object(seed_catalog, "load_games_main", return_value=0) as games, \
            patch("builtins.print") as printed:
        code = seed_catalog.main([])
    report = json.loads(printed.call_args.args[0]) if printed.call_args else None
    return code, report, hardware, games


class SeedCatalogTests(unittest.TestCase):
    def test_versioned_file_has_the_whole_selection(self):
        selection = json.loads((seed_catalog.ROOT / "data/catalog/games.json").read_text(encoding="utf-8"))
        self.assertEqual(set(IDS), {str(item["id"]) for item in selection["games"]})
        self.assertEqual(len(IDS), 120)

    def test_versioned_file_matches_the_versioned_hardware_aliases_and_curation(self):
        # Mudou o CSV, os aliases ou a curadoria? Rode update_catalog.py e versione o JSON novo.
        import load_games
        with patch("builtins.print"):
            self.assertEqual(load_games.main(["--dry-run"]), 0)

    def test_up_to_date_database_is_left_alone(self):
        database = FakeDatabase([{"id": game_id, "hashes": HASHES} for game_id in IDS], complete_parts())
        code, report, hardware, games = run(database)
        self.assertEqual(code, 0)
        self.assertEqual(report["action"], "catálogo já estava em dia")
        hardware.assert_not_called()
        games.assert_not_called()
        self.assertFalse(any("DELETE" in query for query in database.queries))

    def test_empty_database_receives_hardware_and_games(self):
        code, report, hardware, games = run(FakeDatabase([], []))
        self.assertEqual(code, 0)
        self.assertEqual(report["action"], "catálogo carregado")
        hardware.assert_called_once()
        self.assertEqual(hardware.call_args.args[0][:2], ["--format", "manual"])
        games.assert_called_once_with(["--input", str(seed_catalog.GAMES)])

    def test_changed_hash_or_score_reloads(self):
        old = [{"id": game_id, "hashes": ["antigo", *HASHES[1:]]} for game_id in IDS]
        self.assertEqual(run(FakeDatabase(old, complete_parts()))[1]["action"], "catálogo carregado")
        parts = complete_parts()
        parts[0] = {**parts[0], "score": -1}
        current = [{"id": game_id, "hashes": HASHES} for game_id in IDS]
        self.assertEqual(run(FakeDatabase(current, parts))[1]["action"], "catálogo carregado")

    def test_games_out_of_the_selection_leave_unless_someone_interacted(self):
        database = FakeDatabase([{"id": game_id, "hashes": HASHES} for game_id in IDS], complete_parts(),
                                stale=4, interacted_stale=1)
        code, report, _, _ = run(database)
        self.assertEqual(code, 0)
        self.assertEqual((report["removed_stale_games"], report["kept_stale_games_with_interactions"]), (3, 1))
        delete = next(query for query in database.queries if "DETACH DELETE" in query)
        self.assertIn("NOT (g)<-[:INTERACTED]-()", delete)

    def test_failed_load_stops_the_api_from_starting(self):
        with patch.dict("os.environ", {"NEO4J_PASSWORD": "teste"}), \
                patch.object(seed_catalog.GraphDatabase, "driver", return_value=FakeDatabase([], [])), \
                patch.object(seed_catalog, "load_hardware_main", return_value=1), \
                patch("sys.stderr"):
            self.assertEqual(seed_catalog.main([]), 1)


if __name__ == "__main__":
    unittest.main()
