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
