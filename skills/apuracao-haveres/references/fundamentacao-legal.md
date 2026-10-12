# Fundamentação legal da apuração de haveres

Referência: 12/09/2026. Jurisprudência conferida nessa data; conferir o inteiro teor antes de transcrever trecho.

## Sumário

1. Direito material: Código Civil
2. Procedimento: CPC/2015, arts. 599 a 609, com os textos verificados
3. Prova, perícia e exibição de livros
4. Normas técnicas contábeis e de perícia
5. Jurisprudência verificada
6. Precedentes e enunciados não verificados
7. Ônus da prova e distribuição
8. Prescrição e marcos temporais
9. Limites do perito
10. Roteiro de quesitos
11. Protocolo antifabricação aplicado ao domínio
12. Pendências de verificação

---

## 1. Direito material: Código Civil

| Dispositivo | Conteúdo relevante para a perícia |
|---|---|
| CC, art. 1.028 | Morte de sócio: liquida-se a quota, salvo se o contrato dispuser diferentemente, se os remanescentes optarem pela dissolução total ou se houver acordo com os herdeiros para a substituição do falecido. A perícia só cabe na primeira hipótese; nas demais o laudo registra que a apuração ficou prejudicada |
| CC, art. 1.029 | Retirada: na sociedade por prazo indeterminado, por notificação aos demais sócios com antecedência mínima de 60 dias; na de prazo determinado, com prova judicial de justa causa. Parágrafo único: nos 30 dias seguintes à notificação os demais sócios podem optar pela dissolução total |
| CC, art. 1.030 | Exclusão judicial por falta grave no cumprimento das obrigações ou incapacidade superveniente, por iniciativa da maioria dos demais sócios; parágrafo único: exclusão de pleno direito do sócio falido ou cuja quota foi liquidada por credor (art. 1.026, parágrafo único) |
| CC, art. 1.031, caput | Nos casos em que a sociedade se resolve em relação a um sócio, o valor da quota, considerado pelo montante efetivamente realizado, liquida-se, salvo disposição contratual em contrário, com base na situação patrimonial da sociedade na data da resolução, verificada em balanço especialmente levantado. É a matriz do balanço de determinação e da proporção integralizada aplicada pelo script 3 (`--integralizado`) |
| CC, art. 1.031, § 1º | O capital social sofre a redução correspondente, salvo se os demais sócios suprirem o valor da quota. Efeito societário posterior ao laudo; não altera os haveres |
| CC, art. 1.031, § 2º | A quota liquidada é paga em dinheiro, no prazo de 90 dias a partir da liquidação, salvo acordo ou estipulação contratual em contrário. Fonte do prazo padrão do script 3 e do termo inicial dos juros (91º dia) |
| CC, art. 1.085 | Exclusão extrajudicial por justa causa na limitada: maioria representativa de mais da metade do capital, atos de inegável gravidade, previsão contratual e reunião ou assembleia especialmente convocada com direito de defesa (parágrafo único). A data dessa reunião é a data da resolução (CPC, art. 605, V) |
| CC, art. 206, § 3º | Prazo prescricional de três anos aplicado à pretensão do ex-sócio aos lucros declarados e não distribuídos, contado da deliberação da distribuição (STJ, REsp 1.904.252). O inciso específico está em pendência de verificação (seção 12, item 5) |
| CC, arts. 389, parágrafo único, e 406 (Lei 14.905/2024) | Correção monetária pelo IPCA na falta de convenção e juros pela taxa legal (Selic deduzido o IPCA, piso zero) a partir de 30/08/2024. O cálculo é da skill `atualizacao-monetaria`, regime civil; esta skill só fixa os termos iniciais |
| CC, art. 397 | Mora de pleno direito no vencimento de obrigação positiva e líquida com termo certo: fundamento do termo inicial dos juros no dia seguinte ao fim do prazo de pagamento |
| CC, art. 1.026, parágrafo único | Liquidação da quota a pedido de credor particular do sócio: hipótese de resolução com apuração pelo mesmo balanço |

---

## 2. Procedimento: CPC/2015, arts. 599 a 609

Textos dos arts. 602, 604, 605, 606, 608 e 609 verificados em 12/09/2026; os demais, de memória de lei consolidada, com o dispositivo.

| Dispositivo | Conteúdo relevante para a perícia |
|---|---|
| CPC, art. 599, caput e § 1º | Objeto da ação: resolução da sociedade em relação ao sócio falecido, excluído, retirante ou dissidente; apuração dos haveres; ou só uma delas. A inicial vem instruída com o contrato social consolidado, primeira peça que o perito lê |
| CPC, art. 599, § 2º | Sociedade anônima fechada: a ação cabe quando acionistas com 5% ou mais do capital demonstram que a companhia não pode preencher o seu fim. O reembolso de ações segue a Lei 6.404/1976, art. 45 [A VERIFICAR: redação vigente e critério do estatuto] |
| CPC, art. 600 | Legitimidade: espólio, sucessores, sociedade, sócio retirante ou dissidente, sociedade na exclusão; parágrafo único: cônjuge ou companheiro do sócio pode requerer a apuração dos seus haveres, pagos à conta da quota do sócio |
| CPC, art. 601 | Citação dos sócios e da sociedade; dispensada a citação da sociedade se todos os sócios forem citados, ficando ela sujeita aos efeitos da decisão |
| CPC, art. 602 | "A sociedade poderá formular pedido de indenização compensável com o valor dos haveres a apurar." Entra no script 3 como `--indenizacao-compensavel`, sempre com o fundamento da decisão que reconheceu o crédito |
| CPC, art. 603 | Concordância unânime: decreta-se a dissolução parcial e passa-se à liquidação, sem honorários e com custas rateadas (§ 1º); havendo contestação, procedimento comum, mas a liquidação segue este capítulo (§ 2º) |
| CPC, art. 604 | "Para apuração dos haveres, o juiz: I - fixará a data da resolução da sociedade; II - definirá o critério de apuração dos haveres à vista do disposto no contrato social; e III - nomeará o perito. § 1º O juiz determinará à sociedade ou aos sócios que nela permanecerem que depositem em juízo a parte incontroversa dos haveres devidos. § 2º O depósito poderá ser, desde logo, levantando pelo ex-sócio, pelo espólio ou pelos sucessores. § 3º Se o contrato social estabelecer o pagamento dos haveres, será observado o que nele se dispôs no depósito judicial da parte incontroversa." |
| CPC, art. 605 | "A data da resolução da sociedade será: I - no caso de falecimento do sócio, a do óbito; II - na retirada imotivada, o sexagésimo dia seguinte ao do recebimento, pela sociedade, da notificação do sócio retirante; III - no recesso, o dia do recebimento, pela sociedade, da notificação do sócio dissidente; IV - na retirada por justa causa de sociedade por prazo determinado e na exclusão judicial de sócio, a do trânsito em julgado da decisão que dissolver a sociedade; e V - na exclusão extrajudicial, a data da assembleia ou da reunião de sócios que a tiver deliberado." |
| CPC, art. 606 | "Em caso de omissão do contrato social, o juiz definirá, como critério de apuração de haveres, o valor patrimonial apurado em balanço de determinação, tomando-se por referência a data da resolução e avaliando-se bens e direitos do ativo, tangíveis e intangíveis, a preço de saída, além do passivo também a ser apurado de igual forma. Parágrafo único. Em todos os casos em que seja necessária a realização de perícia, a nomeação do perito recairá preferencialmente sobre especialista em avaliação de sociedades." |
| CPC, art. 607 | A data da resolução e o critério de apuração podem ser revistos pelo juiz, a pedido da parte, a qualquer tempo antes do início da perícia. Depois de iniciada, o perito trabalha com a data e o critério fixados e quantifica alternativas só como cenário |
| CPC, art. 608 | "Até a data da resolução, integram o valor devido ao ex-sócio, ao espólio ou aos sucessores a participação nos lucros ou os juros sobre o capital próprio declarados pela sociedade e, se for o caso, a remuneração como administrador. Parágrafo único. Após a data da resolução, o ex-sócio, o espólio ou os sucessores terão direito apenas à correção monetária dos valores apurados e aos juros contratuais ou legais." |
| CPC, art. 609 | "Uma vez apurados, os haveres do sócio retirante serão pagos conforme disciplinar o contrato social e, no silêncio deste, nos termos do § 2º do art. 1.031 da Lei nº 10.406, de 10 de janeiro de 2002 (Código Civil)." |

Leitura conjunta que orienta o laudo: o juiz fixa data e critério (art. 604); a data vem do art. 605 por hipótese; o critério vem do contrato social, e só na omissão dele do art. 606 (balanço de determinação a preço de saída, com intangíveis); até a data entram lucros, JCP e remuneração declarados (art. 608, caput); depois da data só correção e juros (art. 608, parágrafo único); o pagamento segue o contrato e, no silêncio, 90 dias (art. 609 e CC, art. 1.031, § 2º).

---

## 3. Prova, perícia e exibição de livros

| Dispositivo | Uso na perícia de haveres |
|---|---|
| CPC, art. 373, I, II e § 1º | O sócio retirante prova o fato constitutivo (vínculo, participação, data); a sociedade prova pagamentos e compensações. A distribuição dinâmica alcança a sociedade, que detém livros, ECD, contratos e laudos |
| CPC, arts. 396 a 400 | Exibição de documento ou coisa; recusa ilegítima faz o juiz admitir como verdadeiros os fatos que se pretendia provar. O perito registra a recusa e quantifica o efeito como cenário, sem presumir o fato |
| CPC, art. 420, I e II | Exibição integral dos livros e documentos empresariais na liquidação de sociedade e na sucessão por morte de sócio: a apuração de haveres é hipótese típica |
| CPC, arts. 417 e 418 | Livros empresariais provam contra o seu autor e a favor dele quando escriturados sem vício |
| CPC, arts. 464 a 480 | Prova pericial: assistentes e quesitos (art. 465, § 1º), quesitos suplementares (art. 469), quesitos do juiz (art. 470), conteúdo do laudo (art. 473), limites do perito (art. 473, § 2º), esclarecimentos (art. 477) |
| CPC, art. 95 | Honorários periciais adiantados por quem requereu a perícia ou rateados quando determinada de ofício ou requerida por ambas as partes |

---

## 4. Normas técnicas contábeis e de perícia

| Norma | Uso |
|---|---|
| NBC TG 25 (CPC 25) | Provisões, passivos contingentes e ativos contingentes: provável provisiona, possível divulga, remota não provisiona nem divulga. Regra embutida no script 1 |
| NBC TG 46 (CPC 46) | Valor justo: preço que seria recebido pela venda de um ativo ou pago pela transferência de um passivo em transação não forçada entre participantes do mercado na data de mensuração. É a definição técnica mais próxima do "preço de saída" do art. 606 |
| NBC TG 04 (CPC 04) | Ativo intangível: o goodwill gerado internamente não é reconhecido nas demonstrações contábeis. Por isso o fundo de comércio nunca está no PL contábil e precisa ser mensurado no balanço de determinação |
| NBC TG 01 (CPC 01) | Redução ao valor recuperável de ativos: base para baixar ativos sem capacidade de recuperação |
| NBC TG 16 (CPC 16) | Estoques: custo e valor realizável líquido |
| NBC TP 01 (R1) | Perícia contábil: planejamento, procedimentos, laudo, quesitos, memória e limites |
| NBC PP 01 (R1) | Perito contábil: competência, independência, impedimentos e sigilo |
| ABNT NBR 14653 | Avaliação de bens: imóveis (parte 2) e máquinas e equipamentos (parte 5); o laudo do engenheiro avaliador é a fonte do preço de saída do imobilizado |
| ECD, ECF, SPED Fiscal | Fontes digitais do balanço de partida, das DREs e dos estoques |

---

## 5. Jurisprudência verificada

Conferida em 12/09/2026 (JusRatio). Todas são decisões de Turma do STJ, orientativas, nenhuma vinculante. Citar com a identificação abaixo e conferir o inteiro teor antes de transcrever trecho.

| Tribunal e identificação | Tese e uso nesta skill | Fonte |
|---|---|---|
| STJ, REsp 1.335.619, Terceira Turma, Rel. Min. Nancy Andrighi, Rel. p/ acórdão Min. João Otávio de Noronha, j. 03/03/2015, DJe 27/03/2015 (relatora vencida) | Dissolução parcial de limitada; critérios de apuração de haveres; balanço de determinação; fluxo de caixa. Uso: marco inicial da linha que afasta a projeção de fluxos na apuração de haveres | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=201102662563&dt_publicacao=27/03/2015 |
| STJ, REsp 1.877.331, Terceira Turma, Rel. Min. Nancy Andrighi, Rel. p/ acórdão Min. Ricardo Villas Bôas Cueva, j. 13/04/2021, DJe 14/05/2021 (relatora vencida) | Omissão do contrato social; critério legal (CC, art. 1.031, e CPC, art. 606); valor patrimonial; balanço especial de determinação; fundo de comércio e intangíveis; fluxo de caixa descontado inadequado. Uso: fundamento central da seção 3 do SKILL.md e da recusa do DCF no script 2 | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=201902262895&dt_publicacao=14/05/2021 |
| STJ, REsp 1.904.252, Quarta Turma, Rel. Min. Maria Isabel Gallotti, j. 22/08/2023, DJe 01/09/2023 | Projeção de lucros futuros e DCF não cabíveis; lucros não distribuídos ao retirante: prescrição trienal (CC, art. 206, § 3º). Uso: prescrição aplicada pelo script 3 com `--data-ajuizamento` | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202002910230&dt_publicacao=01/09/2023 |
| STJ, REsp 1.892.139, Terceira Turma, Rel. Min. Ricardo Villas Bôas Cueva, j. 08/10/2024, DJe 11/10/2024 | Sociedade prestadora de serviços com elemento de empresa; omissão do contrato; art. 606; balanço especial de determinação; fundo de comércio e intangíveis. Uso: sociedades de serviços também têm intangível a mensurar | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202002176143&dt_publicacao=11/10/2024 |
| STJ, REsp 2.174.631, Terceira Turma, Rel. Min. Moura Ribeiro, j. 17/03/2025, DJEN 20/03/2025 | Fundo de comércio, aviamento e goodwill integram o balanço de determinação; DCF inviável; critério patrimonial legal. Uso: inclusão do intangível como regra, não como exceção | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202403778691&dt_publicacao=20/03/2025 |
| STJ, REsp 1.900.838, Terceira Turma, Rel. Min. Humberto Martins, j. 28/04/2025, DJEN 05/05/2025 | Omissão do contrato; DCF inadequado; Súmula 83 do STJ (orientação firmada no mesmo sentido). Uso: demonstra a estabilidade da orientação | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=201902323752&dt_publicacao=05/05/2025 |
| STJ, AgInt nos EDcl no REsp 2.160.132, Terceira Turma, Rel. Min. Nancy Andrighi, j. 28/04/2025 | Acórdão de origem que adotou DCF em dissonância com a jurisprudência do STJ. Uso: crítica de laudo e de decisão que adotaram DCF | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202402778457&dt_publicacao=05/05/2025 |
| STJ, AREsp 2.883.122, Terceira Turma, Rel. Min. Moura Ribeiro, j. 22/09/2025, DJEN 26/09/2025 | Previsão contratual ou balanço de determinação. Uso: hierarquia de critérios da seção 1 do SKILL.md | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202500897464&dt_publicacao=26/09/2025 |
| STJ, AgInt no AgInt no AREsp 2.903.904, Quarta Turma, Rel. Min. Maria Isabel Gallotti, j. 08/06/2026, DJEN 11/06/2026 | Inclusão do goodwill; inclusão de lucros futuros pelo DCF não cabível. Uso: precedente mais recente das duas Turmas no mesmo sentido | https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202501229330&dt_publicacao=11/06/2026 |
| STJ, AgInt no AREsp 1.736.426, Quarta Turma, Rel. Min. Marco Buzzi, j. 25/10/2021 (orientativo) | Dissolução parcial e haveres. Uso: reforço, nunca fundamento único | Portal do STJ |

Síntese para o laudo: as duas Turmas de direito privado do STJ, entre 2015 e 2026, convergem em três pontos: (1) contrato social válido prevalece e, na omissão, aplica-se o balanço de determinação do art. 606; (2) o fundo de comércio e os demais intangíveis integram esse balanço, avaliados na data da resolução; (3) o fluxo de caixa descontado é inadequado porque projeta lucros futuros que o retirante não tem direito de receber (art. 608, parágrafo único). Nenhum desses julgados é repetitivo: citar como orientação consolidada de Turma, sem a palavra "vinculante".

---

## 6. Precedentes e enunciados não verificados

A v1 desta skill citava, com trechos entre aspas, os REsp 1.239.754, 907.014, 1.286.708, 1.303.284, 1.422.934, 1.557.989, 1.602.240, 1.128.431 e 1.606.366. Nenhum deles foi conferido nesta forja; os trechos não foram localizados e a v2 os retirou. Quem precisar de tese sobre data-base, haveres negativos, termo inicial dos juros ou honorários periciais pesquisa o precedente na fonte oficial e o cita só depois de conferido. Lista completa na seção 12.

---

## 7. Ônus da prova e distribuição

- A existência e o percentual da participação se provam pelo contrato social consolidado e pelas alterações registradas na Junta Comercial; divergência entre o registro e os livros é anotada e resolvida pelo juízo.
- O balanço de partida, os razões, a ECD, os contratos de financiamento, a carteira de clientes, o inventário e os laudos de avaliação estão com a sociedade: distribuição dinâmica (CPC, art. 373, § 1º) e exibição integral (CPC, art. 420). O perito requisita por termo de diligência com prazo e registra o que não veio.
- Pagamentos já feitos ao sócio, levantamento do depósito da parte incontroversa (CPC, art. 604, § 2º) e indenização compensável (CPC, art. 602) são fatos extintivos ou modificativos: prova da sociedade.
- Lacuna documental vira cenário declarado com o efeito quantificado, nunca zero nem o valor pedido pela parte; a consequência da recusa de exibição é do juízo (CPC, art. 400).

---

## 8. Prescrição e marcos temporais

| Marco | Regra | Fonte |
|---|---|---|
| Data da resolução | Por hipótese do art. 605 do CPC; conferida pelo script 1 a partir do marco informado (notificação, óbito, trânsito, assembleia) | CPC, art. 605 |
| Balanço de determinação | Levantado na data da resolução; balancete de data próxima só como ponto de partida, com rolagem documentada | CPC, art. 606; CC, art. 1.031 |
| Lucros e JCP declarados | Integram os haveres se deliberados até a data da resolução; pretensão prescreve em três anos da deliberação | CPC, art. 608; CC, art. 206, § 3º; REsp 1.904.252 |
| Interrupção da prescrição | Citação válida, com efeito retroativo à data da propositura | CPC, art. 240, § 1º |
| Correção monetária | Desde a data da resolução | CPC, art. 608, parágrafo único |
| Prazo de pagamento | 90 dias da liquidação, salvo contrato | CC, art. 1.031, § 2º; CPC, art. 609 |
| Juros de mora | A partir do dia seguinte ao fim do prazo de pagamento, salvo decisão que fixe termo diverso (premissa declarada) | CC, arts. 397 e 406; [A VERIFICAR: orientação do STJ sobre o termo inicial dos juros nos haveres] |
| Revisão de data e critério | Possível até o início da perícia | CPC, art. 607 |

---

## 9. Limites do perito

O perito não decide a validade da cláusula contratual, a ocorrência de justa causa, a abusividade do critério ou a consequência da recusa de exibição (CPC, art. 473, § 2º). Quando a parte alega abusividade do critério contratual, o laudo apresenta dois cenários numerados (critério do contrato e critério legal do art. 606), com a diferença em reais, e deixa a escolha ao juízo. Quando o contrato prevê DCF, o perito registra a cláusula, informa que a jurisprudência do STJ afasta o método na omissão do contrato e que a eficácia da cláusula é questão jurídica; não calcula projeção de fluxo como se fosse valor patrimonial. Honorários, custas e sucumbência ficam fora do laudo.

---

## 10. Roteiro de quesitos

### 10.1 Quesitos do juízo

1. Qual a data da resolução da sociedade em relação ao sócio, à vista da hipótese dos autos e do art. 605 do CPC?
2. O contrato social prevê critério de apuração de haveres? Transcreva a cláusula e informe se o balanço levantado a observou.
3. Apresente o balanço de determinação na data da resolução com a memória de cada ajuste a preço de saída.
4. Informe os haveres do sócio em três cenários: patrimônio líquido contábil; patrimônio líquido de determinação sem intangível; patrimônio líquido de determinação com fundo de comércio.
5. Há lucros, JCP ou remuneração declarados e não pagos até a data da resolução? Quais e em que valor?
6. Houve depósito ou levantamento da parte incontroversa e pagamentos ao sócio? Deduza-os.

### 10.2 Quesitos do sócio retirante, do espólio ou dos sucessores

1. O balanço contábil da sociedade reflete o valor de mercado do imobilizado e dos estoques? Qual a diferença a preço de saída?
2. A sociedade tem carteira de clientes, marca, ponto, contratos ou outro intangível não registrado? Qual o valor na data da resolução?
3. Os lucros dos últimos cinco exercícios superam a remuneração do capital investido? Qual o fundo de comércio daí resultante?
4. As provisões registradas correspondem às contingências efetivamente prováveis, ou há provisão excessiva reduzindo o patrimônio?
5. Quais lucros deliberados deixaram de ser pagos ao sócio e qual o saldo com a data de cada deliberação?

### 10.3 Quesitos da sociedade e dos sócios remanescentes

1. O perito identificou passivos não contabilizados, contingências prováveis ou encargos não apropriados até a data da resolução?
2. Há títulos a receber vencidos, estoques obsoletos ou ativos sem valor de realização que o balanço mantém pelo custo?
3. O resultado dos exercícios usados na mensuração do fundo de comércio contém itens não recorrentes? Quais foram expurgados?
4. O fundo de comércio depende da atuação pessoal do sócio que se retira? Em que medida isso afeta o valor atribuído à sociedade?
5. O sócio retirante recebeu adiantamentos, lucros ou pro labore que devam ser deduzidos? Há crédito da sociedade compensável (CPC, art. 602)?
6. Os lucros reclamados foram deliberados há mais de três anos antes do ajuizamento?

---

## 11. Protocolo antifabricação aplicado ao domínio

- Taxa de remuneração do capital, índice de correção, taxa legal e qualquer parâmetro de mercado entram por arquivo com fonte declarada (bcb.gov.br/SGS, laudo de avaliação, cotação com data). O script 2 recusa taxa sem fonte.
- Fator ou múltiplo sem fundamento é recusado pelo script 2; o laudo expõe a sensibilidade.
- Jurisprudência: só a da seção 5, com a identificação completa. O que faltar entra como `[A VERIFICAR]` e vai para a seção 12.
- Texto de lei: os arts. 602, 604, 605, 606, 608 e 609 do CPC estão transcritos na seção 2 conforme verificação de 12/09/2026; os demais dispositivos são citados pelo número, sem aspas.
- Afirmação sensível ao tempo (vigência da Lei 14.905/2024, orientação do STJ) leva a data de referência 12/09/2026.

---

## 12. Pendências de verificação

Lista consolidada de todo item marcado `[A VERIFICAR]` nesta skill:

1. Informativo STJ 864 (REsp 2.223.719-SP, Terceira Turma, j. 02/09/2025) sobre apuração de haveres: conteúdo não conferido.
2. Enunciados das Jornadas de Direito Comercial do CJF sobre apuração de haveres, data da resolução e fundo de comércio.
3. Existência de tema repetitivo do STJ sobre critério de apuração de haveres ou inclusão do fundo de comércio.
4. Orientação do STJ sobre haveres negativos ou nulos (patrimônio líquido de determinação negativo) e sobre eventual débito do sócio retirante.
5. Inciso do § 3º do art. 206 do Código Civil invocado no REsp 1.904.252 para a prescrição trienal dos lucros não distribuídos (o brief indica o inciso VI; conferir no inteiro teor).
6. Orientação do STJ sobre o termo inicial dos juros de mora nos haveres (citação, liquidação ou 91º dia após a liquidação).
7. Lei 6.404/1976, art. 45: redação vigente e critério de reembolso de ações na sociedade anônima fechada (CPC, art. 599, § 2º).
8. Tratamento do tributo diferido sobre a mais-valia dos ativos reavaliados no balanço de determinação: precedente ou doutrina que o admita ou afaste.
9. Precedentes citados pela v1 e não conferidos: REsp 1.239.754, 907.014, 1.286.708, 1.303.284, 1.422.934, 1.557.989, 1.602.240, 1.128.431 e 1.606.366.
10. Série do SGS do Banco Central adequada à taxa de remuneração do capital em cada caso (a skill não fixa série nem valor).
