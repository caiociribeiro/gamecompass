"""Visualizações e reações: rotas, isolamento entre contas e efeito nas recomendações (regra A).

O Neo4j é substituído por um repositório em memória com o mesmo contrato de UserStore. A parte
Cypher é verificada em test_users_neo4j.py (GAMECOMPASS_TEST_NEO4J=1).
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable

from app import auth_routes
from app.main import app
from app.services.hardware import matching_context, read_hardware
from app.services.steam import Snapshot, normalize_game
from app.services.users import interaction_from
from test_auth import CREDENTIALS, MemoryStore
from test_catalog import fixture_data
from test_recommendations import FakeSteam, RecommendationDriver


class InteractionStore(MemoryStore):
    def __init__(self, known):
        super().__init__()
        self.known = known  # appid -> título; só jogos do catálogo aceitam interação
        self.links = {}

    def _link(self, user_id, game_id):
        return self.links.setdefault((user_id, game_id), {'views': 0})

    def _row(self, user_id, game_id):
        rel = self.links[(user_id, game_id)]
        found = interaction_from({'game_id': game_id, 'title': self.known[game_id], 'rel': rel})
        if not found['reaction'] and not found['views']:
            del self.links[(user_id, game_id)]
        return found

    def record_view(self, *, user_id, game_id, now):
        self._check()
        if game_id not in self.known:
            return None
        rel = self._link(user_id, game_id)
        rel['views'] += 1
        rel.setdefault('first_viewed_at', now)
        rel['last_viewed_at'] = now
        return self._row(user_id, game_id)

    def set_reaction(self, *, user_id, game_id, reaction, now):
        self._check()
        if game_id not in self.known:
            return None
        rel = self._link(user_id, game_id)
        rel['reaction'], rel['reacted_at'] = reaction, (now if reaction else None)
        return self._row(user_id, game_id)

    def list_interactions(self, user_id):
        self._check()
        return [self._row(u, g) for (u, g) in list(self.links) if u == user_id]

    def clear_interactions(self, user_id):
        self._check()
        mine = [key for key in self.links if key[0] == user_id]
        for key in mine:
            del self.links[key]
        return len(mine)


class InteractionApiTests(unittest.TestCase):
    def setUp(self):
        auth_routes.limiter._failures.clear()
        self.driver = RecommendationDriver()
        self.steam = FakeSteam()
        context = matching_context(read_hardware(self.driver, 'neo4j'))
        for appid in ('101', '102', '103', '104', '105'):
            game = normalize_game(Snapshot(fixture_data(appid), {'source_url': 'https://example.org/fixture'}), context)
            game.update(themes=['Fantasia'], themes_status='classified')
            self.driver.games[appid] = game
        self.store = InteractionStore({appid: f'Jogo fixture {appid}' for appid in self.driver.games})
        self.payload = {'anchorIds': ['101', '102', '103'], 'genres': ['RPG'], 'themes': ['Fantasia'],
            'hardware': {'cpuId': 'AMD Ryzen 5 3600', 'gpuId': 'NVIDIA GeForce RTX 5070 12GB',
                         'ramGb': 16, 'os': 'Windows', 'windowsVersion': '11'}}
        for item in (patch('app.main.GraphDatabase.driver', return_value=self.driver),
                     patch('app.main.SteamClient', return_value=self.steam)):
            item.start()
            self.addCleanup(item.stop)
        self.client = self.new_client()
        self.assertEqual(self.client.post('/api/auth/register', json=CREDENTIALS).status_code, 201)

    def new_client(self):
        client = TestClient(app)
        client.__enter__()
        app.state.user_store = self.store
        self.addCleanup(client.__exit__, None, None, None)
        return client

    def ids(self, data, group='items'):
        return [match['game']['id'] for match in data[group]]

    def test_routes_require_a_session(self):
        anonymous = self.new_client()
        self.assertEqual(anonymous.get('/api/me/interactions').status_code, 401)
        self.assertEqual(anonymous.post('/api/me/games/104/view').status_code, 401)
        self.assertEqual(anonymous.put('/api/me/games/104/reaction', json={'reaction': 'liked'}).status_code, 401)
        self.assertEqual(anonymous.delete('/api/me/interactions').status_code, 401)

    def test_views_accumulate_and_reactions_replace_each_other(self):
        self.client.post('/api/me/games/104/view')
        seen = self.client.post('/api/me/games/104/view').json()
        self.assertEqual((seen['gameId'], seen['views'], seen['reaction']), ('104', 2, None))
        liked = self.client.put('/api/me/games/104/reaction', json={'reaction': 'liked'}).json()
        self.assertEqual((liked['reaction'], liked['views']), ('liked', 2))
        disliked = self.client.put('/api/me/games/104/reaction', json={'reaction': 'disliked'}).json()
        self.assertEqual(disliked['reaction'], 'disliked')
        cleared = self.client.put('/api/me/games/104/reaction', json={'reaction': None}).json()
        self.assertEqual((cleared['reaction'], cleared['views']), (None, 2))
        self.assertEqual(len(self.client.get('/api/me/interactions').json()['items']), 1)

    def test_removing_a_reaction_of_a_never_viewed_game_leaves_nothing_behind(self):
        self.client.put('/api/me/games/105/reaction', json={'reaction': 'liked'})
        self.client.put('/api/me/games/105/reaction', json={'reaction': None})
        self.assertEqual(self.client.get('/api/me/interactions').json()['items'], [])

    def test_invalid_input_and_games_outside_the_catalog_are_rejected(self):
        self.assertEqual(self.client.put('/api/me/games/104/reaction', json={'reaction': 'amei'}).status_code, 422)
        self.assertEqual(self.client.put('/api/me/games/104/reaction', json={}).status_code, 422)
        self.assertEqual(self.client.put('/api/me/games/104/reaction', json={'reaction': 'liked', 'x': 1}).status_code, 422)
        self.assertEqual(self.client.post('/api/me/games/abc/view').status_code, 422)
        self.assertEqual(self.client.post('/api/me/games/999999/view').status_code, 404)
        self.assertEqual(self.client.put('/api/me/games/999999/reaction', json={'reaction': 'liked'}).status_code, 404)

    def test_foreign_origin_cannot_write(self):
        response = self.client.put('/api/me/games/104/reaction', json={'reaction': 'liked'},
                                   headers={'Origin': 'https://site-malicioso.example'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get('/api/me/interactions').json()['items'], [])

    def test_accounts_do_not_see_each_others_interactions_and_history_can_be_cleared(self):
        self.client.put('/api/me/games/104/reaction', json={'reaction': 'liked'})
        self.client.post('/api/me/games/105/view')
        other = self.new_client()
        self.assertEqual(other.post('/api/auth/register', json={**CREDENTIALS, 'email': 'bia@example.invalid'}).status_code, 201)
        self.assertEqual(other.get('/api/me/interactions').json()['items'], [])
        self.assertEqual(other.delete('/api/me/interactions').json(), {'removed': 0})
        self.assertEqual(len(self.client.get('/api/me/interactions').json()['items']), 2)
        self.assertEqual(self.client.delete('/api/me/interactions').json(), {'removed': 2})
        self.assertEqual(self.client.get('/api/me/interactions').json()['items'], [])

    def test_database_failure_is_a_503(self):
        self.store.error = ServiceUnavailable('Fixture sem banco')
        self.assertEqual(self.client.get('/api/me/interactions').status_code, 503)

    def test_dislike_removes_the_game_from_recommendations(self):
        before = self.client.post('/api/recommendations', json=self.payload).json()
        self.assertEqual(set(self.ids(before)), {'104', '105'})
        self.client.put('/api/me/games/104/reaction', json={'reaction': 'disliked'})
        after = self.client.post('/api/recommendations', json=self.payload).json()
        self.assertEqual(self.ids(after), ['105'])
        self.assertEqual(after['interactions']['hidden'], ['104'])
        # O detalhe continua acessível por link direto, com a reação marcada.
        detail = self.client.post('/api/games/104/comparison', json=self.payload).json()
        self.assertEqual(detail['match']['reaction'], 'disliked')

    def test_liked_game_becomes_an_extra_anchor_for_the_affinity_of_others(self):
        before = self.client.post('/api/recommendations', json=self.payload).json()
        self.assertFalse(any('104' == a['id'] for m in before['items'] if m['game']['id'] == '105' for a in m['anchorMatches']))
        self.client.put('/api/me/games/104/reaction', json={'reaction': 'liked'})
        after = self.client.post('/api/recommendations', json=self.payload).json()
        self.assertEqual(after['interactions']['likedAnchors'], ['104'])
        self.assertEqual(len(after['anchors']), 3)  # as âncoras do perfil continuam sendo 3
        match = next(m for m in after['items'] if m['game']['id'] == '105')
        self.assertIn('104', [a['id'] for a in match['anchorMatches']])
        liked = next(m for m in after['items'] if m['game']['id'] == '104')
        self.assertEqual(liked['reaction'], 'liked')
        # O jogo curtido não pontua contra si mesmo.
        self.assertNotIn('104', [a['id'] for a in liked['anchorMatches']])
        self.assertEqual(self.client.post('/api/games/105/comparison', json=self.payload).json()['match'], match)

    def test_without_session_the_result_is_the_pure_rules_v1(self):
        anonymous = self.new_client()
        self.client.put('/api/me/games/104/reaction', json={'reaction': 'disliked'})
        result = anonymous.post('/api/recommendations', json=self.payload).json()
        self.assertEqual(set(self.ids(result)), {'104', '105'})
        self.assertEqual(result['interactions'], {'authenticated': False, 'likedAnchors': [], 'hidden': []})
        self.assertEqual(result['calculation']['engine_version'], 'rules_v1')


if __name__ == '__main__':
    unittest.main()
