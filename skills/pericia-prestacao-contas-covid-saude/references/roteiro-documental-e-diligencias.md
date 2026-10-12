# Roteiro documental e diligências da fase zero

Referência: 12/09/2026. Este arquivo cobre o que a perita faz entre a nomeação e o primeiro número: cronologia, documentos por responsável e por fonte, fontes públicas de conferência, termo de diligência, ofícios, petições quando as partes atrasam, amostragem e registro da limitação no laudo. Os modelos são gerados por `scripts/checklist_documental_covid.py` a partir do registro JSON; aqui estão as regras e os textos de apoio.

## Sumário

1. Cronologia da fase zero
2. Documentos por responsável e por fonte
3. Fontes públicas de conferência
4. Termo de diligência
5. Ofícios
6. Atraso das partes: o que peticionar
7. Amostragem
8. Registro da limitação no laudo
9. Layout dos arquivos de entrada

---

## 1. Cronologia da fase zero

| Momento | Ato | Fundamento | Produto |
|---|---|---|---|
| Intimação da nomeação | Ler saneamento e nomeação; aceitar ou escusar-se em quinze dias; verificar impedimento | CPC, arts. 357, 465 e 467 | Nota de leitura com objeto, pontos controvertidos, prazo do laudo |
| Até cinco dias da intimação | Proposta de honorários, currículo e contatos (skill `proposta-pericial-judicial`) | CPC, art. 465, § 2º | Petição |
| Quinze dias da intimação das partes | Partes indicam assistentes e quesitos; perito lê e classifica | CPC, art. 465, § 1º | Quadro de quesitos por origem com pertinência |
| Antes de iniciar | Plano de trabalho | NBC TP 01 (planejamento) | `assets/template_plano_trabalho.md` |
| Antes de iniciar | Registro de documentos, termo de diligência e minutas de ofício | CPC, arts. 473, § 3º, 378 a 380, 401 a 404 | `checklist_documental_covid.py --gerar todos` |
| Data e local de início | Comunicação às partes e assistentes | CPC, arts. 474 e 466, § 2º | Termo de início (seção 6 do termo de diligência) |
| A cada resposta | Atualizar status no JSON e regerar o painel | | Painel com atraso e dias restantes |
| Antes de o prazo vencer | Petição conforme a seção 6 | CPC, arts. 400, 476 e 477 | Petição |
| Quesitos suplementares | Durante a diligência | CPC, art. 469 | Registro no plano |

O prazo do laudo é o fixado pelo juízo; o art. 477 exige a entrega com pelo menos vinte dias de antecedência da audiência de instrução. Quando a decisão não fixa o marco inicial, pedir ao juízo que o conte do termo de início ou da juntada da documentação essencial.

---

## 2. Documentos por responsável e por fonte

### 2.1. Do ente auditado (município, estado, consórcio, fundação)

| ID sugerido | Documento | Para que serve | Fonte |
|---|---|---|---|
| D01 | Relatório de repasses do FNS por competência, portaria e conta, no período | Coluna "recebido" da conciliação | fundo a fundo |
| D02 | Extratos mensais das contas específicas, inclusive aplicação financeira | Confronto com o repassador e com o razão; rendimentos | todas |
| D03 | Razão contábil analítico por fonte de recursos e por conta | Coluna "contabilidade" do confronto; saldo por fonte | todas |
| D04 | Relação de empenhos, liquidações e pagamentos por fonte, com credor, CNPJ, objeto, processo, documento fiscal | Entrada de `conciliacao_fonte_recurso.py` e `matriz_despesas_covid.py` | todas |
| D05 | Processos administrativos das contratações emergenciais: justificativa, termo de referência, estimativa de preço, propostas, contrato, notas fiscais, atesto, comprovante de entrega, publicação | Testes por despesa | todas |
| D07 | Relatório anual de gestão, relatórios quadrimestrais, pareceres e atas do conselho de saúde | Prestação de contas ao controle social; conferência | todas |
| D09 | Controle de almoxarifado e patrimônio: entradas, saídas, tombamento | Entrega comprovada; destino dos bens | todas |
| D10 | Leitos habilitados, produção assistencial, plano de contingência | Aderência ao objeto de investimento e custeio | investimento e custeio covid |
| D14 | Atas do conselho de saúde sobre os recursos covid; plano de contingência | Aderência e controle social | todas |
| D15 | Prestação de contas específica de cada portaria, quando exigida, e comprovantes de devolução (GRU) | Devoluções; saldo reprogramado | fundo a fundo |
| D16 | Relação de servidores com vínculo societário em fornecedores (declaração) | Red flag de sócio servidor | todas |
| D17 | Publicações das contratações no sítio oficial (Lei 13.979/2020, art. 4º, § 2º) e no PNCP | Transparência | todas |

### 2.2. Do autor (Ministério Público, ente lesado, cidadão)

Inquérito civil e relatório técnico em formato pesquisável; portarias e atos de transferência citados na inicial com valores por parcela; planilhas que embasaram o pedido, com a fonte de cada número; consultas já feitas a CEIS, CNEP e Portal da Transparência, com data.

### 2.3. De terceiros (por intermédio do juízo)

| Terceiro | Documento | Observação |
|---|---|---|
| FNS / Ministério da Saúde | Relatório de repasses ao ente por competência, portaria, bloco e conta; devoluções recebidas; situação da prestação de contas | Portal FNS permite consulta pública, mas o ofício traz o relatório oficial assinado |
| Tribunal de contas | Prestação de contas anual dos exercícios; relatórios de auditoria ou inspeção sobre recursos covid; decisões e estágio | Decisão do TCE não vincula o juízo, mas é fonte de documentos |
| Instituição financeira | Extratos e relação de ordens bancárias com beneficiário e CNPJ das contas específicas, inclusive aplicação | Requisição por intermédio do juízo quando a instituição exigir ordem judicial |
| Receita Federal, juntas comerciais | Data de constituição, quadro societário e situação cadastral de fornecedores | Em geral obtidos em consulta pública (seção 3) |

### 2.4. Diligências próprias do perito

Consultas públicas com data e tela anexada: Portal FNS, Portal da Transparência (CEIS, CNEP, CEPIM), PNCP, cadastro CNPJ, SIOPS. Rodar `licitacoes-contratos` para preço de referência e due diligence de fornecedor.

---

## 3. Fontes públicas de conferência

| Fonte | O que confere | Como registrar |
|---|---|---|
| Portal FNS (consulta por ente e competência) `[A VERIFICAR URL vigente]` | Repasses por portaria, bloco e conta | Tela ou CSV com data e hora da consulta |
| SIOPS | Receitas e despesas de saúde declaradas pelo ente | Período e data da consulta |
| Portal da Transparência (CEIS, CNEP, CEPIM) | Sanções e impedimentos de fornecedores | CNPJ, data da consulta e resultado, via `licitacoes-contratos` |
| PNCP e Compras.gov.br | Publicação das contratações; preços praticados | Número de controle, data |
| Sítio do tribunal de contas | Prestações de contas, pareceres, decisões | Número do processo e data |
| Cadastro CNPJ (Receita Federal) | Data de abertura, CNAE, quadro societário, situação | Comprovante com data |
| Sítio oficial do ente | Publicação das contratações covid (Lei 13.979/2020, art. 4º, § 2º) | Tela com data |

Consulta pública não substitui o documento oficial: serve para confrontar e para pedir o que falta.

---

## 4. Termo de diligência

Regras do termo gerado por `--gerar termo`:

1. Transcreve o objeto fixado no saneamento, não o objeto da inicial.
2. Lista os documentos por responsável, com prazo em dias e situação atual; documentos já recebidos ficam fora.
3. Fundamenta em CPC, art. 473, § 3º (documentos em poder da parte, de terceiros ou de repartições públicas) e arts. 378 e 379 (dever de colaboração).
4. Fixa a forma de entrega: meio digital pesquisável, planilhas no layout da seção 9, extratos mês a mês por conta.
5. Declara a consequência: comunicação ao juízo com requerimento de intimação (arts. 396 a 400) ou de ofício (arts. 380 e 401 a 404), e registro no laudo como limitação; a consequência probatória do art. 400 é do juízo.
6. Marca data, hora e local de início dos trabalhos (art. 474) e dá ciência aos assistentes técnicos (art. 466, § 2º).

Prazo usual: quinze dias para a parte; vinte para terceiros. Ajustar no JSON (`prazo_dias`) conforme o volume.

---

## 5. Ofícios

O ofício à parte vai por intermédio do procurador, com cópia ao juízo. O ofício a terceiro é minuta para expedição pelo juízo, ou pelo perito mediante autorização expressa, porque o perito não tem poder de requisição sobre terceiros (CPC, arts. 380 e 401 a 404). O script acrescenta a especificação própria de cada destinatário:

| Destinatário | Especificação |
|---|---|
| FNS / Ministério da Saúde | Repasses por competência, portaria, bloco e conta, no período; devoluções; saldos informados pelo ente |
| Tribunal de contas | Prestação de contas dos exercícios; auditorias sobre recursos covid; decisões e estágio |
| Banco | Extratos e ordens bancárias com beneficiário e CNPJ, por conta, inclusive aplicação; via juízo quando exigida ordem judicial |

Todo ofício sai com número, data, prazo, forma de entrega e a advertência das providências dos arts. 380, 400 e 401 a 404.

---

## 6. Atraso das partes: o que peticionar

| Situação | Petição | Fundamento | Pedido |
|---|---|---|---|
| Parte não entregou no prazo do termo | Ciência do atraso e intimação da parte | CPC, arts. 473, § 3º, 378, 379, 396 a 400 | Intimar para exibir em prazo certo, sob as consequências do art. 400; contar o prazo do laudo da juntada completa ou prorrogar (art. 476) |
| Terceiro não respondeu ao ofício | Expedição ou reiteração de ofício | CPC, arts. 380, 401 a 404, 473, § 3º | Expedir ou reiterar com prazo; remeter layout; se persistir, depósito e busca e apreensão (art. 403 e parágrafo único) |
| Laudo a menos de vinte dias do vencimento com pendências | Prorrogação ou nova contagem | CPC, arts. 476 e 477; NBC TP 01 | Prorrogar por uma vez, pela metade do prazo, demonstrado o motivo legítimo; ou contar da juntada; ou entregar com limitação declarada e complementar depois |
| Prazo vencido | Comunicação imediata com justificativa | CPC, arts. 468, II, e 476 | Cronologia dos pedidos e respostas; novo prazo; estágio dos trabalhos |
| Parte entregou documento ilegível ou incompleto | Ciência e intimação para complementar | CPC, arts. 473, § 3º, e 400 | Especificar o que falta (período, conta, fonte); prazo curto |
| Parte pede quesito suplementar ou documento novo | Registro no plano | CPC, art. 469 | Aceitar o pertinente, informar o impacto no prazo |

Modelo curto de petição de atraso:

> [Nome], perita nomeada nos autos, informa que, pelo termo de diligência de [data], requereu ao réu os documentos [IDs], com prazo de [n] dias, vencido em [data]. Até [data de referência] foram apresentados [IDs recebidos] e não foram apresentados [IDs pendentes], conforme painel anexo. Sem a relação de empenhos por fonte (D04) e os extratos de 2021 (D02), a conciliação por fonte não pode ser concluída. Requer: (a) a intimação do réu para apresentar os documentos em [n] dias, sob as consequências do art. 400 do CPC; (b) a contagem do prazo do laudo a partir da juntada completa ou, subsidiariamente, a prorrogação do art. 476; (c) a expedição de ofício ao [terceiro] para [documento], na forma dos arts. 380 e 401 a 404. [Local, data, assinatura.]

A petição não qualifica o atraso (má-fé, ocultação); descreve datas e efeitos sobre o trabalho.

---

## 7. Amostragem

Regra padrão: teste censitário. Universo de dezenas de empenhos se testa por inteiro, e a maioria dos casos de recursos covid cabe nisso. Acima do limite declarado no plano (padrão de `matriz_despesas_covid.py`: cinquenta despesas), o script sugere amostra composta de três blocos: todas as despesas com achado em teste objetivo (conciliação e flags), os maiores valores até a materialidade declarada (padrão setenta por cento do empenhado) e seleção sistemática dos restantes na ordem do empenho (NBC TA 530, por analogia). O plano de trabalho declara o critério antes do teste, e o laudo informa a cobertura em quantidade e valor.

Não extrapolar achado de amostra para o universo sem dizer que é extrapolação; a quantificação do laudo é a dos itens testados, e a projeção, se feita, vai em seção própria com o método.

---

## 8. Registro da limitação no laudo

Documento requerido e não fornecido aparece em três lugares:

1. Seção de documentos: tabela com ID, documento, responsável, data do pedido, prazo, reiterações e situação na data do laudo.
2. Seção de achados: cada despesa afetada recebe "sem [documento] nos autos" como fato, não como conclusão de irregularidade material; a classe pode mudar com a juntada.
3. Conclusão: parágrafo "Limitações", com o efeito sobre cada resposta (por exemplo, "a conciliação da fonte 215 cobre até 12/2020; os extratos de 2021 não foram apresentados") e a indicação de que a consequência probatória da não exibição é do juízo (CPC, art. 400).

Laudo sem essa seção transfere ao perito a lacuna que é da parte.

---

## 9. Layout dos arquivos de entrada

Receitas (`assets/exemplo_receitas.csv`, separador ponto e vírgula): `data;fonte;origem;documento;valor`. Valor negativo é devolução; origem contendo "rendimento" é aplicação financeira.

Despesas (`assets/exemplo_despesas.csv`): `empenho;data_empenho;fonte;credor;cnpj;objeto;modalidade;processo;valor_empenhado;data_liquidacao;valor_liquidado;data_pagamento;valor_pago;nf;data_nf` mais as colunas de teste `aderencia_objeto (S/N/D);processo_contratacao;pesquisa_precos;contrato;atesto;entrega_comprovada (S/N);quantidade;preco_unitario;preco_referencia;data_constituicao_fornecedor;sancao_ceis (S/N)`. Uma linha por empenho; empenho com mais de uma liquidação ou pagamento é consolidado antes, com a memória guardada.

Registro de documentos (`assets/exemplo_registro_documentos.json`): processo (número, juízo, ação, objeto do saneamento, datas), perito, prazo_laudo (data_inicio, dias), partes (id, nome, papel: autor, réu, terceiro, perito) e documentos (id, descricao, parte_responsavel, fonte_recurso, status recebido|parcial|pendente, data_pedido, prazo_dias, data_recebimento, observacao).

Números no padrão brasileiro (1.234,56) ou técnico (1234.56); datas em dd/mm/aaaa; codificação UTF-8.
