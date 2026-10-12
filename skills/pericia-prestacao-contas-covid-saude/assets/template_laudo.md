# Template de laudo pericial contábil: prestação de contas de recursos da covid-19 na saúde

Uso: preencher os campos entre colchetes; excluir as seções inaplicáveis. Nenhum número entra sem a memória gerada pelos scripts (`conciliacao_fonte_recurso.py`, `matriz_despesas_covid.py`) e nenhum documento ausente entra sem a cronologia do painel (`checklist_documental_covid.py`). Toda citação segue o protocolo antifabricação de `references/fundamentacao-legal.md`, seção 8. Para atuação como assistente técnico, trocar o título por "Parecer técnico contábil", declarar a parte assistida no cabeçalho e manter a mesma memória.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_PrestacaoContasCovid_[NomeAbreviado]_v1.md`.

---

## Laudo pericial contábil

**Processo nº** [número]
**Juízo** [vara e comarca]
**Ação** [classe]
**Autor** [nome]
**Réus** [ente e gestores]
**Perito** [nome], contador, CRC [registro]
**Data-base do laudo** [dd/mm/aaaa]
**Período examinado** [mm/aaaa] a [mm/aaaa]

---

## 1. Objeto

A perícia tem por objeto, conforme a decisão de saneamento de [dd/mm/aaaa], a verificação da aplicação e da prestação de contas dos recursos recebidos por [ente] para o enfrentamento da covid-19 nas fontes [códigos e origens], no período de [mm/aaaa] a [mm/aaaa], compreendendo o inventário das fontes, a conciliação entre recursos recebidos e despesas empenhadas, liquidadas e pagas, a verificação dos estágios da despesa, o teste de cada despesa quanto à aderência ao objeto da fonte, à contratação, à comprovação da entrega e ao preço, e a quantificação do que ficou sem comprovação nos autos ou foi aplicado em objeto estranho à fonte.

Não integram o objeto: a qualificação jurídica dos fatos como improbidade, a aferição de dolo, a responsabilidade pessoal e a prescrição, matérias reservadas ao juízo (CPC, art. 473, § 2º); a atualização monetária dos valores, a cargo da liquidação.

---

## 2. Quesitos

| Origem | Nº | Quesito | Seção da resposta |
|---|---|---|---|
| Juízo | 1 | [transcrever] | [11.1] |
| Autor | 1 | [transcrever] | [11.2] |
| Réu | 1 | [transcrever] | [11.3] |

---

## 3. Metodologia e amostragem

1. Inventário de fontes a partir de três visões confrontadas: relatório do repassador ([consulta ao Portal FNS em dd/mm/aaaa, anexo]), extratos das contas específicas e razão contábil por fonte.
2. Conciliação por fonte e por mês (`scripts/conciliacao_fonte_recurso.py`), com restos a pagar em cada 31/12, devoluções, rendimentos, inconsistências de estágio (Lei 4.320/1964, arts. 60, 62 e 63) e alertas por fonte (LRF, art. 8º, parágrafo único).
3. Testes por despesa (`scripts/matriz_despesas_covid.py`): aderência ao objeto, processo de contratação, pesquisa de preços, contrato, nota fiscal, atesto, entrega, estágios, preço contra referência, fracionamento, fornecedor.
4. Premissas declaradas: tolerância de sobrepreço [20%]; janela de fracionamento [30] dias; fornecedor novo abaixo de [180] dias; preço de referência por [fonte e método], para o mês de cada contratação.
5. Universo de [n] empenhos e R$ [valor]; [teste censitário / amostra de n itens, x% do valor, pelo critério declarado no plano de trabalho de dd/mm/aaaa].
6. Toda operação executada em código, com memória reproduzível em anexo. Valores nominais nas datas dos documentos.

---

## 4. Documentos examinados e documentos não fornecidos

### 4.1. Examinados

| Nº | Documento | Fls. ou origem | Data | Observação |
|---|---|---|---|---|
| 1 | Decisão de saneamento e nomeação | | | |
| 2 | Relatório de repasses do FNS | | | [conferido com o Portal FNS em dd/mm/aaaa] |
| 3 | Extratos das contas específicas | | | [período coberto] |
| 4 | Razão por fonte | | | |
| 5 | Relação de empenhos, liquidações e pagamentos | | | [layout CSV, anexo] |
| 6 | Processos de contratação [números] | | | [n de m processos] |
| 7 | Consultas CNPJ, CEIS, CNEP | | | [datas] |

### 4.2. Requeridos e não fornecidos

| ID | Documento | Responsável | Pedido em | Prazo | Reiterações | Situação na data do laudo | Efeito sobre o laudo |
|---|---|---|---|---|---|---|---|
| [D04] | | | | | [petição de dd/mm/aaaa] | pendente | [seção afetada] |

A consequência probatória da não exibição (CPC, art. 400) é matéria do juízo.

---

## 5. Inventário de fontes de recursos

| Fonte | Origem normativa | Conta | Recebido (repassador) | Recebido (extrato) | Recebido (razão) | Divergência |
|---|---|---|---|---|---|---|
| [214-COVID] | [portarias GM/MS, números e datas conferidos] | [agência/conta] | R$ | R$ | R$ | R$ |
| [LC173-SAUDE] | LC 173/2020, art. 5º, I | | R$ | R$ | R$ | R$ |

Devoluções ao repassador: [data, documento, valor]. Rendimentos de aplicação: [valor, destino].

---

## 6. Conciliação por fonte

| Fonte | Recebido líquido | Empenhado | Liquidado | Pago | Saldo financeiro | A liquidar | A pagar |
|---|---|---|---|---|---|---|---|
| | R$ | R$ | R$ | R$ | R$ | R$ | R$ |
| Total | R$ | R$ | R$ | R$ | R$ | R$ | R$ |

Restos a pagar em [31/12/aaaa]: processados R$ [valor]; não processados R$ [valor] (Anexo I). Inconsistências de estágio: [quantidade e valor por tipo] (Anexo I, seção 5). Alertas por fonte: [descrever]. Sanidade: OK ([n] testes). Quadro mensal no Anexo I.

---

## 7. Matriz de testes: classificação por despesa

| Empenho | Fonte | Credor | Objeto | Pago | Classe | Base | Achados |
|---|---|---|---|---|---|---|---|
| | | | | R$ | | R$ | |

Totais por classe:

| Classe | Quantidade | Pago | Base de quantificação |
|---|---|---|---|
| desvio de finalidade | | R$ | R$ |
| sem comprovação | | R$ | R$ |
| sobrepreço a apurar | | R$ | R$ |
| aderência a esclarecer | | R$ | |
| irregularidade formal | | R$ | |
| regular | | R$ | |
| Total | | R$ | R$ |

Fracionamento, fornecedores e preço contra referência: Anexo II, seções 5 a 7.

---

## 8. Achados

Cada achado em quatro partes: fato, evidência, norma, efeito (`references/matriz-de-testes-e-red-flags.md`, seção 8).

**Achado 1.** [Fato: empenho, data, credor, objeto, valor, estágio.] [Evidência: documento e folha, ou ausência com cronologia.] [Norma: dispositivo.] [Efeito: classe, base de quantificação, o que mudaria com documento novo.]

**Achado 2.** [...]

---

## 9. Quantificação

| Classe | Fonte | Exercício | Quantidade | Valor nominal |
|---|---|---|---|---|
| Aplicado em objeto estranho à fonte | | | | R$ |
| Sem comprovação nos autos | | | | R$ |
| Diferença contra a referência de preço | | | | R$ |
| Total | | | | R$ |

Valores nominais nas datas de pagamento. Devoluções já realizadas relativas aos mesmos objetos: R$ [valor], em [data]. Atualização e juros conforme critério do juízo (skill `atualizacao-monetaria`). A imputação, a solidariedade e o ressarcimento são matéria do juízo (Lei 8.429/1992, art. 12; Tema 1.089/STJ).

---

## 10. Conclusão

[Redigir por fonte e por classe, sem juízo sobre a procedência.]

No período de [mm/aaaa] a [mm/aaaa], o ente recebeu R$ [valor] nas fontes examinadas, empenhou R$ [valor], liquidou R$ [valor] e pagou R$ [valor], com saldo financeiro de R$ [valor] e devolução de R$ [valor] em [data]. Dos [n] empenhos testados, [n] são regulares, [n] têm irregularidade formal sem efeito quantificado, [n] estão sem comprovação nos autos (R$ [valor]), [n] foram aplicados em objeto estranho à fonte (R$ [valor]) e [n] apresentam preço acima da referência além da tolerância declarada (diferença de R$ [valor]).

Limitações declaradas:

1. [Documentos D03 e D04 apresentados em dd/mm/aaaa, após reiteração; cobrem até mm/aaaa.]
2. [Processos de contratação: n de m apresentados; a classe das despesas sem processo pode mudar com a juntada.]
3. [Referência de preço indisponível para os itens x e y.]
4. [Itens marcados `[A VERIFICAR]` na fundamentação.]

---

## 11. Resposta aos quesitos

### 11.1. Quesitos do juízo

**Quesito 1.** [transcrever]
**Resposta.** [objetiva, com remissão à seção e à tabela]

### 11.2. Quesitos do autor

### 11.3. Quesitos do réu

---

## 12. Encerramento

Nada mais havendo a informar, o perito encerra o presente laudo, composto de [n] laudas e [n] anexos, e o submete à apreciação do juízo.

[Cidade], [dd/mm/aaaa].

[Nome do perito]
Contador, CRC [registro]
Perito nomeado

---

## Anexos

| Anexo | Conteúdo |
|---|---|
| I | Conciliação por fonte e mês, restos a pagar, inconsistências (JSON, Markdown e CSV de `conciliacao_fonte_recurso.py`) |
| II | Matriz de testes por despesa, totais, fracionamento, fornecedores, preço x referência (`matriz_despesas_covid.py`) |
| III | Painel de documentos, termo de diligência, ofícios e petições (`checklist_documental_covid.py`) |
| IV | Consultas públicas com data: Portal FNS, CEIS, CNEP, CNPJ, PNCP; referências de preço (`licitacoes-contratos`) |
| V | Transcrição das portarias e atos de transferência; CSV de receitas e despesas transcritos dos autos |

---

## Exemplo preenchido (dados fictícios dos assets)

Processo 0000000-00.0000.0.00.0000, Vara da Fazenda Pública da Comarca de Exemplo. Ministério Público do Estado (autor) x Município de Exemplo e João da Silva, ex-prefeito (réus). Perita Maria da Silva, CRC 000000/O-0. Período 03/2020 a 02/2021; fontes 214-COVID e 215-COVID (fundo a fundo, portarias fictícias 0001, 0002 e 0003/2020), LC173-SAUDE (LC 173/2020, art. 5º, I) e LC173-LIVRE (sem receita registrada nas fontes examinadas).

Conciliação: recebido líquido R$ 721.250,40 (bruto R$ 741.250,40, devolução de R$ 20.000,00 em 15/01/2021 e rendimento de R$ 1.250,40); empenhado R$ 727.500,00; liquidado R$ 705.500,00; pago R$ 723.500,00. Na fonte 215-COVID o pago (R$ 120.000,00) supera o recebido (R$ 100.000,00); a despesa E-2020/0230 (R$ 25.000,00) está na fonte LC173-LIVRE, sem receita registrada. Restos a pagar em 31/12/2020: processados R$ 40.000,00 (E-2020/0260, pago em 12/02/2021); não processados R$ 9.000,00 (E-2020/0271, sem liquidação). Inconsistências: pagamento sem liquidação (E-2020/0130, R$ 18.000,00); nota fiscal e liquidação anteriores ao empenho (E-2020/0163, R$ 42.000,00); liquidação superior ao empenho (E-2020/0205, R$ 5.000,00). Sanidade OK em 21 testes.

Matriz (14 empenhos, teste censitário): desvio de finalidade 1 (E-2020/0158, recapeamento asfáltico, R$ 85.000,00); sem comprovação 1 (E-2020/0170, ventiladores sem evidência de entrega, R$ 120.000,00); sobrepreço a apurar 1 (E-2020/0115, máscaras N95 a R$ 12,00 contra referência de R$ 8,00, variação de 50%, diferença de R$ 32.000,00); aderência a esclarecer 1 (E-2020/0184, tablets, R$ 30.000,00); irregularidade formal 6; regular 4. Fracionamento: Gama Serviços de Limpeza (E-2020/0130 e E-2020/0142, 20 dias, R$ 35.500,00). Fornecedores: Beta (78 dias de constituição) e Kappa (111 dias; sanção registrada). Base de quantificação: R$ 237.000,00.

Resposta ao quesito 5 do juízo: o valor das despesas sem comprovação nos autos é de R$ 120.000,00 (fonte LC173-SAUDE, exercício 2020) e o das despesas aplicadas em objeto estranho à fonte é de R$ 85.000,00 (fonte LC173-SAUDE, exercício 2020), ambos nominais nas datas de pagamento (seção 9), além de R$ 32.000,00 de diferença contra a referência de preço no empenho E-2020/0115 (fonte 214-COVID), a apurar. Os registros de uso dos ventiladores (D09 e D10), requeridos em 15/09/2026 e pendentes, podem alterar a primeira parcela.

---

## Pendências de verificação

Listar aqui todo item `[A VERIFICAR]` que restou no laudo, com o que conferir e onde, na forma da seção 9 de `references/fundamentacao-legal.md`:

1. [Portarias GM/MS de repasse: número, data e valor conferidos no Portal FNS.]
2. [Data-limite de vigência da Lei 13.979/2020 para as contratações de 2021.]
3. [Artigos da LC 141/2012 sobre relatórios de gestão e SIOPS.]
