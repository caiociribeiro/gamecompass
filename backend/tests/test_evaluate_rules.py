"""Avaliação offline: funções puras testadas com jogos e peças fictícios de teste (não são dados reais)."""

import json
import os
import tempfile
import unittest

from app import evaluate_rules as ev
from app.services.recommendation_engine import MIN_AFFINITY

VERSION = 'manual_v1'


def part(kind, name, score):
    return {'id': name, 'name': name, 'vendor': 'Outro', 'performance_score': score, 'score_version': VERSION, 'kind': kind}


HARDWARE = {
    'CPU': [part('CPU', f'CPU {n}', n) for n in (10, 20, 30, 40, 50)] + [part('CPU', 'CPU sem nota', None)],
    'GPU': [part('GPU', f'GPU {n}', n) for n in (10, 20, 30, 40, 50)],
}


def game(identifier, title, genres, themes, *, gpu=10, developer='Estúdio'):
    block = {'requirements': {'ram_gb': 8, 'cpu_score': 10, 'gpu_score': gpu}, 'score_version': VERSION,
             'os_text': 'Windows 10', 'issues': [], 'hardware': {}, 'status': 'resolved'}
    return {'id': identifier, 'title': title, 'developer': f'{developer} {identifier}', 'genres': genres, 'themes': themes,
            'themes_status': 'classified', 'platforms': {'Windows': {'native_support': True, 'minimum': block, 'recommended': None}}}


def games():
    return [
        game('1', 'Âncora A', ['RPG'], ['Fantasia']),
        game('2', 'Âncora B', ['RPG'], ['Fantasia']),
        game('3', 'Âncora C', ['RPG'], ['Fantasia']),
        game('4', 'Compatível', ['RPG'], ['Fantasia'], gpu=10),
        game('5', 'Exigente', ['RPG'], ['Fantasia'], gpu=50),
        game('6', 'Sem relação', ['Corrida'], ['Relaxante']),
    ]


def scenario(tier='baixo'):
    return {'name': 'teste', 'tier': tier, 'anchorIds': ['1', '2', '3'], 'genres': ['RPG'], 'themes': ['Fantasia'],
            'hardware': {'cpuId': 'CPU 20', 'gpuId': 'GPU 20', 'ramGb': 16, 'os': 'Windows', 'windowsVersion': '11'}}


class EvaluateRulesTests(unittest.TestCase):
    def test_tiers_use_real_scored_parts_in_increasing_order(self):
        tiers = ev.hardware_tiers(HARDWARE)
        self.assertEqual([tiers[t]['cpuId'] for t in ('baixo', 'medio', 'alto')], ['CPU 20', 'CPU 30', 'CPU 40'])
        self.assertNotIn('CPU sem nota', [t['cpuId'] for t in tiers.values()])

    def test_tiers_fail_when_there_are_no_scored_parts(self):
        with self.assertRaises(ValueError):
            ev.hardware_tiers({'CPU': [part('CPU', 'x', None)], 'GPU': HARDWARE['GPU']})

    def test_auto_scenarios_are_deterministic_and_use_distinct_catalog_anchors(self):
        first = ev.auto_scenarios(games(), HARDWARE, 6, seed=7)
        self.assertEqual(first, ev.auto_scenarios(games(), HARDWARE, 6, seed=7))
        self.assertEqual([s['tier'] for s in first], ['baixo', 'medio', 'alto'] * 2)
        for s in first:
            self.assertEqual(len(set(s['anchorIds'])), 3)
            self.assertLessEqual(set(s['anchorIds']), {g['id'] for g in games()})

    def test_scenario_counts_groups_anchors_and_below_cut(self):
        result = ev.evaluate_scenario(scenario(), games(), HARDWARE, top_n=5)
        self.assertEqual(result['counts'], {'items': 1, 'pending': 0, 'excluded': 1})
        self.assertEqual(result['below_cut'], 1)  # 'Sem relação'; as âncoras não contam como candidatas
        self.assertEqual([i['title'] for i in result['top_items']], ['Compatível'])
        self.assertTrue(all(a >= MIN_AFFINITY for a in result['affinities']))

    def test_top_n_limits_only_the_listing_not_the_counts(self):
        extra = games() + [game('7', 'Compatível 2', ['RPG'], ['Fantasia'])]
        result = ev.evaluate_scenario(scenario(), extra, HARDWARE, top_n=1)
        self.assertEqual(len(result['top_items']), 1)
        self.assertEqual(result['counts']['items'], 2)

    def test_incomplete_profile_is_an_error_not_a_silent_empty_result(self):
        broken = scenario()
        broken['hardware']['cpuId'] = 'CPU inexistente'
        with self.assertRaises(ValueError):
            ev.evaluate_scenario(broken, games(), HARDWARE, top_n=5)

    def test_summary_histogram_coverage_and_report(self):
        results = [ev.evaluate_scenario(scenario(t), games(), HARDWARE, 5) for t in ('baixo', 'alto')]
        summary = ev.summarize(results, catalog_size=6)
        self.assertEqual(summary['scenarios'], 2)
        self.assertEqual(summary['counts']['items'], {'mean': 1, 'min': 1, 'max': 1})
        self.assertEqual(sum(b['count'] for b in summary['affinity_histogram']), sum(len(r['affinities']) for r in results))
        self.assertEqual(summary['top_coverage'], {'distinct_games': 1, 'catalog_size': 6})
        meta = {'engine_version': 'rules_v1', 'minimum_affinity': MIN_AFFINITY, 'catalog_size': 6,
                'scenario_source': 'teste', 'hardware_sha256': 'h', 'curation_sha256': 'c'}
        text = ev.format_report(meta, summary, results, 5)
        for expected in ('rules_v1', 'Distribuição de afinidade', 'Cobertura do top-5', 'Compatível'):
            self.assertIn(expected, text)

    def test_read_scenarios_uses_the_api_contract(self):
        def write(content):
            handle, path = tempfile.mkstemp(suffix='.json')
            self.addCleanup(os.remove, path)
            with os.fdopen(handle, 'w', encoding='utf-8') as out:
                json.dump(content, out)
            return path
        good = {k: scenario()[k] for k in ('anchorIds', 'genres', 'themes', 'hardware')}
        self.assertEqual(ev.read_scenarios(write({'scenarios': [good]}))[0]['name'], 'cenario-001')
        for bad in ({'scenarios': []}, {'scenarios': [{**good, 'anchorIds': ['1', '2']}]}, [good]):
            with self.assertRaises(ValueError):
                ev.read_scenarios(write(bad))


if __name__ == '__main__':
    unittest.main()
