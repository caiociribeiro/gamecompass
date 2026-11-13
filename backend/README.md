# API do GameCompass

FastAPI em Python 3.12. Cuida de contas e sessões, das reações aos jogos, da leitura do catálogo no Neo4j e do cálculo das recomendações com o motor `rules_v1`, que está congelado. Sobe pelo `docker compose` da raiz (veja o [README principal](../README.md)).

- Swagger: http://localhost:8000/docs
- Saúde: http://localhost:8000/health e http://localhost:8000/health/neo4j

## Estrutura

| Caminho | O que faz |
|---|---|
| `app/main.py` | Cria a aplicação, o driver do Neo4j e o cliente da Steam |
| `app/auth_routes.py` | Cadastro, login, sessão, troca de senha, perfil e e-mail sob demanda |
| `app/interaction_routes.py` | Visualizações, curtidas e histórico |
| `app/catalog_routes.py` | Hardware, jogos, busca por nome, sugestões de âncora e candidatos |
| `app/recommendation_routes.py` | `POST /api/recommendations` e comparação de um jogo |
| `app/services/recommendation_engine.py`, `affinity.py` | Motor `rules_v1`: afinidade e comparação de requisitos |
| `app/services/hardware.py`, `game_graph.py` | Leitura do índice de hardware e dos jogos no grafo |
| `app/services/users.py`, `auth.py` | Contas, sessões e interações no Neo4j; senhas e limitador de login |
| `app/services/steam.py` | Consulta pública à Steam com cache |
| `app/evaluate_rules.py`, `app/evaluate_gold.py` | Avaliação offline do motor |
| `perf/` | Medição de tempo de resposta e carga |

`app/services/hardware.py` reaproveita os módulos de interpretação e matching de `scripts/` (montados como volume de leitura em `/workspace/scripts`). Assim, a API refaz o matching dos requisitos com as notas atuais do hardware.

## Cálculo das recomendações

`POST /api/recommendations` recebe três `anchorIds` distintos, `genres`, `themes` e `hardware` (`cpuId`, `gpuId`, `ramGb`, `os` e, no Windows, `windowsVersion`). Pontuações, requisitos e dados de conta nunca vêm no corpo: a API lê tudo do Neo4j.

A resposta traz `items` (requisitos atendidos), `pending` (com afinidade, aguardando validação), `excluded` (com restrição), `anchors`, `issues`, `source`, `calculation` e `interactions`. `calculation` informa `engine_version: rules_v1`, a versão do índice, o limiar e os hashes de hardware e curadoria.

**Afinidade (0 a 100, limiar 28):** gêneros escolhidos 40%, gêneros das âncoras 25%, temáticas escolhidas 15%, temáticas das âncoras 15% e estúdio em comum 5%.
- **Preferências:** medem a fração atendida.
- **Âncoras:** usam interseção/união (Jaccard), com as três semelhanças agregadas em 60/25/15%.
- **Dados ausentes:** dimensões sem dados saem da conta, e os pesos restantes são normalizados.
- **Desempate:** título e AppID.

São pesos heurísticos do protótipo, não probabilidades.

**Requisitos:** CPU, GPU, RAM e sistema são comparados com os mínimos e os recomendados.
- **Alternativas:** numa lista de opções, uma opção publicada e identificada basta para comprovar o atendimento.
- **Falha:** uma falha conhecida nos mínimos impede a aprovação.
- **Pendências:** campos ausentes ou não identificados ficam pendentes, sem aprovação automática.
- **Troca de peça:** para uma peça abaixo do requisito, a API sugere o modelo do catálogo de menor faixa que atende. Não considera preço nem compatibilidade física.

`POST /api/games/{appid}/comparison` faz o mesmo cálculo para um jogo só e aceita `hardware: null`.

**Erros:**
- **422:** um componente removido do catálogo.
- **503:** o banco está fora do ar. Não há cálculo alternativo.

A paridade com a implementação de referência do TCC1 está em `tests/fixtures/engine_parity.json`. Para regerar: `node tests/generate_engine_parity.mjs`.

## Contas e perfil

As contas ficam no Neo4j como `(:User)-[:HAS_SESSION]->(:Session)`. O perfil fica em propriedades do `User`: `genres`, `themes`, `anchor_ids` e `hw_*`. Ele não tem ligação com `:Game`, para que recarregar o catálogo nunca afete as contas.

| Rota | Função |
|---|---|
| `POST /api/auth/register` | Cria a conta e abre a sessão |
| `POST /api/auth/login` | Abre a sessão; a mesma mensagem para e-mail ou senha inválidos |
| `POST /api/auth/logout` | Revoga a sessão no servidor |
| `GET /api/auth/me` | Nome, ID e perfil da sessão atual (401 sem sessão) |
| `GET /api/me/account` | E-mail da conta, pedido só pela tela de Conta |
| `POST /api/auth/password` | Troca a senha e encerra as demais sessões |
| `PATCH /api/me/profile` | Atualização parcial do perfil; `hardware: null` limpa o computador |

**Segurança:**
- **Senhas:** Argon2id, com no mínimo 8 caracteres.
- **Sessão:** cookie `gc_session` (`HttpOnly`, `SameSite=Lax`, 7 dias). O banco guarda só o SHA-256 do token. Use `SESSION_COOKIE_SECURE=true` atrás de HTTPS.
- **E-mail:** as respostas de conta não trazem o e-mail.
- **Usuário:** vem sempre da sessão. Campos extras são rejeitados.
- **Origem:** rotas que alteram dados recusam `Origin` fora de `ALLOWED_ORIGINS`.
- **Limitador de login:** cinco falhas em cinco minutos bloqueiam aquele IP e e-mail (e a troca de senha, por conta). As falhas ficam no Neo4j, em nós `:LoginAttempt`, com a chave em SHA-256 e sem e-mail nem IP em texto. Todos os processos da API usam a mesma contagem.
- **Conta de demonstração (opcional):** defina `DEMO_EMAIL` e `DEMO_PASSWORD` no `.env` e rode `docker compose run --rm --no-deps api python -m app.seed_demo`.
- **Limitação:** não há recuperação de senha por e-mail nem verificação de e-mail.

## Interações com jogos

Cada par conta-jogo tem uma relação `(:User)-[:INTERACTED {reaction, views, reacted_at, first_viewed_at, last_viewed_at}]->(:Game)`. Só jogos do catálogo aceitam interação. A recarga do catálogo troca só `HAS_GENRE`/`HAS_TAG`, então as interações sobrevivem.

| Rota | Função |
|---|---|
| `POST /api/me/games/{appid}/view` | Soma uma visualização |
| `PUT /api/me/games/{appid}/reaction` | `liked`, `disliked` ou `null` (remove a reação) |
| `GET /api/me/interactions` | Histórico, do mais recente ao mais antigo |
| `DELETE /api/me/interactions` | Apaga o histórico e diz quantos registros removeu |

Efeito nas recomendações:
- **Não curtidos:** saem de todas as listas.
- **Curtidos:** até 10 viram âncoras extras de afinidade, sem substituir as 3 do perfil.
- **Sem reações:** o resultado é idêntico ao `rules_v1` puro.

## Leitura do catálogo

| Rota | Resposta |
|---|---|
| `GET /api/hardware` | CPUs e GPUs `manual_v1` carregadas |
| `GET /api/games?appids=123,456` | Até 30 jogos, do grafo ou, se faltarem, da Steam |
| `GET /api/games/{appid}` | Detalhes de um jogo |
| `GET /api/games/search?q=nome` | Busca por nome na Steam |
| `GET /api/games/anchors` | Sugestões editoriais de âncora (`data/catalog/anchor_suggestions.json`) |
| `GET /api/games/discover` | Candidatos ligados às âncoras por gênero e temática |

O cache da Steam guarda até 128 consultas por seis horas, com no máximo três chamadas simultâneas por processo. Falhas ficam visíveis e não viram dados fictícios.

## Testes

```bash
docker compose run --rm --no-deps api python -m unittest discover -s tests -v
```

Os testes HTTP usam fixtures e um repositório de contas em memória; não dependem de Neo4j nem da Steam. A persistência real tem um teste próprio, que precisa do banco no ar:

```bash
docker compose run --rm -e GAMECOMPASS_TEST_NEO4J=1 api python -m unittest discover -s tests -p "test_users_neo4j.py" -v
```

O teste de ponta a ponta pela API fica em [`../tests/e2e/test_api_flow.py`](../tests/e2e/test_api_flow.py). Ele só usa a biblioteca padrão e roda contra a pilha no ar, a partir da raiz do repositório:

```bash
GAMECOMPASS_E2E=1 python3 tests/e2e/test_api_flow.py
```

## Avaliação do motor

- **Casos de ouro:** 22 casos com o veredito esperado escrito à mão. Estão em [`data/evaluation`](../data/evaluation/README.md) e rodam no CI pelo `tests/test_gold_cases.py`. O resultado atual é 19 corretos, 3 divergências conhecidas e nenhum falso positivo. Relatório: `python -m app.evaluate_gold`, na pasta `backend`.
- **Avaliação offline:** roda o motor sobre o catálogo carregado com perfis simulados, ou com os seus em `--scenarios arquivo.json`:

  ```bash
  docker compose run --rm --no-deps api python -m app.evaluate_rules --auto 30 --top 5
  ```

## Desempenho

Tempo de resposta por rota e comportamento sob carga, com método e como repetir: [`perf/README.md`](perf/README.md). A API sobe com 4 processos (`API_WORKERS`, padrão 4). Com 20 pedidos de sugestões simultâneos, cada um espera ~1,7 s; com 1 processo, eram ~7 s.
