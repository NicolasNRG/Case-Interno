# Case · Vértice Soluções Industriais

Agente de primeiro contato e qualificação de leads. Arquivos nomeados pelo número do entregável.

| # | Entregável | Arquivos | Status |
|---|---|---|---|
| 1 | Tabela analítica e script de ETL | `01_etl.py`, `01_tabela_analitica.csv/.xlsx`, `01_contagens_etl.json`, `01_nota_decisoes.md` | feito |
| 2 | Documento de Baseline | `02_baseline.md`, `02_calculos_baseline.py`, `02_metricas_baseline.json` | feito |
| 3 | Reconciliação do dashboard | `03_reconciliacao_dashboard.md`, `03_reconciliacao.py`, `03_reconciliacao.json` | feito |
| 4 | Critérios de aceite e eventos | `04_criterios_aceite_eventos.md`, `04_linhas_de_base_criterios.py`, `04_linhas_de_base.json` | feito |
| 5 | Arquitetura do agente | `05_arquitetura_agente.md` | feito |
| 6 | Histórico de conversas com o Claude | links compartilhados | a fazer |

Os materiais originais e a versão da tabela com contatos não são versionados (ver `01_nota_decisoes.md`, seção 6).

Para reproduzir (Python 3.10+; `pip install -r requirements.txt`), rode os scripts **nesta ordem**. O 02 e o 03 leem a tabela gerada pelo 01; se o código mudar, gere a tabela de novo antes:

```
python 01_etl.py --input <pasta_dos_materiais> --output . --output-local saida_local
python 02_calculos_baseline.py --tabela 01_tabela_analitica.csv --saida 02_metricas_baseline.json
python 03_reconciliacao.py --input <pasta_dos_materiais> --tabela 01_tabela_analitica.csv --saida 03_reconciliacao.json
python 04_linhas_de_base_criterios.py --tabela 01_tabela_analitica.csv --saida 04_linhas_de_base.json
```
