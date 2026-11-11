"""Avaliação por casos de ouro: o motor contra respostas escritas à mão, sem Neo4j nem Steam.

Cada caso (data/evaluation/gold_cases.json) liga um computador a um jogo e a um nível de
requisito, com o veredito esperado e o motivo. Os textos de requisitos são cópias das respostas
reais da Steam; as notas de hardware vêm do CSV versionado. O esperado não é derivado da saída
do motor. Uso (na pasta backend):

    python -m app.evaluate_gold            # imprime o relatório em Markdown
    python -m app.evaluate_gold --json     # resultado por caso, em JSON
"""

import argparse
import json
import sys

from .services.hardware import ROOT, MANUAL_SCORE_VERSION, matching_context
from .services.recommendation_engine import ENGINE_VERSION, describe_match
from .services.steam import Snapshot, normalize_game
from hardware_catalog import read_catalog

GOLD_PATH = ROOT / 'data/evaluation/gold_cases.json'
CATALOG_PATH = ROOT / 'data/catalog/hardware_manual_v1.csv'
OUTCOMES = {
    'correct': 'Acertou',
    'false_positive': 'Falso positivo (aprovou o que deveria reprovar)',
    'false_negative': 'Falso negativo (reprovou o que deveria aprovar)',
    'overconfident': 'Decidiu onde o esperado era pendência',
    'too_cautious': 'Ficou pendente onde o esperado era uma decisão',
    'wrong_checks': 'Veredito certo, mas as verificações por peça divergem',
}


def load_gold(path=GOLD_PATH):
    return json.loads(path.read_text(encoding='utf-8'))


def load_hardware():
    """Catálogo no formato da API, lido do CSV versionado (a API lê o mesmo conteúdo do Neo4j)."""
    hardware = {'CPU': [], 'GPU': [], 'score_version': MANUAL_SCORE_VERSION, 'source': 'csv'}
    for row in read_catalog(CATALOG_PATH, catalog_format='manual'):
        name = row['name']
        vendor = next((v for v in ('Intel', 'AMD', 'NVIDIA') if name.startswith(v + ' ')), 'Outro')
        hardware[row['component_type']].append({'id': name, 'name': name, 'vendor': vendor,
            'performance_score': row['performance_score'], 'score_version': MANUAL_SCORE_VERSION})
    return hardware


def load_games(gold, context):
    return {appid: normalize_game(Snapshot(item['steam'], {'source_url': item['source_url'], 'collected_at': item['collected_at']}), context)
            for appid, item in gold['games'].items()}


def outcome(expected, actual):
    if expected == actual:
        return 'correct'
    if actual == 'compatible':
        return 'false_positive' if expected == 'incompatible' else 'overconfident'
    if actual == 'incompatible':
        return 'false_negative' if expected == 'compatible' else 'overconfident'
    return 'too_cautious'


def evaluate(gold=None, hardware=None):
    gold = gold or load_gold()
    hardware = hardware or load_hardware()
    context = matching_context(hardware)
    games = load_games(gold, context)
    results = []
    for case in gold['cases']:
        machine = {**gold['machines'][case['machine']]}
        if case.get('windows_version'):
            machine['windowsVersion'] = case['windows_version']
        profile = {'anchorIds': [], 'genres': [], 'themes': [],
                   'hardware': {key: machine[key] for key in ('ramGb', 'os', 'windowsVersion')} | {'cpuId': machine['cpu'], 'gpuId': machine['gpu']}}
        game = games[case['game']]
        match = describe_match(profile, game, [game], hardware)
        assessment = match['assessments'][case['level']]
        checks = {check['label']: check['ok'] for check in assessment['checks']}
        result = outcome(case['expect'], assessment['compatibility'])
        bad = [label for label in case.get('failing_checks', []) if checks.get(label) is not False]
        bad += [label for label in case.get('ok_checks', []) if checks.get(label) is not True]
        if result == 'correct' and bad:
            result = 'wrong_checks'
        known = case.get('known_divergence')
        if result == 'correct':
            status = 'ok' if not known else 'known_fixed'
        else:
            status = 'known' if known and known['actual'] == assessment['compatibility'] and result != 'false_positive' else 'unexpected'
        results.append({'id': case['id'], 'kind': case['kind'], 'status': status,
                        'known_reason': known['reason'] if known else None, 'game': gold['games'][case['game']]['title'],
                        'machine': case['machine'], 'level': case['level'], 'expected': case['expect'],
                        'actual': assessment['compatibility'], 'outcome': result, 'checks': checks,
                        'divergent_checks': bad, 'why': case['why']})
    return results


def format_report(gold, results):
    total = len(results)
    counts = {key: sum(r['outcome'] == key for r in results) for key in OUTCOMES}
    known = sum(r['status'] == 'known' for r in results)
    unexpected = sum(r['status'] in ('unexpected', 'known_fixed') for r in results)
    lines = [f'# Avaliação por casos de ouro ({ENGINE_VERSION}, índice {MANUAL_SCORE_VERSION})', '',
             f'{counts["correct"]} de {total} casos corretos; {known} divergências conhecidas (documentadas no arquivo de casos); '
             f'{unexpected} inesperadas. Falsos positivos: {counts["false_positive"]}.', '',
             '| Resultado | Casos |', '| --- | ---: |']
    lines += [f'| {label} | {counts[key]} |' for key, label in OUTCOMES.items()]
    lines += ['', '| Tipo de caso | Corretos | Total |', '| --- | ---: | ---: |']
    for kind in sorted({r['kind'] for r in results}):
        rows = [r for r in results if r['kind'] == kind]
        lines.append(f'| {kind} | {sum(r["outcome"] == "correct" for r in rows)} | {len(rows)} |')
    lines += ['', '| Caso | Jogo | Nível | Esperado | Obtido | Resultado |', '| --- | --- | --- | --- | --- | --- |']
    for r in results:
        label = 'ok' if r['outcome'] == 'correct' else OUTCOMES[r['outcome']] + (' (conhecida)' if r['status'] == 'known' else '')
        lines.append(f'| {r["id"]} | {r["game"]} | {r["level"]} | {r["expected"]} | {r["actual"]} | {label} |')
    for r in results:
        if r['outcome'] != 'correct':
            lines += ['', f'### {r["id"]}', f'- Esperado: {r["expected"]}; obtido: {r["actual"]}.', f'- Verificações: {r["checks"]}',
                      f'- Motivo do esperado: {r["why"]}']
            if r['known_reason']:
                lines.append(f'- Causa conhecida: {r["known_reason"]}')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--json', action='store_true', help='imprime o resultado de cada caso em JSON')
    args = parser.parse_args(argv)
    gold = load_gold()
    results = evaluate(gold)
    print(json.dumps(results, ensure_ascii=False, indent=2) if args.json else format_report(gold, results))
    return 0 if all(r['status'] in ('ok', 'known') for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
