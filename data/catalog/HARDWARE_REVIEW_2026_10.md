# Revisão das classificações — 30/10/2026

O catálogo conserva 41 CPUs e 40 GPUs. Esta revisão classifica cinco CPUs
e oito GPUs: 61 peças classificadas e 20 pendentes (13 CPUs e sete GPUs).
As notas anteriores e as identidades foram preservadas. São classes
ordinais próprias do GameCompass, com os critérios de [SCORING.md](SCORING.md).

## Classificações acrescentadas

| Tipo | Classe | Modelos acrescentados | Referência |
| --- | ---: | --- | --- |
| CPU | 90 | Core i5-8400; Core i7-8700 | C1 |
| CPU | 100 | Ryzen 3 3300X; Core i7-8700K | C1 |
| CPU | 400 | Ryzen 5 9600X | C2 |
| GPU | 40 | GTX 970 | G1, 1080p Medium |
| GPU | 50 | Arc A380 6GB | G1, 1080p Medium |
| GPU | 300 | GTX 1080 Ti; RTX 2060 SUPER; RX 5700 XT; Arc A580 8GB | G1, 1440p Ultra |
| GPU | 350 | Arc A770 8GB; Arc A770 16GB | G1, 1440p Ultra |

C1: [Tom's Hardware, hierarquia histórica de CPUs](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html),
**Legacy CPU Gaming Hierarchy — Windows 10**, agregado geométrico de seis
jogos a 1080p. A amplitude calculada entre os sete integrantes da CPU 100
é aproximadamente 9,8%; entre os dois da CPU 90, 2,6%. Os integrantes da
90 ficam abaixo da 100 nessa amostra. As tabelas de aplicativos,
single-thread e multithread da mesma página foram excluídas.

C2: [Tom's Hardware, hierarquia atual de CPUs](https://www.tomshardware.com/reviews/cpu-hierarchy,4312.html),
agregado de jogos a 1080p, RTX 5090, presets High/Ultra conforme o jogo,
configuração principal sem PBO adicional. Incluir a 9600X conserva a
amplitude dos onze integrantes da CPU 400 abaixo de 10% (aproximadamente
7,8%). Detalhes da amostra em [RESEARCH_2026_10.md](RESEARCH_2026_10.md).

G1: [Tom's Hardware, hierarquia de GPUs 2022–2024](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-2.html),
oito jogos, média geométrica, Core i9-12900K; rasterização nativa sem RT,
upscaling ou geração de quadros. Na GPU 50, A380, RX 570 4GB e GTX 1060
3GB têm amplitude calculada de 3,5%. A GTX 970 fica abaixo, em classe
individual. Na GPU 300, a amplitude é cerca de 9,94%; na 350, 4,0%.
O agregado também apoia a ordem 200 < 300 < 350 < 500. A classe 300 está
na fronteira do limite: resultados arredondados e drivers posteriores
podem justificar uma nova revisão.

Esses percentuais são inferências de curadoria sobre os agregados
publicados. Não são medições do GameCompass. Não combinamos índices
de sites ou épocas diferentes para calcular proporções de desempenho.
Todas as classes continuam preliminares; uniformizar os recortes é
trabalho do TCC2. `collected_at` é a data de consulta, não do benchmark.

## Revisões ainda necessárias

Nota vazia significa revisão pendente. Identificar uma peça não comprova
equivalência. A relação de alternativas da Steam também não atribui nota.

| Peças | Próxima verificação necessária |
| --- | --- |
| AMD FX-6300; AMD FX-8350; Intel Core i5-2500K; Intel Core i7-4770K | Concluir a comparação histórica conjunta e justificar sua posição abaixo das classes atuais; não usar testes com overclock como stock. |
| AMD Ryzen 5 1400; AMD Ryzen 5 1500X; AMD Ryzen 5 1600 | Fechar o agregado e a posição com modelos de referência. O 1600 original não é o 1600 AF nem o 1600X. |
| Intel Core i5-4690; Intel Core i5-6600; Intel Core i7-6700 | Confirmar testes das variantes sem K e seu encaixe. Uma análise do modelo K não transfere a nota. |
| Intel Core i7-12700 | Escolher o recorte de potência de fábrica; não misturar 65 W com potência liberada ou com o 12700K. |
| AMD Ryzen 7 7700X3D; AMD Ryzen 7 9700X | A evidência consultada não cobre todos os integrantes dos grupos 500/400, respectivamente. |
| AMD Radeon R9 280 3GB; NVIDIA GeForce GTX 770 2GB; NVIDIA GeForce GTX 960 4GB | Fechar a posição histórica com VRAM exata e amostra comparável às referências. |
| AMD Radeon RX 470 4GB; AMD Radeon RX 480 4GB; AMD Radeon RX 580 4GB | Verificar o agregado das variantes de 4GB; não transferir as notas das variantes de 8GB. |
| AMD Radeon RX 7900 GRE 16GB | Fechar uma comparação comum com toda a GPU 500, inclusive RX 9070 GRE. |

Referências para continuar a revisão, sem nota atribuída nesta etapa:
[FX-6300/8350](https://www.techspot.com/review/586-amd-fx-8350-fx-6300/page6.html),
[i5-4690 e gerações anteriores](https://www.computerbase.de/artikel/prozessoren/intel-core-i5-6500-5675c-4690-test.51527/seite-3),
[Ryzen 1400/1600](https://www.notebookcheck.net/Ryzen-5-1400-and-1600-Review.225218.0.html),
[i7-12700](https://www.techspot.com/review/2391-intel-core-i7-12700/),
[7700X3D](https://www.techspot.com/review/3150-amd-ryzen-7700x3d/),
[GTX 960 4GB](https://www.techspot.com/review/1819-geforce-gtx-1660-vs-rtx-2060-vs-gtx-960/).

Nenhuma nota PassMark foi consultada ou copiada para esta revisão.

## Reprodução

Valide o CSV versionado, carregue-o no Neo4j e reprocesse os jogos.
O processamento salva hashes; `load_games.py` recusa CSV/aliases alterados
ou hardware do Neo4j divergente da referência usada nos jogos.
