# Base de hardware do GameCompass

## Armazenamento

O Neo4j continua como banco da aplicação. A fonte de verdade do catálogo
manual é o CSV versionado nesta pasta. Os scripts validam esse arquivo e
carregam CPUs e GPUs no grafo. O catálogo não fica embutido nos scripts.

| Arquivo ou diretório | Responsabilidade | Git |
| --- | --- | --- |
| `hardware_manual_v1.csv` | Cadastro de modelos, pontuações e referências | Versionado |
| `hardware_aliases.json` | Nomes alternativos da mesma peça | Versionado |
| `requirements_curation.json` | Referências manuais específicas para requisitos incompletos de cada jogo | Versionado |
| `SCORING.md` | Critério de classificação e avaliações registradas | Versionado |
| `data/raw/` | Respostas originais e coletas locais | Ignorado, exceto `.gitkeep` |
| `data/processed/` | CSV validado, requisitos e relatórios gerados | Ignorado, exceto `.gitkeep` |
| Neo4j | Cópia do catálogo utilizada pela aplicação | Persistido no volume Docker |

Assim, outro computador recebe o catálogo pelo Git e pode reconstruir a
carga. O `.env`, as coletas locais e o volume do Neo4j pertencem a cada
ambiente. Edite o CSV desta pasta e gere novamente a saída processada.

## Conteúdo do catálogo

São 154 CPUs Intel/AMD e 173 GPUs NVIDIA/AMD/Intel/ATI.
O conjunto inicial foi selecionado a partir dos requisitos Windows de
Cyberpunk 2077, Elden Ring, Baldur's Gate 3, Red Dead Redemption 2 e
Hogwarts Legacy, além de páginas oficiais dos fabricantes e comparações
de hardware com identificação dos modelos.

O cadastro inclui modelos antigos e recentes, como Core i5-2500K,
Ryzen 7 9700X, GTX 1060 3GB/6GB, Arc A770 8GB/16GB, RTX 5070 e RX 9070.
É um primeiro conjunto para expansão, sem pretensão de cobrir todo o mercado.
O lote mais recente inclui o i3-380M móvel e gráficos integrados antigos
citados pelos jogos. São faixas preliminares; RAM compartilhada, energia e
condições de notebooks podem alterar bastante o resultado. Apple Silicon e
outras CPUs ARM continuam exigindo critérios próprios. Os textos dessas
plataformas permanecem nos snapshots da Steam.

As 327 peças têm faixas aproximadas do TCC1. Os grupos iniciais foram preservados:

| Tipo | Classe | Modelos |
| --- | ---: | --- |
| CPU | 100 | Ryzen 5 3600, Ryzen 5 3600X, Ryzen 7 3700X, Core i5-9600K e Core i7-9700K |
| GPU | 50 | GTX 1060 3GB e RX 570 4GB |
| GPU | 100 | GTX 1060 6GB e RX 580 8GB |
| GPU | 200 | GTX 1070 8GB e RX Vega 56 8GB |

O lote de outubro de 2026 acrescenta as classes CPU 400, 500 e 600 e
GPU 500, 550, 600, 700, 800, 900 e 1000. Consulte a
[seleção de 20 CPUs e 20 GPUs](RESEARCH_2026_10.md) para a lista completa,
as fontes e os ajustes da proposta histórica.

As propostas históricas já foram classificadas. O lote dos requisitos adicionou
12 CPUs e 31 GPUs, preservando os 81 registros anteriores. Consulte
[Revisão dos requisitos](REQUIREMENTS_REVIEW_2026_10.md) para fontes,
faixas e pendências dos textos da Steam.
O lote seguinte acrescenta 45 CPUs e 57 GPUs, preservando todos os 124
registros anteriores. Inclui famílias Core 2, Phenom, Core i3/i5 legados,
Ryzen 5000, Core i5-12400, GTX/RTX intermediárias e Radeon RX 6000/7000.
As referências de cada inclusão e o encaixe ordinal estão no CSV; as notas
são decisões do GameCompass, não valores publicados pelos sites consultados.

As referências adicionais incluem as hierarquias históricas do Tom's Hardware,
a [avaliação de Ryzen 5 5500/5600 e Core i5-12400](https://www.tomshardware.com/reviews/amd-ryzen-5-5600-and-ryzen-5-5500-review/3),
a [avaliação da RX 6600](https://www.techspot.com/review/2343-amd-radeon-rx-6600/)
e a [avaliação da GTX 1660 Super](https://www.techspot.com/review/1935-nvidia-geforce-gtx-1660-super/).
O posicionamento é aproximado entre faixas existentes, sem uma nova fórmula
de benchmark e sem alterar notas previamente cadastradas.
Consulte [Critério do índice manual](SCORING.md) para a justificativa,
o recorte da avaliação e os limites da aproximação.

Para peças pendentes, `source_url` comprova a identidade ou a menção nos
requisitos. Nas peças classificadas, aponta para a referência usada na curadoria.
As faixas legadas também usam especificações e hierarquias históricas;
não foram todas medidas juntas. Nenhum score PassMark foi copiado ou convertido
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
AMD e Intel/NVIDIA é representada pela classificação de desempenho,
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

O resultado informa `CPU: 41`, `GPU: 40`, formato manual e versão
`manual_v1`. O processamento é local e preserva o arquivo de entrada.

```text
docker compose run --rm --no-deps data python scripts/hardware_matcher.py --format manual --catalog data/processed/hardware_manual_v1.csv --aliases data/catalog/hardware_aliases.json --type GPU --name "GeForce GTX 1060 6GB"
```

A identidade é encontrada, com `status: matched`, `score_status: classified`
e `performance_score: 100`. Modelos como a RX 580 4GB continuam sendo
reconhecidos com `score_status: pending` e `performance_score: null`.

O primeiro grupo de CPU pode ser consultado com alternativas:

```text
docker compose run --rm --no-deps data python scripts/hardware_matcher.py --format manual --catalog data/processed/hardware_manual_v1.csv --aliases data/catalog/hardware_aliases.json --type CPU --name "Ryzen 5 3600 ou Core i5-9600K" --alternatives
```

O resultado informa `status: resolved` e `required_score: 100`. CPU e GPU
usam escalas independentes, mesmo quando o número da classe coincide.

Para processar um bloco de requisitos, use `process_requirements.py` com
`--format manual`, `--catalog data/processed/hardware_manual_v1.csv` e
`--aliases data/catalog/hardware_aliases.json`, além de `--input` ou `--text`.
O JSON informa `needs_review` enquanto alguma nota necessária estiver pendente.

## Carga no Neo4j

Primeiro valide e conte o lote sem conectar ao banco:

```text
docker compose run --rm --no-deps data python scripts/load_hardware.py --format manual --input data/processed/hardware_manual_v1.csv --dry-run
```

O catálogo atual terá `classified: 48` e `pending: 33`. Para cadastrar as peças:

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

A ampliação para 80 jogos acrescenta 17 CPUs e 19 GPUs às 226 peças anteriores, sem mudar suas notas. Inclui Core i3-10100/F, Core i5-10400/F, Ryzen 3 3100, Ryzen 5 4500, GT 1030 GDDR5, RTX 3050 6GB/8GB e modelos legados citados nos requisitos. As variantes DDR4/GDDR5 da GT 1030 e 6GB/8GB da RTX 3050 são distintas. As fontes e datas de cada encaixe estão no CSV; as faixas continuam sendo ordinais próprias do TCC1. As análises [Core i3-10100](https://www.techspot.com/review/2033-intel-core-i3-10100/), [Core i5-11400F](https://www.techspot.com/review/2232-intel-core-i5-11400f/) e [RTX 3050 6GB](https://www.techspot.com/review/2816-nvidia-geforce-rtx-3050-6gb/) orientam o encaixe aproximado, sem copiar suas pontuações.

A ampliação para 120 jogos acrescenta 30 CPUs e 20 GPUs às 262 peças anteriores (312 no total; a RX 5500 XT 4GB, acrescentada depois, leva a 313) e 78 aliases de nomes publicados pela Steam (1439 no total; a troca de 28 jogos de 10/11/2026 acrescentou 12 e levou a 1453, e a rodada de pendências de 12/11/2026 acrescentou 14 peças, 16 aliases e 7 regras: 327 peças, 1469 aliases e 196 regras de curadoria, ver [HARDWARE_REVIEW_2026_11.md](HARDWARE_REVIEW_2026_11.md)), todos para modelos únicos do catálogo. As classes novas vêm de comparações de jogos ou de um modelo irmão já classificado; a confiança de cada uma está nas `notes` do CSV e em [HARDWARE_REVIEW_2026_11.md](HARDWARE_REVIEW_2026_11.md), que também registra as correções posteriores (RX 6600 XT de 350 para 300 e RTX 4070 de 450 para 500) e as candidatas avaliadas sem mudança. Variantes ambíguas de memória (RX 480, GTX 1060, RTX 2060, Arc A770 e outras) e textos genéricos continuam pendentes de propósito.
