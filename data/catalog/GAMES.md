# Catálogo de jogos e relações

## O que é versionado

`games.json` contém a seleção de 20 AppIDs, o vocabulário de temáticas e
uma justificativa editorial por jogo. Nomes, gêneros, requisitos, preços
e capas vêm da coleta real de `appdetails`, em português e região BR.
As tags representam a curadoria do GameCompass; não são apresentadas como
tags da comunidade Steam. Os recursos de `categories` não substituem
as preferências originais da interface.

| AppID | Jogo da seleção |
| --- | --- |
| 1091500 | Cyberpunk 2077 |
| 1174180 | Red Dead Redemption 2 |
| 292030 | The Witcher 3 |
| 1245620 | Elden Ring |
| 1086940 | Baldur's Gate 3 |
| 413150 | Stardew Valley |
| 367520 | Hollow Knight |
| 1145360 | Hades |
| 620 | Portal 2 |
| 105600 | Terraria |
| 504230 | Celeste |
| 588650 | Dead Cells |
| 646570 | Slay the Spire |
| 990080 | Hogwarts Legacy |
| 275850 | No Man's Sky |
| 782330 | DOOM Eternal |
| 2050650 | Resident Evil 4 |
| 813780 | Age of Empires II: Definitive Edition |
| 227300 | Euro Truck Simulator 2 |
| 289070 | Civilization VI |

## Fluxo de execução

1. `fetch_games.py`: coleta a seleção; cada AppID tem resposta original,
   metadata, URL, data e SHA-256. `--resume` aproveita snapshots válidos
   do mesmo lote. Uma falha parcial retorna código 2 e registra as pendências.
2. `process_games.py`: valida identidade e hashes; reutiliza parser e
   matching manual para mínimos e recomendados, separando Windows,
   macOS e Linux. Salva JSON de forma atômica e preserva os arquivos raw.
3. `load_games.py`: valida o JSON, os arquivos atuais e o hardware no
   Neo4j; depois grava jogos e relações em uma transação. `--dry-run`
   valida os arquivos sem abrir conexão com o banco.
4. A API lê os jogos do grafo; para cada resposta, refaz o matching do
   texto preservado contra as notas atuais do hardware do Neo4j.
5. O botão de sugestões consulta candidatos por relações comuns com as
   âncoras e pelas preferências. A afinidade e a separação de restrições
   continuam no navegador; as temáticas classificadas agora participam.

Não há jogo escolhido automaticamente para o perfil. Buscar nomes continua
consultando a Steam; escolher um jogo catalogado aproveita o Neo4j.
Se o catálogo não tiver candidatos ou estiver indisponível, a API pode
usar os mais vendidos da Steam e informa essa troca na resposta/interface.
Os vinte jogos são uma base inicial limitada; o grafo não busca todos os
similares existentes na loja.

## Contrato do grafo

```cypher
(:Game {id: '1091500'})-[:HAS_GENRE]->(:Genre {name: 'RPG'})
(:Game {id: '1091500'})-[:HAS_TAG]->(:Tag {name: 'Mundo aberto'})
```

Há constraints de unicidade em `Game.id`, `Genre.name` e `Tag.name`.
As de `CPU.name` e `GPU.name` continuam sob responsabilidade da carga
de hardware. Não são criados nós de RAM ou sistema operacional.

`Game` mantém `id` string, `title`, `price` em reais e os seis campos
`min_ram_gb`, `min_cpu_score`, `min_gpu_score`, `rec_ram_gb`,
`rec_cpu_score`, `rec_gpu_score`. Os campos planos correspondem a
**Windows**; o JSON preservado em `catalog_json` mantém as três plataformas.
Preços e requisitos ausentes são nulos: Neo4j omite essas propriedades,
sem tratar ausência como gratuidade ou requisito zero. `price` é o preço
da coleta, sujeito a mudança. Jogos gratuitos têm `price: 0.0`.

Proveniência adicional em `Game`: `catalog_format`, `score_version`,
`source_url`, `collected_at`, hashes de hardware, CSV, aliases e seleção.
`catalog_json` preserva os detalhes necessários à API. Não há relações
diretas entre jogos e peças nesta etapa: a comparação usa suas classes.

## Repetição e preservação

`MERGE` usa AppID para jogos e nome para gêneros/tags. Repetir a carga
conserva a quantidade de nós e relações. Para os jogos presentes no lote,
o script substitui somente relações cuja propriedade
`source = 'gamecompass_catalog_v1'`. Relações de outras origens e jogos
omitidos são preservados. Nós de gêneros/tags antigos podem ficar sem
relações; o script não os apaga. Não há limpeza geral do banco.

Uma falha de escrita reverte a transação de dados inteira. Constraints
são criadas antes, em transação separada. Se existirem duplicatas antigas,
a criação da constraint falhará e os dados precisam ser revisados antes.
Hardware divergente causa interrupção antes da gravação de jogos.

## Estado verificado

No teste de 30/10/2026, o lote gerou 20 jogos, seis gêneros, dez tags,
44 relações HAS_GENRE e 48 HAS_TAG. Esses números podem mudar com novas
respostas da Steam ou alterações na curadoria. A segunda carga conservou
as quantidades. Os testes de integração verificam rollback, idempotência,
atualização de tags, preservação de relações externas e notas antigas.

Nesta coleta, nenhum dos vinte jogos teve RAM, CPU e GPU completamente
resolvidas nos mínimos do Windows. O grafo de conteúdo funciona mesmo
assim; isso não conclui a validação de hardware.
A lista das 20 peças sem nota está em
[HARDWARE_REVIEW_2026_10.md](HARDWARE_REVIEW_2026_10.md).
Textos vagos como CPU de dois núcleos não escolhem um modelo por aproximação.

## Limites atuais da validação

Versão do SO, VRAM, DirectX, instruções e SSD ainda exigem conferência.
Suporte nativo não comprova a versão do SO; Linux sem suporte nativo não
herda os requisitos do Windows. A interface mantém essas pendências e não
promete FPS. Recomendações com pendências aparecem na seção correspondente.

`data/raw/steam_games_*` e `data/processed/` continuam locais e ignorados
pelo Git. Para reproduzir, execute os comandos do README. Para consultar
o grafo, use [games_queries.cypher](games_queries.cypher) no Neo4j Browser.
