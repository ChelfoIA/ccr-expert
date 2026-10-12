# Laudo e quesitos: estrutura, linguagem neutra, cenários sem tese e banco de respostas

Referência: 12/09/2026. Este arquivo apoia as etapas 6 a 9 do workflow: redação do laudo pelo `assets/template_laudo_pasep.md`, apresentação dos cenários, resposta aos quesitos das três origens e esclarecimentos. A jurisprudência citada é a da lista verificada em `references/fundamentacao-legal.md`, seção 6.

## Sumário

1. Estrutura do laudo (CPC art. 473 e NBC TP 01)
2. Linguagem neutra: o que o laudo diz e o que não diz
3. Quadro de cenários sem escolher tese
4. Banco de respostas neutras a quesitos recorrentes
5. Esclarecimentos (CPC art. 477, § 2º)
6. Parecer do assistente técnico: como tratar ponto a ponto
7. Audiência e segunda perícia

---

## 1. Estrutura do laudo (CPC art. 473 e NBC TP 01)

| Seção | Conteúdo mínimo | Fonte do conteúdo |
|---|---|---|
| 1 Identificação e encargo | Processo, juízo, partes e procuradores, assistentes indicados, perito e registro, data da nomeação, prazo, encargo do art. 466 | `lote.json` |
| 2 Objeto e quesitos recebidos | Objeto transcrito do saneamento; o que não integra o objeto (art. 473, § 2º); quadro dos quesitos por proponente com a seção da resposta | saneamento; `matriz.md` |
| 3 Documentos e diligências | Documentos examinados com folhas; período coberto pelo extrato; lacunas; diligências com data, destinatário, resposta ou ausência | `checklist.json`; autos |
| 4 Metodologia e fontes | Reconstrução mês a mês na ordem oficial de valorização; classificação das saídas; conciliação; cenários; séries SGS e tabela do Tesouro com data de consulta; tratamento de lacuna; precisão e arredondamento | `pericia-pasep` |
| 5 Análise | 5.1 datas e marcos de fato; 5.2 reconstrução do saldo; 5.3 saídas, modalidade e comprovação; 5.4 índices, rendimentos e conciliação | `conciliacao.json` |
| 6 Cenários | Quadro A a D aplicável ao polo demandado, com e sem corte, rotulado por tese; impacto percentual entre cenários; ressalvas | `cenarios.json` |
| 7 Resposta aos quesitos | Todos, na ordem juízo, autor, réus; remissão à seção e ao documento | `matriz.md` |
| 8 Conclusão | Fatos apurados; valores por cenário; limitações; o que depende de decisão do juízo | seções 5 e 6 |
| 9 Encerramento e anexos | Termo de encerramento; anexos (memória do motor, consultas SGS, tabela Tesouro, matriz de quesitos, ofícios e respostas); pendências de verificação; o que mudou nesta versão | pastas `02_calculo` e `03_quesitos` |

Tamanho de referência: o corpo (seções 1 a 8) cabe em quinze a vinte e cinco páginas; o que passa disso vai para anexo. Juiz lê a conclusão e as respostas; o assistente lê os anexos.

---

## 2. Linguagem neutra: o que o laudo diz e o que não diz

| O laudo diz | O laudo não diz |
|---|---|
| "O extrato registra saída de R$ 1.250,00 em 14/08/1998 com código de saque em caixa." | "O autor sacou o valor." ou "O banco desviou o valor." |
| "O Banco do Brasil não apresentou recibo, identificação do recebedor ou registro biométrico dessa saída, apesar do ofício de fl. 140." | "O banco não se desincumbiu do ônus." |
| "A autora não juntou contracheques de junho e julho de 2011, apesar da solicitação de fl. 141." | "A autora não provou o desfalque." |
| "A ciência do desfalque alegada pela autora data de 10/03/2021 (extrato de fl. 22)." | "A pretensão não está prescrita porque a ciência ocorreu em 2021." |
| "No cenário A, com corte decenal contado de 10/03/2021, o valor é R$ X; sem corte, R$ Y." | "Aplica-se o cenário A." |
| "A diferença de 1991 decorre de percentual creditado inferior ao oficial (origem: índice)." | "A União é responsável pela diferença de 1991." |
| "A relação cotista e BB é tratada de modo diverso pelos tribunais; o laudo não aplica inversão de ônus." | "Aplica-se o CDC." ou "Não se aplica o CDC." |

Verbos do laudo: verifica-se, apura-se, consta, registra, não consta, não foi apresentado, pressupõe, corresponde a. Verbos vedados no corpo: entende-se que é devido, conclui-se pela procedência, restou comprovado, não se desincumbiu, está prescrito, é parte ilegítima.

Marcadores de precisão: todo número com data, folhas e cenário; todo documento com folhas; toda lacuna com o período afetado e o efeito no cálculo. Datas em dd/mm/aaaa; valores em R$ 1.234,56; percentuais com vírgula.

---

## 3. Quadro de cenários sem escolher tese

Modelo da seção 6 (valores fictícios; cada processo só traz os cenários do polo demandado):

| Cenário | Tese pressuposta | Critério de atualização | Sem corte prescricional | Com o corte da tese | Fundamento rotulado |
|---|---|---|---|---|---|
| A | Diferença imputável ao BB | Tesouro até 05/2020; IPCA-E; juros civis | R$ 48.310,22 | R$ 46.905,80 (decenal desde 10/03/2021) | Tema 1.150/STJ; CC arts. 205 e 406; Lei 14.905/2024 |
| B | BB, critério alternativo | SELIC | R$ 45.120,07 | R$ 43.880,15 | Tema 1.150/STJ; posição alternativa |
| C | Diferença imputável à União | EC 113/2021 e 136/2025; Súmula 85 | R$ 12.004,33 | R$ 3.910,48 (quinquenal anterior a 05/05/2018, parcelas preservadas) | Tema 545/STJ; Súmula 85/STJ; STF Tema 810 |
| D | União, critério alternativo | INPC e juros civis | R$ 11.520,90 | R$ 3.770,16 | Tema 545/STJ; Súmula 85/STJ |

Regras:

1. Cabeçalho do quadro com processo, id do lote, data-base, data de citação e data de ciência adotada, para o teste do cabeçalho (`references/conducao-do-lote.md`, seção 3).
2. Em litisconsórcio, um quadro por origem (saque; índice ou expurgo; omissão de rendimento) e um quadro-resumo com a soma por polo; o perito não funde as origens.
3. Linha de ressalvas abaixo do quadro: regime da EC 136/2025 na fase anterior ao precatório controvertido; lacuna do extrato (período) excluída; saídas sem comprovação incluídas ou excluídas conforme a coluna indicada.
4. Impacto entre cenários em percentual, sem adjetivo ("o cenário A supera o C em 302,4%").
5. Quando a ciência do desfalque não consta dos autos, acrescentar colunas de hipótese (ciência na data do extrato; ciência na data de cada saque) e declarar a lacuna.
6. Nenhuma linha "cenário recomendado". A recomendação é tese.

---

## 4. Banco de respostas neutras a quesitos recorrentes

Formato: abertura padrão e complemento a adaptar com datas, folhas e valores do processo.

### 4.1. Quesitos do Banco do Brasil

| Quesito recorrente | Tipo | Resposta neutra |
|---|---|---|
| A pretensão está prescrita? | Direito | Trata-se de questão de direito, cuja definição cabe ao juízo. Do ponto de vista contábil, a perícia registra as datas de fato (seção 5.1) e apresenta, na seção 6, cada cenário com e sem o corte que a tese pressupõe, sem adotar nenhum deles. |
| Em que data o autor tomou ciência dos saques? | Misto | A qualificação jurídica cabe ao juízo. Quanto ao fato, o autor aponta como ciência a emissão do extrato em dd/mm/aaaa (fl. N); não consta dos autos documento anterior em que as saídas apareçam. Ver seção 5.1. |
| Os saques foram realizados pelo próprio titular? | Fato | O extrato registra as saídas listadas no quadro 5.3 com os códigos indicados. Para as saídas em caixa, [consta / não consta] recibo assinado, identificação do recebedor ou registro biométrico (fls.). A perícia não tem elemento para afirmar quem recebeu os valores além do que consta desses documentos. |
| Os índices creditados são os oficiais? | Fato | Os percentuais creditados foram confrontados com a tabela de valorização do Tesouro Nacional (anexo II). [Conferem em todas as competências / divergem nas competências X, Y e Z, no valor de R$ ...]. Ver seção 5.4. |
| Cabe ao autor provar o crédito em conta e a folha? | Direito | Trata-se de questão de direito, cuja definição cabe ao juízo. Do ponto de vista contábil, a perícia classificou cada saída por modalidade (quadro 5.3) e informa se há nos autos o extrato de destino ou os contracheques correspondentes, sem valorar a quem a ausência aproveita. |
| O BB é parte legítima para a diferença de índices? | Direito | Trata-se de questão de direito, cuja definição cabe ao juízo. Do ponto de vista contábil, a perícia identifica a origem de cada diferença (índice, expurgo, saque ou omissão de rendimento) na seção 5.4 e segrega os valores por origem na seção 6, sem atribuir responsabilidade. |
| A conta foi encerrada em 31/05/2020 com saldo zero? | Fato | O extrato registra em 31/05/2020 saldo de R$ ... e lançamento de [migração / saque integral] em dd/mm/aaaa (fl. N). Ver seção 5.2. |

### 4.2. Quesitos da União

| Quesito recorrente | Tipo | Resposta neutra |
|---|---|---|
| Aplica-se a prescrição quinquenal do DL 20.910/1932? | Direito | Questão de direito, cabe ao juízo. Do ponto de vista contábil, o cenário C aplica o corte quinquenal com preservação das parcelas dos cinco anos anteriores à propositura, na forma da Súmula 85/STJ, e o cenário sem corte mostra o valor integral (seção 6). |
| Qual a data do último creditamento omitido? | Fato | A última competência em que o percentual creditado ficou abaixo do oficial é mm/aaaa (quadro 5.4, linha N; fl. do extrato). |
| Os percentuais fixados pelo Conselho Diretor foram aplicados? | Fato | Confronto na seção 5.4 e no anexo II, competência a competência, com a tabela do Tesouro consultada em dd/mm/aaaa. [Resultado.] |
| A SELIC foi cumulada com juros? | Fato | Não. No cenário C a SELIC incide no período de 12/2021 a 08/2025 sem juros adicionais, e a partir de 09/2025 aplica-se IPCA e 2% a.a. simples, com a SELIC como teto, conforme a memória do anexo III. |
| O regime da EC 136/2025 se aplica antes do precatório? | Direito | Questão de direito, cabe ao juízo; a aplicação à fase anterior à expedição do precatório é controvertida. Do ponto de vista contábil, o cenário C adota o regime na forma operacional vigente e o cenário D apresenta a alternativa pelo INPC (seção 6, ressalva 1). |

### 4.3. Quesitos do autor

| Quesito recorrente | Tipo | Resposta neutra |
|---|---|---|
| O BB é responsável e deve indenizar? | Direito | Questão de direito, cabe ao juízo. Do ponto de vista contábil, a perícia apurou as saídas sem comprovação apresentada pelo réu (quadro 5.3) e o valor correspondente em cada cenário (seção 6). |
| Qual o saldo que a conta teria sem os saques? | Fato | Reconstruído mês a mês pela valorização oficial sem as saídas impugnadas, o saldo em 31/05/2020 seria de R$ ... (quadro 5.2, coluna "sem saídas impugnadas"; anexo I). |
| Qual o valor atualizado com juros desde a citação? | Fato | Depende do cenário: A, R$ ...; B, R$ ...; [C e D se houver]. Cada cenário pressupõe uma tese sobre polo e prescrição, rotulada na seção 6. |
| Cabe inversão do ônus pelo CDC? | Direito | Questão de direito, cabe ao juízo. Do ponto de vista contábil, a perícia registra a modalidade de cada saída e os documentos existentes nos autos, sem aplicar inversão ou redistribuição. |
| Há direito a danos morais? | Fora do objeto | O quesito extrapola o objeto fixado na decisão de saneamento e os limites do art. 473, § 2º, do CPC; a perícia deixa de respondê-lo. |
| O extrato juntado pelo BB está completo? | Fato | O extrato cobre mm/aaaa a mm/aaaa; a conta foi aberta em aaaa (RAIS de fl. N). O período de aaaa a mm/aaaa não está coberto, apesar do ofício de fl. N, e foi excluído da reconstrução com a ressalva da seção 3. |

### 4.4. Quesitos do juízo

| Quesito recorrente | Resposta neutra |
|---|---|
| Qual a evolução do saldo? | Quadro 5.2 mês a mês, com saldo do extrato, saldo reconstruído e diferença por competência; anexo I com a memória do motor. |
| Classifique as saídas e a comprovação | Quadro 5.3: data, valor, código de histórico, modalidade, documento de comprovação ou "sem comprovação apresentada por [réu/autor]", folhas. |
| Quais as diferenças por origem? | Seção 5.4 e quadro-resumo da seção 6: saque, índice ou expurgo, omissão de rendimento, com o valor histórico e o atualizado em cada cenário. |
| Qual o valor em cada hipótese sobre prescrição? | Seção 6: coluna sem corte e coluna com o corte que cada tese pressupõe, com as datas de referência declaradas. |

---

## 5. Esclarecimentos (CPC art. 477, § 2º)

Prazo: quinze dias da intimação. Objeto: divergência ou dúvida de qualquer das partes, do juiz ou do Ministério Público (inciso I) e ponto divergente do parecer do assistente técnico (inciso II). O perito não refaz o laudo nem responde a provocação; responde ao ponto.

Estrutura do documento `AAAA-MM-DD_Esclarecimentos_PASEP_<id>_vN.md`:

1. Identificação e referência ao laudo (versão e data de protocolo).
2. Pontos suscitados, numerados, cada um com: quem suscitou (fl.), transcrição, resposta, decisão do perito (mantido, retificado, fora do objeto).
3. Quadro das retificações, se houver, com o valor anterior, o novo e o motivo, e remissão à nova versão do laudo (`v2`) e ao novo anexo de memória.
4. Encerramento.

Padrão de redação de cada ponto:

> Ponto 3 (parecer do assistente técnico do autor, fls. 210 a 212). O assistente sustenta que a saída de 22/09/2016 deve ser tratada como saque em caixa e incluída no valor devido pelo réu.
> Resposta: Mantido. O extrato registra para a saída código de histórico "47", não constante da legenda juntada pelo Banco do Brasil (fl. 135), e o ofício de fl. 140 solicitou a identificação da modalidade sem resposta. A perícia classificou a saída como não identificada (OUTROS) e apresentou, na seção 6, o valor com e sem a sua inclusão. Atribuir modalidade por inferência seria substituir a prova pela presunção, o que excede o exame técnico (CPC art. 473, § 2º). A qualificação da saída e a consequência da ausência de legenda cabem ao juízo.

Quando retificar: erro material (transcrição, soma, folha), documento juntado depois do laudo que altera fato apurado, ou índice com fonte comprovadamente diversa. Retificação gera `v2` do laudo com o bloco "O que mudou nesta versão" e nova memória; o esclarecimento aponta a versão.

Quando não retificar: divergência de critério jurídico (prescrição, polo, ônus, CDC), escolha de cenário, pedido de que o perito "conclua" por uma tese. Resposta: o ponto é questão de direito; o laudo já apresenta o valor em cada hipótese.

---

## 6. Parecer do assistente técnico: como tratar ponto a ponto

O parecer de assistente técnico sobre PASEP costuma seguir a estrutura da `pericia-pasep` (checklist de dezesseis itens e MIPD). O perito do juízo responde a cada achado, nesta ordem de triagem:

| Achado do assistente | Tratamento |
|---|---|
| Erro material (soma, data, folha) | Conferir; se procede, retificar e agradecer o apontamento em uma linha |
| Erro metodológico (ordem de valorização, índice, período) | Conferir contra a tabela do Tesouro e a série SGS; manter com a memória ou retificar com nova saída do motor |
| Erro jurisprudencial (tema não aplicado, polo trocado) | Explicar que o laudo não aplica tese: apresenta cenários; indicar onde o cenário da tese do assistente está no quadro 6 |
| Omissão (quesito, saída, modalidade) | Se houve omissão, responder agora e registrar; se não houve, apontar a seção e a folha |
| Premissa questionável (data de ciência, tratamento de lacuna) | Manter a premissa declarada e, se útil ao juízo, acrescentar coluna de hipótese alternativa |
| Falta de rastreabilidade | Apontar o anexo e a linha da memória; se faltar, juntar |
| Pedido de conclusão por tese | Devolver como questão de direito |

O perito não qualifica o parecer ("tendencioso", "equivocado"); descreve o achado e a resposta.

---

## 7. Audiência e segunda perícia

Audiência (CPC art. 477, §§ 3º e 4º): a parte requer a intimação do perito com quesitos formulados desde logo; intimação eletrônica com dez dias de antecedência. Preparar uma folha por quesito com a resposta, a seção do laudo e a folha dos autos; levar o laudo, os esclarecimentos e os anexos. Em audiência, responder ao quesito e remeter ao laudo; não discutir tese com o advogado; registrar que questão de direito cabe ao juízo.

Segunda perícia (CPC art. 480): determinada de ofício ou a requerimento quando a matéria não estiver suficientemente esclarecida; tem por objeto os mesmos fatos, rege-se pelas mesmas regras e não substitui a primeira, cabendo ao juiz apreciar o valor de uma e de outra. O melhor antídoto é o anexo de memória completo e o quadro de cenários com todas as hipóteses: a segunda perícia nasce de laudo que escolheu tese ou que não mostrou como chegou ao número.

Encerramento no lote: depois dos esclarecimentos, da audiência e do levantamento dos honorários finais, `lote_pasep.py atualizar --id P-00N --status encerrado --observacao "..."`.
