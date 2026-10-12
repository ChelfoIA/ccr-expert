#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conciliação do devido com os repasses e apuração do saldo em forma mercantil.

Parte da skill: pericia-prestacao-contas-estoque

Recebe a receita líquida devida ao vendedor mês a mês (JSON do script
tributos_sobre_receita.py, JSON do peps_estoque_transferido.py ou CSV
mes;receita_liquida), os repasses alegados pelo comprador e, se houver, as
compensações que ele pretende abater. Classifica cada item (comprovado, sem
comprovante, não previsto no contrato, duplicidade), imputa os repasses
admitidos ao mês mais antigo em aberto, monta a cronologia devido x repassado,
o saldo por mês e o saldo final, e entrega o quadro em forma mercantil do
art. 551 do CPC em três cenários (base, estrito e amplo).

Uso:
    python3 conciliacao_repasses.py --devido tributos.json \\
        --repasses assets/exemplo_repasses.csv \\
        --compensacoes assets/exemplo_compensacoes.csv \\
        --prazo-dias 30 --saida conciliacao.json --md conciliacao.md --csv cronologia.csv

Schemas (CSV separado por ponto e vírgula, com cabeçalho):
    repasses:      data;valor;meio;documento;observacao;aceito_pelo_contrato (S/N)
    compensacoes:  data;valor;natureza;documento;previsto_no_contrato (S/N);observacao
    devido em CSV: mes;receita_liquida  (opcionais: receita_bruta;total_tributos)

Cenários, declarados na saída:
    base     repasses com comprovante, admitidos pelo contrato e sem duplicidade,
             mais compensações previstas no contrato e documentadas. É o cenário
             sustentado pelo perito.
    estrito  só os repasses comprovados e admitidos; nenhuma compensação.
    amplo    tudo o que o comprador alega, inclusive sem comprovante e fora do
             contrato, excluída apenas a duplicidade de comprovante.

Regras fixas:
    1. Imputação do pagamento ao mês mais antigo em aberto (CC, arts. 352 a 355),
       salvo indicação diversa que o perito registre na memória.
    2. No mesmo dia, o devido do mês é lançado antes do repasse.
    3. Duplicidade de comprovante (mesmo documento repetido) sai de todos os
       cenários; mesma data e mesmo valor sem documento repetido é duplicidade
       provável: sai do base e do estrito e entra no amplo com alerta.
    4. Valores monetários em Decimal; arredondamento só na apresentação.
"""

import argparse
import csv
import json
import sys
from calendar import monthrange
from collections import OrderedDict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 28

SKILL = "pericia-prestacao-contas-estoque"
SCRIPT = "conciliacao_repasses.py"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
CENT = Decimal("0.01")

COLUNAS_REPASSES = ["data", "valor", "meio", "documento", "observacao", "aceito_pelo_contrato"]
COLUNAS_COMPENSACOES = ["data", "valor", "natureza", "documento", "previsto_no_contrato", "observacao"]
SIM = {"s", "sim", "y", "yes", "1"}
NAO = {"n", "nao", "não", "no", "0"}


class ErroValidacao(Exception):
    """Erro de entrada do usuário: sai com código 1 e mensagem clara."""


# ----------------------------------------------------------------------------
# Utilitários de número e data
# ----------------------------------------------------------------------------

def parse_num(texto, campo="valor"):
    """Converte número no padrão brasileiro (1.234,56) ou técnico (1234.56) em Decimal."""
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


def validar_mes(mes, origem):
    t = str(mes).strip()
    partes = t.split("/")
    if len(partes) != 2 or not partes[0].isdigit() or not partes[1].isdigit() or not 1 <= int(partes[0]) <= 12:
        raise ErroValidacao(f"{origem}: mês inválido '{mes}' (esperado mm/aaaa)")
    return f"{int(partes[0]):02d}/{partes[1]}"


def chave_mes(mes):
    m, a = mes.split("/")
    return (int(a), int(m))


def fim_do_mes(mes):
    m, a = chave_mes(mes)[1], chave_mes(mes)[0]
    return date(a, m, monthrange(a, m)[1])


def q2(valor):
    return Decimal(valor).quantize(CENT, rounding=ROUND_HALF_UP)


def tec(valor):
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


def sim_nao(texto, campo, linha):
    t = str(texto or "").strip().lower()
    if t in SIM:
        return True
    if t in NAO:
        return False
    raise ErroValidacao(f"linha {linha}: campo '{campo}' deve ser S ou N (recebido '{texto}')")


# ----------------------------------------------------------------------------
# Leitura das entradas
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
    return linhas


def ler_devido(caminho):
    """Devolve (meses ordenados, origem, tem_bruta) com receita_liquida, receita_bruta e total_tributos."""
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"arquivo do devido não encontrado: {caminho}")
    meses = OrderedDict()
    tem_bruta = False
    if p.suffix.lower() == ".json":
        try:
            dados = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ErroValidacao(f"arquivo do devido com JSON inválido: {e}")
        if isinstance(dados, dict) and "meses" in dados:
            origem = f"JSON de {dados.get('script', 'tributos_sobre_receita.py')}"
            for r in dados["meses"]:
                mes = validar_mes(r.get("mes"), "devido")
                bruta = parse_num(r.get("receita_bruta"), f"receita_bruta de {mes}")
                trib = parse_num(r.get("total_tributos", "0"), f"total_tributos de {mes}")
                liq = parse_num(r.get("receita_liquida"), f"receita_liquida de {mes}")
                if bruta - trib != liq:
                    raise ErroValidacao(f"devido {mes}: receita_bruta - total_tributos difere de receita_liquida no JSON de entrada")
                meses[mes] = {"receita_bruta": bruta, "total_tributos": trib, "receita_liquida": liq}
            tem_bruta = True
        elif isinstance(dados, dict) and "receita_antigo_por_mes" in dados:
            origem = f"JSON de {dados.get('script', 'peps_estoque_transferido.py')} (receita bruta, sem dedução de tributos)"
            for r in dados["receita_antigo_por_mes"]:
                mes = validar_mes(r.get("mes"), "devido")
                bruta = parse_num(r.get("receita_bruta"), f"receita_bruta de {mes}")
                meses[mes] = {"receita_bruta": bruta, "total_tributos": Decimal(0), "receita_liquida": bruta}
            tem_bruta = True
        else:
            raise ErroValidacao("JSON do devido sem a chave 'meses' (tributos_sobre_receita.py) nem 'receita_antigo_por_mes' (peps_estoque_transferido.py)")
    else:
        with p.open(encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f, delimiter=";")
            cab = [c.strip().lower() for c in (leitor.fieldnames or [])]
            if "mes" not in cab or "receita_liquida" not in cab:
                raise ErroValidacao("CSV do devido precisa do cabeçalho mes;receita_liquida (opcionais receita_bruta;total_tributos)")
            tem_bruta = "receita_bruta" in cab
            for linha in leitor:
                reg = {k.strip().lower(): (v or "").strip() for k, v in linha.items() if k}
                if not any(reg.values()):
                    continue
                mes = validar_mes(reg["mes"], "devido")
                liq = parse_num(reg["receita_liquida"], f"receita_liquida de {mes}")
                bruta = parse_num(reg["receita_bruta"], f"receita_bruta de {mes}") if tem_bruta and reg.get("receita_bruta") else liq
                trib = parse_num(reg["total_tributos"], f"total_tributos de {mes}") if reg.get("total_tributos") else bruta - liq
                meses[mes] = {"receita_bruta": bruta, "total_tributos": trib, "receita_liquida": liq}
        origem = "CSV mes;receita_liquida"
    if not meses:
        raise ErroValidacao("nenhuma competência encontrada no arquivo do devido")
    for mes, d in meses.items():
        if d["receita_liquida"] < 0:
            raise ErroValidacao(f"devido {mes}: receita líquida negativa; tratar devolução como compensação")
    ordenado = OrderedDict(sorted(meses.items(), key=lambda kv: chave_mes(kv[0])))
    return ordenado, origem, tem_bruta


def montar_itens(linhas_rep, linhas_comp):
    itens = []
    for r in linhas_rep:
        valor = parse_num(r["valor"], "valor")
        if valor <= 0:
            raise ErroValidacao(f"repasses, linha {r['_linha']}: valor deve ser positivo")
        itens.append({
            "tipo": "repasse",
            "data": parse_data(r["data"], "data"),
            "valor": valor,
            "meio": r.get("meio", ""),
            "descricao": r.get("meio", "") or "repasse",
            "documento": r.get("documento", ""),
            "observacao": r.get("observacao", ""),
            "admitido_contrato": sim_nao(r.get("aceito_pelo_contrato"), "aceito_pelo_contrato", r["_linha"]),
            "linha": r["_linha"],
        })
    for r in linhas_comp:
        valor = parse_num(r["valor"], "valor")
        if valor <= 0:
            raise ErroValidacao(f"compensações, linha {r['_linha']}: valor deve ser positivo")
        itens.append({
            "tipo": "compensacao",
            "data": parse_data(r["data"], "data"),
            "valor": valor,
            "meio": "compensação",
            "descricao": r.get("natureza", "") or "compensação",
            "documento": r.get("documento", ""),
            "observacao": r.get("observacao", ""),
            "admitido_contrato": sim_nao(r.get("previsto_no_contrato"), "previsto_no_contrato", r["_linha"]),
            "linha": r["_linha"],
        })
    itens.sort(key=lambda i: (i["data"], 0 if i["tipo"] == "repasse" else 1, i["linha"]))
    return itens


# ----------------------------------------------------------------------------
# Classificação, duplicidades e cenários
# ----------------------------------------------------------------------------

def classificar(itens, alertas):
    """Marca duplicidades e define em quais cenários cada item entra."""
    vistos_doc = {}
    vistos_data_valor = {}
    for i, item in enumerate(itens):
        item["id"] = i + 1
        item["duplicidade"] = ""
        doc = item["documento"].strip().lower()
        chave_dv = (item["tipo"], item["data"], q2(item["valor"]))
        if doc and (item["tipo"], doc) in vistos_doc:
            item["duplicidade"] = "comprovada"
            item["duplicado_de"] = vistos_doc[(item["tipo"], doc)]
            alertas.append(
                f"Item {item['id']} ({fmt_data(item['data'])}, R$ {br(item['valor'])}): mesmo documento do item "
                f"{item['duplicado_de']} ('{item['documento']}'). Duplicidade comprovada, excluída de todos os cenários.")
        elif chave_dv in vistos_data_valor:
            item["duplicidade"] = "provavel"
            item["duplicado_de"] = vistos_data_valor[chave_dv]
            alertas.append(
                f"Item {item['id']} ({fmt_data(item['data'])}, R$ {br(item['valor'])}): mesma data e valor do item "
                f"{item['duplicado_de']} com documento distinto ou ausente. Duplicidade provável: fora do cenário base; "
                f"entra no amplo. Exigir os dois comprovantes bancários.")
        else:
            if doc:
                vistos_doc[(item["tipo"], doc)] = item["id"]
            vistos_data_valor[chave_dv] = item["id"]

        comprovado = bool(item["documento"].strip())
        item["comprovado"] = comprovado
        motivos = []
        if item["duplicidade"] == "comprovada":
            motivos.append("duplicidade de comprovante")
        if item["duplicidade"] == "provavel":
            motivos.append("duplicidade provável (mesma data e valor)")
        if not comprovado:
            motivos.append("sem comprovante")
        if not item["admitido_contrato"]:
            motivos.append("não previsto no contrato")
        item["motivos_exclusao_base"] = motivos

        item["cenarios"] = []
        if item["duplicidade"] != "comprovada":
            item["cenarios"].append("amplo")
            if comprovado and item["admitido_contrato"] and item["duplicidade"] == "":
                item["cenarios"].append("base")
                if item["tipo"] == "repasse":
                    item["cenarios"].append("estrito")
        item["classe"] = "admitido no cenário base" if "base" in item["cenarios"] else "; ".join(motivos)
    return itens


def imputar(meses, itens_base):
    """Imputa cada item admitido ao mês mais antigo com saldo em aberto (CC, arts. 352 a 355)."""
    saldo_mes = OrderedDict((mes, d["receita_liquida"]) for mes, d in meses.items())
    imputacoes = []
    quitacao = {}
    excedente = Decimal(0)
    for item in itens_base:
        restante = item["valor"]
        partes = []
        for mes in saldo_mes:
            if restante <= 0:
                break
            if saldo_mes[mes] <= 0:
                continue
            usar = min(restante, saldo_mes[mes])
            saldo_mes[mes] -= usar
            restante -= usar
            partes.append({"mes": mes, "valor": usar})
            if saldo_mes[mes] == 0:
                quitacao[mes] = fmt_data(item["data"])
        if restante > 0:
            excedente += restante
            partes.append({"mes": "excedente", "valor": restante})
        imputacoes.append({"item": item, "partes": partes})
    return saldo_mes, imputacoes, quitacao, excedente


def cronologia(meses, itens_base):
    """Eventos em ordem de data: devido do mês (no último dia do mês) e itens admitidos; saldo acumulado."""
    eventos = []
    for mes, d in meses.items():
        eventos.append((fim_do_mes(mes), 0, 0, {"tipo": "devido", "mes": mes, "valor": d["receita_liquida"],
                                                "descricao": f"receita líquida do estoque antigo em {mes}"}))
    for item in itens_base:
        eventos.append((item["data"], 1, item["id"], item))
    eventos.sort(key=lambda e: (e[0], e[1], e[2]))
    saldo = Decimal(0)
    linhas = []
    for d, _, _, ev in eventos:
        if ev["tipo"] == "devido":
            saldo += ev["valor"]
            linhas.append(OrderedDict([
                ("data", fmt_data(d)), ("evento", "devido"), ("referencia", ev["mes"]),
                ("descricao", ev["descricao"]), ("devido", tec(ev["valor"])), ("repassado", "0.00"),
                ("saldo_acumulado", tec(saldo)), ("saldo_acumulado_br", br(saldo)),
            ]))
        else:
            saldo -= ev["valor"]
            linhas.append(OrderedDict([
                ("data", fmt_data(d)), ("evento", ev["tipo"]), ("referencia", f"item {ev['id']}"),
                ("descricao", f"{ev['descricao']} ({ev['documento'] or 'sem documento'})"),
                ("devido", "0.00"), ("repassado", tec(ev["valor"])),
                ("saldo_acumulado", tec(saldo)), ("saldo_acumulado_br", br(saldo)),
            ]))
    return linhas, saldo


def saldo_por_mes(meses, saldo_mes_aberto, imputacoes, itens_base, quitacao):
    por_mes = []
    acumulado = Decimal(0)
    repassado_acum = Decimal(0)
    for mes, d in meses.items():
        imputado = sum((p["valor"] for imp in imputacoes for p in imp["partes"] if p["mes"] == mes), Decimal(0))
        no_mes = sum((i["valor"] for i in itens_base if i["data"].strftime("%m/%Y") == mes), Decimal(0))
        acumulado += d["receita_liquida"]
        repassado_acum += no_mes
        aberto = saldo_mes_aberto[mes]
        if d["receita_liquida"] == 0:
            status = "sem receita"
        elif aberto == 0:
            status = "quitado"
        elif imputado > 0:
            status = "parcial"
        else:
            status = "em aberto"
        por_mes.append(OrderedDict([
            ("mes", mes),
            ("receita_bruta", tec(d["receita_bruta"])),
            ("total_tributos", tec(d["total_tributos"])),
            ("devido", tec(d["receita_liquida"])),
            ("imputado", tec(imputado)),
            ("saldo_do_mes_em_aberto", tec(aberto)),
            ("status", status),
            ("quitado_em", quitacao.get(mes, "")),
            ("repassado_no_mes_por_data", tec(no_mes)),
            ("devido_acumulado", tec(acumulado)),
            ("repassado_acumulado", tec(repassado_acum)),
            ("saldo_acumulado", tec(acumulado - repassado_acum)),
            ("saldo_acumulado_br", br(acumulado - repassado_acum)),
        ]))
    return por_mes


def rotulo_credor(saldo, papel_autor):
    vendedor = "autor (vendedor)" if papel_autor == "vendedor" else "réu (vendedor)"
    comprador = "réu (comprador)" if papel_autor == "vendedor" else "autor (comprador)"
    if saldo > 0:
        return f"saldo credor do {vendedor}"
    if saldo < 0:
        return f"saldo credor do {comprador}: repassou além do devido"
    return "saldo zero: contas quitadas"


def montar_cenarios(meses, itens, papel_autor):
    devido_total = sum((d["receita_liquida"] for d in meses.values()), Decimal(0))
    cen = OrderedDict()
    descricoes = {
        "base": "repasses comprovados e admitidos pelo contrato, sem duplicidade, mais compensações previstas no contrato e documentadas",
        "estrito": "somente repasses comprovados e admitidos pelo contrato; nenhuma compensação",
        "amplo": "tudo o que o comprador alega, inclusive sem comprovante e fora do contrato; excluída só a duplicidade de comprovante",
    }
    for nome in ("base", "estrito", "amplo"):
        rep = sum((i["valor"] for i in itens if nome in i["cenarios"] and i["tipo"] == "repasse"), Decimal(0))
        comp = sum((i["valor"] for i in itens if nome in i["cenarios"] and i["tipo"] == "compensacao"), Decimal(0))
        saldo = devido_total - rep - comp
        cen[nome] = OrderedDict([
            ("descricao", descricoes[nome]),
            ("devido_total", tec(devido_total)),
            ("repasses", tec(rep)),
            ("compensacoes", tec(comp)),
            ("saldo_final", tec(saldo)),
            ("saldo_final_br", br(saldo)),
            ("credor", rotulo_credor(saldo, papel_autor)),
            ("itens", [i["id"] for i in itens if nome in i["cenarios"]]),
        ])
    return cen, devido_total


def verificar_sanidade(meses, itens, cen, por_mes, cron_saldo, imputacoes, excedente):
    testes = []
    ok = True
    devido_total = sum((d["receita_liquida"] for d in meses.values()), Decimal(0))

    base = cen["base"]
    esperado = devido_total - Decimal(base["repasses"]) - Decimal(base["compensacoes"])
    fecha = q2(esperado) == Decimal(base["saldo_final"])
    testes.append({"teste": "saldo final base = devido total - repasses admitidos - compensações admitidas",
                   "resultado": "OK" if fecha else f"FALHA ({esperado} / {base['saldo_final']})"})
    ok &= fecha

    aberto = sum((Decimal(m["saldo_do_mes_em_aberto"]) for m in por_mes), Decimal(0))
    fecha = q2(aberto - excedente) == Decimal(base["saldo_final"])
    testes.append({"teste": "soma dos saldos mensais em aberto - excedente = saldo final base",
                   "resultado": "OK" if fecha else f"FALHA ({aberto} - {excedente} / {base['saldo_final']})"})
    ok &= fecha

    imputado = sum((p["valor"] for imp in imputacoes for p in imp["partes"]), Decimal(0))
    admitido = Decimal(base["repasses"]) + Decimal(base["compensacoes"])
    fecha = q2(imputado) == q2(admitido)
    testes.append({"teste": "soma das imputações (inclusive excedente) = total admitido no cenário base",
                   "resultado": "OK" if fecha else f"FALHA ({imputado} / {admitido})"})
    ok &= fecha

    fecha = q2(cron_saldo) == Decimal(base["saldo_final"])
    testes.append({"teste": "último saldo acumulado da cronologia = saldo final base",
                   "resultado": "OK" if fecha else f"FALHA ({cron_saldo} / {base['saldo_final']})"})
    ok &= fecha

    ordem = Decimal(cen["estrito"]["saldo_final"]) >= Decimal(cen["base"]["saldo_final"]) >= Decimal(cen["amplo"]["saldo_final"])
    testes.append({"teste": "ordem dos cenários: saldo estrito >= base >= amplo",
                   "resultado": "OK" if ordem else "FALHA"})
    ok &= ordem

    sem_classe = [i["id"] for i in itens if not i["cenarios"] and i["duplicidade"] != "comprovada"]
    testes.append({"teste": "todo item entra em ao menos um cenário ou é duplicidade comprovada",
                   "resultado": "OK" if not sem_classe else f"FALHA nos itens {sem_classe}"})
    ok &= not sem_classe
    return testes, ok


# ----------------------------------------------------------------------------
# Saídas
# ----------------------------------------------------------------------------

def item_saida(i):
    return OrderedDict([
        ("id", i["id"]), ("tipo", i["tipo"]), ("data", fmt_data(i["data"])), ("valor", tec(i["valor"])),
        ("valor_br", br(i["valor"])), ("meio", i["meio"]), ("descricao", i["descricao"]),
        ("documento", i["documento"] or ""), ("observacao", i["observacao"]),
        ("admitido_pelo_contrato", "S" if i["admitido_contrato"] else "N"),
        ("comprovado", "S" if i["comprovado"] else "N"),
        ("duplicidade", i["duplicidade"] or "não"),
        ("duplicado_de", i.get("duplicado_de", "")),
        ("cenarios", i["cenarios"]), ("classe", i["classe"]),
    ])


def quadro_mercantil(meses, cen, tem_bruta, papel_autor):
    bruta = sum((d["receita_bruta"] for d in meses.values()), Decimal(0))
    trib = sum((d["total_tributos"] for d in meses.values()), Decimal(0))
    liq = sum((d["receita_liquida"] for d in meses.values()), Decimal(0))
    base = cen["base"]
    linhas = []
    if tem_bruta:
        linhas.append(("Receita bruta das vendas do estoque transferido", "+", tec(bruta)))
        linhas.append(("Tributos incidentes sobre essa receita (dedução)", "-", tec(trib)))
    linhas.append(("Receita líquida devida ao vendedor", "=", tec(liq)))
    linhas.append(("Compensações previstas no contrato e documentadas", "-", base["compensacoes"]))
    linhas.append(("Repasses comprovados e admitidos pelo contrato", "-", base["repasses"]))
    linhas.append((f"Saldo final: {base['credor']}", "=", base["saldo_final"]))
    return [OrderedDict([("rubrica", r), ("sinal", s), ("valor", v), ("valor_br", br(v))]) for r, s, v in linhas]


def parcelas_para_atualizacao(meses, itens_base, prazo_dias):
    """Lista para a skill atualizacao-monetaria: devido no vencimento (sinal +) e repasses na data (sinal -)."""
    parcelas = []
    for mes, d in meses.items():
        if d["receita_liquida"] > 0:
            venc = fim_do_mes(mes) + timedelta(days=prazo_dias)
            parcelas.append(OrderedDict([("data", fmt_data(venc)), ("competencia", mes), ("natureza", "devido"),
                                         ("sinal", "+"), ("valor", tec(d["receita_liquida"]))]))
    for i in itens_base:
        parcelas.append(OrderedDict([("data", fmt_data(i["data"])), ("competencia", i["data"].strftime("%m/%Y")),
                                     ("natureza", i["tipo"]), ("sinal", "-"), ("valor", tec(i["valor"]))]))
    parcelas.sort(key=lambda p: datetime.strptime(p["data"], "%d/%m/%Y"))
    return parcelas


def montar_saida(args, origem, meses, itens, cen, por_mes, cron, imputacoes, excedente, quadro, parcelas, alertas, testes, memoria, tem_bruta):
    base = cen["base"]
    return OrderedDict([
        ("skill", SKILL),
        ("script", SCRIPT),
        ("premissas", OrderedDict([
            ("papel_autor", args.papel_autor),
            ("origem_devido", origem),
            ("imputacao", "cada repasse ou compensação admitida é imputada ao mês mais antigo com saldo em aberto (CC, arts. 352 a 355)"),
            ("ordem_mesmo_dia", "devido do mês lançado no último dia do mês, antes de repasse na mesma data"),
            ("vencimento", f"último dia do mês da venda mais {args.prazo_dias} dia(s) (premissa contratual declarada; usada só na lista para atualização monetária)"),
            ("duplicidade", "mesmo documento repetido: comprovada, fora de todos os cenários; mesma data e valor: provável, fora do base e do estrito"),
            ("cenarios", OrderedDict((k, v["descricao"]) for k, v in cen.items())),
            ("fontes", OrderedDict([
                ("devido", str(args.devido)),
                ("repasses", str(args.repasses)),
                ("compensacoes", str(args.compensacoes) if args.compensacoes else "não informado"),
            ])),
        ])),
        ("locale", LOCALE),
        ("arredondamento", ARREDONDAMENTO),
        ("resumo", OrderedDict([
            ("competencias", len(meses)),
            ("itens_alegados", len(itens)),
            ("itens_admitidos_base", len(base["itens"])),
            ("devido_total", base["devido_total"]),
            ("devido_total_br", br(base["devido_total"])),
            ("repasses_admitidos", base["repasses"]),
            ("compensacoes_admitidas", base["compensacoes"]),
            ("saldo_final", base["saldo_final"]),
            ("saldo_final_br", base["saldo_final_br"]),
            ("credor", base["credor"]),
            ("excedente_imputacao", tec(excedente)),
            ("repasses_sem_comprovante", tec(sum((i["valor"] for i in itens if i["tipo"] == "repasse" and not i["comprovado"]), Decimal(0)))),
            ("itens_nao_previstos_no_contrato", tec(sum((i["valor"] for i in itens if not i["admitido_contrato"]), Decimal(0)))),
            ("duplicidades", tec(sum((i["valor"] for i in itens if i["duplicidade"]), Decimal(0)))),
        ])),
        ("quadro_mercantil", quadro),
        ("cenarios", cen),
        ("saldo_por_mes", por_mes),
        ("cronologia", cron),
        ("imputacao", [
            OrderedDict([
                ("item", imp["item"]["id"]), ("data", fmt_data(imp["item"]["data"])), ("tipo", imp["item"]["tipo"]),
                ("valor", tec(imp["item"]["valor"])),
                ("partes", [OrderedDict([("mes", p["mes"]), ("valor", tec(p["valor"]))]) for p in imp["partes"]]),
            ]) for imp in imputacoes
        ]),
        ("itens", [item_saida(i) for i in itens]),
        ("repasses_sem_comprovante", [item_saida(i) for i in itens if i["tipo"] == "repasse" and not i["comprovado"]]),
        ("itens_nao_previstos_no_contrato", [item_saida(i) for i in itens if not i["admitido_contrato"]]),
        ("duplicidades", [item_saida(i) for i in itens if i["duplicidade"]]),
        ("parcelas_para_atualizacao", parcelas),
        ("alertas", alertas),
        ("sanidade", testes),
        ("memoria", memoria),
    ])


def gravar_csv(caminho, cron):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["data", "evento", "referencia", "descricao", "devido", "repassado", "saldo_acumulado"])
        for c in cron:
            w.writerow([c["data"], c["evento"], c["referencia"], c["descricao"], br(c["devido"]), br(c["repassado"]), br(c["saldo_acumulado"])])


def gravar_md(caminho, saida):
    L = ["# Conciliação dos repasses e saldo da prestação de contas", ""]
    L.append("## Quadro em forma mercantil (CPC, art. 551)")
    L.append("")
    L.append("| Rubrica | | Valor (R$) |")
    L.append("|---|:-:|---:|")
    for q in saida["quadro_mercantil"]:
        L.append(f"| {q['rubrica']} | {q['sinal']} | {q['valor_br']} |")
    L.append("")
    L.append("## Cenários")
    L.append("")
    L.append("| Cenário | Repasses (R$) | Compensações (R$) | Saldo final (R$) | Credor |")
    L.append("|---|---:|---:|---:|---|")
    for nome, c in saida["cenarios"].items():
        L.append(f"| {nome} | {br(c['repasses'])} | {br(c['compensacoes'])} | {c['saldo_final_br']} | {c['credor']} |")
    L.append("")
    L.append("## Saldo por mês (cenário base)")
    L.append("")
    L.append("| Mês | Receita bruta (R$) | Tributos (R$) | Devido (R$) | Imputado (R$) | Em aberto (R$) | Situação | Quitado em | Saldo acumulado (R$) |")
    L.append("|---|---:|---:|---:|---:|---:|---|---|---:|")
    for m in saida["saldo_por_mes"]:
        L.append(f"| {m['mes']} | {br(m['receita_bruta'])} | {br(m['total_tributos'])} | {br(m['devido'])} | {br(m['imputado'])} | "
                 f"{br(m['saldo_do_mes_em_aberto'])} | {m['status']} | {m['quitado_em']} | {m['saldo_acumulado_br']} |")
    L.append("")
    L.append("## Cronologia devido x repassado (cenário base)")
    L.append("")
    L.append("| Data | Evento | Referência | Descrição | Devido (R$) | Repassado (R$) | Saldo acumulado (R$) |")
    L.append("|---|---|---|---|---:|---:|---:|")
    for c in saida["cronologia"]:
        L.append(f"| {c['data']} | {c['evento']} | {c['referencia']} | {c['descricao']} | {br(c['devido'])} | {br(c['repassado'])} | {c['saldo_acumulado_br']} |")
    L.append("")
    L.append("## Itens alegados pelo comprador e classificação")
    L.append("")
    L.append("| Id | Tipo | Data | Valor (R$) | Documento | Contrato | Comprovado | Duplicidade | Cenários | Classe |")
    L.append("|---:|---|---|---:|---|:-:|:-:|---|---|---|")
    for i in saida["itens"]:
        L.append(f"| {i['id']} | {i['tipo']} | {i['data']} | {i['valor_br']} | {i['documento'] or 'sem documento'} | {i['admitido_pelo_contrato']} | "
                 f"{i['comprovado']} | {i['duplicidade']} | {', '.join(i['cenarios']) or 'nenhum'} | {i['classe']} |")
    L.append("")
    if saida["alertas"]:
        L.append("## Alertas")
        L.append("")
        L.extend(f"- {a}" for a in saida["alertas"])
        L.append("")
    L.append("## Sanidade")
    L.append("")
    L.extend(f"- {t['teste']}: {t['resultado']}" for t in saida["sanidade"])
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
        description="Concilia o devido com os repasses e apura o saldo da prestação de contas em forma mercantil (skill pericia-prestacao-contas-estoque).")
    p.add_argument("--devido", required=True, help="JSON de tributos_sobre_receita.py (ou de peps_estoque_transferido.py) ou CSV mes;receita_liquida")
    p.add_argument("--repasses", required=True, help="CSV dos repasses alegados: data;valor;meio;documento;observacao;aceito_pelo_contrato (S/N)")
    p.add_argument("--compensacoes", help="CSV opcional das compensações alegadas: data;valor;natureza;documento;previsto_no_contrato (S/N);observacao")
    p.add_argument("--prazo-dias", dest="prazo_dias", type=int, default=30,
                   help="Dias após o fim do mês da venda para o vencimento do repasse, conforme o contrato (padrão 30; só afeta a lista para atualização)")
    p.add_argument("--papel-autor", dest="papel_autor", choices=["vendedor", "comprador"], default="vendedor",
                   help="Quem é o autor da ação: vendedor (padrão, exige contas) ou comprador")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--csv", help="Grava a cronologia devido x repassado em CSV (ponto e vírgula, números em padrão brasileiro)")
    p.add_argument("--md", help="Grava os quadros em Markdown para o laudo")
    return p


def main():
    args = construir_parser().parse_args()
    try:
        if args.prazo_dias < 0:
            raise ErroValidacao("--prazo-dias não pode ser negativo")
        meses, origem, tem_bruta = ler_devido(args.devido)
        linhas_rep = ler_csv(args.repasses, COLUNAS_REPASSES, "repasses")
        linhas_comp = ler_csv(args.compensacoes, COLUNAS_COMPENSACOES, "compensações") if args.compensacoes else []
        alertas, memoria = [], []
        if not tem_bruta:
            alertas.append("Devido informado sem receita bruta e tributos: o quadro mercantil parte da receita líquida.")
        if "sem dedução de tributos" in origem:
            alertas.append("Devido lido do JSON do PEPS, sem dedução de tributos: rodar tributos_sobre_receita.py antes, salvo cláusula de repasse bruto.")
        memoria.append(f"Devido lido de {origem}: {len(meses)} competências, de {next(iter(meses))} a {list(meses)[-1]}.")

        itens = montar_itens(linhas_rep, linhas_comp)
        if not itens:
            raise ErroValidacao("nenhum repasse nem compensação informados: nada a conciliar")
        classificar(itens, alertas)
        itens_base = [i for i in itens if "base" in i["cenarios"]]
        memoria.append(f"{len(itens)} itens alegados ({sum(1 for i in itens if i['tipo'] == 'repasse')} repasses, "
                       f"{sum(1 for i in itens if i['tipo'] == 'compensacao')} compensações); {len(itens_base)} admitidos no cenário base.")
        for i in itens:
            if "base" not in i["cenarios"]:
                memoria.append(f"Item {i['id']} ({i['tipo']}, {fmt_data(i['data'])}, R$ {br(i['valor'])}) fora do cenário base: {i['classe']}.")

        cen, devido_total = montar_cenarios(meses, itens, args.papel_autor)
        saldo_aberto, imputacoes, quitacao, excedente = imputar(meses, itens_base)
        por_mes = saldo_por_mes(meses, saldo_aberto, imputacoes, itens_base, quitacao)
        cron, cron_saldo = cronologia(meses, itens_base)
        if excedente > 0:
            alertas.append(f"Repasses admitidos excedem o devido em R$ {br(excedente)}: saldo credor do comprador no cenário base.")
        for imp in imputacoes:
            partes = "; ".join(f"{p['mes']} R$ {br(p['valor'])}" for p in imp["partes"])
            memoria.append(f"Item {imp['item']['id']} de {fmt_data(imp['item']['data'])} (R$ {br(imp['item']['valor'])}) imputado a: {partes}.")
        memoria.append(f"Devido total R$ {br(devido_total)}; admitido no base R$ {br(Decimal(cen['base']['repasses']) + Decimal(cen['base']['compensacoes']))}; "
                       f"saldo final base R$ {cen['base']['saldo_final_br']} ({cen['base']['credor']}).")
        memoria.append(f"Cenário estrito: saldo R$ {cen['estrito']['saldo_final_br']}; cenário amplo: saldo R$ {cen['amplo']['saldo_final_br']}.")

        testes, ok = verificar_sanidade(meses, itens, cen, por_mes, cron_saldo, imputacoes, excedente)
        if not ok:
            raise RuntimeError(f"teste de sanidade falhou: {[t for t in testes if t['resultado'] != 'OK']}")

        quadro = quadro_mercantil(meses, cen, tem_bruta, args.papel_autor)
        parcelas = parcelas_para_atualizacao(meses, itens_base, args.prazo_dias)
        saida = montar_saida(args, origem, meses, itens, cen, por_mes, cron, imputacoes, excedente, quadro, parcelas, alertas, testes, memoria, tem_bruta)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"JSON gravado em {args.saida}: devido R$ {br(devido_total)}; admitido no cenário base R$ "
                  f"{br(Decimal(cen['base']['repasses']) + Decimal(cen['base']['compensacoes']))}; saldo final R$ {cen['base']['saldo_final_br']} "
                  f"({cen['base']['credor']}); estrito R$ {cen['estrito']['saldo_final_br']}, amplo R$ {cen['amplo']['saldo_final_br']}; "
                  f"{len(alertas)} alerta(s); sanidade OK.")
        else:
            print(texto)
        if args.csv:
            gravar_csv(args.csv, cron)
            print(f"CSV gravado em {args.csv}")
        if args.md:
            gravar_md(args.md, saida)
            print(f"Markdown gravado em {args.md}")
    except ErroValidacao as e:
        print(f"ERRO de validação: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"ERRO: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
