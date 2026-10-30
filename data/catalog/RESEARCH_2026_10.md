# Seleção de hardware para jogos — outubro de 2026

## Escopo e resultado

Curadoria registrada em 30/10/2026. Esta é uma seleção de 20 CPUs e 20 GPUs
desktop de alto desempenho para ampliar o catálogo, e não um ranking
universal dos vinte melhores produtos. Disponibilidade, preço e custo por
quadro não foram usados para classificar. Notebooks, iGPUs e estações de
trabalho não fazem parte deste lote.

O lote acrescenta 36 identidades e revisa quatro já cadastradas. Das
40 peças selecionadas, 37 recebem classe e três ficam pendentes. O
catálogo completo passa a 81 peças: 41 CPUs e 40 GPUs; 48 classificadas
e 33 pendentes. As notas antigas foram preservadas.

Os números são rótulos ordinais definidos pelo GameCompass em
`manual_v1`. Não são scores dos sites, percentuais ou proporções de FPS.
CPU e GPU usam escalas independentes. As fontes mediram o hardware;
o projeto realizou a pesquisa e a curadoria, sem executar esses benchmarks.

## CPUs selecionadas

| Modelo desktop | performance_score | Fonte |
| --- | ---: | --- |
| AMD Ryzen 7 9850X3D | 600 | C2 |
| AMD Ryzen 7 9800X3D | 600 | C2 |
| AMD Ryzen 9 9950X3D2 Dual Edition | 600 | C2 |
| AMD Ryzen 9 9950X3D | 600 | C2 |
| AMD Ryzen 9 9900X3D | 500 | C1 |
| AMD Ryzen 7 7800X3D | 500 | C1 |
| AMD Ryzen 9 7950X3D | 500 | C1 |
| AMD Ryzen 7 7700X3D | Pendente (proposta 500) | C3 |
| AMD Ryzen 5 7600X3D | 500 | C1 |
| Intel Core i9-14900K | 400 | C1 |
| Intel Core Ultra 7 270K Plus | 400 | C1 |
| AMD Ryzen 9 7900X3D | 400 | C1 |
| AMD Ryzen 9 9950X | 400 | C1 |
| Intel Core i9-13900K | 400 | C1 |
| Intel Core i7-14700K | 400 | C1 |
| Intel Core i7-13700K | 400 | C1 |
| AMD Ryzen 9 9900X | 400 | C1 |
| Intel Core Ultra 5 250K Plus | 400 | C1 |
| AMD Ryzen 7 9700X | Pendente (proposta 400) | C2 |
| Intel Core i5-14600K | 400 | C1 |

## GPUs selecionadas

A capacidade de VRAM integra a identidade. Variantes Ti, SUPER, XT, XTX
e GRE são peças distintas e não herdam notas por semelhança textual.

| Modelo desktop | performance_score | Fonte |
| --- | ---: | --- |
| NVIDIA GeForce RTX 5090 32GB | 1000 | G1 |
| NVIDIA GeForce RTX 4090 24GB | 900 | G1 |
| NVIDIA GeForce RTX 5080 16GB | 800 | G1 |
| AMD Radeon RX 7900 XTX 24GB | 700 | G1 |
| NVIDIA GeForce RTX 4080 SUPER 16GB | 700 | G1 |
| NVIDIA GeForce RTX 4080 16GB | 700 | G1 |
| NVIDIA GeForce RTX 5070 Ti 16GB | 700 | G1 |
| AMD Radeon RX 9070 XT 16GB | 700 | G1 |
| AMD Radeon RX 7900 XT 20GB | 600 | G1 |
| NVIDIA GeForce RTX 4070 Ti SUPER 16GB | 600 | G1 |
| NVIDIA GeForce RTX 3090 Ti 24GB | 550 | G1 |
| AMD Radeon RX 9070 16GB | 550 | G1 |
| NVIDIA GeForce RTX 4070 Ti 12GB | 550 | G1 |
| NVIDIA GeForce RTX 5070 12GB | 550 | G1 |
| NVIDIA GeForce RTX 4070 SUPER 12GB | 500 | G1 |
| NVIDIA GeForce RTX 3090 24GB | 500 | G1 |
| NVIDIA GeForce RTX 3080 Ti 12GB | 500 | G1 |
| AMD Radeon RX 6950 XT 16GB | 500 | G1 |
| AMD Radeon RX 9070 GRE 12GB | 500 | G1 |
| AMD Radeon RX 7900 GRE 16GB | Pendente (proposta 500) | G2 |

## Como as classes foram fechadas

O limite experimental de proximidade é de 10% entre os extremos do
agregado de jogos de uma mesma amostra. Amplitude significa
`(maior resultado / menor resultado - 1) * 100`, calculada na curadoria.
Não se normalizam índices de sites diferentes. A regra orienta a revisão
humana; o validador Python verifica o contrato do CSV, não mede desempenho.

| Tipo | Classe | Peças com nota no lote | Amplitude aproximada | Amostra de referência |
| --- | ---: | ---: | ---: | --- |
| CPU | 600 | 4 | 2,9% | C2, índice de jogos 2026-1 |
| CPU | 500 | 4 | 7,8% | C1, 1080p |
| CPU | 400 | 10 | 7,4% | C1, 1080p |
| GPU | 1000 | 1 | Não se aplica | G1, 1440p Ultra nativo |
| GPU | 900 | 1 | Não se aplica | G1, 1440p Ultra nativo |
| GPU | 800 | 1 | Não se aplica | G1, 1440p Ultra nativo |
| GPU | 700 | 5 | 5,0% | G1, 1440p Ultra nativo |
| GPU | 600 | 2 | 3,8% | G1, 1440p Ultra nativo |
| GPU | 550 | 4 | 7,9% | G1, 1440p Ultra nativo |
| GPU | 500 | 5 | 5,7% | G1, 1440p Ultra nativo |

As amplitudes são inferências sobre agregados arredondados publicados.
Não demonstram igualdade em cada jogo. Na fronteira GPU 550/600 há
resultados arredondados empatados em G1; o recorte G2 também foi consultado
para a posição da RTX 4070 Ti SUPER. Essa fronteira e diferenças entre
amostras são limitações da discretização, a validar no TCC2.

### Recortes de CPU

C1 usa 17 jogos e média geométrica em 1080p, com RTX 5090 FE e presets
High/Ultra conforme o jogo. A comparação usa a configuração principal
sem overclock automático adicional. Ela sustenta as classes 400 e 500.
A linha da fonte que chama o 7900X3D de Ryzen 7 é uma inconsistência de
rotulagem: o modelo canônico é AMD Ryzen 9 7900X3D.

C2 inclui os quatro integrantes da classe 600 em seu índice de jogos
2026-1, com seis jogos, presets Medium/Ultra em 1080p e 1440p, RTX 5090
e Windows 11 Pro 25H2. As plataformas usam configurações de memória
distintas. Trata-se de uma exceção explícita à prioridade de 1080p,
sem converter o índice misto de resoluções em um resultado de 1080p.
A comparação C4, em 720p e com RTX 5090, também inclui os quatro e
apresenta amplitude aproximada de 8,5%. É uma checagem independente,
não uma média ou combinação com C2.

As classes altas ficam acima da classe histórica CPU 100. C4 inclui
Ryzen 5 3600 junto de modelos atuais e apoia a direção dessa ordem.
Isso não calibra a distância numérica entre classes ou estudos.

### Recortes de GPU e ajuste da proposta

G1 usa 11 jogos e média geométrica em 1440p Ultra com Ryzen 7 9800X3D.
Foi considerada apenas a tabela de rasterização nativa, sem ray tracing,
DLSS/FSR/XeSS ou geração de quadros. G2 traz outro agregado de jogos;
seus números não foram misturados aos de G1.

A RTX 3090 Ti passa da proposta 600 para 550. Seu resultado em G1 fica
abaixo do da RX 9070; a revisão evita manter essa inversão entre classes.
A RTX 4070 Ti SUPER permanece em 600: no recorte G2 ela não cabe no
mesmo grupo da RTX 5070 dentro do limite experimental de 10%.

G3 inclui GTX 1070 e placas da classe 500 no mesmo recorte histórico e
apoia a ordem acima da classe GPU 200. Não se combinam os resultados
desse estudo com o agregado atual para calcular um multiplicador.

G4 foi consultada para contexto, mas sua tabela de rasterização combina
modos nativos e upscaling entre jogos. Por isso não foi usada como
amostra numérica equivalente ao recorte nativo G1.

### Pendências mantidas

| Peça | Proposta | Motivo para manter o score vazio |
| --- | ---: | --- |
| AMD Ryzen 7 7700X3D | CPU 500 | C3 compara alguns integrantes, mas não inclui 9900X3D e 7950X3D no agregado de jogos usado. |
| AMD Ryzen 7 9700X | CPU 400 | C2 não cobre todos os dez integrantes confirmados da classe; proximidade com apenas parte do grupo não fecha a avaliação. |
| AMD Radeon RX 7900 GRE 16GB | GPU 500 | Ausente da amostra atual G1; G2 e G3 não incluem a RX 9070 GRE que integra a classe. |

Essas identidades ficam disponíveis para matching. O resultado informa
`score_status: pending` e `performance_score: null`; não usa a proposta
como nota válida. Outras 30 peças anteriores também aguardam classificação.

## Referências e datas

- C1 — [Tom's Hardware: CPU hierarchy](https://www.tomshardware.com/reviews/cpu-hierarchy,4312.html), atualização de 05/10/2026; tabela de jogos em 1080p.
- C2 — [Tweakers: Ryzen 9 9950X3D2 Dual Edition](https://tweakers.net/reviews/14648/amd-ryzen-9-9950x3d2-dual-edition-de-cpu-die-amd-zelf-maar-onzinnig-vond.html), 21/04/2026, atualização de 22/04/2026; índice CPU Gaming 2026-1, separado do índice geral de CPU.
- C3 — [ComputerBase: 7700X3D, benchmarks de jogos](https://www.computerbase.de/artikel/prozessoren/amd-ryzen-7-7700x3d-test.98221/seite-2), 16/07/2026; agregado em 720p.
- C4 — [ComputerBase: hierarquia de CPUs](https://www.computerbase.de/artikel/prozessoren/rangliste.89909/), atualização de 03/08/2026; agregado de nove jogos em 720p.
- G1 — [Tom's Hardware: GPU hierarchy](https://www.tomshardware.com/reviews/gpu-hierarchy,4388.html), atualização de 24/06/2026; primeira tabela, coluna 1440p Ultra.
- G2 — [Tweakers: resultados de GPUs](https://tweakers.net/reviews/12950/videokaartbenchmarks-al-onze-gpu-testresultaten.html), atualização de 19/01/2026; agregado raster 1440p Ultra.
- G3 — [Tom's Hardware: GPU hierarchy 2022–2024](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-2.html), amostra histórica indicada nessa página; rasterização, coluna 1440p Ultra.
- G4 — [ComputerBase: hierarquia de GPUs](https://www.computerbase.de/artikel/grafikkarten/rangliste.2487/), atualização de 02/10/2026; contexto e checagem de identidade, sem combinar o agregado com G1.

`collected_at` registra a consulta ou o registro de curadoria, não a data
de execução do benchmark. O Git guarda a revisão do catálogo e o pipeline
registra seu SHA-256. Páginas de hierarquia podem mudar após esta consulta.

## Aplicação e limites

O CSV continua como fonte versionada; Neo4j recebe a cópia validada.
Não foi introduzido outro banco ou uma lista de produção em Python.
Após aplicar o lote, valide o CSV, confira o dry-run (48 classificadas,
33 pendentes), carregue no Neo4j e reprocesse os requisitos afetados.

Compatibilidade de SO, VRAM mínima, instruções da CPU, DirectX e SSD
exigem checagens próprias. Essas classes não asseguram FPS ou atendem
automaticamente a todos os requisitos técnicos de um jogo.
