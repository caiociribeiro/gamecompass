# Revisão de CPU — etapa 17, histórico de 31/10/2026

Este documento registra o critério e as pendências da etapa 17.
A [revisão seguinte](TCC1_REVIEW_2026_10.md) simplifica a curadoria e
classifica a RX 580 4GB na GPU 100. As duas CPUs abaixo mantêm a CPU 80.

| Modelo | Classe manual_v1 | Decisão |
| --- | ---: | --- |
| Intel Core i7-6700 | 80 | Classe experimental, modelo sem K |
| AMD Ryzen 5 1600 | 80 | Classe experimental, original sem AF/X |
| AMD Radeon RX 580 4GB | — | Manter pendente |

O catálogo mantém 41 CPUs e 40 GPUs: 63 peças classificadas e 18 pendentes.
As notas das demais peças foram preservadas. A classe é ordinal e não
representa FPS, porcentagem de desempenho ou garantia de compatibilidade.

## Comparação direta das CPUs

Fonte: [PC-HELP.CZ, Adys301, 15/06/2017](https://pc-help.cnews.cz/viewtopic.php?p=1473466).
Os testes usam as CPUs sem overclock, GTX 1070, 1080p Ultra e Windows 10.
Memórias: AMD 2933 CL16; Intel 2133 CL15. Valores conferidos nos gráficos:

| Jogo | i7-6700 FPS médio | Ryzen 5 1600 FPS médio |
| --- | ---: | ---: |
| Hitman | 108 | 98 |
| DiRT Rally | 108 | 108 |
| Mass Effect: Andromeda | 100 | 87 |
| Rise of the Tomb Raider | 111 | 98 |
| Ashes of the Singularity: Escalation | 32 | 35 |
| Total War: Warhammer | 106 | 106 |
| The Witcher 3 | 84 | 84 |
| Mirror's Edge Catalyst | 127 | 126 |
| DOOM | 143 | 143 |
| Borderlands 2 | 227 | 227 |
| Need for Speed | 124 | 120 |

O autor não fornece média geral. O GameCompass calcula, com peso igual
para os 11 jogos, `R = exp(sum(log(FPS_Intel / FPS_AMD)) / 11)`.
Resultado: `R = 1.0287763904852294`; amplitude aproximada de 2,88%,
dentro do limite experimental de 10%. Não é uma média publicada pela
fonte. O cálculo usa FPS conferidos, sem aproveitar percentuais
arredondados nem incluir os testes sintéticos do artigo.

Cinco jogos apresentam FPS iguais, compatíveis com possível limitação
pela GPU. Memórias diferentes e amostra antiga limitam a comparação.
Esta classe descreve esse recorte e não estabelece equivalência universal.

## Posição provisória na escala

O valor 80 foi escolhido como rótulo abaixo de CPU 90. O apoio adicional
é a [avaliação do i5-8400, Tom's Hardware, 25/10/2017](https://www.tomshardware.com/reviews/intel-coffee-lake-core-i5-8400-cpu,5281-11.html),
que coloca o Ryzen 5 1600 de fábrica abaixo do i5-8400 em jogos. O i7-6700
não participa desse segundo estudo: posicionar o grupo inteiro abaixo da
90 é uma inferência provisória de curadoria. Não calculamos percentuais
entre estudos nem afirmamos ter validado todas as comparações entre classes.
Calibrar ambos contra os integrantes de CPU 90 na mesma configuração
continua como tarefa do TCC2.

## RX 580 de 4 GB

Permanece sem nota. A [comparação direta de variantes do GECID](https://ru.gecid.com/video/radeon_rx_570_4gb_vs_radeon_rx_580_4gb_i_8gb/?s=2)
mostra que memória e clocks influenciam os resultados, mas não reúne os
três modelos da classe GPU 100 nem publica o agregado necessário para
ampliar esse grupo. Não usamos a proximidade entre pares de estudos
diferentes como comprovação de equivalência de todos os integrantes.

## Efeito na pipeline

Após gerar o catálogo processado, carregar as peças e reprocessar os
jogos, o mínimo Windows do Cyberpunk 2077 pode obter CPU 80, GPU 50 e
RAM 12 GB com o snapshot desta etapa. Requisitos recomendados e a
validação de SO permanecem independentes. O mínimo de Elden Ring ainda
depende da RX 580 4GB. Identidade conhecida com nota vazia continua
gerando `needs_review`, nunca uma aprovação automática.

`collected_at` registra a consulta de 2026, não uma nova medição.
Esta revisão ainda pertence ao índice `manual_v1` em elaboração.
