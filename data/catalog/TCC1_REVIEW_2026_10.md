# Faixas aproximadas de hardware para o TCC1

Revisão de 31/10/2026. O catálogo tem 41 CPUs e 40 GPUs, todas classificadas.
Esta etapa atribui notas às 18 peças que estavam pendentes, conservando as
63 classificações anteriores, os nomes, os aliases e o contrato do grafo.

## Critério simplificado

As notas são classes ordinais escolhidas manualmente pelo GameCompass.
Consultamos avaliações de jogos e agrupamos peças de faixa semelhante.
Não exigimos diferença máxima de 10%, média publicada ou um mesmo teste
com todos os integrantes do grupo. Não há conversão de GHz, núcleos ou
resultados sintéticos em uma pontuação de jogos.

Avaliações de períodos diferentes podem orientar o encaixe. Isso é uma
inferência aproximada de curadoria e não uma medição conjunta. As notas
100 e 200 não representam uma proporção de desempenho. CPU e GPU têm
escalas independentes. A versão `manual_v1` ainda está em elaboração;
hashes e commits identificam a revisão usada no processamento.

## CPUs acrescentadas

| Classe | Modelos | Justificativa e fontes |
| --- | --- | --- |
| 40 | AMD FX-6300 | Entrada legada, abaixo do grupo seguinte na comparação histórica. C1 |
| 50 | AMD FX-8350; Intel Core i5-2500K | Faixa legada próxima, com vantagem variável do Intel. C1 |
| 60 | AMD Ryzen 5 1400; Intel Core i5-4690; Intel Core i5-6600 | Faixa intermediária legada. O encaixe entre marcas é uma aproximação entre C2 e C3. |
| 70 | AMD Ryzen 5 1500X; Intel Core i7-4770K | Faixa legada acima do grupo 60. C4 e C5 contextualizam cada modelo; não são um teste direto desse par. |
| 300 | Intel Core i7-12700 | Faixa recente acima dos modelos CPU 100 e abaixo dos modelos modernos CPU 400. Encaixe preliminar apoiado em C6. |
| 400 | AMD Ryzen 7 9700X | Próximo do 9600X e do i7-14700K em jogos. C7 |
| 500 | AMD Ryzen 7 7700X3D | Próximo do 7600X3D e do 7800X3D. C8 |

Referências de CPU, usando as seções de jogos e os resultados de fábrica:

- C1: [ComputerBase, histórico de jogos de 2017](https://www.computerbase.de/artikel/prozessoren/cpu-gaming-benchmarks-amd-ryzen-vs-intel-core.85869/). O quadro antigo distingue FX-6300, FX-8350 e i5-2500K. A divisão em 40 e 50 é nossa curadoria.
- C2: [TechSpot, Ryzen 5 1400, jogos](https://www.techspot.com/review/1386-amd-ryzen-5-1400/page3.html). Mostra diferenças por jogo e o confronto com i5-7400 e 1500X. Usamos essa faixa como orientação, sem copiar resultados de overclock.
- C3: [Overclockers.ru, i5-6600 e outras CPUs em jogos](https://overclockers.ru/lab/show/73717_4/test-processorov-intel-core-i7-6700-core-i5-6600-core-i5-6500-i-core-i5-6400-v-aktualnyh-igrah). Inclui i5-4690 sem K. A conclusão em configuração nominal apoia aproximar os i5 dessas gerações.
- C4: [TechSpot, Ryzen 5 1500X, jogos](https://www.techspot.com/review/1379-and-ryzen-5-1600x-1500x/page4.html). Referência da faixa Zen inicial 4C/8T. O 1500X não recebe a nota do 1600X.
- C5: [TechSpot, i7-4770K, jogos](https://www.techspot.com/review/679-intel-haswell-core-i7-4770k/page12.html). Referência de desempenho do Haswell 4C/8T, com limitação pela GPU em parte dos testes.
- C6: [TechSpot, Core i7-12700](https://www.techspot.com/review/2391-intel-core-i7-12700/). Testa o modelo sem K em dez jogos e mostra o efeito de limites de potência e refrigeração. A CPU 300 é uma nova faixa individual, não uma nota herdada do 12700K.
- C7: [Tom's Hardware, 9600X e 9700X, jogos](https://www.tomshardware.com/pc-components/cpus/amd-ryzen-5-9600x-cpu-review/2). Resultados de fábrica contextualizam o 9700X perto dos modelos CPU 400 já cadastrados.
- C8: [ComputerBase, Ryzen 7 7700X3D](https://www.computerbase.de/artikel/prozessoren/amd-ryzen-7-7700x3d-test.98221/seite-2). O 7700X3D fica próximo do 7800X3D e do 7600X3D no agregado de jogos.

## GPUs acrescentadas

| Classe | Modelos | Justificativa e fontes |
| --- | --- | --- |
| 20 | AMD Radeon R9 280 3GB; NVIDIA GeForce GTX 770 2GB; NVIDIA GeForce GTX 960 4GB | Faixa legada inferior à GTX 970. G1, G2 e G3. |
| 40 | AMD Radeon RX 470 4GB | Próxima da GTX 970, já na classe 40. G4 |
| 50 | AMD Radeon RX 480 4GB | Próxima da GTX 1060 3GB, já na classe 50. G5 |
| 100 | AMD Radeon RX 580 4GB | Mesma faixa aproximada da RX 580 8GB e GTX 1060 6GB. G6 e as referências anteriores de GPU 100. |
| 500 | AMD Radeon RX 7900 GRE 16GB | Próxima da RTX 4070 SUPER em rasterização. G7 |

Referências de GPU, priorizando rasterização nativa:

- G1: [TechSpot, resumo da GTX 960](https://www.techspot.com/review/946-nvidia-geforce-gtx-960/page9.html). A GTX 960 testada fica próxima da R9 280 e abaixo da GTX 970. O modelo desse estudo tem 2GB; o encaixe da variante 4GB usa também G3.
- G2: [TechSpot, Watch Dogs](https://www.techspot.com/review/827-watch-dogs-benchmarks/page3.html). GTX 770 e R9 280 ficam próximas nesse jogo. É apoio pontual, não comprovação de equivalência em todos os títulos.
- G3: [Lock Gamer, GTX 960 4GB](https://lockgamer.com/2015/11/18/review-evga-gtx-960-4gb-4-e-melhor-que-2/). Avalia a variante 4GB e contextualiza a diferença para 2GB. Manter capacidades separadas continua necessário.
- G4: [TechSpot, RX 470](https://www.techspot.com/review/1220-amd-radeon-rx-470/page9.html). A RX 470 fica próxima da GTX 970 no resumo de jogos a 1080p.
- G5: [GamersNexus, RX 480 4GB contra GTX 1060 3GB](https://gamersnexus.net/guides/2649-gtx-1060-3gb-vs-rx-480-4gb-benchmark). As placas alternam posições conforme o jogo e a API, com faixa geral próxima.
- G6: [GECID, RX 580 4GB e 8GB](https://ru.gecid.com/video/radeon_rx_570_4gb_vs_radeon_rx_580_4gb_i_8gb/?s=2). Avalia as duas variantes físicas. O encaixe na GPU 100 é aproximado e considera diferenças de clocks e memória. Refere-se à RX 580 de 2304 SP, não à 2048SP.
- G7: [GamersNexus, RX 7900 GRE](https://gamersnexus.net/gpus/amd-radeon-rx-7900-gre-gpu-review-benchmarks-vs-rx-7900-xt-7800-xt-rtx-4070-super). A comparação com a RTX 4070 SUPER apoia a proximidade em rasterização; resultados de ray tracing não recebem essa equivalência.

## O que fica para o TCC2

Calibrar a escala em amostras comparáveis, testar o limite das faixas e
avaliar erros na previsão de compatibilidade. Separar melhor VRAM,
instruções de CPU, SO, DirectX e armazenamento. Essas verificações não
estão implícitas na classe de desempenho.

O catálogo completo significa que as 81 peças atuais têm nota. Textos
genéricos da Steam, modelos ausentes ou variantes ambíguas continuam
gerando revisão, sem receber uma classe por adivinhação.

Depois de atualizar o CSV processado, recarregue hardware, reprocesse os
snapshots existentes, recarregue jogos e reinicie a API. Não é necessário
coletar novamente nem apagar o Neo4j. `collected_at` registra a consulta
da curadoria, não uma nova execução dos benchmarks.
