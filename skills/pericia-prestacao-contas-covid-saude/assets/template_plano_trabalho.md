# Template de plano de trabalho pericial: prestação de contas de recursos da covid-19

Uso: preencher os campos entre colchetes antes do início dos trabalhos; o plano é documento interno do perito e pode ser juntado aos autos quando o juízo o exigir ou quando convier declarar o método e a amostra. Alimenta `assets/exemplo_registro_documentos.json` (seção 6) e orienta o termo de diligência gerado por `scripts/checklist_documental_covid.py`. Nenhuma norma entra sem conferência (`references/fundamentacao-legal.md`); o que não estiver verificado leva `[A VERIFICAR]`.

Nome de arquivo sugerido: `AAAA-MM-DD_PlanoTrabalho_PrestacaoContasCovid_v1.md`.

---

## Plano de trabalho pericial

**Processo nº** [número]
**Juízo** [vara e comarca]
**Ação** [classe; por exemplo, ação civil pública por improbidade administrativa]
**Autor** [nome]
**Réus** [ente e gestores]
**Perito** [nome], contador, CRC [registro]
**Nomeação** [dd/mm/aaaa]; intimação em [dd/mm/aaaa]
**Prazo do laudo** [n] dias, contados de [marco fixado pelo juízo ou a requerer]

---

## 1. Objeto conforme a decisão de saneamento

Transcrever os pontos controvertidos e o objeto da perícia fixados na decisão de [dd/mm/aaaa] (CPC, art. 357). Delimitar o período ([mm/aaaa] a [mm/aaaa]), as fontes de recursos ([códigos e origens]) e o ente ou unidade auditada.

Fora do objeto, por delimitação do juízo ou por natureza: [qualificação jurídica dos fatos; responsabilidade pessoal; atualização monetária, a cargo da liquidação].

---

## 2. Quesitos e pertinência

| Origem | Nº | Quesito (síntese) | Pertinente ao objeto | Etapa que responde | Observação |
|---|---|---|---|---|---|
| Juízo | 1 | | sim | conciliação | |
| Autor | 1 | | sim | matriz | |
| Réu | 1 | | [sim / parcial / impugnar, CPC art. 470] | | |

Quesitos impertinentes ou que pedem conclusão jurídica: indicar ao juízo na forma do art. 470 do CPC, com a razão.

---

## 3. Metodologia

1. Inventário de fontes: relatório do repassador, extratos das contas específicas e razão por fonte, confrontados; transcrição em CSV (`assets/exemplo_receitas.csv`).
2. Conciliação por fonte e mês (`scripts/conciliacao_fonte_recurso.py`): recebido, empenhado, liquidado, pago, saldo, restos a pagar, devoluções, inconsistências de estágio, alertas por fonte.
3. Testes por despesa (`scripts/matriz_despesas_covid.py`): aderência ao objeto, processo, pesquisa de preços, contrato, nota fiscal, atesto, entrega, estágios, preço contra referência, fracionamento, fornecedor.
4. Quantificação por classe e por fonte, em valores nominais.
5. Laudo pelo template `assets/template_laudo.md`, com resposta a cada quesito e seção de limitações.

Premissas declaradas: tolerância de sobrepreço [20%]; janela de fracionamento [30] dias; fornecedor novo abaixo de [180] dias; preço de referência obtido por `licitacoes-contratos` em [fonte] para o mês de cada contratação.

---

## 4. Universo e amostragem

| Item | Valor |
|---|---|
| Empenhos no período (conforme relação do ente ou da inicial) | [n] |
| Valor empenhado | R$ [valor] |
| Limite para teste censitário | [50] despesas |
| Critério acima do limite | todas as despesas com achado objetivo; maiores valores até [70%] do empenhado; seleção sistemática dos restantes (NBC TA 530, por analogia) |
| Cobertura prevista | [100% / n itens, x% do valor] |

Declarar aqui o que for decidido; o laudo informa a cobertura efetiva.

---

## 5. Cronograma

| Semana | Atividade | Produto | Dependência |
|---|---|---|---|
| 1 | Leitura dos autos; plano; registro de documentos; termo de diligência; ofícios | plano, termo, ofícios | nomeação |
| 2 a 3 | Recebimento e conferência; consultas públicas (FNS, CEIS, CNPJ, PNCP) | painel atualizado; consultas anexadas | respostas das partes |
| 3 a 4 | Transcrição dos CSV; conciliação por fonte | conciliação.json e .md | D01 a D04 |
| 4 a 6 | Testes por despesa; preço de referência; diligências adicionais | matriz.json e .md | D05, D09, D10 |
| 6 a 7 | Quantificação; redação dos achados; resposta a quesitos | minuta do laudo | tudo acima |
| 8 | Revisão, anexos, protocolo com antecedência do art. 477 | laudo | |

Marco de risco: se D03 e D04 não chegarem até a semana [3], peticionar na forma de `references/roteiro-documental-e-diligencias.md`, seção 6.

---

## 6. Documentos requeridos por responsável

| ID | Documento | Responsável | Prazo (dias) | Fonte | Uso na perícia |
|---|---|---|---|---|---|
| D01 | Relatório de repasses do FNS por competência e portaria | ente | 15 | fundo a fundo | conciliação, coluna recebido |
| D02 | Extratos das contas específicas, com aplicação | ente | 15 | todas | confronto; rendimentos |
| D03 | Razão por fonte e por conta | ente | 15 | todas | confronto; saldo |
| D04 | Relação de empenhos, liquidações e pagamentos por fonte | ente | 15 | todas | conciliação e matriz |
| D05 | Processos das contratações emergenciais | ente | 15 | todas | matriz |
| D06 | Portarias e atos de transferência citados na inicial | autor | 15 | fundo a fundo | inventário de fontes |
| D07 | RAG, relatórios quadrimestrais, pareceres do conselho | ente | 15 | todas | conferência |
| D08 | Prestação de contas e auditorias do tribunal de contas | TCE (ofício) | 20 | todas | conferência |
| D09 | Almoxarifado e patrimônio | ente | 15 | todas | entrega comprovada |
| D10 | Leitos, produção, plano de contingência | ente | 15 | investimento | aderência |
| D11 | Consultas CNPJ, CEIS, CNEP | perito | 5 | todas | fornecedor |
| D12 | Inquérito civil pesquisável | autor | 15 | todas | leitura |
| D13 | Extratos e ordens bancárias diretamente do banco | banco (ofício) | 20 | todas | confronto |
| D14 | Atas do conselho; plano de contingência | ente | 15 | todas | aderência |

Transcrever esta tabela no JSON de registro e gerar o termo e os ofícios.

---

## 7. Comunicação, assistentes e início dos trabalhos

Data e local de início: [dd/mm/aaaa, local], comunicados às partes e aos assistentes técnicos (CPC, art. 474). Acesso dos assistentes às diligências e aos arquivos de trabalho (CPC, art. 466, § 2º): [forma]. Canal de recebimento de documentos: [e-mail, sistema]. Quesitos suplementares (CPC, art. 469) serão registrados nesta seção com data.

---

## 8. Riscos e contingências

| Risco | Sinal | Resposta |
|---|---|---|
| Documentação essencial não chega | painel com D03 ou D04 atrasados | petição de intimação (CPC, art. 400) e nova contagem ou prorrogação (art. 476) |
| Extratos divergem do razão | confronto da etapa 1 | ofício ao banco (D13); achado de divergência |
| Sem referência de preço para itens de 2020 | `licitacoes-contratos` sem resultado para o mês | registrar "sem referência"; não arbitrar |
| Universo maior que o previsto | relação D04 com mais de [50] empenhos | aplicar a amostra da seção 4 e declarar |
| Prazo do laudo próximo com pendências | painel com menos de [20] dias | prorrogação ou laudo com limitação declarada e complementação |

---

## 9. Honorários e custos

Proposta apresentada em [dd/mm/aaaa] (CPC, art. 465, § 2º), pela skill `proposta-pericial-judicial`; horas estimadas por etapa: [tabela]. Custos de diligência (deslocamento, cópias): [valor], a requerer.

---

## Exemplo preenchido (dados fictícios)

Processo 0000000-00.0000.0.00.0000, Vara da Fazenda Pública da Comarca de Exemplo. Ação civil pública por improbidade. Ministério Público do Estado (autor) x Município de Exemplo e João da Silva, ex-prefeito (réus). Perita Maria da Silva, CRC 000000/O-0, nomeada em 01/09/2026, intimada em 08/09/2026; prazo de 60 dias contados do termo de início (15/09/2026), limite em 14/11/2026.

Objeto conforme o saneamento de 20/08/2026: aplicação e prestação de contas dos recursos das fontes 214-COVID, 215-COVID e LC 173/2020, art. 5º, I, nos exercícios de 2020 e 2021; despesas sem comprovação, desvio de finalidade e sobrepreço. Universo informado na inicial: 14 empenhos, R$ 727.500,00; teste censitário. Premissas: tolerância de sobrepreço 20%; janela de fracionamento 30 dias; fornecedor novo abaixo de 180 dias; referência de preços pela mediana de contratações similares do mesmo mês, via `licitacoes-contratos`.

Documentos requeridos em 15/09/2026 ao Município (D01 a D05, D07, D09, D10, D14; 15 dias), ao autor (D06, D12; 15 dias) e, por ofício requerido ao juízo em 18/09/2026, ao TCE (D08) e ao Banco Alfa S.A. (D13; 20 dias). Diligência própria D11 concluída em 17/09/2026. Marco de risco: sem D03 e D04 até 06/10/2026, petição de intimação com pedido de contagem do prazo a partir da juntada.

---

## Pendências de verificação

1. [Portarias GM/MS citadas na inicial: número, data e valor conferidos no Portal FNS.]
2. [Vigência da Lei 13.979/2020 para as contratações de 2021.]
3. [Artigos da LC 141/2012 sobre relatórios e SIOPS.]
