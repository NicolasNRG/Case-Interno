# Case · Vértice Soluções Industriais

Agente de primeiro contato e qualificação de leads. Arquivos nomeados pelo número do entregável.

| # | Entregável | Arquivos | Status |
|---|---|---|---|
| 1 | Tabela analítica e script de ETL | `01_etl.py`, `01_tabela_analitica.csv/.xlsx`, `01_contagens_etl.json`, `01_nota_decisoes.md` | feito |
| 2 | Documento de Baseline | `02_baseline.md`, `02_calculos_baseline.py`, `02_metricas_baseline.json` | feito |
| 3 | Reconciliação do dashboard | — | a fazer |
| 4 | Critérios de aceite e eventos | — | a fazer |
| 5 | Arquitetura do agente | — | a fazer |
| 6 | Histórico de conversas com o Claude | links compartilhados | a fazer |

Os materiais originais e a versão da tabela com contatos não são versionados (ver `01_nota_decisoes.md`, seção 6).

Para reproduzir:

```
python 01_etl.py --input <pasta_dos_materiais> --output . --output-local saida_local
python 02_calculos_baseline.py --tabela 01_tabela_analitica.csv --saida 02_metricas_baseline.json
```
