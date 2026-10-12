#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
encargos_auto_infracao.py: apura os encargos do lançamento de ofício de IRPF
sobre o principal recalculado (ou informado): multa de ofício (percentual e
fundamento declarados), juros pela Selic acumulada (Lei 9.430/1996, art. 61,
§ 3º: soma simples das taxas mensais a partir do mês seguinte ao vencimento
até o mês anterior ao do pagamento, mais 1% no mês do pagamento), cenário
informativo de multa de mora (art. 61, caput e §§ 1º e 2º), confronto item a
item com o auto de infração ou a CDA e teste de decadência por ano
(CTN, art. 150, § 4º, x art. 173, I).

A série Selic nunca é embutida: entra por CSV com fonte e o script aborta se
faltar qualquer mês do período.

Parte da skill: pericia-irpf-rendimentos-nao-declarados

Uso:
    python3 scripts/encargos_auto_infracao.py --recalculo recalculo.json --cenario base \
        --modo anual --ano 2023 --vencimento 30/04/2024 --data-referencia 12/09/2026 \
        --multa 75 --selic assets/exemplo_selic.csv --lancado assets/exemplo_lancado.json \
        --ciencia 15/03/2026 --pagamento-antecipado S --saida encargos.json --md encargos.md
    python3 scripts/encargos_auto_infracao.py --principal 95.550,00 --vencimento 30/04/2024 \
        --pagamento 12/09/2026 --selic assets/exemplo_selic.csv --cenario-mora

Colunas do CSV da Selic (separador ';', cabeçalho obrigatório):
    competencia;taxa_mensal;fonte   (competência mm/aaaa; taxa em % ao mês)
"""

import argparse
import csv
import json
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, getcontext
from pathlib import Path

getcontext().prec = 28
CENT = Decimal("0.01")
CEM = Decimal("100")
DATA_REFERENCIA = "12/09/2026"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
FUNDAMENTO_75 = ("Lei 9.430/1996, art. 44, I (multa de ofício de 75%); redação vigente dos percentuais "
                 "[A VERIFICAR: alterações da Lei 14.689/2023]")


class ErroValidacao(Exception):
    """Erro de dado de entrada: sai com código 1 e mensagem objetiva."""


def parse_num(texto, contexto=""):
    """Aceita 1.234,56 (padrão brasileiro) e 1234.56 (técnico); devolve Decimal."""
    if texto is None:
        raise ErroValidacao(f"valor ausente {contexto}")
    if isinstance(texto, (int, Decimal)):
        return Decimal(texto)
    t = str(texto).strip().replace("R$", "").replace("%", "").replace(" ", "")
    if t == "":
        raise ErroValidacao(f"valor ausente {contexto}")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return Decimal(t)
    except InvalidOperation:
        raise ErroValidacao(f"valor inválido {texto!r} {contexto}")


def parse_data(texto, contexto=""):
    t = (texto or "").strip()
    try:
        return datetime.strptime(t, "%d/%m/%Y").date()
    except ValueError:
        raise ErroValidacao(f"data inválida {texto!r} {contexto} (formato dd/mm/aaaa)")


def fmt_data(d):
    return d.strftime("%d/%m/%Y")


def q2(valor):
    return valor.quantize(CENT, rounding=ROUND_HALF_UP)


def fmt_brl(valor):
    v = q2(valor)
    inteiro, _, frac = f"{v:.2f}".partition(".")
    negativo = inteiro.startswith("-")
    inteiro = inteiro.lstrip("-")
    grupos = []
    while inteiro:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    return ("-" if negativo else "") + "R$ " + ".".join(grupos) + "," + frac


def fmt_pct(valor):
    return f"{q2(valor):.2f}".replace(".", ",") + "%"


def serializar(obj):
    if isinstance(obj, Decimal):
        return str(q2(obj))
    if isinstance(obj, date):
        return fmt_data(obj)
    if isinstance(obj, dict):
        return {k: serializar(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serializar(v) for v in obj]
    return obj


def ler_selic(caminho):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"série Selic não encontrada: {caminho}")
    serie = {}
    fontes = set()
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        cab = [c.strip() for c in (leitor.fieldnames or [])]
        faltam = [c for c in ("competencia", "taxa_mensal", "fonte") if c not in cab]
        if faltam:
            raise ErroValidacao(f"CSV da Selic sem as colunas obrigatórias: {', '.join(faltam)}")
        for n, linha in enumerate(leitor, start=2):
            linha = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
            if not any(linha.values()):
                continue
            ctx = f"(Selic, linha {n})"
            comp = linha["competencia"]
            try:
                datetime.strptime(comp, "%m/%Y")
            except ValueError:
                raise ErroValidacao(f"competência inválida {comp!r} {ctx} (formato mm/aaaa)")
            if not linha["fonte"]:
                raise ErroValidacao(f"linha da Selic sem fonte {ctx}: a série exige fonte declarada")
            taxa = parse_num(linha["taxa_mensal"], ctx)
            if taxa < 0 or taxa > 10:
                raise ErroValidacao(f"taxa Selic mensal fora da ordem de grandeza esperada ({taxa}%) {ctx}")
            if comp in serie:
                raise ErroValidacao(f"competência duplicada {comp} {ctx}")
            serie[comp] = taxa
            fontes.add(linha["fonte"])
    if not serie:
        raise ErroValidacao("série Selic vazia")
    return serie, sorted(fontes)


def meses_entre(inicio_exclusivo, fim_exclusivo):
    """Competências mm/aaaa estritamente entre o mês de início e o mês de fim."""
    ano, mes = inicio_exclusivo.year, inicio_exclusivo.month
    meses = []
    while True:
        mes += 1
        if mes > 12:
            mes, ano = 1, ano + 1
        if (ano, mes) >= (fim_exclusivo.year, fim_exclusivo.month):
            break
        meses.append(f"{mes:02d}/{ano}")
    return meses


def juros_selic(vencimento, data_fim, serie):
    """Soma simples das Selic mensais do mês seguinte ao vencimento até o mês anterior ao de data_fim,
    mais 1% no mês de data_fim (Lei 9.430/1996, art. 61, § 3º). Devolve (percentual, detalhe)."""
    if data_fim < vencimento:
        raise ErroValidacao(f"data de pagamento ou referência ({fmt_data(data_fim)}) anterior ao vencimento ({fmt_data(vencimento)})")
    if (data_fim.year, data_fim.month) == (vencimento.year, vencimento.month):
        return Decimal(0), {"meses": [], "mes_pagamento": None, "observacao": "pagamento no próprio mês do vencimento: sem juros"}
    meses = meses_entre(vencimento, data_fim)
    faltantes = [m for m in meses if m not in serie]
    if faltantes:
        raise ErroValidacao(f"série Selic sem as competências: {', '.join(faltantes)}; obter em bcb.gov.br/SGS e completar o CSV")
    soma = sum((serie[m] for m in meses), Decimal(0))
    detalhe = {"meses": [{"competencia": m, "taxa": serie[m]} for m in meses],
               "soma_selic_meses_cheios": soma,
               "mes_pagamento": f"{data_fim.month:02d}/{data_fim.year}", "juros_mes_pagamento": Decimal(1)}
    return soma + Decimal(1), detalhe


def carregar_principal(args, memoria):
    if args.principal is not None and args.recalculo:
        raise ErroValidacao("informe --principal ou --recalculo, não ambos")
    if args.principal is not None:
        principal = parse_num(args.principal, "(--principal)")
        memoria.append(f"Principal informado diretamente: {fmt_brl(principal)}")
        return principal, "informado"
    if not args.recalculo:
        raise ErroValidacao("informe o principal (--principal) ou o JSON de recalculo_irpf.py (--recalculo)")
    p = Path(args.recalculo)
    if not p.is_file():
        raise ErroValidacao(f"recálculo não encontrado: {args.recalculo}")
    with p.open("r", encoding="utf-8") as f:
        rec = json.load(f)
    if rec.get("script") != "recalculo_irpf.py" or "resultados" not in rec:
        raise ErroValidacao("o JSON informado não foi gerado por recalculo_irpf.py")
    cen = rec["resultados"].get(args.cenario)
    if not cen:
        raise ErroValidacao(f"cenário {args.cenario!r} ausente do recálculo (disponíveis: {list(rec['resultados'])})")
    anos = list(cen)
    ano = str(args.ano) if args.ano else (anos[0] if len(anos) == 1 else None)
    if ano is None or ano not in cen:
        raise ErroValidacao(f"informe --ano entre os disponíveis no recálculo: {anos}")
    modos = cen[ano]["modos"]
    if args.modo not in modos:
        raise ErroValidacao(f"modo {args.modo!r} ausente do recálculo para {ano} (disponíveis: {list(modos)})")
    principal = parse_num(modos[args.modo]["imposto_suplementar"], "(recálculo)")
    memoria.append(f"Principal lido de {args.recalculo}: cenário {args.cenario}, ano {ano}, modo {args.modo}: {fmt_brl(principal)}")
    if principal <= 0:
        raise ErroValidacao(f"imposto suplementar não positivo ({fmt_brl(principal)}): não há encargos a apurar neste cenário")
    return principal, f"recalculo_irpf.py ({args.cenario}/{ano}/{args.modo})"


def calcular_encargos(principal, multa_pct, vencimento, data_fim, serie, juros_sobre_multa, memoria, rotulo="recálculo"):
    pct_juros, detalhe = juros_selic(vencimento, data_fim, serie)
    multa = principal * multa_pct / CEM
    base_juros = principal + (multa if juros_sobre_multa else Decimal(0))
    juros = base_juros * pct_juros / CEM
    total = principal + multa + juros
    if abs(q2(total) - (q2(principal) + q2(multa) + q2(juros))) > CENT:
        raise ErroValidacao("sanidade falhou: total não fecha com principal + multa + juros")
    memoria.append(f"[{rotulo}] multa de ofício {fmt_pct(multa_pct)} x {fmt_brl(principal)} = {fmt_brl(multa)}")
    memoria.append(f"[{rotulo}] Selic acumulada de {fmt_data(vencimento)} a {fmt_data(data_fim)}: "
                   f"{len(detalhe.get('meses', []))} meses cheios somam {fmt_pct(detalhe.get('soma_selic_meses_cheios', Decimal(0)))} "
                   f"+ 1,00% no mês do pagamento = {fmt_pct(pct_juros)}; base dos juros {fmt_brl(base_juros)}"
                   f"{' (principal + multa)' if juros_sobre_multa else ' (só o principal)'}; juros {fmt_brl(juros)}")
    memoria.append(f"[{rotulo}] total = {fmt_brl(principal)} + {fmt_brl(multa)} + {fmt_brl(juros)} = {fmt_brl(total)}")
    return {"principal": principal, "multa_pct": multa_pct, "multa": multa, "selic_acumulada_pct": pct_juros,
            "selic_detalhe": detalhe, "base_juros": base_juros, "juros": juros, "total": total,
            "vencimento": vencimento, "data_fim": data_fim}


def cenario_mora(principal, vencimento, data_fim, serie, pct_dia, teto, memoria):
    dias = (data_fim - vencimento).days
    pct = min(pct_dia * Decimal(dias), teto)
    multa = principal * pct / CEM
    pct_juros, _ = juros_selic(vencimento, data_fim, serie)
    juros = principal * pct_juros / CEM
    total = principal + multa + juros
    memoria.append(f"[cenário mora] {dias} dias de atraso x {fmt_pct(pct_dia)} ao dia = {fmt_pct(pct_dia * dias)}, "
                   f"limitada a {fmt_pct(teto)}: multa de mora {fmt_brl(multa)}; juros {fmt_brl(juros)}; total {fmt_brl(total)}")
    return {"dias_atraso": dias, "multa_mora_pct": pct, "multa_mora": multa, "juros": juros, "total": total,
            "fundamento": "Lei 9.430/1996, art. 61, caput e §§ 1º a 3º (multa de mora de 0,33% ao dia, limitada a 20%; juros Selic)",
            "uso": "cenário informativo: pagamento espontâneo antes do lançamento ou hipótese de afastamento da multa de ofício"}


def confrontar(lancado_path, rec, serie, args, memoria):
    p = Path(lancado_path)
    if not p.is_file():
        raise ErroValidacao(f"arquivo do lançado não encontrado: {lancado_path}")
    with p.open("r", encoding="utf-8") as f:
        lanc = json.load(f)
    if not str(lanc.get("fonte", "")).strip():
        raise ErroValidacao("JSON do lançado sem 'fonte' (folhas do auto ou da CDA)")
    itens = {}
    for campo in ("principal", "multa", "juros", "total"):
        if lanc.get(campo) is None:
            continue
        v_l = parse_num(lanc[campo], f"(lançado, {campo})")
        v_r = rec[campo]
        itens[campo] = {"lancado": v_l, "recalculado": v_r, "diferenca_lancado_menos_recalculado": v_l - v_r}
        memoria.append(f"[confronto] {campo}: lançado {fmt_brl(v_l)} - recalculado {fmt_brl(v_r)} = {fmt_brl(v_l - v_r)}")
    saida = {"fonte": lanc["fonte"], "itens": itens}
    if lanc.get("multa_pct") is not None:
        mp = parse_num(lanc["multa_pct"], "(lançado, multa_pct)")
        saida["multa_pct_lancada"] = mp
        if mp != rec["multa_pct"]:
            memoria.append(f"[confronto] percentual de multa do auto ({fmt_pct(mp)}) difere do adotado ({fmt_pct(rec['multa_pct'])})")
    # Reprodutibilidade dos juros do auto na data em que ele os calculou.
    if lanc.get("data_juros") and lanc.get("principal") is not None and lanc.get("juros") is not None:
        dj = parse_data(lanc["data_juros"], "(lançado, data_juros)")
        pct_auto, _ = juros_selic(rec["vencimento"], dj, serie)
        p_l = parse_num(lanc["principal"])
        j_l = parse_num(lanc["juros"])
        base = p_l + (parse_num(lanc["multa"]) if args.juros_sobre_multa and lanc.get("multa") is not None else Decimal(0))
        j_rep = base * pct_auto / CEM
        implicita = (j_l / base * CEM) if base else Decimal(0)
        saida["juros_do_auto"] = {"data_juros": dj, "selic_acumulada_pela_serie": pct_auto, "selic_implicita_no_auto": implicita,
                                  "juros_reproduzidos": j_rep, "juros_lancados": j_l, "diferenca": j_l - j_rep,
                                  "reproduzivel": abs(q2(j_l) - q2(j_rep)) <= Decimal("1.00")}
        memoria.append(f"[confronto] juros do auto em {fmt_data(dj)}: série informada acumula {fmt_pct(pct_auto)} sobre "
                       f"{fmt_brl(base)} = {fmt_brl(j_rep)}; lançado {fmt_brl(j_l)} (Selic implícita {fmt_pct(implicita)}); "
                       f"{'reproduzível' if saida['juros_do_auto']['reproduzivel'] else 'não reproduzível pela série informada'}")
        # Recálculo completo na data do auto, para comparação homogênea.
        rec_auto = calcular_encargos(rec["principal"], rec["multa_pct"], rec["vencimento"], dj, serie,
                                     args.juros_sobre_multa, memoria, rotulo="recálculo na data do auto")
        saida["recalculo_na_data_do_auto"] = {k: v for k, v in rec_auto.items() if k != "selic_detalhe"}
        if lanc.get("total") is not None:
            t_l = parse_num(lanc["total"])
            saida["recalculo_na_data_do_auto"]["diferenca_total_lancado_menos_recalculado"] = t_l - rec_auto["total"]
            memoria.append(f"[confronto] na data do auto: total lançado {fmt_brl(t_l)} - recalculado {fmt_brl(rec_auto['total'])} "
                           f"= {fmt_brl(t_l - rec_auto['total'])}")
    return saida


def soma_anos(d, anos):
    try:
        return d.replace(year=d.year + anos)
    except ValueError:
        return d.replace(year=d.year + anos, day=28)


def decadencia(args, memoria):
    if not args.ciencia:
        return None
    ciencia = parse_data(args.ciencia, "(--ciencia)")
    if args.fato_gerador:
        fg = parse_data(args.fato_gerador, "(--fato-gerador)")
        origem_fg = "informado"
    elif args.ano:
        fg = date(args.ano, 12, 31)
        origem_fg = "31/12 do ano-calendário (apuração anual)"
    else:
        raise ErroValidacao("para o teste de decadência informe --fato-gerador ou --ano")
    fim_150 = soma_anos(fg, 5)
    inicio_173 = date(fg.year + 2, 1, 1)
    fim_173 = date(fg.year + 6, 12, 31)
    pag = (args.pagamento_antecipado or "").strip().upper()
    if pag not in ("", "S", "N"):
        raise ErroValidacao("--pagamento-antecipado aceita S ou N")
    r = {"fato_gerador": fg, "origem_fato_gerador": origem_fg, "ciencia_do_lancamento": ciencia,
         "art_150_par_4": {"regra": "cinco anos contados do fato gerador (homologação tácita)", "termo_final": fim_150,
                           "lancamento_dentro_do_prazo": ciencia <= fim_150},
         "art_173_I": {"regra": "cinco anos contados do primeiro dia do exercício seguinte àquele em que o lançamento "
                                "poderia ter sido efetuado", "termo_inicial": inicio_173, "termo_final": fim_173,
                       "lancamento_dentro_do_prazo": ciencia <= fim_173},
         "pagamento_antecipado_informado": pag or "não informado",
         "orientacao": ("havendo pagamento antecipado (imposto pago ou retido) e sem dolo, fraude ou simulação, aplica-se o "
                        "art. 150, § 4º; sem pagamento antecipado, o art. 173, I. Orientação atribuída à Súmula 555/STJ "
                        "[A VERIFICAR]. Sob o § 4º do art. 42 o fato gerador mensal é tese alternativa [A VERIFICAR: "
                        "Súmula CARF 38, fato gerador em 31/12]. A regra aplicável é matéria do juízo")}
    memoria.append(f"[decadência] fato gerador {fmt_data(fg)} ({origem_fg}); ciência em {fmt_data(ciencia)}; "
                   f"art. 150, § 4º: termo final {fmt_data(fim_150)} ({'dentro' if ciencia <= fim_150 else 'fora'} do prazo); "
                   f"art. 173, I: {fmt_data(inicio_173)} a {fmt_data(fim_173)} ({'dentro' if ciencia <= fim_173 else 'fora'} do prazo)")
    return r


def brl(texto):
    """Formata o valor já serializado (texto com ponto decimal) no padrão brasileiro."""
    return fmt_brl(Decimal(str(texto)))


def pct(texto):
    return fmt_pct(Decimal(str(texto)))


def gravar_md(caminho, s):
    r = s["encargos"]
    linhas = ["# Encargos do lançamento de ofício e confronto com o auto", "",
              f"Principal: {brl(r['principal'])} ({s['premissas']['origem_principal']}). Vencimento {r['vencimento']}; "
              f"juros até {r['data_fim']} ({s['premissas']['natureza_data_fim']}).", "",
              "| Item | Valor |", "|---|---|",
              f"| Principal | {brl(r['principal'])} |",
              f"| Multa de ofício ({pct(r['multa_pct'])}) | {brl(r['multa'])} |",
              f"| Selic acumulada | {pct(r['selic_acumulada_pct'])} |",
              f"| Juros | {brl(r['juros'])} |",
              f"| Total | {brl(r['total'])} |", ""]
    if s.get("cenario_mora"):
        m = s["cenario_mora"]
        linhas += ["## Cenário informativo: multa de mora", "", "| Item | Valor |", "|---|---|",
                   f"| Dias de atraso | {m['dias_atraso']} |", f"| Multa de mora ({pct(m['multa_mora_pct'])}) | {brl(m['multa_mora'])} |",
                   f"| Juros | {brl(m['juros'])} |", f"| Total | {brl(m['total'])} |", ""]
    if s.get("confronto"):
        linhas += ["## Confronto com o lançado", "", "| Item | Lançado | Recalculado | Diferença |", "|---|---|---|---|"]
        for k, v in s["confronto"]["itens"].items():
            linhas.append(f"| {k} | {brl(v['lancado'])} | {brl(v['recalculado'])} | {brl(v['diferenca_lancado_menos_recalculado'])} |")
        ja = s["confronto"].get("juros_do_auto")
        if ja:
            linhas += ["", f"Juros do auto em {ja['data_juros']}: Selic acumulada pela série {pct(ja['selic_acumulada_pela_serie'])}, "
                           f"implícita no auto {pct(ja['selic_implicita_no_auto'])}; "
                           f"{'reproduzível' if ja['reproduzivel'] else 'não reproduzível pela série informada'}."]
        linhas.append("")
    if s.get("decadencia"):
        d = s["decadencia"]
        linhas += ["## Decadência", "", "| Regra | Termo final | Ciência | Situação |", "|---|---|---|---|",
                   f"| CTN, art. 150, § 4º | {d['art_150_par_4']['termo_final']} | {d['ciencia_do_lancamento']} | "
                   f"{'dentro do prazo' if d['art_150_par_4']['lancamento_dentro_do_prazo'] else 'fora do prazo'} |",
                   f"| CTN, art. 173, I | {d['art_173_I']['termo_final']} | {d['ciencia_do_lancamento']} | "
                   f"{'dentro do prazo' if d['art_173_I']['lancamento_dentro_do_prazo'] else 'fora do prazo'} |", "",
                   d["orientacao"], ""]
    linhas += ["## Memória de cálculo", ""] + [f"{i + 1}. {m}" for i, m in enumerate(s["memoria"])]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def executar(args):
    memoria = []
    principal, origem = carregar_principal(args, memoria)
    vencimento = parse_data(args.vencimento, "(--vencimento)")
    if args.pagamento and args.data_referencia:
        raise ErroValidacao("informe --pagamento ou --data-referencia, não ambos")
    if not (args.pagamento or args.data_referencia):
        raise ErroValidacao("informe a data do pagamento (--pagamento) ou a data de referência do cálculo (--data-referencia)")
    data_fim = parse_data(args.pagamento or args.data_referencia, "(--pagamento/--data-referencia)")
    natureza = "data do pagamento" if args.pagamento else "data de referência (sem pagamento)"
    multa_pct = parse_num(args.multa, "(--multa)")
    if multa_pct < 0:
        raise ErroValidacao("percentual de multa negativo")
    if multa_pct != Decimal(75) and not args.fundamento:
        raise ErroValidacao("multa diversa de 75% exige --fundamento (dispositivo e motivo da qualificação ou agravamento)")
    fundamento = args.fundamento or FUNDAMENTO_75
    serie, fontes = ler_selic(args.selic)
    memoria.append(f"Série Selic lida de {args.selic}: {len(serie)} competências; fontes: {'; '.join(fontes)}")
    rec = calcular_encargos(principal, multa_pct, vencimento, data_fim, serie, args.juros_sobre_multa, memoria)
    saida = {
        "skill": "pericia-irpf-rendimentos-nao-declarados",
        "script": "encargos_auto_infracao.py",
        "data_referencia": DATA_REFERENCIA,
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "premissas": {
            "origem_principal": origem, "vencimento": vencimento, "data_fim": data_fim, "natureza_data_fim": natureza,
            "multa_pct": multa_pct, "fundamento_multa": fundamento,
            "juros_sobre_multa": bool(args.juros_sobre_multa),
            "nota_juros_sobre_multa": ("juros aplicados também sobre a multa de ofício [A VERIFICAR: súmula do CARF sobre "
                                       "incidência da Selic na multa de ofício]" if args.juros_sobre_multa
                                       else "juros só sobre o principal; a incidência sobre a multa é controvertida "
                                            "[A VERIFICAR: súmula do CARF sobre incidência da Selic na multa de ofício]"),
            "regra_juros": "Lei 9.430/1996, art. 61, § 3º: Selic acumulada do mês seguinte ao vencimento ao mês anterior "
                           "ao pagamento, mais 1% no mês do pagamento; soma simples, sem capitalização",
            "serie_selic": args.selic, "fontes_selic": fontes,
        },
        "encargos": rec,
        "cenario_mora": None,
        "confronto": None,
        "decadencia": None,
        "memoria": memoria,
    }
    if args.cenario_mora:
        saida["cenario_mora"] = cenario_mora(principal, vencimento, data_fim, serie,
                                             parse_num(args.multa_mora_dia), parse_num(args.multa_mora_teto), memoria)
    if args.lancado:
        saida["confronto"] = confrontar(args.lancado, rec, serie, args, memoria)
    saida["decadencia"] = decadencia(args, memoria)
    return serializar(saida)


def main():
    p = argparse.ArgumentParser(
        description="Multa de ofício, juros Selic, confronto com o auto de infração e decadência em lançamento de IRPF.")
    p.add_argument("--principal", help="imposto suplementar (principal) em R$; alternativa a --recalculo")
    p.add_argument("--recalculo", help="JSON gerado por recalculo_irpf.py, de onde se lê o principal")
    p.add_argument("--cenario", choices=["base", "ampliado"], default="base", help="cenário a ler do recálculo (padrão base)")
    p.add_argument("--modo", choices=["anual", "mensal"], default="anual", help="modo a ler do recálculo (padrão anual)")
    p.add_argument("--ano", type=int, help="ano-calendário (obrigatório se o recálculo tiver mais de um; usado na decadência)")
    p.add_argument("--vencimento", required=True, help="vencimento do imposto (dd/mm/aaaa), conforme o prazo do exercício")
    p.add_argument("--pagamento", help="data do pagamento (dd/mm/aaaa)")
    p.add_argument("--data-referencia", help="data de referência do cálculo quando não houve pagamento (dd/mm/aaaa)")
    p.add_argument("--multa", default="75", help="percentual da multa de ofício (padrão 75); outro valor exige --fundamento")
    p.add_argument("--fundamento", help="dispositivo e motivo do percentual da multa (obrigatório se diverso de 75)")
    p.add_argument("--juros-sobre-multa", action="store_true", help="aplica a Selic também sobre a multa de ofício (controvertido)")
    p.add_argument("--selic", required=True, help="CSV da Selic mensal (competencia;taxa_mensal;fonte)")
    p.add_argument("--lancado", help="JSON com principal, multa, juros, total, multa_pct, data_juros e fonte do auto ou da CDA")
    p.add_argument("--cenario-mora", action="store_true", help="acrescenta o cenário informativo de multa de mora (art. 61)")
    p.add_argument("--multa-mora-dia", default="0,33", help="multa de mora em %% por dia (padrão 0,33; art. 61, § 1º)")
    p.add_argument("--multa-mora-teto", default="20", help="teto da multa de mora em %% (padrão 20; art. 61, § 2º)")
    p.add_argument("--ciencia", help="data da ciência do lançamento (dd/mm/aaaa) para o teste de decadência")
    p.add_argument("--fato-gerador", help="data do fato gerador (dd/mm/aaaa); padrão 31/12 de --ano")
    p.add_argument("--pagamento-antecipado", help="S ou N: houve imposto pago ou retido no ano (orienta a regra de decadência)")
    p.add_argument("--saida", help="arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="grava o quadro de encargos, confronto e decadência em Markdown")
    args = p.parse_args()
    try:
        saida = executar(args)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            e = saida["encargos"]
            print(f"Encargos gravados em {args.saida}: principal R$ {e['principal']}, multa R$ {e['multa']}, "
                  f"juros R$ {e['juros']} (Selic {e['selic_acumulada_pct']}%), total R$ {e['total']}")
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
