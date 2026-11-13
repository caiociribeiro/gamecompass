# Interface do GameCompass

React 19, TypeScript e Vite, com visual em pixel art. As fontes Press Start 2P e VT323 vêm empacotadas, sem CDN. Toda regra de negócio fica na API; a interface guarda o perfil, mostra os resultados e envia as escolhas.

## Rodar

O serviço `frontend` do `docker compose` serve o build pelo `vite preview` em http://localhost:5173 e repassa `/api` para a API. Depois de mudar o código, refaça a imagem:

```bash
docker compose up -d --build frontend
```

Para desenvolver com recarga automática (Node 22.22.2+ ou 24.15+), pare o contêiner, que usa a mesma porta, e use o Vite com a API no ar:

```bash
docker compose stop frontend
```

```bash
npm ci && npm run dev
```

O Vite encaminha `/api` para `API_PORT` do `.env` da raiz (8000 por padrão), ou para `API_PROXY_TARGET`. Se aparecer `ECONNREFUSED 127.0.0.1:8000`, confira `docker compose ps api` e http://localhost:8000/health.

## O que a pessoa faz

1. **Landing e cadastro:** a conta fica no servidor.
2. **Início:** passo a passo das quatro fases e o que já está pronto.
3. **Fase 1, Perfil:** gêneros e temáticas, das listas de `src/data/preferences.ts`.
4. **Fase 2, Âncoras:** três jogos escolhidos por busca, pelo botão Usar ou arrastando a capa até um espaço. As oito sugestões editoriais vêm de `data/catalog/anchor_suggestions.json`.
5. **Fase 3, Computador:** CPU e GPU do catálogo, RAM e sistema. As GPUs aparecem primeiro pela participação na Steam Hardware Survey (`src/data/steamGpuSurvey.json`, gerado por `scripts/steam_hw_survey.py`); as CPUs, pela pontuação do catálogo. O computador salva sozinho quando está completo.
6. **Fase 4, Sugestões:** a busca só acontece quando a pessoa pede.
   - **Organização:** a lista vem em atendidos, aguardando validação e com restrição, 12 por página, com filtros por nome e situação.
   - **Corações:** curtir reforça a afinidade das próximas sugestões; não curtir tira o jogo da lista.
7. **Ficha do jogo:** três abas: comparação com o PC, requisitos na Steam e por que combina.
8. **Conta:** nome, senha, e-mail (só ao clicar em Mostrar), histórico de reações e de jogos vistos, limpar perfil e sair.

**Comportamentos gerais:**
- **Salvamento:** as edições do perfil são agrupadas e enviadas depois de 0,6 s sem cliques. Ao esconder ou fechar a aba, saem na hora, com `fetch keepalive`.
- **Navegador:** guarda só a preferência de som e o aviso de ajuda já lido; os dados da conta ficam no servidor.
- **Movimento:** quem ativa "reduzir movimento" no sistema não vê animações.
- **Celular:** a interface foi conferida a 375 px de largura.

## Estrutura

| Caminho | O que tem |
|---|---|
| `src/pages/` | Uma tela por rota (`App.tsx` define as rotas) |
| `src/components/` | Cabeçalho, trilha de fases, cards, corações, paginação e outros |
| `src/context/` | Sessão (conta e salvamento), catálogo (jogos, hardware, sugestões) e som |
| `src/lib/` | Funções puras: perfil, cálculo do pedido, ordenação de peças e textos |
| `src/styles/` | `global.css` (tema e componentes) e um arquivo por grupo de telas |
| `tests/` | Testes de unidade e de interface (React em jsdom); `tests/helpers/` monta os componentes |
| `tests/reference/` | Implementação antiga do motor, congelada só para os testes de paridade |
| `e2e/` | Roteiro Playwright e o registro das execuções |
| `perf/` e `scripts/measure-idle.mjs` | Medição do custo das telas paradas |

## Testes

```bash
npm test
```

```bash
npm run build
```

`npm test` roda os testes de unidade e de interface. Os de interface montam os componentes reais num jsdom, com respostas HTTP fictícias. `npm run build` checa os tipos e gera o build.

O teste de ponta a ponta percorre cadastro, as quatro fases, as reações, a ficha, a conta e a saída, só pelos botões da tela. Ele roda contra a pilha no ar em http://127.0.0.1:5173, cria uma conta descartável e a apaga no fim. Não faz parte do CI, porque precisa do catálogo carregado no Neo4j. Na primeira vez, baixe o Chromium:

```bash
npx playwright install chromium
```

```bash
npm run e2e
```

As execuções registradas ficam em [`e2e/EXECUCOES.md`](e2e/EXECUCOES.md). Se uma etapa falhar, o print fica em `test-results/`.

## Desempenho

Custo das telas paradas (recálculos de layout e CPU), antes e depois da troca das animações por `transform`, com o script e o ambiente: [`perf/README.md`](perf/README.md).
