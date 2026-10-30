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

## Interface conectada: Steam e hardware

Use Node.js 22.18+ ou Node.js 24. Docker Desktop precisa estar iniciado no Windows.
Na raiz do projeto, valide e carregue o catálogo manual que está disponível
no seu checkout. Este passo funciona com a base anterior e com sua ampliação:

```text
docker compose run --rm --no-deps data python scripts/hardware_catalog.py --format manual --input data/catalog/hardware_manual_v1.csv --output data/processed/hardware_manual_v1.csv
docker compose run --rm data python scripts/load_hardware.py --format manual --input data/processed/hardware_manual_v1.csv
docker compose up -d --build api
```

Em outro terminal, a partir da raiz:

```text
cd frontend
npm ci
npm run dev
```

Abra http://localhost:5173. O Vite encaminha `/api` para a API na porta
`API_PORT` do `.env` da raiz, usando 8000 por padrão. Também existe proxy
em `npm run preview`. Uma configuração de produção precisará encaminhar
esse prefixo para o backend. O Swagger permanece em http://localhost:8000/docs.

A conta local de teste continua sendo `demo@gamecompass.dev`, senha
`demo123`. Escolha novamente as preferências, as âncoras e o computador:
a primeira abertura migra o perfil antigo, que usava IDs fictícios,
preservando a conta. O cadastro, a senha e o perfil ainda ficam neste navegador.

### O que vem de cada fonte

| Informação | Fonte |
| --- | --- |
| CPU e GPU, nomes, notas e versão do índice | Neo4j, somente registros `manual_v1` |
| Aliases para identificar os requisitos | `data/catalog/hardware_aliases.json`, validado contra o CSV versionado |
| Título, capa, preço, gêneros, recursos e requisitos | Endpoint público `appdetails` da loja Steam, região BR, idioma português |
| Seleção inicial de jogos | Vinte AppIDs em `data/catalog/steam_appids.json`; o arquivo não contém dados fictícios de jogos |
| RAM e família de sistema operacional | Opções locais em `frontend/src/data/hardware.ts` |

RAM e sistema operacional são valores do perfil e não ganham nós próprios
no Neo4j. Os requisitos de RAM dos jogos continuam numéricos. A comparação
usa as notas lidas do banco; não usa as antigas pontuações da interface.
CPU e GPU têm escalas independentes. Peças sem nota permanecem selecionáveis
com indicação de classificação pendente.

### Rotas de leitura

| Rota | Resposta |
| --- | --- |
| `GET /api/hardware` | CPUs e GPUs carregadas, incluindo notas nulas |
| `GET /api/games` | Seleção consultada na Steam, com falhas parciais identificadas |
| `GET /api/games/{appid}` | Um jogo por AppID, com requisitos por plataforma e nível |
| `GET /api/games?extra_appids=123,456` | Até três jogos adicionais para restaurar âncoras salvas |

No PowerShell, para verificar a comunicação:

```powershell
Invoke-RestMethod http://localhost:8000/api/hardware
Invoke-RestMethod http://localhost:8000/api/games/1091500
```

A API monta `scripts/` e `data/` como leitura para reutilizar o parser e o
matching existentes. Os endpoints não criam nem alteram nós. Esta etapa
consulta os jogos diretamente da Steam; a carga de jogos no grafo continua
como etapa da pipeline.

### Fluxo para testar

1. Entre na conta local e confira o catálogo no painel.
2. Abra um jogo e veja mínimos e recomendados de Windows, Linux e macOS.
3. Em Hardware, procure as peças carregadas no seu Neo4j e salve RAM e SO.
4. Escolha gêneros e recursos e três jogos âncora.
5. Consulte a afinidade e as verificações técnicas na lista e no detalhe.
6. Para outro título, abra Jogos âncora e informe seu Steam AppID.

Os recursos usados nesta etapa vêm de `categories` da Steam, como cooperação
ou um jogador. As tags da comunidade ficam para uma integração posterior.
A ordenação por afinidade permanece no navegador. Não são inventadas
pontuações para preencher requisitos desconhecidos.

A interface distingue restrições confirmadas de validações pendentes.
Escolher a família Windows, Linux ou macOS não confirma a versão exigida;
por isso a checagem completa de SO permanece pendente. VRAM, DirectX,
instruções e SSD também precisam de verificações específicas. Os textos
originais limpos ficam acessíveis para conferência; não há garantia de FPS.

A API mantém até 128 respostas em memória por seis horas, com três chamadas
simultâneas e intervalo mínimo entre inícios. Reiniciar a API limpa esse
cache. Ao atualizar o catálogo e recarregar o Neo4j, use Atualizar catálogo
na interface: os requisitos são processados novamente contra as notas
atuais, mesmo quando a resposta Steam vem do cache. As respostas incluem
origem, data e hashes para rastrear o que foi consultado.

Falhas da Steam são mostradas na interface. Um AppID indisponível não é
substituído por um jogo fictício. Banco vazio não gera peças de demonstração.

### Testes desta integração

```text
docker compose run --rm --no-deps api python -m unittest discover -s tests -v
```

Os testes HTTP usam fixtures identificadas e não exigem uma chamada externa
à Steam ou conexão real com Neo4j. Na pasta `frontend/`:

```text
npm test
npm run build
```

Os testes verificam notas nulas, versões do índice, plataformas, RAM,
cache, falhas de serviços e distinção entre pendência e restrição.
