#!/usr/bin/env python3
"""
lote_pasep.py: registro, atualização e painel de um lote de perícias judiciais do PASEP.

Parte da skill: pericia-pasep-laudo-judicial

O script organiza os processos em que a perita foi nomeada pelo juízo. Cada
processo tem registro próprio (número, juízo, partes, polo demandado, datas,
prazo do laudo, quesitos recebidos, documentos recebidos, status, próxima
ação e histórico de alterações). Não há cálculo monetário aqui: o cálculo do
PASEP fica no motor da skill pericia-pasep (conciliacao_pasep.py,
cenarios_atualizacao.py, bcb_loader.py e selftest.py).

Uso:
    python3 scripts/lote_pasep.py criar --registro lote.json --perito "Nome da perita"
    python3 scripts/lote_pasep.py adicionar --registro lote.json --processo assets/exemplo_processos_lote.json
    python3 scripts/lote_pasep.py atualizar --registro lote.json --id P-002 --status diligencia \
        --documento microfilmagem=pendente --quesitos reu=6 --proxima-acao "Expedir ofício ao BB"
    python3 scripts/lote_pasep.py painel --registro lote.json --hoje 12/09/2026 --md painel.md --csv painel.csv --saida painel.json

Saída: JSON em stdout (ou no arquivo de --saida) com premissas, locale e a
memória das operações. O painel também sai em Markdown com --md.
Códigos de saída: 0 sucesso; 1 erro de validação ou erro inesperado.
"""

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SKILL = "pericia-pasep-laudo-judicial"
VERSAO_REGISTRO = "1.0.0"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "não se aplica: script de organização, sem cálculo monetário"

STATUS_VALIDOS = (
    "nomeado", "proposta_entregue", "diligencia", "calculo",
    "laudo_entregue", "esclarecimentos", "encerrado",
)
POLOS_VALIDOS = ("BB", "UNIAO", "LITISCONSORCIO")
MODALIDADES_VALIDAS = ("CAIXA-BB", "CREDITO-CC", "FOPAG", "OUTROS")
DOCUMENTOS_PADRAO = ("extrato_analitico", "microfilmagem", "rais", "contracheques", "conta_destino")
ESTADOS_DOCUMENTO = ("recebido", "pendente", "parcial", "nao_aplicavel")
PROPONENTES = ("juizo", "autor", "reu")
CAMPOS_OBRIGATORIOS = ("id", "numero", "vara", "comarca", "autor", "reus", "polo_demandado", "data_nomeacao", "prazo_laudo")
CAMPOS_TEXTO_LIVRES = ("justica", "objeto_saneamento", "data_saneamento", "prazo_esclarecimentos", "assistente_autor", "assistente_reu", "honorarios", "versao_laudo")


class ErroValidacao(Exception):
    """Erro de dado de entrada: mensagem clara para a perita, saída com código 1."""


# ---------------------------------------------------------------------------
# Utilidades de data e arquivo
# ---------------------------------------------------------------------------

def parse_data(texto, campo="data"):
    """Converte 'dd/mm/aaaa' em date. Levanta ErroValidacao se o formato estiver errado."""
    if not texto:
        raise ErroValidacao(f"{campo} vazio; informe no formato dd/mm/aaaa")
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ErroValidacao(f"{campo} inválido: '{texto}' (esperado dd/mm/aaaa)")


def formata_data(d):
    """Formata date como dd/mm/aaaa."""
    return d.strftime("%d/%m/%Y")


def resolve_hoje(texto):
    """Data de referência: --hoje quando informado, senão a data do sistema."""
    return parse_data(texto, "--hoje") if texto else date.today()


def dias_uteis_entre(inicio, fim):
    """
    Conta dias úteis (segunda a sexta) depois de 'inicio' até 'fim', inclusive.
    Resultado negativo quando 'fim' é anterior a 'inicio'. Feriados não são
    considerados: o número serve de alerta, e a contagem oficial do prazo
    (CPC art. 219) fica com a perita, com o calendário forense do tribunal.
    """
    if fim == inicio:
        return 0
    sinal = 1 if fim > inicio else -1
    a, b = (inicio, fim) if fim > inicio else (fim, inicio)
    total = 0
    atual = a + timedelta(days=1)
    while atual <= b:
        if atual.weekday() < 5:
            total += 1
        atual += timedelta(days=1)
    return sinal * total


def carrega_json(caminho, descricao):
    """Lê um arquivo JSON com mensagem de erro clara."""
    p = Path(caminho)
    if not p.exists():
        raise ErroValidacao(f"{descricao} não encontrado: {caminho}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErroValidacao(f"{descricao} com JSON inválido ({caminho}): {e}")


def grava_json(caminho, dados):
    """Grava JSON legível, UTF-8, sem escapar acentos."""
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def carrega_registro(caminho):
    """Lê e valida a estrutura mínima do registro do lote."""
    reg = carrega_json(caminho, "Registro do lote")
    if not isinstance(reg, dict) or "processos" not in reg or not isinstance(reg["processos"], list):
        raise ErroValidacao(f"Registro sem a lista 'processos': {caminho}")
    return reg


def salva_registro(caminho, reg, hoje):
    """Atualiza o carimbo e grava o registro."""
    reg["atualizado_em"] = formata_data(hoje)
    grava_json(caminho, reg)


def localiza(reg, id_proc):
    """Encontra um processo pelo id, ou levanta ErroValidacao."""
    for p in reg["processos"]:
        if p.get("id") == id_proc:
            return p
    ids = ", ".join(p.get("id", "?") for p in reg["processos"]) or "(nenhum)"
    raise ErroValidacao(f"Processo '{id_proc}' não existe no registro. Ids cadastrados: {ids}")


# ---------------------------------------------------------------------------
# Validação de um processo
# ---------------------------------------------------------------------------

def normaliza_processo(p, ids_existentes):
    """
    Preenche padrões e valida um processo antes de entrar no registro.
    Isolamento de premissas: nada é herdado de outro processo do lote.
    """
    if not isinstance(p, dict):
        raise ErroValidacao("cada processo precisa ser um objeto JSON")
    faltando = [c for c in CAMPOS_OBRIGATORIOS if not p.get(c)]
    if faltando:
        raise ErroValidacao(f"processo '{p.get('id', '?')}' sem os campos obrigatórios: {', '.join(faltando)}")
    if p["id"] in ids_existentes:
        raise ErroValidacao(f"id duplicado no lote: '{p['id']}'")
    if not isinstance(p["reus"], list) or not p["reus"]:
        raise ErroValidacao(f"processo '{p['id']}': 'reus' precisa ser lista não vazia")
    polo = str(p["polo_demandado"]).upper()
    if polo not in POLOS_VALIDOS:
        raise ErroValidacao(f"processo '{p['id']}': polo_demandado '{p['polo_demandado']}' inválido; use {', '.join(POLOS_VALIDOS)}")
    p["polo_demandado"] = polo
    parse_data(p["data_nomeacao"], f"processo '{p['id']}': data_nomeacao")
    parse_data(p["prazo_laudo"], f"processo '{p['id']}': prazo_laudo")
    if p.get("prazo_esclarecimentos"):
        parse_data(p["prazo_esclarecimentos"], f"processo '{p['id']}': prazo_esclarecimentos")

    status = p.get("status") or "nomeado"
    if status not in STATUS_VALIDOS:
        raise ErroValidacao(f"processo '{p['id']}': status '{status}' inválido; use {', '.join(STATUS_VALIDOS)}")
    p["status"] = status

    modalidades = p.get("modalidades_alegadas") or []
    if not isinstance(modalidades, list):
        raise ErroValidacao(f"processo '{p['id']}': modalidades_alegadas precisa ser lista")
    for m in modalidades:
        if m not in MODALIDADES_VALIDAS:
            raise ErroValidacao(f"processo '{p['id']}': modalidade '{m}' inválida; use {', '.join(MODALIDADES_VALIDAS)}")
    p["modalidades_alegadas"] = modalidades

    quesitos = p.get("quesitos") or {}
    if not isinstance(quesitos, dict):
        raise ErroValidacao(f"processo '{p['id']}': quesitos precisa ser objeto {{juizo, autor, reu}}")
    for prop in PROPONENTES:
        valor = quesitos.get(prop, 0)
        try:
            quesitos[prop] = int(valor)
        except (TypeError, ValueError):
            raise ErroValidacao(f"processo '{p['id']}': quesitos.{prop} precisa ser inteiro")
    p["quesitos"] = quesitos

    docs = p.get("documentos") or {}
    if not isinstance(docs, dict):
        raise ErroValidacao(f"processo '{p['id']}': documentos precisa ser objeto")
    for d in DOCUMENTOS_PADRAO:
        docs.setdefault(d, "pendente")
    for nome, estado in docs.items():
        if estado not in ESTADOS_DOCUMENTO:
            raise ErroValidacao(f"processo '{p['id']}': documento '{nome}' com estado '{estado}'; use {', '.join(ESTADOS_DOCUMENTO)}")
    p["documentos"] = docs

    p.setdefault("proxima_acao", "")
    p.setdefault("observacoes", "")
    p.setdefault("historico", [])
    for campo in CAMPOS_TEXTO_LIVRES:
        p.setdefault(campo, "")
    return p


# ---------------------------------------------------------------------------
# Subcomandos
# ---------------------------------------------------------------------------

def cmd_criar(args, hoje):
    """Cria um registro vazio do lote."""
    destino = Path(args.registro)
    if destino.exists() and not args.forcar:
        raise ErroValidacao(f"o registro já existe: {destino}. Use --forcar para sobrescrever")
    reg = {
        "skill": SKILL,
        "versao_registro": VERSAO_REGISTRO,
        "perito": args.perito or "",
        "criado_em": formata_data(hoje),
        "atualizado_em": formata_data(hoje),
        "locale": LOCALE,
        "premissas": {
            "isolamento": "cada processo tem registro, extrato, caso.json e quadro de cenários próprios; nada é copiado entre processos",
            "prazos": "prazo_laudo e prazo_esclarecimentos são datas fixadas ou calculadas pela perita; o painel apenas mede a distância até elas",
            "calculo": "nenhum valor monetário é tratado aqui; usar o motor da skill pericia-pasep",
        },
        "processos": [],
    }
    grava_json(destino, reg)
    return {
        "operacao": "criar",
        "registro": str(destino),
        "memoria": [f"registro criado em {formata_data(hoje)} com 0 processos"],
    }


def cmd_adicionar(args, hoje):
    """Adiciona um ou mais processos (arquivo JSON com objeto ou lista de objetos)."""
    reg = carrega_registro(args.registro)
    novos = carrega_json(args.processo, "Arquivo de processo(s)")
    if isinstance(novos, dict):
        novos = [novos]
    if not isinstance(novos, list) or not novos:
        raise ErroValidacao("o arquivo de processos precisa conter um objeto ou uma lista de objetos")
    ids = {p.get("id") for p in reg["processos"]}
    memoria = []
    for bruto in novos:
        p = normaliza_processo(bruto, ids)
        p["historico"].append({"data": formata_data(hoje), "evento": "adicionado ao lote", "alteracoes": {}})
        reg["processos"].append(p)
        ids.add(p["id"])
        memoria.append(f"{p['id']}: {p['numero']} ({p['vara']}, {p['comarca']}); polo {p['polo_demandado']}; status {p['status']}; prazo do laudo {p['prazo_laudo']}")
    salva_registro(args.registro, reg, hoje)
    return {
        "operacao": "adicionar",
        "registro": args.registro,
        "adicionados": [p["id"] for p in novos],
        "total_processos": len(reg["processos"]),
        "memoria": memoria,
    }


def parse_par(texto, opcao):
    """Divide 'chave=valor' de uma opção repetível."""
    if "=" not in texto:
        raise ErroValidacao(f"{opcao} espera chave=valor, recebeu '{texto}'")
    chave, valor = texto.split("=", 1)
    chave, valor = chave.strip(), valor.strip()
    if not chave or not valor:
        raise ErroValidacao(f"{opcao} com chave ou valor vazio em '{texto}'")
    return chave, valor


def cmd_atualizar(args, hoje):
    """Atualiza status, prazo, documentos, quesitos, próxima ação e campos livres de um processo."""
    reg = carrega_registro(args.registro)
    p = localiza(reg, args.id)
    alteracoes = {}

    def registra(chave, anterior, novo):
        """Registra a alteração apenas quando o valor muda de fato; repetição vira aviso."""
        if anterior == novo:
            sem_efeito.append(f"{chave} já era '{novo}'")
            return False
        alteracoes[chave] = (anterior, novo)
        return True

    sem_efeito = []
    if args.status:
        if args.status not in STATUS_VALIDOS:
            raise ErroValidacao(f"status '{args.status}' inválido; use {', '.join(STATUS_VALIDOS)}")
        if registra("status", p["status"], args.status):
            p["status"] = args.status
    if args.prazo_laudo:
        parse_data(args.prazo_laudo, "--prazo-laudo")
        if registra("prazo_laudo", p["prazo_laudo"], args.prazo_laudo):
            p["prazo_laudo"] = args.prazo_laudo
    if args.prazo_esclarecimentos:
        parse_data(args.prazo_esclarecimentos, "--prazo-esclarecimentos")
        if registra("prazo_esclarecimentos", p.get("prazo_esclarecimentos", ""), args.prazo_esclarecimentos):
            p["prazo_esclarecimentos"] = args.prazo_esclarecimentos
    if args.proxima_acao is not None:
        if registra("proxima_acao", p.get("proxima_acao", ""), args.proxima_acao):
            p["proxima_acao"] = args.proxima_acao
    if args.observacao:
        anterior = p.get("observacoes", "")
        novo = (anterior + " | " if anterior else "") + f"{formata_data(hoje)}: {args.observacao}"
        alteracoes["observacoes"] = (anterior, novo)
        p["observacoes"] = novo
    for item in args.documento or []:
        nome, estado = parse_par(item, "--documento")
        if estado not in ESTADOS_DOCUMENTO:
            raise ErroValidacao(f"documento '{nome}' com estado '{estado}'; use {', '.join(ESTADOS_DOCUMENTO)}")
        if registra(f"documentos.{nome}", p["documentos"].get(nome, ""), estado):
            p["documentos"][nome] = estado
    for item in args.quesitos or []:
        prop, n = parse_par(item, "--quesitos")
        if prop not in PROPONENTES:
            raise ErroValidacao(f"proponente '{prop}' inválido; use {', '.join(PROPONENTES)}")
        try:
            n_int = int(n)
        except ValueError:
            raise ErroValidacao(f"--quesitos {prop} precisa ser inteiro, recebeu '{n}'")
        if registra(f"quesitos.{prop}", p["quesitos"].get(prop, 0), n_int):
            p["quesitos"][prop] = n_int
    for item in args.modalidade or []:
        if item not in MODALIDADES_VALIDAS:
            raise ErroValidacao(f"modalidade '{item}' inválida; use {', '.join(MODALIDADES_VALIDAS)}")
        if item not in p["modalidades_alegadas"]:
            p["modalidades_alegadas"].append(item)
            alteracoes[f"modalidades_alegadas.{item}"] = ("", "incluída")
    for item in args.campo or []:
        chave, valor = parse_par(item, "--campo")
        if chave in ("id", "processos", "historico", "documentos", "quesitos"):
            raise ErroValidacao(f"o campo '{chave}' não pode ser alterado por --campo")
        if registra(chave, p.get(chave, ""), valor):
            p[chave] = valor

    if not alteracoes:
        detalhe = ("; valores repetidos: " + ", ".join(sem_efeito)) if sem_efeito else ""
        raise ErroValidacao("nenhuma alteração efetiva; use --status, --prazo-laudo, --documento, --quesitos, --proxima-acao, --observacao, --modalidade ou --campo" + detalhe)

    p["historico"].append({
        "data": formata_data(hoje),
        "evento": "atualização",
        "alteracoes": {k: {"de": v[0], "para": v[1]} for k, v in alteracoes.items()},
    })
    salva_registro(args.registro, reg, hoje)
    return {
        "operacao": "atualizar",
        "registro": args.registro,
        "id": p["id"],
        "alteracoes": {k: {"de": v[0], "para": v[1]} for k, v in alteracoes.items()},
        "sem_efeito": sem_efeito,
        "memoria": [f"{p['id']}: {k}: '{v[0]}' -> '{v[1]}'" for k, v in alteracoes.items()]
                   + [f"{p['id']}: sem efeito: {t}" for t in sem_efeito],
    }


def prazo_vigente(p):
    """Devolve (rótulo, data) do prazo que manda no momento, ou (rótulo, None) se não há prazo a vigiar."""
    status = p.get("status")
    if status == "encerrado":
        return ("encerrado", None)
    if status == "esclarecimentos" and p.get("prazo_esclarecimentos"):
        return ("esclarecimentos (CPC art. 477, § 2º)", parse_data(p["prazo_esclarecimentos"], "prazo_esclarecimentos"))
    if status == "laudo_entregue":
        return ("laudo entregue; aguardando manifestação das partes", None)
    return ("laudo", parse_data(p["prazo_laudo"], "prazo_laudo"))


def linha_painel(p, hoje, alerta_dias):
    """Monta a linha do painel de um processo."""
    rotulo, data_prazo = prazo_vigente(p)
    if data_prazo is None:
        corridos = None
        uteis = None
        alerta = "-"
    else:
        corridos = (data_prazo - hoje).days
        uteis = dias_uteis_entre(hoje, data_prazo)
        if corridos < 0:
            alerta = f"vencido há {-corridos} dias corridos"
        elif corridos < alerta_dias:
            alerta = f"alerta: menos de {alerta_dias} dias"
        else:
            alerta = "ok"
    pendentes = [n for n, e in p["documentos"].items() if e in ("pendente", "parcial")]
    total_quesitos = sum(int(p["quesitos"].get(x, 0)) for x in PROPONENTES)
    return {
        "id": p["id"],
        "numero": p["numero"],
        "juizo": f"{p['vara']}, {p['comarca']}",
        "autor": p["autor"],
        "polo_demandado": p["polo_demandado"],
        "status": p["status"],
        "prazo_rotulo": rotulo,
        "prazo_data": formata_data(data_prazo) if data_prazo else "-",
        "dias_corridos": corridos,
        "dias_uteis_aprox": uteis,
        "alerta": alerta,
        "quesitos_total": total_quesitos,
        "documentos_pendentes": pendentes,
        "proxima_acao": p.get("proxima_acao", ""),
    }


def cmd_painel(args, hoje):
    """Emite o painel do lote ordenado por prazo vigente."""
    reg = carrega_registro(args.registro)
    if not reg["processos"]:
        raise ErroValidacao("o registro não tem processos; use 'adicionar' primeiro")
    linhas = [linha_painel(p, hoje, args.alerta_dias) for p in reg["processos"]]
    # Ordena: prazos vencidos e mais próximos primeiro; sem prazo ao final
    linhas.sort(key=lambda l: (l["dias_corridos"] is None, l["dias_corridos"] if l["dias_corridos"] is not None else 0, l["id"]))
    for i, l in enumerate(linhas, start=1):
        l["ordem"] = i

    # Sanidade: uma linha por processo, ids únicos, nenhum processo perdido na ordenação
    ids = [l["id"] for l in linhas]
    if len(linhas) != len(reg["processos"]) or len(set(ids)) != len(ids):
        raise RuntimeError("inconsistência interna: o painel não reproduz um processo por linha com ids únicos")

    por_status = {}
    for l in linhas:
        por_status[l["status"]] = por_status.get(l["status"], 0) + 1
    alertas = [f"{l['id']} ({l['numero']}): {l['alerta']}, prazo de {l['prazo_rotulo']} em {l['prazo_data']}"
               for l in linhas if l["alerta"] not in ("ok", "-")]

    md = []
    md.append(f"# Painel do lote PASEP em {formata_data(hoje)}")
    md.append("")
    md.append(f"Perito(a): {reg.get('perito') or '[não informado]'}. Processos: {len(linhas)}. Alerta para prazo inferior a {args.alerta_dias} dias corridos.")
    md.append("")
    md.append("| Ordem | Id | Processo | Juízo | Autor | Polo | Status | Prazo vigente | Data | Dias corridos | Dias úteis (aprox.) | Alerta | Quesitos | Docs pendentes | Próxima ação |")
    md.append("|---|---|---|---|---|---|---|---|---|---:|---:|---|---:|---|---|")
    for l in linhas:
        md.append("| {ordem} | {id} | {numero} | {juizo} | {autor} | {polo} | {status} | {rot} | {data} | {dc} | {du} | {al} | {q} | {docs} | {pa} |".format(
            ordem=l["ordem"], id=l["id"], numero=l["numero"], juizo=l["juizo"], autor=l["autor"],
            polo=l["polo_demandado"], status=l["status"], rot=l["prazo_rotulo"], data=l["prazo_data"],
            dc="-" if l["dias_corridos"] is None else l["dias_corridos"],
            du="-" if l["dias_uteis_aprox"] is None else l["dias_uteis_aprox"],
            al=l["alerta"], q=l["quesitos_total"],
            docs=", ".join(l["documentos_pendentes"]) or "nenhum",
            pa=l["proxima_acao"] or "-",
        ))
    md.append("")
    md.append("Resumo por status: " + "; ".join(f"{k}: {v}" for k, v in sorted(por_status.items())) + ".")
    md.append("")
    if alertas:
        md.append("Alertas de prazo:")
        md.append("")
        for a in alertas:
            md.append(f"- {a}")
    else:
        md.append("Sem alertas de prazo.")
    md.append("")
    md.append("Nota: dias úteis contados de segunda a sexta, sem feriados; a contagem oficial (CPC art. 219) segue o calendário forense do tribunal.")
    texto_md = "\n".join(md) + "\n"

    if args.md:
        Path(args.md).write_text(texto_md, encoding="utf-8")
    if args.csv:
        colunas = ["ordem", "id", "numero", "juizo", "autor", "polo_demandado", "status", "prazo_rotulo",
                   "prazo_data", "dias_corridos", "dias_uteis_aprox", "alerta", "quesitos_total",
                   "documentos_pendentes", "proxima_acao"]
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
            w.writeheader()
            for l in linhas:
                linha = dict(l)
                linha["documentos_pendentes"] = ", ".join(l["documentos_pendentes"])
                w.writerow({c: ("" if linha.get(c) is None else linha.get(c)) for c in colunas})

    return {
        "operacao": "painel",
        "registro": args.registro,
        "data_referencia": formata_data(hoje),
        "premissas": {
            "alerta_dias": args.alerta_dias,
            "dias_uteis": "segunda a sexta, sem feriados (aproximação)",
            "ordenacao": "prazo vigente crescente; processos sem prazo a vigiar ao final",
        },
        "locale": LOCALE,
        "arredondamento": ARREDONDAMENTO,
        "total_processos": len(linhas),
        "por_status": por_status,
        "alertas": alertas,
        "linhas": linhas,
        "painel_markdown": texto_md,
        "memoria": [f"{l['id']}: prazo de {l['prazo_rotulo']} em {l['prazo_data']}; {l['dias_corridos']} dias corridos; alerta '{l['alerta']}'" for l in linhas],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def monta_parser():
    """Constrói o argparse com os quatro subcomandos."""
    parser = argparse.ArgumentParser(
        description="Registro e painel de um lote de perícias judiciais do PASEP (perito do juízo). Sem cálculo monetário.",
    )
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--hoje", help="Data de referência dd/mm/aaaa (padrão: data do sistema)")
    comum.add_argument("--saida", help="Arquivo JSON de saída (padrão: stdout)")
    sub = parser.add_subparsers(dest="comando", required=True, help="Subcomando")

    s = sub.add_parser("criar", help="Cria o registro do lote", parents=[comum])
    s.add_argument("--registro", required=True, help="Caminho do registro JSON a criar")
    s.add_argument("--perito", help="Nome do perito ou da perita nomeada")
    s.add_argument("--forcar", action="store_true", help="Sobrescreve registro existente")

    s = sub.add_parser("adicionar", help="Adiciona processo(s) ao lote", parents=[comum])
    s.add_argument("--registro", required=True, help="Caminho do registro JSON")
    s.add_argument("--processo", required=True, help="Arquivo JSON com um processo ou lista de processos")

    s = sub.add_parser("atualizar", help="Atualiza um processo do lote", parents=[comum])
    s.add_argument("--registro", required=True, help="Caminho do registro JSON")
    s.add_argument("--id", required=True, help="Id do processo no lote (ex.: P-002)")
    s.add_argument("--status", help=f"Novo status: {', '.join(STATUS_VALIDOS)}")
    s.add_argument("--prazo-laudo", dest="prazo_laudo", help="Novo prazo do laudo dd/mm/aaaa")
    s.add_argument("--prazo-esclarecimentos", dest="prazo_esclarecimentos", help="Prazo dos esclarecimentos dd/mm/aaaa (CPC art. 477, § 2º)")
    s.add_argument("--documento", action="append", help=f"nome=estado, repetível; estados: {', '.join(ESTADOS_DOCUMENTO)}")
    s.add_argument("--quesitos", action="append", help="proponente=quantidade, repetível; proponentes: juizo, autor, reu")
    s.add_argument("--modalidade", action="append", help=f"Inclui modalidade alegada, repetível: {', '.join(MODALIDADES_VALIDAS)}")
    s.add_argument("--proxima-acao", dest="proxima_acao", help="Texto da próxima ação")
    s.add_argument("--observacao", help="Observação datada, acrescentada ao histórico do processo")
    s.add_argument("--campo", action="append", help="campo=valor para campos livres (ex.: objeto_saneamento=...)")

    s = sub.add_parser("painel", help="Emite o painel do lote ordenado por prazo", parents=[comum])
    s.add_argument("--registro", required=True, help="Caminho do registro JSON")
    s.add_argument("--md", help="Grava o painel em Markdown neste arquivo")
    s.add_argument("--csv", help="Grava o painel em CSV (separador ;) neste arquivo")
    s.add_argument("--alerta-dias", dest="alerta_dias", type=int, default=15, help="Limite de alerta em dias corridos (padrão 15)")
    return parser


def main():
    """Ponto de entrada: despacha o subcomando e trata os erros."""
    parser = monta_parser()
    args = parser.parse_args()
    try:
        hoje = resolve_hoje(args.hoje)
        despacho = {"criar": cmd_criar, "adicionar": cmd_adicionar, "atualizar": cmd_atualizar, "painel": cmd_painel}
        resultado = despacho[args.comando](args, hoje)
        resultado.setdefault("skill", SKILL)
        resultado.setdefault("locale", LOCALE)
        resultado.setdefault("arredondamento", ARREDONDAMENTO)
        resultado.setdefault("premissas", {"data_referencia": formata_data(hoje)})
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
