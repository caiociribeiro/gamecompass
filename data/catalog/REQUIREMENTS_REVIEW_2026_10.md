# Revisão dos requisitos da amostra Steam

Revisão de 31/10/2026 para o protótipo TCC1. O catálogo passa a ter
53 CPUs e 71 GPUs, com 124 faixas preenchidas. Foram adicionadas 12 CPUs
e 31 GPUs citadas pelos requisitos; os 81 registros anteriores foram
preservados. CSV e aliases continuam como entradas versionadas da pipeline.

## Critério das novas faixas

As notas são rótulos ordinais próprios, definidos por curadoria aproximada.
As referências ajudam a posicionar modelos antigos em relação aos grupos
existentes. Não houve um benchmark uniforme dos 124 componentes. As
distâncias entre números não representam proporções de FPS. Os integrados
e o i3-380M recebem apenas um encaixe legado preliminar; memória
compartilhada, refrigeração e energia não são avaliadas pelo índice.

As CPUs acrescentadas são Athlon 64 X2 5600+, FX-4300, Ryzen 3 1200,
Ryzen 5 2600, Ryzen 7 1800X, Core i3-380M, i3-3240, i5-3470, i5-6400,
i5-7500, i5-9600 e i7-6700K. As GPUs incluem os modelos legados usados
por Hollow Knight e Civilization VI, RX 560, RX 5500 XT, RX 5700,
RX 590, RX 6600 XT, GTX 1050/1050 Ti/1650/1660 e Arc B580.
Cada registro do CSV conserva sua referência e data de consulta.

Referências principais de curadoria, com testes e especificações dos autores:

- [Hierarquia de CPUs antigas, Tom's Hardware](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html).
- [Ryzen 3 1200 e comparação com i5-7500, TechSpot](https://www.techspot.com/review/1455-ryzen-3/page3.html).
- [Ryzen 5 2600 e Core i5-8400, TechSpot](https://www.techspot.com/review/1627-core-i5-8400-vs-ryzen-5-2600/).
- [Ryzen 7 1800X em jogos, TechSpot](https://www.techspot.com/review/1863-two-years-later-ryzen-1800x-vs-core-i7-7700k/).
- [Identidade e características do i3-380M, Notebookcheck](https://www.notebookcheck.net/Intel-Core-i3-380M-Notebook-Processor.37085.0.html).
- [Hierarquia de GPUs antigas, Tom's Hardware](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html).
- [RX 5500 XT, TechSpot](https://www.techspot.com/review/1958-amd-radeon-rx-5500-xt/).
- [RX 6600 XT, TechSpot](https://www.techspot.com/review/2305-amd-radeon-rx-6600-xt/).
- [Arc B580, TechSpot](https://www.techspot.com/review/2935-intel-arc-b580/).
- [HD Graphics 4000, Notebookcheck](https://www.notebookcheck.net/Intel-HD-Graphics-4000-Benchmarked.73567.0.html).

Os gráficos HD 530, HD 630 e UHD 630 também conservam suas páginas
específicas no CSV. O encaixe é uma inferência de curadoria do GameCompass,
não uma nota publicada por essas fontes. Nenhum resultado PassMark foi
coletado, reproduzido ou convertido nesta ampliação.

## Identificação e comparação

O parser separa listas por vírgula quando o próximo trecho começa com
um nome de fabricante ou família. Preserva vírgulas decimais e conteúdo
entre parênteses. Expressões finais como `or better` são qualificadores,
não novos modelos. Marcas registradas não impedem a consulta, e a grafia
original permanece no resultado. Aliases continuam explícitos; não há
aprovação por similaridade de números nem escolha arbitrária de VRAM.

O processamento ainda preenche o limite global apenas quando todas as
alternativas estão identificadas e classificadas. A interface agora pode
comprovar o atendimento por uma alternativa publicada conhecida. Em
[Hogwarts Legacy](https://www.hogwartslegacy.com/en-au/pc-specs), por exemplo,
uma GPU suficiente para a GTX 1080 Ti ou RX 5700 XT permite atender ao
campo recomendado, mesmo com Arc A770 sem memória especificada. A Arc
não é convertida em um modelo de 8 ou 16 GB. Se a GPU ficar abaixo das
opções conhecidas, o resultado parcial permanece pendente.

Os recomendados comprovados são uma condição suficiente quando algum
campo mínimo é genérico. A pendência mínima original continua visível.
Qualquer falha mínima conhecida prevalece, mesmo que os recomendados
apareçam menos exigentes por uma inconsistência da fonte. Esses critérios
usam a mesma versão do índice e mantêm CPU e GPU em escalas distintas.

Cabeçalho acompanhado apenas do aviso genérico de 64 bits passa a ser
considerado requisito não publicado. Isso corrige o bloco recomendado
vazio de No Man's Sky, sem preencher campos ausentes.

## Cobertura verificada

Na amostra preservada de 20 jogos, para Windows:

| Cobertura dos campos | Mínimos | Recomendados |
| --- | ---: | ---: |
| Completa | 9 | 8 |
| Com alternativas conhecidas suficientes para comparar um perfil | 2 | 3 |
| Ainda exige curadoria | 9 | 4 |
| Não publicado | 0 | 5 |

Treze jogos possuem base de comparação em pelo menos um nível. No teste
com Ryzen 7 9700X, RTX 5070 12GB, 16 GB de RAM e Windows 11, onze
atenderam aos recomendados e dois aos mínimos nos campos implementados.
Isso não afirma que todos aparecerão nas sugestões: a afinidade e as
âncoras continuam sendo filtros independentes.

Sete jogos permanecem sem uma comparação concluída para esse perfil:

| Jogo | Principal pendência |
| --- | --- |
| Stardew Valley | CPU informada apenas por frequência; GPU por recursos gráficos |
| Hades | CPU por núcleos/frequência; GPU por VRAM/DirectX |
| Portal 2 | Famílias de CPU e descrição gráfica composta |
| Terraria | CPU por frequência; GPU por memória/shader |
| Dead Cells | Família `Intel i5+` sem modelo |
| Slay the Spire | CPU por frequência; GPU por VRAM/OpenGL |
| No Man's Sky | Família `Intel Core i3` sem modelo; recomendados não publicados |

Esses textos exigem uma regra de curadoria específica ou evidência
adicional de execução. Não existe conversão universal de GHz, VRAM ou
nome de família para desempenho em jogos. Eles continuam disponíveis
para análise e não recebem notas fictícias para eliminar uma pendência.

O relatório `review_game_requirements.py` registra cobertura, consultas
pendentes, jogos de origem e hash da entrada. Seu resumo é independente
do status global dos documentos: `needs_review` também pode registrar uma
alternativa desconhecida, requisitos de outra plataforma ou nível ausente.
VRAM, DirectX, instruções, SSD e detalhes de versões de SO continuam com
verificações próprias a implementar. Esta revisão não conclui o TCC2.
