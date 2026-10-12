#!/usr/bin/env python3
"""
Frutos dos imóveis do espólio, imóvel a imóvel e mês a mês: aluguel esperado (contratual, de
mercado para o ocupante, potencial para o vago), recebido, diferença; aluguel devido pelo
herdeiro que ocupa imóvel com exclusividade (mercado x (1 - fração do ocupante) x meses, a
partir do marco inicial parametrizado); meses sem lastro documental; encargos do imóvel
ocupado pagos pelo espólio.

Parte da skill: auditoria-contabil-espolio

Uso:
    python3 scripts/rendimentos_imoveis.py --imoveis assets/exemplo_imoveis.csv \
        --recebimentos assets/exemplo_recebimentos_alugueis.csv --herdeiros 4 \
        --abertura-sucessao 10/01/2024 --data-referencia 30/06/2026 \
        --saida imoveis.json --md imoveis.md --csv imoveis.csv

Entrada --imoveis (CSV, ponto e vírgula, cabeçalho):
    id;descricao;pais;moeda;situacao;aluguel_contratual;aluguel_mercado;fonte_mercado;
    ocupante;fracao_ocupante;marco_inicial;fim;encargos_pagos_espolio
    situacao          locado | ocupado_herdeiro | vago | uso_espolio
    fracao_ocupante   fração do ocupante no imóvel: "1/4", "0,25" ou "25%"; vazio = 1/N herdeiros
    marco_inicial     dd/mm/aaaa: para locado, a abertura da sucessão ou o início do contrato;
                      para ocupado_herdeiro, a oposição, notificação ou citação adotada
    fim               dd/mm/aaaa; vazio = data de referência
    encargos_pagos_espolio  (opcional) IPTU e condomínio do imóvel ocupado pagos pelo espólio no período

Entrada --recebimentos (CSV): data;imovel_id;valor;moeda

Regras: frutos civis contam-se dia a dia (CC, art. 1.215), por isso mês parcial entra pro rata
die (desligável com --sem-pro-rata). Moeda nunca se mistura: totais por moeda; converter euro
antes com scripts/conversao_ptax.py. Todo valor em Decimal; ROUND_HALF_UP só na apresentação.
"""

import argparse
import calendar
import csv
import json
import sys
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

SITUACOES = {"locado", "ocupado_herdeiro", "vago", "uso_espolio"}
CENTAVOS = Decimal("0.01")
ZERO = Decimal("0")
UM = Decimal("1")
TOLERANCIA = Decimal("0.000001")


def q2(valor):
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def s2(valor):
    return str(q2(valor))


def fmt_moeda(valor, moeda="BRL"):
    """R$ 1.234,56 ou EUR 1.234,56."""
    v = q2(valor)
    sinal = "-" if v < 0 else ""
    inteiro, frac = f"{abs(v):.2f}".split(".")
    inteiro = "{:,}".format(int(inteiro)).replace(",", ".")
    prefixo = "R$ " if moeda == "BRL" else f"{moeda} "
    return f"{sinal}{prefixo}{inteiro},{frac}"


def parse_num(texto):
    """Aceita 1.234,56 (brasileiro) e 1234.56 (técnico). Devolve Decimal."""
    if texto is None:
        raise ValueError("valor ausente")
    s = str(texto).strip().replace("R$", "").replace("EUR", "").replace(" ", "")
    if s == "":
        raise ValueError("valor vazio")
    negativo = s.startswith("-")
    s = s.lstrip("+-")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") >= 1:
        partes = s.split(".")
        if len(partes) > 1 and all(len(p) == 3 for p in partes[1:]):
            s = "".join(partes)
    try:
        d = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"número inválido: {texto!r}") from exc
    return -d if negativo else d


def parse_fracao(texto):
    """"1/4", "0,25" ou "25%" para Decimal entre 0 e 1."""
    s = str(texto).strip().replace(" ", "")
    if "/" in s:
        num, den = s.split("/", 1)
        den_d = parse_num(den)
        if den_d == ZERO:
            raise ValueError(f"fração com denominador zero: {texto!r}")
        f = parse_num(num) / den_d
    elif s.endswith("%"):
        f = parse_num(s[:-1]) / Decimal("100")
    else:
        f = parse_num(s)
    if f < ZERO or f > UM:
        raise ValueError(f"fração fora de [0, 1]: {texto!r}")
    return f


def parse_data(texto, campo="data"):
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(f"{campo} inválida (esperado dd/mm/aaaa): {texto!r}") from exc


def fmt_data(d):
    return d.strftime("%d/%m/%Y")


def fim_do_mes(d):
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def meses_cobertos(inicio, fim, pro_rata=True):
    """Gera (mm/aaaa, dias cobertos, dias do mês, fração) de inicio a fim, inclusive."""
    atual = date(inicio.year, inicio.month, 1)
    while atual <= fim:
        ultimo = fim_do_mes(atual)
        ini_c = max(atual, inicio)
        fim_c = min(ultimo, fim)
        dias = (fim_c - ini_c).days + 1
        dias_mes = ultimo.day
        if pro_rata:
            fracao = Decimal(dias) / Decimal(dias_mes)
        else:
            fracao = UM
        yield atual.strftime("%m/%Y"), dias, dias_mes, fracao
        atual = ultimo + timedelta(days=1)


def ler_imoveis(caminho, herdeiros, data_ref):
    imoveis = []
    avisos = []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        obrig = {"id", "descricao", "moeda", "situacao", "marco_inicial"}
        faltam = obrig - set(leitor.fieldnames or [])
        if faltam:
            raise ValueError(f"colunas obrigatórias ausentes em --imoveis: {sorted(faltam)}")
        ids = set()
        for n, l in enumerate(leitor, start=2):
            if not any((v or "").strip() for v in l.values()):
                continue
            iid = (l.get("id") or "").strip()
            if not iid or iid in ids:
                raise ValueError(f"linha {n}: id de imóvel vazio ou repetido: {iid!r}")
            ids.add(iid)
            situacao = (l.get("situacao") or "").strip().lower()
            if situacao not in SITUACOES:
                raise ValueError(f"linha {n}: situacao deve ser {sorted(SITUACOES)}, veio {situacao!r}")
            moeda = (l.get("moeda") or "BRL").strip().upper() or "BRL"
            contratual = parse_num(l["aluguel_contratual"]) if (l.get("aluguel_contratual") or "").strip() else None
            mercado = parse_num(l["aluguel_mercado"]) if (l.get("aluguel_mercado") or "").strip() else None
            fonte_mercado = (l.get("fonte_mercado") or "").strip()
            if situacao == "locado" and contratual is None:
                raise ValueError(f"linha {n}: imóvel locado {iid} sem aluguel_contratual")
            if situacao in {"ocupado_herdeiro", "vago"} and mercado is None:
                raise ValueError(f"linha {n}: imóvel {iid} ({situacao}) exige aluguel_mercado com fonte")
            if mercado is not None and not fonte_mercado:
                raise ValueError(f"linha {n}: aluguel_mercado do imóvel {iid} sem fonte_mercado (laudo, anúncios, índice)")
            marco = parse_data(l.get("marco_inicial"), f"linha {n}: marco_inicial")
            fim = parse_data(l["fim"], f"linha {n}: fim") if (l.get("fim") or "").strip() else data_ref
            if fim < marco:
                raise ValueError(f"linha {n}: fim {fmt_data(fim)} anterior ao marco inicial {fmt_data(marco)} no imóvel {iid}")
            fracao = None
            if situacao == "ocupado_herdeiro":
                if (l.get("fracao_ocupante") or "").strip():
                    fracao = parse_fracao(l["fracao_ocupante"])
                else:
                    if not herdeiros or herdeiros < 1:
                        raise ValueError(f"linha {n}: imóvel {iid} ocupado sem fracao_ocupante e sem --herdeiros")
                    fracao = UM / Decimal(herdeiros)
                    avisos.append(
                        f"imóvel {iid}: fração do ocupante assumida como 1/{herdeiros} (igualitária); "
                        "conferir meação, regime de bens e testamento"
                    )
            encargos = parse_num(l["encargos_pagos_espolio"]) if (l.get("encargos_pagos_espolio") or "").strip() else ZERO
            imoveis.append({
                "id": iid, "descricao": (l.get("descricao") or "").strip(),
                "pais": (l.get("pais") or "").strip(), "moeda": moeda, "situacao": situacao,
                "contratual": contratual, "mercado": mercado, "fonte_mercado": fonte_mercado,
                "ocupante": (l.get("ocupante") or "").strip(), "fracao_ocupante": fracao,
                "marco": marco, "fim": fim, "encargos": encargos,
            })
    if not imoveis:
        raise ValueError("nenhum imóvel válido em --imoveis")
    return imoveis, avisos


def ler_recebimentos(caminho, imoveis_por_id):
    """Devolve dicionário (imovel_id, mm/aaaa) -> lista de (data, valor) e avisos."""
    rec = defaultdict(list)
    avisos = []
    if not caminho:
        return rec, avisos
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        faltam = {"data", "imovel_id", "valor"} - set(leitor.fieldnames or [])
        if faltam:
            raise ValueError(f"colunas obrigatórias ausentes em --recebimentos: {sorted(faltam)}")
        for n, l in enumerate(leitor, start=2):
            if not any((v or "").strip() for v in l.values()):
                continue
            iid = (l.get("imovel_id") or "").strip()
            if iid not in imoveis_por_id:
                raise ValueError(f"recebimentos, linha {n}: imovel_id {iid!r} não consta de --imoveis")
            moeda = (l.get("moeda") or imoveis_por_id[iid]["moeda"]).strip().upper()
            if moeda != imoveis_por_id[iid]["moeda"]:
                raise ValueError(
                    f"recebimentos, linha {n}: moeda {moeda} difere da moeda do imóvel {iid} "
                    f"({imoveis_por_id[iid]['moeda']}); converter antes com conversao_ptax.py"
                )
            d = parse_data(l.get("data"), f"recebimentos, linha {n}: data")
            v = parse_num(l.get("valor"))
            if v <= ZERO:
                raise ValueError(f"recebimentos, linha {n}: valor deve ser positivo")
            rec[(iid, d.strftime("%m/%Y"))].append((d, v))
    return rec, avisos


def processar_imovel(im, rec, pro_rata, abertura):
    """Tabela mensal e totais de um imóvel."""
    moeda = im["moeda"]
    tabela = []
    total_esp = ZERO
    total_rec = ZERO
    meses_equiv = ZERO
    sem_lastro = []
    if im["situacao"] == "locado":
        base = im["contratual"]
        natureza = "aluguel contratual"
    elif im["situacao"] == "ocupado_herdeiro":
        base = im["mercado"] * (UM - im["fracao_ocupante"])
        natureza = "aluguel de mercado x (1 - fração do ocupante), devido aos demais coerdeiros"
    elif im["situacao"] == "vago":
        base = im["mercado"]
        natureza = "renda potencial de mercado (vacância): depende de prova de culpa na administração"
    else:
        base = ZERO
        natureza = "uso do próprio espólio: sem fruto esperado"

    meses_do_imovel = set()
    for mes, dias, dias_mes, fracao in meses_cobertos(im["marco"], im["fim"], pro_rata):
        meses_do_imovel.add(mes)
        esperado = base * fracao
        recebidos = rec.get((im["id"], mes), [])
        recebido = sum((v for _, v in recebidos), ZERO)
        diferenca = esperado - recebido
        total_esp += esperado
        total_rec += recebido
        meses_equiv += fracao
        if esperado > ZERO and recebido == ZERO:
            sem_lastro.append(mes)
        tabela.append(OrderedDict([
            ("mes", mes), ("dias_cobertos", dias), ("dias_do_mes", dias_mes),
            ("fracao_mes", str(fracao.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))),
            ("esperado", s2(esperado)), ("recebido", s2(recebido)), ("diferenca", s2(diferenca)),
            ("datas_recebimento", [fmt_data(d) for d, _ in sorted(recebidos)]),
        ]))

    # Sanidade: soma mensal = base x meses equivalentes
    conferencia = base * meses_equiv
    if abs(conferencia - total_esp) > TOLERANCIA:
        raise ValueError(
            f"sanidade do imóvel {im['id']}: soma mensal {total_esp} difere de base x meses equivalentes {conferencia}"
        )

    # Recebimentos fora da janela do imóvel
    fora = [(k[1], sum((v for _, v in lst), ZERO)) for k, lst in rec.items() if k[0] == im["id"] and k[1] not in meses_do_imovel]

    res = OrderedDict()
    res["id"] = im["id"]
    res["descricao"] = im["descricao"]
    res["pais"] = im["pais"]
    res["moeda"] = moeda
    res["situacao"] = im["situacao"]
    res["natureza_do_esperado"] = natureza
    res["aluguel_contratual"] = s2(im["contratual"]) if im["contratual"] is not None else None
    res["aluguel_mercado"] = s2(im["mercado"]) if im["mercado"] is not None else None
    res["fonte_mercado"] = im["fonte_mercado"] or None
    res["gap_contratual_x_mercado_mensal"] = (
        s2(im["mercado"] - im["contratual"]) if im["contratual"] is not None and im["mercado"] is not None else None
    )
    res["periodo"] = OrderedDict([("marco_inicial", fmt_data(im["marco"])), ("fim", fmt_data(im["fim"]))])
    res["meses_equivalentes"] = str(meses_equiv.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
    res["base_mensal"] = s2(base)
    if im["situacao"] == "ocupado_herdeiro":
        res["ocupante"] = im["ocupante"]
        res["fracao_ocupante"] = str(im["fracao_ocupante"].quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
        res["fracao_demais_coerdeiros"] = str((UM - im["fracao_ocupante"]).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
        res["formula"] = "devido = aluguel_mercado x (1 - fracao_ocupante) x meses"
        res["conferencia_formula"] = OrderedDict([
            ("aluguel_mercado", s2(im["mercado"])),
            ("um_menos_fracao", res["fracao_demais_coerdeiros"]),
            ("meses", res["meses_equivalentes"]),
            ("produto", s2(conferencia)),
        ])
        res["encargos_pagos_pelo_espolio"] = s2(im["encargos"])
        res["encargos_nota"] = (
            "IPTU e condomínio posteriores à abertura da sucessão do imóvel de uso exclusivo ficam a cargo do ocupante "
            "(REsp 1.704.528); não abater do quinhão e cobrar como indenização ao mesmo tempo (REsp 1.918.125)"
        )
        if abertura and abertura < im["marco"]:
            alt_meses = sum((f for _, _, _, f in meses_cobertos(abertura, im["fim"], pro_rata)), ZERO)
            alt_valor = base * alt_meses
            res["cenario_alternativo_marco_na_abertura"] = OrderedDict([
                ("marco", fmt_data(abertura)), ("meses_equivalentes", str(alt_meses.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))),
                ("devido", s2(alt_valor)), ("acrescimo_sobre_cenario_base", s2(alt_valor - total_esp)),
                ("nota", "sensibilidade: só prevalece se o juízo fixar o marco na abertura da sucessão"),
            ])
    res["tabela_mensal"] = tabela
    res["total_esperado"] = s2(total_esp)
    res["total_recebido"] = s2(total_rec)
    res["diferenca"] = s2(total_esp - total_rec)
    res["meses_sem_recebimento"] = sem_lastro
    res["recebimentos_fora_da_janela"] = [OrderedDict([("mes", m), ("valor", s2(v))]) for m, v in sorted(fora)]
    res["_total_esp"] = total_esp
    res["_total_rec"] = total_rec
    res["_encargos"] = im["encargos"]
    return res


def escrever_md(saida, caminho):
    linhas = ["## Frutos dos imóveis do espólio", ""]
    for r in saida["imoveis"]:
        m = r["moeda"]
        linhas.append(f"### {r['id']}: {r['descricao']} ({r['situacao']})")
        linhas.append("")
        linhas.append(f"Período {r['periodo']['marco_inicial']} a {r['periodo']['fim']}; base mensal {fmt_moeda(r['base_mensal'], m)} ({r['natureza_do_esperado']}).")
        if r["situacao"] == "ocupado_herdeiro":
            c = r["conferencia_formula"]
            linhas.append(f"Ocupante: {r['ocupante']}, fração {r['fracao_ocupante']}. Fórmula: {fmt_moeda(c['aluguel_mercado'], m)} x {c['um_menos_fracao']} x {c['meses']} meses = {fmt_moeda(c['produto'], m)}.")
        linhas += ["", "| Mês | Fração do mês | Esperado | Recebido | Diferença |", "|---|---:|---:|---:|---:|"]
        for t in r["tabela_mensal"]:
            linhas.append(f"| {t['mes']} | {t['fracao_mes']} | {fmt_moeda(t['esperado'], m)} | {fmt_moeda(t['recebido'], m)} | {fmt_moeda(t['diferenca'], m)} |")
        linhas.append(f"| Total | {r['meses_equivalentes']} | {fmt_moeda(r['total_esperado'], m)} | {fmt_moeda(r['total_recebido'], m)} | {fmt_moeda(r['diferenca'], m)} |")
        if r["meses_sem_recebimento"]:
            linhas.append("")
            linhas.append("Meses sem recebimento: " + ", ".join(r["meses_sem_recebimento"]) + ".")
        if r["situacao"] == "ocupado_herdeiro" and Decimal(r["encargos_pagos_pelo_espolio"]) > ZERO:
            linhas.append("")
            linhas.append(f"Encargos do imóvel pagos pelo espólio: {fmt_moeda(r['encargos_pagos_pelo_espolio'], m)} ({r['encargos_nota']}).")
        linhas.append("")
    linhas += ["## Resumo do que o espólio deixou de receber (sem atualização)", "", "| Moeda | Natureza | Valor |", "|---|---|---:|"]
    for moeda, bloco in saida["resumo_por_moeda"].items():
        for k, v in bloco.items():
            if k != "total":
                linhas.append(f"| {moeda} | {k} | {fmt_moeda(v, moeda)} |")
        linhas.append(f"| {moeda} | total | {fmt_moeda(bloco['total'], moeda)} |")
    linhas += ["", "## Memória de cálculo", ""] + [f"- {x}" for x in saida["memoria"]]
    if saida["avisos"]:
        linhas += ["", "## Avisos", ""] + [f"- {a}" for a in saida["avisos"]]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def escrever_csv(saida, caminho):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["imovel_id", "situacao", "moeda", "mes", "fracao_mes", "esperado", "recebido", "diferenca"])
        for r in saida["imoveis"]:
            for t in r["tabela_mensal"]:
                w.writerow([r["id"], r["situacao"], r["moeda"], t["mes"], t["fracao_mes"], t["esperado"], t["recebido"], t["diferenca"]])


def main():
    parser = argparse.ArgumentParser(description="Frutos dos imóveis do espólio e aluguel devido por herdeiro ocupante (skill auditoria-contabil-espolio).")
    parser.add_argument("--imoveis", required=True, help="CSV de imóveis (ponto e vírgula), ver docstring")
    parser.add_argument("--recebimentos", help="CSV de recebimentos: data;imovel_id;valor;moeda")
    parser.add_argument("--herdeiros", type=int, help="Número de herdeiros, usado como 1/N quando fracao_ocupante vier vazia")
    parser.add_argument("--data-referencia", required=True, help="Data final da apuração (dd/mm/aaaa) quando 'fim' vier vazio")
    parser.add_argument("--abertura-sucessao", help="Data do óbito (dd/mm/aaaa) para o cenário alternativo de marco na abertura")
    parser.add_argument("--sem-pro-rata", action="store_true", help="Conta mês parcial como mês inteiro (padrão: pro rata die, CC art. 1.215)")
    parser.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--md", help="Grava tabelas em Markdown para o laudo")
    parser.add_argument("--csv", help="Grava a tabela mensal em CSV")
    args = parser.parse_args()

    try:
        data_ref = parse_data(args.data_referencia, "data de referência")
        abertura = parse_data(args.abertura_sucessao, "abertura da sucessão") if args.abertura_sucessao else None
        imoveis, avisos = ler_imoveis(args.imoveis, args.herdeiros, data_ref)
        por_id = {im["id"]: im for im in imoveis}
        rec, avisos_rec = ler_recebimentos(args.recebimentos, por_id)
        avisos += avisos_rec
        pro_rata = not args.sem_pro_rata

        resultados = []
        memoria = [f"Data de referência {fmt_data(data_ref)}; mês parcial {'pro rata die (CC, art. 1.215)' if pro_rata else 'contado como mês inteiro'}; moedas apuradas em separado."]
        resumo = OrderedDict()
        for im in imoveis:
            r = processar_imovel(im, rec, pro_rata, abertura)
            moeda = im["moeda"]
            bloco = resumo.setdefault(moeda, OrderedDict([
                ("alugueis_contratuais_nao_recebidos", ZERO), ("aluguel_devido_por_ocupacao_de_herdeiro", ZERO),
                ("encargos_de_imovel_ocupado_pagos_pelo_espolio", ZERO), ("renda_potencial_de_imovel_vago", ZERO),
                ("recebido_a_maior_ou_fora_da_janela", ZERO), ("total", ZERO),
            ]))
            dif = r["_total_esp"] - r["_total_rec"]
            if im["situacao"] == "locado":
                bloco["alugueis_contratuais_nao_recebidos"] += max(dif, ZERO)
            elif im["situacao"] == "ocupado_herdeiro":
                bloco["aluguel_devido_por_ocupacao_de_herdeiro"] += max(dif, ZERO)
                bloco["encargos_de_imovel_ocupado_pagos_pelo_espolio"] += r["_encargos"]
            elif im["situacao"] == "vago":
                bloco["renda_potencial_de_imovel_vago"] += max(dif, ZERO)
            if dif < ZERO:
                bloco["recebido_a_maior_ou_fora_da_janela"] += -dif
                avisos.append(f"imóvel {im['id']}: recebido supera o esperado em {fmt_moeda(-dif, moeda)}; conferir contrato ou classificação")
            for m_fora, v_fora in [(x["mes"], Decimal(x["valor"])) for x in r["recebimentos_fora_da_janela"]]:
                avisos.append(f"imóvel {im['id']}: recebimento de {fmt_moeda(v_fora, moeda)} em {m_fora} fora da janela auditada; não computado")
            memoria.append(
                f"{im['id']} ({im['situacao']}, {moeda}): base {fmt_moeda(r['base_mensal'], moeda)} x {r['meses_equivalentes']} meses = "
                f"esperado {fmt_moeda(r['total_esperado'], moeda)}; recebido {fmt_moeda(r['total_recebido'], moeda)}; diferença {fmt_moeda(r['diferenca'], moeda)}."
            )
            for k in ("_total_esp", "_total_rec", "_encargos"):
                del r[k]
            resultados.append(r)

        for moeda, bloco in resumo.items():
            bloco["total"] = (bloco["alugueis_contratuais_nao_recebidos"] + bloco["aluguel_devido_por_ocupacao_de_herdeiro"]
                              + bloco["encargos_de_imovel_ocupado_pagos_pelo_espolio"])
            memoria.append(
                f"Resumo {moeda}: deixou de receber {fmt_moeda(bloco['total'], moeda)} (contratual não recebido + devido por ocupação + encargos do imóvel ocupado); "
                f"renda potencial de imóvel vago {fmt_moeda(bloco['renda_potencial_de_imovel_vago'], moeda)} informada em separado."
            )
        resumo_str = OrderedDict((moeda, OrderedDict((k, s2(v)) for k, v in bloco.items())) for moeda, bloco in resumo.items())

        saida = OrderedDict()
        saida["skill"] = "auditoria-contabil-espolio"
        saida["script"] = "rendimentos_imoveis.py"
        saida["premissas"] = OrderedDict([
            ("arquivo_imoveis", str(args.imoveis)),
            ("arquivo_recebimentos", str(args.recebimentos) if args.recebimentos else None),
            ("data_referencia", fmt_data(data_ref)),
            ("abertura_sucessao", fmt_data(abertura) if abertura else None),
            ("herdeiros", args.herdeiros),
            ("mes_parcial", "pro rata die (CC, art. 1.215)" if pro_rata else "mês inteiro"),
            ("formula_ocupante", "aluguel_mercado x (1 - fracao_ocupante) x meses desde o marco inicial"),
            ("marco_inicial", "parametrizado por imóvel (oposição, notificação ou citação); cenário alternativo na abertura quando informada"),
            ("moedas", "apuradas em separado; converter euro com conversao_ptax.py antes de somar"),
            ("atualizacao_monetaria", "não aplicada; usar a skill atualizacao-monetaria"),
        ])
        saida["locale"] = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
        saida["arredondamento"] = "ROUND_HALF_UP, 2 casas na apresentação"
        saida["imoveis"] = resultados
        saida["resumo_por_moeda"] = resumo_str
        saida["sanidade"] = OrderedDict([
            ("soma_mensal_igual_base_x_meses_equivalentes", True),
            ("moedas_nao_misturadas", True),
        ])
        saida["avisos"] = avisos
        saida["memoria"] = memoria

        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto, encoding="utf-8")
            print(f"JSON gravado em {args.saida}")
        else:
            print(texto)
        if args.md:
            escrever_md(saida, args.md)
            print(f"Markdown gravado em {args.md}")
        if args.csv:
            escrever_csv(saida, args.csv)
            print(f"CSV gravado em {args.csv}")
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
