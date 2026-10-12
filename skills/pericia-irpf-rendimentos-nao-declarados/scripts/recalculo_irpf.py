#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recalculo_irpf.py: recalcula o imposto de renda da pessoa física a partir da
classificação crédito a crédito produzida por classificar_rendimentos.py, em
dois modos: anual (toda a base adicional entra no ajuste anual, com deduções
e tabela anual) e mensal (o rendimento presumido do art. 42 da Lei 9.430/1996
é tributado no mês do crédito pela tabela mensal, § 4º, sem deduções, e o
rendimento de fonte identificada ausente da DIRPF segue para o ajuste anual).
Compensa o imposto já apurado na DIRPF original e o IRRF compensável e apura a
diferença (imposto suplementar), por cenário (base e ampliado).

A tabela progressiva nunca é embutida: entra por arquivo CSV com a coluna
fonte preenchida, e o script aborta se faltar o ano ou o modo. Os limites de
dedução também entram por arquivo JSON, item a item, com fonte.

Parte da skill: pericia-irpf-rendimentos-nao-declarados

Uso:
    python3 scripts/recalculo_irpf.py --classificacao classificacao.json \
        --tabela assets/exemplo_tabela_progressiva.csv --ano 2023 \
        --deducoes assets/exemplo_deducoes.json --rendimentos-declarados 54.000,00 \
        --irrf 225,00 --modo ambos --cenario ambos --saida recalculo.json --md recalculo.md

Colunas do CSV da tabela (separador ';', cabeçalho obrigatório):
    ano;modo;faixa_inicio;faixa_fim;aliquota;deducao;fonte
    modo: anual ou mensal; faixa_fim vazia na última faixa; aliquota em %.
"""

import argparse
import csv
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, getcontext
from pathlib import Path

getcontext().prec = 28
CENT = Decimal("0.01")
CEM = Decimal("100")
DATA_REFERENCIA = "12/09/2026"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
MODOS = ("anual", "mensal")
CENARIOS = ("base", "ampliado")
TIPOS_DEDUCAO = ("dependentes", "previdencia_oficial", "saude", "educacao",
                 "pensao_alimenticia", "livro_caixa", "previdencia_privada", "outras")


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
    if isinstance(obj, dict):
        return {k: serializar(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serializar(v) for v in obj]
    return obj


def ler_tabela(caminho):
    """Lê a tabela progressiva e valida contiguidade, alíquotas e parcela a deduzir."""
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"tabela progressiva não encontrada: {caminho}")
    tabelas = {}
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        esperadas = ["ano", "modo", "faixa_inicio", "faixa_fim", "aliquota", "deducao", "fonte"]
        cab = [c.strip() for c in (leitor.fieldnames or [])]
        faltam = [c for c in esperadas if c not in cab]
        if faltam:
            raise ErroValidacao(f"tabela sem as colunas obrigatórias: {', '.join(faltam)}")
        for n, linha in enumerate(leitor, start=2):
            linha = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
            if not any(linha.values()):
                continue
            ctx = f"(tabela, linha {n})"
            try:
                ano = int(linha["ano"])
            except ValueError:
                raise ErroValidacao(f"ano inválido {linha['ano']!r} {ctx}")
            modo = linha["modo"].lower()
            if modo not in MODOS:
                raise ErroValidacao(f"modo inválido {linha['modo']!r} {ctx}; use anual ou mensal")
            if not linha["fonte"]:
                raise ErroValidacao(f"linha da tabela sem fonte {ctx}: a tabela progressiva exige fonte declarada")
            faixa = {
                "inicio": parse_num(linha["faixa_inicio"], ctx),
                "fim": parse_num(linha["faixa_fim"], ctx) if linha["faixa_fim"] else None,
                "aliquota": parse_num(linha["aliquota"], ctx),
                "deducao": parse_num(linha["deducao"], ctx),
                "fonte": linha["fonte"],
            }
            tabelas.setdefault((ano, modo), []).append(faixa)
    if not tabelas:
        raise ErroValidacao("tabela progressiva vazia")
    for (ano, modo), faixas in tabelas.items():
        faixas.sort(key=lambda x: x["inicio"])
        if faixas[0]["inicio"] != 0:
            raise ErroValidacao(f"tabela {ano}/{modo}: a primeira faixa deve começar em 0,00")
        if faixas[-1]["fim"] is not None:
            raise ErroValidacao(f"tabela {ano}/{modo}: a última faixa deve ter faixa_fim vazia (aberta)")
        acumulada = Decimal(0)
        for i, fx in enumerate(faixas):
            if i > 0:
                ant = faixas[i - 1]
                if ant["fim"] is None:
                    raise ErroValidacao(f"tabela {ano}/{modo}: faixa aberta antes da última")
                if fx["inicio"] != ant["fim"] + CENT:
                    raise ErroValidacao(
                        f"tabela {ano}/{modo}: faixa que começa em {fmt_brl(fx['inicio'])} não é contígua "
                        f"à anterior, que termina em {fmt_brl(ant['fim'])}")
                if fx["aliquota"] < ant["aliquota"]:
                    raise ErroValidacao(f"tabela {ano}/{modo}: alíquota decrescente na faixa {i + 1}")
                acumulada += ant["fim"] * (fx["aliquota"] - ant["aliquota"]) / CEM
            if abs(q2(acumulada) - q2(fx["deducao"])) > CENT:
                raise ErroValidacao(
                    f"tabela {ano}/{modo}: parcela a deduzir da faixa {i + 1} ({fmt_brl(fx['deducao'])}) "
                    f"não corresponde à estrutura das faixas (esperado {fmt_brl(acumulada)}); conferir a transcrição")
    return tabelas


def imposto_tabela(base, faixas):
    """Imposto pela tabela progressiva, por fatias (marginal), com conferência pela fórmula
    alíquota x base menos parcela a deduzir. Devolve (imposto, memória por faixa, alíquota marginal)."""
    if base <= 0:
        return Decimal(0), [], Decimal(0)
    imposto = Decimal(0)
    mem = []
    inferior = Decimal(0)
    marginal = None
    for fx in faixas:
        superior = fx["fim"] if fx["fim"] is not None else base
        fatia = min(base, superior) - inferior
        if fatia <= 0:
            break
        parcela = fatia * fx["aliquota"] / CEM
        imposto += parcela
        marginal = fx
        mem.append({"faixa": f"{fmt_brl(fx['inicio'])} a " + (fmt_brl(fx["fim"]) if fx["fim"] is not None else "acima"),
                    "fatia": fatia, "aliquota": fx["aliquota"], "imposto_faixa": parcela})
        inferior = superior
        if fx["fim"] is None or base <= fx["fim"]:
            break
    formula = base * marginal["aliquota"] / CEM - marginal["deducao"]
    if abs(q2(formula) - q2(imposto)) > CENT:
        raise ErroValidacao(
            f"sanidade falhou: imposto por fatias ({fmt_brl(imposto)}) difere da fórmula "
            f"alíquota x base menos parcela a deduzir ({fmt_brl(formula)})")
    return imposto, mem, marginal["aliquota"]


def ler_deducoes(caminho, memoria):
    """Lê as deduções legais item a item (cada item com fonte) e os parâmetros do desconto simplificado."""
    if not caminho:
        memoria.append("Deduções: nenhum arquivo informado; base de cálculo sem deduções (premissa declarada)")
        return {"legais": Decimal(0), "itens": [], "simplificado": None}
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"arquivo de deduções não encontrado: {caminho}")
    with p.open("r", encoding="utf-8") as f:
        dados = json.load(f)
    itens_saida = []
    total = Decimal(0)
    for i, item in enumerate(dados.get("itens", []), start=1):
        ctx = f"(deduções, item {i})"
        tipo = str(item.get("tipo", "")).lower()
        if tipo not in TIPOS_DEDUCAO:
            raise ErroValidacao(f"tipo de dedução desconhecido {tipo!r} {ctx}; válidos: {', '.join(TIPOS_DEDUCAO)}")
        if not str(item.get("fonte", "")).strip():
            raise ErroValidacao(f"dedução sem fonte {ctx}: limite ou comprovante precisa de fonte declarada")
        if tipo == "dependentes":
            qtd = int(item.get("quantidade", 0))
            unit = parse_num(item.get("valor_unitario"), ctx)
            valor = unit * qtd
            detalhe = f"{qtd} x {fmt_brl(unit)}"
        else:
            pago = parse_num(item.get("valor"), ctx)
            valor = pago
            detalhe = f"pago {fmt_brl(pago)}"
            if item.get("limite_por_pessoa") is not None:
                lim = parse_num(item["limite_por_pessoa"], ctx) * int(item.get("pessoas", 1))
                valor = min(pago, lim)
                detalhe += f", limite {fmt_brl(lim)}"
            elif item.get("limite") is not None:
                lim = parse_num(item["limite"], ctx)
                valor = min(pago, lim)
                detalhe += f", limite {fmt_brl(lim)}"
        if valor < 0:
            raise ErroValidacao(f"dedução negativa {ctx}")
        total += valor
        itens_saida.append({"tipo": tipo, "valor_dedutivel": valor, "detalhe": detalhe, "fonte": item["fonte"]})
    simplificado = None
    ds = dados.get("desconto_simplificado")
    if ds:
        if not str(ds.get("fonte", "")).strip():
            raise ErroValidacao("desconto simplificado sem fonte declarada")
        simplificado = {"percentual": parse_num(ds.get("percentual"), "(desconto simplificado)"),
                        "limite": parse_num(ds.get("limite"), "(desconto simplificado)"), "fonte": ds["fonte"]}
    memoria.append(f"Deduções legais lidas de {caminho}: {len(itens_saida)} itens, total {fmt_brl(total)}"
                   + (f"; desconto simplificado de {fmt_pct(simplificado['percentual'])} da base bruta, limitado a "
                      f"{fmt_brl(simplificado['limite'])}" if simplificado else "; sem desconto simplificado"))
    return {"legais": total, "itens": itens_saida, "simplificado": simplificado}


def escolher_deducao(ded, opcao, base_bruta):
    """Devolve (valor da dedução, critério, valor do simplificado para esta base)."""
    simp = None
    if ded["simplificado"] is not None:
        simp = min(base_bruta * ded["simplificado"]["percentual"] / CEM, ded["simplificado"]["limite"])
    if opcao == "legais" or simp is None:
        return ded["legais"], "deduções legais", simp
    if opcao == "simplificado":
        return simp, "desconto simplificado", simp
    if simp > ded["legais"]:
        return simp, "desconto simplificado (maior que as legais)", simp
    return ded["legais"], "deduções legais (maiores ou iguais ao simplificado)", simp


def carregar_classificacao(caminho):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"classificação não encontrada: {caminho}")
    with p.open("r", encoding="utf-8") as f:
        d = json.load(f)
    if d.get("script") != "classificar_rendimentos.py" or "totais" not in d:
        raise ErroValidacao("o JSON informado não foi gerado por classificar_rendimentos.py")
    if not d.get("sanidade", {}).get("ok"):
        raise ErroValidacao("a classificação informada não passou na própria sanidade; refaça a etapa anterior")
    return d


def dec_map(m):
    return {k: parse_num(v) for k, v in (m or {}).items()}


def calcular_cenario(cen, ano, tot, tabelas, args, ded_cache, memoria):
    """Calcula os modos pedidos para um cenário e um ano. Devolve dict por modo."""
    pres_ano = dec_map(tot["presumido_por_ano"]).get(str(ano), Decimal(0))
    aj_ano = dec_map(tot["ajuste_nao_declarado_por_ano"]).get(str(ano), Decimal(0))
    base_adic = dec_map(tot["base_adicional_ajuste_por_ano"]).get(str(ano), Decimal(0))
    pres_mes = {k: v for k, v in dec_map(tot.get("presumido_por_mes")).items() if k.endswith(str(ano))}
    aj_mes = {k: v for k, v in dec_map(tot.get("ajuste_nao_declarado_por_mes")).items() if k.endswith(str(ano))}
    if q2(sum(pres_mes.values(), Decimal(0))) != q2(pres_ano):
        raise ErroValidacao(f"sanidade falhou ({cen}, {ano}): soma mensal do presumido difere do anual")
    if q2(sum(aj_mes.values(), Decimal(0))) != q2(aj_ano):
        raise ErroValidacao(f"sanidade falhou ({cen}, {ano}): soma mensal do ajuste não declarado difere do anual")
    if q2(pres_ano + aj_ano) != q2(base_adic):
        raise ErroValidacao(f"sanidade falhou ({cen}, {ano}): presumido + ajuste não declarado difere da base adicional")
    memoria.append(f"[{cen} {ano}] base adicional {fmt_brl(base_adic)} = presumido (art. 42) {fmt_brl(pres_ano)} "
                   f"+ rendimento de fonte identificada não declarado {fmt_brl(aj_ano)}; sanidade mensal x anual OK")

    declarados = parse_num(args.rendimentos_declarados, "(--rendimentos-declarados)")
    irrf = parse_num(args.irrf, "(--irrf)")
    anual = tabelas.get((ano, "anual"))
    mensal = tabelas.get((ano, "mensal"))
    modos = MODOS if args.modo == "ambos" else (args.modo,)
    if "anual" in modos or "mensal" in modos:
        if anual is None:
            raise ErroValidacao(f"tabela anual do ano {ano} ausente no arquivo; o script não embute valores de tabela")
    if "mensal" in modos and mensal is None:
        raise ErroValidacao(f"tabela mensal do ano {ano} ausente no arquivo; o script não embute valores de tabela")

    if "ded" not in ded_cache:
        ded_cache["ded"] = ler_deducoes(args.deducoes, memoria)
    ded = ded_cache["ded"]

    def ajuste_anual(base_bruta):
        valor_ded, criterio, simp = escolher_deducao(ded, args.opcao_deducoes, base_bruta)
        base_calc = max(Decimal(0), base_bruta - valor_ded)
        imposto, mem, marginal = imposto_tabela(base_calc, anual)
        return {"base_bruta": base_bruta, "deducao": valor_ded, "criterio_deducao": criterio,
                "deducoes_legais": ded["legais"], "desconto_simplificado": simp, "itens_deducao": ded["itens"],
                "base_calculo": base_calc, "imposto": imposto, "aliquota_marginal": marginal, "faixas": mem}

    # Imposto da DIRPF original (T0): informado ou recalculado pela mesma tabela.
    if args.imposto_dirpf is not None:
        t0 = parse_num(args.imposto_dirpf, "(--imposto-dirpf)")
        origem_t0 = "informado (DIRPF original)"
    else:
        t0 = ajuste_anual(declarados)["imposto"] if declarados > 0 else Decimal(0)
        origem_t0 = "recalculado pela tabela e deduções informadas sobre os rendimentos declarados"
    memoria.append(f"[{cen} {ano}] imposto da DIRPF original (T0) {fmt_brl(t0)}: {origem_t0}; "
                   f"IRRF compensável adicional {fmt_brl(irrf)}")

    saida = {"presumido_ano": pres_ano, "ajuste_nao_declarado_ano": aj_ano, "base_adicional": base_adic,
             "rendimentos_declarados": declarados, "imposto_dirpf_original": t0, "origem_imposto_dirpf": origem_t0,
             "irrf_compensavel": irrf, "modos": {}}
    if "anual" in modos:
        aa = ajuste_anual(declarados + base_adic)
        dif = aa["imposto"] - t0 - irrf
        aa["imposto_suplementar"] = dif
        aa["fonte_tabela"] = anual[0]["fonte"]
        saida["modos"]["anual"] = aa
        memoria.append(f"[{cen} {ano} anual] base bruta {fmt_brl(aa['base_bruta'])} - {aa['criterio_deducao']} "
                       f"{fmt_brl(aa['deducao'])} = base de cálculo {fmt_brl(aa['base_calculo'])}; imposto "
                       f"{fmt_brl(aa['imposto'])} (alíquota marginal {fmt_pct(aa['aliquota_marginal'])}); "
                       f"suplementar = {fmt_brl(aa['imposto'])} - T0 {fmt_brl(t0)} - IRRF {fmt_brl(irrf)} = {fmt_brl(dif)}")
    if "mensal" in modos:
        parte_anual = ajuste_anual(declarados + aj_ano)
        dif_anual = parte_anual["imposto"] - t0 - irrf
        meses = []
        soma_mensal = Decimal(0)
        for mes in sorted(pres_mes, key=lambda m: (m[3:], m[:2])):
            base_m = pres_mes[mes]
            imp_m, mem_m, marg_m = imposto_tabela(base_m, mensal)
            soma_mensal += imp_m
            meses.append({"mes": mes, "base": base_m, "imposto": imp_m, "aliquota_marginal": marg_m, "faixas": mem_m})
        total = dif_anual + soma_mensal
        saida["modos"]["mensal"] = {
            "parte_anual": parte_anual, "imposto_suplementar_parte_anual": dif_anual,
            "meses": meses, "imposto_mensal_total": soma_mensal, "imposto_suplementar": total,
            "fonte_tabela_mensal": mensal[0]["fonte"], "fonte_tabela_anual": anual[0]["fonte"],
            "premissa": "presumido do art. 42 tributado no mês do crédito pela tabela mensal (§ 4º), sem deduções; "
                        "rendimento de fonte identificada não declarado no ajuste anual"}
        memoria.append(f"[{cen} {ano} mensal] parte anual: base bruta {fmt_brl(parte_anual['base_bruta'])} - "
                       f"{parte_anual['criterio_deducao']} {fmt_brl(parte_anual['deducao'])} = {fmt_brl(parte_anual['base_calculo'])}; "
                       f"imposto {fmt_brl(parte_anual['imposto'])}; suplementar da parte anual {fmt_brl(dif_anual)}")
        for m in meses:
            memoria.append(f"[{cen} {ano} mensal] {m['mes']}: base {fmt_brl(m['base'])} x tabela mensal = {fmt_brl(m['imposto'])}")
        memoria.append(f"[{cen} {ano} mensal] soma mensal {fmt_brl(soma_mensal)} + parte anual {fmt_brl(dif_anual)} = "
                       f"suplementar {fmt_brl(total)}")
    return saida


def confronto(resultados, imposto_lancado, memoria):
    if imposto_lancado is None:
        return None
    lanc = parse_num(imposto_lancado, "(--imposto-lancado)")
    quadro = {}
    for cen, anos in resultados.items():
        for ano, r in anos.items():
            for modo, m in r["modos"].items():
                dif = lanc - m["imposto_suplementar"]
                quadro[f"{cen}/{ano}/{modo}"] = {"recalculado": m["imposto_suplementar"], "lancado": lanc,
                                                 "diferenca_lancado_menos_recalculado": dif}
                memoria.append(f"Confronto {cen}/{ano}/{modo}: lançado {fmt_brl(lanc)} - recalculado "
                               f"{fmt_brl(m['imposto_suplementar'])} = {fmt_brl(dif)}")
    return quadro


def brl(texto):
    """Formata o valor já serializado (texto com ponto decimal) no padrão brasileiro."""
    return fmt_brl(Decimal(str(texto)))


def gravar_md(caminho, saida):
    linhas = ["# Recálculo do IRPF por cenário e modo", "",
              f"Data de referência: {DATA_REFERENCIA}. Tabela: {saida['premissas']['tabela']}. "
              f"Valores em R$, padrão brasileiro.", ""]
    for cen, anos in saida["resultados"].items():
        for ano, r in anos.items():
            linhas += [f"## Cenário {cen}, ano-calendário {ano}", "",
                       "| Item | Valor |", "|---|---|",
                       f"| Rendimentos declarados | {brl(r['rendimentos_declarados'])} |",
                       f"| Presumido (art. 42) | {brl(r['presumido_ano'])} |",
                       f"| Fonte identificada não declarado | {brl(r['ajuste_nao_declarado_ano'])} |",
                       f"| Imposto da DIRPF original (T0) | {brl(r['imposto_dirpf_original'])} |",
                       f"| IRRF compensável adicional | {brl(r['irrf_compensavel'])} |", ""]
            for modo, m in r["modos"].items():
                if modo == "anual":
                    linhas += ["| Modo anual | Valor |", "|---|---|",
                               f"| Base bruta | {brl(m['base_bruta'])} |",
                               f"| Dedução ({m['criterio_deducao']}) | {brl(m['deducao'])} |",
                               f"| Base de cálculo | {brl(m['base_calculo'])} |",
                               f"| Imposto devido | {brl(m['imposto'])} |",
                               f"| Imposto suplementar | {brl(m['imposto_suplementar'])} |", ""]
                else:
                    linhas += ["| Modo mensal (§ 4º) | Base | Imposto |", "|---|---|---|"]
                    for mm in m["meses"]:
                        linhas.append(f"| {mm['mes']} | {brl(mm['base'])} | {brl(mm['imposto'])} |")
                    linhas += [f"| Soma mensal | | {brl(m['imposto_mensal_total'])} |",
                               f"| Parte anual (suplementar) | | {brl(m['imposto_suplementar_parte_anual'])} |",
                               f"| Imposto suplementar total | | {brl(m['imposto_suplementar'])} |", ""]
    if saida.get("confronto"):
        linhas += ["## Confronto com o principal lançado", "", "| Cenário/ano/modo | Recalculado | Lançado | Diferença |",
                   "|---|---|---|---|"]
        for k, v in saida["confronto"].items():
            linhas.append(f"| {k} | {brl(v['recalculado'])} | {brl(v['lancado'])} | {brl(v['diferenca_lancado_menos_recalculado'])} |")
        linhas.append("")
    linhas += ["## Memória de cálculo", ""] + [f"{i + 1}. {m}" for i, m in enumerate(saida["memoria"])]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def executar(args):
    memoria = []
    clas = carregar_classificacao(args.classificacao)
    tabelas = ler_tabela(args.tabela)
    memoria.append(f"Classificação lida de {args.classificacao}; tabela progressiva lida de {args.tabela} "
                   f"({len(tabelas)} combinações ano/modo, todas com fonte declarada)")
    anos_disp = sorted({int(a) for cen in CENARIOS for a in clas["totais"][f"cenario_{cen}"]["por_ano"]})
    anos = [args.ano] if args.ano else anos_disp
    for a in anos:
        if a not in anos_disp:
            raise ErroValidacao(f"ano {a} não consta da classificação (anos disponíveis: {anos_disp})")
    cenarios = CENARIOS if args.cenario == "ambos" else (args.cenario,)
    ded_cache = {}
    resultados = {}
    for cen in cenarios:
        tot = clas["totais"][f"cenario_{cen}"]
        resultados[cen] = {}
        for ano in anos:
            resultados[cen][str(ano)] = calcular_cenario(cen, ano, tot, tabelas, args, ded_cache, memoria)
    conf = confronto(resultados, args.imposto_lancado, memoria)
    fontes = sorted({fx["fonte"] for fxs in tabelas.values() for fx in fxs})
    saida = {
        "skill": "pericia-irpf-rendimentos-nao-declarados",
        "script": "recalculo_irpf.py",
        "data_referencia": DATA_REFERENCIA,
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "premissas": {
            "classificacao": args.classificacao,
            "tabela": args.tabela,
            "fontes_tabela": fontes,
            "deducoes": args.deducoes,
            "opcao_deducoes": args.opcao_deducoes,
            "rendimentos_declarados": parse_num(args.rendimentos_declarados),
            "imposto_dirpf": args.imposto_dirpf,
            "irrf_compensavel": parse_num(args.irrf),
            "modo": args.modo,
            "cenario": args.cenario,
            "anos": anos,
            "modo_anual": "toda a base adicional no ajuste anual, com deduções e tabela anual",
            "modo_mensal": "presumido do art. 42 no mês do crédito pela tabela mensal (§ 4º), sem deduções; "
                           "rendimento de fonte identificada não declarado no ajuste anual",
            "escolha_do_modo": "controvérsia jurídica (§ 4º x apuração anual); o laudo apresenta os dois e a escolha é do juízo",
        },
        "resultados": resultados,
        "confronto": conf,
        "memoria": memoria,
    }
    return serializar(saida)


def main():
    p = argparse.ArgumentParser(
        description="Recálculo do IRPF a partir da classificação crédito a crédito (modos anual e mensal do art. 42, § 4º).")
    p.add_argument("--classificacao", required=True, help="JSON gerado por classificar_rendimentos.py")
    p.add_argument("--tabela", required=True, help="CSV da tabela progressiva (ano;modo;faixa_inicio;faixa_fim;aliquota;deducao;fonte)")
    p.add_argument("--ano", type=int, help="ano-calendário a recalcular (padrão: todos os anos da classificação)")
    p.add_argument("--deducoes", help="JSON com as deduções legais (item a item, com fonte) e o desconto simplificado")
    p.add_argument("--opcao-deducoes", choices=["legais", "simplificado", "maior"], default="maior",
                   help="critério de dedução no ajuste anual (padrão: a maior entre legais e simplificado)")
    p.add_argument("--rendimentos-declarados", default="0", help="rendimentos tributáveis já oferecidos na DIRPF original (padrão 0)")
    p.add_argument("--imposto-dirpf", help="imposto devido apurado na DIRPF original; se omitido, é recalculado pela tabela informada")
    p.add_argument("--irrf", default="0", help="IRRF compensável ainda não compensado na DIRPF original (padrão 0)")
    p.add_argument("--modo", choices=["anual", "mensal", "ambos"], default="ambos", help="modo de recálculo (padrão ambos)")
    p.add_argument("--cenario", choices=["base", "ampliado", "ambos"], default="ambos", help="cenário da classificação (padrão ambos)")
    p.add_argument("--imposto-lancado", help="principal lançado no auto, para confronto rápido (o confronto completo é de encargos_auto_infracao.py)")
    p.add_argument("--saida", help="arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="grava o quadro do recálculo em Markdown")
    args = p.parse_args()
    try:
        saida = executar(args)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            resumo = "; ".join(f"{cen}/{ano}/{modo}: {brl(m['imposto_suplementar'])}"
                               for cen, anos in saida["resultados"].items()
                               for ano, r in anos.items() for modo, m in r["modos"].items())
            print(f"Recálculo gravado em {args.saida}: imposto suplementar por cenário/ano/modo: {resumo}")
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
