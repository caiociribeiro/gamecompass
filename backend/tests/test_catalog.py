"""Testes HTTP com Steam e driver substituídos por fixtures identificadas."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
from threading import Lock
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx
from neo4j.exceptions import ServiceUnavailable

from app.main import app
from app.services.hardware import matching_context, read_hardware
from app.services.steam import SteamClient, SteamError, Snapshot, normalize_game


def fixture_data(appid="1091500"):
    """Dados fictícios de teste; os números não são benchmarks reais."""
    return {
        "type": "game", "steam_appid": int(appid), "name": f"Jogo fixture {appid}",
        "developers": ["Estúdio fixture"], "short_description": "<b>Descrição fixture</b><script>oculto</script>",
        "release_date": {"date": "10 out. 2026"}, "is_free": False,
        "price_overview": {"final_formatted": "R$ 10,00", "currency": "BRL"},
        "header_image": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1091500/header.jpg",
        "genres": [{"id": "3", "description": "RPG"}],
        "categories": [{"id": 2, "description": "Um jogador"}],
        "platforms": {"windows": True, "mac": True, "linux": False},
        "pc_requirements": {
            "minimum": "<strong>Mínimos:</strong><br>SO: Windows 10<br>Processador: AMD Ryzen 5 3600<br>Memória: 8192 MB de RAM<br>Placa de vídeo: NVIDIA GeForce RTX 5070 12GB",
            "recommended": "<strong>Recomendados:</strong><br>SO: Windows 11<br>Processador: AMD Ryzen 7 9800X3D<br>Memória: 16 GB RAM<br>Placa de vídeo: AMD Radeon RX 7900 GRE 16GB",
        },
        "mac_requirements": {"minimum": "OS: macOS 15.5<br>Processor: M1<br>Memory: 16 GB RAM"},
        "linux_requirements": [],
    }


def fixture_rows():
    return [{"component_type": kind, "name": name, "performance_score": score, "score_version": "manual_v1"}
        for kind, name, score in [
            ("CPU", "AMD Ryzen 5 3600", 777),
            ("CPU", "AMD Ryzen 7 9800X3D", 888),
            ("GPU", "NVIDIA GeForce RTX 5070 12GB", 555),
            ("GPU", "AMD Radeon RX 7900 GRE 16GB", None),
        ]]


class FakeResult:
    def __init__(self, rows): self.rows = rows
    def data(self): return deepcopy(self.rows)
    def single(self): return {"status": 1}


class FakeDriver:
    def __init__(self):
        self.rows = fixture_rows()
        self.queries = []
        self.error = None
        self.graph_rows = []
    def session(self, **kwargs):
        self.session_options = kwargs
        return self
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute_read(self, function):
        if self.error: raise self.error
        return function(self)
    def run(self, query, **params):
        if self.error: raise self.error
        self.queries.append((query, params))
        return FakeResult(self.graph_rows if "c.catalog_json" in query else self.rows)
    def close(self): pass


class CatalogTests(unittest.TestCase):
    def graph_fixture(self, appid="1091500"):
        game = normalize_game(Snapshot(fixture_data(appid), {"source_url": "https://example.org/fixture"}), matching_context(read_hardware(self.driver, "neo4j")))
        self.driver.graph_rows = [{"id": appid, "catalog_json": json.dumps(game),
            "genres": ["RPG"], "tags": ["Fantasia"], "shared": ["RPG"]}]

    def test_graph_game_uses_edges_and_current_database_scores_without_steam(self):
        self.graph_fixture()
        self.driver.rows[0]["performance_score"] = 901
        data = self.client.get("/api/games/1091500").json()
        self.assertEqual(data["catalog_source"], "neo4j")
        self.assertEqual(data["themes"], ["Fantasia"])
        self.assertEqual(data["themes_status"], "classified")
        self.assertEqual(data["platforms"]["Windows"]["minimum"]["requirements"]["cpu_score"], 901)
        self.assertEqual(data["min_cpu_score"], 901)
        self.assertEqual(self.calls, [])

    def test_graph_collection_reports_correct_source(self):
        self.graph_fixture()
        data = self.client.get("/api/games?appids=1091500").json()
        self.assertEqual(data["source"], "neo4j")
        self.assertEqual(self.calls, [])

    def test_graph_candidates_receive_anchor_and_profile_filters(self):
        self.graph_fixture("620")
        response = self.client.get("/api/games/discover", params={"anchor_ids": "1091500,292030", "genres": "RPG,Aventura", "tags": "Fantasia"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["source"], "neo4j")
        self.assertEqual(data["items"][0]["id"], "620")
        params = next(params for query, params in self.driver.queries if "c.catalog_json" in query)
        self.assertEqual(params["anchors"], ["1091500", "292030"])
        self.assertEqual(params["excluded"], params["anchors"])
        self.assertEqual(params["genres"], ["RPG", "Aventura"])
        self.assertEqual(params["tags"], ["Fantasia"])
        self.assertEqual(self.calls, [])

    def test_empty_graph_discovery_explains_steam_fallback(self):
        data = self.client.get("/api/games/discover").json()
        self.assertEqual(data["source"], "steam")
        self.assertTrue(any("catalogados" in issue["message"] for issue in data["issues"]))

    def test_graph_discovery_rejects_invalid_filters(self):
        for params in ({"anchor_ids": "1,2,3,4"}, {"tags": "Fantasia,,Terror"}, {"genres": "a" * 81}):
            self.assertEqual(self.client.get("/api/games/discover", params=params).status_code, 422)
        self.assertEqual(self.calls, [])

    def setUp(self):
        self.driver = FakeDriver()
        self.calls = []
        self.responses = {}
        self.search_rows = [{"id": 1091500, "name": "Jogo fixture 1091500", "type": "app"}]
        def handle(request):
            self.calls.append(request)
            if request.url.path.endswith("/storesearch/"):
                if "search" in self.responses:
                    status, body = self.responses["search"]
                    return httpx.Response(status, json=body)
                return httpx.Response(200, json={"total": len(self.search_rows), "items": self.search_rows})
            if request.url.path.endswith("/featuredcategories/"):
                return httpx.Response(200, json={"top_sellers": {"items": [
                    {"id": 10, "type": 0}, {"id": 11, "type": 0},
                    {"id": 10, "type": 0}, {"id": 99, "type": 1}]}})
            appid = request.url.params["appids"]
            if appid in self.responses:
                status, body = self.responses[appid]
                return httpx.Response(status, json=body)
            return httpx.Response(200, json={appid: {"success": True, "data": fixture_data(appid)}})
        self.steam = SteamClient(httpx.Client(transport=httpx.MockTransport(handle)), min_interval=0)
        self.driver_patch = patch("app.main.GraphDatabase.driver", return_value=self.driver)
        self.steam_patch = patch("app.main.SteamClient", return_value=self.steam)
        self.driver_patch.start()
        self.steam_patch.start()
        self.client = TestClient(app).__enter__()
        self.addCleanup(self.driver_patch.stop)
        self.addCleanup(self.steam_patch.stop)
        self.addCleanup(lambda: self.client.__exit__(None, None, None))

    def test_hardware_is_read_only_and_uses_database_scores(self):
        response = self.client.get("/api/hardware")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["CPU"][0]["performance_score"], 777)
        self.assertIsNone(data["GPU"][1]["performance_score"])
        self.assertEqual(data["CPU"][0]["id"], "AMD Ryzen 5 3600")
        self.assertEqual(self.driver.session_options["default_access_mode"], "READ")
        for query, params in self.driver.queries:
            self.assertNotRegex(query, r"\b(?:MERGE|CREATE|SET|DELETE|REMOVE)\b")
            self.assertIn("score_version = $version", query)
            self.assertEqual(params, {"version": "manual_v1"})

    def test_empty_database_never_falls_back_to_csv_or_mock_parts(self):
        self.driver.rows = []
        data = self.client.get("/api/hardware").json()
        self.assertEqual((data["CPU"], data["GPU"]), ([], []))

    def test_unavailable_database_returns_503_for_hardware(self):
        self.driver.error = ServiceUnavailable("fixture")
        self.assertEqual(self.client.get("/api/hardware").status_code, 503)

    def test_legacy_version_is_not_exposed_as_manual(self):
        self.driver.rows[0]["score_version"] = "passmark"
        self.assertEqual(self.client.get("/api/hardware").status_code, 503)

    def test_game_maps_minimum_recommended_and_platforms_separately(self):
        response = self.client.get("/api/games/1091500")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "1091500")
        self.assertEqual(data["genres"], ["RPG"])
        self.assertEqual(data["themes"], [])
        self.assertEqual(data["themes_status"], "pending")
        self.assertNotIn("features", data)
        self.assertNotIn("oculto", data["summary"])
        self.assertEqual(data["platforms"]["Windows"]["minimum"]["requirements"], {"ram_gb": 8, "cpu_score": 777, "gpu_score": 555})
        self.assertEqual(data["platforms"]["Windows"]["recommended"]["requirements"], {"ram_gb": 16, "cpu_score": 888, "gpu_score": None})
        self.assertEqual(data["platforms"]["macOS"]["minimum"]["requirements"]["ram_gb"], 16)
        self.assertFalse(data["platforms"]["Linux"]["native_support"])
        self.assertIsNone(data["platforms"]["Linux"]["minimum"])
        self.assertEqual(len(data["source"]["response_sha256"]), 64)
        self.assertEqual(len(data["hardware_source"]["hardware_sha256"]), 64)
        self.assertEqual(self.calls[0].url.params["l"], "portuguese")

    def test_steam_cache_reprocesses_current_database_scores(self):
        first = self.client.get("/api/games/1091500").json()
        self.driver.rows[0]["performance_score"] = 123
        second = self.client.get("/api/games/1091500").json()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(second["platforms"]["Windows"]["minimum"]["requirements"]["cpu_score"], 123)
        self.assertNotEqual(first["hardware_source"]["hardware_sha256"], second["hardware_source"]["hardware_sha256"])

    def test_games_remain_visible_with_database_unavailable(self):
        self.driver.error = ServiceUnavailable("fixture")
        data = self.client.get("/api/games/1091500").json()
        self.assertEqual(data["title"], "Jogo fixture 1091500")
        self.assertIsNone(data["hardware_source"])
        self.assertIsNone(data["platforms"]["Windows"]["minimum"]["requirements"]["cpu_score"])

    def test_invalid_appid_is_rejected_before_http(self):
        for appid in ("abc", "0", "001", "123456789012345"):
            self.assertEqual(self.client.get("/api/games/" + appid).status_code, 422)
        self.assertEqual(len(self.calls), 0)

    def test_steam_unavailable_app_is_404(self):
        self.responses["1091500"] = (200, {"1091500": {"success": False}})
        self.assertEqual(self.client.get("/api/games/1091500").status_code, 404)

    def test_rate_limit_is_visible_and_not_cached_as_a_game(self):
        self.responses["1091500"] = (429, {})
        self.assertEqual(self.client.get("/api/games/1091500").status_code, 503)
        del self.responses["1091500"]
        self.assertEqual(self.client.get("/api/games/1091500").status_code, 200)

    def test_wrong_identity_and_non_game_are_rejected(self):
        data = fixture_data("999")
        self.responses["1091500"] = (200, {"1091500": {"success": True, "data": data}})
        self.assertEqual(self.client.get("/api/games/1091500").status_code, 502)
        data = fixture_data()
        data["type"] = "dlc"
        self.responses["1091500"] = (200, {"1091500": {"success": True, "data": data}})
        self.assertEqual(self.client.get("/api/games/1091500").status_code, 404)

    def test_partial_selection_reports_failed_appids(self):
        self.responses["1091500"] = (200, {"1091500": {"success": False}})
        response = self.client.get("/api/games?appids=1091500,620")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["issues"][0]["appid"], "1091500")

    def test_saved_anchor_is_reloaded_without_a_preset_catalog(self):
        response = self.client.get("/api/games?appids=12345")
        self.assertEqual(response.status_code, 200)
        self.assertIn("12345", [game["id"] for game in response.json()["items"]])
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(self.client.get("/api/games?appids=" + ",".join(str(i) for i in range(1, 32))).status_code, 422)
        self.assertEqual(self.client.get("/api/games?appids=abc").status_code, 422)

    def test_all_steam_requests_failing_is_503_not_mock_data(self):
        with patch.object(self.steam, "get_many", return_value=([], [{"appid": "1", "message": "fixture"}])):
            self.assertEqual(self.client.get("/api/games?appids=1091500").status_code, 503)

    def test_empty_catalog_does_not_query_steam_or_database(self):
        response = self.client.get("/api/games")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.driver.queries, [])

    def test_anchor_suggestions_use_real_snapshots_without_hardware_queries(self):
        self.driver.error = ServiceUnavailable("fixture")
        response = self.client.get("/api/games/anchors")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["items"]), 8)
        self.assertEqual(data["selection"], "editorial")
        self.assertEqual(data["items"][0]["title"], "Jogo fixture 1091500")
        self.assertTrue(data["items"][0]["image_url"].startswith("https://"))
        self.assertEqual(len(data["items"][0]["source"]["response_sha256"]), 64)
        self.assertNotIn("platforms", data["items"][0])
        self.assertEqual(self.driver.queries, [])
        self.assertTrue(all(call.url.path.endswith("/appdetails") for call in self.calls))

    def test_anchor_suggestions_reuse_cache_and_do_not_replace_search(self):
        for _ in range(2):
            self.assertEqual(self.client.get("/api/games/anchors").status_code, 200)
        self.assertEqual(len(self.calls), 8)
        self.assertEqual(self.client.get("/api/games/search?q=outro").status_code, 200)
        self.assertEqual(len(self.calls), 9)
        self.assertEqual(self.client.get("/api/games").json()["items"], [])

    def test_anchor_suggestions_keep_available_games_when_one_fails(self):
        self.responses["1091500"] = (200, {"1091500": {"success": False}})
        response = self.client.get("/api/games/anchors")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 7)
        self.assertEqual(response.json()["issues"][0]["appid"], "1091500")

    def test_anchor_suggestions_all_failing_do_not_return_mock_games(self):
        with patch.object(self.steam, "get_many", return_value=([], [])):
            self.assertEqual(self.client.get("/api/games/anchors").status_code, 503)

    def test_invalid_anchor_selection_does_not_contact_steam(self):
        for selection in ({"appids": ["1", "1"]}, {"appids": ["abc"]}, [], {"appids": []}):
            with patch.object(Path, "read_text", return_value=json.dumps(selection)):
                self.assertEqual(self.client.get("/api/games/anchors").status_code, 503)
        self.assertEqual(self.calls, [])

    def test_api_health_is_independent_of_steam_and_database(self):
        self.driver.error = ServiceUnavailable("fixture")
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.calls, [])
        self.assertEqual(self.driver.queries, [])

    def test_search_by_name_does_not_load_game_details(self):
        response = self.client.get("/api/games/search", params={"q": "Cyberpunk"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [{"id": "1091500", "title": "Jogo fixture 1091500"}])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0].url.params["term"], "Cyberpunk")
        self.assertNotIn("appids", self.calls[0].url.params)
        self.assertEqual(self.driver.queries, [])

    def test_search_is_cached_and_is_not_an_appid_route(self):
        for query in ("Cyberpunk", "cyberpunk"):
            self.assertEqual(self.client.get("/api/games/search", params={"q": query}).status_code, 200)
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.calls[0].url.path.endswith("/storesearch/"))

    def test_invalid_search_is_rejected_before_http(self):
        for query in ("a", "  ", "x" * 101):
            self.assertEqual(self.client.get("/api/games/search", params={"q": query}).status_code, 422)
        self.assertEqual(self.calls, [])

    def test_search_empty_results_do_not_create_examples(self):
        self.search_rows = []
        response = self.client.get("/api/games/search", params={"q": "inexistente"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])

    def test_search_ignores_invalid_rows_and_packages(self):
        self.search_rows += [None, {"id": 22, "type": "sub", "name": "Pacote fixture"},
            {"id": True, "type": "app", "name": "Inválido"}, self.search_rows[0]]
        data = self.client.get("/api/games/search", params={"q": "fixture"}).json()
        self.assertEqual(len(data["items"]), 1)

    def test_search_failure_is_visible_and_not_cached_as_a_game(self):
        self.responses["search"] = (429, {})
        self.assertEqual(self.client.get("/api/games/search", params={"q": "fixture"}).status_code, 503)
        del self.responses["search"]
        self.assertEqual(self.client.get("/api/games/search", params={"q": "fixture"}).status_code, 200)

    def test_discovery_only_runs_on_explicit_request(self):
        self.assertEqual(self.client.get("/api/games").json()["items"], [])
        self.assertEqual(self.calls, [])
        response = self.client.get("/api/games/discover")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([game["id"] for game in response.json()["items"]], ["10", "11"])
        self.assertEqual(len(self.calls), 3)
        self.assertIn("featuredcategories", response.json()["candidate_source"]["source_url"])

    def test_bad_memory_stays_pending_without_losing_hardware(self):
        data = fixture_data()
        data["pc_requirements"]["minimum"] = data["pc_requirements"]["minimum"].replace("8192 MB de RAM", "muita memória")
        self.responses["1091500"] = (200, {"1091500": {"success": True, "data": data}})
        result = self.client.get("/api/games/1091500").json()["platforms"]["Windows"]["minimum"]
        self.assertEqual(result["requirements"], {"ram_gb": None, "cpu_score": 777, "gpu_score": 555})
        self.assertEqual(result["status"], "needs_review")

    def test_alias_uses_graph_identity_without_copied_catalog_score(self):
        context = matching_context(read_hardware(self.driver, "neo4j"))
        self.assertEqual(context["catalog"][("CPU", "amd ryzen 5 3600")]["performance_score"], 777)


class SteamCacheTests(unittest.TestCase):
    def test_parallel_same_appid_shares_one_http_request(self):
        calls, lock = [], Lock()
        def handler(request):
            with lock: calls.append(request)
            time.sleep(0.03)
            return httpx.Response(200, json={"1091500": {"success": True, "data": fixture_data()}})
        steam = SteamClient(httpx.Client(transport=httpx.MockTransport(handler)), min_interval=0)
        self.addCleanup(steam.close)
        with ThreadPoolExecutor(max_workers=6) as pool:
            snapshots = list(pool.map(steam.get, ["1091500"] * 6))
        self.assertEqual(len(calls), 1)
        self.assertTrue(all(snapshot.data["steam_appid"] == 1091500 for snapshot in snapshots))

    def test_lru_cache_has_a_bound(self):
        def handler(request):
            appid = request.url.params["appids"]
            return httpx.Response(200, json={appid: {"success": True, "data": fixture_data(appid)}})
        steam = SteamClient(httpx.Client(transport=httpx.MockTransport(handler)), min_interval=0, max_entries=2)
        self.addCleanup(steam.close)
        for appid in ("1", "2", "3"): steam.get(appid)
        self.assertLessEqual(len(steam.cache), 2)
        self.assertNotIn("1", steam.cache)


if __name__ == "__main__":
    unittest.main(verbosity=2)
