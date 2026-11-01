"""Integração real: python scripts/test_game_loader.py --integration.

Usa NEO4J_*; cria identificadores exclusivos e remove somente suas fixtures.
Não limpa o catálogo nem remove constraints existentes.
"""

from copy import deepcopy
import os
import sys
import unittest
import uuid

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from game_catalog import FIELDS, FORMAT, OWNER, hardware_digest
from load_games import create_constraints, prepare_payload, write_games


@unittest.skipUnless("--integration" in sys.argv, "Use --integration com Neo4j ativo.")
class GameLoaderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        password = os.getenv("NEO4J_PASSWORD")
        if not password:
            raise ValueError("Defina NEO4J_PASSWORD para a integração.")
        cls.driver = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), password), max_transaction_retry_time=1)
        cls.database = os.getenv("NEO4J_DATABASE", "neo4j")
        try:
            cls.driver.verify_connectivity()
            with cls.driver.session(database=cls.database) as session:
                session.execute_write(create_constraints)
        except Exception:
            cls.driver.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()

    def query(self, cypher, **params):
        with self.driver.session(database=self.database) as session:
            return session.run(cypher, **params).data()

    def setUp(self):
        self.token = "__gc_game_test_" + uuid.uuid4().hex
        self.names = [self.token + suffix for suffix in ("_CPU", "_GPU", "_genre1", "_genre2", "_genre3", "_tag1", "_tag2", "_tag3", "_foreign")]
        # Reserva AppIDs ainda ausentes antes de registrar a limpeza.
        while True:
            start = 9_000_000_000 + uuid.uuid4().int % 900_000_000
            self.ids = [str(start + i) for i in range(4)]
            if not self.query("MATCH (g:Game) WHERE g.id IN $ids RETURN g.id", ids=self.ids):
                break
        self.addCleanup(self.cleanup)
        self.query("UNWIND $ids AS id CREATE (:Game {id:id, test_run:$token})", ids=self.ids, token=self.token)
        hardware = [{"component_type": kind, "name": self.names[i], "performance_score": score, "score_version": "manual_v1"}
            for i, (kind, score) in enumerate((("CPU", 100), ("GPU", 200)))]
        for row in hardware:
            kind = row["component_type"]  # Constante fechada CPU/GPU, nunca entrada livre.
            self.query(f"CREATE (h:{kind}) SET h = $props", props={key: value for key, value in row.items() if key != "component_type"})
        games = []
        for i, appid in enumerate(self.ids):
            game = {"id": appid, "title": f"Fixture {i} {self.token}", "price": 1.0,
                **{field: None for field in FIELDS}, "genres": [self.names[2 + (0 if i < 2 else i - 1)]],
                "themes": [self.names[5 + (i % 3)]], "themes_status": "classified",
                "platforms": {name: {"native_support": True, "minimum": None, "recommended": None} for name in ("Windows", "macOS", "Linux")},
                "source": {"source_url": "https://store.steampowered.com/api/appdetails", "collected_at": "2026-10-30T00:00:00Z", "response_sha256": "a" * 64},
                "issues": ["Fixture fictícia sem requisitos."], "status": "needs_review"}
            games.append(game)
        games[2]["themes"] = games[0]["themes"][:]
        games[3]["themes"] = [self.names[7]]
        self.data = {"schema_version": FORMAT, "score_version": "manual_v1", "currency": "BRL", "hardware": hardware,
            "hardware_sha256": hardware_digest(hardware), "games": games,
            **{key: "b" * 64 for key in ("catalog_sha256", "aliases_sha256", "selection_sha256")}}

    def cleanup(self):
        self.query("MATCH (g:Game {test_run:$token}) DETACH DELETE g", token=self.token)
        self.query("MATCH (n) WHERE (n:CPU OR n:GPU OR n:Genre OR n:Tag) AND n.name IN $names DETACH DELETE n", names=self.names)

    def load(self, data=None, rows=None):
        data = self.data if data is None else data
        with self.driver.session(database=self.database) as session:
            return session.execute_write(write_games, data, prepare_payload(data) if rows is None else rows)

    def counts(self):
        return self.query("MATCH (g:Game) WHERE g.id IN $ids OPTIONAL MATCH (g)-[r]->() RETURN count(DISTINCT g) AS games, count(r) AS edges", ids=self.ids)[0]

    def test_repeated_load_keeps_node_and_edge_counts(self):
        self.load()
        before = self.counts()
        self.load()
        self.assertEqual(before, {"games": 4, "edges": 8})
        self.assertEqual(self.counts(), before)

    def test_tag_update_preserves_foreign_edges_and_omitted_games(self):
        self.load()
        self.query("MATCH (g:Game {id:$id}) MERGE (t:Tag {name:$tag}) CREATE (g)-[:HAS_TAG {source:'external'}]->(t)", id=self.ids[0], tag=self.names[8])
        changed = deepcopy(self.data)
        changed["games"] = changed["games"][:1]
        changed["games"][0]["themes"] = [self.names[6]]
        self.load(changed)
        rows = self.query("MATCH (:Game {id:$id})-[r:HAS_TAG]->(t) RETURN t.name AS name, r.source AS source", id=self.ids[0])
        self.assertEqual({(r["name"], r["source"]) for r in rows}, {(self.names[6], OWNER), (self.names[8], "external")})
        self.assertEqual(self.query("MATCH (:Game {id:$id})-[r]->() RETURN count(r) AS n", id=self.ids[1])[0]["n"], 2)

    def test_stale_or_missing_hardware_rejects_all_game_updates(self):
        self.load()
        self.query("MATCH (h:GPU {name:$name}) SET h.performance_score=201", name=self.names[1])
        changed = deepcopy(self.data)
        changed["games"][0]["title"] = "Não deve persistir"
        with self.assertRaisesRegex(ValueError, "mesmo catálogo"):
            self.load(changed)
        title = self.query("MATCH (g:Game {id:$id}) RETURN g.title AS title", id=self.ids[0])[0]["title"]
        self.assertEqual(title, self.data["games"][0]["title"])

    def test_database_error_rolls_back_previous_game_and_edges(self):
        self.load()
        rows = prepare_payload(self.data)
        rows[0]["properties"]["title"] = "Não deve persistir"
        rows[-1]["properties"]["invalid_property"] = {"map": "Neo4j não aceita mapas como propriedade"}
        with self.assertRaises(Neo4jError):
            self.load(rows=rows)
        self.assertEqual(self.counts(), {"games": 4, "edges": 8})
        self.assertEqual(self.query("MATCH (g:Game {id:$id}) RETURN g.title AS title", id=self.ids[0])[0]["title"], self.data["games"][0]["title"])

    def test_unknown_requirement_removes_old_score(self):
        self.query("MATCH (g:Game {id:$id}) SET g.min_cpu_score=999", id=self.ids[0])
        self.load()
        self.assertIsNone(self.query("MATCH (g:Game {id:$id}) RETURN g.min_cpu_score AS score", id=self.ids[0])[0]["score"])


if __name__ == "__main__":
    unittest.main(argv=[arg for arg in sys.argv if arg != "--integration"], verbosity=2)
