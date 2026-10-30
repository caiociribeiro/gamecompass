# Base de hardware do GameCompass

## Armazenamento

O Neo4j continua como banco da aplicação. A fonte de verdade do catálogo
manual é o CSV versionado nesta pasta. Os scripts validam esse arquivo e
carregam CPUs e GPUs no grafo. O catálogo não fica embutido nos scripts.

| Arquivo ou diretório | Responsabilidade | Git |
| --- | --- | --- |
| `hardware_manual_v1.csv` | Cadastro de modelos, pontuações e referências | Versionado |
| `hardware_aliases.json` | Nomes alternativos da mesma peça | Versionado |
| `SCORING.md` | Critério de classificação e avaliações registradas | Versionado |
| `data/raw/` | Respostas originais e coletas locais | Ignorado, exceto `.gitkeep` |
| `data/processed/` | CSV validado, requisitos e relatórios gerados | Ignorado, exceto `.gitkeep` |
| Neo4j | Cópia do catálogo utilizada pela aplicação | Persistido no volume Docker |

Assim, outro computador recebe o catálogo pelo Git e pode reconstruir a
carga. O `.env`, as coletas locais e o volume do Neo4j pertencem a cada
ambiente. Edite o CSV desta pasta e gere novamente a saída processada.

## Conteúdo do catálogo

São 20 CPUs Intel/AMD e 22 GPUs NVIDIA/AMD/Intel, todas de desktop.
Os modelos foram selecionados a partir dos requisitos Windows de
Cyberpunk 2077, Elden Ring, Baldur's Gate 3, Red Dead Redemption 2 e
Hogwarts Legacy, além de páginas oficiais dos fabricantes e comparações
de hardware com identificação dos modelos.

O cadastro inclui modelos antigos e recentes, como Core i5-2500K,
Ryzen 7 9700X, GTX 1060 3GB/6GB, Arc A770 8GB/16GB, RTX 5070 e RX 9070.
É um primeiro conjunto para expansão, sem pretensão de cobrir todo o mercado.
Notebooks, GPUs integradas, Apple Silicon e outras CPUs ARM exigirão
cadastros e critérios próprios. Os requisitos coletados dessas plataformas
continuam preservados nos snapshots da Steam.

Há 4 GPUs classificadas: GTX 1060 6GB e RX 580 8GB na classe 100;
GTX 1060 3GB e RX 570 4GB na classe 50. As outras 38 peças têm
`performance_score` vazio e continuam pendentes.
Consulte [Critério do índice manual](SCORING.md) para a justificativa,
o recorte da avaliação e os limites da aproximação.

Para peças pendentes, `source_url` comprova a identidade ou a menção nos
requisitos. Nas peças classificadas, aponta para a comparação que
fundamenta a classe. Nenhum score PassMark foi copiado ou convertido
em índice próprio.

## Contrato do CSV

UTF-8, vírgula como separador e cabeçalho nesta ordem:

```text
component_type,name,performance_score,score_version,source_url,collected_at,notes
```

| Campo | Regra |
| --- | --- |
| `component_type` | `CPU` ou `GPU` |
| `name` | Nome canônico da peça, preservando variantes |
| `performance_score` | Inteiro positivo; vazio enquanto não classificado |
| `score_version` | `manual_v1` nesta versão |
| `source_url` | URL HTTPS da referência utilizada |
| `collected_at` | Data/hora da consulta ou registro, com fuso ISO 8601 |
| `notes` | Justificativa da classificação ou pendência explícita |

O par tipo/nome deve ser único. Preserve sufixos como K, X, X3D, Ti e XT.
Versões com memória diferente ficam separadas quando essa informação
identifica variantes. A normalização ajusta espaços e caixa para consulta,
sem aproximar modelos por similaridade do nome.

Ao atribuir uma nota, atualize referência, data e justificativa, incluindo
as condições da comparação. CPU e GPU usam escalas independentes.
O Git registra as revisões; os requisitos processados registram os hashes
do catálogo e dos aliases. `manual_v1` está em elaboração. Uma revisão
publicada dos critérios precisará de nova versão e suporte no validador.

## Aliases

Aliases identificam a mesma peça. O arquivo mantém o contrato já utilizado
por `hardware_matcher.py`: `component_type`, `alias` e `canonical_name`.
Todos os destinos precisam existir neste CSV. Há variantes de escrita,
abreviações e nomes efetivamente encontrados nos requisitos consultados.

`Core i7-6700` identifica `Intel Core i7-6700`. Equivalência aproximada entre
AMD e Intel/NVIDIA será representada pela classificação de desempenho,
preservando registros distintos.

Consultas genéricas como `GTX 1060`, `RX 480`, `RX 570`, `RX 580` e `Arc A770` não
escolhem automaticamente uma capacidade de memória. Elas seguem para revisão.
Os aliases desta pasta são usados com o catálogo manual. O arquivo anterior
`data/hardware_aliases.json` continua associado ao catálogo legado.

## RAM, sistema operacional e outros requisitos

| Informação | Representação |
| --- | --- |
| CPU e GPU | Modelo no catálogo e pontuação quando classificado |
| RAM | Quantidade numérica em GB no perfil e nos requisitos; a normalização já existe |
| SO | Suporte nativo e texto por plataforma já extraídos da Steam; validação de versões ainda pendente |
| VRAM | Variantes preservadas no nome; campo numérico e checagem independente ainda pendentes |
| Armazenamento | Espaço em GB e exigência de SSD serão tratados como requisitos próprios; implementação pendente |

Não é necessário cadastrar marcas e modelos de módulos de RAM ou SSD para
comparar capacidade. Esses requisitos não recebem pontuação de CPU/GPU.

## Processar e consultar

Na raiz do repositório, os comandos abaixo funcionam em PowerShell e Bash.
O modo manual continua explícito durante a migração. Informe a entrada
versionada com `--input`, pois o padrão antigo do script ainda usa `data/raw`.

```text
docker compose run --rm --no-deps data python scripts/hardware_catalog.py --format manual --input data/catalog/hardware_manual_v1.csv --output data/processed/hardware_manual_v1.csv
```

O resultado informa `CPU: 20`, `GPU: 22`, formato manual e versão
`manual_v1`. O processamento é local e preserva o arquivo de entrada.

```text
docker compose run --rm --no-deps data python scripts/hardware_matcher.py --format manual --catalog data/processed/hardware_manual_v1.csv --aliases data/catalog/hardware_aliases.json --type GPU --name "GeForce GTX 1060 6GB"
```

A identidade é encontrada, com `status: matched`, `score_status: classified`
e `performance_score: 100`. Modelos como a RX 580 4GB continuam sendo
reconhecidos com `score_status: pending` e `performance_score: null`.

Para processar um bloco de requisitos, use `process_requirements.py` com
`--format manual`, `--catalog data/processed/hardware_manual_v1.csv` e
`--aliases data/catalog/hardware_aliases.json`, além de `--input` ou `--text`.
O JSON informa `needs_review` enquanto alguma nota necessária estiver pendente.

## Carga no Neo4j

Primeiro valide e conte o lote sem conectar ao banco:

```text
docker compose run --rm --no-deps data python scripts/load_hardware.py --format manual --input data/processed/hardware_manual_v1.csv --dry-run
```

O catálogo atual terá `classified: 4` e `pending: 38`. Para cadastrar as peças:

```text
docker compose run --rm data python scripts/load_hardware.py --format manual --input data/processed/hardware_manual_v1.csv
```

O grafo recebe `CPU`/`GPU` com `name`, `score_version` e `performance_score`
quando há nota. Fonte, data e justificativa permanecem no CSV versionado.
Uma nota vazia remove a pontuação anterior daquela peça; a carga manual
também remove `passmark_score` dos modelos carregados. O script usa `MERGE`
pelo nome exato e preserva modelos que não aparecem no CSV.

Nomes diferentes usados em cargas antigas não são renomeados por aliases.
Aliases atuam na identificação antes da carga. No banco, consulte esta
versão explicitamente para separar os registros manuais dos legados:

```cypher
MATCH (h)
WHERE (h:CPU OR h:GPU) AND h.score_version = 'manual_v1'
RETURN labels(h) AS tipo, h.name AS nome,
       h.performance_score AS pontuacao,
       CASE WHEN h.performance_score IS NULL
            THEN 'pendente' ELSE 'classificado' END AS classificacao
ORDER BY tipo, nome;
```

A integração com a API precisa usar os novos campos e a mesma versão do
índice nos perfis e requisitos dos jogos. A classificação pendente ainda
não fornece limite para aprovar compatibilidade por desempenho.

## Atualizar e compartilhar

1. Edite o CSV e, se necessário, os aliases desta pasta.
2. Registre referência, data e justificativa em cada item alterado.
3. Processe o catálogo e confira a simulação da carga.
4. Carregue o catálogo e reprocese os requisitos afetados pelas notas.
5. Versione os arquivos de `data/catalog` com os scripts/documentação alterados.

Os arquivos processados continuam locais e podem ser reconstruídos.
O contrato de `Game`, `Genre`, `Tag` e seus relacionamentos permanece sob
o acordo de integração do projeto; este catálogo cadastra apenas hardware.
