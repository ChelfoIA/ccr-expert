#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classificar_rendimentos.py: classifica, crédito a crédito, os rendimentos ou
depósitos imputados à pessoa física em lançamento de IRPF (Lei 9.430/1996,
art. 42; DIRF; acréscimo patrimonial), avalia a suficiência da prova de origem
por regras declaradas, aplica as exclusões do § 3º (transferências próprias e
créditos de pequeno valor) e do § 6º (conta conjunta) e devolve totais por
natureza, tratamento tributário, mês e ano em dois cenários: base (só prova
suficiente) e ampliado (prova parcial aceita).

Parte da skill: pericia-irpf-rendimentos-nao-declarados

Uso:
    python3 scripts/classificar_rendimentos.py \
        --rendimentos assets/exemplo_rendimentos.csv --ano 2023 \
        --saida classificacao.json --md classificacao.md

Colunas do CSV (separador ';', cabeçalho obrigatório):
    id;data;valor;conta;historico;origem_alegada;natureza_alegada;documento;
    doc_data;doc_valor;doc_terceiro_identificado;transferencia_propria
    Opcionais: ja_declarado (S/N) e doc_qualificado (S/N).
Um crédito pode ser desdobrado em linhas (ids 12a e 12b) quando parte dele
tem natureza distinta, por exemplo resgate: principal e rendimento.
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
DATA_REFERENCIA = "12/09/2026"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"

# Limites do art. 42, § 3º, II, da Lei 9.430/1996, na redação da Lei 9.481/1997,
# art. 4º (reproduzidos no RIR/2018, art. 913, § 3º). São valores de lei, não
# de tabela anual; podem ser sobrepostos por --limite-individual e --limite-anual.
LIMITE_INDIVIDUAL_PADRAO = Decimal("12000.00")
LIMITE_ANUAL_PADRAO = Decimal("80000.00")

TRATAMENTOS = (
    "ajuste", "exclusivo_fonte", "isento", "nao_rendimento",
    "terceiro", "presumido_omissao", "excluido_par3",
)

# Tabela de naturezas: tratamento tributário da origem comprovada, fundamento,
# prova exigida, exigência de prova qualificada (data certa, registro público,
# ITCMD, decisão judicial) e alerta pericial. Detalhamento em
# references/natureza-dos-rendimentos.md.
NATUREZAS = {
    "salario": dict(
        tratamento="ajuste",
        fundamento="CTN, art. 43; Lei 7.713/1988, art. 3º; Lei 9.250/1995, arts. 8º e 11",
        prova="contracheque, DIRF ou informe de rendimentos da fonte pagadora conciliado ao crédito líquido",
        qualificada=False,
        alerta="IRRF retido pela fonte é compensável; conferir se o rendimento já constava da DIRPF"),
    "prolabore": dict(
        tratamento="ajuste",
        fundamento="CTN, art. 43; Lei 7.713/1988, art. 3º",
        prova="informe de rendimentos da pessoa jurídica, DIRF, folha ou contabilidade da empresa",
        qualificada=False,
        alerta="IRRF compensável; valor sem registro contábil na empresa sugere distribuição disfarçada"),
    "aluguel": dict(
        tratamento="ajuste",
        fundamento="Lei 7.713/1988, art. 3º, § 1º; carnê-leão quando o pagador é pessoa física",
        prova="contrato de locação, DIMOB da administradora, recibos e DIRF quando o locatário é pessoa jurídica",
        qualificada=False,
        alerta="deduzir do bruto os encargos do imóvel pagos pelo locador e a comissão da administradora, com comprovante"),
    "honorarios": dict(
        tratamento="ajuste",
        fundamento="Lei 7.713/1988, art. 3º; carnê-leão quando o pagador é pessoa física",
        prova="recibo ou nota, contrato de prestação de serviço, DIRF quando o pagador é pessoa jurídica",
        qualificada=False,
        alerta="despesas de livro-caixa só com escrituração e comprovantes [A VERIFICAR: Lei 8.134/1990, art. 6º]"),
    "dividendos": dict(
        tratamento="isento",
        fundamento="Lei 9.249/1995, art. 10; RIR/2018, art. 35",
        prova="informe de rendimentos da pessoa jurídica, ata ou deliberação, ECF e contabilidade com lucro apurado",
        qualificada=False,
        alerta="distribuição sem lucro contábil apurado é tributável; regime alterado a partir de 2026 [A VERIFICAR: Lei 15.270/2025]"),
    "doacao": dict(
        tratamento="isento",
        fundamento="Lei 7.713/1988, art. 6º, XVI; RIR/2018, art. 35",
        prova="ITCMD pago, declarado ou isenção reconhecida; DIRPF do doador (ficha de doações); transferência bancária do doador",
        qualificada=True,
        alerta="recibo particular sem data certa (CPC, art. 409) e doador sem capacidade financeira não comprovam a doação"),
    "heranca": dict(
        tratamento="isento",
        fundamento="Lei 7.713/1988, art. 6º, XVI; RIR/2018, art. 35",
        prova="formal de partilha, alvará judicial ou escritura de inventário; ITCMD; DIRPF do espólio",
        qualificada=True,
        alerta="valor recebido acima do quinhão declarado no espólio é acréscimo a comprovar"),
    "indenizacao_trabalhista": dict(
        tratamento="isento",
        fundamento="Lei 7.713/1988, art. 6º, V (parcela indenizatória)",
        prova="TRCT, sentença ou acordo homologado com discriminação das verbas, alvará de levantamento",
        qualificada=False,
        alerta="verbas remuneratórias do acordo (salários, horas extras, 13º) são tributáveis como RRA (Lei 7.713/1988, art. 12-A): separar por rubrica"),
    "fgts": dict(
        tratamento="isento",
        fundamento="Lei 7.713/1988, art. 6º, V",
        prova="extrato da conta vinculada com o saque e TRCT ou alvará",
        qualificada=False,
        alerta="conferir data e valor do saque no extrato da Caixa"),
    "poupanca": dict(
        tratamento="isento",
        fundamento="rendimento de caderneta de poupança isento [A VERIFICAR: Lei 8.981/1995, art. 68, III]",
        prova="extrato da poupança com o crédito de rendimento",
        qualificada=False,
        alerta="crédito vindo de poupança própria é transferência própria (natureza transferencia_propria), não rendimento"),
    "aplicacao_financeira": dict(
        tratamento="exclusivo_fonte",
        fundamento="rendimento de renda fixa com tributação exclusiva na fonte [A VERIFICAR: Lei 8.981/1995, art. 65]",
        prova="informe de rendimentos da instituição ou nota de resgate com IRRF destacado",
        qualificada=False,
        alerta="só o rendimento; o principal resgatado é resgate_principal; renda variável tem apuração mensal própria"),
    "resgate_principal": dict(
        tratamento="nao_rendimento",
        fundamento="CTN, art. 43 (não há acréscimo patrimonial)",
        prova="nota de resgate ou extrato da aplicação com a aplicação de origem identificada e a DIRPF (bens e direitos)",
        qualificada=False,
        alerta="aplicação de origem sem lastro declarado desloca o problema para a data da aplicação"),
    "mutuo_recebido": dict(
        tratamento="nao_rendimento",
        fundamento="CC, art. 586; CPC, art. 409 (data certa); Lei 9.430/1996, art. 42, § 2º",
        prova="contrato com data certa (registro ou firma reconhecida à época), DIRPF do mutuante e do mutuário, transferência do mutuante, capacidade financeira do mutuante, devolução posterior",
        qualificada=True,
        alerta="contrato sem data certa, mutuante sem lastro ou devolução inexistente reduzem a prova a parcial"),
    "venda_bem": dict(
        tratamento="nao_rendimento",
        fundamento="preço não é renda; ganho de capital tem apuração própria [A VERIFICAR: Lei 9.250/1995, arts. 22 e 23, valores vigentes]",
        prova="escritura ou registro, CRLV e ATPV, contrato com data certa, DIRPF com a baixa do bem, GCAP e DARF do ganho",
        qualificada=True,
        alerta="preço acima do valor declarado na DIRPF é acréscimo; sem DARF ou isenção, o ganho de capital é lançável em separado"),
    "transferencia_propria": dict(
        tratamento="nao_rendimento",
        fundamento="Lei 9.430/1996, art. 42, § 3º, I",
        prova="extrato da conta de origem, do mesmo titular, com débito de igual data e valor",
        qualificada=False,
        alerta="conta conjunta ou de cônjuge não é conta própria: aplicar o § 6º ou exigir prova da titularidade do recurso"),
    "pensao_alimenticia": dict(
        tratamento="isento",
        fundamento="não incidência reconhecida pelo STF [A VERIFICAR: ADI 5.422 e data de eficácia]",
        prova="decisão judicial ou escritura pública que fixa os alimentos e comprovante de pagamento do alimentante",
        qualificada=False,
        alerta="antes da decisão do STF o valor era tributável no ajuste: verificar a data do crédito"),
    "seguro": dict(
        tratamento="isento",
        fundamento="Lei 7.713/1988, art. 6º (capital de apólice e indenização por sinistro)",
        prova="apólice, aviso de sinistro e comprovante de pagamento da seguradora",
        qualificada=False,
        alerta="indenização que exceda o dano (lucros cessantes) pode ser tributável"),
    "restituicao_ir": dict(
        tratamento="nao_rendimento",
        fundamento="CTN, art. 165 (restituição de tributo)",
        prova="consulta de restituição da RFB (lote e valor) e DIRPF do exercício",
        qualificada=False,
        alerta="conferir se o valor creditado coincide com o lote de restituição"),
    "estorno": dict(
        tratamento="nao_rendimento",
        fundamento="ausência de acréscimo patrimonial (CTN, art. 43)",
        prova="lançamento de débito correspondente no mesmo extrato, anterior ao crédito",
        qualificada=False,
        alerta="estorno sem débito prévio identificado é crédito sem origem"),
    "terceiro": dict(
        tratamento="terceiro",
        fundamento="Lei 9.430/1996, art. 42, §§ 5º e 6º",
        prova="mandato ou procuração, DIRPF do terceiro com o rendimento, extratos do terceiro, contrato que explique a passagem do recurso",
        qualificada=True,
        alerta="o § 5º exige prova, não alegação; o efeito é o lançamento contra o terceiro, não a extinção do crédito"),
    "sem_prova": dict(
        tratamento="presumido_omissao",
        fundamento="Lei 9.430/1996, art. 42, caput e § 4º",
        prova="nenhuma apresentada",
        qualificada=False,
        alerta="candidato à exclusão do § 3º, II, quando de pequeno valor"),
}


class ErroValidacao(Exception):
    """Erro de dado de entrada: sai com código 1 e mensagem objetiva."""


def parse_num(texto, contexto=""):
    """Aceita 1.234,56 (padrão brasileiro) e 1234.56 (técnico); devolve Decimal."""
    if texto is None:
        raise ErroValidacao(f"valor ausente {contexto}")
    t = str(texto).strip().replace("R$", "").replace(" ", "")
    if t == "":
        raise ErroValidacao(f"valor ausente {contexto}")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return Decimal(t)
    except InvalidOperation:
        raise ErroValidacao(f"valor inválido {texto!r} {contexto}")


def parse_data(texto, contexto=""):
    """Data em dd/mm/aaaa; devolve datetime.date."""
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


def sn(texto, contexto=""):
    t = (texto or "").strip().upper()
    if t in ("", "N", "NAO", "NÃO", "0", "FALSE"):
        return False
    if t in ("S", "SIM", "1", "TRUE"):
        return True
    raise ErroValidacao(f"campo S/N inválido {texto!r} {contexto}")


COLUNAS = ["id", "data", "valor", "conta", "historico", "origem_alegada",
           "natureza_alegada", "documento", "doc_data", "doc_valor",
           "doc_terceiro_identificado", "transferencia_propria"]
OPCIONAIS = ["ja_declarado", "doc_qualificado"]


def ler_creditos(caminho, ano_filtro):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"arquivo não encontrado: {caminho}")
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        amostra = f.read(4096)
        f.seek(0)
        delim = ";" if amostra.count(";") >= amostra.count(",") else ","
        leitor = csv.DictReader(f, delimiter=delim)
        cabecalho = [c.strip() for c in (leitor.fieldnames or [])]
        faltantes = [c for c in COLUNAS if c not in cabecalho]
        if faltantes:
            raise ErroValidacao(f"CSV sem as colunas obrigatórias: {', '.join(faltantes)}")
        creditos = []
        ids = set()
        for n, linha in enumerate(leitor, start=2):
            linha = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
            if not any(linha.values()):
                continue
            ctx = f"(linha {n})"
            cid = linha["id"]
            if not cid:
                raise ErroValidacao(f"id vazio {ctx}")
            if cid in ids:
                raise ErroValidacao(f"id duplicado {cid!r} {ctx}")
            ids.add(cid)
            data = parse_data(linha["data"], ctx)
            valor = parse_num(linha["valor"], ctx)
            if valor <= 0:
                raise ErroValidacao(f"valor do crédito deve ser positivo {ctx}")
            natureza = linha["natureza_alegada"].lower()
            if natureza not in NATUREZAS:
                raise ErroValidacao(
                    f"natureza desconhecida {natureza!r} {ctx}; válidas: {', '.join(NATUREZAS)}")
            doc_data = parse_data(linha["doc_data"], ctx) if linha["doc_data"] else None
            doc_valor = parse_num(linha["doc_valor"], ctx) if linha["doc_valor"] else None
            credito = {
                "id": cid, "data": data, "valor": valor, "conta": linha["conta"],
                "historico": linha["historico"], "origem_alegada": linha["origem_alegada"],
                "natureza": natureza, "documento": linha["documento"],
                "doc_data": doc_data, "doc_valor": doc_valor,
                "doc_terceiro": sn(linha["doc_terceiro_identificado"], ctx),
                "transferencia_propria": sn(linha["transferencia_propria"], ctx),
                "ja_declarado": sn(linha.get("ja_declarado", ""), ctx),
                "doc_qualificado": sn(linha.get("doc_qualificado", ""), ctx),
                "linha": n,
            }
            if ano_filtro and data.year != ano_filtro:
                continue
            creditos.append(credito)
    if not creditos:
        raise ErroValidacao("nenhum crédito lido (verifique o arquivo e o filtro --ano)")
    creditos.sort(key=lambda c: (c["data"], c["id"]))
    return creditos


def avaliar_prova(c, tol_dias, tol_pct):
    """Devolve (nivel, motivos): suficiente, parcial ou ausente."""
    regra = NATUREZAS[c["natureza"]]
    if c["natureza"] == "sem_prova" or not c["documento"]:
        return "ausente", ["nenhum documento apresentado"]
    motivos = []
    if c["doc_data"] is None:
        motivos.append("documento sem data conciliável")
    elif abs((c["doc_data"] - c["data"]).days) > tol_dias:
        motivos.append(f"data do documento ({fmt_data(c['doc_data'])}) fora da tolerância de {tol_dias} dias")
    if c["doc_valor"] is None:
        motivos.append("documento sem valor conciliável")
    else:
        tolerancia = max(Decimal("1.00"), c["valor"] * tol_pct / Decimal(100))
        if abs(c["doc_valor"] - c["valor"]) > tolerancia:
            motivos.append(f"valor do documento ({fmt_brl(c['doc_valor'])}) não coincide com o crédito")
    if c["natureza"] == "transferencia_propria":
        if not c["transferencia_propria"]:
            motivos.append("coluna transferencia_propria não marcada")
        if not c["doc_terceiro"]:
            motivos.append("conta de origem do próprio titular não identificada no documento")
    elif not c["doc_terceiro"]:
        motivos.append("contraparte (depositante ou fonte pagadora) não identificada")
    if regra["qualificada"] and not c["doc_qualificado"]:
        motivos.append("natureza exige prova qualificada (data certa, registro público, ITCMD ou decisão) não apresentada")
    if motivos:
        return "parcial", motivos
    return "suficiente", ["data, valor e contraparte conciliados" + (
        "; prova qualificada presente" if regra["qualificada"] else "")]


def tratamento_cenario(c, nivel, aceitar_parcial):
    natural = NATUREZAS[c["natureza"]]["tratamento"]
    if nivel == "ausente":
        return "presumido_omissao"
    if nivel == "parcial" and not aceitar_parcial:
        return "presumido_omissao"
    return natural


def aplicar_par3_ii(creditos, chave, lim_ind, lim_anual, memoria):
    """Exclui do presumido os créditos de pequeno valor quando a soma anual cabe no limite."""
    por_ano = {}
    for c in creditos:
        if c[chave] == "presumido_omissao" and c["valor"] <= lim_ind:
            por_ano.setdefault(c["data"].year, []).append(c)
    for ano, lista in sorted(por_ano.items()):
        soma = sum((x["valor"] for x in lista), Decimal(0))
        if soma <= lim_anual:
            for x in lista:
                x[chave] = "excluido_par3"
                x.setdefault("motivos_" + chave, []).append(
                    f"§ 3º, II: crédito de {fmt_brl(x['valor'])} até {fmt_brl(lim_ind)} e soma anual de {fmt_brl(soma)} até {fmt_brl(lim_anual)}")
            memoria.append(f"[{chave}] ano {ano}: {len(lista)} créditos até {fmt_brl(lim_ind)} somam {fmt_brl(soma)}, dentro de {fmt_brl(lim_anual)}: excluídos (§ 3º, II)")
        else:
            memoria.append(f"[{chave}] ano {ano}: {len(lista)} créditos até {fmt_brl(lim_ind)} somam {fmt_brl(soma)}, acima de {fmt_brl(lim_anual)}: nenhum excluído (§ 3º, II)")


def totais(creditos, chave, fracoes):
    t = {"por_tratamento": {}, "por_natureza": {}, "por_mes": {}, "por_ano": {},
         "base_adicional_ajuste_por_ano": {}, "base_adicional_por_mes": {},
         "presumido_por_ano": {}, "ajuste_nao_declarado_por_ano": {}}
    soma_classes = Decimal(0)
    for c in creditos:
        trat = c[chave]
        v = c["valor"]
        mes = c["data"].strftime("%m/%Y")
        ano = str(c["data"].year)
        t["por_tratamento"][trat] = t["por_tratamento"].get(trat, Decimal(0)) + v
        t["por_natureza"][c["natureza"]] = t["por_natureza"].get(c["natureza"], Decimal(0)) + v
        t["por_mes"][mes] = t["por_mes"].get(mes, Decimal(0)) + v
        t["por_ano"][ano] = t["por_ano"].get(ano, Decimal(0)) + v
        soma_classes += v
        fracao = fracoes.get(c["conta"], 1)
        imputado = v / Decimal(fracao)
        c["valor_imputado_titular_" + chave] = imputado
        entra = False
        if trat == "presumido_omissao":
            entra = True
            t["presumido_por_ano"][ano] = t["presumido_por_ano"].get(ano, Decimal(0)) + imputado
        elif trat == "ajuste" and not c["ja_declarado"]:
            entra = True
            t["ajuste_nao_declarado_por_ano"][ano] = t["ajuste_nao_declarado_por_ano"].get(ano, Decimal(0)) + imputado
        if entra:
            t["base_adicional_ajuste_por_ano"][ano] = t["base_adicional_ajuste_por_ano"].get(ano, Decimal(0)) + imputado
            t["base_adicional_por_mes"][mes] = t["base_adicional_por_mes"].get(mes, Decimal(0)) + imputado
    t["soma_classes"] = soma_classes
    return t


def serializar(obj):
    if isinstance(obj, Decimal):
        return str(q2(obj))
    if isinstance(obj, date):
        return fmt_data(obj)
    if isinstance(obj, dict):
        return {k: serializar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serializar(v) for v in obj]
    return obj


def tabela_md(creditos, tot_base, tot_amp, sanidade):
    linhas = ["| id | data | valor | natureza alegada | prova | trat. base | trat. ampliado | motivo |",
              "|---|---|---|---|---|---|---|---|"]
    for c in creditos:
        motivo = "; ".join(c["motivos_prova"])
        linhas.append(f"| {c['id']} | {fmt_data(c['data'])} | {fmt_brl(c['valor'])} | {c['natureza']} | {c['prova']} | "
                      f"{c['tratamento_base']} | {c['tratamento_ampliado']} | {motivo} |")
    linhas.append("")
    linhas.append("| tratamento | cenário base | cenário ampliado |")
    linhas.append("|---|---|---|")
    for trat in TRATAMENTOS:
        vb = tot_base["por_tratamento"].get(trat, Decimal(0))
        va = tot_amp["por_tratamento"].get(trat, Decimal(0))
        if vb or va:
            linhas.append(f"| {trat} | {fmt_brl(vb)} | {fmt_brl(va)} |")
    linhas.append(f"| total imputado | {fmt_brl(sanidade['total_imputado'])} | {fmt_brl(sanidade['total_imputado'])} |")
    linhas.append("")
    linhas.append("| ano | base adicional (cenário base) | base adicional (cenário ampliado) |")
    linhas.append("|---|---|---|")
    anos = sorted(set(tot_base["por_ano"]) | set(tot_amp["por_ano"]))
    for ano in anos:
        linhas.append(f"| {ano} | {fmt_brl(tot_base['base_adicional_ajuste_por_ano'].get(ano, Decimal(0)))} | "
                      f"{fmt_brl(tot_amp['base_adicional_ajuste_por_ano'].get(ano, Decimal(0)))} |")
    return "\n".join(linhas) + "\n"


def executar(args):
    memoria = []
    tol_pct = parse_num(args.tolerancia_valor, "(--tolerancia-valor)")
    lim_ind = parse_num(args.limite_individual, "(--limite-individual)")
    lim_anual = parse_num(args.limite_anual, "(--limite-anual)")
    if args.tolerancia_dias < 0 or tol_pct < 0:
        raise ErroValidacao("tolerâncias não podem ser negativas")
    fracoes = {}
    for item in args.conta_conjunta or []:
        if "=" not in item:
            raise ErroValidacao(f"--conta-conjunta espera CONTA=N, recebido {item!r}")
        conta, n = item.split("=", 1)
        try:
            n = int(n)
        except ValueError:
            raise ErroValidacao(f"número de titulares inválido em {item!r}")
        if n < 2:
            raise ErroValidacao("conta conjunta exige ao menos 2 titulares")
        fracoes[conta.strip()] = n

    creditos = ler_creditos(args.rendimentos, args.ano)
    total = sum((c["valor"] for c in creditos), Decimal(0))
    memoria.append(f"Lidos {len(creditos)} créditos de {args.rendimentos}"
                   + (f" (ano {args.ano})" if args.ano else "") + f", total imputado {fmt_brl(total)}")
    memoria.append(f"Regra de prova: data do documento a até {args.tolerancia_dias} dias do crédito; valor com tolerância de "
                   f"{tol_pct}% (mínimo R$ 1,00); contraparte identificada; prova qualificada quando a natureza exige")

    for c in creditos:
        nivel, motivos = avaliar_prova(c, args.tolerancia_dias, tol_pct)
        regra = NATUREZAS[c["natureza"]]
        c["prova"] = nivel
        c["motivos_prova"] = motivos
        c["tratamento_natural"] = regra["tratamento"]
        c["fundamento"] = regra["fundamento"]
        c["prova_exigida"] = regra["prova"]
        c["alerta"] = regra["alerta"]
        c["tratamento_base"] = tratamento_cenario(c, nivel, aceitar_parcial=False)
        c["tratamento_ampliado"] = tratamento_cenario(c, nivel, aceitar_parcial=True)
        c["motivos_tratamento_base"] = []
        c["motivos_tratamento_ampliado"] = []
        if c["tratamento_base"] == "presumido_omissao" and regra["tratamento"] != "presumido_omissao":
            c["motivos_tratamento_base"].append("origem não comprovada no cenário base: " + "; ".join(motivos))
        if c["tratamento_base"] == "nao_rendimento" and c["natureza"] == "transferencia_propria":
            c["motivos_tratamento_base"].append("§ 3º, I: transferência entre contas do próprio titular")
        if c["ja_declarado"] and c["tratamento_base"] == "ajuste":
            c["motivos_tratamento_base"].append("já oferecido à tributação na DIRPF: não compõe a base adicional")

    memoria.append("Cenário base: só prova suficiente afasta a presunção; cenário ampliado: prova parcial aceita, para medir a sensibilidade")
    aplicar_par3_ii(creditos, "tratamento_base", lim_ind, lim_anual, memoria)
    aplicar_par3_ii(creditos, "tratamento_ampliado", lim_ind, lim_anual, memoria)
    if fracoes:
        memoria.append("§ 6º: " + "; ".join(f"conta {k} dividida por {v} titulares" for k, v in fracoes.items()))

    tot_base = totais(creditos, "tratamento_base", fracoes)
    tot_amp = totais(creditos, "tratamento_ampliado", fracoes)
    sanidade = {
        "total_imputado": total,
        "soma_classes_base": tot_base["soma_classes"],
        "soma_classes_ampliado": tot_amp["soma_classes"],
        "ok": tot_base["soma_classes"] == total and tot_amp["soma_classes"] == total,
    }
    if not sanidade["ok"]:
        raise ErroValidacao("sanidade falhou: soma das classes difere do total imputado")
    memoria.append(f"Sanidade: soma das classes = total imputado = {fmt_brl(total)} nos dois cenários")

    sem_prova = [c["id"] for c in creditos if c["prova"] == "ausente"]
    parciais = [c["id"] for c in creditos if c["prova"] == "parcial"]
    alertas = [f"{c['id']}: {c['alerta']}" for c in creditos if c["prova"] != "ausente"]
    for c in creditos:
        for chave in ("tratamento_base", "tratamento_ampliado"):
            k = "motivos_" + chave
            if k in c and chave == "tratamento_base" and "motivos_tratamento_base" in c:
                pass
    saida = {
        "skill": "pericia-irpf-rendimentos-nao-declarados",
        "script": "classificar_rendimentos.py",
        "data_referencia": DATA_REFERENCIA,
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "premissas": {
            "arquivo": args.rendimentos,
            "ano_filtro": args.ano,
            "tolerancia_dias": args.tolerancia_dias,
            "tolerancia_valor_pct": str(tol_pct),
            "limite_individual_par3_ii": lim_ind,
            "limite_anual_par3_ii": lim_anual,
            "fonte_limites": "Lei 9.430/1996, art. 42, § 3º, II, na redação da Lei 9.481/1997, art. 4º; RIR/2018, art. 913, § 3º",
            "contas_conjuntas": fracoes,
            "cenario_base": "só prova suficiente afasta a presunção do art. 42",
            "cenario_ampliado": "prova parcial aceita; mede a sensibilidade do resultado",
            "ja_declarado": "crédito de natureza ajuste já oferecido na DIRPF não entra na base adicional",
        },
        "creditos": [{
            "id": c["id"], "data": c["data"], "mes": c["data"].strftime("%m/%Y"), "valor": c["valor"],
            "valor_brl": fmt_brl(c["valor"]), "conta": c["conta"], "historico": c["historico"],
            "origem_alegada": c["origem_alegada"], "natureza": c["natureza"],
            "tratamento_natural": c["tratamento_natural"], "fundamento": c["fundamento"],
            "documento": c["documento"], "prova": c["prova"], "motivos_prova": c["motivos_prova"],
            "prova_exigida": c["prova_exigida"], "alerta": c["alerta"],
            "ja_declarado": c["ja_declarado"],
            "tratamento_base": c["tratamento_base"], "motivos_tratamento_base": c["motivos_tratamento_base"],
            "tratamento_ampliado": c["tratamento_ampliado"], "motivos_tratamento_ampliado": c["motivos_tratamento_ampliado"],
            "valor_imputado_titular_base": c["valor_imputado_titular_tratamento_base"],
            "valor_imputado_titular_ampliado": c["valor_imputado_titular_tratamento_ampliado"],
        } for c in creditos],
        "totais": {"cenario_base": tot_base, "cenario_ampliado": tot_amp},
        "creditos_sem_prova": sem_prova,
        "creditos_prova_parcial": parciais,
        "alertas": alertas,
        "sanidade": sanidade,
        "memoria": memoria,
    }
    return serializar(saida), creditos, tot_base, tot_amp, sanidade


def main():
    p = argparse.ArgumentParser(
        description="Classificação crédito a crédito de rendimentos imputados em lançamento de IRPF (Lei 9.430/1996, art. 42).")
    p.add_argument("--rendimentos", required=True, help="CSV com os créditos ou rendimentos imputados (ver docstring)")
    p.add_argument("--ano", type=int, help="ano-calendário a filtrar; sem filtro, processa todos os anos do arquivo")
    p.add_argument("--tolerancia-dias", type=int, default=10, help="dias de tolerância entre a data do documento e a do crédito (padrão 10)")
    p.add_argument("--tolerancia-valor", default="0,5", help="tolerância percentual entre valor do documento e do crédito (padrão 0,5)")
    p.add_argument("--limite-individual", default="12000,00", help="limite individual do § 3º, II (padrão R$ 12.000,00, Lei 9.481/1997)")
    p.add_argument("--limite-anual", default="80000,00", help="limite anual do § 3º, II (padrão R$ 80.000,00, Lei 9.481/1997)")
    p.add_argument("--conta-conjunta", action="append", help="CONTA=N para dividir o presumido pelo número de titulares (§ 6º); repetível")
    p.add_argument("--saida", help="arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="grava a tabela crédito a crédito e os totais em Markdown")
    p.add_argument("--csv", help="grava a tabela crédito a crédito em CSV")
    args = p.parse_args()
    try:
        saida, creditos, tot_base, tot_amp, sanidade = executar(args)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto, encoding="utf-8")
            print(f"Classificação gravada em {args.saida}: {len(creditos)} créditos, total {fmt_brl(sanidade['total_imputado'])}; "
                  f"base adicional (cenário base) {', '.join(f'{a}: {fmt_brl(v)}' for a, v in tot_base['base_adicional_ajuste_por_ano'].items())}")
        else:
            print(texto)
        if args.md:
            Path(args.md).write_text(tabela_md(creditos, tot_base, tot_amp, sanidade), encoding="utf-8")
            print(f"Tabela Markdown gravada em {args.md}")
        if args.csv:
            with open(args.csv, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["id", "data", "valor", "natureza", "prova", "tratamento_base", "tratamento_ampliado", "motivo"])
                for c in creditos:
                    w.writerow([c["id"], fmt_data(c["data"]), str(q2(c["valor"])).replace(".", ","), c["natureza"],
                                c["prova"], c["tratamento_base"], c["tratamento_ampliado"], "; ".join(c["motivos_prova"])])
            print(f"Tabela CSV gravada em {args.csv}")
    except ErroValidacao as e:
        print(f"ERRO de validação: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"ERRO: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
