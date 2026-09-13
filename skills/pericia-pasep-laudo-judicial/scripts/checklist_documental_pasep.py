#!/usr/bin/env python3
"""
checklist_documental_pasep.py: cruza os documentos recebidos com o que a perícia do PASEP exige.

Parte da skill: pericia-pasep-laudo-judicial

Para cada modalidade de saída alegada (CAIXA-BB, CREDITO-CC, FOPAG) o script
lista o documento exigido, quem deve fornecê-lo, o fundamento do ônus (CPC
art. 373 e Tema 1.300/STJ) e a consequência da falta. Depois gera o texto do
termo de diligência, do ofício ao Banco do Brasil e, quando cabível, do
requerimento à parte autora, todos com placeholders entre colchetes e prazo
sugerido. Não há cálculo monetário: o script decide apenas se o cálculo pode
começar e com quais ressalvas.

Uso:
    python3 scripts/checklist_documental_pasep.py --documentos assets/exemplo_documentos.json --hoje 12/09/2026 --md termo.md
    python3 scripts/checklist_documental_pasep.py --registro lote.json --processo P-002 --prazo-dias 15 --saida checklist.json

Códigos de saída: 0 sucesso; 1 erro de validação ou erro inesperado.
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SKILL = "pericia-pasep-laudo-judicial"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "não se aplica: script de organização, sem cálculo monetário"
ESTADOS_DOCUMENTO = ("recebido", "pendente", "parcial", "nao_aplicavel")
MODALIDADES_VALIDAS = ("CAIXA-BB", "CREDITO-CC", "FOPAG", "OUTROS")

# Documentos exigidos em qualquer perícia de PASEP, independentemente da modalidade
EXIGENCIAS_BASE = [
    {
        "chave": "extrato_analitico",
        "documento": "Extrato analítico completo da conta individual PASEP, desde a abertura (ou desde o primeiro crédito de cotas) até o encerramento ou a migração de 31/05/2020, com todos os lançamentos, códigos de histórico, datas e saldos",
        "fornecedor": "Banco do Brasil S.A., administrador do Fundo",
        "onus": "Dever de exibição do documento comum (CPC arts. 396 a 400); solicitação direta pelo perito (CPC art. 473, § 3º)",
        "consequencia": "Sem o extrato completo não há reconstrução do saldo. Período não coberto entra no laudo como ressalva expressa, nunca como saldo zero.",
    },
    {
        "chave": "rais",
        "documento": "RAIS, ficha financeira ou declaração do órgão empregador que comprove o vínculo, o cadastro PASEP e os períodos de crédito de cotas",
        "fornecedor": "Parte autora ou órgão empregador (por requerimento ao juízo, se necessário)",
        "onus": "Fato constitutivo (CPC art. 373, I); serve para validar os créditos do extrato",
        "consequencia": "Sem RAIS ou ficha financeira, os créditos anuais são aceitos apenas conforme o extrato, com ressalva de ausência de validação cruzada.",
    },
]

# Documento exigido por modalidade de saída (Tema 1.300/STJ)
EXIGENCIAS_POR_MODALIDADE = {
    "CAIXA-BB": {
        "chave": "microfilmagem",
        "documento": "Microfilmagem ou cópia legível do recibo de saque assinado, documento de identificação do recebedor e registro biométrico ou eletrônico da operação, para cada saída em caixa de agência",
        "fornecedor": "Banco do Brasil S.A.",
        "onus": "Réu: fato extintivo (CPC art. 373, II; Tema 1.300/STJ; CC art. 320)",
        "consequencia": "Sem a prova do BB, a saída fica registrada no quadro como 'sem comprovação apresentada pelo réu'. O laudo informa; a valoração do ônus cabe ao juízo.",
    },
    "CREDITO-CC": {
        "chave": "conta_destino",
        "documento": "Extrato da conta-corrente de destino nos meses de cada saída lançada como crédito em conta e no mês seguinte, com identificação de agência e conta",
        "fornecedor": "Parte autora (ou banco de destino, mediante requerimento do autor ao juízo)",
        "onus": "Participante: fato constitutivo (CPC art. 373, I; Tema 1.300/STJ), sem inversão nem redistribuição",
        "consequencia": "Sem o extrato de destino, a alegada não entrada do valor fica 'sem comprovação apresentada pelo autor'. O laudo não presume o desfalque.",
    },
    "FOPAG": {
        "chave": "contracheques",
        "documento": "Contracheques ou fichas financeiras dos meses de cada saída lançada como pagamento em folha (PASEP-FOPAG) e do mês seguinte",
        "fornecedor": "Parte autora ou órgão empregador",
        "onus": "Participante: fato constitutivo (CPC art. 373, I; Tema 1.300/STJ), sem inversão nem redistribuição",
        "consequencia": "Sem os contracheques, a alegada não entrada do valor fica 'sem comprovação apresentada pelo autor'. O laudo não presume o desfalque.",
    },
}

EXIGENCIA_MODALIDADE_DESCONHECIDA = {
    "chave": "identificacao_modalidade",
    "documento": "Identificação, pelo Banco do Brasil, da modalidade de cada saída impugnada (saque em caixa, crédito em conta-corrente, folha de pagamento ou outra), com a legenda dos códigos de histórico do extrato",
    "fornecedor": "Banco do Brasil S.A.",
    "onus": "Pressuposto para aplicar o Tema 1.300/STJ; sem a modalidade não se sabe a quem cabe o ônus",
    "consequencia": "Saída sem modalidade identificada entra no quadro como OUTROS, com ressalva expressa e sem atribuição de ônus pelo perito.",
}


class ErroValidacao(Exception):
    """Erro de dado de entrada: mensagem clara para a perita, saída com código 1."""


def parse_data(texto, campo="data"):
    """Converte 'dd/mm/aaaa' em date."""
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        raise ErroValidacao(f"{campo} inválido: '{texto}' (esperado dd/mm/aaaa)")


def formata_data(d):
    """Formata date como dd/mm/aaaa."""
    return d.strftime("%d/%m/%Y")


def soma_dias_uteis(inicio, n):
    """Avança n dias úteis (segunda a sexta, sem feriados) a partir de inicio."""
    atual = inicio
    contados = 0
    while contados < n:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            contados += 1
    return atual


def carrega_json(caminho, descricao):
    """Lê um arquivo JSON com mensagem clara em caso de falha."""
    p = Path(caminho)
    if not p.exists():
        raise ErroValidacao(f"{descricao} não encontrado: {caminho}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErroValidacao(f"{descricao} com JSON inválido ({caminho}): {e}")


def obtem_processo(args):
    """Carrega o processo do registro do lote ou do arquivo de documentos."""
    if args.documentos:
        proc = carrega_json(args.documentos, "Arquivo de documentos")
    else:
        if not args.registro or not args.processo:
            raise ErroValidacao("informe --documentos arquivo.json ou o par --registro lote.json --processo <id>")
        reg = carrega_json(args.registro, "Registro do lote")
        procs = reg.get("processos") if isinstance(reg, dict) else None
        if not isinstance(procs, list):
            raise ErroValidacao("registro sem a lista 'processos'")
        proc = next((p for p in procs if p.get("id") == args.processo), None)
        if proc is None:
            raise ErroValidacao(f"processo '{args.processo}' não existe no registro")
    if not isinstance(proc, dict):
        raise ErroValidacao("o processo precisa ser um objeto JSON")
    docs = proc.get("documentos")
    if not isinstance(docs, dict) or not docs:
        raise ErroValidacao("o processo precisa ter o objeto 'documentos' com os estados recebidos")
    for nome, estado in docs.items():
        if estado not in ESTADOS_DOCUMENTO:
            raise ErroValidacao(f"documento '{nome}' com estado '{estado}'; use {', '.join(ESTADOS_DOCUMENTO)}")
    modalidades = proc.get("modalidades_alegadas") or []
    for m in modalidades:
        if m not in MODALIDADES_VALIDAS:
            raise ErroValidacao(f"modalidade '{m}' inválida; use {', '.join(MODALIDADES_VALIDAS)}")
    return proc


def avalia(proc):
    """Cruza exigências com documentos recebidos e devolve faltantes, atendidos e conclusão."""
    docs = proc["documentos"]
    modalidades = list(proc.get("modalidades_alegadas") or [])
    saidas = proc.get("saidas_impugnadas") or []
    for s in saidas:
        m = (s.get("modalidade") or "").strip()
        if m and m not in modalidades and m in EXIGENCIAS_POR_MODALIDADE:
            modalidades.append(m)
    sem_modalidade = bool(proc.get("saidas_sem_modalidade")) or any(not (s.get("modalidade") or "").strip() for s in saidas) or ("OUTROS" in modalidades)

    exigencias = list(EXIGENCIAS_BASE)
    for m in modalidades:
        if m in EXIGENCIAS_POR_MODALIDADE:
            exigencias.append(dict(EXIGENCIAS_POR_MODALIDADE[m], modalidade=m))
    if sem_modalidade:
        exigencias.append(EXIGENCIA_MODALIDADE_DESCONHECIDA)

    faltantes, atendidos, avisos = [], [], []
    for ex in exigencias:
        estado = docs.get(ex["chave"], "pendente")
        item = dict(ex, estado_atual=estado)
        if estado == "recebido":
            atendidos.append(item)
        elif estado == "nao_aplicavel":
            avisos.append(f"'{ex['chave']}' marcado como não aplicável, mas a modalidade {ex.get('modalidade', 'base')} o exige: conferir a marcação")
            faltantes.append(item)
        else:
            faltantes.append(item)

    # Extrato parcial: registrar o período coberto e o não coberto
    periodo = proc.get("periodo_extrato_recebido") or {}
    abertura = proc.get("data_abertura_conta")
    if docs.get("extrato_analitico") == "parcial":
        cobertura = f"extrato recebido cobre {periodo.get('de', '[?]')} a {periodo.get('ate', '[?]')}"
        if abertura:
            cobertura += f"; conta aberta em {abertura}"
        avisos.append("extrato analítico parcial: " + cobertura + ". Solicitar o período faltante e ressalvar no laudo.")

    for nome, estado in docs.items():
        if estado == "nao_aplicavel" and nome in ("microfilmagem", "conta_destino", "contracheques"):
            mod = {"microfilmagem": "CAIXA-BB", "conta_destino": "CREDITO-CC", "contracheques": "FOPAG"}[nome]
            if mod in modalidades:
                pass  # já tratado acima como faltante com aviso

    extrato = docs.get("extrato_analitico", "pendente")
    if extrato == "pendente":
        pode_calcular = "não: sem extrato analítico não há base para a reconstrução do saldo"
    elif extrato == "parcial":
        pode_calcular = "parcialmente: reconstruir apenas o período coberto pelo extrato e ressalvar o restante"
    else:
        pode_calcular = "sim: o extrato permite a reconstrução; saídas sem comprovação entram no quadro com a ressalva de ônus"

    return {
        "modalidades_consideradas": modalidades,
        "saidas_sem_modalidade": sem_modalidade,
        "faltantes": faltantes,
        "atendidos": atendidos,
        "avisos": avisos,
        "pode_calcular": pode_calcular,
    }


def bloco_processo(proc):
    """Cabeçalho comum dos textos."""
    reus = ", ".join(proc.get("reus") or ["[RÉU]"])
    return (
        f"Processo nº {proc.get('numero', '[NÚMERO]')}\n"
        f"Juízo: {proc.get('vara', '[VARA]')}, {proc.get('comarca', '[COMARCA]')}\n"
        f"Autor(a): {proc.get('autor', '[AUTOR]')}\n"
        f"Réu(s): {reus}\n"
    )


def texto_termo(proc, aval, prazo_txt, prazo_dias):
    """Termo de diligência dirigido ao juízo e às partes (CPC art. 473, § 3º; art. 474; NBC TP 01)."""
    linhas = []
    linhas.append("TERMO DE DILIGÊNCIA")
    linhas.append("")
    linhas.append(bloco_processo(proc))
    linhas.append("[NOME DO PERITO], contador(a), CRC [UF] [NÚMERO], perito(a) nomeado(a) nos autos, no exercício do encargo (CPC arts. 156 e 466) e com fundamento no art. 473, § 3º, do CPC e na NBC TP 01 (R2), solicita a juntada dos documentos abaixo, indispensáveis à reconstrução da conta individual PASEP nº [CADASTRO PASEP] e à classificação das saídas por modalidade (Tema 1.300/STJ):")
    linhas.append("")
    for i, f in enumerate(aval["faltantes"], start=1):
        linhas.append(f"{i}. {f['documento']}.")
        linhas.append(f"   Fornecedor: {f['fornecedor']}. Estado atual: {f['estado_atual']}. Ônus: {f['onus']}.")
    linhas.append("")
    if aval["avisos"]:
        linhas.append("Observações da perícia:")
        for a in aval["avisos"]:
            linhas.append(f"- {a}")
        linhas.append("")
    linhas.append(f"Prazo sugerido para atendimento: {prazo_dias} dias úteis, até {prazo_txt}, sem prejuízo do prazo que o juízo fixar. Não atendida a solicitação, a perícia requererá ao juízo a determinação de exibição (CPC arts. 396 a 400) e, persistindo a falta, o laudo será entregue com a ressalva expressa da lacuna, sem presunção de valores.")
    linhas.append("")
    linhas.append("As partes e seus assistentes técnicos ficam cientes desta diligência (CPC art. 466, § 2º, e art. 474). Toda comunicação da perícia corre nos autos.")
    linhas.append("")
    linhas.append("[CIDADE], [DATA].")
    linhas.append("[NOME DO PERITO], CRC [UF] [NÚMERO]")
    return "\n".join(linhas)


def texto_oficio_bb(proc, aval, prazo_txt, prazo_dias):
    """Ofício ao Banco do Brasil pelos documentos sob sua guarda."""
    itens = [f for f in aval["faltantes"] if "Banco do Brasil" in f["fornecedor"]]
    if not itens:
        return ""
    linhas = []
    linhas.append("OFÍCIO AO BANCO DO BRASIL S.A.")
    linhas.append("")
    linhas.append("Ao Banco do Brasil S.A., [AGÊNCIA OU CENTRAL DE ATENDIMENTO A DEMANDAS JUDICIAIS], [ENDEREÇO OU CANAL ELETRÔNICO].")
    linhas.append("")
    linhas.append(bloco_processo(proc))
    linhas.append(f"Na condição de perito(a) nomeado(a) pelo juízo (CPC art. 156 e 465), e com fundamento no art. 473, § 3º, do CPC, solicito a apresentação, no prazo de {prazo_dias} dias úteis (até {prazo_txt}), dos documentos relativos à conta individual PASEP nº [CADASTRO PASEP], titular {proc.get('autor', '[AUTOR]')}, CPF 000.000.000-00:")
    linhas.append("")
    for i, f in enumerate(itens, start=1):
        linhas.append(f"{i}. {f['documento']}.")
    linhas.append("")
    saidas = proc.get("saidas_impugnadas") or []
    if saidas:
        linhas.append("Saídas impugnadas nos autos, para as quais se requer a comprovação individualizada:")
        for s in saidas:
            linhas.append(f"- {s.get('data', '[DATA]')}: {s.get('valor', '[VALOR]')}; modalidade informada: {s.get('modalidade') or 'não identificada'}")
        linhas.append("")
    linhas.append("Solicita-se ainda a legenda dos códigos de histórico utilizados no extrato e a indicação de eventual período sem registro, com a justificativa.")
    linhas.append("")
    linhas.append("A entrega pode ser feita por juntada aos autos ou por remessa ao endereço eletrônico da perícia ([E-MAIL]), com cópia para as partes. A ausência de resposta será comunicada ao juízo para os fins dos arts. 396 a 400 do CPC.")
    linhas.append("")
    linhas.append("[CIDADE], [DATA].")
    linhas.append("[NOME DO PERITO], CRC [UF] [NÚMERO], perito(a) do juízo")
    return "\n".join(linhas)


def texto_requerimento_autor(proc, aval, prazo_txt, prazo_dias):
    """Requerimento à parte autora pelos documentos que lhe cabem (CREDITO-CC e FOPAG)."""
    itens = [f for f in aval["faltantes"] if "autora" in f["fornecedor"].lower() or "autor" in f["fornecedor"].lower()]
    if not itens:
        return ""
    linhas = []
    linhas.append("SOLICITAÇÃO À PARTE AUTORA (POR MEIO DO JUÍZO)")
    linhas.append("")
    linhas.append(bloco_processo(proc))
    linhas.append(f"A perícia solicita que a parte autora, por seu(sua) advogado(a), junte aos autos, no prazo de {prazo_dias} dias úteis (até {prazo_txt}), os documentos abaixo, cujo ônus lhe cabe por se tratar de fato constitutivo (CPC art. 373, I; Tema 1.300/STJ):")
    linhas.append("")
    for i, f in enumerate(itens, start=1):
        linhas.append(f"{i}. {f['documento']}.")
    linhas.append("")
    linhas.append("Se o documento estiver em poder do órgão empregador ou de outro banco, a parte pode requerer ao juízo a expedição de ofício. Não vindo o documento, o laudo registrará a saída como 'sem comprovação apresentada pelo autor', sem presumir a não entrada do valor.")
    linhas.append("")
    linhas.append("[CIDADE], [DATA].")
    linhas.append("[NOME DO PERITO], CRC [UF] [NÚMERO], perito(a) do juízo")
    return "\n".join(linhas)


def monta_md(proc, aval, termo, oficio, requerimento, prazo_txt, hoje):
    """Relatório em Markdown com quadro de documentos e textos prontos."""
    md = []
    md.append(f"# Checklist documental PASEP: processo {proc.get('id', '')} {proc.get('numero', '')}")
    md.append("")
    md.append(f"Data de referência: {formata_data(hoje)}. Modalidades consideradas: {', '.join(aval['modalidades_consideradas']) or 'nenhuma alegada (discussão de índices)'}. Saídas sem modalidade: {'sim' if aval['saidas_sem_modalidade'] else 'não'}.")
    md.append("")
    md.append(f"Pode calcular: {aval['pode_calcular']}.")
    md.append("")
    md.append("## Documentos faltantes")
    md.append("")
    md.append("| Nº | Documento | Fornecedor | Estado atual | Ônus e fundamento | Consequência da falta |")
    md.append("|---:|---|---|---|---|---|")
    for i, f in enumerate(aval["faltantes"], start=1):
        md.append(f"| {i} | {f['documento']} | {f['fornecedor']} | {f['estado_atual']} | {f['onus']} | {f['consequencia']} |")
    if not aval["faltantes"]:
        md.append("| - | nenhum documento faltante | | | | |")
    md.append("")
    md.append("## Documentos atendidos")
    md.append("")
    for a in aval["atendidos"]:
        md.append(f"- {a['chave']}: recebido")
    if not aval["atendidos"]:
        md.append("- nenhum")
    md.append("")
    if aval["avisos"]:
        md.append("## Avisos")
        md.append("")
        for a in aval["avisos"]:
            md.append(f"- {a}")
        md.append("")
    md.append(f"Prazo sugerido: {prazo_txt}.")
    md.append("")
    md.append("## Termo de diligência")
    md.append("")
    md.append("```")
    md.append(termo)
    md.append("```")
    md.append("")
    if oficio:
        md.append("## Ofício ao Banco do Brasil")
        md.append("")
        md.append("```")
        md.append(oficio)
        md.append("```")
        md.append("")
    if requerimento:
        md.append("## Solicitação à parte autora")
        md.append("")
        md.append("```")
        md.append(requerimento)
        md.append("```")
        md.append("")
    return "\n".join(md) + "\n"


def main():
    """Ponto de entrada."""
    parser = argparse.ArgumentParser(description="Checklist documental da perícia judicial do PASEP: faltantes por modalidade, termo de diligência e ofício ao BB.")
    parser.add_argument("--documentos", help="Arquivo JSON do processo com 'documentos' e 'modalidades_alegadas' (ex.: assets/exemplo_documentos.json)")
    parser.add_argument("--registro", help="Registro do lote (lote.json) gerado por lote_pasep.py")
    parser.add_argument("--processo", help="Id do processo no registro (ex.: P-002), usado com --registro")
    parser.add_argument("--hoje", help="Data de referência dd/mm/aaaa (padrão: data do sistema)")
    parser.add_argument("--prazo-dias", dest="prazo_dias", type=int, default=15, help="Prazo sugerido em dias úteis para a diligência (padrão 15)")
    parser.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--md", help="Grava o relatório e os textos em Markdown neste arquivo")
    args = parser.parse_args()
    try:
        hoje = parse_data(args.hoje, "--hoje") if args.hoje else date.today()
        if args.prazo_dias <= 0:
            raise ErroValidacao("--prazo-dias precisa ser maior que zero")
        proc = obtem_processo(args)
        aval = avalia(proc)
        prazo = soma_dias_uteis(hoje, args.prazo_dias)
        prazo_txt = formata_data(prazo)
        termo = texto_termo(proc, aval, prazo_txt, args.prazo_dias)
        oficio = texto_oficio_bb(proc, aval, prazo_txt, args.prazo_dias)
        requerimento = texto_requerimento_autor(proc, aval, prazo_txt, args.prazo_dias)
        md = monta_md(proc, aval, termo, oficio, requerimento, prazo_txt, hoje)
        if args.md:
            Path(args.md).write_text(md, encoding="utf-8")

        # Sanidade: todo faltante precisa aparecer no termo; nenhuma exigência pode sumir
        for f in aval["faltantes"]:
            if f["documento"] not in termo:
                raise RuntimeError(f"inconsistência interna: faltante '{f['chave']}' ausente do termo de diligência")

        resultado = {
            "skill": SKILL,
            "processo": {k: proc.get(k, "") for k in ("id", "numero", "vara", "comarca", "autor", "reus", "polo_demandado")},
            "premissas": {
                "data_referencia": formata_data(hoje),
                "prazo_dias_uteis": args.prazo_dias,
                "prazo_sugerido": prazo_txt,
                "dias_uteis": "segunda a sexta, sem feriados; o juízo fixa o prazo definitivo",
                "onus": "CAIXA-BB ao réu (CPC art. 373, II); CREDITO-CC e FOPAG ao participante (CPC art. 373, I); Tema 1.300/STJ",
            },
            "locale": LOCALE,
            "arredondamento": ARREDONDAMENTO,
            "modalidades_consideradas": aval["modalidades_consideradas"],
            "saidas_sem_modalidade": aval["saidas_sem_modalidade"],
            "pode_calcular": aval["pode_calcular"],
            "faltantes": aval["faltantes"],
            "atendidos": [a["chave"] for a in aval["atendidos"]],
            "avisos": aval["avisos"],
            "termo_diligencia": termo,
            "oficio_bb": oficio,
            "requerimento_autor": requerimento,
            "memoria": [
                f"exigências avaliadas: {len(aval['faltantes']) + len(aval['atendidos'])}; faltantes: {len(aval['faltantes'])}; atendidas: {len(aval['atendidos'])}",
                f"modalidades consideradas: {', '.join(aval['modalidades_consideradas']) or 'nenhuma'}",
                f"prazo sugerido: {args.prazo_dias} dias úteis a partir de {formata_data(hoje)} = {prazo_txt}",
            ] + [f"faltante: {f['chave']} ({f['estado_atual']}) -> {f['fornecedor']}" for f in aval["faltantes"]],
        }
        texto = json.dumps(resultado, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"Saída gravada em {args.saida}")
        else:
            print(texto)
    except ErroValidacao as e:
        print(f"ERRO de validação: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"ERRO: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
