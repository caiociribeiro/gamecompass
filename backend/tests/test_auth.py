"""Rotas de conta com um repositório em memória no lugar do Neo4j.

Estes testes verificam a lógica HTTP (hash, cookie, sessão, isolamento). A parte
Cypher é verificada em test_users_neo4j.py, que exige um Neo4j real.
"""

import json
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable

from app import auth_routes
from app.main import app
from app.services.auth import AttemptLimiter
from app.services.users import EmailTaken, account_from, profile_properties
from test_catalog import FakeDriver
from test_recommendations import FakeSteam


class MemoryStore:
    """Mesmo contrato de UserStore; guarda tudo em dicionários."""

    def __init__(self):
        self.users, self.sessions, self.error = {}, {}, None
        self.failures: dict[str, list[float]] = {}

    def _check(self):
        if self.error:
            raise self.error

    def create_user(self, *, name, email, password_hash, now):
        self._check()
        if any(user['email'] == email for user in self.users.values()):
            raise EmailTaken(email)
        user = {'id': f'u{len(self.users) + 1}', 'name': name, 'email': email, 'password_hash': password_hash,
                'genres': [], 'themes': [], 'anchor_ids': []}
        self.users[user['id']] = user
        return dict(user)

    def find_by_email(self, email):
        self._check()
        return next((dict(user) for user in self.users.values() if user['email'] == email), None)

    def create_session(self, *, user_id, token_hash, now, expires_at):
        self._check()
        self.sessions[token_hash] = (user_id, expires_at)

    def user_for_session(self, token_hash, now):
        self._check()
        found = self.sessions.get(token_hash)
        return dict(self.users[found[0]]) if found and found[1] > now else None

    def delete_session(self, token_hash):
        self._check()
        self.sessions.pop(token_hash, None)

    def set_password(self, *, user_id, password_hash, keep_token_hash, now):
        self._check()
        self.users[user_id]['password_hash'] = password_hash
        self.sessions = {key: value for key, value in self.sessions.items()
                         if value[0] != user_id or key == keep_token_hash}

    def recent_failures(self, *, key, since):
        self._check()
        return len([moment for moment in self.failures.get(key, []) if moment > since])

    def add_failure(self, *, key, now, since):
        self._check()
        self.failures[key] = [moment for moment in self.failures.get(key, []) if moment > since] + [now]
        return len(self.failures[key])

    def clear_failures(self, *, key):
        self._check()
        self.failures.pop(key, None)

    def update_profile(self, *, user_id, changes, now):
        self._check()
        user = self.users[user_id]
        for key, value in profile_properties(changes).items():
            if value is None:
                user.pop(key, None)
            else:
                user[key] = value
        return dict(user)


HARDWARE = {'cpuId': 'AMD Ryzen 5 3600', 'gpuId': 'NVIDIA GeForce RTX 5070 12GB', 'ramGb': 16,
            'os': 'Windows', 'windowsVersion': '11'}
CREDENTIALS = {'name': 'Ana', 'email': 'ana@example.invalid', 'password': 'senha-de-teste-1'}


class AuthApiTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        patches = [patch('app.main.GraphDatabase.driver', return_value=FakeDriver()),
                   patch('app.main.SteamClient', return_value=FakeSteam())]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.clients = []
        self.client = self.new_client()

    def new_client(self):
        client = TestClient(app)
        client.__enter__()
        app.state.user_store = self.store
        self.clients.append(client)
        self.addCleanup(client.__exit__, None, None, None)
        return client

    def register(self, client=None, **overrides):
        return (client or self.client).post('/api/auth/register', json={**CREDENTIALS, **overrides})

    def test_register_hashes_password_and_sets_http_only_session_cookie(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertNotIn('email', body)  # o e-mail só sai por /me/account
        self.assertEqual(self.client.get('/api/me/account').json(), {'email': 'ana@example.invalid'})
        self.assertNotIn('password', response.text.lower().replace('"password"', ''))
        self.assertEqual(body['hardware'], None)
        stored = self.store.users[body['id']]['password_hash']
        self.assertTrue(stored.startswith('$argon2'))
        self.assertNotIn(CREDENTIALS['password'], stored)
        cookie = response.headers['set-cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=lax', cookie)
        token = self.client.cookies.get(auth_routes.COOKIE)
        self.assertTrue(token)
        self.assertNotIn(token, self.store.sessions)  # o banco guarda só o digest
        self.assertEqual(self.client.get('/api/auth/me').json()['id'], body['id'])

    def test_register_validates_and_rejects_duplicate_email_ignoring_case(self):
        self.assertEqual(self.register(password='curta').status_code, 422)
        self.assertEqual(self.register(email='sem-arroba').status_code, 422)
        self.assertEqual(self.register(extra='x').status_code, 422)
        self.assertEqual(self.register(email='  ANA@Example.Invalid ').status_code, 201)
        other = self.new_client()
        duplicate = self.register(other)
        self.assertEqual(duplicate.status_code, 409)
        self.assertNotIn(auth_routes.COOKIE, other.cookies)

    def test_login_logout_and_generic_error(self):
        self.register()
        fresh = self.new_client()
        wrong = fresh.post('/api/auth/login', json={'email': CREDENTIALS['email'], 'password': 'errada-errada'})
        unknown = fresh.post('/api/auth/login', json={'email': 'ninguem@example.invalid', 'password': 'errada-errada'})
        self.assertEqual((wrong.status_code, unknown.status_code), (401, 401))
        self.assertEqual(wrong.json(), unknown.json())
        self.assertEqual(fresh.get('/api/auth/me').status_code, 401)
        self.assertEqual(fresh.get('/api/me/account').status_code, 401)
        ok = fresh.post('/api/auth/login', json={'email': 'ANA@example.invalid', 'password': CREDENTIALS['password']})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(fresh.get('/api/auth/me').status_code, 200)
        self.assertEqual(fresh.post('/api/auth/logout').status_code, 200)
        self.assertEqual(fresh.get('/api/auth/me').status_code, 401)
        self.assertEqual(len(self.store.sessions), 1)  # a sessão do cadastro continua

    def test_logout_revokes_server_side_even_if_cookie_is_replayed(self):
        self.register()
        token = self.client.cookies.get(auth_routes.COOKIE)
        self.client.post('/api/auth/logout')
        replay = self.new_client()
        replay.cookies.set(auth_routes.COOKIE, token)
        self.assertEqual(replay.get('/api/auth/me').status_code, 401)

    def test_expired_session_is_rejected(self):
        self.register()
        key = next(iter(self.store.sessions))
        user_id, _ = self.store.sessions[key]
        self.store.sessions[key] = (user_id, int(time.time()) - 1)
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)

    def test_login_is_throttled_after_repeated_failures(self):
        self.register()
        fresh = self.new_client()
        payload = {'email': CREDENTIALS['email'], 'password': 'errada-errada'}
        codes = [fresh.post('/api/auth/login', json=payload).status_code for _ in range(7)]
        self.assertEqual(codes, [401] * 5 + [429] * 2)
        right = fresh.post('/api/auth/login', json={**payload, 'password': CREDENTIALS['password']})
        self.assertEqual(right.status_code, 429)
        # A contagem fica no repositório de contas, só com o hash da chave (sem e-mail nem IP).
        self.assertEqual(len(self.store.failures), 1)
        self.assertNotIn(CREDENTIALS['email'], json.dumps(self.store.failures))

    def test_login_limit_is_shared_by_every_api_process(self):
        # Cada processo da API tem seu próprio AttemptLimiter; todos usam o mesmo repositório.
        processes = [AttemptLimiter(), AttemptLimiter(), AttemptLimiter(), AttemptLimiter()]
        key = 'login:203.0.113.7:ana@example.invalid'
        for attempt in range(5):
            self.assertFalse(processes[attempt % 4].blocked(self.store, key))
            processes[attempt % 4].fail(self.store, key)
        self.assertTrue(all(process.blocked(self.store, key) for process in processes))
        processes[2].reset(self.store, key)
        self.assertFalse(any(process.blocked(self.store, key) for process in processes))

    def test_login_limit_forgets_failures_outside_the_window(self):
        limiter = AttemptLimiter(limit=2, window_seconds=60)
        key = 'login:203.0.113.8:bia@example.invalid'
        with patch('app.services.auth.time.time', return_value=1_000.0):
            limiter.fail(self.store, key)
            limiter.fail(self.store, key)
            self.assertTrue(limiter.blocked(self.store, key))
        with patch('app.services.auth.time.time', return_value=1_061.0):
            self.assertFalse(limiter.blocked(self.store, key))

    def test_profile_requires_session_and_persists_partial_updates(self):
        self.assertEqual(self.new_client().patch('/api/me/profile', json={'genres': ['RPG']}).status_code, 401)
        self.register()
        first = self.client.patch('/api/me/profile', json={'genres': ['RPG', 'RPG', 'Aventura'], 'themes': ['Fantasia']})
        self.assertEqual(first.json()['genres'], ['RPG', 'Aventura'])
        hardware = self.client.patch('/api/me/profile', json={'hardware': HARDWARE, 'anchorIds': ['101', '102', '103']})
        self.assertEqual(hardware.json()['hardware'], HARDWARE)
        name_only = self.client.patch('/api/me/profile', json={'name': 'Ana Maria'}).json()
        self.assertEqual((name_only['genres'], name_only['themes'], name_only['hardware']),
                         (['RPG', 'Aventura'], ['Fantasia'], HARDWARE))
        self.assertEqual(name_only['anchorIds'], ['101', '102', '103'])
        again = self.new_client()  # outro navegador/dispositivo
        again.post('/api/auth/login', json={'email': CREDENTIALS['email'], 'password': CREDENTIALS['password']})
        self.assertEqual(again.get('/api/auth/me').json(), name_only)
        cleared = self.client.patch('/api/me/profile', json={'hardware': None, 'genres': []}).json()
        self.assertIsNone(cleared['hardware'])
        self.assertEqual(cleared['genres'], [])
        self.assertEqual(cleared['anchorIds'], ['101', '102', '103'])

    def test_profile_rejects_forged_fields_and_invalid_values(self):
        self.register()
        for body in ({'id': 'u9'}, {'email': 'x@example.invalid'}, {'password_hash': 'x'}, {'name': None},
                     {'anchorIds': ['1', '2', '3', '4']}, {'anchorIds': ['abc']},
                     {'hardware': {**HARDWARE, 'os': 'BeOS'}}, {'hardware': {**HARDWARE, 'extra': 1}},
                     {'genres': [''] }, {'genres': ['x'] * 21}):
            self.assertEqual(self.client.patch('/api/me/profile', json=body).status_code, 422, body)

    def test_two_accounts_are_isolated(self):
        self.register()
        self.client.patch('/api/me/profile', json={'genres': ['RPG'], 'hardware': HARDWARE, 'anchorIds': ['101']})
        other = self.new_client()
        self.register(other, name='Bia', email='bia@example.invalid')
        mine = other.get('/api/auth/me').json()
        self.assertEqual((mine['name'], mine['genres'], mine['hardware'], mine['anchorIds']), ('Bia', [], None, []))
        other.patch('/api/me/profile', json={'genres': ['Puzzle']})
        self.assertEqual(self.client.get('/api/auth/me').json()['genres'], ['RPG'])
        self.assertEqual(self.client.get('/api/auth/me').json()['hardware'], HARDWARE)

    def test_change_password_checks_current_and_revokes_other_sessions(self):
        self.register()
        other = self.new_client()
        other.post('/api/auth/login', json={'email': CREDENTIALS['email'], 'password': CREDENTIALS['password']})
        self.assertEqual(other.get('/api/auth/me').status_code, 200)
        bad = self.client.post('/api/auth/password', json={'current': 'errada-errada', 'next': 'nova-senha-123'})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.client.post('/api/auth/password', json={'current': CREDENTIALS['password'], 'next': 'curta'}).status_code, 422)
        done = self.client.post('/api/auth/password', json={'current': CREDENTIALS['password'], 'next': 'nova-senha-123'})
        self.assertEqual(done.status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me').status_code, 200)
        self.assertEqual(other.get('/api/auth/me').status_code, 401)
        fresh = self.new_client()
        self.assertEqual(fresh.post('/api/auth/login', json={'email': CREDENTIALS['email'], 'password': CREDENTIALS['password']}).status_code, 401)
        self.assertEqual(fresh.post('/api/auth/login', json={'email': CREDENTIALS['email'], 'password': 'nova-senha-123'}).status_code, 200)

    def test_cross_site_writes_are_blocked_but_known_origins_work(self):
        evil = self.client.post('/api/auth/register', json=CREDENTIALS, headers={'Origin': 'https://evil.example'})
        self.assertEqual(evil.status_code, 403)
        self.assertFalse(self.store.users)
        good = self.client.post('/api/auth/register', json=CREDENTIALS, headers={'Origin': 'http://localhost:5173'})
        self.assertEqual(good.status_code, 201)
        forged = self.client.patch('/api/me/profile', json={'genres': ['RPG']}, headers={'Origin': 'https://evil.example'})
        self.assertEqual(forged.status_code, 403)
        self.assertEqual(self.client.get('/api/auth/me', headers={'Origin': 'https://evil.example'}).status_code, 200)

    def test_database_failure_is_reported_not_hidden(self):
        self.register()
        self.store.error = ServiceUnavailable('indisponível')
        for call in (lambda: self.client.get('/api/auth/me'),
                     lambda: self.client.patch('/api/me/profile', json={'genres': ['RPG']}),
                     lambda: self.client.post('/api/auth/login', json={'email': CREDENTIALS['email'], 'password': 'qualquer-coisa'}),
                     lambda: self.client.post('/api/auth/logout')):
            self.assertEqual(call().status_code, 503)

    def test_seed_demo_creates_then_updates_without_touching_profile(self):
        from app.seed_demo import seed
        from app.services.auth import verify_password
        self.assertEqual(seed(self.store, name='Demo', email=' Demo@Example.invalid ', password='senha-demo-1'), 'criada')
        user = self.store.find_by_email('demo@example.invalid')
        self.assertTrue(verify_password(user['password_hash'], 'senha-demo-1'))
        self.store.update_profile(user_id=user['id'], changes={'genres': ['RPG']}, now=0)
        self.assertEqual(seed(self.store, name='Demo', email='demo@example.invalid', password='senha-demo-2'), 'atualizada')
        again = self.store.find_by_email('demo@example.invalid')
        self.assertTrue(verify_password(again['password_hash'], 'senha-demo-2'))
        self.assertFalse(verify_password(again['password_hash'], 'senha-demo-1'))
        self.assertEqual(again['genres'], ['RPG'])
        self.assertEqual(len(self.store.users), 1)
        with self.assertRaises(Exception):
            seed(self.store, name='Demo', email='demo@example.invalid', password='curta')

    def test_account_shape_never_exposes_hash_or_internal_properties(self):
        shape = account_from({'id': 'u1', 'name': 'A', 'email': 'a@example.invalid', 'password_hash': 'segredo',
                              'hw_cpu': 'C', 'hw_gpu': 'G', 'hw_ram_gb': 8, 'hw_os': 'Linux', 'created_at': 1})
        self.assertEqual(set(shape), {'id', 'name', 'genres', 'themes', 'anchorIds', 'hardware'})
        self.assertEqual(shape['hardware'], {'cpuId': 'C', 'gpuId': 'G', 'ramGb': 8, 'os': 'Linux'})


if __name__ == '__main__':
    unittest.main()
