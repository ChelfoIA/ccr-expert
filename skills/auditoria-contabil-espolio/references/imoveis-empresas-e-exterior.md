# Imóveis, sociedades fechadas e bens no exterior

Referência: 12/09/2026. Método de apuração dos frutos por tipo de bem e das rendas que o espólio deixou de receber. Fundamentação e precedentes em `references/fundamentacao-legal.md`; documentos em `references/roteiro-auditoria-e-documentos.md`.

## Sumário

1. Imóvel ocupado com exclusividade por herdeiro
2. Imóvel locado a terceiro
3. Imóvel vago e imóvel de uso do espólio
4. Bens em Portugal: jurisdição, fluxo em euro e PTAX
5. Sociedades de capital fechado
6. Sinais de retirada disfarçada
7. Quantificação consolidada sem dupla contagem

---

## 1. Imóvel ocupado com exclusividade por herdeiro

Fundamento: até a partilha a herança é condomínio (CC, art. 1.791, parágrafo único); o condômino responde aos demais pelos frutos que percebeu (CC, art. 1.319); herdeiro em posse de bem da herança traz ao acervo os frutos desde a abertura da sucessão (CC, art. 2.020). O uso exclusivo equivale a perceber o fruto (a renda que o bem daria), e por isso o ocupante deve aos demais coerdeiros a parcela correspondente às frações deles.

Fórmula do script: devido = aluguel de mercado x (1 - fração do ocupante) x meses desde o marco inicial, mês a mês, pro rata die no mês parcial (CC, art. 1.215). A fração do ocupante é a que ele tem no imóvel (quinhão mais meação, se for o caso); vazia, o script assume 1/N herdeiros e avisa, porque meação, testamento e regime de bens alteram a fração.

Marco inicial: o perito não escolhe; calcula em cada marco documentado e apresenta em quadro:

| Marco | Fundamento na lista verificada | Documento típico |
|---|---|---|
| Abertura da sucessão | Cenário de sensibilidade (CC, art. 2.020 fala em frutos "desde a abertura da sucessão"); o script calcula como alternativa | Certidão de óbito |
| Oposição inequívoca dos demais | REsp 1.583.973 (oposição manifestada por outros meios, não só a citação); AgInt no REsp 2.240.323 | Mensagens, ata de reunião, manifestação nos autos do inventário |
| Notificação extrajudicial | AREsp 3.121.778/SP | Notificação com aviso de recebimento |
| Citação na ação de arbitramento | CPC, art. 240; AREsp 3.121.778/SP | Certidão de citação |

Exceções que afastam o aluguel: decisão do juízo deferindo o uso antecipado do bem como parte da cota (CPC, art. 647, parágrafo único), anuência expressa dos demais, ou uso compartilhado comprovado. A inércia dos demais herdeiros não configura supressio (AgInt no REsp 2.240.323).

Encargos: IPTU e condomínio posteriores à abertura da sucessão ficam a cargo de quem usa com exclusividade (REsp 1.704.528). Se o espólio os pagou, o valor é recomposto. Dupla compensação é vedada (REsp 1.918.125): o mesmo encargo não pode ser descontado do quinhão e cobrado como indenização; o mesmo aluguel não pode entrar como fruto devido e como dano. O laudo declara em qual quadro cada parcela está.

Aluguel de mercado: laudo de avaliação, anúncios de imóveis equivalentes com data e endereço, ou índice de locação da região, sempre com fonte na coluna `fonte_mercado`. Benfeitorias feitas pelo ocupante: reembolso das necessárias e úteis (CC, art. 2.020, parte final), com nota fiscal, em quadro separado e sem compensação automática.

Via processual: a cobrança pode correr no inventário quando a prova é documental (CPC, art. 612) ou em ação autônoma quando exige dilação probatória (REsp 2.054.388). A prescrição só corre após o trânsito em julgado da partilha (AgInt no REsp 2.240.323); o prazo em si é pendência (`[A VERIFICAR]`).

Exemplo com os assets: IM02, aluguel de mercado R$ 4.000,00 (laudo de fl. 210), ocupante Pedro Alfa com fração 1/4, notificação em 01/07/2024, referência 30/06/2026: R$ 4.000,00 x 0,75 x 24 = R$ 72.000,00 devidos aos demais; cenário com marco na abertura (10/01/2024): 29,7097 meses, R$ 89.129,03; encargos pagos pelo espólio R$ 11.400,00 (condomínio de 02/2024 a 12/2024 e IPTU de 2024 e 2025).

---

## 2. Imóvel locado a terceiro

Esperado = aluguel contratual vigente em cada mês, com reajustes previstos no contrato. Recebido = ingressos identificados em conta do espólio ou, se em conta de herdeiro ou inventariante, ingressos que o perito rastreou (e que então aparecem no fluxo como saída não repassada). Diferença = inadimplência do locatário (crédito do espólio contra terceiro), aluguel retido por quem recebeu (REsp 1.655.720) ou mês sem lastro (nem recibo nem extrato), que o script lista.

Gap contratual x mercado: é informação, não dano, quando o contrato vem da época do falecido. Vira achado de gestão quando o inventariante firmou ou renovou contrato abaixo do mercado sem justificativa, ou deixou de pedir a revisão possível após três anos (Lei 8.245/1991, art. 19); mesmo assim, o perito descreve e o juízo qualifica (CC, art. 2.020, dano por culpa; CPC, art. 622, III).

Aluguel pago em conta pessoal do herdeiro: entra no fluxo como ingresso do espólio naquela conta (uso misto) e, se não repassado, como saída em favor do herdeiro.

---

## 3. Imóvel vago e imóvel de uso do espólio

Vago: a renda potencial (mercado x meses de vacância) é cenário, apresentado em linha separada e fora do total do que o espólio deixou de receber, porque só vira dano com prova de culpa na administração (imóvel em condições de locação, demanda existente, inércia injustificada do inventariante). O script já separa `renda_potencial_de_imovel_vago` do total.

Uso do espólio (sede de empresa do acervo, depósito de bens): sem fruto esperado; as despesas são de conservação.

---

## 4. Bens em Portugal: jurisdição, fluxo em euro e PTAX

Jurisdição: a autoridade brasileira tem competência exclusiva para inventariar e partilhar bens situados no Brasil (CPC, art. 23, II); os bens em Portugal seguem a jurisdição e o procedimento locais (habilitação de herdeiros, Imposto do Selo, registo predial), com a lei aplicável à sucessão definida pela LINDB, art. 10, e, do lado europeu, pelo Regulamento (UE) 650/2012 `[A VERIFICAR]`. Para a auditoria isso é irrelevante: a renda do imóvel de Lisboa é fruto do espólio desde o óbito (CC, arts. 1.784 e 2.020) e o inventariante ou o herdeiro que a recebeu presta contas dela, onde quer que o bem venha a ser partilhado. O laudo anota a questão de jurisdição em uma frase e segue.

Fluxo em euro: transcrever os movimentos da conta portuguesa no mesmo layout do CSV de movimentos, com `moeda` EUR, e converter com `conversao_ptax.py` antes de qualquer soma. Regras:

1. Cotação da data do movimento; sem cotação no dia (fim de semana, feriado), a do dia útil anterior disponível, com a defasagem declarada linha a linha.
2. Critério declarado: venda (padrão, por ser a cotação de quem precisa comprar euro para repor o valor), compra ou média. O juízo pode fixar outro; o script recalcula.
3. A série PTAX entra por arquivo com a coluna `fonte` obrigatória: código da série no SGS do BCB `[A VERIFICAR]` e data da consulta. O exemplo dos assets é fictício e o script avisa quando o encontra. Nunca estimar cotação; sem série, o script falha.
4. Totais apresentados nas duas moedas: o quadro por imóvel de `rendimentos_imoveis.py` sai em euro; a conversão para reais é feita sobre os movimentos e sobre os totais, com a cotação da data de cada parcela, nunca por uma cotação média do período.

Despesas locais: IMI, IRS sobre rendimentos prediais e condomínio são despesas documentadas do imóvel (nota de cobrança, nota de liquidação, recibo), de conservação (CPC, art. 619, IV), e seguem no fluxo como `tributo` ou `condominio` com `imovel_id`. As regras portuguesas de IMI e de IRS do não residente são pendência `[A VERIFICAR]`; o perito não recalcula imposto português, confere que o pagamento tem documento e que o valor corresponde à nota.

Imposto de renda brasileiro sobre renda do exterior (carnê-leão do espólio) e compensação do imposto pago em Portugal: pendência `[A VERIFICAR]`; registrar se houve recolhimento.

---

## 5. Sociedades de capital fechado

O que muda com a morte do sócio (CC, art. 1.028): a quota se liquida (apuração de haveres, CC, art. 1.031, skill `apuracao-haveres`), salvo se o contrato prevê continuidade com os herdeiros, se os sócios dissolvem a sociedade ou se há acordo de substituição. O contrato social decide; o perito lê a cláusula e classifica cada sociedade como "continuidade com o espólio" (o espólio é sócio e participa dos lucros) ou "liquidação da quota" (o espólio tem crédito de haveres mais os lucros até a data da resolução).

Quadro por sociedade (layout em `assets/exemplo_sociedades.csv`, preenchido à mão a partir de balanço, DRE, atas e razão):

| Campo | Fonte | Uso |
|---|---|---|
| participacao_espolio | Contrato social | Fração dos lucros que cabe ao espólio (CC, art. 1.007) |
| continuidade_com_espolio | Contrato social, cláusula de falecimento | S: lucros do período; N: haveres mais lucros até a resolução |
| lucro_liquido_periodo | DRE de cada exercício | Base do que poderia ser distribuído |
| lucro_distribuido_total e ao espólio | Atas, razão de lucros a distribuir, DIRPF dos sócios | Distribuído x devido pro rata |
| clausula_distribuicao | Contrato social | Pro rata ou desproporcional com cláusula válida |
| pro_labore_herdeiro_admin e referência | Folha; pesquisa salarial com fonte | Excesso sobre a referência |
| mutuos_a_herdeiros | Razão de conta corrente de sócios, contratos | Retirada disfarçada quando sem contrato, juros e prazo |
| despesas_pessoais_na_empresa | Razão de despesas, notas | Retirada disfarçada |

Cálculo da diferença para o espólio, por sociedade:

1. Lucro distribuído devido ao espólio = lucro distribuído total x participação (ou pela cláusula válida de distribuição desproporcional, quando houver). Diferença = devido menos recebido pelo espólio.
2. Lucro retido: não é devido automaticamente; depende de deliberação. Entra como informação ("o espólio tem direito a X do lucro acumulado não distribuído") e como achado quando os demais sócios receberam e o espólio não.
3. Pró-labore acima da referência de mercado, mútuo sem contrato e despesa pessoal na empresa reduzem o lucro distribuível; a parcela que cabe ao espólio nesse lucro suprimido é participação x excesso. Apresentar como "lucro suprimido por retirada" em quadro separado, sem somar ao item 1 quando a mesma importância já voltou como distribuição.
4. Sociedade com liquidação da quota: lucros até a data da resolução pelo item 1; o valor da quota vai para `apuracao-haveres` e `valuation-capital-fechado`.

Exemplo com os assets: Alfa Comércio Ltda. (E01), participação 60%, continuidade S, lucro distribuído total R$ 100.000,00: devido pro rata R$ 60.000,00, recebido R$ 25.000,00, diferença R$ 35.000,00. Pró-labore do herdeiro-administrador R$ 180.000,00 contra referência de R$ 96.000,00 (pesquisa de fl. 320): excesso R$ 84.000,00, parcela do espólio no lucro suprimido R$ 50.400,00. Mútuos a herdeiros R$ 40.000,00 e despesas pessoais R$ 12.000,00 sem contrato: R$ 52.000,00, parcela do espólio R$ 31.200,00, em quadro separado. Beta Participações (E02), 30%, nada distribuído, lucro R$ 90.000,00: direito a R$ 27.000,00 do acumulado, informação. Gama Serviços (E03), 25%, continuidade N: R$ 50.000,00 distribuídos aos remanescentes depois da resolução sem nada ao espólio; lucros até a data da resolução a apurar e haveres pela skill própria.

---

## 6. Sinais de retirada disfarçada

- Pró-labore do herdeiro-administrador acima da referência de mercado, criado ou majorado após o óbito.
- Mútuo a sócio ou herdeiro sem contrato, sem juros, sem prazo, sem amortização.
- Despesa pessoal escriturada na empresa (veículo, viagem, cartão, escola, residência).
- Distribuição desproporcional sem cláusula contratual ou sem deliberação com participação do espólio.
- Lucro distribuído em ata a todos os sócios, mas pagamento ao espólio não localizado em extrato.
- Aumento de capital ou alteração contratual após o óbito sem o espólio.
- Venda de ativo da sociedade a herdeiro abaixo do valor contábil.
- Conta corrente de sócio com saldo devedor crescente do herdeiro-administrador.

Cada sinal é achado descritivo (fato, evidência, norma, efeito); a qualificação é do juízo.

---

## 7. Quantificação consolidada sem dupla contagem

Os três scripts produzem números que se sobrepõem em parte. O quadro consolidado do laudo adota uma única atribuição:

| Parcela | Origem | Entra em | Não entra em |
|---|---|---|---|
| Despesas pessoais e saídas a herdeiro ou inventariante sem decisão | `fluxo_caixa_espolio.py`, recomposição | Recomposição do caixa | Quadro de imóveis |
| Encargos de imóvel ocupado pagos pelo espólio | Aparecem nos dois scripts | Quadro de imóveis (coluna encargos) | Recomposição do caixa (subtrair para evitar a dupla contagem, declarando) |
| Aluguel devido pelo ocupante | `rendimentos_imoveis.py` | Quadro de imóveis | Fluxo (não houve caixa) |
| Aluguel contratual não recebido | `rendimentos_imoveis.py` | Quadro de imóveis, separado entre inadimplência de terceiro e retenção por herdeiro | Recomposição, salvo quando o fluxo mostra o ingresso em conta de herdeiro (então entra como saída a herdeiro e sai do quadro de imóveis) |
| Renda potencial de imóvel vago | `rendimentos_imoveis.py` | Linha informativa | Total do que deixou de receber |
| Rendas e despesas em euro | `conversao_ptax.py` | Fluxo e quadro de imóveis, já em reais | Soma em euro com real |
| Lucros devidos e não recebidos | Quadro de sociedades | Quadro de sociedades | Fluxo (não houve caixa) |
| Lucro suprimido por retirada | Quadro de sociedades | Linha separada | Lucros devidos |

Com os assets: recomposição do caixa R$ 29.200,00 menos encargos do imóvel ocupado R$ 11.400,00 já no quadro de imóveis = R$ 17.800,00; quadro de imóveis em reais R$ 91.529,03 (contratual não recebido R$ 8.129,03, ocupação R$ 72.000,00, encargos R$ 11.400,00) mais o equivalente em reais de EUR 2.051,61 do imóvel de Lisboa pela cotação de cada mês; sociedades R$ 35.000,00 de lucros devidos e não recebidos, mais R$ 50.400,00 e R$ 31.200,00 em linhas separadas de lucro suprimido. Valores nominais; atualização pela skill `atualizacao-monetaria`.
