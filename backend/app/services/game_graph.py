"""Lê o catálogo Game/Genre/Tag e reavalia requisitos com o hardware atual."""

import json

from .hardware import requirements_block

QUERY = """
MATCH (c:Game)
WHERE c.catalog_format = $format AND (size($ids) = 0 OR c.id IN $ids)
  AND NOT c.id IN $excluded
OPTIONAL MATCH (c)-[:HAS_GENRE]->(genre:Genre)
WITH c, collect(DISTINCT genre.name) AS genres
OPTIONAL MATCH (c)-[:HAS_TAG]->(tag:Tag)
WITH c, genres, collect(DISTINCT tag.name) AS tags
OPTIONAL MATCH (a:Game)-[:HAS_GENRE|HAS_TAG]->(facet)<-[:HAS_GENRE|HAS_TAG]-(c)
WHERE a.id IN $anchors
WITH c, genres, tags, collect(DISTINCT facet.name) AS shared
WHERE NOT $related OR size(shared) > 0
   OR any(name IN genres WHERE name IN $genres)
   OR any(name IN tags WHERE name IN $tags)
RETURN c.id AS id, c.catalog_json AS catalog_json, genres, tags, shared
ORDER BY size(shared) DESC, c.title, c.id
LIMIT $limit
"""


def read_graph_games(driver, database, *, ids=(), anchors=(), genres=(), tags=(), related=False):
    with driver.session(database=database, default_access_mode="READ") as session:
        rows = session.execute_read(lambda tx: tx.run(QUERY, format="steam_games_v1", ids=list(ids),
            excluded=list(anchors) if related else [], anchors=list(anchors), genres=list(genres),
            tags=list(tags), related=related, limit=30 if related else 250).data())
    result = []
    for row in rows:
        raw = row.get("catalog_json")
        if not isinstance(raw, str):
            continue
        game = json.loads(raw)
        if (not isinstance(game, dict) or game.get("id") != row.get("id")
            or not isinstance(game.get("title"), str) or not isinstance(game.get("platforms"), dict)):
            raise ValueError("Registro de jogo inválido no Neo4j.")
        game["genres"] = row["genres"]
        game["themes"] = row["tags"]
        game["themes_status"] = "classified"
        game["catalog_source"] = "neo4j"
        game["shared_facets"] = row["shared"]
        result.append(game)
    return result


def refresh_requirements(game, context):
    """O texto preservado evita servir notas de hardware antigas do snapshot."""
    for platform in game["platforms"].values():
        for level in ("minimum", "recommended"):
            block = platform.get(level)
            if isinstance(block, dict):
                platform[level] = requirements_block(block.get("text"), context)
    for level, prefix in (("minimum", "min"), ("recommended", "rec")):
        block = game["platforms"].get("Windows", {}).get(level)
        requirements = block["requirements"] if block else {}
        game.update({f"{prefix}_{field}": requirements.get(field) for field in ("ram_gb", "cpu_score", "gpu_score")})
    game["hardware_source"] = {key: context[key] for key in ("catalog_sha256", "aliases_sha256", "hardware_sha256")} if context else None
    return game
