# Entregável 2 · Documento de Baseline

**Pergunta que este documento responde:** qual é a situação de hoje, com número e fonte.

Todos os números saem de `02_calculos_baseline.py`, aplicado à tabela do entregável 1, e ficam registrados em `02_metricas_baseline.json`. Nenhum foi digitado à mão.

**Classes de fonte:**
- **A**: extraído de sistema (Pipeway CRM e log do WhatsApp e do e-mail);
- **B**: amostra medida;
- **C**: estimativa do executor com base em registro. Uso C para tudo que depende da planilha dos SDRs: ela é um registro manual, editável, sem trilha de alteração, e diverge do CRM em 18% dos leads;
- **D**: estimativa sem base.

---

## 1. Resumo

| Métrica da Ficha | Ficha (classe) | Baseline (classe) | Leitura |
|---|---|---|---|
| Leads por mês | ~480 (A) | **481 leads únicos/mês no Q3** (A) e 456 de média Jan–Set (A) | O 480 da Ficha conta **deals**, com 5,4% de duplicados. Coincide com o Q3, mas por acaso |
| Taxa de conversão | ~30% (A) | **11,7%** de lead até ganho (A) e 30,1% de qualificado até ganho (A) | Os 30% valem para qualificado até ganho. De lead até ganho, a conversão é cerca de 1/3 disso. O painel mistura grupos (entregável 3) |
| Tempo de resposta | ~15 min (D) | **Mediana de 27 min úteis.** Só **26%** dos leads são contatados dentro do SLA de 15 min (A) | E **21% nunca são contatados** |
| Horas de SDR/semana | ~60h (D) | **60h (D), mantido** | Nenhuma fonte mede tempo. O volume registrado não sustenta nem derruba o número |
| Ticket médio | R$ 14 mil (D) | **Média de R$ 15,6 mil** e mediana de R$ 14,2 mil (A) | A Ficha está próxima. O painel mostra R$ 28,9 mil por causa de erros de digitação |
| Ciclo até fechamento | ~45 dias (D) | **Mediana de 32 dias**, p75 de 42 (A) | O ciclo é mais curto do que se acredita |
| **Custo mensal do processo** | — | **260 h/mês (D)**, equivalente a 37,5% da capacidade dos 4 SDRs | Premissas na seção 4 |

**O que mais pesa para o projeto:**
- **A dor existe, mas não é a que a Ficha descreve.** O problema não é "responder em 15 min e às vezes atrasar". É que **1 em cada 5 leads de entrada nunca recebe contato** e **3 em cada 4 ficam fora do SLA do playbook**.
- **A velocidade anda junto com o resultado.** Leads contatados em até 15 min viram venda em 18,5% dos casos; acima de 4h úteis, em 6,9% (seção 5).

---

## 2. Decisões de método (e por quê)

| # | Decisão | Por quê |
|---|---|---|
| D1 | **A unidade é o lead único (pessoa), não o deal.** Deals com o mesmo telefone ou e-mail são um lead | É a regra do playbook (seção 6). Contar deals infla volume e denominador em 5,4% |
| D2 | **A conversão oficial é de lead até ganho, por grupo de entrada.** Numerador e denominador são o mesmo grupo de leads, contado pelo mês de entrada | O agente atua no topo do funil. Uma taxa que começa no lead qualificado não enxerga o que ele muda |
| D3 | **Janela de maturação de 60 dias.** Para métricas de resultado, só entram os grupos de **Jan–Jul** | Nenhum dos 412 ganhos levou mais de 59 dias. Agosto e setembro ainda estão abertos: 65% e 99,6% dos leads seguem sem desfecho |
| D4 | **Métricas operacionais usam o Q3** e mostram Jan–Set ao lado | O Q3 é o período mais recente e o único com as três fontes. A série mensal é estável (mediana de 22 a 29 min, SLA de 25% a 29%), então o Q3 representa bem o ano |
| D5 | **Tempo de resposta = da chegada do lead ao primeiro contato da Vértice, em minutos úteis.** Reporto **mediana e percentual dentro do SLA**, nunca a média | A média (95 min) é puxada por poucos casos de dias; a mediana (27) representa o lead típico. O SLA é o que o playbook promete |
| D6 | **O SLA é medido sobre todos os leads de entrada**, e quem nunca foi contatado conta como fora do SLA | Medir só os contatados esconde o pior caso. Ficam fora: listas frias (canal Outbound, onde a Vértice aborda e não responde) e leads com menos de 7 dias no export (99% dos contatos acontecem em até 2,7 dias) |
| D7 | **Ticket oficial = média sem os 4 outliers.** A mediana fica como referência | Para projetar receita (leads × conversão × ticket), o estimador certo é a média. Os outliers têm entre R$ 630 mil e R$ 2,29 mi, contra uma faixa de R$ 8 mil a R$ 25 mil por linha no playbook |
| D8 | **As horas de SDR continuam D.** Mostro um teste de consistência e o caminho para chegar a B | O enunciado proíbe melhorar a classe sem base. Volume de mensagens é A, mas "minutos por mensagem" seria eu inventando |
| D9 | **As taxas trazem intervalo de confiança de 95% (Wilson).** | Para saber, já no baseline, que mudança será detectável em 60 dias (seção 6) |

**Uma correção feita no caminho.** A primeira versão media o tempo de resposta como "da 1ª mensagem do lead à 1ª resposta", usando só o log. O resultado foi um paradoxo: leads respondidos depois de 4h convertiam mais (22%) do que os respondidos em 15 min (17%).

A causa é o método. Quando a Vértice inicia a conversa, a "primeira resposta" medida desse jeito é um follow-up dias depois. E quanto mais o lead avança no funil, mais follow-ups ele recebe. Troquei pela definição D5, que junta CRM e log: da chegada (a entrada no CRM ou a 1ª mensagem do lead, o que vier antes) ao primeiro contato (a etapa Contato ou a 1ª mensagem da Vértice, o que vier antes). Nos 4.100 leads, o log nunca mostra contato antes da etapa Contato do CRM. Isso **valida o horário do CRM como o primeiro contato real**.

---

## 3. Métricas da Ficha

### 3.1 Leads por mês

| Campo | Conteúdo |
|---|---|
| **Valor** | **481 leads únicos por mês no Q3.** Média Jan–Set: 455,6/mês. A série mensal vai de 404 a 501 e é crescente (jan 418, jul 501). Além disso, há **~11 leads por mês que só existem na planilha** (32 no Q3, 12 deles marcados como "qualificado") |
| **Fonte** | **A** para o CRM; **C** para os leads só da planilha |
| **Método** | Leads únicos, depois da deduplicação por telefone ou e-mail, contados pelo mês da primeira entrada no CRM |
| **Ficha** | "~480, média Jan–Set". Reproduzido exatamente: 4.332 deals ÷ 9 = 481,3. É a contagem de **deals**, não de leads, e 232 deles (5,4%) são duplicados que o playbook proíbe criar |

O sponsor também diz que "entra 500 por mês" (D). Só julho chegou lá (501).

### 3.2 Taxa de conversão

| Campo | Conteúdo |
|---|---|
| **Valor oficial** | **11,7% de lead até ganho** (368 de 3.158; IC95 10,6–12,8%), grupos de entrada Jan–Jul. Por mês, varia de 10,1% a 13,6% |
| **Etapas do funil** | Lead até contato: 77,6%. Lead até qualificado: **38,7%**. Qualificado até proposta: 56,6%. Proposta até ganho: 53,3%. **Qualificado até ganho: 30,1%** (IC95 27,6–32,8%) |
| **Fonte** | **A** |
| **Método** | Ganho = status *won* em qualquer deal do lead. Qualificado = passou pela etapa "Qualificação" no histórico; a `qualified_flag` não é usada porque foi herdada pelos duplicados (entregável 1) |
| **Ficha** | "~30%" vem do painel: ganhos fechados no Q3 ÷ qualificados que entraram no Q3. Bate por acaso com a taxa de qualificado até ganho, mas mistura dois grupos de leads diferentes (entregável 3) |
| **Limitação** | 15,5% dos leads de Jan–Jul (489) continuam "abertos" no CRM depois de 60 dias ou mais. Como nenhum ganho levou mais de 59 dias, eles são tratados como não convertidos. A taxa, portanto, é um **piso** |

### 3.3 Tempo de resposta ao lead

| Campo | Conteúdo |
|---|---|
| **Valor oficial (Q3)** | **Mediana de 27 min úteis** até o primeiro contato (p75 63, p90 135; média 95). **25,9% dos leads de entrada são contatados dentro do SLA** de 15 min |
| **Jan–Set** | Mediana de 25 min úteis; 26,7% dentro do SLA; 21,9% nunca contatados; 11,2% escreveram e ficaram sem resposta |
| **O resto do quadro (Q3)** | **21,5% nunca foram contatados** e **10,3% escreveram e ficaram sem resposta.** Entre os que foram contatados, só 33% receberam contato em até 15 min |
| **Fonte** | **A.** Horário do CRM validado pelo horário do log de mensagens |
| **Método** | Ver D5 e D6. Minutos úteis = seg–sex, 8h–18h, conforme o playbook |
| **Ficha** | "~15 min. A meta é 15 e a gente cumpre" (D). **Não se sustenta:** 3 em cada 4 leads ficam fora da meta |
| **Por SDR (Jan–Set)** | Ana Paula: mediana de 9 min, 61,5% no SLA. Carla: 19 min, 30,1%. Bruno: 37 min, 12,6%. Diego: 77,5 min, 3,4%. Confirma a dor do "cada um responde de um jeito" |
| **Limitação** | **É um limite inferior.** Nenhuma das 4.100 chegadas aparece fora do expediente, mas 46% delas caem entre 8h e 9h e 35% na segunda-feira. Quem chega à noite ou no fim de semana só é registrado na manhã seguinte, então a espera real fora do horário não é medida. Por isso a regra do playbook "fora do expediente, até 2h após a abertura" nunca é acionada nos dados |

### 3.4 Horas de SDR por semana em primeiro contato e qualificação

| Campo | Conteúdo |
|---|---|
| **Valor** | **60 h/semana** (15h × 4 SDRs) |
| **Fonte** | **D, mantido.** Nenhum sistema registra tempo de trabalho |
| **Método** | O número declarado pelo comercial. O teste de consistência está na seção 4 |

### 3.5 Ticket médio

| Campo | Conteúdo |
|---|---|
| **Valor oficial** | **Média de R$ 15.552** sobre 408 ganhos Jan–Set. Mediana de R$ 14.150; metade dos ganhos fica entre R$ 10.300 e R$ 19.050 |
| **Fonte** | **A.** Campo `estimated_value` do CRM |
| **Método** | Ficam de fora 4 ganhos com valor entre R$ 630 mil e R$ 2,29 mi. Todos são múltiplos de R$ 10 mil e estão separados do resto por um vazio (o maior valor normal é R$ 60,1 mil). É compatível com digitação ×100, mas não corrigi: só excluí. Com eles, a média seria R$ 29.940 |
| **Ficha** | "R$ 14 mil" (D) bate com a mediana. O painel mostra R$ 28.906,55 porque inclui um único deal de R$ 2,29 mi |
| **Limitação** | É **valor estimado** no CRM, não faturado. Não recebemos fonte de faturamento |

### 3.6 Ciclo médio até fechamento

| Campo | Conteúdo |
|---|---|
| **Valor oficial** | **Mediana de 32 dias** (média 32,3; p25 23; p75 42; p90 49; máximo 59) |
| **Fonte** | **A** |
| **Método** | Da primeira entrada à etapa "Fechamento" dos 412 ganhos. Em 12 ganhos sem essa etapa, uso `updated_at` |
| **Ficha** | "Uns 45 dias" (D). Só 1 em cada 4 ganhos leva mais de 42 dias |

---

## 4. Custo mensal do processo atual em horas

| Item | Valor | Classe | Premissa |
|---|---|---|---|
| **Horas por mês em primeiro contato e qualificação** | **260 h/mês** | D | 60 h/semana declaradas × 4,33 semanas/mês (52 ÷ 12) |
| Em proporção da equipe | 37,5% da capacidade dos 4 SDRs | D | Jornada de 40 h/semana por SDR. A jornada contratual não foi informada |
| Por lead que entra | 34 min | D | 260 h ÷ 456 leads únicos/mês |
| Em reais | **não calculado** | — | Os materiais não trazem salário nem custo do SDR. Não estimei para não inventar |

**Teste de consistência.** Os volumes são A; o resultado continua D. Por mês, os SDRs enviam **638 mensagens** e contatam **355 leads**. Se as 60 h/semana forem verdade, cada mensagem consome **24 min**, ou **44 min por lead contatado**.

As mensagens do log são curtas e seguem 5 modelos, então escrever não explica esse tempo. Se o número estiver certo, o resto está em trabalho que **não aparece em nenhuma fonte**:
- **ligações:** cerca de 56 leads por mês pedem ligação já na primeira mensagem, e nenhuma ligação é registrada;
- **pesquisa sobre o lead;**
- **digitação dupla, no CRM e na planilha:** cerca de 383 linhas por mês na planilha.

Se não estiver, 60h é um exagero. Os dados não permitem decidir.

**Sensibilidade, para usar quando houver medição:**

| Cada minuto gasto por… | equivale a |
|---|---|
| mensagem enviada | 10,6 h/mês |
| lead contatado | 5,9 h/mês |
| linha da planilha | 6,4 h/mês |

**Como chegar à classe B (recomendado antes do go-live):**
- **O que fazer:** cronometrar uma amostra. Durante 1 semana, os 4 SDRs anotam o tempo por atividade (primeiro contato, follow-up, ligação, registro no CRM, registro na planilha). Alternativa: acompanhar cerca de 30 leads por SDR do início ao fim.
- **Por que antes do go-live:** sem isso, o critério de impacto em horas do entregável 4 não terá contra o que comparar.

---

## 5. Métricas que faltavam na Ficha

| Métrica | Valor | Classe | Método | Por que importa |
|---|---|---|---|---|
| Leads de entrada **contatados dentro do SLA** | **25,9%** (Q3) | A | D5 e D6 | É o que o agente muda primeiro. Detectável em semanas |
| Leads de entrada **nunca contatados** | **21,5%** (Q3) | A | Sem etapa Contato e sem mensagem da Vértice | É a "perda por demora" no seu extremo: conversão de 0% |
| Leads que **escreveram e ficaram sem resposta** | **10,3%** (Q3) | A | Mensagem do lead sem nenhuma mensagem da Vértice depois | Lead ativo e ignorado |
| **Ganho por velocidade de contato** (Jan–Jul) | ≤15 min: **18,5%** · 15–60 min: 15,1% · 1–4h: 12,8% · >4h: **6,9%** · nunca: 0% | A | Lead até ganho por faixa de tempo até o 1º contato | Sustenta a hipótese do sponsor. **É correlação, não causa:** o padrão se mantém dentro de 3 dos 4 SDRs, mas leads mais promissores podem ser atendidos antes |
| Tempo até a qualificação | Mediana de 2,9 dias (p90 5) | A | Da entrada à etapa Qualificação | A qualificação acontece em menos de uma semana. É mensurável dentro dos 60 dias |
| Variação entre SDRs | SLA de 3,4% (Diego) a 61,5% (Ana Paula) | A | Seção 3.3 | Padronização é um ganho tão grande quanto velocidade |
| Principal motivo de perda | **"Sem resposta": 974 leads (40% dos perdidos)** | A | `motivo_perda` no nível do lead | O lead some. O follow-up do agente ataca isso |
| Leads com porte que obriga escalar (>500 func.) | 13,7% (562 leads, ~62/mês) | A | Faixas 501-1000 e 1000+ | Volume que o agente **deve** passar ao SDR. São as faixas que mais convertem (15–16%) |
| Leads com porte indefinido (faixa 11-50) | 21,1% (865) | A | A faixa cruza os limites de 20 e 50 do playbook | O agente precisa perguntar o número exato |
| Deals duplicados | 5,4% dos deals (232) | A | Seção 2 do entregável 1 | O playbook proíbe. O agente precisa reconhecer contato repetido |
| Leads fora do CRM | 32 no Q3 (2,2%), 12 deles qualificados | C | Planilha sem par no CRM | Demanda invisível para o painel |
| Planilha divergente do CRM | 18% (201 de 1.117) | C | Resultado da planilha diferente do CRM | Mostra que a planilha não serve como fonte de resultado |
| Leads "abertos" esquecidos | 15,5% dos leads de Jan–Jul | A | `status = open` com 60 dias ou mais | Higiene de registro. O playbook pede atualizar a etapa no mesmo dia |
| Conformidade com o playbook | 108 leads perdidos por "Sem orçamento"; 13 vendas (R$ 167 mil) para empresas de 1 a 10 funcionários | A | `motivo_perda` e `porte_faixa` | Orçamento não é critério no playbook. E a regra "<20 elimina", aplicada à risca pelo agente, teria descartado 3% das vendas. **Decisão para o sponsor antes de construir** |
| Intenção da 1ª mensagem do lead | Preço 16% · agendamento 15% · orçamento 15% · região 14% · pede ligação 14% · já tem solução 14% · como funciona 13% | A | Classificação por palavra-chave do texto do log | Mostra o que o agente vai receber. Vira o conjunto de teste do entregável 4 |

---

## 6. O que dá para ver em 60 dias

A diretora quer resultado "em 60 dias, no máximo". Com cerca de 425 leads de entrada por mês, e para detectar a diferença com 95% de confiança e 80% de poder:

| Mudança a detectar | Leads por grupo | Meses de leads para encher **um** grupo | Com piloto 50/50 (dois grupos) |
|---|---|---|---|
| SLA: de 26% para 36% (+10 p.p.) | 334 | menos de 1 mês | **~1,6 mês** |
| Lead até qualificado: de 38,7% para 43,7% (+5 p.p.) | 1.520 | ~3,6 meses | ~7 meses |
| Lead até ganho: de 11,7% para 14,7% (+3 p.p.) | 1.991 | ~4,7 meses | ~9,4 meses, **mais 60 dias** de maturação |
| Lead até ganho: +2 p.p. | 4.336 | ~10 meses | ~20 meses |

A comparação pede dois grupos (agente e controle), por isso o tempo real é o da última coluna. Correção feita durante o entregável 4: a versão anterior desta tabela mostrava só a coluna de um grupo.

**Implicação para o entregável 4:** em 60 dias dá para provar velocidade, cobertura (ninguém sem contato) e qualidade do registro. **Conversão em venda não dá:** ela entra como métrica de acompanhamento, com uma data honesta de leitura.

---

## 7. Limitações declaradas

1. **Espera fora do expediente invisível** (seção 3.3). O tempo de resposta é um limite inferior. É preciso confirmar com a Vértice se o WhatsApp Business guarda o horário original de recebimento.
2. **Feriados não descontados** dos minutos úteis.
3. **Horas e custo continuam D.** Não há como melhorar sem uma medição (seção 4).
4. **Ticket sobre valor estimado,** não faturado.
5. **Conversão é um piso,** por causa dos 15,5% de leads abertos e parados.
6. **Ligações telefônicas não aparecem em nenhuma fonte.** Só 26 dos 3.199 leads contatados no CRM não têm nenhuma mensagem da Vértice no log, o que sugere que contato só por telefone é raro. O horário desse contato, porém, depende de o SDR mover a etapa no CRM.
7. **Velocidade × ganho é correlação.** A prova causal fica para o piloto (entregável 4), comparando leads atendidos pelo agente com leads atendidos só por humanos no mesmo período.

**Reprodução:** `python 02_calculos_baseline.py --tabela 01_tabela_analitica.csv --saida 02_metricas_baseline.json`
