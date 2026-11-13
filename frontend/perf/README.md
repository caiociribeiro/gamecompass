# Medição de desempenho das telas paradas (RNF10)

Registro da medição de 13/11/2026 que compara o frontend antes e depois da troca das animações por `transform` (PR #20).

## O que é medido

O script [`../scripts/measure-idle.mjs`](../scripts/measure-idle.mjs) abre cada tela num Chromium controlado pelo Playwright. Espera 1,5 s para a tela assentar e lê os contadores do Chrome DevTools Protocol (`Performance.getMetrics`) antes e depois de 3 s sem nenhuma interação:

| Campo | Contador do Chrome | Significado |
|---|---|---|
| `recalc_style` | `RecalcStyleCount` | Recálculos de estilo |
| `layout` | `LayoutCount` | Recálculos de layout (posição e tamanho dos elementos) |
| `task_ms` | `TaskDuration` | Tempo de CPU do navegador no período, em ms |
| `script_ms` | `ScriptDuration` | Parte desse tempo gasta em JavaScript, em ms |
| `elementos` | `document.querySelectorAll("*").length` | Elementos na página (só nas Sugestões) |

Telas: Landing, Início de uma conta recém-criada e Sugestões, depois de um perfil completo: RPG + Fantasia; Cyberpunk 2077, The Witcher 3 e ELDEN RING; Ryzen 5 3600, RTX 3060 12GB, 16 GB e Windows 11. Cada versão foi medida 3 vezes, e a tabela mostra a mediana. As amostras estão nos arquivos JSON desta pasta.

## Versões comparadas

- **Antes:** commit `2878595`, o redesenho em pixel art (PR #18), com as animações em `left`, `margin` e `background-position`.
- **Depois:** commit `4d2e72f`, o `master` com o PR #20.

As duas foram servidas pelo Vite em modo de desenvolvimento, na mesma porta (127.0.0.1:5173), a partir de cópias isoladas do repositório (`git worktree`). Usaram a mesma API e o mesmo Neo4j, uma de cada vez. O contêiner do frontend ficou parado durante a medição.

## Ambiente

| Item | Valor |
|---|---|
| Data | 13/11/2026, 03h59 e 04h01 (UTC) |
| Navegador | Chromium 158.0.8127.18 (headless), Playwright 1.65.0 |
| Node.js | v26.13.0 |
| Sistema | Linux 7.0.0-42-generic |
| Processador | 13th Gen Intel Core i5-1334U (12 threads) |
| Memória | 15 GB |
| Janela | 1440 × 900 |

## Resultados (mediana de 3)

| Tela | Versão | Recálculo de estilo | Layout | CPU (ms) | Elementos |
|---|---|---|---|---|---|
| Landing | Antes | 57 | 57 | 280 | — |
| Landing | Depois | 30 | **0** | **68** | — |
| Início (conta nova) | Antes | 179 | 35 | 264 | — |
| Início (conta nova) | Depois | 34 | **0** | **69** | — |
| Sugestões | Antes | 18 | 0 | 17 | 3.379 |
| Sugestões | Depois | 15 | 0 | 12 | **1.398** |

Amostras de CPU (ms): Landing 280, 270, 288 → 71, 68, 68. Início 253, 286, 264 → 92, 67, 69. Sugestões 17, 18, 14 → 12, 17, 12.

## Como interpretar

- **Landing e Início:** pararam de recalcular o layout com a tela parada. O tempo de CPU caiu cerca de 4 vezes.
- **Sugestões:** a paginação (12 jogos por seção) reduziu os elementos da página a menos da metade. O custo parado já era baixo e mudou pouco.
- **O que não é:** não é medição de quadros por segundo nem de tempo de resposta da API. É o custo do navegador numa máquina, no modo de desenvolvimento do Vite. Os números absolutos mudam com o hardware; a comparação vale porque as duas versões rodaram nas mesmas condições.

## Como repetir

Com a stack no ar (`docker compose up -d`) e a API em 127.0.0.1:8000:

```bash
cd frontend
node scripts/measure-idle.mjs http://127.0.0.1:5173 3 perf/nova-medicao.json
```

O script cria uma conta descartável e a apaga do Neo4j no fim. Para medir uma versão antiga, sirva aquele commit na porta 5173: a API só aceita escrita vinda de `localhost:5173` e `127.0.0.1:5173`.

```bash
git worktree add --detach /tmp/gc-antes 2878595
```

```bash
ln -s "$PWD/node_modules" /tmp/gc-antes/frontend/node_modules
```

```bash
docker compose stop frontend
```

```bash
cd /tmp/gc-antes/frontend && node node_modules/vite/bin/vite.js --port 5173 --strictPort --host 127.0.0.1
```
