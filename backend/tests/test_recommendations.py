"""API do motor com banco e Steam substituídos por fixtures explícitas."""

from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable

from app.main import app
from app.services.hardware import matching_context, read_hardware
from app.services.steam import Snapshot, SteamError, normalize_game
from test_catalog import FakeDriver, FakeResult, fixture_data


class RecommendationDriver(FakeDriver):
    def __init__(self):
        super().__init__()
        self.games = {}

    def run(self, query, **params):
        if self.error:
            raise self.error
        self.queries.append((query, params))
        if 'c.catalog_json' not in query:
            return FakeResult(self.rows)
        ids, excluded = params.get('ids', []), params.get('excluded', [])
        return FakeResult([{'id': key, 'catalog_json': json.dumps(game), 'genres': game['genres'],
                            'tags': game['themes'], 'shared': ['RPG']} for key, game in self.games.items()
                           if (not ids or key in ids) and key not in excluded])


class FakeSteam:
    def __init__(self):
        self.calls = []
        self.data = {}
        self.featured_ids = []

    def get(self, appid):
        self.calls.append(appid)
        if appid not in self.data:
            raise SteamError('Jogo fixture indisponível.', 404)
        return Snapshot(self.data[appid], {'source_url': 'https://example.org/fixture', 'collected_at': '2026-10-31T12:00:00Z'})

    def get_many(self, ids):
        items, issues = [], []
        for appid in ids:
            try:
                items.append(self.get(appid))
            except SteamError as exc:
                issues.append({'appid': appid, 'message': str(exc)})
        return items, issues

    def featured(self):
        return {'appids': self.featured_ids, 'source': {'type': 'steam_featured_fixture'}}

    def close(self):
        pass


class RecommendationApiTests(unittest.TestCase):
    def setUp(self):
        self.driver = RecommendationDriver()
        self.steam = FakeSteam()
        context = matching_context(read_hardware(self.driver, 'neo4j'))
        for appid in ('101', '102', '103', '104', '105'):
            game = normalize_game(Snapshot(fixture_data(appid), {'source_url': 'https://example.org/fixture'}), context)
            game.update(themes=['Fantasia'], themes_status='classified')
            self.driver.games[appid] = game
        self.driver.queries.clear()
        self.payload = {'anchorIds': ['101', '102', '103'], 'genres': ['RPG'], 'themes': ['Fantasia'],
            'hardware': {'cpuId': 'AMD Ryzen 5 3600', 'gpuId': 'NVIDIA GeForce RTX 5070 12GB',
                         'ramGb': 16, 'os': 'Windows', 'windowsVersion': '11'}}
        self.driver_patch = patch('app.main.GraphDatabase.driver', return_value=self.driver)
        self.steam_patch = patch('app.main.SteamClient', return_value=self.steam)
        self.driver_patch.start()
        self.steam_patch.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.driver_patch.stop)
        self.addCleanup(self.steam_patch.stop)
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_recommendations_exclude_anchors_and_use_one_database_hardware_context(self):
        response = self.client.post('/api/recommendations', json=self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual({m['game']['id'] for m in data['items']}, {'104', '105'})
        self.assertEqual(data['source'], 'neo4j')
        self.assertEqual(data['calculation']['engine_version'], 'rules_v1')
        self.assertTrue(all(m['meets'] == 'minimum' for m in data['items']))
        self.assertEqual(data['items'][0]['game']['platforms']['Windows']['minimum']['requirements']['gpu_score'], 555)
        self.assertEqual(sum('c.catalog_json' not in query for query, _ in self.driver.queries), 1)
        self.assertEqual(self.steam.calls, [])
        self.assertEqual(len(data['anchors']), 3)

    def test_detail_comparison_matches_recommendation_and_old_flat_scores_are_not_trusted(self):
        self.driver.games['104']['min_gpu_score'] = 1
        result = self.client.post('/api/recommendations', json=self.payload).json()
        match = next(m for m in result['items'] if m['game']['id'] == '104')
        comparison = self.client.post('/api/games/104/comparison', json=self.payload)
        self.assertEqual(comparison.status_code, 200)
        self.assertEqual(comparison.json()['match'], match)
        self.assertEqual(match['game']['min_gpu_score'], 555)

    def test_scores_requirements_and_extra_account_fields_cannot_be_sent_by_client(self):
        for extra in ({'performance_score': 999999}, {'games': [{'id': '104', 'min_gpu_score': 0}]}, {'password': 'fixture'}):
            response = self.client.post('/api/recommendations', json={**self.payload, **extra})
            self.assertEqual(response.status_code, 422)
        for extra in ({'performance_score': 999999}, {'score_version': 'manual_v2'}, {'min_gpu_score': 0}):
            value = deepcopy(self.payload)
            value['hardware'].update(extra)
            self.assertEqual(self.client.post('/api/recommendations', json=value).status_code, 422)
        self.assertEqual(self.driver.queries, [])

    def test_invalid_or_incomplete_profile_is_rejected_before_database_queries(self):
        cases = []
        for anchors in (['101', '102'], ['101', '101', '103'], ['101', '102', '0']):
            cases.append({**self.payload, 'anchorIds': anchors})
        cases.extend([{**self.payload, 'genres': []}, {**self.payload, 'themes': []}, {**self.payload, 'hardware': None}])
        for ram in (0, -1, True, 16.5, '16'):
            value = deepcopy(self.payload)
            value['hardware']['ramGb'] = ram
            cases.append(value)
        for value in cases:
            self.assertEqual(self.client.post('/api/recommendations', json=value).status_code, 422, value)
        value = deepcopy(self.payload)
        del value['hardware']['windowsVersion']
        self.assertEqual(self.client.post('/api/recommendations', json=value).status_code, 422)
        self.assertEqual(self.client.post('/api/games/invalid/comparison', json=self.payload).status_code, 422)
        self.assertEqual(self.driver.queries, [])

    def test_removed_component_returns_actionable_error(self):
        self.payload['hardware']['cpuId'] = 'Modelo removido fixture'
        response = self.client.post('/api/recommendations', json=self.payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn('Selecione novamente', response.json()['detail'])

    def test_unclassified_selected_component_stays_pending(self):
        self.driver.rows[0]['performance_score'] = None
        data = self.client.post('/api/recommendations', json=self.payload).json()
        self.assertEqual(data['items'], [])
        self.assertEqual(len(data['pending']), 2)
        self.assertTrue(all(m['meets'] is None for m in data['pending']))

    def test_database_failure_returns_503_and_does_not_use_local_csv_scores(self):
        self.driver.error = ServiceUnavailable('Fixture sem banco')
        response = self.client.post('/api/recommendations', json=self.payload)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.steam.calls, [])

    def test_incomplete_anchor_collection_is_an_error_instead_of_a_different_profile(self):
        del self.driver.games['102']
        response = self.client.post('/api/recommendations', json=self.payload)
        self.assertEqual(response.status_code, 503)
        self.assertIn('todos os jogos âncora', response.json()['detail'])

    def test_comparison_before_hardware_setup_has_no_approval(self):
        response = self.client.post('/api/games/104/comparison', json={'genres': ['RPG'], 'themes': []})
        self.assertEqual(response.status_code, 200, response.text)
        match = response.json()['match']
        self.assertEqual(match['checks'], [])
        self.assertEqual(match['compatibility'], 'needs_review')
        self.assertIsNone(match['meets'])

    def test_detail_with_an_old_profile_missing_windows_version_still_shows_pending_comparison(self):
        del self.payload['hardware']['windowsVersion']
        response = self.client.post('/api/games/104/comparison', json=self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        match = response.json()['match']
        self.assertEqual(match['compatibility'], 'needs_review')
        self.assertIsNone(match['meets'])
        self.assertIsNone(next(c for c in match['checks'] if c['label'] == 'Sistema operacional')['ok'])

    def test_steam_fallback_is_explicit_and_still_calculated_on_server(self):
        # Somente as âncoras permanecem no grafo; a consulta relacionada fica vazia.
        self.driver.games = {k: v for k, v in self.driver.games.items() if k in self.payload['anchorIds']}
        self.steam.data['106'] = fixture_data('106')
        self.steam.featured_ids = ['106']
        response = self.client.post('/api/recommendations', json=self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data['source'], 'steam')
        self.assertTrue(any(issue['appid'] == '' for issue in data['issues']))
        self.assertTrue(any(m['game']['id'] == '106' for group in ('items', 'pending', 'excluded') for m in data[group]))
