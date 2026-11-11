# Avaliação do motor

- `gold_cases.json`: casos de ouro. Cada caso liga um computador (`machines`) a um jogo (`games`, com o texto de requisitos copiado da resposta real da Steam e o `sha256` da resposta) e a um nível, com o veredito esperado (`compatible`, `incompatible` ou `needs_review`), as verificações por peça que devem falhar ou passar e o motivo. Um caso com `known_divergence` registra o que o motor devolve hoje e por quê; o teste exige que continue assim.
- `GOLD_REPORT_2026_11.md`: relatório da última execução, com as divergências conhecidas e os limites.
- Teste: `backend/tests/test_gold_cases.py` (roda no CI, sem Neo4j nem Steam). Relatório: `python -m app.evaluate_gold` na pasta `backend`.

**Como acrescentar um caso.** Escreva o veredito esperado e o motivo antes de rodar o motor, a partir do texto da Steam e de relações de desempenho que você consiga justificar. Só use pares de peças com diferença grande e documentada. Para um jogo novo, copie `pc_requirements` do snapshot (`appdetails.json`) para `games`. Se o motor divergir, descubra se o erro é do gabarito, da curadoria ou do motor antes de mexer em qualquer um.
