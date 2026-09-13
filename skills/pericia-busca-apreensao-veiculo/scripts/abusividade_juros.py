#!/usr/bin/env python3
"""
Teste técnico de abusividade dos juros remuneratórios em financiamento de
veículo: converte taxas mensal e anual (juros compostos), compara a taxa
contratada com a taxa média de mercado do BACEN da modalidade e do mês da
contratação, mede razão e spread, aplica o limiar declarado e testa os sinais
de capitalização (anual informada acima do duodécuplo da mensal; capitalização
diária sem taxa diária informada).
Parte da skill: pericia-busca-apreensao-veiculo

Antifabricação: a taxa média nunca é estimada. Entra por parâmetro, com
--fonte e --competencia obrigatórios. O limiar (padrão 1,5 vez a média) é
premissa usual de jurisprudência, declarada como tal, e não norma: o REsp
1.061.530 fala em discrepância substancial, sem percentual fixo.

Uso:
    python3 scripts/abusividade_juros.py --entrada assets/exemplo_abusividade_juros.json --md teste_juros.md
    python3 scripts/abusividade_juros.py --taxa-contratada-mensal 2,90 --taxa-contratada-anual 40,92 \
        --taxa-media-mensal 1,60 --fonte "BACEN/SGS, série validada em dd/mm/aaaa" --competencia 03/2024
"""
import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 34

SKILL = "pericia-busca-apreensao-veiculo"
VERSAO = "1.0.0"
CEM = Decimal("100")
UM = Decimal(1)
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
TOL_PP = Decimal("0.05")  # tolerância em pontos percentuais para igualdade de taxas anuais


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


def mensal_para_anual(m: Decimal) -> Decimal:
    return (UM + m) ** 12 - UM


def anual_para_mensal(a: Decimal) -> Decimal:
    return (UM + a) ** (UM / Decimal(12)) - UM


def diaria_para_mensal(d: Decimal) -> Decimal:
    return (UM + d) ** 30 - UM


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Teste de abusividade dos juros remuneratórios contra a taxa média do BACEN.")
    p.add_argument("--entrada", help="JSON com os parâmetros (ver assets/exemplo_abusividade_juros.json); flags têm precedência")
    p.add_argument("--taxa-contratada-mensal", help="Taxa remuneratória contratada em %% a.m. (ex.: 2,90)")
    p.add_argument("--taxa-contratada-anual", help="Taxa anual informada no contrato em %% a.a. (opcional)")
    p.add_argument("--taxa-media-mensal", help="Taxa média BACEN da modalidade em %% a.m.")
    p.add_argument("--taxa-media-anual", help="Taxa média BACEN da modalidade em %% a.a. (alternativa)")
    p.add_argument("--fonte", help="Fonte da taxa média (SGS/BACEN, série, data de consulta). Obrigatória")
    p.add_argument("--competencia", help="Competência da taxa média (mm/aaaa). Obrigatória")
    p.add_argument("--serie-sgs", help="Código da série do SGS, apenas documental; validar na API antes de citar")
    p.add_argument("--limiar", help="Múltiplo da média que dispara o veredito 'acima do limiar' (padrão 1,5; premissa, não norma)")
    p.add_argument("--periodicidade-capitalizacao", choices=["mensal", "diaria", "nao-informada"],
                   help="Periodicidade de capitalização prevista no contrato (padrão: mensal)")
    p.add_argument("--taxa-diaria-informada", help="Taxa diária informada no contrato em %% a.d., se houver")
    p.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    p.add_argument("--md", help="Grava o quadro do teste em Markdown")
    return p


def consolidar(args) -> dict:
    """Une JSON de entrada e flags; flag preenchida tem precedência."""
    base = {}
    if args.entrada:
        p = Path(args.entrada)
        if not p.exists():
            raise ValueError(f"arquivo de entrada não encontrado: {args.entrada}")
        with p.open(encoding="utf-8") as fh:
            base = json.load(fh)
    campos = {
        "taxa_contratada_mensal": args.taxa_contratada_mensal,
        "taxa_contratada_anual": args.taxa_contratada_anual,
        "taxa_media_mensal": args.taxa_media_mensal,
        "taxa_media_anual": args.taxa_media_anual,
        "fonte": args.fonte,
        "competencia": args.competencia,
        "serie_sgs": args.serie_sgs,
        "limiar": args.limiar,
        "periodicidade_capitalizacao": args.periodicidade_capitalizacao,
        "taxa_diaria_informada": args.taxa_diaria_informada,
    }
    for k, v in campos.items():
        if v is not None:
            base[k] = v
    if base.get("taxa_contratada_mensal") in (None, ""):
        raise ValueError("taxa contratada mensal ausente (--taxa-contratada-mensal ou campo taxa_contratada_mensal)")
    if base.get("taxa_media_mensal") in (None, "") and base.get("taxa_media_anual") in (None, ""):
        raise ValueError("taxa média ausente: informar --taxa-media-mensal ou --taxa-media-anual, com fonte e competência")
    if not base.get("fonte") or not base.get("competencia"):
        raise ValueError("fonte e competência da taxa média são obrigatórias (antifabricação)")
    base.setdefault("limiar", "1,5")
    base.setdefault("periodicidade_capitalizacao", "mensal")
    return base


def executar(cfg: dict) -> dict:
    memoria = []
    m_c = parse_num(cfg["taxa_contratada_mensal"]) / CEM
    if m_c < 0:
        raise ValueError("taxa contratada mensal negativa")
    a_c_inf = parse_num(cfg["taxa_contratada_anual"]) / CEM if cfg.get("taxa_contratada_anual") not in (None, "") else None
    if cfg.get("taxa_media_mensal") not in (None, ""):
        m_m = parse_num(cfg["taxa_media_mensal"]) / CEM
        a_m = mensal_para_anual(m_m)
        memoria.append(f"Taxa média informada em base mensal: {fmt_num(m_m * CEM, 4)}% a.m.; anual equivalente"
                       f" (1 + m)^12 - 1 = {fmt_num(a_m * CEM, 4)}% a.a.")
    else:
        a_m = parse_num(cfg["taxa_media_anual"]) / CEM
        m_m = anual_para_mensal(a_m)
        memoria.append(f"Taxa média informada em base anual: {fmt_num(a_m * CEM, 4)}% a.a.; mensal equivalente"
                       f" (1 + a)^(1/12) - 1 = {fmt_num(m_m * CEM, 4)}% a.m.")
    if m_m <= 0:
        raise ValueError("taxa média deve ser positiva")
    limiar = parse_num(cfg["limiar"])
    if limiar <= 0:
        raise ValueError("limiar deve ser positivo")

    a_c_eq = mensal_para_anual(m_c)
    memoria.append(f"Taxa contratada {fmt_num(m_c * CEM, 4)}% a.m.; anual equivalente composta (1 + m)^12 - 1 ="
                   f" {fmt_num(a_c_eq * CEM, 4)}% a.a.; duodécuplo 12 x m = {fmt_num(m_c * 12 * CEM, 4)}% a.a.")

    razao_m = m_c / m_m
    razao_a = a_c_eq / a_m
    spread_m = (m_c - m_m) * CEM
    spread_a = (a_c_eq - a_m) * CEM
    memoria.append(f"Razão contratada/média em base mensal: {fmt_num(m_c * CEM, 4)} / {fmt_num(m_m * CEM, 4)} = {fmt_num(razao_m, 4)};"
                   f" em base anual: {fmt_num(a_c_eq * CEM, 4)} / {fmt_num(a_m * CEM, 4)} = {fmt_num(razao_a, 4)}.")
    memoria.append(f"Spread: {fmt_num(spread_m, 4)} p.p. a.m.; {fmt_num(spread_a, 4)} p.p. a.a.")
    if razao_m > limiar:
        veredito = "acima do limiar declarado"
        leitura = (f"a taxa contratada corresponde a {fmt_num(razao_m, 4)} vezes a média da modalidade no mês da contratação,"
                   f" acima do limiar de {fmt_num(limiar, 2)} declarado como premissa; sinal técnico de discrepância substancial"
                   " (REsp 1.061.530). A qualificação jurídica é do juízo")
    elif razao_m > UM:
        veredito = "acima da média, dentro do limiar declarado"
        leitura = (f"a taxa contratada supera a média em {fmt_num(spread_m, 4)} p.p. a.m. ({fmt_num(razao_m, 4)} vezes),"
                   f" sem alcançar o limiar de {fmt_num(limiar, 2)}; a mera superação da média não caracteriza abusividade"
                   " (REsp 1.061.530)")
    else:
        veredito = "igual ou abaixo da média"
        leitura = "a taxa contratada não supera a média da modalidade; ausente sinal técnico de abusividade"
    memoria.append(f"Veredito técnico: {veredito}.")

    # Teste de capitalização pela taxa anual informada
    duodecuplo = m_c * 12
    if a_c_inf is None:
        cap_teste = {"resultado": "taxa anual não informada no contrato",
                     "leitura": ("sem taxa anual no instrumento, o sinal do duodécuplo não pode ser aplicado; a pactuação"
                                 " expressa da capitalização deve ser buscada na cláusula (Súmula 539/STJ); a orientação"
                                 " sobre o duodécuplo é matéria da Súmula 541/STJ [A VERIFICAR]")}
        memoria.append("Capitalização: taxa anual não informada; teste do duodécuplo inaplicável.")
    else:
        dif_eq = abs(a_c_inf - a_c_eq) * CEM
        if a_c_inf > duodecuplo:
            res = "anual informada supera o duodécuplo da mensal"
            leitura_cap = ("sinal de pactuação de capitalização mensal (orientação atribuída à Súmula 541/STJ"
                           " [A VERIFICAR]); " + ("a anual informada coincide com a composta (1 + m)^12 - 1, dentro da tolerância"
                                                  if dif_eq <= TOL_PP else
                                                  f"a anual informada difere da composta em {fmt_num(dif_eq, 4)} p.p., registrar a divergência"))
        elif abs(a_c_inf - duodecuplo) * CEM <= TOL_PP:
            res = "anual informada igual ao duodécuplo da mensal"
            leitura_cap = "taxa anual linear (12 x m): não há sinal de capitalização pela taxa anual; verificar a cláusula"
        else:
            res = "anual informada inferior ao duodécuplo da mensal"
            leitura_cap = "incoerência entre taxas informadas: registrar e confrontar com a planilha do credor"
        cap_teste = {"taxa_anual_informada_pct": fmt_num(a_c_inf * CEM, 4),
                     "duodecuplo_da_mensal_pct": fmt_num(duodecuplo * CEM, 4),
                     "anual_composta_equivalente_pct": fmt_num(a_c_eq * CEM, 4),
                     "diferenca_informada_x_composta_pp": fmt_num(dif_eq, 4),
                     "resultado": res, "leitura": leitura_cap}
        memoria.append(f"Capitalização: anual informada {fmt_num(a_c_inf * CEM, 4)}% x duodécuplo {fmt_num(duodecuplo * CEM, 4)}%"
                       f" x composta {fmt_num(a_c_eq * CEM, 4)}%: {res}.")

    # Teste da capitalização diária
    per = cfg.get("periodicidade_capitalizacao", "mensal")
    diaria = {"periodicidade_contratual": per}
    if per == "diaria":
        if cfg.get("taxa_diaria_informada") in (None, ""):
            diaria["resultado"] = "capitalização diária pactuada sem taxa diária informada"
            diaria["leitura"] = ("o contrato prevê capitalização diária sem informar a taxa diária: sinal de violação do dever"
                                 " de informação, tratado como abusivo no REsp 2.238.832 (Terceira Turma, j. 09/12/2025)")
            memoria.append("Capitalização diária pactuada sem taxa diária informada: sinal do REsp 2.238.832.")
        else:
            d = parse_num(cfg["taxa_diaria_informada"]) / CEM
            m_eq = diaria_para_mensal(d)
            diaria["taxa_diaria_informada_pct"] = fmt_num(d * CEM, 6)
            diaria["mensal_equivalente_pct"] = fmt_num(m_eq * CEM, 4)
            diaria["diferenca_para_mensal_contratada_pp"] = fmt_num((m_eq - m_c) * CEM, 4)
            diaria["resultado"] = "taxa diária informada; conferir equivalência com a mensal"
            diaria["leitura"] = ("com taxa diária informada o dever de informação está atendido quanto à periodicidade;"
                                 " a equivalência (1 + d)^30 - 1 deve coincidir com a mensal contratada")
            memoria.append(f"Capitalização diária com taxa {fmt_num(d * CEM, 6)}% a.d.: mensal equivalente"
                           f" {fmt_num(m_eq * CEM, 4)}% x contratada {fmt_num(m_c * CEM, 4)}%.")
    elif per == "nao-informada":
        diaria["resultado"] = "periodicidade de capitalização não informada"
        diaria["leitura"] = "sem cláusula de periodicidade, a pactuação expressa exigida pela Súmula 539/STJ deve ser demonstrada pelo credor"
    else:
        diaria["resultado"] = "capitalização mensal"
        diaria["leitura"] = "periodicidade mensal; a pactuação expressa é aferida pela cláusula e pelo teste da taxa anual"

    return {
        "skill": SKILL, "script": "abusividade_juros.py", "versao": VERSAO,
        "locale": LOCALE, "arredondamento": ARREDONDAMENTO,
        "premissas": {
            "conversao_de_taxas": "juros compostos: anual = (1 + mensal)^12 - 1; mensal = (1 + anual)^(1/12) - 1",
            "limiar": f"{fmt_num(limiar, 2)} vez a média (premissa usual de jurisprudência; não é norma)",
            "referencial": "taxa média de mercado do BACEN da modalidade no mês da contratação (REsp 1.061.530)",
            "taxa_media": {"mensal_pct": fmt_num(m_m * CEM, 4), "anual_pct": fmt_num(a_m * CEM, 4),
                           "fonte": cfg["fonte"], "competencia": cfg["competencia"],
                           "serie_sgs": cfg.get("serie_sgs") or "não informada (validar na API antes de citar)"},
            "descricao": cfg.get("descricao", ""),
        },
        "taxa_contratada": {"mensal_pct": fmt_num(m_c * CEM, 4), "anual_informada_pct": fmt_num(a_c_inf * CEM, 4) if a_c_inf is not None else "não informada",
                            "anual_composta_equivalente_pct": fmt_num(a_c_eq * CEM, 4), "duodecuplo_pct": fmt_num(duodecuplo * CEM, 4)},
        "comparacao": {"razao_mensal": fmt_num(razao_m, 4), "razao_anual": fmt_num(razao_a, 4),
                       "spread_pp_am": fmt_num(spread_m, 4), "spread_pp_aa": fmt_num(spread_a, 4),
                       "limiar": fmt_num(limiar, 2), "veredito_tecnico": veredito, "leitura": leitura},
        "teste_capitalizacao_taxa_anual": cap_teste,
        "teste_capitalizacao_diaria": diaria,
        "memoria": memoria,
    }


def cap(texto: str) -> str:
    """Inicia a frase com maiúscula para a prosa do Markdown."""
    return texto[:1].upper() + texto[1:] if texto else texto


def gravar_md(caminho: str, r: dict) -> None:
    tc, cp, tm = r["taxa_contratada"], r["comparacao"], r["premissas"]["taxa_media"]
    out = ["# Teste de abusividade dos juros remuneratórios", "",
           f"Taxa média: {tm['mensal_pct']}% a.m. ({tm['anual_pct']}% a.a.), competência {tm['competencia']}, fonte: {tm['fonte']}.", "",
           "| Item | Contratada | Média BACEN | Razão | Spread (p.p.) |", "|---|---|---|---|---|",
           f"| Mensal | {tc['mensal_pct']}% | {tm['mensal_pct']}% | {cp['razao_mensal']} | {cp['spread_pp_am']} |",
           f"| Anual | {tc['anual_composta_equivalente_pct']}% (composta) | {tm['anual_pct']}% | {cp['razao_anual']} | {cp['spread_pp_aa']} |",
           "", f"Veredito técnico (limiar {cp['limiar']}): {cp['veredito_tecnico']}. {cap(cp['leitura'])}.", "",
           f"Capitalização pela taxa anual: {r['teste_capitalizacao_taxa_anual']['resultado']}. {cap(r['teste_capitalizacao_taxa_anual']['leitura'])}.", "",
           f"Capitalização diária: {r['teste_capitalizacao_diaria']['resultado']}. {cap(r['teste_capitalizacao_diaria']['leitura'])}.", "",
           "## Memória de cálculo", ""] + [f"{k + 1}. {m}" for k, m in enumerate(r["memoria"])]
    Path(caminho).write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    args = montar_parser().parse_args()
    try:
        cfg = consolidar(args)
        r = executar(cfg)
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
