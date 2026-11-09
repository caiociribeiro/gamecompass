"""Avaliação offline do motor rules_v1 sobre o catálogo carregado no Neo4j.

Uso (somente leitura no banco):
  docker compose run --rm --no-deps -v ./backend/app:/app/app api python -m app.evaluate_rules
  docker compose run --rm --no-deps -v ./backend/app:/app/app api python -m app.evaluate_rules --auto 60 --top 10 --json

Os cenários podem vir de um arquivo (--scenarios) ou ser gerados de forma
determinística a partir do próprio catálogo (--auto). Cenários automáticos são
SIMULAÇÕES: âncoras sorteadas com semente fixa e hardware escolhido por faixa
(percentil) entre as peças reais do índice. Não representam usuários reais.
"""

import argparse
import json
import random
import sys
from collections import Counter

from neo4j import GraphDatabase
from pydantic import ValidationError

from .core.config import settings
from .schemas.recommendations import RecommendationInput
from .services.affinity import title_key
from .services.game_graph import read_graph_games, refresh_requirements
from .services.hardware import matching_context, read_hardware
from .services.recommendation_engine import ENGINE_VERSION, MIN_AFFINITY, anchors_of, build_recommendations, profile_ready

GROUPS = ('items', 'pending', 'excluded')
# Faixa de hardware: nome, percentil entre as peças com nota, RAM em GB (premissa da simulação).
TIERS = (('baixo', 0.20, 8), ('medio', 0.50, 16), ('alto', 0.85, 32))
BINS = ((MIN_AFFINITY, 39), (40, 49), (50, 59), (60, 69), (70, 79), (80, 89), (90, 100))


def hardware_tiers(hardware):
    """Escolhe CPU e GPU reais por percentil de nota; peças sem nota são ignoradas."""
    picked = {}
    for kind in ('CPU', 'GPU'):
        scored = sorted((p for p in hardware[kind] if type(p.get('performance_score')) is int and p['performance_score'] > 0),
                        key=lambda p: (p['performance_score'], p['name']))
        if not scored:
            raise ValueError(f'Não há peças de {kind} com nota no catálogo de hardware.')
        picked[kind] = scored
    return {name: {'cpuId': picked['CPU'][round((len(picked['CPU']) - 1) * pct)]['id'],
                   'gpuId': picked['GPU'][round((len(picked['GPU']) - 1) * pct)]['id'],
                   'ramGb': ram, 'os': 'Windows', 'windowsVersion': '11'}
            for name, pct, ram in TIERS}


def auto_scenarios(games, hardware, count, seed):
    """Perfis simulados: 3 âncoras sorteadas; gêneros e temáticas = união das âncoras."""
    eligible = sorted((g for g in games if g['genres'] and g['themes'] and g['themes_status'] == 'classified'),
                      key=lambda g: g['id'])
    if len(eligible) < 3:
        raise ValueError('São necessários ao menos 3 jogos classificados para sortear âncoras.')
    rng, tiers, scenarios = random.Random(seed), hardware_tiers(hardware), []
    for index in range(count):
        anchors = rng.sample(eligible, 3)
        tier = TIERS[index % len(TIERS)][0]
        scenarios.append({'name': f'auto-{index + 1:03d}', 'tier': tier,
            'anchorIds': [a['id'] for a in anchors],
            'genres': sorted({x for a in anchors for x in a['genres']})[:20],
            'themes': sorted({x for a in anchors for x in a['themes']})[:20],
            'hardware': tiers[tier]})
    return scenarios


def read_scenarios(path):
    """Valida cada cenário com o mesmo contrato da API; erro explícito em vez de resultado vazio."""
    with open(path, encoding='utf-8') as handle:
        raw = json.load(handle)
    rows = raw.get('scenarios') if isinstance(raw, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError('O arquivo deve ter {"scenarios": [...]} com ao menos um cenário.')
    scenarios = []
    for position, row in enumerate(rows, 1):
        try:
            profile = RecommendationInput(**{k: row.get(k) for k in ('anchorIds', 'genres', 'themes', 'hardware')}).model_dump()
        except (ValidationError, AttributeError) as exc:
            raise ValueError(f'Cenário {position} inválido: {exc}') from exc
        scenarios.append({'name': row.get('name') or f'cenario-{position:03d}', 'tier': row.get('tier'), **profile})
    return scenarios


def evaluate_scenario(scenario, games, hardware, top_n):
    user = {k: scenario[k] for k in ('anchorIds', 'genres', 'themes', 'hardware')}
    if not profile_ready(user, games, hardware):
        raise ValueError(f"{scenario['name']}: perfil incompleto ou com peça/âncora fora do catálogo; o motor devolveria vazio.")
    result = build_recommendations(user, games, hardware)
    ranked = sorted((m for group in GROUPS for m in result[group]),
                    key=lambda m: (-m['affinity'], title_key(m['game']['title']), m['game']['id']))
    candidates = len(games) - len(anchors_of(user, games))
    counts = {group: len(result[group]) for group in GROUPS}
    return {'name': scenario['name'], 'tier': scenario.get('tier'), 'anchorIds': user['anchorIds'],
        'counts': counts, 'below_cut': candidates - sum(counts.values()),
        'affinities': [m['affinity'] for m in ranked],
        'top_items': [{'id': m['game']['id'], 'title': m['game']['title'], 'affinity': m['affinity'],
                       'meets': m['meets']} for m in result['items'][:top_n]]}


def mean(values):
    return round(sum(values) / len(values), 2) if values else 0


def summarize(results, catalog_size):
    affinities = [a for r in results for a in r['affinities']]
    histogram = [{'range': f'{low}-{high}', 'count': sum(low <= a <= high for a in affinities)} for low, high in BINS]
    shown = Counter((i['id'], i['title']) for r in results for i in r['top_items'])
    def stats(rows):
        return {group: {'mean': mean([r['counts'][group] for r in rows]),
                        'min': min(r['counts'][group] for r in rows), 'max': max(r['counts'][group] for r in rows)}
                for group in GROUPS}
    tiers = sorted({r['tier'] for r in results if r['tier']})
    return {'scenarios': len(results), 'counts': stats(results),
        'by_tier': {t: stats([r for r in results if r['tier'] == t]) for t in tiers},
        'without_items': sum(r['counts']['items'] == 0 for r in results),
        'below_cut_mean': mean([r['below_cut'] for r in results]),
        'affinity_histogram': histogram, 'affinity_mean': mean(affinities),
        'top_coverage': {'distinct_games': len(shown), 'catalog_size': catalog_size},
        'most_recommended': [{'id': k[0], 'title': k[1], 'appearances': n}
                             for k, n in sorted(shown.items(), key=lambda kv: (-kv[1], title_key(kv[0][1]), kv[0][0]))[:5]]}


def format_report(meta, summary, results, top_n):
    lines = [f"Avaliação do motor {meta['engine_version']} (corte de afinidade {meta['minimum_affinity']})",
        f"Catálogo: {meta['catalog_size']} jogos | cenários: {summary['scenarios']} | origem: {meta['scenario_source']}",
        f"hardware_sha256={meta['hardware_sha256']} curation_sha256={meta['curation_sha256']}", '',
        'Grupos por cenário (média [mín–máx]):']
    for group in GROUPS:
        s = summary['counts'][group]
        lines.append(f"  {group:<9} {s['mean']:>6} [{s['min']}–{s['max']}]")
    lines.append(f"  abaixo do corte (média): {summary['below_cut_mean']} | cenários sem nenhum item: {summary['without_items']}")
    if summary['by_tier']:
        lines += ['', 'Por faixa de hardware (itens / pendentes / excluídos, médias):']
        for tier, s in summary['by_tier'].items():
            lines.append(f"  {tier:<6} {s['items']['mean']} / {s['pending']['mean']} / {s['excluded']['mean']}")
    lines += ['', f"Distribuição de afinidade (média {summary['affinity_mean']}):"]
    total = sum(b['count'] for b in summary['affinity_histogram']) or 1
    for b in summary['affinity_histogram']:
        lines.append(f"  {b['range']:>7} {b['count']:>6} {'#' * round(40 * b['count'] / total)}")
    c = summary['top_coverage']
    lines += ['', f"Cobertura do top-{top_n}: {c['distinct_games']} de {c['catalog_size']} jogos aparecem em algum cenário.",
              'Mais recomendados:'] + [f"  {m['appearances']:>4}x {m['title']} ({m['id']})" for m in summary['most_recommended']]
    lines += ['', f'Top-{top_n} por cenário:']
    for r in results:
        head = ', '.join(f"{i['title']} ({i['affinity']})" for i in r['top_items']) or 'nenhum item compatível'
        lines.append(f"  {r['name']} [{r['tier'] or '-'}] {r['counts']['items']}/{r['counts']['pending']}/{r['counts']['excluded']}: {head}")
    return '\n'.join(lines)


def load_catalog(driver, database):
    hardware = read_hardware(driver, database)
    context = matching_context(hardware)
    games = [refresh_requirements(g, context) for g in read_graph_games(driver, database)]
    return hardware, context, games


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--scenarios', help='JSON {"scenarios": [{anchorIds, genres, themes, hardware}]}')
    parser.add_argument('--auto', type=int, default=30, help='nº de cenários simulados quando não há --scenarios (padrão 30)')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--top', type=int, default=5)
    parser.add_argument('--json', action='store_true', help='saída em JSON')
    args = parser.parse_args(argv)
    if args.auto < 1 or args.top < 1:
        parser.error('--auto e --top devem ser maiores que zero.')
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password), connection_timeout=5)
    try:
        hardware, context, games = load_catalog(driver, settings.neo4j_database)
        if not games:
            raise ValueError('Nenhum jogo no Neo4j. Carregue o catálogo antes de avaliar.')
        scenarios = read_scenarios(args.scenarios) if args.scenarios else auto_scenarios(games, hardware, args.auto, args.seed)
        results = [evaluate_scenario(s, games, hardware, args.top) for s in scenarios]
    except Exception as exc:  # noqa: BLE001 - mensagem única e código de saída para o terminal
        print(f'Erro na avaliação ({type(exc).__name__}): {exc}', file=sys.stderr)
        return 1
    finally:
        driver.close()
    source = f'arquivo {args.scenarios}' if args.scenarios else f'simulação (semente {args.seed})'
    meta = {'engine_version': ENGINE_VERSION, 'minimum_affinity': MIN_AFFINITY, 'catalog_size': len(games),
        'scenario_source': source, 'hardware_sha256': context['hardware_sha256'], 'curation_sha256': context['curation_sha256']}
    summary = summarize(results, len(games))
    if args.json:
        print(json.dumps({'meta': meta, 'summary': summary, 'scenarios': results}, ensure_ascii=False, indent=2))
    else:
        print(format_report(meta, summary, results, args.top))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
