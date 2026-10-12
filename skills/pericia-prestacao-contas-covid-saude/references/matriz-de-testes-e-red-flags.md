# Matriz de testes por despesa e red flags

Referência: 12/09/2026. Este arquivo define o que `scripts/matriz_despesas_covid.py` testa em cada despesa, como classifica, quais sinais de alerta merecem diligência adicional, como quantificar e como redigir o achado sem qualificação jurídica.

## Sumário

1. Teste por despesa
2. Regras de classificação e ordem de severidade
3. Red flags e diligência adicional
4. Fracionamento: método
5. Preço de referência e sobrepreço: método
6. Fornecedor: constituição, sanção, quadro societário
7. Quantificação
8. Redação do achado
9. Erros que derrubam o laudo

---

## 1. Teste por despesa

| Teste | Pergunta | Evidência esperada | Norma | Achado (código) | Classe |
|---|---|---|---|---|---|
| Aderência ao objeto | O objeto cabe na finalidade da fonte que pagou? | Portaria ou lei da fonte; plano de contingência; enquadramento como ASPS | LRF, art. 8º, parágrafo único; LC 141/2012, arts. 2º a 4º | ADERENCIA_N / ADERENCIA_D | desvio de finalidade / aderência a esclarecer |
| Processo de contratação | Há processo formalizado com justificativa e autorização? | Autuação, justificativa da dispensa, autorização | Lei 13.979/2020, art. 4º; Lei 14.133/2021, art. 72 | PROCESSO_N | irregularidade formal |
| Pesquisa de preços | Há estimativa ou justificativa para a sua dispensa? | Cotações, painel, contratações similares; justificativa do art. 4º-E, § 2º | Lei 14.133/2021, arts. 23 e 72, II; Lei 13.979/2020, art. 4º-E | PESQUISA_N | irregularidade formal |
| Contrato | Há contrato ou instrumento substitutivo? | Contrato, nota de empenho com condições, ordem de fornecimento | Lei 14.133/2021, art. 95 `[A VERIFICAR o alcance]` | CONTRATO_N | irregularidade formal |
| Nota fiscal | A liquidação tem documento fiscal? | NF ou documento equivalente com data e valor | Lei 4.320/1964, art. 63 | NF_AUSENTE | sem comprovação |
| Atesto | Alguém atestou o recebimento? | Atesto do fiscal ou responsável, datado | Lei 4.320/1964, art. 63; Lei 14.133/2021, art. 140 | ATESTO_N | irregularidade formal |
| Entrega ou prestação | Há prova de que o bem entrou ou o serviço foi prestado? | Entrada no almoxarifado, tombamento, relatório de execução, registro de produção, fotos datadas | Lei 4.320/1964, art. 63, § 2º, III | ENTREGA_N | sem comprovação |
| Estágios | Empenho, liquidação e pagamento na ordem e nos valores? | Datas e valores dos três estágios | Lei 4.320/1964, arts. 60, 62 e 63 | PAGO_SEM_LIQ, LIQ_MAIOR_EMP, NF_ANTES_EMP, LIQ_ANTES_EMP, PAG_ANTES_LIQ | irregularidade formal |
| Preço | O unitário cabe na referência do mesmo item e mês? | Referência datada com fonte (seção 5) | Lei 14.133/2021, art. 23; Lei 13.979/2020, art. 4º-E, § 3º | SOBREPRECO / PRECO_ACIMA_TOL / SEM_REFERENCIA | sobrepreço a apurar / regular |
| Fracionamento | Há empenhos encadeados do mesmo credor? | Datas de empenho por CNPJ (seção 4) | Lei 14.133/2021, art. 75, § 1º | FRACIONAMENTO | irregularidade formal |
| Fornecedor novo | Constituído há menos dias que o parâmetro? | Cadastro CNPJ com data de abertura | Devida diligência; capacidade operacional | FORNECEDOR_NOVO | irregularidade formal |
| Fornecedor sancionado | Consta de CEIS ou CNEP na consulta? | Consulta datada | Lei 14.133/2021, art. 156; Lei 13.979/2020, art. 4º, § 3º | FORNECEDOR_SANCIONADO | irregularidade formal |

Testes de comprovação (NF, atesto, entrega) só se aplicam à despesa liquidada ou paga; empenho não executado recebe a observação NAO_EXECUTADA e só os testes de processo e fornecedor.

---

## 2. Regras de classificação e ordem de severidade

A classe de cada despesa é o achado mais grave presente, nesta ordem:

1. Desvio de finalidade: aderência N. Base de quantificação: valor pago.
2. Sem comprovação: entrega N ou nota fiscal ausente em despesa liquidada ou paga. Base: valor pago.
3. Sobrepreço a apurar: variação acima da tolerância declarada. Base: (unitário menos referência) vezes quantidade.
4. Aderência a esclarecer: aderência D. Sem base; exige justificativa do ente.
5. Irregularidade formal: qualquer achado de processo, estágio, fracionamento ou fornecedor. Sem base.
6. Regular: nenhum achado, ou apenas observação.

Os achados por tipo são não exclusivos: uma despesa com sobrepreço e sem pesquisa de preços conta nos dois tipos, mas em uma única classe. Totais por classe fecham com o universo (sanidade); totais por tipo não somam ao universo, e o laudo diz isso.

Por que "a apurar" no sobrepreço: a diferença contra a referência é indício, não dano líquido; o ente pode demonstrar oscilação de mercado (Lei 13.979/2020, art. 4º-E, § 3º) ou especificação distinta. O laudo apresenta o valor como "diferença contra a referência", e o juízo decide.

---

## 3. Red flags e diligência adicional

| Sinal | Como detectar | O que pedir ou fazer | Norma de apoio |
|---|---|---|---|
| Nota fiscal ou liquidação anterior ao empenho | Datas no CSV (NF_ANTES_EMP, LIQ_ANTES_EMP) | Processo completo; conferir se houve "empenho de regularização" | Lei 4.320/1964, art. 60 |
| Pagamento sem liquidação | PAGO_SEM_LIQ | Documentos da liquidação; ordem de pagamento | Lei 4.320/1964, arts. 62 e 63 |
| Liquidação acima do empenho | LIQ_MAIOR_EMP | Reforço de empenho; justificativa | Lei 4.320/1964, art. 60 |
| Objeto estranho à covid ou à saúde | ADERENCIA_N / D | Justificativa, plano de contingência, portaria da fonte | LRF, art. 8º, parágrafo único; LC 141/2012, art. 4º |
| Despesa em fonte sem receita | Conciliação | Razão e extrato da fonte; reclassificação | LRF, art. 50, I |
| Pagamento acima do recebido na fonte | Alerta por fonte | Extrato da conta; origem do recurso que cobriu | LRF, art. 8º, parágrafo único |
| Empenhos encadeados do mesmo credor | FRACIONAMENTO | Processos; objeto e modalidade; somatório no exercício | Lei 14.133/2021, art. 75, § 1º |
| Fornecedor constituído há pouco | FORNECEDOR_NOVO | Cadastro CNPJ, CNAE, capital, endereço, quadro societário | Devida diligência |
| Fornecedor sancionado | FORNECEDOR_SANCIONADO | Consulta com data; alcance e vigência da sanção; se único fornecedor | Lei 14.133/2021, art. 156; Lei 13.979/2020, art. 4º, § 3º |
| Sócio servidor ou parente de gestor | Cruzar quadro societário com folha e declarações | Declaração do ente; consulta | Lei 14.133/2021, art. 14 `[A VERIFICAR o inciso]` |
| CNAE incompatível com o objeto | Cadastro CNPJ | Justificativa da escolha (Lei 14.133/2021, art. 72, VI) | |
| Preço muito acima da referência | SOBREPRECO | Especificação, quantidade, mês, estimativa do processo, justificativa de oscilação | Lei 13.979/2020, art. 4º-E, § 3º |
| Contrato prorrogado além do permitido | Datas de vigência e aditivos | Aditivos e justificativas | Lei 13.979/2020, art. 4º-H; Lei 14.133/2021, art. 75, VIII |
| Entrega sem destino rastreável | ENTREGA_N com NF presente | Almoxarifado, tombamento, distribuição às unidades | Lei 4.320/1964, art. 63, § 2º |
| Sem publicação da contratação | D17 ausente | Tela do sítio oficial e do PNCP | Lei 13.979/2020, art. 4º, § 2º; Lei 14.133/2021, art. 72, parágrafo único |
| Devolução não registrada ou saldo não devolvido | Conciliação (devoluções, saldo final) | GRU; reprogramação aprovada | Portaria da fonte `[A VERIFICAR]` |

Red flag não é achado: vira achado quando a diligência adicional confirma o fato, e vira "limitação" quando a diligência não é atendida.

---

## 4. Fracionamento: método

1. Agrupar empenhos por CNPJ (ou credor, quando sem CNPJ).
2. Ordenar por data de empenho; encadear os que distam até a janela declarada (padrão trinta dias) do anterior do grupo.
3. Reportar grupos com dois ou mais empenhos: empenhos, datas, dias entre o primeiro e o último, modalidades, objetos e somatório.
4. Conferir manualmente: objeto da mesma natureza, modalidade adotada e o somatório no exercício contra o limite da dispensa por valor vigente na data (Lei 14.133/2021, art. 75, I, II e § 1º; valor atualizado por decreto `[A VERIFICAR o valor vigente na data do ato]`).

Em emergência covid, compras repetidas ao mesmo fornecedor podem refletir a escassez e a entrega parcelada; o achado descreve o encadeamento e remete ao processo, sem presumir burla.

---

## 5. Preço de referência e sobrepreço: método

1. Obter a referência por item, especificação, unidade e mês da contratação, pela skill `licitacoes-contratos` (painel de preços, contratações similares, mediana após saneamento), com fonte e data anexadas. Em 2020 os preços de EPI e insumos oscilaram semana a semana; a referência precisa ser do mesmo mês ou declarar o ajuste.
2. Informar `preco_referencia` e `quantidade` no CSV; o script calcula a variação percentual e, acima da tolerância declarada (padrão vinte por cento), a base de sobrepreço.
3. Distinguir sobrepreço (estimativa ou contratação acima do mercado) de superfaturamento (pagamento efetivo acima), e descrever qual dos dois o dado permite.
4. Sem referência, o teste não roda; o laudo registra "sem referência de preço para o item" e não arbitra.

A tolerância é premissa declarada; não há percentual normativo. Justificativa de oscilação no processo (Lei 13.979/2020, art. 4º-E, § 3º) é transcrita no achado.

---

## 6. Fornecedor: constituição, sanção, quadro societário

| Verificação | Fonte | Registro |
|---|---|---|
| Data de constituição e dias até o empenho | Cadastro CNPJ | `data_constituicao_fornecedor`; sinal abaixo do parâmetro declarado (padrão cento e oitenta dias) |
| CNAE compatível com o objeto | Cadastro CNPJ | Observação na matriz |
| Sanção vigente (CEIS, CNEP) na data da consulta | Portal da Transparência via `licitacoes-contratos` | `sancao_ceis`; alcance (ente sancionador ou nacional) e vigência |
| Quadro societário x servidores e gestores | Cadastro CNPJ, declaração do ente, folha | Red flag de sócio servidor |
| Endereço, capital social, porte | Cadastro CNPJ | Capacidade operacional para o volume contratado |

Nenhum desses fatos, isolado, prova irregularidade material; juntos, orientam a amostra e a diligência. O laudo descreve e não adjetiva ("empresa de fachada" é conclusão, não fato).

---

## 7. Quantificação

| Classe | Base | Apresentação no laudo |
|---|---|---|
| Desvio de finalidade | Valor pago | "Aplicado em objeto estranho à fonte", por fonte e exercício |
| Sem comprovação | Valor pago | "Sem comprovação nos autos", por fonte e exercício; pode mudar com a juntada |
| Sobrepreço a apurar | (Unitário menos referência) vezes quantidade | "Diferença contra a referência", com fonte e mês da referência |
| Aderência a esclarecer | Nenhuma | Lista de empenhos e valores, sem somar à base |
| Irregularidade formal | Nenhuma | Lista de empenhos e valores, sem somar à base |

Valores nominais nas datas de pagamento. Atualização e juros pelo critério que o juízo fixar, em `atualizacao-monetaria`. Devoluções já realizadas ao repassador são abatidas da fonte na conciliação e mencionadas na quantificação quando se referirem ao mesmo objeto.

---

## 8. Redação do achado

Estrutura fixa em quatro partes:

1. Fato: o que o documento mostra (empenho, data, credor, objeto, valor, estágio).
2. Evidência: documento e folha, ou ausência do documento com a cronologia do pedido.
3. Norma contábil ou orçamentária: o dispositivo que exige o que falta ou veda o que ocorreu.
4. Efeito: a classe, a base de quantificação e o que mudaria com documento novo.

Exemplo de achado material:

> Achado 4. O empenho E-2020/0170, de 10/06/2020 (R$ 120.000,00, fonte LC173-SAUDE), à Zeta Locação de Equipamentos Ltda., objeto "locação de 10 ventiladores pulmonares por seis meses", foi liquidado em 15/12/2020 e pago em 22/12/2020 com a NF 501. Não há nos autos termo de entrega, registro de instalação nas unidades ou relatório de uso dos equipamentos (D09 e D10 requeridos em 15/09/2026, pendentes). A liquidação exige comprovante da prestação efetiva do serviço (Lei 4.320/1964, art. 63, § 2º, III). Classe: sem comprovação; base de quantificação R$ 120.000,00, que se altera com a juntada dos registros de uso.

Exemplo de achado formal:

> Achado 7. Os empenhos E-2020/0130 (15/04/2020, R$ 18.000,00) e E-2020/0142 (05/05/2020, R$ 17.500,00), ambos por dispensa, à Gama Serviços de Limpeza Ltda., objeto "sanitização das unidades básicas de saúde" de abril e de maio, distam vinte dias e somam R$ 35.500,00. O processo 2020.0060 não contém contrato nem atesto, e o pagamento de 20/04/2020 não tem liquidação registrada (Lei 4.320/1964, arts. 62 e 63). Classe: irregularidade formal; sem base de quantificação. O enquadramento do encadeamento como fracionamento (Lei 14.133/2021, art. 75, § 1º) é matéria do juízo.

Palavras que não entram no achado: dolo, má-fé, fraude, desvio de dinheiro, empresa de fachada, conluio, superfaturamento (salvo com pagamento efetivo acima do mercado demonstrado).

---

## 9. Erros que derrubam o laudo

1. Testar nota fiscal antes de fechar a fonte: o assistente técnico mostra um extrato e a conciliação cai.
2. Somar achados não exclusivos como se fossem dano: uma despesa, uma classe, uma base.
3. Sobrepreço sem referência do mesmo item e mês, ou com referência de 2023 para compra de abril de 2020.
4. Chamar de fracionamento a entrega parcelada de um único processo.
5. Tratar documento não fornecido como prova de desvio, ou o contrário, presumir a entrega.
6. Citar portaria GM/MS de memória: o número errado invalida a fonte inteira.
7. Qualificar: "houve improbidade", "o gestor agiu com dolo". É do juízo.
