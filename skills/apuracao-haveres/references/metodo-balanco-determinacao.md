# Método do balanço de determinação a preço de saída

Referência: 12/09/2026. Detalha as etapas 3, 4 e 5 do workflow: preço de saída por classe, passivos e contingências, balanço reconstruído, fundo de comércio como intangível, lucros até a data e exemplo numérico com os dados fictícios de `assets/`.

## Sumário

1. O que é o balanço de determinação e o que ele não é
2. Preço de saída por classe de ativo
3. Passivos, contingências e tributo sobre a mais-valia
4. Balanço reconstruído quando não há balancete na data
5. Fundo de comércio como intangível na data da resolução
6. Lucros, JCP e remuneração até a data sem dupla contagem
7. Haveres negativos, quota não integralizada e participação
8. Exemplo numérico encadeado
9. Armadilhas e como a skill as evita

---

## 1. O que é o balanço de determinação e o que ele não é

O balanço de determinação é o balanço especialmente levantado (CC, art. 1.031) na data da resolução, com bens e direitos do ativo, tangíveis e intangíveis, e o passivo avaliados a preço de saída (CPC, art. 606). Ele mede a situação patrimonial da sociedade naquele dia como se o patrimônio fosse realizado em transação não forçada. Não é o balanço contábil (custo histórico, provisões fiscais, goodwill interno proibido pela NBC TG 04), nem o balanço de liquidação (venda forçada, com deságio), nem uma avaliação econômica da empresa (valor presente de fluxos futuros). A distinção importa porque cada um desses três produz um número diferente e só o primeiro é o critério legal na omissão do contrato.

Ordem de trabalho: (1) balanço contábil de partida na data da resolução ou na data mais próxima, com rolagem documentada; (2) conciliação dos saldos relevantes com documentos externos (extratos, circularização, certidões); (3) ajuste conta a conta a preço de saída, com fundamento e fonte; (4) contingências pelo CPC 25; (5) separação dos intangíveis já reconhecidos para obter o PL tangível; (6) mensuração do fundo de comércio no script 2; (7) sanidade.

---

## 2. Preço de saída por classe de ativo

| Classe | Preço de saída | Procedimento | Erro típico |
|---|---|---|---|
| Caixa e equivalentes | Saldo conciliado na data, com rendimentos apropriados pro rata | Extratos e conciliação; cheques pré-datados e saldos bloqueados segregados | Usar saldo contábil não conciliado |
| Clientes e outros recebíveis | Valor de realização: saldo menos perda esperada real; valor presente para vencimentos longos sem encargos | Aging list na data, histórico de perdas dos últimos anos, cobrança posterior como evidência (até a entrega do laudo) | PDD fiscal (percentual legal) tomada como perda real; títulos vencidos há anos mantidos pelo nominal |
| Estoques | Valor realizável líquido (preço de venda estimado menos custos para vender); itens obsoletos e sem giro a valor de liquidação | Inventário valorado na data, relatório de giro, visita quando relevante | Custo médio sem teste de obsolescência; estoque de dezembro usado para junho |
| Imobilizado: imóveis | Valor de mercado por laudo (ABNT NBR 14653-2) na data da resolução | Laudo de engenheiro avaliador; matrícula com ônus | Custo histórico de décadas atrás; valor de IPTU |
| Imobilizado: máquinas, veículos, equipamentos | Valor de mercado para bens usados (ABNT NBR 14653-5; cotações datadas; tabelas de referência de mercado para veículos) | Relação do imobilizado com localização; vistoria | Valor contábil líquido de depreciação fiscal |
| Investimentos em outras sociedades | Balanço de determinação da investida (recursivo) ou valor de mercado se houver cotação | Demonstrações da investida na mesma data | Equivalência patrimonial sobre balanço contábil da investida |
| Intangíveis registrados (software, marca adquirida, licenças) | Custo amortizado se não houver evidência de perda nem de valor superior; avaliação específica quando relevante | Razão da conta; registro no INPI; contratos de licença | Baixar a zero por "não ser tangível" |
| Tributos a recuperar e ativo fiscal diferido | Valor realizável em prazo definido; sem evidência de realização, zero com nota | Apuração fiscal, histórico de compensação | Manter crédito sem perspectiva de uso |
| Despesas antecipadas | Valor que a sociedade recuperaria ou aproveitaria; seguros pelo prêmio não decorrido | Apólices e contratos | Manter integral sem aproveitamento |

Todo ajuste precisa de fundamento e fonte no JSON; o script 1 recusa ajuste sem fundamento. Quando o laudo de avaliação não existe e o valor envolvido é relevante, o perito o requisita ou o produz com apoio de profissional habilitado; na falta, mantém o valor contábil com ressalva e quantifica o efeito por hipótese ("cada R$ 100.000,00 de mais-valia do imóvel eleva a quota do autor em R$ 25.000,00").

---

## 3. Passivos, contingências e tributo sobre a mais-valia

Passivos a preço de saída são avaliados pelo valor necessário para liquidá-los na data: fornecedores pelo saldo conciliado por circularização; empréstimos pelo saldo devedor com encargos contratuais apropriados pro rata até a data (o balancete mensal costuma não apropriar o período quebrado); tributos vencidos com multa e juros na data; parcelamentos pelo saldo consolidado; obrigações trabalhistas e sociais pelo valor devido na data, inclusive provisão de férias e décimo terceiro proporcionais; pro labore e lucros deliberados e não pagos como passivo (ver seção 6).

Contingências seguem o CPC 25 (NBC TG 25):

| Probabilidade de perda | Tratamento no balanço de determinação | Efeito no script 1 |
|---|---|---|
| Provável | Provisiona pelo valor estimado; provisão adicional igual ao estimado menos o já provisionado | Reduz o PL de determinação |
| Possível | Não provisiona; divulga em nota com o valor | Quadro separado; não reduz o PL; o laudo informa o efeito hipotético por participação |
| Remota | Não provisiona nem divulga | Registrada apenas na memória |

A classificação vem do parecer dos advogados da sociedade ou, na falta, de critério declarado pelo perito (fase processual, valor da causa, sentença já proferida), sempre com sensibilidade. Provisão contábil para contingência classificada como possível ou remota é revertida no valor de saída do passivo, com alerta do script.

Tributo diferido sobre a mais-valia: parte da prática pericial deduz IRPJ e CSLL que incidiriam se os ativos reavaliados fossem vendidos, por entender que o preço de saída é líquido do tributo; outra parte não deduz, porque a venda não ocorre e o sócio que fica também não paga. Não há precedente verificado nesta skill sobre o ponto [A VERIFICAR]. Conduta: cenário base sem dedução, cenário alternativo com dedução pelo regime tributário da sociedade, diferença informada; a escolha é do juízo.

---

## 4. Balanço reconstruído quando não há balancete na data

Quando a sociedade não tem balancete na data da resolução (escrituração atrasada, exclusão em data intermediária), o perito parte do último balanço ou balancete confiável (ECD) e rola os saldos até a data: caixa pelos extratos; clientes e fornecedores pelas notas e pagamentos do período; estoques pelo último inventário mais compras menos custo das vendas; imobilizado pelas aquisições e baixas; empréstimos pelas planilhas do banco; tributos pelas guias e declarações. O resultado é apresentado como cenário reconstruído, com a lista do que foi rolado por documento e do que foi estimado, e com a ressalva de que a entrega do balancete pode alterar os valores. O ônus de apresentar a escrituração é da sociedade (CPC, arts. 373, § 1º, e 420); a consequência da recusa é do juízo (CPC, art. 400). O laudo nunca escolhe a data de um balanço existente (31/12 anterior ou posterior) no lugar da data da resolução por comodidade: a data é a do art. 605.

---

## 5. Fundo de comércio como intangível na data da resolução

### 5.1 Por que o intangível entra e por que o DCF não

O art. 606 manda avaliar "bens e direitos do ativo, tangíveis e intangíveis". O goodwill gerado internamente (carteira de clientes, reputação, ponto, organização, know-how) não é reconhecido na contabilidade (NBC TG 04), mas existe na data da resolução e o STJ o inclui no balanço de determinação (REsp 2.174.631; REsp 1.892.139; AgInt no AgInt no AREsp 2.903.904). O que o STJ afasta é a mensuração por fluxo de caixa descontado, porque o método precifica lucros de exercícios posteriores à resolução, que o ex-sócio não tem direito de receber (CPC, art. 608, parágrafo único) e cujo risco é dos sócios que ficam (REsp 1.877.331; REsp 1.904.252; REsp 1.900.838; AgInt nos EDcl no REsp 2.160.132). O intangível é, portanto, medido por evidência de capacidade histórica de gerar lucro acima da remuneração do capital tangível, na data da resolução.

### 5.2 Método do lucro excedente (padrão)

1. Série de 3 a 5 exercícios encerrados antes da data da resolução, com lucro contábil e ajustes descritos: retirar ganhos e perdas não recorrentes (venda de imóvel, multa, indenização recebida, baixa extraordinária), retirar o resultado de ativos já reavaliados no balanço (para não contar a mais-valia duas vezes), ajustar o pro labore ao valor de mercado quando os sócios retiravam acima ou abaixo dele, e considerar o lucro após tributos sobre o lucro.
2. Lucro médio normalizado: média aritmética, ou ponderada com pesos declarados quando a tendência for relevante.
3. Remuneração do capital tangível: PL de determinação tangível (PL de determinação menos intangíveis já reconhecidos) multiplicado pela taxa de remuneração do capital. A taxa entra com fonte (série do SGS do Banco Central consultada com data, ou custo de oportunidade fundamentado no laudo); o script recusa taxa sem fonte.
4. Lucro excedente: lucro médio normalizado menos remuneração do capital. Se nulo ou negativo, o fundo de comércio é zero: o resultado histórico não remunera o capital tangível.
5. Fundo de comércio: lucro excedente multiplicado pelo fator, que representa o número de anos de lucro excedente que um comprador pagaria antecipadamente. A prática pericial usa de 2 a 5; o fundamento considera setor, estabilidade da clientela, barreiras à entrada e dependência da pessoa do sócio. O script apresenta sensibilidade ao fator (mais ou menos um) e à taxa (mais ou menos um ponto percentual).

### 5.3 Método do múltiplo (contraprova)

Valor de referência igual ao lucro médio normalizado multiplicado por um múltiplo fundamentado em transações ou laudos comparáveis; fundo de comércio igual ao valor de referência menos o PL tangível, com piso zero. Serve de contraprova do lucro excedente; não é cenário base sem comparáveis documentados.

### 5.4 Dependência da pessoa do sócio e sociedades de serviços

Quando a clientela e o resultado dependem da atuação pessoal do sócio que se retira (profissional liberal, representante comercial), parte do intangível sai com ele e não pertence à sociedade. O perito separa o fundo de comércio da sociedade (estrutura, equipe, contratos, marca) do intangível pessoal, com fundamento no fator reduzido ou em ajuste declarado do lucro normalizado, e expõe a sensibilidade. Sociedade prestadora de serviços com elemento de empresa tem intangível a mensurar (REsp 1.892.139).

### 5.5 Contrato social que prevê DCF ou exclui o intangível

Cláusula que prevê DCF: o perito registra a cláusula, informa que a jurisprudência afasta o método na omissão do contrato e que a eficácia da cláusula é questão jurídica; apresenta o balanço de determinação com o intangível pelo lucro excedente e, se o juízo determinar, calcula o DCF fora desta skill (`valuation-capital-fechado`) como cenário rotulado, nunca como valor patrimonial. Cláusula que exclui o intangível ou fixa valor contábil: cenário contratual e cenário legal, com a diferença; a abusividade é do juízo.

---

## 6. Lucros, JCP e remuneração até a data sem dupla contagem

O art. 608 do CPC integra aos haveres a participação nos lucros ou os JCP declarados até a data da resolução e, se for o caso, a remuneração como administrador. Três situações:

| Situação | Onde está no balanço de determinação | Como entra nos haveres |
|---|---|---|
| Lucro deliberado e pago ao sócio antes da data | Já saiu do caixa e do PL | Não entra; se pago depois da data, é adiantamento a deduzir |
| Lucro deliberado e não pago | Passivo (lucros a distribuir), reduzindo o PL | A parte do sócio entra pelo `--lucros-declarados` do script 3, sujeita à prescrição trienal |
| Lucro do exercício em curso, não deliberado | Dentro do PL de determinação (resultado até a data) | Entra pela quota; somar de novo é dupla contagem |
| Pro labore devido e não pago ao sócio administrador | Passivo (obrigações com administradores) | Entra pelo `--remuneracao-administrador` |

Se o balanço contábil mantém no PL um lucro já deliberado (sem transferir para o passivo), o perito reclassifica no balanço de determinação antes de rodar o script 3; o script alerta quando recebe lucros declarados e o balanço não tem conta de lucros ou dividendos a pagar. A prescrição trienal (CC, art. 206, § 3º; REsp 1.904.252) conta da deliberação e se interrompe com a citação, retroagindo à propositura (CPC, art. 240, § 1º); o script exclui os prescritos, lista o valor e aceita `--incluir-prescritos` quando a decisão determinar.

---

## 7. Haveres negativos, quota não integralizada e participação

PL de determinação negativo: a quota patrimonial é zero (o script alerta) e o eventual débito do sócio para com a sociedade é questão jurídica marcada `[A VERIFICAR]` na pendência 4 de `fundamentacao-legal.md`. Quota parcialmente integralizada: o CC, art. 1.031, caput, manda considerar o montante efetivamente realizado; o script aplica `--integralizado` (padrão 100%) e registra a premissa. Participação: a do contrato social consolidado na data da resolução; alteração não registrada é anotada e resolvida pelo juízo. Sócio que exerceu retirada de parte das quotas (resolução parcial da participação) entra com o percentual das quotas liquidadas.

---

## 8. Exemplo numérico encadeado

Dados fictícios de `assets/` (Alfa Comércio Ltda., retirada imotivada, notificação recebida em 01/05/2025, data da resolução 30/06/2025, sócio com 25%):

| Etapa | Cálculo | Resultado |
|---|---|---|
| Ativo contábil / a preço de saída | 950.000,00 / 1.025.000,00 (imóvel de 400.000,00 para 550.000,00; clientes menos 30.000,00; estoques menos 20.000,00; veículos menos 25.000,00) | Ajuste de ativo 75.000,00 |
| Passivo contábil / a preço de saída | 470.000,00 / 475.000,00 (encargos pro rata do empréstimo 5.000,00) | Ajuste de passivo 5.000,00 |
| Contingências | Trabalhista provável 80.000,00 com 20.000,00 provisionados: adicional 60.000,00; ICMS possível 150.000,00 divulgado; cível remota 50.000,00 registrada | Provisão adicional 60.000,00 |
| PL contábil | 950.000,00 menos 470.000,00 | 480.000,00 |
| PL de determinação | 1.025.000,00 menos 475.000,00 menos 60.000,00 | 490.000,00 |
| PL tangível | 490.000,00 menos 30.000,00 de software registrado | 460.000,00 |
| Lucro médio normalizado | (110.000 + 180.000 + 215.000 + 170.000 + 190.000) / 5 | 173.000,00 |
| Remuneração do capital | 460.000,00 x 12% (taxa fictícia com fonte declarada) | 55.200,00 |
| Lucro excedente | 173.000,00 menos 55.200,00 | 117.800,00 |
| Fundo de comércio | 117.800,00 x fator 3 (sensibilidade: 235.600,00 com 2; 471.200,00 com 4) | 353.400,00 |
| Quota patrimonial | (490.000,00 + 353.400,00) x 25% | 210.850,00 |
| Lucros declarados | 2022: 15.000,00; 2024: 6.000,00; 2021 (12.500,00) prescrito, ajuizamento em 15/08/2025 | 21.000,00 |
| Remuneração como administrador | Pro labore de maio e junho de 2025 | 16.000,00 |
| Haveres brutos | 210.850,00 + 21.000,00 + 16.000,00 | 247.850,00 |
| Dedução | Levantamento da parte incontroversa em 10/09/2025 | (30.000,00) |
| Haveres líquidos | Correção desde 30/06/2025; juros a partir de 09/06/2026 (liquidação em 10/03/2026 mais 90 dias) | 217.850,00 |

Pelo múltiplo de 4 (contraprova), o fundo de comércio seria de 232.000,00 (173.000,00 x 4 menos 460.000,00), e a quota, de 180.500,00; a diferença vai ao laudo como sensibilidade de método.

---

## 9. Armadilhas e como a skill as evita

- Balanço levantado em 31/12 por comodidade: a data é a do art. 605; o script 1 confere o marco e recusa divergência.
- Mais-valia contada duas vezes: o ganho na venda do ativo reavaliado sai do lucro normalizado (ajuste descrito no JSON do script 2).
- Fundo de comércio por "percentual do faturamento" sem base: o script 2 só aceita lucro excedente ou múltiplo com fundamento e fonte.
- Contingência possível deduzida: o script 1 só provisiona a provável.
- Lucro deliberado no PL e no art. 608: alerta do script 3 e passo 9 da memória do script 1.
- Juros desde a data-base a 1% ao mês: termos declarados pelo script 3; taxa e índice na `atualizacao-monetaria`.
- Projeção de lucros rotulada de "goodwill": recusa do método `dcf` com a jurisprudência na mensagem.
