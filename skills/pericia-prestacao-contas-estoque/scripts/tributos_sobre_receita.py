#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tributos incidentes sobre a receita do estoque transferido e receita líquida devida.

Parte da skill: pericia-prestacao-contas-estoque

Recebe a receita bruta mensal atribuída ao estoque antigo (JSON do script
peps_estoque_transferido.py ou CSV mes;receita_bruta), o regime tributário e um
arquivo de parâmetros com as alíquotas e a fonte de cada uma, e devolve, mês a
mês, cada tributo, o total de tributos e a receita líquida que o comprador devia
repassar ao vendedor sob a cláusula "abatidos os impostos".

Uso:
    python3 tributos_sobre_receita.py --receitas peps.json --regime presumido \\
        --parametros assets/exemplo_parametros_tributos.json --cenario amplo \\
        --saida tributos.json --md tributos.md

Regimes e cenários:
    simples    DAS pela alíquota efetiva do PGDAS-D (por mês) ou calculada a partir de
               RBT12 e das faixas do Anexo informadas (LC 123/2006, art. 18, § 1º-A).
               Cenário base e amplo coincidem: o DAS já contém IRPJ e CSLL.
    presumido  ICMS (sempre por arquivo), PIS 0,65% e COFINS 3% (padrões de lei
               consolidada, substituíveis pelo arquivo). Cenário amplo acrescenta IRPJ
               (presunção 8%, 15% e adicional de 10% conforme método declarado) e CSLL
               (presunção 12%, 9%).
    real       Toda alíquota por arquivo (ICMS, PIS, COFINS; IRPJ e CSLL efetivos no
               cenário amplo). Nenhum padrão embutido.

Regra de arredondamento: cada tributo mensal é apurado em centavos (ROUND_HALF_UP),
como no documento de arrecadação; somas e líquidos operam sobre esses centavos,
de modo que todo quadro fecha ao centavo.
"""

import argparse
import csv
import json
import sys
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 28

SKILL = "pericia-prestacao-contas-estoque"
SCRIPT = "tributos_sobre_receita.py"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação; tributo mensal apurado em centavos"
CENT = Decimal("0.01")
CEM = Decimal("100")

# Padrões embutidos: apenas alíquotas de lei federal consolidada, com dispositivo.
PADROES_PRESUMIDO = {
    "pis": {"aliquota": "0,65", "fonte": "Lei 9.715/1998, art. 8º, I (regime cumulativo)"},
    "cofins": {"aliquota": "3,00", "fonte": "Lei 9.718/1998, art. 8º (regime cumulativo)"},
    "irpj": {"presuncao": "8,00", "aliquota": "15,00", "adicional": "10,00", "limite_adicional_mensal": "20.000,00",
             "adicional_metodo": "nenhum",
             "fonte": "Lei 9.249/1995, art. 15, caput (presunção de 8% para comércio) e art. 3º, caput e § 1º (15% e adicional de 10%)"},
    "csll": {"presuncao": "12,00", "aliquota": "9,00",
             "fonte": "Lei 9.249/1995, art. 20 (base de 12% para comércio); Lei 7.689/1988, art. 3º (alíquota geral de 9%)"},
}
METODOS_ADICIONAL = ("nenhum", "integral", "faixa_mensal")


class ErroValidacao(Exception):
    """Erro de entrada do usuário: sai com código 1 e mensagem clara."""


# ----------------------------------------------------------------------------
# Utilitários
# ----------------------------------------------------------------------------

def parse_num(texto, campo="valor"):
    """Converte número brasileiro (1.234,56) ou técnico (1234.56) em Decimal."""
    if texto is None:
        raise ErroValidacao(f"campo '{campo}' ausente")
    t = str(texto).strip().replace("R$", "").replace("%", "").replace(" ", "")
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


def pct(valor):
    """Alíquota em padrão brasileiro com 4 casas, sem zeros supérfluos além de 2."""
    v = Decimal(valor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    texto = f"{v:.4f}".rstrip("0")
    if texto.endswith("."):
        texto += "00"
    elif len(texto.split(".")[1]) < 2:
        texto += "0"
    return texto.replace(".", ",") + "%"


def validar_mes(mes, origem):
    t = str(mes).strip()
    partes = t.split("/")
    if len(partes) != 2 or not partes[0].isdigit() or not partes[1].isdigit() or not 1 <= int(partes[0]) <= 12:
        raise ErroValidacao(f"{origem}: mês inválido '{mes}' (esperado mm/aaaa)")
    return f"{int(partes[0]):02d}/{partes[1]}"


def chave_mes(mes):
    m, a = mes.split("/")
    return (int(a), int(m))


# ----------------------------------------------------------------------------
# Entrada de receitas
# ----------------------------------------------------------------------------

def ler_receitas(caminho):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"arquivo de receitas não encontrado: {caminho}")
    if p.suffix.lower() == ".json":
        dados = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(dados, dict) and "receita_antigo_por_mes" in dados:
            lista = dados["receita_antigo_por_mes"]
            origem = f"JSON de {dados.get('script', 'script anterior')}"
        elif isinstance(dados, list):
            lista = dados
            origem = "lista JSON"
        else:
            raise ErroValidacao("JSON de receitas sem a chave 'receita_antigo_por_mes' nem formato de lista [{mes, receita_bruta}]")
        receitas = OrderedDict()
        for r in lista:
            mes = validar_mes(r.get("mes"), "receitas")
            receitas[mes] = parse_num(r.get("receita_bruta"), f"receita_bruta de {mes}")
    else:
        with p.open(encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f, delimiter=";")
            if leitor.fieldnames is None or "mes" not in [c.strip().lower() for c in leitor.fieldnames]:
                raise ErroValidacao("CSV de receitas precisa do cabeçalho mes;receita_bruta")
            receitas = OrderedDict()
            for linha in leitor:
                reg = {k.strip().lower(): (v or "").strip() for k, v in linha.items() if k}
                if not any(reg.values()):
                    continue
                mes = validar_mes(reg["mes"], "receitas")
                receitas[mes] = parse_num(reg.get("receita_bruta"), f"receita_bruta de {mes}")
        origem = "CSV mes;receita_bruta"
    if not receitas:
        raise ErroValidacao("nenhuma competência de receita encontrada")
    for mes, v in receitas.items():
        if v < 0:
            raise ErroValidacao(f"receita bruta negativa em {mes}: tratar devolução como compensação, não como receita negativa")
    ordenado = OrderedDict(sorted(receitas.items(), key=lambda kv: chave_mes(kv[0])))
    return ordenado, origem


# ----------------------------------------------------------------------------
# Parâmetros tributários
# ----------------------------------------------------------------------------

def ler_parametros(caminho):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"arquivo de parâmetros não encontrado: {caminho}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErroValidacao(f"arquivo de parâmetros com JSON inválido: {e}")


def exigir_fonte(bloco, nome):
    fonte = str(bloco.get("fonte", "")).strip()
    if not fonte:
        raise ErroValidacao(f"parâmetro '{nome}' sem o campo 'fonte': toda alíquota precisa declarar de onde veio")
    return fonte


def aliquota_do_mes(bloco, nome, mes, campo="aliquota"):
    """Alíquota única (campo) ou por mês (campo + '_por_mes'); percentual, ex. 18,00."""
    por_mes = bloco.get(f"{campo}_por_mes")
    if por_mes:
        if mes not in por_mes:
            raise ErroValidacao(f"parâmetro '{nome}': falta {campo} para a competência {mes} em '{campo}_por_mes'")
        return parse_num(por_mes[mes], f"{nome}.{campo}_por_mes[{mes}]")
    if campo in bloco:
        return parse_num(bloco[campo], f"{nome}.{campo}")
    raise ErroValidacao(f"parâmetro '{nome}' sem '{campo}' nem '{campo}_por_mes'")


def resolver_bloco(parametros, nome, regime, obrigatorio, alertas):
    """Une o bloco do arquivo com o padrão embutido (se houver) e registra a origem."""
    bloco = dict(parametros.get(nome) or {})
    padrao = PADROES_PRESUMIDO.get(nome) if regime == "presumido" else None
    if not bloco:
        if padrao:
            bloco = dict(padrao)
            bloco["_origem"] = "padrão embutido (lei federal consolidada)"
            alertas.append(f"{nome.upper()}: alíquota não informada no arquivo; adotado o padrão legal ({padrao['fonte']}).")
        elif obrigatorio:
            raise ErroValidacao(f"regime {regime}: o parâmetro '{nome}' deve constar do arquivo com alíquota e fonte")
        else:
            return None
    else:
        if padrao:
            for k, v in padrao.items():
                bloco.setdefault(k, v)
        bloco["_origem"] = "arquivo de parâmetros"
    exigir_fonte(bloco, nome)
    return bloco


def aliquota_efetiva_simples(rbt12, faixas):
    """LC 123/2006, art. 18, § 1º-A: (RBT12 x alíquota nominal - parcela a deduzir) / RBT12."""
    if rbt12 <= 0:
        raise ErroValidacao("RBT12 deve ser positivo para calcular a alíquota efetiva do Simples")
    for faixa in faixas:
        if rbt12 <= parse_num(faixa["ate"], "faixa.ate"):
            nominal = parse_num(faixa["aliquota"], "faixa.aliquota")
            deduzir = parse_num(faixa["deduzir"], "faixa.deduzir")
            return (rbt12 * nominal / CEM - deduzir) / rbt12 * CEM, nominal, deduzir
    raise ErroValidacao(f"RBT12 de R$ {br(rbt12)} acima da última faixa informada: contribuinte fora do Simples ou tabela incompleta")


# ----------------------------------------------------------------------------
# Cálculo
# ----------------------------------------------------------------------------

def calcular(receitas, regime, cenario, parametros, alertas, memoria):
    tributos_premissas = OrderedDict()
    meses = []

    if regime == "simples":
        simples = parametros.get("simples")
        if not simples:
            raise ErroValidacao("regime simples exige o bloco 'simples' no arquivo de parâmetros")
        fonte = exigir_fonte(simples, "simples")
        tem_declarada = bool(simples.get("aliquota_efetiva") or simples.get("aliquota_efetiva_por_mes"))
        tem_calculo = bool(simples.get("rbt12_por_mes") and simples.get("faixas_anexo"))
        if not tem_declarada and not tem_calculo:
            raise ErroValidacao("bloco 'simples' precisa de 'aliquota_efetiva' (ou '_por_mes') ou de 'rbt12_por_mes' com 'faixas_anexo'")
        tributos_premissas["das"] = OrderedDict([
            ("base", "receita bruta do estoque antigo"),
            ("origem_aliquota", "PGDAS-D declarada" + (" com conferência pelas faixas" if tem_calculo else "") if tem_declarada else "calculada por RBT12 e faixas do Anexo"),
            ("fonte", fonte),
            ("fonte_faixas", simples.get("fonte_faixas", "não informada")),
        ])
        if cenario == "amplo":
            alertas.append("Simples Nacional: cenário amplo coincide com o base, pois o DAS já reúne IRPJ e CSLL (LC 123/2006, art. 13).")
        memoria.append("Regime Simples Nacional: tributo único (DAS) sobre a receita bruta, pela alíquota efetiva de cada competência.")
        for mes, receita in receitas.items():
            detalhe = OrderedDict()
            calculada = None
            if tem_calculo:
                rbt12_txt = simples["rbt12_por_mes"].get(mes)
                if rbt12_txt is None:
                    raise ErroValidacao(f"simples.rbt12_por_mes sem a competência {mes}")
                rbt12 = parse_num(rbt12_txt, f"rbt12[{mes}]")
                calculada, nominal, deduzir = aliquota_efetiva_simples(rbt12, simples["faixas_anexo"])
                detalhe["rbt12"] = tec(rbt12)
                detalhe["aliquota_nominal"] = pct(nominal)
                detalhe["parcela_deduzir"] = tec(deduzir)
                detalhe["aliquota_efetiva_calculada"] = pct(calculada)
            if tem_declarada:
                aliq = aliquota_do_mes(simples, "simples", mes, "aliquota_efetiva")
                detalhe["aliquota_efetiva_declarada"] = pct(aliq)
                if calculada is not None and abs(aliq - calculada) > Decimal("0.01"):
                    alertas.append(
                        f"Simples {mes}: alíquota efetiva declarada {pct(aliq)} diverge da calculada {pct(calculada)} "
                        f"pelas faixas informadas. Prevalece a declarada (PGDAS-D) e a divergência vai ao laudo para conferência.")
            else:
                aliq = calculada
            valor = q2(receita * aliq / CEM)
            tributos = OrderedDict([("das", OrderedDict([("aliquota", pct(aliq)), ("valor", tec(valor))] + list(detalhe.items())))])
            meses.append(montar_mes(mes, receita, tributos, valor))
            memoria.append(f"{mes}: DAS = R$ {br(receita)} x {pct(aliq)} = R$ {br(valor)}; líquida R$ {br(receita - valor)}.")
        return meses, tributos_premissas

    # presumido e real
    obrig = True
    icms = resolver_bloco(parametros, "icms", regime, obrig, alertas)
    pis = resolver_bloco(parametros, "pis", regime, obrig, alertas)
    cofins = resolver_bloco(parametros, "cofins", regime, obrig, alertas)
    for nome, bloco in (("icms", icms), ("pis", pis), ("cofins", cofins)):
        tributos_premissas[nome] = OrderedDict([
            ("base", "receita bruta do estoque antigo (tributo por dentro do preço)"),
            ("aliquota", bloco.get("aliquota", "por mês")),
            ("origem", bloco["_origem"]),
            ("fonte", bloco["fonte"]),
        ])
        if nome == "icms" and "aliquota" in bloco and parse_num(bloco["aliquota"], "icms.aliquota") == 0:
            if not str(bloco.get("justificativa", "")).strip():
                raise ErroValidacao("ICMS com alíquota zero exige o campo 'justificativa' (ex.: substituição tributária, isenção)")
            tributos_premissas[nome]["justificativa"] = bloco["justificativa"]

    irpj = csll = None
    if cenario == "amplo":
        irpj = resolver_bloco(parametros, "irpj", regime, True, alertas)
        csll = resolver_bloco(parametros, "csll", regime, True, alertas)
        if regime == "presumido":
            metodo = str(irpj.get("adicional_metodo", "nenhum")).strip().lower()
            if metodo not in METODOS_ADICIONAL:
                raise ErroValidacao(f"irpj.adicional_metodo deve ser um de {METODOS_ADICIONAL}")
            if metodo != "nenhum" and not str(irpj.get("justificativa_adicional", "")).strip():
                raise ErroValidacao("irpj.adicional_metodo diferente de 'nenhum' exige 'justificativa_adicional' (ex.: ECF do período)")
            tributos_premissas["irpj"] = OrderedDict([
                ("base", "lucro presumido = receita bruta x presunção"),
                ("presuncao", irpj["presuncao"]), ("aliquota", irpj["aliquota"]),
                ("adicional", irpj["adicional"]), ("limite_adicional_mensal", irpj["limite_adicional_mensal"]),
                ("adicional_metodo", metodo), ("justificativa_adicional", irpj.get("justificativa_adicional", "")),
                ("origem", irpj["_origem"]), ("fonte", irpj["fonte"]),
            ])
            tributos_premissas["csll"] = OrderedDict([
                ("base", "base presumida = receita bruta x presunção"),
                ("presuncao", csll["presuncao"]), ("aliquota", csll["aliquota"]),
                ("origem", csll["_origem"]), ("fonte", csll["fonte"]),
            ])
            memoria.append(f"Cenário amplo: IRPJ e CSLL presumidos; adicional de IRPJ pelo método '{metodo}'.")
        else:
            for nome, bloco in (("irpj", irpj), ("csll", csll)):
                if "aliquota_efetiva" not in bloco and "aliquota_efetiva_por_mes" not in bloco:
                    raise ErroValidacao(f"regime real, cenário amplo: '{nome}' exige 'aliquota_efetiva' sobre a receita (ou '_por_mes'), extraída da apuração do período")
                tributos_premissas[nome] = OrderedDict([
                    ("base", "receita bruta x alíquota efetiva informada pelo perito a partir da apuração real"),
                    ("origem", bloco["_origem"]), ("fonte", bloco["fonte"]),
                ])
            memoria.append("Cenário amplo no Lucro Real: IRPJ e CSLL por alíquota efetiva informada.")
    memoria.append(f"Regime {regime}: tributos sobre a receita (ICMS, PIS e COFINS) apurados mês a mês em centavos.")

    for mes, receita in receitas.items():
        tributos = OrderedDict()
        total = Decimal(0)
        for nome, bloco in (("icms", icms), ("pis", pis), ("cofins", cofins)):
            aliq = aliquota_do_mes(bloco, nome, mes)
            valor = q2(receita * aliq / CEM)
            tributos[nome] = OrderedDict([("aliquota", pct(aliq)), ("valor", tec(valor))])
            total += valor
        if cenario == "amplo":
            if regime == "presumido":
                presuncao = parse_num(irpj["presuncao"], "irpj.presuncao")
                base_irpj = receita * presuncao / CEM
                irpj_normal = q2(base_irpj * parse_num(irpj["aliquota"], "irpj.aliquota") / CEM)
                metodo = tributos_premissas["irpj"]["adicional_metodo"]
                adicional_aliq = parse_num(irpj["adicional"], "irpj.adicional")
                if metodo == "integral":
                    adicional = q2(base_irpj * adicional_aliq / CEM)
                elif metodo == "faixa_mensal":
                    limite = parse_num(irpj["limite_adicional_mensal"], "irpj.limite_adicional_mensal")
                    adicional = q2(max(base_irpj - limite, Decimal(0)) * adicional_aliq / CEM)
                else:
                    adicional = Decimal(0)
                tributos["irpj"] = OrderedDict([
                    ("base_presumida", tec(base_irpj)), ("aliquota", pct(parse_num(irpj["aliquota"], "irpj.aliquota"))),
                    ("valor_normal", tec(irpj_normal)), ("adicional", tec(adicional)), ("valor", tec(irpj_normal + adicional)),
                ])
                total += irpj_normal + adicional
                base_csll = receita * parse_num(csll["presuncao"], "csll.presuncao") / CEM
                v_csll = q2(base_csll * parse_num(csll["aliquota"], "csll.aliquota") / CEM)
                tributos["csll"] = OrderedDict([("base_presumida", tec(base_csll)),
                                                ("aliquota", pct(parse_num(csll["aliquota"], "csll.aliquota"))), ("valor", tec(v_csll))])
                total += v_csll
            else:
                for nome, bloco in (("irpj", irpj), ("csll", csll)):
                    aliq = aliquota_do_mes(bloco, nome, mes, "aliquota_efetiva")
                    valor = q2(receita * aliq / CEM)
                    tributos[nome] = OrderedDict([("aliquota", pct(aliq)), ("valor", tec(valor))])
                    total += valor
        meses.append(montar_mes(mes, receita, tributos, total))
        detalhe = ", ".join(f"{k.upper()} {v['valor']}" for k, v in tributos.items())
        memoria.append(f"{mes}: receita R$ {br(receita)}; tributos R$ {br(total)} ({detalhe}); líquida R$ {br(receita - total)}.")
    return meses, tributos_premissas


def montar_mes(mes, receita, tributos, total):
    liquida = receita - total
    return OrderedDict([
        ("mes", mes),
        ("receita_bruta", tec(receita)),
        ("tributos", tributos),
        ("total_tributos", tec(total)),
        ("receita_liquida", tec(liquida)),
        ("receita_liquida_br", br(liquida)),
        ("carga_efetiva", pct(total / receita * CEM) if receita else "0,00%"),
    ])


def verificar_sanidade(meses):
    testes = []
    ok = True
    quebra = [m["mes"] for m in meses
              if Decimal(m["receita_bruta"]) - Decimal(m["total_tributos"]) != Decimal(m["receita_liquida"])]
    testes.append({"teste": "receita bruta - tributos = receita líquida, em cada mês",
                   "resultado": "OK" if not quebra else f"FALHA em {quebra}"})
    ok &= not quebra
    soma = [m["mes"] for m in meses
            if sum((Decimal(t["valor"]) for t in m["tributos"].values()), Decimal(0)) != Decimal(m["total_tributos"])]
    testes.append({"teste": "soma dos tributos do mês = total de tributos do mês",
                   "resultado": "OK" if not soma else f"FALHA em {soma}"})
    ok &= not soma
    excesso = [m["mes"] for m in meses if Decimal(m["total_tributos"]) > Decimal(m["receita_bruta"])]
    testes.append({"teste": "tributos nunca superam a receita bruta",
                   "resultado": "OK" if not excesso else f"FALHA em {excesso}"})
    ok &= not excesso
    negativos = [m["mes"] for m in meses if any(Decimal(t["valor"]) < 0 for t in m["tributos"].values())]
    testes.append({"teste": "nenhum tributo negativo",
                   "resultado": "OK" if not negativos else f"FALHA em {negativos}"})
    ok &= not negativos
    return testes, ok


def gravar_md(caminho, saida):
    nomes = []
    for m in saida["meses"]:
        for k in m["tributos"]:
            if k not in nomes:
                nomes.append(k)
    L = [f"# Tributos sobre a receita do estoque transferido (regime {saida['premissas']['regime']}, cenário {saida['premissas']['cenario']})", ""]
    L.append("| Mês | Receita bruta (R$) | " + " | ".join(f"{n.upper()} (R$)" for n in nomes) + " | Total tributos (R$) | Receita líquida (R$) | Carga |")
    L.append("|---|---:|" + "---:|" * len(nomes) + "---:|---:|---:|")
    for m in saida["meses"]:
        L.append(f"| {m['mes']} | {br(m['receita_bruta'])} | " + " | ".join(br(m["tributos"][n]["valor"]) if n in m["tributos"] else "0,00" for n in nomes)
                 + f" | {br(m['total_tributos'])} | {br(m['receita_liquida'])} | {m['carga_efetiva']} |")
    t = saida["totais"]
    L.append(f"| Total | {br(t['receita_bruta'])} | " + " | ".join(br(t["tributos"].get(n, "0")) for n in nomes)
             + f" | {br(t['total_tributos'])} | {br(t['receita_liquida'])} | {t['carga_efetiva']} |")
    L.append("")
    L.append("## Alíquotas e fontes")
    L.append("")
    for nome, p in saida["premissas"]["tributos"].items():
        L.append(f"- {nome.upper()}: " + "; ".join(f"{k} = {v}" for k, v in p.items() if v not in ("", None)))
    L.append("")
    if saida["alertas"]:
        L.append("## Alertas")
        L.append("")
        L.extend(f"- {a}" for a in saida["alertas"])
        L.append("")
    L.append("## Sanidade")
    L.append("")
    L.extend(f"- {x['teste']}: {x['resultado']}" for x in saida["sanidade"])
    L.append("")
    L.append(f"Leitura da cláusula: {saida['premissas']['leitura_clausula']}")
    L.append(f"Locale: {saida['locale']}. Arredondamento: {saida['arredondamento']}.")
    Path(caminho).write_text("\n".join(L) + "\n", encoding="utf-8")


def construir_parser():
    p = argparse.ArgumentParser(
        description="Apura os tributos sobre a receita do estoque transferido e a receita líquida devida (skill pericia-prestacao-contas-estoque).")
    p.add_argument("--receitas", required=True, help="JSON gerado por peps_estoque_transferido.py ou CSV mes;receita_bruta")
    p.add_argument("--regime", required=True, choices=["simples", "presumido", "real"], help="Regime tributário do comprador no período das vendas")
    p.add_argument("--parametros", required=True, help="JSON com alíquotas e fonte de cada tributo (ver assets/exemplo_parametros_tributos.json)")
    p.add_argument("--cenario", default="base", choices=["base", "amplo"],
                   help="base: só tributos sobre a receita (ICMS, PIS, COFINS ou DAS); amplo: acrescenta IRPJ e CSLL")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="Grava o quadro mensal em Markdown para o laudo")
    return p


def main():
    args = construir_parser().parse_args()
    try:
        receitas, origem = ler_receitas(args.receitas)
        parametros = ler_parametros(args.parametros)
        regime_arquivo = str(parametros.get("regime", "")).strip().lower()
        alertas, memoria = [], []
        if regime_arquivo and regime_arquivo != args.regime:
            alertas.append(f"O arquivo de parâmetros declara regime '{regime_arquivo}', mas a execução usa '{args.regime}'. Conferir.")
        memoria.append(f"Receitas lidas de {origem}: {len(receitas)} competências, de {next(iter(receitas))} a {list(receitas)[-1]}.")

        meses, tributos_premissas = calcular(receitas, args.regime, args.cenario, parametros, alertas, memoria)
        testes, ok = verificar_sanidade(meses)
        if not ok:
            raise RuntimeError(f"teste de sanidade falhou: {[t for t in testes if t['resultado'] != 'OK']}")

        tot_bruta = sum((Decimal(m["receita_bruta"]) for m in meses), Decimal(0))
        tot_trib = sum((Decimal(m["total_tributos"]) for m in meses), Decimal(0))
        tot_liq = sum((Decimal(m["receita_liquida"]) for m in meses), Decimal(0))
        por_tributo = OrderedDict()
        for m in meses:
            for nome, t in m["tributos"].items():
                por_tributo[nome] = tec(Decimal(por_tributo.get(nome, "0")) + Decimal(t["valor"]))
        memoria.append(f"Totais: receita bruta R$ {br(tot_bruta)}; tributos R$ {br(tot_trib)}; receita líquida devida R$ {br(tot_liq)}.")

        saida = OrderedDict([
            ("skill", SKILL),
            ("script", SCRIPT),
            ("premissas", OrderedDict([
                ("regime", args.regime),
                ("cenario", args.cenario),
                ("leitura_clausula", parametros.get("leitura_clausula", "não informada no arquivo de parâmetros")),
                ("tributos", tributos_premissas),
                ("fontes", OrderedDict([("receitas", str(args.receitas)), ("parametros", str(args.parametros))])),
            ])),
            ("locale", LOCALE),
            ("arredondamento", ARREDONDAMENTO),
            ("meses", meses),
            ("totais", OrderedDict([
                ("receita_bruta", tec(tot_bruta)), ("tributos", por_tributo), ("total_tributos", tec(tot_trib)),
                ("receita_liquida", tec(tot_liq)), ("receita_liquida_br", br(tot_liq)),
                ("carga_efetiva", pct(tot_trib / tot_bruta * CEM) if tot_bruta else "0,00%"),
            ])),
            ("alertas", alertas),
            ("sanidade", testes),
            ("memoria", memoria),
        ])
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"JSON gravado em {args.saida}: regime {args.regime}, cenário {args.cenario}; receita bruta R$ {br(tot_bruta)}, "
                  f"tributos R$ {br(tot_trib)}, líquida devida R$ {br(tot_liq)}; {len(alertas)} alerta(s); sanidade OK.")
        else:
            print(texto)
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
