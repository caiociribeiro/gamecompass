"""Afinidade por preferências e Jaccard das âncoras; regras preservadas do TCC1."""

import math
import unicodedata


def ordered_sum(values):
    # Python 3.12 usa soma compensada; a regra original usa reduce sequencial.
    # A mesma ordem preserva o arredondamento nos limites de meio ponto.
    total = 0
    for value in values:
        total += value
    return total


def fold(value):
    return ''.join(char for char in unicodedata.normalize('NFD', value)
                   if not unicodedata.combining(char)).lower()


def key(value):
    return fold(' '.join(value.split()))


def title_key(value):
    # Desempate textual estável, independente do locale instalado no contêiner.
    return fold(value), value.lower(), value


def unique(values):
    return list({key(value): value.strip() for value in values}.values())


def shared(values, selected):
    wanted = {key(value) for value in selected}
    return [value for value in unique(values) if key(value) in wanted]


def facet_similarity(left, right):
    a, b = {key(v) for v in left}, {key(v) for v in right}
    return len(a & b) / len(a | b) if a | b else 0


def preference_coverage(values, selected):
    wanted = unique(selected)
    return len(shared(values, wanted)) / len(wanted) if wanted else 0


def anchor_aggregate(values):
    ordered = sorted(values, reverse=True)[:3]
    weights = [0.6, 0.25, 0.15][:len(ordered)]
    return ordered_sum(v * w for v, w in zip(ordered, weights)) / ordered_sum(weights) if weights else 0


def content_affinity(user, game, anchors):
    genres = shared(game['genres'], user['genres'])
    themes = shared(game['themes'], user['themes']) if game['themes_status'] == 'classified' else []
    genre_anchors = [a for a in anchors if a['genres']]
    theme_anchors = [a for a in anchors if a['themes_status'] == 'classified' and a['themes']]
    same_studio = next((a for a in anchors if a['id'] != game['id'] and key(a['developer']) == key(game['developer'])), None) if game['developer'].strip() else None
    components = []
    if game['genres'] and user['genres']:
        components.append((preference_coverage(game['genres'], user['genres']), 0.4))
    if game['genres'] and genre_anchors:
        components.append((anchor_aggregate([facet_similarity(game['genres'], a['genres']) for a in genre_anchors]), 0.25))
    if game['developer'].strip() and any(a['developer'].strip() for a in anchors):
        components.append((1 if same_studio else 0, 0.05))
    if game['themes_status'] == 'classified' and game['themes'] and user['themes']:
        components.append((preference_coverage(game['themes'], user['themes']), 0.15))
    if game['themes_status'] == 'classified' and game['themes'] and theme_anchors:
        components.append((anchor_aggregate([facet_similarity(game['themes'], a['themes']) for a in theme_anchors]), 0.15))
    total = ordered_sum(weight for _, weight in components)
    affinity = math.floor(100 * ordered_sum(value * weight for value, weight in components) / total + 0.5) if total else 0
    matches = []
    for anchor in anchors:
        common_genres = shared(game['genres'], anchor['genres'])
        common_themes = shared(game['themes'], anchor['themes']) if game['themes_status'] == anchor['themes_status'] == 'classified' else []
        factors = []
        if game['genres'] and anchor['genres']:
            factors.append((facet_similarity(game['genres'], anchor['genres']), 0.25))
        if game['themes_status'] == anchor['themes_status'] == 'classified' and game['themes'] and anchor['themes']:
            factors.append((facet_similarity(game['themes'], anchor['themes']), 0.15))
        weight = ordered_sum(w for _, w in factors)
        if common_genres or common_themes:
            matches.append({'id': anchor['id'], 'title': anchor['title'], 'genres': common_genres, 'themes': common_themes,
                'similarity': ordered_sum(v * w for v, w in factors) / weight if weight else 0})
    matches.sort(key=lambda a: (-a['similarity'], title_key(a['title']), a['id']))
    reasons = []
    if genres:
        reasons.append(f"Gêneros do perfil: {', '.join(genres)}.")
    if themes:
        reasons.append(f"Temáticas do perfil: {', '.join(themes)}.")
    for anchor in matches[:2]:
        reasons.append(f"Em comum com {anchor['title']}: {', '.join(unique(anchor['genres'] + anchor['themes'])[:4])}.")
    if same_studio:
        reasons.append(f"Mesmo estúdio de {same_studio['title']}.")
    return {'affinity': max(0, min(100, affinity)), 'reasons': reasons, 'anchorMatches': matches, 'preferredGenres': genres}
