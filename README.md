# GameCompass — ambiente de desenvolvimento

API FastAPI, Neo4j Community 5.23.0 e um ambiente Python separado para
construir a pipeline de dados. Os scripts normalizam catálogos CSV de
benchmarks e carregam CPUs e GPUs no grafo. A coleta automática e a
extração de requisitos da Steam serão implementadas nas próximas etapas.

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

## Pipeline de hardware e próximas etapas

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

Para CPUs, o campo `passmark_score` representará CPU Mark; para GPUs,
G3D Mark. As métricas têm escalas diferentes e serão comparadas dentro
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

## Interface de demonstração

O frontend em `frontend/` é um protótipo sem API. Conta, perfil e recomendações ficam no navegador.

É preciso Node.js 20 ou superior.

```bash
cd frontend
npm install
npm run dev
```

A interface abre em http://localhost:5173. A conta de demonstração é `demo@gamecompass.dev`, senha `demo123`.
