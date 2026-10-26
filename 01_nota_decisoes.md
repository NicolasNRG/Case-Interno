# Entregável 1 · Nota de decisões do ETL

**Resultado:** 4.132 leads únicos, um por linha: 4.100 vindos do CRM e 32 que só existem na planilha dos SDRs. Nenhuma mensagem e nenhum deal foi descartado sem virar contagem. O que saiu foi fundido em duplicidade ou está documentado abaixo.

| Arquivo | O que é |
|---|---|
| `01_etl.py` | Script reproduzível (Python 3.10+, pandas, openpyxl). Gera todos os arquivos abaixo |
| `01_tabela_analitica_com_contatos.xlsx` | **A tabela entregue:** um lead por linha, com nome, telefone e e-mail. Vai para uma pasta separada (`--output-local`), fora do git (ver seção 6) |
| `01_tabela_analitica.csv` / `.xlsx` | Gerada ao rodar o script: a mesma tabela **pseudonimizada** (sem nome, telefone e e-mail). É a versão que fica no git e a que os scripts dos entregáveis 2 a 4 leem |
| `01_contagens_etl.json` | Gerado ao rodar o script: as contagens da seção 4, em formato de máquina |

Para rodar: `python 01_etl.py --input <pasta_dos_materiais> --output . --output-local saida_local`. Leva cerca de 10 segundos.

---

## 1. Como as fontes foram juntadas

```
CRM (4.332 deals) ──dedup por telefone OU e-mail──> 4.100 leads ──┬──> tabela (1 lead por linha)
Conversas (12.900 msgs) ──telefone (WhatsApp) / e-mail──────────────┤
Planilha SDR (1.170 linhas) ──telefone, conferido pelo código VS────┘   + 32 leads só da planilha
```

- **Chave do lead:** telefone normalizado (11 dígitos, sem o 55; havia 6 formatos) **ou** e-mail normalizado (minúsculas, sem espaços). É a regra do próprio playbook (seção 6: "mesmo telefone ou e-mail = mesmo lead").
- **Papel de cada fonte quando elas discordam:**
  - **O CRM manda no funil e no resultado.** É o único sistema de registro.
  - **O log de conversas manda no tempo de resposta.** O horário vem do sistema de mensagens, não de quem preencheu.
  - **A planilha é auxiliar.** Entra como colunas `planilha_*`, mas não altera nenhum campo do CRM.
- **Planilha → CRM:** liguei pelo telefone, que está presente nas 1.170 linhas. O código VS faltava em 112 linhas e estava fora do padrão em outras 71 ("VS 02818", "vs-…"). Por isso serviu só de conferência: nas 1.039 linhas com código, ele bate com o telefone em 100% dos casos.
- **Conversas → CRM:** 100% das 12.900 mensagens se ligaram a um lead. Cada lead usa um único canal.

## 2. Duplicatas

| Fonte | O que encontrei | Regra aplicada |
|---|---|---|
| CRM | 232 pares de deals com o mesmo telefone e e-mail. As cópias são os IDs D-2026-04101 a 04332, criadas de 1 a 21 dias depois do original, com o mesmo dono e a mesma origem. **Só 52 estavam marcadas como "Duplicado".** | Os deals viram um lead só. O **deal principal** é o que entrou primeiro. As **datas de etapa** são a primeira ocorrência entre os deals. O **status** é ganho se qualquer deal ganhou; senão aberto se algum está aberto; senão perdido. O **motivo de perda** vem do deal perdido mais recente, ignorando "Duplicado" (motivo administrativo). O **valor** é o do deal ganho ou, se não houver, o do principal. `n_deals_crm` e `deal_ids` guardam o rastro. |
| Planilha | 21 linhas repetidas (mesmo telefone), todas idênticas à primeira ocorrência e sempre na mesma aba | Fica a primeira ocorrência; as outras 21 são descartadas |
| Conversas | Nenhuma linha repetida | — |
| Homônimos | 8 pares com o mesmo nome e a mesma empresa, mas telefone e e-mail diferentes | **Não** foram fundidos: pela regra do playbook são contatos distintos |

**Efeito colateral importante:** as cópias herdaram `qualified_flag = true` (86 casos) e `proposal_sent = true` (49 casos) sem ter passado pelas etapas. Por isso **"qualificado" é definido pela etapa no histórico, não pela flag.** A flag original fica em `qualified_flag_crm` para a reconciliação do entregável 3.

## 3. O que foi corrigido sem descartar registro

| Problema | Quantidade | Tratamento |
|---|---|---|
| `created_at` inválido: ano 2024, dias 31/04 e 30/02, mês 13 e o valor fixo "30/06/2026 14:20" | 52 deals | Uso a data da etapa "Entrada", que é sempre válida e coincide com `created_at` nos outros 4.280 deals. Marcado em `dq_created_at_invalido` |
| `stage_history` fora de ordem no array, mas com horários consistentes | 81 deals | Ordenado pelo horário. Depois disso, 100% das sequências ficam canônicas |
| Deal ganho sem a etapa "Fechamento" | 12 deals | `updated_at` é usado como data do ganho |
| Segmento com 23 grafias | 1.329 deals | Mapeado para os 7 segmentos do playbook ("Autopeças" vira Automotivo, "Celulose" vira Papel e Celulose). Nada ficou sem mapear. O original fica em `segmento_original` |
| Valor estimado entre R$ 450 mil e R$ 3,3 milhões | 61 deals (4 ganhos) | Existe um vazio entre R$ 60,1 mil e R$ 450 mil, e todos esses valores são múltiplos de R$ 10 mil. Isso é compatível com digitação ×100, mas é só hipótese. **Decisão conservadora:** `valor_estimado` mantém o original e `valor_estimado_tratado` fica vazio, sem tentar corrigir |
| Data na planilha em 4 formatos | 1.170 linhas | Data do Excel (656), "dd/mm/aaaa hh:mm" (336) e "dd/mm" sem ano, assumido 2026 (121). **"mm/dd/aaaa" no padrão americano (57):** detectado porque o mês aparece na primeira posição e bate com a aba. O cruzamento com o CRM confirma 56 dos 57 |
| SDR com 15 grafias e status com 19 valores | 1.170 linhas | Os SDRs foram mapeados para os 4 nomes do CRM. Os status foram mapeados para 8 categorias. **"fechado/FECHADO" foi tratado como ganho:** das linhas "fechado/ganho", 108 estão ganhas no CRM, 63 abertas em Proposta e nenhuma perdida |
| Horário com sufixo "Z" (UTC) no log | 129 mensagens | Tratado como horário local (-03:00). Evidência: nas 31 primeiras respostas com "Z", 30 batem exatamente com a etapa "Contato" do CRM quando lidas como horário local; lidas como UTC, ficariam 3h fora |

## 4. Registros por etapa (o que entrou, o que saiu)

| Etapa | Entrou | Saiu | Ficou | Observação |
|---|---|---|---|---|
| CRM · leitura | 4.332 deals | 0 | 4.332 | Bate com o `record_count` do export |
| CRM · deduplicação | 4.332 | 232 (fundidos) | **4.100 leads** | Nenhum dado se perde: a cópia é absorvida pelo lead |
| Conversas · leitura | 12.900 msgs | 0 | 12.900 | — |
| Conversas · ligação ao lead | 12.900 | 0 | 12.900 msgs em 3.533 leads | — |
| Planilha · leitura | 1.170 linhas | 0 | 1.170 | Jul 398 · Ago 381 · Set 391 |
| Planilha · linhas repetidas | 1.170 | 21 | 1.149 | Cópias exatas |
| Planilha · ligação ao CRM | 1.149 | 0 | 1.117 ligadas + 32 sem CRM | As 32 têm Obs "não achei no CRM" e viraram leads `LP-…` |
| **Tabela final** | | | **4.132 leads** | 1.475 no Q3 (1.443 do CRM + 32 só da planilha) |

**Cobertura por fonte:**

| Fonte | Leads (total) | Leads no Q3 |
|---|---|---|
| CRM + conversas + planilha | 1.117 | 1.117 |
| CRM + conversas | 2.416 | 125 |
| Só CRM | 567 | 201 |
| Só planilha | 32 | 32 |

Fora do Q3 a planilha não existe, e por isso as colunas `planilha_*` ficam vazias para esses leads.

## 5. O que os cruzamentos já revelam (insumo para os próximos entregáveis)

- **A planilha só registra quem foi contatado.** Os 313 leads do Q3 que nunca saíram de "Entrada" não aparecem nela. Ela não serve para medir demanda.
- **A planilha discorda do CRM no resultado em 201 de 1.117 leads (18%):**
  - 63 estão "fechado/ganho" na planilha e abertos em Proposta no CRM;
  - 132 estão "qualificado/proposta" na planilha e perdidos no CRM.
  A planilha não é atualizada depois do primeiro registro.
- **Os 32 leads só da planilha** vieram de "whatsapp direto" ou "ligou" (18) e de indicação (14). **12 deles estão marcados "qualificado" e nunca entraram no CRM:** é demanda que o painel não enxerga.
- **13 leads do Q3 tiveram o primeiro deal ignorado** e só foram contatados quando voltaram por um deal duplicado. No nível do lead, o tempo de resposta deles é medido desde a primeira entrada (dias). Do ponto de vista do lead, foi isso que aconteceu.
- **Tempo até o primeiro contato** (da chegada do lead ao primeiro contato, juntando CRM e log): mediana de 25 min úteis. **Só 27% dos leads de entrada são contatados dentro do SLA do playbook**, e 463 leads mandaram mensagem e nunca receberam resposta. Números oficiais no entregável 2.
- **O log nunca mostra contato antes da etapa "Contato" do CRM.** Isso valida o horário do CRM como o primeiro contato real.
- **Nenhuma chegada aparece fora do expediente,** mas as entradas se concentram às 8h e na segunda-feira. Ver limitação 2.

### Revisão feita durante o entregável 2

A primeira versão da tabela media o tempo de resposta pelo log, como "da 1ª mensagem do lead à 1ª resposta". Ao cruzar essa medida com a conversão, apareceu um paradoxo: leads respondidos depois de 4h convertiam mais. A causa: quando a Vértice inicia a conversa, a "resposta" capturada é um follow-up de dias depois, e leads que avançam no funil recebem mais follow-ups.

A medida foi trocada por **chegada → primeiro contato**:
- a **chegada** é a entrada no CRM ou a 1ª mensagem do lead, o que vier antes;
- o **contato** é a etapa Contato ou a 1ª mensagem da Vértice, o que vier antes.

As colunas `tempo_1a_resposta_*` e `tempo_resposta_crm_*` saíram da tabela. Deram lugar às colunas `data_chegada`, `data_primeiro_contato` e `tempo_ate_1o_contato_*`, e às colunas de SLA. Detalhes no entregável 2, seção 2.

## 6. Decisões de privacidade

A Ficha proíbe que dados de contato dos leads saiam do ambiente da Vértice. A versão versionada no git **não tem nome, telefone nem e-mail do contato**. O `lead_id` é derivado do número do deal (`L-01003`) ou da linha da planilha (`LP-Jul-013`), e por isso não carrega dado pessoal. A versão com contatos é gerada em `saida_local/`, que está no `.gitignore`. Os materiais originais também não são versionados.

## 7. Limitações declaradas

1. **Feriados não foram considerados** no cálculo de minutos úteis (expediente seg–sex, 8h–18h, conforme o playbook).
2. **A espera fora do expediente é invisível.** Quase nenhuma mensagem ou entrada aparece fora do horário comercial, e há picos às 8h e na segunda-feira. O registro parece acontecer quando alguém abre o sistema, não quando o lead escreve. O tempo de resposta calculado é, portanto, um **limite inferior**. Confirmar com a Vértice se o WhatsApp Business guarda o horário original de recebimento.
3. **O segmento do CRM não é confiável para qualificação.** Todos os 4.100 leads estão num segmento-alvo, e mesmo assim há 555 deals perdidos por "Fora do segmento". O campo parece preenchido por padrão.
4. **O porte vem em faixa.** A faixa "11-50" cruza os dois limites do playbook (20 e 50) e é classificada como `indefinido` em `porte_playbook`.
5. **A campanha não é confiável:** o rótulo de trimestre da campanha não bate com a data do lead. A tabela usa `canal_origem` como origem oficial.
6. **Para os 32 leads só da planilha**, `data_entrada` é a data do 1º contato registrada pelo SDR, porque é a única disponível. Eles não têm resultado e ficam fora das métricas de conversão.

## 8. Dicionário de colunas (75)

**Identificação e cobertura**

| Coluna | Significado |
|---|---|
| `lead_id` | Identificador do lead |
| `fonte_registro` | Em quais fontes o lead aparece (`em_crm`, `em_conversas` e `em_planilha` são as mesmas informações como colunas booleanas) |
| `deal_id_principal` / `deal_ids` / `n_deals_crm` | Deal principal, todos os deals do lead e quantos são |
| `codigo_vs` | Código VS do deal |

**Empresa**

| Coluna | Significado |
|---|---|
| `segmento` / `segmento_original` | Segmento normalizado e grafia original |
| `porte_faixa` / `porte_playbook` | Faixa de funcionários e o que o playbook permite concluir dela |
| `cidade`, `uf` | Localização |

**Origem e responsável**

| Coluna | Significado |
|---|---|
| `canal_origem` | Canal do CRM (para os leads só da planilha, mapeado da coluna Origem) |
| `campanha` | Campanha do CRM (pouco confiável, ver limitação 5) |
| `sdr_responsavel` | SDR dono do lead |

**Funil (CRM)**

| Coluna | Significado |
|---|---|
| `data_entrada`, `mes_entrada` | Data e mês de entrada do lead |
| `periodo_q3` | Entrada entre 01/07 e 30/09 |
| `dias_entrada_ate_export` | Idade do lead na data do export, usada para saber se o grupo já teve tempo de fechar |
| `data_primeiro_contato_crm`, `data_qualificacao`, `data_proposta`, `data_ganho` | Primeira vez em cada etapa |
| `etapa_max` | Etapa mais avançada alcançada |
| `status_lead` (won/open/lost), `motivo_perda` | Resultado e motivo |
| `contatado_crm`, `qualificado`, `proposta_enviada`, `ganho` | Booleanos derivados do histórico de etapas |
| `ciclo_dias` | Dias da entrada ao ganho |
| `valor_estimado`, `valor_estimado_tratado` | Valor original e valor sem os outliers |
| `qualified_flag_crm` | Flag original do CRM, mantida para a reconciliação |

**Conversas**

| Coluna | Significado |
|---|---|
| `canal_conversa` | WhatsApp ou e-mail |
| `n_msg_lead`, `n_msg_vertice` | Quantidade de mensagens de cada lado |
| `conversa_iniciada_por` | `lead` ou `vertice` |
| `data_primeira_msg_lead`, `data_primeira_msg_vertice` | Primeira mensagem de cada lado |
| `lead_sem_resposta` | Lead mandou mensagem e não recebeu nenhuma mensagem da Vértice depois |
| `intencao_primeira_msg` | 7 categorias |
| `data_ultima_msg` | Última mensagem trocada |

**Tempo até o primeiro contato (CRM + log)**

| Coluna | Significado |
|---|---|
| `data_chegada` | Entrada no CRM ou 1ª mensagem do lead, o que vier antes |
| `chegada_no_expediente` | Se a chegada foi dentro do horário comercial |
| `data_primeiro_contato` | Etapa Contato ou 1ª mensagem da Vértice, o que vier antes |
| `tempo_ate_1o_contato_min`, `tempo_ate_1o_contato_min_uteis` | Tempo entre as duas, em minutos corridos e úteis |
| `aplica_sla` | Falso para lista fria (canal Outbound) |
| `sla_playbook_min` | 15 ou 120, conforme o horário de chegada |
| `dentro_sla_playbook` | Se o contato cumpriu o SLA. Nunca contatado conta como fora do SLA |

**Planilha**

| Coluna | Significado |
|---|---|
| `planilha_aba`, `planilha_linha` | Origem na planilha |
| `planilha_data_1o_contato`, `planilha_formato_data` | Data lida e o formato em que estava |
| `planilha_dif_dias_vs_crm` | Diferença em dias para a data de contato do CRM |
| `planilha_sdr` | SDR normalizado |
| `planilha_status_original`, `planilha_status` | Status digitado e categoria |
| `planilha_resultado_conflita_crm` | Se o resultado da planilha discorda do CRM |
| `planilha_obs`, `planilha_origem_original` | Texto livre de observação e origem digitada |

**Qualidade (`dq_*`):** uma flag por problema da seção 3, para que qualquer métrica possa ser recalculada com ou sem os registros afetados.
