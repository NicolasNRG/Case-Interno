# Entregável 3 · Reconciliação do dashboard

**O painel diz 29,7%. A base diz 11,7%.** Este documento explica por que os dois números divergem, qual deles está certo e qual passa a ser a definição oficial da métrica.

Todos os números saem de `03_reconciliacao.py`, que lê o próprio export do painel e o export bruto do Pipeway. O resultado fica registrado em `03_reconciliacao.json`.

## Resposta curta

- **Por que divergem.** Os dois números respondem perguntas diferentes, e o do painel ainda mistura dois grupos de leads.
  - O painel divide as **vendas fechadas no Q3** pelos **qualificados que entraram no Q3**. 36% dessas vendas vêm de leads que entraram antes do Q3, e 58% desses qualificados ainda não tiveram tempo de fechar.
  - Na prática, a fórmula do painel aproxima a **conversão de qualificados** (30,1%, medida corretamente). Não é a conversão de leads.
- **Qual está certo.** Nenhum dos dois serve sem dizer a pergunta. A conta do painel está certa, mas o rótulo "taxa de conversão" está errado e a regra é instável. Para a pergunta "de cada lead que entra, quantos viram venda", o número certo é **11,7%** (leads de Jan–Jul, que já tiveram 60 dias para fechar).
- **Definição oficial:** **conversão de leads por grupo de entrada, com janela de 60 dias** (seção 4). A conversão de qualificados (30,1%) continua existindo, como métrica secundária e com nome próprio.

---

## 1. O que o painel calcula de verdade

Antes de discutir qual número está certo, reproduzi o painel a partir do mesmo export bruto que o conector do Databox lê.

| Indicador | Painel | Reproduzido? | Regra que reproduz | Problema |
|---|---|---|---|---|
| Leads qualificados (Q3) | 565 (191 · 194 · 180) | **Sim, total e mês a mês** | Deals que passaram pela etapa "Qualificação", contados pelo **mês de entrada** | **A regra escrita no painel não gera o número.** "`qualified_flag = true`, criados no período" dá **591** (198 · 201 · 192) |
| Negócios ganhos (Q3) | 168 (56 · 61 · 51) | **Total sim**; por mês, diferença de até 2 | `status = won` com `updated_at` no Q3 | `updated_at` muda a cada edição do deal, então uma venda pode "migrar" de mês. Pela data do ganho dá 57 · 60 · 51 |
| Taxa de conversão (Q3) | 29,7% | **Sim** | 168 ÷ 565 | Numerador e denominador são grupos diferentes (seção 2) |
| Ticket médio (Q3) | R$ 28.906,55 | **Sim** | Média do valor dos 168 ganhos | **Um único deal de R$ 2,29 mi dobra a média.** Mediana R$ 13.650; média sem esse deal R$ 15.367 |
| Total de deals criados (Q3) | 1.521 | **Sim** | `created_at` válido no Q3 (1.507), mais os de data ilegível com entrada no Q3 (14) | Inclui **85 deals duplicados**. Perde **7 deals** com ano digitado como 2024. São 1.443 leads únicos |
| Tempo médio de resposta | 50,8 min | **Não** | Nenhuma regra testada chega a 50,8. Nos mesmos deals, a média da entrada ao contato é de 118,6 min corridos e a mediana de 28 min | A média **ignora os 359 deals do período que nunca foram contatados** |

**Conclusão da reprodução:** a taxa do painel é aritmeticamente fiel ao CRM. A divergência com a base não é erro de conta. É **definição**.

---

## 2. Por que divergem: a ponte de 29,7% a 11,7%

| Passo | Taxa | O que mudou |
|---|---|---|
| 1. Painel: vendas fechadas no Q3 ÷ qualificados que entraram no Q3 | **29,7%** | — |
| 2. Mesmo denominador, mas só as vendas **desses mesmos** 565 qualificados | 19,1% | O grupo fica coerente. Desses 565, 108 viraram venda e 325 seguem abertos: o Q3 ainda não teve tempo de fechar |
| 3. Qualificados que **já tiveram 60 dias** (entrada em Jan–Jul) | **30,1%** | Conversão de qualificados medida corretamente. É o que o painel aproxima |
| 4. Denominador = **todos os leads únicos** (entrada em Jan–Jul) | **11,7%** | Conversão de leads: a definição oficial |

**Causa 1: a fórmula mistura dois grupos.** O numerador é "o que fechou no trimestre", e 60 dos 168 ganhos (36%) vêm de leads que entraram antes do Q3. O denominador é "quem se qualificou no trimestre", e 325 dos 565 ainda estão em aberto.

Quando o fluxo é estável, os dois erros se compensam e o número cai perto do certo. Foi o que aconteceu no Q3: 29,7% contra 30,1%. Mas é coincidência, não método. Aplicada mês a mês, a mesma fórmula oscila muito mais do que a realidade:

| Mês | Fórmula do painel | Conversão de qualificados (correta) | Conversão de leads (oficial) |
|---|---|---|---|
| Fev | 18,2% | 24,9% | 10,2% |
| Mar | 31,4% | 29,1% | 11,4% |
| Abr | 30,1% | 27,3% | 10,1% |
| Mai | **20,4%** | 29,3% | 11,6% |
| Jun | **37,5%** | 35,2% | 13,6% |
| Jul | 29,8% | 33,5% | 12,8% |
| Ago | 30,9% | (em maturação) | (em maturação) |
| Set | 28,3% | (em maturação) | (em maturação) |

Janeiro fica de fora: o export não traz os leads de dezembro, que geram as vendas de janeiro (a fórmula dá 1,9%).

**Causa 2: o denominador começa no lugar errado para este projeto.** A fórmula só olha quem já foi qualificado. Mas a maior perda do funil acontece antes disso: **61% dos leads nunca se qualificam e 22% nunca são contatados.** É exatamente onde o agente vai atuar. Uma taxa que começa no qualificado é cega para o efeito do agente.

**Causa 3: dados sujos.** Na taxa, esse efeito é pequeno. Pela regra escrita no painel, que conta os duplicados, a taxa seria 168 ÷ 591 = 28,4%. Os dados sujos pesam muito mais no ticket (um erro de digitação dobra a média) e na contagem de deals (85 duplicados).

---

## 3. Qual está certo

| | Painel (29,7%) | Base (11,7%) |
|---|---|---|
| A conta | Certa: reproduz exatamente | Certa |
| O que mede | Vendas do trimestre ÷ qualificados do trimestre | De cada lead que entra, quantos viram venda em até 60 dias |
| Problema | O rótulo diz "taxa de conversão", mas mede outra coisa. Mistura grupos. Oscila de 18% a 37,5% sem que a realidade mude. Cai sozinha quando o volume sobe (seção 5) | É um piso: 15,5% dos leads de Jan–Jul seguem "abertos" e parados no CRM. Só pode ser lida 60 dias depois do mês |
| **Veredito** | **Errado como "taxa de conversão".** Serve, no máximo, como aproximação da conversão de qualificados quando o fluxo é estável | **Certo para a pergunta do projeto.** Passa a ser a definição oficial |

---

## 4. Definição oficial

| Campo | Definição |
|---|---|
| **Nome** | Conversão de leads (por grupo de entrada, 60 dias) |
| **Pergunta que responde** | De cada 100 leads que entram num mês, quantos viram venda? |
| **Fórmula** | Leads únicos que entraram no mês M e viraram venda em até 60 dias da entrada ÷ leads únicos que entraram no mês M |
| **Lead único** | Mesmo telefone ou e-mail = mesmo lead (playbook, seção 6). Duplicados contam uma vez só |
| **Data de entrada** | A primeira etapa "Entrada" do histórico. Não usar `created_at` (52 deals com data inválida) |
| **Venda** | `status = won`. A data da venda é a etapa "Fechamento". `updated_at` só entra se essa etapa faltar |
| **Janela de 60 dias** | Fixa, para que meses antigos e recentes sejam comparáveis. O maior ciclo observado é de 59 dias |
| **Quando ler** | O grupo do mês M fecha no dia 1º do mês M+3 (julho fecha em 1º de outubro). Antes disso, o painel o mostra como "em maturação" |
| **Escopo** | Todos os canais. Recortes por canal são opcionais |
| **Fonte** | Pipeway (A), pela tabela do entregável 1 |
| **Baseline** | **11,7%** (Jan–Jul; IC95 10,6%–12,8%). Por mês, de 10,1% a 13,6% |

**Métricas que acompanham a oficial:**
- **Conversão de qualificados:** mesma regra, com o denominador formado pelos leads que passaram pela etapa "Qualificação" (não pela `qualified_flag`, que os duplicados herdaram). **Baseline: 30,1%.** É o "30%" que a diretora conhece, agora com o nome certo.
- **Indicador antecipado:** como a oficial só pode ser lida em M+3, os 60 dias do projeto precisam de um indicador que se leia antes (qualificação na primeira semana). Fica definido no entregável 4.

**O que muda no Databox:**
1. A "taxa de conversão" atual sai e entra a métrica oficial, com os meses em maturação marcados.
2. A `qualified_flag` dá lugar à etapa "Qualificação" do histórico.
3. `updated_at` dá lugar à data da etapa "Fechamento".
4. A contagem passa a ser por lead único.
5. O ticket passa a mostrar a mediana, e a média só depois de corrigir os 4 valores com erro na origem.
6. O "tempo médio de resposta" dá lugar à mediana do tempo até o primeiro contato e ao percentual dentro do SLA, contando também quem nunca foi contatado (entregável 2).

---

## 5. Por que trocar o painel *antes* de ligar o agente

Se o agente aumentar o número de qualificados, a fórmula atual vai mostrar **queda** de conversão, mesmo que a conversão real não mude. O denominador sobe na hora; as vendas só chegam um ou dois meses depois. Dos ganhos observados, 14% fecham no mesmo mês da entrada, 64% no mês seguinte e 22% dois meses depois.

Cálculo ilustrativo (não é dado observado): +30% de qualificados a partir do mês M, com a conversão real constante em 30,1%.

| Mês | Fórmula do painel mostraria |
|---|---|
| M | **24,2%** |
| M+1 | 28,6% |
| M+2 | 30,1% |

Em plena janela de 60 dias da diretora, o painel diria que **o agente piorou a conversão em 6 pontos**. O efeito inverso também vale: uma queda de volume "melhora" a taxa.

---

## 6. Decisões tomadas (e por quê)

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Reproduzir o painel a partir do export bruto**, não da base limpa | Só assim dá para separar "diferença de definição" de "diferença de dado". Se eu partisse da base limpa, misturaria as duas coisas |
| D2 | **Exigir reprodução mês a mês, não só do total** | Um total pode bater por coincidência; a série mensal confirma a regra. Os qualificados bateram nos três meses. Os ganhos bateram no total, mas não por mês, e isso está declarado |
| D3 | **Tratar o rótulo do painel como hipótese, não como verdade** | O rótulo descreve uma regra que dá 591; a regra real dá 565. O painel documenta uma coisa e calcula outra. Sem testar, eu teria explicado a diferença pela regra errada |
| D4 | **Decompor a diferença em passos (ponte)** | Cada parte da diferença ganha uma causa com nome. Fica claro que a maior parte é definição, e não sujeira de dado |
| D5 | **Oficial = conversão de leads, não de qualificados** | (a) É a pergunta da Ficha: "quantos leads entraram, quantos foram qualificados e quantos viraram negócio". (b) É onde o agente atua: antes da qualificação. (c) Não se distorce quando o volume muda |
| D6 | **Janela fixa de 60 dias e leitura em M+3** | A janela fixa torna os meses comparáveis. 60 dias cobre todos os ganhos observados. O custo é a leitura atrasada, compensado por um indicador antecipado (entregável 4) |
| D7 | **Manter a conversão de qualificados (30,1%) com nome próprio** | O número que a diretora conhece continua existindo, com o nome certo. Evita a leitura de que "a conversão caiu de 30% para 12%": o que mudou foi a pergunta, não a operação |
| D8 | **Rotular como ilustrativo o cálculo da seção 5** | Não é dado observado: é a fórmula do painel aplicada a um cenário hipotético, usando a defasagem real das vendas. Serve para mostrar o risco, não para prever |
| D9 | **Não "consertar" ticket nem duplicados só no painel** | Os erros estão na origem: valores digitados errado e deals duplicados. A correção certa é no Pipeway, e o agente precisa evitar criar novos duplicados (critério técnico, entregável 4) |

---

## 7. As duas frases para a diretora

> **"Os 30% do painel são a conversão de quem já foi qualificado, calculada misturando vendas e leads de períodos diferentes; de cada 100 leads que entram na Vértice, 12 viram venda, e é esse número que o agente precisa mover."**
>
> **"A partir de agora, a conversão oficial é a dos leads de cada mês que viram venda em até 60 dias, e vamos corrigir o painel antes de ligar o agente, porque do jeito que está ele mostraria a conversão caindo justamente quando o agente começar a qualificar mais leads."**
