"""
Entregável 2 · Cálculos do baseline

Lê a tabela do entregável 1 e calcula cada métrica do documento 02_baseline.md.
Nenhum número do documento é digitado à mão: todos saem daqui.

Uso:
    python 02_calculos_baseline.py --tabela 01_tabela_analitica.csv --saida 02_metricas_baseline.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

EXPORT = pd.Timestamp("2026-10-01 06:00")
MESES_MADUROS = [f"2026-{m:02d}" for m in range(1, 8)]  # Jan-Jul: todo lead com >= 60 dias de vida
MESES_Q3 = ["2026-07", "2026-08", "2026-09"]
SEMANAS_POR_MES = 52 / 12
HORAS_SDR_SEMANA_DECLARADAS = 60  # Ficha: 15h x 4 SDRs, sem apontamento
JORNADA_SEMANAL_SDR = 40           # premissa para expressar em % da capacidade
N_SDRS = 4

DATAS = ["data_entrada", "data_primeiro_contato_crm", "data_qualificacao", "data_proposta",
         "data_ganho", "data_primeira_msg_lead", "data_primeira_msg_vertice", "data_ultima_msg",
         "data_chegada", "data_primeiro_contato",
         "planilha_data_1o_contato"]


def wilson(sucessos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de 95% para uma proporção."""
    if n == 0:
        return (math.nan, math.nan)
    p = sucessos / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margem = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (round(centro - margem, 4), round(centro + margem, 4))


def taxa(sucessos, n) -> dict:
    sucessos, n = int(sucessos), int(n)
    return {"num": sucessos, "den": n, "taxa": round(sucessos / n, 4) if n else None,
            "ic95": wilson(sucessos, n)}


def pct(serie: pd.Series, qs=(0.25, 0.5, 0.75, 0.9)) -> dict:
    s = serie.dropna()
    return {"n": int(s.size), "media": round(float(s.mean()), 1),
            **{f"p{int(q * 100)}": round(float(s.quantile(q)), 1) for q in qs}}


def n_por_grupo(p1: float, delta: float, z_alfa: float = 1.96, z_poder: float = 0.8416) -> int:
    """Leads por grupo para detectar +delta numa proporção (bicaudal 5%, poder 80%)."""
    p2 = p1 + delta
    pm = (p1 + p2) / 2
    return math.ceil((z_alfa * math.sqrt(2 * pm * (1 - pm))
                      + z_poder * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / delta ** 2)


def carrega(caminho: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", parse_dates=DATAS, low_memory=False)
    for c in df.columns:  # booleanos com vazio chegam como texto; viram booleano anulável
        if df[c].dtype == object and set(df[c].dropna().unique()) <= {True, False, "True", "False"}:
            df[c] = df[c].map({True: True, False: False, "True": True, "False": False}).astype("boolean")
    return df


def calcula(df: pd.DataFrame) -> dict:
    crm = df[df["em_crm"]].copy()
    m = {}

    # 1. Volume -------------------------------------------------------------------------
    por_mes = crm.groupby("mes_entrada").agg(leads=("lead_id", "size"), deals=("n_deals_crm", "sum"))
    m["volume"] = {
        "deals_brutos_total": int(crm["n_deals_crm"].sum()),
        "deals_brutos_por_mes_media": round(crm["n_deals_crm"].sum() / 9, 1),
        "leads_unicos_total": int(len(crm)),
        "leads_unicos_por_mes_media": round(len(crm) / 9, 1),
        "leads_unicos_por_mes_q3": round(crm["mes_entrada"].isin(MESES_Q3).sum() / 3, 1),
        "serie_mensal": por_mes.reset_index().to_dict("records"),
        "min_mes": int(por_mes["leads"].min()), "max_mes": int(por_mes["leads"].max()),
        "leads_so_planilha_q3": int((~df["em_crm"]).sum()),
        "leads_so_planilha_q3_qualificados": int(((~df["em_crm"]) & (df["planilha_status"] == "qualificado")).sum()),
        "taxa_duplicidade_deals": round(1 - len(crm) / crm["n_deals_crm"].sum(), 4),
    }

    # 2. Funil por coorte de entrada ---------------------------------------------------
    madura = crm[crm["mes_entrada"].isin(MESES_MADUROS)]
    q = madura["qualificado"]
    m["funil_coortes_maduras_jan_jul"] = {
        "leads": int(len(madura)),
        "lead_para_ganho": taxa(madura["ganho"].sum(), len(madura)),
        "lead_para_contato": taxa(madura["contatado_crm"].sum(), len(madura)),
        "lead_para_qualificado": taxa(q.sum(), len(madura)),
        "qualificado_para_proposta": taxa(madura.loc[q, "proposta_enviada"].sum(), q.sum()),
        "proposta_para_ganho": taxa(madura["ganho"].sum(), madura["proposta_enviada"].sum()),
        "qualificado_para_ganho": taxa(madura.loc[q, "ganho"].sum(), q.sum()),
        "ainda_abertos": taxa((madura["status_lead"] == "open").sum(), len(madura)),
    }
    coorte = crm.groupby("mes_entrada").agg(
        leads=("lead_id", "size"), contatados=("contatado_crm", "sum"),
        qualificados=("qualificado", "sum"), ganhos=("ganho", "sum"),
        abertos=("status_lead", lambda s: (s == "open").sum()))
    coorte["lead_para_ganho"] = (coorte["ganhos"] / coorte["leads"]).round(4)
    coorte["lead_para_qualificado"] = (coorte["qualificados"] / coorte["leads"]).round(4)
    coorte["madura"] = coorte.index.isin(MESES_MADUROS)
    m["funil_por_coorte"] = coorte.reset_index().to_dict("records")
    m["todos_os_leads_jan_set"] = {
        "lead_para_ganho": taxa(crm["ganho"].sum(), len(crm)),
        "qualificado_para_ganho": taxa(crm.loc[crm["qualificado"], "ganho"].sum(), crm["qualificado"].sum()),
    }

    # Tempo até cada etapa (para justificar a janela de maturação)
    dias = lambda a, b: (crm[b] - crm[a]).dt.total_seconds() / 86400
    m["tempos_entre_etapas_dias"] = {
        "entrada_ate_contato": pct(dias("data_entrada", "data_primeiro_contato_crm"), (0.5, 0.9, 0.99)),
        "entrada_ate_qualificacao": pct(dias("data_entrada", "data_qualificacao"), (0.5, 0.9, 0.99)),
        "entrada_ate_ganho_ciclo": pct(crm["ciclo_dias"], (0.25, 0.5, 0.75, 0.9)) | {"max": int(crm["ciclo_dias"].max())},
    }

    # 3. Tempo até o primeiro contato (chegada do lead -> 1º contato, CRM + log) -------
    # Base: leads de entrada (sem lista fria) com pelo menos 7 dias de vida no export,
    # para dar tempo do contato acontecer (p99 entrada->contato = 2,7 dias).
    conv = crm[crm["em_conversas"]]
    eleg = crm[crm["aplica_sla"] & (crm["dias_entrada_ate_export"] >= 7)].copy()

    def resposta(base: pd.DataFrame) -> dict:
        contatados = base[base["data_primeiro_contato"].notna()]
        t = contatados["tempo_ate_1o_contato_min_uteis"]
        return {
            "leads": int(len(base)),
            "minutos_uteis_entre_contatados": pct(t),
            "minutos_corridos_entre_contatados": pct(contatados["tempo_ate_1o_contato_min"]),
            "ate_15_min_uteis_entre_contatados": taxa((t <= 15).sum(), len(contatados)),
            "dentro_sla_playbook_entre_todos": taxa(base["dentro_sla_playbook"].sum(), len(base)),
            "nunca_contatados": taxa(base["data_primeiro_contato"].isna().sum(), len(base)),
            "escreveram_e_ficaram_sem_resposta": taxa((base["lead_sem_resposta"] == True).sum(), len(base)),
        }

    def resumo(g: pd.DataFrame) -> dict:
        return {"leads": int(len(g)),
                "mediana_min_uteis": round(float(g["tempo_ate_1o_contato_min_uteis"].median()), 1),
                "dentro_sla": round(float(g["dentro_sla_playbook"].mean()), 4),
                "nunca_contatados": round(float(g["data_primeiro_contato"].isna().mean()), 4)}

    m["resposta_jan_set"] = resposta(eleg)
    m["resposta_q3"] = resposta(eleg[eleg["mes_entrada"].isin(MESES_Q3)])
    m["resposta_por_mes"] = {mes: resumo(g) for mes, g in eleg.groupby("mes_entrada")}
    m["resposta_por_sdr"] = {sdr: resumo(g) for sdr, g in eleg.groupby("sdr_responsavel")}
    m["chegadas_fora_do_expediente"] = int((crm["chegada_no_expediente"] == False).sum())

    # Velocidade x resultado (coortes maduras): a hipótese "perde lead por demora"
    mad = eleg[eleg["mes_entrada"].isin(MESES_MADUROS)].copy()
    faixas = pd.cut(mad["tempo_ate_1o_contato_min_uteis"], [-0.1, 15, 60, 240, math.inf],
                    labels=["1. ate 15 min", "2. 15-60 min", "3. 1-4 h uteis", "4. mais de 4 h uteis"])
    mad["faixa"] = faixas.astype(object).where(mad["data_primeiro_contato"].notna(), "5. nunca contatado")
    m["ganho_por_faixa_de_contato_jan_jul"] = {
        f: taxa(g["ganho"].sum(), len(g)) | {"lead_para_qualificado": round(float(g["qualificado"].mean()), 4)}
        for f, g in mad.groupby("faixa")}
    m["ganho_por_faixa_e_sdr_jan_jul"] = (
        mad[mad["data_primeiro_contato"].notna()]
        .assign(ate15=lambda d: d["tempo_ate_1o_contato_min_uteis"] <= 15)
        .groupby(["sdr_responsavel", "ate15"])["ganho"].agg(["size", "mean"]).round(4)
        .reset_index().to_dict("records"))

    # 4. Leads que nunca receberam atenção --------------------------------------------
    m["nao_atendidos_jan_jul"] = {
        "nunca_contatados_no_crm": taxa((~madura["contatado_crm"]).sum(), len(madura)),
        "nunca_contatados_sem_nenhuma_msg": taxa(((~madura["contatado_crm"]) & (~madura["em_conversas"])).sum(), len(madura)),
        "nunca_contatados_que_mandaram_msg": taxa(((~madura["contatado_crm"]) & (madura["lead_sem_resposta"] == True)).sum(), len(madura)),
        "motivo_perda_dos_nunca_contatados": madura.loc[~madura["contatado_crm"], "motivo_perda"].fillna("(aberto)").value_counts().to_dict(),
    }

    # 5. Ticket e ciclo -----------------------------------------------------------------
    ganhos = crm[crm["ganho"]]
    m["ticket"] = {
        "ganhos": int(len(ganhos)),
        "media_bruta": round(float(ganhos["valor_estimado"].mean()), 2),
        "media_sem_outliers": round(float(ganhos["valor_estimado_tratado"].mean()), 2),
        "mediana_sem_outliers": float(ganhos["valor_estimado_tratado"].median()),
        "p25_p75_sem_outliers": [float(ganhos["valor_estimado_tratado"].quantile(.25)),
                                 float(ganhos["valor_estimado_tratado"].quantile(.75))],
        "ganhos_outlier": int(ganhos["dq_valor_outlier"].sum()),
        "valores_outlier": sorted(ganhos.loc[ganhos["dq_valor_outlier"], "valor_estimado"].astype(int).tolist()),
    }
    m["ciclo_dias"] = pct(ganhos["ciclo_dias"], (0.25, 0.5, 0.75, 0.9)) | {
        "min": int(ganhos["ciclo_dias"].min()), "max": int(ganhos["ciclo_dias"].max()),
        "ganhos_com_data_por_updated_at": int(ganhos["dq_ganho_sem_etapa_fechamento"].sum())}

    # 6. Perfil da demanda (o que o agente vai receber) -------------------------------
    m["perfil"] = {
        "motivo_perda_leads": crm["motivo_perda"].value_counts().to_dict(),
        "porte_playbook": crm["porte_playbook"].value_counts().to_dict(),
        "intencao_primeira_msg": conv["intencao_primeira_msg"].value_counts().to_dict(),
        "canal_conversa": conv["canal_conversa"].value_counts().to_dict(),
        "conversa_iniciada_por": conv["conversa_iniciada_por"].value_counts().to_dict(),
        "entrada_por_hora": crm["data_entrada"].dt.hour.value_counts().sort_index().to_dict(),
        "entrada_por_dia_semana": crm["data_entrada"].dt.dayofweek.value_counts().sort_index().to_dict(),
    }
    m["conformidade_playbook"] = {
        "leads_perdidos_por_sem_orcamento": int((crm["motivo_perda"] == "Sem orçamento").sum()),
        "ganhos_com_porte_1_10": int(((crm["porte_faixa"] == "1-10") & crm["ganho"]).sum()),
        "leads_com_deal_duplicado": int(crm["dq_duplicado_no_crm"].sum()),
        "planilha_obs_concorrente": int((df["planilha_obs"] == "comparando com Senseye").sum()),
        "valor_ganhos_porte_1_10": int(crm.loc[(crm["porte_faixa"] == "1-10") & crm["ganho"], "valor_estimado_tratado"].sum()),
        "leads_abertos_coortes_maduras": int((madura["status_lead"] == "open").sum()),
    }
    m["funil_por_porte_jan_jul"] = (
        madura.groupby("porte_faixa").agg(leads=("lead_id", "size"), ganhos=("ganho", "sum"),
                                          qualificados=("qualificado", "sum"))
        .assign(lead_para_ganho=lambda d: (d["ganhos"] / d["leads"]).round(4))
        .reset_index().to_dict("records"))

    # 7. Esforço do processo atual ------------------------------------------------------
    horas_mes = HORAS_SDR_SEMANA_DECLARADAS * SEMANAS_POR_MES
    msgs_vertice_mes = df["n_msg_vertice"].sum() / 9
    contatados_mes = crm["contatado_crm"].sum() / 9
    linhas_planilha_mes = df["em_planilha"].sum() / 3
    m["esforco"] = {
        "horas_mes_declaradas": round(horas_mes, 1),
        "pct_capacidade_sdr": round(horas_mes / (N_SDRS * JORNADA_SEMANAL_SDR * SEMANAS_POR_MES), 4),
        "volume_mes": {
            "leads_unicos": round(len(crm) / 9, 1),
            "leads_contatados": round(contatados_mes, 1),
            "leads_qualificados": round(crm["qualificado"].sum() / 9, 1),
            "mensagens_enviadas_pelos_sdrs": round(msgs_vertice_mes, 1),
            "mensagens_recebidas_dos_leads": round(df["n_msg_lead"].sum() / 9, 1),
            "linhas_na_planilha_paralela": round(linhas_planilha_mes, 1),
            "pedidos_de_ligacao_primeira_msg": round((conv["intencao_primeira_msg"] == "pede_ligacao").sum() / 9, 1),
        },
        "horas_declaradas_implicam": {
            "min_por_lead_que_entra": round(horas_mes * 60 / (len(crm) / 9), 1),
            "min_por_lead_contatado": round(horas_mes * 60 / contatados_mes, 1),
            "min_por_mensagem_enviada": round(horas_mes * 60 / msgs_vertice_mes, 1),
        },
        "horas_mes_por_minuto_de_premissa": {
            "por_mensagem_enviada": round(msgs_vertice_mes / 60, 1),
            "por_lead_contatado": round(contatados_mes / 60, 1),
            "por_linha_da_planilha": round(linhas_planilha_mes / 60, 1),
        },
    }
    # 8. O que dá para detectar em 60 dias ---------------------------------------------
    leads_mes = len(eleg[eleg["mes_entrada"].isin(MESES_Q3)]) / 3
    base = {
        "lead_para_ganho +2pp": (m["funil_coortes_maduras_jan_jul"]["lead_para_ganho"]["taxa"], 0.02),
        "lead_para_ganho +3pp": (m["funil_coortes_maduras_jan_jul"]["lead_para_ganho"]["taxa"], 0.03),
        "lead_para_qualificado +5pp": (m["funil_coortes_maduras_jan_jul"]["lead_para_qualificado"]["taxa"], 0.05),
        "dentro_sla +10pp": (m["resposta_q3"]["dentro_sla_playbook_entre_todos"]["taxa"], 0.10),
    }
    m["detectabilidade"] = {"leads_de_entrada_por_mes_q3": round(leads_mes, 1)} | {
        nome: {"leads_por_grupo": n_por_grupo(p, d), "meses_de_leads": round(n_por_grupo(p, d) / leads_mes, 1)}
        for nome, (p, d) in base.items()}
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tabela", type=Path, default=Path("01_tabela_analitica.csv"))
    ap.add_argument("--saida", type=Path, default=Path("02_metricas_baseline.json"))
    args = ap.parse_args()
    m = calcula(carrega(args.tabela))
    args.saida.write_text(json.dumps(m, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(m, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
