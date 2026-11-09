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

Use Node.js 22.22.2+ ou Node.js 24.15+ (os testes React usam jsdom). Docker Desktop precisa estar iniciado no Windows.
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

Contas e perfis ficam no servidor (veja "Contas e perfil" abaixo). Não existe
mais conta de demonstração: crie uma conta em `/cadastro`. Escolhas guardadas
no navegador pela versão anterior podem ser importadas uma vez, de forma
explícita, depois do login. As listas originais de gêneros e temáticas ficam
disponíveis mesmo sem jogos.

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
| Título, capa, preço, gêneros gerais e requisitos | Endpoint público `appdetails` da Steam, região BR e idioma português |
| Plataforma, Roguelike, Tiro e Puzzle | Curadoria de jogabilidade do GameCompass em `games.json`, com justificativa e origem separada |
| Candidatos para sugestões | Jogos do Neo4j relacionados por gênero/temática; consulta aos mais vendidos da Steam se faltarem candidatos, com aviso |
| Gêneros e temáticas do perfil | Listas originais em `frontend/src/data/preferences.ts` |
| CPUs, GPUs e suas notas | Neo4j, somente registros `manual_v1` |
| RAM, família do SO e Windows 10/11 | Opções locais em `frontend/src/data/hardware.ts` |

RAM e SO não recebem nós próprios no Neo4j. As notas de hardware são lidas
do banco. Os aliases versionados servem à identificação dos requisitos;
os endpoints não criam nem alteram nós e não usam as antigas notas fictícias.

As temáticas são salvas no perfil. Os jogos do catálogo versionado recebem
tags editoriais do GameCompass, ligadas por `HAS_TAG`; essas temáticas
participam da afinidade. Consultas fora do catálogo podem retornar
`themes: []` e `themes_status: pending`. Recursos de `categories` não são
usados como temáticas. A ordenação e a comparação são calculadas pela FastAPI; informações
ausentes não são tratadas como desinteresse.

As preferências originais foram preservadas. Quatro delas precisavam de
classificação complementar porque o campo de gêneros da Steam é mais
geral: `Plataforma`, `Roguelike`, `Tiro` e `Puzzle`. Os jogos classificados receberam
essas categorias, também ligadas por `HAS_GENRE`. `genre_source` mantém
separados os gêneros Steam e os editoriais. Roguelike é usado aqui como
categoria ampla da família roguelike/roguelite.

O cálculo usa 40% para gêneros escolhidos, 25% para gêneros das âncoras,
15% para temáticas escolhidas, 15% para temáticas das âncoras e 5% para
estúdio compartilhado. A parte das preferências mede a fração atendida;
a parte das âncoras compara cada conjunto por interseção/união (Jaccard).
Em cada dimensão, as semelhanças são ordenadas e agregadas com pesos
60%, 25% e 15%, independentemente da ordem de seleção. Dimensões sem dados
são removidas e os pesos disponíveis são normalizados. O resultado é
arredondado de 0 a 100, com limiar 28, e não representa uma probabilidade.
O desempate usa título e AppID. As explicações identificam até duas
âncoras com características em comum, combinando gêneros e temas na
proporção 25:15 dos termos de âncora. São pesos heurísticos do protótipo;
a avaliação com usuários continua necessária. Se os candidatos não
contiverem outros jogos dos gêneros escolhidos, a interface explica que
a lista se aproxima pelas âncoras e temáticas.

Mudar gêneros, temáticas ou âncoras invalida os candidatos anteriores e
cancela consultas pendentes. O usuário solicita a nova busca pelo botão;
uma resposta antiga não substitui o novo perfil. Reordenar escolhas ou
trocar apenas a RAM/peças refaz automaticamente o cálculo na API quando já
houver uma busca solicitada. Resultados do hardware anterior ficam ocultos
até a nova resposta. Reordenar preferências mantém o resultado.

Quando uma peça fica abaixo de um requisito identificado, a sugestão
prioriza modelos reconhecidos naquele requisito e pode listar até três
fabricantes. As demais opções seguem as classes suficientes do catálogo.
No empate de classe, prefere o fabricante atual e depois o nome. Essa
ordenação não considera preço, disponibilidade nem compatibilidade física.
Campos pendentes continuam sem gerar uma necessidade de troca automática.

Mais vendidos são apenas uma fonte de candidatos, não uma recomendação
personalizada pronta. A análise de afinidade e de requisitos é aplicada
a esses candidatos pela API, após a solicitação do cliente.

### Cálculo na API

`POST /api/recommendations` recebe três `anchorIds` distintos, `genres`, `themes` e `hardware` com `cpuId`, `gpuId`, `ramGb`, `os` e, em Windows, `windowsVersion`. A API consulta uma única referência de hardware do Neo4j por requisição e reutiliza esse contexto para as âncoras, os candidatos e a comparação. Não aceita pontuações, requisitos de jogos ou dados de conta no corpo.

A resposta contém `items`, `pending`, `excluded`, `anchors`, `issues`, `source` e `calculation`. Cada resultado contém afinidade, justificativas, verificações separadas de mínimos/recomendados e sugestões de substituição. `calculation` informa `engine_version: rules_v1`, versão do índice, limiar e hashes de hardware/curadoria. As sugestões continuam sendo referências de desempenho, sem cotação ou validação de encaixe físico.

`POST /api/games/{appid}/comparison` recebe as mesmas preferências e até três âncoras; aceita `hardware: null` para consultar afinidade antes de cadastrar o computador. Devolve `match`, `issues` e `calculation`. Um detalhe aberto pela lista reutiliza a resposta atual do servidor; outros jogos usam esse endpoint. Trocar perfil cancela a comparação anterior.

Um componente removido do catálogo retorna 422 e pede nova seleção. Hardware sem classificação permanece pendente. Indisponibilidade do banco retorna 503 para o cálculo com hardware; não usa notas do CSV ou um cálculo alternativo no navegador. Os jogos ainda podem vir da Steam quando faltam no grafo, com a origem informada.

Os pesos, Jaccard, corte 28, alternativas OR e regras de mínimos/recomendados foram preservados. A soma sequencial e o arredondamento em meio ponto também foram preservados. O desempate textual em Python usa normalização de acentos e caixa, título e AppID, sem depender do locale instalado no contêiner. A implementação anterior fica congelada apenas em `frontend/tests/reference/`; não entra no bundle da aplicação. `backend/tests/fixtures/engine_parity.json` guarda os casos extraídos dessa referência. Para regenerar a fixture de desenvolvimento: `node backend/tests/generate_engine_parity.mjs`.

Ao atualizar este bloco, execute:

```bash
docker compose up -d --build --wait api
docker compose run --rm --no-deps api python -m unittest discover -s tests -v
cd frontend
npm ci
npm test
npm run build
npm run dev
```

O catálogo de 120 jogos e o CSV de hardware já carregados continuam sendo usados. O cálculo continua recebendo apenas os dados necessários no corpo da requisição; ele não lê a conta.

### Contas e perfil

As contas ficam no Neo4j como `(:User)-[:HAS_SESSION]->(:Session)`, com
constraints de unicidade em `User.id`, `User.email` e `Session.token_hash`
(criadas na primeira operação de conta). O perfil são propriedades do próprio
`User`: `genres`, `themes`, `anchor_ids` (ids Steam, sem relacionamento com
`:Game`, para que recarregar o catálogo nunca afete contas) e `hw_*`.

| Rota | Função |
| --- | --- |
| `POST /api/auth/register` | Cria a conta e abre a sessão. |
| `POST /api/auth/login` | Abre a sessão; mensagem única para e-mail ou senha inválidos. |
| `POST /api/auth/logout` | Revoga a sessão no servidor. |
| `GET /api/auth/me` | Conta e perfil da sessão atual (401 sem sessão válida). |
| `POST /api/auth/password` | Troca a senha e encerra as demais sessões. |
| `PATCH /api/me/profile` | Atualização parcial de nome, gêneros, temáticas, âncoras e hardware; `hardware: null` limpa o computador. |

- Senhas: Argon2id (`argon2-cffi`), mínimo de 8 caracteres. Nenhuma senha em texto puro é guardada.
- Sessão: token aleatório em cookie `gc_session` (`HttpOnly`, `SameSite=Lax`, 7 dias). O banco guarda apenas o SHA-256 do token. Defina `SESSION_COOKIE_SECURE=true` atrás de HTTPS.
- O usuário vem sempre da sessão, nunca do corpo da requisição; o perfil de outra conta não é alcançável. Campos extras são rejeitados.
- Rotas que alteram dados recusam `Origin` fora de `ALLOWED_ORIGINS` (padrão: `http://localhost:5173` e `http://127.0.0.1:5173`).
- Cinco falhas de login em cinco minutos bloqueiam novas tentativas daquele IP/e-mail (contador em memória, reinicia com a API).
- Conta de demonstração opcional: defina `DEMO_EMAIL` e `DEMO_PASSWORD` no `.env` e rode `docker compose run --rm --no-deps api python -m app.seed_demo`. Repetir o comando redefine a senha e preserva o perfil.
- Limitações do protótipo: não há recuperação de senha por e-mail nem verificação de e-mail.

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

Em Hardware, selecione Windows 10 ou 11 de **64 bits** e salve novamente
o computador. Contas anteriores preservam as escolhas e precisam apenas
informar essa versão. A recomendação compara a versão principal com os
requisitos Windows identificados na Steam. Atualizações específicas da mesma
versão, requisitos vagos e versões de Linux/macOS continuam para conferência.
O checklist compara somente os campos implementados, sem certificar cada jogo.
RAM fracionada, como 2.5 GB, é arredondada para cima no contrato inteiro.

O detalhe do jogo compara CPU, GPU, RAM e SO em colunas de **mínimos** e
**recomendados**. Os cards informam o maior nível atendido. Os recomendados
comprovados também permitem concluir a análise quando os mínimos são
genéricos, preservando a pendência original. Uma falha mínima conhecida
continua impedindo aprovação. O card indica mínimos quando estes foram
validados e os recomendados falharam ou continuam pendentes. Recomendados
ausentes não são preenchidos com os mínimos. Uma falha nos mínimos continua
excluindo o jogo da lista de requisitos atendidos.

Para uma CPU ou GPU abaixo de um requisito identificado, a API sugere
um modelo do catálogo do mesmo tipo, com a mesma versão do índice e a menor
faixa que atenda ao requisito. Desempates usam o nome do modelo; a escolha
não considera preço. Sem uma opção identificada suficiente ou com versão
incompatível, a comparação fica pendente e não gera substituição. Se não houver modelo
suficiente no catálogo, a tela informa isso. Para RAM, a indicação é a
capacidade total necessária. As sugestões são referências de desempenho e
exigem conferir soquete, placa-mãe, fonte e demais condições físicas.

As pontuações e versões continuam internas à comparação. A interface de
hardware e o detalhe do jogo exibem nomes e resultados, sem classes numéricas.

Ao abrir um card, o detalhe guarda a página de origem. O botão Voltar
retorna às Recomendações quando o jogo foi aberto por essa lista, mantendo
a busca e o filtro de situação. Também há filtros de recomendados atendidos,
apenas mínimos, pendências e restrições. Abrir um detalhe diretamente usa
Recomendações como destino de retorno. Consultar um detalhe e voltar não
dispara outra busca de sugestões.

Em listas de alternativas, uma opção publicada e identificada é suficiente
para comprovar o atendimento à CPU ou GPU. Exemplo: em Hogwarts, atender
à GTX 1080 Ti ou à RX 5700 XT permite validar esse campo recomendado,
mesmo que a Arc A770 ainda não tenha VRAM especificada. Abaixo das opções
conhecidas a comparação continua pendente, pois a alternativa desconhecida
poderia ser menos exigente. O processamento preserva esse desconhecido e
o limite global nulo; a API usa as alternativas e a versão do índice
para comprovar o caso do computador. Detalhes e fontes em
[REQUIREMENTS_REVIEW_2026_10.md](data/catalog/REQUIREMENTS_REVIEW_2026_10.md).

O relatório abaixo separa níveis completos, alternativas conhecidas,
requisitos genéricos e níveis não publicados. Mede cobertura dos dados;
não certifica um computador nem a execução do jogo:

```text
docker compose run --rm --no-deps data python scripts/review_game_requirements.py --input data/processed/games_manual_v1.json --output data/processed/games_requirements_review.json
```

### Testes

```text
docker compose run --rm --no-deps api python -m unittest discover -s tests -v
```

Os testes HTTP usam fixtures identificadas e dispensam serviços externos. Os
testes de conta usam um repositório em memória; a persistência real no Neo4j
tem um teste próprio, executado apenas com o banco ativo:

```text
docker compose run --rm -e GAMECOMPASS_TEST_NEO4J=1 api python -m unittest discover -s tests -p "test_users_neo4j.py" -v
```

Na pasta `frontend/`:

```text
npm test
npm run build
```

A verificação cobre âncoras inicialmente vazias, sugestões editoriais,
busca por nome, cache, falhas totais e parciais, migração do perfil,
classificações pendentes e preservação dos dados já escolhidos.

### Testes de ponta a ponta

Percorrem o caminho de uma pessoa nova: cadastro, preferências, jogos âncora, computador e
recomendações. Rodam só na sua máquina, contra a pilha no ar, e **não fazem parte do CI**: dependem
do Neo4j com o catálogo carregado, e esse catálogo vem de coletas da Steam que não vão para o git.
Cada teste cria uma conta descartável (e-mail e senha aleatórios) e a apaga no final pelo
contêiner do Neo4j.

```bash
docker compose up -d neo4j api
```

Pela API, só com a biblioteca padrão do Python (sem instalar nada). No PowerShell, use
`$env:GAMECOMPASS_E2E=1` antes do comando:

```bash
GAMECOMPASS_E2E=1 python3 tests/e2e/test_api_flow.py
```

Pelo navegador, com Playwright. Com o site no ar em `http://127.0.0.1:5173` (`npm run dev`), na pasta
`frontend/`. A primeira vez baixa o Chromium (algumas centenas de MB, fora do repositório):

```bash
npm install
npx playwright install chromium
npm run e2e
```

O teste do navegador segue só os botões da tela, sem o menu lateral, e confere o rodapé de cada
etapa do perfil. As sugestões de âncoras da Steam são simuladas para ele não depender da internet;
os dados dos jogos vêm do banco de verdade. Se uma etapa falhar, o Playwright guarda um print em
`frontend/test-results/`.

### Avaliação offline do `rules_v1`

`backend/app/evaluate_rules.py` roda o motor sobre o catálogo e o hardware
carregados no Neo4j (somente leitura, mesmo cálculo da API) e relata a
contagem de `items`/`pending`/`excluded`, a distribuição de afinidade, o
top-N e a cobertura do catálogo:

```text
docker compose run --rm --no-deps api python -m app.evaluate_rules --auto 30 --top 5
```

Sem `--scenarios`, os perfis são **simulados** de forma determinística
(`--seed`): três âncoras sorteadas do catálogo, gêneros e temáticas iguais à
união das âncoras e hardware de três faixas (percentis 20/50/85 das peças com
nota, com 8/16/32 GB de RAM). São simulações, não usuários reais. Para perfis
próprios, passe `--scenarios arquivo.json` com `{"scenarios": [{"anchorIds":
[...], "genres": [...], "themes": [...], "hardware": {...}}]}` (mesmo contrato
da API). `--json` troca o texto por JSON. O resultado depende do catálogo
carregado no banco da máquina em uso.

## Jogos, gêneros e tags no Neo4j

A seleção está em `data/catalog/games.json`: 120 jogos reais,
incluindo Cyberpunk, RDR2, The Witcher 3, Elden Ring, BG3, Skyrim,
Fallout 4, Monster Hunter, Factorio, Valheim, Forza Horizon 4 e 5, Rocket League, Frostpunk, Helldivers 2 e jogos indie.
As informações vêm da Steam; as tags seguem a curadoria do projeto.
Detalhes dos scripts, esquema e limites: [GAMES.md](data/catalog/GAMES.md).

Na raiz do projeto, valide e atualize primeiro o hardware. A revisão
atual tem 145 CPUs e 167 GPUs (312 peças), todas com classificação manual aproximada
para o TCC1. O lote mais recente adiciona modelos citados pelos requisitos.
As justificativas estão em
[REQUIREMENTS_REVIEW_2026_10.md](data/catalog/REQUIREMENTS_REVIEW_2026_10.md),
[HARDWARE_REVIEW_2026_11.md](data/catalog/HARDWARE_REVIEW_2026_11.md)
e o critério simplificado em [TCC1_REVIEW_2026_10.md](data/catalog/TCC1_REVIEW_2026_10.md).

Para atualizar o lote inteiro, o comando abaixo coleta os jogos que faltam,
valida todos os snapshots, processa o hardware e os jogos e carrega os dois
catálogos no Neo4j. A pasta deve ser nova na primeira execução. Repita o
mesmo comando para retomar uma coleta interrompida; snapshots válidos não
são baixados novamente. Uma atualização da Steam requer outra pasta nova.

```bash
docker compose up -d neo4j
docker compose run --rm data python scripts/update_catalog.py --snapshot-dir data/raw/steam_games_lote80_20261031 --reuse-snapshot-dir data/raw/steam_games_lote50_20261031 --fetch --load
docker compose up -d --build --wait api
```

A seleção ampliada reforça Puzzle e Plataforma: Portal, The Witness, The Talos Principle 2, Ori, LIMBO, INSIDE, Shovel Knight e outros. `--reuse-snapshot-dir` copia os snapshots selecionados do lote anterior depois de verificar identidade, região, idioma e hashes. Preserva os bytes e a data de coleta, registra a origem no manifesto novo e baixa somente os AppIDs que faltam. As pastas devem ser separadas; o comando não altera as respostas anteriores. Se seu lote de 50 tiver outro nome, ajuste somente esse argumento.

A ampliação para 120 jogos (40 novos, escolhidos para cobrir corridas, esporte, casual, competitivo, relaxante, terror, estratégia e simulação) usa o mesmo fluxo, reaproveitando o lote de 80 e baixando só os jogos que faltam. O comando e os números verificados estão em [GAMES.md](data/catalog/GAMES.md).

Fichas antigas que publicam mínimos e recomendados juntos passam a ser separadas pelos títulos explícitos. RAM/GPU ausentes continuam pendentes: Unpacking não publica RAM nessa coleta e A Hat in Time não publica GPU. DirectX ou espaço em disco não preenchem esses campos. A cobertura dos 80 deve ser conferida após a coleta local; os testes offline não equivalem a uma coleta completa da Steam.

Sem `--fetch`, usa apenas os snapshots existentes. Sem `--load`, processa
e valida sem conectar ao Neo4j. As cargas de hardware e jogos são etapas
separadas: se uma carga falhar, a seguinte não roda; repetir é idempotente.
O comando não gera relatório adicional. A coleta parcial tem até três
tentativas e pode ser retomada depois com o mesmo comando.

`data/catalog/requirements_curation.json` registra referências manuais por
jogo, plataforma, nível e campo quando a descrição original é genérica ou
omite variantes. O texto original, os resultados anteriores, os modelos
escolhidos e a justificativa são preservados. Essas comparações aparecem
como **estimativa** na interface; não são requisitos de SKU certificados
pelo desenvolvedor. Se o texto mudar ou a peça não estiver classificada no
Neo4j atual, a regra não preenche a nota. Não há alias global de “2 GHz”,
“Intel i5+” ou escolha automática da memória de uma Arc A770.

No lote anterior de 31/10/2026, os 50 jogos têm base para comparar os mínimos no
Windows; 40 publicam recomendados com base de comparação e dez não os
informam. Parte dos campos usa alternativas identificadas ou referências
manuais. Isso descreve cobertura de dados, sem certificar execução ou FPS.
Outras plataformas e exigências específicas continuam sujeitas a revisão.

Para incorporar as categorias complementares após atualizar o código,
reprocesse o lote existente. A contagem de gêneros passa de dez para 14:

```bash
docker compose run --rm data python scripts/update_catalog.py --snapshot-dir data/raw/steam_games_lote50_20261031 --load
docker compose up -d --build --wait api
```

O coletor também aceita retomar os mesmos AppIDs depois de uma revisão
editorial, sem baixar novamente respostas válidas. Preserva o hash da
seleção que iniciou a coleta e registra o hash da seleção atual. Lotes
antigos completos são reconhecidos pelos diretórios de AppIDs; mudar os
AppIDs continua exigindo uma pasta nova. Idioma, região e hashes dos
snapshots são verificados antes de reutilizá-los.

Teste offline do novo fluxo:

```bash
docker compose run --rm --no-deps data python scripts/test_catalog_batch.py
docker compose run --rm --no-deps data python scripts/test_catalog_expansion.py
```

A revisão de grafias reconhece rótulos como `Nvidia GPU GeForce GTX 660`, sem trocar o modelo ou descartar a memória. Também aceita `256 MB of RAM` no campo de memória e qualificadores finais como `and higher`. Psychonauts e FTL receberam referências manuais para descrições antigas; a curadoria pode registrar `query_variants` com traduções exatas previamente revisadas. Uma tradução diferente continua pendente.

Na interface, `XP` isolado no campo Windows e listas antigas com XP são interpretados como versões Windows. `64-bit only` é compatível com a arquitetura já escolhida no perfil; restrições a uma versão específica, a Windows Server, a ARM ou a 32 bits continuam exigindo conferência. Isso permanece uma heurística do TCC1.

Depois de aplicar essas correções, reprocesse o lote de 80 existente, sem nova coleta:

```bash
docker compose run --rm data python scripts/update_catalog.py --snapshot-dir data/raw/steam_games_lote80_20261031 --load
docker compose up -d --build --wait api
```

Para conferir as pendências dos seus próprios snapshots no terminal, sem gerar outro arquivo:

```bash
docker compose run --rm --no-deps data python scripts/review_game_requirements.py --input data/processed/games_manual_v1.json
```

O resumo separa mínimos/recomendados e lista o campo que bloqueia cada nível. `not_provided` identifica campo ausente; `unparsed`, texto que não foi interpretado; `unidentified`, peça não identificada; `unclassified`, peça conhecida sem nota. Um nível recomendado inteiramente ausente é contabilizado à parte. `--output caminho.json` continua disponível quando for necessário salvar essa análise.

Blocos com apenas rede e observações, como os recomendados de Spelunky 2, recebem `requirements_kind: notes_only`. O texto publicado continua visível nos detalhes. Esse bloco é contabilizado como requisito de hardware não informado (`not_provided`), com a contagem auxiliar `notes_only`, e nunca aprova os recomendados nem herda as notas dos mínimos. Um campo real parcial, como a RAM publicada nos recomendados de Baba Is You, continua pendente. Texto desconhecido também continua pendente.

A descrição antiga de GPU dos recomendados de Left 4 Dead 2 usa agora uma referência manual limitada ao texto revisado. A comparação continua marcada como estimativa. Campos ausentes em Unpacking e A Hat in Time permanecem sem preenchimento automático.

Os comandos individuais continuam disponíveis:

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
nulas. Alterar CSV, aliases ou referências manuais exige reprocessamento antes de carregar jogos.

No frontend, atualize o catálogo de hardware e clique em Buscar sugestões.
A API usa `HAS_GENRE`/`HAS_TAG` para escolher candidatos, calcula a afinidade
e compara o hardware; o frontend apresenta pendências e restrições. Os jogos não são escolhidos
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
fixtures. Não apagam o banco. Casos pendentes de versão do SO e outras
restrições não recebem aprovação automática.

Os testes de campos e da interface podem ser executados sem escrever no banco:

```bash
docker compose run --rm --no-deps data python scripts/test_requirement_fields.py
cd frontend
npm test
npm run build
```
