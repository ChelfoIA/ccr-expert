#!/usr/bin/env python3
"""
Evolução da dívida em financiamento de veículo (CDC veículo ou CCB) em dois
cenários lado a lado: A (contratual, como cobrado) e B (revisado: taxa média
do BACEN quando a contratada supera o limiar declarado, e tarifas contestadas
excluídas do principal). Opcionalmente gera o cenário C (B sem capitalização,
pelo Método de Equivalência a Juros Simples, MEJS).
Parte da skill: pericia-busca-apreensao-veiculo

Antifabricação: a taxa média de mercado nunca é estimada. Ela entra por
parâmetro, com fonte e competência declaradas, obtida pelo perito no SGS do
BACEN (ver references/taxa-media-bacen.md). Sem taxa média, só o cenário A é
produzido e o JSON registra a lacuna.

Uso:
    python3 scripts/evolucao_cdc_veiculo.py --contrato assets/exemplo_contrato.json \
        --taxa-media-mensal 1,60 --fonte-taxa-media "BACEN/SGS, serie validada em dd/mm/aaaa" \
        --competencia-taxa-media 03/2024 --data-referencia 10/09/2025 \
        --saida evolucao.json --csv evolucao.csv --md evolucao.md

    Cenário adicional sem capitalização (MEJS):
    python3 scripts/evolucao_cdc_veiculo.py --contrato assets/exemplo_contrato.json \
        --taxa-media-mensal 1,60 --fonte-taxa-media "..." --competencia-taxa-media 03/2024 \
        --data-referencia 10/09/2025 --sem-capitalizacao
"""
import argparse
import calendar
import csv
import json
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 34

SKILL = "pericia-busca-apreensao-veiculo"
VERSAO = "1.0.0"
CENTAVO = Decimal("0.01")
CEM = Decimal("100")
TRINTA = Decimal("30")
TOLERANCIA = Decimal("0.005")
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"


# ----------------------------------------------------------------------------
# Utilitários de número e data
# ----------------------------------------------------------------------------
def parse_num(texto) -> Decimal:
    """Converte número no padrão brasileiro (1.234,56) ou técnico (1234.56).

    Regra: se houver vírgula, o ponto é separador de milhar e a vírgula é o
    separador decimal; sem vírgula, o ponto é decimal. Aceita prefixo R$ e
    sufixo %.
    """
    if texto is None:
        raise ValueError("valor numérico ausente")
    if isinstance(texto, (int, float, Decimal)):
        return Decimal(str(texto))
    s = str(texto).strip().replace("R$", "").replace("%", "").replace(" ", "")
    if s == "":
        raise ValueError("valor numérico vazio")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except Exception as exc:
        raise ValueError(f"número inválido: {texto!r}") from exc


def q2(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def fmt_num(valor: Decimal, casas: int = 2) -> str:
    """Formata no padrão brasileiro: 1.234,56 (sem prefixo)."""
    quant = Decimal(1).scaleb(-casas)
    v = valor.quantize(quant, rounding=ROUND_HALF_UP)
    negativo = v < 0
    v = abs(v)
    inteiro, _, frac = f"{v:f}".partition(".")
    frac = (frac + "0" * casas)[:casas] if casas else ""
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    texto = ".".join(grupos) + ("," + frac if casas else "")
    return ("-" if negativo else "") + texto


def fmt_brl(valor: Decimal) -> str:
    return fmt_num(valor, 2)


def fmt_pct(valor: Decimal, casas: int = 4) -> str:
    return fmt_num(valor, casas)


def parse_data(texto: str) -> date:
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(f"data inválida (esperado dd/mm/aaaa): {texto!r}") from exc


def fmt_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def add_months(d: date, k: int) -> date:
    """Soma k meses preservando o dia; se o mês não tiver o dia, usa o último."""
    mes = d.month - 1 + k
    ano = d.year + mes // 12
    mes = mes % 12 + 1
    dia = min(d.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


# ----------------------------------------------------------------------------
# Matemática financeira
# ----------------------------------------------------------------------------
def pmt_price(pv: Decimal, i: Decimal, n: int) -> Decimal:
    """Prestação da Tabela Price: PMT = PV * i / (1 - (1 + i)^-n)."""
    if i == 0:
        return pv / Decimal(n)
    fator = (Decimal(1) + i) ** (-n)
    return pv * i / (Decimal(1) - fator)


def pmt_mejs(pv: Decimal, i: Decimal, n: int) -> Decimal:
    """Prestação constante a juros simples (MEJS): PV = soma PMT / (1 + i*k)."""
    soma = sum((Decimal(1) / (Decimal(1) + i * Decimal(k)) for k in range(1, n + 1)), Decimal(0))
    return pv / soma


def juros_carencia(pv: Decimal, i: Decimal, dias_excedentes: int, composto: bool) -> Decimal:
    """Juros pro rata dos dias em que a 1a parcela excede um mês civil da contratação."""
    if dias_excedentes <= 0:
        return Decimal(0)
    fracao = Decimal(dias_excedentes) / TRINTA
    if composto:
        return pv * ((Decimal(1) + i) ** fracao - Decimal(1))
    return pv * i * fracao


def tabela_price(pv: Decimal, i: Decimal, n: int, vencimentos: list) -> tuple:
    pmt = pmt_price(pv, i, n)
    linhas, saldo = [], pv
    for k in range(1, n + 1):
        juros = saldo * i
        amort = pmt - juros
        saldo_final = saldo - amort
        linhas.append({"n": k, "vencimento": vencimentos[k - 1], "saldo_inicial": saldo,
                       "juros": juros, "amortizacao": amort, "parcela": pmt, "saldo_final": saldo_final})
        saldo = saldo_final
    return pmt, linhas


def tabela_mejs(pv: Decimal, i: Decimal, n: int, vencimentos: list) -> tuple:
    pmt = pmt_mejs(pv, i, n)
    linhas, saldo = [], pv
    for k in range(1, n + 1):
        amort = pmt / (Decimal(1) + i * Decimal(k))
        juros = pmt - amort
        saldo_final = saldo - amort
        linhas.append({"n": k, "vencimento": vencimentos[k - 1], "saldo_inicial": saldo,
                       "juros": juros, "amortizacao": amort, "parcela": pmt, "saldo_final": saldo_final})
        saldo = saldo_final
    return pmt, linhas


def sanidade(linhas: list, pv: Decimal, rotulo: str) -> dict:
    soma_amort = sum((l["amortizacao"] for l in linhas), Decimal(0))
    soma_parc = sum((l["parcela"] for l in linhas), Decimal(0))
    soma_juros = sum((l["juros"] for l in linhas), Decimal(0))
    ultimo = linhas[-1]["saldo_final"]
    ok_amort = abs(soma_amort - pv) <= TOLERANCIA
    ok_saldo = abs(ultimo) <= TOLERANCIA
    ok_parc = abs(soma_parc - (soma_amort + soma_juros)) <= TOLERANCIA
    if not (ok_amort and ok_saldo and ok_parc):
        raise ValueError(
            f"teste de sanidade falhou no cenário {rotulo}: soma das amortizações "
            f"{fmt_brl(soma_amort)} x principal {fmt_brl(pv)}; último saldo {fmt_brl(ultimo)}")
    return {"soma_amortizacoes": fmt_brl(soma_amort), "principal": fmt_brl(pv),
            "soma_juros": fmt_brl(soma_juros), "soma_parcelas": fmt_brl(soma_parc),
            "ultimo_saldo": fmt_brl(ultimo), "resultado": "OK"}


# ----------------------------------------------------------------------------
# Leitura e validação do contrato
# ----------------------------------------------------------------------------
def carregar_contrato(caminho: str) -> dict:
    p = Path(caminho)
    if not p.exists():
        raise ValueError(f"arquivo de contrato não encontrado: {caminho}")
    with p.open(encoding="utf-8") as fh:
        c = json.load(fh)
    obrig = ["valor_financiado", "data_contratacao", "taxa_mensal_contratada", "n_parcelas",
             "data_primeira_parcela"]
    faltam = [k for k in obrig if k not in c]
    if faltam:
        raise ValueError(f"campos obrigatórios ausentes no contrato: {', '.join(faltam)}")
    c["_valor_financiado"] = parse_num(c["valor_financiado"])
    c["_taxa_mensal"] = parse_num(c["taxa_mensal_contratada"]) / CEM
    c["_taxa_anual"] = parse_num(c["taxa_anual_informada"]) / CEM if c.get("taxa_anual_informada") not in (None, "") else None
    c["_n"] = int(c["n_parcelas"])
    c["_data_contratacao"] = parse_data(c["data_contratacao"])
    c["_data_primeira"] = parse_data(c["data_primeira_parcela"])
    c["_iof"] = parse_num(c.get("iof") or "0")
    if c["_valor_financiado"] <= 0:
        raise ValueError("valor_financiado deve ser positivo")
    if c["_n"] < 1:
        raise ValueError("n_parcelas deve ser maior ou igual a 1")
    if c["_taxa_mensal"] < 0:
        raise ValueError("taxa_mensal_contratada não pode ser negativa")
    if c["_data_primeira"] <= c["_data_contratacao"]:
        raise ValueError("data_primeira_parcela deve ser posterior à data_contratacao")
    itens = []
    for grupo in ("tarifas", "seguros"):
        for t in c.get(grupo) or []:
            if "nome" not in t or "valor" not in t:
                raise ValueError(f"item de {grupo} sem nome ou valor")
            itens.append({"grupo": grupo, "nome": t["nome"], "valor": parse_num(t["valor"]),
                          "incluida_no_financiado": bool(t.get("incluida_no_financiado", True)),
                          "contestada": bool(t.get("contestada", False)),
                          "motivo": t.get("motivo", "")})
    c["_itens"] = itens
    soma_incl = sum((t["valor"] for t in itens if t["incluida_no_financiado"]), Decimal(0)) + c["_iof"]
    if soma_incl > c["_valor_financiado"]:
        raise ValueError(
            f"soma de tarifas, seguros e IOF incluídos ({fmt_brl(soma_incl)}) supera o valor financiado "
            f"({fmt_brl(c['_valor_financiado'])})")
    pagamentos = []
    for pg in c.get("pagamentos") or []:
        n = int(pg["n_parcela"])
        if not 1 <= n <= c["_n"]:
            raise ValueError(f"pagamento refere-se à parcela {n}, fora do intervalo 1 a {c['_n']}")
        pagamentos.append({"n_parcela": n, "data": parse_data(pg["data"]), "valor": parse_num(pg["valor"])})
    c["_pagamentos"] = pagamentos
    return c


# ----------------------------------------------------------------------------
# Montagem dos cenários
# ----------------------------------------------------------------------------
def montar_cenario(rotulo: str, descricao: str, pv_base: Decimal, i: Decimal, n: int, vencimentos: list,
                   dias_carencia_exc: int, metodo: str, pagos_por_parcela: dict, memoria: list) -> dict:
    composto = metodo == "price"
    jc = juros_carencia(pv_base, i, dias_carencia_exc, composto)
    pv = pv_base + jc
    if metodo == "price":
        pmt, linhas = tabela_price(pv, i, n, vencimentos)
        formula = "PMT = PV x i / (1 - (1 + i)^-n)"
    else:
        pmt, linhas = tabela_mejs(pv, i, n, vencimentos)
        formula = "PMT = PV / soma[k=1..n] 1/(1 + i x k)"
    san = sanidade(linhas, pv, rotulo)
    memoria.append(f"Cenário {rotulo}: {descricao}.")
    memoria.append(f"Cenário {rotulo}: principal base R$ {fmt_brl(pv_base)}"
                   + (f" + juros de carência R$ {fmt_brl(jc)} ({dias_carencia_exc} dias além de um mês)" if jc else "")
                   + f" = PV R$ {fmt_brl(pv)}; i = {fmt_pct(i * CEM)}% a.m.; n = {n}; {formula};"
                   f" PMT = R$ {fmt_brl(pmt)}.")
    memoria.append(f"Cenário {rotulo}: sanidade: soma das amortizações R$ {san['soma_amortizacoes']} = PV;"
                   f" último saldo R$ {san['ultimo_saldo']}.")
    tabela = []
    for l in linhas:
        pago = pagos_por_parcela.get(l["n"], Decimal(0))
        if pago == 0:
            status = "em aberto"
        elif pago + TOLERANCIA >= l["parcela"]:
            status = "paga"
        else:
            status = "paga parcialmente"
        tabela.append({"n": l["n"], "vencimento": fmt_data(l["vencimento"]),
                       "saldo_inicial": fmt_brl(l["saldo_inicial"]), "juros": fmt_brl(l["juros"]),
                       "amortizacao": fmt_brl(l["amortizacao"]), "parcela": fmt_brl(l["parcela"]),
                       "saldo_final": fmt_brl(l["saldo_final"]), "pago": fmt_brl(pago), "status": status})
    return {"rotulo": rotulo, "descricao": descricao, "metodo": metodo, "formula": formula,
            "taxa_mensal_pct": fmt_pct(i * CEM), "taxa_anual_equivalente_pct": fmt_pct(((Decimal(1) + i) ** 12 - 1) * CEM),
            "principal_base": fmt_brl(pv_base), "juros_carencia": fmt_brl(jc), "principal": fmt_brl(pv),
            "parcela": fmt_brl(pmt), "total_parcelas": san["soma_parcelas"], "total_juros": san["soma_juros"],
            "sanidade": san, "tabela": tabela,
            "_linhas": linhas, "_pmt": pmt, "_pv": pv}


def situacao_na_referencia(cen: dict, data_ref: date, pagos: dict) -> dict:
    vencidas = [l for l in cen["_linhas"] if l["vencimento"] <= data_ref]
    vincendas = [l for l in cen["_linhas"] if l["vencimento"] > data_ref]
    abertas = []
    for l in vencidas:
        pago = pagos.get(l["n"], Decimal(0))
        residual = l["parcela"] - pago
        if residual > TOLERANCIA:
            abertas.append({"n": l["n"], "vencimento": fmt_data(l["vencimento"]), "parcela": fmt_brl(l["parcela"]),
                            "pago": fmt_brl(pago), "residual": fmt_brl(residual),
                            "dias_atraso": (data_ref - l["vencimento"]).days})
    saldo_vp = vencidas[-1]["saldo_final"] if vencidas else cen["_pv"]
    # Nominal das vincendas: soma das parcelas arredondadas ao centavo, como
    # constam do carnê e da planilha do credor; coincide com purga_mora.py.
    nominal_vinc = sum((q2(l["parcela"]) for l in vincendas), Decimal(0))
    return {"parcelas_vencidas": len(vencidas), "parcelas_vincendas": len(vincendas),
            "vencidas_nao_pagas": abertas,
            "total_residual_vencidas": fmt_brl(sum((parse_num(a["residual"]) for a in abertas), Decimal(0))),
            "saldo_devedor_valor_presente_vincendas": fmt_brl(saldo_vp),
            "vincendas_valor_nominal": fmt_brl(nominal_vinc)}


# ----------------------------------------------------------------------------
# Saídas em CSV e Markdown
# ----------------------------------------------------------------------------
def gravar_csv(caminho: str, resultado: dict) -> None:
    cen = resultado["cenarios"]
    rotulos = [r for r in ("A", "B", "C") if r in cen]
    with Path(caminho).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        cab = ["n", "vencimento"]
        for r in rotulos:
            cab += [f"saldo_inicial_{r}", f"juros_{r}", f"amortizacao_{r}", f"parcela_{r}", f"saldo_final_{r}"]
        cab += ["pago", "status_A"]
        w.writerow(cab)
        n = len(cen[rotulos[0]]["tabela"])
        for k in range(n):
            linha = [cen[rotulos[0]]["tabela"][k]["n"], cen[rotulos[0]]["tabela"][k]["vencimento"]]
            for r in rotulos:
                t = cen[r]["tabela"][k]
                linha += [t["saldo_inicial"], t["juros"], t["amortizacao"], t["parcela"], t["saldo_final"]]
            linha += [cen[rotulos[0]]["tabela"][k]["pago"], cen[rotulos[0]]["tabela"][k]["status"]]
            w.writerow(linha)


def gravar_md(caminho: str, resultado: dict) -> None:
    cen = resultado["cenarios"]
    rotulos = [r for r in ("A", "B", "C") if r in cen]
    out = ["# Evolução da dívida: cenários comparados", "",
           f"Contrato: {resultado['contrato']['identificacao']}. Data de referência: {resultado['data_referencia']}.", "",
           "## Premissas", ""]
    for k, v in resultado["premissas"].items():
        out.append(f"- {k}: {v}")
    out += ["", "## Quadro resumo", "", "| Item | " + " | ".join(f"Cenário {r}" for r in rotulos) + " |",
            "|---|" + "---|" * len(rotulos)]
    for campo, rot in (("descricao", "Descrição"), ("taxa_mensal_pct", "Taxa mensal (%)"),
                       ("principal", "Principal (R$)"), ("parcela", "Parcela (R$)"),
                       ("total_parcelas", "Soma das parcelas (R$)"), ("total_juros", "Juros totais (R$)")):
        out.append(f"| {rot} | " + " | ".join(str(cen[r][campo]) for r in rotulos) + " |")
    out += ["", "## Comparativo parcela a parcela", "",
            "| n | Vencimento | " + " | ".join(f"Parcela {r}" for r in rotulos) + " | Dif. A-B | Pago | Status |",
            "|---|---|" + "---|" * len(rotulos) + "---|---|---|"]
    for k, comp in enumerate(resultado["comparativo_parcelas"]):
        ta = cen["A"]["tabela"][k]
        out.append(f"| {comp['n']} | {comp['vencimento']} | "
                   + " | ".join(cen[r]["tabela"][k]["parcela"] for r in rotulos)
                   + f" | {comp.get('diferenca_A_B', '')} | {ta['pago']} | {ta['status']} |")
    pg = resultado["pagamentos"]
    out += ["", "## Pagamentos e excesso", "",
            f"- Total pago: R$ {pg['total_pago']}",
            f"- Devido no cenário B pelas mesmas parcelas: R$ {pg.get('devido_B_parcelas_pagas', 'n/d')}",
            f"- Excesso (pago menos devido em B): R$ {pg.get('excesso_A_B', 'n/d')}", "",
            "## Situação na data de referência", ""]
    for r in rotulos:
        s = resultado["situacao_na_referencia"][r]
        out.append(f"- Cenário {r}: {s['parcelas_vencidas']} vencidas, {len(s['vencidas_nao_pagas'])} em aberto"
                   f" (residual R$ {s['total_residual_vencidas']}); {s['parcelas_vincendas']} vincendas,"
                   f" valor presente R$ {s['saldo_devedor_valor_presente_vincendas']},"
                   f" nominal R$ {s['vincendas_valor_nominal']}.")
    out += ["", "## Memória de cálculo", ""] + [f"{k + 1}. {m}" for k, m in enumerate(resultado["memoria"])]
    Path(caminho).write_text("\n".join(out) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Evolução da dívida de financiamento de veículo em cenários A, B e C.")
    p.add_argument("--contrato", required=True, help="JSON do contrato (ver assets/exemplo_contrato.json)")
    p.add_argument("--taxa-media-mensal", help="Taxa média BACEN da modalidade no mês da contratação, em %% a.m. (ex.: 1,60)")
    p.add_argument("--taxa-media-anual", help="Alternativa: taxa média em %% a.a.; convertida por (1+a)^(1/12)-1")
    p.add_argument("--fonte-taxa-media", help="Fonte declarada da taxa média (SGS/BACEN, série, data de consulta)")
    p.add_argument("--competencia-taxa-media", help="Competência da taxa média no formato mm/aaaa")
    p.add_argument("--limiar", default="1,5", help="Múltiplo da média acima do qual o cenário B adota a média (padrão 1,5; premissa, não norma)")
    p.add_argument("--forcar-taxa-media", action="store_true", help="Cenário B usa a taxa média mesmo abaixo do limiar (ex.: decisão judicial já fixou)")
    p.add_argument("--excluir-iof", action="store_true", help="Retira o IOF do principal no cenário B (padrão: mantém)")
    p.add_argument("--sem-capitalizacao", action="store_true", help="Gera o cenário C: B sem capitalização (MEJS)")
    p.add_argument("--ignorar-carencia", action="store_true", help="Não calcula juros pro rata de carência acima de 30 dias")
    p.add_argument("--data-referencia", help="Data para posição de vencidas e vincendas (dd/mm/aaaa); padrão: hoje")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--csv", help="Grava a tabela comparativa em CSV (separador ;)")
    p.add_argument("--md", help="Grava o quadro comparativo em Markdown")
    return p


def executar(args) -> dict:
    c = carregar_contrato(args.contrato)
    memoria = []
    n, i_a = c["_n"], c["_taxa_mensal"]
    vencimentos = [add_months(c["_data_primeira"], k) for k in range(n)]
    data_ref = parse_data(args.data_referencia) if args.data_referencia else date.today()
    dias_carencia = (c["_data_primeira"] - c["_data_contratacao"]).days
    # Carência: só há juros pro rata quando a primeira parcela vence depois de
    # um mês civil contado da contratação (15/03 para 15/04 é um mês, sem carência).
    dias_exc = 0 if args.ignorar_carencia else max(0, (c["_data_primeira"] - add_months(c["_data_contratacao"], 1)).days)
    memoria.append(f"Contrato de {fmt_data(c['_data_contratacao'])}, valor financiado R$ {fmt_brl(c['_valor_financiado'])},"
                   f" taxa contratada {fmt_pct(i_a * CEM)}% a.m., {n} parcelas, primeira em {fmt_data(c['_data_primeira'])}"
                   f" ({dias_carencia} dias após a contratação).")

    pagos = {}
    for pg in c["_pagamentos"]:
        pagos[pg["n_parcela"]] = pagos.get(pg["n_parcela"], Decimal(0)) + pg["valor"]

    # Taxa média e critério do cenário B
    taxa_media = None
    if args.taxa_media_mensal:
        taxa_media = parse_num(args.taxa_media_mensal) / CEM
    elif args.taxa_media_anual:
        taxa_media = (Decimal(1) + parse_num(args.taxa_media_anual) / CEM) ** (Decimal(1) / Decimal(12)) - Decimal(1)
    limiar = parse_num(args.limiar)
    if taxa_media is not None and not (args.fonte_taxa_media and args.competencia_taxa_media):
        raise ValueError("taxa média informada sem --fonte-taxa-media e --competencia-taxa-media (antifabricação)")

    contestadas_incl = [t for t in c["_itens"] if t["contestada"] and t["incluida_no_financiado"]]
    contestadas_fora = [t for t in c["_itens"] if t["contestada"] and not t["incluida_no_financiado"]]
    soma_contest_incl = sum((t["valor"] for t in contestadas_incl), Decimal(0))
    pv_b = c["_valor_financiado"] - soma_contest_incl - (c["_iof"] if args.excluir_iof else Decimal(0))
    if pv_b <= 0:
        raise ValueError("principal do cenário B ficou não positivo após as exclusões")

    cenarios = {}
    cenarios["A"] = montar_cenario("A", "contratual, como cobrado (Price, taxa e principal do contrato)",
                                   c["_valor_financiado"], i_a, n, vencimentos, dias_exc, "price", pagos, memoria)

    razao = None
    i_b = i_a
    criterio_b = "taxa média não informada: cenário B não produzido"
    if taxa_media is not None:
        razao = i_a / taxa_media if taxa_media > 0 else None
        acima = args.forcar_taxa_media or (razao is not None and razao > limiar)
        i_b = taxa_media if acima else i_a
        if args.forcar_taxa_media:
            criterio_b = "taxa média adotada por determinação expressa (--forcar-taxa-media)"
        elif acima:
            criterio_b = (f"taxa contratada {fmt_pct(i_a * CEM)}% = {fmt_num(razao, 4)} x a média {fmt_pct(taxa_media * CEM)}%,"
                          f" acima do limiar {fmt_num(limiar, 2)}: cenário B adota a média")
        else:
            criterio_b = (f"taxa contratada {fmt_pct(i_a * CEM)}% = {fmt_num(razao, 4) if razao is not None else 'n/d'} x a média"
                          f" {fmt_pct(taxa_media * CEM)}%, dentro do limiar {fmt_num(limiar, 2)}: cenário B mantém a taxa contratada")
        memoria.append("Critério do cenário B: " + criterio_b + ".")
        if contestadas_incl:
            memoria.append("Cenário B: excluídos do principal " + "; ".join(
                f"{t['nome']} R$ {fmt_brl(t['valor'])}" for t in contestadas_incl)
                + f" (total R$ {fmt_brl(soma_contest_incl)}).")
        if args.excluir_iof:
            memoria.append(f"Cenário B: IOF de R$ {fmt_brl(c['_iof'])} excluído do principal por opção do usuário.")
        cenarios["B"] = montar_cenario("B", "revisado (Price; taxa média se contratada acima do limiar; tarifas contestadas fora do principal)",
                                       pv_b, i_b, n, vencimentos, dias_exc, "price", pagos, memoria)
        if args.sem_capitalizacao:
            cenarios["C"] = montar_cenario("C", "B sem capitalização (juros simples pelo MEJS, mesma taxa e principal de B)",
                                           pv_b, i_b, n, vencimentos, dias_exc, "mejs", pagos, memoria)
    else:
        memoria.append("Taxa média não informada: cenário B não produzido. Informar --taxa-media-mensal com fonte e competência.")

    # Comparativo parcela a parcela e excesso
    comparativo, excesso_total, devido_b_pagas = [], Decimal(0), Decimal(0)
    total_pago = sum(pagos.values(), Decimal(0))
    for k in range(n):
        la = cenarios["A"]["_linhas"][k]
        item = {"n": la["n"], "vencimento": fmt_data(la["vencimento"]), "parcela_A": fmt_brl(la["parcela"])}
        if "B" in cenarios:
            lb = cenarios["B"]["_linhas"][k]
            item["parcela_B"] = fmt_brl(lb["parcela"])
            item["diferenca_A_B"] = fmt_brl(la["parcela"] - lb["parcela"])
            pago = pagos.get(la["n"], Decimal(0))
            if pago > 0:
                exc = pago - lb["parcela"]
                excesso_total += exc
                devido_b_pagas += lb["parcela"]
                item["pago"] = fmt_brl(pago)
                item["excesso_sobre_B"] = fmt_brl(exc)
        if "C" in cenarios:
            item["parcela_C"] = fmt_brl(cenarios["C"]["_linhas"][k]["parcela"])
        comparativo.append(item)
    pagamentos = {"quantidade_pagamentos": len(c["_pagamentos"]), "parcelas_com_pagamento": sorted(pagos),
                  "total_pago": fmt_brl(total_pago)}
    if "B" in cenarios:
        pagamentos["devido_B_parcelas_pagas"] = fmt_brl(devido_b_pagas)
        pagamentos["excesso_A_B"] = fmt_brl(excesso_total)
        memoria.append(f"Excesso: total pago R$ {fmt_brl(total_pago)} menos devido em B pelas mesmas parcelas"
                       f" R$ {fmt_brl(devido_b_pagas)} = R$ {fmt_brl(excesso_total)} (valores nominais nas datas de pagamento;"
                       " atualização pela skill atualizacao-monetaria).")
    if contestadas_fora:
        pagamentos["tarifas_contestadas_pagas_a_vista"] = [
            {"nome": t["nome"], "valor": fmt_brl(t["valor"]), "motivo": t["motivo"]} for t in contestadas_fora]
        pagamentos["total_tarifas_contestadas_pagas_a_vista"] = fmt_brl(sum((t["valor"] for t in contestadas_fora), Decimal(0)))

    situacao = {r: situacao_na_referencia(cenarios[r], data_ref, pagos) for r in cenarios}
    for r in cenarios:
        s = situacao[r]
        memoria.append(f"Situação em {fmt_data(data_ref)}, cenário {r}: {s['parcelas_vencidas']} parcelas vencidas,"
                       f" {len(s['vencidas_nao_pagas'])} em aberto (residual R$ {s['total_residual_vencidas']}),"
                       f" {s['parcelas_vincendas']} vincendas (valor presente R$ {s['saldo_devedor_valor_presente_vincendas']};"
                       f" nominal R$ {s['vincendas_valor_nominal']}).")

    premissas = {
        "sistema_amortizacao": "Tabela Price nos cenários A e B; MEJS no cenário C quando solicitado",
        "capitalizacao": "mensal nos cenários A e B (pactuação expressa é matéria da Súmula 539/STJ, aferida pelo juízo)",
        "carencia": ("ignorada por opção" if args.ignorar_carencia else
                     "juros pro rata (base 30 dias) sobre os dias em que a primeira parcela excede um mês civil da contratação"),
        "criterio_cenario_B": criterio_b,
        "limiar_multiplo_da_media": fmt_num(limiar, 2) + " (premissa usual de jurisprudência, não norma; REsp 1.061.530 fala em discrepância substancial)",
        "tarifas_contestadas": "excluídas do principal de B quando incluídas no financiado; se pagas à vista, listadas para restituição",
        "iof": "mantido no principal em A e B" + (" (excluído em B por opção)" if args.excluir_iof else ""),
        "taxa_media": ({"mensal_pct": fmt_pct(taxa_media * CEM), "fonte": args.fonte_taxa_media,
                        "competencia": args.competencia_taxa_media} if taxa_media is not None else "não informada"),
        "pagamentos": "imputados à parcela indicada; pagamento parcial gera residual; sem imputação de excesso em amortização",
        "data_referencia": fmt_data(data_ref),
        "parcelas_vincendas": "saldo devedor a valor presente = saldo da tabela após a última vencida; nominal = soma das parcelas arredondadas ao centavo, como cobradas",
    }
    resultado = {
        "skill": SKILL, "script": "evolucao_cdc_veiculo.py", "versao": VERSAO,
        "locale": LOCALE, "arredondamento": ARREDONDAMENTO,
        "premissas": premissas,
        "contrato": {"identificacao": c.get("identificacao", "não informada"), "devedor": c.get("devedor", ""),
                     "credor": c.get("credor", ""), "processo": c.get("processo", ""),
                     "data_contratacao": fmt_data(c["_data_contratacao"]), "valor_financiado": fmt_brl(c["_valor_financiado"]),
                     "taxa_mensal_contratada_pct": fmt_pct(i_a * CEM),
                     "taxa_anual_informada_pct": fmt_pct(c["_taxa_anual"] * CEM) if c["_taxa_anual"] is not None else "não informada",
                     "taxa_anual_equivalente_composta_pct": fmt_pct(((Decimal(1) + i_a) ** 12 - 1) * CEM),
                     "n_parcelas": n, "data_primeira_parcela": fmt_data(c["_data_primeira"]),
                     "dias_ate_primeira_parcela": dias_carencia, "iof": fmt_brl(c["_iof"]),
                     "itens": [{"grupo": t["grupo"], "nome": t["nome"], "valor": fmt_brl(t["valor"]),
                                "incluida_no_financiado": t["incluida_no_financiado"], "contestada": t["contestada"],
                                "motivo": t["motivo"]} for t in c["_itens"]]},
        "data_referencia": fmt_data(data_ref),
        "razao_contratada_sobre_media": fmt_num(razao, 4) if razao is not None else "n/d",
        "cenarios": {r: {k: v for k, v in cenarios[r].items() if not k.startswith("_")} for r in cenarios},
        "comparativo_parcelas": comparativo,
        "pagamentos": pagamentos,
        "situacao_na_referencia": situacao,
        "memoria": memoria,
    }
    return resultado


def main() -> None:
    args = montar_parser().parse_args()
    try:
        resultado = executar(args)
        texto = json.dumps(resultado, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"JSON gravado em {args.saida}")
        else:
            print(texto)
        if args.csv:
            gravar_csv(args.csv, resultado)
            print(f"CSV gravado em {args.csv}")
        if args.md:
            gravar_md(args.md, resultado)
            print(f"Markdown gravado em {args.md}")
    except ValueError as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
