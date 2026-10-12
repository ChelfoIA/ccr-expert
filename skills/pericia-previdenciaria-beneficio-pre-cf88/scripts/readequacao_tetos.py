#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Readequação de benefício anterior à CF/88 aos tetos das EC 20/1998 e 41/2003 (Tema 1.140 do
STJ), com evolução mês a mês da renda, equivalência em salários mínimos do art. 58 do ADCT e
apuração da diferença mensal entre a renda devida e a renda paga.

Parte da skill: pericia-previdenciaria-beneficio-pre-cf88

Mecânica implementada (parâmetros e tabelas entram por arquivo ou linha de comando):
  1. Lê a RMI, a média sem limitação, o coeficiente, a fração do excedente e os tetos da DIB
     (JSON de rmi_clps84.py ou valores informados) e classifica a limitação na concessão.
  2. Evolui três rendas desde a DIB: a média sem teto ("salário de benefício evoluído"), a
     renda limitada (RMI evoluída, que é o que o INSS pagou) e a renda devida; aplica os
     cortes de padrão monetário (arquivo de conversões) e os índices oficiais de reajuste.
  3. Na janela do art. 58 do ADCT (padrão 04/1989 a 12/1991), expressa cada renda pelo seu
     número de salários mínimos na DIB vezes o salário mínimo da competência (Súmula 25/TNU).
  4. Em cada emenda (padrão: EC 20/1998 em 12/1998, R$ 1.200,00; EC 41/2003 em 12/2003,
     R$ 2.400,00) aplica os limitadores da época sobre a média evoluída, usando o teto da
     emenda como maior valor-teto e a metade como menor valor-teto, com o mesmo coeficiente e
     a mesma fração do excedente da concessão; a renda devida passa a ser a readequada quando
     esta supera a renda que vinha sendo devida.
  5. Trava a renda devida no teto vigente informado (ou projetado pelos índices) e confronta
     com a renda paga (arquivo de pagamentos; na falta, presume a renda limitada evoluída).
  6. Teste embutido: benefício não limitado na concessão produz diferença zero.

Uso:
    python3 readequacao_tetos.py --rmi rmi_1987.json \
        --reajustes assets/exemplo_reajustes.csv --conversoes assets/exemplo_conversoes.csv \
        --tetos assets/exemplo_tetos.csv --pago assets/exemplo_pagamentos.csv \
        --art58 --salarios-minimos assets/exemplo_salario_minimo.csv \
        --fim 12/2024 --saida readequacao.json --md readequacao.md --csv readequacao.csv

    python3 readequacao_tetos.py --rmi assets/exemplo_rmi_nao_limitado.json \
        --reajustes assets/exemplo_reajustes.csv --conversoes assets/exemplo_conversoes.csv \
        --tetos assets/exemplo_tetos.csv --fim 12/2010 --saida readequacao_nao_limitado.json

Toda operação monetária usa Decimal; o arredondamento a 2 casas (ROUND_HALF_UP) ocorre
apenas na apresentação. Nenhum índice, teto histórico ou salário mínimo é embutido no código;
os únicos valores padrão são os tetos do texto das emendas, com ressalva de conferência.
"""

import argparse
import csv
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, getcontext, InvalidOperation
from pathlib import Path

getcontext().prec = 40

LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
EMENDAS_PADRAO = "12/1998:1200,00:EC 20/1998, art. 14;12/2003:2400,00:EC 41/2003, art. 5º"


class ErroValidacao(Exception):
    """Erro de entrada do usuário: sai com código 1 e mensagem objetiva."""


# ----------------------------------------------------------------------------
# Utilitários de número, data e formatação
# ----------------------------------------------------------------------------

def parse_num(texto):
    """Aceita número no padrão brasileiro (1.234,56) e no técnico (1234.56)."""
    if texto is None:
        raise ErroValidacao("valor numérico ausente")
    s = str(texto).strip()
    for simbolo in ("NCz$", "NCr$", "Cz$", "Cr$", "CR$", "R$"):
        s = s.replace(simbolo, "")
    s = s.replace(" ", "")
    if s == "":
        raise ErroValidacao("valor numérico vazio")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ErroValidacao("número inválido: %r" % texto)


def parse_fracao(texto):
    """Aceita fração 'a/b' (ex.: 1/30) ou número decimal (ex.: 0,8)."""
    s = str(texto).strip()
    if "/" in s:
        num, den = s.split("/", 1)
        den_d = parse_num(den)
        if den_d == 0:
            raise ErroValidacao("fração com denominador zero: %r" % texto)
        return parse_num(num) / den_d
    return parse_num(s)


def parse_comp(texto):
    """Competência mm/aaaa -> (ano, mês)."""
    s = str(texto).strip()
    partes = s.split("/")
    if len(partes) != 2 or not (partes[0].isdigit() and partes[1].isdigit()):
        raise ErroValidacao("competência inválida (esperado mm/aaaa): %r" % texto)
    mes, ano = int(partes[0]), int(partes[1])
    if not 1 <= mes <= 12 or ano < 1900:
        raise ErroValidacao("competência fora de faixa: %r" % texto)
    return (ano, mes)


def comp_str(c):
    return "%02d/%04d" % (c[1], c[0])


def proxima(c):
    ano, mes = c
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def q2(valor):
    return Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt_br(valor, casas=2):
    """Formata Decimal no padrão brasileiro: 1.234,56."""
    v = Decimal(valor).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    negativo = v < 0
    inteiro, _, frac = str(abs(v)).partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    txt = ".".join(grupos)
    if casas > 0:
        txt += "," + (frac or "").ljust(casas, "0")
    return ("-" if negativo else "") + txt


def ler_csv(caminho, obrigatorias):
    """Lê CSV com separador ';' (ou ',' se não houver ';' no cabeçalho)."""
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao("arquivo não encontrado: %s" % caminho)
    texto = p.read_text(encoding="utf-8-sig")
    linhas = [l for l in texto.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    if not linhas:
        raise ErroValidacao("arquivo vazio: %s" % caminho)
    sep = ";" if ";" in linhas[0] else ","
    leitor = csv.DictReader(linhas, delimiter=sep)
    campos = [c.strip().lower() for c in (leitor.fieldnames or [])]
    faltantes = [c for c in obrigatorias if c not in campos]
    if faltantes:
        raise ErroValidacao("%s sem as colunas obrigatórias %s (encontradas: %s)"
                            % (caminho, faltantes, campos))
    registros = []
    for linha in leitor:
        registros.append({(k or "").strip().lower(): (v or "").strip() for k, v in linha.items()})
    return registros


class CodificadorDecimal(json.JSONEncoder):
    """Decimal já quantizado sai como número JSON; a conta nunca usa float."""

    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


# ----------------------------------------------------------------------------
# Carga das entradas
# ----------------------------------------------------------------------------

def carregar_rmi(args):
    """Lê o bloco para_readequacao do JSON de rmi_clps84.py ou os valores da linha de comando."""
    caminho = Path(args.rmi)
    if caminho.is_file():
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ErroValidacao("JSON da RMI inválido (%s): %s" % (args.rmi, e))
        bloco = dados.get("para_readequacao")
        if not bloco:
            raise ErroValidacao("o JSON %s não traz o bloco para_readequacao de rmi_clps84.py" % args.rmi)
        obrig = ["dib", "moeda_dib", "media", "rmi", "coeficiente", "fracao_excedente_efetiva",
                 "menor_valor_teto", "maior_valor_teto"]
        falt = [k for k in obrig if bloco.get(k) in (None, "")]
        if falt:
            raise ErroValidacao("bloco para_readequacao sem os campos %s" % falt)
        base = {
            "origem": "JSON de rmi_clps84.py: %s" % args.rmi,
            "dib": parse_comp(bloco["dib"]),
            "moeda_dib": bloco["moeda_dib"],
            "media": Decimal(str(bloco["media"])),
            "rmi": Decimal(str(bloco["rmi"])),
            "coeficiente": Decimal(str(bloco["coeficiente"])),
            "fracao": Decimal(str(bloco["fracao_excedente_efetiva"])),
            "menor_teto": Decimal(str(bloco["menor_valor_teto"])),
            "maior_teto": Decimal(str(bloco["maior_valor_teto"])),
            "sm_dib": Decimal(str(bloco["salario_minimo_dib"])) if bloco.get("salario_minimo_dib") else None,
            "fonte_sm": bloco.get("fonte_salario_minimo") or "",
            "limitacao_informada": bloco.get("limitacao_na_concessao") or "",
        }
    else:
        falt = [n for n, v in (("--media", args.media), ("--coeficiente", args.coeficiente),
                                ("--menor-teto", args.menor_teto), ("--maior-teto", args.maior_teto),
                                ("--dib", args.dib), ("--moeda-dib", args.moeda_dib)) if not v]
        if falt:
            raise ErroValidacao("--rmi informado como valor exige também %s" % ", ".join(falt))
        base = {
            "origem": "valores da linha de comando",
            "dib": parse_comp(args.dib),
            "moeda_dib": args.moeda_dib,
            "media": parse_num(args.media),
            "rmi": parse_num(args.rmi),
            "coeficiente": parse_num(args.coeficiente) / Decimal(100),
            "fracao": parse_fracao(args.fracao_excedente) if args.fracao_excedente else Decimal(0),
            "menor_teto": parse_num(args.menor_teto),
            "maior_teto": parse_num(args.maior_teto),
            "sm_dib": parse_num(args.salario_minimo_dib) if args.salario_minimo_dib else None,
            "fonte_sm": args.fonte_sm or "",
            "limitacao_informada": "",
        }
    # Sobreposições opcionais da linha de comando
    if args.salario_minimo_dib and caminho.is_file():
        base["sm_dib"] = parse_num(args.salario_minimo_dib)
        base["fonte_sm"] = args.fonte_sm or base["fonte_sm"]
    if base["media"] <= 0 or base["rmi"] <= 0:
        raise ErroValidacao("média e RMI precisam ser positivas")
    if base["menor_teto"] <= 0 or base["maior_teto"] < base["menor_teto"]:
        raise ErroValidacao("tetos da DIB inválidos (menor valor-teto positivo e não superior ao maior)")
    if not (Decimal(0) < base["coeficiente"] <= Decimal("1.5")):
        raise ErroValidacao("coeficiente fora da faixa plausível (0 a 150%)")
    if not (Decimal(0) <= base["fracao"] <= Decimal(1)):
        raise ErroValidacao("fração efetiva do excedente fora de 0 a 1")
    if base["sm_dib"] is not None and base["sm_dib"] <= 0:
        raise ErroValidacao("salário mínimo da DIB deve ser positivo")
    # Classificação da limitação na concessão, recomputada a partir dos números
    if base["media"] > base["maior_teto"]:
        lim = "maior valor-teto"
    elif base["media"] > base["menor_teto"]:
        lim = "menor valor-teto (excedente fracionado)"
    else:
        lim = "não limitado"
    base["limitacao"] = lim
    return base


def carregar_reajustes(caminho):
    regs = ler_csv(caminho, ["competencia", "indice_percentual", "fonte"])
    out = {}
    for r in regs:
        c = parse_comp(r["competencia"])
        if c in out:
            raise ErroValidacao("competência repetida nos reajustes: %s" % comp_str(c))
        i = parse_num(r["indice_percentual"])
        if i < -100:
            raise ErroValidacao("índice de reajuste inferior a -100%% em %s" % comp_str(c))
        if not r["fonte"]:
            raise ErroValidacao("reajuste de %s sem fonte" % comp_str(c))
        out[c] = {"pct": i, "fonte": r["fonte"]}
    return out


def carregar_conversoes(caminho):
    regs = ler_csv(caminho, ["competencia", "divisor", "moeda_nova", "fonte"])
    out = {}
    for r in regs:
        c = parse_comp(r["competencia"])
        d = parse_num(r["divisor"])
        if d <= 0:
            raise ErroValidacao("divisor não positivo na conversão de %s" % comp_str(c))
        out[c] = {"divisor": d, "moeda_nova": r["moeda_nova"], "fonte": r["fonte"]}
    return out


def carregar_tetos(caminho):
    regs = ler_csv(caminho, ["competencia", "teto", "fonte"])
    out = {}
    for r in regs:
        c = parse_comp(r["competencia"])
        v = parse_num(r["teto"])
        if v <= 0:
            raise ErroValidacao("teto não positivo em %s" % comp_str(c))
        if not r["fonte"]:
            raise ErroValidacao("teto de %s sem fonte" % comp_str(c))
        out[c] = {"valor": v, "moeda": r.get("moeda") or "", "fonte": r["fonte"]}
    return out


def carregar_pagamentos(caminho):
    regs = ler_csv(caminho, ["competencia", "valor_pago"])
    out = {}
    for r in regs:
        c = parse_comp(r["competencia"])
        if c in out:
            raise ErroValidacao("competência repetida nos pagamentos: %s" % comp_str(c))
        v = parse_num(r["valor_pago"])
        if v < 0:
            raise ErroValidacao("valor pago negativo em %s" % comp_str(c))
        out[c] = {"valor": v, "moeda": r.get("moeda") or ""}
    return out


def carregar_salarios_minimos(caminho):
    regs = ler_csv(caminho, ["competencia", "valor", "fonte"])
    lista = []
    for r in regs:
        c = parse_comp(r["competencia"])
        v = parse_num(r["valor"])
        if v <= 0:
            raise ErroValidacao("salário mínimo não positivo em %s" % comp_str(c))
        if not r["fonte"]:
            raise ErroValidacao("salário mínimo de %s sem fonte" % comp_str(c))
        lista.append({"competencia": c, "valor": v, "moeda": r.get("moeda") or "", "fonte": r["fonte"]})
    lista.sort(key=lambda x: x["competencia"])
    return lista


def sm_vigente(lista, c):
    """Salário mínimo em vigor na competência: última linha com competência não posterior."""
    atual = None
    for item in lista:
        if item["competencia"] <= c:
            atual = item
        else:
            break
    return atual


def parse_emendas(texto):
    """'mm/aaaa:valor:fonte;mm/aaaa:valor:fonte' -> lista ordenada."""
    out = []
    for parte in texto.split(";"):
        parte = parte.strip()
        if not parte:
            continue
        campos = parte.split(":", 2)
        if len(campos) < 2:
            raise ErroValidacao("emenda mal formada (esperado mm/aaaa:valor:fonte): %r" % parte)
        c = parse_comp(campos[0])
        v = parse_num(campos[1])
        if v <= 0:
            raise ErroValidacao("teto de emenda não positivo em %s" % comp_str(c))
        out.append({"competencia": c, "teto": v, "fonte": campos[2].strip() if len(campos) == 3 else ""})
    out.sort(key=lambda x: x["competencia"])
    return out


# ----------------------------------------------------------------------------
# Núcleo do cálculo
# ----------------------------------------------------------------------------

def readequar(sb, teto_ec, coef, fracao):
    """Limitadores da época sobre a média evoluída: maior valor-teto = teto da emenda,
    menor valor-teto = metade (tese do Tema 1.140 do STJ)."""
    maior = teto_ec
    menor = teto_ec / Decimal(2)
    sb_lim = min(sb, maior)
    base = min(sb_lim, menor)
    exced = max(Decimal(0), sb_lim - menor)
    renda = coef * (base + fracao * exced)
    return {"maior_valor_teto": maior, "menor_valor_teto": menor, "sb_evoluido": sb,
            "sb_limitado": sb_lim, "parcela_ate_menor_teto": base, "excedente": exced,
            "parcela_excedente_considerada": fracao * exced, "renda_readequada": renda}


def calcular(args):
    base = carregar_rmi(args)
    reaj = carregar_reajustes(args.reajustes)
    conv = carregar_conversoes(args.conversoes) if args.conversoes else {}
    tetos = carregar_tetos(args.tetos) if args.tetos else {}
    pagos = carregar_pagamentos(args.pago) if args.pago else {}
    sms = carregar_salarios_minimos(args.salarios_minimos) if args.salarios_minimos else []
    emendas = [] if args.sem_emendas else parse_emendas(args.emendas)
    avisos = []
    memoria = []

    dib = base["dib"]
    if args.inicio:
        inicio = parse_comp(args.inicio)
        if inicio < dib:
            raise ErroValidacao("--inicio não pode ser anterior à DIB")
    else:
        inicio = dib
    candidatos = [max(d) for d in (reaj, tetos, pagos) if d]
    if args.fim:
        fim = parse_comp(args.fim)
    elif candidatos:
        fim = max(candidatos)
    else:
        raise ErroValidacao("informe --fim (mm/aaaa) ou arquivos com competências para delimitar o período")
    if fim < inicio:
        raise ErroValidacao("--fim anterior ao início do período")

    # Art. 58 do ADCT
    art58_ini = parse_comp(args.art58_inicio)
    art58_fim = parse_comp(args.art58_fim)
    if art58_fim < art58_ini:
        raise ErroValidacao("janela do art. 58 invertida")
    aplica_art58 = bool(args.art58)
    if aplica_art58:
        if not sms:
            raise ErroValidacao("--art58 exige --salarios-minimos (competencia;valor;moeda;fonte)")
        if base["sm_dib"] is None:
            raise ErroValidacao("--art58 exige o salário mínimo da DIB (JSON de rmi_clps84.py com "
                                "--salario-minimo-dib, ou --salario-minimo-dib aqui, com --fonte-sm)")
        if dib > art58_ini:
            raise ErroValidacao("a DIB (%s) é posterior ao início da janela do art. 58 (%s): o art. 58 "
                                "alcança benefícios mantidos na promulgação da CF/88"
                                % (comp_str(dib), comp_str(art58_ini)))
    if sms and not aplica_art58:
        avisos.append("arquivo de salários mínimos informado sem --art58: ignorado")

    coef = base["coeficiente"]
    fracao = base["fracao"]
    limitacao = base["limitacao"]
    if base["limitacao_informada"] and base["limitacao_informada"] != limitacao:
        avisos.append("limitação informada no JSON (%s) difere da recomputada (%s); prevalece a recomputada"
                      % (base["limitacao_informada"], limitacao))
    if args.criterio_limitacao == "maior":
        aplicavel = limitacao == "maior valor-teto"
        motivo = ("benefício limitado ao maior valor-teto na concessão" if aplicavel else
                  "benefício não limitado ao maior valor-teto na concessão (%s): sem readequação pelo "
                  "critério 'maior' (linha do TRF1)" % limitacao)
    else:
        aplicavel = limitacao != "não limitado"
        motivo = ("benefício limitado na concessão (%s)" % limitacao if aplicavel else
                  "benefício não limitado na concessão: sem readequação")
    if not emendas:
        aplicavel_emendas = False
        avisos.append("sem emendas: a evolução confronta apenas a renda limitada com a renda paga")
    else:
        aplicavel_emendas = aplicavel

    # Estado inicial na DIB
    moeda = base["moeda_dib"]
    sb = base["media"]
    lim = base["rmi"]
    dev = base["rmi"]
    teto = base["maior_teto"]
    teto_origem = "maior valor-teto da DIB"
    media_em_sm = (base["media"] / base["sm_dib"]) if base["sm_dib"] else None
    rmi_em_sm = (base["rmi"] / base["sm_dib"]) if base["sm_dib"] else None
    teto_em_sm = (base["maior_teto"] / base["sm_dib"]) if base["sm_dib"] else None

    memoria.append("RMI %s %s na DIB %s (%s); média sem limitação %s; coeficiente %s%%; fração efetiva "
                   "do excedente %s; menor e maior valor-teto da DIB %s e %s; limitação na concessão: %s."
                   % (moeda, fmt_br(lim), comp_str(dib), base["origem"], fmt_br(sb), fmt_br(coef * 100),
                      fmt_br(fracao, 6), fmt_br(base["menor_teto"]), fmt_br(base["maior_teto"]), limitacao))
    memoria.append("Readequação às emendas: %s. Critério de limitação: %s."
                   % ("aplicável" if aplicavel_emendas else "não aplicável", args.criterio_limitacao))
    if rmi_em_sm is not None:
        memoria.append("Salário mínimo na DIB %s %s (fonte: %s): RMI = %s SM; média = %s SM; maior valor-teto = %s SM."
                       % (moeda, fmt_br(base["sm_dib"]), base["fonte_sm"] or "não informada", fmt_br(rmi_em_sm, 4),
                          fmt_br(media_em_sm, 4), fmt_br(teto_em_sm, 4)))

    emenda_por_comp = {e["competencia"]: e for e in emendas}
    for e in emendas:
        if e["competencia"] < dib:
            raise ErroValidacao("emenda em %s anterior à DIB %s" % (comp_str(e["competencia"]), comp_str(dib)))
    blocos_emendas = []
    emenda_aplicada = False
    evolucao = []
    c = dib
    while c <= fim:
        eventos = []
        # 1. Corte de padrão monetário (apenas cortes posteriores à DIB)
        if c in conv and c > dib:
            d = conv[c]["divisor"]
            sb, lim, dev = sb / d, lim / d, dev / d
            if teto is not None:
                teto = teto / d
            moeda = conv[c]["moeda_nova"]
            eventos.append("conversão para %s (divisor %s; %s)" % (moeda, fmt_br(d, 0), conv[c]["fonte"]))
        # 2. Reajuste oficial
        pct = None
        if c in reaj:
            pct = reaj[c]["pct"]
            fator = Decimal(1) + pct / Decimal(100)
            sb, lim, dev = sb * fator, lim * fator, dev * fator
            if teto is not None:
                teto = teto * fator
                teto_origem = "projetado pelos índices"
            eventos.append("reajuste de %s%% (%s)" % (fmt_br(pct), reaj[c]["fonte"]))
        # 3. Art. 58 do ADCT: equivalência em salários mínimos
        sm_val = None
        if aplica_art58 and art58_ini <= c <= art58_fim:
            item = sm_vigente(sms, c)
            if item is None:
                raise ErroValidacao("sem salário mínimo para %s no arquivo informado" % comp_str(c))
            if item["moeda"] and item["moeda"] != moeda:
                raise ErroValidacao("salário mínimo de %s está em %s, mas a moeda da competência é %s"
                                    % (comp_str(c), item["moeda"], moeda))
            sm_val = item["valor"]
            sb = media_em_sm * sm_val
            lim = rmi_em_sm * sm_val
            if not emenda_aplicada:
                dev = lim
            else:
                dev = max(dev, lim)
            if c not in tetos:
                teto = teto_em_sm * sm_val
                teto_origem = "projetado por salários mínimos"
            eventos.append("art. 58 do ADCT: %s SM x %s (%s)" % (fmt_br(rmi_em_sm, 4), fmt_br(sm_val), item["fonte"]))
        # 4. Teto informado por arquivo
        if c in tetos:
            if tetos[c]["moeda"] and tetos[c]["moeda"] != moeda:
                raise ErroValidacao("teto de %s está em %s, mas a moeda da competência é %s"
                                    % (comp_str(c), tetos[c]["moeda"], moeda))
            teto = tetos[c]["valor"]
            teto_origem = "informado (%s)" % tetos[c]["fonte"]
        # 5. Emenda constitucional: readequação pelos limitadores da época
        if c in emenda_por_comp:
            e = emenda_por_comp[c]
            if moeda != "R$":
                raise ErroValidacao("emenda em %s com a renda em %s: o arquivo de conversões precisa levar a "
                                    "renda ao real antes das emendas" % (comp_str(c), moeda))
            teto = e["teto"]
            teto_origem = "teto da emenda (%s)" % (e["fonte"] or "sem fonte")
            bloco = readequar(sb, e["teto"], coef, fracao)
            bloco_out = {
                "competencia": comp_str(c), "fonte": e["fonte"], "moeda": moeda,
                "renda_devida_antes": q2(dev), "renda_limitada_evoluida": q2(lim),
                "aplicada": False, "acrescimo": q2(Decimal(0)),
            }
            for k, v in bloco.items():
                bloco_out[k] = q2(v)
            if aplicavel_emendas and bloco["renda_readequada"] > dev:
                bloco_out["aplicada"] = True
                bloco_out["acrescimo"] = q2(bloco["renda_readequada"] - dev)
                dev = bloco["renda_readequada"]
                emenda_aplicada = True
                eventos.append("readequação %s: renda devida %s" % (e["fonte"] or comp_str(c), fmt_br(dev)))
            else:
                eventos.append("emenda %s sem acréscimo (%s)" % (e["fonte"] or comp_str(c),
                               "não aplicável" if not aplicavel_emendas else "readequada não supera a devida"))
            bloco_out["renda_devida_depois"] = q2(dev)
            blocos_emendas.append(bloco_out)
            memoria.append("Emenda em %s (%s): média evoluída %s %s; maior valor-teto %s; menor valor-teto %s; "
                           "parcela até o menor %s; excedente %s x fração %s = %s; renda readequada = %s%% x %s = %s; "
                           "renda devida antes %s; %s."
                           % (comp_str(c), e["fonte"], moeda, fmt_br(sb), fmt_br(bloco["maior_valor_teto"]),
                              fmt_br(bloco["menor_valor_teto"]), fmt_br(bloco["parcela_ate_menor_teto"]),
                              fmt_br(bloco["excedente"]), fmt_br(fracao, 6),
                              fmt_br(bloco["parcela_excedente_considerada"]), fmt_br(coef * 100),
                              fmt_br(bloco["parcela_ate_menor_teto"] + bloco["parcela_excedente_considerada"]),
                              fmt_br(bloco["renda_readequada"]), fmt_br(bloco_out["renda_devida_antes"]),
                              "aplicada" if bloco_out["aplicada"] else "não aplicada"))
        # 6. Trava no teto vigente
        travada = False
        if teto is not None and not args.sem_trava_teto and dev > teto + Decimal("0.000001"):
            eventos.append("renda devida travada no teto %s" % fmt_br(teto))
            dev = teto
            travada = True
        if teto is not None and lim > teto + Decimal("0.01"):
            avisos.append("em %s a renda limitada evoluída (%s) supera o teto (%s): conferir índices e tetos"
                          % (comp_str(c), fmt_br(lim), fmt_br(teto)))
        # 7. Renda paga
        if c in pagos:
            if pagos[c]["moeda"] and pagos[c]["moeda"] != moeda:
                raise ErroValidacao("pagamento de %s está em %s, mas a moeda da competência é %s"
                                    % (comp_str(c), pagos[c]["moeda"], moeda))
            paga = pagos[c]["valor"]
            origem_paga = "informado"
        else:
            paga = lim
            origem_paga = "presumido (renda limitada evoluída)"
        dif_bruta = dev - paga
        dif = dif_bruta if dif_bruta > 0 else Decimal(0)
        evolucao.append({
            "competencia": comp_str(c), "moeda": moeda,
            "indice_pct": q2(pct) if pct is not None else None,
            "salario_minimo": q2(sm_val) if sm_val is not None else None,
            "sb_sem_teto": q2(sb), "renda_limitada_evoluida": q2(lim),
            "teto_vigente": q2(teto) if teto is not None else None, "origem_teto": teto_origem,
            "renda_devida": q2(dev), "travada_no_teto": travada,
            "renda_paga": q2(paga), "origem_renda_paga": origem_paga,
            "diferenca_bruta": q2(dif_bruta), "diferenca": q2(dif),
            "eventos": "; ".join(eventos),
            "_dev": dev, "_paga": paga, "_dif": dif, "_lim": lim, "_teto": teto,
        })
        c = proxima(c)

    pagos_fora = [comp_str(k) for k in pagos if not (inicio <= k <= fim)]
    if pagos_fora:
        avisos.append("%d pagamento(s) fora do período calculado foram ignorados" % len(pagos_fora))

    # Totais por moeda (não se somam valores de moedas diferentes)
    totais = {}
    for l in evolucao:
        t = totais.setdefault(l["moeda"], {"meses": 0, "meses_com_diferenca": 0, "diferenca": Decimal(0),
                                            "primeira_competencia_com_diferenca": None})
        t["meses"] += 1
        if l["_dif"] > 0:
            t["meses_com_diferenca"] += 1
            t["diferenca"] += l["_dif"]
            if t["primeira_competencia_com_diferenca"] is None:
                t["primeira_competencia_com_diferenca"] = l["competencia"]
    negativos = [l["competencia"] for l in evolucao if l["_paga"] - l["_dev"] > Decimal("0.01")]
    if negativos:
        avisos.append("renda paga superior à devida em %d competência(s) (ex.: %s): diferença zerada nessas "
                      "competências; conferir se houve outra revisão" % (len(negativos), negativos[0]))

    # Testes de sanidade
    testes = []
    soma_dif = sum((l["_dif"] for l in evolucao), Decimal(0))
    soma_tot = sum((t["diferenca"] for t in totais.values()), Decimal(0))
    testes.append(("soma das diferenças por moeda fecha com a soma da evolução", abs(soma_dif - soma_tot) < Decimal("0.000001")))
    testes.append(("renda devida nunca inferior à renda limitada evoluída",
                   all(l["_dev"] >= l["_lim"] - Decimal("0.000001") for l in evolucao)))
    testes.append(("renda devida não excede o teto vigente conhecido",
                   args.sem_trava_teto or all(l["_teto"] is None or l["_dev"] <= l["_teto"] + Decimal("0.000001")
                                              for l in evolucao)))
    testes.append(("nenhuma diferença negativa", all(l["_dif"] >= 0 for l in evolucao)))
    if limitacao == "não limitado":
        testes.append(("benefício não limitado na concessão: diferença zero em toda a evolução", soma_dif == 0))
    if not aplicavel_emendas:
        presumidas = all(l["origem_renda_paga"].startswith("presumido") for l in evolucao)
        if presumidas:
            testes.append(("readequação não aplicável e renda paga presumida: diferença zero", soma_dif == 0))
    reprovados = [t for t, ok in testes if not ok]
    if reprovados:
        raise ErroValidacao("teste de sanidade reprovado: %s" % "; ".join(reprovados))

    memoria.append("Período evoluído de %s a %s, %d competências; renda paga lida de %s em %d competência(s) e "
                   "presumida (renda limitada evoluída) nas demais."
                   % (comp_str(dib), comp_str(fim), len(evolucao), args.pago or "nenhum arquivo",
                      sum(1 for l in evolucao if l["origem_renda_paga"] == "informado")))
    for m, t in totais.items():
        memoria.append("Em %s: %d competências, %d com diferença, soma nominal das diferenças %s %s%s."
                       % (m, t["meses"], t["meses_com_diferenca"], m, fmt_br(t["diferenca"]),
                          ("; primeira em %s" % t["primeira_competencia_com_diferenca"])
                          if t["primeira_competencia_com_diferenca"] else ""))

    linhas_saida = []
    for l in evolucao:
        linhas_saida.append({k: v for k, v in l.items() if not k.startswith("_")})
    # Encadeamento com 8 casas decimais: precisão muito acima do centavo, sem inflar o JSON
    q8 = Decimal("0.00000001")
    para_atrasados = [{"competencia": l["competencia"], "moeda": l["moeda"],
                       "renda_devida": str(l["_dev"].quantize(q8, rounding=ROUND_HALF_UP)),
                       "renda_paga": str(l["_paga"].quantize(q8, rounding=ROUND_HALF_UP)),
                       "diferenca": str(l["_dif"].quantize(q8, rounding=ROUND_HALF_UP)),
                       "origem_renda_paga": l["origem_renda_paga"]} for l in evolucao]

    resultado = {
        "skill": "pericia-previdenciaria-beneficio-pre-cf88",
        "script": "readequacao_tetos.py",
        "premissas": {
            "origem_rmi": base["origem"],
            "dib": comp_str(dib), "fim": comp_str(fim), "moeda_dib": base["moeda_dib"],
            "rmi": q2(base["rmi"]), "media_sem_limitacao": q2(base["media"]),
            "coeficiente_pct": q2(coef * 100), "fracao_excedente_efetiva": fracao.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            "menor_valor_teto_dib": q2(base["menor_teto"]), "maior_valor_teto_dib": q2(base["maior_teto"]),
            "salario_minimo_dib": q2(base["sm_dib"]) if base["sm_dib"] is not None else None,
            "limitacao_na_concessao": limitacao,
            "limitado_na_concessao": limitacao != "não limitado",
            "limitado_ao_maior_valor_teto": limitacao == "maior valor-teto",
            "criterio_limitacao": args.criterio_limitacao,
            "readequacao_aplicavel": aplicavel_emendas, "motivo": motivo,
            "emendas": [{"competencia": comp_str(e["competencia"]), "teto": q2(e["teto"]),
                         "menor_valor_teto": q2(e["teto"] / 2), "fonte": e["fonte"]} for e in emendas],
            "ressalva_emendas": "tetos das emendas lidos do texto da EC 20/1998, art. 14, e da EC 41/2003, art. 5º; "
                                "conferir em planalto.gov.br antes do laudo",
            "art58": {"aplicado": aplica_art58, "inicio": comp_str(art58_ini), "fim": comp_str(art58_fim),
                      "arquivo_salarios_minimos": args.salarios_minimos or "",
                      "rmi_em_salarios_minimos": (rmi_em_sm.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                                                  if rmi_em_sm is not None else None),
                      "criterio": "número de salários mínimos na data da concessão (Súmula 25 da TNU)"},
            "trava_no_teto": not args.sem_trava_teto,
            "teto_entre_competencias": "último teto informado, projetado pelos índices de reajuste; na janela do "
                                       "art. 58, projetado por salários mínimos",
            "renda_paga_ausente": "presumida igual à renda limitada evoluída (RMI reajustada)",
            "arquivos": {"reajustes": args.reajustes, "conversoes": args.conversoes or "",
                         "tetos": args.tetos or "", "pagamentos": args.pago or ""},
            "moeda": "cada competência declara a moeda; os cortes vêm do arquivo de conversões, obtido com "
                     "padroes_monetarios.py da skill atualizacao-monetaria",
        },
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "emendas": blocos_emendas,
        "totais_por_moeda": {m: {"meses": t["meses"], "meses_com_diferenca": t["meses_com_diferenca"],
                                 "diferenca_nominal": q2(t["diferenca"]),
                                 "primeira_competencia_com_diferenca": t["primeira_competencia_com_diferenca"]}
                             for m, t in totais.items()},
        "evolucao": linhas_saida,
        "testes_sanidade": [{"teste": t, "ok": ok} for t, ok in testes],
        "avisos": avisos,
        "memoria": memoria,
        "para_atrasados": {"dib": comp_str(dib), "fim": comp_str(fim), "coeficiente": str(coef),
                           "precisao": "8 casas decimais no encadeamento; apresentação com 2 casas",
                           "limitacao_na_concessao": limitacao, "readequacao_aplicavel": aplicavel_emendas,
                           "linhas": para_atrasados},
    }
    return resultado


def gerar_md(res):
    p = res["premissas"]
    linhas = ["# Readequação aos tetos das emendas (Tema 1.140 do STJ): DIB %s" % p["dib"], ""]
    linhas.append("Limitação na concessão: %s. Readequação: %s (%s)."
                  % (p["limitacao_na_concessao"], "aplicável" if p["readequacao_aplicavel"] else "não aplicável", p["motivo"]))
    linhas.append("")
    if res["emendas"]:
        linhas.append("| Emenda | Média evoluída | Maior valor-teto | Menor valor-teto | Parcela até o menor | Excedente considerado | Renda readequada | Renda devida antes | Acréscimo | Aplicada |")
        linhas.append("|---|---|---|---|---|---|---|---|---|---|")
        for b in res["emendas"]:
            linhas.append("| %s (%s) | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                b["competencia"], b["fonte"], fmt_br(b["sb_evoluido"]), fmt_br(b["maior_valor_teto"]),
                fmt_br(b["menor_valor_teto"]), fmt_br(b["parcela_ate_menor_teto"]),
                fmt_br(b["parcela_excedente_considerada"]), fmt_br(b["renda_readequada"]),
                fmt_br(b["renda_devida_antes"]), fmt_br(b["acrescimo"]), "sim" if b["aplicada"] else "não"))
        linhas.append("")
    linhas.append("| Moeda | Meses | Meses com diferença | Diferença nominal | Primeira competência |")
    linhas.append("|---|---|---|---|---|")
    for m, t in res["totais_por_moeda"].items():
        linhas.append("| %s | %d | %d | %s | %s |" % (m, t["meses"], t["meses_com_diferenca"],
                                                     fmt_br(t["diferenca_nominal"]),
                                                     t["primeira_competencia_com_diferenca"] or "-"))
    linhas.append("")
    linhas.append("| Competência | Moeda | Índice % | SM | SB sem teto | Renda limitada | Teto | Renda devida | Renda paga | Origem | Diferença | Eventos |")
    linhas.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for l in res["evolucao"]:
        linhas.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            l["competencia"], l["moeda"],
            fmt_br(l["indice_pct"]) if l["indice_pct"] is not None else "",
            fmt_br(l["salario_minimo"]) if l["salario_minimo"] is not None else "",
            fmt_br(l["sb_sem_teto"]), fmt_br(l["renda_limitada_evoluida"]),
            fmt_br(l["teto_vigente"]) if l["teto_vigente"] is not None else "",
            fmt_br(l["renda_devida"]), fmt_br(l["renda_paga"]), l["origem_renda_paga"],
            fmt_br(l["diferenca"]), l["eventos"]))
    linhas.append("")
    linhas.append("Memória:")
    for i, t in enumerate(res["memoria"], start=1):
        linhas.append("%d. %s" % (i, t))
    if res["avisos"]:
        linhas.append("")
        linhas.append("Avisos:")
        for a in res["avisos"]:
            linhas.append("- %s" % a)
    return "\n".join(linhas) + "\n"


def gerar_csv(res):
    cab = ["competencia", "moeda", "indice_pct", "salario_minimo", "sb_sem_teto", "renda_limitada_evoluida",
           "teto_vigente", "renda_devida", "renda_paga", "origem_renda_paga", "diferenca", "eventos"]
    linhas = [";".join(cab)]
    for l in res["evolucao"]:
        vals = []
        for k in cab:
            v = l[k]
            if isinstance(v, Decimal):
                v = fmt_br(v)
            elif v is None:
                v = ""
            vals.append(str(v))
        linhas.append(";".join(vals))
    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Readequação de benefício anterior à CF/88 aos tetos das EC 20/1998 e 41/2003 "
                    "(skill pericia-previdenciaria-beneficio-pre-cf88)")
    parser.add_argument("--rmi", required=True,
                        help="JSON gerado por rmi_clps84.py ou valor da RMI na DIB (exige --media, --coeficiente, "
                             "--menor-teto, --maior-teto, --dib e --moeda-dib)")
    parser.add_argument("--media", default=None, help="média sem limitação na DIB (quando --rmi é valor)")
    parser.add_argument("--coeficiente", default=None, help="coeficiente da espécie em percentual (quando --rmi é valor)")
    parser.add_argument("--fracao-excedente", default=None,
                        help="fração efetiva do excedente aplicada na concessão (ex.: 0,8 ou 24/30), quando --rmi é valor")
    parser.add_argument("--menor-teto", default=None, help="menor valor-teto na DIB (quando --rmi é valor)")
    parser.add_argument("--maior-teto", default=None, help="maior valor-teto na DIB (quando --rmi é valor)")
    parser.add_argument("--dib", default=None, help="competência da DIB, mm/aaaa (quando --rmi é valor)")
    parser.add_argument("--moeda-dib", default=None, help="moeda da DIB, ex.: Cz$ (quando --rmi é valor)")
    parser.add_argument("--salario-minimo-dib", default=None, help="salário mínimo na DIB (sobrepõe o JSON)")
    parser.add_argument("--fonte-sm", default=None, help="fonte do salário mínimo da DIB")
    parser.add_argument("--reajustes", required=True,
                        help="CSV competencia;indice_percentual;fonte com os reajustes oficiais dos benefícios")
    parser.add_argument("--conversoes", default=None,
                        help="CSV competencia;divisor;moeda_nova;fonte com os cortes de padrão monetário")
    parser.add_argument("--tetos", default=None, help="CSV competencia;teto;moeda;fonte com os tetos informados")
    parser.add_argument("--pago", default=None, help="CSV competencia;valor_pago;moeda com a renda paga (HISCRE)")
    parser.add_argument("--emendas", default=EMENDAS_PADRAO,
                        help="emendas no formato mm/aaaa:teto:fonte;... (padrão: EC 20/1998 e EC 41/2003, "
                             "valores do texto das emendas, a conferir)")
    parser.add_argument("--sem-emendas", action="store_true", help="não aplica readequação alguma")
    parser.add_argument("--criterio-limitacao", choices=["maior", "qualquer"], default="maior",
                        help="'maior': readequa só benefício limitado ao maior valor-teto (padrão); 'qualquer': "
                             "também o limitado pelo menor valor-teto com excedente fracionado")
    parser.add_argument("--art58", action="store_true",
                        help="aplica a equivalência em salários mínimos do art. 58 do ADCT na janela informada")
    parser.add_argument("--salarios-minimos", default=None,
                        help="CSV competencia;valor;moeda;fonte com o salário mínimo (linhas nas alterações)")
    parser.add_argument("--art58-inicio", default="04/1989", help="início da janela do art. 58 (padrão 04/1989)")
    parser.add_argument("--art58-fim", default="12/1991", help="fim da janela do art. 58 (padrão 12/1991)")
    parser.add_argument("--sem-trava-teto", action="store_true", help="não trava a renda devida no teto vigente")
    parser.add_argument("--inicio", default=None, help="primeira competência a evoluir (padrão: DIB)")
    parser.add_argument("--fim", default=None, help="última competência (padrão: maior competência dos arquivos)")
    parser.add_argument("--saida", default=None, help="arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--md", default=None, help="grava a memória em Markdown neste arquivo")
    parser.add_argument("--csv", default=None, help="grava a evolução mês a mês em CSV neste arquivo")
    args = parser.parse_args()

    try:
        res = calcular(args)
        texto = json.dumps(res, ensure_ascii=False, indent=2, cls=CodificadorDecimal)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            resumo = "; ".join("%s %s em %d mês(es)" % (m, fmt_br(t["diferenca_nominal"]), t["meses_com_diferenca"])
                               for m, t in res["totais_por_moeda"].items())
            print("Limitação na concessão: %s; readequação %s; diferenças nominais: %s; JSON gravado em %s"
                  % (res["premissas"]["limitacao_na_concessao"],
                     "aplicável" if res["premissas"]["readequacao_aplicavel"] else "não aplicável", resumo, args.saida))
        else:
            print(texto)
        if args.md:
            Path(args.md).write_text(gerar_md(res), encoding="utf-8")
            print("Memória Markdown gravada em %s" % args.md)
        if args.csv:
            Path(args.csv).write_text(gerar_csv(res), encoding="utf-8")
            print("Evolução CSV gravada em %s" % args.csv)
        for a in res["avisos"]:
            print("AVISO: %s" % a, file=sys.stderr)
    except ErroValidacao as e:
        print("ERRO de validação: %s" % e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("ERRO: %s" % e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
