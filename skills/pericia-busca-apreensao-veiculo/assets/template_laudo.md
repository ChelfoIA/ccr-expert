# Template de laudo pericial contábil: busca e apreensão de veículo e revisional conexa

Uso: preencher os campos entre colchetes; excluir as seções inaplicáveis. Nenhum número entra sem memória de cálculo gerada pelos scripts. Toda citação segue o protocolo antifabricação de `references/fundamentacao-legal.md`, seção 8. Para atuação como assistente técnico, trocar o título por "Parecer técnico contábil", declarar a parte assistida no cabeçalho e manter a mesma memória de cálculo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_BuscaApreensao_[NomeAbreviado]_v1.md` (por exemplo, `2026-09-12_Laudo_BuscaApreensao_v1.md`).

---

## LAUDO PERICIAL CONTÁBIL

**Processo nº** [número]
**Vara** [juízo]
**Ação** Busca e apreensão (DL 911/1969) [e revisional conexa nº ...]
**Autor** [instituição financeira]
**Réu** [devedor fiduciante]
**Perito** [nome], contador, CRC [registro]
**Data-base do laudo** [dd/mm/aaaa]
**Data da liminar** [dd/mm/aaaa]

---

## 1. OBJETO

A perícia tem por objeto a análise do contrato de financiamento de veículo com alienação fiduciária nº [número], celebrado em [data], a descrição dos fatos relativos à constituição em mora, o confronto dos juros remuneratórios com a taxa média de mercado divulgada pelo Banco Central para a modalidade no mês da contratação, a aferição da capitalização e das tarifas e seguros embutidos, a reconstrução da evolução da dívida em cenário contratual e em cenário revisado, e a apuração do valor exigível para a purga da mora na data da liminar.

Não integram o objeto: a validade jurídica da constituição em mora, a nulidade de cláusulas e a procedência dos pedidos, matérias reservadas ao juízo (CPC, art. 473, § 2º).

---

## 2. QUESITOS

| Origem | Nº | Quesito | Seção da resposta |
|---|---|---|---|
| Juízo | 1 | [transcrever] | [7.1] |
| Autor (credor) | 1 | [transcrever] | [7.2] |
| Réu (devedor) | 1 | [transcrever] | [7.3] |

---

## 3. DOCUMENTOS EXAMINADOS

| Nº | Documento | Fls. | Origem | Observação |
|---|---|---|---|---|
| 1 | Contrato ou CCB nº [número], de [data] | | Credor | [taxa mensal, taxa anual, CET, n de parcelas, tarifas] |
| 2 | Planilha de evolução da dívida apresentada na inicial | | Credor | [reproduzível ou não; ver 5.8] |
| 3 | Notificação extrajudicial e aviso de recebimento | | Credor | [data do envio, endereço, resultado do AR] |
| 4 | Comprovantes de pagamento | | Devedor | [parcelas e datas] |
| 5 | Decisão liminar | | Autos | [data] |
| 6 | Consulta ao SGS do BACEN (série, código, competência) | | Perito | [anexo com a tela ou o CSV] |

---

## 4. METODOLOGIA

1. Extração dos dados do contrato para o arquivo estruturado (`exemplo_contrato.json` como modelo), com transcrição literal das cláusulas de taxa, capitalização, encargos moratórios, tarifas e seguros.
2. Descrição factual da notificação extrajudicial: data, endereço de destino comparado ao do contrato, resultado do aviso de recebimento, parcela mais antiga em aberto naquela data.
3. Confronto da taxa contratada com a taxa média do BACEN da modalidade no mês da contratação (`scripts/abusividade_juros.py`), com conversão a juros compostos e razão contratada/média. Limiar adotado como premissa: [1,5] vez a média.
4. Teste dos sinais de capitalização: taxa anual informada contra o duodécuplo da mensal e contra a composta; periodicidade diária e taxa diária informada.
5. Classificação das tarifas e seguros: incluídos ou não no financiado; contestados ou não; prova do serviço ou da adesão nos autos.
6. Reconstrução da evolução em dois cenários (`scripts/evolucao_cdc_veiculo.py`): A, contratual; B, revisado (taxa média se a contratada superou o limiar; tarifas contestadas fora do principal). [Cenário C, sem capitalização, se determinado.]
7. Apuração do valor de purga na data da liminar (`scripts/purga_mora.py`): vencidas com juros de mora de [1,00% a.m.] pro rata die e multa de [2%], mais vincendas [pelo valor nominal / a valor presente].
8. Toda operação executada em código, com memória reproduzível em anexo. Valores nominais; atualização monetária a cargo da liquidação.

**Cenários apurados**

| Cenário | Taxa | Principal | Sistema |
|---|---|---|---|
| A (contratual) | [2,90% a.m.] | [R$ 38.500,00] | Price |
| B (revisado) | [1,60% a.m., média BACEN] | [R$ 37.750,00, sem tarifas contestadas] | Price |
| C (sem capitalização, se houver) | [1,60% a.m.] | [R$ 37.750,00] | MEJS |

---

## 5. ANÁLISE

### 5.1. Dados do contrato

| Item | Valor | Cláusula |
|---|---|---|
| Valor do bem | R$ | |
| Entrada | R$ | |
| Valor financiado | R$ | |
| Taxa mensal | % | |
| Taxa anual informada | % | |
| Taxa anual composta equivalente | % | apurada |
| CET informado | % a.a. | |
| Número e periodicidade das parcelas | | |
| Primeira parcela | dd/mm/aaaa | |
| Encargos moratórios previstos | | |
| Tarifas, seguros e IOF | ver 5.5 | |

### 5.2. Constituição em mora: descrição factual

| Fato | Registro |
|---|---|
| Data do envio da notificação | |
| Endereço de destino | [idêntico ao do contrato / diverso] |
| Resultado do AR | [recebido / não procurado / mudou-se / outro] |
| Parcela mais antiga em aberto na data do envio | |
| Parcelas vencidas e não pagas na data da liminar | |

O perito registra os fatos. A suficiência da notificação para a constituição em mora é matéria do Tema 1.132 do STJ e cabe ao juízo.

### 5.3. Juros remuneratórios e taxa média

| Item | Contratada | Média BACEN | Razão | Spread |
|---|---|---|---|---|
| Mensal | % | % | | p.p. |
| Anual | % | % | | p.p. |

Fonte da média: [série, código validado em dd/mm/aaaa, competência mm/aaaa, consulta em dd/mm/aaaa]. Veredito técnico com o limiar de [1,5]: [acima do limiar / acima da média, dentro do limiar / igual ou abaixo da média].

### 5.4. Capitalização

| Teste | Resultado |
|---|---|
| Taxa anual informada x duodécuplo da mensal | |
| Taxa anual informada x composta equivalente | |
| Periodicidade prevista e taxa diária informada | |

### 5.5. Tarifas, seguros e IOF

| Item | Valor | No financiado | Contestado | Prova nos autos | Tratamento no cenário B |
|---|---|---|---|---|---|
| Tarifa de cadastro | R$ | sim | | | |
| Registro de contrato | R$ | sim | | | |
| Avaliação do bem | R$ | sim | | | |
| Seguro prestamista | R$ | sim | | | |
| IOF | R$ | sim | não | tributo | mantido |

### 5.6. Evolução da dívida: quadro resumo

| Item | Cenário A | Cenário B | Diferença |
|---|---|---|---|
| Principal | R$ | R$ | R$ |
| Parcela | R$ | R$ | R$ |
| Soma das parcelas | R$ | R$ | R$ |
| Juros totais | R$ | R$ | R$ |
| Sanidade (soma das amortizações = principal; saldo final zero) | OK | OK | |

Tabela parcela a parcela no Anexo I.

### 5.7. Pagamentos e excesso

| Item | Valor |
|---|---|
| Parcelas pagas | [n], de [data] a [data] |
| Total pago | R$ |
| Devido no cenário B pelas mesmas parcelas | R$ |
| Excesso nominal | R$ |
| Tarifas contestadas pagas à vista | R$ |

Excesso em valor nominal na data de cada pagamento; atualização e juros conforme critério a ser fixado pelo juízo (skill `atualizacao-monetaria`).

### 5.8. Purga da mora na data da liminar

| Item | Cenário A | Cenário B |
|---|---|---|
| Parcelas vencidas em aberto | | |
| Residual das vencidas | R$ | R$ |
| Juros de mora ([1,00% a.m.] pro rata die) | R$ | R$ |
| Multa ([2%]) | R$ | R$ |
| Subtotal vencidas | R$ | R$ |
| Vincendas ([nominal / valor presente]) | R$ | R$ |
| Valor para purga (integralidade, Tema 722) | R$ | R$ |

Planilha do credor na inicial: [reproduzível a partir das cláusulas / diverge em: ...].

### 5.9. Encargo abusivo no período de normalidade

Resposta técnica: [sim / não]. Motivos: [juros acima do limiar declarado; tarifas contestadas no principal; capitalização diária sem taxa diária informada]. Consequência, a critério do juízo: reconhecida a abusividade do encargo no período de normalidade, a mora se descaracteriza (REsp 1.061.530; REsp 2.239.793; REsp 2.134.805) e o valor da purga passa a ser informativo.

---

## 6. CONCLUSÃO

[Redigir por cenário, sem juízo sobre a procedência.]

No cenário contratual, o valor exigível para purga da mora em [data da liminar] é de R$ [valor], sendo R$ [valor] de parcelas vencidas com encargos e R$ [valor] de vincendas. No cenário revisado, com a taxa média de [x]% a.m. e a exclusão das tarifas de [nomes], o valor é de R$ [valor], com diferença de R$ [valor]. No período anterior ao inadimplemento, o cenário revisado [aponta / não aponta] encargos que a revisão afasta, no total nominal de R$ [valor] pagos a maior em [n] parcelas.

Limitações declaradas:

1. [Taxa média obtida em consulta de dd/mm/aaaa; código da série validado.]
2. [Comprovação do serviço de registro e avaliação não localizada nos autos.]
3. [Itens marcados `[A VERIFICAR]` na fundamentação.]

---

## 7. RESPOSTA AOS QUESITOS

### 7.1. Quesitos do juízo

**Quesito 1.** [transcrever]
**Resposta.** [objetiva, com remissão à seção e à tabela]

### 7.2. Quesitos do autor (credor)

### 7.3. Quesitos do réu (devedor)

---

## 8. ENCERRAMENTO

Nada mais havendo a informar, o perito encerra o presente laudo, composto de [n] laudas e [n] anexos, e o submete à apreciação do juízo.

[Cidade], [dd/mm/aaaa].

[Nome do perito]
Contador, CRC [registro]
Perito nomeado

---

## ANEXOS

| Anexo | Conteúdo |
|---|---|
| I | Tabelas de evolução, cenários A e B (e C), parcela a parcela (CSV e Markdown dos scripts) |
| II | Memória de cálculo da purga da mora |
| III | Teste de abusividade dos juros, com conversões e memória |
| IV | Consulta ao SGS do BACEN (tela ou CSV), com código, competência e data |
| V | Transcrição das cláusulas de taxa, capitalização, encargos e tarifas |

---

## EXEMPLO PREENCHIDO (dados fictícios dos assets)

Processo 0000000-00.0000.0.00.0000. Banco Alfa S.A. x Maria da Silva. CCB nº 000000, de 15/03/2024, valor financiado R$ 38.500,00, 36 parcelas de R$ 1.737,23, taxa de 2,90% a.m. (40,92% a.a. informada; composta equivalente 40,92% a.a.). Taxa média fictícia da modalidade em 03/2024: 1,60% a.m. (20,98% a.a.). Razão 1,8125, acima do limiar de 1,5 adotado como premissa. Taxa anual informada superior ao duodécuplo (34,80%), sinal de pactuação de capitalização mensal. Tarifas de registro (R$ 350,00) e de avaliação (R$ 400,00) sem prova do serviço, excluídas do principal no cenário B; cadastro e seguro prestamista mantidos.

Notificação enviada em 20/07/2025 ao endereço do contrato; AR devolvido com a anotação "não procurado"; parcela 15 (15/06/2025) era a mais antiga em aberto. Liminar em 10/09/2025, com as parcelas 15, 16 e 17 vencidas e não pagas.

| Item | Cenário A | Cenário B |
|---|---|---|
| Parcela | R$ 1.737,23 | R$ 1.387,58 |
| Pago em 14 parcelas | R$ 24.321,22 | devido R$ 19.426,19 |
| Excesso nominal | | R$ 4.895,03 |
| Vencidas com encargos (3) | R$ 5.414,37 | R$ 4.324,62 |
| Vincendas nominais (19) | R$ 33.007,37 | R$ 26.364,02 |
| Purga em 10/09/2025 | R$ 38.421,74 | R$ 30.688,64 |

Resposta ao quesito 2 do juízo: no período de normalidade (parcelas 1 a 14), o cenário revisado aponta encargos que a revisão afasta: juros de 2,90% a.m. contra média de 1,60% a.m. e tarifas de registro e avaliação sem prova do serviço, com excesso nominal de R$ 4.895,03. A consequência sobre a mora (REsp 1.061.530; REsp 2.239.793) é matéria do juízo.

---

## PENDÊNCIAS DE VERIFICAÇÃO

Listar aqui todo item `[A VERIFICAR]` que restou no laudo, com o que conferir e onde, na forma da seção 9 de `references/fundamentacao-legal.md`:

1. [Súmula 541/STJ: texto literal, antes de citar o sinal do duodécuplo.]
2. [Tema 958/STJ: tese sobre tarifas de registro e avaliação.]
3. [Código da série do SGS usado para a taxa média.]
