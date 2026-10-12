#!/usr/bin/env python3
"""
Valor exigível para purga da mora em ação de busca e apreensão (DL 911/1969,
art. 3º, § 2º, na redação da Lei 10.931/2004; Tema 722 do STJ, integralidade
da dívida), calculado nos cenários A (contratual) e B (revisado) a partir do
JSON produzido por scripts/evolucao_cdc_veiculo.py: parcelas vencidas com
encargos moratórios (juros de mora pro rata die e multa) mais parcelas
vincendas a valor nominal (padrão) ou a valor presente.
Parte da skill: pericia-busca-apreensao-veiculo

O script responde primeiro à pergunta da mora (houve encargo abusivo no
período de normalidade, segundo o cenário B?) e só depois ao valor, porque em
busca e apreensão a resposta afirmativa descaracteriza a mora (REsp 1.061.530;
REsp 2.239.793) e o valor da purga perde objeto. A conclusão jurídica é do
juízo; o script produz o sinal técnico.

Uso:
    python3 scripts/purga_mora.py --evolucao assets/exemplo_evolucao.json --data-liminar 10/09/2025 \
        --juros-mora-am 1,0 --multa 2,0 --saida purga.json --md purga.md
    python3 scripts/purga_mora.py --evolucao evolucao.json --data-liminar 10/09/2025 --comissao-permanencia
"""
import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 34

SKILL = "pericia-busca-apreensao-veiculo"
VERSAO = "1.0.0"
CEM = Decimal("100")
TRINTA = Decimal("30")
TOLERANCIA = Decimal("0.005")
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"


def parse_num(texto) -> Decimal:
    """Aceita 1.234,56 (brasileiro) e 1234.56 (técnico); remove R$ e %."""
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


def fmt_num(valor: Decimal, casas: int = 2) -> str:
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
    return ("-" if negativo else "") + ".".join(grupos) + ("," + frac if casas else "")


def fmt_brl(valor: Decimal) -> str:
    return fmt_num(valor, 2)


def parse_data(texto: str) -> date:
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(f"data inválida (esperado dd/mm/aaaa): {texto!r}") from exc


def fmt_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Valor para purga da mora (integralidade, Tema 722) nos cenários A e B.")
    p.add_argument("--evolucao", required=True, help="JSON gerado por scripts/evolucao_cdc_veiculo.py")
    p.add_argument("--data-liminar", required=True, help="Data da decisão liminar (dd/mm/aaaa)")
    p.add_argument("--data-calculo", help="Data de cálculo dos encargos, se diversa da liminar (ex.: data da inicial); padrão: a liminar")
    p.add_argument("--juros-mora-am", default="1,0", help="Juros de mora em %% a.m., pro rata die sobre 30 dias (padrão 1,0)")
    p.add_argument("--multa", default="2,0", help="Multa moratória em %% sobre a parcela vencida (padrão 2,0; CDC, art. 52, § 1º)")
    p.add_argument("--vincendas", choices=["nominal", "valor-presente"], default="nominal",
                   help="Vincendas pelo valor nominal das parcelas (padrão) ou pelo saldo devedor a valor presente")
    p.add_argument("--comissao-permanencia", action="store_true",
                   help="Sinaliza que o contrato prevê comissão de permanência; o script não a soma e registra a cumulação vedada")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="Grava o quadro da purga em Markdown")
    return p


def carregar_evolucao(caminho: str) -> dict:
    p = Path(caminho)
    if not p.exists():
        raise ValueError(f"arquivo de evolução não encontrado: {caminho}")
    with p.open(encoding="utf-8") as fh:
        ev = json.load(fh)
    if ev.get("script") != "evolucao_cdc_veiculo.py" or "cenarios" not in ev:
        raise ValueError("o JSON informado não foi gerado por evolucao_cdc_veiculo.py")
    if "A" not in ev["cenarios"]:
        raise ValueError("o JSON de evolução não contém o cenário A")
    return ev


def purga_cenario(rotulo: str, cen: dict, data_calc: date, jm: Decimal, multa: Decimal, modo_vinc: str, memoria: list) -> dict:
    vencidas, vincendas = [], []
    for t in cen["tabela"]:
        venc = parse_data(t["vencimento"])
        parcela = parse_num(t["parcela"])
        pago = parse_num(t.get("pago", "0"))
        if venc <= data_calc:
            residual = parcela - pago
            if residual > TOLERANCIA:
                dias = (data_calc - venc).days
                juros = residual * jm * Decimal(dias) / TRINTA
                mult = residual * multa
                vencidas.append({"n": t["n"], "vencimento": t["vencimento"], "parcela": parcela, "pago": pago,
                                 "residual": residual, "dias_atraso": dias, "juros_mora": juros, "multa": mult,
                                 "subtotal": residual + juros + mult})
        else:
            vincendas.append({"n": t["n"], "vencimento": t["vencimento"], "parcela": parcela})
    soma_residual = sum((v["residual"] for v in vencidas), Decimal(0))
    soma_juros = sum((v["juros_mora"] for v in vencidas), Decimal(0))
    soma_multa = sum((v["multa"] for v in vencidas), Decimal(0))
    soma_vencidas = sum((v["subtotal"] for v in vencidas), Decimal(0))
    if abs(soma_vencidas - (soma_residual + soma_juros + soma_multa)) > TOLERANCIA:
        raise ValueError(f"sanidade falhou no cenário {rotulo}: subtotal das vencidas não fecha com as parcelas")
    nominal_vinc = sum((v["parcela"] for v in vincendas), Decimal(0))
    ultima_vencida = [t for t in cen["tabela"] if parse_data(t["vencimento"]) <= data_calc]
    vp_vinc = parse_num(ultima_vencida[-1]["saldo_final"]) if ultima_vencida else parse_num(cen["principal"])
    valor_vinc = nominal_vinc if modo_vinc == "nominal" else vp_vinc
    total = soma_vencidas + valor_vinc
    if abs(total - (soma_residual + soma_juros + soma_multa + valor_vinc)) > TOLERANCIA:
        raise ValueError(f"sanidade falhou no cenário {rotulo}: total da purga não fecha com as parcelas")
    memoria.append(f"Cenário {rotulo}: {len(vencidas)} parcelas vencidas em aberto em {fmt_data(data_calc)}"
                   f" (residual R$ {fmt_brl(soma_residual)}); juros de mora {fmt_num(jm * CEM, 2)}% a.m. pro rata die"
                   f" = R$ {fmt_brl(soma_juros)}; multa {fmt_num(multa * CEM, 2)}% = R$ {fmt_brl(soma_multa)};"
                   f" subtotal vencidas R$ {fmt_brl(soma_vencidas)}.")
    memoria.append(f"Cenário {rotulo}: {len(vincendas)} parcelas vincendas; nominal R$ {fmt_brl(nominal_vinc)};"
                   f" valor presente (saldo da tabela) R$ {fmt_brl(vp_vinc)}; adotado {modo_vinc}: R$ {fmt_brl(valor_vinc)}.")
    memoria.append(f"Cenário {rotulo}: purga = R$ {fmt_brl(soma_vencidas)} + R$ {fmt_brl(valor_vinc)} = R$ {fmt_brl(total)}.")
    return {"taxa_mensal_pct": cen.get("taxa_mensal_pct"), "parcela": cen.get("parcela"),
            "vencidas_em_aberto": [{"n": v["n"], "vencimento": v["vencimento"], "parcela": fmt_brl(v["parcela"]),
                                    "pago": fmt_brl(v["pago"]), "residual": fmt_brl(v["residual"]),
                                    "dias_atraso": v["dias_atraso"], "juros_mora": fmt_brl(v["juros_mora"]),
                                    "multa": fmt_brl(v["multa"]), "subtotal": fmt_brl(v["subtotal"])} for v in vencidas],
            "quantidade_vencidas": len(vencidas), "soma_residual_vencidas": fmt_brl(soma_residual),
            "juros_mora": fmt_brl(soma_juros), "multa": fmt_brl(soma_multa), "subtotal_vencidas": fmt_brl(soma_vencidas),
            "quantidade_vincendas": len(vincendas), "vincendas_nominal": fmt_brl(nominal_vinc),
            "vincendas_valor_presente": fmt_brl(vp_vinc), "vincendas_adotado": fmt_brl(valor_vinc),
            "valor_purga": fmt_brl(total), "_total": total}


def sinal_mora(ev: dict) -> dict:
    """Sinal técnico sobre encargo abusivo no período de normalidade, lido do cenário B."""
    prem = ev.get("premissas", {})
    crit = str(prem.get("criterio_cenario_B", ""))
    itens = ev.get("contrato", {}).get("itens", [])
    contestadas = [t for t in itens if t.get("contestada")]
    taxa_reduzida = "adota a média" in crit or "determinação expressa" in crit
    motivos = []
    if taxa_reduzida:
        motivos.append("juros remuneratórios acima do limiar declarado (cenário B recalculado pela taxa média)")
    if contestadas:
        motivos.append("tarifas ou seguros contestados no principal: " + "; ".join(t["nome"] for t in contestadas))
    if "B" not in ev.get("cenarios", {}):
        return {"resposta": "não aferido", "motivos": ["cenário B ausente: taxa média não informada na evolução"],
                "consequencia": "informar a taxa média e reexecutar evolucao_cdc_veiculo.py"}
    if motivos:
        return {"resposta": "sim (sinal técnico)", "motivos": motivos,
                "consequencia": ("se o juízo reconhecer a abusividade do encargo no período de normalidade, a mora se"
                                 " descaracteriza (REsp 1.061.530; REsp 2.239.793; REsp 2.134.805) e a purga perde objeto;"
                                 " o valor abaixo vale para a hipótese de mora mantida")}
    return {"resposta": "não (sinal técnico)", "motivos": ["taxa dentro do limiar e nenhuma tarifa contestada no principal"],
            "consequencia": "mora preservada segundo o cenário B; a purga exige a integralidade (Tema 722)"}


def gravar_md(caminho: str, r: dict) -> None:
    out = ["# Purga da mora: valor exigível por cenário", "",
           f"Data da liminar: {r['data_liminar']}. Data de cálculo: {r['data_calculo']}.", "",
           f"Encargo abusivo no período de normalidade (cenário B)? {r['sinal_mora']['resposta']}.",
           "Motivos: " + "; ".join(r["sinal_mora"]["motivos"]) + ".", "",
           "| Item | " + " | ".join(f"Cenário {c}" for c in r["cenarios"]) + " |", "|---|" + "---|" * len(r["cenarios"])]
    campos = [("taxa_mensal_pct", "Taxa mensal (%)"), ("parcela", "Parcela (R$)"), ("quantidade_vencidas", "Vencidas em aberto"),
              ("soma_residual_vencidas", "Residual das vencidas (R$)"), ("juros_mora", "Juros de mora (R$)"), ("multa", "Multa (R$)"),
              ("subtotal_vencidas", "Subtotal vencidas (R$)"), ("quantidade_vincendas", "Vincendas"),
              ("vincendas_nominal", "Vincendas nominal (R$)"), ("vincendas_valor_presente", "Vincendas valor presente (R$)"),
              ("vincendas_adotado", "Vincendas adotado (R$)"), ("valor_purga", "Valor para purga (R$)")]
    for campo, rot in campos:
        out.append(f"| {rot} | " + " | ".join(str(r["cenarios"][c][campo]) for c in r["cenarios"]) + " |")
    if "diferenca_A_B" in r:
        out += ["", f"Diferença A menos B: R$ {r['diferenca_A_B']}."]
    out += ["", "## Notas", ""] + [f"- {n}" for n in r["notas"]]
    out += ["", "## Memória de cálculo", ""] + [f"{k + 1}. {m}" for k, m in enumerate(r["memoria"])]
    Path(caminho).write_text("\n".join(out) + "\n", encoding="utf-8")


def executar(args) -> dict:
    ev = carregar_evolucao(args.evolucao)
    data_lim = parse_data(args.data_liminar)
    data_calc = parse_data(args.data_calculo) if args.data_calculo else data_lim
    jm = parse_num(args.juros_mora_am) / CEM
    multa = parse_num(args.multa) / CEM
    if jm < 0 or multa < 0:
        raise ValueError("juros de mora e multa não podem ser negativos")
    memoria = [f"Evolução lida de {args.evolucao} (contrato {ev.get('contrato', {}).get('identificacao', 'n/d')}),"
               f" data de referência da evolução {ev.get('data_referencia')}; data de cálculo da purga {fmt_data(data_calc)}."]
    if ev.get("data_referencia") and parse_data(ev["data_referencia"]) != data_calc:
        memoria.append("Aviso: a data de cálculo difere da data de referência da evolução; os pagamentos considerados são os do JSON.")
    cenarios = {}
    for rot in ("A", "B", "C"):
        if rot in ev["cenarios"]:
            cenarios[rot] = purga_cenario(rot, ev["cenarios"][rot], data_calc, jm, multa, args.vincendas, memoria)
    notas = [
        "Integralidade: a purga exige parcelas vencidas e vincendas (DL 911/1969, art. 3º, § 2º, redação da Lei 10.931/2004;"
        " Tema 722 do STJ, REsp 1.418.593; AgInt nos EDcl no REsp 2.164.201).",
        "Vincendas: valor nominal reproduz a planilha usual do credor; o valor presente corresponde ao saldo devedor da tabela"
        " e dialoga com a redução proporcional de juros na liquidação antecipada (CDC, art. 52, § 2º). Declarar a opção no laudo.",
        f"Encargos moratórios adotados: juros de mora {fmt_num(jm * CEM, 2)}% a.m. pro rata die (base 30 dias) e multa"
        f" {fmt_num(multa * CEM, 2)}% (CDC, art. 52, § 1º). Conferir a cláusula contratual e ajustar os parâmetros.",
        "Adimplemento substancial não afasta a exigência de pagamento integral (REsp 2.240.342).",
    ]
    if args.comissao_permanencia:
        notas.append("Comissão de permanência prevista no contrato: não somada. Sua cumulação com juros de mora, multa e correção"
                     " é vedada (orientação atribuída à Súmula 472/STJ [A VERIFICAR]); o valor acima já contém os encargos"
                     " moratórios, e a inclusão da comissão duplicaria a remuneração da mora.")
    r = {"skill": SKILL, "script": "purga_mora.py", "versao": VERSAO, "locale": LOCALE, "arredondamento": ARREDONDAMENTO,
         "premissas": {"juros_mora_am_pct": fmt_num(jm * CEM, 2), "multa_pct": fmt_num(multa * CEM, 2),
                       "vincendas": args.vincendas, "comissao_permanencia_no_contrato": bool(args.comissao_permanencia),
                       "base_pro_rata": "30 dias", "origem_das_parcelas": "tabelas dos cenários do JSON de evolução"},
         "data_liminar": fmt_data(data_lim), "data_calculo": fmt_data(data_calc),
         "sinal_mora": sinal_mora(ev),
         "cenarios": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in cenarios.items()},
         "notas": notas, "memoria": memoria}
    if "A" in cenarios and "B" in cenarios:
        dif = cenarios["A"]["_total"] - cenarios["B"]["_total"]
        r["diferenca_A_B"] = fmt_brl(dif)
        memoria.append(f"Diferença A menos B: R$ {fmt_brl(cenarios['A']['_total'])} - R$ {fmt_brl(cenarios['B']['_total'])}"
                       f" = R$ {fmt_brl(dif)}.")
    return r


def main() -> None:
    args = montar_parser().parse_args()
    try:
        r = executar(args)
        texto = json.dumps(r, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"JSON gravado em {args.saida}")
        else:
            print(texto)
        if args.md:
            gravar_md(args.md, r)
            print(f"Markdown gravado em {args.md}")
    except ValueError as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
