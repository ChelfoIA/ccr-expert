#!/usr/bin/env python3
"""
Conciliação por fonte de recursos entre o que o ente recebeu para o enfrentamento
da covid-19 (transferências fundo a fundo do FNS, auxílio financeiro da LC 173/2020,
outras fontes vinculadas) e o que empenhou, liquidou e pagou, por fonte e por mês,
com saldo financeiro e orçamentário, restos a pagar, devoluções, rendimentos e
inconsistências nos estágios da despesa (Lei 4.320/1964, arts. 58 a 65).
Parte da skill: pericia-prestacao-contas-covid-saude

Teste de sanidade embutido: a soma por fonte e a soma por mês fecham com os
totais gerais, ou o script falha de propósito (código 1). Nenhum valor é
estimado: tudo vem dos dois CSV informados.

Uso:
    python3 scripts/conciliacao_fonte_recurso.py --receitas assets/exemplo_receitas.csv \
        --despesas assets/exemplo_despesas.csv --saida conciliacao.json --md conciliacao.md
    python3 scripts/conciliacao_fonte_recurso.py --receitas receitas.csv --despesas despesas.csv \
        --data-corte 31/12/2020 --csv conciliacao_mensal.csv

Layout dos CSV (separador ponto e vírgula, cabeçalho na primeira linha):
    receitas: data;fonte;origem;documento;valor
              (valor negativo registra devolução; "rendimento" na origem marca aplicação financeira)
    despesas: empenho;data_empenho;fonte;credor;cnpj;objeto;valor_empenhado;data_liquidacao;
              valor_liquidado;data_pagamento;valor_pago;nf;processo (data_nf é opcional)
"""
import argparse
import csv
import json
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 34

SKILL = "pericia-prestacao-contas-covid-saude"
VERSAO = "1.0.0"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
TOLERANCIA = Decimal("0.005")
ZERO = Decimal("0")

COLUNAS_RECEITAS = ["data", "fonte", "origem", "documento", "valor"]
COLUNAS_DESPESAS = ["empenho", "data_empenho", "fonte", "credor", "cnpj", "objeto",
                    "valor_empenhado", "data_liquidacao", "valor_liquidado",
                    "data_pagamento", "valor_pago", "nf", "processo"]


def parse_num(texto) -> Decimal:
    """Aceita 1.234,56 (brasileiro) e 1234.56 (técnico); remove R$, % e espaços."""
    if texto is None:
        raise ValueError("valor numérico ausente")
    if isinstance(texto, (int, Decimal)):
        return Decimal(str(texto))
    if isinstance(texto, float):
        raise ValueError("valor monetário em float não é aceito; informe texto ou Decimal")
    s = str(texto).strip().replace("R$", "").replace("%", "").replace(" ", "")
    if s == "":
        raise ValueError("valor numérico vazio")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except Exception as exc:
        raise ValueError(f"número inválido: {texto!r}") from exc


def parse_num_opcional(texto) -> Decimal:
    if texto is None or str(texto).strip() == "":
        return ZERO
    return parse_num(texto)


def fmt_num(valor: Decimal, casas: int = 2) -> str:
    quant = Decimal(1).scaleb(-casas)
    v = valor.quantize(quant, rounding=ROUND_HALF_UP)
    negativo = v < 0
    v = abs(v)
    inteiro, _, frac = f"{v:f}".partition(".")
    frac = (frac + "0" * casas)[:casas] if casas else ""
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return ("-" if negativo else "") + ".".join(grupos) + ("," + frac if casas else "")


def fmt_brl(valor: Decimal) -> str:
    return fmt_num(valor, 2)


def parse_data(texto, contexto: str = "") -> date:
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        onde = f" ({contexto})" if contexto else ""
        raise ValueError(f"data inválida{onde}, esperado dd/mm/aaaa: {texto!r}") from exc


def parse_data_opcional(texto, contexto: str = ""):
    if texto is None or str(texto).strip() == "":
        return None
    return parse_data(texto, contexto)


def fmt_data(d) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def chave_mes(d: date) -> str:
    return d.strftime("%m/%Y")


def ordem_mes(chave: str):
    mes, ano = chave.split("/")
    return (int(ano), int(mes))


def ler_csv(caminho: str, colunas: list, rotulo: str) -> list:
    p = Path(caminho)
    if not p.exists():
        raise ValueError(f"arquivo de {rotulo} não encontrado: {caminho}")
    with p.open(encoding="utf-8-sig", newline="") as fh:
        leitor = csv.DictReader(fh, delimiter=";")
        if leitor.fieldnames is None:
            raise ValueError(f"arquivo de {rotulo} vazio: {caminho}")
        campos = [c.strip() for c in leitor.fieldnames]
        faltam = [c for c in colunas if c not in campos]
        if faltam:
            raise ValueError(f"arquivo de {rotulo} sem as colunas obrigatórias: {', '.join(faltam)}")
        linhas = []
        for numero, linha in enumerate(leitor, start=2):
            limpa = {(k or "").strip(): (v or "").strip() for k, v in linha.items() if k is not None}
            if not any(limpa.values()):
                continue
            limpa["_linha"] = numero
            linhas.append(limpa)
    if not linhas:
        raise ValueError(f"arquivo de {rotulo} sem registros: {caminho}")
    return linhas


def processar_receitas(linhas: list) -> list:
    receitas = []
    for r in linhas:
        ctx = f"receitas, linha {r['_linha']}"
        fonte = r["fonte"]
        if not fonte:
            raise ValueError(f"{ctx}: fonte de recursos vazia")
        d = parse_data(r["data"], ctx)
        valor = parse_num(r["valor"])
        if valor == ZERO:
            raise ValueError(f"{ctx}: receita com valor zero")
        origem = r["origem"]
        tipo = "devolução" if valor < 0 else ("rendimento" if "rendimento" in origem.lower() else "ingresso")
        receitas.append({"linha": r["_linha"], "data": d, "mes": chave_mes(d), "fonte": fonte,
                         "origem": origem, "documento": r["documento"], "valor": valor, "tipo": tipo})
    return receitas


def processar_despesas(linhas: list) -> list:
    despesas = []
    vistos = set()
    for r in linhas:
        ctx = f"despesas, linha {r['_linha']}"
        emp = r["empenho"]
        if not emp:
            raise ValueError(f"{ctx}: número de empenho vazio")
        if emp in vistos:
            raise ValueError(f"{ctx}: empenho {emp} repetido; consolide os registros antes de conciliar")
        vistos.add(emp)
        de = parse_data(r["data_empenho"], f"{ctx}, data_empenho")
        ve = parse_num(r["valor_empenhado"])
        if ve <= ZERO:
            raise ValueError(f"{ctx}: empenho {emp} com valor empenhado não positivo")
        dl = parse_data_opcional(r.get("data_liquidacao"), f"{ctx}, data_liquidacao")
        vl = parse_num_opcional(r.get("valor_liquidado"))
        dp = parse_data_opcional(r.get("data_pagamento"), f"{ctx}, data_pagamento")
        vp = parse_num_opcional(r.get("valor_pago"))
        dnf = parse_data_opcional(r.get("data_nf"), f"{ctx}, data_nf")
        if vl < ZERO or vp < ZERO:
            raise ValueError(f"{ctx}: empenho {emp} com valor liquidado ou pago negativo")
        despesas.append({"linha": r["_linha"], "empenho": emp, "data_empenho": de, "fonte": r["fonte"],
                         "credor": r["credor"], "cnpj": r["cnpj"], "objeto": r["objeto"],
                         "valor_empenhado": ve, "data_liquidacao": dl, "valor_liquidado": vl,
                         "data_pagamento": dp, "valor_pago": vp, "nf": r.get("nf", ""),
                         "data_nf": dnf, "processo": r.get("processo", "")})
    return despesas


def testar_estagios(despesas: list, fontes_receita: set) -> list:
    """Testes dos estágios da despesa (Lei 4.320/1964, arts. 60, 62 e 63) e da fonte."""
    achados = []

    def add(d, tipo, detalhe, valor):
        achados.append({"empenho": d["empenho"], "fonte": d["fonte"], "credor": d["credor"],
                        "tipo": tipo, "detalhe": detalhe, "valor": valor})

    for d in despesas:
        ve, vl, vp = d["valor_empenhado"], d["valor_liquidado"], d["valor_pago"]
        if not d["fonte"]:
            add(d, "despesa sem fonte", "registro sem código de fonte de recursos", ve)
        elif d["fonte"] not in fontes_receita:
            add(d, "despesa em fonte sem receita registrada",
                f"fonte {d['fonte']} não consta do arquivo de receitas", ve)
        if vp > ZERO and vl == ZERO:
            add(d, "pagamento sem liquidação",
                "valor pago sem liquidação registrada (Lei 4.320/1964, art. 62)", vp)
        if vl > ve + TOLERANCIA:
            add(d, "liquidação superior ao empenho",
                f"liquidado {fmt_brl(vl)} contra empenhado {fmt_brl(ve)}; diferença sem prévio empenho "
                "(Lei 4.320/1964, art. 60)", vl - ve)
        if vl > ZERO and vp > vl + TOLERANCIA:
            add(d, "pagamento superior à liquidação",
                f"pago {fmt_brl(vp)} contra liquidado {fmt_brl(vl)} (Lei 4.320/1964, art. 62)", vp - vl)
        if d["data_liquidacao"] and d["data_liquidacao"] < d["data_empenho"]:
            add(d, "liquidação anterior ao empenho",
                f"liquidação em {fmt_data(d['data_liquidacao'])} e empenho em {fmt_data(d['data_empenho'])} "
                "(Lei 4.320/1964, art. 60)", vl)
        if d["data_nf"] and d["data_nf"] < d["data_empenho"]:
            add(d, "nota fiscal anterior ao empenho",
                f"NF {d['nf'] or 's/n'} de {fmt_data(d['data_nf'])} e empenho em {fmt_data(d['data_empenho'])}; "
                "indício de despesa realizada antes do empenho (Lei 4.320/1964, art. 60)", ve)
        if d["data_pagamento"] and d["data_liquidacao"] and d["data_pagamento"] < d["data_liquidacao"]:
            add(d, "pagamento anterior à liquidação",
                f"pagamento em {fmt_data(d['data_pagamento'])} e liquidação em {fmt_data(d['data_liquidacao'])} "
                "(Lei 4.320/1964, arts. 62 e 63)", vp)
        if vp > ZERO and not d["data_pagamento"]:
            add(d, "pagamento sem data", "valor pago sem data de pagamento informada", vp)
        if vl > ZERO and not d["data_liquidacao"]:
            add(d, "liquidação sem data", "valor liquidado sem data de liquidação informada", vl)
        if vl > ZERO and not d["nf"]:
            add(d, "liquidação sem nota fiscal", "liquidação registrada sem documento fiscal informado "
                "(Lei 4.320/1964, art. 63, § 2º)", vl)
    return achados


def consolidar(receitas: list, despesas: list) -> tuple:
    fontes = {}

    def nova():
        return {"recebido_bruto": ZERO, "devolvido": ZERO, "rendimentos": ZERO, "recebido_liquido": ZERO,
                "empenhado": ZERO, "liquidado": ZERO, "pago": ZERO, "qtd_receitas": 0, "qtd_empenhos": 0}

    meses = {}

    def nova_mes():
        return {"recebido": ZERO, "empenhado": ZERO, "liquidado": ZERO, "pago": ZERO}

    for r in receitas:
        f = fontes.setdefault(r["fonte"], nova())
        f["qtd_receitas"] += 1
        if r["valor"] < 0:
            f["devolvido"] += -r["valor"]
        else:
            f["recebido_bruto"] += r["valor"]
            if r["tipo"] == "rendimento":
                f["rendimentos"] += r["valor"]
        f["recebido_liquido"] += r["valor"]
        meses.setdefault((r["fonte"], r["mes"]), nova_mes())["recebido"] += r["valor"]

    for d in despesas:
        f = fontes.setdefault(d["fonte"], nova())
        f["qtd_empenhos"] += 1
        f["empenhado"] += d["valor_empenhado"]
        f["liquidado"] += d["valor_liquidado"]
        f["pago"] += d["valor_pago"]
        meses.setdefault((d["fonte"], chave_mes(d["data_empenho"])), nova_mes())["empenhado"] += d["valor_empenhado"]
        if d["valor_liquidado"] > ZERO:
            chave = chave_mes(d["data_liquidacao"]) if d["data_liquidacao"] else "sem data"
            meses.setdefault((d["fonte"], chave), nova_mes())["liquidado"] += d["valor_liquidado"]
        if d["valor_pago"] > ZERO:
            chave = chave_mes(d["data_pagamento"]) if d["data_pagamento"] else "sem data"
            meses.setdefault((d["fonte"], chave), nova_mes())["pago"] += d["valor_pago"]

    for f in fontes.values():
        f["saldo_financeiro"] = f["recebido_liquido"] - f["pago"]
        f["a_empenhar"] = f["recebido_liquido"] - f["empenhado"]
        f["a_liquidar"] = f["empenhado"] - f["liquidado"]
        f["a_pagar"] = f["liquidado"] - f["pago"]

    linhas_mes = []
    for fonte in sorted(fontes):
        acumulado_rec, acumulado_emp, acumulado_pago = ZERO, ZERO, ZERO
        chaves = [m for (fo, m) in meses if fo == fonte]
        chaves.sort(key=lambda c: (c == "sem data", ordem_mes(c) if c != "sem data" else (9999, 99)))
        for m in chaves:
            v = meses[(fonte, m)]
            acumulado_rec += v["recebido"]
            acumulado_emp += v["empenhado"]
            acumulado_pago += v["pago"]
            linhas_mes.append({"fonte": fonte, "mes": m, "recebido": v["recebido"], "empenhado": v["empenhado"],
                               "liquidado": v["liquidado"], "pago": v["pago"],
                               "saldo_financeiro_acumulado": acumulado_rec - acumulado_pago,
                               "saldo_orcamentario_acumulado": acumulado_rec - acumulado_emp})
    return fontes, linhas_mes


def restos_a_pagar(despesas: list, corte: date) -> dict:
    """Restos a pagar na data de corte (Lei 4.320/1964, art. 36): não processados e processados."""
    por_fonte = {}
    itens = []
    for d in despesas:
        if d["data_empenho"] > corte:
            continue
        liq_c = d["valor_liquidado"] if (d["data_liquidacao"] and d["data_liquidacao"] <= corte) else ZERO
        pago_c = d["valor_pago"] if (d["data_pagamento"] and d["data_pagamento"] <= corte) else ZERO
        consumido = max(liq_c, pago_c)
        nao_proc = d["valor_empenhado"] - consumido
        proc = liq_c - pago_c
        if nao_proc < TOLERANCIA:
            nao_proc = ZERO
        if proc < TOLERANCIA:
            proc = ZERO
        if nao_proc == ZERO and proc == ZERO:
            continue
        f = por_fonte.setdefault(d["fonte"], {"nao_processados": ZERO, "processados": ZERO, "itens": 0})
        f["nao_processados"] += nao_proc
        f["processados"] += proc
        f["itens"] += 1
        itens.append({"empenho": d["empenho"], "fonte": d["fonte"], "credor": d["credor"],
                      "nao_processados": nao_proc, "processados": proc,
                      "situacao_posterior": situacao_posterior(d, corte)})
    return {"por_fonte": por_fonte, "itens": itens}


def situacao_posterior(d: dict, corte: date) -> str:
    partes = []
    if d["data_liquidacao"] and d["data_liquidacao"] > corte:
        partes.append(f"liquidado em {fmt_data(d['data_liquidacao'])}")
    if d["data_pagamento"] and d["data_pagamento"] > corte:
        partes.append(f"pago em {fmt_data(d['data_pagamento'])}")
    if not partes:
        partes.append("sem liquidação ou pagamento posterior nos dados")
    return "; ".join(partes)


def alertas_por_fonte(fontes: dict, linhas_mes: list) -> list:
    """Sinais no nível da fonte: gasto acima do recebido e saldo acumulado negativo (LRF, art. 8º, parágrafo único)."""
    alertas = []
    for fonte, f in sorted(fontes.items()):
        if f["recebido_liquido"] <= ZERO and f["empenhado"] > ZERO:
            alertas.append({"fonte": fonte, "tipo": "fonte sem receita registrada",
                            "detalhe": f"empenhado {fmt_brl(f['empenhado'])} sem nenhum ingresso na fonte; conferir classificação da fonte ou receita não informada",
                            "valor": f["empenhado"]})
            continue
        if f["pago"] > f["recebido_liquido"] + TOLERANCIA:
            alertas.append({"fonte": fonte, "tipo": "pagamentos superam o recebido líquido",
                            "detalhe": f"pago {fmt_brl(f['pago'])} contra recebido líquido {fmt_brl(f['recebido_liquido'])}; "
                                       "indício de pagamento com recurso de outra fonte ou de classificação incorreta",
                            "valor": f["pago"] - f["recebido_liquido"]})
        elif f["empenhado"] > f["recebido_liquido"] + TOLERANCIA:
            alertas.append({"fonte": fonte, "tipo": "empenhos superam o recebido líquido",
                            "detalhe": f"empenhado {fmt_brl(f['empenhado'])} contra recebido líquido {fmt_brl(f['recebido_liquido'])}",
                            "valor": f["empenhado"] - f["recebido_liquido"]})
        negativos = [m for m in linhas_mes if m["fonte"] == fonte and m["mes"] != "sem data"
                     and m["saldo_financeiro_acumulado"] < -TOLERANCIA]
        if negativos:
            alertas.append({"fonte": fonte, "tipo": "saldo financeiro acumulado negativo",
                            "detalhe": f"a partir de {negativos[0]['mes']}: pagamento anterior ao ingresso ou acima dele na fonte",
                            "valor": -min(m["saldo_financeiro_acumulado"] for m in negativos)})
        if f["a_pagar"] < -TOLERANCIA:
            alertas.append({"fonte": fonte, "tipo": "pago acima do liquidado na fonte",
                            "detalhe": "'a pagar' negativo decorre de pagamento sem liquidação ou superior à liquidação (ver inconsistências por empenho)",
                            "valor": -f["a_pagar"]})
    return alertas


def sanidade(receitas: list, despesas: list, fontes: dict, linhas_mes: list) -> dict:
    testes = []
    total_rec = sum((r["valor"] for r in receitas), ZERO)
    total_emp = sum((d["valor_empenhado"] for d in despesas), ZERO)
    total_liq = sum((d["valor_liquidado"] for d in despesas), ZERO)
    total_pago = sum((d["valor_pago"] for d in despesas), ZERO)
    pares = [("recebido líquido", total_rec, sum((f["recebido_liquido"] for f in fontes.values()), ZERO)),
             ("empenhado", total_emp, sum((f["empenhado"] for f in fontes.values()), ZERO)),
             ("liquidado", total_liq, sum((f["liquidado"] for f in fontes.values()), ZERO)),
             ("pago", total_pago, sum((f["pago"] for f in fontes.values()), ZERO))]
    for nome, total, soma in pares:
        ok = abs(total - soma) <= TOLERANCIA
        testes.append({"teste": f"soma por fonte fecha com o total ({nome})", "total": fmt_brl(total),
                       "soma_por_fonte": fmt_brl(soma), "ok": ok})
    for fonte, f in fontes.items():
        for campo_m, campo_f in (("recebido", "recebido_liquido"), ("empenhado", "empenhado"),
                                 ("liquidado", "liquidado"), ("pago", "pago")):
            soma_m = sum((lm[campo_m] for lm in linhas_mes if lm["fonte"] == fonte), ZERO)
            ok = abs(soma_m - f[campo_f]) <= TOLERANCIA
            testes.append({"teste": f"soma mensal fecha com a fonte {fonte} ({campo_m})",
                           "total": fmt_brl(f[campo_f]), "soma_por_mes": fmt_brl(soma_m), "ok": ok})
    qtd = sum(f["qtd_receitas"] + f["qtd_empenhos"] for f in fontes.values())
    testes.append({"teste": "quantidade de registros por fonte fecha com os arquivos",
                   "total": str(len(receitas) + len(despesas)), "soma_por_fonte": str(qtd),
                   "ok": qtd == len(receitas) + len(despesas)})
    falhos = [t["teste"] for t in testes if not t["ok"]]
    if falhos:
        raise ValueError("sanidade falhou: " + "; ".join(falhos))
    return {"ok": True, "testes": testes,
            "totais": {"recebido_liquido": total_rec, "empenhado": total_emp, "liquidado": total_liq, "pago": total_pago}}


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Conciliação por fonte de recursos: recebido x empenhado, liquidado e pago, por mês, "
                    "com restos a pagar, devoluções e inconsistências nos estágios da despesa.")
    p.add_argument("--receitas", required=True, help="CSV de receitas por fonte (data;fonte;origem;documento;valor)")
    p.add_argument("--despesas", required=True, help="CSV de despesas por empenho (ver docstring para o layout)")
    p.add_argument("--data-corte", help="Data de corte única para restos a pagar (dd/mm/aaaa); padrão: 31/12 de cada exercício presente nos dados")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="Grava os quadros da conciliação em Markdown")
    p.add_argument("--csv", help="Grava o quadro por fonte e mês em CSV (separador ponto e vírgula)")
    return p


def exercicios(despesas: list) -> list:
    anos = set()
    for d in despesas:
        for campo in ("data_empenho", "data_liquidacao", "data_pagamento"):
            if d[campo]:
                anos.add(d[campo].year)
    return [date(a, 12, 31) for a in sorted(anos)]


def serializar(obj):
    if isinstance(obj, Decimal):
        return fmt_brl(obj)
    if isinstance(obj, date):
        return fmt_data(obj)
    if isinstance(obj, dict):
        return {k: serializar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serializar(v) for v in obj]
    return obj


def gerar_md(res: dict) -> str:
    L = []
    L.append("# Conciliação por fonte de recursos")
    L.append("")
    L.append(f"Arquivos: receitas `{res['premissas']['arquivo_receitas']}`; despesas `{res['premissas']['arquivo_despesas']}`. "
             f"Regra de mês: {res['premissas']['regra_de_mes']}. Valores em R$, nominais. Script `conciliacao_fonte_recurso.py` v{VERSAO}.")
    L.append("")
    L.append("## 1. Resumo por fonte")
    L.append("")
    L.append("| Fonte | Recebido bruto | Devolvido | Recebido líquido | Empenhado | Liquidado | Pago | Saldo financeiro | A empenhar | A liquidar | A pagar |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for f in res["por_fonte"]:
        L.append(f"| {f['fonte']} | {f['recebido_bruto']} | {f['devolvido']} | {f['recebido_liquido']} | {f['empenhado']} | "
                 f"{f['liquidado']} | {f['pago']} | {f['saldo_financeiro']} | {f['a_empenhar']} | {f['a_liquidar']} | {f['a_pagar']} |")
    t = res["totais"]
    L.append(f"| Total | {t['recebido_bruto']} | {t['devolvido']} | {t['recebido_liquido']} | {t['empenhado']} | {t['liquidado']} | "
             f"{t['pago']} | {t['saldo_financeiro']} | {t['a_empenhar']} | {t['a_liquidar']} | {t['a_pagar']} |")
    L.append("")
    if res["fontes_sem_receita"]:
        L.append("Fontes com despesa e sem receita registrada: " + ", ".join(res["fontes_sem_receita"]) + ".")
        L.append("")
    if res["alertas_por_fonte"]:
        L.append("| Fonte | Alerta | Detalhe | Valor |")
        L.append("|---|---|---|---:|")
        for a in res["alertas_por_fonte"]:
            L.append(f"| {a['fonte']} | {a['tipo']} | {a['detalhe']} | {a['valor']} |")
        L.append("")
    L.append("## 2. Por fonte e mês")
    L.append("")
    L.append("| Fonte | Mês | Recebido | Empenhado | Liquidado | Pago | Saldo financeiro acumulado | Saldo orçamentário acumulado |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for m in res["por_fonte_mes"]:
        L.append(f"| {m['fonte']} | {m['mes']} | {m['recebido']} | {m['empenhado']} | {m['liquidado']} | {m['pago']} | "
                 f"{m['saldo_financeiro_acumulado']} | {m['saldo_orcamentario_acumulado']} |")
    L.append("")
    L.append("## 3. Restos a pagar")
    L.append("")
    for corte, bloco in res["restos_a_pagar"].items():
        L.append(f"Posição em {corte}:")
        L.append("")
        L.append("| Fonte | Não processados | Processados | Empenhos |")
        L.append("|---|---:|---:|---:|")
        if not bloco["por_fonte"]:
            L.append("| (nenhum) | 0,00 | 0,00 | 0 |")
        for fonte, v in bloco["por_fonte"].items():
            L.append(f"| {fonte} | {v['nao_processados']} | {v['processados']} | {v['itens']} |")
        L.append("")
        if bloco["itens"]:
            L.append("| Empenho | Fonte | Credor | Não processados | Processados | Situação posterior |")
            L.append("|---|---|---|---:|---:|---|")
            for i in bloco["itens"]:
                L.append(f"| {i['empenho']} | {i['fonte']} | {i['credor']} | {i['nao_processados']} | {i['processados']} | {i['situacao_posterior']} |")
            L.append("")
    L.append("## 4. Devoluções e rendimentos")
    L.append("")
    L.append("| Tipo | Data | Fonte | Documento | Origem | Valor |")
    L.append("|---|---|---|---|---|---:|")
    for r in res["devolucoes"] + res["rendimentos"]:
        L.append(f"| {r['tipo']} | {r['data']} | {r['fonte']} | {r['documento']} | {r['origem']} | {r['valor']} |")
    if not res["devolucoes"] and not res["rendimentos"]:
        L.append("| (nenhum) | | | | | |")
    L.append("")
    L.append("## 5. Inconsistências nos estágios da despesa e na fonte")
    L.append("")
    L.append("| Empenho | Fonte | Credor | Tipo | Detalhe | Valor |")
    L.append("|---|---|---|---|---|---:|")
    for a in res["inconsistencias"]:
        L.append(f"| {a['empenho']} | {a['fonte']} | {a['credor']} | {a['tipo']} | {a['detalhe']} | {a['valor']} |")
    if not res["inconsistencias"]:
        L.append("| (nenhuma) | | | | | |")
    L.append("")
    L.append("| Tipo | Quantidade | Valor envolvido |")
    L.append("|---|---:|---:|")
    for tipo, v in res["resumo_inconsistencias"].items():
        L.append(f"| {tipo} | {v['quantidade']} | {v['valor']} |")
    L.append("")
    L.append("## 6. Sanidade")
    L.append("")
    L.append(f"Resultado: {'OK' if res['sanidade']['ok'] else 'FALHOU'}; {len(res['sanidade']['testes'])} testes "
             "(soma por fonte e soma por mês fecham com os totais; quantidade de registros fecha com os arquivos).")
    L.append("")
    L.append("Os valores são nominais nas datas dos documentos; atualização monetária, quando determinada, é objeto da skill `atualizacao-monetaria`. "
             "A qualificação jurídica das inconsistências é do juízo.")
    return "\n".join(L) + "\n"


def main():
    parser = montar_parser()
    args = parser.parse_args()
    try:
        receitas = processar_receitas(ler_csv(args.receitas, COLUNAS_RECEITAS, "receitas"))
        despesas = processar_despesas(ler_csv(args.despesas, COLUNAS_DESPESAS, "despesas"))
        fontes_receita = {r["fonte"] for r in receitas}
        inconsistencias = testar_estagios(despesas, fontes_receita)
        fontes, linhas_mes = consolidar(receitas, despesas)
        san = sanidade(receitas, despesas, fontes, linhas_mes)
        cortes = [parse_data(args.data_corte, "data-corte")] if args.data_corte else exercicios(despesas)
        rap = {fmt_data(c): restos_a_pagar(despesas, c) for c in cortes}
        fontes_sem_receita = sorted(f for f in fontes if f not in fontes_receita)
        alertas_fonte = alertas_por_fonte(fontes, linhas_mes)

        totais = {k: sum((f[k] for f in fontes.values()), ZERO) for k in
                  ("recebido_bruto", "devolvido", "rendimentos", "recebido_liquido", "empenhado", "liquidado", "pago",
                   "saldo_financeiro", "a_empenhar", "a_liquidar", "a_pagar")}
        totais["qtd_receitas"] = len(receitas)
        totais["qtd_empenhos"] = len(despesas)

        resumo_inc = {}
        for a in inconsistencias:
            b = resumo_inc.setdefault(a["tipo"], {"quantidade": 0, "valor": ZERO})
            b["quantidade"] += 1
            b["valor"] += a["valor"]

        memoria = [
            f"1. Lidos {len(receitas)} registros de receita e {len(despesas)} empenhos; números aceitos em padrão brasileiro e técnico; datas dd/mm/aaaa.",
            "2. Receita com valor negativo tratada como devolução; origem contendo 'rendimento' tratada como rendimento de aplicação (ambas somam no recebido líquido).",
            "3. Por fonte: recebido bruto, devolvido, recebido líquido, empenhado, liquidado, pago; saldo financeiro = recebido líquido - pago; "
            "a empenhar = recebido líquido - empenhado; a liquidar = empenhado - liquidado; a pagar = liquidado - pago.",
            "4. Por fonte e mês: receita pelo mês da data; empenho pelo mês da data de empenho; liquidação e pagamento pelos respectivos meses; "
            "saldos acumulados em ordem cronológica.",
            "5. Testes dos estágios (Lei 4.320/1964, arts. 60, 62 e 63): pagamento sem liquidação, liquidação superior ao empenho, pagamento superior à liquidação, "
            "liquidação ou NF anterior ao empenho, pagamento anterior à liquidação, datas e documento fiscal ausentes; fonte sem receita registrada.",
            "6. Restos a pagar (Lei 4.320/1964, art. 36) em cada corte: não processados = empenhado - maior entre liquidado e pago até o corte; "
            "processados = liquidado até o corte - pago até o corte; empenhos posteriores ao corte excluídos.",
            "7. Alertas por fonte (LRF, art. 8º, parágrafo único): pagamentos ou empenhos acima do recebido líquido, saldo acumulado negativo, "
            "pago acima do liquidado.",
            "8. Sanidade: soma por fonte e soma por mês fecham com os totais gerais; quantidade de registros fecha com os arquivos. Falha interrompe a execução.",
            "9. Arredondamento apenas na apresentação (ROUND_HALF_UP, 2 casas); cálculo em Decimal.",
        ]

        resultado = {
            "script": "conciliacao_fonte_recurso.py", "skill": SKILL, "versao": VERSAO,
            "premissas": {
                "arquivo_receitas": args.receitas, "arquivo_despesas": args.despesas,
                "regra_de_mes": "receita pela data do ingresso; empenho, liquidação e pagamento pelas respectivas datas",
                "cortes_restos_a_pagar": [fmt_data(c) for c in cortes],
                "devolucao": "receita com valor negativo", "rendimento": "origem contendo a palavra rendimento",
                "tolerancia": "0,005 (meio centavo)", "valores": "nominais, sem atualização",
            },
            "locale": LOCALE, "arredondamento": ARREDONDAMENTO,
            "totais": totais,
            "por_fonte": [dict(fonte=f, **v) for f, v in sorted(fontes.items())],
            "fontes_sem_receita": fontes_sem_receita,
            "alertas_por_fonte": alertas_fonte,
            "por_fonte_mes": linhas_mes,
            "restos_a_pagar": rap,
            "devolucoes": [r for r in receitas if r["tipo"] == "devolução"],
            "rendimentos": [r for r in receitas if r["tipo"] == "rendimento"],
            "inconsistencias": inconsistencias,
            "resumo_inconsistencias": resumo_inc,
            "sanidade": {"ok": san["ok"], "testes": san["testes"]},
            "memoria": memoria,
        }
        saida = serializar(resultado)
        for r in saida["devolucoes"] + saida["rendimentos"]:
            r.pop("linha", None)
            r.pop("mes", None)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto, encoding="utf-8")
            print(f"JSON gravado em {args.saida}")
        else:
            print(texto)
        if args.md:
            Path(args.md).write_text(gerar_md(saida), encoding="utf-8")
            print(f"Markdown gravado em {args.md}")
        if args.csv:
            with Path(args.csv).open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["fonte", "mes", "recebido", "empenhado", "liquidado", "pago",
                            "saldo_financeiro_acumulado", "saldo_orcamentario_acumulado"])
                for m in saida["por_fonte_mes"]:
                    w.writerow([m["fonte"], m["mes"], m["recebido"], m["empenhado"], m["liquidado"], m["pago"],
                                m["saldo_financeiro_acumulado"], m["saldo_orcamentario_acumulado"]])
            print(f"CSV gravado em {args.csv}")
        t = saida["totais"]
        print(f"Conciliação: {t['qtd_receitas']} receitas e {t['qtd_empenhos']} empenhos em {len(fontes)} fontes; "
              f"recebido líquido R$ {t['recebido_liquido']}, empenhado R$ {t['empenhado']}, pago R$ {t['pago']}, "
              f"saldo financeiro R$ {t['saldo_financeiro']}; {len(inconsistencias)} inconsistências por empenho; "
              f"{len(alertas_fonte)} alertas por fonte; sanidade OK.", file=sys.stderr)
    except ValueError as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
