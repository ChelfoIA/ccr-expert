#!/usr/bin/env python3
"""
matriz_quesitos.py: matriz quesito -> seção do laudo -> evidência -> cenário -> status.

Parte da skill: pericia-pasep-laudo-judicial

O script recebe os quesitos do juízo, do autor e do réu (Banco do Brasil e/ou
União), classifica cada um por tema e por tipo (fato contábil, questão de
direito, misto ou fora do objeto) com regras simples de palavra-chave, sugere a
seção do laudo, a evidência necessária e o cenário em que a resposta se apoia,
e checa a cobertura: nenhum quesito pode ficar sem resposta ou sem seção. Para
questão de direito, a abertura da resposta é devolvida ao juízo na forma
"questão de direito, cabe ao juízo; do ponto de vista contábil...". Não há
cálculo monetário: o valor de cada cenário vem do motor da skill pericia-pasep.

Uso:
    python3 scripts/matriz_quesitos.py --quesitos assets/exemplo_quesitos.json --md matriz.md --csv matriz.csv
    python3 scripts/matriz_quesitos.py --quesitos quesitos.json --documentos assets/exemplo_documentos.json --saida matriz.json
    python3 scripts/matriz_quesitos.py --quesitos quesitos.json --registro lote.json --processo P-002 --rigoroso

Entrada: lista JSON de objetos {proponente, numero, texto, tema?, status?,
secao_resposta?} ou objeto {"processo": {...}, "quesitos": [...]}.
Códigos de saída: 0 sucesso; 1 erro de validação ou erro inesperado;
com --rigoroso, cobertura incompleta também sai com código 1.
"""

import argparse
import csv
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

SKILL = "pericia-pasep-laudo-judicial"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "não se aplica: script de organização, sem cálculo monetário"

PROPONENTES = ("juizo", "autor", "reu")
TEMAS = ("saldo", "saques", "indices", "prescricao", "polo", "juros", "outro")
TIPOS = ("fato contábil", "questão de direito", "misto", "fora do objeto")
STATUS_VALIDOS = ("a_responder", "respondido", "prejudicado", "fora_do_objeto", "pendente_diligencia", "questao_de_direito")

# Palavras-chave já normalizadas (sem acento, minúsculas). A ordem das listas importa:
# fora do objeto vence; depois questão de direito; depois tema.
FORA_DO_OBJETO = (
    "dano moral", "danos morais", "honorarios advocaticios", "sucumbencia", "fgts", "pis-caixa", "abono salarial",
    "lucros cessantes", "assedio", "conduta do advogado", "litigancia de ma-fe", "litigancia de ma fe",
)
QUESTAO_DE_DIREITO = (
    "prescri", "decaden", "actio nata", "legitimidade", "ilegitimidade", "parte legitima", "polo passivo",
    "onus da prova", "inversao do onus", "redistribui", "responsabilidade", "culpa", "dever de indenizar",
    "ilicito", "ma-fe", "ma fe", "abusiv", "nulidade", "nulo", "codigo de defesa do consumidor", "cdc",
    "relacao de consumo", "procedencia", "improcedencia", "direito do autor", "devido", "indevido",
    "deve ser condenad", "cabe ao banco", "cabe a uniao", "fazenda publica", "interpretacao", "aplicavel ao caso",
)
# Verbos e expressões de fato que, presentes junto a uma palavra de direito, tornam o quesito misto
MARCADORES_DE_FATO = (
    "data", "quando", "em que momento", "qual o valor", "quanto", "quantifique", "apure", "calcule", "demonstre",
    "memoria", "extrato", "lancamento", "saldo", "indique o documento", "consta dos autos", "ha nos autos",
    "qual o saldo", "classifique", "identifique",
)
# Temas de qualificação jurídica (prescrição e polo) pesam o dobro e vêm primeiro: a palavra "saque"
# aparece em quase todo quesito de PASEP e não pode decidir o tema sozinha.
TEMA_KW = {
    "prescricao": ("prescri", "actio nata", "ciencia", "tomou conhecimento", "quinquen", "decenal", "sumula 85",
                   "trato sucessivo", "ultimo creditamento", "termo inicial"),
    "polo": ("legitimidade", "polo passivo", "litiscons", "banco do brasil e uniao", "responsabilidade", "responsavel",
             "condenad", "indenizar", "quem responde", "ma gestao", "ma-gestao"),
    "saldo": ("saldo", "qual o saldo", "saldo que", "evolucao", "reconstru", "cotas", "quotas", "deposito", "contribui",
              "rais", "credito de cotas", "periodo", "abertura da conta", "migra"),
    "saques": ("saque", "retirada", "debito", "saida", "microfilm", "recibo", "assinatura", "biometri", "modalidade",
               "fopag", "folha de pagamento", "credito em conta", "conta corrente", "conta-corrente", "caixa", "desfalque"),
    "indices": ("indice", "correcao", "expurgo", "tjlp", "rla", "atualizacao monetaria", "conselho diretor", "rendimento",
                "valorizacao", "rac", "percentual oficial", "tesouro", "ipca", "selic", "inpc", "tr "),
    "juros": ("juros", "mora", "taxa legal", "capitaliza", "anatocismo", "ec 113", "ec 136", "emenda constitucional"),
}
PESO_TEMA = {"prescricao": 2, "polo": 2}

# Mapa tema -> seção do laudo (numeração do assets/template_laudo_pasep.md), evidência, cenário
MAPA_TEMA = {
    "saldo": {
        "secao": "5.2 Reconstrução do saldo",
        "evidencia": "extrato analítico completo; RAIS ou ficha financeira; tabela do Tesouro (percentuais oficiais)",
        "cenario": "n/a: fato apurado antes da atualização (quadro de conciliação)",
        "documentos": ("extrato_analitico", "rais"),
    },
    "saques": {
        "secao": "5.3 Saídas, modalidade e comprovação (Tema 1.300/STJ)",
        "evidencia": "extrato analítico; microfilmagem ou recibo (CAIXA-BB); extrato da conta de destino (CREDITO-CC); contracheques (FOPAG)",
        "cenario": "n/a: fato apurado; a saída sem comprovação entra no quadro com a ressalva de ônus",
        "documentos": ("extrato_analitico", "microfilmagem", "conta_destino", "contracheques"),
    },
    "indices": {
        "secao": "5.4 Índices, rendimentos e conciliação",
        "evidencia": "tabela de valorização do Tesouro Nacional; séries BCB SGS com data de consulta; memória do motor pericia-pasep",
        "cenario": "A a D (o índice de cada cenário é premissa rotulada)",
        "documentos": ("extrato_analitico",),
    },
    "juros": {
        "secao": "6 Cenários de atualização",
        "evidencia": "memória de cenarios_atualizacao.py; data da citação; regime por polo (CC art. 406 para o BB; EC 113/2021 e 136/2025 para a União)",
        "cenario": "A e B (BB); C e D (União)",
        "documentos": ("extrato_analitico",),
    },
    "prescricao": {
        "secao": "6 Cenários de atualização (prescrição como premissa de cenário)",
        "evidencia": "datas de fato: ciência do desfalque, último creditamento, propositura e citação, com o documento de cada uma",
        "cenario": "todos, cada um com o corte prescricional que a tese pressupõe (decenal BB; quinquenal União com Súmula 85/STJ)",
        "documentos": ("extrato_analitico",),
    },
    "polo": {
        "secao": "6 Cenários de atualização (polo passivo como premissa de cenário)",
        "evidencia": "causa de pedir de cada diferença (índice, expurgo, saque, omissão de rendimento) e a origem documental",
        "cenario": "A e B se a diferença decorre de gestão do BB; C e D se decorre de índice ou expurgo (União)",
        "documentos": ("extrato_analitico",),
    },
    "outro": {
        "secao": "5 Análise (subseção a definir pelo perito)",
        "evidencia": "a definir conforme o quesito",
        "cenario": "a definir",
        "documentos": (),
    },
}

ABERTURAS = {
    "fato contábil": "Ver seção {secao}. [Resposta objetiva, com remissão ao quadro e ao documento de fls. ...]",
    "questão de direito": (
        "Trata-se de questão de direito, cuja definição cabe ao juízo. Do ponto de vista contábil, "
        "{complemento}"
    ),
    "misto": (
        "A qualificação jurídica do ponto cabe ao juízo. Quanto ao fato, {complemento_fato} "
        "Ver seção {secao}."
    ),
    "fora do objeto": (
        "O quesito extrapola o objeto da perícia fixado na decisão de saneamento e os limites do art. 473, § 2º, do CPC; "
        "a perícia deixa de respondê-lo, sem prejuízo de o juízo ampliar o objeto, hipótese em que o ponto será examinado em esclarecimentos."
    ),
}
COMPLEMENTO_DIREITO = {
    "prescricao": "a perícia registra as datas de fato relevantes (ciência do desfalque, último creditamento, propositura e citação, seção 5.1) e apresenta, na seção 6, o valor de cada cenário com e sem o corte prescricional que cada tese pressupõe, sem adotar nenhum deles.",
    "polo": "a perícia identifica a origem de cada diferença (índice, expurgo, saque ou omissão de rendimento, seção 5.4) e segrega os valores por origem na seção 6, sem atribuir responsabilidade a qualquer dos réus.",
    "saques": "a perícia classifica cada saída por modalidade e informa se há, nos autos, a comprovação correspondente (seção 5.3), sem valorar a quem o ônus aproveita.",
    "indices": "a perícia apresenta o índice aplicado em cada cenário, com fonte e data de consulta, e o efeito de cada alternativa (seção 6).",
    "juros": "a perícia apresenta os juros de cada cenário segundo o regime que cada tese pressupõe, com o fundamento rotulado no quadro (seção 6).",
    "saldo": "a perícia apresenta o saldo reconstruído e a conciliação com o extrato (seção 5.2), sem conclusão sobre o direito às diferenças.",
    "outro": "a perícia apresenta os elementos de fato que constam dos autos sobre o ponto (seção 5).",
}
COMPLEMENTO_FATO = {
    "prescricao": "as datas constam da seção 5.1 com o documento de cada uma;",
    "polo": "a origem de cada diferença consta da seção 5.4 e a segregação por origem, da seção 6;",
    "saques": "a modalidade e a comprovação de cada saída constam do quadro da seção 5.3;",
    "indices": "os índices aplicados e suas fontes constam da seção 5.4;",
    "juros": "os juros de cada cenário constam da seção 6;",
    "saldo": "o saldo reconstruído e a conciliação constam da seção 5.2;",
    "outro": "os elementos de fato constam da seção 5;",
}


class ErroValidacao(Exception):
    """Erro de dado de entrada: mensagem clara para a perita, saída com código 1."""


def normaliza(texto):
    """Minúsculas, sem acento e com espaços simples, para comparação de palavras-chave."""
    t = unicodedata.normalize("NFKD", str(texto or ""))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", t).strip()


def parse_data(texto, campo="data"):
    """Converte 'dd/mm/aaaa' em date."""
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        raise ErroValidacao(f"{campo} inválido: '{texto}' (esperado dd/mm/aaaa)")


def carrega_json(caminho, descricao):
    """Lê um arquivo JSON com mensagem clara em caso de falha."""
    p = Path(caminho)
    if not p.exists():
        raise ErroValidacao(f"{descricao} não encontrado: {caminho}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErroValidacao(f"{descricao} com JSON inválido ({caminho}): {e}")


def carrega_quesitos(caminho):
    """Aceita lista de quesitos ou objeto {processo, quesitos}; valida campos."""
    dados = carrega_json(caminho, "Arquivo de quesitos")
    processo = {}
    if isinstance(dados, dict):
        processo = dados.get("processo") or {}
        quesitos = dados.get("quesitos")
    else:
        quesitos = dados
    if not isinstance(quesitos, list) or not quesitos:
        raise ErroValidacao("o arquivo precisa conter uma lista 'quesitos' não vazia (ou ser a própria lista)")
    vistos = set()
    saida = []
    for i, q in enumerate(quesitos, start=1):
        if not isinstance(q, dict):
            raise ErroValidacao(f"quesito na posição {i} não é um objeto JSON")
        prop = normaliza(q.get("proponente"))
        prop = {"juízo": "juizo", "juiz": "juizo", "réu": "reu", "re": "reu", "ré": "reu", "banco": "reu", "uniao": "reu", "bb": "reu"}.get(prop, prop)
        if prop not in PROPONENTES:
            raise ErroValidacao(f"quesito {i}: proponente '{q.get('proponente')}' inválido; use {', '.join(PROPONENTES)}")
        texto = str(q.get("texto") or "").strip()
        if not texto:
            raise ErroValidacao(f"quesito {i}: 'texto' vazio")
        try:
            numero = int(q.get("numero"))
        except (TypeError, ValueError):
            raise ErroValidacao(f"quesito {i}: 'numero' precisa ser inteiro")
        chave = (prop, numero)
        if chave in vistos:
            raise ErroValidacao(f"numeração duplicada: {prop} nº {numero}")
        vistos.add(chave)
        tema = normaliza(q.get("tema")) or ""
        tema = {"índices": "indices", "prescrição": "prescricao"}.get(tema, tema)
        if tema and tema not in TEMAS:
            raise ErroValidacao(f"quesito {prop} nº {numero}: tema '{q.get('tema')}' inválido; use {', '.join(TEMAS)}")
        status = normaliza(q.get("status")) or "a_responder"
        if status not in STATUS_VALIDOS:
            raise ErroValidacao(f"quesito {prop} nº {numero}: status '{q.get('status')}' inválido; use {', '.join(STATUS_VALIDOS)}")
        saida.append({
            "proponente": prop,
            "proponente_rotulo": str(q.get("proponente_rotulo") or {"juizo": "Juízo", "autor": "Autor", "reu": "Réu"}[prop]),
            "numero": numero,
            "texto": texto,
            "tema_declarado": tema,
            "status_informado": status,
            "secao_resposta_informada": str(q.get("secao_resposta") or "").strip(),
        })
    return processo, saida


def infere_tema(texto_norm):
    """Tema por contagem ponderada de palavras-chave; empate resolvido pela ordem de TEMA_KW."""
    pontos = {}
    for tema, kws in TEMA_KW.items():
        pontos[tema] = PESO_TEMA.get(tema, 1) * sum(1 for k in kws if k in texto_norm)
    melhor = max(pontos.items(), key=lambda kv: kv[1])
    return melhor[0] if melhor[1] > 0 else "outro"


def classifica(q):
    """Define tema, tipo e palavras que motivaram a classificação."""
    t = normaliza(q["texto"])
    motivos = []
    fora = [k for k in FORA_DO_OBJETO if k in t]
    direito = [k for k in QUESTAO_DE_DIREITO if k in t]
    fato = [k for k in MARCADORES_DE_FATO if k in t]
    tema = q["tema_declarado"] or infere_tema(t)
    if fora:
        tipo = "fora do objeto"
        motivos = fora
    elif direito and fato:
        tipo = "misto"
        motivos = direito + fato
    elif direito:
        tipo = "questão de direito"
        motivos = direito
    else:
        tipo = "fato contábil"
        motivos = fato
    # Tema prescrição e polo são, por natureza, questão de direito quando perguntam o "se"
    if tema in ("prescricao", "polo") and tipo == "fato contábil":
        tipo = "misto"
        motivos.append(f"tema {tema} pressupõe qualificação jurídica")
    return tema, tipo, motivos


def abertura_resposta(tema, tipo, secao):
    """Texto de abertura da resposta, neutro, conforme o tipo."""
    if tipo == "questão de direito":
        return ABERTURAS[tipo].format(complemento=COMPLEMENTO_DIREITO[tema])
    if tipo == "misto":
        return ABERTURAS[tipo].format(complemento_fato=COMPLEMENTO_FATO[tema], secao=secao)
    if tipo == "fora do objeto":
        return ABERTURAS[tipo]
    return ABERTURAS[tipo].format(secao=secao)


def obtem_documentos(args):
    """Estados dos documentos (opcional), do arquivo de documentos ou do registro do lote."""
    if args.documentos:
        proc = carrega_json(args.documentos, "Arquivo de documentos")
    elif args.registro and args.processo:
        reg = carrega_json(args.registro, "Registro do lote")
        procs = reg.get("processos") if isinstance(reg, dict) else None
        if not isinstance(procs, list):
            raise ErroValidacao("registro sem a lista 'processos'")
        proc = next((p for p in procs if p.get("id") == args.processo), None)
        if proc is None:
            raise ErroValidacao(f"processo '{args.processo}' não existe no registro")
    elif args.registro or args.processo:
        raise ErroValidacao("--registro e --processo precisam ser informados juntos")
    else:
        return None, {}
    docs = proc.get("documentos") if isinstance(proc, dict) else None
    if not isinstance(docs, dict):
        raise ErroValidacao("o processo informado não tem o objeto 'documentos'")
    modalidades = proc.get("modalidades_alegadas") or []
    return proc, {"documentos": docs, "modalidades": modalidades}


def documentos_relevantes(tema, contexto):
    """Filtra os documentos do tema pelas modalidades alegadas (quando houver)."""
    docs = list(MAPA_TEMA[tema]["documentos"])
    if tema == "saques" and contexto:
        mods = set(contexto.get("modalidades") or [])
        filtro = {"microfilmagem": "CAIXA-BB", "conta_destino": "CREDITO-CC", "contracheques": "FOPAG"}
        docs = [d for d in docs if d not in filtro or filtro[d] in mods]
    return docs


def monta_matriz(quesitos, contexto):
    """Classifica todos os quesitos e define status e seção."""
    linhas = []
    textos_vistos = {}
    for q in quesitos:
        tema, tipo, motivos = classifica(q)
        mapa = MAPA_TEMA[tema]
        secao = q["secao_resposta_informada"] or mapa["secao"]
        docs = documentos_relevantes(tema, contexto)
        pendentes = []
        if contexto:
            estados = contexto["documentos"]
            pendentes = [d for d in docs if estados.get(d, "pendente") in ("pendente", "parcial")]

        status = q["status_informado"]
        if status == "a_responder":
            if tipo == "fora do objeto":
                status = "fora_do_objeto"
            elif tipo == "questão de direito":
                status = "questao_de_direito"
            elif pendentes:
                status = "pendente_diligencia"
        chave_texto = normaliza(q["texto"])
        remissao = textos_vistos.get(chave_texto)
        if remissao is None:
            textos_vistos[chave_texto] = f"{q['proponente_rotulo']} nº {q['numero']}"

        linhas.append({
            "proponente": q["proponente"],
            "proponente_rotulo": q["proponente_rotulo"],
            "numero": q["numero"],
            "texto": q["texto"],
            "tema": tema,
            "tema_origem": "declarado" if q["tema_declarado"] else "inferido por palavra-chave",
            "tipo": tipo,
            "motivos": motivos,
            "secao_laudo": secao,
            "evidencia": mapa["evidencia"],
            "documentos_exigidos": docs,
            "documentos_pendentes": pendentes,
            "cenario": mapa["cenario"],
            "status": status,
            "repete": remissao or "",
            "abertura_resposta": abertura_resposta(tema, tipo, secao) if not remissao else f"Respondido no quesito {remissao}, ao qual se remete.",
        })
    return linhas


def cobertura(linhas):
    """Checagem de cobertura: tudo classificado, tudo com seção, nada 'a_responder' sem motivo."""
    total = len(linhas)
    sem_secao = [f"{l['proponente_rotulo']} nº {l['numero']}" for l in linhas if not l["secao_laudo"]]
    abertos = [f"{l['proponente_rotulo']} nº {l['numero']}" for l in linhas if l["status"] == "a_responder"]
    pendentes = [f"{l['proponente_rotulo']} nº {l['numero']}" for l in linhas if l["status"] == "pendente_diligencia"]
    direito = [f"{l['proponente_rotulo']} nº {l['numero']}" for l in linhas if l["tipo"] == "questão de direito"]
    fora = [f"{l['proponente_rotulo']} nº {l['numero']}" for l in linhas if l["tipo"] == "fora do objeto"]
    inferidos = [f"{l['proponente_rotulo']} nº {l['numero']}" for l in linhas if l["tema_origem"] != "declarado"]
    cobertos = total - len(abertos) - len(sem_secao)
    por_prop = {}
    for l in linhas:
        por_prop[l["proponente"]] = por_prop.get(l["proponente"], 0) + 1
    por_tipo = {}
    for l in linhas:
        por_tipo[l["tipo"]] = por_tipo.get(l["tipo"], 0) + 1
    return {
        "total": total,
        "por_proponente": por_prop,
        "por_tipo": por_tipo,
        "cobertos": cobertos,
        "percentual_cobertura": f"{(100 * cobertos / total):.1f}%".replace(".", ","),
        "sem_secao": sem_secao,
        "a_responder": abertos,
        "pendentes_de_diligencia": pendentes,
        "devolvidos_ao_juizo": direito,
        "fora_do_objeto": fora,
        "tema_inferido_conferir": inferidos,
        "completa": not abertos and not sem_secao,
    }


def rotulo_resposta(l):
    """'do juízo', 'do autor', 'do réu' e, se houver, o detalhe entre parênteses do rótulo (ex.: 'do réu (BB)')."""
    base = {"juizo": "do juízo", "autor": "do autor", "reu": "do réu"}[l["proponente"]]
    r = l["proponente_rotulo"]
    return base + (" " + r[r.find("("):] if "(" in r else "")


def monta_md(processo, linhas, cob, hoje):
    """Matriz em Markdown."""
    md = []
    titulo = processo.get("numero") or processo.get("id") or ""
    md.append(f"# Matriz de quesitos PASEP {titulo}".rstrip())
    md.append("")
    md.append(f"Data de referência: {hoje}. Quesitos: {cob['total']} (" + "; ".join(f"{k}: {v}" for k, v in sorted(cob["por_proponente"].items())) + f"). Cobertura: {cob['percentual_cobertura']}.")
    md.append("")
    md.append("| Proponente | Nº | Quesito | Tema | Tipo | Seção do laudo | Evidência | Cenário | Status |")
    md.append("|---|---:|---|---|---|---|---|---|---|")
    for l in linhas:
        texto = l["texto"].replace("|", "/")
        md.append(f"| {l['proponente_rotulo']} | {l['numero']} | {texto} | {l['tema']} | {l['tipo']} | {l['secao_laudo']} | {l['evidencia']} | {l['cenario']} | {l['status']} |")
    md.append("")
    md.append("## Aberturas de resposta sugeridas")
    md.append("")
    for l in linhas:
        md.append(f"> Quesito {l['numero']} {rotulo_resposta(l)}: \"{l['texto']}\"")
        md.append(f"> Resposta: {l['abertura_resposta']}")
        md.append("")
    md.append("## Checagem de cobertura")
    md.append("")
    md.append(f"- Devolvidos ao juízo como questão de direito: {', '.join(cob['devolvidos_ao_juizo']) or 'nenhum'}")
    md.append(f"- Fora do objeto: {', '.join(cob['fora_do_objeto']) or 'nenhum'}")
    md.append(f"- Pendentes de diligência: {', '.join(cob['pendentes_de_diligencia']) or 'nenhum'}")
    md.append(f"- Sem resposta prevista: {', '.join(cob['a_responder']) or 'nenhum'}")
    md.append(f"- Tema inferido por palavra-chave (conferir): {', '.join(cob['tema_inferido_conferir']) or 'nenhum'}")
    md.append("")
    md.append("Nota: a classificação por palavra-chave é auxiliar; a leitura de cada quesito pelo perito prevalece. A resposta final de cada quesito é redigida no laudo, com remissão à seção e ao documento.")
    return "\n".join(md) + "\n"


def grava_csv(caminho, linhas):
    """Matriz em CSV (separador ;)."""
    colunas = ["proponente", "numero", "texto", "tema", "tipo", "secao_laudo", "evidencia", "cenario", "status", "documentos_pendentes", "repete"]
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
        w.writeheader()
        for l in linhas:
            linha = {c: l.get(c, "") for c in colunas}
            linha["documentos_pendentes"] = ", ".join(l["documentos_pendentes"])
            w.writerow(linha)


def main():
    """Ponto de entrada."""
    parser = argparse.ArgumentParser(description="Matriz de quesitos da perícia judicial do PASEP: tema, tipo, seção do laudo, evidência, cenário, status e cobertura.")
    parser.add_argument("--quesitos", required=True, help="Arquivo JSON com os quesitos (ex.: assets/exemplo_quesitos.json)")
    parser.add_argument("--documentos", help="Arquivo JSON do processo com 'documentos' (ex.: assets/exemplo_documentos.json), para marcar quesitos pendentes de diligência")
    parser.add_argument("--registro", help="Registro do lote (lote.json) gerado por lote_pasep.py, alternativa a --documentos")
    parser.add_argument("--processo", help="Id do processo no registro (ex.: P-002), usado com --registro")
    parser.add_argument("--hoje", help="Data de referência dd/mm/aaaa (padrão: data do sistema)")
    parser.add_argument("--rigoroso", action="store_true", help="Sai com código 1 se a cobertura não estiver completa")
    parser.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    parser.add_argument("--md", help="Grava a matriz em Markdown neste arquivo")
    parser.add_argument("--csv", help="Grava a matriz em CSV (separador ;) neste arquivo")
    args = parser.parse_args()
    try:
        hoje = parse_data(args.hoje, "--hoje") if args.hoje else date.today()
        hoje_txt = hoje.strftime("%d/%m/%Y")
        processo, quesitos = carrega_quesitos(args.quesitos)
        proc_docs, contexto = obtem_documentos(args)
        if proc_docs and not processo:
            processo = {k: proc_docs.get(k, "") for k in ("id", "numero", "vara", "comarca", "autor", "reus")}
        linhas = monta_matriz(quesitos, contexto)
        cob = cobertura(linhas)

        # Sanidade: uma linha por quesito; todo quesito com tipo e tema válidos
        if len(linhas) != len(quesitos):
            raise RuntimeError("inconsistência interna: a matriz não tem uma linha por quesito")
        for l in linhas:
            if l["tipo"] not in TIPOS or l["tema"] not in TEMAS:
                raise RuntimeError(f"inconsistência interna: quesito {l['proponente']} nº {l['numero']} sem tipo ou tema válido")

        md = monta_md(processo, linhas, cob, hoje_txt)
        if args.md:
            Path(args.md).write_text(md, encoding="utf-8")
        if args.csv:
            grava_csv(args.csv, linhas)

        resultado = {
            "skill": SKILL,
            "processo": processo,
            "premissas": {
                "data_referencia": hoje_txt,
                "classificacao": "palavra-chave auxiliar; fora do objeto vence; direito + marcador de fato = misto; tema prescrição ou polo nunca é fato puro",
                "questao_de_direito": "devolvida ao juízo com a forma 'questão de direito, cabe ao juízo; do ponto de vista contábil...'",
                "documentos": "quando informados, documento pendente ou parcial marca o quesito como pendente_diligencia",
                "secoes": "numeração do assets/template_laudo_pasep.md",
            },
            "locale": LOCALE,
            "arredondamento": ARREDONDAMENTO,
            "cobertura": cob,
            "matriz": linhas,
            "matriz_markdown": md,
            "memoria": [f"quesitos lidos: {len(quesitos)}; linhas da matriz: {len(linhas)}; cobertura {cob['percentual_cobertura']}"]
                       + [f"{l['proponente_rotulo']} nº {l['numero']}: tema {l['tema']} ({l['tema_origem']}); tipo {l['tipo']}; motivos: {', '.join(l['motivos']) or 'nenhum marcador'}; status {l['status']}" for l in linhas],
        }
        texto = json.dumps(resultado, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"Saída gravada em {args.saida}")
        else:
            print(texto)
        if args.rigoroso and not cob["completa"]:
            print(f"ERRO de validação: cobertura incompleta; sem resposta prevista: {', '.join(cob['a_responder']) or 'nenhum'}; sem seção: {', '.join(cob['sem_secao']) or 'nenhum'}", file=sys.stderr)
            sys.exit(1)
    except ErroValidacao as e:
        print(f"ERRO de validação: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"ERRO: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
