#!/usr/bin/env python3
"""
Matriz de testes despesa a despesa em prestação de contas de recursos da covid-19:
aderência ao objeto da fonte, processo de contratação (Lei 13.979/2020, art. 4º e
seguintes; Lei 14.133/2021, arts. 23, 72 e 75, VIII), pesquisa de preços, contrato,
nota fiscal, atesto, entrega ou prestação comprovada, estágios da despesa
(Lei 4.320/1964, arts. 60, 62 e 63), preço contra referência, fracionamento por
credor na janela declarada, fornecedor constituído há pouco tempo e fornecedor
sancionado. Classifica cada despesa, totaliza por classe e por fonte, lista os
sinais de alerta e sugere amostra quando o universo supera o limite declarado.
Parte da skill: pericia-prestacao-contas-covid-saude

O script descreve fatos contábeis e documentais. A qualificação jurídica
(improbidade, dolo, dano) é do juízo; a tolerância de sobrepreço, a janela de
fracionamento e o prazo de fornecedor novo são premissas declaradas, não normas.

Uso:
    python3 scripts/matriz_despesas_covid.py --despesas assets/exemplo_despesas.csv \
        --saida matriz.json --md matriz.md --csv matriz.csv
    python3 scripts/matriz_despesas_covid.py --despesas despesas.csv --tolerancia-sobrepreco 15 \
        --janela-fracionamento 30 --dias-fornecedor-novo 180 --amostra-limite 10

Colunas obrigatórias (separador ponto e vírgula): empenho;data_empenho;fonte;credor;cnpj;objeto;
    valor_empenhado;valor_liquidado;valor_pago;aderencia_objeto (S/N/D);processo_contratacao (S/N);
    pesquisa_precos (S/N);contrato (S/N);atesto (S/N);entrega_comprovada (S/N)
Colunas opcionais: modalidade;processo;data_liquidacao;data_pagamento;nf;data_nf;quantidade;
    preco_unitario;preco_referencia;data_constituicao_fornecedor;sancao_ceis (S/N)
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
CEM = Decimal("100")

COLUNAS_OBRIGATORIAS = ["empenho", "data_empenho", "fonte", "credor", "cnpj", "objeto", "valor_empenhado",
                        "valor_liquidado", "valor_pago", "aderencia_objeto", "processo_contratacao",
                        "pesquisa_precos", "contrato", "atesto", "entrega_comprovada"]

# Ordem de severidade: a classe da despesa é o achado mais grave encontrado.
CLASSES = ["desvio de finalidade", "sem comprovação", "sobrepreço a apurar", "aderência a esclarecer",
           "irregularidade formal", "regular"]
SEVERIDADE = {c: i for i, c in enumerate(CLASSES)}

DESCRICAO_GENERICA = {
    "ADERENCIA_N": "objeto estranho à finalidade da fonte",
    "ADERENCIA_D": "aderência ao objeto da fonte a esclarecer",
    "ENTREGA_N": "sem evidência de entrega ou prestação",
    "NF_AUSENTE": "liquidação ou pagamento sem documento fiscal",
    "ATESTO_N": "sem atesto do recebimento",
    "PROCESSO_N": "sem processo de contratação formalizado",
    "PESQUISA_N": "sem pesquisa ou estimativa de preços",
    "CONTRATO_N": "sem contrato ou instrumento substitutivo",
    "PAGO_SEM_LIQ": "pagamento sem liquidação",
    "LIQ_MAIOR_EMP": "liquidação superior ao empenho",
    "NF_ANTES_EMP": "nota fiscal anterior ao empenho",
    "LIQ_ANTES_EMP": "liquidação anterior ao empenho",
    "PAG_ANTES_LIQ": "pagamento anterior à liquidação",
    "SOBREPRECO": "preço unitário acima da referência além da tolerância",
    "FORNECEDOR_NOVO": "fornecedor constituído há menos dias que o parâmetro",
    "FORNECEDOR_DATA": "data de constituição do fornecedor posterior ao empenho",
    "FORNECEDOR_SANCIONADO": "fornecedor com sanção registrada (CEIS/CNEP)",
    "FRACIONAMENTO": "empenhos ao mesmo credor dentro da janela",
}


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


def parse_num_opcional(texto):
    if texto is None or str(texto).strip() == "":
        return None
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


def fmt_pct(valor: Decimal) -> str:
    return fmt_num(valor, 2) + "%"


def fmt_quantidade(valor):
    """Quantidade inteira sem casas decimais; fracionária com duas casas."""
    if valor is None:
        return ""
    if valor == valor.to_integral_value():
        return fmt_num(valor, 0)
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


def flag(valor: str, campo: str, ctx: str, permitidos=("S", "N")) -> str:
    v = (valor or "").strip().upper()
    if v == "" and campo in ("sancao_ceis",):
        return "N"
    if v not in permitidos:
        raise ValueError(f"{ctx}: coluna {campo} deve ser {'/'.join(permitidos)}, recebido {valor!r}")
    return v


def ler_csv(caminho: str) -> list:
    p = Path(caminho)
    if not p.exists():
        raise ValueError(f"arquivo de despesas não encontrado: {caminho}")
    with p.open(encoding="utf-8-sig", newline="") as fh:
        leitor = csv.DictReader(fh, delimiter=";")
        if leitor.fieldnames is None:
            raise ValueError(f"arquivo de despesas vazio: {caminho}")
        campos = [c.strip() for c in leitor.fieldnames]
        faltam = [c for c in COLUNAS_OBRIGATORIAS if c not in campos]
        if faltam:
            raise ValueError("arquivo de despesas sem as colunas obrigatórias: " + ", ".join(faltam))
        linhas = []
        for numero, linha in enumerate(leitor, start=2):
            limpa = {(k or "").strip(): (v or "").strip() for k, v in linha.items() if k is not None}
            if not any(limpa.values()):
                continue
            limpa["_linha"] = numero
            linhas.append(limpa)
    if not linhas:
        raise ValueError(f"arquivo de despesas sem registros: {caminho}")
    return linhas


def processar(linhas: list) -> list:
    despesas = []
    vistos = set()
    for r in linhas:
        ctx = f"despesas, linha {r['_linha']}"
        emp = r["empenho"]
        if not emp:
            raise ValueError(f"{ctx}: número de empenho vazio")
        if emp in vistos:
            raise ValueError(f"{ctx}: empenho {emp} repetido")
        vistos.add(emp)
        d = {
            "linha": r["_linha"], "empenho": emp, "data_empenho": parse_data(r["data_empenho"], f"{ctx}, data_empenho"),
            "fonte": r["fonte"], "credor": r["credor"], "cnpj": r["cnpj"], "cnpj_digitos": "".join(ch for ch in r["cnpj"] if ch.isdigit()),
            "objeto": r["objeto"], "modalidade": r.get("modalidade", ""), "processo": r.get("processo", ""),
            "valor_empenhado": parse_num(r["valor_empenhado"]),
            "valor_liquidado": parse_num_opcional(r["valor_liquidado"]) or ZERO,
            "valor_pago": parse_num_opcional(r["valor_pago"]) or ZERO,
            "data_liquidacao": parse_data_opcional(r.get("data_liquidacao"), f"{ctx}, data_liquidacao"),
            "data_pagamento": parse_data_opcional(r.get("data_pagamento"), f"{ctx}, data_pagamento"),
            "nf": r.get("nf", ""), "data_nf": parse_data_opcional(r.get("data_nf"), f"{ctx}, data_nf"),
            "aderencia_objeto": flag(r["aderencia_objeto"], "aderencia_objeto", ctx, ("S", "N", "D")),
            "processo_contratacao": flag(r["processo_contratacao"], "processo_contratacao", ctx),
            "pesquisa_precos": flag(r["pesquisa_precos"], "pesquisa_precos", ctx),
            "contrato": flag(r["contrato"], "contrato", ctx),
            "atesto": flag(r["atesto"], "atesto", ctx),
            "entrega_comprovada": flag(r["entrega_comprovada"], "entrega_comprovada", ctx),
            "quantidade": parse_num_opcional(r.get("quantidade")),
            "preco_unitario": parse_num_opcional(r.get("preco_unitario")),
            "preco_referencia": parse_num_opcional(r.get("preco_referencia")),
            "data_constituicao_fornecedor": parse_data_opcional(r.get("data_constituicao_fornecedor"), f"{ctx}, data_constituicao_fornecedor"),
            "sancao_ceis": flag(r.get("sancao_ceis", ""), "sancao_ceis", ctx),
        }
        if d["valor_empenhado"] <= ZERO:
            raise ValueError(f"{ctx}: empenho {emp} com valor empenhado não positivo")
        if not d["fonte"]:
            raise ValueError(f"{ctx}: empenho {emp} sem fonte de recursos")
        despesas.append(d)
    return despesas


def testar_despesa(d: dict, tol: Decimal, dias_novo: int) -> None:
    """Aplica os testes individuais e grava achados, classe e base de quantificação na própria despesa."""
    achados = []

    def add(codigo, classe, descricao, valor=ZERO):
        achados.append({"codigo": codigo, "classe": classe, "descricao": descricao, "valor": valor})

    executada = d["valor_liquidado"] > ZERO or d["valor_pago"] > ZERO
    base_dano = d["valor_pago"] if d["valor_pago"] > ZERO else ZERO

    # 1. Aderência ao objeto permitido pela fonte
    if d["aderencia_objeto"] == "N":
        add("ADERENCIA_N", "desvio de finalidade",
            "objeto estranho à finalidade da fonte (LRF, art. 8º, parágrafo único; LC 141/2012, arts. 2º a 4º)", base_dano)
    elif d["aderencia_objeto"] == "D":
        add("ADERENCIA_D", "aderência a esclarecer",
            "aderência ao objeto da fonte duvidosa; exigir justificativa do ente e vínculo com o plano de contingência", ZERO)

    # 2. Comprovação da entrega e da liquidação (somente despesa liquidada ou paga)
    if executada:
        if d["entrega_comprovada"] == "N":
            add("ENTREGA_N", "sem comprovação",
                "sem evidência de entrega do bem ou da prestação do serviço (Lei 4.320/1964, art. 63, § 2º, III)", base_dano)
        if not d["nf"]:
            add("NF_AUSENTE", "sem comprovação", "sem documento fiscal que lastreie a liquidação (Lei 4.320/1964, art. 63)", base_dano)
        if d["atesto"] == "N":
            add("ATESTO_N", "irregularidade formal", "sem atesto do recebimento pelo fiscal ou responsável (Lei 4.320/1964, art. 63)")
    else:
        add("NAO_EXECUTADA", "regular", "empenho sem liquidação e sem pagamento nos dados: testes de comprovação aguardam a execução")

    # 3. Processo de contratação
    if d["processo_contratacao"] == "N":
        add("PROCESSO_N", "irregularidade formal",
            "sem processo de contratação formalizado (Lei 13.979/2020, art. 4º; Lei 14.133/2021, art. 72)")
    if d["pesquisa_precos"] == "N":
        add("PESQUISA_N", "irregularidade formal",
            "sem pesquisa ou estimativa de preços (Lei 14.133/2021, arts. 23 e 72, II; Lei 13.979/2020, art. 4º-E, § 2º, exigia justificativa para dispensá-la)")
    if d["contrato"] == "N":
        add("CONTRATO_N", "irregularidade formal", "sem contrato ou instrumento substitutivo identificado")

    # 4. Estágios da despesa
    if d["valor_pago"] > ZERO and d["valor_liquidado"] == ZERO:
        add("PAGO_SEM_LIQ", "irregularidade formal", "pagamento sem liquidação registrada (Lei 4.320/1964, art. 62)")
    if d["valor_liquidado"] > d["valor_empenhado"] + TOLERANCIA:
        add("LIQ_MAIOR_EMP", "irregularidade formal",
            f"liquidação {fmt_brl(d['valor_liquidado'])} superior ao empenho {fmt_brl(d['valor_empenhado'])} (Lei 4.320/1964, art. 60)",
            d["valor_liquidado"] - d["valor_empenhado"])
    if d["data_nf"] and d["data_nf"] < d["data_empenho"]:
        add("NF_ANTES_EMP", "irregularidade formal",
            f"NF de {fmt_data(d['data_nf'])} anterior ao empenho de {fmt_data(d['data_empenho'])} (Lei 4.320/1964, art. 60)")
    if d["data_liquidacao"] and d["data_liquidacao"] < d["data_empenho"]:
        add("LIQ_ANTES_EMP", "irregularidade formal",
            f"liquidação em {fmt_data(d['data_liquidacao'])} anterior ao empenho de {fmt_data(d['data_empenho'])} (Lei 4.320/1964, art. 60)")
    if d["data_pagamento"] and d["data_liquidacao"] and d["data_pagamento"] < d["data_liquidacao"]:
        add("PAG_ANTES_LIQ", "irregularidade formal", "pagamento anterior à liquidação (Lei 4.320/1964, arts. 62 e 63)")

    # 5. Preço contra referência
    d["sobrepreco_pct"] = None
    d["sobrepreco_valor"] = ZERO
    if d["preco_unitario"] is not None and d["preco_referencia"] is not None:
        if d["preco_referencia"] <= ZERO:
            raise ValueError(f"empenho {d['empenho']}: preço de referência deve ser positivo")
        pct = (d["preco_unitario"] / d["preco_referencia"] - 1) * CEM
        d["sobrepreco_pct"] = pct
        qtd = d["quantidade"] if d["quantidade"] is not None else Decimal(1)
        if pct > tol:
            d["sobrepreco_valor"] = (d["preco_unitario"] - d["preco_referencia"]) * qtd
            add("SOBREPRECO", "sobrepreço a apurar",
                f"preço unitário {fmt_brl(d['preco_unitario'])} supera a referência {fmt_brl(d['preco_referencia'])} em {fmt_pct(pct)} "
                f"(tolerância declarada {fmt_pct(tol)}); diferença x quantidade = {fmt_brl(d['sobrepreco_valor'])}",
                d["sobrepreco_valor"])
        elif pct > ZERO:
            add("PRECO_ACIMA_TOL", "regular",
                f"preço unitário {fmt_pct(pct)} acima da referência, dentro da tolerância declarada de {fmt_pct(tol)}")
    elif d["preco_unitario"] is not None and d["preco_referencia"] is None:
        add("SEM_REFERENCIA", "regular", "sem preço de referência informado: teste de preço não aplicado (obter em licitacoes-contratos)")

    # 6. Fornecedor
    d["dias_fornecedor"] = None
    if d["data_constituicao_fornecedor"]:
        dias = (d["data_empenho"] - d["data_constituicao_fornecedor"]).days
        d["dias_fornecedor"] = dias
        if dias < 0:
            add("FORNECEDOR_DATA", "irregularidade formal", "data de constituição do fornecedor posterior ao empenho: conferir cadastro")
        elif dias < dias_novo:
            add("FORNECEDOR_NOVO", "irregularidade formal",
                f"fornecedor constituído {dias} dias antes do empenho (parâmetro declarado: {dias_novo} dias); conferir capacidade operacional e quadro societário")
    if d["sancao_ceis"] == "S":
        add("FORNECEDOR_SANCIONADO", "irregularidade formal",
            "fornecedor com sanção registrada (CEIS/CNEP) na consulta anexada; conferir alcance e data da sanção (Lei 14.133/2021, art. 156; Lei 13.979/2020, art. 4º, § 3º)")

    d["achados"] = achados
    classes_presentes = [a["classe"] for a in achados if a["classe"] != "regular"]
    d["classe"] = min(classes_presentes, key=lambda c: SEVERIDADE[c]) if classes_presentes else "regular"
    if d["classe"] in ("desvio de finalidade", "sem comprovação"):
        d["base_quantificacao"] = base_dano
    elif d["classe"] == "sobrepreço a apurar":
        d["base_quantificacao"] = d["sobrepreco_valor"]
    else:
        d["base_quantificacao"] = ZERO
    d["executada"] = executada


def testar_fracionamento(despesas: list, janela: int) -> list:
    """Agrupa empenhos do mesmo credor (CNPJ) cujas datas se encadeiam dentro da janela declarada."""
    grupos = []
    por_cnpj = {}
    for d in despesas:
        chave = d["cnpj_digitos"] or d["credor"].strip().lower()
        por_cnpj.setdefault(chave, []).append(d)
    for chave, itens in por_cnpj.items():
        itens.sort(key=lambda x: x["data_empenho"])
        atual = [itens[0]]
        for d in itens[1:]:
            if (d["data_empenho"] - atual[-1]["data_empenho"]).days <= janela:
                atual.append(d)
            else:
                if len(atual) > 1:
                    grupos.append(atual)
                atual = [d]
        if len(atual) > 1:
            grupos.append(atual)
    saida = []
    for g in grupos:
        soma = sum((x["valor_empenhado"] for x in g), ZERO)
        for x in g:
            x["achados"].append({"codigo": "FRACIONAMENTO", "classe": "irregularidade formal",
                                 "descricao": f"{len(g)} empenhos ao mesmo credor em {(g[-1]['data_empenho'] - g[0]['data_empenho']).days} dias "
                                              f"(janela declarada {janela}); soma {fmt_brl(soma)}; conferir objeto e modalidade (Lei 14.133/2021, art. 75, § 1º)",
                                 "valor": ZERO})
            if x["classe"] == "regular":
                x["classe"] = "irregularidade formal"
        saida.append({"cnpj": g[0]["cnpj"], "credor": g[0]["credor"], "empenhos": [x["empenho"] for x in g],
                      "datas": [fmt_data(x["data_empenho"]) for x in g], "dias_entre_primeiro_e_ultimo": (g[-1]["data_empenho"] - g[0]["data_empenho"]).days,
                      "modalidades": sorted({x["modalidade"] or "não informada" for x in g}),
                      "objetos": [x["objeto"] for x in g], "soma_empenhada": soma})
    return saida


def sugerir_amostra(despesas: list, limite: int, materialidade: Decimal) -> dict:
    n = len(despesas)
    if n <= limite:
        return {"aplicavel": False, "universo": n, "limite_declarado": limite,
                "criterio": f"universo de {n} despesas igual ou abaixo do limite de {limite}: teste censitário, sem amostragem"}
    total = sum((d["valor_empenhado"] for d in despesas), ZERO)
    selecionados = {}
    for d in despesas:
        if d["classe"] != "regular":
            selecionados[d["empenho"]] = "achado em teste objetivo"
    acumulado = ZERO
    for d in sorted(despesas, key=lambda x: x["valor_empenhado"], reverse=True):
        if total > ZERO and acumulado / total * CEM >= materialidade:
            break
        acumulado += d["valor_empenhado"]
        selecionados.setdefault(d["empenho"], "materialidade (maiores valores)")
    restantes = [d for d in despesas if d["empenho"] not in selecionados]
    passo = max(1, len(restantes) // 10) if restantes else 1
    for i, d in enumerate(sorted(restantes, key=lambda x: x["empenho"])):
        if i % passo == 0:
            selecionados[d["empenho"]] = f"sistemática (1 a cada {passo} dos restantes, ordem do empenho)"
    valor_sel = sum((d["valor_empenhado"] for d in despesas if d["empenho"] in selecionados), ZERO)
    cobertura = (valor_sel / total * CEM) if total > ZERO else ZERO
    return {"aplicavel": True, "universo": n, "limite_declarado": limite, "materialidade_declarada": materialidade,
            "criterio": "todas as despesas com achado + maiores valores até a materialidade declarada + seleção sistemática dos restantes "
                        "(NBC TA 530 por analogia); amostra sugerida, a ser declarada no plano de trabalho",
            "itens": [{"empenho": e, "motivo": m} for e, m in sorted(selecionados.items())],
            "quantidade": len(selecionados), "cobertura_valor": cobertura}


def consolidar(despesas: list) -> dict:
    por_classe = {c: {"quantidade": 0, "empenhado": ZERO, "pago": ZERO, "base_quantificacao": ZERO} for c in CLASSES}
    por_fonte_classe = {}
    por_achado = {}
    for d in despesas:
        c = por_classe[d["classe"]]
        c["quantidade"] += 1
        c["empenhado"] += d["valor_empenhado"]
        c["pago"] += d["valor_pago"]
        c["base_quantificacao"] += d["base_quantificacao"]
        fc = por_fonte_classe.setdefault(d["fonte"], {k: {"quantidade": 0, "pago": ZERO, "base_quantificacao": ZERO} for k in CLASSES})
        fc[d["classe"]]["quantidade"] += 1
        fc[d["classe"]]["pago"] += d["valor_pago"]
        fc[d["classe"]]["base_quantificacao"] += d["base_quantificacao"]
        for a in d["achados"]:
            if a["classe"] == "regular":
                continue
            b = por_achado.setdefault(a["codigo"], {"classe": a["classe"], "quantidade": 0, "pago_envolvido": ZERO,
                                                   "descricao": DESCRICAO_GENERICA.get(a["codigo"], a["descricao"])})
            b["quantidade"] += 1
            b["pago_envolvido"] += d["valor_pago"]
    return {"por_classe": por_classe, "por_fonte_classe": por_fonte_classe, "por_achado": por_achado}


def sanidade(despesas: list, cons: dict) -> dict:
    testes = []
    total_emp = sum((d["valor_empenhado"] for d in despesas), ZERO)
    total_pago = sum((d["valor_pago"] for d in despesas), ZERO)
    total_base = sum((d["base_quantificacao"] for d in despesas), ZERO)
    soma_emp = sum((c["empenhado"] for c in cons["por_classe"].values()), ZERO)
    soma_pago = sum((c["pago"] for c in cons["por_classe"].values()), ZERO)
    soma_base = sum((c["base_quantificacao"] for c in cons["por_classe"].values()), ZERO)
    soma_qtd = sum(c["quantidade"] for c in cons["por_classe"].values())
    testes.append({"teste": "soma por classe fecha com o total empenhado", "total": fmt_brl(total_emp), "soma": fmt_brl(soma_emp), "ok": abs(total_emp - soma_emp) <= TOLERANCIA})
    testes.append({"teste": "soma por classe fecha com o total pago", "total": fmt_brl(total_pago), "soma": fmt_brl(soma_pago), "ok": abs(total_pago - soma_pago) <= TOLERANCIA})
    testes.append({"teste": "soma por classe fecha com a base de quantificação", "total": fmt_brl(total_base), "soma": fmt_brl(soma_base), "ok": abs(total_base - soma_base) <= TOLERANCIA})
    testes.append({"teste": "quantidade por classe fecha com o universo", "total": str(len(despesas)), "soma": str(soma_qtd), "ok": soma_qtd == len(despesas)})
    soma_fc = sum((v["pago"] for fc in cons["por_fonte_classe"].values() for v in fc.values()), ZERO)
    testes.append({"teste": "soma por fonte e classe fecha com o total pago", "total": fmt_brl(total_pago), "soma": fmt_brl(soma_fc), "ok": abs(total_pago - soma_fc) <= TOLERANCIA})
    for d in despesas:
        if d["base_quantificacao"] > d["valor_pago"] + TOLERANCIA and d["classe"] != "sobrepreço a apurar":
            testes.append({"teste": f"base de quantificação do empenho {d['empenho']} não excede o pago", "total": fmt_brl(d["valor_pago"]), "soma": fmt_brl(d["base_quantificacao"]), "ok": False})
    falhos = [t["teste"] for t in testes if not t["ok"]]
    if falhos:
        raise ValueError("sanidade falhou: " + "; ".join(falhos))
    return {"ok": True, "testes": testes, "total_empenhado": total_emp, "total_pago": total_pago, "total_base_quantificacao": total_base}


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
    p = res["premissas"]
    L.append("# Matriz de testes por despesa")
    L.append("")
    L.append(f"Arquivo `{p['arquivo_despesas']}`. Premissas declaradas: tolerância de sobrepreço {p['tolerancia_sobrepreco']}; "
             f"janela de fracionamento {p['janela_fracionamento_dias']} dias; fornecedor novo abaixo de {p['dias_fornecedor_novo']} dias; "
             f"limite para amostragem {p['amostra_limite']} despesas. Valores nominais em R$. Script `matriz_despesas_covid.py` v{VERSAO}.")
    L.append("")
    L.append("## 1. Classificação por despesa")
    L.append("")
    L.append("| Empenho | Fonte | Credor | Objeto | Empenhado | Pago | Classe | Base de quantificação | Achados |")
    L.append("|---|---|---|---|---:|---:|---|---:|---|")
    for d in res["despesas"]:
        ach = "; ".join(f"{a['codigo']}: {a['descricao']}" for a in d["achados"] if a["classe"] != "regular") or "nenhum"
        L.append(f"| {d['empenho']} | {d['fonte']} | {d['credor']} | {d['objeto']} | {d['valor_empenhado']} | {d['valor_pago']} | "
                 f"{d['classe']} | {d['base_quantificacao']} | {ach} |")
    L.append("")
    L.append("## 2. Totais por classe")
    L.append("")
    L.append("| Classe | Quantidade | Empenhado | Pago | Base de quantificação |")
    L.append("|---|---:|---:|---:|---:|")
    for c, v in res["totais"]["por_classe"].items():
        L.append(f"| {c} | {v['quantidade']} | {v['empenhado']} | {v['pago']} | {v['base_quantificacao']} |")
    s = res["sanidade"]
    L.append(f"| Total | {res['universo']} | {s['total_empenhado']} | {s['total_pago']} | {s['total_base_quantificacao']} |")
    L.append("")
    L.append("## 3. Totais por fonte e classe (valor pago)")
    L.append("")
    L.append("| Fonte | " + " | ".join(CLASSES) + " |")
    L.append("|---|" + "---:|" * len(CLASSES))
    for fonte, fc in res["totais"]["por_fonte_classe"].items():
        L.append(f"| {fonte} | " + " | ".join(f"{fc[c]['pago']} ({fc[c]['quantidade']})" for c in CLASSES) + " |")
    L.append("")
    L.append("## 4. Achados por tipo (não exclusivos)")
    L.append("")
    L.append("| Código | Classe | Quantidade | Pago envolvido | Descrição |")
    L.append("|---|---|---:|---:|---|")
    for cod, v in res["totais"]["por_achado"].items():
        L.append(f"| {cod} | {v['classe']} | {v['quantidade']} | {v['pago_envolvido']} | {v['descricao']} |")
    L.append("")
    L.append("## 5. Fracionamento (mesmo credor na janela)")
    L.append("")
    if res["fracionamento"]:
        L.append("| CNPJ | Credor | Empenhos | Datas | Dias | Modalidades | Soma empenhada | Objetos |")
        L.append("|---|---|---|---|---:|---|---:|---|")
        for g in res["fracionamento"]:
            L.append(f"| {g['cnpj']} | {g['credor']} | {', '.join(g['empenhos'])} | {', '.join(g['datas'])} | {g['dias_entre_primeiro_e_ultimo']} | "
                     f"{', '.join(g['modalidades'])} | {g['soma_empenhada']} | {' / '.join(g['objetos'])} |")
    else:
        L.append("Nenhum grupo na janela declarada.")
    L.append("")
    L.append("## 6. Fornecedores: constituição recente e sanção")
    L.append("")
    L.append("| Empenho | Credor | CNPJ | Constituição | Dias até o empenho | Sanção (CEIS/CNEP) |")
    L.append("|---|---|---|---|---:|---|")
    algum = False
    for d in res["despesas"]:
        codigos = {a["codigo"] for a in d["achados"]}
        if codigos & {"FORNECEDOR_NOVO", "FORNECEDOR_SANCIONADO", "FORNECEDOR_DATA"}:
            algum = True
            L.append(f"| {d['empenho']} | {d['credor']} | {d['cnpj']} | {d['data_constituicao_fornecedor']} | "
                     f"{d['dias_fornecedor'] if d['dias_fornecedor'] is not None else ''} | {'sim' if d['sancao_ceis'] == 'S' else 'não'} |")
    if not algum:
        L.append("| (nenhum) | | | | | |")
    L.append("")
    L.append("## 7. Preço contra referência")
    L.append("")
    L.append("| Empenho | Credor | Quantidade | Preço unitário | Referência | Variação | Sobrepreço a apurar |")
    L.append("|---|---|---:|---:|---:|---:|---:|")
    algum = False
    for d in res["despesas"]:
        if d["sobrepreco_pct"] is not None:
            algum = True
            L.append(f"| {d['empenho']} | {d['credor']} | {d['quantidade'] or ''} | {d['preco_unitario']} | {d['preco_referencia']} | "
                     f"{d['sobrepreco_pct']}% | {d['sobrepreco_valor']} |")
    if not algum:
        L.append("| (nenhum com referência) | | | | | | |")
    L.append("")
    L.append("## 8. Amostra sugerida")
    L.append("")
    am = res["amostra_sugerida"]
    L.append(am["criterio"] + ".")
    if am["aplicavel"]:
        L.append("")
        L.append(f"Selecionados {am['quantidade']} de {am['universo']} empenhos; cobertura de {am['cobertura_valor']}% do valor empenhado.")
        L.append("")
        L.append("| Empenho | Motivo |")
        L.append("|---|---|")
        for i in am["itens"]:
            L.append(f"| {i['empenho']} | {i['motivo']} |")
    L.append("")
    L.append("## 9. Sanidade e limites")
    L.append("")
    L.append(f"Sanidade: {'OK' if s['ok'] else 'FALHOU'}; {len(s['testes'])} testes (somas por classe e por fonte fecham com os totais; base de quantificação não excede o pago).")
    L.append("")
    L.append("A classe é o achado mais grave da despesa; os achados por tipo não são exclusivos. Tolerância, janela e prazo de fornecedor novo são premissas declaradas. "
             "O preço de referência vem de pesquisa própria com fonte e data (skill `licitacoes-contratos`). A qualificação jurídica dos achados é do juízo.")
    return "\n".join(L) + "\n"


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Matriz de testes despesa a despesa em prestação de contas de recursos da covid-19.")
    p.add_argument("--despesas", required=True, help="CSV de despesas com as colunas de teste (ver docstring)")
    p.add_argument("--tolerancia-sobrepreco", default="20", help="Variação máxima do preço unitário sobre a referência, em %% (padrão 20)")
    p.add_argument("--janela-fracionamento", type=int, default=30, help="Janela em dias para agrupar empenhos do mesmo credor (padrão 30)")
    p.add_argument("--dias-fornecedor-novo", type=int, default=180, help="Fornecedor constituído há menos de N dias do empenho é sinalizado (padrão 180)")
    p.add_argument("--amostra-limite", type=int, default=50, help="Acima deste número de despesas o script sugere amostra (padrão 50)")
    p.add_argument("--materialidade", default="70", help="Percentual do valor empenhado coberto pelos maiores itens na amostra sugerida (padrão 70)")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="Grava a matriz em Markdown")
    p.add_argument("--csv", help="Grava a classificação por despesa em CSV (separador ponto e vírgula)")
    return p


def main():
    parser = montar_parser()
    args = parser.parse_args()
    try:
        tol = parse_num(args.tolerancia_sobrepreco)
        materialidade = parse_num(args.materialidade)
        if tol < ZERO or materialidade <= ZERO or materialidade > CEM:
            raise ValueError("tolerância deve ser não negativa e materialidade entre 0 e 100")
        if args.janela_fracionamento < 0 or args.dias_fornecedor_novo < 0 or args.amostra_limite < 1:
            raise ValueError("janela, dias de fornecedor novo e limite de amostra devem ser positivos")
        despesas = processar(ler_csv(args.despesas))
        for d in despesas:
            testar_despesa(d, tol, args.dias_fornecedor_novo)
        fracionamento = testar_fracionamento(despesas, args.janela_fracionamento)
        cons = consolidar(despesas)
        san = sanidade(despesas, cons)
        amostra = sugerir_amostra(despesas, args.amostra_limite, materialidade)

        memoria = [
            f"1. Lidas {len(despesas)} despesas; números em padrão brasileiro ou técnico; datas dd/mm/aaaa; flags S/N (aderência admite D).",
            "2. Aderência: N = desvio de finalidade com base no valor pago; D = aderência a esclarecer, sem base.",
            "3. Comprovação (só despesa liquidada ou paga): entrega N ou NF ausente = sem comprovação com base no valor pago; atesto N = irregularidade formal.",
            "4. Processo: processo_contratacao, pesquisa_precos ou contrato N = irregularidade formal.",
            "5. Estágios (Lei 4.320/1964, arts. 60, 62 e 63): pagamento sem liquidação, liquidação acima do empenho, NF ou liquidação anterior ao empenho, pagamento anterior à liquidação.",
            f"6. Preço: variação = preço unitário / referência - 1; acima de {fmt_pct(tol)} = sobrepreço a apurar, base = (unitário - referência) x quantidade.",
            f"7. Fracionamento: empenhos do mesmo CNPJ encadeados em até {args.janela_fracionamento} dias; fornecedor novo abaixo de {args.dias_fornecedor_novo} dias; sanção CEIS/CNEP conforme consulta anexada.",
            "8. Classe = achado mais grave na ordem: " + " > ".join(CLASSES) + ".",
            f"9. Amostra sugerida só acima de {args.amostra_limite} despesas: achados + materialidade de {fmt_pct(materialidade)} + seleção sistemática (NBC TA 530 por analogia).",
            "10. Sanidade: somas por classe e por fonte fecham com os totais; base de quantificação nunca excede o pago (exceto sobrepreço, que usa diferença x quantidade).",
            "11. Arredondamento apenas na apresentação (ROUND_HALF_UP, 2 casas); cálculo em Decimal.",
        ]
        resultado = {
            "script": "matriz_despesas_covid.py", "skill": SKILL, "versao": VERSAO,
            "premissas": {"arquivo_despesas": args.despesas, "tolerancia_sobrepreco": fmt_pct(tol),
                          "janela_fracionamento_dias": args.janela_fracionamento, "dias_fornecedor_novo": args.dias_fornecedor_novo,
                          "amostra_limite": args.amostra_limite, "materialidade": fmt_pct(materialidade),
                          "classes": CLASSES, "valores": "nominais, sem atualização"},
            "locale": LOCALE, "arredondamento": ARREDONDAMENTO,
            "universo": len(despesas),
            "despesas": [{k: (fmt_quantidade(v) if k == "quantidade" else v) for k, v in d.items() if k not in ("linha", "cnpj_digitos")}
                         for d in despesas],
            "totais": cons,
            "fracionamento": fracionamento,
            "amostra_sugerida": amostra,
            "sanidade": san,
            "memoria": memoria,
        }
        saida = serializar(resultado)
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
                w.writerow(["empenho", "fonte", "credor", "cnpj", "objeto", "valor_empenhado", "valor_pago", "classe",
                            "base_quantificacao", "achados"])
                for d in saida["despesas"]:
                    w.writerow([d["empenho"], d["fonte"], d["credor"], d["cnpj"], d["objeto"], d["valor_empenhado"], d["valor_pago"],
                                d["classe"], d["base_quantificacao"],
                                " | ".join(a["codigo"] for a in d["achados"] if a["classe"] != "regular")])
            print(f"CSV gravado em {args.csv}")
        pc = saida["totais"]["por_classe"]
        resumo = "; ".join(f"{c}: {pc[c]['quantidade']}" for c in CLASSES)
        print(f"Matriz: {len(despesas)} despesas ({resumo}); base de quantificação R$ {saida['sanidade']['total_base_quantificacao']}; "
              f"{len(fracionamento)} grupos de fracionamento; sanidade OK.", file=sys.stderr)
    except ValueError as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
