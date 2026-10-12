#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atrasados de revisão de benefício anterior à CF/88: parcelas mensais da diferença, abono
anual, prescrição quinquenal, decadência (informativa), óbito do segurado com conversão em
pensão por morte, óbito da pensionista, habilitação de dependentes ou sucessores e arquivo de
parcelas para a skill atualizacao-monetaria (regime da Fazenda Pública).

Parte da skill: pericia-previdenciaria-beneficio-pre-cf88

Mecânica implementada:
  1. Lê as diferenças mensais de readequacao_tetos.py (JSON com o bloco para_atrasados) ou um
     CSV competencia;moeda;renda_devida;renda_paga;diferenca.
  2. Divide o período em bloco do titular (até o mês do óbito do segurado, inclusive) e bloco
     da pensão (do mês seguinte ao óbito até o mês do óbito da pensionista ou o fim). Na
     pensão, a diferença é o coeficiente da pensão sobre a renda devida revisada menos a
     pensão paga (arquivo) ou, na falta, o mesmo coeficiente sobre a renda paga.
  3. Acrescenta o abono anual (Lei 8.213/1991, art. 40) proporcional aos meses de cada bloco
     no ano, na competência do último mês do bloco no ano.
  4. Aplica a prescrição quinquenal (Lei 8.213/1991, art. 103, parágrafo único) contada do
     ajuizamento, pelo critério da competência (padrão) ou da data de pagamento.
  5. Informa os termos da decadência do art. 103, caput, sem concluir sobre a sua incidência.
  6. Grava parcelas.json no formato [{"competencia": "mm/aaaa", "valor": ..., "descricao": "..."}].

Uso:
    python3 atrasados_prescricao.py --diferencas readequacao.json --ajuizamento 15/03/2008 \
        --obito-segurado 15/06/2010 --coeficiente-pensao 100 \
        --fundamento-pensao "Lei 8.213/1991, art. 75, redação da Lei 9.528/1997 [A VERIFICAR regime do óbito]" \
        --pago-pensao assets/exemplo_pagamentos_pensao.csv --obito-pensionista 20/09/2023 \
        --saida atrasados.json --md atrasados.md --csv atrasados.csv --parcelas parcelas.json

Toda operação monetária usa Decimal; o arredondamento a 2 casas (ROUND_HALF_UP) ocorre apenas
na apresentação. Valores de moedas diferentes nunca são somados entre si.
"""

import argparse
import csv
import json
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, getcontext, InvalidOperation
from pathlib import Path

getcontext().prec = 40

LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"


class ErroValidacao(Exception):
    """Erro de entrada do usuário: sai com código 1 e mensagem objetiva."""


# ----------------------------------------------------------------------------
# Utilitários
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


def parse_comp(texto):
    s = str(texto).strip()
    partes = s.split("/")
    if len(partes) != 2 or not (partes[0].isdigit() and partes[1].isdigit()):
        raise ErroValidacao("competência inválida (esperado mm/aaaa): %r" % texto)
    mes, ano = int(partes[0]), int(partes[1])
    if not 1 <= mes <= 12 or ano < 1900:
        raise ErroValidacao("competência fora de faixa: %r" % texto)
    return (ano, mes)


def parse_data(texto):
    """Data dd/mm/aaaa -> date."""
    s = str(texto).strip()
    partes = s.split("/")
    if len(partes) != 3 or not all(p.isdigit() for p in partes):
        raise ErroValidacao("data inválida (esperado dd/mm/aaaa): %r" % texto)
    d, m, a = (int(x) for x in partes)
    try:
        return date(a, m, d)
    except ValueError:
        raise ErroValidacao("data inexistente: %r" % texto)


def data_str(d):
    return d.strftime("%d/%m/%Y")


def comp_str(c):
    return "%02d/%04d" % (c[1], c[0])


def comp_de_data(d):
    return (d.year, d.month)


def proxima(c):
    ano, mes = c
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def anterior(c):
    ano, mes = c
    return (ano - 1, 12) if mes == 1 else (ano, mes - 1)


def subtrair_anos(d, anos):
    try:
        return d.replace(year=d.year - anos)
    except ValueError:  # 29/02 em ano não bissexto
        return d.replace(year=d.year - anos, day=28)


def somar_anos(d, anos):
    try:
        return d.replace(year=d.year + anos)
    except ValueError:
        return d.replace(year=d.year + anos, day=28)


def q2(valor):
    return Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt_br(valor, casas=2):
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
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


# ----------------------------------------------------------------------------
# Carga
# ----------------------------------------------------------------------------

def carregar_diferencas(caminho):
    """JSON de readequacao_tetos.py (completo ou só o bloco para_atrasados) ou CSV."""
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao("arquivo não encontrado: %s" % caminho)
    meta = {}
    if p.suffix.lower() == ".json":
        try:
            dados = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ErroValidacao("JSON de diferenças inválido: %s" % e)
        if isinstance(dados, dict) and "para_atrasados" in dados:
            bloco = dados["para_atrasados"]
            meta = {k: bloco.get(k) for k in ("dib", "fim", "coeficiente", "limitacao_na_concessao",
                                             "readequacao_aplicavel")}
            linhas = bloco.get("linhas", [])
        elif isinstance(dados, dict) and "linhas" in dados:
            meta = {k: dados.get(k) for k in ("dib", "fim")}
            linhas = dados["linhas"]
        elif isinstance(dados, list):
            linhas = dados
        else:
            raise ErroValidacao("JSON sem o bloco para_atrasados nem lista de linhas")
        regs = []
        for l in linhas:
            regs.append({"competencia": l["competencia"], "moeda": l.get("moeda", "R$"),
                         "renda_devida": str(l["renda_devida"]), "renda_paga": str(l["renda_paga"]),
                         "diferenca": str(l["diferenca"]),
                         "origem_renda_paga": l.get("origem_renda_paga", "")})
    else:
        regs = ler_csv(caminho, ["competencia", "renda_devida", "renda_paga"])
        for r in regs:
            r.setdefault("moeda", "R$")
            r["moeda"] = r["moeda"] or "R$"
            if not r.get("diferenca"):
                d = parse_num(r["renda_devida"]) - parse_num(r["renda_paga"])
                r["diferenca"] = str(d if d > 0 else Decimal(0))
            r.setdefault("origem_renda_paga", "")
    out = []
    for r in regs:
        out.append({"competencia": parse_comp(r["competencia"]), "moeda": r["moeda"],
                    "renda_devida": parse_num(r["renda_devida"]), "renda_paga": parse_num(r["renda_paga"]),
                    "diferenca": parse_num(r["diferenca"]), "origem_renda_paga": r.get("origem_renda_paga", "")})
    if not out:
        raise ErroValidacao("nenhuma linha de diferença encontrada")
    out.sort(key=lambda x: x["competencia"])
    vistos = set()
    for l in out:
        if l["competencia"] in vistos:
            raise ErroValidacao("competência repetida nas diferenças: %s" % comp_str(l["competencia"]))
        vistos.add(l["competencia"])
        if l["diferenca"] < 0:
            raise ErroValidacao("diferença negativa em %s" % comp_str(l["competencia"]))
    return out, meta


def carregar_pagos(caminho):
    regs = ler_csv(caminho, ["competencia", "valor_pago"])
    out = {}
    for r in regs:
        c = parse_comp(r["competencia"])
        if c in out:
            raise ErroValidacao("competência repetida nos pagamentos da pensão: %s" % comp_str(c))
        v = parse_num(r["valor_pago"])
        if v < 0:
            raise ErroValidacao("pensão paga negativa em %s" % comp_str(c))
        out[c] = {"valor": v, "moeda": r.get("moeda") or ""}
    return out


# ----------------------------------------------------------------------------
# Núcleo
# ----------------------------------------------------------------------------

def calcular(args):
    linhas, meta = carregar_diferencas(args.diferencas)
    por_comp = {l["competencia"]: l for l in linhas}
    avisos = []
    memoria = []
    premissas_texto = []

    inicio = linhas[0]["competencia"]
    fim = parse_comp(args.fim) if args.fim else linhas[-1]["competencia"]
    if fim < inicio:
        raise ErroValidacao("--fim anterior à primeira competência das diferenças")
    if fim > linhas[-1]["competencia"]:
        raise ErroValidacao("--fim (%s) posterior à última competência disponível (%s)"
                            % (comp_str(fim), comp_str(linhas[-1]["competencia"])))
    # Contiguidade
    c = inicio
    lacunas = []
    while c <= fim:
        if c not in por_comp:
            lacunas.append(comp_str(c))
        c = proxima(c)
    if lacunas:
        avisos.append("%d competência(s) sem linha de diferença (ex.: %s): tratadas como zero"
                      % (len(lacunas), lacunas[0]))

    # Óbitos e blocos
    obito_seg = parse_data(args.obito_segurado) if args.obito_segurado else None
    obito_pen = parse_data(args.obito_pensionista) if args.obito_pensionista else None
    if obito_pen and not obito_seg:
        raise ErroValidacao("--obito-pensionista exige --obito-segurado")
    if obito_seg and obito_pen and obito_pen <= obito_seg:
        raise ErroValidacao("óbito da pensionista não pode ser anterior ou igual ao do segurado")
    coef_pensao = None
    if obito_seg:
        if comp_de_data(obito_seg) < inicio:
            raise ErroValidacao("óbito do segurado anterior à primeira competência das diferenças")
        if args.coeficiente_pensao is None:
            raise ErroValidacao("--obito-segurado exige --coeficiente-pensao (percentual) e --fundamento-pensao "
                                "(regime vigente na data do óbito, marcado [A VERIFICAR] se não conferido)")
        if not args.fundamento_pensao:
            raise ErroValidacao("--coeficiente-pensao exige --fundamento-pensao")
        coef_pensao = parse_num(args.coeficiente_pensao) / Decimal(100)
        if not (Decimal(0) < coef_pensao <= Decimal(1)):
            raise ErroValidacao("coeficiente da pensão fora de 0 a 100%")
    pagos_pensao = carregar_pagos(args.pago_pensao) if args.pago_pensao else {}
    if pagos_pensao and not obito_seg:
        avisos.append("arquivo de pensão paga informado sem --obito-segurado: ignorado")

    fim_titular = fim
    if obito_seg and comp_de_data(obito_seg) < fim:
        fim_titular = comp_de_data(obito_seg)
    elif obito_seg and comp_de_data(obito_seg) >= fim:
        avisos.append("óbito do segurado (%s) igual ou posterior ao fim do período (%s): sem bloco de pensão"
                      % (data_str(obito_seg), comp_str(fim)))
    blocos = [{"nome": "titular", "inicio": inicio, "fim": fim_titular,
               "descricao": "Diferença de renda mensal do titular"}]
    if obito_seg and comp_de_data(obito_seg) < fim:
        ini_pen = proxima(comp_de_data(obito_seg))
        fim_pen = fim
        if obito_pen:
            if comp_de_data(obito_pen) < ini_pen:
                raise ErroValidacao("óbito da pensionista no mesmo mês do óbito do segurado ou antes: sem pensão")
            if comp_de_data(obito_pen) < fim:
                fim_pen = comp_de_data(obito_pen)
            else:
                avisos.append("óbito da pensionista (%s) posterior ao fim do período (%s): pensão até o fim"
                              % (data_str(obito_pen), comp_str(fim)))
        blocos.append({"nome": "pensao", "inicio": ini_pen, "fim": fim_pen,
                       "descricao": "Diferença de pensão por morte (%s%% da renda revisada)" % fmt_br(coef_pensao * 100)})

    # Prescrição
    if args.sem_prescricao:
        marco = None
        premissas_texto.append("prescrição afastada por parâmetro (%s)" % (args.fundamento_prescricao or
                               "ressalva do art. 103, parágrafo único, da Lei 8.213/1991: menores, incapazes e ausentes"))
    else:
        if not args.ajuizamento and not args.marco_prescricao:
            raise ErroValidacao("informe --ajuizamento (dd/mm/aaaa), ou --marco-prescricao, ou --sem-prescricao")
        data_marco = parse_data(args.marco_prescricao) if args.marco_prescricao else parse_data(args.ajuizamento)
        if args.marco_prescricao and not args.fundamento_prescricao:
            raise ErroValidacao("--marco-prescricao exige --fundamento-prescricao")
        marco = subtrair_anos(data_marco, 5)
        premissas_texto.append("quinquênio contado de %s (%s): parcelas com %s anterior a %s prescritas"
                               % (data_str(data_marco), "marco informado: %s" % args.fundamento_prescricao
                                  if args.marco_prescricao else "ajuizamento",
                                  "competência" if args.criterio_prescricao == "competencia" else "mês de pagamento",
                                  comp_str(comp_de_data(marco))))

    def prescrita(comp):
        if marco is None:
            return False
        limite = comp_de_data(marco)
        if args.criterio_prescricao == "competencia":
            return comp < limite
        return proxima(comp) < limite

    # Parcelas
    parcelas = []
    for b in blocos:
        c = b["inicio"]
        por_ano = {}
        while c <= b["fim"]:
            l = por_comp.get(c)
            moeda = l["moeda"] if l else "R$"
            if b["nome"] == "titular":
                valor = l["diferenca"] if l else Decimal(0)
                origem = l["origem_renda_paga"] if l else "sem linha"
                detalhe = {"renda_devida": l["renda_devida"] if l else Decimal(0),
                           "renda_paga": l["renda_paga"] if l else Decimal(0)}
            else:
                devida = (l["renda_devida"] if l else Decimal(0)) * coef_pensao
                if c in pagos_pensao:
                    if pagos_pensao[c]["moeda"] and pagos_pensao[c]["moeda"] != moeda:
                        raise ErroValidacao("pensão paga de %s em %s, mas a competência está em %s"
                                            % (comp_str(c), pagos_pensao[c]["moeda"], moeda))
                    paga = pagos_pensao[c]["valor"]
                    origem = "informado"
                else:
                    paga = (l["renda_paga"] if l else Decimal(0)) * coef_pensao
                    origem = "presumido (coeficiente sobre a renda paga)"
                valor = devida - paga
                if valor < 0:
                    valor = Decimal(0)
                detalhe = {"renda_devida": devida, "renda_paga": paga}
            parcelas.append({"competencia": c, "bloco": b["nome"], "tipo": "mensal", "moeda": moeda,
                             "valor": valor, "origem_renda_paga": origem, "prescrita": prescrita(c),
                             "descricao": "%s, competência %s (%s)" % (b["descricao"], comp_str(c), moeda),
                             **detalhe})
            por_ano.setdefault(c[0], []).append((c, valor, moeda))
            c = proxima(c)
        if not args.sem_abono:
            for ano, itens in sorted(por_ano.items()):
                n = len(itens)
                ultimo, valor_ult, moeda = itens[-1]
                abono = valor_ult * Decimal(n) / Decimal(12)
                parcelas.append({"competencia": ultimo, "bloco": b["nome"], "tipo": "abono", "moeda": moeda,
                                 "valor": abono, "origem_renda_paga": "", "prescrita": prescrita(ultimo),
                                 "descricao": "Abono anual %d, %s, %d/12 da diferença de %s (%s)"
                                              % (ano, "titular" if b["nome"] == "titular" else "pensão", n,
                                                 comp_str(ultimo), moeda),
                                 "renda_devida": None, "renda_paga": None})
    parcelas.sort(key=lambda p: (p["competencia"], 0 if p["tipo"] == "mensal" else 1, p["bloco"]))

    # Totais por bloco, situação e moeda
    totais = {}
    for p in parcelas:
        chave = (p["bloco"], "prescritas" if p["prescrita"] else "devidas", p["moeda"])
        t = totais.setdefault(chave, {"parcelas": 0, "valor": Decimal(0)})
        t["parcelas"] += 1
        t["valor"] += p["valor"]
    por_moeda = {}
    for (bloco, sit, moeda), t in totais.items():
        m = por_moeda.setdefault(moeda, {"bruto": Decimal(0), "prescritas": Decimal(0), "devidas": Decimal(0)})
        m["bruto"] += t["valor"]
        m[sit] += t["valor"]

    # Arquivo de parcelas para atualizacao-monetaria
    saida_parcelas = []
    for p in parcelas:
        if not p["prescrita"] and p["valor"] > 0:
            saida_parcelas.append({"competencia": comp_str(p["competencia"]), "valor": q2(p["valor"]),
                                   "descricao": p["descricao"]})

    # Decadência (informativa)
    decadencia = None
    primeira = parse_comp(args.primeira_prestacao) if args.primeira_prestacao else (
        parse_comp(meta["dib"]) if meta.get("dib") else None)
    if primeira:
        inicio_contagem = proxima(primeira)
        if primeira < (1997, 8):
            termo_inicial = date(1997, 8, 1)
            termo_final = somar_anos(termo_inicial, 10)
            nota = ("benefício anterior à MP 1.523-9/1997: termo inicial da decadência decenal atribuído a "
                    "01/08/1997 e termo final a 01/08/2007 [A VERIFICAR: STF, Tema 313, RE 626.489]")
        else:
            termo_inicial = date(inicio_contagem[0], inicio_contagem[1], 1)
            termo_final = somar_anos(termo_inicial, 10)
            nota = "dia primeiro do mês seguinte ao do recebimento da primeira prestação (art. 103, caput)"
        ajuiz = parse_data(args.ajuizamento) if args.ajuizamento else None
        decadencia = {
            "primeira_prestacao": comp_str(primeira), "termo_inicial": data_str(termo_inicial),
            "termo_final": data_str(termo_final), "nota": nota,
            "ajuizamento": data_str(ajuiz) if ajuiz else None,
            "ajuizado_dentro_do_decenio": (ajuiz <= termo_final) if ajuiz else None,
            "observacao": "a readequação aos tetos das emendas não revisa o ato de concessão; a linha do TRF1 "
                          "(AC 1018697-75.2023.4.01.3300, Corte Especial, j. 02/12/2024) afasta a decadência; "
                          "a incidência é matéria do juízo",
        }

    # Habilitação
    habilitacao = []
    if obito_seg:
        habilitacao.append({
            "bloco": "titular",
            "periodo": "%s a %s" % (comp_str(blocos[0]["inicio"]), comp_str(blocos[0]["fim"])),
            "quem_recebe": "dependentes habilitados à pensão por morte ou, na falta deles, sucessores na forma da "
                           "lei civil, independentemente de inventário ou arrolamento (Lei 8.213/1991, art. 112)",
            "processual": "morte da parte: suspensão (CPC, art. 313, I) e sucessão pelo espólio ou sucessores "
                          "(CPC, art. 110), mediante habilitação (CPC, arts. 687 a 692)",
            "obito": data_str(obito_seg),
        })
        if len(blocos) > 1:
            habilitacao.append({
                "bloco": "pensao",
                "periodo": "%s a %s" % (comp_str(blocos[1]["inicio"]), comp_str(blocos[1]["fim"])),
                "quem_recebe": ("sucessores da pensionista na forma da lei civil, por aplicação do art. 112 da "
                                "Lei 8.213/1991 ao valor não recebido em vida pela pensionista [A VERIFICAR "
                                "alcance do art. 112 à pensionista falecida]" if obito_pen else
                                "a própria pensionista, titular da cota"),
                "processual": ("nova habilitação dos sucessores da pensionista (CPC, arts. 687 a 692); a cota "
                               "cessa com a morte da pensionista (Decreto 3.048/1999, art. 114, I)" if obito_pen
                               else "habilitação da pensionista como sucessora do segurado (CPC, arts. 687 a 692)"),
                "obito": data_str(obito_pen) if obito_pen else None,
                "coeficiente_pensao_pct": q2(coef_pensao * 100), "fundamento_pensao": args.fundamento_pensao,
            })

    # Testes de sanidade
    testes = []
    for moeda, m in por_moeda.items():
        testes.append(("%s: bruto = prescritas + devidas" % moeda,
                       abs(m["bruto"] - m["prescritas"] - m["devidas"]) < Decimal("0.000001")))
        soma_arquivo = sum((Decimal(str(p["valor"])) for p in saida_parcelas
                            if p["descricao"].endswith("(%s)" % moeda)), Decimal(0))
        testes.append(("%s: soma de parcelas.json fecha com o total devido (tolerância de centavos)" % moeda,
                       abs(soma_arquivo - m["devidas"]) <= Decimal("0.01") * max(1, len(saida_parcelas))))
    testes.append(("nenhuma parcela negativa", all(p["valor"] >= 0 for p in parcelas)))
    if len(blocos) > 1:
        testes.append(("blocos do titular e da pensão não se sobrepõem", blocos[0]["fim"] < blocos[1]["inicio"]))
    n_mensais = sum(1 for p in parcelas if p["tipo"] == "mensal")
    esperado = sum(((b["fim"][0] - b["inicio"][0]) * 12 + (b["fim"][1] - b["inicio"][1]) + 1) for b in blocos)
    testes.append(("quantidade de parcelas mensais igual aos meses dos blocos", n_mensais == esperado))
    reprovados = [t for t, ok in testes if not ok]
    if reprovados:
        raise ErroValidacao("teste de sanidade reprovado: %s" % "; ".join(reprovados))

    memoria.append("Diferenças lidas de %s: %d competências de %s a %s; período calculado de %s a %s."
                   % (args.diferencas, len(linhas), comp_str(linhas[0]["competencia"]),
                      comp_str(linhas[-1]["competencia"]), comp_str(inicio), comp_str(fim)))
    for b in blocos:
        memoria.append("Bloco %s: %s a %s (%s)." % (b["nome"], comp_str(b["inicio"]), comp_str(b["fim"]), b["descricao"]))
    if obito_seg:
        memoria.append("Óbito do segurado em %s: o mês do óbito fica com o titular; a pensão começa no mês seguinte "
                       "com coeficiente de %s%% (%s); pensão paga lida de %s em %d competência(s)."
                       % (data_str(obito_seg), fmt_br(coef_pensao * 100), args.fundamento_pensao,
                          args.pago_pensao or "nenhum arquivo",
                          sum(1 for p in parcelas if p["bloco"] == "pensao" and p["origem_renda_paga"] == "informado")))
    if obito_pen:
        memoria.append("Óbito da pensionista em %s: a cota cessa no mês do óbito (Decreto 3.048/1999, art. 114, I)."
                       % data_str(obito_pen))
    memoria.append("Abono anual: %s." % ("incluído, proporcional aos meses de cada bloco no ano, na competência do "
                                         "último mês do bloco no ano (Lei 8.213/1991, art. 40)" if not args.sem_abono
                                         else "excluído por parâmetro"))
    for t in premissas_texto:
        memoria.append("Prescrição: %s." % t)
    for moeda, m in por_moeda.items():
        memoria.append("Em %s: bruto %s; prescritas %s; devidas %s." % (moeda, fmt_br(m["bruto"]),
                                                                       fmt_br(m["prescritas"]), fmt_br(m["devidas"])))
    memoria.append("parcelas.json: %d parcelas não prescritas e positivas, valores nominais na moeda da competência; "
                   "atualização e juros pela skill atualizacao-monetaria, regime fazenda_publica."
                   % len(saida_parcelas))

    resultado = {
        "skill": "pericia-previdenciaria-beneficio-pre-cf88",
        "script": "atrasados_prescricao.py",
        "premissas": {
            "arquivo_diferencas": args.diferencas, "meta_diferencas": meta,
            "inicio": comp_str(inicio), "fim": comp_str(fim),
            "ajuizamento": args.ajuizamento or "", "criterio_prescricao": args.criterio_prescricao,
            "marco_prescricao": data_str(marco) if marco else None, "sem_prescricao": bool(args.sem_prescricao),
            "fundamento_prescricao": args.fundamento_prescricao or "Lei 8.213/1991, art. 103, parágrafo único",
            "obito_segurado": data_str(obito_seg) if obito_seg else None,
            "coeficiente_pensao_pct": q2(coef_pensao * 100) if coef_pensao is not None else None,
            "fundamento_pensao": args.fundamento_pensao or "",
            "pensao_paga_arquivo": args.pago_pensao or "",
            "obito_pensionista": data_str(obito_pen) if obito_pen else None,
            "abono_anual": not args.sem_abono,
            "mes_do_obito": "fica com o titular; a pensão começa no mês seguinte",
            "moeda": "valores nominais na moeda de cada competência; moedas distintas não se somam",
            "blocos": [{"nome": b["nome"], "inicio": comp_str(b["inicio"]), "fim": comp_str(b["fim"]),
                        "descricao": b["descricao"]} for b in blocos],
        },
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "totais": [{"bloco": k[0], "situacao": k[1], "moeda": k[2], "parcelas": t["parcelas"], "valor": q2(t["valor"])}
                   for k, t in sorted(totais.items())],
        "totais_por_moeda": {m: {"bruto": q2(v["bruto"]), "prescritas": q2(v["prescritas"]), "devidas": q2(v["devidas"])}
                             for m, v in por_moeda.items()},
        "decadencia": decadencia,
        "habilitacao": habilitacao,
        "parcelas": [{"competencia": comp_str(p["competencia"]), "bloco": p["bloco"], "tipo": p["tipo"],
                      "moeda": p["moeda"],
                      "renda_devida": q2(p["renda_devida"]) if p["renda_devida"] is not None else None,
                      "renda_paga": q2(p["renda_paga"]) if p["renda_paga"] is not None else None,
                      "valor": q2(p["valor"]), "origem_renda_paga": p["origem_renda_paga"],
                      "prescrita": p["prescrita"], "descricao": p["descricao"]} for p in parcelas],
        "parcelas_para_atualizacao": saida_parcelas,
        "testes_sanidade": [{"teste": t, "ok": ok} for t, ok in testes],
        "avisos": avisos,
        "memoria": memoria,
    }
    return resultado


def gerar_md(res):
    p = res["premissas"]
    linhas = ["# Atrasados, prescrição e sucessão: período %s a %s" % (p["inicio"], p["fim"]), ""]
    linhas.append("| Bloco | Situação | Moeda | Parcelas | Valor nominal |")
    linhas.append("|---|---|---|---|---|")
    for t in res["totais"]:
        linhas.append("| %s | %s | %s | %d | %s |" % (t["bloco"], t["situacao"], t["moeda"], t["parcelas"], fmt_br(t["valor"])))
    linhas.append("")
    if res["decadencia"]:
        d = res["decadencia"]
        linhas.append("Decadência (informativo): primeira prestação %s; termo inicial %s; termo final %s; %s. %s."
                      % (d["primeira_prestacao"], d["termo_inicial"], d["termo_final"], d["nota"], d["observacao"]))
        linhas.append("")
    for h in res["habilitacao"]:
        linhas.append("Habilitação (%s, %s): %s. %s." % (h["bloco"], h["periodo"], h["quem_recebe"], h["processual"]))
    if res["habilitacao"]:
        linhas.append("")
    linhas.append("| Competência | Bloco | Tipo | Moeda | Renda devida | Renda paga | Parcela | Prescrita | Descrição |")
    linhas.append("|---|---|---|---|---|---|---|---|---|")
    for q in res["parcelas"]:
        linhas.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            q["competencia"], q["bloco"], q["tipo"], q["moeda"],
            fmt_br(q["renda_devida"]) if q["renda_devida"] is not None else "",
            fmt_br(q["renda_paga"]) if q["renda_paga"] is not None else "",
            fmt_br(q["valor"]), "sim" if q["prescrita"] else "não", q["descricao"]))
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
    cab = ["competencia", "bloco", "tipo", "moeda", "renda_devida", "renda_paga", "valor", "prescrita", "descricao"]
    linhas = [";".join(cab)]
    for q in res["parcelas"]:
        vals = []
        for k in cab:
            v = q[k]
            if isinstance(v, Decimal):
                v = fmt_br(v)
            elif isinstance(v, bool):
                v = "sim" if v else "não"
            elif v is None:
                v = ""
            vals.append(str(v))
        linhas.append(";".join(vals))
    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Atrasados, prescrição, óbito e sucessão em revisão de benefício anterior à CF/88 "
                    "(skill pericia-previdenciaria-beneficio-pre-cf88)")
    parser.add_argument("--diferencas", required=True,
                        help="JSON de readequacao_tetos.py (ou bloco para_atrasados) ou CSV "
                             "competencia;moeda;renda_devida;renda_paga;diferenca")
    parser.add_argument("--ajuizamento", default=None, help="data do ajuizamento, dd/mm/aaaa")
    parser.add_argument("--criterio-prescricao", choices=["competencia", "pagamento"], default="competencia",
                        help="'competencia': prescreve a competência anterior ao marco (padrão); 'pagamento': "
                             "considera a parcela paga no mês seguinte à competência")
    parser.add_argument("--marco-prescricao", default=None,
                        help="data que substitui o ajuizamento na contagem do quinquênio (ex.: requerimento "
                             "administrativo), dd/mm/aaaa; exige --fundamento-prescricao")
    parser.add_argument("--sem-prescricao", action="store_true",
                        help="não aplica prescrição (menores, incapazes, ausentes); informe --fundamento-prescricao")
    parser.add_argument("--fundamento-prescricao", default=None, help="fundamento do marco ou do afastamento")
    parser.add_argument("--obito-segurado", default=None, help="data do óbito do segurado, dd/mm/aaaa")
    parser.add_argument("--coeficiente-pensao", default=None,
                        help="coeficiente da pensão em percentual, pelo regime vigente na data do óbito")
    parser.add_argument("--fundamento-pensao", default=None, help="dispositivo que fundamenta o coeficiente da pensão")
    parser.add_argument("--pago-pensao", default=None,
                        help="CSV competencia;valor_pago;moeda com a pensão efetivamente paga (HISCRE)")
    parser.add_argument("--obito-pensionista", default=None, help="data do óbito da pensionista, dd/mm/aaaa")
    parser.add_argument("--fim", default=None, help="última competência considerada, mm/aaaa (padrão: última do arquivo)")
    parser.add_argument("--sem-abono", action="store_true", help="não inclui o abono anual")
    parser.add_argument("--primeira-prestacao", default=None,
                        help="competência da primeira prestação, mm/aaaa, para o quadro informativo da decadência "
                             "(padrão: DIB do JSON)")
    parser.add_argument("--saida", default=None, help="arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--md", default=None, help="grava a memória em Markdown neste arquivo")
    parser.add_argument("--csv", default=None, help="grava as parcelas em CSV neste arquivo")
    parser.add_argument("--parcelas", default=None,
                        help="grava as parcelas não prescritas no formato da skill atualizacao-monetaria")
    args = parser.parse_args()

    try:
        res = calcular(args)
        texto = json.dumps(res, ensure_ascii=False, indent=2, cls=CodificadorDecimal)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            resumo = "; ".join("%s devidas %s (prescritas %s)" % (m, fmt_br(v["devidas"]), fmt_br(v["prescritas"]))
                               for m, v in res["totais_por_moeda"].items())
            print("Blocos: %s; %s; JSON gravado em %s"
                  % (", ".join("%s %s a %s" % (b["nome"], b["inicio"], b["fim"]) for b in res["premissas"]["blocos"]),
                     resumo, args.saida))
        else:
            print(texto)
        if args.md:
            Path(args.md).write_text(gerar_md(res), encoding="utf-8")
            print("Memória Markdown gravada em %s" % args.md)
        if args.csv:
            Path(args.csv).write_text(gerar_csv(res), encoding="utf-8")
            print("Parcelas CSV gravadas em %s" % args.csv)
        if args.parcelas:
            Path(args.parcelas).write_text(
                json.dumps(res["parcelas_para_atualizacao"], ensure_ascii=False, indent=2, cls=CodificadorDecimal) + "\n",
                encoding="utf-8")
            print("Arquivo de parcelas para atualizacao-monetaria gravado em %s (%d parcelas)"
                  % (args.parcelas, len(res["parcelas_para_atualizacao"])))
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
