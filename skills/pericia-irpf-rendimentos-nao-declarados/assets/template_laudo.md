# Template de laudo pericial contábil: IRPF por rendimentos não declarados

Uso: preencher os campos entre colchetes; excluir as seções inaplicáveis. Nenhum número entra sem memória de cálculo gerada pelos scripts. Toda citação segue o protocolo antifabricação de `references/fundamentacao-legal.md`, seção 9. Para atuação como assistente técnico, trocar o título por "Parecer técnico contábil", declarar a parte assistida no cabeçalho e manter a mesma memória de cálculo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_IRPF_RendimentosNaoDeclarados_[NomeAbreviado]_v1.md` (por exemplo, `2026-09-12_Laudo_IRPF_RendimentosNaoDeclarados_v1.md`).

---

## Laudo pericial contábil

**Processo nº** [número]
**Vara** [juízo]
**Ação** [Anulatória de débito fiscal / Embargos à execução fiscal nº ...]
**Autora** [contribuinte]
**Ré** União (Fazenda Nacional)
**Perito** [nome], contador, CRC [registro]
**Data-base do laudo** [dd/mm/aaaa]
**Auto de infração** [número, processo administrativo, anos-calendário]

---

## 1. Objeto

A perícia tem por objeto o exame da documentação apresentada pela autora para comprovar a origem dos valores imputados no auto de infração nº [número] (anos-calendário [anos]), a classificação da natureza tributária de cada crédito, a aplicação das exclusões do § 3º do art. 42 da Lei 9.430/1996, o recálculo do imposto devido pela apuração anual e pela tributação mensal do § 4º, a apuração da multa de ofício e dos juros, o confronto com os valores lançados e o levantamento das datas relevantes para a decadência.

Não integram o objeto: a validade da intimação, a nulidade do lançamento, a boa-fé da contribuinte, a suficiência jurídica da prova e a regra de decadência aplicável, matérias reservadas ao juízo (CPC, art. 473, § 2º).

---

## 2. Quesitos

| Origem | Nº | Quesito | Seção da resposta |
|---|---|---|---|
| Juízo | 1 | [transcrever] | [7.1] |
| Autora | 1 | [transcrever] | [7.2] |
| União | 1 | [transcrever] | [7.3] |

---

## 3. Documentos examinados

| Nº | Documento | Fls. | Origem | Observação |
|---|---|---|---|---|
| 1 | Auto de infração e demonstrativos de apuração, multa e juros | | União | [base da infração, anos, tabela, multa, data dos juros] |
| 2 | Termo de intimação para comprovar a origem dos créditos e resposta | | PAF | [data, discriminação dos créditos] |
| 3 | Extratos bancários das contas examinadas | | Autos | [contas, período, completude] |
| 4 | DIRPF dos anos [anos] e do ano anterior | | Autora | [bens, dívidas, rendimentos isentos, doações] |
| 5 | Documentos de origem por crédito (contratos, informes, ITCMD, ATPV, extratos de terceiros) | | Autora | [relacionados no quadro 5.2] |
| 6 | Tabela progressiva anual e mensal dos anos [anos] | | Perito | [fonte: gov.br/receitafederal, consulta em dd/mm/aaaa] |
| 7 | Limites de dedução do exercício | | Perito | [fonte e data] |
| 8 | Série Selic mensal de [mm/aaaa] a [mm/aaaa] | | Perito | [fonte: bcb.gov.br/SGS, código validado, consulta em dd/mm/aaaa] |

---

## 4. Metodologia

1. Transcrição de todos os créditos imputados no arquivo estruturado (`exemplo_rendimentos.csv` como modelo), inclusive os já excluídos pelo auto, para reproduzir o lançamento.
2. Classificação crédito a crédito (`scripts/classificar_rendimentos.py`) pela tabela de naturezas, com avaliação da prova por regras declaradas: data do documento a até [10] dias do crédito; valor coincidente com tolerância de [0,5%]; contraparte identificada; prova qualificada quando a natureza exige. Dois cenários: base (só prova suficiente afasta a presunção) e ampliado (prova parcial aceita).
3. Aplicação do § 3º, I (transferências próprias) e II (créditos até R$ 12.000,00 com soma anual até R$ 80.000,00, Lei 9.481/1997, art. 4º) e, se o caso, do § 6º (conta conjunta).
4. Recálculo do imposto (`scripts/recalculo_irpf.py`) em dois modos: anual (base adicional no ajuste, com deduções e tabela anual) e mensal (presumido no mês do crédito pela tabela mensal, § 4º; rendimento de fonte identificada no ajuste), com compensação do imposto da DIRPF original e do IRRF.
5. Encargos (`scripts/encargos_auto_infracao.py`): multa de ofício de [75%] (Lei 9.430/1996, art. 44, I), juros pela Selic acumulada do mês seguinte ao vencimento ao mês anterior ao pagamento mais 1% no mês do pagamento (art. 61, § 3º), confronto item a item com o auto e reprodução dos juros na data do auto.
6. Decadência: termos finais dos arts. 150, § 4º, e 173, I, do CTN por ano-calendário, contra a data da ciência.
7. Toda operação executada em código, com memória reproduzível em anexo. Valores nominais na data de referência dos juros.

---

## 5. Análise

### 5.1. Lançamento e intimação

| Item | Registro |
|---|---|
| Base da infração | [DIRF / depósitos / patrimônio] |
| Anos-calendário | |
| Intimação para comprovar a origem | [data, discriminação dos créditos, resposta] |
| Créditos imputados | [quantidade e total] |
| Exclusões já aplicadas pelo auto | [§ 3º, I e II; § 6º] |
| Tabela e deduções usadas pelo auto | |
| IRRF compensado pelo auto | |
| Multa (percentual e fundamento) | |
| Juros calculados até | |
| Ciência do lançamento | |

### 5.2. Quadro crédito a crédito

| id | Data | Valor | Natureza alegada | Documento | Prova | Motivo | Tratamento base | Tratamento ampliado |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

(Tabela completa gerada pelo script no Anexo I.)

### 5.3. Quadro por tratamento

| Tratamento | Cenário base | Cenário ampliado |
|---|---|---|
| Ajuste (já declarado e não declarado) | R$ | R$ |
| Exclusivo na fonte | R$ | R$ |
| Isento | R$ | R$ |
| Não rendimento | R$ | R$ |
| Terceiro (§ 5º) | R$ | R$ |
| Presumido (art. 42) | R$ | R$ |
| Excluído pelo § 3º, II | R$ | R$ |
| Total imputado (sanidade) | R$ | R$ |

### 5.4. Exclusões do § 3º e conta conjunta

[Créditos até R$ 12.000,00 que permaneceram presumidos, soma por ano, resultado; transferências próprias com o extrato de origem; conta conjunta e titulares.]

### 5.5. Recálculo do imposto

| Item | Cenário base, anual | Cenário base, mensal | Cenário ampliado, anual | Cenário ampliado, mensal |
|---|---|---|---|---|
| Rendimentos declarados | R$ | R$ | R$ | R$ |
| Presumido (art. 42) | R$ | R$ | R$ | R$ |
| Fonte identificada não declarado | R$ | R$ | R$ | R$ |
| Dedução adotada | R$ | R$ | R$ | R$ |
| Base de cálculo | R$ | (mensal) | R$ | (mensal) |
| Imposto devido | R$ | R$ | R$ | R$ |
| Imposto da DIRPF original (T0) | R$ | R$ | R$ | R$ |
| IRRF compensável | R$ | R$ | R$ | R$ |
| Imposto suplementar | R$ | R$ | R$ | R$ |

### 5.6. Encargos e confronto com o auto

| Item | Lançado | Recalculado ([cenário/modo]) | Diferença |
|---|---|---|---|
| Principal | R$ | R$ | R$ |
| Multa ([75%]) | R$ | R$ | R$ |
| Juros (Selic acumulada [x%]) | R$ | R$ | R$ |
| Total | R$ | R$ | R$ |

Juros do auto em [data]: Selic implícita [x%] contra [y%] acumulados pela série oficial; [reproduzível / não reproduzível em: ...]. Cenário informativo de multa de mora (art. 61): R$ [valor].

### 5.7. Decadência

| Ano-calendário | Fato gerador | Ciência | Termo final art. 150, § 4º | Termo final art. 173, I |
|---|---|---|---|---|
| | | | [dentro / fora] | [dentro / fora] |

O perito registra as datas; a regra aplicável (Súmula 555/STJ [A VERIFICAR]; tese do fato gerador mensal sob o § 4º) é matéria do juízo.

---

## 6. Conclusão

[Redigir por cenário e modo, sem juízo sobre a procedência.]

Dos [n] créditos imputados (R$ [total]), [n] têm prova suficiente de origem, [n] prova parcial e [n] nenhuma prova. No cenário base, permanecem presumidos R$ [valor], e o imposto suplementar é de R$ [valor] na apuração anual e R$ [valor] na tributação mensal; no cenário ampliado, R$ [valor] e R$ [valor]. Com multa de [75%] e juros até [data], o total recalculado no cenário base e modo anual é de R$ [valor], contra R$ [valor] lançados, diferença de R$ [valor], decorrente de [§ 3º, II, não aplicado; IRRF não compensado; série de juros diversa].

Limitações declaradas:

1. [Tabela, deduções e Selic obtidas em consulta de dd/mm/aaaa.]
2. [Documentos não localizados nos autos: ...]
3. [Itens marcados [A VERIFICAR] na fundamentação.]

---

## 7. Resposta aos quesitos

### 7.1. Quesitos do juízo

**Quesito 1.** [transcrever]
**Resposta.** [objetiva, com remissão à seção e ao quadro]

### 7.2. Quesitos da autora

### 7.3. Quesitos da União

---

## 8. Encerramento

Nada mais havendo a informar, o perito encerra o presente laudo, composto de [n] laudas e [n] anexos, e o submete à apreciação do juízo.

[Cidade], [dd/mm/aaaa].

[Nome do perito]
Contador, CRC [registro]
Perito nomeado

---

## Anexos

| Anexo | Conteúdo |
|---|---|
| I | Classificação crédito a crédito e totais (CSV e Markdown de `classificar_rendimentos.py`) |
| II | Recálculo do imposto por cenário e modo, com memória (`recalculo_irpf.py`) |
| III | Encargos, confronto com o auto e decadência, com memória (`encargos_auto_infracao.py`) |
| IV | Tabela progressiva, limites de dedução e série Selic com as consultas às fontes |
| V | Transcrição do termo de intimação e do enquadramento legal do auto |

---

## Exemplo preenchido (dados fictícios dos assets)

Processo 0000000-00.0000.0.00.0000. Maria da Silva (autora) x União. Auto de infração sobre o ano-calendário 2023, com 20 créditos imputados na conta CC 0001-1 do Banco Alfa, total de R$ 457.550,00. Intimação de [data] discriminou os créditos; a autora respondeu com os documentos das fls. 41 a 101.

Quadro por tratamento (cenário base): ajuste R$ 19.500,00 (dos quais R$ 15.000,00 de aluguéis e honorários não declarados, com IRRF de R$ 225,00 não compensado pelo auto); exclusivo na fonte R$ 500,00; isento R$ 12.200,00; não rendimento R$ 69.700,00; presumido R$ 340.000,00 (créditos 5, 7 e 12); excluído pelo § 3º, II, R$ 15.650,00 (créditos 8, 9, 17 e 19, que o auto não excluiu). Treze créditos com prova suficiente, três com prova parcial (mútuo sem data certa, doação sem ITCMD, declaração de terceira sem procuração), quatro sem prova.

| Item | Base, anual | Base, mensal | Ampliado, anual | Ampliado, mensal |
|---|---|---|---|---|
| Base adicional | R$ 355.000,00 | R$ 355.000,00 | R$ 30.000,00 | R$ 30.000,00 |
| Imposto suplementar | R$ 95.421,00 | R$ 93.189,50 | R$ 6.046,00 | R$ 5.664,50 |

Encargos no cenário base, modo anual, até 12/09/2026: multa de 75% R$ 71.565,75; Selic acumulada 29,82%; juros R$ 28.454,54; total R$ 195.441,29. Lançado: principal R$ 99.949,75, multa R$ 74.962,31, juros R$ 29.385,23 até 31/08/2026 (Selic implícita 29,40% contra 28,84% da série), total R$ 204.297,29; diferença na data do auto R$ 9.791,12. Decadência: fato gerador 31/12/2023, ciência em 15/03/2026, dentro dos dois prazos (31/12/2028 e 31/12/2029).

Resposta ao quesito 3 da autora: em parte. Treze dos 20 créditos têm prova suficiente de origem, mas R$ 15.000,00 deles são aluguéis e honorários tributáveis no ajuste (§ 2º). Os créditos 5 e 7 (R$ 325.000,00) têm prova parcial e permanecem presumidos no cenário base; a suficiência é matéria do juízo (TRF1, AC 0002129-66.2013.4.01.4200).

---

## Pendências de verificação

Listar aqui todo item `[A VERIFICAR]` que restou no laudo, com o que conferir e onde, na forma da seção 10 de `references/fundamentacao-legal.md`:

1. [Súmula 555/STJ: texto literal, antes de citar a regra de decadência.]
2. [Súmula CARF 38: fato gerador em 31/12, antes de fundamentar o modo anual.]
3. [Lei 9.430/1996, art. 44: redação vigente dos percentuais da multa.]
4. [Tabela progressiva, limites de dedução e série Selic do ano do caso, com a consulta anexada.]
