# Critério inicial do índice manual_v1

## Estado da avaliação

O índice é uma classificação preliminar do TCC1, preenchida por curadoria.
As medições pertencem aos autores das referências. O GameCompass registra
sua própria classe, a referência consultada e a justificativa.

Nesta etapa, 2 GPUs estão classificadas e 39 peças continuam pendentes:
20 CPUs e 19 GPUs. O primeiro grupo usa a GTX 1060 6GB e a RX 580 8GB
como referência. As notas das outras variantes permanecem vazias.

## Significado da pontuação

`performance_score` representa uma classe ordenada dentro do mesmo tipo
de componente. O número 100 foi escolhido como referência inicial de GPU.
Classes inferiores poderão usar valores positivos menores que 100;
classes superiores usarão valores maiores, quando houver comparação que
sustente a ordem. Os intervalos entre números não representam proporções
de desempenho, FPS ou porcentagens. CPUs terão classificação independente.

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
e configurações continuam relevantes. A avaliação não foi estendida à
GTX 1060 3GB nem à RX 580 4GB.

## Outros grupos e limites

As demais GPUs aguardam avaliações próprias. A RTX 5070 e a RX 9070
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

Após esta etapa, a carga informa `classified: 2` e `pending: 39`.
Requisitos que citam alternativas ainda sem nota continuam com
`required_score: null` e `status: needs_review`. Por exemplo, a Arc A380
segue pendente nos mínimos do Cyberpunk 2077, preservando essa pendência
mesmo com as duas alternativas deste primeiro grupo já classificadas.
