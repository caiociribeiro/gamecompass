# Catálogo de jogos e relações

## O que é versionado

`games.json` contém a seleção de 120 AppIDs, o vocabulário de temáticas e
uma justificativa editorial por jogo. Nomes, gêneros gerais, requisitos,
preços e capas vêm da coleta real de `appdetails`, em português e região BR.
`editorial_genres` complementa os gêneros com Plataforma, Roguelike, Tiro
e Puzzle quando aplicável; `genre_curation_notes` explica essa decisão.
Essas categorias compartilham `HAS_GENRE`, com origem separada no JSON
`genre_source.steam`/`genre_source.editorial`, sem atribuí-las à Steam.
As tags representam a curadoria do GameCompass; não são apresentadas como
tags da comunidade Steam. Os recursos de `categories` não substituem
as preferências originais da interface.

Seleção inicial, preservada nas ampliações para 50, 80 e 120 jogos:

| AppID | Jogo da seleção inicial |
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
   âncoras e pelas preferências. A FastAPI calcula afinidade e comparação de hardware;
   o navegador apresenta a resposta e mantém os filtros de exibição.

Não há jogo escolhido automaticamente para o perfil. Buscar nomes continua
consultando a Steam; escolher um jogo catalogado aproveita o Neo4j.
Se o catálogo não tiver candidatos ou estiver indisponível, a API pode
usar os mais vendidos da Steam e informa essa troca na resposta/interface.
Os 120 jogos selecionados formam uma base limitada; o grafo não busca todos os
similares existentes na loja.

A ampliação para 80 inclui 30 novos AppIDs, com mais Puzzle, Plataforma, Roguelike e cooperativos. `reuse_snapshots.py`, chamado por `update_catalog.py --reuse-snapshot-dir ... --fetch`, verifica e copia as coletas selecionadas para o lote novo, preservando resposta e metadata. O manifesto guarda `reuse_sources` e o SHA-256 do manifesto anterior. O coletor completa somente os jogos ausentes. Nunca atualiza a data de uma resposta reaproveitada como se fosse uma coleta recente.

A ampliação para 120 (06/11/2026) inclui 40 novos AppIDs escolhidos para cobrir lacunas do catálogo: corridas, esporte, casual, competitivo, relaxante, terror, estratégia e simulação. Cada AppID foi verificado em `appdetails` (jogo base, requisitos mínimos publicados, Windows); jogos em acesso antecipado ficaram de fora para não acrescentar esse gênero. As tags saem do mesmo vocabulário de dez temáticas e cada jogo tem uma justificativa em `curation_notes`; Tiro, Plataforma e Roguelike seguem as frases-padrão já usadas. A classificação editorial dos 40 jogos novos é do GameCompass e deve ser revisada por quem mantém o projeto. Com a ampliação o grafo tem 120 jogos, 15 gêneros, 10 temáticas e 601 relações (340 `HAS_GENRE` e 261 `HAS_TAG`). No Windows, 99 jogos têm base de comparação de hardware e 21 ainda exigem curadoria de requisitos; os pendentes vêm sobretudo de CPUs e GPUs que o índice não identifica (ver [HARDWARE_REVIEW_2026_11.md](HARDWARE_REVIEW_2026_11.md)). Para repetir a coleta em outra máquina, reaproveite o lote anterior e baixe só os 40 novos:

```bash
docker compose run --rm data python scripts/update_catalog.py --snapshot-dir data/raw/steam_games_lote120_<data> --reuse-snapshot-dir data/raw/steam_games_lote80_20261031 --fetch --load
```

Os snapshots não vão para o git. Preços e requisitos coletados em dias diferentes podem divergir entre máquinas; para resultados idênticos, copie a mesma pasta de snapshots.

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

O lote anterior de 50 jogos, verificado em 31/10/2026, contém 50 jogos, 14 gêneros e dez temáticas,
usando 98 CPUs e 128 GPUs com faixas aproximadas do TCC1. Foram preservados
os vinte jogos e os 124 registros anteriores de hardware.
As quatro categorias adicionais acrescentam 20 relações: a seleção atual
gera 133 `HAS_GENRE` e 124 `HAS_TAG`, sujeitos à versão dos dados Steam.
Não é preciso coletar a Steam novamente para acrescentar categorias:
reprocesse e carregue os snapshots existentes.

No Windows, 38 mínimos estão completamente identificados e outros 12
oferecem alternativas suficientes para comparação. Entre os recomendados,
30 estão identificados, dez oferecem alternativas conhecidas e dez não
foram publicados. Essas contagens incluem referências manuais para 31
jogos e descrevem cobertura dos dados, sem certificar execução ou FPS.

As referências manuais estão em `requirements_curation.json`. Cada uma
registra AppID, plataforma, nível, campo, texto esperado, modelos de
referência, fonte, data e justificativa. São estimativas do GameCompass;
o texto Steam e a extração original permanecem no resultado processado.
Um texto alterado não reutiliza a estimativa. A API reaplica as regras com
as notas atuais do Neo4j, sem recuperar uma nota antiga do CSV se a peça
estiver ausente ou pendente. O hash da curadoria também acompanha a carga.

Stardew Valley, Hades, Portal 2, Terraria, Dead Cells, Slay the Spire e
No Man's Sky passaram a ter referências locais para os campos genéricos.
Isso não transforma famílias ou frequências em aliases globais de modelos.
O documento [REQUIREMENTS_REVIEW_2026_10.md](REQUIREMENTS_REVIEW_2026_10.md)
conserva o histórico da amostra anterior, antes dessa ampliação.

`scripts/update_catalog.py` executa coleta retomável, processamento e
carga com `--fetch --load`. Sem `--load`, não conecta ao banco. Não gera
relatórios automaticamente. Os scripts individuais continuam disponíveis.

Na seleção de 80, foram exercitados aqui 70 snapshots reais: 68 oferecem base de comparação no Windows. Unpacking mantém RAM ausente e A Hat in Time mantém GPU ausente. Os dez snapshots restantes precisam ser coletados no ambiente de execução; essas contagens não afirmam a cobertura dos 80. Os modelos e regras conferidos nas páginas públicas do Suporte Steam só serão aplicados se o texto coletado corresponder.

A extração também separa títulos explícitos mínimo/recomendado publicados juntos em `minimum`, quando `recommended` está ausente. A resposta raw não é alterada. Nas fichas antigas em uma linha, somente CPU, RAM explícita, descrição de GPU e Windows publicados são lidos; capacidade de GPU ou armazenamento não é usada como RAM.

## Limites atuais da validação

O extrator reconhece OS, SO, Operating System, Sistema Operacional e
Sistema Operativo, inclusive o asterisco de requisitos antigos da Steam.
A interface pede Windows 10 ou 11 de 64 bits e compara a versão principal
informada com a menor versão Windows reconhecida no mínimo do jogo.
Aceitar uma versão posterior é uma heurística do TCC1. Não constitui
certificação de execução de todos os jogos: a própria
[Microsoft informa que podem ocorrer incompatibilidades](https://support.microsoft.com/en-us/windows/apps/make-older-apps-or-programs-compatible-with-the-latest-version-of-windows).

Quando uma atualização/build específica for exigida na mesma versão,
o resultado permanece pendente. Linux/macOS continuam com conferência de
versão própria. Linux sem suporte nativo não herda requisitos Windows.
VRAM, DirectX, instruções e SSD também exigem conferência. A interface
mantém essas pendências e não promete FPS.

Três aliases explícitos reconhecem as grafias Intel Core i7 8700K,
Intel Core i7 8700 e Intel Arc A580 (8GB+ of VRAM). Não escolhem a variante
de um Arc A770 sem capacidade de memória. A RAM fracionada é arredondada
para cima: 2.5 GB resulta em 3 GB, sem confundir RAM com VRAM.

`data/raw/steam_games_*` e `data/processed/` continuam locais e ignorados
pelo Git. Para reproduzir, execute os comandos do README. Para consultar
o grafo, use [games_queries.cypher](games_queries.cypher) no Neo4j Browser.


A revisão de requisitos legados aceita RAM com `of RAM`, rótulos editoriais de CPU/GPU e qualificadores finais de desempenho. Não remove capacidades de memória, sufixos ou famílias desconhecidas. A curadoria de FTL e Psychonauts foi conferida nas páginas públicas do Suporte Steam; sua aplicação depende do texto do snapshot local. Essas páginas não substituem os bytes e metadados de uma coleta real.

Uma regra pode incluir `query_variants`, lista opcional de até cinco textos completos alternativos, como traduções revisadas. O AppID, plataforma, nível e componente continuam obrigatórios. Nenhuma correspondência aproximada de frases é aplicada. O resultado preserva em `original_query` o texto efetivamente coletado, e o hash da curadoria inclui todas as variantes.

`review_game_requirements.py --input ...` imprime o resumo e os campos bloqueantes sem salvar um relatório. Com `--output ...`, preserva a saída em arquivo como antes. Ausência de dados não se transforma em nota zero ou recomendação de troca. As mensagens da comparação distinguem campo ausente na Steam de texto ainda não interpretado.


Blocos publicados com somente cabeçalho, aviso genérico de 64 bits, rede e observações recebem `requirements_kind: notes_only`. A lista de formatos é explícita; uma linha desconhecida ou um campo parcial de CPU/GPU/RAM/SO impede essa classificação. O texto é preservado no JSON e continua visível no frontend. O validador rejeita um bloco marcado como observações que contenha pontuações de desempenho, RAM, modelos ou SO identificados. A API refaz essa classificação a partir do texto ao ler registros antigos do grafo.

A revisão inclui esses blocos em `not_provided` e os contabiliza separadamente em `notes_only`, por nível. Eles não entram como falha de identificação e não comprovam atendimento. As referências dos mínimos nunca são copiadas para eles. A ficha de recomendados de Spelunky 2 é um exemplo; a RAM parcial publicada para Baba Is You permanece uma pendência de requisitos.

## Revisão de qualidade dos requisitos — 01/11/2026

Objetivo: separar erro de extração ou identificação de informação que a Steam
realmente não publica, sem inventar requisitos para chegar a 100% de cobertura.

**Pendências dos jogos.** O texto original (`appdetails.json`) dos quatro jogos
foi comparado com o resultado do parser. Em todos, o dado falta na fonte:

| Jogo | O que a Steam publica | Situação |
| --- | --- | --- |
| Unpacking (1135690) | Mínimos sem linha de memória; CPU "SSE2" e GPU "DX10" genéricos. Recomendados só com o aviso de 64 bits. | RAM ausente na fonte. |
| A Hat in Time (253230) | Mínimos e recomendados com CPU, RAM e DirectX 9.0c, sem linha de GPU. | GPU ausente na fonte. |
| Baba Is You (736260) | Recomendados só com RAM e disco. | CPU, GPU e SO ausentes na fonte. |
| Spelunky 2 (418530) | Recomendados só com rede e "Gamepad Recommended". | `notes_only`; não aprova nem herda os mínimos. |

Continuam pendentes e documentados como limitação da fonte. Nenhum valor foi
completado por referência manual.

**Auditoria do lote de 80.** Nenhum campo com valor no texto original deixou de
ser extraído. O que mantinha requisitos pendentes eram alternativas que o
catálogo de hardware não reconhecia (36 no início): requisitos como
"RTX 2060 SUPER ou RX 5700 XT ou Arc A770" ficam pendentes enquanto uma das
opções for desconhecida. Foram acrescentados 59 aliases revisados (agora
1361 no total) para modelos que já existem no catálogo com uma única
variante: GTX 1650, RX 590, RX Vega 56, RX 470, RX 570, GTX 950, 760, 770, 680 e
560, GTS 450, 9600 GT, R7 260X, R7 360, HD 7870 e R9 290X. Regra: um alias sem
memória só pode apontar para um modelo com uma única variante no catálogo
(`scripts/test_alias_policy.py`).

Efeito no lote: alternativas não identificadas 36 → 20; mínimos resolvidos
64 → 72 (com alternativa desconhecida 14 → 6); recomendados resolvidos 41 → 46
(12 → 7). Jogos com base de comparação no Windows: continuam 78 de 80.

**Continuam pendentes, por motivo explícito:**

- Ambíguos por variante: Arc A770 (8GB ou 16GB), RX 480 (4GB ou 8GB), RX 550
  (2GB ou 4GB) e RTX 2060 (a versão de 12GB tem outra configuração de chip).
- Genéricos: "R9 series", "shader model 4.0", "GeForce 2xx-Series", "Radeon
  HD 7800", "Radeon HD 4650 series", "Core 2 Duo" e "HD Graphics 4000 ou
  melhor com 2 GB de VRAM".
- Fora do catálogo: Snapdragon X Elite, Adreno X1 e Iris Xe G7.
- Erro na fonte: Monster Hunter: World cita "Core i3-8350" e "Core i3-9350F",
  que não existem (o modelo real seria i3-8350K). Não corrigimos por conta
  própria.
- Texto com resíduo: Factorio ("DirectX 11 capable GPU with 1GB VRAM - GeForce
  GTX 750 Ti"), que mistura uma exigência de classe com exemplos.

Para aplicar no banco depois de mudar aliases: reprocessar e carregar
(`update_catalog.py --snapshot-dir ... --load`); a carga não duplica nós.
