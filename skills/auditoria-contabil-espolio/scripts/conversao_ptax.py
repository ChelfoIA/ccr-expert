#!/usr/bin/env python3
"""
Conversão de movimentos em moeda estrangeira (euro, por padrão) para reais pela PTAX da data,
lida de arquivo com fonte declarada: cotação do dia; se não houver, a do dia útil anterior
disponível no arquivo, declarando a defasagem. O script nunca estima cotação e não acessa a rede.

Parte da skill: auditoria-contabil-espolio

Uso:
    python3 scripts/conversao_ptax.py --ptax assets/exemplo_ptax_eur.csv \
        --movimentos assets/exemplo_movimentos_eur.csv --criterio venda \
        --saida ptax.json --csv movimentos_brl.csv --md ptax.md

    O CSV gravado por --csv mantém todas as colunas de entrada, troca "valor" pelo valor em
    reais (2 casas) e "moeda" por BRL, e acrescenta valor_original, moeda_original, cotacao,
    data_cotacao, criterio_cotacao e defasagem_dias. Serve de entrada para
    scripts/fluxo_caixa_espolio.py e para a coluna de recebimentos de rendimentos_imoveis.py.

Entrada --ptax (CSV, ponto e vírgula, cabeçalho): data;compra;venda;fonte
    data    dd/mm/aaaa, um registro por dia útil
    compra  cotação de compra (ex.: 5,3701)
    venda   cotação de venda (ex.: 5,3717)
    fonte   obrigatória: série e código do SGS do BCB e data da consulta. O arquivo dos assets
            é fictício e está marcado como tal; o script avisa quando encontra a marca.
    Onde obter: www3.bcb.gov.br/sgspub (série PTAX da moeda, código [A VERIFICAR]) ou
    www.bcb.gov.br/estabilidadefinanceira/historicocotacoes.

Entrada --movimentos (CSV, ponto e vírgula, cabeçalho): exige data e valor; a coluna moeda é
    opcional (vazio equivale à moeda de --moeda); BRL passa sem conversão; as demais colunas
    (conta, historico, tipo, categoria etc.) são preservadas na saída.

Saída: JSON com premissas, movimentos convertidos (cotação usada, data da cotação, defasagem),
totais por moeda, por mês e por tipo, testes de sanidade e memória de cálculo. Todo valor em
Decimal; arredondamento ROUND_HALF_UP só na apresentação.
"""

import argparse
import csv
import json
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

CRITERIOS = {"venda", "compra", "media"}
CENTAVOS = Decimal("0.01")
QUATRO_CASAS = Decimal("0.0001")
ZERO = Decimal("0")
DOIS = Decimal("2")
TOLERANCIA = Decimal("0.000000001")
# Faixa de plausibilidade da cotação de uma moeda forte em reais; fora dela o script avisa.
FAIXA_PLAUSIVEL = (Decimal("0.5"), Decimal("50"))
MARCA_FICTICIA = "exemplo fict"
COLUNAS_EXTRA = ["valor_original", "moeda_original", "cotacao", "data_cotacao", "criterio_cotacao", "defasagem_dias"]


def q2(valor):
    """Arredonda para 2 casas, ROUND_HALF_UP, só na apresentação."""
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


def fmt_cotacao(c):
    """Cotação com 4 casas e vírgula decimal: 5,3717."""
    return str(Decimal(c).quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)).replace(".", ",")


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
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(f"{campo} inválida (esperado dd/mm/aaaa): {texto!r}") from exc


def fmt_data(d):
    return d.strftime("%d/%m/%Y")


def ler_ptax(caminho):
    """Lê a série de cotações. Devolve (tabela por data, fontes distintas, série fictícia?, avisos)."""
    tabela = {}
    fontes = []
    avisos = []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        faltam = {"data", "compra", "venda", "fonte"} - set(leitor.fieldnames or [])
        if faltam:
            raise ValueError(f"colunas obrigatórias ausentes em --ptax: {sorted(faltam)}")
        for n, l in enumerate(leitor, start=2):
            if not any((v or "").strip() for v in l.values()):
                continue
            d = parse_data(l.get("data"), f"ptax, linha {n}: data")
            if d in tabela:
                raise ValueError(f"ptax, linha {n}: data {fmt_data(d)} repetida na série")
            compra = parse_num(l.get("compra"))
            venda = parse_num(l.get("venda"))
            if compra <= ZERO or venda <= ZERO:
                raise ValueError(f"ptax, linha {n}: cotação deve ser positiva (compra {compra}, venda {venda})")
            if venda < compra:
                avisos.append(f"ptax {fmt_data(d)}: venda ({fmt_cotacao(venda)}) menor que compra ({fmt_cotacao(compra)}); conferir a série")
            fonte = (l.get("fonte") or "").strip()
            if not fonte:
                raise ValueError(
                    f"ptax, linha {n}: cotação de {fmt_data(d)} sem fonte declarada; "
                    "informar série, código do SGS do BCB e data da consulta"
                )
            if fonte not in fontes:
                fontes.append(fonte)
            tabela[d] = {"compra": compra, "venda": venda, "fonte": fonte, "linha": n}
    if not tabela:
        raise ValueError("nenhuma cotação válida em --ptax")
    ficticia = any(MARCA_FICTICIA in f.lower() for f in fontes)
    if ficticia:
        avisos.append(
            "a série PTAX informada está marcada como EXEMPLO FICTÍCIO: substituir pela série oficial do BCB "
            "antes de levar qualquer valor ao laudo"
        )
    return tabela, fontes, ficticia, avisos


def cotacao_para(tabela, d, max_defasagem):
    """Cotação do dia; se não houver, a do dia anterior mais próximo no arquivo, até max_defasagem dias."""
    for k in range(0, max_defasagem + 1):
        dd = d - timedelta(days=k)
        if dd in tabela:
            return dd, tabela[dd], k
    raise ValueError(
        f"sem cotação em {fmt_data(d)} nem nos {max_defasagem} dias anteriores no arquivo --ptax; "
        "obter a série oficial do BCB para o período (o script nunca estima cotação)"
    )


def taxa(registro, criterio):
    if criterio == "venda":
        return registro["venda"]
    if criterio == "compra":
        return registro["compra"]
    return (registro["compra"] + registro["venda"]) / DOIS


def ler_movimentos(caminho, moeda_padrao):
    """Devolve (lista de colunas originais, lista de movimentos)."""
    linhas = []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        campos = list(leitor.fieldnames or [])
        faltam = {"data", "valor"} - set(campos)
        if faltam:
            raise ValueError(f"colunas obrigatórias ausentes em --movimentos: {sorted(faltam)}")
        for n, l in enumerate(leitor, start=2):
            if not any((v or "").strip() for v in l.values()):
                continue
            d = parse_data(l.get("data"), f"movimentos, linha {n}: data")
            v = parse_num(l.get("valor"))
            if v <= ZERO:
                raise ValueError(f"movimentos, linha {n}: valor deve ser positivo; o sentido vai na coluna tipo (C ou D)")
            moeda = (l.get("moeda") or "").strip().upper() or moeda_padrao
            linhas.append({"linha": n, "data": d, "valor": v, "moeda": moeda, "original": dict(l)})
    if not linhas:
        raise ValueError("nenhum movimento válido em --movimentos")
    return campos, linhas


def converter(linhas, tabela, moeda, criterio, max_defasagem):
    """Converte cada movimento. Devolve (movimentos convertidos, totais, avisos, memória)."""
    avisos = []
    memoria = []
    convertidos = []
    total_original = defaultdict(lambda: ZERO)
    total_brl_exato = ZERO
    total_brl_2casas = ZERO
    por_mes = defaultdict(lambda: ZERO)
    por_tipo = defaultdict(lambda: ZERO)
    convertidos_n = 0
    passados_n = 0
    for m in linhas:
        hist = (m["original"].get("historico") or "").strip()
        if m["moeda"] == "BRL":
            valor_brl = m["valor"]
            data_cot = None
            cot = None
            defas = None
            nota = "já em reais: sem conversão"
            passados_n += 1
            memoria.append(f"{fmt_data(m['data'])}: {fmt_moeda(m['valor'])} já em reais ({hist}).")
        elif m["moeda"] == moeda:
            data_cot, registro, defas = cotacao_para(tabela, m["data"], max_defasagem)
            cot = taxa(registro, criterio)
            valor_brl = m["valor"] * cot
            # Sanidade reversa: dividir o convertido pela cotação devolve o valor original.
            if abs(valor_brl / cot - m["valor"]) > TOLERANCIA:
                raise ValueError(f"sanidade: conversão não reversível na linha {m['linha']}")
            if not (FAIXA_PLAUSIVEL[0] <= cot <= FAIXA_PLAUSIVEL[1]):
                avisos.append(
                    f"cotação {fmt_cotacao(cot)} de {fmt_data(data_cot)} fora da faixa de plausibilidade "
                    f"({fmt_cotacao(FAIXA_PLAUSIVEL[0])} a {fmt_cotacao(FAIXA_PLAUSIVEL[1])}); conferir a série"
                )
            if defas == 0:
                nota = "cotação do dia"
            else:
                nota = (f"sem cotação em {fmt_data(m['data'])} no arquivo: usada a do dia útil anterior disponível "
                        f"({fmt_data(data_cot)}), defasagem de {defas} dia(s)")
                if defas > 3:
                    avisos.append(f"linha {m['linha']}: defasagem de {defas} dias na cotação; conferir se a série está completa")
            convertidos_n += 1
            memoria.append(
                f"{fmt_data(m['data'])}: {fmt_moeda(m['valor'], moeda)} x {fmt_cotacao(cot)} "
                f"({criterio}, PTAX de {fmt_data(data_cot)}) = {fmt_moeda(valor_brl)} ({hist})."
            )
        else:
            raise ValueError(
                f"movimentos, linha {m['linha']}: moeda {m['moeda']} não é BRL nem {moeda}; "
                "rodar o script uma vez por moeda, com a série PTAX correspondente"
            )
        total_original[m["moeda"]] += m["valor"]
        total_brl_exato += valor_brl
        total_brl_2casas += q2(valor_brl)
        por_mes[m["data"].strftime("%m/%Y")] += valor_brl
        tipo = (m["original"].get("tipo") or "").strip().upper()
        por_tipo[tipo if tipo in {"C", "D"} else "nao_informado"] += valor_brl
        convertidos.append(OrderedDict([
            ("linha_csv", m["linha"]),
            ("data", fmt_data(m["data"])),
            ("historico", hist),
            ("tipo", tipo),
            ("valor_original", s2(m["valor"])),
            ("moeda_original", m["moeda"]),
            ("data_cotacao", fmt_data(data_cot) if data_cot else None),
            ("cotacao", fmt_cotacao(cot) if cot is not None else None),
            ("criterio_cotacao", criterio if cot is not None else None),
            ("defasagem_dias", defas),
            ("valor_brl", s2(valor_brl)),
            ("valor_brl_exato", str(valor_brl)),
            ("valor_brl_formatado", fmt_moeda(valor_brl)),
            ("nota", nota),
        ]))

    # Sanidade: soma por mês fecha com o total convertido.
    soma_meses = sum(por_mes.values(), ZERO)
    if soma_meses != total_brl_exato:
        raise ValueError(f"sanidade: soma por mês ({soma_meses}) difere do total convertido ({total_brl_exato})")
    # Sanidade: soma por tipo fecha com o total.
    if sum(por_tipo.values(), ZERO) != total_brl_exato:
        raise ValueError("sanidade: soma por tipo difere do total convertido")

    totais = OrderedDict()
    totais["movimentos_convertidos"] = convertidos_n
    totais["movimentos_ja_em_reais"] = passados_n
    totais["total_por_moeda_original"] = OrderedDict((k, s2(v)) for k, v in sorted(total_original.items()))
    totais["total_brl_exato"] = str(total_brl_exato)
    totais["total_brl"] = s2(total_brl_exato)
    totais["soma_das_linhas_a_2_casas"] = s2(total_brl_2casas)
    totais["diferenca_de_arredondamento"] = s2(total_brl_2casas - q2(total_brl_exato))
    totais["por_mes_brl"] = OrderedDict(
        (k, s2(v)) for k, v in sorted(por_mes.items(), key=lambda kv: (kv[0][3:], kv[0][:2]))
    )
    totais["por_tipo_brl"] = OrderedDict((k, s2(v)) for k, v in sorted(por_tipo.items()))
    memoria.append(
        f"Total convertido: {fmt_moeda(total_brl_exato)} ({convertidos_n} movimento(s) convertido(s), "
        f"{passados_n} já em reais); soma por mês e por tipo conferem. Soma das linhas a 2 casas "
        f"{fmt_moeda(total_brl_2casas)} (diferença de arredondamento {fmt_moeda(total_brl_2casas - q2(total_brl_exato))})."
    )
    return convertidos, totais, avisos, memoria


def escrever_csv(campos, linhas, convertidos, caminho):
    """Mesmas colunas de entrada, com valor em BRL e colunas de rastreabilidade da conversão."""
    cab = list(campos)
    if "moeda" not in cab:
        cab.append("moeda")
    cab += [c for c in COLUNAS_EXTRA if c not in cab]
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cab)
        for m, c in zip(linhas, convertidos):
            linha = dict(m["original"])
            linha["valor"] = c["valor_brl"]
            linha["moeda"] = "BRL"
            linha["valor_original"] = c["valor_original"]
            linha["moeda_original"] = c["moeda_original"]
            linha["cotacao"] = c["cotacao"] or ""
            linha["data_cotacao"] = c["data_cotacao"] or ""
            linha["criterio_cotacao"] = c["criterio_cotacao"] or ""
            linha["defasagem_dias"] = "" if c["defasagem_dias"] is None else c["defasagem_dias"]
            w.writerow([linha.get(k, "") if linha.get(k) is not None else "" for k in cab])


def escrever_md(saida, caminho):
    p = saida["premissas"]
    linhas = ["## Conversão de movimentos em moeda estrangeira pela PTAX", ""]
    linhas.append(
        f"Moeda {p['moeda']}; critério {p['criterio']}; sem cotação no dia, a do dia útil anterior disponível "
        f"(defasagem máxima {p['max_defasagem_dias']} dias). Fonte da série: {'; '.join(p['fontes_declaradas'])}."
    )
    if p["serie_ficticia"]:
        linhas.append("")
        linhas.append("Atenção: a série usada é um exemplo fictício e precisa ser substituída pela série oficial do BCB.")
    linhas += ["", "| Data | Histórico | Tipo | Valor original | Cotação (data, critério) | Em reais | Nota |",
               "|---|---|---|---:|---|---:|---|"]
    for c in saida["movimentos"]:
        cot = f"{c['cotacao']} ({c['data_cotacao']}, {c['criterio_cotacao']})" if c["cotacao"] else "1,0000 (BRL)"
        linhas.append(
            f"| {c['data']} | {c['historico']} | {c['tipo']} | {fmt_moeda(c['valor_original'], c['moeda_original'])} | "
            f"{cot} | {c['valor_brl_formatado']} | {c['nota']} |"
        )
    t = saida["totais"]
    linhas.append(f"| Total | | | | | {fmt_moeda(t['total_brl'])} | |")
    linhas += ["", "## Totais por mês (em reais)", "", "| Mês | Valor |", "|---|---:|"]
    for mes, v in t["por_mes_brl"].items():
        linhas.append(f"| {mes} | {fmt_moeda(v)} |")
    linhas += ["", "## Memória de cálculo", ""] + [f"- {x}" for x in saida["memoria"]]
    if saida["avisos"]:
        linhas += ["", "## Avisos", ""] + [f"- {a}" for a in saida["avisos"]]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Converte movimentos em moeda estrangeira para reais pela PTAX da data, lida de arquivo (skill auditoria-contabil-espolio)."
    )
    parser.add_argument("--ptax", required=True, help="CSV da série PTAX: data;compra;venda;fonte (fonte obrigatória)")
    parser.add_argument("--movimentos", required=True, help="CSV de movimentos com data, valor e, opcionalmente, moeda; demais colunas preservadas")
    parser.add_argument("--moeda", default="EUR", help="Código da moeda da série e dos movimentos a converter (padrão EUR)")
    parser.add_argument("--criterio", default="venda", choices=sorted(CRITERIOS), help="Cotação a usar: venda (padrão), compra ou media")
    parser.add_argument("--max-defasagem", type=int, default=5, help="Dias para trás admitidos na busca da cotação anterior (padrão 5); além disso o script falha")
    parser.add_argument("--online", action="store_true", help="Reservado: a busca na API do SGS do BCB não está implementada; com a flag o script falha com mensagem clara e nunca estima cotação")
    parser.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--csv", help="Grava os movimentos convertidos em CSV, prontos para fluxo_caixa_espolio.py")
    parser.add_argument("--md", help="Grava a tabela de conversão em Markdown para o laudo")
    args = parser.parse_args()

    try:
        if args.online:
            raise ValueError(
                "busca online indisponível: baixar a série PTAX no SGS do BCB (www3.bcb.gov.br/sgspub) "
                "e informar por --ptax com a coluna fonte preenchida; cotação nunca é estimada"
            )
        if args.max_defasagem < 0:
            raise ValueError("--max-defasagem deve ser zero ou positivo")
        moeda = args.moeda.strip().upper()
        if moeda == "BRL":
            raise ValueError("--moeda deve ser a moeda estrangeira da série (ex.: EUR), não BRL")
        tabela, fontes, ficticia, avisos = ler_ptax(args.ptax)
        campos, linhas = ler_movimentos(args.movimentos, moeda)
        convertidos, totais, avisos_conv, memoria = converter(linhas, tabela, moeda, args.criterio, args.max_defasagem)
        avisos += avisos_conv
        datas = sorted(tabela)

        saida = OrderedDict()
        saida["skill"] = "auditoria-contabil-espolio"
        saida["script"] = "conversao_ptax.py"
        saida["premissas"] = OrderedDict([
            ("arquivo_ptax", str(args.ptax)),
            ("arquivo_movimentos", str(args.movimentos)),
            ("moeda", moeda),
            ("criterio", args.criterio),
            ("regra_sem_cotacao_no_dia", "usar a cotação do dia útil anterior disponível no arquivo, declarando a defasagem"),
            ("max_defasagem_dias", args.max_defasagem),
            ("serie_periodo", f"{fmt_data(datas[0])} a {fmt_data(datas[-1])}, {len(datas)} cotações"),
            ("fontes_declaradas", fontes),
            ("serie_ficticia", ficticia),
            ("origem_da_serie", "arquivo local; sem rede; busca online não implementada; nenhuma cotação estimada"),
            ("atualizacao_monetaria", "não aplicada; usar a skill atualizacao-monetaria sobre os valores em reais"),
        ])
        saida["locale"] = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
        saida["arredondamento"] = "ROUND_HALF_UP, 2 casas na apresentação"
        saida["movimentos"] = convertidos
        saida["totais"] = totais
        saida["sanidade"] = OrderedDict([
            ("conversao_reversivel_em_cada_linha", True),
            ("soma_por_mes_igual_total", True),
            ("soma_por_tipo_igual_total", True),
            ("cotacoes_estimadas", 0),
            ("toda_cotacao_tem_fonte", True),
        ])
        saida["avisos"] = avisos
        saida["memoria"] = memoria

        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto, encoding="utf-8")
            print(f"JSON gravado em {args.saida}")
        else:
            print(texto)
        if args.csv:
            escrever_csv(campos, linhas, convertidos, args.csv)
            print(f"CSV gravado em {args.csv}")
        if args.md:
            escrever_md(saida, args.md)
            print(f"Markdown gravado em {args.md}")
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
