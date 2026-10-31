# GameCompass — ambiente de desenvolvimento

Frontend React, API FastAPI, Neo4j Community 5.23.0 e pipeline Python.
A interface consulta jogos na loja Steam e lê CPUs e GPUs do catálogo
manual carregado no Neo4j. As etapas de coleta e limpeza também podem
ser executadas pelos scripts de dados.

## Pré-requisitos

- Git
- Docker com Docker Compose v2
- No Windows, Docker Desktop iniciado e configurado para contêineres Linux

## 1. Obter o projeto e abrir uma branch

```bash
git clone https://github.com/caiociribeiro/gamecompass.git
cd gamecompass
git switch master
git pull --ff-only origin master
git switch -c chore/ambiente-dados
```

Se o repositório já estiver clonado, entre nele e execute `git status` antes
de trocar de branch ou atualizar. A branch principal deste projeto é `master`.

## 2. Configurar o ambiente local

Na raiz do projeto, crie `.env` a partir de `.env.example` somente se ainda
não houver um `.env` configurado.

PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Linux/macOS:

```bash
test -f .env || cp .env.example .env
```

O exemplo define o usuário `neo4j` e a senha local de desenvolvimento
`compass_secret`. O `.env` está ignorado pelo Git. Não altere a senha de um
banco já inicializado apenas editando esse arquivo: `NEO4J_AUTH` configura a
credencial inicial, não redefine usuários de um volume existente.

Esta configuração fixa o Neo4j em 5.23.0. Um volume criado por uma versão
mais nova do Neo4j não deve ser reutilizado para fazer downgrade.

## 3. Subir e verificar os serviços

```bash
docker compose version
docker compose config --quiet
docker compose up --build -d neo4j api
docker compose ps
```

Aguarde o serviço `neo4j` aparecer como `healthy`. Os endereços locais são:

| Serviço | Endereço |
| --- | --- |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Saúde da API | http://localhost:8000/health |
| Conexão API → Neo4j | http://localhost:8000/health/neo4j |
| Neo4j Browser | http://localhost:7474 |
| Bolt, no computador | bolt://localhost:7687 |

Se mudar uma porta publicada em `.env`, ajuste o endereço local correspondente.
Por exemplo, `NEO4J_BOLT_PORT=7688` exige `NEO4J_URI=bolt://localhost:7688`
para scripts executados diretamente no computador. Nos contêineres, a porta
interna continua sendo 7687. As portas publicadas estão restritas ao computador local.

No PowerShell, verifique as respostas:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/neo4j
```

## 4. Verificar o ambiente da pipeline

```bash
docker compose build data
docker compose run --rm data
```

Resultado esperado:

```json
{"status": "ok", "database": "neo4j", "query_result": 1}
```

O serviço `data` usa o perfil `data`, mas pode ser executado diretamente
pelo nome sem ativar o perfil manualmente. É um processo sob demanda:
o contêiner termina ao concluir o script. A checagem executa apenas
`RETURN 1 AS status`, em sessão de leitura.

As pastas `scripts/` e `data/` são montadas no contêiner. Alterações nos
scripts ficam disponíveis sem reconstruir a imagem. Ao alterar as
dependências em `scripts/requirements.txt`, execute novamente
`docker compose build data`.

Para um futuro script que não dependa do banco:

```bash
docker compose run --rm --no-deps data python --version
```

O Compose injeta as credenciais e `bolt://neo4j:7687` nos serviços `api` e
`data`. O `localhost` do contêiner aponta para o próprio contêiner.
Para execução direta no computador, Python precisa receber as variáveis
do ambiente: os scripts não carregam `.env` automaticamente.

## 5. Registrar e publicar esta etapa

Execute depois de validar o ambiente:

```bash
git status --short --branch
git diff --check
git add docker-compose.yml .env.example README.md scripts/Dockerfile scripts/.dockerignore scripts/requirements.txt scripts/check_neo4j.py
git diff --cached --stat
git commit -m "chore: prepara Docker para pipeline de dados"
git push -u origin chore/ambiente-dados
```

O `.env` e os datasets gerados não fazem parte desse commit. Os arquivos
em `data/raw/` e `data/processed/` continuam ignorados conforme a regra
atual do projeto. Os formatos e a política de versionamento dos dados
serão definidos na próxima etapa.

## Pipeline de hardware e formato legado

O contrato do catálogo e suas regras de validação estão em
[data/README.md](data/README.md). Para inspecioná-lo sem conectar ao banco:

```bash
docker compose run --rm --no-deps data python scripts/hardware_catalog.py --describe
```

Este script usa apenas a biblioteca padrão do Python e fica disponível
pelo volume de `scripts/`; não é necessário reconstruir a imagem.

Depois de processar um CSV, simule a carga antes de conectar ao banco:

```bash
docker compose run --rm --no-deps data python scripts/load_hardware.py --input data/processed/hardware_sample_20261023.csv --dry-run
```

Remova `--dry-run` e `--no-deps` para executar a carga dos nós CPU e GPU.
O carregador usa `MERGE` pelo nome e atualiza o score sem duplicar peças.
Os detalhes e a consulta de conferência estão em [data/README.md](data/README.md).

Próximas etapas:

1. Definir o acesso à fonte para ampliar o catálogo, preservando a origem
   e a data de cada coleta.
2. Extrair requisitos da Steam, normalizar a RAM e associar os modelos
   aos benchmarks, encaminhando correspondências ambíguas para revisão.
3. Carregar os jogos validados no contrato de grafo da API.

No formato legado, `passmark_score` representa CPU Mark para CPUs e
G3D Mark para GPUs. O catálogo atual usa `performance_score` e `score_version`,
conforme [o contrato manual](data/catalog/README.md). As métricas têm escalas diferentes e serão comparadas dentro
do mesmo tipo de componente e de um mesmo conjunto de dados. Nomes de
variantes, como Ti, SUPER, XT, versões de notebook e capacidades de VRAM,
devem ser preservados na identificação dos modelos.

A compatibilidade inicial exige simultaneamente CPU, GPU e RAM suficientes.
Um benchmark sintético é uma estimativa comparativa e não garante FPS,
suporte a instruções, DirectX, VRAM ou demais requisitos do jogo.

## Logs e encerramento

```bash
docker compose logs --tail=100 neo4j api
docker compose down
```

`docker compose down` encerra os serviços preservando os volumes nomeados.

## Interface conectada: busca por nome e hardware

Use Node.js 22.18+ ou Node.js 24. Docker Desktop precisa estar iniciado no Windows.
Na raiz do projeto, inicie a API:

```text
docker compose up -d --build --wait api
```

Esse comando aguarda a API responder ao healthcheck. O `npm run dev` inicia
somente o frontend; o container `api` também precisa estar rodando.
A checagem `/health` confirma o processo da API; `/health/neo4j` verifica
se a conexão com o banco também funciona.

Se o Vite registrar `ECONNREFUSED 127.0.0.1:8000`, execute na raiz:

```text
docker compose ps -a api neo4j
docker compose logs --tail=80 api
```

Confira http://localhost:8000/health antes de testar a busca. Se `API_PORT`
for diferente no `.env`, use essa porta no endereço. Se houver
`API_PROXY_TARGET` definido, ele deve apontar para a API em execução.
Depois de mudar essas variáveis, reinicie o Vite. Não é necessário apagar
volumes ou recarregar o hardware para iniciar a API novamente.

Se a página Hardware informar que o servidor respondeu sem componentes,
a rota foi acessada, mas não retornou CPUs ou GPUs utilizáveis. Consulte
http://localhost:8000/api/hardware para conferir as listas. A API expõe
somente registros com `score_version: manual_v1`; carregar um catálogo
legado não preenche essa seleção. Um volume Neo4j novo também começa vazio.
Execute os dois comandos abaixo para validar e carregar o catálogo manual,
depois clique em Atualizar catálogo na interface. O carregador atualiza por
nome, sem duplicar componentes ou apagar os modelos omitidos.

O catálogo manual já carregado continua sendo usado. Se precisar reconstruí-lo:

```text
docker compose run --rm --no-deps data python scripts/hardware_catalog.py --format manual --input data/catalog/hardware_manual_v1.csv --output data/processed/hardware_manual_v1.csv
docker compose run --rm data python scripts/load_hardware.py --format manual --input data/processed/hardware_manual_v1.csv
```

Em outro terminal:

```text
cd frontend
npm ci
npm run dev
```

Abra http://localhost:5173. O Vite encaminha `/api` para a porta `API_PORT`
do `.env` da raiz, usando 8000 por padrão. O proxy também funciona no preview.
O Swagger permanece em http://localhost:8000/docs.

A conta local de teste é `demo@gamecompass.dev`, senha `demo123`. Conta,
senha e perfil continuam no navegador. A migração preserva peças e âncoras
Steam já escolhidas; os recursos da loja deixam de fazer parte do perfil.
As listas originais de gêneros e temáticas ficam disponíveis mesmo sem jogos.

### Fluxo da interface

1. Uma conta nova começa com três espaços vazios para âncoras; nenhum jogo é escolhido automaticamente.
2. Em Preferências, escolha gêneros e temáticas nas listas originais.
3. Em Jogos âncora, escolha uma das oito sugestões ou busque pelo nome e clique em Usar.
4. Em Hardware, escolha CPU e GPU do Neo4j e informe RAM e sistema operacional.
5. Em Recomendações, clique em Buscar sugestões quando quiser consultar candidatos.
6. Abra o detalhe de um jogo para conferir os requisitos mínimos e recomendados por plataforma.

A tela de âncoras oferece uma seleção editorial de oito jogos conhecidos:
Cyberpunk 2077, Red Dead Redemption 2, The Witcher 3, Elden Ring,
Baldur's Gate 3, Stardew Valley, Hollow Knight e Hades. É uma ajuda para
escolher âncoras, sem representar um ranking da Steam. A seleção contém
somente IDs em `data/catalog/anchor_suggestions.json`; nomes e capas são
consultados na Steam. Falhas individuais não escondem os demais resultados,
e há um botão para tentar novamente em caso de indisponibilidade.

Esses cards são carregados apenas ao abrir Jogos âncora. Eles ficam separados
do catálogo de recomendações e não contam como escolhas até clicar em Usar.
A busca pelo nome continua disponível para títulos fora dessa seleção.
Não há entrada manual de AppID na interface. IDs continuam internos para
identificar os resultados e persistir as escolhas. Ao entrar novamente,
somente as âncoras que o próprio cliente salvou são restauradas.
A página pública não mostra uma vitrine de títulos predefinidos.

A busca exige ao menos dois caracteres, aguarda 350 ms de pausa e cancela
consultas anteriores. Pesquisar retorna nomes; os detalhes são consultados
após selecionar um resultado. A busca da loja também pode encontrar DLCs e
software: a seleção valida o tipo e informa quando o resultado não é um jogo base.

### Fontes dos dados

| Informação | Fonte |
| --- | --- |
| Nomes de jogos na busca | Endpoint público `storesearch` da Steam |
| Sugestões para escolher âncoras | IDs editoriais versionados; nomes e capas reais de `appdetails` |
| Título, capa, preço, gêneros e requisitos | Endpoint público `appdetails` da Steam, região BR e idioma português |
| Candidatos para sugestões | Jogos do Neo4j relacionados por gênero/temática; consulta aos mais vendidos da Steam se faltarem candidatos, com aviso |
| Gêneros e temáticas do perfil | Listas originais em `frontend/src/data/preferences.ts` |
| CPUs, GPUs e suas notas | Neo4j, somente registros `manual_v1` |
| RAM e família do SO | Opções locais em `frontend/src/data/hardware.ts` |

RAM e SO não recebem nós próprios no Neo4j. As notas de hardware são lidas
do banco. Os aliases versionados servem à identificação dos requisitos;
os endpoints não criam nem alteram nós e não usam as antigas notas fictícias.

As temáticas são salvas no perfil. Os jogos do catálogo versionado recebem
tags editoriais do GameCompass, ligadas por `HAS_TAG`; essas temáticas
participam da afinidade. Consultas fora do catálogo podem retornar
`themes: []` e `themes_status: pending`. Recursos de `categories` não são
usados como temáticas. A ordenação permanece no navegador; informações
ausentes não são tratadas como desinteresse.

Mais vendidos são apenas uma fonte de candidatos, não uma recomendação
personalizada pronta. A análise de afinidade e de requisitos é aplicada
a esses candidatos pelo protótipo, após a solicitação do cliente.

### Rotas de leitura

| Rota | Resposta |
| --- | --- |
| `GET /api/hardware` | CPUs e GPUs carregadas, incluindo notas nulas |
| `GET /api/games` | Lista vazia, sem chamada à Steam ou ao banco |
| `GET /api/games/search?q=nome` | Busca por nome, sem carregar detalhes de cada resultado |
| `GET /api/games/anchors` | Até oito nomes e capas da Steam, sem ler hardware nem selecionar jogos no perfil |
| `GET /api/games/discover` | Candidatos solicitados pelo botão de sugestões |
| `GET /api/games/{appid}` | Detalhes de um jogo, utilizado internamente pela interface |
| `GET /api/games?appids=123,456` | Até trinta jogos explicitamente identificados, inclusive âncoras salvas |

No PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/api/hardware
Invoke-RestMethod "http://localhost:8000/api/games/search?q=cyberpunk"
```

A API reutiliza os scripts de limpeza e matching por volumes de leitura.
A carga de jogos no grafo é executada pelos scripts descritos abaixo.

O cache em memória guarda até 128 consultas por seis horas, com no máximo
três chamadas simultâneas e intervalo mínimo entre inícios. Ao recarregar
o Neo4j, atualize o catálogo de hardware e solicite novamente as sugestões:
os requisitos são processados contra as notas atuais, mesmo com Steam em cache.
As respostas incluem origem, data e hashes. Falhas ficam visíveis e não são
substituídas por jogos ou peças fictícias.

Notas ausentes, modelos não identificados e versões de SO sem validação
continuam pendentes. VRAM, DirectX, instruções e SSD exigem conferências
próprias. Os requisitos limpos continuam visíveis no detalhe, sem garantia de FPS.

### Testes

```text
docker compose run --rm --no-deps api python -m unittest discover -s tests -v
```

Os testes HTTP usam fixtures identificadas e dispensam serviços externos.
Na pasta `frontend/`:

```text
npm test
npm run build
```

A verificação cobre âncoras inicialmente vazias, sugestões editoriais,
busca por nome, cache, falhas totais e parciais, migração do perfil,
classificações pendentes e preservação dos dados já escolhidos.

## Jogos, gêneros e tags no Neo4j

A seleção inicial está em `data/catalog/games.json`: 20 jogos reais,
incluindo Cyberpunk, RDR2, The Witcher 3, Elden Ring, BG3 e jogos indie.
As informações vêm da Steam; as tags seguem a curadoria do projeto.
Detalhes dos scripts, esquema e limites: [GAMES.md](data/catalog/GAMES.md).

Na raiz do projeto, valide e atualize primeiro o hardware. A revisão
atual tem 41 CPUs e 40 GPUs, com 61 peças classificadas e 20 pendentes;
as justificativas estão em
[HARDWARE_REVIEW_2026_10.md](data/catalog/HARDWARE_REVIEW_2026_10.md).

```bash
docker compose build data
docker compose up -d neo4j
docker compose run --rm --no-deps data python scripts/hardware_catalog.py --format manual --input data/catalog/hardware_manual_v1.csv --output data/processed/hardware_manual_v1.csv
docker compose run --rm data python scripts/load_hardware.py --format manual --input data/processed/hardware_manual_v1.csv
```

Colete o lote em uma pasta nova. No Linux, a variável abaixo evita colidir
com coletas anteriores. Preserve seu valor se precisar continuar a coleta:

```bash
GC_SNAPSHOT="data/raw/steam_games_$(date -u +%Y%m%dT%H%M%SZ)"
docker compose run --rm --no-deps data python scripts/fetch_games.py --output-dir "$GC_SNAPSHOT"
```

Se houver falha parcial, repita o último comando acrescentando `--resume`.
O comando precisa terminar com `status: ok` antes do processamento.

```bash
docker compose run --rm --no-deps data python scripts/process_games.py --snapshot-dir "$GC_SNAPSHOT"
docker compose run --rm --no-deps data python scripts/load_games.py --dry-run
docker compose run --rm data python scripts/load_games.py
docker compose up -d --build --wait api
```

Não há limpeza geral. A carga usa `MERGE`, preserva hardware, jogos
omitidos e relações de outras origens. Repetir o lote conserva a quantidade
de nós e relações. Os campos planos de requisitos correspondem ao Windows;
macOS/Linux permanecem separados no JSON preservado. Ausências continuam
nulas. Alterar CSV ou aliases exige reprocessamento antes de carregar jogos.

No frontend, atualize o catálogo de hardware e clique em Buscar sugestões.
A API usa `HAS_GENRE`/`HAS_TAG` para escolher candidatos; o frontend aplica
a afinidade e mostra pendências e restrições. Os jogos não são escolhidos
automaticamente para as âncoras. As preferências originais foram mantidas.

Teste a resposta no Linux:

```bash
curl -fsS 'http://localhost:8000/api/games/discover?anchor_ids=1091500,292030,1245620' | python3 -m json.tool
```

Com o lote carregado, a resposta deve ter `source: neo4j`. Os arquivos
raw e processados ficam locais; seleção, curadoria, scripts e consultas
são versionados. No [Neo4j Browser](http://localhost:7474), execute uma
das consultas de [games_queries.cypher](data/catalog/games_queries.cypher).

Testes específicos desta etapa:

```bash
docker compose run --rm --no-deps data python scripts/test_game_catalog.py
docker compose run --rm data python scripts/test_game_loader.py --integration
docker compose run --rm --no-deps api python -m unittest discover -s tests -v
```

Os testes de carga usam identidades exclusivas e limpam apenas suas
fixtures. Não apagam o banco. A comparação de versão do SO e outras
restrições ainda pendentes não são aprovadas automaticamente.
