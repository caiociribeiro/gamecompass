# Tempo de resposta e carga da API (RNF10)

Medição de 13/11/2026 da API do GameCompass, servida como no `docker compose` do projeto. Complementa a [medição das telas do frontend](../../frontend/perf/README.md).

## Método

O script [`measure_api.py`](measure_api.py) usa só a biblioteca padrão do Python. Ele cria uma conta descartável com perfil completo e a apaga do Neo4j no fim. O perfil usado é RPG + Fantasia; Cyberpunk 2077, The Witcher 3 e ELDEN RING; Ryzen 5 3600, RTX 3060 12GB, 16 GB e Windows 11.

**Tempo de resposta:** chamadas em sequência, numa conexão persistente, a cada endpoint usado pelo frontend.
- **Endpoints do Neo4j:** 3 chamadas de aquecimento e 50 medidas.
- **Endpoints da Steam** (busca e sugestões de âncora): 5 medidas. A 1ª chamada vai à Steam; as seguintes saem do cache da própria API. Por isso a tabela mostra as duas.

**Carga:** 1, 5, 10 e 20 clientes simultâneos chamando `POST /api/recommendations`, a rota mais pesada, por 15 s em cada nível. Cada cliente usa sua conexão persistente, e a próxima chamada só sai depois da resposta anterior. No meio de cada nível, o script lê o uso de CPU e memória dos contêineres com `docker stats` (100% = um núcleo).

Rotas que consultam a Steam ao vivo ficam fora da carga, para não sobrecarregar um serviço de terceiros.

## Ambiente

| Item | Valor |
|---|---|
| Data | 13/11/2026, das 04:24 às 04:29 (UTC) |
| Código | `master` em `803a895` (o mesmo de `67ee46b`) |
| Servidor da API | uvicorn, 1 processo (comando padrão do `backend/Dockerfile` até o PR #23), Python 3.12 |
| Banco | Neo4j do `docker compose`, 120 jogos e 327 peças |
| Máquina | Intel Core i5-1334U (12 threads), 15 GB, Linux 7.0.0-42; contêineres sem limite de CPU ou memória |
| Cliente | Python 3.14 no host, na mesma máquina da API e do Neo4j |

## Tempo de resposta (sem carga)

Em ms. "1ª" é a primeira chamada; p50 e p95 são as medianas e o percentil 95 das chamadas medidas.

| Endpoint | Sessão | 1ª | p50 | p95 | Máx |
|---|---|---|---|---|---|
| `GET /health/neo4j` | — | 5,7 | 5,6 | 7,2 | 9,0 |
| `GET /api/auth/me` | logada | 8,8 | 7,6 | 9,7 | 10,1 |
| `GET /api/hardware` | logada | 33,9 | 21,8 | 33,6 | 40,0 |
| `GET /api/games?appids=` (3 âncoras) | logada | 43,6 | 37,5 | 57,4 | 77,7 |
| `GET /api/games/{id}` | logada | 46,7 | 34,9 | 50,7 | 51,7 |
| `GET /api/me/interactions` | logada | 4,7 | 8,7 | 14,6 | 15,2 |
| `PATCH /api/me/profile` | logada | 18,8 | 11,1 | 18,0 | 20,8 |
| `POST /api/recommendations` | logada | 208,6 | 171,0 | 233,5 | 271,7 |
| `POST /api/recommendations` | anônima | 178,9 | 171,7 | 238,9 | 261,3 |
| `POST /api/games/{id}/comparison` | logada | 34,0 | 43,8 | 64,6 | 75,4 |
| `GET /api/games/search?q=elden` (Steam) | logada | **915,5** | 2,8 | 3,2 | 3,2 |
| `GET /api/games/anchors` (Steam) | logada | **2.049,8** | 3,1 | 3,2 | 3,2 |

Nenhuma chamada falhou.

## Carga em `POST /api/recommendations`

### Configuração atual (1 processo)

| Clientes simultâneos | Respostas | Vazão (req/s) | p50 (ms) | p95 (ms) | Máx (ms) | CPU da API | CPU do Neo4j |
|---|---|---|---|---|---|---|---|
| 1 | 81 | 5,35 | 174,7 | 270,5 | 343,7 | 87% | 16% |
| 5 | 74 | 4,70 | 994,9 | 1.336,9 | 1.434,9 | 107% | 159% |
| 10 | 51 | 3,00 | 2.686,4 | 3.444,2 | 4.009,0 | 113% | 4% |
| 20 | 33 | 1,66 | 7.089,5 | 8.106,6 | 9.002,6 | 128% | 433% |

Nenhuma requisição falhou. Os números de CPU são uma amostra só, no meio de cada nível, e oscilam.

### Teste com 4 processos (não é a configuração do projeto)

Para entender o limite, a mesma carga rodou com um servidor temporário `uvicorn --workers 4`, aberto na porta interna 8001 do próprio contêiner. A configuração do projeto não mudou. Nesse teste, o cliente rodou dentro do contêiner. Para comparar nas mesmas condições, o 1 processo foi medido de novo também de dentro (arquivos `2026-11-13-api-carga-*.json`):

| Clientes | 1 processo: req/s | 1 processo: p50 (ms) | 4 processos: req/s | 4 processos: p50 (ms) |
|---|---|---|---|---|
| 1 | 5,42 | 176,5 | 5,53 | 172,9 |
| 5 | 4,58 | 1.010,1 | 12,65 | 344,8 |
| 10 | 2,97 | 2.792,8 | 10,14 | 889,2 |
| 20 | 2,06 | 6.688,5 | 9,30 | 1.840,5 |

## Leitura dos resultados

- **Uso individual:**
  - **Rotas mais usadas:** quase todas respondem em menos de 60 ms no p95.
  - **Recomendações:** é a rota mais lenta, com ~170 ms na mediana e ~235 ms no p95. É ela que roda o motor `rules_v1` sobre os candidatos.
  - **Rotas da Steam:** só a 1ª chamada é lenta (0,9 s na busca e 2 s nas sugestões de âncora), porque depende da Steam. Depois vêm do cache, em ~3 ms.
- **Sob carga, a configuração atual não escala:**
  - **Gargalo:** com 1 processo, a API usa praticamente um núcleo inteiro (87% a 128%). O cálculo das recomendações é CPU em Python, e as requisições simultâneas disputam o mesmo processo.
  - **Efeito:** a vazão não aumenta com mais clientes; ela cai de 5,4 para 1,7 req/s. A espera cresce na mesma proporção: com 20 pessoas pedindo sugestões ao mesmo tempo, cada uma espera ~7 s (p50).
  - **Falhas:** nenhuma. A API fica lenta, mas não erra.
- **Com mais processos a capacidade melhora:**
  - **Ganho:** 4 processos chegam a 12,7 req/s com 5 clientes (2,7× a vazão), e a espera com 20 clientes cai de 6,7 s para 1,8 s (p50).
  - **Limite:** acima de 5 clientes a vazão volta a cair um pouco. Cliente, API e Neo4j dividem os mesmos 12 threads da máquina.
- **Limites da medição:**
  - **Rede:** cliente e servidores na mesma máquina, sem rede real entre eles.
  - **Duração:** 15 s por nível e uma amostra de CPU por nível.
  - **Abrangência:** um único perfil e um único tipo de requisição na carga.
  - **Interpretação:** os números absolutos valem para esta máquina; a comparação entre configurações vale porque elas rodaram nas mesmas condições.

## Padrão adotado: 4 processos

A partir da branch `chore/organizacao`, a API sobe com 4 processos. É a variável `WEB_CONCURRENCY` do uvicorn, definida no `backend/Dockerfile` e ajustável por `API_WORKERS` no `.env`. A medição com essa configuração, feita do host como a principal, está em `2026-11-13-api-4-processos-padrao.json`:

| Clientes | Vazão (req/s) | p50 (ms) | p95 (ms) | CPU da API | Memória da API |
|---|---|---|---|---|---|
| 1 | 5,45 | 168,9 | 276,1 | 89% | 341 MB |
| 5 | 11,47 | 362,9 | 670,3 | 375% | 356 MB |
| 10 | 10,88 | 835,7 | 1.288,0 | 412% | 379 MB |
| 20 | 9,32 | 1.733,9 | 2.978,6 | 423% | 427 MB |

O tempo de cada rota sem carga não muda. Com 20 clientes, a espera mediana cai de 7,1 s para 1,7 s. Em troca, a API passa de ~80 MB para ~340 a 430 MB de memória.

O teste de regressão de 13/11 com os 4 processos mostrou:
- **Sessão:** um login vale em todos os processos (40 de 40 chamadas em conexões novas), o perfil gravado é lido igual e o logout revoga a sessão em todos.
- **Limitador de login:** cada processo conta as falhas sozinho. Com 4 processos, o bloqueio veio depois de 12 tentativas erradas, e não 5. Um limitador compartilhado (no Neo4j) devolveria o limite exato.
- **Cache da Steam:** cada processo tem o seu, então a primeira busca de um termo pode ir à Steam até 4 vezes.

## Como repetir

Com a stack no ar (`docker compose up -d`):

```bash
python3 backend/perf/measure_api.py --out backend/perf/nova-medicao-api.json
```

O teste com 4 processos, dentro do contêiner:

```bash
docker exec -d gamecompass-api uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 4
```

```bash
docker cp backend/perf/measure_api.py gamecompass-api:/tmp/measure_api.py
```

```bash
docker exec gamecompass-api python /tmp/measure_api.py --base http://127.0.0.1:8001 --skip-latency --label "uvicorn --workers 4"
```

Dentro do contêiner não há `docker`, então o script mostra a consulta Cypher para apagar a conta de teste. Depois, `docker compose restart api` desliga o servidor temporário.
