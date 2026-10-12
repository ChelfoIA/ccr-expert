# Template de laudo pericial contábil: revisão de benefício concedido antes da CF/88

Uso: preencher os campos entre colchetes; excluir as seções inaplicáveis. Nenhum número entra sem memória de cálculo gerada pelos scripts. Toda citação segue o protocolo antifabricação de `references/fundamentacao-legal.md`, seção 8. Para atuação como assistente técnico, trocar o título por "Parecer técnico contábil", declarar a parte assistida no cabeçalho e manter a mesma memória de cálculo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_BeneficioPreCF88_[NomeAbreviado]_v1.md` (por exemplo, `2026-09-12_Laudo_BeneficioPreCF88_v1.md`).

---

## Laudo pericial contábil

**Processo nº** [número]
**Vara** [Vara Federal e Seção Judiciária]
**Ação** [Revisional de benefício previdenciário]
**Autor** [segurado, falecido em dd/mm/aaaa; sucedido por ...]
**Réu** Instituto Nacional do Seguro Social (INSS)
**Perito** [nome], contador, CRC [registro]
**Data-base do laudo** [dd/mm/aaaa]
**Benefício** [espécie, NB, DIB mm/aaaa, moeda da DIB]

---

## 1. Objeto

A perícia tem por objeto a reconstrução da renda mensal inicial do benefício NB [número], concedido em [mm/aaaa] sob o regime da CLPS (Decreto 89.312/1984), a verificação da equivalência em salários mínimos do art. 58 do ADCT entre 04/1989 e 12/1991, a readequação aos tetos das EC 20/1998 e 41/2003 pelos limitadores da época (STJ, Tema 1.140), a apuração das diferenças mensais em relação à renda paga, o corte da prescrição quinquenal, a conversão em pensão por morte a partir do óbito do segurado, o encerramento no óbito da pensionista e a identificação dos destinatários de cada bloco de parcelas.

Não integram o objeto: a incidência da decadência e da prescrição, o regime jurídico da pensão aplicável, a validade das habilitações e a procedência da revisão, matérias reservadas ao juízo (CPC, art. 473, § 2º).

---

## 2. Quesitos

| Origem | Nº | Quesito | Seção da resposta |
|---|---|---|---|
| Juízo | 1 | [transcrever] | [7.1] |
| Autor/sucessores | 1 | [transcrever] | [7.2] |
| INSS | 1 | [transcrever] | [7.3] |

---

## 3. Documentos examinados

| Nº | Documento | Fls. | Origem | Observação |
|---|---|---|---|---|
| 1 | Carta de concessão e memória de cálculo do INSS | | Autos | [espécie, DIB, 36 SC, coeficientes, tetos, coeficiente, RMI] |
| 2 | Relação de salários de contribuição / CTPS | | Autos | [competências, moeda] |
| 3 | Extratos de pagamento HISCRE/HISCON (aposentadoria e pensão) | | INSS | [período coberto, lacunas] |
| 4 | Certidão de óbito do segurado | | Autos | [data] |
| 5 | Carta de concessão da pensão por morte | | Autos | [DIB da pensão, coeficiente] |
| 6 | Certidão de óbito da pensionista | | Autos | [data] |
| 7 | Decisões de habilitação | | Autos | [quem, título, data] |
| 8 | Tabela de coeficientes ORTN/OTN para DIB [mm/aaaa] | | Perito | [portaria MPAS, consulta em dd/mm/aaaa] |
| 9 | Salário mínimo da DIB e de 04/1989 a 12/1991 | | Perito | [decretos e leis, consulta em dd/mm/aaaa] |
| 10 | Menor e maior valor-teto na DIB; tetos por competência | | Perito | [portarias, EC 20/1998 art. 14, EC 41/2003 art. 5º] |
| 11 | Índices de reajuste dos benefícios | | Perito | [portarias MPS/INSS, consulta em dd/mm/aaaa] |
| 12 | Cortes de padrão monetário | | Perito | [padroes_monetarios.py da atualizacao-monetaria] |

---

## 4. Metodologia

1. Reconstrução da RMI (`scripts/rmi_clps84.py`): 36 salários de contribuição anteriores à DIB, correção dos 24 anteriores aos 12 últimos pelos coeficientes da tabela nº 8, conversão de moeda pelos cortes da tabela nº 12, média, limitação ao maior valor-teto, parcela até o menor valor-teto, excedente na fração de [1/30 por grupo de 12 contribuições x N grupos] `[A VERIFICAR: art. 23 do Decreto 89.312/1984]`, coeficiente de [x%], RMI e número de salários mínimos (Súmula 25 da TNU).
2. Evolução (`scripts/readequacao_tetos.py`): conversões de moeda, reajustes oficiais, equivalência do art. 58 do ADCT de 04/1989 a 12/1991, readequação em 12/1998 (maior valor-teto R$ 1.200,00; menor R$ 600,00) e em 12/2003 (R$ 2.400,00; R$ 1.200,00), trava no teto vigente, confronto com a renda paga; na falta de extrato, renda paga presumida igual à RMI reajustada.
3. Atrasados (`scripts/atrasados_prescricao.py`): bloco do titular até o mês do óbito; bloco da pensão do mês seguinte, com coeficiente de [x%] ([fundamento, regime vigente no óbito]), até o mês do óbito da pensionista; abono anual proporcional; prescrição quinquenal contada do ajuizamento em [dd/mm/aaaa], critério da [competência]; quadro informativo da decadência.
4. Valores nominais na moeda de cada competência; atualização e juros pela skill `atualizacao-monetaria`, regime da Fazenda Pública, a partir de `parcelas.json`.
5. Toda operação executada em código, com `Decimal` e arredondamento de duas casas apenas na apresentação; memórias em anexo.

---

## 5. Análise

### 5.1. Concessão e RMI reconstruída

| Item | INSS (carta) | Perícia | Divergência |
|---|---|---|---|
| Soma dos SC corrigidos | | | |
| Média (salário de benefício) | | | |
| Menor e maior valor-teto | | | |
| Parcela até o menor valor-teto | | | |
| Excedente e fração | | | |
| Coeficiente | | | |
| RMI | | | |
| RMI em salários mínimos | | | |
| Limitação na concessão | | [maior valor-teto / menor valor-teto / não limitado] | |

### 5.2. Moedas

[Cadeia de conversão aplicada, com os diplomas de cada corte; ressalva de conversão nominal.]

### 5.3. Art. 58 do ADCT (04/1989 a 12/1991)

| Competência | Salário mínimo | Renda devida (n x SM) | Renda paga | Diferença |
|---|---|---|---|---|

### 5.4. Readequação aos tetos das emendas (Tema 1.140)

| Emenda | Média evoluída | Maior valor-teto | Menor valor-teto | Renda readequada | Renda devida antes | Acréscimo | Aplicada |
|---|---|---|---|---|---|---|---|

[Evolução mês a mês no Anexo II; indicador "benefício limitado na concessão": S/N; critério de limitação adotado e cenário alternativo, se controvertido.]

### 5.5. Diferenças mensais, prescrição e abono

| Bloco | Situação | Moeda | Parcelas | Valor nominal |
|---|---|---|---|---|

### 5.6. Óbito do segurado, pensão e óbito da pensionista

[Datas, coeficiente da pensão e fundamento, pensão paga e presumida, cessação da cota (Decreto 3.048/1999, art. 114, I), destinatários de cada bloco (Lei 8.213/1991, art. 112; CPC, arts. 110, 313, I, 687 a 692).]

### 5.7. Decadência (informativo)

[Primeira prestação, termo inicial e final atribuídos `[A VERIFICAR: STF, Tema 313]`, ajuizamento, linha do TRF1 sobre readequação de teto; sem conclusão.]

---

## 6. Conclusão

[RMI reconstruída e número de salários mínimos; limitação na concessão; resultado do art. 58; acréscimos em cada emenda; total nominal por moeda das parcelas devidas e prescritas por bloco; limitações da prova (extratos faltantes, documentos ilegíveis); remissão à atualização.]

---

## 7. Respostas aos quesitos

### 7.1. Do juízo

> Quesito 1: "[...]"
> Resposta: [...]

### 7.2. Do autor ou sucessores

### 7.3. Do INSS

---

## 8. Encerramento e anexos

Anexo I: memória da RMI (`rmi_1987.md`). Anexo II: evolução mês a mês (`readequacao.md` e `.csv`). Anexo III: emendas e readequação. Anexo IV: parcelas, prescrição e blocos (`atrasados.md` e `.csv`). Anexo V: `parcelas.json` e memória da atualização. Anexo VI: tabelas utilizadas com fonte e data de consulta.

[Local, data, assinatura, CRC.]

---

## Pendências de verificação

[Listar cada item marcado `[A VERIFICAR]` no laudo, com o que precisa ser conferido e onde.]

---

## Exemplo preenchido (dados fictícios dos assets)

**Processo nº** 0000000-00.0000.0.00.0000. **Autor** José da Silva (segurado, falecido em 15/06/2010), sucedido por Maria da Silva (viúva pensionista, falecida em 20/09/2023), representada por seus sucessores. **Benefício** aposentadoria por tempo de serviço, DIB 03/1987 (Cz$). **Ajuizamento** 15/03/2008.

**5.1.** Os 36 salários de contribuição de 03/1984 a 02/1987 (24 em Cr$, convertidos a Cz$ pelo corte de 03/1986, e 12 em Cz$), corrigidos os 24 primeiros pelos coeficientes da tabela nº 8, somam Cz$ 987.700,00; média de Cz$ 27.436,11, superior ao maior valor-teto de Cz$ 24.000,00. Parcela até o menor valor-teto Cz$ 12.000,00; excedente Cz$ 12.000,00 na fração de 0,8 (1/30 x 24 grupos `[A VERIFICAR: art. 23 do Decreto 89.312/1984]`), Cz$ 9.600,00; coeficiente 95%; RMI Cz$ 20.520,00, equivalente a 17,1 salários mínimos de Cz$ 1.200,00. Limitação na concessão: maior valor-teto.

**5.3.** De 04/1989 a 12/1991 a renda devida é 17,1 vezes o salário mínimo da competência (Súmula 25 da TNU); sem extrato do período, a renda paga foi presumida igual à RMI reajustada, e a diferença de equivalência compõe o Anexo II.

**5.4.** Em 12/1998, média evoluída R$ 1.147,54; maior valor-teto R$ 1.200,00; menor R$ 600,00; renda readequada 95% x (600,00 + 0,8 x 547,54) = R$ 986,13 contra R$ 858,27 devidos antes: acréscimo de R$ 127,86. Em 12/2003, média evoluída R$ 1.804,25; renda readequada 95% x (1.200,00 + 0,8 x 604,25) = R$ 1.599,23 contra R$ 1.550,47: acréscimo de R$ 48,76. Diferença em 12/2003 em relação à renda paga (R$ 1.349,43): R$ 249,80.

**5.5.** Ajuizamento em 15/03/2008, marco 15/03/2003, critério da competência: prescritas as parcelas até 02/2003 (R$ 8.163,76 nominais); devidas de 03/2003 a 06/2010 ao titular (96 parcelas, R$ 27.488,97) e de 07/2010 a 09/2023 à pensão (173 parcelas, R$ 93.110,28), abono anual incluído. Total devido nominal R$ 120.599,25 em 269 parcelas (`parcelas.json`).

**5.6.** Óbito do segurado em 15/06/2010: o mês do óbito fica com o titular; pensão de 07/2010 com coeficiente de 100% (Lei 8.213/1991, art. 75, redação da Lei 9.528/1997 `[A VERIFICAR regime vigente no óbito]`) sobre a renda revisada, menos a pensão paga (HISCRE). Óbito da pensionista em 20/09/2023: cota cessada em 09/2023 (Decreto 3.048/1999, art. 114, I). Parcelas do titular até 06/2010 e da pensão até 09/2023 destinam-se, na forma do art. 112 da Lei 8.213/1991, à pensionista habilitada e, por seu falecimento, aos sucessores dela habilitados em [fls.] `[A VERIFICAR alcance do art. 112 à pensionista]`.

**5.7.** Primeira prestação em 03/1987; termo inicial da decadência atribuído a 01/08/1997 e final a 01/08/2007 `[A VERIFICAR: STF, Tema 313]`; ajuizamento posterior; a readequação aos tetos não revisa o ato de concessão (TRF1, Corte Especial, AC 1018697-75.2023.4.01.3300); a incidência é do juízo.

> Quesito 4 do juízo: "Aplicados os limitadores da época com os tetos das EC 20/1998 e 41/2003, qual a renda devida e qual a diferença em relação à renda paga?"
> Resposta: A renda devida em 12/1998 é de R$ 986,13 e em 12/2003 de R$ 1.599,23 (Anexo III), contra R$ 858,27 e R$ 1.349,43 pagos, diferenças de R$ 127,86 e R$ 249,80. A diferença mensal evolui pelos mesmos índices e alcança R$ 791,80 em 12/2024 (Anexo II). As parcelas devidas após a prescrição somam R$ 120.599,25 nominais (Anexo IV), a atualizar pela `atualizacao-monetaria`.

Pendências de verificação do exemplo: art. 23 do Decreto 89.312/1984 (fração do excedente); regime da pensão em 2010; alcance do art. 112 à pensionista; STF, Tema 313; tabelas oficiais em substituição aos dados fictícios.
