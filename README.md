# GameCompass

Recomenda jogos da Steam que combinam com o gosto da pessoa e que rodam no computador dela. A pessoa escolhe gêneros e temáticas, três jogos que já aprovou (as âncoras) e informa o computador. A API calcula a afinidade com o motor `rules_v1` e compara o computador com os requisitos mínimos e recomendados de cada jogo.

Protótipo do TCC. O catálogo tem 120 jogos reais e um índice manual de 327 CPUs e GPUs.

## Como funciona

```text
Navegador (React, :5173) ──/api──▶ API FastAPI (:8000) ──▶ Neo4j (jogos, peças, contas)
                                        │
                                        └──▶ Steam (busca por nome e jogos fora do catálogo, com cache)

Pipeline Python (scripts/) ──▶ coleta na Steam, interpreta requisitos, cruza com o índice de hardware ──▶ Neo4j
```

| Parte | Onde | Documentação |
|---|---|---|
| Interface | `frontend/` | [frontend/README.md](frontend/README.md) |
| API e motor de recomendação | `backend/` | [backend/README.md](backend/README.md) |
| Pipeline do catálogo | `scripts/` | [data/catalog/GAMES.md](data/catalog/GAMES.md) (jogos) e [data/catalog/README.md](data/catalog/README.md) (hardware) |
| Dados versionados | `data/catalog/`, `data/evaluation/` | [data/README.md](data/README.md) |

## Começar

Precisa de Git e Docker com Compose v2. No Windows, use o Docker Desktop com contêineres Linux.

```bash
git clone https://github.com/caiociribeiro/gamecompass.git && cd gamecompass
```

```bash
test -f .env || cp .env.example .env
```

No PowerShell: `if (-not (Test-Path .env)) { Copy-Item .env.example .env }`.

```bash
docker compose up --build -d
```

Isso sobe o Neo4j, carrega o catálogo, sobe a API e o site, nessa ordem. O site só inicia quando a API passa no healthcheck.

| Serviço | Endereço |
|---|---|
| Site | http://localhost:5173 |
| API (Swagger) | http://localhost:8000/docs |
| Saúde da API e do banco | http://localhost:8000/health e http://localhost:8000/health/neo4j |
| Neo4j Browser | http://localhost:7474 |

As portas ficam presas ao `127.0.0.1` e podem ser trocadas no `.env`. Ao publicar o site em outra porta, inclua a nova origem em `ALLOWED_ORIGINS`, ou a API recusa cadastro e perfil. `API_WORKERS` define quantos processos a API usa (padrão 4).

O `.env` define a senha local do Neo4j (`compass_secret`) e é ignorado pelo Git. `NEO4J_AUTH` só vale na criação do volume: mudar a senha depois não altera um banco que já existe. O Neo4j está fixo na 5.23.0; não reaproveite um volume criado por uma versão mais nova.

O catálogo já vem pronto. A cada `up`, o serviço `catalog` confere o Neo4j e, se o banco estiver vazio ou desatualizado, carrega as 327 peças e os 120 jogos versionados em `data/catalog/`. Num banco novo isso leva menos de um minuto, e nos `up` seguintes só confere. A API só sobe depois disso. Não é preciso coletar nada da Steam nem rodar scripts.

Para **atualizar** o catálogo (trocar jogos, revisar requisitos ou peças), quem mantém o projeto roda o `scripts/update_catalog.py` e versiona o `data/catalog/games_manual_v1.json` que ele gera. No próximo `up`, todas as máquinas recebem a versão nova, e os jogos que saíram da seleção são removidos (exceto os que têm reação de alguma conta). O passo a passo está em [data/catalog/GAMES.md](data/catalog/GAMES.md#atualizar-o-catálogo).

## Testes

| O quê | Comando | No CI |
|---|---|---|
| API | `docker compose run --rm --no-deps api python -m unittest discover -s tests -v` | Sim |
| Scripts de dados | `python -m unittest discover -s scripts -p "test_*.py" -v` | Sim |
| Frontend (unidade, interface e build) | `cd frontend && npm test && npm run build` | Sim |
| Ponta a ponta pela API | `GAMECOMPASS_E2E=1 python3 tests/e2e/test_api_flow.py` | Não (precisa do catálogo no Neo4j) |
| Ponta a ponta no navegador | `cd frontend && npm run e2e` | Não (precisa do catálogo no Neo4j) |

O CI (`.github/workflows/ci.yml`) roda em todo pull request e em todo push para o `master`, sem Neo4j, Steam ou segredos. Os testes de ponta a ponta criam uma conta descartável e a apagam no fim.

## Pastas

| Pasta | Conteúdo |
|---|---|
| `frontend/` | Site React, testes, roteiro Playwright e medições das telas |
| `backend/` | API, motor `rules_v1`, testes e medições de carga |
| `scripts/` | Coleta, processamento e carga do catálogo, com os testes de cada etapa |
| `data/catalog/` | Seleção de jogos, jogos processados (`games_manual_v1.json`), índice de hardware, aliases, curadoria e revisões |
| `data/evaluation/` | Casos de ouro do motor e o relatório |
| `tests/e2e/` | Teste de ponta a ponta pela API |
| `data/raw/`, `data/processed/` | Coletas da Steam e arquivos intermediários; locais, fora do Git |

## Dia a dia

```bash
docker compose logs --tail=100 api neo4j
```

```bash
docker compose up -d --build frontend
```

```bash
docker compose down
```

O `down` encerra os serviços e preserva os volumes. **Não use `docker compose down -v`**: o `-v` apaga o volume do Neo4j, com contas, catálogo e interações.

## Limites do protótipo

- **Afinidade:** os pesos são heurísticos e não representam probabilidade. A avaliação com usuários ainda é necessária.
- **Requisitos:** a comparação usa um índice manual aproximado de CPUs e GPUs. Não garante FPS e não confere VRAM, DirectX, instruções ou espaço em disco. O que não dá para comprovar fica pendente.
- **Catálogo:** são 120 jogos escolhidos. O grafo não cobre toda a loja da Steam.
- **Contas:** não há recuperação de senha por e-mail.
