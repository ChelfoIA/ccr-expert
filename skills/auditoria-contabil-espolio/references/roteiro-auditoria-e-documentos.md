# Roteiro de auditoria e documentos do espólio

Referência: 12/09/2026. Este arquivo organiza a fase documental e os testes por categoria. A fundamentação está em `references/fundamentacao-legal.md`; o tratamento de imóveis, sociedades e bens no exterior está em `references/imoveis-empresas-e-exterior.md`.

## Sumário

1. Perímetro: o que é do espólio e desde quando
2. Documentos a requisitar no Brasil
3. Documentos a requisitar em Portugal
4. Transcrição dos movimentos para o CSV
5. Conta conjunta e despesas do inventariante misturadas
6. Testes por categoria
7. Amostragem e materialidade
8. Redação dos achados
9. Limitações declaradas

---

## 1. Perímetro: o que é do espólio e desde quando

O perímetro tem três eixos, e todos entram na seção de metodologia do laudo:

- Tempo: da abertura da sucessão (data do óbito, CC, art. 1.784) até a data de referência fixada no laudo (partilha homologada, última prestação de contas ou data da perícia). Movimento anterior ao óbito pertence ao autor da herança em vida e sai do fluxo; vai para a lista `fora_do_periodo` do script, porque pode revelar bem ou renda não declarada.
- Bens: tudo o que consta das primeiras e últimas declarações (CPC, arts. 620 e 636) mais o que a auditoria encontrar e não constar (candidato a sonegado, CC, arts. 1.992 a 1.996, qualificação do juízo). Inclui imóveis no Brasil e no exterior, contas, aplicações, veículos, participações societárias, créditos e direitos.
- Contas: as do falecido (que viram contas do espólio), as abertas em nome do espólio e as do inventariante ou de herdeiro quando usadas para receber ou pagar algo do espólio. Conta de uso misto entra com identificação explícita na coluna `conta` ("uso misto").

Regra de ouro: sem saldo inicial documentado na data do óbito não há conciliação. Requisitar o extrato que cubra a data do óbito, com saldo, de cada conta.

---

## 2. Documentos a requisitar no Brasil

| Grupo | Documento | Para quê | De quem |
|---|---|---|---|
| Sucessão | Certidão de óbito; testamento, se houver; certidão de casamento com regime de bens | Data de corte; meação; frações | Autos |
| Inventário | Primeiras e últimas declarações; termo de compromisso do inventariante; plano de partilha; alvarás e decisões de autorização (CPC, art. 619); decisões sobre uso de bem (CPC, art. 647, parágrafo único) | Perímetro de bens; o que foi autorizado; marco de eventual uso deferido | Autos |
| Bancário | Extratos de todas as contas do falecido e do espólio desde noventa dias antes do óbito até a data de referência, com saldo; extratos de aplicações; extratos de contas do inventariante usadas para o espólio | Fluxo de caixa; saldo inicial; conciliação | Inventariante; bancos por ofício (CPC, arts. 401 a 404) |
| Imóveis | Matrículas atualizadas; contratos de locação, aditivos e recibos; carnês de IPTU; boletos de condomínio; apólices; notas fiscais de reforma; laudo de avaliação ou anúncios equivalentes com data | Esperado x recebido; encargos; aluguel de mercado | Inventariante; administradora; cartório |
| Tributário | DIRPF do falecido do último exercício; declarações inicial, intermediárias e final de espólio; guias de ITCMD; DARF do carnê-leão sobre rendas do exterior `[A VERIFICAR a norma da RFB aplicável]` | Rendas declaradas x apuradas; tributos pagos pelo espólio | Inventariante; contador do espólio |
| Societário | Contrato social consolidado e alterações; balanços e DRE de cada exercício do período; atas ou deliberações de distribuição de lucros; razão das contas de sócios (lucros a distribuir, mútuos, conta corrente de sócios); folha de pró-labore; DIRPF dos sócios quanto a lucros recebidos; contratos de mútuo | Lucro devido x recebido pelo espólio; pró-labore; retiradas | Sociedade, por ofício; herdeiro-administrador |
| Dívidas | Habilitações de crédito; boletos e contratos de dívidas do falecido pagas no período; comprovantes de honorários e custas | Saídas autorizadas e sua natureza | Autos; inventariante |

---

## 3. Documentos a requisitar em Portugal

| Documento | Conteúdo | Para quê |
|---|---|---|
| Certidão permanente do registo predial | Titularidade, ônus e registros do prédio | Confirmar que o bem integra o acervo e em que fração |
| Caderneta predial urbana (Autoridade Tributária e Aduaneira) | Valor patrimonial tributário, localização, afetação | Base do IMI; identificação do imóvel |
| Contrato de arrendamento e recibos de renda eletrônicos | Renda mensal, prazo, inquilino | Esperado x recebido em euro |
| Notas de cobrança do IMI e comprovantes | Imposto municipal anual, em prestações | Despesa documentada do imóvel `[A VERIFICAR prazos e prestações]` |
| IRS Modelo 3 (anexo F) e notas de liquidação | Rendimentos prediais e imposto devido por não residente | Despesa documentada `[A VERIFICAR regras do não residente]` |
| Extratos da conta bancária portuguesa (IBAN) | Rendas creditadas, tributos e condomínio debitados | Fluxo em euro para `conversao_ptax.py` |
| Atas e recibos do condomínio | Quotas de condomínio e obras | Despesa documentada |
| Habilitação de herdeiros e participação do Imposto do Selo | Quem são os herdeiros perante a lei portuguesa; imposto sobre a transmissão | Contexto do bem no exterior `[A VERIFICAR]` |

A obtenção de documento em Portugal passa pelo inventariante, pelo advogado constituído em Portugal ou por cooperação jurídica internacional; o perito registra o pedido e o prazo como faz com qualquer terceiro.

---

## 4. Transcrição dos movimentos para o CSV

Layout de `assets/exemplo_movimentos.csv`: `data;conta;historico;valor;tipo;categoria;beneficiario;vinculo_beneficiario;autorizacao_judicial;documento;imovel_id;empresa_id`, com `moeda` opcional (só BRL; euro passa antes por `conversao_ptax.py`).

Regras de transcrição:

1. Um movimento por linha, no valor exato do extrato, positivo, com o sentido na coluna `tipo` (C ou D).
2. `categoria` escolhida pela natureza econômica, não pelo nome do favorecido: PIX a herdeiro é `retirada_herdeiro` mesmo que o histórico diga "reembolso", e a prova do reembolso vai na coluna `documento`.
3. `vinculo_beneficiario`: herdeiro, inventariante, terceiro ou espolio (transferência entre contas do próprio espólio). O inventariante que também é herdeiro entra como inventariante, porque a prestação de contas é dele.
4. `autorizacao_judicial`: S só com alvará ou decisão localizada nos autos, indicada em `documento`; vazio equivale a N.
5. `documento`: folha ou identificação do lastro. Sem lastro, deixar vazio; o script lista.
6. `imovel_id` e `empresa_id` ligam o movimento ao quadro de imóveis ou de sociedades, e permitem ao script separar os encargos do imóvel ocupado.
7. Transferência entre contas do espólio entra duas vezes (D numa conta, C na outra) com a categoria `transferencia_interna`; o script confere que fecham e as exclui dos totais operacionais.
8. Histórico abreviado do banco é complementado entre parênteses com o que o documento informa, sem apagar o texto original.

---

## 5. Conta conjunta e despesas do inventariante misturadas

Situação frequente: a conta do inventariante recebe aluguel do espólio e paga, na mesma conta, IPTU do espólio e supermercado da família. Procedimento:

1. Transcrever todos os movimentos da conta no período, marcando `conta` como "uso misto".
2. Classificar cada movimento pela natureza: o que é do espólio recebe categoria do espólio; o que é pessoal recebe `despesa_pessoal` quando pago com recursos que ingressaram do espólio, ou fica fora do CSV quando não há ingresso do espólio na conta no período.
3. Quando a origem dos recursos não puder ser separada (saldo misturado), aplicar e declarar um critério: primeiro, atribuição direta por histórico e documento; segundo, para o resíduo, proporção entre ingressos do espólio e ingressos próprios no mês; terceiro, cenário sem atribuição, com o valor apresentado como "não segregável". O critério é premissa do laudo, não norma.
4. Transferência do espólio para a conta mista é `transferencia_interna` com `vinculo_beneficiario` espolio; o que sai dela em favor do próprio inventariante sem documento vira `retirada_herdeiro` com vínculo inventariante.
5. Conta conjunta do falecido com terceiro (cônjuge, filho): o saldo na data do óbito entra pela fração que a prova indicar; sem prova, apresentar cenários (metade e integral) e remeter ao juízo.

---

## 6. Testes por categoria

| Categoria | Teste | Evidência que fecha | Achado típico |
|---|---|---|---|
| aluguel_recebido | Confronta com contrato e com o quadro de `rendimentos_imoveis.py`; competência x recebimento | Contrato, recibo, extrato | Mês sem ingresso; aluguel recebido em conta pessoal; reajuste não aplicado |
| dividendo | Confronta com ata de distribuição, balanço e DIRPF dos sócios | Ata, razão de lucros a distribuir | Distribuição desproporcional; lucro distribuído a outros e não ao espólio |
| venda_bem | Alvará, valor de avaliação, destino do produto | Alvará, escritura, recibo, extrato | Venda sem alvará; produto não ingressou; valor abaixo da avaliação |
| rendimento_financeiro | Extrato da aplicação | Extrato | Aplicação não declarada |
| itcmd, custas, honorarios | Guia, alvará ou decisão, contrato de honorários | Guia e decisão | Honorário pago sem contrato ou acima do autorizado |
| iptu, condominio, seguro, manutencao, tributo | Natureza de conservação (CPC, art. 619, IV); vínculo com imóvel do acervo; quem usa o imóvel | Guia, boleto, nota fiscal, apólice | Encargo de imóvel ocupado por herdeiro pago pelo espólio; reforma sem nota |
| divida_espolio | Alvará; habilitação do crédito; dívida do falecido ou do herdeiro | Alvará, contrato, boleto | Dívida pessoal de herdeiro paga pelo espólio; pagamento sem alvará |
| retirada_herdeiro | Decisão autorizando adiantamento; recibo; natureza | Decisão, recibo | Adiantamento sem decisão; valor diferente entre herdeiros |
| despesa_pessoal | Qualquer saída estranha ao espólio | Nenhuma válida | Viagem, cartão, mensalidade, veículo pessoal |
| transferencia_interna | Espelho na outra conta, mesmo valor e data próxima | Extratos das duas contas | Saída sem entrada espelho: conta fora do perímetro |
| outros | Reclassificar antes do laudo | Documento | Categoria desconhecida mascarando retirada |

---

## 7. Amostragem e materialidade

Censo para: toda saída em favor de herdeiro ou inventariante; toda saída sem documento; toda saída acima da materialidade declarada (sugestão: o maior entre 1% do total de saídas e um valor fixo declarado); toda venda de bem; todo movimento das contas do exterior. Amostra, por analogia com a NBC TA 530, só para despesas recorrentes de conservação (condomínio, IPTU, pequenas manutenções) quando ultrapassarem o volume que o prazo comporta, com o critério de seleção (sistemático por valor ou aleatório) declarado no laudo e a extrapolação limitada ao que a amostra permite. Achado em item amostrado estende o teste a toda a categoria.

---

## 8. Redação dos achados

Cada achado tem quatro partes, nesta ordem: fato (data, conta, valor, beneficiário, categoria), evidência (documento e folha, ou ausência com a cronologia do pedido), norma (dispositivo e, quando houver, precedente da lista verificada) e efeito (quadro em que o valor entra, valor nominal, o que mudaria com documento novo). Exemplo:

> Achado 3. Em 20/12/2024 saíram R$ 8.000,00 da conta do espólio no Banco do Brasil por PIX a Paula Alfa, herdeira (linha 51 do CSV). Não há nos autos recibo, decisão autorizando adiantamento de quinhão nem documento de despesa do espólio paga por ela; o pedido de esclarecimento de 15/08/2026 ficou sem resposta. Herdeiro em posse de valores da herança traz ao acervo o que recebeu (CC, art. 2.020); a saída em favor de herdeiro sem decisão consta da lista de exceções e integra a recomposição sugerida (quadro 7, R$ 8.000,00, nominal). Com decisão ou recibo juntados, o valor passa a adiantamento de quinhão, compensável na partilha, matéria do juízo.

Vocabulário: "sem documento nos autos", "sem autorização localizada", "estranha ao espólio", "em favor de", "não segregável". Nunca "desviou", "fraudou", "ocultou".

---

## 9. Limitações declaradas

O laudo registra, em seção própria e na conclusão: contas cujo extrato não veio ou veio parcial (período coberto); imóvel sem contrato ou sem fonte de mercado; sociedade sem balanço ou sem ata; série PTAX usada e sua fonte; critério de segregação de conta mista; marco inicial e fração adotados como premissa; valores nominais, sem atualização; itens `[A VERIFICAR]`. Para cada limitação, dizer o que mudaria no número se o documento viesse.
