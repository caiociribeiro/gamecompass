"""Casos de ouro: o motor contra respostas escritas à mão (data/evaluation/gold_cases.json).

Roda sem Neo4j nem Steam: os textos de requisitos estão no arquivo (cópias das respostas da loja) e as
notas de hardware vêm do CSV versionado. Falha se surgir um falso positivo, uma divergência nova ou se uma
divergência conhecida deixar de existir (então a marca known_divergence deve ser removida do caso).
"""

import unittest

from app import evaluate_gold as gold_eval


class GoldCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gold = gold_eval.load_gold()
        cls.results = gold_eval.evaluate(cls.gold)

    def test_every_case_is_well_formed_and_uses_catalog_parts(self):
        hardware = gold_eval.load_hardware()
        names = {kind: {part['name'] for part in hardware[kind]} for kind in ('CPU', 'GPU')}
        for key, machine in self.gold['machines'].items():
            with self.subTest(machine=key):
                self.assertIn(machine['cpu'], names['CPU'])
                self.assertIn(machine['gpu'], names['GPU'])
        ids = [case['id'] for case in self.gold['cases']]
        self.assertEqual(len(ids), len(set(ids)), 'Há ids de caso repetidos.')
        for case in self.gold['cases']:
            with self.subTest(case=case['id']):
                self.assertIn(case['machine'], self.gold['machines'])
                self.assertIn(case['game'], self.gold['games'])
                self.assertIn(case['level'], ('minimum', 'recommended'))
                self.assertIn(case['expect'], ('compatible', 'incompatible', 'needs_review'))
                self.assertTrue(case['why'].strip())

    def test_the_engine_never_approves_what_the_gold_case_says_to_reject(self):
        false_positives = [r['id'] for r in self.results if r['outcome'] == 'false_positive']
        self.assertEqual(false_positives, [])

    def test_no_unexpected_divergence_and_known_ones_stay_as_documented(self):
        problems = [(r['id'], r['status'], r['expected'], r['actual']) for r in self.results if r['status'] not in ('ok', 'known')]
        self.assertEqual(problems, [], 'Divergência nova ou divergência conhecida que mudou; veja python -m app.evaluate_gold.')

    def test_the_report_is_built_from_the_same_results(self):
        report = gold_eval.format_report(self.gold, self.results)
        self.assertIn(f'de {len(self.results)} casos corretos', report)
        self.assertIn('Falsos positivos: 0', report)


if __name__ == '__main__':
    unittest.main()
