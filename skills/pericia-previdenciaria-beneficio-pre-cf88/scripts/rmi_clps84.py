#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconstrução da renda mensal inicial (RMI) de benefício do RGPS concedido antes da
Constituição de 1988, pelas regras da CLPS (Decreto 89.312/1984) e da legislação anterior.

Parte da skill: pericia-previdenciaria-beneficio-pre-cf88

Mecânica implementada (parâmetros entram por arquivo ou por linha de comando, nunca de
memória):
  1. Lê os salários de contribuição (SC) do período básico, normalmente 36 competências
     imediatamente anteriores à DIB, cada um com a moeda da época.
  2. Corrige os SC anteriores aos 12 últimos (normalmente 24) pelos coeficientes oficiais
     (ORTN/OTN) informados por arquivo com fonte. Aborta se faltar coeficiente.
  3. Converte a moeda dos SC para a moeda da DIB por arquivo de conversões (divisor com
     fonte) ou aceita a declaração de que os coeficientes já embutem a conversão.
  4. Média aritmética dos SC (salário de benefício).
  5. Limita a média ao maior valor-teto; separa a parcela até o menor valor-teto e o
     excedente; aplica ao excedente a fração informada pelo perito (com fundamento).
  6. Aplica o coeficiente da espécie e apura a RMI, o tipo de limitação sofrida e o
     número de salários mínimos da RMI na DIB (quando informado o salário mínimo).

Uso:
    python3 rmi_clps84.py --salarios assets/exemplo_salarios_1987.csv \
        --coeficientes assets/exemplo_coeficientes_ortn.csv \
        --conversoes assets/exemplo_conversoes.csv --dib 03/1987 \
        --menor-teto 14000,00 --maior-teto 28000,00 --fonte-tetos "EXEMPLO FICTÍCIO" \
        --coeficiente 95 --fracao-excedente 1/30 --grupos-12 24 \
        --fundamento-fracao "1/30 por grupo de 12 contribuições acima do menor valor-teto" \
        --salario-minimo-dib 1400,00 --fonte-sm "EXEMPLO FICTÍCIO" \
        --saida rmi_1987.json --md rmi_1987.md

Toda operação monetária usa Decimal; o arredondamento a 2 casas (ROUND_HALF_UP) ocorre
apenas na apresentação. Nenhum coeficiente, teto ou salário mínimo é embutido no código.
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


class ErroValidacao(Exception):
    """Erro de entrada do usuário: sai com código 1 e mensagem objetiva."""


# ----------------------------------------------------------------------------
# Utilitários de número, data e formatação
# ----------------------------------------------------------------------------

def parse_num(texto):
    """Aceita número no padrão brasileiro (1.234,56) e no técnico (1234.56)."""
    if texto is None:
        raise ErroValidacao("valor numérico ausente")
    s = str(texto).strip().replace("R$", "").replace("Cz$", "").replace("NCz$", "")
    s = s.replace("Cr$", "").replace("CR$", "").replace(" ", "")
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


def meses_entre(c_ini, c_fim):
    """Número de meses de c_ini até c_fim (positivo se c_fim é posterior)."""
    return (c_fim[0] - c_ini[0]) * 12 + (c_fim[1] - c_ini[1])


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


def fmt_fator(valor, casas=6):
    return fmt_br(valor, casas)


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
# Núcleo do cálculo
# ----------------------------------------------------------------------------

def carregar_salarios(caminho):
    regs = ler_csv(caminho, ["competencia", "salario_contribuicao", "moeda"])
    sal = []
    for r in regs:
        sal.append({
            "competencia": parse_comp(r["competencia"]),
            "valor": parse_num(r["salario_contribuicao"]),
            "moeda": r["moeda"] or "",
        })
    sal.sort(key=lambda x: x["competencia"])
    vistos = set()
    for s in sal:
        if s["competencia"] in vistos:
            raise ErroValidacao("competência repetida nos salários: %s" % comp_str(s["competencia"]))
        vistos.add(s["competencia"])
        if s["valor"] < 0:
            raise ErroValidacao("salário de contribuição negativo em %s" % comp_str(s["competencia"]))
        if not s["moeda"]:
            raise ErroValidacao("moeda ausente em %s (informar Cr$, Cz$, NCz$, CR$ ou R$)"
                                % comp_str(s["competencia"]))
    return sal


def carregar_coeficientes(caminho):
    regs = ler_csv(caminho, ["competencia", "coeficiente", "fonte"])
    coef = {}
    for r in regs:
        c = parse_comp(r["competencia"])
        v = parse_num(r["coeficiente"])
        if v <= 0:
            raise ErroValidacao("coeficiente não positivo em %s" % comp_str(c))
        coef[c] = {"valor": v, "fonte": r["fonte"]}
    return coef


def carregar_conversoes(caminho):
    """Cortes de padrão monetário: competência do corte, divisor, moeda nova, fonte."""
    regs = ler_csv(caminho, ["competencia", "divisor", "moeda_nova", "fonte"])
    cortes = []
    for r in regs:
        d = parse_num(r["divisor"])
        if d <= 0:
            raise ErroValidacao("divisor não positivo na conversão de %s" % r["competencia"])
        cortes.append({"competencia": parse_comp(r["competencia"]), "divisor": d,
                       "moeda_nova": r["moeda_nova"], "fonte": r["fonte"]})
    cortes.sort(key=lambda x: x["competencia"])
    return cortes


def divisor_ate_dib(comp, dib, cortes):
    """Produto dos divisores dos cortes posteriores à competência e não posteriores à DIB."""
    div = Decimal(1)
    aplicados = []
    for c in cortes:
        if comp < c["competencia"] <= dib:
            div *= c["divisor"]
            aplicados.append("%s: divisor %s (%s)" % (comp_str(c["competencia"]),
                                                       fmt_br(c["divisor"], 0), c["moeda_nova"]))
    return div, aplicados


def calcular(args):
    dib = parse_comp(args.dib)
    salarios = carregar_salarios(args.salarios)
    coefs = carregar_coeficientes(args.coeficientes)
    cortes = carregar_conversoes(args.conversoes) if args.conversoes else []
    avisos = []

    n_sc = args.n_sc
    n_corr = args.n_corrigidos
    if n_corr < 0 or n_corr > n_sc:
        raise ErroValidacao("--n-corrigidos deve estar entre 0 e --n-sc")
    if len(salarios) != n_sc:
        raise ErroValidacao("esperadas exatamente %d competências de salário de contribuição, "
                            "encontradas %d; o perito seleciona o período básico antes de rodar"
                            % (n_sc, len(salarios)))
    if salarios[-1]["competencia"] >= dib:
        raise ErroValidacao("há salário de contribuição em competência igual ou posterior à DIB "
                            "(%s)" % comp_str(salarios[-1]["competencia"]))
    amplitude = meses_entre(salarios[0]["competencia"], salarios[-1]["competencia"]) + 1
    if amplitude > 48:
        raise ErroValidacao("período básico com amplitude de %d meses; a CLPS limita a 48 "
                            "[A VERIFICAR: art. 21 do Decreto 89.312/1984]" % amplitude)
    if amplitude != n_sc:
        avisos.append("período básico não é contínuo: %d competências em %d meses; conferir "
                      "se as lacunas correspondem a meses sem contribuição" % (n_sc, amplitude))

    moeda_dib = args.moeda_dib or salarios[-1]["moeda"]
    menor_teto = parse_num(args.menor_teto)
    maior_teto = parse_num(args.maior_teto)
    if menor_teto <= 0 or maior_teto <= 0 or menor_teto > maior_teto:
        raise ErroValidacao("tetos inválidos: menor valor-teto deve ser positivo e não superior "
                            "ao maior valor-teto")
    coeficiente = parse_num(args.coeficiente) / Decimal(100)
    if not (Decimal("0") < coeficiente <= Decimal("1.5")):
        raise ErroValidacao("coeficiente da espécie fora de faixa plausível (0 a 150%)")

    # Quais competências são corrigidas: as n_corr primeiras (anteriores às 12 últimas)
    corrigidas = salarios[:n_corr]
    faltam = [comp_str(s["competencia"]) for s in corrigidas if s["competencia"] not in coefs]
    if faltam:
        raise ErroValidacao("faltam coeficientes de correção para %d competência(s) do período "
                            "corrigido: %s. Obter nas portarias do extinto MPAS (ORTN/OTN) e "
                            "informar por arquivo com fonte" % (len(faltam), ", ".join(faltam)))
    ignorados = [comp_str(s["competencia"]) for s in salarios[n_corr:] if s["competencia"] in coefs]
    if ignorados:
        avisos.append("coeficientes informados para competências não corrigidas foram ignorados "
                      "(os %d últimos SC entram pelo valor nominal): %s"
                      % (n_sc - n_corr, ", ".join(ignorados)))

    quadro = []
    soma = Decimal(0)
    memoria = []
    memoria.append("Período básico: %d competências de %s a %s; DIB %s; moeda da DIB %s."
                   % (n_sc, comp_str(salarios[0]["competencia"]),
                      comp_str(salarios[-1]["competencia"]), comp_str(dib), moeda_dib))
    memoria.append("Corrigidas as %d competências anteriores às %d últimas pelos coeficientes "
                   "do arquivo %s." % (n_corr, n_sc - n_corr, args.coeficientes))
    for i, s in enumerate(salarios, start=1):
        eh_corrigida = i <= n_corr
        coef = coefs[s["competencia"]]["valor"] if eh_corrigida else Decimal(1)
        fonte = coefs[s["competencia"]]["fonte"] if eh_corrigida else "sem correção (12 últimos)"
        divisor = Decimal(1)
        cadeia = []
        if s["moeda"] != moeda_dib:
            if args.coeficientes_embutem_conversao:
                cadeia = ["conversão embutida no coeficiente (declaração do perito)"]
            elif cortes:
                divisor, cadeia = divisor_ate_dib(s["competencia"], dib, cortes)
                if divisor == 1:
                    raise ErroValidacao("a competência %s está em %s, a DIB em %s, e o arquivo "
                                        "de conversões não traz corte entre elas"
                                        % (comp_str(s["competencia"]), s["moeda"], moeda_dib))
            else:
                raise ErroValidacao("a competência %s está em %s e a DIB em %s: informe "
                                    "--conversoes (competencia;divisor;moeda_nova;fonte), obtido "
                                    "com padroes_monetarios.py da skill atualizacao-monetaria, "
                                    "ou declare --coeficientes-embutem-conversao"
                                    % (comp_str(s["competencia"]), s["moeda"], moeda_dib))
        valor_conv = s["valor"] / divisor
        corrigido = valor_conv * coef
        soma += corrigido
        quadro.append({
            "ordem": i,
            "competencia": comp_str(s["competencia"]),
            "moeda_origem": s["moeda"],
            "sc_nominal": q2(s["valor"]),
            "divisor_moeda": divisor,
            "sc_na_moeda_dib": q2(valor_conv),
            "corrigido": eh_corrigida,
            "coeficiente": coef,
            "fonte_coeficiente": fonte,
            "sc_corrigido": q2(corrigido),
            "conversao": "; ".join(cadeia) if cadeia else "",
        })

    media = soma / Decimal(n_sc)
    memoria.append("Soma dos SC corrigidos: %s %s; média (salário de benefício) = soma / %d = %s %s."
                   % (moeda_dib, fmt_br(soma), n_sc, moeda_dib, fmt_br(media)))

    # Limitação pelos dois tetos
    media_limitada = min(media, maior_teto)
    parcela_base = min(media_limitada, menor_teto)
    excedente = max(Decimal(0), media_limitada - menor_teto)
    if media > maior_teto:
        limitacao = "maior valor-teto"
    elif media > menor_teto:
        limitacao = "menor valor-teto (excedente fracionado)"
    else:
        limitacao = "não limitado"
    memoria.append("Menor valor-teto %s %s; maior valor-teto %s %s (fonte: %s). Média limitada ao "
                   "maior valor-teto: %s; parcela até o menor valor-teto: %s; excedente: %s."
                   % (moeda_dib, fmt_br(menor_teto), moeda_dib, fmt_br(maior_teto), args.fonte_tetos,
                      fmt_br(media_limitada), fmt_br(parcela_base), fmt_br(excedente)))

    fracao_efetiva = Decimal(0)
    fracao_txt = "não aplicada (média não excede o menor valor-teto)"
    if excedente > 0:
        if args.fracao_excedente is None:
            raise ErroValidacao("a média (%s) excede o menor valor-teto (%s): informe "
                                "--fracao-excedente (ex.: 1/30 com --grupos-12 N) e "
                                "--fundamento-fracao com o dispositivo da CLPS/84 aplicado"
                                % (fmt_br(media), fmt_br(menor_teto)))
        if not args.fundamento_fracao:
            raise ErroValidacao("--fracao-excedente exige --fundamento-fracao (dispositivo e "
                                "critério, marcado [A VERIFICAR] se não conferido)")
        fracao = parse_fracao(args.fracao_excedente)
        grupos = args.grupos_12 if args.grupos_12 is not None else 1
        if grupos < 0:
            raise ErroValidacao("--grupos-12 não pode ser negativo")
        fracao_efetiva = fracao * Decimal(grupos)
        fracao_txt = "%s x %d grupo(s) = %s" % (args.fracao_excedente, grupos,
                                                 fmt_fator(fracao_efetiva, 6))
        if fracao_efetiva > 1:
            avisos.append("fração efetiva do excedente superior a 1 (%s); limitada a 1 (100%% do "
                          "excedente)" % fmt_fator(fracao_efetiva, 6))
            fracao_efetiva = Decimal(1)
        if fracao_efetiva < 0:
            raise ErroValidacao("fração do excedente negativa")
    parcela_excedente = excedente * fracao_efetiva
    base_renda = parcela_base + parcela_excedente
    rmi = base_renda * coeficiente
    memoria.append("Fração do excedente: %s (fundamento: %s). Parcela do excedente considerada: %s."
                   % (fracao_txt, args.fundamento_fracao or "n/a", fmt_br(parcela_excedente)))
    memoria.append("RMI = coeficiente %s%% x (%s + %s) = %s %s."
                   % (fmt_br(coeficiente * 100, 2), fmt_br(parcela_base), fmt_br(parcela_excedente),
                      moeda_dib, fmt_br(rmi)))

    rmi_em_sm = None
    sm_dib = None
    if args.salario_minimo_dib:
        sm_dib = parse_num(args.salario_minimo_dib)
        if sm_dib <= 0:
            raise ErroValidacao("salário mínimo da DIB deve ser positivo")
        if not args.fonte_sm:
            raise ErroValidacao("--salario-minimo-dib exige --fonte-sm")
        rmi_em_sm = rmi / sm_dib
        memoria.append("Salário mínimo na DIB: %s %s (fonte: %s). RMI em salários mínimos: %s "
                       "(critério da Súmula 25 da TNU para o art. 58 do ADCT)."
                       % (moeda_dib, fmt_br(sm_dib), args.fonte_sm, fmt_br(rmi_em_sm, 4)))

    # Testes de sanidade embutidos
    testes = []
    soma_quadro = sum((Decimal(str(l["sc_corrigido"])) for l in quadro), Decimal(0))
    testes.append(("soma do quadro fecha com a soma usada na média (tolerância de centavos)",
                   abs(soma_quadro - soma) <= Decimal("0.01") * n_sc))
    testes.append(("RMI positiva", rmi > 0))
    testes.append(("RMI não excede coeficiente x maior valor-teto", rmi <= coeficiente * maior_teto + Decimal("0.005")))
    if limitacao == "não limitado":
        testes.append(("benefício não limitado: RMI = coeficiente x média",
                       abs(rmi - coeficiente * media) < Decimal("0.000001")))
    reprovados = [t for t, ok in testes if not ok]
    if reprovados:
        raise ErroValidacao("teste de sanidade reprovado: %s" % "; ".join(reprovados))

    resultado = {
        "skill": "pericia-previdenciaria-beneficio-pre-cf88",
        "script": "rmi_clps84.py",
        "premissas": {
            "regime": "CLPS, Decreto 89.312/1984, e legislação anterior [A VERIFICAR: arts. 21 e 23]",
            "dib": comp_str(dib),
            "moeda_dib": moeda_dib,
            "n_sc": n_sc,
            "n_corrigidos": n_corr,
            "arquivo_salarios": args.salarios,
            "arquivo_coeficientes": args.coeficientes,
            "arquivo_conversoes": args.conversoes or "",
            "coeficientes_embutem_conversao": bool(args.coeficientes_embutem_conversao),
            "menor_valor_teto": q2(menor_teto),
            "maior_valor_teto": q2(maior_teto),
            "fonte_tetos": args.fonte_tetos,
            "coeficiente_especie_pct": q2(coeficiente * 100),
            "fracao_excedente_informada": args.fracao_excedente or "",
            "grupos_12": args.grupos_12,
            "fracao_excedente_efetiva": fracao_efetiva.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            "fundamento_fracao": args.fundamento_fracao or "",
            "salario_minimo_dib": q2(sm_dib) if sm_dib is not None else None,
            "fonte_salario_minimo": args.fonte_sm or "",
            "coeficiente_aplicado_sobre": "soma da parcela até o menor valor-teto e da parcela "
                                          "fracionada do excedente [A VERIFICAR contra o art. 23 "
                                          "da CLPS/84]",
        },
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "quadro_sc": quadro,
        "soma_sc_corrigidos": q2(soma),
        "media": q2(media),
        "media_limitada_maior_teto": q2(media_limitada),
        "parcela_ate_menor_teto": q2(parcela_base),
        "excedente": q2(excedente),
        "parcela_excedente_considerada": q2(parcela_excedente),
        "base_da_renda": q2(base_renda),
        "rmi": q2(rmi),
        "rmi_em_salarios_minimos": (rmi_em_sm.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                                    if rmi_em_sm is not None else None),
        "limitacao_na_concessao": limitacao,
        "limitado_ao_maior_valor_teto": limitacao == "maior valor-teto",
        "testes_sanidade": [{"teste": t, "ok": ok} for t, ok in testes],
        "avisos": avisos,
        "memoria": memoria,
        "para_readequacao": {
            "dib": comp_str(dib),
            "moeda_dib": moeda_dib,
            "media": str(media),
            "rmi": str(rmi),
            "coeficiente": str(coeficiente),
            "fracao_excedente_efetiva": str(fracao_efetiva),
            "menor_valor_teto": str(menor_teto),
            "maior_valor_teto": str(maior_teto),
            "limitacao_na_concessao": limitacao,
            "rmi_em_salarios_minimos": str(rmi_em_sm) if rmi_em_sm is not None else None,
            "salario_minimo_dib": str(sm_dib) if sm_dib is not None else None,
            "media_em_salarios_minimos": str(media / sm_dib) if sm_dib is not None else None,
            "fonte_salario_minimo": args.fonte_sm or "",
        },
    }
    return resultado


def gerar_md(res):
    p = res["premissas"]
    m = p["moeda_dib"]
    linhas = []
    linhas.append("# Memória da RMI pela CLPS/84 (DIB %s)" % p["dib"])
    linhas.append("")
    linhas.append("| Ordem | Competência | Moeda | SC nominal | SC na moeda da DIB | Coeficiente | SC corrigido | Fonte |")
    linhas.append("|---|---|---|---|---|---|---|---|")
    for l in res["quadro_sc"]:
        linhas.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (
            l["ordem"], l["competencia"], l["moeda_origem"], fmt_br(l["sc_nominal"]),
            fmt_br(l["sc_na_moeda_dib"]), fmt_fator(l["coeficiente"], 6) if l["corrigido"] else "1,000000",
            fmt_br(l["sc_corrigido"]), l["fonte_coeficiente"]))
    linhas.append("")
    linhas.append("| Item | Valor |")
    linhas.append("|---|---|")
    linhas.append("| Soma dos SC corrigidos | %s %s |" % (m, fmt_br(res["soma_sc_corrigidos"])))
    linhas.append("| Média (salário de benefício) | %s %s |" % (m, fmt_br(res["media"])))
    linhas.append("| Menor valor-teto | %s %s |" % (m, fmt_br(p["menor_valor_teto"])))
    linhas.append("| Maior valor-teto | %s %s |" % (m, fmt_br(p["maior_valor_teto"])))
    linhas.append("| Parcela até o menor valor-teto | %s %s |" % (m, fmt_br(res["parcela_ate_menor_teto"])))
    linhas.append("| Excedente (até o maior valor-teto) | %s %s |" % (m, fmt_br(res["excedente"])))
    linhas.append("| Fração efetiva do excedente | %s |" % fmt_fator(p["fracao_excedente_efetiva"], 6))
    linhas.append("| Parcela do excedente considerada | %s %s |" % (m, fmt_br(res["parcela_excedente_considerada"])))
    linhas.append("| Coeficiente da espécie | %s%% |" % fmt_br(p["coeficiente_especie_pct"]))
    linhas.append("| RMI | %s %s |" % (m, fmt_br(res["rmi"])))
    if res["rmi_em_salarios_minimos"] is not None:
        linhas.append("| RMI em salários mínimos | %s |" % fmt_br(res["rmi_em_salarios_minimos"], 4))
    linhas.append("| Limitação na concessão | %s |" % res["limitacao_na_concessao"])
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


def main():
    parser = argparse.ArgumentParser(
        description="RMI de benefício anterior à CF/88 pelas regras da CLPS/84 (skill "
                    "pericia-previdenciaria-beneficio-pre-cf88)")
    parser.add_argument("--salarios", required=True,
                        help="CSV competencia;salario_contribuicao;moeda com o período básico")
    parser.add_argument("--coeficientes", required=True,
                        help="CSV competencia;coeficiente;fonte com os coeficientes ORTN/OTN oficiais")
    parser.add_argument("--conversoes", default=None,
                        help="CSV competencia;divisor;moeda_nova;fonte com os cortes de padrão monetário")
    parser.add_argument("--coeficientes-embutem-conversao", action="store_true",
                        help="declara que os coeficientes já convertem a moeda para a da DIB")
    parser.add_argument("--dib", required=True, help="competência da DIB, mm/aaaa")
    parser.add_argument("--moeda-dib", default=None,
                        help="moeda da DIB (padrão: moeda da última competência do período básico)")
    parser.add_argument("--n-sc", type=int, default=36,
                        help="quantidade de salários de contribuição do período básico (padrão 36)")
    parser.add_argument("--n-corrigidos", type=int, default=24,
                        help="quantidade de SC corrigidos, anteriores aos 12 últimos (padrão 24)")
    parser.add_argument("--menor-teto", required=True, help="menor valor-teto na DIB, na moeda da DIB")
    parser.add_argument("--maior-teto", required=True, help="maior valor-teto na DIB, na moeda da DIB")
    parser.add_argument("--fonte-tetos", required=True, help="fonte dos valores-teto (portaria, tabela)")
    parser.add_argument("--coeficiente", required=True,
                        help="coeficiente da espécie em percentual (ex.: 95 para 95%%)")
    parser.add_argument("--fracao-excedente", default=None,
                        help="fração aplicada ao excedente entre os tetos (ex.: 1/30 ou 0,8)")
    parser.add_argument("--grupos-12", type=int, default=None,
                        help="grupos de 12 contribuições acima do menor valor-teto (multiplica a fração)")
    parser.add_argument("--fundamento-fracao", default=None,
                        help="dispositivo e critério da fração do excedente")
    parser.add_argument("--salario-minimo-dib", default=None,
                        help="salário mínimo vigente na DIB, na moeda da DIB")
    parser.add_argument("--fonte-sm", default=None, help="fonte do salário mínimo da DIB")
    parser.add_argument("--saida", default=None, help="arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--md", default=None, help="grava a memória em Markdown neste arquivo")
    args = parser.parse_args()

    try:
        res = calcular(args)
        texto = json.dumps(res, ensure_ascii=False, indent=2, cls=CodificadorDecimal)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print("RMI %s %s (%s); limitação: %s; JSON gravado em %s"
                  % (res["premissas"]["moeda_dib"], fmt_br(res["rmi"]),
                     ("%s SM" % fmt_br(res["rmi_em_salarios_minimos"], 4))
                     if res["rmi_em_salarios_minimos"] is not None else "SM não informado",
                     res["limitacao_na_concessao"], args.saida))
        else:
            print(texto)
        if args.md:
            Path(args.md).write_text(gerar_md(res), encoding="utf-8")
            print("Memória Markdown gravada em %s" % args.md)
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
