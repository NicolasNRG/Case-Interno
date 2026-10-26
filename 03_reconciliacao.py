"""
Entregável 3 · Reconciliação do dashboard

1. Lê os números do painel (export do Databox) e tenta reproduzir cada um a partir do
   export BRUTO do Pipeway, que é o que o conector nativo do Databox lê.
2. Decompõe a diferença entre a taxa do painel e a taxa oficial (ponte).
3. Calcula a série oficial por coorte e mostra como a fórmula do painel reage quando o
   volume de qualificados muda (cálculo ilustrativo, não dado observado).

Uso:
    python 03_reconciliacao.py --input <pasta_dos_materiais> --tabela 01_tabela_analitica.csv \
        --saida 03_reconciliacao.json
"""

from __future__ import annotations

import argparse
import json
import statistics as st
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openpyxl
import pandas as pd

TZ = timezone(timedelta(hours=-3))
Q3 = (datetime(2026, 7, 1, tzinfo=TZ), datetime(2026, 10, 1, tzinfo=TZ))
MESES_Q3 = [(2026, 7), (2026, 8), (2026, 9)]
JANELA_DIAS = 60
MESES_MADUROS = [f"2026-{m:02d}" for m in range(1, 8)]
AUMENTO_QUALIFICADOS_ILUSTRATIVO = 0.30


def parse(valor: str):
    try:
        return datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def no_q3(d) -> bool:
    return d is not None and Q3[0] <= d < Q3[1]


def mes(d):
    return (d.year, d.month) if d else None


# ---------------------------------------------------------------------------
# Painel e export bruto
# ---------------------------------------------------------------------------

def le_painel(caminho: Path) -> dict:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    kpis = {r[0]: {"valor": r[1], "definicao": r[2]}
            for r in wb["KPIs Q3 2026"].iter_rows(min_row=4, values_only=True) if r[0]}
    mensal = [{"mes": r[0], "qualificados": r[1], "ganhos": r[2]}
              for r in wb["Conversão por mês"].iter_rows(min_row=2, values_only=True) if r[0]]
    return {"kpis": kpis, "mensal": mensal}


def le_deals(caminho: Path, copias: set[str]) -> list[dict]:
    deals = []
    for d in json.loads(caminho.read_text(encoding="utf-8"))["deals"]:
        etapas = {}
        for s in sorted(d["stage_history"], key=lambda s: parse(s["at"])):
            etapas.setdefault(s["stage"], parse(s["at"]))
        ganho = d["status"] == "won"
        deals.append({
            "id": d["deal_id"], "copia": d["deal_id"] in copias,
            "created": parse(d["created_at"]), "entrada": etapas["Entrada"], "etapas": etapas,
            "won": ganho, "updated": parse(d["updated_at"]),
            "data_ganho": (etapas.get("Fechamento") or parse(d["updated_at"])) if ganho else None,
            "valor": d["estimated_value"], "qflag": d["custom_fields"]["qualified_flag"],
        })
    return deals


def reproduz_painel(deals: list[dict], painel: dict) -> dict:
    def por_mes(filtro, data):
        c = Counter(mes(data(d)) for d in deals if filtro(d))
        return [c[m] for m in MESES_Q3]

    r = {}
    # Leads qualificados
    rotulo = por_mes(lambda d: d["qflag"], lambda d: d["created"])
    reproduz = por_mes(lambda d: "Qualificação" in d["etapas"], lambda d: d["entrada"])
    equivalente = por_mes(lambda d: d["qflag"] and not d["copia"], lambda d: d["entrada"])
    r["leads_qualificados"] = {
        "painel": painel["kpis"]["Leads qualificados (Q3)"]["valor"],
        "painel_mensal": [m["qualificados"] for m in painel["mensal"]],
        "regra_do_rotulo_qualified_flag_e_created_at": {"mensal": rotulo, "total": sum(rotulo)},
        "regra_que_reproduz_etapa_qualificacao_e_mes_de_entrada": {"mensal": reproduz, "total": sum(reproduz)},
        "equivalente_qualified_flag_sem_copias_duplicadas": {"mensal": equivalente, "total": sum(equivalente)},
    }
    # Negócios ganhos
    ganhos_q3 = [d for d in deals if d["won"] and no_q3(d["updated"])]
    r["negocios_ganhos"] = {
        "painel": painel["kpis"]["Negócios ganhos (Q3)"]["valor"],
        "painel_mensal": [m["ganhos"] for m in painel["mensal"]],
        "regra_updated_at_no_periodo": {"total": len(ganhos_q3),
                                        "mensal": por_mes(lambda d: d["won"], lambda d: d["updated"])},
        "regra_data_do_ganho_no_periodo": {"total": sum(1 for d in deals if d["won"] and no_q3(d["data_ganho"])),
                                           "mensal": por_mes(lambda d: d["won"], lambda d: d["data_ganho"])},
        "ganhos_q3_de_deals_que_entraram_antes_do_q3": sum(1 for d in ganhos_q3 if d["entrada"] < Q3[0]),
    }
    r["taxa_conversao"] = {
        "painel": painel["kpis"]["Taxa de conversão (Q3)"]["valor"],
        "reproduzida": len(ganhos_q3) / sum(reproduz),
    }
    # Ticket médio
    valores = [d["valor"] for d in ganhos_q3]
    normais = [v for v in valores if v < 100_000]
    r["ticket_medio"] = {
        "painel": painel["kpis"]["Ticket médio (ganhos, Q3)"]["valor"],
        "media_dos_168": round(st.mean(valores), 2),
        "mediana_dos_168": st.median(valores),
        "media_sem_outlier": round(st.mean(normais), 2),
        "outliers": sorted(v for v in valores if v >= 100_000),
    }
    # Total de deals criados
    total = [d for d in deals if no_q3(d["created"]) or (d["created"] is None and no_q3(d["entrada"]))]
    r["total_deals_criados"] = {
        "painel": painel["kpis"]["Total de deals criados (Q3)"]["valor"],
        "reproduzido_created_at_valido_ou_entrada_se_invalido": len(total),
        "copias_duplicadas_incluidas": sum(d["copia"] for d in total),
        "deals_perdidos_pelo_ano_2024_digitado": sum(
            1 for d in deals if d["created"] and d["created"].year == 2024 and no_q3(d["entrada"])),
    }
    # Tempo médio de resposta: não reproduzido; registra as candidatas testadas
    base = [d for d in total if "Contato" in d["etapas"]]
    minutos = [(d["etapas"]["Contato"] - d["entrada"]).total_seconds() / 60 for d in base]
    r["tempo_medio_resposta"] = {
        "painel": painel["kpis"]["Tempo médio de resposta"]["valor"],
        "reproduzido": False,
        "media_minutos_corridos_mesmos_deals": round(st.mean(minutos), 1),
        "mediana_minutos_corridos_mesmos_deals": st.median(minutos),
        "deals_do_periodo_sem_contato_fora_da_media": len(total) - len(base),
    }
    return r


# ---------------------------------------------------------------------------
# Ponte, série oficial e efeito da fórmula do painel
# ---------------------------------------------------------------------------

COLUNAS_EXIGIDAS = ["deal_id_principal", "deal_ids", "em_crm", "mes_entrada", "data_entrada",
                    "data_ganho", "ciclo_dias", "qualificado", "ganho", "status_lead"]


def carrega_tabela(caminho: Path) -> pd.DataFrame:
    cabecalho = set(pd.read_csv(caminho, sep=";", encoding="utf-8-sig", nrows=0).columns)
    faltando = [c for c in COLUNAS_EXIGIDAS if c not in cabecalho]
    if faltando:
        raise SystemExit(
            f"A tabela {caminho} não tem as colunas: {', '.join(faltando)}.\n"
            "Gere a tabela de novo com a versão atual do 01_etl.py:\n"
            "    python 01_etl.py --input <pasta_dos_materiais> --output . --output-local saida_local")
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", low_memory=False,
                     parse_dates=["data_entrada", "data_ganho"])
    df = df[df["em_crm"] == True].copy()
    for c in ("qualificado", "ganho"):
        df[c] = df[c].astype(str) == "True"
    df["ganho_60d"] = df["ganho"] & (df["ciclo_dias"] <= JANELA_DIAS)
    df["mes_ganho"] = df["data_ganho"].dt.strftime("%Y-%m")
    return df


def ponte(df: pd.DataFrame, painel_taxa: float) -> list[dict]:
    q3 = df[df["mes_entrada"].isin(["2026-07", "2026-08", "2026-09"])]
    qual_q3 = q3[q3["qualificado"]]
    madura = df[df["mes_entrada"].isin(MESES_MADUROS)]
    qual_mad = madura[madura["qualificado"]]
    passos = [
        ("1. Painel: ganhos fechados no Q3 ÷ qualificados que entraram no Q3",
         painel_taxa, "Numerador e denominador são grupos diferentes"),
        ("2. Mesmo denominador, numerador só com ganhos desses mesmos qualificados",
         qual_q3["ganho"].sum() / len(qual_q3),
         "Coorte coerente, mas o Q3 ainda não teve tempo de fechar (agosto e setembro em aberto)"),
        ("3. Qualificados que já tiveram 60 dias (coortes Jan-Jul)",
         qual_mad["ganho_60d"].sum() / len(qual_mad),
         "Conversão de qualificados: é o que a fórmula do painel aproxima quando o fluxo é estável"),
        ("4. Denominador = todos os leads únicos (coortes Jan-Jul)",
         madura["ganho_60d"].sum() / len(madura),
         "Conversão de leads: a definição oficial"),
    ]
    return [{"passo": p, "taxa": round(float(t), 4), "leitura": l} for p, t, l in passos] + [{
        "qualificados_q3": int(len(qual_q3)),
        "desses_ja_ganhos": int(qual_q3["ganho"].sum()),
        "desses_ainda_abertos": int((qual_q3["status_lead"] == "open").sum()),
    }]


def serie_oficial(df: pd.DataFrame) -> list[dict]:
    linhas = []
    for m, g in df.groupby("mes_entrada"):
        q = g[g["qualificado"]]
        fechados_no_mes = (df["mes_ganho"] == m).sum()
        linhas.append({
            "mes": m, "madura": m in MESES_MADUROS, "leads": int(len(g)), "qualificados": int(len(q)),
            "ganhos_ate_60d": int(g["ganho_60d"].sum()),
            "conversao_leads_oficial": round(float(g["ganho_60d"].mean()), 4),
            "conversao_qualificados": round(float(q["ganho_60d"].mean()), 4),
            "formula_do_painel_no_mes": round(float(fechados_no_mes / len(q)), 4),
        })
    return linhas


def efeito_da_formula(df: pd.DataFrame) -> dict:
    """Se o agente qualificar +30% a partir do mês M, sem mudar a conversão real."""
    ganhos = df[df["ganho"]].copy()
    defasagem = (ganhos["data_ganho"].dt.to_period("M") - ganhos["data_entrada"].dt.to_period("M")).map(lambda x: x.n)
    s = (defasagem.value_counts(normalize=True).sort_index()).to_dict()
    c = float(df.loc[df["mes_entrada"].isin(MESES_MADUROS) & df["qualificado"], "ganho_60d"].mean())
    k = 1 + AUMENTO_QUALIFICADOS_ILUSTRATIVO
    # ganhos do mês M+i = c * soma(qualificados da coorte M+i-j * s_j); denominador = qualificados de M+i
    def taxa_painel(i):
        ganhos_m = sum(c * s.get(j, 0) * (k if i - j >= 0 else 1) for j in s)
        return round(ganhos_m / k, 4)
    return {
        "defasagem_entrada_ganho_em_meses": {int(j): round(v, 4) for j, v in s.items()},
        "conversao_real_de_qualificados": round(c, 4),
        "aumento_de_qualificados": AUMENTO_QUALIFICADOS_ILUSTRATIVO,
        "painel_mostraria": {f"M+{i}": taxa_painel(i) for i in range(3)},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("materiais"))
    ap.add_argument("--tabela", type=Path, default=Path("01_tabela_analitica.csv"))
    ap.add_argument("--saida", type=Path, default=Path("03_reconciliacao.json"))
    args = ap.parse_args()

    df = carrega_tabela(args.tabela)
    copias = {i for ids, p in zip(df["deal_ids"], df["deal_id_principal"]) for i in ids.split(";") if i != p}
    painel = le_painel(args.input / "dashboard_comercial_Q3_2026_export.xlsx")
    deals = le_deals(args.input / "crm_export_pipeway_2026-10-01.json", copias)

    r = {"reproducao_do_painel": reproduz_painel(deals, painel)}
    r["ponte"] = ponte(df, r["reproducao_do_painel"]["taxa_conversao"]["painel"])
    r["serie_oficial_por_coorte"] = serie_oficial(df)
    r["efeito_da_formula_do_painel_ilustrativo"] = efeito_da_formula(df)
    args.saida.write_text(json.dumps(r, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
