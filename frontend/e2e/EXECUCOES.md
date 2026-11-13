# Execuções registradas do roteiro Playwright

Roteiro: [`perfil-ate-recomendacoes.spec.ts`](perfil-ate-recomendacoes.spec.ts), um teste de ponta a ponta no navegador ("do cadastro às recomendações, só pelos botões da tela"). Ele cria uma conta descartável e a apaga do Neo4j no fim.

## Como executar

Com a stack no ar (`docker compose up -d`) e o frontend em http://127.0.0.1:5173:

```bash
cd frontend && npx playwright test --reporter=list
```

## Passos cobertos

1. Cria a conta.
2. O painel mostra por onde começar.
3. Preferências: o rodapé só libera o avanço depois das escolhas.
4. Jogos âncora: três escolhas liberam a próxima etapa.
5. Computador: salva sozinho quando as peças estão completas.
6. Recomendações: o motor devolve jogos que não são as âncoras.
7. Não curtir tira o jogo da lista na hora.
8. Curtir avisa que a afinidade muda no próximo cálculo, e atualizar aplica.
9. Abrir a ficha de um jogo registra a visualização.
10. A conta lista as reações, os jogos só visualizados e permite limpar o histórico.
11. O painel termina com o perfil completo.
12. Sair da conta leva à Landing, não ao login.

## Execuções

| Data (UTC) | Código | Resultado | Duração | Ambiente |
|---|---|---|---|---|
| 2026-11-13 04:10:58 a 04:11:11 | `803a895` (master após o PR #21), frontend do contêiner `gamecompass-frontend` reconstruído desse código | 1 de 1 passou | 10,7 s | Playwright 1.65.0, Chromium 158.0.8127.18, Node v26.13.0, Linux 7.0.0-42 |
| 2026-11-13 ~04:43 | Branch `chore/organizacao` antes do commit (base `6860b71`), API com 4 processos (`WEB_CONCURRENCY=4`) | 1 de 1 passou | 10,0 s | Mesmo ambiente |

Execuções anteriores no mesmo dia (04:02 UTC, código do PR #21 antes do merge) também passaram, mas não foram registradas aqui com o commit exato.
