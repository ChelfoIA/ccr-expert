#!/usr/bin/env python3
"""
Reconstrução do fluxo de caixa do espólio por conta, mês e categoria, com listas de exceção
(saídas sem alvará, sem documento, em favor de herdeiro ou inventariante, despesas pessoais e
despesas de imóvel ocupado com exclusividade por herdeiro).

Parte da skill: auditoria-contabil-espolio

Uso:
    python3 scripts/fluxo_caixa_espolio.py --movimentos assets/exemplo_movimentos.csv \
        --abertura-sucessao 10/01/2024 --saldo-inicial 12.500,00 \
        --imoveis-ocupados IM02 --saida fluxo.json --csv dfc.csv --md dfc.md

    Conciliação com o extrato: acrescentar --saldo-final-extrato 38.430,55; se o saldo
    reconstruído divergir, o script falha de propósito (ERRO de validação).

Entrada (CSV separado por ponto e vírgula, com cabeçalho):
    data;conta;historico;valor;tipo;categoria;beneficiario;vinculo_beneficiario;
    autorizacao_judicial;documento;imovel_id;empresa_id

    data                 dd/mm/aaaa
    valor                positivo, em padrão brasileiro (1.234,56) ou técnico (1234.56)
    tipo                 C (entrada) ou D (saída)
    categoria            ver CATEGORIAS_ENTRADA e CATEGORIAS_SAIDA; desconhecida vira "outros" com aviso
    vinculo_beneficiario herdeiro | inventariante | terceiro | espolio
    autorizacao_judicial S | N (vazio equivale a N)
    documento            referência ao lastro (fl., recibo, nota); vazio equivale a sem documento
    moeda                (opcional) só BRL é aceito; movimento em euro é convertido antes por
                         scripts/conversao_ptax.py, cujo CSV de saída entra aqui diretamente

Saída: JSON com premissas, DFC mensal, totais por categoria, por conta e por vínculo do
beneficiário, listas de exceção, avisos, testes de sanidade e memória de cálculo.
Todo valor monetário é Decimal; arredondamento ROUND_HALF_UP apenas na apresentação.
"""

import argparse
import csv
import json
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

CATEGORIAS_ENTRADA = {
    "aluguel_recebido", "dividendo", "venda_bem", "resgate_aplicacao",
    "rendimento_financeiro", "restituicao", "indenizacao", "aporte_herdeiro",
    "transferencia_interna", "outros",
}
CATEGORIAS_SAIDA = {
    "itcmd", "iptu", "condominio", "manutencao", "seguro", "tributo", "honorarios",
    "custas", "divida_espolio", "retirada_herdeiro", "despesa_pessoal",
    "aplicacao_financeira", "transferencia_interna", "outros",
}
# Despesas de conservação e melhoramento (CPC, art. 619, IV): admitem ratificação posterior,
# por isso entram em lista própria e não se confundem com retirada ou pagamento de dívida.
CATEGORIAS_CONSERVACAO = {"iptu", "condominio", "manutencao", "seguro", "tributo"}
# Atos que exigem autorização prévia do juízo (CPC, art. 619, I e III).
CATEGORIAS_ALVARA_OBRIGATORIO = {"venda_bem", "divida_espolio"}
VINCULOS = {"herdeiro", "inventariante", "terceiro", "espolio", ""}

CENTAVOS = Decimal("0.01")
ZERO = Decimal("0")


def q2(valor):
    """Arredonda para 2 casas, ROUND_HALF_UP, só na apresentação."""
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def s2(valor):
    """Decimal em string técnica com 2 casas (para JSON)."""
    return str(q2(valor))


def fmt_br(valor, moeda="BRL"):
    """Formata no padrão brasileiro: R$ 1.234,56."""
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


def parse_data(texto, campo="data"):
    """dd/mm/aaaa para date."""
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(f"{campo} inválida (esperado dd/mm/aaaa): {texto!r}") from exc


def fmt_data(d):
    return d.strftime("%d/%m/%Y")


def ler_movimentos(caminho):
    """Lê o CSV e valida linha a linha. Devolve lista de dicionários e avisos."""
    avisos = []
    movimentos = []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        obrigatorias = {"data", "conta", "historico", "valor", "tipo", "categoria"}
        faltam = obrigatorias - set(leitor.fieldnames or [])
        if faltam:
            raise ValueError(f"colunas obrigatórias ausentes no CSV: {sorted(faltam)}")
        for n, linha in enumerate(leitor, start=2):
            if not any((v or "").strip() for v in linha.values()):
                continue
            tipo = (linha.get("tipo") or "").strip().upper()
            if tipo not in {"C", "D"}:
                raise ValueError(f"linha {n}: tipo deve ser C ou D, veio {tipo!r}")
            valor = parse_num(linha.get("valor"))
            if valor <= ZERO:
                raise ValueError(f"linha {n}: valor deve ser positivo, veio {valor}")
            categoria = (linha.get("categoria") or "").strip().lower()
            universo = CATEGORIAS_ENTRADA if tipo == "C" else CATEGORIAS_SAIDA
            if categoria not in universo:
                avisos.append(
                    f"linha {n}: categoria {categoria!r} não reconhecida para tipo {tipo}; "
                    f"tratada como 'outros'. Categorias válidas: {sorted(universo)}"
                )
                categoria = "outros"
            vinculo = (linha.get("vinculo_beneficiario") or "").strip().lower()
            if vinculo not in VINCULOS:
                raise ValueError(
                    f"linha {n}: vinculo_beneficiario deve ser herdeiro, inventariante, "
                    f"terceiro ou espolio, veio {vinculo!r}"
                )
            aut = (linha.get("autorizacao_judicial") or "").strip().upper()
            if aut not in {"S", "N", ""}:
                raise ValueError(f"linha {n}: autorizacao_judicial deve ser S ou N, veio {aut!r}")
            # O fluxo é apurado em reais: moeda estrangeira precisa passar antes por conversao_ptax.py,
            # porque somar euro com real produz um saldo sem significado.
            moeda = (linha.get("moeda") or "BRL").strip().upper() or "BRL"
            if moeda != "BRL":
                raise ValueError(
                    f"linha {n}: moeda {moeda} diferente de BRL; converter antes com scripts/conversao_ptax.py "
                    "e usar o CSV gerado por --csv como entrada"
                )
            conversao = ""
            if (linha.get("moeda_original") or "").strip() and (linha.get("moeda_original") or "").strip().upper() != "BRL":
                conversao = (f"{linha.get('moeda_original', '').strip()} {linha.get('valor_original', '').strip()} x "
                             f"{linha.get('cotacao', '').strip()} ({linha.get('criterio_cotacao', '').strip()}, "
                             f"PTAX de {linha.get('data_cotacao', '').strip()})")
            movimentos.append({
                "linha": n,
                "data": parse_data(linha.get("data"), f"linha {n}: data"),
                "conta": (linha.get("conta") or "").strip(),
                "historico": (linha.get("historico") or "").strip(),
                "valor": valor,
                "tipo": tipo,
                "categoria": categoria,
                "beneficiario": (linha.get("beneficiario") or "").strip(),
                "vinculo": vinculo,
                "autorizacao": aut or "N",
                "documento": (linha.get("documento") or "").strip(),
                "imovel_id": (linha.get("imovel_id") or "").strip(),
                "empresa_id": (linha.get("empresa_id") or "").strip(),
                "conversao": conversao,
            })
    if not movimentos:
        raise ValueError("nenhum movimento válido encontrado no CSV")
    return movimentos, avisos


def resumo_mov(m, motivo):
    """Linha de exceção com os campos que o laudo precisa citar."""
    return OrderedDict([
        ("linha_csv", m["linha"]),
        ("data", fmt_data(m["data"])),
        ("conta", m["conta"]),
        ("historico", m["historico"]),
        ("valor", s2(m["valor"])),
        ("valor_br", fmt_br(m["valor"])),
        ("tipo", m["tipo"]),
        ("categoria", m["categoria"]),
        ("beneficiario", m["beneficiario"]),
        ("vinculo_beneficiario", m["vinculo"]),
        ("autorizacao_judicial", m["autorizacao"]),
        ("documento", m["documento"] or "sem documento"),
        ("imovel_id", m["imovel_id"]),
        ("conversao", m.get("conversao", "")),
        ("motivo", motivo),
    ])


def totalizar(lista):
    return sum((Decimal(x["valor"]) for x in lista), ZERO)


def processar(movimentos, abertura, saldo_inicial, imoveis_ocupados, data_referencia):
    """Monta DFC mensal, totais e exceções. Devolve dicionário de resultado (sem JSON)."""
    avisos = []
    memoria = []

    fora = [m for m in movimentos if m["data"] < abertura]
    if fora:
        avisos.append(
            f"{len(fora)} movimento(s) anterior(es) à abertura da sucessão em {fmt_data(abertura)} "
            "foram excluídos do fluxo do espólio (pertencem ao autor da herança em vida); listados em excecoes.fora_do_periodo"
        )
    dentro = [m for m in movimentos if m["data"] >= abertura]
    if data_referencia:
        depois = [m for m in dentro if m["data"] > data_referencia]
        if depois:
            avisos.append(
                f"{len(depois)} movimento(s) posterior(es) à data de referência {fmt_data(data_referencia)} excluídos"
            )
        dentro = [m for m in dentro if m["data"] <= data_referencia]
    if not dentro:
        raise ValueError("nenhum movimento dentro do período auditado")

    dentro.sort(key=lambda m: (m["data"], m["linha"]))
    memoria.append(f"Período auditado: {fmt_data(abertura)} a {fmt_data(dentro[-1]['data'] if not data_referencia else data_referencia)}; {len(dentro)} movimentos considerados, {len(fora)} excluídos por data.")

    # Saldo corrente movimento a movimento
    saldo = saldo_inicial
    for m in dentro:
        saldo = saldo + m["valor"] if m["tipo"] == "C" else saldo - m["valor"]
        m["saldo_apos"] = saldo
    saldo_final = saldo
    memoria.append(f"Saldo inicial informado: {fmt_br(saldo_inicial)}; saldo final reconstruído: {fmt_br(saldo_final)}.")

    # DFC mensal
    meses = OrderedDict()
    for m in dentro:
        chave = m["data"].strftime("%m/%Y")
        bloco = meses.setdefault(chave, {
            "entradas": defaultdict(lambda: ZERO), "saidas": defaultdict(lambda: ZERO),
            "total_entradas": ZERO, "total_saidas": ZERO, "saldo_final": ZERO,
        })
        if m["tipo"] == "C":
            bloco["entradas"][m["categoria"]] += m["valor"]
            bloco["total_entradas"] += m["valor"]
        else:
            bloco["saidas"][m["categoria"]] += m["valor"]
            bloco["total_saidas"] += m["valor"]
        bloco["saldo_final"] = m["saldo_apos"]

    dfc = []
    acumulado = saldo_inicial
    soma_variacoes = ZERO
    for chave, bloco in meses.items():
        variacao = bloco["total_entradas"] - bloco["total_saidas"]
        soma_variacoes += variacao
        saldo_ini_mes = acumulado
        acumulado = acumulado + variacao
        if acumulado != bloco["saldo_final"]:
            raise ValueError(
                f"sanidade: saldo acumulado do mês {chave} ({acumulado}) difere do saldo corrente ({bloco['saldo_final']})"
            )
        dfc.append(OrderedDict([
            ("mes", chave),
            ("saldo_inicial", s2(saldo_ini_mes)),
            ("entradas", OrderedDict((k, s2(v)) for k, v in sorted(bloco["entradas"].items()))),
            ("total_entradas", s2(bloco["total_entradas"])),
            ("saidas", OrderedDict((k, s2(v)) for k, v in sorted(bloco["saidas"].items()))),
            ("total_saidas", s2(bloco["total_saidas"])),
            ("variacao", s2(variacao)),
            ("saldo_final", s2(acumulado)),
        ]))

    total_entradas = sum((m["valor"] for m in dentro if m["tipo"] == "C"), ZERO)
    total_saidas = sum((m["valor"] for m in dentro if m["tipo"] == "D"), ZERO)
    variacao_total = saldo_final - saldo_inicial

    # Sanidade 1: entradas menos saídas = variação de saldo
    if total_entradas - total_saidas != variacao_total:
        raise ValueError(
            f"sanidade: entradas ({total_entradas}) menos saídas ({total_saidas}) "
            f"difere da variação de saldo ({variacao_total})"
        )
    # Sanidade 2: soma das variações mensais = variação total
    if soma_variacoes != variacao_total:
        raise ValueError("sanidade: soma das variações mensais difere da variação total")
    memoria.append(
        f"Teste: entradas {fmt_br(total_entradas)} menos saídas {fmt_br(total_saidas)} = "
        f"variação {fmt_br(variacao_total)} = saldo final menos saldo inicial. Fechou."
    )

    # Totais por categoria, conta e vínculo
    por_categoria = {"entradas": defaultdict(lambda: ZERO), "saidas": defaultdict(lambda: ZERO)}
    por_conta = defaultdict(lambda: {"entradas": ZERO, "saidas": ZERO, "movimentos": 0})
    por_vinculo = {"entradas": defaultdict(lambda: ZERO), "saidas": defaultdict(lambda: ZERO)}
    for m in dentro:
        lado = "entradas" if m["tipo"] == "C" else "saidas"
        por_categoria[lado][m["categoria"]] += m["valor"]
        por_conta[m["conta"]][lado] += m["valor"]
        por_conta[m["conta"]]["movimentos"] += 1
        por_vinculo[lado][m["vinculo"] or "nao_informado"] += m["valor"]
    # Sanidade 3: soma das categorias = totais
    if sum(por_categoria["entradas"].values(), ZERO) != total_entradas or \
            sum(por_categoria["saidas"].values(), ZERO) != total_saidas:
        raise ValueError("sanidade: soma por categoria difere dos totais")

    transf_c = por_categoria["entradas"].get("transferencia_interna", ZERO)
    transf_d = por_categoria["saidas"].get("transferencia_interna", ZERO)
    if transf_c != transf_d:
        avisos.append(
            f"transferências internas não fecham: saídas {fmt_br(transf_d)} x entradas {fmt_br(transf_c)}; "
            "diferença aponta conta fora do perímetro ou classificação errada"
        )
    entradas_operacionais = total_entradas - transf_c
    saidas_operacionais = total_saidas - transf_d

    # Exceções
    exc = OrderedDict()
    exc["fora_do_periodo"] = [resumo_mov(m, "anterior à abertura da sucessão") for m in fora]
    exc["saidas_sem_autorizacao_nao_rotineiras"] = [
        resumo_mov(m, "saída sem autorização judicial fora das despesas de conservação (CPC, art. 619)")
        for m in dentro if m["tipo"] == "D" and m["autorizacao"] == "N"
        and m["categoria"] not in CATEGORIAS_CONSERVACAO and m["categoria"] != "transferencia_interna"
    ]
    exc["saidas_conservacao_sem_autorizacao"] = [
        resumo_mov(m, "despesa de conservação sem alvará prévio (CPC, art. 619, IV): conferir ratificação na prestação de contas")
        for m in dentro if m["tipo"] == "D" and m["autorizacao"] == "N" and m["categoria"] in CATEGORIAS_CONSERVACAO
    ]
    exc["atos_com_alvara_obrigatorio_sem_autorizacao"] = [
        resumo_mov(m, "alienação ou pagamento de dívida sem alvará (CPC, art. 619, I e III)")
        for m in dentro if m["categoria"] in CATEGORIAS_ALVARA_OBRIGATORIO and m["autorizacao"] == "N"
    ]
    exc["saidas_sem_documento"] = [
        resumo_mov(m, "saída sem lastro documental") for m in dentro if m["tipo"] == "D" and not m["documento"]
    ]
    exc["saidas_a_herdeiro_ou_inventariante"] = [
        resumo_mov(m, "saída em favor de herdeiro ou inventariante: adiantamento de quinhão, reembolso ou desvio, conforme prova")
        for m in dentro if m["tipo"] == "D" and m["vinculo"] in {"herdeiro", "inventariante"}
        and m["categoria"] != "transferencia_interna"
    ]
    exc["despesas_pessoais"] = [
        resumo_mov(m, "despesa estranha ao espólio (desvio de finalidade): recompor ao acervo (CC, art. 2.020)")
        for m in dentro if m["tipo"] == "D" and m["categoria"] == "despesa_pessoal"
    ]
    exc["despesas_imovel_ocupado_por_herdeiro"] = [
        resumo_mov(m, "encargo de imóvel de uso exclusivo de herdeiro pago pelo espólio (REsp 1.704.528): a cargo do ocupante")
        for m in dentro if m["tipo"] == "D" and m["imovel_id"] and m["imovel_id"] in imoveis_ocupados
    ]

    beneficiarios = defaultdict(lambda: ZERO)
    for m in dentro:
        if m["tipo"] == "D" and m["vinculo"] in {"herdeiro", "inventariante"} and m["categoria"] != "transferencia_interna":
            beneficiarios[f"{m['beneficiario']} ({m['vinculo']})"] += m["valor"]

    totais_exc = OrderedDict((k, s2(totalizar(v))) for k, v in exc.items())
    memoria.append(
        "Exceções: " + "; ".join(f"{k}: {len(v)} item(ns), {fmt_br(totalizar(v))}" for k, v in exc.items())
    )

    # Recomposição sugerida (sem dupla contagem): despesas pessoais + saídas a herdeiro/inventariante
    # sem autorização + encargos do imóvel ocupado. Um mesmo movimento entra uma única vez.
    vistos = set()
    recompor = ZERO
    for chave in ("despesas_pessoais", "saidas_a_herdeiro_ou_inventariante", "despesas_imovel_ocupado_por_herdeiro"):
        for item in exc[chave]:
            if chave == "saidas_a_herdeiro_ou_inventariante" and item["autorizacao_judicial"] == "S":
                continue
            if item["linha_csv"] not in vistos:
                vistos.add(item["linha_csv"])
                recompor += Decimal(item["valor"])
    memoria.append(
        f"Recomposição sugerida ao acervo, sem atualização e sem dupla contagem: {fmt_br(recompor)} "
        "(despesas pessoais + saídas a herdeiro ou inventariante sem alvará + encargos de imóvel ocupado)."
    )

    resultado = OrderedDict()
    resultado["periodo"] = OrderedDict([
        ("abertura_sucessao", fmt_data(abertura)),
        ("primeiro_movimento", fmt_data(dentro[0]["data"])),
        ("ultimo_movimento", fmt_data(dentro[-1]["data"])),
        ("data_referencia", fmt_data(data_referencia) if data_referencia else fmt_data(dentro[-1]["data"])),
        ("movimentos_considerados", len(dentro)),
        ("movimentos_excluidos_por_data", len(fora)),
    ])
    resultado["totais"] = OrderedDict([
        ("saldo_inicial", s2(saldo_inicial)),
        ("total_entradas", s2(total_entradas)),
        ("total_saidas", s2(total_saidas)),
        ("variacao_saldo", s2(variacao_total)),
        ("saldo_final", s2(saldo_final)),
        ("entradas_sem_transferencias_internas", s2(entradas_operacionais)),
        ("saidas_sem_transferencias_internas", s2(saidas_operacionais)),
        ("recomposicao_sugerida_sem_atualizacao", s2(recompor)),
    ])
    resultado["dfc_mensal"] = dfc
    resultado["por_categoria"] = OrderedDict([
        ("entradas", OrderedDict((k, s2(v)) for k, v in sorted(por_categoria["entradas"].items()))),
        ("saidas", OrderedDict((k, s2(v)) for k, v in sorted(por_categoria["saidas"].items()))),
    ])
    resultado["por_conta"] = OrderedDict(
        (c, OrderedDict([("entradas", s2(v["entradas"])), ("saidas", s2(v["saidas"])),
                         ("liquido", s2(v["entradas"] - v["saidas"])), ("movimentos", v["movimentos"])]))
        for c, v in por_conta.items()
    )
    resultado["por_vinculo_beneficiario"] = OrderedDict([
        ("entradas", OrderedDict((k, s2(v)) for k, v in sorted(por_vinculo["entradas"].items()))),
        ("saidas", OrderedDict((k, s2(v)) for k, v in sorted(por_vinculo["saidas"].items()))),
    ])
    resultado["saidas_por_herdeiro_ou_inventariante"] = OrderedDict(
        (k, s2(v)) for k, v in sorted(beneficiarios.items(), key=lambda kv: -kv[1])
    )
    resultado["excecoes_totais"] = totais_exc
    resultado["excecoes"] = exc
    resultado["avisos"] = avisos
    resultado["memoria"] = memoria
    resultado["_dentro"] = dentro
    return resultado


def escrever_csv(resultado, caminho):
    """DFC mensal em formato largo: uma coluna por categoria presente."""
    dfc = resultado["dfc_mensal"]
    cats_e = sorted({c for l in dfc for c in l["entradas"]})
    cats_s = sorted({c for l in dfc for c in l["saidas"]})
    cab = ["mes", "saldo_inicial"] + [f"entrada_{c}" for c in cats_e] + ["total_entradas"] + \
          [f"saida_{c}" for c in cats_s] + ["total_saidas", "variacao", "saldo_final"]
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cab)
        for l in dfc:
            w.writerow([l["mes"], l["saldo_inicial"]] + [l["entradas"].get(c, "0.00") for c in cats_e] +
                       [l["total_entradas"]] + [l["saidas"].get(c, "0.00") for c in cats_s] +
                       [l["total_saidas"], l["variacao"], l["saldo_final"]])


def escrever_md(resultado, caminho):
    """Tabelas em Markdown prontas para o laudo (valores em padrão brasileiro)."""
    t = resultado["totais"]
    linhas = ["## Fluxo de caixa do espólio (DFC mensal)", ""]
    linhas.append(f"Período: {resultado['periodo']['abertura_sucessao']} a {resultado['periodo']['data_referencia']}. "
                  f"Saldo inicial {fmt_br(t['saldo_inicial'])}; saldo final {fmt_br(t['saldo_final'])}.")
    linhas += ["", "| Mês | Saldo inicial | Entradas | Saídas | Variação | Saldo final |", "|---|---:|---:|---:|---:|---:|"]
    for l in resultado["dfc_mensal"]:
        linhas.append(f"| {l['mes']} | {fmt_br(l['saldo_inicial'])} | {fmt_br(l['total_entradas'])} | "
                      f"{fmt_br(l['total_saidas'])} | {fmt_br(l['variacao'])} | {fmt_br(l['saldo_final'])} |")
    linhas.append(f"| Total | {fmt_br(t['saldo_inicial'])} | {fmt_br(t['total_entradas'])} | {fmt_br(t['total_saidas'])} | "
                  f"{fmt_br(t['variacao_saldo'])} | {fmt_br(t['saldo_final'])} |")
    linhas += ["", "## Totais por categoria", "", "| Fluxo | Categoria | Valor |", "|---|---|---:|"]
    for lado in ("entradas", "saidas"):
        for c, v in resultado["por_categoria"][lado].items():
            linhas.append(f"| {lado} | {c} | {fmt_br(v)} |")
    linhas += ["", "## Exceções", ""]
    for chave, itens in resultado["excecoes"].items():
        linhas.append(f"### {chave.replace('_', ' ')} ({len(itens)} item(ns), {fmt_br(resultado['excecoes_totais'][chave])})")
        linhas.append("")
        if not itens:
            linhas += ["Nenhum item.", ""]
            continue
        linhas += ["| Data | Conta | Histórico | Valor | Beneficiário | Vínculo | Alvará | Documento |", "|---|---|---|---:|---|---|---|---|"]
        for i in itens:
            linhas.append(f"| {i['data']} | {i['conta']} | {i['historico']} | {i['valor_br']} | {i['beneficiario']} | "
                          f"{i['vinculo_beneficiario']} | {i['autorizacao_judicial']} | {i['documento']} |")
        linhas.append("")
    linhas += ["## Memória de cálculo", ""] + [f"- {m}" for m in resultado["memoria"]]
    if resultado["avisos"]:
        linhas += ["", "## Avisos", ""] + [f"- {a}" for a in resultado["avisos"]]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Fluxo de caixa do espólio por conta, mês e categoria, com listas de exceção (skill auditoria-contabil-espolio)."
    )
    parser.add_argument("--movimentos", required=True, help="CSV de movimentos (separador ponto e vírgula), ver docstring")
    parser.add_argument("--abertura-sucessao", required=True, help="Data do óbito (dd/mm/aaaa); movimentos anteriores são excluídos")
    parser.add_argument("--data-referencia", help="Data final do período auditado (dd/mm/aaaa); padrão: último movimento")
    parser.add_argument("--saldo-inicial", default="0", help="Saldo das contas na abertura da sucessão (padrão 0)")
    parser.add_argument("--saldo-final-extrato", help="Saldo final somado dos extratos, para conciliação; divergência gera erro")
    parser.add_argument("--imoveis-ocupados", default="", help="Ids de imóveis ocupados com exclusividade por herdeiro, separados por vírgula (ex.: IM02,IM05)")
    parser.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--csv", help="Grava a DFC mensal em CSV (formato largo)")
    parser.add_argument("--md", help="Grava tabelas em Markdown para o laudo")
    args = parser.parse_args()

    try:
        abertura = parse_data(args.abertura_sucessao, "abertura da sucessão")
        data_ref = parse_data(args.data_referencia, "data de referência") if args.data_referencia else None
        if data_ref and data_ref < abertura:
            raise ValueError("data de referência anterior à abertura da sucessão")
        saldo_inicial = parse_num(args.saldo_inicial)
        ocupados = {x.strip() for x in args.imoveis_ocupados.split(",") if x.strip()}
        movimentos, avisos_leitura = ler_movimentos(args.movimentos)
        resultado = processar(movimentos, abertura, saldo_inicial, ocupados, data_ref)
        resultado["avisos"] = avisos_leitura + resultado["avisos"]

        conciliacao = OrderedDict([("saldo_final_extrato", None), ("saldo_final_reconstruido", resultado["totais"]["saldo_final"]), ("fechou", None)])
        if args.saldo_final_extrato:
            extrato = parse_num(args.saldo_final_extrato)
            reconstruido = Decimal(resultado["totais"]["saldo_final"])
            conciliacao["saldo_final_extrato"] = s2(extrato)
            conciliacao["fechou"] = q2(extrato) == reconstruido
            if not conciliacao["fechou"]:
                raise ValueError(
                    f"conciliação não fecha: saldo do extrato {fmt_br(extrato)} x reconstruído {fmt_br(reconstruido)}; "
                    f"diferença {fmt_br(extrato - reconstruido)} indica movimento faltante ou conta fora do perímetro"
                )
            resultado["memoria"].append(f"Conciliação com o extrato: saldo final {fmt_br(extrato)} confere.")

        saida = OrderedDict()
        saida["skill"] = "auditoria-contabil-espolio"
        saida["script"] = "fluxo_caixa_espolio.py"
        saida["premissas"] = OrderedDict([
            ("arquivo_movimentos", str(args.movimentos)),
            ("abertura_sucessao", fmt_data(abertura)),
            ("data_referencia", fmt_data(data_ref) if data_ref else "último movimento"),
            ("saldo_inicial", s2(saldo_inicial)),
            ("imoveis_ocupados_por_herdeiro", sorted(ocupados)),
            ("criterio_periodo", "movimentos anteriores à abertura da sucessão excluídos (CC, art. 1.784)"),
            ("criterio_autorizacao", "vazio equivale a N; conservação (CPC, art. 619, IV) listada em separado das demais saídas"),
            ("criterio_documento", "vazio equivale a sem lastro documental"),
            ("criterio_moeda", "só BRL; movimento em moeda estrangeira entra convertido por conversao_ptax.py, com a cotação rastreada na coluna conversao"),
            ("categorias_entrada", sorted(CATEGORIAS_ENTRADA)),
            ("categorias_saida", sorted(CATEGORIAS_SAIDA)),
        ])
        saida["locale"] = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
        saida["arredondamento"] = "ROUND_HALF_UP, 2 casas na apresentação"
        saida["conciliacao"] = conciliacao
        for chave in ("periodo", "totais", "dfc_mensal", "por_categoria", "por_conta",
                      "por_vinculo_beneficiario", "saidas_por_herdeiro_ou_inventariante",
                      "excecoes_totais", "excecoes", "avisos"):
            saida[chave] = resultado[chave]
        saida["sanidade"] = OrderedDict([
            ("entradas_menos_saidas_igual_variacao_saldo", True),
            ("soma_variacoes_mensais_igual_variacao_total", True),
            ("soma_categorias_igual_totais", True),
            ("transferencias_internas_fecham", Decimal(resultado["por_categoria"]["entradas"].get("transferencia_interna", "0")) ==
             Decimal(resultado["por_categoria"]["saidas"].get("transferencia_interna", "0"))),
        ])
        saida["memoria"] = resultado["memoria"]

        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto, encoding="utf-8")
            print(f"JSON gravado em {args.saida}")
        else:
            print(texto)
        if args.csv:
            escrever_csv(resultado, args.csv)
            print(f"CSV gravado em {args.csv}")
        if args.md:
            escrever_md(resultado, args.md)
            print(f"Markdown gravado em {args.md}")
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
