"""Testa a carga manual com dados fictícios.

Sem banco: python scripts/test_manual_loader.py
Com Neo4j: python scripts/test_manual_loader.py --integration

A integração usa as variáveis NEO4J_* e cria nomes exclusivos com UUID.
Remove somente seus próprios nós de teste ao terminar cada caso.
"""

import argparse
from contextlib import redirect_stderr, redirect_stdout
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from hardware_catalog import COLUMNS, MANUAL_COLUMNS
from load_hardware import NEO4J_MAX_INTEGER, create_constraints, main, prepare_payload, write_hardware


def write_manual_csv(path, models):
    with path.open("w", encoding="utf-8", newline="") as handle:
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


class LoaderUnitTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="gamecompass-loader-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.path = self.root / "manual.csv"
        write_manual_csv(self.path, [
            ("CPU", "CPU fictícia", 300),
            ("GPU", "GPU fictícia", 500),
            ("GPU", "GPU fictícia pendente", ""),
        ])

    def legacy_csv(self, score="1234"):
        path = self.root / "legacy.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerow({
                "component_type": "CPU", "name": "CPU legada fictícia",
                "passmark_score": score, "benchmark": "CPU Mark",
                "source_url": "https://www.cpubenchmark.net/",
                "collected_at": "2026-10-27T00:00:00Z",
            })
        return path

    def run_main(self, *args):
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = main(list(map(str, args)))
        return code, output.getvalue(), error.getvalue()

    def test_manual_payload_contains_only_graph_properties(self):
        result = prepare_payload(self.path, catalog_format="manual")
        self.assertEqual(result["CPU"], [{
            "name": "CPU fictícia", "performance_score": 300, "score_version": "manual_v1",
        }])
        for rows in result.values():
            for row in rows:
                self.assertEqual(set(row), {"name", "performance_score", "score_version"})

    def test_pending_score_remains_none(self):
        result = prepare_payload(self.path, catalog_format="manual")
        pending = next(row for row in result["GPU"] if row["name"].endswith("pendente"))
        self.assertIsNone(pending["performance_score"])
        self.assertEqual(pending["score_version"], "manual_v1")

    def test_cpu_and_gpu_are_separate_groups(self):
        result = prepare_payload(self.path, catalog_format="manual")
        self.assertEqual((len(result["CPU"]), len(result["GPU"])), (1, 2))

    def test_largest_neo4j_integer_is_accepted(self):
        write_manual_csv(self.path, [("GPU", "GPU fictícia", NEO4J_MAX_INTEGER)])
        self.assertEqual(prepare_payload(self.path, catalog_format="manual")["GPU"][0]["performance_score"], NEO4J_MAX_INTEGER)

    def test_manual_integer_overflow_is_rejected(self):
        write_manual_csv(self.path, [("GPU", "GPU fictícia", NEO4J_MAX_INTEGER + 1)])
        with self.assertRaisesRegex(ValueError, "limite inteiro"):
            prepare_payload(self.path, catalog_format="manual")

    def test_zero_score_is_rejected(self):
        write_manual_csv(self.path, [("GPU", "GPU fictícia", 0)])
        with self.assertRaises(ValueError):
            prepare_payload(self.path, catalog_format="manual")

    def test_negative_score_is_rejected(self):
        write_manual_csv(self.path, [("GPU", "GPU fictícia", -1)])
        with self.assertRaises(ValueError):
            prepare_payload(self.path, catalog_format="manual")

    def test_timezone_is_required(self):
        self.path.write_text(self.path.read_text().replace("2026-10-27T00:00:00Z", "2026-10-27T00:00:00"), encoding="utf-8")
        with self.assertRaises(ValueError):
            prepare_payload(self.path, catalog_format="manual")

    def test_other_score_version_is_rejected(self):
        self.path.write_text(self.path.read_text().replace("manual_v1", "manual_v2"), encoding="utf-8")
        with self.assertRaises(ValueError):
            prepare_payload(self.path, catalog_format="manual")

    def test_legacy_header_is_rejected_in_manual_mode(self):
        with self.assertRaisesRegex(ValueError, "Cabeçalho"):
            prepare_payload(self.legacy_csv(), catalog_format="manual")

    def test_duplicate_models_are_rejected(self):
        write_manual_csv(self.path, [("GPU", "GPU fictícia", 400), ("GPU", " gpu  FICTÍCIA ", 500)])
        with self.assertRaisesRegex(ValueError, "duplicado"):
            prepare_payload(self.path, catalog_format="manual")

    def test_empty_catalog_is_rejected(self):
        write_manual_csv(self.path, [])
        with self.assertRaisesRegex(ValueError, "vazio"):
            prepare_payload(self.path, catalog_format="manual")

    def test_legacy_payload_keeps_old_contract(self):
        self.assertEqual(prepare_payload(self.legacy_csv()), {
            "CPU": [{"name": "CPU legada fictícia", "passmark_score": 1234}], "GPU": [],
        })

    def test_legacy_integer_overflow_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "limite inteiro"):
            prepare_payload(self.legacy_csv(str(NEO4J_MAX_INTEGER + 1)))

    def test_manual_dry_run_counts_without_connecting(self):
        with patch("load_hardware.GraphDatabase.driver") as driver:
            code, output, error = self.run_main("--format", "manual", "--input", self.path, "--dry-run")
            driver.assert_not_called()
        self.assertEqual(code, 0, error)
        report = json.loads(output)
        self.assertEqual((report["CPU"], report["GPU"], report["classified"], report["pending"]), (1, 2, 2, 1))
        self.assertEqual(report["score_version"], "manual_v1")
        self.assertNotIn("nodes_created", report)

    def test_legacy_dry_run_keeps_old_report(self):
        code, output, error = self.run_main("--input", self.legacy_csv(), "--dry-run")
        self.assertEqual(code, 0, error)
        self.assertEqual(set(json.loads(output)), {"status", "dry_run", "CPU", "GPU", "input"})

    def test_missing_password_is_reported_before_connecting(self):
        with patch.dict(os.environ, {"NEO4J_PASSWORD": ""}), patch("load_hardware.GraphDatabase.driver") as driver:
            code, output, error = self.run_main("--format", "manual", "--input", self.path)
            driver.assert_not_called()
        self.assertEqual(code, 1)
        self.assertIn("NEO4J_PASSWORD", error)
        self.assertEqual(output, "")

    def test_invalid_catalog_never_opens_connection(self):
        self.path.write_text("invalid\n", encoding="utf-8")
        with patch("load_hardware.GraphDatabase.driver") as driver:
            code, output, error = self.run_main("--format", "manual", "--input", self.path)
            driver.assert_not_called()
        self.assertEqual(code, 1)
        self.assertIn("Erro no catálogo", error)
        self.assertEqual(output, "")

    def test_cli_manual_dry_run_with_unreachable_uri(self):
        environment = {**os.environ, "NEO4J_URI": "bolt://127.0.0.1:1", "NEO4J_PASSWORD": ""}
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("load_hardware.py")), "--format", "manual", "--input", str(self.path), "--dry-run"],
            env=environment, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["pending"], 1)

    def test_invalid_write_format_is_rejected_before_query(self):
        with self.assertRaisesRegex(ValueError, "catalog_format"):
            write_hardware(None, {"CPU": [], "GPU": []}, catalog_format="invalid")


@unittest.skipUnless("--integration" in sys.argv, "Use --integration para executar contra Neo4j.")
class Neo4jIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        password = os.getenv("NEO4J_PASSWORD", "")
        if not password:
            raise ValueError("Defina NEO4J_PASSWORD para executar a integração.")
        cls.database = os.getenv("NEO4J_DATABASE", "neo4j")
        cls.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), password),
            connection_timeout=10, connection_acquisition_timeout=15,
            max_transaction_retry_time=10,
        )
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

    def setUp(self):
        prefix = "__gc_loader_test_" + uuid.uuid4().hex
        self.cpu = prefix + "_CPU"
        self.gpu = prefix + "_GPU"
        self.outside = prefix + "_outside_GPU"
        self.names = [self.cpu, self.gpu, self.outside]
        self.addCleanup(self.cleanup_nodes)

    def cleanup_nodes(self):
        with self.driver.session(database=self.database) as session:
            session.run(
                "MATCH (n) WHERE (n:CPU OR n:GPU) AND n.name IN $names DELETE n",
                names=self.names,
            ).consume()

    def properties(self, name):
        with self.driver.session(database=self.database) as session:
            record = session.run("MATCH (n) WHERE n.name = $name RETURN properties(n) AS properties", name=name).single()
            return record["properties"] if record else None

    def seed(self, query, **parameters):
        with self.driver.session(database=self.database) as session:
            session.run(query, **parameters).consume()

    def manual_payload(self):
        return {
            "CPU": [{"name": self.cpu, "performance_score": 300, "score_version": "manual_v1"}],
            "GPU": [{"name": self.gpu, "performance_score": 500, "score_version": "manual_v1"}],
        }

    def load(self, payload, kind="manual"):
        with self.driver.session(database=self.database) as session:
            return session.execute_write(write_hardware, payload, catalog_format=kind)

    def test_migrates_existing_nodes_without_touching_omitted_models(self):
        self.seed(
            "CREATE (:CPU {name:$cpu, passmark_score:111}), (:GPU {name:$gpu, passmark_score:222}), (:GPU {name:$outside, passmark_score:999})",
            cpu=self.cpu, gpu=self.gpu, outside=self.outside,
        )
        self.assertEqual(self.load(self.manual_payload()), 0)
        self.assertEqual(self.properties(self.cpu), {"name": self.cpu, "performance_score": 300, "score_version": "manual_v1"})
        self.assertEqual(self.properties(self.gpu), {"name": self.gpu, "performance_score": 500, "score_version": "manual_v1"})
        self.assertEqual(self.properties(self.outside), {"name": self.outside, "passmark_score": 999})

    def test_pending_score_removes_both_old_scores(self):
        self.seed(
            "CREATE (:GPU {name:$gpu, performance_score:500, score_version:'manual_v1', passmark_score:222})", gpu=self.gpu,
        )
        payload = {"CPU": [], "GPU": [{"name": self.gpu, "performance_score": None, "score_version": "manual_v1"}]}
        self.assertEqual(self.load(payload), 0)
        self.assertEqual(self.properties(self.gpu), {"name": self.gpu, "score_version": "manual_v1"})

    def test_failure_in_gpu_rolls_back_cpu_update(self):
        self.seed("CREATE (:CPU {name:$cpu, passmark_score:111})", cpu=self.cpu)
        payload = self.manual_payload()
        payload["GPU"][0]["performance_score"] = {"invalid": "property map"}
        with self.assertRaises(Neo4jError):
            self.load(payload)
        self.assertEqual(self.properties(self.cpu), {"name": self.cpu, "passmark_score": 111})
        self.assertIsNone(self.properties(self.gpu))

    def test_legacy_reload_is_rejected_and_rolls_back_other_kind(self):
        self.seed(
            "CREATE (:CPU {name:$cpu, passmark_score:111}), (:GPU {name:$gpu, score_version:'manual_v1'})",
            cpu=self.cpu, gpu=self.gpu,
        )
        payload = {"CPU": [{"name": self.cpu, "passmark_score": 999}], "GPU": [{"name": self.gpu, "passmark_score": 999}]}
        with self.assertRaisesRegex(ValueError, "já migrado"):
            self.load(payload, "passmark")
        self.assertEqual(self.properties(self.cpu), {"name": self.cpu, "passmark_score": 111})
        self.assertEqual(self.properties(self.gpu), {"name": self.gpu, "score_version": "manual_v1"})

    def test_repeated_load_does_not_duplicate_new_nodes(self):
        self.assertEqual(self.load(self.manual_payload()), 2)
        self.assertEqual(self.load(self.manual_payload()), 0)
        with self.driver.session(database=self.database) as session:
            count = session.run("MATCH (n) WHERE n.name IN $names RETURN count(n) AS total", names=[self.cpu, self.gpu]).single()["total"]
        self.assertEqual(count, 2)

    def test_cli_loads_validated_manual_csv(self):
        with tempfile.TemporaryDirectory(prefix="gc-loader-integration-") as directory:
            path = Path(directory) / "manual.csv"
            write_manual_csv(path, [("CPU", self.cpu, 300), ("GPU", self.gpu, "")])
            before = path.read_bytes()
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("load_hardware.py")), "--format", "manual", "--input", str(path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual((report["nodes_created"], report["classified"], report["pending"]), (2, 1, 1))
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.properties(self.gpu), {"name": self.gpu, "score_version": "manual_v1"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration", action="store_true", help="Executa seis testes no Neo4j usando nomes exclusivos e limpeza ao terminar.")
    args, remaining = parser.parse_known_args()
    unittest.main(
        argv=[sys.argv[0], *remaining], verbosity=2,
        defaultTest="Neo4jIntegrationTests" if args.integration else "LoaderUnitTests",
    )
