# Template de laudo pericial contábil: auditoria da administração do espólio

Uso: preencher os campos entre colchetes; excluir as seções inaplicáveis (por exemplo, a seção 7.2 quando não houver bem no exterior, ou a seção 8 quando não houver sociedade). Nenhum número entra sem a memória gerada pelos scripts (`fluxo_caixa_espolio.py`, `rendimentos_imoveis.py`, `conversao_ptax.py`) ou sem o quadro de sociedades preenchido a partir de balanço e ata. Toda citação segue o protocolo antifabricação de `references/fundamentacao-legal.md`, seção 8. Para atuação como assistente técnico de herdeiro, trocar o título por "Parecer técnico contábil", declarar a parte assistida no cabeçalho e manter a mesma memória.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_AuditoriaEspolio_[NomeAbreviado]_v1.md`.

---

## Laudo pericial contábil

**Processo nº** [número]
**Juízo** [vara de sucessões e comarca]
**Feito** [inventário / prestação de contas em apenso / ação autônoma de exigir contas / arbitramento de aluguel]
**Espólio de** [nome do autor da herança], falecido em [dd/mm/aaaa]
**Inventariante** [nome e vínculo]
**Herdeiros** [nomes, frações e meação, se houver]
**Perito** [nome], contador, CRC [registro]
**Data-base do laudo** [dd/mm/aaaa]
**Período auditado** [dd/mm/aaaa, abertura da sucessão] a [dd/mm/aaaa, data de referência]

---

## 1. Objeto

A perícia tem por objeto, conforme [decisão de saneamento ou despacho de dd/mm/aaaa], a auditoria contábil da administração dos bens do espólio desde a abertura da sucessão, compreendendo: a reconstrução do fluxo de caixa por conta, mês e categoria; a identificação de saídas sem autorização judicial, sem documento, em favor de herdeiro ou inventariante e de despesas estranhas ao espólio; a apuração dos frutos de cada imóvel (contratado, recebido e de mercado), inclusive o aluguel devido por herdeiro que ocupa imóvel com exclusividade e os encargos desse imóvel; a conversão em reais das rendas e despesas dos bens situados em [Portugal]; o confronto, por sociedade, entre lucros distribuídos, pró-labore, mútuos e o que coube ao espólio; e a quantificação do que o espólio deixou de receber.

Não integram o objeto: a fixação do marco inicial do aluguel, da fração ideal de cada herdeiro, a colação, a partilha, a remoção do inventariante, a pena de sonegados e a qualificação jurídica das saídas, matérias do juízo (CPC, art. 473, § 2º); a avaliação das quotas e dos imóveis; a atualização monetária dos valores, a cargo da liquidação.

---

## 2. Quesitos

| Origem | Nº | Quesito | Seção da resposta |
|---|---|---|---|
| Juízo | 1 | [transcrever] | [11.1] |
| Herdeiro requerente | 1 | [transcrever] | [11.2] |
| Inventariante | 1 | [transcrever] | [11.3] |

---

## 3. Metodologia e premissas

1. Perímetro: abertura da sucessão em [dd/mm/aaaa] (certidão de óbito, fl. [x]); data de referência [dd/mm/aaaa]; contas [listar, com indicação das de uso misto]; bens [remissão ao quadro da seção 4].
2. Fluxo de caixa (`scripts/fluxo_caixa_espolio.py`): saldo inicial de R$ [valor] na data do óbito (extratos de fls. [x]); conciliação com o saldo final dos extratos; categorias e critérios de autorização e documento conforme o JSON anexo.
3. Imóveis (`scripts/rendimentos_imoveis.py`): mês parcial pro rata die (CC, art. 1.215); aluguel de mercado por [laudo / anúncios / índice], com fonte por imóvel; fração do ocupante [x], pelo [quinhão e meação]; marco inicial calculado em cada data documentada: [abertura da sucessão, oposição, notificação, citação].
4. Bens no exterior (`scripts/conversao_ptax.py`): cotação PTAX [venda] da data de cada movimento, série [código do SGS, consulta em dd/mm/aaaa] [A VERIFICAR o código]; sem cotação no dia, a do dia útil anterior, com defasagem declarada.
5. Sociedades: quadro por sociedade a partir de [balanços, DRE, atas, razão de sócios, DIRPF], com participação do espólio pelo contrato social e distribuição pro rata (CC, art. 1.007), salvo cláusula.
6. Conta de uso misto: critério de segregação [atribuição direta por documento; resíduo por proporção dos ingressos; cenário não segregável], premissa declarada.
7. Valores nominais nas datas dos movimentos; dupla contagem evitada conforme o quadro da seção 9; toda operação executada em código com memória reproduzível em anexo.

---

## 4. Documentos examinados, documentos não fornecidos e perímetro

### 4.1. Examinados

| Nº | Documento | Fls. ou origem | Período | Observação |
|---|---|---|---|---|
| 1 | Certidão de óbito | | | |
| 2 | Primeiras e últimas declarações | | | |
| 3 | Termo de inventariante; alvarás e decisões de autorização | | | |
| 4 | Extratos das contas do espólio | | [mm/aaaa a mm/aaaa] | [saldo na data do óbito] |
| 5 | Extratos da conta de uso misto do inventariante | | | |
| 6 | Matrículas, contratos de locação, recibos | | | |
| 7 | Documentos do imóvel em Portugal (certidão do registo predial, caderneta, recibos de renda, IMI, IRS, extratos) | | | |
| 8 | Contrato social, balanços, DRE, atas, razão de sócios | | | |
| 9 | Série PTAX [código] obtida em [data] | anexo | | |

### 4.2. Requeridos e não fornecidos

| ID | Documento | Responsável | Pedido em | Prazo | Reiterações | Situação | Efeito sobre o laudo |
|---|---|---|---|---|---|---|---|
| [D01] | | | | | | pendente | [seção afetada e o que mudaria] |

A consequência probatória da não exibição (CPC, art. 400) é matéria do juízo.

### 4.3. Perímetro de bens e contas

| Id | Bem ou conta | Situação | Fração do espólio | Observação |
|---|---|---|---|---|
| IM01 | | locado / ocupado por herdeiro / vago / uso do espólio | | |
| E01 | | continuidade com o espólio / liquidação da quota | | |

---

## 5. Fluxo de caixa do espólio

Período [dd/mm/aaaa] a [dd/mm/aaaa]; saldo inicial R$ [valor]; entradas R$ [valor]; saídas R$ [valor]; saldo final reconstruído R$ [valor], conciliado com o extrato ([fechou / divergência de R$ valor, tratada na seção 6]). Quadro mensal, totais por categoria, por conta e por vínculo do beneficiário no Anexo I.

| Mês | Saldo inicial | Entradas | Saídas | Variação | Saldo final |
|---|---:|---:|---:|---:|---:|
| | R$ | R$ | R$ | R$ | R$ |

Sanidade: entradas menos saídas igual à variação do saldo; soma das variações mensais igual à variação total; transferências internas [fecham / não fecham, indicando conta fora do perímetro].

---

## 6. Exceções e desvio de finalidade

| Lista | Itens | Valor nominal | Norma | Tratamento |
|---|---|---:|---|---|
| Saídas sem autorização, fora da conservação | | R$ | CPC, art. 619 | |
| Despesas de conservação sem alvará prévio | | R$ | CPC, art. 619, IV | ratificação na prestação de contas |
| Alienação ou pagamento de dívida sem alvará | | R$ | CPC, art. 619, I e III | |
| Saídas sem documento | | R$ | CPC, art. 618, VII; art. 553 | não comprovadas nos autos |
| Saídas em favor de herdeiro ou inventariante | | R$ | CC, art. 2.020 | adiantamento, reembolso ou recomposição, conforme prova |
| Despesas estranhas ao espólio | | R$ | CC, art. 2.020 | recomposição |
| Encargos de imóvel ocupado pagos pelo espólio | | R$ | REsp 1.704.528 | quadro de imóveis (seção 7), não aqui |

Achados, cada um em fato, evidência, norma e efeito (`references/roteiro-auditoria-e-documentos.md`, seção 8):

**Achado 1.** [...]

---

## 7. Frutos dos imóveis

### 7.1. Imóveis no Brasil

| Imóvel | Situação | Base mensal | Meses | Esperado | Recebido | Diferença | Natureza |
|---|---|---:|---:|---:|---:|---:|---|
| IM01 | locado | R$ | | R$ | R$ | R$ | aluguel contratual não recebido |
| IM02 | ocupado por herdeiro | R$ [mercado x (1 - fração)] | | R$ | R$ 0,00 | R$ | devido aos demais coerdeiros |
| IM04 | vago | R$ | | R$ | R$ 0,00 | R$ | renda potencial, informativa |

Imóvel ocupado: ocupante [nome], fração [x]; aluguel de mercado R$ [valor] ([fonte, fl.]); marcos calculados: [abertura da sucessão: R$ valor; notificação de dd/mm/aaaa: R$ valor; citação: R$ valor]; encargos pagos pelo espólio R$ [valor] (IPTU e condomínio posteriores à abertura da sucessão, REsp 1.704.528), computados uma única vez (REsp 1.918.125). Meses sem lastro documental: [listar].

### 7.2. Bens em Portugal

Jurisdição: o inventário e a partilha de bens situados no Brasil são de competência exclusiva da autoridade brasileira (CPC, art. 23, II); o bem em Portugal segue a jurisdição local, o que não altera a apuração dos frutos, que pertencem ao espólio desde o óbito (CC, arts. 1.784 e 2.020).

| Movimento | Data | Valor em euro | Cotação (data, critério) | Valor em reais | Documento |
|---|---|---:|---|---:|---|
| Renda [mês] | | EUR | | R$ | recibo fl. |
| IMI | | EUR | | R$ | nota de cobrança fl. |
| IRS | | EUR | | R$ | nota de liquidação fl. |

Série PTAX: [código do SGS, consulta em dd/mm/aaaa] [A VERIFICAR o código]. Total em euro: esperado EUR [valor]; recebido EUR [valor]; diferença EUR [valor], equivalente a R$ [valor] pela cotação de cada mês. Tributos portugueses conferidos contra as notas, sem recálculo [A VERIFICAR regras de IMI e IRS de não residente].

---

## 8. Sociedades de capital fechado

| Sociedade | Participação | Continuidade | Lucro distribuído total | Devido ao espólio | Recebido | Diferença | Pró-labore x referência | Mútuos e despesas pessoais |
|---|---:|---|---:|---:|---:|---:|---|---:|
| E01 | | S | R$ | R$ | R$ | R$ | R$ x R$ | R$ |
| E03 | | N | | | | | | haveres: skill própria |

Lucro suprimido por retirada (pró-labore acima da referência, mútuo sem contrato, despesa pessoal), parcela do espólio: R$ [valor], em linha separada. Valor das quotas: fora do objeto (`apuracao-haveres`, `valuation-capital-fechado`).

---

## 9. Quantificação consolidada

| Parcela | Origem | Valor nominal | Entra uma única vez em |
|---|---|---:|---|
| Despesas estranhas e saídas a herdeiro ou inventariante sem decisão | fluxo, seção 6 | R$ | recomposição do caixa |
| Encargos do imóvel ocupado pagos pelo espólio | seção 7.1 | R$ | quadro de imóveis |
| Aluguel devido pelo herdeiro ocupante (marco [x]) | seção 7.1 | R$ | quadro de imóveis |
| Aluguel contratual não recebido | seção 7.1 | R$ | quadro de imóveis |
| Rendas e despesas em Portugal, em reais | seção 7.2 | R$ | quadro de imóveis |
| Lucros devidos e não recebidos | seção 8 | R$ | quadro de sociedades |
| Lucro suprimido por retirada | seção 8 | R$ | linha separada |
| Renda potencial de imóvel vago | seção 7.1 | R$ | informativa, fora do total |
| Total do que o espólio deixou de receber ou pagou indevidamente | | R$ | |

Valores nominais nas datas dos movimentos. Atualização e juros conforme o critério que o juízo fixar (skill `atualizacao-monetaria`). Marco, fração, compensação na partilha e qualificação das saídas são matéria do juízo.

---

## 10. Conclusão e limitações

[Redigir por eixo: caixa, imóveis, exterior, sociedades, sem juízo sobre responsabilidade.]

No período de [dd/mm/aaaa] a [dd/mm/aaaa], o espólio recebeu R$ [valor] e pagou R$ [valor]; das saídas, R$ [valor] não têm documento nos autos, R$ [valor] foram em favor de herdeiro ou do inventariante sem decisão localizada e R$ [valor] são estranhas ao espólio. O imóvel [IM02], ocupado por [nome] desde [data], gera aluguel devido aos demais coerdeiros de R$ [valor] a partir de [marco], ou R$ [valor] se o juízo adotar a abertura da sucessão; o espólio pagou R$ [valor] de encargos desse imóvel. O imóvel de [Lisboa] rendeu EUR [valor], dos quais EUR [valor] não ingressaram em conta do espólio. A sociedade [E01] distribuiu R$ [valor], dos quais caberiam ao espólio R$ [valor], tendo ingressado R$ [valor].

Limitações declaradas:

1. [Extratos da conta x: período não coberto.]
2. [Imóvel y sem fonte de mercado; esperado não calculado.]
3. [Sociedade z sem balanço de aaaa; lucro não apurado.]
4. [Série PTAX: código a confirmar; critério venda por premissa.]
5. [Itens marcados `[A VERIFICAR]` na fundamentação.]

---

## 11. Resposta aos quesitos

### 11.1. Quesitos do juízo

**Quesito 1.** [transcrever]
**Resposta.** [objetiva, com remissão à seção e ao anexo]

### 11.2. Quesitos do herdeiro requerente

### 11.3. Quesitos do inventariante ou do ocupante

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
| I | Fluxo de caixa mensal, totais, listas de exceção e memória (JSON, Markdown e CSV de `fluxo_caixa_espolio.py`) |
| II | Quadro por imóvel e tabela mensal do aluguel devido pelo ocupante (`rendimentos_imoveis.py`) |
| III | Conversão PTAX linha a linha e série utilizada com fonte (`conversao_ptax.py`) |
| IV | Quadro por sociedade com os documentos de origem (layout de `assets/exemplo_sociedades.csv`) |
| V | CSV dos movimentos transcritos dos extratos; cronologia dos pedidos de documentos |

---

## Exemplo preenchido (dados fictícios dos assets)

Processo 0000000-00.0000.0.00.0000, Vara de Sucessões da Comarca de Exemplo. Espólio de José Alfa, falecido em 10/01/2024. Inventariante Maria Alfa, viúva meeira; herdeiros Pedro Alfa, Paula Alfa e dois outros filhos, em partes iguais. Perito João da Silva, CRC 000000/O-0. Período auditado 10/01/2024 a 30/06/2026.

Fluxo de caixa: saldo inicial R$ 12.500,00; entradas R$ 151.730,55; saídas R$ 125.800,00; saldo final R$ 38.430,55, conciliado com os extratos. Exceções: saídas sem autorização fora da conservação R$ 21.800,00 (5 itens); conservação sem alvará prévio R$ 24.800,00 (18 itens, ratificáveis); pagamento de dívida sem alvará R$ 4.000,00; saídas sem documento R$ 17.900,00 (4 itens); saídas a herdeiro ou inventariante R$ 13.000,00 (PIX de R$ 8.000,00 a Paula Alfa em 20/12/2024 e de R$ 5.000,00 a Maria Alfa em 10/06/2025, sem decisão nem recibo); despesas estranhas ao espólio R$ 4.800,00 (pacote de viagem e compras de cartão); encargos do imóvel ocupado pagos pelo espólio R$ 11.400,00. Recomposição do caixa, sem os encargos já no quadro de imóveis: R$ 17.800,00.

Imóveis: IM01 (apartamento locado por R$ 3.000,00) esperado R$ 89.129,03 em 29,7097 meses, recebido R$ 81.000,00, diferença R$ 8.129,03 (competência 01/2024 pro rata e meses 05/2025 e 11/2025 sem ingresso). IM02 (casa ocupada por Pedro Alfa, fração 1/4, mercado R$ 4.000,00 pelo laudo de fl. 210): devido aos demais R$ 4.000,00 x 0,75 x 24 meses = R$ 72.000,00 desde a notificação de 01/07/2024; R$ 89.129,03 se o juízo adotar a abertura da sucessão; encargos pagos pelo espólio R$ 11.400,00. IM04 (sala vaga desde 01/01/2025): renda potencial R$ 27.000,00, informativa. IM03 (Lisboa, renda EUR 1.200,00): esperado EUR 35.651,61, recebido EUR 33.600,00, diferença EUR 2.051,61; conversão dos movimentos pela PTAX venda de cada data (série fictícia dos assets, a substituir), por exemplo renda de 05/02/2024 EUR 1.200,00 x 5,3717 = R$ 6.446,04; IMI de 15/05/2024 EUR 310,00 x 5,5617 = R$ 1.724,13.

Sociedades: Alfa Comércio Ltda. (60%, continuidade com o espólio): distribuído R$ 100.000,00, devido pro rata R$ 60.000,00, recebido R$ 25.000,00, diferença R$ 35.000,00; pró-labore do herdeiro-administrador R$ 180.000,00 contra referência de R$ 96.000,00, lucro suprimido na parcela do espólio R$ 50.400,00; mútuos e despesas pessoais R$ 52.000,00, parcela do espólio R$ 31.200,00, linhas separadas.

Resposta ao quesito 4 do juízo: o valor mensal devido por Pedro Alfa aos demais coerdeiros pelo uso exclusivo do imóvel IM02 é de R$ 3.000,00 (aluguel de mercado de R$ 4.000,00, laudo de fl. 210, multiplicado pela fração dos demais, 3/4). Desde a notificação de 01/07/2024 até 30/06/2026 o total é de R$ 72.000,00; desde a abertura da sucessão, R$ 89.129,03 (Anexo II). O espólio pagou R$ 11.400,00 de condomínio e IPTU desse imóvel após o óbito, a cargo do ocupante, computados uma única vez no quadro de imóveis. Valores nominais; a escolha do marco é do juízo.

---

## Pendências de verificação

Listar aqui todo item `[A VERIFICAR]` que restou no laudo, com o que conferir e onde, na forma da seção 9 de `references/fundamentacao-legal.md`:

1. [Código da série PTAX euro no SGS do BCB e data da consulta.]
2. [Regras portuguesas de IMI e IRS de não residente aplicáveis ao imóvel.]
3. [Prazo prescricional da pretensão de aluguéis entre coerdeiros, conforme o inteiro teor do AgInt no REsp 2.240.323.]
