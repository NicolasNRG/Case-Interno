# Entregável 4 · Critérios de aceite e eventos

**Pergunta que este documento responde:** como vamos saber se o agente funcionou.

Os critérios estão em três blocos:
- **técnico:** o agente faz certo;
- **impacto:** o número da Vértice muda em relação ao baseline;
- **adoção:** o SDR usa o agente.

Cada métrica diz de quais eventos é calculada.

As linhas de base vêm do entregável 2 (`02_metricas_baseline.json`) e de `04_linhas_de_base_criterios.py` (`04_linhas_de_base.json`). As metas são **propostas**, para validar com Felipe (dono do playbook) e Renata (sponsor).

---

## 1. Resumo

| Bloco | O que decide o aceite no dia 60 | Meta principal |
|---|---|---|
| Técnico | O agente não diz o que o playbook proíbe, escala quando deve, qualifica certo, registra tudo e não perde lead quando algo falha | **Zero violações do playbook**; resposta em até 2 min (p95) |
| Impacto | Leads contatados dentro do SLA, leads sem contato, leads sem resposta. A qualificação não pode piorar | **SLA de 25,9% para ≥ 90%**; nunca contatados de 21,5% para ≤ 2% |
| Adoção | O SDR decide os handoffs, assume rápido, atende os escalonamentos e larga a planilha | **≥ 95% dos handoffs decididos** em até 1 dia útil |

A **conversão em venda** (11,7%) não é critério de aceite no dia 60: não é detectável nesse prazo (entregável 2, seção 6). Ela é acompanhada depois do dia 60, e o tempo para prová-la depende do desenho escolhido (seção 2.1).

---

## 2. Como o resultado é medido

**Cronograma dos 60 dias:**

| Semanas | Fase | O que se mede | Portão para seguir |
|---|---|---|---|
| 1–2 | Construção, conjunto de teste e **cronometragem das horas de SDR** (processo atual) | Critérios técnicos T1–T4 e T8 no conjunto de teste. Baseline B de horas | T1–T4 atingidos |
| 3 | **Modo assistido:** o agente propõe cada mensagem e o SDR aprova, edita ou rejeita antes do envio | Aceite sem edição; violações | ≥ 90% das mensagens aceitas sem edição (mínimo de 150) e 0 violações |
| 4–8 | **Piloto aleatorizado 50/50:** metade dos leads de entrada vai para o agente, metade segue o processo atual | Todos os critérios técnicos, de impacto e de adoção, em produção | Regra de decisão (seção 7) |
| Depois do dia 60 | Desenho escolhido pela sponsor (seção 2.1) | Qualificação (I4) e venda (I6) | — |

**Por que aleatorizar por lead, e não comparar antes e depois:**
- **O que acontece:** cada lead é sorteado no momento em que chega (evento `lead_recebido`, campo `grupo`), por uma regra fixa sobre o `lead_id`.
- **Por que não antes e depois:** o volume da Vértice cresce ao longo do ano (418 leads em janeiro, 501 em julho), e os SDRs mudam de comportamento quando sabem que estão sendo medidos. Só o sorteio isola o efeito do agente.
- **Por que 50/50:** é a divisão que dá mais poder estatístico com 245 leads por grupo em 5 semanas.

**Comparação com o baseline:** as métricas de impacto usam **as mesmas definições e o mesmo código** do entregável 2, reaplicados ao export do Pipeway. Os eventos só acrescentam o que o CRM não tem: o grupo do lead, o horário de origem e o autor de cada mensagem.

**O que dá para detectar em 5 semanas, com 245 leads por grupo:**

| Métrica | Baseline | Efeito esperado | Menor efeito detectável | Detectável no dia 60? |
|---|---|---|---|---|
| Contatados dentro do SLA | 25,9% | cerca de +64 p.p. (para ≥ 90%) | 11,8 p.p. | **Sim** |
| Nunca contatados | 21,5% | cerca de −20 p.p. | 9,5 p.p. | **Sim** |
| Qualificação em 7 dias | 39,2% | +6,4 p.p. (hipótese) | 12,6 p.p. | **Não para melhora. Sim para descartar piora grande** |
| Conversão em venda | 11,7% | — | 9,4 p.p., e ainda faltariam 60 dias de maturação | **Não** |

**De onde vem a hipótese de +6,4 p.p.:** 21,5% dos leads nunca são contatados hoje. 40% deles já foram descartados por segmento ou porte. Quem é contatado se qualifica em 49,8% dos casos. A conta é 21,5% × 60% × 49,8% = 6,4 p.p. Ela supõe que esses leads se qualificariam na mesma proporção dos que hoje são contatados.

**Limitação:** os SDRs do grupo de controle ficam com metade da carga e tendem a responder mais rápido. Isso **subestima** o efeito do agente. É um viés conservador, aceitável.

### 2.1 Depois do dia 60: quanto custa provar a venda

| Desenho | Provar +6,4 p.p. na qualificação | Provar +3 p.p. na venda | Custo |
|---|---|---|---|
| Manter 50/50 | ~4,4 meses de leads | ~9,4 meses de leads, mais 60 dias de maturação | Metade dos leads continua no processo que deixa 21,5% sem contato |
| 100% com 20% de controle | ~10,9 meses | ~23 meses | 20% dos leads sem o agente. **Serve como alarme de piora, não como prova de venda** |
| 100% sem controle | Não prova; só compara com a série histórica | Idem | Nenhum. A evidência é fraca: sem agente, a venda mensal já oscila de 10,1% a 13,6% |

**Recomendação: 100% com 20% de controle.**
- No dia 60, o ganho operacional (SLA, cobertura) já estará provado de forma causal.
- A relação entre velocidade e venda (entregável 2) dá suporte à hipótese de receita.
- Provar a venda de forma causal custaria manter metade dos leads no processo atual por mais 9 meses.

Se a diretora precisar de prova de receita (por exemplo, para ampliar o investimento), o desenho é manter o 50/50. **A escolha é da sponsor:** é uma troca entre prova e benefício, não uma questão técnica.

---

## 3. Eventos

### 3.1 Campos comuns a todo evento

Nenhum evento carrega nome, telefone ou e-mail. A Ficha proíbe que dados de contato saiam do ambiente da Vértice, então os eventos usam os mesmos pseudônimos do entregável 1.

| Campo | Exemplo | Para quê |
|---|---|---|
| `event_id` | uuid | Idempotência: um evento reenviado não conta duas vezes |
| `event_name` | `mensagem_enviada` | — |
| `ts_evento` | `2026-11-03T14:02:11-03:00` | Quando o evento aconteceu |
| `ts_origem` | horário do canal (WhatsApp, e-mail, Pipeway) | Mede a espera real, **inclusive fora do expediente**, que hoje é invisível |
| `lead_id`, `deal_id`, `conversa_id`, `execucao_id` | `L-01003`, `D-2026-01003` | Liga o evento ao Pipeway sem dado pessoal |
| `grupo` | `agente` / `controle` | Comparação do piloto |
| `canal` | `whatsapp` / `email` | — |
| `versao_agente`, `versao_prompt`, `modelo`, `versao_playbook` | `a1b2c3d`, `qualificacao@1.3.0`, id do modelo, `3.2` | Saber **qual versão gerou cada resposta** |
| `ambiente` | `producao` / `homologacao` | Não misturar teste com produção |

### 3.2 Os seis eventos mínimos

| Evento | Quando é emitido | Campos específicos | Usado em |
|---|---|---|---|
| `execucao_iniciada` | O agente começa a processar um gatilho | `gatilho` (lead_novo, mensagem_lead, follow_up, retomada_apos_erro), `ts_gatilho` | T5, T7 |
| `execucao_concluida` | O processamento termina | `resultado` (respondeu, escalou, aguardando_lead, encerrou, falhou), `duracao_ms`, `estado_qualificacao` (em_qualificacao, qualificado, desqualificado), `criterios` (porte, segmento, dor, prazo: pendente / atende / elimina), `tokens`, `custo` | T3, T7, I4 |
| `erro` | Qualquer falha | `tipo` (api_crm, api_whatsapp, api_email, modelo, timeout, validacao), `etapa`, `recuperavel`, `tentativa`, `resolvido_por` (retry, fila, escalonamento, nao_resolvido) | T7 |
| `escalonamento_humano` | O agente passa o lead ao SDR por um dos gatilhos da seção 5 do playbook | `motivo` (pede_humano, problema_em_andamento, mais_de_500, irritacao, fora_do_playbook, erro_tecnico), `sdr_destino`, `id_msg_gatilho`, `resumo_completo` (nome, empresa, respostas, motivo) | T2, T7, A4 |
| `acao_proposta` | O agente propõe algo que **depende de decisão humana** | `acao_id`, `tipo` (handoff_qualificado, desqualificar, enviar_mensagem [só no modo assistido], agendar_especialista), `para_sdr`, `resumo_completo` | T3, A1–A3, portão da fase assistida |
| `acao_aceita_rejeitada` | O SDR decide | `acao_id`, `decisao` (aceita, editada, rejeitada), `decidido_por`, `motivo_rejeicao` (lista fechada: nao_qualificado, ja_e_cliente, duplicado, dado_errado, outro), `latencia_min` | T3, A1–A3, portão da fase assistida |

### 3.3 Extensões propostas, e por que os seis não bastam

| Evento | Por que os seis não bastam | Campos específicos | Usado em |
|---|---|---|---|
| `lead_recebido` | O denominador não pode depender de o agente ter funcionado. Se só houver `execucao_iniciada`, um lead que o agente nunca processou **some da conta**, que é exatamente o problema dos 21,5% de hoje. É emitido pela camada de entrada, antes do agente | `ts_origem`, `grupo`, `aplica_sla` (falso para lista fria), `contato_repetido` (deal existente ou novo) | I1, I2, I4, T5, T6, A5 |
| `mensagem_recebida` | Para medir lead sem resposta e a latência de cada mensagem, não só da primeira execução | `ts_origem`, `n_mensagem_na_conversa` | I3, T2, T5 |
| `mensagem_enviada` | Os seis não registram que a mensagem **chegou** ao lead, nem **quem** enviou. O SLA vale para qualquer autor, inclusive o SDR do grupo de controle | `autor` (agente, sdr), `status_entrega` (enviada, entregue, lida, falhou), `primeira_ao_lead`, verificações (`n_frases`, `n_perguntas`, `tem_emoji`, `n_exclamacoes`, `violacao_detectada`) | I1–I3, T1, T4, T5, A3–A5 |
| `guardrail_acionado` | Registra a proteção funcionando: uma mensagem bloqueada ou reescrita antes do envio. **Não é violação.** Se a taxa subir, é sinal de que o prompt piorou | `regra` (preco_fechado, desconto, prazo, roi, concorrente, compatibilidade, dado_extra, orcamento, emoji_1o_contato), `resultado` (reescrita, bloqueada_e_escalada) | T1 (monitoramento) |
| `crm_atualizado` | "Registrar tudo no Pipeway" precisa de prova por escrita, com sucesso ou falha | `operacao` (criar_deal, usar_deal_existente, mudar_etapa, registrar_motivo, registrar_resumo), `sucesso`, `chave_idempotencia` | T6, T7 |
| `revisao_qa` | Tom e conformidade não são 100% verificáveis por regra automática. A revisão humana por amostra dá a medida B | `revisor`, notas de 1 a 5 (conformidade, tom, perguntas, escalonamento, resumo), `violacao` (sim/não e regra) | T1, T2, T4 |

**Resultado de negócio não é evento.** A etapa "Qualificação" e o status *won* vêm do Pipeway, lidos pela mesma regra do entregável 1, para os dois grupos.

### 3.4 Exemplo

```json
{
  "event_id": "5f1c...", "event_name": "mensagem_enviada",
  "ts_evento": "2026-11-03T21:40:07-03:00", "ts_origem": "2026-11-03T21:39:58-03:00",
  "lead_id": "L-04512", "deal_id": "D-2026-04512", "conversa_id": "C-88213", "execucao_id": "X-1931",
  "grupo": "agente", "canal": "whatsapp", "autor": "agente", "primeira_ao_lead": true,
  "status_entrega": "entregue", "n_frases": 3, "n_perguntas": 1, "tem_emoji": false,
  "n_exclamacoes": 0, "violacao_detectada": false,
  "versao_agente": "a1b2c3d", "versao_prompt": "qualificacao@1.3.0",
  "modelo": "<id do modelo>", "versao_playbook": "3.2", "ambiente": "producao"
}
```

---

## 4. Critérios técnicos: o agente faz certo

**Conjunto de teste** (portão das semanas 1–2):
- **Tamanho:** pelo menos 200 casos, rotulados pelo dono do playbook.
- **Mensagens comuns:** as 7 intenções reais do log (preço, orçamento, região, ligação, agendamento, já tem solução, como funciona), com variações.
- **Escalonamento:** pelo menos 10 casos para cada um dos 5 gatilhos.
- **Armadilhas:** pelo menos 40 pedidos do que o playbook proíbe (preço fechado, desconto, prazo, "e a Senseye?", "funciona com a minha prensa X?", "qual o orçamento ideal?").
- **Conversas completas:** diálogos de qualificação de ponta a ponta.

| ID | Critério | Meta | Como medir | Eventos | Quando |
|---|---|---|---|---|---|
| T1 | **Não diz nada que o playbook proíbe:** preço fechado, desconto, condição de pagamento, prazo de instalação ou de retorno, concorrente (fora a frase padrão), compatibilidade sem especialista, pedido de dados além de nome/empresa/cargo/telefone/e-mail, pergunta de orçamento | **0 violações** no conjunto de teste e **0 violações confirmadas** em produção | Verificação automática em 100% das mensagens, mais revisão humana de ≥ 10% das conversas (mínimo de 30 por semana). Violações = `revisao_qa.violacao` + `mensagem_enviada.violacao_detectada` | `mensagem_enviada`, `revisao_qa`, `guardrail_acionado` (alerta) | Teste e produção |
| T2 | **Escala quando deve** (os 5 gatilhos do §5 do playbook) | No teste: acerto ≥ 95% por gatilho e ≤ 10% de escalonamentos indevidos. Em produção: p95 ≤ 2 min do gatilho ao escalonamento; ≥ 95% corretos na revisão | Tempo de `mensagem_recebida` (gatilho) até `escalonamento_humano`; motivo conferido em `revisao_qa` | `mensagem_recebida`, `escalonamento_humano`, `revisao_qa` | Teste e produção |
| T3 | **Qualifica certo** pelos 4 critérios | No teste: concordância ≥ 90% com o rótulo (estado e motivo). **Nenhuma desqualificação por porte sem o número informado pelo lead** (a faixa do CRM não basta). Em produção: ≥ 90% das desqualificações confirmadas pelo SDR, que revisa 100% delas durante o piloto | `execucao_concluida.estado_qualificacao` comparado ao rótulo; `acao_proposta(desqualificar)` seguido de `acao_aceita_rejeitada` | `execucao_concluida`, `acao_proposta`, `acao_aceita_rejeitada` | Teste e produção |
| T4 | **Escreve como o playbook pede:** 1 ou 2 perguntas por mensagem, 2 ou 3 frases, sem emoji no primeiro contato, sem excesso de exclamação | ≥ 98% das mensagens com ≤ 3 frases, ≤ 2 perguntas e ≤ 1 exclamação. 100% sem emoji na primeira mensagem. Nota de tom ≥ 4/5 na revisão | Campos de verificação de `mensagem_enviada` e notas de `revisao_qa` | `mensagem_enviada`, `revisao_qa` | Teste e produção |
| T5 | **Responde em minutos, 24/7** | p95 ≤ 2 min corridos entre a chegada (ou a mensagem do lead) e a resposta do agente. Hoje: p95 de 201 min úteis | `mensagem_enviada(autor=agente).ts_evento` − `lead_recebido.ts_origem` ou `mensagem_recebida.ts_origem` | `lead_recebido`, `mensagem_recebida`, `mensagem_enviada` | Produção |
| T6 | **Registra tudo no Pipeway, sem duplicar** | 100% dos leads do grupo agente com etapa e motivo ou resumo atualizados no mesmo dia. **0 deals duplicados criados** (hoje: 5,4% dos deals) | `crm_atualizado(sucesso)` por lead e dia. Conferência diária do export do Pipeway pela regra de duplicidade do entregável 1 | `crm_atualizado`, `lead_recebido.contato_repetido` | Produção |
| T7 | **Falha sem perder lead** | Erro em ≤ 2% das execuções. 100% das execuções com erro terminam em nova tentativa bem-sucedida ou em escalonamento. **0 leads sem contato por falha técnica.** 0 mensagens duplicadas ao lead | Execuções com `erro` × `resolvido_por`. Lead perdido = `lead_recebido` sem `mensagem_enviada` nem `escalonamento_humano` em 15 min | `execucao_iniciada`, `execucao_concluida`, `erro`, `escalonamento_humano`, `mensagem_enviada` | Produção |
| T8 | **Rastreável e sem dado pessoal** | 100% das `mensagem_enviada` com `versao_prompt`, `modelo` e `versao_agente`. 0 ocorrências de telefone, e-mail ou nome nos eventos | Campos preenchidos. Varredura diária com expressões regulares no repositório de eventos | Todos (campos comuns) | Teste e produção |

---

## 5. Critérios de impacto: o que muda no número da Vértice

Grupo agente contra grupo de controle, no mesmo período, com as definições do entregável 2.

| ID | Métrica | Baseline (classe) | Meta no dia 60 | Fórmula | Eventos |
|---|---|---|---|---|---|
| I1 | **Leads de entrada contatados dentro do SLA** do playbook | **25,9%** (Q3, A). Mediana de 27 min úteis até o 1º contato | **≥ 90%** no grupo agente, com diferença sobre o controle maior que o intervalo de confiança. Mediana ≤ 2 min | Leads cuja 1ª `mensagem_enviada` (qualquer autor) − `lead_recebido.ts_origem` ≤ SLA, em minutos úteis ÷ `lead_recebido` com `aplica_sla` | `lead_recebido`, `mensagem_enviada` |
| I2 | **Leads nunca contatados** | **21,5%** (Q3, A) | **≤ 2%** | `lead_recebido` sem `mensagem_enviada` em 7 dias ÷ `lead_recebido` | `lead_recebido`, `mensagem_enviada` |
| I3 | **Leads que escreveram e ficaram sem resposta** | **10,3%** (Q3, A) | **≤ 1%** | Leads com `mensagem_recebida` sem `mensagem_enviada` posterior ÷ `lead_recebido` | `mensagem_recebida`, `mensagem_enviada`, `lead_recebido` |
| I4 | **Qualificação em até 7 dias da entrada** (indicador antecipado da venda) | **39,2%** (Jan–Set, A; estável entre 37,7% e 40,9%) | **Não piorar:** diferença observada ≥ 0 e limite inferior do IC95 acima de −9 p.p. Hipótese de **+6,4 p.p.**, que só pode ser confirmada depois do dia 60 (seção 2.1) | Etapa "Qualificação" do Pipeway em até 7 dias de `lead_recebido.ts_origem`, por grupo. Conferido com `execucao_concluida(estado=qualificado)` no grupo agente | `lead_recebido`, `execucao_concluida` + Pipeway |
| I5 | **Horas de SDR em primeiro contato e qualificação** | **260 h/mês (D).** Vira **B** com a cronometragem das semanas 1–2 | −50% das horas por lead de entrada no grupo agente, contra o controle. A meta é hipótese, a calibrar com o B | Cronometragem B repetida nas semanas 7–8, por grupo. Triangulação com `mensagem_enviada(autor=sdr)` por lead | `mensagem_enviada`, `escalonamento_humano`, `acao_proposta` + cronometragem |
| I6 | **Conversão de leads (por grupo de entrada, 60 dias)**. Acompanhamento, **não é critério do dia 60** | **11,7%** (Jan–Jul, A) | Leitura em M+3 por grupo de entrada. Provar +3 p.p. leva de 9 a 23 meses, conforme o desenho (seção 2.1). Até lá, comparação com a faixa histórica (10,1% a 13,6% ao mês) | Definição oficial do entregável 3, por grupo | `lead_recebido` + Pipeway |

**Leads que chegam fora do expediente** (agora visíveis pelo `ts_origem`) entram nas metas do grupo agente. Na comparação com o baseline, eles aparecem **separados**, porque hoje não existe linha de base para eles.

---

## 6. Critérios de adoção: o SDR está usando

| ID | Critério | Meta | Fórmula | Eventos |
|---|---|---|---|---|
| A1 | **Handoffs decididos:** o SDR olha o que o agente passa | ≥ 95% dos handoffs de qualificados com aceite ou rejeição em até 1 dia útil | `acao_aceita_rejeitada` em até 1 dia útil ÷ `acao_proposta(handoff_qualificado)` | `acao_proposta`, `acao_aceita_rejeitada` |
| A2 | **Handoffs aceitos:** o SDR confia no que recebe | ≥ 80% aceitos. 100% das rejeições com motivo, revisados toda semana | `decisao=aceita` ÷ handoffs decididos | `acao_proposta`, `acao_aceita_rejeitada` |
| A3 | **O SDR assume rápido** | Mediana ≤ 2 h úteis entre o aceite e a 1ª mensagem do SDR ao lead | `mensagem_enviada(autor=sdr).ts` − `acao_aceita_rejeitada.ts` | `acao_aceita_rejeitada`, `mensagem_enviada` |
| A4 | **Escalonamentos atendidos:** o SLA do playbook vale também para o humano | ≥ 95% dos escalonamentos com mensagem do SDR ao lead em até 15 min úteis | `mensagem_enviada(autor=sdr).ts` − `escalonamento_humano.ts` | `escalonamento_humano`, `mensagem_enviada` |
| A5 | **Sem atalho e sem planilha paralela** | ≤ 5% dos leads do grupo agente com a 1ª mensagem enviada por um SDR antes do agente. **0 linhas novas na planilha de controle** para leads do grupo agente a partir da semana 5 | Ordem de autoria das `mensagem_enviada` por lead. Contagem semanal das linhas novas da planilha (fonte C) | `lead_recebido`, `mensagem_enviada` + planilha |

---

## 7. Regra de decisão no dia 60

| Decisão | Condição |
|---|---|
| **Ampliar para 100%**, com o desenho de controle escolhido (seção 2.1) | T1–T8 atingidos. I1, I2 e I3 atingidos. I4 sem piora. A1–A4 atingidos |
| **Mais 4 semanas de piloto,** com ajustes | Técnico e impacto atingidos, mas adoção abaixo da meta. Ou I4 inconclusivo com estimativa negativa |
| **Parar e corrigir** | Qualquer violação confirmada de T1 que se repita após correção, lead perdido por falha técnica (T7) ou I4 com piora fora do intervalo |

---

## 8. Decisões tomadas (e por quê)

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Separar critério de aceite de métrica de acompanhamento** | A venda não é detectável em 60 dias: mesmo com 50/50, provar +3 p.p. leva cerca de 9 meses de leads, mais 60 dias de maturação. Prometer conversão em venda no dia 60 seria prometer um número que não existe. O aceite usa o que se mede no prazo: velocidade, cobertura, ausência de piora na qualificação |
| D2 | **Piloto aleatorizado 50/50 por lead,** em vez de comparar antes e depois | O volume cresce ao longo do ano e o comportamento dos SDRs muda. Só o sorteio separa o efeito do agente. O 50/50 maximiza o poder com o volume disponível |
| D3 | **Mesmas definições e mesmo código do baseline** para o impacto | Comparar uma métrica nova com um baseline calculado de outro jeito seria repetir o erro do painel (entregável 3) |
| D4 | **Qualificação como "não piorar",** não como meta de alta | Com 245 leads por grupo, só se detecta diferença acima de 12,6 p.p., e o efeito esperado é de 6,4. O que dá para provar no prazo é que o agente não piora a qualificação, inclusive por aplicar o playbook com mais rigor que os SDRs |
| D5 | **Seis extensões aos eventos mínimos** | Cada uma fecha uma lacuna nomeada na seção 3.3. A principal é o `lead_recebido`: sem ele, o lead que o agente nunca processou some do denominador |
| D6 | **"Ação proposta / aceita" só onde há decisão humana:** handoff, desqualificação no piloto e mensagens na semana assistida | Colocar aprovação humana em toda mensagem anularia a velocidade, que é o principal ganho. A semana assistida mede a confiança antes de liberar a autonomia |
| D7 | **Revisar 100% das desqualificações durante o piloto** | Desqualificação errada é invisível: o lead não volta. O dado mostra o risco: 13 vendas (R$ 167 mil) vieram de empresas que a regra "<20 elimina" descartaria, e o campo de segmento do CRM não é confiável |
| D8 | **Zero tolerância só em T1** | Preço fechado, prazo ou crítica a concorrente geram compromisso comercial e risco à marca. No resto, metas de 90% a 98% evitam travar o projeto por ruído de medição |
| D9 | **Verificação automática (A) mais revisão humana por amostra (B)** | A regra automática pega formato e termos proibidos em 100% das mensagens. Tom e julgamento de escalonamento exigem leitura humana |
| D10 | **Cronometrar as horas nas semanas 1–2, antes do agente** | Sem um baseline B, a meta de horas (I5) compararia uma medição com um "achismo" (classe D). É o momento certo: os SDRs ainda estão no processo atual |
| D11 | **Eventos sem dado pessoal,** com os mesmos pseudônimos do entregável 1 | É restrição da Ficha. O `lead_id` liga ao Pipeway dentro do ambiente da Vértice |
| D12 | **Leads fora do expediente separados** na comparação com o baseline | Hoje eles não têm linha de base (entregável 2, limitação 1). Misturá-los inflaria ou esconderia o efeito |
| D13 | **Deixar com a sponsor a escolha do desenho depois do dia 60,** com uma recomendação | O tempo para provar a venda vai de 9 a 23 meses conforme o tamanho do controle. Quanto mais prova, mais leads ficam sem o agente. Essa troca entre prova e benefício é de negócio, não técnica |
