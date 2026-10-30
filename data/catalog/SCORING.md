# Critério inicial do índice manual_v1

## Estado da avaliação

O índice é uma classificação preliminar do TCC1, preenchida por curadoria.
As medições pertencem aos autores das referências. O GameCompass registra
sua própria classe, a referência consultada e a justificativa.

Nesta etapa, 5 CPUs e 6 GPUs estão classificadas. As 34 peças pendentes
são 18 CPUs e 16 GPUs. O cadastro tem 45 peças.

| Tipo | Classe | Modelos |
| --- | ---: | --- |
| CPU | 100 | Ryzen 5 3600, Ryzen 5 3600X, Ryzen 7 3700X, Core i5-9600K e Core i7-9700K |
| GPU | 50 | GTX 1060 3GB e RX 570 4GB |
| GPU | 100 | GTX 1060 6GB e RX 580 8GB |
| GPU | 200 | GTX 1070 8GB e RX Vega 56 8GB |

## Significado da pontuação

`performance_score` representa uma classe ordenada dentro do mesmo tipo
de componente. O número 100 foi escolhido como referência inicial nas
escalas independentes de CPU e GPU.
Classes inferiores poderão usar valores positivos menores que 100;
classes superiores usarão valores maiores, quando houver comparação que
sustente a ordem. Os intervalos entre números não representam proporções
de desempenho, FPS ou porcentagens. Uma comparação exige o mesmo tipo de
componente e a mesma versão do índice.

Modelos com a mesma pontuação permanecem como registros distintos.
Compartilhar uma classe significa proximidade aproximada no recorte
documentado; não comprova desempenho igual em cada jogo.

## Regra de curadoria das GPUs

1. Confirmar o modelo e a variante de memória.
2. Usar testes que comparem as placas na mesma configuração e amostra de jogos.
3. Registrar resolução, qualidade por jogo, renderização e data do estudo.
4. Nesta etapa, priorizar comparações em 1080p com rasterização, sem usar
   geração de quadros ou mistura de modos de upscaling como equivalência.
5. Admitir a mesma classe quando a diferença média publicada no recorte
   comparável for de até 10% e as ressalvas do estudo forem registradas.
6. Exigir uma comparação compatível com os integrantes do grupo ao ampliá-lo.
   Proximidade entre A/B e B/C não comprova proximidade entre A/C.
7. Manter a nota vazia quando a comparação for insuficiente ou incompatível.

O limite de 10% é uma escolha experimental do GameCompass para o protótipo.
Sua adequação deverá ser avaliada no TCC2. Esta regra orienta a curadoria;
os scripts atuais apenas validam e consultam as notas cadastradas.

Não combine médias de FPS, médias de percentuais e médias geométricas como
se fossem a mesma métrica. Preserve o agregado informado pelo autor.
Os presets podem variar entre jogos: declare as condições do estudo,
sem assumir uma configuração Ultra universal.

## Primeiro grupo: classe GPU 100

| Modelo canônico | performance_score | score_version |
| --- | ---: | --- |
| NVIDIA GeForce GTX 1060 6GB | 100 | manual_v1 |
| AMD Radeon RX 580 8GB | 100 | manual_v1 |

Referência principal: [comparação de 32 jogos publicada pelo TechSpot](https://www.techspot.com/review/1990-geforce-1060-vs-radeon-580/),
de Steven Walton, em 28/02/2020. No agregado publicado para 1080p, a RX 580
ficou 5% à frente. O resultado sustenta a proximidade desta classe, sob
o critério experimental de até 10% adotado pelo projeto.

O estudo usou Gigabyte Aorus GTX 1060 6G 9Gbps e RX 580 XTR 8G, em um
Core i9-9900K a 5 GHz com 32 GB de DDR4-3400. O catálogo identifica GPU e
VRAM; diferenças de placa parceira e clocks não têm campos próprios.
Essa limitação torna a nota uma estimativa da classe dos modelos.

O recorte adotado é 1920 x 1080. As configurações de qualidade são as de
cada jogo no estudo; não foi assumido um preset único para os 32 títulos.

O levantamento é histórico: a data de consulta em `collected_at` não
representa uma nova execução do benchmark. Diferenças por jogo, drivers
e configurações continuam relevantes. A classe 100 não foi atribuída à
GTX 1060 3GB nem à RX 580 4GB. A variante de 3GB recebeu uma avaliação
própria no segundo grupo; a RX 580 4GB permanece pendente.

## Segundo grupo: classe GPU 50

| Modelo canônico | performance_score | score_version |
| --- | ---: | --- |
| NVIDIA GeForce GTX 1060 3GB | 50 | manual_v1 |
| AMD Radeon RX 570 4GB | 50 | manual_v1 |

Referência: [comparação de 36 jogos do TechSpot](https://www.techspot.com/review/1780-geforce-1060-vs-radeon-580-vs-radeon-570/),
de Steven Walton, em 18/01/2019. A GTX 1060 3GB ficou cerca de 4% à frente
da RX 570 4GB no resumo publicado. A proximidade atende ao critério
experimental de até 10% para compartilhar uma classe.

O mesmo estudo inclui GTX 1060 6GB e RX 580 8GB e coloca esse grupo acima
das duas placas da classe 50. A ordem entre 50 e 100 fica apoiada nessa
comparação conjunta, sem normalizar números de estudos diferentes.
O valor 50 foi escolhido como rótulo inferior a 100 e não representa
metade do desempenho, 50 FPS ou uma diferença percentual de 50%.

O artigo apresenta testes em 1080p e 1440p e explicita uma média aritmética
dos FPS para resumir as cinco GPUs avaliadas. A curadoria utiliza o resumo
publicado; não o combina com o agregado do estudo de 2020. Qualidade e
resolução seguem as configurações declaradas para cada teste da fonte.
São medições históricas, sem atualização própria dos drivers ou jogos.

A RX 570 4GB foi adicionada ao catálogo com cinco aliases que preservam a
capacidade de memória. Uma consulta genérica por RX 570 não escolhe a
variante de 4GB, pois outras capacidades exigem avaliação independente.

## Terceiro grupo: classe GPU 200

| Modelo canônico | performance_score | score_version |
| --- | ---: | --- |
| NVIDIA GeForce GTX 1070 8GB | 200 | manual_v1 |
| AMD Radeon RX Vega 56 8GB | 200 | manual_v1 |

Referência principal: [avaliação de 25 jogos do TechSpot](https://www.techspot.com/review/1468-amd-radeon-rx-vega-56/page8.html),
de Steven Walton, em 14/08/2017. O autor descreve desempenho próximo em
1080p e informa vantagem média de 2,5% da Vega 56 em 1440p. O recorte
numérico desta classe é 2560 x 1440, dentro do limite experimental de 10%.
O percentual de 2,5% não foi tratado como um resultado de 1080p.
A uniformização quantitativa em 1080p continua aberta para esta classe.

As [condições do teste](https://www.techspot.com/review/1468-amd-radeon-rx-vega-56/)
incluem Core i7-7700K a 4,9 GHz, 32 GB DDR4-3200, GTX 1070 MSI Gaming X
e Vega 56 de referência. Qualidade varia por jogo. A avaliação é histórica,
com drivers de 2017 e diferenças de placa parceira não modeladas no CSV.

Para a ordenação preliminar acima da classe 100, a referência adicional
é a [comparação direta de GTX 1070 e RX 580 8GB em 15 jogos](https://www.techspot.com/review/2285-geforce-gtx-1070-revisit/),
de Steven Walton, em 14/07/2021: a GTX 1070 ficou cerca de 27% à frente
no agregado publicado para cada resolução, 1080p e 1440p. Esse estudo usou
Ryzen 9 5950X e 32 GB DDR4-3200, com diferentes presets por jogo.

O projeto usa essa comparação como apoio à ordem entre grupos. Não
normaliza os dois estudos nem calcula uma vantagem percentual da Vega 56
sobre a RX 580 por transitividade. A uniformização entre as amostras ainda
precisa ser validada. A classe 200 é uma aproximação preliminar e não
representa o dobro do desempenho da classe 100.

GTX 1070 Ti, modelos de notebook e outras GPUs Vega não recebem esta nota
por semelhança do nome. Os modelos deste grupo já estavam cadastrados;
não foram adicionados novos aliases ou novas peças nesta etapa.

## Regra inicial de curadoria das CPUs

1. Confirmar o modelo exato, incluindo sufixos e segmento desktop/notebook.
2. Usar comparações diretas de desempenho em jogos, com plataformas e
   condições de memória, GPU, resolução e qualidade documentadas.
3. Priorizar 1080p e testes que procurem reduzir a limitação pela GPU.
4. Avaliar os resultados em configuração de fábrica, preservando o boost
   normal. Resultados de overclock manual precisam de avaliação separada.
5. Usar o agregado de jogos publicado pelo autor e manter a mesma classe
   quando a diferença for de até 10%, registrando as limitações da amostra.
6. Exigir comparação com todos os integrantes ao ampliar um grupo. Uma
   alternativa citada pela Steam não atribui classe a outro modelo.
7. Preservar a pendência quando faltar comparação suficiente.

O limite de 10% também é uma escolha experimental para CPUs. A nota
classifica proximidade em jogos no recorte documentado. Não agrega
Cinebench, renderização ou produtividade ao índice de jogos. Frequência,
núcleos, instruções suportadas e estabilidade dos tempos de quadro
continuam sendo características que exigem avaliação própria.

## Primeiro grupo de CPU: classe 100

| Modelo canônico | performance_score | score_version |
| --- | ---: | --- |
| AMD Ryzen 5 3600 | 100 | manual_v1 |
| AMD Ryzen 5 3600X | 100 | manual_v1 |
| AMD Ryzen 7 3700X | 100 | manual_v1 |
| Intel Core i5-9600K | 100 | manual_v1 |
| Intel Core i7-9700K | 100 | manual_v1 |

Referência: [avaliação do Tweakers](https://tweakers.net/reviews/7222/ryzen-5-3600-en-3600x-nieuwe-ryzens-op-budget.html),
de Willem de Moor, em 19/07/2019. Os cinco modelos participam da mesma
avaliação. No agregado de jogos publicado, os extremos deste grupo são
129 e 137 pontos. O GameCompass calcula a amplitude relativa como
`((137 / 129) - 1) * 100`, aproximadamente 6,2%, dentro do limite
experimental de 10%.

Esse cálculo é uma inferência de curadoria sobre o índice arredondado
da fonte. Não equivale a uma vantagem de FPS em cada jogo. A comparação
conjunta dos cinco modelos sustenta o grupo sem depender de transitividade
entre pares avaliados em estudos diferentes.

A amostra tem seis jogos em 1080p, nos presets Medium e Ultra. O agregado
de jogos da fonte dá o mesmo peso aos testes. O GameCompass conserva essa
interpretação e atribui seu próprio rótulo ordinal 100, sem converter
os pontos publicados em uma pontuação de benchmark própria.

Foi usada uma GTX 1080 Ti. O sistema AMD usou X570 e 2x8 GB DDR4-3200 CL14;
o Intel, Z390 e 2x8 GB DDR4-2667 CL13. O estudo também lista Windows 10 x64
nas versões 1903 e 1803. Essas diferenças fazem parte das condições da
comparação. Alguns presets Ultra também apresentam limitação
pela GPU. A amostra e essas condições limitam a generalização para
outros jogos e configurações.

A nota considera a comparação principal em configuração de fábrica.
As experiências de overclock e de troca de plataforma relatadas em
outras seções não são misturadas a esse grupo. São medições históricas;
`collected_at` registra a consulta ou o registro de curadoria, sem indicar
novo teste de hardware.

Os cinco modelos mantêm registros distintos. Os aliases identificam
nomes alternativos da mesma peça. Sufixos como KF e XT
identificam outros modelos e não herdam a nota automaticamente.

## Outros grupos e limites

As demais CPUs e GPUs aguardam avaliações próprias. A RTX 5070 e a RX 9070
não herdam uma classe apenas por terem sido sugeridas como um par.
Estudos consultados desse par usam amostras e configurações diferentes:
[Tom's Hardware, 29/05/2025](https://www.tomshardware.com/pc-components/gpus/nvidia-rtx-5070-vs-amd-rx-9070-face-off)
e [TechSpot, 21/10/2025](https://www.techspot.com/review/3044-nvidia-rtx-5070-vs-amd-radeon-9070-dlss-fsr/).
A avaliação deve fixar um recorte comparável antes de atribuir as notas.

A classe não cobre automaticamente versão de SO, capacidade mínima de
VRAM, DirectX, instruções de CPU, ray tracing, SSD ou estabilidade de FPS.
Esses requisitos precisam de verificações próprias. O protótipo oferece
uma aproximação por classe, cuja qualidade ainda precisa ser validada.

## Reprocessamento e reprodução

Ao atualizar as notas, gere o CSV processado e reexecute a carga no Neo4j.
Reprocesse os requisitos afetados para que consultem o catálogo atualizado.
Use a mesma versão do índice para comparar o PC com os requisitos do jogo.
O commit Git e os hashes dos arquivos identificam a revisão utilizada.

Após esta etapa, a carga informa `classified: 11` e `pending: 34`.
Requisitos que citam alternativas ainda sem nota continuam com
`required_score: null` e `status: needs_review`. Por exemplo, a Arc A380
segue pendente nos mínimos do Cyberpunk 2077, preservando essa pendência
mesmo com as duas alternativas deste primeiro grupo já classificadas.
