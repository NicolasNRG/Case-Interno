# Entregável 9 · Protótipo de 16 horas

## A pergunta que ele responde para a diretora

> **"Dá para confiar o primeiro contato da Vértice a um agente? Ele segue o playbook, sem prometer preço nem prazo, escala quando deve e qualifica como o seu melhor SDR?"**

**Por que esta pergunta, e não "o agente aumenta as vendas?":**
- **É a premissa mais arriscada do projeto (R2).** Se o agente não for confiável, nada mais importa: integração, piloto e painel seriam investimento perdido.
- **É a única que 16 horas conseguem responder.** "Muda o número da Vértice?" exige o piloto de 60 dias com grupo de controle (entregável 4). Venda exige meses.
- **Responde antes do custo grande.** As integrações (WhatsApp, Pipeway, Google Cloud) são o que consome as 2 primeiras semanas do plano. O protótipo decide se vale começá-las.

---

## O que é (e o que não é)

**É uma simulação do núcleo do agente**, igual ao desenho do entregável 5:
- prompt com o playbook;
- saída estruturada;
- regras de qualificação e de escalonamento em código;
- verificador antes do envio.

Esse núcleo roda contra um **conjunto de teste montado a partir dos dados reais** e contra **leads simulados**.

**Não é um produto:**
- não tem WhatsApp, Pipeway nem infraestrutura;
- **não usa nenhum dado de contato real**: só perfis sintéticos e a tabela pseudonimizada. Por isso pode rodar na API da Anthropic sem ferir a restrição da Ficha. A produção vai para o Vertex AI, no projeto da Vértice (entregável 5).

**Modelo:** o mesmo da produção (Claude Opus 5.5), para que o resultado valha para o piloto.

---

## O conjunto de teste: cerca de 150 casos, montados a partir dos dados

| Bloco | Casos | Origem |
|---|---|---|
| **Primeiras mensagens reais** | 70 | As 7 intenções do log (preço "por máquina", orçamento para 4 linhas, "atendem em Minas?", "me liga depois das 14h", "recebi o material", "já temos sistema interno", "como funciona"), com 10 variações cada |
| **Armadilhas** | 40 | Preço fechado, desconto, prazo de instalação, retorno do investimento, "e a Senseye?", "funciona com a minha prensa X?", pedido de dados além do permitido, pergunta de orçamento, tentativa de manipulação ("ignore suas regras") |
| **Escalonamentos** | 25 | Os 5 gatilhos do §5 do playbook, 5 casos de cada |
| **Conversas completas com lead simulado** | 15 | Perfis sorteados da distribuição real do CRM (porte, segmento, dor, prazo), **forçando os casos de borda**: faixa 11–50, 1–10, mais de 500, segmento fora do alvo, "só pesquisando" |

**Rótulos:** Felipe marca a resposta esperada de cada caso (estado do lead, motivo, escalar ou não). São cerca de 2 h dele, fora das 16 h.

**Separação para não "decorar a prova":** 30% dos casos ficam guardados e não são usados no ajuste do prompt.

---

## Plano das 16 horas

| Bloco | Horas | Entrega |
|---|---|---|
| 1. Conjunto de teste | 3 | 150 casos em arquivo, prontos para o rótulo |
| 2. Núcleo do agente | 4 | Prompt v0 com o playbook v3.2, esquema de saída, regras do §2 e gatilhos do §5 em código |
| 3. Verificador | 2 | Regras fixas sobre o que é proibido + verificador com modelo |
| 4. Simulador de lead | 2 | Um "lead" que responde a partir de um perfil, para as 15 conversas completas |
| 5. Rodar, pontuar e ajustar uma vez | 3 | Placar T1–T4 nos casos de ajuste e nos 30% guardados |
| 6. Material para a diretora | 2 | 1 página de resultado + 10 conversas para ler, no formato do WhatsApp |
| **Total** | **16** | |

---

## O que ele mede

Os limites são os mesmos do portão das semanas 1–2 do entregável 4.

| Medida | Limite para "passou" |
|---|---|
| T1 · Violações do que o playbook proíbe | **0** |
| T2 · Escalonamento correto, por gatilho | ≥ 95% |
| T3 · Qualificação igual ao rótulo do Felipe | ≥ 90%, e nenhuma desqualificação por porte sem o número informado |
| T4 · Forma das mensagens (frases, perguntas, emoji) | ≥ 98% |
| Mensagens até qualificar, nas conversas completas | Reportado (sem limite) |
| Latência e custo por turno | Reportados (sem limite). Estimativa: menos de US$ 50 para rodar tudo |

---

## O que ele **não** responde (limitações declaradas)

1. **Se a venda aumenta.** Isso é o piloto e o grupo de controle (entregável 4).
2. **Se os SDRs vão usar.** A adoção só aparece em produção.
3. **Se as integrações funcionam no prazo.** Isso é o R3.
4. **Como o agente se sai com mensagens reais variadas.** O log só tem 7 modelos de mensagem de entrada. As variações do conjunto de teste ajudam, mas leads reais escrevem de formas que o teste não cobre. **O protótipo pode superestimar o desempenho.** Por isso a semana assistida do plano (o SDR aprova cada mensagem antes do envio) continua necessária.

---

## Como a diretora decide com o resultado

| Resultado | Decisão |
|---|---|
| **Passou nos quatro limites,** inclusive nos 30% guardados | Começar o plano de 60 dias, com as integrações |
| **Falhou por ambiguidade do playbook** (ex.: preço "por máquina") | Felipe decide a regra e o protótipo roda de novo. O custo é de horas, não de semanas |
| **Falhou em conformidade mesmo com as camadas de proteção** | Não seguir para um piloto com autonomia. Avaliar um modo assistido permanente, em que o agente rascunha e o SDR envia |

**Subproduto útil mesmo se der errado:** a lista de lacunas do playbook encontradas no caminho, que melhora o trabalho dos SDRs com ou sem agente.
