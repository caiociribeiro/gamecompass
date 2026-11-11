# Relatório dos casos de ouro, 10/11/2026

Motor `rules_v1`, índice `manual_v1`, catálogo de hardware com 313 peças e 188 regras de curadoria. Reproduzir: `docker compose run --rm -v "$PWD:/workspace" -e GAMECOMPASS_ROOT=/workspace -w /workspace/backend api python -m app.evaluate_gold`. Os casos e os motivos estão em `gold_cases.json`; o teste automático é `backend/tests/test_gold_cases.py`.

## Como ler

- **Falso positivo** é o erro grave: o motor aprova um computador para um jogo que ele não roda. Nenhum ocorreu.
- **Falso negativo** reprova a mais; **pendente a mais** pede conferência a mais. Os dois são erros na direção segura.
- O esperado de cada caso foi escrito a partir do texto de requisitos da Steam (copiado dos snapshots de 06/11/2026) e de relações de desempenho amplamente documentadas, como placas de entrada contra placas duas gerações acima, ou de regras determinísticas (Windows 11 exigido, RAM, campo não publicado). Foi escrito antes de rodar o motor e nunca copiado da saída dele. Ao escolher os jogos, eu já conhecia as notas processadas de vários deles, então a escolha dos jogos não é cega; os vereditos não vieram delas.
- Casos em que a diferença real entre as peças é pequena ou discutível ficam de fora de propósito (por exemplo GTX 1050 Ti contra GTX 1060 3GB, ou RTX 3060 contra RX 5700 XT).

## Resultado

19 de 22 casos corretos; 3 divergências conhecidas (documentadas no arquivo de casos); 0 inesperadas. Falsos positivos: 0.

| Resultado | Casos |
| --- | ---: |
| Acertou | 19 |
| Falso positivo (aprovou o que deveria reprovar) | 0 |
| Falso negativo (reprovou o que deveria aprovar) | 2 |
| Decidiu onde o esperado era pendência | 0 |
| Ficou pendente onde o esperado era uma decisão | 1 |
| Veredito certo, mas as verificações por peça divergem | 0 |

| Tipo de caso | Corretos | Total |
| --- | ---: | ---: |
| hardware_gap | 12 | 14 |
| policy | 4 | 4 |
| rule | 3 | 4 |

| Caso | Jogo | Nível | Esperado | Obtido | Resultado |
| --- | --- | --- | --- | --- | --- |
| low-cyberpunk-min | Cyberpunk 2077 | minimum | incompatible | incompatible | ok |
| low-rdr2-min | Red Dead Redemption 2 | minimum | incompatible | incompatible | ok |
| low-cs2-min | Counter-Strike 2 | minimum | incompatible | incompatible | ok |
| low-stardew-min | Stardew Valley | minimum | compatible | incompatible | Falso negativo (reprovou o que deveria aprovar) (conhecida) |
| low-hades-min | Hades | minimum | compatible | incompatible | Falso negativo (reprovou o que deveria aprovar) (conhecida) |
| gtx1050ti-cyberpunk-rec | Cyberpunk 2077 | recommended | incompatible | incompatible | ok |
| gtx1050ti-eldenring-rec | ELDEN RING | recommended | incompatible | incompatible | ok |
| gtx1050ti-factorio-min | Factorio | minimum | compatible | compatible | ok |
| gtx1050ti-skyrim-min | The Elder Scrolls V: Skyrim Special Edition | minimum | compatible | compatible | ok |
| rtx3060-bg3-rec | Baldur's Gate 3 | recommended | compatible | compatible | ok |
| top-rdr2-rec | Red Dead Redemption 2 | recommended | compatible | compatible | ok |
| top-eldenring-rec | ELDEN RING | recommended | compatible | compatible | ok |
| top-bg3-rec | Baldur's Gate 3 | recommended | compatible | compatible | ok |
| top-witcher3-rec | The Witcher 3: Wild Hunt — Remastered | recommended | compatible | compatible | ok |
| rtx3060-dd2-rec-win11 | Dragon's Dogma 2 | recommended | compatible | compatible | ok |
| rtx3060-dd2-min-win10 | Dragon's Dogma 2 | minimum | incompatible | incompatible | ok |
| rtx3060-witcher3-min-win10 | The Witcher 3: Wild Hunt — Remastered | minimum | incompatible | incompatible | ok |
| top-overcooked2-min | Overcooked! 2 | minimum | compatible | needs_review | Ficou pendente onde o esperado era uma decisão (conhecida) |
| top-re2-rec | Resident Evil 2 | recommended | needs_review | needs_review | ok |
| top-re2-min | Resident Evil 2 | minimum | compatible | compatible | ok |
| top-hat-in-time-min | A Hat in Time | minimum | needs_review | needs_review | ok |
| top-unpacking-min | Unpacking | minimum | needs_review | needs_review | ok |

### low-stardew-min
- Esperado: compatible; obtido: incompatible.
- Verificações: {'Processador': True, 'Placa de vídeo': False, 'Memória RAM': True, 'Sistema operacional': True}
- Motivo do esperado: O mínimo é 2 GHz, 2 GB, 256 MB de vídeo e shader model 3.0. Um Core 2 Duo de 3 GHz, 4 GB e uma GT 1030 cumprem com folga.
- Causa conhecida: A curadoria de 31/10/2026 (TCC1) usa a GeForce GTS 450 (classe 3) como referência de "256 mb video memory, shader model 3.0+". É um exemplo representativo, acima do mínimo literal (que uma placa de classe 1 cumpre), e a GT 1030 DDR4 (classe 2) fica abaixo dela. Erro na direção segura (reprova a mais).

### low-hades-min
- Esperado: compatible; obtido: incompatible.
- Verificações: {'Processador': False, 'Placa de vídeo': False, 'Memória RAM': True, 'Sistema operacional': True}
- Motivo do esperado: O mínimo é um dual core de 2,4 GHz, 4 GB e 1 GB de vídeo com DirectX 10. Um Core 2 Duo E8400 (dual core, 3,0 GHz), 4 GB e uma GT 1030 cumprem.
- Causa conhecida: A curadoria de 31/10/2026 (TCC1) usa o Core i3-3240 (classe 25) para "Dual Core 2.4 GHz" e a GTS 450 (classe 3) para "1GB VRAM / DirectX 10+". Ambos estão acima do mínimo literal (um Core 2 Duo de 2,4 GHz é classe 5). Erro na direção segura (reprova a mais).

### top-overcooked2-min
- Esperado: compatible; obtido: needs_review.
- Verificações: {'Processador': True, 'Placa de vídeo': True, 'Memória RAM': True, 'Sistema operacional': None}
- Motivo do esperado: O texto lista "GeForce GTX 630 / Radeon HD 6570". A GTX 630 não existe com esse nome (política: nomes com erro de grafia ficam pendentes), mas a Radeon HD 6570 é identificada e o computador a supera; uma alternativa identificada basta para aprovar.
- Causa conhecida: O requisito de sistema vem como "WIN7-64 bit" (mínimo) e "Win7 -64 bit" (recomendado); o windows_check não reconhece "WIN7" sem o espaço e deixa o sistema operacional pendente. Erro na direção segura (pede conferência a mais). 4 outros blocos do catálogo de 120 jogos têm o mesmo tipo de texto não reconhecido.

## Divergências conhecidas

As três são erros na direção segura e têm causa entendida. Nenhuma foi corrigida nesta rodada, porque mexer na curadoria genérica do TCC1 ou no `windows_check` muda resultados de vários jogos e merece decisão separada.

1. **Referências genéricas acima do mínimo literal (Stardew Valley, Hades).** A curadoria de 31/10/2026 usa a GTS 450 (classe 3) para "256 MB, shader model 3.0+" e "1GB VRAM / DirectX 10+", e o Core i3-3240 (classe 25) para "Dual Core 2.4 GHz". Um Core 2 Duo E8400 com GT 1030 DDR4 roda os dois jogos, mas é reprovado. Efeito: só computadores muito antigos são reprovados a mais.
2. **`windows_check` não reconhece "WIN7-64 bit" / "Win7 -64 bit" (Overcooked! 2).** O sistema operacional fica pendente em vez de aprovado. Outros 5 blocos do catálogo de 120 jogos têm texto de sistema não reconhecido: "Windows 10(64-bit versions only)" (Anno 1800, pendência intencional por causa de "only"), "Window 10 64-bit +" (Dead Space, erro de grafia na fonte) e um campo vazio (Baba Is You).

## Limites

- 22 casos são uma amostra, não uma prova de que o motor está certo em geral. 15 jogos e 4 computadores.
- Os casos validam a aplicação correta dos requisitos publicados. Não provam que o jogo roda a certo FPS.
- As notas do índice são ordinais e curadas; a verificação confirma a coerência delas com relações conhecidas, não é uma medição.
