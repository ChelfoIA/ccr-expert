#!/usr/bin/env python3
"""
Fase zero da perícia de prestação de contas de recursos da covid-19: controle dos
documentos requeridos a cada parte e a terceiros (recebido, parcial, pendente, dias
de atraso), acompanhamento do prazo do laudo, geração do termo de diligência
(CPC, art. 473, § 3º) e das minutas de ofício (ao ente, ao FNS/Ministério da Saúde,
ao TCE, ao banco), com sugestão do que peticionar quando a documentação atrasa
(CPC, arts. 378 a 380, 400, 401 a 404, 468, II, 476 e 477).
Parte da skill: pericia-prestacao-contas-covid-saude

Não há cálculo monetário neste script; só datas e contagem de dias. Nenhum
documento é presumido entregue: o que não consta como recebido no registro é
pendência e vai para o painel.

Uso:
    python3 scripts/checklist_documental_covid.py --registro assets/exemplo_registro_documentos.json \
        --gerar painel --data-referencia 12/10/2026 --md painel.md --saida painel.json
    python3 scripts/checklist_documental_covid.py --registro registro.json --gerar termo --md termo.md
    python3 scripts/checklist_documental_covid.py --registro registro.json --gerar oficio --destinatario tce --md oficio_tce.md
    python3 scripts/checklist_documental_covid.py --registro registro.json --gerar todos --md fase_zero.md

Layout do JSON de registro: ver assets/exemplo_registro_documentos.json (processo, perito, prazo_laudo,
partes com id/nome/papel, documentos com id/descricao/parte_responsavel/status/data_pedido/prazo_dias/
data_recebimento). Status aceitos: recebido, parcial, pendente.
"""
import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SKILL = "pericia-prestacao-contas-covid-saude"
VERSAO = "1.0.0"
LOCALE = "pt-BR (R$ 1.234,56; 12,5%; dd/mm/aaaa)"
ARREDONDAMENTO = "não se aplica: script sem cálculo monetário; dias contados por diferença de datas"
STATUS = ("recebido", "parcial", "pendente")
PAPEIS = ("autor", "réu", "terceiro", "perito")


def parse_data(texto, contexto: str = "") -> date:
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError) as exc:
        onde = f" ({contexto})" if contexto else ""
        raise ValueError(f"data inválida{onde}, esperado dd/mm/aaaa: {texto!r}") from exc


def parse_data_opcional(texto, contexto: str = ""):
    if texto is None or str(texto).strip() == "":
        return None
    return parse_data(texto, contexto)


def fmt_data(d) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def carregar_registro(caminho: str) -> dict:
    p = Path(caminho)
    if not p.exists():
        raise ValueError(f"arquivo de registro não encontrado: {caminho}")
    with p.open(encoding="utf-8") as fh:
        try:
            reg = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON de registro inválido: {exc}") from exc
    for chave in ("processo", "perito", "prazo_laudo", "partes", "documentos"):
        if chave not in reg:
            raise ValueError(f"registro sem a chave obrigatória '{chave}'")
    if not isinstance(reg["partes"], list) or not reg["partes"]:
        raise ValueError("registro sem partes")
    if not isinstance(reg["documentos"], list) or not reg["documentos"]:
        raise ValueError("registro sem documentos")
    ids = set()
    for parte in reg["partes"]:
        for k in ("id", "nome", "papel"):
            if not parte.get(k):
                raise ValueError(f"parte sem o campo '{k}': {parte}")
        if parte["papel"] not in PAPEIS:
            raise ValueError(f"parte {parte['id']} com papel inválido {parte['papel']!r}; aceitos: {', '.join(PAPEIS)}")
        if parte["id"] in ids:
            raise ValueError(f"id de parte repetido: {parte['id']}")
        ids.add(parte["id"])
    if "perito" not in ids:
        reg["partes"].append({"id": "perito", "nome": reg["perito"].get("nome", "perito"), "papel": "perito", "endereco": ""})
    pl = reg["prazo_laudo"]
    if not pl.get("data_inicio") or not pl.get("dias"):
        raise ValueError("prazo_laudo exige data_inicio (dd/mm/aaaa) e dias (inteiro)")
    try:
        pl["dias"] = int(pl["dias"])
    except (TypeError, ValueError) as exc:
        raise ValueError("prazo_laudo.dias deve ser inteiro") from exc
    return reg


def avaliar_documentos(reg: dict, ref: date) -> list:
    partes = {p["id"]: p for p in reg["partes"]}
    docs = []
    vistos = set()
    for d in reg["documentos"]:
        ctx = f"documento {d.get('id', '?')}"
        for k in ("id", "descricao", "parte_responsavel", "status", "data_pedido"):
            if d.get(k) in (None, ""):
                raise ValueError(f"{ctx}: campo obrigatório '{k}' ausente")
        if d["id"] in vistos:
            raise ValueError(f"{ctx}: id repetido")
        vistos.add(d["id"])
        if d["parte_responsavel"] not in partes:
            raise ValueError(f"{ctx}: parte_responsavel {d['parte_responsavel']!r} não consta das partes")
        status = d["status"].strip().lower()
        if status not in STATUS:
            raise ValueError(f"{ctx}: status {d['status']!r} inválido; aceitos: {', '.join(STATUS)}")
        pedido = parse_data(d["data_pedido"], f"{ctx}, data_pedido")
        try:
            prazo = int(d.get("prazo_dias", 0) or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{ctx}: prazo_dias deve ser inteiro") from exc
        if prazo < 0:
            raise ValueError(f"{ctx}: prazo_dias negativo")
        recebimento = parse_data_opcional(d.get("data_recebimento"), f"{ctx}, data_recebimento")
        if status in ("recebido", "parcial") and recebimento is None:
            raise ValueError(f"{ctx}: status {status} exige data_recebimento")
        if status == "pendente" and recebimento is not None:
            raise ValueError(f"{ctx}: status pendente não admite data_recebimento")
        if recebimento and recebimento < pedido:
            raise ValueError(f"{ctx}: data_recebimento anterior à data_pedido")
        limite = pedido + timedelta(days=prazo)
        if status == "recebido":
            atraso = max(0, (recebimento - limite).days)
            situacao = "recebido no prazo" if atraso == 0 else f"recebido com atraso de {atraso} dias"
            exigivel = False
        else:
            atraso = max(0, (ref - limite).days)
            restantes = (limite - ref).days
            rotulo = "parcial" if status == "parcial" else "pendente"
            situacao = (f"{rotulo}, atrasado {atraso} dias" if atraso > 0
                        else f"{rotulo}, no prazo ({restantes} dias restantes)")
            exigivel = True
        parte = partes[d["parte_responsavel"]]
        docs.append({"id": d["id"], "descricao": d["descricao"], "parte_id": parte["id"], "parte": parte["nome"],
                     "papel": parte["papel"], "fonte_recurso": d.get("fonte_recurso", ""), "status": status,
                     "data_pedido": pedido, "prazo_dias": prazo, "data_limite": limite, "data_recebimento": recebimento,
                     "dias_atraso": atraso, "situacao": situacao, "exigivel": exigivel, "observacao": d.get("observacao", "")})
    return docs


def avaliar_prazo_laudo(reg: dict, ref: date) -> dict:
    pl = reg["prazo_laudo"]
    inicio = parse_data(pl["data_inicio"], "prazo_laudo.data_inicio")
    limite = inicio + timedelta(days=pl["dias"])
    restantes = (limite - ref).days
    if restantes < 0:
        situacao = f"vencido há {-restantes} dias"
    elif restantes == 0:
        situacao = "vence hoje"
    else:
        situacao = f"{restantes} dias restantes"
    return {"data_inicio": inicio, "dias": pl["dias"], "data_limite": limite, "dias_restantes": restantes,
            "situacao": situacao, "observacao": pl.get("observacao", "")}


def resumir_por_parte(reg: dict, docs: list) -> list:
    linhas = []
    for p in reg["partes"]:
        meus = [d for d in docs if d["parte_id"] == p["id"]]
        if not meus:
            continue
        linhas.append({"parte_id": p["id"], "parte": p["nome"], "papel": p["papel"], "total": len(meus),
                       "recebidos": sum(1 for d in meus if d["status"] == "recebido"),
                       "parciais": sum(1 for d in meus if d["status"] == "parcial"),
                       "pendentes": sum(1 for d in meus if d["status"] == "pendente"),
                       "atrasados": sum(1 for d in meus if d["exigivel"] and d["dias_atraso"] > 0),
                       "maior_atraso_dias": max([d["dias_atraso"] for d in meus if d["exigivel"]] or [0])})
    return linhas


def sugerir_peticoes(docs: list, prazo: dict, alerta_dias: int) -> tuple:
    alertas = []
    sugestoes = []
    atrasados_partes = [d for d in docs if d["exigivel"] and d["dias_atraso"] > 0 and d["papel"] in ("autor", "réu")]
    atrasados_terceiros = [d for d in docs if d["exigivel"] and d["dias_atraso"] > 0 and d["papel"] == "terceiro"]
    pendentes = [d for d in docs if d["exigivel"]]
    proprias = [d for d in docs if d["exigivel"] and d["papel"] == "perito"]

    if atrasados_partes:
        ids = ", ".join(d["id"] for d in atrasados_partes)
        alertas.append(f"documentos de parte com prazo vencido: {len(atrasados_partes)} ({ids})")
        sugestoes.append({
            "tipo": "petição de ciência do atraso e requerimento de intimação da parte",
            "fundamento": "CPC, art. 473, § 3º (solicitação de documentos pelo perito); arts. 378 e 379 (dever de colaboração); "
                          "arts. 396 a 400 (exibição de documento em poder da parte); art. 400 (consequências da não exibição)",
            "pedido": "informar ao juízo os documentos requeridos no termo de diligência e não apresentados, com as datas; requerer a intimação "
                      "da parte para exibi-los em prazo certo, sob as consequências do art. 400 do CPC; requerer que o prazo do laudo seja "
                      "contado da juntada completa, ou a sua prorrogação (art. 476)",
            "documentos": [d["id"] for d in atrasados_partes]})
    if atrasados_terceiros:
        ids = ", ".join(d["id"] for d in atrasados_terceiros)
        alertas.append(f"documentos de terceiros com prazo vencido: {len(atrasados_terceiros)} ({ids})")
        sugestoes.append({
            "tipo": "requerimento de expedição ou reiteração de ofício a terceiro",
            "fundamento": "CPC, art. 380 (dever do terceiro de informar e exibir); arts. 401 a 404 (exibição por terceiro); art. 473, § 3º "
                          "(documentos em repartições públicas)",
            "pedido": "requerer que o juízo expeça ou reitere ofício ao terceiro (ente repassador, tribunal de contas, instituição financeira) "
                      "com prazo para resposta, remetendo a relação de documentos e o layout de entrega; registrar no laudo a data de cada pedido",
            "documentos": [d["id"] for d in atrasados_terceiros]})
    if proprias:
        alertas.append(f"diligências próprias do perito ainda abertas: {len(proprias)} ({', '.join(d['id'] for d in proprias)})")
    if pendentes and prazo["dias_restantes"] <= alerta_dias:
        alertas.append(f"prazo do laudo com {prazo['dias_restantes']} dias restantes e {len(pendentes)} documentos ainda exigíveis")
        sugestoes.append({
            "tipo": "pedido de prorrogação ou de nova contagem do prazo do laudo",
            "fundamento": "CPC, art. 476 (prorrogação, por uma vez, pela metade do prazo, por motivo legítimo); art. 477, caput (prazo do laudo "
                          "e antecedência mínima da audiência); NBC TP 01 (planejamento e limitação de escopo)",
            "pedido": "demonstrar o motivo legítimo (documentação não fornecida, com datas) e requerer a prorrogação do art. 476 ou a contagem do "
                      "prazo a partir da juntada; alternativamente, comunicar que o laudo será entregue com limitação de escopo declarada e "
                      "proposta de complementação após a juntada",
            "documentos": [d["id"] for d in pendentes]})
    if prazo["dias_restantes"] < 0:
        alertas.append("prazo do laudo vencido: comunicar o juízo imediatamente")
        sugestoes.append({
            "tipo": "comunicação imediata do vencimento do prazo com justificativa e pedido de novo prazo",
            "fundamento": "CPC, art. 468, II (substituição do perito que, sem motivo legítimo, deixa de cumprir o encargo no prazo); art. 476",
            "pedido": "justificar o motivo legítimo com a cronologia dos pedidos e das respostas, requerer novo prazo e informar o estágio dos trabalhos",
            "documentos": [d["id"] for d in pendentes]})
    if not pendentes:
        alertas.append("nenhum documento exigível em aberto: fase zero concluída, iniciar a conciliação")
    return alertas, sugestoes


def md_painel(reg: dict, ref: date, docs: list, prazo: dict, resumo: list, alertas: list, sugestoes: list) -> str:
    pr = reg["processo"]
    L = []
    L.append("# Painel de documentos da perícia (fase zero)")
    L.append("")
    L.append(f"Processo {pr.get('numero', '[número]')}, {pr.get('juizo', '[juízo]')}. {pr.get('acao', '')}")
    L.append(f"Perito: {reg['perito'].get('nome', '[nome]')}, {reg['perito'].get('registro', '[registro]')}. "
             f"Data de referência do painel: {fmt_data(ref)}. Script `checklist_documental_covid.py` v{VERSAO}.")
    L.append("")
    L.append("## 1. Prazo do laudo")
    L.append("")
    L.append(f"Início em {fmt_data(prazo['data_inicio'])}, {prazo['dias']} dias, limite em {fmt_data(prazo['data_limite'])}: {prazo['situacao']}. "
             f"{prazo['observacao']}".strip())
    L.append("")
    L.append("## 2. Documentos requeridos")
    L.append("")
    L.append("| ID | Documento | Fonte | Responsável | Status | Pedido em | Limite | Recebido em | Atraso (dias) | Situação |")
    L.append("|---|---|---|---|---|---|---|---|---:|---|")
    for d in docs:
        L.append(f"| {d['id']} | {d['descricao']} | {d['fonte_recurso']} | {d['parte']} | {d['status']} | {fmt_data(d['data_pedido'])} | "
                 f"{fmt_data(d['data_limite'])} | {fmt_data(d['data_recebimento'])} | {d['dias_atraso']} | {d['situacao']} |")
    L.append("")
    L.append("## 3. Resumo por responsável")
    L.append("")
    L.append("| Responsável | Papel | Total | Recebidos | Parciais | Pendentes | Atrasados | Maior atraso (dias) |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for r in resumo:
        L.append(f"| {r['parte']} | {r['papel']} | {r['total']} | {r['recebidos']} | {r['parciais']} | {r['pendentes']} | {r['atrasados']} | {r['maior_atraso_dias']} |")
    L.append("")
    L.append("## 4. Alertas")
    L.append("")
    for a in alertas:
        L.append(f"- {a}")
    L.append("")
    L.append("## 5. O que peticionar")
    L.append("")
    if not sugestoes:
        L.append("Nenhuma petição sugerida na data de referência.")
    for i, s in enumerate(sugestoes, start=1):
        L.append(f"{i}. {s['tipo'].capitalize()}. Fundamento: {s['fundamento']}. Pedido: {s['pedido']}. Documentos: {', '.join(s['documentos'])}.")
    L.append("")
    L.append("Registrar no laudo, na seção de documentos, a cronologia de cada pedido e resposta; o que não vier é limitação declarada, "
             "e a consequência probatória da não exibição (CPC, art. 400) é do juízo.")
    return "\n".join(L) + "\n"


def md_termo(reg: dict, ref: date, docs: list, prazo: dict) -> str:
    pr = reg["processo"]
    pe = reg["perito"]
    exigiveis = [d for d in docs if d["exigivel"] and d["papel"] != "perito"]
    L = []
    L.append("# Termo de diligência nº [N]/[ANO]")
    L.append("")
    L.append(f"Processo nº {pr.get('numero', '[número]')}, {pr.get('juizo', '[juízo]')}.")
    L.append(f"Ação: {pr.get('acao', '[classe]')}.")
    L.append(f"Perito: {pe.get('nome', '[nome]')}, {pe.get('registro', '[registro]')}, nomeado em {pr.get('data_nomeacao', '[dd/mm/aaaa]')}.")
    L.append(f"Data do termo: {fmt_data(ref)}. Prazo do laudo: {prazo['dias']} dias contados de {fmt_data(prazo['data_inicio'])}, "
             f"limite em {fmt_data(prazo['data_limite'])}.")
    L.append("")
    L.append("## 1. Objeto da perícia conforme a decisão de saneamento")
    L.append("")
    L.append(pr.get("objeto_saneamento", "[transcrever os pontos controvertidos e o objeto fixado pelo juízo]"))
    L.append("")
    L.append("## 2. Fundamento")
    L.append("")
    L.append("O perito solicita os documentos abaixo com fundamento no art. 473, § 3º, do CPC (documentos em poder da parte, de terceiros ou de "
             "repartições públicas) e nos arts. 378 e 379 do CPC (dever de colaboração com o Poder Judiciário). Os assistentes técnicos "
             "ficam cientes desta diligência e podem acompanhá-la (CPC, art. 466, § 2º).")
    L.append("")
    L.append("## 3. Documentos requeridos, por responsável")
    L.append("")
    partes_ordem = []
    for d in exigiveis:
        if d["parte_id"] not in partes_ordem:
            partes_ordem.append(d["parte_id"])
    if not exigiveis:
        L.append("Nenhum documento pendente na data do termo.")
    for pid in partes_ordem:
        meus = [d for d in exigiveis if d["parte_id"] == pid]
        L.append(f"### {meus[0]['parte']}")
        L.append("")
        L.append("| ID | Documento | Fonte de recursos | Prazo para entrega | Situação atual |")
        L.append("|---|---|---|---|---|")
        for d in meus:
            L.append(f"| {d['id']} | {d['descricao']} | {d['fonte_recurso']} | {d['prazo_dias']} dias ({fmt_data(d['data_limite'])}) | {d['situacao']} |")
        L.append("")
    L.append("## 4. Forma de entrega")
    L.append("")
    L.append("Meio digital, em formato pesquisável, com indicação das folhas dos autos quando o documento já estiver juntado. As relações de "
             "receitas e de empenhos, liquidações e pagamentos devem seguir o layout anexo (CSV com separador ponto e vírgula, uma linha por "
             "documento ou por empenho, valores no padrão brasileiro, datas em dd/mm/aaaa). Extratos bancários mês a mês, inclusive de aplicação "
             "financeira, por conta específica.")
    L.append("")
    L.append("## 5. Prazo e consequências")
    L.append("")
    L.append("Os prazos acima correm da ciência deste termo. A documentação não apresentada no prazo será comunicada ao juízo, com requerimento "
             "de intimação da parte (CPC, arts. 396 a 400) ou de expedição de ofício ao terceiro (CPC, arts. 380 e 401 a 404), e constará do "
             "laudo como limitação de escopo; a consequência probatória da não exibição (CPC, art. 400) é matéria do juízo.")
    L.append("")
    L.append("## 6. Início dos trabalhos")
    L.append("")
    L.append(f"Os trabalhos de campo terão início em [dd/mm/aaaa], às [hh:mm], em [local], com ciência às partes e aos assistentes técnicos "
             f"(CPC, art. 474). Contato do perito: [e-mail e telefone].")
    L.append("")
    L.append(f"{pe.get('cidade', '[cidade]')}, {fmt_data(ref)}.")
    L.append("")
    L.append(f"{pe.get('nome', '[nome]')}")
    L.append(f"{pe.get('registro', '[registro]')}")
    L.append("Perito nomeado")
    return "\n".join(L) + "\n"


def md_oficios(reg: dict, ref: date, docs: list, destinatario: str = None) -> str:
    pr = reg["processo"]
    pe = reg["perito"]
    partes = {p["id"]: p for p in reg["partes"]}
    exigiveis = [d for d in docs if d["exigivel"] and d["papel"] != "perito"]
    alvos = []
    for d in exigiveis:
        if destinatario and d["parte_id"] != destinatario:
            continue
        if d["parte_id"] not in alvos:
            alvos.append(d["parte_id"])
    if destinatario and destinatario not in partes:
        raise ValueError(f"destinatário {destinatario!r} não consta das partes do registro")
    if not alvos:
        return "# Ofícios\n\nNenhum documento pendente para o destinatário informado.\n"
    blocos = []
    for n, pid in enumerate(alvos, start=1):
        p = partes[pid]
        meus = [d for d in exigiveis if d["parte_id"] == pid]
        prazo_max = max(d["prazo_dias"] for d in meus)
        L = []
        L.append(f"# Ofício nº [{n:02d}]/[ANO] (minuta)")
        L.append("")
        if p["papel"] == "terceiro":
            L.append("Minuta para expedição pelo juízo, ou pelo perito mediante autorização expressa, por se tratar de terceiro "
                     "(CPC, arts. 380 e 401 a 404; art. 473, § 3º).")
        else:
            L.append("Minuta dirigida à parte, por intermédio de seu procurador, com cópia ao juízo (CPC, art. 473, § 3º; arts. 378 e 379).")
        L.append("")
        L.append(f"Ao(À) {p['nome']}")
        L.append(f"{p.get('endereco', '[endereço]')}")
        L.append("")
        L.append(f"Ref.: Processo nº {pr.get('numero', '[número]')}, {pr.get('juizo', '[juízo]')}. {pr.get('acao', '')}")
        L.append("")
        L.append(f"Senhor(a) [cargo do destinatário],")
        L.append("")
        L.append(f"Na condição de perito nomeado nos autos em referência, solicito a apresentação dos documentos abaixo, necessários "
                 f"à perícia contábil sobre a aplicação e a prestação de contas dos recursos destinados ao enfrentamento da covid-19, "
                 f"no prazo de {prazo_max} dias contados do recebimento deste ofício.")
        L.append("")
        L.append("| ID | Documento | Fonte de recursos | Período ou detalhe |")
        L.append("|---|---|---|---|")
        for d in meus:
            L.append(f"| {d['id']} | {d['descricao']} | {d['fonte_recurso']} | {d['observacao'] or '[período]'} |")
        L.append("")
        L.append("Forma de entrega: meio digital, formato pesquisável, planilhas no layout anexo (CSV com separador ponto e vírgula), "
                 "para o endereço eletrônico [e-mail do perito], com cópia ao juízo.")
        if pid in ("fns",) or "fundo nacional" in p["nome"].lower():
            L.append("")
            L.append("Especificação: relatório de repasses fundo a fundo ao ente por competência, portaria, bloco ou grupo de financiamento e conta "
                     "bancária de destino, no período de [mm/aaaa] a [mm/aaaa], inclusive devoluções e saldos informados pelo ente.")
        if "tribunal de contas" in p["nome"].lower():
            L.append("")
            L.append("Especificação: prestação de contas anual dos exercícios de [aaaa] e [aaaa], relatórios de auditoria ou inspeção sobre os "
                     "recursos covid e decisões proferidas, com indicação do estágio (julgadas, em instrução).")
        if "banco" in p["nome"].lower():
            L.append("")
            L.append("Especificação: extratos mensais e relação de ordens bancárias ou transferências, com beneficiário e CNPJ, das contas "
                     "[agência/conta] no período de [mm/aaaa] a [mm/aaaa], inclusive aplicação financeira; requisição por intermédio do juízo "
                     "quando a instituição exigir ordem judicial.")
        L.append("")
        L.append("A não apresentação será comunicada ao juízo para as providências dos arts. 380, 400 e 401 a 404 do CPC, conforme o caso.")
        L.append("")
        L.append(f"{pe.get('cidade', '[cidade]')}, {fmt_data(ref)}.")
        L.append("")
        L.append(f"{pe.get('nome', '[nome]')}")
        L.append(f"{pe.get('registro', '[registro]')}")
        L.append("Perito nomeado")
        blocos.append("\n".join(L))
    return "\n\n---\n\n".join(blocos) + "\n"


def serializar(obj):
    if isinstance(obj, date):
        return fmt_data(obj)
    if isinstance(obj, dict):
        return {k: serializar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serializar(v) for v in obj]
    return obj


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fase zero: painel de documentos, termo de diligência e ofícios da perícia de prestação de contas covid.")
    p.add_argument("--registro", required=True, help="JSON de registro de partes e documentos (ver assets/exemplo_registro_documentos.json)")
    p.add_argument("--gerar", choices=["painel", "termo", "oficio", "todos"], default="painel",
                   help="O que gerar no Markdown: painel de controle, termo de diligência, ofícios ou todos (padrão painel)")
    p.add_argument("--destinatario", help="Id da parte ou terceiro para o ofício (padrão: todos com pendência)")
    p.add_argument("--data-referencia", help="Data de referência para contagem de atraso e prazo (dd/mm/aaaa; padrão: hoje)")
    p.add_argument("--alerta-dias", type=int, default=20, help="Dias restantes do prazo do laudo abaixo dos quais o script sugere prorrogação (padrão 20)")
    p.add_argument("--saida", help="Arquivo JSON de saída com o painel (padrão: stdout)")
    p.add_argument("--md", help="Grava o Markdown gerado (painel, termo, ofícios ou todos)")
    return p


def main():
    parser = montar_parser()
    args = parser.parse_args()
    try:
        if args.alerta_dias < 0:
            raise ValueError("alerta-dias deve ser não negativo")
        reg = carregar_registro(args.registro)
        if args.destinatario and args.destinatario not in {p["id"] for p in reg["partes"]}:
            raise ValueError(f"destinatário {args.destinatario!r} não consta das partes do registro")
        ref = parse_data(args.data_referencia, "data-referencia") if args.data_referencia else date.today()
        docs = avaliar_documentos(reg, ref)
        prazo = avaliar_prazo_laudo(reg, ref)
        resumo = resumir_por_parte(reg, docs)
        alertas, sugestoes = sugerir_peticoes(docs, prazo, args.alerta_dias)
        total_exigiveis = sum(1 for d in docs if d["exigivel"])
        if sum(r["total"] for r in resumo) != len(docs):
            raise ValueError("sanidade falhou: soma dos documentos por responsável não fecha com o total")
        resultado = {
            "script": "checklist_documental_covid.py", "skill": SKILL, "versao": VERSAO,
            "premissas": {"arquivo_registro": args.registro, "data_referencia": ref, "alerta_dias": args.alerta_dias,
                          "contagem": "dias corridos por diferença de datas; limite = data do pedido + prazo em dias",
                          "status_exigiveis": "pendente e parcial"},
            "locale": LOCALE, "arredondamento": ARREDONDAMENTO,
            "processo": reg["processo"], "perito": reg["perito"],
            "prazo_laudo": prazo,
            "documentos": docs,
            "resumo_por_parte": resumo,
            "totais": {"documentos": len(docs), "exigiveis": total_exigiveis,
                       "atrasados": sum(1 for d in docs if d["exigivel"] and d["dias_atraso"] > 0)},
            "alertas": alertas,
            "sugestoes_peticao": sugestoes,
            "memoria": [
                f"1. Registro lido com {len(reg['partes'])} partes ou terceiros e {len(docs)} documentos; data de referência {fmt_data(ref)}.",
                "2. Limite de cada documento = data do pedido + prazo em dias corridos; atraso = dias entre o limite e a referência (pendente ou parcial) "
                "ou entre o limite e o recebimento (recebido).",
                f"3. Prazo do laudo = data de início + {prazo['dias']} dias; dias restantes contados até a referência.",
                "4. Sugestões de petição derivadas do papel do responsável (parte ou terceiro), do atraso e dos dias restantes do laudo.",
                "5. Sanidade: soma dos documentos por responsável fecha com o total do registro.",
            ],
        }
        saida = serializar(resultado)
        texto = json.dumps(saida, ensure_ascii=False, indent=2)
        if args.saida:
            Path(args.saida).write_text(texto, encoding="utf-8")
            print(f"JSON gravado em {args.saida}")
        else:
            print(texto)
        if args.md:
            partes_md = []
            if args.gerar in ("painel", "todos"):
                partes_md.append(md_painel(reg, ref, docs, prazo, resumo, alertas, sugestoes))
            if args.gerar in ("termo", "todos"):
                partes_md.append(md_termo(reg, ref, docs, prazo))
            if args.gerar in ("oficio", "todos"):
                partes_md.append(md_oficios(reg, ref, docs, args.destinatario))
            Path(args.md).write_text("\n\n---\n\n".join(partes_md), encoding="utf-8")
            print(f"Markdown ({args.gerar}) gravado em {args.md}")
        print(f"Fase zero: {len(docs)} documentos, {total_exigiveis} exigíveis, {saida['totais']['atrasados']} atrasados; "
              f"prazo do laudo: {prazo['situacao']}; {len(sugestoes)} petições sugeridas.", file=sys.stderr)
    except ValueError as exc:
        print(f"ERRO de validação: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
