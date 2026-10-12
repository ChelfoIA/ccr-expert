#!/usr/bin/env python3
"""
Fundo de comércio (goodwill, aviamento) como intangível na data da resolução.

Parte da skill: apuracao-haveres (v2.0.0).

Mensura o intangível não registrado que integra o balanço de determinação
(CPC, art. 606: bens e direitos do ativo, tangíveis e intangíveis, a preço de
saída) a partir de resultados históricos normalizados, sem projetar fluxos
futuros. O método de fluxo de caixa descontado (dcf) é recusado porque a
jurisprudência do STJ o considera inadequado para apuração de haveres.

Métodos aceitos:
    lucro-excedente  fundo = (lucro médio normalizado - PL tangível x taxa) x fator
    multiplo         fundo = lucro médio normalizado x múltiplo - PL tangível

Uso:
    python3 fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json
    python3 fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json \
        --balanco balanco.json --metodo lucro-excedente --saida fundo.json --md fundo.md
    python3 fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json --metodo dcf
        (recusa com explicação jurídica e código de saída 1)
"""

import argparse
import json
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 28

VERSAO = "2.0.0"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
CENTAVO = Decimal("0.01")
METODOS = ("lucro-excedente", "multiplo", "dcf")
ROTULOS = {
    "lucro_medio_normalizado": "Lucro médio normalizado",
    "pl_determinacao_tangivel": "PL de determinação tangível",
    "taxa_remuneracao_capital": "Taxa de remuneração do capital",
    "remuneracao_capital": "Remuneração do capital tangível",
    "lucro_excedente": "Lucro excedente anual",
    "fator": "Fator (anos de lucro excedente)",
    "multiplo": "Múltiplo sobre o lucro normalizado",
    "valor_referencia_por_multiplo": "Valor de referência por múltiplo",
    "fundo_comercio": "Fundo de comércio na data da resolução",
}

RECUSA_DCF = (
    "método 'dcf' recusado. O fluxo de caixa descontado projeta lucros futuros e desconta a valor presente, "
    "o que a jurisprudência do STJ considera inadequado para apuração de haveres: o critério legal é o valor "
    "patrimonial em balanço de determinação a preço de saída na data da resolução (CPC, art. 606; CC, art. 1.031), "
    "no qual o fundo de comércio entra como intangível mensurado naquela data, não como expectativa de resultados "
    "posteriores à saída do sócio. Precedentes (Turmas do STJ, nenhum vinculante): REsp 1.877.331 (3ª Turma, "
    "j. 13/04/2021), REsp 1.904.252 (4ª Turma, j. 22/08/2023), REsp 2.174.631 (3ª Turma, j. 17/03/2025), "
    "REsp 1.900.838 (3ª Turma, j. 28/04/2025), AgInt nos EDcl no REsp 2.160.132 (3ª Turma, j. 28/04/2025) e "
    "AgInt no AgInt no AREsp 2.903.904 (4ª Turma, j. 08/06/2026). Use --metodo lucro-excedente ou --metodo multiplo. "
    "Se o contrato social prever expressamente o fluxo de caixa descontado, trate a cláusula na skill contrato-social "
    "e registre a controvérsia no laudo; o script continua não calculando DCF."
)

NOTA_JURIDICA = (
    "O valor apurado mensura o fundo de comércio como intangível existente na data da resolução, a partir de "
    "resultados históricos normalizados (capacidade de gerar lucro acima da remuneração do capital tangível). "
    "Não projeta fluxos de caixa futuros nem desconta expectativas posteriores à saída do sócio, em linha com a "
    "jurisprudência do STJ que afasta o fluxo de caixa descontado na apuração de haveres (REsp 1.877.331, "
    "REsp 1.904.252, REsp 2.174.631, REsp 1.900.838, AgInt no AgInt no AREsp 2.903.904) e integra o intangível "
    "ao balanço de determinação (CPC, art. 606)."
)


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
    return fmt_br(Decimal(fracao) * 100, 2) + "%"


def parse_data(texto, campo="data"):
    if not texto:
        raise ErroValidacao(f"campo '{campo}' ausente (formato dd/mm/aaaa)")
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ErroValidacao(f"campo '{campo}' fora do formato dd/mm/aaaa: {texto!r}")


def ler_json(caminho, rotulo):
    p = Path(caminho)
    if not p.is_file():
        raise ErroValidacao(f"{rotulo} não encontrado: {p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ErroValidacao(f"JSON inválido em {p}: {exc}")


# ----------------------------------------------------------------------------
# Núcleo
# ----------------------------------------------------------------------------

def ler_exercicios(lista, permitir_menos):
    if not isinstance(lista, list) or not lista:
        raise ErroValidacao("lista 'lucros' vazia: informe de 3 a 5 exercícios com lucro contábil e ajustes")
    if len(lista) < 3 and not permitir_menos:
        raise ErroValidacao(f"apenas {len(lista)} exercício(s) informado(s); a normalização exige de 3 a 5 (use --permitir-menos-exercicios para forçar, declarando a limitação no laudo)")
    exercicios = []
    for i, e in enumerate(lista):
        rotulo = str(e.get("exercicio") or "").strip()
        if not rotulo:
            raise ErroValidacao(f"lucros[{i}] sem 'exercicio'")
        lucro = parse_num(e.get("lucro_contabil"), f"lucros[{i}].lucro_contabil")
        ajustes = []
        for j, a in enumerate(e.get("ajustes") or []):
            desc = (a.get("descricao") or "").strip()
            if not desc:
                raise ErroValidacao(f"lucros[{i}].ajustes[{j}] sem 'descricao'")
            ajustes.append({"descricao": desc, "valor": parse_num(a.get("valor"), f"lucros[{i}].ajustes[{j}].valor")})
        peso = parse_num(e.get("peso", "1"), f"lucros[{i}].peso")
        if peso <= 0:
            raise ErroValidacao(f"lucros[{i}] peso deve ser positivo")
        total_ajustes = sum((a["valor"] for a in ajustes), Decimal(0))
        exercicios.append({
            "exercicio": rotulo, "lucro_contabil": lucro, "ajustes": ajustes,
            "total_ajustes": total_ajustes, "lucro_ajustado": lucro + total_ajustes,
            "peso": peso, "fonte": (e.get("fonte") or "").strip(),
        })
    return exercicios


def ler_taxa(bloco):
    if not isinstance(bloco, dict):
        raise ErroValidacao("'taxa_remuneracao_capital' deve ser objeto com valor, descricao e fonte")
    taxa = parse_num(bloco.get("valor"), "taxa_remuneracao_capital.valor")
    nota = ""
    if taxa > 1:
        taxa = taxa / Decimal(100)
        nota = "valor informado acima de 1 interpretado como pontos percentuais"
    if taxa <= 0 or taxa > 1:
        raise ErroValidacao("taxa de remuneração do capital deve ficar entre 0 e 100% (ex.: 12% ou 0,12)")
    fonte = (bloco.get("fonte") or "").strip()
    if not fonte:
        raise ErroValidacao("taxa_remuneracao_capital sem 'fonte': a taxa nunca é digitada de memória; informe a origem (ex.: bcb.gov.br/SGS, série e data de consulta)")
    return taxa, (bloco.get("descricao") or "").strip(), fonte, nota


def ler_parametro(bloco, nome):
    if not isinstance(bloco, dict):
        raise ErroValidacao(f"'{nome}' deve ser objeto com valor e fundamento")
    valor = parse_num(bloco.get("valor"), f"{nome}.valor")
    if valor <= 0:
        raise ErroValidacao(f"{nome} deve ser positivo")
    fundamento = (bloco.get("fundamento") or "").strip()
    if not fundamento:
        raise ErroValidacao(f"{nome} sem 'fundamento': explique a escolha (setor, risco, prática pericial, laudos comparáveis)")
    return valor, fundamento


def obter_pl_tangivel(dados, balanco):
    if balanco is not None:
        totais = balanco.get("totais") or {}
        if "pl_determinacao_tangivel" not in totais:
            raise ErroValidacao("JSON do balanço sem totais.pl_determinacao_tangivel; gere-o com balanco_determinacao.py v2")
        return parse_num(totais["pl_determinacao_tangivel"], "balanco.totais.pl_determinacao_tangivel"), f"balanco_determinacao.py ({balanco.get('premissas', {}).get('empresa', '')}, data da resolução {balanco.get('premissas', {}).get('data_resolucao', '')})"
    if dados.get("pl_determinacao_tangivel") is None:
        raise ErroValidacao("informe 'pl_determinacao_tangivel' no JSON ou passe --balanco com a saída de balanco_determinacao.py")
    return parse_num(dados["pl_determinacao_tangivel"], "pl_determinacao_tangivel"), (dados.get("fonte_pl") or "informado no JSON de entrada").strip()


def calcular(dados, metodo, balanco=None, permitir_menos=False):
    if metodo == "dcf":
        raise ErroValidacao(RECUSA_DCF)
    if metodo not in METODOS:
        raise ErroValidacao(f"método desconhecido: {metodo}")
    empresa = (dados.get("empresa") or "").strip()
    data_resolucao = parse_data(dados.get("data_resolucao"), "data_resolucao")
    if balanco is not None and balanco.get("premissas", {}).get("data_resolucao") not in (None, "", data_resolucao.strftime("%d/%m/%Y")):
        raise ErroValidacao(f"data_resolucao do JSON ({data_resolucao.strftime('%d/%m/%Y')}) difere da do balanço ({balanco['premissas']['data_resolucao']})")
    exercicios = ler_exercicios(dados.get("lucros"), permitir_menos)
    alertas = []
    if len(exercicios) > 5:
        alertas.append(f"{len(exercicios)} exercícios informados: a prática usa de 3 a 5; justifique a série longa")
    pl_tangivel, fonte_pl = obter_pl_tangivel(dados, balanco)

    soma_pesos = sum((e["peso"] for e in exercicios), Decimal(0))
    lucro_medio = sum((e["lucro_ajustado"] * e["peso"] for e in exercicios), Decimal(0)) / soma_pesos
    ponderada = any(e["peso"] != 1 for e in exercicios)

    memoria = [
        f"Passo 1. Série de resultados: {len(exercicios)} exercícios ({exercicios[0]['exercicio']} a {exercicios[-1]['exercicio']}), lucro contábil ajustado por itens não recorrentes, cada ajuste descrito.",
    ]
    for e in exercicios:
        detalhe = "; ".join(f"{a['descricao']} {moeda(a['valor'])}" for a in e["ajustes"]) or "sem ajustes"
        memoria.append(f"  {e['exercicio']}: lucro contábil {moeda(e['lucro_contabil'])}, ajustes {moeda(e['total_ajustes'])} ({detalhe}), lucro ajustado {moeda(e['lucro_ajustado'])}, peso {fmt_br(e['peso'], 2)}.")
    memoria.append(f"Passo 2. Lucro médio normalizado ({'média ponderada' if ponderada else 'média aritmética'}) = {moeda(lucro_medio)}.")
    memoria.append(f"Passo 3. PL de determinação tangível = {moeda(pl_tangivel)} (fonte: {fonte_pl}).")

    sensibilidade = []
    if metodo == "lucro-excedente":
        taxa, taxa_desc, taxa_fonte, taxa_nota = ler_taxa(dados.get("taxa_remuneracao_capital"))
        fator, fator_fund = ler_parametro(dados.get("fator"), "fator")
        remuneracao = pl_tangivel * taxa
        excedente = lucro_medio - remuneracao
        fundo = excedente * fator if excedente > 0 else Decimal(0)
        memoria.append(f"Passo 4. Remuneração do capital tangível = {moeda(pl_tangivel)} x {pct(taxa)} = {moeda(remuneracao)} (taxa: {taxa_desc}; fonte: {taxa_fonte}).")
        memoria.append(f"Passo 5. Lucro excedente = {moeda(lucro_medio)} - {moeda(remuneracao)} = {moeda(excedente)}.")
        if excedente > 0:
            memoria.append(f"Passo 6. Fundo de comércio = {moeda(excedente)} x fator {fmt_br(fator, 2)} = {moeda(fundo)} (fator: {fator_fund}).")
        else:
            memoria.append("Passo 6. Lucro excedente nulo ou negativo: não há evidência de intangível acima da remuneração do capital; fundo de comércio = R$ 0,00.")
            alertas.append("sem lucro excedente: fundo de comércio zerado; registre no laudo que o resultado histórico não remunera o capital tangível")
        for delta in (Decimal(-1), Decimal(0), Decimal(1)):
            f_alt = fator + delta
            if f_alt <= 0:
                continue
            sensibilidade.append({"parametro": "fator", "valor": fmt_br(f_alt, 2), "fundo_comercio": tecnico(excedente * f_alt if excedente > 0 else Decimal(0))})
        for delta_pp in (Decimal("-0.01"), Decimal("0.01")):
            t_alt = taxa + delta_pp
            if t_alt <= 0:
                continue
            exc_alt = lucro_medio - pl_tangivel * t_alt
            sensibilidade.append({"parametro": "taxa", "valor": pct(t_alt), "fundo_comercio": tecnico(exc_alt * fator if exc_alt > 0 else Decimal(0))})
        resultado = {
            "lucro_medio_normalizado": tecnico(lucro_medio),
            "pl_determinacao_tangivel": tecnico(pl_tangivel),
            "taxa_remuneracao_capital": pct(taxa),
            "remuneracao_capital": tecnico(remuneracao),
            "lucro_excedente": tecnico(excedente),
            "fator": fmt_br(fator, 2),
            "fundo_comercio": tecnico(fundo),
        }
        parametros = {"taxa": {"valor": pct(taxa), "descricao": taxa_desc, "fonte": taxa_fonte, "nota": taxa_nota}, "fator": {"valor": fmt_br(fator, 2), "fundamento": fator_fund}}
    else:
        multiplo, mult_fund = ler_parametro(dados.get("multiplo"), "multiplo")
        valor_empresa = lucro_medio * multiplo
        fundo = valor_empresa - pl_tangivel if valor_empresa > pl_tangivel else Decimal(0)
        memoria.append(f"Passo 4. Valor de referência por múltiplo = {moeda(lucro_medio)} x {fmt_br(multiplo, 2)} = {moeda(valor_empresa)} (múltiplo: {mult_fund}).")
        if fundo > 0:
            memoria.append(f"Passo 5. Fundo de comércio = {moeda(valor_empresa)} - {moeda(pl_tangivel)} = {moeda(fundo)}.")
        else:
            memoria.append("Passo 5. Valor por múltiplo não supera o PL tangível: fundo de comércio = R$ 0,00.")
            alertas.append("múltiplo sobre o lucro normalizado não supera o PL tangível: fundo de comércio zerado")
        for delta in (Decimal(-1), Decimal(0), Decimal(1)):
            m_alt = multiplo + delta
            if m_alt <= 0:
                continue
            v_alt = lucro_medio * m_alt
            sensibilidade.append({"parametro": "multiplo", "valor": fmt_br(m_alt, 2), "fundo_comercio": tecnico(v_alt - pl_tangivel if v_alt > pl_tangivel else Decimal(0))})
        resultado = {
            "lucro_medio_normalizado": tecnico(lucro_medio),
            "pl_determinacao_tangivel": tecnico(pl_tangivel),
            "multiplo": fmt_br(multiplo, 2),
            "valor_referencia_por_multiplo": tecnico(valor_empresa),
            "fundo_comercio": tecnico(fundo),
        }
        parametros = {"multiplo": {"valor": fmt_br(multiplo, 2), "fundamento": mult_fund}}

    memoria.append("Passo final. O valor mensura o intangível na data da resolução; não projeta fluxos futuros (ver nota_juridica).")
    return {
        "script": "fundo_comercio.py",
        "versao": VERSAO,
        "premissas": {
            "empresa": empresa,
            "data_resolucao": data_resolucao.strftime("%d/%m/%Y"),
            "metodo": metodo,
            "criterio": "fundo de comércio como intangível integrante do balanço de determinação (CPC, art. 606), mensurado na data da resolução por resultados históricos normalizados",
            "fonte_pl_tangivel": fonte_pl,
            "media": "ponderada por peso" if ponderada else "aritmética simples",
            "parametros": parametros,
        },
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "exercicios": [{
            "exercicio": e["exercicio"], "lucro_contabil": tecnico(e["lucro_contabil"]),
            "ajustes": [{"descricao": a["descricao"], "valor": tecnico(a["valor"])} for a in e["ajustes"]],
            "total_ajustes": tecnico(e["total_ajustes"]), "lucro_ajustado": tecnico(e["lucro_ajustado"]),
            "peso": fmt_br(e["peso"], 2), "fonte": e["fonte"],
        } for e in exercicios],
        "resultado": resultado,
        "sensibilidade": sensibilidade,
        "nota_juridica": NOTA_JURIDICA,
        "alertas": alertas,
        "memoria": memoria,
    }


def gravar_md(saida, caminho):
    r = saida["resultado"]
    linhas = [
        f"# Fundo de comércio na data da resolução: {saida['premissas']['empresa']}",
        "",
        f"Método: {saida['premissas']['metodo']}. Data da resolução: {saida['premissas']['data_resolucao']}.",
        "",
        "| Exercício | Lucro contábil | Ajustes | Lucro ajustado | Peso |",
        "|---|---:|---:|---:|---:|",
    ]
    for e in saida["exercicios"]:
        linhas.append(f"| {e['exercicio']} | {fmt_br(e['lucro_contabil'])} | {fmt_br(e['total_ajustes'])} | {fmt_br(e['lucro_ajustado'])} | {e['peso']} |")
    linhas += ["", "| Rubrica | Valor |", "|---|---:|"]
    for k, v in r.items():
        rotulo = ROTULOS.get(k, k.replace("_", " "))
        valor = v if k in ("taxa_remuneracao_capital", "fator", "multiplo") else fmt_br(v)
        linhas.append(f"| {rotulo} | {valor} |")
    linhas += ["", "## Sensibilidade", "", "| Parâmetro | Valor | Fundo de comércio (R$) |", "|---|---:|---:|"]
    for s in saida["sensibilidade"]:
        linhas.append(f"| {s['parametro']} | {s['valor']} | {fmt_br(s['fundo_comercio'])} |")
    linhas += ["", "## Memória de cálculo", ""] + [f"- {m}" for m in saida["memoria"]]
    linhas += ["", "## Nota jurídica", "", saida["nota_juridica"]]
    if saida["alertas"]:
        linhas += ["", "## Alertas", ""] + [f"- {a}" for a in saida["alertas"]]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Fundo de comércio como intangível na data da resolução (lucro excedente ou múltiplo); recusa DCF.")
    parser.add_argument("--entrada", required=True, help="JSON com lucros dos exercícios, taxa de remuneração do capital (com fonte), fator ou múltiplo (com fundamento) e, opcionalmente, pl_determinacao_tangivel")
    parser.add_argument("--balanco", help="JSON gerado por balanco_determinacao.py; fornece o PL de determinação tangível e confere a data")
    parser.add_argument("--metodo", choices=METODOS, default="lucro-excedente", help="lucro-excedente (padrão), multiplo, ou dcf (recusado com explicação)")
    parser.add_argument("--saida", help="arquivo JSON de saída; padrão: stdout")
    parser.add_argument("--md", help="grava quadro e memória em Markdown neste caminho")
    parser.add_argument("--permitir-menos-exercicios", action="store_true", help="aceita menos de 3 exercícios, declarando a limitação")
    args = parser.parse_args()
    try:
        dados = ler_json(args.entrada, "arquivo de entrada")
        balanco = ler_json(args.balanco, "JSON do balanço") if args.balanco else None
        saida = calcular(dados, args.metodo, balanco, args.permitir_menos_exercicios)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"Fundo de comércio gravado em {args.saida}", file=sys.stderr)
        else:
            print(texto)
        if args.md:
            gravar_md(saida, args.md)
            print(f"Quadro Markdown gravado em {args.md}", file=sys.stderr)
        r = saida["resultado"]
        print(f"Lucro médio normalizado {moeda(r['lucro_medio_normalizado'])} | fundo de comércio ({args.metodo}) {moeda(r['fundo_comercio'])}", file=sys.stderr)
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
