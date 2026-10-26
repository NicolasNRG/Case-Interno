"""
Entregável 4 · Linhas de base e poder estatístico para os critérios de aceite

Calcula, a partir da tabela do entregável 1, os números que o documento 04 usa e que
o baseline (entregável 2) ainda não tinha:
  - qualificação em até 7 dias da entrada (indicador antecipado);
  - hipótese de ganho de qualificação se nenhum lead ficar sem contato;
  - efeito mínimo detectável num piloto aleatorizado 50/50;
  - percentis de velocidade de hoje, para comparar com a meta do agente.

Uso:
    python 04_linhas_de_base_criterios.py --tabela 01_tabela_analitica.csv --saida 04_linhas_de_base.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

MESES_MADUROS = [f"2026-{m:02d}" for m in range(1, 8)]
MESES_Q3 = ["2026-07", "2026-08", "2026-09"]
SEMANAS_PILOTO = 5           # semanas 4 a 8 do cronograma (60 dias)
DIVISAO_AGENTE = 0.5          # fração dos leads de entrada que vai para o agente
SEMANAS_POR_MES = 52 / 12
COLUNAS = ["em_crm", "mes_entrada", "dias_entrada_ate_export", "aplica_sla", "data_entrada",
           "data_qualificacao", "contatado_crm", "qualificado", "ganho", "motivo_perda",
           "tempo_ate_1o_contato_min_uteis", "dentro_sla_playbook", "data_primeiro_contato"]


def n_por_grupo(p1: float, delta: float, z_alfa: float = 1.96, z_poder: float = 0.8416) -> int:
    p2 = min(p1 + delta, 0.9999)
    pm = (p1 + p2) / 2
    return math.ceil((z_alfa * math.sqrt(2 * pm * (1 - pm))
                      + z_poder * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (p2 - p1) ** 2)


def efeito_minimo(p: float, n: int, sentido: int = 1) -> float:
    """Menor diferença (em p.p.) detectável com n leads por grupo (5%, poder 80%)."""
    d = 0.001
    while d < 1:
        alvo = p + sentido * d
        if 0 < alvo < 1 and n_por_grupo(min(p, alvo), abs(d)) <= n:
            return round(d, 3)
        d += 0.001
    return math.nan


def carrega(caminho: Path) -> pd.DataFrame:
    cab = set(pd.read_csv(caminho, sep=";", encoding="utf-8-sig", nrows=0).columns)
    faltando = [c for c in COLUNAS if c not in cab]
    if faltando:
        raise SystemExit(f"A tabela {caminho} não tem as colunas: {', '.join(faltando)}. "
                         "Gere-a de novo com a versão atual do 01_etl.py.")
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", low_memory=False,
                     parse_dates=["data_entrada", "data_qualificacao", "data_primeiro_contato"])
    df = df[df["em_crm"] == True].copy()
    for c in ("aplica_sla", "contatado_crm", "qualificado", "ganho", "dentro_sla_playbook"):
        df[c] = df[c].astype(str) == "True"
    return df


def calcula(df: pd.DataFrame) -> dict:
    df["qualificado_7d"] = df["qualificado"] & (
        (df["data_qualificacao"] - df["data_entrada"]).dt.total_seconds() <= 7 * 86400)
    eleg = df[df["aplica_sla"] & (df["dias_entrada_ate_export"] >= 7)]
    q3 = eleg[eleg["mes_entrada"].isin(MESES_Q3)]
    madura = df[df["mes_entrada"].isin(MESES_MADUROS)]
    r = {}

    r["qualificacao_7d"] = {
        "q3": round(float(q3["qualificado_7d"].mean()), 4),
        "jan_set": round(float(eleg["qualificado_7d"].mean()), 4),
        "por_mes": {m: round(float(g["qualificado_7d"].mean()), 4) for m, g in eleg.groupby("mes_entrada")},
        "qualificacao_total_coortes_maduras": round(float(madura["qualificado"].mean()), 4),
        "qualificacoes_que_acontecem_em_7d": round(float(df.loc[df["qualificado"], "qualificado_7d"].mean()), 4),
    }

    # Hipótese de ganho: contatar quem hoje nunca é contatado (coortes maduras)
    nunca = madura[~madura["contatado_crm"]]
    desq_formulario = nunca["motivo_perda"].isin(["Fora do segmento", "Porte abaixo do mínimo"]).mean()
    qual_contatados = madura.loc[madura["contatado_crm"], "qualificado"].mean()
    nunca_q3 = 1 - q3["data_primeiro_contato"].notna().mean()
    r["hipotese_ganho_qualificacao"] = {
        "nunca_contatados_q3": round(float(nunca_q3), 4),
        "desses_ja_desqualificados_por_segmento_ou_porte": round(float(desq_formulario), 4),
        "taxa_qualificacao_de_quem_e_contatado": round(float(qual_contatados), 4),
        "ganho_esperado_pp": round(float(nunca_q3 * (1 - desq_formulario) * qual_contatados), 4),
        "formula": "nunca_contatados x (1 - ja_desqualificados) x taxa_qualificacao_de_quem_e_contatado",
    }

    # Velocidade de hoje (leads de entrada contatados, Q3)
    t = q3["tempo_ate_1o_contato_min_uteis"].dropna()
    r["velocidade_hoje_q3_min_uteis"] = {f"p{int(p*100)}": round(float(t.quantile(p)), 1) for p in (.5, .9, .95, .99)}

    # Poder do piloto: 50/50 durante N semanas
    leads_semana = len(q3) / 3 / SEMANAS_POR_MES
    n_grupo = int(leads_semana * SEMANAS_PILOTO * min(DIVISAO_AGENTE, 1 - DIVISAO_AGENTE))
    bases = {
        "dentro_sla": (float(q3["dentro_sla_playbook"].mean()), 1),
        "nunca_contatados": (float(nunca_q3), -1),
        "qualificacao_7d": (float(q3["qualificado_7d"].mean()), 1),
        "lead_para_ganho": (float(madura["ganho"].mean()), 1),
    }
    r["piloto"] = {
        "semanas": SEMANAS_PILOTO, "divisao_agente": DIVISAO_AGENTE,
        "leads_de_entrada_por_semana": round(leads_semana, 1), "leads_por_grupo": n_grupo,
        "efeito_minimo_detectavel_pp": {k: efeito_minimo(p, n_grupo, s) for k, (p, s) in bases.items()},
        "meio_ic95_da_diferenca_qualificacao_7d_pp": round(
            1.96 * math.sqrt(2 * bases["qualificacao_7d"][0] * (1 - bases["qualificacao_7d"][0]) / n_grupo), 3),
    }

    # Depois do dia 60: quanto tempo cada desenho leva para provar a hipótese
    leads_mes = len(q3) / 3
    alvos = {"qualificacao_7d_+6.4pp": (bases["qualificacao_7d"][0], r["hipotese_ganho_qualificacao"]["ganho_esperado_pp"]),
             "lead_para_ganho_+3pp": (bases["lead_para_ganho"][0], 0.03)}
    r["pos_piloto_meses_para_provar"] = {
        f"controle_{int(c * 100)}%": {k: round(n_por_grupo(p, d) / (leads_mes * c), 1) for k, (p, d) in alvos.items()}
        for c in (0.5, 0.2)}
    r["pos_piloto_meses_para_provar"]["nota"] = ("meses de entrada de leads até o grupo menor atingir o tamanho necessário; "
                                                 "a venda ainda precisa de +60 dias de maturação")
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tabela", type=Path, default=Path("01_tabela_analitica.csv"))
    ap.add_argument("--saida", type=Path, default=Path("04_linhas_de_base.json"))
    args = ap.parse_args()
    r = calcula(carrega(args.tabela))
    args.saida.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
