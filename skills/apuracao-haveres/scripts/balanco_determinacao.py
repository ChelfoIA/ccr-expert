#!/usr/bin/env python3
"""
Balanço de determinação a preço de saída na data da resolução (CPC, art. 606).

Parte da skill: apuracao-haveres (v2.0.0).

Lê um JSON com ativos e passivos (valor contábil e valor de saída, conta a conta,
com fundamento), mais as contingências classificadas pelo CPC 25, e devolve o
quadro contábil x preço de saída x ajuste, as provisões adicionais, o patrimônio
líquido contábil e o patrimônio líquido de determinação, com memória reproduzível.

Uso:
    python3 balanco_determinacao.py --entrada assets/exemplo_balanco.json
    python3 balanco_determinacao.py --entrada assets/exemplo_balanco.json \
        --saida balanco.json --md balanco.md --csv balanco.csv

Regras embutidas:
    - Provável: provisiona a diferença entre o valor estimado e o já provisionado.
    - Possível: não provisiona; divulga em nota (quadro separado da saída).
    - Remota: não provisiona nem divulga; fica apenas registrada na memória.
    - Sanidade: ativo ajustado - passivo ajustado - provisões = PL de determinação.
    - Data da resolução conferida contra a hipótese (CPC, art. 605) quando o JSON
      traz data_notificacao, data_obito, data_transito ou data_assembleia.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 28

VERSAO = "2.0.0"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "ROUND_HALF_UP, 2 casas na apresentação"
CENTAVO = Decimal("0.01")

HIPOTESES = {
    "retirada_imotivada": ("CPC, art. 605, II", "sexagésimo dia seguinte ao do recebimento, pela sociedade, da notificação do sócio retirante", "data_notificacao", 60),
    "recesso": ("CPC, art. 605, III", "dia do recebimento, pela sociedade, da notificação do sócio dissidente", "data_notificacao", 0),
    "falecimento": ("CPC, art. 605, I", "data do óbito", "data_obito", 0),
    "retirada_justa_causa": ("CPC, art. 605, IV", "trânsito em julgado da decisão que dissolver a sociedade", "data_transito", 0),
    "exclusao_judicial": ("CPC, art. 605, IV", "trânsito em julgado da decisão que dissolver a sociedade", "data_transito", 0),
    "exclusao_extrajudicial": ("CPC, art. 605, V", "data da assembleia ou da reunião de sócios que deliberou a exclusão", "data_assembleia", 0),
}
PROBABILIDADES = ("provavel", "possivel", "remota")
TIPOS_CONTINGENCIA = ("trabalhista", "fiscal", "civel", "ambiental", "regulatoria", "outra")


class ErroValidacao(Exception):
    """Erro de dado de entrada: sai com código 1 e mensagem objetiva."""


# ----------------------------------------------------------------------------
# Utilidades de número e data (padrão brasileiro e técnico)
# ----------------------------------------------------------------------------

def parse_num(valor, campo="valor"):
    """Aceita 1.234,56 (brasileiro), 1234.56 (técnico) e 12,5% (vira fração)."""
    if valor is None:
        raise ErroValidacao(f"campo '{campo}' ausente")
    if isinstance(valor, bool):
        raise ErroValidacao(f"campo '{campo}' não pode ser booleano")
    if isinstance(valor, (int, float)):
        texto = repr(valor)
    else:
        texto = str(valor)
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
    """Arredonda para 2 casas só na apresentação."""
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def tecnico(valor):
    """Valor monetário em texto técnico exato (1234.56) para consumo por outro script."""
    return str(q2(valor))


def fmt_br(valor, casas=2):
    """Formata 1234.5 como 1.234,50."""
    quantum = Decimal(1).scaleb(-casas)
    texto = f"{Decimal(valor).quantize(quantum, rounding=ROUND_HALF_UP):,.{casas}f}"
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


def moeda(valor):
    return "R$ " + fmt_br(valor)


def parse_data(texto, campo="data"):
    if not texto:
        raise ErroValidacao(f"campo '{campo}' ausente (formato dd/mm/aaaa)")
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ErroValidacao(f"campo '{campo}' fora do formato dd/mm/aaaa: {texto!r}")


def fmt_data(d):
    return d.strftime("%d/%m/%Y")


# ----------------------------------------------------------------------------
# Data da resolução por hipótese (CPC, art. 605)
# ----------------------------------------------------------------------------

def conferir_data_resolucao(dados):
    """Confere a data da resolução informada contra a hipótese do art. 605 do CPC."""
    data_resolucao = parse_data(dados.get("data_resolucao"), "data_resolucao")
    hipotese = (dados.get("hipotese") or "").strip().lower()
    if not hipotese:
        return data_resolucao, {"hipotese": "não informada", "regra": "CPC, art. 605: informar a hipótese para conferência automática da data"}
    if hipotese not in HIPOTESES:
        raise ErroValidacao(f"hipótese desconhecida: {hipotese!r}; use uma de {', '.join(HIPOTESES)}")
    dispositivo, regra, campo_marco, dias = HIPOTESES[hipotese]
    premissa = {"hipotese": hipotese, "dispositivo": dispositivo, "regra": regra}
    marco = dados.get(campo_marco)
    if marco:
        data_marco = parse_data(marco, campo_marco)
        esperada = data_marco + timedelta(days=dias)
        premissa[campo_marco] = fmt_data(data_marco)
        premissa["data_esperada"] = fmt_data(esperada)
        if esperada != data_resolucao:
            raise ErroValidacao(
                f"data_resolucao {fmt_data(data_resolucao)} incompatível com {dispositivo}: "
                f"{regra} = {fmt_data(esperada)} (marco {campo_marco} = {fmt_data(data_marco)}). "
                "Corrija a data ou a hipótese; o balanço só vale se levantado na data legal da resolução."
            )
        premissa["conferencia"] = "data da resolução confere com o marco legal"
    else:
        premissa["conferencia"] = f"marco '{campo_marco}' não informado; data aceita sem conferência automática"
    return data_resolucao, premissa


# ----------------------------------------------------------------------------
# Núcleo do balanço
# ----------------------------------------------------------------------------

def ler_item(item, indice, lado):
    conta = (item.get("conta") or "").strip()
    if not conta:
        raise ErroValidacao(f"{lado}[{indice}] sem 'conta'")
    contabil = parse_num(item.get("valor_contabil"), f"{lado}[{indice}].valor_contabil")
    if contabil < 0:
        raise ErroValidacao(f"{lado}[{indice}] '{conta}': valor contábil negativo; lance contas retificadoras pelo líquido")
    if item.get("valor_saida") is None:
        saida = contabil
        fundamento = (item.get("fundamento") or "").strip() or "sem ajuste: mantido o valor contábil"
    else:
        saida = parse_num(item.get("valor_saida"), f"{lado}[{indice}].valor_saida")
        fundamento = (item.get("fundamento") or "").strip()
        if saida < 0:
            raise ErroValidacao(f"{lado}[{indice}] '{conta}': valor de saída negativo")
        if saida != contabil and not fundamento:
            raise ErroValidacao(f"{lado}[{indice}] '{conta}': ajuste de {moeda(saida - contabil)} sem 'fundamento'; todo ajuste a preço de saída exige base documental")
        if saida == contabil and not fundamento:
            fundamento = "sem ajuste: mantido o valor contábil"
    return {
        "conta": conta,
        "grupo": (item.get("grupo") or "").strip().lower() or "nao_informado",
        "valor_contabil": contabil,
        "valor_saida": saida,
        "ajuste": saida - contabil,
        "fundamento": fundamento,
        "fonte": (item.get("fonte") or "").strip(),
    }


def ler_contingencia(item, indice):
    descricao = (item.get("descricao") or "").strip()
    if not descricao:
        raise ErroValidacao(f"contingencias[{indice}] sem 'descricao'")
    tipo = (item.get("tipo") or "outra").strip().lower()
    if tipo not in TIPOS_CONTINGENCIA:
        raise ErroValidacao(f"contingencias[{indice}] '{descricao}': tipo {tipo!r} inválido; use {', '.join(TIPOS_CONTINGENCIA)}")
    probabilidade = (item.get("probabilidade") or "").strip().lower()
    if probabilidade not in PROBABILIDADES:
        raise ErroValidacao(f"contingencias[{indice}] '{descricao}': probabilidade {probabilidade!r} inválida; use provavel, possivel ou remota (CPC 25)")
    valor = parse_num(item.get("valor"), f"contingencias[{indice}].valor")
    provisionado = parse_num(item.get("provisionado", "0"), f"contingencias[{indice}].provisionado")
    if valor < 0 or provisionado < 0:
        raise ErroValidacao(f"contingencias[{indice}] '{descricao}': valores negativos")
    if provisionado > valor:
        raise ErroValidacao(f"contingencias[{indice}] '{descricao}': provisionado ({moeda(provisionado)}) maior que o valor estimado ({moeda(valor)})")
    if probabilidade == "provavel":
        adicional = valor - provisionado
        tratamento = "provável: provisionar integralmente (CPC 25); provisão adicional = valor estimado - já provisionado"
    elif probabilidade == "possivel":
        adicional = Decimal(0)
        tratamento = "possível: não provisiona; divulgar em nota explicativa do balanço de determinação (CPC 25)"
    else:
        adicional = Decimal(0)
        tratamento = "remota: não provisiona nem divulga (CPC 25); registrada apenas na memória"
    return {
        "descricao": descricao,
        "tipo": tipo,
        "valor": valor,
        "probabilidade": probabilidade,
        "provisionado": provisionado,
        "provisao_adicional": adicional,
        "tratamento": tratamento,
        "fundamento": (item.get("fundamento") or "").strip(),
    }


def somar(itens, chave):
    return sum((i[chave] for i in itens), Decimal(0))


def montar_balanco(dados):
    empresa = (dados.get("empresa") or "").strip()
    if not empresa:
        raise ErroValidacao("campo 'empresa' ausente")
    data_resolucao, premissa_data = conferir_data_resolucao(dados)
    ativos_brutos = dados.get("ativos") or []
    passivos_brutos = dados.get("passivos") or []
    if not ativos_brutos:
        raise ErroValidacao("lista 'ativos' vazia")
    ativos = [ler_item(a, i, "ativos") for i, a in enumerate(ativos_brutos)]
    passivos = [ler_item(p, i, "passivos") for i, p in enumerate(passivos_brutos)]
    contingencias = [ler_contingencia(c, i) for i, c in enumerate(dados.get("contingencias") or [])]

    alertas = []
    if not passivos:
        alertas.append("nenhum passivo informado: confirme se a sociedade realmente não tem obrigações na data da resolução")

    ativo_contabil = somar(ativos, "valor_contabil")
    ativo_saida = somar(ativos, "valor_saida")
    passivo_contabil = somar(passivos, "valor_contabil")
    passivo_saida = somar(passivos, "valor_saida")
    provisoes_adicionais = somar([c for c in contingencias if c["probabilidade"] == "provavel"], "provisao_adicional")
    possiveis = somar([c for c in contingencias if c["probabilidade"] == "possivel"], "valor")
    remotas = somar([c for c in contingencias if c["probabilidade"] == "remota"], "valor")
    intangiveis = somar([a for a in ativos if a["grupo"] in ("intangivel", "fundo_comercio")], "valor_saida")

    pl_contabil = ativo_contabil - passivo_contabil
    pl_determinacao = ativo_saida - passivo_saida - provisoes_adicionais
    ajustes_ativo = somar(ativos, "ajuste")
    ajustes_passivo = somar(passivos, "ajuste")

    # Sanidade por caminho independente: PL contábil + ajustes de ativo - ajustes de passivo - provisões.
    pl_por_ajustes = pl_contabil + ajustes_ativo - ajustes_passivo - provisoes_adicionais
    if q2(pl_por_ajustes) != q2(pl_determinacao):
        raise ErroValidacao(f"sanidade falhou: PL por ajustes {moeda(pl_por_ajustes)} difere de ativo - passivo - provisões {moeda(pl_determinacao)}")

    provisionado_total = somar(contingencias, "provisionado")
    contas_provisao = [p for p in passivos if "provis" in p["conta"].lower()]
    if contingencias and contas_provisao:
        saldo_contas = somar(contas_provisao, "valor_saida")
        if q2(saldo_contas) != q2(provisionado_total):
            alertas.append(f"conta(s) de provisão no passivo somam {moeda(saldo_contas)}, mas as contingências informam {moeda(provisionado_total)} já provisionados: concilie antes de fechar o laudo")
    for c in contingencias:
        if c["probabilidade"] != "provavel" and c["provisionado"] > 0:
            alertas.append(f"contingência '{c['descricao']}' classificada como {c['probabilidade']} tem {moeda(c['provisionado'])} provisionados na contabilidade: pelo CPC 25 a provisão só cabe à provável; avalie a reversão no valor de saída do passivo")
    if pl_determinacao < 0:
        alertas.append("PL de determinação negativo: a quota patrimonial do sócio será nula ou negativa; ver alerta em haveres_socio.py")

    memoria = [
        f"Passo 1. Balanço de partida: {dados.get('fonte_balanco') or 'fonte não informada (informe fonte_balanco)'}; data da resolução {fmt_data(data_resolucao)} ({premissa_data.get('dispositivo', 'CPC, art. 605')}).",
        f"Passo 2. Ativo: contábil {moeda(ativo_contabil)}; a preço de saída {moeda(ativo_saida)}; ajuste líquido {moeda(ajustes_ativo)} em {len(ativos)} contas, cada uma com fundamento próprio.",
        f"Passo 3. Passivo: contábil {moeda(passivo_contabil)}; a preço de saída {moeda(passivo_saida)}; ajuste líquido {moeda(ajustes_passivo)}.",
        f"Passo 4. Contingências (CPC 25): prováveis geram provisão adicional de {moeda(provisoes_adicionais)}; possíveis divulgadas em nota somam {moeda(possiveis)}; remotas registradas somam {moeda(remotas)}.",
        f"Passo 5. PL contábil = {moeda(ativo_contabil)} - {moeda(passivo_contabil)} = {moeda(pl_contabil)}.",
        f"Passo 6. PL de determinação = {moeda(ativo_saida)} - {moeda(passivo_saida)} - {moeda(provisoes_adicionais)} = {moeda(pl_determinacao)} (CPC, art. 606: bens e direitos, tangíveis e intangíveis, e passivo a preço de saída).",
        f"Passo 7. Sanidade: PL contábil + ajustes de ativo - ajustes de passivo - provisões = {moeda(pl_por_ajustes)}; confere com o passo 6.",
        f"Passo 8. Intangíveis já reconhecidos no ativo (grupo intangivel ou fundo_comercio): {moeda(intangiveis)}; PL de determinação tangível = {moeda(pl_determinacao - intangiveis)} (base do fundo_comercio.py).",
    ]
    contas_lucros = [p["conta"] for p in passivos if any(k in p["conta"].lower() for k in ("lucro", "dividendo", "jcp", "juros sobre o capital"))]
    if contas_lucros:
        memoria.append(f"Passo 9. Conta(s) de lucros ou dividendos a pagar no passivo ({'; '.join(contas_lucros)}) já reduzem o PL de determinação; a parte do sócio nesses valores entra pelo CPC, art. 608, em haveres_socio.py (--lucros-declarados), sem dupla contagem.")

    def serializar_item(i):
        return {
            "conta": i["conta"], "grupo": i["grupo"],
            "valor_contabil": tecnico(i["valor_contabil"]), "valor_saida": tecnico(i["valor_saida"]),
            "ajuste": tecnico(i["ajuste"]), "fundamento": i["fundamento"], "fonte": i["fonte"],
        }

    def serializar_contingencia(c):
        return {
            "descricao": c["descricao"], "tipo": c["tipo"], "probabilidade": c["probabilidade"],
            "valor": tecnico(c["valor"]), "provisionado": tecnico(c["provisionado"]),
            "provisao_adicional": tecnico(c["provisao_adicional"]), "tratamento": c["tratamento"],
            "fundamento": c["fundamento"],
        }

    return {
        "script": "balanco_determinacao.py",
        "versao": VERSAO,
        "premissas": {
            "empresa": empresa,
            "cnpj": dados.get("cnpj", ""),
            "processo": dados.get("processo", ""),
            "data_resolucao": fmt_data(data_resolucao),
            "data_resolucao_conferencia": premissa_data,
            "criterio": "CPC, art. 606: valor patrimonial apurado em balanço de determinação, ativo e passivo a preço de saída na data da resolução",
            "contingencias": "CPC 25: provável provisiona; possível divulga; remota não provisiona nem divulga",
            "fonte_balanco": dados.get("fonte_balanco", ""),
            "valores_em": "texto técnico exato (1234.56), sem arredondamento intermediário",
        },
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "ativos": [serializar_item(a) for a in ativos],
        "passivos": [serializar_item(p) for p in passivos],
        "contingencias": [serializar_contingencia(c) for c in contingencias],
        "totais": {
            "ativo_contabil": tecnico(ativo_contabil),
            "ativo_saida": tecnico(ativo_saida),
            "ajustes_ativo": tecnico(ajustes_ativo),
            "passivo_contabil": tecnico(passivo_contabil),
            "passivo_saida": tecnico(passivo_saida),
            "ajustes_passivo": tecnico(ajustes_passivo),
            "provisoes_adicionais": tecnico(provisoes_adicionais),
            "contingencias_possiveis_divulgadas": tecnico(possiveis),
            "contingencias_remotas_registradas": tecnico(remotas),
            "pl_contabil": tecnico(pl_contabil),
            "pl_determinacao": tecnico(pl_determinacao),
            "ajuste_liquido_pl": tecnico(pl_determinacao - pl_contabil),
            "intangiveis_reconhecidos": tecnico(intangiveis),
            "pl_determinacao_tangivel": tecnico(pl_determinacao - intangiveis),
        },
        "sanidade": {
            "formula": "ativo_saida - passivo_saida - provisoes_adicionais = pl_determinacao",
            "por_ajustes": tecnico(pl_por_ajustes),
            "fecha": True,
        },
        "alertas": alertas,
        "memoria": memoria,
    }


# ----------------------------------------------------------------------------
# Saídas
# ----------------------------------------------------------------------------

def gravar_md(resultado, caminho):
    p = resultado["premissas"]
    t = resultado["totais"]
    linhas = [
        f"# Balanço de determinação: {p['empresa']}",
        "",
        f"Data da resolução: {p['data_resolucao']} ({p['data_resolucao_conferencia'].get('dispositivo', 'CPC, art. 605')}). Critério: {p['criterio']}.",
        "",
        "## Ativo",
        "",
        "| Conta | Grupo | Contábil | Preço de saída | Ajuste | Fundamento |",
        "|---|---|---:|---:|---:|---|",
    ]
    for a in resultado["ativos"]:
        linhas.append(f"| {a['conta']} | {a['grupo']} | {fmt_br(a['valor_contabil'])} | {fmt_br(a['valor_saida'])} | {fmt_br(a['ajuste'])} | {a['fundamento']} |")
    linhas += [f"| Total do ativo | | {fmt_br(t['ativo_contabil'])} | {fmt_br(t['ativo_saida'])} | {fmt_br(t['ajustes_ativo'])} | |", "", "## Passivo", "", "| Conta | Grupo | Contábil | Preço de saída | Ajuste | Fundamento |", "|---|---|---:|---:|---:|---|"]
    for a in resultado["passivos"]:
        linhas.append(f"| {a['conta']} | {a['grupo']} | {fmt_br(a['valor_contabil'])} | {fmt_br(a['valor_saida'])} | {fmt_br(a['ajuste'])} | {a['fundamento']} |")
    linhas += [f"| Total do passivo | | {fmt_br(t['passivo_contabil'])} | {fmt_br(t['passivo_saida'])} | {fmt_br(t['ajustes_passivo'])} | |", "", "## Contingências (CPC 25)", "", "| Descrição | Tipo | Probabilidade | Valor estimado | Já provisionado | Provisão adicional | Tratamento |", "|---|---|---|---:|---:|---:|---|"]
    for c in resultado["contingencias"]:
        linhas.append(f"| {c['descricao']} | {c['tipo']} | {c['probabilidade']} | {fmt_br(c['valor'])} | {fmt_br(c['provisionado'])} | {fmt_br(c['provisao_adicional'])} | {c['tratamento'].split(':')[0]} |")
    linhas += [
        "", "## Patrimônio líquido", "",
        "| Rubrica | Valor (R$) |", "|---|---:|",
        f"| PL contábil | {fmt_br(t['pl_contabil'])} |",
        f"| Ajustes de ativo a preço de saída | {fmt_br(t['ajustes_ativo'])} |",
        f"| Ajustes de passivo a preço de saída | ({fmt_br(t['ajustes_passivo'])}) |",
        f"| Provisões adicionais (contingências prováveis) | ({fmt_br(t['provisoes_adicionais'])}) |",
        f"| PL de determinação | {fmt_br(t['pl_determinacao'])} |",
        f"| Intangíveis já reconhecidos | {fmt_br(t['intangiveis_reconhecidos'])} |",
        f"| PL de determinação tangível | {fmt_br(t['pl_determinacao_tangivel'])} |",
        "", "Contingências possíveis divulgadas em nota: R$ " + fmt_br(t["contingencias_possiveis_divulgadas"]) + ".", "",
        "## Memória de cálculo", "",
    ]
    linhas += [f"- {m}" for m in resultado["memoria"]]
    if resultado["alertas"]:
        linhas += ["", "## Alertas", ""] + [f"- {a}" for a in resultado["alertas"]]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def gravar_csv(resultado, caminho):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["lado", "conta", "grupo", "valor_contabil", "valor_saida", "ajuste", "fundamento"])
        for lado, chave in (("ativo", "ativos"), ("passivo", "passivos")):
            for i in resultado[chave]:
                w.writerow([lado, i["conta"], i["grupo"], fmt_br(i["valor_contabil"]), fmt_br(i["valor_saida"]), fmt_br(i["ajuste"]), i["fundamento"]])
        for c in resultado["contingencias"]:
            w.writerow(["contingencia", c["descricao"], c["probabilidade"], fmt_br(c["valor"]), fmt_br(c["provisionado"]), fmt_br(c["provisao_adicional"]), c["tratamento"]])


def main():
    parser = argparse.ArgumentParser(description="Balanço de determinação a preço de saída (CPC, art. 606) com contingências pelo CPC 25.")
    parser.add_argument("--entrada", required=True, help="JSON com empresa, data_resolucao, hipotese, ativos, passivos e contingencias (ver assets/exemplo_balanco.json)")
    parser.add_argument("--saida", help="arquivo JSON de saída; padrão: stdout")
    parser.add_argument("--md", help="grava o quadro do balanço em Markdown neste caminho")
    parser.add_argument("--csv", help="grava o quadro conta a conta em CSV (separador ;) neste caminho")
    args = parser.parse_args()
    try:
        caminho = Path(args.entrada)
        if not caminho.is_file():
            raise ErroValidacao(f"arquivo de entrada não encontrado: {caminho}")
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ErroValidacao(f"JSON inválido em {caminho}: {exc}")
        resultado = montar_balanco(dados)
        texto = json.dumps(resultado, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"Balanço gravado em {args.saida}", file=sys.stderr)
        else:
            print(texto)
        if args.md:
            gravar_md(resultado, args.md)
            print(f"Quadro Markdown gravado em {args.md}", file=sys.stderr)
        if args.csv:
            gravar_csv(resultado, args.csv)
            print(f"CSV gravado em {args.csv}", file=sys.stderr)
        t = resultado["totais"]
        print(f"PL contábil {moeda(t['pl_contabil'])} | PL de determinação {moeda(t['pl_determinacao'])} | provisões adicionais {moeda(t['provisoes_adicionais'])}", file=sys.stderr)
        for a in resultado["alertas"]:
            print(f"ALERTA: {a}", file=sys.stderr)
    except ErroValidacao as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
