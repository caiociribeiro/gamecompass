"""Observações da loja não são uma ficha de hardware nem uma aprovação.

Os snapshots criados nestes testes são fixtures inventadas.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from extract_steam_requirements import is_notes_only_requirement_text, extract_snapshot
from fetch_steam import save_snapshot
from game_catalog import ROOT, build_catalog, validate_catalog
from hardware_catalog import read_catalog
from hardware_matcher import normalize_name, read_aliases
from process_requirements import process_requirements
from regex_parser import clean_html
from requirements_curation import read_curation, apply_curation
from review_game_requirements import review_catalog

NOTES = ('<strong>Recommended:</strong><br>Requires a 64-bit processor and operating system'
         '<br>Network: Broadband Internet connection<br>Additional Notes: Gamepad Recommended')
MINIMUM = ('OS: Windows 10<br>Processor: AMD Ryzen 5 3600<br>Memory: 4 GB RAM'
           '<br>Graphics: NVIDIA GeForce GTX 660')


class NotesOnlyTests(unittest.TestCase):
    def test_network_and_notes_are_kept_separate_from_hardware_in_both_languages(self):
        for html in (NOTES, 'Recomendados:<br>Requer um processador e sistema operacional de 64 bits'
                     '<br>Rede: Conexão de internet banda larga<br>Outras observações: Controle recomendado'):
            self.assertTrue(is_notes_only_requirement_text(clean_html(html)))

    def test_partial_hardware_fields_and_unknown_text_are_not_discarded(self):
        for html in ('Recomendados:<br>Memória: 1 GB de RAM<br>Espaço no disco: 200 MB',
                     'Recommended:<br>Memory: 1 GB RAM', 'OS: Windows 10',
                     'Processor: quad core', 'Graphics: GPU fixture', 'Storage: 1 GB',
                     'Texto desconhecido sobre o hardware', 'Additional Notes: controle<br>Memory: inválida'):
            with self.subTest(html=html):
                self.assertFalse(is_notes_only_requirement_text(clean_html(html)))

    def test_empty_block_and_boilerplate_are_not_new_notes_only_blocks(self):
        for html in ('', 'Recommended:', 'Requires a 64-bit processor and operating system'):
            self.assertFalse(is_notes_only_requirement_text(clean_html(html)))

    def build(self, recommended=NOTES):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        selection = self.root / 'selection.json'
        selection.write_text(json.dumps({'schema_version': 'steam_games_v1', 'tag_vocabulary': ['Fantasia'],
            'games': [{'id': '999001', 'tags': ['Fantasia'], 'curation_notes': 'Fixture inventada.'}]}))
        raw = json.dumps({'999001': {'success': True, 'data': {'type': 'game', 'steam_appid': 999001,
            'name': 'Fixture de observações', 'is_free': True, 'genres': [{'description': 'Indie'}],
            'platforms': {'windows': True, 'mac': False, 'linux': False},
            'pc_requirements': {'minimum': MINIMUM, 'recommended': recommended}}}}).encode()
        self.folder = self.root / 'raw/999001'
        save_snapshot(self.folder, raw, {'appid': '999001', 'title': 'Fixture de observações',
            'source_url': 'https://store.steampowered.com/api/appdetails?appids=999001',
            'response_sha256': hashlib.sha256(raw).hexdigest(), 'collected_at': '2026-10-31T12:00:00Z',
            'country': 'br', 'language': 'portuguese'})
        return build_catalog(self.root / 'raw', selection, ROOT / 'data/catalog/hardware_manual_v1.csv',
                             ROOT / 'data/catalog/hardware_aliases.json')

    def test_pipeline_preserves_notes_and_raw_without_creating_recommended_scores(self):
        data = self.build()
        before = (self.folder / 'appdetails.json').read_bytes()
        extracted = extract_snapshot(self.folder)
        self.assertFalse(any('recommended: campo de SO ausente' in issue for issue in extracted['issues']))
        game = data['games'][0]
        block = game['platforms']['Windows']['recommended']
        self.assertEqual(block['requirements_kind'], 'notes_only')
        self.assertEqual(block['text'], clean_html(NOTES))
        self.assertIsNone(game['rec_ram_gb'])
        self.assertIsNone(game['rec_cpu_score'])
        self.assertIsNone(game['rec_gpu_score'])
        self.assertEqual((self.folder / 'appdetails.json').read_bytes(), before)
        validate_catalog(data)
        review = review_catalog(data)
        self.assertEqual(review['summary']['recommended']['not_provided'], 1)
        self.assertEqual(review['summary']['notes_only']['recommended'], 1)
        self.assertEqual(review['summary']['requiring_curation'], 0)
        self.assertEqual(review['games'][0]['recommended']['blocking_fields'], [])

    def test_old_processed_block_can_be_reviewed_without_trusting_a_new_flag(self):
        data = self.build()
        del data['games'][0]['platforms']['Windows']['recommended']['requirements_kind']
        self.assertEqual(review_catalog(data)['summary']['notes_only']['recommended'], 1)

    def test_partial_ram_recommended_stays_pending_and_does_not_inherit_the_minimum(self):
        data = self.build('Recommended:<br>Memory: 1 GB RAM')
        game = data['games'][0]
        self.assertNotIn('requirements_kind', game['platforms']['Windows']['recommended'])
        self.assertIsNone(game['rec_cpu_score'])
        self.assertEqual(review_catalog(data)['summary']['recommended']['needs_review'], 1)
        self.assertEqual(review_catalog(data)['summary']['notes_only']['recommended'], 0)

    def test_notes_only_flag_cannot_hide_a_hardware_score_or_a_partial_hardware_field(self):
        data = self.build()
        tampered = deepcopy(data)
        tampered['games'][0]['platforms']['Windows']['recommended']['requirements']['cpu_score'] = 100
        with self.assertRaisesRegex(ValueError, 'observações'):
            validate_catalog(tampered)
        data['games'][0]['platforms']['Windows']['recommended']['text'] = 'Memory: 1 GB RAM'
        with self.assertRaisesRegex(ValueError, 'observações'):
            validate_catalog(data)

    def test_l4d2_recommended_uses_a_scoped_reference_and_current_hardware_score(self):
        records = read_catalog(ROOT / 'data/catalog/hardware_manual_v1.csv', catalog_format='manual')
        index = {(r['component_type'], normalize_name(r['name'])): r for r in records}
        aliases = read_aliases(ROOT / 'data/catalog/hardware_aliases.json', index)
        rules = read_curation(ROOT / 'data/catalog/requirements_curation.json', index)
        rule = rules['550', 'Windows', 'recommended', 'GPU']
        index['GPU', normalize_name(rule['reference_models'][0])]['performance_score'] = 987
        html = ('OS: Windows 7<br>Processor: Intel core 2 duo 2.4GHz<br>Memory: 2 GB RAM'
                '<br>Graphics: ' + rule['expected_query'])
        original = process_requirements(html, index, aliases, catalog_format='manual')
        block = apply_curation(original, '550', 'Windows', 'recommended', rules, index, aliases)
        self.assertEqual(block['status'], 'resolved')
        self.assertEqual(block['requirements']['gpu_score'], 987)
        self.assertEqual(block['original_hardware']['GPU']['query'], rule['expected_query'])
        unrelated = apply_curation(original, '999999', 'Windows', 'recommended', rules, index, aliases)
        self.assertIsNone(unrelated['requirements']['gpu_score'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
