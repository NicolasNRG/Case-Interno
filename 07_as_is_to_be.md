# Entregável 7 · AS-IS e TO-BE

**Pergunta que este documento responde:** quem faz o quê hoje, em que sistema e quanto tempo leva cada etapa. E onde o agente entra.

- Os tempos e volumes vêm de `07_tempos_por_etapa.py`, aplicado à tabela do entregável 1. Ao rodar, o script grava os valores em `07_tempos_por_etapa.json`; rode antes o `01_etl.py`.
- As classes de fonte (A, B, C, D) são as mesmas do entregável 2.

---

## 1. AS-IS: como funciona hoje

```
 Lead chega ──> SDR registra ──> SDR faz o ──> SDR qualifica ──> SDR agenda ──> Especialista ──> Vendas
 (anúncio,      no Pipeway E     1º contato    (porte, segmento,  o especialista  envia a        fecha
  orgânico,     na planilha      (WhatsApp,    dor, prazo)                        proposta
  indicação,    do Drive         e-mail,
  evento, lista)                 telefone)
```

| # | Etapa | Quem executa | Sistema | Tempo decorrido (A) | Volume no Q3 (por mês) e passagem | O que os dados mostram |
|---|---|---|---|---|---|---|
| 1 | **Entrada do lead** | Canais de marketing. O deal fica com um dos 4 SDRs | Formulários e anúncios → **Pipeway** | — | **481 leads únicos/mês** (A), mais ~11 que só existem na planilha (C) | 5,4% dos deals são duplicados. 46% das entradas caem entre 8h e 9h e 35% na segunda: quem chega à noite ou no fim de semana só é registrado no expediente seguinte |
| 2 | **Primeiro contato** | SDR | **WhatsApp Business (aplicativo)** no número da empresa, e-mail e telefone | **Mediana de 27 min úteis**, p90 de 135 min | 377 contatados/mês. **77,6%** dos leads recebem contato | Só **26%** dos leads de entrada são contatados dentro do SLA de 15 min, e **21,5% nunca recebem contato**. Por SDR, o SLA vai de 3,4% (Diego) a 61,5% (Ana Paula) |
| 3 | **Registro** | SDR | **Pipeway + planilha no Drive** (registro duplo) | 98,3% das linhas da planilha têm a mesma data do CRM (C) | 383 linhas/mês na planilha (C) | A planilha discorda do CRM no resultado em 18% dos leads. 32 leads do Q3 existem só nela, 12 deles "qualificados" |
| 4 | **Qualificação** (as 6 perguntas do playbook) | SDR | WhatsApp, e-mail e telefone (**sem registro**) | **Mediana de 2,9 dias** do contato à qualificação (p90 de 4,9) | 188 qualificados/mês. **49,8%** dos contatados se qualificam | No log, a Vértice manda **1,8 mensagens por lead contatado**, pouco para 6 perguntas. Parte relevante da qualificação provavelmente acontece por telefone, que não deixa rastro (inferência). 108 leads perdidos por "Sem orçamento", critério que o playbook proíbe |
| 5 | **Agendamento e proposta** | O SDR agenda; o especialista técnico conversa e envia a proposta | Agenda (não está nos materiais) → Pipeway (etapa Proposta) | **Mediana de 8 dias** da qualificação à proposta (p90 de 14) | 111 propostas/mês. **56,6%** dos qualificados recebem proposta | O CRM registra o SDR como autor **de todas as etapas**: não há rastro de quem fez a proposta |
| 6 | **Fechamento** | Time de vendas | Pipeway | **Mediana de 21 dias** da proposta à venda (p90 de 37). Ciclo total: **mediana de 32 dias** | **53,3%** das propostas viram venda | Ticket mediano de R$ 14,2 mil |
| 7 | **Acompanhamento** | Gerente (Felipe) e diretora (Renata) | Painel do Databox + planilha | — | — | A "taxa de conversão" do painel mede outra coisa (entregável 3) |

**Tempo de trabalho por etapa: não existe em nenhuma fonte (D).**
- O único número é o declarado: **60 h/semana** para as etapas 2 a 4 juntas, sem apontamento.
- Os tempos acima são **decorridos**: o intervalo entre dois registros, não o esforço gasto.
- Dividir o esforço por etapa exige a cronometragem prevista para as semanas 1–2 do piloto (entregável 4, I5), anotando por atividade: primeiro contato, follow-up, ligação, registro no CRM, registro na planilha.

### Onde se perde o lead

A cada 100 leads que entram (grupos de Jan–Jul):

```
 100 entram ──> 78 contatados ──> 39 qualificados ──> 22 propostas ──> 12 vendas
          -22              -39                -17               -10
```

**As etapas 1 a 4 perdem 61 de cada 100 leads.** Elas ocupam os primeiros ~3 dias de um ciclo de ~32. É exatamente onde o agente atua.

---

## 2. TO-BE: onde o agente entra

```
 Lead chega ─> AGENTE: 1º contato em minutos, 24/7 ─> AGENTE qualifica ─┬─ qualificado ───> SDR aceita o handoff ─> agenda o especialista ─> Proposta ─> Vendas
               (registro automático no Pipeway)      (o código aplica  ├─ gatilho §5 ────> SDR assume a conversa
                                                      as regras)        └─ desqualificado ─> SDR confirma (no piloto)
```

| # | Etapa | Quem executa | Sistema | O que muda | Meta (entregável 4) |
|---|---|---|---|---|---|
| 1 | **Entrada** | Ingestão automática | API oficial do WhatsApp Business, e-mail, webhook do Pipeway | O horário de origem passa a ser registrado, inclusive à noite e no fim de semana. Contato repetido usa o deal que já existe | 0 deals duplicados (T6) |
| 2 | **Primeiro contato** | **Agente** | API do WhatsApp e e-mail | Em minutos, 24/7, no tom do playbook | p95 ≤ 2 min (T5). SLA ≥ 90% (I1). Nunca contatados ≤ 2% (I2) |
| 3 | **Registro** | **Agente**, automático | Pipeway, via fila com nova tentativa | **A planilha deixa de existir** para os leads do agente | 100% registrados no mesmo dia (T6). 0 linhas novas na planilha (A5) |
| 4 | **Qualificação** | **O agente conversa; o código aplica as regras do playbook** | — | 1 ou 2 perguntas por mensagem. Critérios em campos estruturados, com o porte em número | Qualificação em 7 dias não piora (I4) |
| 4a | **Escalonamento** (5 gatilhos do §5) | O agente detecta; **o SDR assume** | Caixa de entrada compartilhada | ~14% dos leads pedem ligação e ~14% têm mais de 500 funcionários: vão direto ao SDR, com resumo | ≥ 95% atendidos em até 15 min úteis (A4) |
| 4b | **Desqualificação** | O agente propõe; **o SDR confirma** (no piloto) | Caixa de entrada | Proteção contra descartar lead bom | ≥ 90% confirmadas (T3) |
| 5 | **Handoff e agendamento** | **O SDR** aceita o lead qualificado e agenda o especialista. O agente já ofereceu a conversa de 20 min, como o playbook permite | Caixa de entrada + agenda | O SDR recebe só quem vale a pena, com as respostas prontas | ≥ 95% decididos em 1 dia útil (A1). O SDR assume em ≤ 2 h úteis (A3) |
| 6 | **Proposta e fechamento** | Especialista e vendas | Pipeway | Sem mudança | Conversão de leads acompanhada (I6) |
| 7 | **Acompanhamento** | Gerente e diretora | Painel corrigido (entregável 3) + eventos | "Quantos entraram, quantos foram qualificados, quantos viraram negócio", **sem planilha paralela** (item 5 da Ficha) | — |

---

## 3. O que muda para cada pessoa

| Quem | Deixa de fazer | Passa a fazer |
|---|---|---|
| **SDRs** | Primeiro contato e digitação dupla nos leads do agente | Atender escalonamentos e pedidos de ligação; decidir handoffs; agendar o especialista; revisar desqualificações durante o piloto. O tempo liberado é o que a meta de horas mede (I5) |
| **Felipe** | Depender da planilha paralela para ver "o que foi feito no dia", o motivo que a Ficha dá para ela existir | Ser dono das regras (configuração) e do conjunto de teste; aprovar as versões do prompt; acompanhar a adoção |
| **Renata** | Ler uma "conversão" que mede outra coisa | Ler o painel com a definição oficial; decidir o desenho depois do dia 60 (entregável 4) |
| **Especialista e vendas** | — | Receber leads com o resumo das respostas |

---

## 4. Limitações

1. **Tempo de trabalho por etapa é D.** Só existe o total declarado de 60 h/semana.
2. **Quem faz a proposta e o fechamento** vem da Ficha. O CRM registra o SDR dono como autor de todas as etapas.
3. **Ligações não aparecem em nenhuma fonte.** A conclusão de que parte da qualificação é feita por telefone é uma inferência a partir de 1,8 mensagens por lead.
4. **A agenda do especialista não está nos materiais.** O tempo da qualificação até a proposta (8 dias) mistura a espera pela agenda com o trabalho do especialista.
