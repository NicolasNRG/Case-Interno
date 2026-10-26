"""
Entregável 7 · Tempos e volumes por etapa do processo atual (AS-IS)

Lê a tabela do entregável 1 e calcula, para cada etapa do funil:
tempo decorrido até a etapa seguinte, taxa de passagem e volume mensal.
O tempo de TRABALHO por etapa não existe em nenhuma fonte (classe D): só o
tempo decorrido entre registros (classe A).

Uso (rode antes o 01_etl.py, que gera a tabela):
    python 07_tempos_por_etapa.py --tabela <caminho>/01_tabela_analitica.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

MESES_MADUROS = [f"2026-{m:02d}" for m in range(1, 8)]
MESES_Q3 = ["2026-07", "2026-08", "2026-09"]
DATAS = ["data_entrada", "data_primeiro_contato_crm", "data_qualificacao", "data_proposta",
         "data_ganho", "planilha_data_1o_contato"]
COLUNAS = DATAS + ["em_crm", "em_planilha", "mes_entrada", "contatado_crm", "qualificado",
                   "aplica_sla", "dias_entrada_ate_export",
                   "proposta_enviada", "ganho", "n_msg_vertice", "n_msg_lead",
                   "tempo_ate_1o_contato_min_uteis", "planilha_dif_dias_vs_crm"]


def carrega(caminho: Path) -> pd.DataFrame:
    cab = set(pd.read_csv(caminho, sep=";", encoding="utf-8-sig", nrows=0).columns)
    faltando = [c for c in COLUNAS if c not in cab]
    if faltando:
        raise SystemExit(f"A tabela {caminho} não tem as colunas: {', '.join(faltando)}. "
                         "Gere-a de novo com a versão atual do 01_etl.py.")
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", low_memory=False, parse_dates=DATAS)
    for c in ("em_crm", "em_planilha", "contatado_crm", "qualificado", "proposta_enviada", "ganho", "aplica_sla"):
        df[c] = df[c].astype(str) == "True"
    return df


def dias(serie: pd.Series) -> dict:
    s = serie.dropna().dt.total_seconds() / 86400
    return {"n": int(s.size), "mediana": round(float(s.median()), 1),
            "p75": round(float(s.quantile(.75)), 1), "p90": round(float(s.quantile(.9)), 1)}


def calcula(df: pd.DataFrame) -> dict:
    crm = df[df["em_crm"]]
    mad = crm[crm["mes_entrada"].isin(MESES_MADUROS)]
    q3 = crm[crm["mes_entrada"].isin(MESES_Q3)]
    r = {}

    r["tempo_decorrido_dias"] = {
        "entrada_ate_contato": dias(crm["data_primeiro_contato_crm"] - crm["data_entrada"]),
        "contato_ate_qualificacao": dias(crm["data_qualificacao"] - crm["data_primeiro_contato_crm"]),
        "qualificacao_ate_proposta": dias(crm["data_proposta"] - crm["data_qualificacao"]),
        "proposta_ate_ganho": dias(crm["data_ganho"] - crm["data_proposta"]),
        "entrada_ate_ganho": dias(crm["data_ganho"] - crm["data_entrada"]),
    }
    # mesma base do baseline (entregável 2): leads de entrada com pelo menos 7 dias de vida
    eleg_q3 = q3[q3["aplica_sla"] & (q3["dias_entrada_ate_export"] >= 7)]
    t = eleg_q3["tempo_ate_1o_contato_min_uteis"].dropna()
    r["entrada_ate_contato_min_uteis_q3"] = {"mediana": float(t.median()), "p90": round(float(t.quantile(.9)), 1)}

    contatados = mad["contatado_crm"].sum()
    qualificados = mad["qualificado"].sum()
    propostas = mad["proposta_enviada"].sum()
    r["passagem_entre_etapas_jan_jul"] = {
        "entrada_para_contato": round(contatados / len(mad), 4),
        "contato_para_qualificacao": round(qualificados / contatados, 4),
        "qualificacao_para_proposta": round(propostas / qualificados, 4),
        "proposta_para_ganho": round(mad["ganho"].sum() / propostas, 4),
    }

    por_mes = 3  # volumes do Q3
    pl = df[df["em_planilha"]]
    pl_crm = pl[pl["em_crm"]]
    r["volume_mensal_q3"] = {
        "leads_unicos_crm": round(len(q3) / por_mes, 1),
        "leads_so_na_planilha": round(int((~df["em_crm"]).sum()) / por_mes, 1),
        "contatados": round(int(q3["contatado_crm"].sum()) / por_mes, 1),
        "qualificados": round(int(q3["qualificado"].sum()) / por_mes, 1),
        "propostas": round(int(q3["proposta_enviada"].sum()) / por_mes, 1),
        "linhas_na_planilha": round(len(pl) / por_mes, 1),
    }
    r["registro_duplo"] = {
        "linhas_planilha_ligadas_ao_crm": int(len(pl_crm)),
        "mesma_data_que_o_crm": round(float((pl_crm["planilha_dif_dias_vs_crm"] == 0).mean()), 4),
    }
    contatados_conv = crm[crm["contatado_crm"]]
    r["mensagens_por_lead_contatado"] = {
        "da_vertice": round(float(contatados_conv["n_msg_vertice"].fillna(0).mean()), 2),
        "do_lead": round(float(contatados_conv["n_msg_lead"].fillna(0).mean()), 2),
    }
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tabela", type=Path, default=Path("01_tabela_analitica.csv"))
    ap.add_argument("--saida", type=Path, default=Path("07_tempos_por_etapa.json"))
    args = ap.parse_args()
    r = calcula(carrega(args.tabela))
    args.saida.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
