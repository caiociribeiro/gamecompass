"""Regressões offline de grafias e requisitos legados.

Os cenários são fixtures; não substituem os snapshots coletados no ambiente local.
"""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from fetch_steam import save_snapshot
from game_catalog import ROOT, build_catalog
from hardware_catalog import read_catalog
from hardware_matcher import match_alternatives, match_hardware, normalize_name, read_aliases
from process_requirements import process_requirements
from regex_parser import extract_ram_gb, normalize_ram_gb
from requirements_curation import apply_curation, read_curation, validate_curated_block
from review_game_requirements import main as review_main, review_catalog


class RequirementVariationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records = read_catalog(ROOT / 'data/catalog/hardware_manual_v1.csv', catalog_format='manual')
        cls.index = {(r['component_type'], normalize_name(r['name'])): r for r in records}
        cls.aliases = read_aliases(ROOT / 'data/catalog/hardware_aliases.json', cls.index)
        cls.rules = read_curation(ROOT / 'data/catalog/requirements_curation.json', cls.index)

    def match(self, query, kind='GPU', catalog=None):
        return match_hardware(query, kind, self.index if catalog is None else catalog,
                              self.aliases, catalog_format='manual')

    def process(self, appid, level, html, catalog=None):
        catalog = self.index if catalog is None else catalog
        original = process_requirements(html, catalog, self.aliases, catalog_format='manual')
        return apply_curation(original, appid, 'Windows', level, self.rules, catalog, self.aliases)

    def test_editorial_gpu_label_preserves_model_query_and_current_catalog_score(self):
        catalog = deepcopy(self.index)
        catalog['GPU', normalize_name('NVIDIA GeForce GTX 660')]['performance_score'] = 987
        for query in ('Nvidia GPU GeForce GTX 660', '  Nvidia GPU GeForce GTX 660  '):
            result = self.match(query, catalog=catalog)
            self.assertEqual(result['query'], query)
            self.assertEqual(result['name'], 'NVIDIA GeForce GTX 660')
            self.assertEqual(result['performance_score'], 987)
            self.assertEqual(result['method'], 'normalized')

    def test_cpu_editorial_label_and_ascii_trademarks_do_not_change_sku(self):
        for query in ('Intel CPU Core i5-8400', 'Intel(R) Core(TM) i5-8400'):
            with self.subTest(query=query):
                self.assertEqual(self.match(query, 'CPU')['name'], 'Intel Core i5-8400')

    def test_vendor_label_cleanup_does_not_remove_vram_suffix_or_cross_component_type(self):
        self.assertEqual(self.match('NVIDIA GPU GeForce RTX 3050 6GB')['name'], 'NVIDIA GeForce RTX 3050 6GB')
        for query in ('NVIDIA GPU GeForce RTX 3050 4GB', 'NVIDIA GPU GeForce GTX 660 Ti 9GB',
                      'NVIDIA CPU GeForce GTX 660', 'NVIDIA GPU GeForce GTX 660 Laptop'):
            with self.subTest(query=query):
                self.assertEqual(self.match(query)['status'], 'not_found')
        self.assertEqual(self.match('NVIDIA GPU GeForce GTX 660', 'CPU')['status'], 'not_found')

    def test_and_higher_is_a_qualifier_and_does_not_complete_an_unknown_family(self):
        result = match_alternatives('Intel HD Graphics 4000 and higher, ATI Radeon HD-Series 4650 and higher',
                                    'GPU', self.index, self.aliases, catalog_format='manual')
        self.assertEqual(result['alternatives'][0]['name'], 'Intel HD Graphics 4000')
        self.assertEqual(result['alternatives'][1]['status'], 'not_found')
        self.assertIsNone(result['required_score'])
        self.assertEqual(result['status'], 'needs_review')

    def test_ram_of_ram_is_supported_only_in_the_memory_field(self):
        self.assertEqual(normalize_ram_gb('256 MB of RAM'), 1)
        self.assertEqual(extract_ram_gb('Memory: 512 MB of RAM<br>Graphics: 8 GB'), 1)
        self.assertIsNone(extract_ram_gb('Graphics: 512 MB of RAM'))
        with self.assertRaises(ValueError):
            extract_ram_gb('Memory: 256 MB of RAM or 512 MB of RAM')

    def test_little_nightmares_minimum_and_recommended_resolve_separately(self):
        for level, cpu, gpu, ram in [('minimum', 'Intel CPU Core i3', 'Nvidia GTX 460', 4),
                                    ('recommended', 'Intel CPU Core i7', 'Nvidia GPU GeForce GTX 660', 8)]:
            html = f'OS: Windows 7, 64-bit<br>Processor: {cpu}<br>Memory: {ram} GB RAM<br>Graphics: {gpu}'
            block = self.process('424840', level, html)
            self.assertEqual(block['status'], 'resolved')
            self.assertEqual(block['requirements']['ram_gb'], ram)
            self.assertEqual(block['requirements']['gpu_score'], 8 if level == 'minimum' else 15)
            self.assertEqual(block['hardware']['GPU']['alternatives'][0]['query'], gpu)
            validate_curated_block(block, self.index)

    def test_little_nightmares_does_not_use_csv_score_for_a_missing_or_pending_gpu(self):
        html = 'OS: Windows 7<br>Processor: Intel CPU Core i7<br>Memory: 8 GB RAM<br>Graphics: Nvidia GPU GeForce GTX 660'
        for remove in (False, True):
            catalog = deepcopy(self.index)
            key = 'GPU', normalize_name('NVIDIA GeForce GTX 660')
            if remove:
                del catalog[key]
            else:
                catalog[key]['performance_score'] = None
            block = self.process('424840', 'recommended', html, catalog)
            self.assertIsNone(block['requirements']['gpu_score'])
            self.assertEqual(block['status'], 'needs_review')

    def test_reviewed_translations_match_only_their_original_game_and_level(self):
        rule = self.rules['212680', 'Windows', 'minimum', 'GPU']
        for query in [rule['expected_query'], *rule['query_variants']]:
            html = f'OS: Windows XP / Vista / 7<br>Processor: 2 GHz<br>Memory: 1 GB RAM<br>Graphics: {query}'
            block = self.process('212680', 'minimum', html)
            self.assertEqual(block['status'], 'resolved')
            self.assertEqual(block['curation'][-1]['original_query'], query)
            validate_curated_block(block, self.index)
            for appid, level in [('212680', 'recommended'), ('999999', 'minimum')]:
                unrelated = self.process(appid, level, html)
                self.assertIsNone(unrelated['requirements']['gpu_score'])

    def test_changed_or_unreviewed_translation_stays_pending(self):
        html = 'OS: Windows 10<br>Processor: 2 GHz<br>Memory: 1 GB RAM<br>Graphics: descrição diferente da revisada'
        self.assertIsNone(self.process('212680', 'minimum', html)['requirements']['gpu_score'])

    def test_legacy_rules_keep_original_queries_and_fractional_ram(self):
        for level, cpu, ram in [('minimum', '1.0 GHz Pentium(R) III and AMD Athlon(tm)', '256 MB of RAM'),
                                ('recommended', '2.0 GHz Pentium(R) IV and AMD Athlon(tm)', '512 MB of RAM')]:
            rule = self.rules['3830', 'Windows', level, 'GPU']
            html = f'OS: Windows 98 SE/2000/XP<br>Processor: {cpu}<br>Memory: {ram}<br>Graphics: {rule["expected_query"]}'
            block = self.process('3830', level, html)
            self.assertEqual(block['status'], 'resolved')
            self.assertEqual(block['requirements']['ram_gb'], 1)
            self.assertEqual(len(block['curation']), 2)
            self.assertEqual(block['original_hardware']['CPU']['query'], cpu)
            validate_curated_block(block, self.index)

    def test_query_variants_reject_malformed_or_duplicate_entries(self):
        original = deepcopy(self.rules['212680', 'Windows', 'minimum', 'GPU'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'curation.json'
            for values in (None, 'not a list', [''], [original['expected_query']], [5], ['a'] * 6):
                row = {**original, 'query_variants': values}
                path.write_text(json.dumps({'schema_version': 'gamecompass_requirements_curation_v1', 'rules': [row]}))
                with self.subTest(values=values), self.assertRaises(ValueError):
                    read_curation(path, self.index)


class CoverageSummaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.selection = self.root / 'selection.json'
        self.selection.write_text(json.dumps({'schema_version': 'steam_games_v1', 'tag_vocabulary': ['Fantasia'],
            'games': [{'id': '999001', 'tags': ['Fantasia'], 'curation_notes': 'Jogo inventado de teste.'}]}))

    def build(self, html):
        import hashlib
        raw = json.dumps({'999001': {'success': True, 'data': {'type': 'game', 'steam_appid': 999001,
            'name': 'Fixture de revisão', 'is_free': True, 'genres': [{'description': 'Indie'}],
            'platforms': {'windows': True, 'mac': False, 'linux': False},
            'pc_requirements': {'minimum': html}}}}).encode()
        save_snapshot(self.root / 'raw/999001', raw, {'appid': '999001', 'title': 'Fixture de revisão',
            'source_url': 'https://store.steampowered.com/api/appdetails?appids=999001',
            'response_sha256': hashlib.sha256(raw).hexdigest(), 'country': 'br', 'language': 'portuguese',
            'collected_at': '2026-10-31T12:00:00Z'})
        return build_catalog(self.root / 'raw', self.selection, ROOT / 'data/catalog/hardware_manual_v1.csv',
                             ROOT / 'data/catalog/hardware_aliases.json')

    def test_summary_distinguishes_missing_ram_and_gpu_from_an_unknown_cpu(self):
        data = self.build('OS: Windows 10<br>Processor: processador fixture desconhecido')
        result = review_catalog(data)
        fields = result['games'][0]['minimum']['blocking_fields']
        self.assertEqual(fields, [{'field': 'CPU', 'reason': 'unidentified'},
                                  {'field': 'GPU', 'reason': 'not_provided'},
                                  {'field': 'RAM', 'reason': 'not_provided'}])
        self.assertEqual(result['games'][0]['recommended']['status'], 'not_provided')

    def test_invalid_ram_is_not_reported_as_omitted_by_the_source(self):
        data = self.build('OS: Windows 10<br>Processor: AMD Ryzen 5 3600<br>Memory: 8/16 GB RAM<br>Graphics: NVIDIA GeForce GTX 660')
        self.assertEqual(review_catalog(data)['games'][0]['minimum']['blocking_fields'],
                         [{'field': 'RAM', 'reason': 'unparsed'}])

    def test_cli_can_show_pending_fields_without_creating_an_extra_file(self):
        data = self.build('OS: Windows 10<br>Processor: AMD Ryzen 5 3600<br>Graphics: NVIDIA GeForce GTX 660')
        source = self.root / 'processed.json'
        source.write_text(json.dumps(data))
        before = source.read_bytes(), set(self.root.iterdir())
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(review_main(['--input', str(source)]), 0)
        result = json.loads(output.getvalue())
        self.assertNotIn('output', result)
        self.assertEqual(result['pending_games'][0]['levels'],
                         {'minimum': [{'field': 'RAM', 'reason': 'not_provided'}]})
        self.assertEqual((source.read_bytes(), set(self.root.iterdir())), before)

    def test_absent_recommended_is_not_listed_as_a_defective_level(self):
        data = self.build('OS: Windows 10<br>Processor: AMD Ryzen 5 3600<br>Memory: 8 GB RAM<br>Graphics: NVIDIA GeForce GTX 660')
        source = self.root / 'processed.json'
        source.write_text(json.dumps(data))
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(review_main(['--input', str(source)]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result['pending_games'], [])
        self.assertEqual(result['recommended']['not_provided'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
