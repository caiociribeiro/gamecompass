"""Contrato congelado a partir dos testes do motor TypeScript da etapa27."""

import json
from pathlib import Path
import unittest

from app.services import recommendation_engine as engine
from app.services.affinity import facet_similarity, content_affinity

FUNCTIONS = {
    'facetSimilarity': facet_similarity, 'contentAffinity': content_affinity, 'replacementOptions': engine.replacement_options,
    'windowsCheck': engine.windows_check, 'hardwareChecks': engine.hardware_checks,
    'describeMatch': engine.describe_match, 'replacementPart': engine.replacement_part,
    'buildRecommendations': engine.build_recommendations, 'hardwareProfileReady': engine.hardware_profile_ready,
    'profileReady': engine.profile_ready,
}


class EngineParityTests(unittest.TestCase):
    def compare(self, actual, expected, path='result'):
        if type(expected) in (float, int) and type(actual) in (float, int):
            self.assertAlmostEqual(actual, expected, places=10, msg=path)
        elif isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected), path)
            for key in expected:
                self.compare(actual[key], expected[key], path + '.' + key)
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected), path)
            for index, (left, right) in enumerate(zip(actual, expected)):
                self.compare(left, right, f'{path}[{index}]')
        else:
            self.assertEqual(actual, expected, path)

    def test_frozen_typescript_cases(self):
        cases = json.loads((Path(__file__).parent / 'fixtures/engine_parity.json').read_text())
        self.assertGreater(len(cases), 100)
        for index, case in enumerate(cases):
            with self.subTest(index=index, function=case['function']):
                self.compare(FUNCTIONS[case['function']](*case['args']), case.get('expected'))
