#!/usr/bin/env python3
"""
Haveres do sócio: quota patrimonial, lucros e JCP declarados, remuneração de
administrador, deduções, prazo de pagamento e termos de correção e juros.

Parte da skill: apuracao-haveres (v2.0.0).

Encadeia a saída de balanco_determinacao.py (PL de determinação) e, se houver,
de fundo_comercio.py, aplica a participação do sócio (CC, art. 1.031: quota pelo
montante efetivamente realizado), integra lucros ou JCP declarados e não pagos e
a remuneração como administrador devida até a data da resolução (CPC, art. 608),
deduz adiantamentos e indenização compensável (CPC, art. 602) e informa o prazo
de pagamento (CC, art. 1.031, § 2º: 90 dias da liquidação, salvo contrato) com
os termos iniciais de correção (data da resolução) e de juros (91º dia).

Gera parcelas.json no formato da skill atualizacao-monetaria, regime civil:
    [{"competencia": "mm/aaaa", "valor": 1234.56, "descricao": "..."}]
Deduções entram como parcelas negativas na própria competência.

Uso:
    python3 haveres_socio.py --balanco balanco.json --fundo-comercio fundo.json \
        --participacao 25% --data-resolucao 30/06/2025 \
        --lucros-declarados assets/exemplo_lucros_declarados.json \
        --remuneracao-administrador assets/exemplo_remuneracao_administrador.json \
        --adiantamentos assets/exemplo_adiantamentos.json \
        --data-ajuizamento 15/08/2025 --saida haveres.json --md haveres.md --parcelas parcelas.json
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 28

VERSAO = "2.0.0"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
CENTAVO = Decimal("0.01")
PRAZO_LEGAL_DIAS = 90

HIPOTESES = {
    "retirada_imotivada": ("CPC, art. 605, II", "sexagésimo dia seguinte ao do recebimento, pela sociedade, da notificação do sócio retirante"),
    "recesso": ("CPC, art. 605, III", "dia do recebimento, pela sociedade, da notificação do sócio dissidente"),
    "falecimento": ("CPC, art. 605, I", "data do óbito"),
    "retirada_justa_causa": ("CPC, art. 605, IV", "trânsito em julgado da decisão que dissolver a sociedade"),
    "exclusao_judicial": ("CPC, art. 605, IV", "trânsito em julgado da decisão que dissolver a sociedade"),
    "exclusao_extrajudicial": ("CPC, art. 605, V", "data da assembleia ou da reunião de sócios que deliberou a exclusão"),
}


class ErroValidacao(Exception):
    """Erro de dado de entrada: sai com código 1 e mensagem objetiva."""


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------

def parse_num(valor, campo="valor"):
    """Aceita 1.234,56 (brasileiro), 1234.56 (técnico) e 12,5% (vira fração)."""
    if valor is None:
        raise ErroValidacao(f"campo '{campo}' ausente")
    if isinstance(valor, bool):
        raise ErroValidacao(f"campo '{campo}' não pode ser booleano")
    texto = repr(valor) if isinstance(valor, (int, float)) else str(valor)
    texto = texto.strip().replace("R$", "").replace(" ", "")
    if texto == "":
        raise ErroValidacao(f"campo '{campo}' vazio")
    percentual = texto.endswith("%")
    if percentual:
        texto = texto[:-1]
    negativo = texto.startswith("-")
    if negativo or texto.startswith("+"):
        texto = texto[1:]
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1:
        texto = texto.replace(".", "")
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        raise ErroValidacao(f"campo '{campo}' com número inválido: {valor!r}")
    if negativo:
        numero = -numero
    if percentual:
        numero = numero / Decimal(100)
    return numero


def q2(valor):
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def tecnico(valor):
    return str(q2(valor))


def fmt_br(valor, casas=2):
    quantum = Decimal(1).scaleb(-casas)
    texto = f"{Decimal(valor).quantize(quantum, rounding=ROUND_HALF_UP):,.{casas}f}"
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


def moeda(valor):
    return "R$ " + fmt_br(valor)


def pct(fracao):
    return fmt_br(Decimal(fracao) * 100, 4).rstrip("0").rstrip(",") + "%"


def parse_data(texto, campo="data"):
    if not texto:
        raise ErroValidacao(f"campo '{campo}' ausente (formato dd/mm/aaaa)")
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ErroValidacao(f"campo '{campo}' fora do formato dd/mm/aaaa: {texto!r}")


def fmt_data(d):
    return d.strftime("%d/%m/%Y")


def competencia(d):
    return d.strftime("%m/%Y")


def parse_competencia(texto, campo):
    try:
        return datetime.strptime(str(texto).strip(), "%m/%Y").date()
    except ValueError:
        raise ErroValidacao(f"campo '{campo}' fora do formato mm/aaaa: {texto!r}")


def somar_anos(d, anos):
    """Soma anos preservando dia e mês (29/02 vira 28/02), na forma do CC, art. 132, § 3º."""
    try:
        return d.replace(year=d.year + anos)
    except ValueError:
        return d.replace(year=d.year + anos, day=28)


def ler_json(caminho, rotulo):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"{rotulo} não encontrado: {p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ErroValidacao(f"JSON inválido em {p}: {exc}")


def numero_ou_arquivo(arg, campo):
    """Aceita um valor (1.234,56) ou o caminho de um JSON com lista de lançamentos."""
    if arg is None:
        return None
    if str(arg).lower().endswith(".json"):
        dados = ler_json(arg, campo)
        if not isinstance(dados, list):
            raise ErroValidacao(f"{campo}: o JSON deve ser uma lista de lançamentos")
        return dados
    return parse_num(arg, campo)


# ----------------------------------------------------------------------------
# Componentes
# ----------------------------------------------------------------------------

def ler_lucros(lista, participacao, data_resolucao, data_ajuizamento, incluir_prescritos, alertas):
    itens, total, prescritos = [], Decimal(0), Decimal(0)
    limite = somar_anos(data_ajuizamento, -3) if data_ajuizamento else None
    for i, item in enumerate(lista or []):
        desc = (item.get("descricao") or "").strip() or f"lucros declarados {i + 1}"
        tipo = (item.get("tipo") or "lucros").strip().lower()
        if tipo not in ("lucros", "jcp"):
            raise ErroValidacao(f"lucros[{i}] tipo {tipo!r} inválido; use lucros ou jcp")
        deliberacao = parse_data(item.get("data_deliberacao"), f"lucros[{i}].data_deliberacao")
        if deliberacao > data_resolucao:
            raise ErroValidacao(f"lucros[{i}] '{desc}': deliberado em {fmt_data(deliberacao)}, após a data da resolução {fmt_data(data_resolucao)}; o CPC, art. 608, só integra lucros declarados até a data da resolução")
        if item.get("valor_socio") is not None:
            valor = parse_num(item["valor_socio"], f"lucros[{i}].valor_socio")
            base = "valor atribuído ao sócio"
        elif item.get("valor_sociedade") is not None:
            valor = parse_num(item["valor_sociedade"], f"lucros[{i}].valor_sociedade") * participacao
            base = f"valor total deliberado x participação {pct(participacao)}"
        else:
            raise ErroValidacao(f"lucros[{i}] '{desc}': informe valor_socio ou valor_sociedade")
        pago = parse_num(item.get("pago", "0"), f"lucros[{i}].pago")
        if pago < 0 or valor < 0:
            raise ErroValidacao(f"lucros[{i}] '{desc}': valores negativos")
        if pago > valor:
            raise ErroValidacao(f"lucros[{i}] '{desc}': pago ({moeda(pago)}) maior que o devido ({moeda(valor)})")
        saldo = valor - pago
        situacao = "exigível"
        if limite is not None and somar_anos(deliberacao, 3) < data_ajuizamento:
            situacao = "prescrito"
        registro = {
            "descricao": desc, "tipo": tipo, "data_deliberacao": fmt_data(deliberacao),
            "competencia": competencia(deliberacao), "base": base, "valor": tecnico(valor),
            "pago": tecnico(pago), "saldo": tecnico(saldo), "situacao": situacao,
            "fonte": (item.get("fonte") or "").strip(),
        }
        if situacao == "prescrito" and not incluir_prescritos:
            registro["tratamento"] = f"excluído: deliberado em {fmt_data(deliberacao)}, mais de 3 anos antes do ajuizamento em {fmt_data(data_ajuizamento)} (CC, art. 206, § 3º; REsp 1.904.252, 4ª Turma)"
            prescritos += saldo
        else:
            if situacao == "prescrito":
                registro["tratamento"] = "incluído por --incluir-prescritos apesar do prazo trienal; declarar a controvérsia no laudo"
                alertas.append(f"'{desc}' incluído apesar da prescrição trienal aparente")
            else:
                registro["tratamento"] = "integra os haveres (CPC, art. 608, caput)"
            total += saldo
        itens.append(registro)
    if lista and limite is None:
        alertas.append("sem --data-ajuizamento: prescrição trienal dos lucros declarados não conferida (CC, art. 206, § 3º)")
    return itens, total, prescritos


def ler_lancamentos(dados, campo, data_resolucao, alertas, descricao_padrao):
    """Remuneração de administrador ou adiantamentos: número único ou lista com competência/data."""
    itens, total = [], Decimal(0)
    if dados is None:
        return itens, total
    if isinstance(dados, Decimal):
        if dados < 0:
            raise ErroValidacao(f"{campo}: valor negativo")
        itens.append({"descricao": descricao_padrao, "competencia": competencia(data_resolucao), "valor": tecnico(dados), "fonte": "informado na linha de comando"})
        return itens, dados
    for i, item in enumerate(dados):
        valor = parse_num(item.get("valor"), f"{campo}[{i}].valor")
        if valor < 0:
            raise ErroValidacao(f"{campo}[{i}]: valor negativo")
        if item.get("data"):
            comp = competencia(parse_data(item["data"], f"{campo}[{i}].data"))
            data_txt = fmt_data(parse_data(item["data"], f"{campo}[{i}].data"))
        elif item.get("competencia"):
            comp_data = parse_competencia(item["competencia"], f"{campo}[{i}].competencia")
            comp = competencia(comp_data)
            data_txt = ""
            if campo == "remuneracao_administrador" and comp_data > data_resolucao.replace(day=1):
                raise ErroValidacao(f"{campo}[{i}]: competência {comp} posterior à data da resolução; a remuneração só integra os haveres até a resolução (CPC, art. 608)")
        else:
            raise ErroValidacao(f"{campo}[{i}]: informe 'data' (dd/mm/aaaa) ou 'competencia' (mm/aaaa)")
        itens.append({"descricao": (item.get("descricao") or "").strip() or descricao_padrao, "competencia": comp, "data": data_txt, "valor": tecnico(valor), "fonte": (item.get("fonte") or "").strip()})
        total += valor
    return itens, total


# ----------------------------------------------------------------------------
# Núcleo
# ----------------------------------------------------------------------------

def apurar(args):
    alertas = []
    balanco = ler_json(args.balanco, "JSON do balanço")
    totais = balanco.get("totais") or {}
    if "pl_determinacao" not in totais:
        raise ErroValidacao("JSON do balanço sem totais.pl_determinacao; gere-o com balanco_determinacao.py v2")
    pl_determinacao = parse_num(totais["pl_determinacao"], "balanco.totais.pl_determinacao")
    premissas_bal = balanco.get("premissas") or {}
    data_resolucao = parse_data(args.data_resolucao, "--data-resolucao")
    if premissas_bal.get("data_resolucao") and premissas_bal["data_resolucao"] != fmt_data(data_resolucao):
        raise ErroValidacao(f"--data-resolucao {fmt_data(data_resolucao)} difere da data do balanço ({premissas_bal['data_resolucao']}); o balanço de determinação precisa ser levantado na data da resolução (CPC, arts. 605 e 606)")
    hipotese = (args.hipotese or (premissas_bal.get("data_resolucao_conferencia") or {}).get("hipotese") or "").strip().lower()
    if hipotese and hipotese not in HIPOTESES:
        raise ErroValidacao(f"hipótese desconhecida: {hipotese!r}; use uma de {', '.join(HIPOTESES)}")
    regra_605 = f"{HIPOTESES[hipotese][0]}: {HIPOTESES[hipotese][1]}" if hipotese else "CPC, art. 605 (hipótese não informada)"

    participacao = parse_num(args.participacao, "--participacao")
    if args.participacao.strip().endswith("%") is False:
        participacao = participacao / Decimal(100)
    if participacao <= 0 or participacao > 1:
        raise ErroValidacao("--participacao deve ficar entre 0 e 100 (informe em pontos percentuais, ex.: 25 ou 25%)")
    if participacao < Decimal("0.01"):
        alertas.append(f"participação de {pct(participacao)}: confirme se o valor foi informado em pontos percentuais")
    integralizado = parse_num(args.integralizado, "--integralizado")
    if not args.integralizado.strip().endswith("%"):
        integralizado = integralizado / Decimal(100)
    if integralizado <= 0 or integralizado > 1:
        raise ErroValidacao("--integralizado deve ficar entre 0 e 100%")

    fundo = Decimal(0)
    fundo_info = "não informado: haveres sem fundo de comércio (registrar no laudo se o intangível foi avaliado e por quê)"
    if args.fundo_comercio:
        fc = ler_json(args.fundo_comercio, "JSON do fundo de comércio")
        if fc.get("premissas", {}).get("data_resolucao") not in (None, "", fmt_data(data_resolucao)):
            raise ErroValidacao(f"data da resolução do fundo de comércio ({fc['premissas']['data_resolucao']}) difere de {fmt_data(data_resolucao)}")
        fundo = parse_num((fc.get("resultado") or {}).get("fundo_comercio"), "fundo_comercio.resultado.fundo_comercio")
        fundo_info = f"fundo_comercio.py, método {fc.get('premissas', {}).get('metodo', '')}"
        if parse_num(totais.get("intangiveis_reconhecidos", "0")) > 0 and any(a.get("grupo") == "fundo_comercio" for a in balanco.get("ativos", [])):
            raise ErroValidacao("o balanço já contém conta do grupo fundo_comercio e foi informado --fundo-comercio: risco de dupla contagem; retire um dos dois")
    if not args.fundo_comercio:
        alertas.append("sem --fundo-comercio: confirme se o intangível foi avaliado; o CPC, art. 606, manda avaliar bens tangíveis e intangíveis")

    pl_com_fundo = pl_determinacao + fundo
    quota_bruta = pl_com_fundo * participacao * integralizado
    quota = quota_bruta
    if quota_bruta < 0:
        quota = Decimal(0)
        alertas.append(f"quota patrimonial negativa ({moeda(quota_bruta)}): PL de determinação negativo; considerada R$ 0,00 nos haveres; a existência de débito do sócio depende do contrato e da decisão judicial [A VERIFICAR: jurisprudência sobre haveres negativos]")

    data_ajuizamento = parse_data(args.data_ajuizamento, "--data-ajuizamento") if args.data_ajuizamento else None
    lucros_lista = ler_json(args.lucros_declarados, "JSON de lucros declarados") if args.lucros_declarados else []
    if lucros_lista and not isinstance(lucros_lista, list):
        raise ErroValidacao("--lucros-declarados deve apontar para uma lista JSON")
    lucros, total_lucros, prescritos = ler_lucros(lucros_lista, participacao, data_resolucao, data_ajuizamento, args.incluir_prescritos, alertas)
    remuneracao, total_remuneracao = ler_lancamentos(numero_ou_arquivo(args.remuneracao_administrador, "remuneracao_administrador"), "remuneracao_administrador", data_resolucao, alertas, "Remuneração como administrador devida e não paga até a data da resolução (CPC, art. 608)")
    adiantamentos, total_adiantamentos = ler_lancamentos(numero_ou_arquivo(args.adiantamentos, "adiantamentos"), "adiantamentos", data_resolucao, alertas, "Adiantamento de haveres já recebido")
    indenizacao = parse_num(args.indenizacao_compensavel, "--indenizacao-compensavel") if args.indenizacao_compensavel else Decimal(0)
    if indenizacao < 0:
        raise ErroValidacao("--indenizacao-compensavel deve ser positiva")
    if indenizacao > 0 and not args.fundamento_indenizacao:
        raise ErroValidacao("--indenizacao-compensavel exige --fundamento-indenizacao (decisão que reconheceu o crédito da sociedade, CPC, art. 602)")

    haveres_brutos = quota + total_lucros + total_remuneracao
    total_deducoes = total_adiantamentos + indenizacao
    haveres_liquidos = haveres_brutos - total_deducoes
    if haveres_liquidos < 0:
        alertas.append(f"haveres líquidos negativos ({moeda(haveres_liquidos)}): as deduções superam o crédito; verificar se há saldo a restituir à sociedade")

    prazo_dias = int(args.prazo_pagamento_dias)
    if prazo_dias <= 0:
        raise ErroValidacao("--prazo-pagamento-dias deve ser positivo")
    fundamento_prazo = args.fundamento_prazo or ("CC, art. 1.031, § 2º: pagamento em dinheiro em 90 dias a partir da liquidação, salvo acordo ou cláusula contratual" if prazo_dias == PRAZO_LEGAL_DIAS else "prazo diverso do legal: informe --fundamento-prazo com a cláusula do contrato social ou a decisão")
    if prazo_dias != PRAZO_LEGAL_DIAS and not args.fundamento_prazo:
        raise ErroValidacao("prazo diverso de 90 dias exige --fundamento-prazo (cláusula contratual ou decisão), CPC, art. 609")
    pagamento = {"prazo_dias": prazo_dias, "fundamento": fundamento_prazo, "termo_inicial_correcao": fmt_data(data_resolucao), "fundamento_correcao": "CPC, art. 608, parágrafo único: após a data da resolução, correção monetária e juros contratuais ou legais"}
    if args.data_liquidacao:
        data_liq = parse_data(args.data_liquidacao, "--data-liquidacao")
        if data_liq < data_resolucao:
            raise ErroValidacao("--data-liquidacao anterior à data da resolução")
        vencimento = data_liq + timedelta(days=prazo_dias)
        pagamento.update({"data_liquidacao": fmt_data(data_liq), "vencimento": fmt_data(vencimento), "termo_inicial_juros": fmt_data(vencimento + timedelta(days=1)), "fundamento_juros": f"mora a partir do {prazo_dias + 1}º dia seguinte à liquidação (CC, art. 1.031, § 2º; CC, art. 397); taxa legal do CC, art. 406 (Lei 14.905/2024) salvo juros contratuais; calcular na skill atualizacao-monetaria, regime civil"})
    else:
        pagamento.update({"data_liquidacao": "a definir", "termo_inicial_juros": f"{prazo_dias + 1}º dia seguinte à data da liquidação (informar --data-liquidacao quando fixada)", "fundamento_juros": "CC, art. 1.031, § 2º, e CPC, art. 608, parágrafo único; taxa legal do CC, art. 406 (Lei 14.905/2024) salvo juros contratuais; calcular na skill atualizacao-monetaria, regime civil"})
        alertas.append("sem --data-liquidacao: o termo inicial dos juros fica descrito pela regra, não pela data")

    parcelas = [{"competencia": competencia(data_resolucao), "valor": q2(quota), "descricao": f"Haveres: quota patrimonial {pct(participacao)} sobre PL de determinação com fundo de comércio (CPC, arts. 606 e 608); correção desde a data da resolução"}]
    for l in lucros:
        if l["tratamento"].startswith("excluído"):
            continue
        parcelas.append({"competencia": l["competencia"], "valor": q2(parse_num(l["saldo"])), "descricao": f"{l['tipo'].upper() if l['tipo'] == 'jcp' else 'Lucros'} declarados em {l['data_deliberacao']}, saldo não pago: {l['descricao']}"})
    for r in remuneracao:
        parcelas.append({"competencia": r["competencia"], "valor": q2(parse_num(r["valor"])), "descricao": r["descricao"]})
    for a in adiantamentos:
        parcelas.append({"competencia": a["competencia"], "valor": -q2(parse_num(a["valor"])), "descricao": f"Dedução: {a['descricao']}" + (f" em {a['data']}" if a.get("data") else "")})
    if indenizacao > 0:
        parcelas.append({"competencia": competencia(data_resolucao), "valor": -q2(indenizacao), "descricao": f"Dedução: indenização compensável (CPC, art. 602): {args.fundamento_indenizacao}"})
    soma_parcelas = sum((p["valor"] for p in parcelas), Decimal(0))
    if q2(soma_parcelas) != q2(haveres_liquidos):
        raise ErroValidacao(f"sanidade falhou: soma das parcelas {moeda(soma_parcelas)} difere dos haveres líquidos {moeda(haveres_liquidos)}")
    if q2(haveres_brutos - total_deducoes) != q2(haveres_liquidos):
        raise ErroValidacao("sanidade falhou: brutos - deduções não fecha com líquidos")

    memoria = [
        f"Passo 1. Data da resolução {fmt_data(data_resolucao)} ({regra_605}). PL de determinação {moeda(pl_determinacao)} (balanco_determinacao.py; CPC, art. 606).",
        f"Passo 2. Fundo de comércio {moeda(fundo)} ({fundo_info}). PL de determinação com fundo de comércio = {moeda(pl_com_fundo)}.",
        f"Passo 3. Quota patrimonial = {moeda(pl_com_fundo)} x {pct(participacao)} x {pct(integralizado)} integralizado = {moeda(quota_bruta)} (CC, art. 1.031, caput: quota pelo montante efetivamente realizado)." + (" Considerada R$ 0,00 por ser negativa." if quota_bruta < 0 else ""),
        f"Passo 4. Lucros e JCP declarados e não pagos até a data da resolução (CPC, art. 608, caput): {moeda(total_lucros)} integrados; {moeda(prescritos)} excluídos por prescrição trienal (CC, art. 206, § 3º; REsp 1.904.252)." + (f" Limite: deliberações anteriores a {fmt_data(somar_anos(data_ajuizamento, -3))} (ajuizamento em {fmt_data(data_ajuizamento)}, CPC, art. 240, § 1º)." if data_ajuizamento else ""),
        f"Passo 5. Remuneração como administrador devida até a data da resolução: {moeda(total_remuneracao)} (CPC, art. 608, caput).",
        f"Passo 6. Haveres brutos = {moeda(quota)} + {moeda(total_lucros)} + {moeda(total_remuneracao)} = {moeda(haveres_brutos)}.",
        f"Passo 7. Deduções: adiantamentos {moeda(total_adiantamentos)}; indenização compensável {moeda(indenizacao)} (CPC, art. 602); total {moeda(total_deducoes)}.",
        f"Passo 8. Haveres líquidos = {moeda(haveres_brutos)} - {moeda(total_deducoes)} = {moeda(haveres_liquidos)}.",
        f"Passo 9. Pagamento: {pagamento['prazo_dias']} dias ({pagamento['fundamento']}). Correção monetária desde {pagamento['termo_inicial_correcao']}; juros a partir do {pagamento['termo_inicial_juros']}. Atualização na skill atualizacao-monetaria (regime civil) com parcelas.json.",
        f"Passo 10. Sanidade: soma das {len(parcelas)} parcelas = {moeda(soma_parcelas)} = haveres líquidos.",
    ]
    return {
        "script": "haveres_socio.py",
        "versao": VERSAO,
        "premissas": {
            "empresa": premissas_bal.get("empresa", ""), "processo": premissas_bal.get("processo", ""), "socio": args.socio or "",
            "hipotese": hipotese or "não informada", "regra_data_resolucao": regra_605, "data_resolucao": fmt_data(data_resolucao),
            "participacao": pct(participacao), "integralizado": pct(integralizado),
            "criterio": "CPC, arts. 604 a 609; CC, art. 1.031: quota liquidada com base na situação patrimonial na data da resolução, verificada em balanço de determinação",
            "fundo_comercio": fundo_info, "data_ajuizamento": fmt_data(data_ajuizamento) if data_ajuizamento else "não informada",
            "prescricao": "CC, art. 206, § 3º: 3 anos da deliberação da distribuição (REsp 1.904.252, 4ª Turma); interrupção retroage à propositura (CPC, art. 240, § 1º)",
            "pagamento": pagamento,
        },
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "componentes": {
            "pl_determinacao": tecnico(pl_determinacao), "fundo_comercio": tecnico(fundo), "pl_com_fundo_comercio": tecnico(pl_com_fundo),
            "quota_patrimonial_bruta": tecnico(quota_bruta), "quota_patrimonial": tecnico(quota),
            "lucros_declarados": lucros, "total_lucros_integrados": tecnico(total_lucros), "lucros_prescritos_excluidos": tecnico(prescritos),
            "remuneracao_administrador": remuneracao, "total_remuneracao_administrador": tecnico(total_remuneracao),
        },
        "haveres_brutos": tecnico(haveres_brutos),
        "deducoes": {"adiantamentos": adiantamentos, "total_adiantamentos": tecnico(total_adiantamentos), "indenizacao_compensavel": tecnico(indenizacao), "fundamento_indenizacao": args.fundamento_indenizacao or "", "total": tecnico(total_deducoes)},
        "haveres_liquidos": tecnico(haveres_liquidos),
        "sanidade": {"brutos_menos_deducoes": tecnico(haveres_brutos - total_deducoes), "soma_parcelas": tecnico(soma_parcelas), "fecha": True},
        "parcelas": [{"competencia": p["competencia"], "valor": float(p["valor"]), "descricao": p["descricao"]} for p in parcelas],
        "alertas": alertas,
        "memoria": memoria,
    }


def gravar_md(saida, caminho):
    p, c, d = saida["premissas"], saida["componentes"], saida["deducoes"]
    linhas = [
        f"# Apuração de haveres: {p['empresa']}",
        "",
        f"Sócio: {p['socio'] or '[NOME]'}. Participação: {p['participacao']} (integralizado {p['integralizado']}). Data da resolução: {p['data_resolucao']} ({p['regra_data_resolucao']}).",
        "",
        "| Rubrica | Valor (R$) |", "|---|---:|",
        f"| PL de determinação (CPC, art. 606) | {fmt_br(c['pl_determinacao'])} |",
        f"| Fundo de comércio na data da resolução | {fmt_br(c['fundo_comercio'])} |",
        f"| PL de determinação com fundo de comércio | {fmt_br(c['pl_com_fundo_comercio'])} |",
        f"| Quota patrimonial ({p['participacao']}) | {fmt_br(c['quota_patrimonial'])} |",
        f"| Lucros e JCP declarados e não pagos (CPC, art. 608) | {fmt_br(c['total_lucros_integrados'])} |",
        f"| Remuneração como administrador (CPC, art. 608) | {fmt_br(c['total_remuneracao_administrador'])} |",
        f"| Haveres brutos | {fmt_br(saida['haveres_brutos'])} |",
        f"| Adiantamentos recebidos | ({fmt_br(d['total_adiantamentos'])}) |",
        f"| Indenização compensável (CPC, art. 602) | ({fmt_br(d['indenizacao_compensavel'])}) |",
        f"| Haveres líquidos | {fmt_br(saida['haveres_liquidos'])} |",
        "", "## Lucros e JCP declarados", "",
        "| Descrição | Deliberação | Valor | Pago | Saldo | Situação | Tratamento |", "|---|---|---:|---:|---:|---|---|",
    ]
    for l in c["lucros_declarados"]:
        linhas.append(f"| {l['descricao']} | {l['data_deliberacao']} | {fmt_br(l['valor'])} | {fmt_br(l['pago'])} | {fmt_br(l['saldo'])} | {l['situacao']} | {l['tratamento']} |")
    linhas += ["", "## Pagamento, correção e juros", ""]
    for k, v in p["pagamento"].items():
        linhas.append(f"- {k.replace('_', ' ')}: {v}")
    linhas += ["", "## Parcelas para atualizacao-monetaria (regime civil)", "", "| Competência | Valor (R$) | Descrição |", "|---|---:|---|"]
    for pr in saida["parcelas"]:
        linhas.append(f"| {pr['competencia']} | {fmt_br(Decimal(str(pr['valor'])))} | {pr['descricao']} |")
    linhas += ["", "## Memória de cálculo", ""] + [f"- {m}" for m in saida["memoria"]]
    if saida["alertas"]:
        linhas += ["", "## Alertas", ""] + [f"- {a}" for a in saida["alertas"]]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Haveres do sócio a partir do balanço de determinação, com lucros declarados, deduções, prazo e termos de correção e juros; gera parcelas.json para atualizacao-monetaria.")
    parser.add_argument("--balanco", required=True, help="JSON gerado por balanco_determinacao.py")
    parser.add_argument("--fundo-comercio", help="JSON gerado por fundo_comercio.py (opcional)")
    parser.add_argument("--participacao", required=True, help="participação do sócio em pontos percentuais (ex.: 25 ou 25%%)")
    parser.add_argument("--integralizado", default="100%", help="parcela da quota efetivamente integralizada, em %% (CC, art. 1.031, caput); padrão 100%%")
    parser.add_argument("--data-resolucao", required=True, help="data da resolução dd/mm/aaaa (deve coincidir com a do balanço)")
    parser.add_argument("--hipotese", choices=sorted(HIPOTESES), help="hipótese do art. 605 do CPC; padrão: a registrada no balanço")
    parser.add_argument("--socio", help="nome do sócio retirante, excluído ou falecido (opcional)")
    parser.add_argument("--lucros-declarados", help="JSON com lucros ou JCP declarados e não pagos até a data da resolução (ver assets/exemplo_lucros_declarados.json)")
    parser.add_argument("--data-ajuizamento", help="data do ajuizamento dd/mm/aaaa, para conferir a prescrição trienal dos lucros")
    parser.add_argument("--incluir-prescritos", action="store_true", help="integra lucros aparentemente prescritos, com alerta (quando a decisão assim determinar)")
    parser.add_argument("--remuneracao-administrador", help="valor único ou JSON com competências da remuneração devida e não paga até a resolução")
    parser.add_argument("--adiantamentos", help="valor único ou JSON com adiantamentos já recebidos (ex.: levantamento do depósito da parte incontroversa, CPC, art. 604, § 2º)")
    parser.add_argument("--indenizacao-compensavel", help="valor reconhecido em favor da sociedade a compensar (CPC, art. 602)")
    parser.add_argument("--fundamento-indenizacao", help="decisão ou fundamento da indenização compensável")
    parser.add_argument("--prazo-pagamento-dias", default=str(PRAZO_LEGAL_DIAS), help="prazo de pagamento em dias; padrão 90 (CC, art. 1.031, § 2º)")
    parser.add_argument("--fundamento-prazo", help="cláusula contratual ou decisão que fixa prazo diverso de 90 dias")
    parser.add_argument("--data-liquidacao", help="data da liquidação dd/mm/aaaa, para datar o vencimento e o termo dos juros")
    parser.add_argument("--saida", help="arquivo JSON de saída; padrão: stdout")
    parser.add_argument("--md", help="grava o quadro de haveres em Markdown neste caminho")
    parser.add_argument("--parcelas", default="parcelas.json", help="arquivo parcelas.json no formato da atualizacao-monetaria; padrão: parcelas.json no diretório atual")
    args = parser.parse_args()
    try:
        saida = apurar(args)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"Haveres gravados em {args.saida}", file=sys.stderr)
        else:
            print(texto)
        Path(args.parcelas).write_text(json.dumps(saida["parcelas"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Parcelas para atualizacao-monetaria gravadas em {args.parcelas}", file=sys.stderr)
        if args.md:
            gravar_md(saida, args.md)
            print(f"Quadro Markdown gravado em {args.md}", file=sys.stderr)
        print(f"Haveres brutos {moeda(saida['haveres_brutos'])} | deduções {moeda(saida['deducoes']['total'])} | haveres líquidos {moeda(saida['haveres_liquidos'])}", file=sys.stderr)
        for a in saida["alertas"]:
            print(f"ALERTA: {a}", file=sys.stderr)
    except ErroValidacao as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
