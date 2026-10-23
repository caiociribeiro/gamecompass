# Catálogo de equivalência de hardware — contrato inicial

O catálogo associa o modelo exato de uma peça à sua pontuação de benchmark.
Esta etapa define e valida o formato; não contém um catálogo artificial,
um coletor de páginas ou uma carga para o Neo4j.

## Formato do CSV

Use UTF-8, vírgula como separador e o seguinte cabeçalho, nesta ordem:

```text
component_type,name,passmark_score,benchmark,source_url,collected_at
```

| Campo | Conteúdo |
| --- | --- |
| component_type | CPU ou GPU |
| name | Nome completo do modelo, preservando sua variante |
| passmark_score | Pontuação inteira positiva publicada pela fonte |
| benchmark | CPU Mark para CPU; G3D Mark para GPU |
| source_url | URL pública HTTPS da página da fonte correspondente |
| collected_at | Data e hora reais da coleta, com fuso, em ISO 8601 |

O processamento aceita pontuações inteiras já sem separadores. Também
aceita vírgulas de milhar no formato da fonte em inglês, desde que o campo
esteja entre aspas no CSV. Ele não arredonda pontuações nem atribui zero
a valores ausentes. Todos os campos são obrigatórios.

## Identidade dos modelos

Preserve nomes e informações como Ti, SUPER, XT, Laptop e capacidade de
VRAM quando fizerem parte do modelo. Não associe automaticamente modelos
somente porque os nomes são parecidos.

A normalização desta etapa ajusta espaços, tipo de componente, nome da
métrica e fuso da coleta. A correspondência com os nomes dos requisitos
da Steam será uma etapa própria. Duplicidades do par tipo/nome são
rejeitadas, inclusive quando diferem apenas por maiúsculas ou espaços.

## Como funciona a pontuação

`passmark_score` armazena o CPU Mark ou G3D Mark publicado pela fonte.
O sistema não estima essa nota a partir de núcleos, GHz ou quantidade de VRAM.

A comparação posterior usa três verificações independentes:

```python
cpu_atende = cpu_do_pc >= cpu_minima_do_jogo
gpu_atende = gpu_do_pc >= gpu_minima_do_jogo
ram_atende = ram_do_pc_gb >= ram_minima_do_jogo_gb
atende = cpu_atende and gpu_atende and ram_atende
```

Uma razão entre o score do PC e o score exigido mede a posição relativa
naquela métrica; não corresponde a uma razão de FPS. CPU Mark e G3D Mark
não serão somados. Os modelos do PC e dos requisitos devem ser associados
ao mesmo catálogo de referência. Um modelo não identificado fica pendente
de revisão, sem receber uma pontuação arbitrária.

## Diretórios e execução

- `data/raw/`: arquivos de entrada obtidos da fonte, preservados para auditoria.
- `data/processed/`: resultado normalizado e validado.
- O CSV inicial de importação deve seguir o contrato acima. O adaptador
  específico da fonte será desenvolvido depois de definir o acesso aos dados.

Na raiz do projeto, inspecione o contrato:

```bash
docker compose run --rm --no-deps data python scripts/hardware_catalog.py --describe
```

Quando houver uma entrada real no formato acordado:

```bash
docker compose run --rm --no-deps data python scripts/hardware_catalog.py
```

A entrada padrão é `data/raw/hardware_benchmarks.csv`; a saída é
`data/processed/hardware_benchmarks.csv`. Use `--input` e `--output` para
escolher outros caminhos. Um catálogo vazio é rejeitado. Se um registro
for inválido, a saída anterior é preservada. O script não altera a entrada
nem o banco e não acessa a internet.

## Fonte e reprodução do experimento

Registre a origem e a data real da coleta. Preserve a entrada utilizada
no experimento; não a substitua silenciosamente por uma coleta nova.
Os datasets gerados continuam ignorados pelo Git; este documento e os
scripts de processamento são versionados.

O PassMark oferece os dados estruturados por assinatura e informa
restrições de uso e republicação. A disponibilidade das páginas públicas
não deve ser tratada como uma API gratuita. A obtenção e a forma de uso
dos dados do TCC ainda precisam ser definidas. Esta etapa de processamento
funciona com arquivos fornecidos ao projeto por uma via autorizada.

Referências consultadas em 23/10/2026:

- https://www.passmark.com/services/market-analysis.php
- https://www.cpubenchmark.net/graph_notes.html
- https://www.videocardbenchmark.net/
