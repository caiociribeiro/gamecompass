"""Verificação real da persistência de contas no Neo4j.

Só roda com GAMECOMPASS_TEST_NEO4J=1 e o banco do Compose ativo. Usa e-mails
únicos de teste e apaga o que criou; não toca em jogos, CPUs ou GPUs.
"""

import os
import time
import unittest
import uuid

from neo4j import GraphDatabase

from app.core.config import settings
from app.services.users import EmailTaken, UserStore, account_from

ENABLED = os.getenv('GAMECOMPASS_TEST_NEO4J') == '1'


@unittest.skipUnless(ENABLED, 'Defina GAMECOMPASS_TEST_NEO4J=1 com o Neo4j ativo para executar.')
class UserStoreNeo4jTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        cls.store = UserStore(cls.driver, settings.neo4j_database)
        cls.tag = uuid.uuid4().hex[:10]

    @classmethod
    def tearDownClass(cls):
        with cls.driver.session(database=settings.neo4j_database) as session:
            session.run("MATCH (u:User) WHERE u.email ENDS WITH $suffix OPTIONAL MATCH (u)-[:HAS_SESSION]->(s:Session)"
                        " DETACH DELETE s, u", suffix=f'-{cls.tag}@example.invalid').consume()
        cls.driver.close()

    def email(self, name):
        return f'{name}-{self.tag}@example.invalid'

    def test_full_account_lifecycle_on_real_database(self):
        now = int(time.time())
        ana = self.store.create_user(name='Ana', email=self.email('ana'), password_hash='hash-a', now=now)
        bia = self.store.create_user(name='Bia', email=self.email('bia'), password_hash='hash-b', now=now)
        with self.assertRaises(EmailTaken):
            self.store.create_user(name='Outra', email=self.email('ana'), password_hash='x', now=now)
        self.assertEqual(self.store.find_by_email(self.email('ana'))['id'], ana['id'])

        self.store.create_session(user_id=ana['id'], token_hash=f'a1-{self.tag}', now=now, expires_at=now + 100)
        self.store.create_session(user_id=ana['id'], token_hash=f'a2-{self.tag}', now=now, expires_at=now + 100)
        self.store.create_session(user_id=bia['id'], token_hash=f'b1-{self.tag}', now=now, expires_at=now + 100)
        self.assertEqual(self.store.user_for_session(f'a1-{self.tag}', now)['id'], ana['id'])
        self.assertIsNone(self.store.user_for_session(f'a1-{self.tag}', now + 100))  # expirada
        self.assertIsNone(self.store.user_for_session('inexistente', now))

        hardware = {'cpuId': 'AMD Ryzen 5 3600', 'gpuId': 'NVIDIA GeForce RTX 5070 12GB', 'ramGb': 16,
                    'os': 'Windows', 'windowsVersion': '11'}
        saved = account_from(self.store.update_profile(user_id=ana['id'], now=now, changes={
            'genres': ['RPG'], 'themes': ['Fantasia'], 'anchorIds': ['101', '102', '103'], 'hardware': hardware}))
        self.assertEqual(saved['hardware'], hardware)
        self.assertEqual(saved['anchorIds'], ['101', '102', '103'])
        self.assertEqual(account_from(self.store.find_by_email(self.email('bia')))['hardware'], None)  # isolamento
        self.assertEqual(account_from(self.store.find_by_email(self.email('bia')))['genres'], [])

        cleared = account_from(self.store.update_profile(user_id=ana['id'], now=now, changes={'hardware': None}))
        self.assertIsNone(cleared['hardware'])
        self.assertEqual(cleared['genres'], ['RPG'])
        with self.driver.session(database=settings.neo4j_database) as session:
            props = session.run("MATCH (u:User {id: $id}) RETURN keys(u) AS keys", id=ana['id']).single()['keys']
        self.assertFalse([key for key in props if key.startswith('hw_')])

        self.store.set_password(user_id=ana['id'], password_hash='hash-novo', keep_token_hash=f'a2-{self.tag}', now=now)
        self.assertEqual(self.store.find_by_email(self.email('ana'))['password_hash'], 'hash-novo')
        self.assertIsNone(self.store.user_for_session(f'a1-{self.tag}', now))
        self.assertIsNotNone(self.store.user_for_session(f'a2-{self.tag}', now))
        self.assertIsNotNone(self.store.user_for_session(f'b1-{self.tag}', now))  # outra conta intacta

        self.store.delete_session(f'a2-{self.tag}')
        self.assertIsNone(self.store.user_for_session(f'a2-{self.tag}', now))


    def test_interactions_use_one_relationship_per_game(self):
        now = int(time.time())
        ana = self.store.create_user(name='Ana', email=self.email('inter'), password_hash='hash', now=now)
        with self.driver.session(database=settings.neo4j_database) as session:
            game = session.run("MATCH (g:Game) RETURN g.id AS id, g.title AS title ORDER BY g.id LIMIT 1").single()
        if game is None:
            self.skipTest('Catálogo de jogos não carregado no Neo4j.')
        gid = game['id']
        self.assertIsNone(self.store.record_view(user_id=ana['id'], game_id='0', now=now))  # fora do catálogo
        self.assertEqual(self.store.record_view(user_id=ana['id'], game_id=gid, now=now)['views'], 1)
        self.assertEqual(self.store.record_view(user_id=ana['id'], game_id=gid, now=now + 5)['views'], 2)
        liked = self.store.set_reaction(user_id=ana['id'], game_id=gid, reaction='liked', now=now + 6)
        self.assertEqual((liked['reaction'], liked['views'], liked['reactedAt'], liked['title']), ('liked', 2, now + 6, game['title']))
        self.store.set_reaction(user_id=ana['id'], game_id=gid, reaction='disliked', now=now + 7)
        items = self.store.list_interactions(ana['id'])
        self.assertEqual([(i['gameId'], i['reaction']) for i in items], [(gid, 'disliked')])
        with self.driver.session(database=settings.neo4j_database) as session:
            count = session.run("MATCH (:User {id: $uid})-[r:INTERACTED]->(:Game {id: $gid}) RETURN count(r) AS n",
                                uid=ana['id'], gid=gid).single()['n']
        self.assertEqual(count, 1)
        # Reação removida de um jogo nunca visto não deixa relação vazia.
        other = self.store.list_interactions(ana['id'])[0]['gameId']
        self.assertEqual(self.store.clear_interactions(ana['id']), 1)
        self.assertEqual(self.store.list_interactions(ana['id']), [])
        self.store.set_reaction(user_id=ana['id'], game_id=other, reaction='liked', now=now)
        self.store.set_reaction(user_id=ana['id'], game_id=other, reaction=None, now=now)
        self.assertEqual(self.store.list_interactions(ana['id']), [])


if __name__ == '__main__':
    unittest.main()
