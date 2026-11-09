# Revisão de hardware de 06/11/2026

Acrescenta 50 peças (30 CPUs e 20 GPUs) ao índice `manual_v1`, que passa de 262 para 312 componentes (145 CPUs e 167 GPUs). Elas aparecem nos requisitos dos 120 jogos do catálogo e estavam como "não identificadas". Os nomes, notas e aliases anteriores não foram alterados.

## Critério e limites desta revisão

- As classes seguem o critério simplificado de [TCC1_REVIEW_2026_10.md](TCC1_REVIEW_2026_10.md): classe ordinal por curadoria, sem proporção de FPS e sem conversão de GHz ou núcleos.
- **A página do Tom's Hardware usada em revisões anteriores não pôde ser lida nesta etapa** (o conteúdo veio truncado). Por isso ela não é citada aqui como fonte.
- Muitas classes vêm de **família**: mesma microarquitetura e clock próximo de um modelo irmão já classificado. Nesses casos `source_url` repete a fonte do irmão e a coluna "Justificativa" diz qual é. Isso é inferência de curadoria, não medição do próprio modelo.
- Fontes diretas usadas: TechSpot (i3-8100, i5-11600K, HD 6870 vs HD 5870, revisão das Vega), Tom's Hardware (Ryzen 5 2400G), technical.city e hardwaredb.net. Várias são agregadores sem metodologia documentada; as classes que dependem só deles estão marcadas com confiança média ou baixa.
- A escala de CPU não tem classe abaixo de 5. Pentium E2180 e Athlon 64 (3000+ e X2 3800+) ficam coladas em 5 e perdem distinção entre si e em relação ao X2 5600+.
- Confiança **alta**: irmão direto da mesma microarquitetura ou comparação direta encontrada. **Média**: encaixe entre duas classes ou fonte agregadora. **Baixa**: sem comparação direta; classe aproximada. As classes de confiança baixa podem ser revisadas sem afetar as demais.

## Peças acrescentadas

| Tipo | Peça | Classe | Confiança | Justificativa | Fonte |
| --- | --- | ---: | --- | --- | --- |
| CPU | AMD Athlon 64 3000+ | 5 | baixa | Núcleo único de 1,8 GHz, abaixo do X2 5600+; a escala não tem classe abaixo de 5, então perde distinção. | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | AMD Athlon 64 X2 3800+ | 5 | baixa | Dual-core de 2,0 GHz, abaixo do X2 5600+; colado na classe mínima 5. | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core 2 Duo E4400 | 5 | alta | Allendale dual-core de mesma família do E4500 (classe 5). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core 2 Duo E6750 | 5 | média | Conroe dual-core (2,66 GHz) próximo do E6600 (classe 5); fronteira com a classe 8. | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Pentium E2180 | 5 | baixa | Allendale de 2 MB de cache a 2,0 GHz, abaixo ou igual ao E4500; a escala não tem classe abaixo de 5. | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core 2 Duo E8500 | 8 | alta | Wolfdale dual-core, mesma família e clock próximo do E8400 (classe 8). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | AMD Phenom X4 9850 | 10 | alta | Phenom X4 original (Agena) de mesma família do 9950 (classe 10). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i3-530 | 10 | média | Clarkdale dual-core com Hyper-Threading, mesma família do i3-380M (classe 10). | [link](https://www.notebookcheck.net/Intel-Core-i3-380M-Notebook-Processor.37085.0.html) |
| CPU | Intel Core 2 Quad Q9650 | 15 | baixa | Yorkfield quad-core; a fonte afirma que supera o Q6600 (classe 10) em todos os testes de jogos, sem números. Classe 15 é aproximada. | [link](https://www.hardwaredb.net/core-2-quad-q6600-vs-core-2-quad-q9650) |
| CPU | Intel Core i5-650 | 15 | baixa | Clarkdale dual-core com Hyper-Threading; encaixe aproximado na classe 15, sem comparação direta encontrada. | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | AMD Phenom II X4 940 | 20 | alta | Phenom II X4 de mesma família e clock próximo do X4 945 (classe 20). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | AMD Phenom II X4 955 | 20 | alta | Phenom II X4 de mesma família e clock próximo do X4 945 (classe 20). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i3-2120 | 20 | alta | Sandy Bridge dual-core com Hyper-Threading, clock próximo do i3-2100 (classe 20). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i3-2130 | 20 | alta | Sandy Bridge dual-core com Hyper-Threading, clock próximo do i3-2100 (classe 20). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i5-760 | 20 | alta | Lynnfield quad-core, mesma família e clock próximo do i5-750 (classe 20). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | AMD A10-5800K | 30 | média | Trinity de 2 módulos/4 threads, faixa próxima do FX-4300 (classe 30). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | AMD A8-5600K | 30 | média | Trinity de 2 módulos/4 threads, faixa próxima do FX-4300 (classe 30). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i3-4170 | 30 | média | Haswell dual-core com Hyper-Threading a 3,7 GHz; mantido na classe do i3-4130 (30) por prudência, entre 30 e 35. | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i3-7100 | 35 | alta | Kaby Lake dual-core com Hyper-Threading, praticamente o i3-6100 (classe 35). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i7-3820 | 55 | média | Sandy Bridge-E 4 núcleos/8 threads, entre o i7-2700K (55) e o i7-3770 (60). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i3-8100 | 60 | alta | Coffee Lake quad-core sem HT; fica atrás do i3-8350K (60) e do i5-7600K (70) na fonte. | [link](https://www.techspot.com/review/1499-intel-core-i3-8100-i3-8350K/) |
| CPU | Intel Core i5-4690K | 60 | alta | Mesma microarquitetura Haswell e clock próximo do i5-4690 e do i5-4670K (classe 60). | [link](https://overclockers.ru/lab/show/73717_4/test-processorov-intel-core-i7-6700-core-i5-6600-core-i5-6500-i-core-i5-6400-v-aktualnyh-igrah) |
| CPU | AMD Ryzen 5 2400G | 70 | alta | Zen+ 4 núcleos/8 threads; o Ryzen 5 3400G (classe 70) é o refresh com clock 100 MHz maior. | [link](https://www.tomshardware.com/reviews/amd-ryzen-5-2400g-zen-vega-cpu-gpu,5467-6.html) |
| CPU | Intel Core i7-4790K | 70 | alta | Mesma microarquitetura Haswell do i7-4790 e do i7-4770K (classe 70). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i5-8500 | 90 | alta | Coffee Lake 6 núcleos/6 threads com clock próximo do i5-8400 (classe 90). | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | Intel Core i5-8600 | 90 | média | Coffee Lake 6 núcleos/6 threads entre o i5-8400 (classe 90) e o i5-8600K (classe 100); mantido em 90 por ser modelo sem K. | [link](https://www.tomshardware.com/reviews/cpu-hierarchy,4312-2.html) |
| CPU | AMD Ryzen 5 3500 | 100 | média | Zen 2 de 6 núcleos/6 threads, pouco abaixo do Ryzen 5 3600 (classe 100). | [link](https://tweakers.net/reviews/7222/ryzen-5-3600-en-3600x-nieuwe-ryzens-op-budget.html) |
| CPU | Intel Core i5-8600K | 100 | alta | O i5-9600K é um refresh do i5-8600K (6 núcleos/6 threads); o i7-8700K também é classe 100. | [link](https://tweakers.net/reviews/7222/ryzen-5-3600-en-3600x-nieuwe-ryzens-op-budget.html) |
| CPU | Intel Core i7-10700 | 150 | média | Agregador de jogos coloca o i7-10700 perto e pouco abaixo do i5-11400F (classe 150). Fonte sem metodologia documentada. | [link](https://howmanyfps.com/processors/comparisons/core-i7-10700-vs-core-i5-11400f) |
| CPU | Intel Core i5-11600K | 200 | média | Fontes divergem; fica próximo do Ryzen 5 5600X (classe 200) em jogos. | [link](https://www.techspot.com/review/2220-intel-core-i5-11600k) |
| GPU | AMD Radeon HD 5450 | 1 | baixa | Placa de entrada abaixo da HD 5570; classe mínima 1. | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | ATI Radeon X1950 Pro 256MB | 1 | baixa | Geração Shader Model 3.0 na faixa da X800 (classe 1). | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | NVIDIA GeForce 6800 GT | 1 | baixa | Geração anterior à GeForce 7; classe mínima 1. | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | NVIDIA GeForce GT 430 | 1 | baixa | Fermi de entrada (96 shaders), na faixa inferior da GT 630 (classe 2); classe 1 por prudência. | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | AMD Radeon HD 5650 | 2 | baixa | Versão móvel de 400 shaders, similar à HD 5570 (classe 2); sem comparação direta encontrada. | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | ATI Radeon HD 3850 512MB | 2 | baixa | Da mesma geração da HD 3870 (classe 2), um pouco abaixo. | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | Intel HD Graphics 4400 | 2 | baixa | Haswell GT2 com clock menor que a HD 4600 (classe 2). | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | Intel HD Graphics 520 | 2 | alta | Mesma geração Skylake GT2 da HD 530 (classe 2). | [link](https://www.notebookcheck.net/Intel-HD-Graphics-530.148358.0.html) |
| GPU | NVIDIA GeForce GT 550M | 2 | baixa | Versão móvel Fermi de 96 shaders, similar à GT 630 (classe 2). | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | AMD Radeon HD 4870 1GB | 3 | média | A HD 6850 (classe 8) fica cerca de 40% à frente; faixa comumente associada à HD 5770 (classe 3). | [link](https://technical.city/en/video/Radeon-HD-4870-vs-Radeon-HD-6850) |
| GPU | AMD Radeon RX Vega 11 | 3 | média | Gráfico integrado perto da GT 1030 (num teste, ~9% abaixo); entre as classes 2 e 4. | [link](https://www.tomshardware.com/reviews/amd-ryzen-5-2400g-zen-vega-cpu-gpu,5467-6.html) |
| GPU | NVIDIA GeForce 8800 GTS 512MB | 3 | média | G92 acima da 9600 GT (classe 2). | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | NVIDIA GeForce 9800 GT 1GB | 3 | média | G92 acima da 9600 GT (classe 2). | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | NVIDIA GeForce GT 740M | 3 | baixa | Versão móvel Kepler, na faixa da GT 650M (classe 3). | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | AMD Radeon HD 5870 | 8 | alta | A HD 6870 (classe 8) fica perto da HD 5870 (entre -11% e +10% conforme o jogo); a HD 5850 também é classe 8. | [link](https://www.techspot.com/review/325-amd-radeon-6870/page4.html) |
| GPU | AMD Radeon R7 250X 1GB | 8 | média | Equivale à HD 7770 (Cape Verde XT), acima da HD 7750 (classe 5); fronteira entre 5 e 8. | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | AMD Radeon R9 270X 2GB | 15 | alta | Mesmo chip Pitcairn da HD 7870 (classe 15). | [link](https://www.tomshardware.com/reviews/gpu-hierarchy,4388-3.html) |
| GPU | AMD Radeon R9 285 2GB | 20 | alta | Tonga, na faixa da R9 280 (classe 20). | [link](https://www.techspot.com/review/946-nvidia-geforce-gtx-960/page9.html) |
| GPU | Intel Arc A310 4GB | 25 | média | A RX 6400 (classe 40) fica ~42% à frente e a GTX 1650 ~36% a 73%; faixa da GTX 1050 Ti (classe 25). Fonte agregadora. | [link](https://technical.city/en/video/Radeon-RX-6400-vs-Arc-A310) |
| GPU | AMD Radeon RX Vega 64 8GB | 250 | alta | Cerca de 14% acima da Vega 56 (classe 200) e ~30% abaixo da GTX 1080 Ti (classe 300); faixa da RX 5700 (250). | [link](https://www.techspot.com/review/2523-amd-vega-gpu-revisit/) |

## Não classificado de propósito

- **Variantes ambíguas** (a nota depende da memória ou do chip): RX 480, RX 550, RX 580, GTX 960, GTX 1060, RTX 2060 e Arc A770, além de `AMD RX 5500XT 4GB` (o catálogo só tem a versão de 8 GB). Seguem a política de `scripts/test_alias_policy.py`.
- **Sem modelo definido**: textos como "2.5 GHz Dual Core", "DirectX 10 capable" e "Ryzen 5 series".
- **Outros**: Intel Iris Xe e Qualcomm Adreno X1 (variam por configuração ou são ARM), Snapdragon X Elite, Intel Core i3-9350F (nome inexistente; o modelo é i3-9350KF), GTX 630 (grafia incorreta de GT 630), Radeon HD 6450 (aparece só em lista composta) e Radeon HD 7510/7800.

## Como reprocessar

```bash
docker compose run --rm data python scripts/update_catalog.py --snapshot-dir data/raw/<pasta-do-lote> --load
```

O hash do catálogo de hardware muda; é preciso reprocessar os jogos para que os novos modelos sejam resolvidos.

## Correções posteriores

Regra adotada: peças com diferença de até cerca de 10% em médias de jogos (rasterização nativa) tendem a ficar na mesma classe. Ela é aproximada: o agrupamento não é transitivo, então cada caso foi conferido contra comparações diretas.

| Peça | Antes | Depois | Evidência |
| --- | ---: | ---: | --- |
| AMD Radeon RX 6600 XT 8GB | 350 | 300 | [TechSpot, 50 jogos (2022)](https://www.techspot.com/review/2525-geforce-gtx-1080-ti-revisit/): GTX 1080 Ti 3% à frente da RTX 3060 a 1080p e 3% atrás da RX 5700 XT; a 6600 XT tem desempenho comparável ao da 3060. [TechSpot, 33 jogos](https://www.techspot.com/review/2508-radeon-5700-xt-revisit/): 5700 XT 6% à frente da 3060 a 1440p; a 6600 XT entrega desempenho de 5700 XT. Todas essas estão na classe 300. |
| NVIDIA GeForce RTX 4070 12GB | 450 | 500 | [Tom's Hardware](https://www.tomshardware.com/reviews/nvidia-geforce-rtx-4070-review/5): menos de 2% de diferença para a RTX 3080 a 1440p e 26% acima da RTX 3070 Ti. [TechSpot](https://www.techspot.com/review/2663-nvidia-geforce-rtx-4070/): entre -3% e +4% da 3080 em vários jogos. Confiança alta. |

Efeito: o Dragon's Dogma 2 pede RTX 2070 SUPER ou RX 6600 XT nos recomendados; o menor valor entre as alternativas passou de 350 para 300, e a RTX 3060 12GB passa a atender esse nível.

### Candidatas avaliadas e não alteradas

- **RX Vega 64 (250):** o PassMark (usado só como apoio) a coloca cerca de 14% abaixo da RX 5700 XT (300); a classe 250 parece razoável.
- **RX 5700 8GB (250) contra RTX 2060 SUPER (300):** confirmar a distância em jogos.
- **RX 6650 XT (350) e RX 7600 (350) contra RTX 3060 12GB (300):** as fontes divergem entre 2% e 18% de diferença.
- **RTX 2070 SUPER (350):** fica 7% a 13% acima da 3060 e da 5700 XT, na fronteira entre 300 e 350.
- **GTX 1050 Ti (25) e GTX 780 (30):** TechSpot e Technical City apontam a 780 cerca de 8% à frente em jogos; a distância de cinco classes parece grande.

Verificações com dados de jogos, sem alteração: **RX 560 (15)** fica igual à GTX 1050 em 30 jogos do [TechSpot](https://www.techspot.com/review/1430-radeon-rx-560-vs-geforce-gtx-1050/page8.html) e a RX 460 fica 18% abaixo; **Arc A750 (300)** empata com a RTX 3060 no Tom's Hardware e fica 13% acima da RX 6600 a 1440p no TechPowerUp, enquanto o PassMark subestima as Arc; **GTX 780 (30)** e **GTX 960/R9 380/GTX 1050 Ti**: as comparações em jogos são só de agregadores e divergem, sem base para mover.

**GTX 970 (40):** foi subida para 50 e depois revertida. A evidência da GTX 1650 mostrou que a 970 fica de 7% a 12% abaixo da GTX 1060 3GB (classe 50) e praticamente empata com a GTX 1650 (classe 40): a 970 é só 1% a 3% mais rápida segundo a [PC Gamer](https://www.pcgamer.com/nvidia-geforce-gtx-1650-review), e a 1650 fica 9% a 15% atrás da 1060 3GB segundo o [TechSpot](https://www.techspot.com/review/1835-nvidia-geforce-gtx-1650/). A classificação original (970, GTX 1650, RX 470 e RX 6400 em 40; 1060 3GB, RX 480 e RX 570 em 50) se sustenta. A margem exata é incerta, porque os percentuais vieram de resumos e as duas versões do TechSpot divergem.

## Variantes de VRAM

Oito modelos tinham variantes de memória diferentes na mesma classe. Cada par foi comparado em jogos antes de decidir se separar:

| Modelo | O que as fontes mostram | Decisão |
| --- | --- | --- |
| RX 480 4GB e 8GB | ~5% a 1080p ([LegitReviews](https://legitreviews.com/amd-radeon-rx-480-4gb-versus-radeon-rx-480-8gb_183576/4)); a diferença vem da velocidade da memória (7 e 8 Gbps), não da capacidade. | Mesma classe (50) |
| RX 580 4GB e 8GB | ~10% só no agregador [CheckFPS](https://checkfps.io/en/compare/rx-580-4gb-vs-rx-580-8gb), sem outra fonte. | Mesma classe (100); evidência fraca |
| RX 550 e RX 560, 2GB e 4GB | Sem comparação confiável encontrada. | Mesma classe; sem base para separar |
| GTX 960 2GB e 4GB | Média de 5% a 7% e até ~14% em jogos novos ([GamersNexus](https://gamersnexus.net/guides/1888-evga-supersc-4gb-960-benchmark-vs-2gb)); o [TechSpot](https://www.techspot.com/review/1114-vram-comparison-test/) não achou diferença em vários jogos. | Mesma classe (20) |
| **GTX 1050 2GB** e 4GB | Estouro de VRAM documentado: a versão de 3GB rende 65% mais no Wolfenstein ([TechSpot](https://www.techspot.com/review/1675-nvidia-geforce-gtx-1050-3gb/)) e a de 2GB tem picos de tempo de quadro ([Tom's Hardware](https://www.tomshardware.com/reviews/geforce-gtx-1050-3gb-benchmarks,5654.html)). | **2GB passa de 15 para 10**; 4GB continua em 15 |
| Arc A770 8GB e 16GB | A Intel diz que rendem o mesmo; uma revista aponta o dobro a 1440p, sem como conferir. | Mesma classe (350) |
| RTX 4060 Ti 8GB e 16GB | Rasterização 0% a 5% ([Tom's Hardware](https://www.tomshardware.com/reviews/nvidia-geforce-rtx-4060-ti-16gb-review/7)); 18% a 34% só com ray tracing e texturas máximas. | Mesma classe (400) |

A regra resultante está em `SCORING.md` (item 5). Dúvida aberta: o catálogo tem uma "GTX 1050 4GB", mas a NVIDIA vendeu a GTX 1050 só com 2GB e 3GB (os 4GB são a 1050 Ti, outro chip); vale conferir se o nome está certo.


## Curadoria dos textos genéricos de requisito

Das 45 combinações (jogo, nível e campo) em que a Steam publica um texto genérico, **34 receberam uma referência manual** em `requirements_curation.json` (164 regras no total, eram 130). Cada regra vale para um único jogo, nível e texto exato; se o texto da Steam mudar, ela deixa de valer. A nota é o **menor** valor entre os modelos de referência. Na tela, a comparação aparece como **estimativa**, e o texto original é preservado.

**Critério.** Curei quando o texto fixa um piso nomeado ("HD 4000 or better"), uma geração de API (DirectX 10 ou 11), um clock com número de núcleos, ou lista alternativas em que o modelo nomeado domina. Deixei pendente quando o texto só cita memória ("512 MB display memory"), uma família que atravessa gerações ("Core i5", "Ryzen 5 series", "Six-Core CPU") ou nada útil ("Intel"). Alternativas em ARM (Snapdragon X Elite, Adreno X1) ficam fora porque o perfil do GameCompass é x64, e isso está dito na justificativa de cada regra.

| Jogo | Nível | Campo | Texto da Steam | Referência | Nota |
| --- | --- | --- | --- | --- | ---: |
| Baldur's Gate 3 | mín. | CPU | Intel I5 4690 / AMD FX 8350 / Snapdragon X Elite | Intel Core i5-4690, AMD FX-8350 | 50 |
| Baldur's Gate 3 | mín. | GPU | Nvidia GTX 970 / RX 480 / Intel Arc A380 / Qualcomm Adreno X1 (4GB+ of | NVIDIA GeForce GTX 970, AMD Radeon RX 480 4GB, AMD Radeon RX 480 8GB, Intel Arc A380 6GB | 40 |
| Age of Empires II: Definitive Edit | mín. | CPU | Intel Core 2 Duo or AMD Athlon 64x2 5600+ | Intel Core 2 Duo E4500, AMD Athlon 64 X2 5600+ | 5 |
| Age of Empires II: Definitive Edit | mín. | GPU | NVIDIA® GeForce® GT 420 or ATI™ Radeon™ HD 6850 or Intel® HD Graphics  | NVIDIA GeForce GT 420, AMD Radeon HD 6850, Intel HD Graphics 4000 | 1 |
| DARK SOULS™ III | rec. | GPU | NVIDIA® GeForce GTX 970 / ATI Radeon R9 series | NVIDIA GeForce GTX 970, AMD Radeon R9 290X 4GB | 40 |
| RimWorld | mín. | GPU | Intel HD Graphics 4000 or other shader model 4.0 | Intel HD Graphics 4000 | 1 |
| Cities: Skylines | mín. | GPU | Nvidia® GeForce™ GTS 450 (1 GB) / AMD® R7 250 (2 GB) / Intel Iris Xe G | NVIDIA GeForce GTS 450, AMD Radeon R7 250 2GB | 3 |
| The Binding of Isaac: Rebirth | rec. | GPU | Intel HD Graphics 4000 and higher, ATI Radeon HD-Series 4650 and highe | Intel HD Graphics 4000 | 1 |
| Assetto Corsa | mín. | CPU | AMD Athlon X2 2.8 GHZ, Intel Core 2 Duo 2.4 GHZ | AMD Athlon 64 X2 5600+, Intel Core 2 Duo E6600 | 5 |
| Rocket League® | mín. | CPU | 2.5 GHz Dual core | Intel Core 2 Duo E6750 | 5 |
| Rocket League® | rec. | CPU | 3.0+ GHz Quad core | Intel Core 2 Quad Q9650 | 15 |
| Counter-Strike 2 | mín. | GPU | A placa gráfica deve ter, no mínimo, 1 GB e ser compatível com DirectX | AMD Radeon HD 5450 | 1 |
| Dota 2 | mín. | CPU | Dual core da Intel ou da AMD com 2,8 GHz | AMD Athlon 64 X2 5600+ | 5 |
| Dota 2 | mín. | GPU | NVIDIA GeForce 8600/9600GT, ATI/AMD Radeon HD2600/3600 | NVIDIA GeForce 9600 GT 512MB | 2 |
| A Short Hike | mín. | CPU | Intel or AMD Dual Core at 2 GHz or better | Intel Core 2 Duo E4400 | 5 |
| Dorfromantik | mín. | CPU | 2 GHz Dual Core (Intel / AMD) | Intel Core 2 Duo E4400 | 5 |
| Dorfromantik | mín. | GPU | Nvidia GT550M / AMD Radeon R7/HD 5650 / Intel HD 520 | NVIDIA GeForce GT 550M, AMD Radeon HD 5650, Intel HD Graphics 520 | 2 |
| Dorfromantik | rec. | CPU | 2.5 GHz Dual Core (Intel / AMD) | Intel Core 2 Duo E6750 | 5 |
| Dorfromantik | rec. | GPU | Nvidia GT740M / AMD Radeon R8 / Intel HD 630 | NVIDIA GeForce GT 740M, Intel HD Graphics 630 | 2 |
| Spiritfarer®: Edição Farewell | mín. | CPU | Dual Core 3.0 GHz Processor | Intel Core 2 Duo E8400 | 8 |
| Spiritfarer®: Edição Farewell | mín. | GPU | DirectX 10-compatible graphics card with at least 1GB of video memory | AMD Radeon HD 5450 | 1 |
| Coffee Talk | mín. | CPU | 2.4 GHz or faster processor | Intel Core 2 Duo E6600 | 5 |
| PowerWash Simulator | mín. | CPU | Intel i5-760 (4*2800), AMD Phenom II | Intel Core i5-760, AMD Phenom II X4 945 | 20 |
| Frostpunk | mín. | CPU | 3.2 GHz Dual Core Processor | Intel Core 2 Duo E8500 | 8 |
| Frostpunk | rec. | CPU | 3.2 GHz Quad Core Processor | AMD Phenom II X4 955 | 20 |
| Kerbal Space Program | mín. | CPU | Core 2 Duo 2.0 Ghz | Intel Core 2 Duo E4400 | 5 |
| Kerbal Space Program | mín. | GPU | DX10 (SM 4.0) capable, 512MB VRAM | AMD Radeon HD 5450 | 1 |
| Kerbal Space Program | rec. | GPU | DX10 (SM 4.0) capable, 1GB VRAM | AMD Radeon HD 5450 | 1 |
| Crusader Kings III | mín. | GPU | NVIDIA GeForce GTX 660 / AMD Radeon HD 7870 / Intel Arc A310 / Intel I | NVIDIA GeForce GTX 660, AMD Radeon HD 7870 2GB, Intel Arc A310 4GB, AMD Radeon RX Vega 11 | 3 |
| Amnesia: The Dark Descent | mín. | CPU | 2.0Ghz - Low budget CPUs such as Celeron or Duron needs to be at about | Intel Core 2 Duo E4400 | 5 |
| Amnesia: The Dark Descent | mín. | GPU | Radeon X1000/GF 6 - Integrated graphics and very low budget cards migh | ATI Radeon X1950 Pro 256MB, NVIDIA GeForce 6800 GT | 1 |
| Don't Starve Together | mín. | CPU | 1.7+ GHz or better | AMD Athlon 64 3000+ | 5 |
| Rayman® Legends | mín. | CPU | Intel Pentium IV @ 3.0 GHz or AMD Athlon64 3000 + @ 1.8 GHz | AMD Athlon 64 3000+ | 5 |
| Rayman® Legends | rec. | GPU | nVidia GeForce 9600GT or higher, AMD Radeon HD3850 or higher (512MB VR | NVIDIA GeForce 9600 GT 512MB, ATI Radeon HD 3850 512MB | 2 |

**Ficaram pendentes de propósito (11):** Assetto Corsa recomendado ("Six-Core CPU, Quad-Core CPU"), Coffee Talk GPU ("512 MB display memory"), Total War: WARHAMMER III (CPU "i3/Ryzen 3 series", GPU "GTX 900/RX 400 series" e CPU recomendada "i5/Ryzen 5 series"), Kerbal Space Program recomendado ("Core i5"), Raft ("Core i5 2.6GHz or similar"), TUNIC ("i5 Quad-Core") e Firewatch ("Core i3 2.00 GHz or AMD equivalent"). Faltam gerações para limitar a classe.

**Efeito.** Blocos do mínimo em revisão: 36 para 21. Jogos com base de comparação no Windows: 99 para 108 de 120. Na avaliação offline (60 perfis simulados), os jogos `pending` por perfil caíram de 10,5 para 7,0 e os `items` subiram de 36,6 para 39,9.

**O que ainda impede os 21 jogos do mínimo.** Quase todos têm uma única pendência de GPU: variantes de memória sem a capacidade no texto (RX 550, GTX 960, GeForce 7600 GT e outras, que continuam pendentes pela política dos aliases), textos compostos ou com "or equivalent" (Factorio, Rainbow Six Siege, Frostpunk, Alien: Isolation, Don't Starve Together), peças ainda fora do índice (GeForce GTX 630 e "GTX 700 series", entre outras) e dois campos que a Steam não publicou (RAM do Unpacking, GPU do A Hat in Time).
