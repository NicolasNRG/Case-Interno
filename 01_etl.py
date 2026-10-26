"""
Entregável 1 · ETL da tabela analítica de leads (Vértice Soluções Industriais)

Junta as três fontes de dados em uma tabela com UM LEAD POR LINHA:
  - crm_export_pipeway_2026-10-01.json  (sistema de registro: funil e resultado)
  - conversas_whatsapp_email_2026.csv    (mensagens: tempo real de resposta)
  - controle_sdr_jul-set_2026.xlsx       (planilha paralela dos SDRs, jul-set)

Uso:
    python 01_etl.py --input <pasta_com_os_materiais> --output <pasta_de_saida>

Saídas:
    <output>/01_tabela_analitica.csv / .xlsx        pseudonimizada (sem nome, telefone, e-mail)
    <output>/01_contagens_etl.json                  registros por etapa (o que entrou, o que saiu)
    <output-local>/01_tabela_analitica_com_contatos.xlsx   versão com contatos (NÃO versionar)

Dependências: Python 3.10+, pandas, openpyxl. Todas as decisões estão em 01_nota_decisoes.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import openpyxl
import pandas as pd

# ---------------------------------------------------------------------------
# Parâmetros e dicionários de normalização
# ---------------------------------------------------------------------------

TZ = timezone(timedelta(hours=-3))  # todas as fontes estão em horário de Brasília
EXPORT_CRM = datetime(2026, 10, 1, 6, 0, tzinfo=TZ)
Q3_INICIO, Q3_FIM = datetime(2026, 7, 1, tzinfo=TZ), datetime(2026, 10, 1, tzinfo=TZ)

# Expediente do playbook (seção 1): seg-sex, 8h às 18h. Feriados não são considerados.
EXPEDIENTE_INICIO, EXPEDIENTE_FIM = 8, 18
SLA_NO_EXPEDIENTE_MIN = 15    # resposta em até 15 min no horário comercial
SLA_FORA_EXPEDIENTE_MIN = 120  # até 2h após o início do próximo expediente

# Valores de deal acima disto são tratados como erro de digitação (ver nota, seção 3).
LIMITE_VALOR_OUTLIER = 100_000

ETAPAS = ["Entrada", "Contato", "Qualificação", "Proposta", "Fechamento"]

SEGMENTOS = {
    "metalurgia": "Metalurgia", "metalurgica": "Metalurgia",
    "alimentos e bebidas": "Alimentos e Bebidas", "alimentos": "Alimentos e Bebidas",
    "alimentos & bebidas": "Alimentos e Bebidas",
    "papel e celulose": "Papel e Celulose", "celulose": "Papel e Celulose",
    "papel/celulose": "Papel e Celulose",
    "quimica": "Química", "quimico": "Química",
    "automotivo": "Automotivo", "autopecas": "Automotivo",
    "textil": "Têxtil",
    "mineracao": "Mineração",
}

# Faixa de funcionários do CRM -> o que o playbook (seção 2 e 5) permite concluir.
PORTE_PLAYBOOK = {
    "1-10": "elimina (<20)",
    "11-50": "indefinido (faixa cruza 20 e 50)",
    "51-200": "qualifica (>=50)",
    "201-500": "qualifica (>=50)",
    "501-1000": "escala p/ humano (>500)",
    "1000+": "escala p/ humano (>500)",
}

SDRS = {
    "ana": "Ana Paula Mendes", "bruno": "Bruno Takahashi",
    "carla": "Carla Nogueira", "c.": "Carla Nogueira", "diego": "Diego Fontoura",
}

STATUS_PLANILHA = {
    "retornar": "em_contato", "aguardando retorno": "em_contato",
    "em contato": "em_contato", "tentei 2x": "em_contato",
    "qualificado": "qualificado", "qualificado ✔": "qualificado", "qualif.": "qualificado",
    "proposta": "proposta", "proposta enviada": "proposta",
    "fechado": "ganho", "ganho": "ganho",
    "perdido": "perdido", "sem interesse": "perdido",
    "sem orçamento": "perdido_sem_orcamento",
    "fora do segmento": "desqualificado_segmento", "porte pequeno": "desqualificado_porte",
}
RESULTADO_STATUS_PLANILHA = {
    "ganho": "won", "perdido": "lost", "perdido_sem_orcamento": "lost",
    "desqualificado_segmento": "lost", "desqualificado_porte": "lost",
}  # demais categorias = "open"

ORIGEM_PLANILHA = {
    "face/insta": "Paid Social", "anúncio insta": "Paid Social", "meta": "Paid Social",
    "instagram": "Paid Social", "google": "Paid Search", "google ads": "Paid Search",
    "adwords": "Paid Search", "blog": "Organic", "orgânico": "Organic", "site": "Organic",
    "indicação": "Referral", "parceiro": "Referral", "webinar": "Event", "feira": "Event",
    "evento": "Event", "lista": "Outbound", "outbound": "Outbound", "prospecção": "Outbound",
    "whatsapp direto": "Direto (fora do CRM)", "ligou": "Direto (fora do CRM)",
}

# Mensagens de entrada do log: palavra-chave -> intenção.
INTENCOES = [
    ("quanto custa", "preco"),
    ("orçamento", "pedido_orcamento"),
    ("me liga", "pede_ligacao"),
    ("atendem em", "cobertura_regiao"),
    ("recebi o material", "agendamento"),
    ("sistema interno", "ja_tem_solucao"),
    ("como funciona", "como_funciona"),
]

COLUNAS_CONTATO = ["contato_nome", "telefone", "email"]  # removidas na versão pseudonimizada


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower().strip()


def normaliza_telefone(valor) -> str:
    """Seis formatos nas fontes -> 11 dígitos (DDD + número), sem o 55."""
    digitos = re.sub(r"\D", "", str(valor or ""))
    if digitos.startswith("55") and len(digitos) == 13:
        digitos = digitos[2:]
    return digitos


def normaliza_email(valor) -> str:
    return str(valor or "").strip().lower()


def normaliza_codigo(valor) -> str | None:
    """'VS-02818', 'VS 02818' e 'vs-02818' -> 'VS-02818'."""
    m = re.search(r"(\d{5})", str(valor or ""))
    return f"VS-{m.group(1)}" if m else None


def normaliza_sdr(valor) -> str | None:
    if not valor:
        return None
    return SDRS.get(str(valor).strip().lower().split()[0])


def parse_iso(valor: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)


def em_expediente(dt: datetime) -> bool:
    return dt.weekday() < 5 and EXPEDIENTE_INICIO <= dt.hour < EXPEDIENTE_FIM


def minutos_uteis(inicio: datetime, fim: datetime) -> float:
    """Minutos entre dois instantes contando só seg-sex, 8h-18h."""
    if fim <= inicio:
        return 0.0
    total, dia = 0.0, inicio.date()
    while dia <= fim.date():
        if dia.weekday() < 5:
            abre = datetime.combine(dia, time(EXPEDIENTE_INICIO), tzinfo=TZ)
            fecha = datetime.combine(dia, time(EXPEDIENTE_FIM), tzinfo=TZ)
            trecho = (min(fecha, fim) - max(abre, inicio)).total_seconds() / 60
            total += max(trecho, 0)
        dia += timedelta(days=1)
    return total


def minutos(inicio: datetime | None, fim: datetime | None) -> float | None:
    if inicio is None or fim is None:
        return None
    return round((fim - inicio).total_seconds() / 60, 1)


def classifica_intencao(mensagem: str) -> str:
    texto = mensagem.lower()
    for chave, intencao in INTENCOES:
        if chave in texto:
            return intencao
    return "outra"


class UniaoBusca:
    """Agrupa deals que compartilham telefone OU e-mail (fecho transitivo)."""

    def __init__(self):
        self.pai: dict[str, str] = {}

    def acha(self, x: str) -> str:
        self.pai.setdefault(x, x)
        while self.pai[x] != x:
            self.pai[x] = self.pai[self.pai[x]]
            x = self.pai[x]
        return x

    def une(self, a: str, b: str) -> None:
        self.pai[self.acha(a)] = self.acha(b)


# ---------------------------------------------------------------------------
# 1. CRM: um registro por deal, já limpo
# ---------------------------------------------------------------------------

def carrega_crm(caminho: Path, cont: dict) -> list[dict]:
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    deals = bruto["deals"]
    cont["crm"] = {
        "deals_lidos": len(deals),
        "record_count_declarado_no_export": bruto["export_meta"]["record_count"],
    }
    q = Counter()
    saida = []
    for d in deals:
        hist = [(s["stage"], parse_iso(s["at"])) for s in d["stage_history"]]
        ordenado = sorted(hist, key=lambda s: s[1])
        q["historico_fora_de_ordem"] += hist != ordenado
        etapas = {}
        for etapa, quando in ordenado:
            etapas.setdefault(etapa, quando)

        criado = parse_iso(d["created_at"])
        created_invalido = criado is None or criado != etapas["Entrada"]
        q["created_at_invalido_substituido_pela_entrada"] += created_invalido

        ganho = d["status"] == "won"
        data_ganho = etapas.get("Fechamento")
        ganho_sem_fechamento = ganho and data_ganho is None
        if ganho_sem_fechamento:
            data_ganho = parse_iso(d["updated_at"])
        q["ganho_sem_etapa_fechamento"] += ganho_sem_fechamento

        cf = d["custom_fields"]
        q["qualified_flag_sem_etapa_qualificacao"] += cf["qualified_flag"] and "Qualificação" not in etapas
        q["proposal_sent_sem_etapa_proposta"] += cf["proposal_sent"] and "Proposta" not in etapas

        empresa = d["contact"]["company"]
        segmento = SEGMENTOS.get(sem_acento(empresa["segment"]))
        q["segmento_nao_mapeado"] += segmento is None
        q["segmento_grafia_fora_do_padrao"] += segmento != empresa["segment"]
        q["valor_outlier"] += d["estimated_value"] >= LIMITE_VALOR_OUTLIER

        saida.append({
            "deal_id": d["deal_id"],
            "num": int(d["deal_id"].split("-")[-1]),
            "external_ref": d["external_ref"],
            "telefone": normaliza_telefone(d["contact"]["phone"]),
            "email": normaliza_email(d["contact"]["email"]),
            "contato_nome": d["contact"]["name"].strip(),
            "empresa": empresa["name"].strip(),
            "segmento": segmento,
            "segmento_original": empresa["segment"],
            "porte_faixa": empresa["employees"],
            "cidade": empresa["city"],
            "uf": empresa["state"],
            "canal_origem": d["source"]["channel"],
            "campanha": d["source"]["campaign"],
            "sdr": d["owner"]["name"],
            "etapas": etapas,
            "status": d["status"],
            "motivo_perda": d["lost_reason"],
            "valor": d["estimated_value"],
            "data_ganho": data_ganho if ganho else None,
            "qualified_flag": cf["qualified_flag"],
            "dq_created_at_invalido": created_invalido,
            "dq_historico_reordenado": hist != ordenado,
            "dq_ganho_sem_etapa_fechamento": ganho_sem_fechamento,
            "dq_flag_qualificado_sem_etapa": cf["qualified_flag"] and "Qualificação" not in etapas,
        })
    cont["crm"]["problemas_corrigidos_sem_descarte"] = dict(q)
    return saida


def deduplica_crm(deals: list[dict], cont: dict) -> list[dict]:
    """Playbook seção 6: mesmo telefone ou e-mail = mesmo lead."""
    ub = UniaoBusca()
    for d in deals:
        ub.une(d["deal_id"], "tel:" + d["telefone"])
        ub.une(d["deal_id"], "mail:" + d["email"])
    grupos = defaultdict(list)
    for d in deals:
        grupos[ub.acha(d["deal_id"])].append(d)

    ordem_status = {"won": 0, "open": 1, "lost": 2}
    leads = []
    for membros in grupos.values():
        membros.sort(key=lambda d: (d["etapas"]["Entrada"], d["num"]))
        p = membros[0]  # deal principal = o que entrou primeiro
        datas = {e: min((d["etapas"][e] for d in membros if e in d["etapas"]), default=None)
                 for e in ETAPAS}
        status = min((d["status"] for d in membros), key=ordem_status.get)
        perdas = [d for d in membros if d["status"] == "lost"]
        motivos = [d["motivo_perda"] for d in sorted(perdas, key=lambda d: d["etapas"]["Entrada"], reverse=True)
                   if d["motivo_perda"] != "Duplicado"]
        motivo = (motivos or ["Duplicado"])[0] if status == "lost" else None
        ganhos = [d for d in membros if d["status"] == "won"]
        ref = ganhos[0] if ganhos else p
        etapa_max = max((ETAPAS.index(e) for d in membros for e in d["etapas"]))
        data_ganho = min((d["data_ganho"] for d in ganhos), default=None)
        refs = sorted({d["external_ref"] for d in membros if d["external_ref"]})

        leads.append({
            "lead_id": f"L-{p['num']:05d}",
            "deal_id_principal": p["deal_id"],
            "deal_ids": ";".join(d["deal_id"] for d in membros),
            "n_deals_crm": len(membros),
            "codigo_vs": ";".join(refs) or None,
            "contato_nome": p["contato_nome"],
            "telefone": p["telefone"],
            "email": p["email"],
            "telefones_todos": {d["telefone"] for d in membros},
            "emails_todos": {d["email"] for d in membros},
            "codigos_todos": set(refs) | {f"VS-{d['num']:05d}" for d in membros},
            "empresa": p["empresa"],
            "segmento": p["segmento"],
            "segmento_original": p["segmento_original"],
            "porte_faixa": p["porte_faixa"],
            "porte_playbook": PORTE_PLAYBOOK.get(p["porte_faixa"]),
            "cidade": p["cidade"],
            "uf": p["uf"],
            "canal_origem": p["canal_origem"],
            "campanha": p["campanha"],
            "sdr_responsavel": p["sdr"],
            "data_entrada": datas["Entrada"],
            "data_primeiro_contato_crm": datas["Contato"],
            "data_qualificacao": datas["Qualificação"],
            "data_proposta": datas["Proposta"],
            "data_ganho": data_ganho,
            "etapa_max": ETAPAS[etapa_max],
            "status_lead": status,
            "motivo_perda": motivo,
            "contatado_crm": datas["Contato"] is not None,
            "qualificado": datas["Qualificação"] is not None,
            "proposta_enviada": datas["Proposta"] is not None,
            "ganho": status == "won",
            "ciclo_dias": (data_ganho - datas["Entrada"]).days if data_ganho else None,
            "valor_estimado": ref["valor"],
            "valor_estimado_tratado": ref["valor"] if ref["valor"] < LIMITE_VALOR_OUTLIER else None,
            "qualified_flag_crm": any(d["qualified_flag"] for d in membros),
            "dq_duplicado_no_crm": len(membros) > 1,
            "dq_duplicado_marcado_no_crm": any(d["motivo_perda"] == "Duplicado" for d in membros),
            "dq_created_at_invalido": any(d["dq_created_at_invalido"] for d in membros),
            "dq_historico_reordenado": any(d["dq_historico_reordenado"] for d in membros),
            "dq_ganho_sem_etapa_fechamento": any(d["dq_ganho_sem_etapa_fechamento"] for d in ganhos),
            "dq_flag_qualificado_sem_etapa": any(d["dq_flag_qualificado_sem_etapa"] for d in membros),
            "dq_valor_outlier": ref["valor"] >= LIMITE_VALOR_OUTLIER,
        })

    n_dup = sum(1 for l in leads if l["n_deals_crm"] > 1)
    cont["crm"].update({
        "grupos_de_duplicados": n_dup,
        "deals_absorvidos_por_duplicidade": len(deals) - len(leads),
        "duplicados_que_ja_estavam_marcados_como_Duplicado": sum(l["dq_duplicado_marcado_no_crm"] for l in leads),
        "leads_unicos": len(leads),
    })
    return leads


# ---------------------------------------------------------------------------
# 2. Log de conversas: agrega por lead
# ---------------------------------------------------------------------------

def carrega_conversas(caminho: Path, leads: list[dict], cont: dict) -> dict[str, dict]:
    por_tel, por_mail, contato_crm = {}, {}, {}
    for l in leads:
        for t in l["telefones_todos"]:
            por_tel[t] = l["lead_id"]
        for e in l["emails_todos"]:
            por_mail[e] = l["lead_id"]
        contato_crm[l["lead_id"]] = l["data_primeiro_contato_crm"]

    with caminho.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))

    q = Counter(mensagens_lidas=len(linhas))
    msgs = defaultdict(list)
    vistos = set()
    for r in linhas:
        chave = tuple(r.values())
        if chave in vistos:
            q["mensagens_duplicadas_descartadas"] += 1
            continue
        vistos.add(chave)
        ts_texto = r["timestamp"].strip()
        if ts_texto.endswith("Z"):
            # Sufixo "Z" com relógio local: ver nota, seção 4. Tratado como -03:00.
            q["timestamps_Z_tratados_como_local"] += 1
            ts_texto = ts_texto[:-1] + "-03:00"
        ts = parse_iso(ts_texto)
        if ts is None:
            q["mensagens_descartadas_timestamp_invalido"] += 1
            continue
        if r["telefone"].strip():
            lead_id = por_tel.get(normaliza_telefone(r["telefone"]))
        else:
            lead_id = por_mail.get(normaliza_email(r["email"]))
        if lead_id is None:
            q["mensagens_descartadas_sem_lead_no_crm"] += 1
            continue
        msgs[lead_id].append({"ts": ts, "canal": r["canal"], "dir": r["direcao"],
                              "texto": r["mensagem"], "z": r["timestamp"].strip().endswith("Z")})

    # Evidência para o tratamento do "Z": 1ª resposta com Z vs etapa Contato do CRM.
    evid = Counter()
    agg = {}
    for lead_id, ms in msgs.items():
        ms.sort(key=lambda m: m["ts"])
        ins = [m for m in ms if m["dir"] == "in"]
        outs = [m for m in ms if m["dir"] == "out"]
        if outs and outs[0]["z"] and contato_crm[lead_id]:
            delta = minutos(contato_crm[lead_id], outs[0]["ts"])
            evid["igual_ao_CRM_lendo_como_local" if delta == 0 else "diferente_do_CRM"] += 1

        primeira_in = ins[0]["ts"] if ins else None
        resposta = next((m["ts"] for m in outs if primeira_in and m["ts"] >= primeira_in), None)
        agg[lead_id] = {
            "canal_conversa": ";".join(sorted({m["canal"] for m in ms})),
            "n_msg_lead": len(ins),
            "n_msg_vertice": len(outs),
            "conversa_iniciada_por": "lead" if ms[0]["dir"] == "in" else "vertice",
            "data_primeira_msg_lead": primeira_in,
            "data_primeira_msg_vertice": outs[0]["ts"] if outs else None,
            "lead_sem_resposta": bool(primeira_in) and resposta is None,
            "intencao_primeira_msg": classifica_intencao(ins[0]["texto"]) if ins else None,
            "data_ultima_msg": ms[-1]["ts"],
        }
    q["mensagens_ligadas_a_leads"] = sum(len(v) for v in msgs.values())
    q["leads_com_conversa"] = len(agg)
    q["evidencia_Z_primeira_resposta"] = dict(evid)
    cont["conversas"] = dict(q)
    return agg


# ---------------------------------------------------------------------------
# 3. Planilha dos SDRs
# ---------------------------------------------------------------------------

MES_ABA = {"Jul": 7, "Ago": 8, "Set": 9}


def parse_data_planilha(valor, mes_aba: int):
    """Quatro formatos na mesma coluna. Devolve (datetime|None, formato, tem_hora)."""
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=TZ), "data_excel", True
    texto = str(valor or "").strip()
    if m := re.fullmatch(r"(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2})", texto):
        d, mes, a, h, mi = map(int, m.groups())
        return datetime(a, mes, d, h, mi, tzinfo=TZ), "texto dd/mm/aaaa hh:mm", True
    if m := re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", texto):
        x, y, a = map(int, m.groups())
        if y == mes_aba:
            return datetime(a, y, x, tzinfo=TZ), "texto dd/mm/aaaa", False
        if x == mes_aba:  # formato americano: o mês vem primeiro
            return datetime(a, x, y, tzinfo=TZ), "texto mm/dd/aaaa (EUA)", False
        return datetime(a, y, x, tzinfo=TZ), "texto dd/mm/aaaa (ambíguo)", False
    if m := re.fullmatch(r"(\d{2})/(\d{2})", texto):
        d, mes = map(int, m.groups())
        return datetime(2026, mes, d, tzinfo=TZ), "texto dd/mm (sem ano)", False
    return None, "invalido", False


def carrega_planilha(caminho: Path, leads: list[dict], cont: dict):
    wb = openpyxl.load_workbook(caminho, data_only=True, read_only=True)
    linhas = []
    for ws in wb.worksheets:
        for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if all(v is None for v in r[:9]):
                continue
            codigo, empresa, contato, tel, origem, data, sdr, status, obs = (tuple(r) + (None,) * 9)[:9]
            dt, formato, tem_hora = parse_data_planilha(data, MES_ABA[ws.title])
            st_txt = str(status or "").strip()
            linhas.append({
                "aba": ws.title, "linha": i,
                "codigo_original": codigo, "codigo": normaliza_codigo(codigo),
                "empresa": (empresa or "").strip(), "contato_nome": (contato or "").strip(),
                "telefone": normaliza_telefone(tel), "origem_original": origem,
                "data": dt, "formato_data": formato, "tem_hora": tem_hora,
                "sdr": normaliza_sdr(sdr), "status_original": st_txt,
                "status": STATUS_PLANILHA.get(st_txt.lower()), "obs": obs,
            })
    q = Counter(linhas_lidas=len(linhas))
    q["linhas_por_aba"] = dict(Counter(l["aba"] for l in linhas))
    q["sem_codigo"] = sum(l["codigo"] is None for l in linhas)
    q["codigo_fora_do_padrao_corrigido"] = sum(
        bool(l["codigo"]) and l["codigo_original"] != l["codigo"] for l in linhas)
    q["formatos_de_data"] = dict(Counter(l["formato_data"] for l in linhas))
    q["status_nao_mapeado"] = sum(l["status"] is None for l in linhas)
    q["sdr_nao_mapeado"] = sum(l["sdr"] is None for l in linhas)

    # Linhas repetidas: mesmo telefone na planilha. Fica a primeira ocorrência.
    unicas, vistos = [], {}
    identicas = 0
    for l in linhas:
        if l["telefone"] in vistos:
            a = vistos[l["telefone"]]
            identicas += all(a[k] == l[k] for k in ("codigo", "data", "status_original", "sdr"))
            continue
        vistos[l["telefone"]] = l
        unicas.append(l)
    q["linhas_repetidas_descartadas"] = len(linhas) - len(unicas)
    q["linhas_repetidas_identicas_a_primeira"] = identicas

    # Ligação com o CRM: telefone (chave do playbook), conferido pelo código quando existe.
    por_tel = {t: l for l in leads for t in l["telefones_todos"]}
    por_cod = {c: l for l in leads for c in l["codigos_todos"]}
    ligadas, so_planilha = {}, []
    for l in unicas:
        lead = por_tel.get(l["telefone"])
        if lead is None and l["codigo"]:
            lead = por_cod.get(l["codigo"])
            q["ligadas_so_pelo_codigo"] += lead is not None
        if lead is None:
            so_planilha.append(l)
            continue
        q["ligadas_pelo_telefone"] += 1
        if l["codigo"]:
            q["codigo_confere_com_o_telefone"] += l["codigo"] in lead["codigos_todos"]
            q["codigo_diverge_do_telefone"] += l["codigo"] not in lead["codigos_todos"]
        if lead["lead_id"] in ligadas:
            q["lead_em_mais_de_uma_linha_apos_dedup"] += 1
            continue
        ligadas[lead["lead_id"]] = l
    q["linhas_sem_lead_no_crm_(viram_lead_so_planilha)"] = len(so_planilha)
    q["obs_das_linhas_sem_crm"] = dict(Counter(l["obs"] for l in so_planilha))
    cont["planilha"] = dict(q)
    return ligadas, so_planilha


def colunas_planilha(l: dict, lead: dict | None) -> dict:
    status_crm = lead["status_lead"] if lead else None
    resultado = RESULTADO_STATUS_PLANILHA.get(l["status"], "open")
    dif = None
    if lead and lead["data_primeiro_contato_crm"] and l["data"]:
        dif = (l["data"].date() - lead["data_primeiro_contato_crm"].date()).days
    return {
        "planilha_aba": l["aba"],
        "planilha_linha": l["linha"],
        "planilha_data_1o_contato": l["data"],
        "planilha_formato_data": l["formato_data"],
        "planilha_dif_dias_vs_crm": dif,
        "planilha_sdr": l["sdr"],
        "planilha_status_original": l["status_original"],
        "planilha_status": l["status"],
        "planilha_resultado_conflita_crm": (resultado != status_crm) if lead else None,
        "planilha_obs": l["obs"],
        "planilha_origem_original": l["origem_original"],
        "dq_planilha_sem_codigo": l["codigo"] is None,
        "dq_planilha_codigo_fora_padrao": bool(l["codigo"]) and l["codigo_original"] != l["codigo"],
    }


# ---------------------------------------------------------------------------
# 4. Montagem da tabela
# ---------------------------------------------------------------------------

def tempo_ate_primeiro_contato(reg: dict) -> dict:
    """Do primeiro sinal do lead ao primeiro contato da Vértice, juntando CRM e log.

    Chegada = o que vier antes entre a entrada no CRM e a 1ª mensagem do lead.
    Contato = o que vier antes entre a etapa Contato do CRM e a 1ª mensagem da Vértice.
    Leads de lista fria (canal Outbound) não têm SLA de resposta: a Vértice é quem aborda.
    """
    chegada = min(d for d in (reg["data_entrada"], reg["data_primeira_msg_lead"]) if d)
    contato = min((d for d in (reg["data_primeiro_contato_crm"], reg["data_primeira_msg_vertice"]) if d),
                  default=None)
    contato = max(contato, chegada) if contato else None  # contato antes da chegada conta como imediato
    no_exp = em_expediente(chegada)
    sla = SLA_NO_EXPEDIENTE_MIN if no_exp else SLA_FORA_EXPEDIENTE_MIN
    uteis = round(minutos_uteis(chegada, contato), 1) if contato else None
    return {
        "data_chegada": chegada,
        "chegada_no_expediente": no_exp,
        "data_primeiro_contato": contato,
        "tempo_ate_1o_contato_min": minutos(chegada, contato),
        "tempo_ate_1o_contato_min_uteis": uteis,
        "aplica_sla": reg["canal_origem"] != "Outbound",
        "sla_playbook_min": sla,
        "dentro_sla_playbook": uteis is not None and uteis <= sla,
    }


def monta_tabela(leads, conversas, planilha_ligadas, so_planilha, cont) -> pd.DataFrame:
    vazio_conv = {k: None for k in next(iter(conversas.values()))}
    linhas = []
    for l in leads:
        reg = {k: v for k, v in l.items() if not k.endswith("_todos")}
        reg.update(conversas.get(l["lead_id"], vazio_conv))
        reg.update(tempo_ate_primeiro_contato(reg))
        pl = planilha_ligadas.get(l["lead_id"])
        reg.update(colunas_planilha(pl, l) if pl else {})
        reg.update(em_crm=True, em_conversas=l["lead_id"] in conversas, em_planilha=pl is not None)
        linhas.append(reg)

    for p in so_planilha:
        reg = {
            "lead_id": f"LP-{p['aba']}-{p['linha']:03d}",
            "codigo_vs": p["codigo"], "n_deals_crm": 0,
            "contato_nome": p["contato_nome"], "telefone": p["telefone"], "email": None,
            "empresa": p["empresa"],
            "canal_origem": ORIGEM_PLANILHA.get(str(p["origem_original"]).strip().lower()),
            "sdr_responsavel": p["sdr"],
            "data_entrada": p["data"],
            "em_crm": False, "em_conversas": False, "em_planilha": True,
        }
        reg.update(colunas_planilha(p, None))
        linhas.append(reg)

    df = pd.DataFrame(linhas)
    # Datas saem sem fuso (todas em -03:00) para abrir direto no Excel.
    for c in [c for c in df.columns if c.startswith("data_")] + ["planilha_data_1o_contato"]:
        df[c] = pd.to_datetime(df[c], utc=True).dt.tz_convert(TZ).dt.tz_localize(None)
    naive = lambda dt: dt.replace(tzinfo=None)
    df["fonte_registro"] = df.apply(
        lambda r: "+".join(n for n, f in (("crm", r.em_crm), ("conversas", r.em_conversas),
                                         ("planilha", r.em_planilha)) if f), axis=1)
    df["mes_entrada"] = df["data_entrada"].dt.strftime("%Y-%m")
    df["periodo_q3"] = df["data_entrada"].between(naive(Q3_INICIO), naive(Q3_FIM), inclusive="left")
    df["dias_entrada_ate_export"] = (naive(EXPORT_CRM) - df["data_entrada"]).dt.days

    ordem = [
        # identificação e cobertura
        "lead_id", "fonte_registro", "em_crm", "em_conversas", "em_planilha",
        "deal_id_principal", "deal_ids", "n_deals_crm", "codigo_vs",
        *COLUNAS_CONTATO,
        # empresa
        "empresa", "segmento", "segmento_original", "porte_faixa", "porte_playbook", "cidade", "uf",
        # origem e responsável
        "canal_origem", "campanha", "sdr_responsavel",
        # funil (CRM)
        "data_entrada", "mes_entrada", "periodo_q3", "dias_entrada_ate_export",
        "data_primeiro_contato_crm", "data_qualificacao", "data_proposta", "data_ganho",
        "etapa_max", "status_lead", "motivo_perda", "contatado_crm", "qualificado",
        "proposta_enviada", "ganho", "ciclo_dias", "valor_estimado", "valor_estimado_tratado",
        "qualified_flag_crm",
        # conversas
        "canal_conversa", "n_msg_lead", "n_msg_vertice", "conversa_iniciada_por",
        "data_primeira_msg_lead", "data_primeira_msg_vertice", "lead_sem_resposta",
        "intencao_primeira_msg", "data_ultima_msg",
        # tempo até o primeiro contato (CRM + log)
        "data_chegada", "chegada_no_expediente", "data_primeiro_contato",
        "tempo_ate_1o_contato_min", "tempo_ate_1o_contato_min_uteis", "aplica_sla",
        "sla_playbook_min", "dentro_sla_playbook",
        # planilha
        "planilha_aba", "planilha_linha", "planilha_data_1o_contato", "planilha_formato_data",
        "planilha_dif_dias_vs_crm", "planilha_sdr", "planilha_status_original", "planilha_status",
        "planilha_resultado_conflita_crm", "planilha_obs", "planilha_origem_original",
        # qualidade de dados
        "dq_duplicado_no_crm", "dq_duplicado_marcado_no_crm", "dq_created_at_invalido",
        "dq_historico_reordenado", "dq_ganho_sem_etapa_fechamento", "dq_flag_qualificado_sem_etapa",
        "dq_valor_outlier", "dq_planilha_sem_codigo", "dq_planilha_codigo_fora_padrao",
    ]
    df = df[ordem].sort_values("lead_id").reset_index(drop=True)

    cont["tabela_final"] = {
        "linhas": len(df),
        "leads_por_fonte": df["fonte_registro"].value_counts().to_dict(),
        "leads_q3": int(df["periodo_q3"].sum()),
        "leads_q3_por_fonte": df.loc[df["periodo_q3"], "fonte_registro"].value_counts().to_dict(),
        "lead_id_unico": bool(df["lead_id"].is_unique),
    }
    return df


# ---------------------------------------------------------------------------
# 5. Exportação
# ---------------------------------------------------------------------------

def exporta(df: pd.DataFrame, saida: Path, saida_local: Path, cont: dict) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    saida_local.mkdir(parents=True, exist_ok=True)

    publica = df.drop(columns=COLUNAS_CONTATO)
    publica.to_csv(saida / "01_tabela_analitica.csv", sep=";", index=False,
                   encoding="utf-8-sig", date_format="%Y-%m-%d %H:%M:%S")
    publica.to_excel(saida / "01_tabela_analitica.xlsx", index=False, sheet_name="leads")
    df.to_excel(saida_local / "01_tabela_analitica_com_contatos.xlsx", index=False, sheet_name="leads")

    (saida / "01_contagens_etl.json").write_text(
        json.dumps(cont, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("materiais"), help="pasta com os 3 arquivos de dados")
    ap.add_argument("--output", type=Path, default=Path("."), help="saída versionável (pseudonimizada)")
    ap.add_argument("--output-local", type=Path, default=Path("saida_local"),
                    help="saída com dados de contato (fica fora do git)")
    args = ap.parse_args()

    cont: dict = {}
    deals = carrega_crm(args.input / "crm_export_pipeway_2026-10-01.json", cont)
    leads = deduplica_crm(deals, cont)
    conversas = carrega_conversas(args.input / "conversas_whatsapp_email_2026.csv", leads, cont)
    ligadas, so_planilha = carrega_planilha(args.input / "controle_sdr_jul-set_2026.xlsx", leads, cont)
    df = monta_tabela(leads, conversas, ligadas, so_planilha, cont)
    exporta(df, args.output, args.output_local, cont)
    print(json.dumps(cont, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
