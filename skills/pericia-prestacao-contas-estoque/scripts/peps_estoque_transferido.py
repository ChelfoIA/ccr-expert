#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atribuição PEPS das vendas ao estoque transferido na data-base.

Parte da skill: pericia-prestacao-contas-estoque

Monta o estoque inicial por item a partir do inventário da data-base, recebe as
compras e as vendas posteriores e atribui cada venda, pelo método PEPS (primeiro
a entrar, primeiro a sair), ao estoque antigo (do vendedor) ou ao estoque novo
(adquirido pelo comprador depois da data-base). Devolve a receita bruta
atribuível ao estoque antigo por mês e por item, o CMV correspondente, o
remanescente do estoque antigo e os alertas de integridade.

Uso:
    python3 peps_estoque_transferido.py --inventario assets/exemplo_inventario.csv \\
        --compras assets/exemplo_compras.csv --vendas assets/exemplo_vendas.csv \\
        --data-base 31/03/2025 --saida peps.json --csv atribuicao.csv --md peps.md

Schemas (CSV separado por ponto e vírgula, com cabeçalho):
    inventario: item;descricao;quantidade;custo_unitario;preco_venda_ref
    compras:    data;item;quantidade;custo_unitario;nf
    vendas:     data;item;quantidade;preco_unitario;nf;cliente

Regras fixas, declaradas na saída:
    1. Movimentos com data igual ou anterior à data-base são ignorados e listados
       em alertas: o inventário da data-base já os reflete.
    2. No mesmo dia, a compra é processada antes da venda.
    3. Quantidade vendida sem lastro (item ausente do inventário e sem compra,
       ou estoque esgotado) é marcada como "sem_lastro", nunca redistribuída.
    4. Valores monetários em Decimal; arredondamento só na apresentação.
"""

import argparse
import csv
import json
import sys
from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 28

SKILL = "pericia-prestacao-contas-estoque"
SCRIPT = "peps_estoque_transferido.py"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
CENT = Decimal("0.01")

COLUNAS_INVENTARIO = ["item", "descricao", "quantidade", "custo_unitario", "preco_venda_ref"]
COLUNAS_COMPRAS = ["data", "item", "quantidade", "custo_unitario", "nf"]
COLUNAS_VENDAS = ["data", "item", "quantidade", "preco_unitario", "nf", "cliente"]


class ErroValidacao(Exception):
    """Erro de entrada do usuário: sai com código 1 e mensagem clara."""


# ----------------------------------------------------------------------------
# Utilitários de número e data
# ----------------------------------------------------------------------------

def parse_num(texto, campo="valor"):
    """Converte número no padrão brasileiro (1.234,56) ou técnico (1234.56) em Decimal.

    Regra: havendo vírgula, o texto é brasileiro (pontos são milhar). Sem vírgula
    e com mais de um ponto, os pontos são milhar. Sem vírgula e com um só ponto,
    o ponto é decimal (padrão técnico).
    """
    if texto is None:
        raise ErroValidacao(f"campo '{campo}' ausente")
    t = str(texto).strip().replace("R$", "").replace(" ", "")
    if t == "":
        raise ErroValidacao(f"campo '{campo}' vazio")
    negativo = t.startswith("-")
    t = t.lstrip("-").lstrip("+")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif t.count(".") > 1:
        t = t.replace(".", "")
    try:
        valor = Decimal(t)
    except InvalidOperation:
        raise ErroValidacao(f"campo '{campo}' com número inválido: '{texto}'")
    return -valor if negativo else valor


def parse_data(texto, campo="data"):
    """Lê data em dd/mm/aaaa (padrão) ou aaaa-mm-dd."""
    t = str(texto or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue
    raise ErroValidacao(f"campo '{campo}' com data inválida: '{texto}' (esperado dd/mm/aaaa)")


def fmt_data(d):
    return d.strftime("%d/%m/%Y")


def mes_de(d):
    return d.strftime("%m/%Y")


def chave_mes(mes):
    """'04/2025' -> (2025, 4) para ordenação."""
    m, a = mes.split("/")
    return (int(a), int(m))


def q2(valor):
    return valor.quantize(CENT, rounding=ROUND_HALF_UP)


def tec(valor):
    """Valor monetário em string técnica com 2 casas, para encadeamento entre scripts."""
    return str(q2(valor))


def br(valor, casas=2):
    """Apresentação brasileira: 1.234.567,89."""
    v = Decimal(valor).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    negativo = v < 0
    v = abs(v)
    inteiro, _, frac = f"{v:.{casas}f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    texto = ".".join(grupos) + ("," + frac if casas else "")
    return "-" + texto if negativo else texto


def qtd(valor):
    """Quantidade sem zeros supérfluos (400, 12,5, 0,25)."""
    v = Decimal(valor).normalize()
    if v == v.to_integral():
        return str(int(v))
    return str(v).replace(".", ",")


# ----------------------------------------------------------------------------
# Leitura dos CSV
# ----------------------------------------------------------------------------

def ler_csv(caminho, colunas, nome):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"arquivo de {nome} não encontrado: {caminho}")
    with p.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        if leitor.fieldnames is None:
            raise ErroValidacao(f"arquivo de {nome} vazio: {caminho}")
        cabecalho = [c.strip().lower() for c in leitor.fieldnames]
        faltantes = [c for c in colunas if c not in cabecalho]
        if faltantes:
            raise ErroValidacao(
                f"arquivo de {nome} sem as colunas {faltantes}; cabeçalho esperado: {';'.join(colunas)}")
        linhas = []
        for i, linha in enumerate(leitor, start=2):
            registro = {k.strip().lower(): (v or "").strip() for k, v in linha.items() if k is not None}
            if not any(registro.values()):
                continue
            registro["_linha"] = i
            linhas.append(registro)
    if not linhas:
        raise ErroValidacao(f"arquivo de {nome} sem registros: {caminho}")
    return linhas


def montar_inventario(linhas):
    inventario = OrderedDict()
    for r in linhas:
        item = r["item"].upper()
        if not item:
            raise ErroValidacao(f"inventário, linha {r['_linha']}: código do item vazio")
        if item in inventario:
            raise ErroValidacao(f"inventário, linha {r['_linha']}: item '{item}' repetido; consolidar antes")
        quantidade = parse_num(r["quantidade"], "quantidade")
        custo = parse_num(r["custo_unitario"], "custo_unitario")
        if quantidade < 0 or custo < 0:
            raise ErroValidacao(f"inventário, linha {r['_linha']}: quantidade ou custo negativo em '{item}'")
        preco_ref = parse_num(r["preco_venda_ref"], "preco_venda_ref") if r.get("preco_venda_ref") else None
        inventario[item] = {
            "descricao": r.get("descricao", ""),
            "quantidade": quantidade,
            "custo_unitario": custo,
            "preco_venda_ref": preco_ref,
        }
    return inventario


def montar_movimentos(linhas, tipo):
    movimentos = []
    for r in linhas:
        item = r["item"].upper()
        if not item:
            raise ErroValidacao(f"{tipo}, linha {r['_linha']}: código do item vazio")
        data = parse_data(r["data"], "data")
        quantidade = parse_num(r["quantidade"], "quantidade")
        if quantidade <= 0:
            raise ErroValidacao(f"{tipo}, linha {r['_linha']}: quantidade deve ser positiva (item '{item}')")
        campo_valor = "custo_unitario" if tipo == "compras" else "preco_unitario"
        valor = parse_num(r[campo_valor], campo_valor)
        if valor < 0:
            raise ErroValidacao(f"{tipo}, linha {r['_linha']}: {campo_valor} negativo (item '{item}')")
        movimentos.append({
            "tipo": "compra" if tipo == "compras" else "venda",
            "data": data,
            "item": item,
            "quantidade": quantidade,
            "valor_unitario": valor,
            "nf": r.get("nf", ""),
            "cliente": r.get("cliente", ""),
            "linha": r["_linha"],
        })
    return movimentos


# ----------------------------------------------------------------------------
# Motor PEPS
# ----------------------------------------------------------------------------

def processar(inventario, compras, vendas, data_base):
    alertas = []
    memoria = []
    camadas = OrderedDict()   # item -> lista de camadas [{origem, quantidade, custo_unitario, referencia}]
    consumo_antigo = {}       # item -> quantidade do inventário já atribuída

    for item, dados in inventario.items():
        camadas[item] = []
        if dados["quantidade"] > 0:
            camadas[item].append({
                "origem": "antigo",
                "quantidade": dados["quantidade"],
                "custo_unitario": dados["custo_unitario"],
                "referencia": f"inventário de {fmt_data(data_base)}",
            })
        consumo_antigo[item] = Decimal(0)
    memoria.append(f"Estoque antigo montado com {len(inventario)} itens do inventário de {fmt_data(data_base)}.")

    eventos = []
    for m in compras + vendas:
        if m["data"] <= data_base:
            alertas.append(
                f"{m['tipo'].capitalize()} NF {m['nf']} de {fmt_data(m['data'])} (item {m['item']}, "
                f"{qtd(m['quantidade'])} un.) tem data igual ou anterior à data-base e foi ignorada: "
                f"o inventário da data-base já a reflete.")
            continue
        ordem = 0 if m["tipo"] == "compra" else 1
        eventos.append((m["data"], ordem, m["linha"], m))
    eventos.sort(key=lambda e: (e[0], e[1], e[2]))
    memoria.append(f"{len(eventos)} movimentos posteriores à data-base ordenados por data; no mesmo dia, compra antes de venda.")

    resultado_vendas = []
    itens_inexistentes = set()

    for _, _, _, m in eventos:
        item = m["item"]
        if item not in camadas:
            camadas[item] = []
            consumo_antigo[item] = Decimal(0)
        if m["tipo"] == "compra":
            camadas[item].append({
                "origem": "novo",
                "quantidade": m["quantidade"],
                "custo_unitario": m["valor_unitario"],
                "referencia": f"NF {m['nf']} de {fmt_data(m['data'])}",
            })
            continue

        restante = m["quantidade"]
        atrib = []
        fila = camadas[item]
        while restante > 0 and fila:
            camada = fila[0]
            usar = min(restante, camada["quantidade"])
            atrib.append({
                "origem": camada["origem"],
                "quantidade": usar,
                "custo_unitario": camada["custo_unitario"],
                "referencia": camada["referencia"],
            })
            camada["quantidade"] -= usar
            restante -= usar
            if camada["origem"] == "antigo":
                consumo_antigo[item] += usar
            if camada["quantidade"] == 0:
                fila.pop(0)
        sem_lastro = restante

        q_antigo = sum((a["quantidade"] for a in atrib if a["origem"] == "antigo"), Decimal(0))
        q_novo = sum((a["quantidade"] for a in atrib if a["origem"] == "novo"), Decimal(0))
        cmv_antigo = sum((a["quantidade"] * a["custo_unitario"] for a in atrib if a["origem"] == "antigo"), Decimal(0))
        preco = m["valor_unitario"]

        if item not in inventario and sem_lastro > 0:
            itens_inexistentes.add(item)
        elif sem_lastro > 0:
            alertas.append(
                f"Venda NF {m['nf']} de {fmt_data(m['data'])}: {qtd(sem_lastro)} un. de {item} sem lastro "
                f"(estoque antigo e compras esgotados). Indica inventário subavaliado ou compra não informada; "
                f"conferir Bloco H e NF-e de entrada.")

        resultado_vendas.append({
            "data": fmt_data(m["data"]),
            "mes": mes_de(m["data"]),
            "nf": m["nf"],
            "cliente": m["cliente"],
            "item": item,
            "quantidade": m["quantidade"],
            "preco_unitario": preco,
            "quantidade_antigo": q_antigo,
            "quantidade_novo": q_novo,
            "quantidade_sem_lastro": sem_lastro,
            "receita_bruta_total": m["quantidade"] * preco,
            "receita_bruta_antigo": q_antigo * preco,
            "receita_bruta_novo": q_novo * preco,
            "receita_bruta_sem_lastro": sem_lastro * preco,
            "cmv_antigo": cmv_antigo,
            "atribuicoes": atrib,
        })

    for item in sorted(itens_inexistentes):
        total = sum((v["quantidade_sem_lastro"] for v in resultado_vendas if v["item"] == item), Decimal(0))
        alertas.append(
            f"Item {item} vendido ({qtd(total)} un.) sem constar do inventário da data-base nem de compra posterior: "
            f"receita excluída do estoque antigo e classificada como sem lastro. Conferir se o inventário omitiu o item.")

    return resultado_vendas, camadas, consumo_antigo, alertas, memoria


def consolidar(inventario, vendas_res, camadas, consumo_antigo, data_base):
    por_mes = OrderedDict()
    if vendas_res:
        meses = sorted({chave_mes(v["mes"]) for v in vendas_res})
        a, m = meses[0]
        fim = meses[-1]
        while (a, m) <= fim:
            por_mes[f"{m:02d}/{a}"] = {
                "receita_bruta": Decimal(0), "cmv_antigo": Decimal(0),
                "receita_bruta_novo": Decimal(0), "receita_bruta_sem_lastro": Decimal(0), "vendas": 0,
            }
            m += 1
            if m > 12:
                m, a = 1, a + 1
    for v in vendas_res:
        agg = por_mes[v["mes"]]
        agg["receita_bruta"] += v["receita_bruta_antigo"]
        agg["cmv_antigo"] += v["cmv_antigo"]
        agg["receita_bruta_novo"] += v["receita_bruta_novo"]
        agg["receita_bruta_sem_lastro"] += v["receita_bruta_sem_lastro"]
        if v["quantidade_antigo"] > 0:
            agg["vendas"] += 1

    por_item = []
    for item, dados in inventario.items():
        vendido = consumo_antigo.get(item, Decimal(0))
        receita = sum((v["receita_bruta_antigo"] for v in vendas_res if v["item"] == item), Decimal(0))
        cmv = sum((v["cmv_antigo"] for v in vendas_res if v["item"] == item), Decimal(0))
        remanescente = dados["quantidade"] - vendido
        por_item.append({
            "item": item,
            "descricao": dados["descricao"],
            "quantidade_inventario": dados["quantidade"],
            "custo_unitario": dados["custo_unitario"],
            "quantidade_vendida_antigo": vendido,
            "quantidade_remanescente": remanescente,
            "valor_remanescente_custo": remanescente * dados["custo_unitario"],
            "receita_bruta_antigo": receita,
            "cmv_antigo": cmv,
        })
    return por_mes, por_item


def verificar_sanidade(inventario, vendas_res, consumo_antigo, por_mes, por_item):
    testes = []
    ok_total = True

    excede = [i for i, q in consumo_antigo.items() if i in inventario and q > inventario[i]["quantidade"]]
    testes.append({"teste": "atribuição ao estoque antigo nunca excede o inventário",
                   "resultado": "OK" if not excede else f"FALHA nos itens {excede}"})
    ok_total &= not excede

    quebra = [v["nf"] for v in vendas_res
              if v["quantidade_antigo"] + v["quantidade_novo"] + v["quantidade_sem_lastro"] != v["quantidade"]]
    testes.append({"teste": "soma das atribuições (antigo + novo + sem lastro) = quantidade vendida, em cada venda",
                   "resultado": "OK" if not quebra else f"FALHA nas NF {quebra}"})
    ok_total &= not quebra

    total_vendas = sum((v["receita_bruta_antigo"] for v in vendas_res), Decimal(0))
    total_mes = sum((m["receita_bruta"] for m in por_mes.values()), Decimal(0))
    total_item = sum((i["receita_bruta_antigo"] for i in por_item), Decimal(0))
    fecha = total_vendas == total_mes == total_item
    testes.append({"teste": "receita do estoque antigo por venda = por mês = por item",
                   "resultado": "OK" if fecha else f"FALHA ({total_vendas} / {total_mes} / {total_item})"})
    ok_total &= fecha

    negativos = [i["item"] for i in por_item if i["quantidade_remanescente"] < 0]
    testes.append({"teste": "remanescente do estoque antigo nunca negativo",
                   "resultado": "OK" if not negativos else f"FALHA nos itens {negativos}"})
    ok_total &= not negativos

    return testes, ok_total


# ----------------------------------------------------------------------------
# Saídas
# ----------------------------------------------------------------------------

def montar_saida(args, inventario, vendas_res, por_mes, por_item, alertas, memoria, testes):
    total_receita = sum((m["receita_bruta"] for m in por_mes.values()), Decimal(0))
    total_cmv = sum((m["cmv_antigo"] for m in por_mes.values()), Decimal(0))
    total_novo = sum((m["receita_bruta_novo"] for m in por_mes.values()), Decimal(0))
    total_sem_lastro = sum((m["receita_bruta_sem_lastro"] for m in por_mes.values()), Decimal(0))
    valor_inventario = sum((d["quantidade"] * d["custo_unitario"] for d in inventario.values()), Decimal(0))
    remanescente = sum((i["valor_remanescente_custo"] for i in por_item), Decimal(0))

    memoria.append(f"Receita bruta atribuída ao estoque antigo: R$ {br(total_receita)} em {len(por_mes)} meses.")
    memoria.append(f"CMV do estoque antigo: R$ {br(total_cmv)}; inventário a custo: R$ {br(valor_inventario)}; "
                   f"remanescente a custo: R$ {br(remanescente)}.")
    memoria.append(f"Receita de estoque novo (fora da prestação de contas): R$ {br(total_novo)}; "
                   f"receita sem lastro: R$ {br(total_sem_lastro)}.")

    return OrderedDict([
        ("skill", SKILL),
        ("script", SCRIPT),
        ("premissas", OrderedDict([
            ("metodo", "PEPS (primeiro a entrar, primeiro a sair) por item"),
            ("data_base", fmt_data(args.data_base)),
            ("criterio_data_base", "inventário representa o estoque ao fim do dia da data-base; só movimentos posteriores são processados"),
            ("ordem_mesmo_dia", "compra antes de venda"),
            ("sem_lastro", "quantidade vendida além do estoque antigo e das compras é marcada como sem lastro, nunca redistribuída"),
            ("fontes", OrderedDict([
                ("inventario", str(args.inventario)),
                ("compras", str(args.compras) if args.compras else "não informado"),
                ("vendas", str(args.vendas)),
            ])),
        ])),
        ("locale", LOCALE),
        ("arredondamento", ARREDONDAMENTO),
        ("resumo", OrderedDict([
            ("itens_inventario", len(inventario)),
            ("valor_inventario_custo", tec(valor_inventario)),
            ("vendas_processadas", len(vendas_res)),
            ("vendas_com_estoque_antigo", sum(1 for v in vendas_res if v["quantidade_antigo"] > 0)),
            ("receita_bruta_antigo_total", tec(total_receita)),
            ("receita_bruta_antigo_total_br", br(total_receita)),
            ("cmv_antigo_total", tec(total_cmv)),
            ("estoque_antigo_remanescente_custo", tec(remanescente)),
            ("receita_bruta_novo_total", tec(total_novo)),
            ("receita_bruta_sem_lastro_total", tec(total_sem_lastro)),
        ])),
        ("receita_antigo_por_mes", [
            OrderedDict([
                ("mes", mes),
                ("receita_bruta", tec(d["receita_bruta"])),
                ("receita_bruta_br", br(d["receita_bruta"])),
                ("cmv_antigo", tec(d["cmv_antigo"])),
                ("vendas_com_estoque_antigo", d["vendas"]),
                ("receita_bruta_novo", tec(d["receita_bruta_novo"])),
                ("receita_bruta_sem_lastro", tec(d["receita_bruta_sem_lastro"])),
            ]) for mes, d in por_mes.items()
        ]),
        ("receita_antigo_por_item", [
            OrderedDict([
                ("item", i["item"]),
                ("descricao", i["descricao"]),
                ("quantidade_inventario", qtd(i["quantidade_inventario"])),
                ("quantidade_vendida_antigo", qtd(i["quantidade_vendida_antigo"])),
                ("quantidade_remanescente", qtd(i["quantidade_remanescente"])),
                ("receita_bruta_antigo", tec(i["receita_bruta_antigo"])),
                ("cmv_antigo", tec(i["cmv_antigo"])),
            ]) for i in por_item
        ]),
        ("estoque_antigo_remanescente", [
            OrderedDict([
                ("item", i["item"]),
                ("descricao", i["descricao"]),
                ("quantidade", qtd(i["quantidade_remanescente"])),
                ("custo_unitario", tec(i["custo_unitario"])),
                ("valor_custo", tec(i["valor_remanescente_custo"])),
            ]) for i in por_item if i["quantidade_remanescente"] > 0
        ]),
        ("vendas", [
            OrderedDict([
                ("data", v["data"]),
                ("mes", v["mes"]),
                ("nf", v["nf"]),
                ("cliente", v["cliente"]),
                ("item", v["item"]),
                ("quantidade", qtd(v["quantidade"])),
                ("preco_unitario", tec(v["preco_unitario"])),
                ("quantidade_antigo", qtd(v["quantidade_antigo"])),
                ("quantidade_novo", qtd(v["quantidade_novo"])),
                ("quantidade_sem_lastro", qtd(v["quantidade_sem_lastro"])),
                ("receita_bruta_total", tec(v["receita_bruta_total"])),
                ("receita_bruta_antigo", tec(v["receita_bruta_antigo"])),
                ("cmv_antigo", tec(v["cmv_antigo"])),
                ("camadas", [
                    OrderedDict([("origem", a["origem"]), ("quantidade", qtd(a["quantidade"])),
                                 ("custo_unitario", tec(a["custo_unitario"])), ("referencia", a["referencia"])])
                    for a in v["atribuicoes"]
                ]),
            ]) for v in vendas_res
        ]),
        ("alertas", alertas),
        ("sanidade", testes),
        ("memoria", memoria),
    ])


def gravar_csv(caminho, vendas_res):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["data", "nf", "cliente", "item", "quantidade", "preco_unitario", "qtd_antigo", "qtd_novo",
                    "qtd_sem_lastro", "receita_bruta_total", "receita_bruta_antigo", "cmv_antigo"])
        for v in vendas_res:
            w.writerow([v["data"], v["nf"], v["cliente"], v["item"], qtd(v["quantidade"]), br(v["preco_unitario"]),
                        qtd(v["quantidade_antigo"]), qtd(v["quantidade_novo"]), qtd(v["quantidade_sem_lastro"]),
                        br(v["receita_bruta_total"]), br(v["receita_bruta_antigo"]), br(v["cmv_antigo"])])


def gravar_md(caminho, saida, por_mes, por_item, vendas_res):
    L = []
    L.append(f"# Atribuição PEPS do estoque transferido (data-base {saida['premissas']['data_base']})")
    L.append("")
    L.append("## Receita bruta do estoque antigo por mês")
    L.append("")
    L.append("| Mês | Receita bruta (R$) | CMV (R$) | Vendas com estoque antigo |")
    L.append("|---|---:|---:|---:|")
    for mes, d in por_mes.items():
        L.append(f"| {mes} | {br(d['receita_bruta'])} | {br(d['cmv_antigo'])} | {d['vendas']} |")
    L.append(f"| Total | {saida['resumo']['receita_bruta_antigo_total_br']} | {br(saida['resumo']['cmv_antigo_total'])} | "
             f"{saida['resumo']['vendas_com_estoque_antigo']} |")
    L.append("")
    L.append("## Estoque antigo por item")
    L.append("")
    L.append("| Item | Descrição | Inventário | Vendido (antigo) | Remanescente | Receita antigo (R$) | CMV (R$) |")
    L.append("|---|---|---:|---:|---:|---:|---:|")
    for i in por_item:
        L.append(f"| {i['item']} | {i['descricao']} | {qtd(i['quantidade_inventario'])} | {qtd(i['quantidade_vendida_antigo'])} | "
                 f"{qtd(i['quantidade_remanescente'])} | {br(i['receita_bruta_antigo'])} | {br(i['cmv_antigo'])} |")
    L.append("")
    L.append("## Atribuição venda a venda")
    L.append("")
    L.append("| Data | NF | Item | Qtd | Preço (R$) | Antigo | Novo | Sem lastro | Receita antigo (R$) |")
    L.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for v in vendas_res:
        L.append(f"| {v['data']} | {v['nf']} | {v['item']} | {qtd(v['quantidade'])} | {br(v['preco_unitario'])} | "
                 f"{qtd(v['quantidade_antigo'])} | {qtd(v['quantidade_novo'])} | {qtd(v['quantidade_sem_lastro'])} | "
                 f"{br(v['receita_bruta_antigo'])} |")
    L.append("")
    if saida["alertas"]:
        L.append("## Alertas")
        L.append("")
        for a in saida["alertas"]:
            L.append(f"- {a}")
        L.append("")
    L.append("## Sanidade")
    L.append("")
    for t in saida["sanidade"]:
        L.append(f"- {t['teste']}: {t['resultado']}")
    L.append("")
    L.append("## Premissas")
    L.append("")
    for k, v in saida["premissas"].items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                L.append(f"- {k}.{k2}: {v2}")
        else:
            L.append(f"- {k}: {v}")
    L.append(f"- locale: {saida['locale']}")
    L.append(f"- arredondamento: {saida['arredondamento']}")
    Path(caminho).write_text("\n".join(L) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def construir_parser():
    p = argparse.ArgumentParser(
        description="Atribui vendas ao estoque transferido na data-base pelo método PEPS (skill pericia-prestacao-contas-estoque).")
    p.add_argument("--inventario", required=True, help="CSV do inventário na data-base: item;descricao;quantidade;custo_unitario;preco_venda_ref")
    p.add_argument("--compras", help="CSV das compras posteriores à data-base: data;item;quantidade;custo_unitario;nf (opcional, recomendado)")
    p.add_argument("--vendas", required=True, help="CSV das vendas: data;item;quantidade;preco_unitario;nf;cliente")
    p.add_argument("--data-base", required=True, dest="data_base", help="Data da transferência do estoque, em dd/mm/aaaa")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--csv", help="Grava a atribuição venda a venda em CSV (ponto e vírgula, números em padrão brasileiro)")
    p.add_argument("--md", help="Grava os quadros em Markdown para o laudo")
    return p


def main():
    args = construir_parser().parse_args()
    try:
        args.data_base = parse_data(args.data_base, "data-base")
        inventario = montar_inventario(ler_csv(args.inventario, COLUNAS_INVENTARIO, "inventário"))
        compras = montar_movimentos(ler_csv(args.compras, COLUNAS_COMPRAS, "compras"), "compras") if args.compras else []
        vendas = montar_movimentos(ler_csv(args.vendas, COLUNAS_VENDAS, "vendas"), "vendas")

        vendas_res, camadas, consumo_antigo, alertas, memoria = processar(inventario, compras, vendas, args.data_base)
        if not vendas_res:
            raise ErroValidacao("nenhuma venda posterior à data-base: nada a atribuir")
        por_mes, por_item = consolidar(inventario, vendas_res, camadas, consumo_antigo, args.data_base)
        testes, ok = verificar_sanidade(inventario, vendas_res, consumo_antigo, por_mes, por_item)
        if not ok:
            falhas = [t for t in testes if t["resultado"] != "OK"]
            raise RuntimeError(f"teste de sanidade falhou: {falhas}")

        saida = montar_saida(args, inventario, vendas_res, por_mes, por_item, alertas, memoria, testes)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"JSON gravado em {args.saida}: receita bruta do estoque antigo R$ "
                  f"{saida['resumo']['receita_bruta_antigo_total_br']} em {len(por_mes)} meses; "
                  f"{len(alertas)} alerta(s); sanidade OK.")
        else:
            print(texto)
        if args.csv:
            gravar_csv(args.csv, vendas_res)
            print(f"CSV gravado em {args.csv}")
        if args.md:
            gravar_md(args.md, saida, por_mes, por_item, vendas_res)
            print(f"Markdown gravado em {args.md}")
    except ErroValidacao as e:
        print(f"ERRO de validação: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"ERRO: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
