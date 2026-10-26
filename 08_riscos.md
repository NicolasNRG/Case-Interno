# Entregável 8 · Três riscos do projeto

Escolhi os três riscos que, se acontecerem, **derrubam o projeto ou o resultado**, e que têm evidência nos dados. A probabilidade e o impacto são avaliações minhas, não medições.

| # | Risco | Probabilidade | Impacto | Dono |
|---|---|---|---|---|
| R1 | Medir errado e julgar o agente pelo número errado | Alta | Alto | **Renata Albuquerque** (sponsor) |
| R2 | O agente dizer o que o playbook proíbe ou descartar lead bom | Média | Alto | **Felipe Andrade** (dono do playbook) |
| R3 | Integrações e adoção não ficarem prontas no prazo de 60 dias | Alta | Médio | **Felipe Andrade**, com a TI da Vértice executando |

---

## R1 · Medir errado e julgar o agente pelo número errado

**O risco:** a diretora avalia o agente pelo painel atual ou espera ver venda em 60 dias. O agente pode estar funcionando e o projeto ser encerrado. O contrário também pode acontecer: um ganho que não existe ser comemorado.

**Por que é real:**
- **O painel mede outra coisa.** Mostra 29,7% como "conversão", mas mistura grupos de leads diferentes; a conversão de leads é 11,7% (entregável 3).
- **A fórmula do painel cai sozinha quando o agente funciona.** Com +30% de qualificados e a conversão real constante, ela iria de 30,1% para **24,2%** no primeiro mês (entregável 3, seção 5).
- **Venda não é detectável em 60 dias.** Mesmo com 50/50, provar +3 pontos leva cerca de 9 meses de leads, mais 60 dias de maturação (entregável 4).
- A Ficha registra a expectativa de ver o resultado "em 60 dias, no máximo".

**Sinais de alerta:**
- A "taxa de conversão" do Databox aparece em alguma reunião durante o piloto.
- Alguém pede "o ROI em receita" no dia 60.

**Mitigação:**

| Quando | O que fazer |
|---|---|
| **Antes** | • Registrar com a Renata, por escrito, **o que será lido no dia 60** (critérios e regra de decisão do entregável 4) e **o que não será** (venda, com a data em que poderá ser lida). <br>• **Trocar a definição no Databox antes do go-live** (entregável 3, seção 4). |
| **Durante** | • Relatório semanal do piloto só com as métricas oficiais, sempre com intervalo de confiança. <br>• Grupo de controle mantido depois do dia 60 (entregável 4, seção 2.1). |

**Dono:** Renata Albuquerque. É ela quem aprova o acordo de leitura; o líder do projeto executa.

---

## R2 · O agente dizer o que o playbook proíbe ou descartar lead bom

**O risco:** de um lado, o agente promete preço, prazo ou fala de concorrente e cria um compromisso comercial. Do outro, aplica o playbook ao pé da letra e descarta leads que virariam venda. Esse segundo erro é **invisível**: o lead descartado não volta.

**Por que é real:**
- **A prática atual já diverge do playbook.** 108 leads foram perdidos por "Sem orçamento", critério que o playbook proíbe. Há 29 observações de lead "comparando com Senseye".
- **A regra "menos de 20 funcionários elimina" teria descartado 13 vendas, somando R$ 167 mil** (entregável 2).
- **O campo de segmento do CRM não é confiável.** Há 555 deals perdidos por "Fora do segmento", mas 100% dos leads estão num segmento-alvo.
- **Há ambiguidade no próprio playbook.** 16% das primeiras mensagens perguntam "quanto custa **o sensor por máquina**?", e o playbook só dá a faixa **por linha** (R$ 8 mil a R$ 25 mil). O agente precisa de uma resposta decidida, não improvisada.

**Sinais de alerta:**
- A taxa de `guardrail_acionado` sobe.
- Os SDRs rejeitam mais de 10% das desqualificações.
- Algum lead reclama.

**Mitigação:**

| Quando | O que fazer |
|---|---|
| **Antes** | • Felipe **decide as ambiguidades**: preço por máquina ou por linha; manter ou não o "<20 elimina"; o que responder a "já temos sistema interno". <br>• Felipe rotula o conjunto de teste. <br>• Portão T1–T4 antes de qualquer contato real (entregável 4). |
| **Durante** | • As 6 camadas de proteção (entregável 5, seção 10). <br>• Revisão de **100% das desqualificações** no piloto. <br>• Revisão humana de ≥ 10% das conversas. <br>• Voltar à versão anterior do prompt em minutos (entregável 5, seção 9). |

**Dono:** Felipe Andrade, dono do playbook.

---

## R3 · Integrações e adoção não ficarem prontas no prazo de 60 dias

**O risco:** o cronograma tem 2 semanas de construção. Uma dependência externa travada (número do WhatsApp, API do Pipeway, aprovação de modelos de mensagem) come o piloto. E, mesmo com o agente no ar, os SDRs podem continuar no celular e na planilha, e então as métricas de adoção não medem nada.

**Por que é real:**
- **O WhatsApp hoje é o aplicativo** no número da empresa. O agente precisa da API oficial, e os SDRs, de uma caixa de entrada compartilhada (entregável 5, seção 11).
- **Fora da janela de 24h do WhatsApp, só vale mensagem com modelo aprovado pela Meta.** Os follow-ups dependem dessa aprovação. E "Sem resposta" é o principal motivo de perda (40% dos perdidos).
- **A API do Pipeway não foi testada:** busca por telefone, escrita de etapa, webhook de deal novo.
- **A planilha existe por um motivo:** "o CRM não mostra direito o que foi feito no dia" (Ficha). Se nada a substituir, o hábito continua.

**Sinais de alerta:**
- Na semana 1, ainda não há acesso à API do Pipeway, ou o número ainda está no aplicativo.
- SDRs respondendo pelo celular.
- Linhas novas na planilha para leads do agente (A5).

**Mitigação:**

| Quando | O que fazer |
|---|---|
| **Antes (semana 0)** | • **Lista de acessos fechada antes do kickoff:** credenciais de teste da API do Pipeway; conta na plataforma oficial do WhatsApp Business; decisão entre migrar o número ou usar um número dedicado ao piloto; projeto Google Cloud com região e termos aprovados. <br>• **Modelos de mensagem enviados à Meta no dia 1**, porque a aprovação leva dias. |
| **Plano B** | Começar o piloto pelo e-mail (cerca de 18% das conversas) ou com um número dedicado, sem depender da migração. |
| **Durante** | • A caixa compartilhada e o painel passam a mostrar "o que foi feito no dia", que é o motivo da planilha. <br>• 1 h de treinamento com os SDRs. <br>• Felipe acompanha A5 toda semana. |

**Dono:** Felipe Andrade, gestor dos SDRs e de quem depende a decisão sobre o número. A TI da Vértice executa as integrações; o responsável é a nomear no kickoff.

---

## Outros riscos acompanhados (fora dos três principais)

| Risco | Por que não está entre os três | Onde está tratado |
|---|---|---|
| Dado de contato sair do ambiente da Vértice (LGPD) | A arquitetura já elimina o caminho: modelo no projeto da Vértice, eventos sem dado pessoal | Entregável 5, seção 3, e entregável 4, seção 3 |
| Grupo de controle melhorar por ter menos carga | Subestima o efeito do agente: o viés é conservador | Entregável 4, seção 2 |
| "Máquina parou" fora do expediente sem ninguém para atender | Volume baixo, mas o impacto por caso é alto. É decisão de plantão da Vértice | Entregável 5, seção 11 |
| Custo ou latência do modelo | Estimados em US$ 100–200/mês e com folga sobre a meta de 2 min | Entregável 5, seção 3 |
