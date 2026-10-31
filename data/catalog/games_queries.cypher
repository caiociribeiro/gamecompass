// Execute uma consulta por vez em http://localhost:7474.
// Quantidade de jogos, gêneros e tags do banco.
MATCH (n)
WHERE n:Game OR n:Genre OR n:Tag
RETURN labels(n) AS labels, count(*) AS total;

// Vizinhos do Cyberpunk 2077.
MATCH (g:Game {id:'1091500'})-[r:HAS_GENRE|HAS_TAG]->(category)
RETURN g, r, category;

// Jogos relacionados por gênero ou temática (não recomenda hardware).
MATCH (anchor:Game {id:'1091500'})-[:HAS_GENRE|HAS_TAG]->(category)
      <-[:HAS_GENRE|HAS_TAG]-(candidate:Game)
WHERE candidate.id <> anchor.id
RETURN candidate.id AS id, candidate.title AS title,
       collect(DISTINCT category.name) AS shared
ORDER BY size(shared) DESC, title
LIMIT 20;

// Mínimos e recomendados planos, correspondentes ao Windows.
MATCH (g:Game)
RETURN g.id, g.title, g.min_ram_gb, g.min_cpu_score, g.min_gpu_score,
       g.rec_ram_gb, g.rec_cpu_score, g.rec_gpu_score
ORDER BY g.title;

// Peças que ainda precisam de classificação.
MATCH (h)
WHERE (h:CPU OR h:GPU) AND h.score_version='manual_v1'
  AND h.performance_score IS NULL
RETURN labels(h) AS type, h.name AS name
ORDER BY type, name;
