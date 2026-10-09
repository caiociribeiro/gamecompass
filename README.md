# GameCompass — ambiente inicial

Base da Sprint 0: API Python/FastAPI e banco de grafos Neo4j executados com Docker Compose.

## Pré-requisitos

- Git
- Docker com Docker Compose v2 (Docker Desktop no Windows ou Docker Engine no Linux)

## 1. Configurar o ambiente

Na raiz do projeto, copie `.env.example` para `.env` e defina uma senha para o Neo4j.

Linux/macOS:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

## 2. Iniciar os serviços

```bash
docker compose up --build -d
docker compose ps
```

A API ficará em http://localhost:8000. A documentação interativa ficará em http://localhost:8000/docs.
O Neo4j Browser ficará em http://localhost:7474. Para entrar, use as credenciais definidas em `.env`.

## 3. Rotas iniciais

- `GET /` — identificação da API
- `GET /health` — verifica se a API está ativa
- `GET /health/neo4j` — testa a conexão com o Neo4j

## 4. Comandos úteis

```bash
docker compose logs -f api
docker compose logs -f neo4j
docker compose down
```

`docker compose down` preserva os dados no volume. Para apagar também o banco local, use `docker compose down -v` (isso remove os dados persistidos).

## Estrutura

```text
gamecompass/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── core/
│   │       ├── __init__.py
│   │       └── config.py
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

O pipeline de ingestão e os modelos de dados ainda serão implementados na Sprint 1 e nas sprints seguintes.
