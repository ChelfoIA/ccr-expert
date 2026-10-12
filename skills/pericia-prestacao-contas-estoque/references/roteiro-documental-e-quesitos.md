# Roteiro documental, diligência, reconstrução do estoque e quesitos

Referência: 12/09/2026. Este arquivo sustenta a etapa 1 do workflow (perímetro e requisição de documentos), a etapa 2 quando falta inventário assinado e a redação dos quesitos. Os quesitos das partes e do juízo estão em `references/fundamentacao-legal.md`, seção 7; aqui ficam os quesitos suplementares e os de esclarecimento.

## Sumário

1. Documentos a requisitar do autor (vendedor)
2. Documentos a requisitar do réu (comprador)
3. Documentos de terceiros e ofícios
4. Termo de diligência: modelo curto
5. Estoque sem inventário assinado: reconstrução com ressalva
6. Amostragem e conferência de NF-e
7. Quesitos suplementares e de esclarecimento
8. Checklist de pré-entrega

---

## 1. Documentos a requisitar do autor (vendedor)

| Nº | Documento | Para quê | Se faltar |
|---|---|---|---|
| 1 | Contrato de venda da sociedade ou de trespasse, com anexos e aditivos | Cláusula do estoque: base (bruta ou líquida), o que são "impostos", prazo de repasse, compensações admitidas, foro | Sem contrato escrito, a cláusula é provada por correspondência e prática; apontar como pendência jurídica |
| 2 | Inventário físico da data-base assinado pelas partes, ou anexo do contrato com a lista de itens | Estoque transferido por item, quantidade e custo | Reconstrução da seção 5 |
| 3 | Balancete ou balanço na data-base e Razão da conta Estoques | Teto de valor e teste de razoabilidade do inventário | Pedir ao contador da época |
| 4 | SPED Fiscal do ano da data-base, Bloco H (H005 e H010), se a transferência coincidir com 31/12 ou com mudança de regime | Inventário declarado ao fisco | Rolagem a partir do último H010 |
| 5 | XML das NF-e de entrada dos seis meses anteriores à data-base | Custo unitário e confirmação dos itens | SPED C170 de entrada |
| 6 | Extratos bancários do vendedor (pessoa física ou jurídica que recebeu os repasses) no período | Confirmar os repasses que o réu alega | Ofício ao banco |
| 7 | Correspondência, mensagens e planilhas trocadas sobre o repasse | Prática das partes quanto à leitura da cláusula | Sem efeito no cenário base |
| 8 | Notificações extrajudiciais e respostas | Datas de mora e de recusa | Registrar na cronologia |

## 2. Documentos a requisitar do réu (comprador)

| Nº | Documento | Para quê | Se faltar |
|---|---|---|---|
| 1 | SPED Fiscal (EFD ICMS/IPI) em TXT, do mês da data-base até o esgotamento do estoque antigo: Blocos 0, C, H e K | Universo de vendas e compras por item; estoque declarado | Requerer exibição (CPC, arts. 396 a 400; CC, art. 1.191) |
| 2 | XML das NF-e de saída e de entrada do mesmo período, com eventos | Base do CSV de vendas e de compras; cancelamentos e devoluções | Consulta por chave no portal da NF-e; ofício à SEFAZ |
| 3 | Livros Diário e Razão (contas Estoques, Vendas, Devoluções, Clientes, Caixa e Bancos) | Cruzamento receita escriturada x receita fiscal; lançamentos de repasse | Livros provam contra o autor deles (CPC, art. 417) |
| 4 | PGDAS-D e DAS (Simples) ou GIA/EFD, DCTF, DARF de PIS, COFINS, IRPJ e CSLL e ECF (Presumido ou Real) | Regime, alíquota efetiva e método do adicional | Alíquota por arquivo com fonte; sem comprovante, declarar a premissa |
| 5 | Comprovantes bancários de todos os repasses (PIX, TED, cheque compensado) e recibos assinados | Repasses comprovados | Repasse sem comprovante fica fora do cenário base |
| 6 | Documentos das compensações alegadas (NF de devolução, boletos pagos por conta do vendedor, notificações) | Classificar como prevista ou não no contrato | Compensação sem documento fica fora do base |
| 7 | Controle interno do estoque antigo (planilha, relatório do sistema, separação física) | Identificação específica quando existir | PEPS por item |
| 8 | Extratos bancários da empresa no período, limitados aos lançamentos de repasse e às vendas do estoque antigo (STF, Súmula 260) | Confirmar datas e valores | Ofício ao banco |

## 3. Documentos de terceiros e ofícios

- SEFAZ da UF: relação das NF-e emitidas e recebidas pelo CNPJ no período, quando o réu não exibe os XML.
- Instituição financeira: comprovantes de transferência identificados por número de documento, quando as partes divergem sobre a existência do repasse.
- Contador da sociedade na data-base: balancete, Razão e inventário contábil.
- Junta Comercial: averbação do trespasse ou da alteração contratual (CC, art. 1.144), para fixar a data-base quando o contrato é omisso.

## 4. Termo de diligência: modelo curto

> Termo de diligência nº [N]. Processo [0000000-00.0000.0.00.0000]. Perito [nome], CRC [registro]. Com fundamento nos arts. 473, § 3º, e 551, § 1º, do CPC, solicito à parte [ré/autora], no prazo de [10] dias, os documentos abaixo, em formato eletrônico original (TXT do SPED, XML das NF-e, OFX ou PDF pesquisável dos extratos): [lista numerada conforme as seções 1 e 2]. A falta de entrega será registrada no laudo com a indicação do seu efeito sobre a apuração (CPC, arts. 373, § 1º, e 400). Data e assinatura.

Registrar no laudo a data do termo, a data da resposta e o que foi entregue, documento a documento.

## 5. Estoque sem inventário assinado: reconstrução com ressalva

Quando não há inventário assinado, o perito reconstrói o estoque da data-base e o apresenta como cenário, nunca como fato incontroverso. Ordem de preferência:

1. Registro H010 com H005 na data-base: adotar como inventário, anotando que é declaração unilateral do contribuinte que prova contra ele (CPC, art. 417).
2. H010 em data anterior mais rolagem por item até a data-base: estoque na data-base = H010 anterior mais entradas (C170 de compra) menos saídas (C170 de venda) menos devoluções de compra mais devoluções de venda, por código de item. A rolagem é feita em planilha ou script e vai inteira para a memória.
3. Balancete na data-base (valor total da conta Estoques) mais composição percentual do último H010 disponível: distribuir o valor pelos itens na proporção do último inventário. Precisão baixa; só para teste de ordem de grandeza.
4. Preço de referência do inventário multiplicado pela quantidade transferida como estimativa de receita quando não há notas de saída: cenário de lacuna do réu.

Redação da ressalva (adaptar):

> A composição do estoque em [data-base] foi reconstruída a partir de [fonte], por não constar dos autos inventário assinado pelas partes. A reconstrução é apresentada como cenário "reconstruído" e tem a precisão da fonte utilizada; divergência posterior documentada por qualquer das partes altera a quantidade atribuída e, por consequência, a receita e o saldo. A lacuna documental é da parte [ré], que detinha o estoque e os livros (CPC, art. 373, § 1º).

Sinais de inventário inconsistente: quantidade negativa após a rolagem (compra não informada ou venda antes da data-base), custo unitário fora da faixa das notas de entrada, item sem movimento algum depois da data-base com saldo relevante (verificar perda, avaria ou venda sem nota), e valor total divergente do balancete em mais de 5%.

## 6. Amostragem e conferência de NF-e

- Até 500 documentos de saída no período: população integral, sem amostragem.
- Acima de 500: integral para os itens do inventário (a atribuição PEPS exige todos os movimentos desses itens) e amostragem estratificada por valor para os demais, usada só na conferência SPED x XML.
- Conferências mínimas: (a) soma de C170 por documento = C100; (b) total de C100 de saída do mês = Razão de Vendas = base da apuração fiscal; (c) toda NF-e cancelada excluída e toda carta de correção lida; (d) CFOP de venda filtrado (5.102, 6.102, 5.405 e correlatos, conferida a tabela vigente); (e) devoluções (1.202 e 2.202) casadas com a venda original.
- Divergência acima de 0,5% entre receita fiscal e contábil: explicar antes de rodar o script 1; divergência não explicada vai ao laudo como alerta.
- Registrar no laudo a chave de acesso das NF-e que compõem a receita do estoque antigo (anexo em CSV), para que a impugnação possa ser específica (CPC, art. 550, § 3º).

## 7. Quesitos suplementares e de esclarecimento

Quesitos suplementares (CPC, art. 469) que costumam surgir depois do laudo:

1. Considerado o inventário retificado apresentado pela parte [X] em [data], qual o novo saldo?
2. Adotada a leitura ampla da cláusula (IRPJ e CSLL), qual a diferença de saldo?
3. Admitida a compensação de [item] pelo juízo, qual o saldo resultante?
4. Qual o estoque antigo remanescente em poder do réu na data do laudo, e qual seu valor a custo e a preço de referência?
5. Qual a data de cada repasse omitido, para fins de termo inicial de atualização?

Respostas de esclarecimento (CPC, art. 477, § 2º): responder com remissão à memória e, se houver mudança de premissa, rodar os scripts de novo e anexar o novo JSON com a data; nunca corrigir número à mão.

## 8. Checklist de pré-entrega

1. Data-base declarada e fonte do inventário identificada (assinado, H010 ou reconstruído).
2. Movimentos anteriores à data-base listados como ignorados.
3. Sanidade dos três scripts com todos os testes "OK" e JSON anexado.
4. Alíquotas com campo `fonte` preenchido; ICMS e faixas do Simples marcados `[A VERIFICAR]` se não conferidos no RICMS e no Anexo do ano.
5. Cenários base, estrito e amplo com saldo e credor; leitura A e B da cláusula com a diferença.
6. Repasses sem comprovante, itens fora do contrato e duplicidades listados com id, data e valor.
7. Quadro em forma mercantil (CPC, art. 551) fechando ao centavo com a cronologia.
8. Quesitos respondidos um a um, com remissão ao quadro ou à memória.
9. Pendências de verificação consolidadas no fim do laudo.
10. Verificação tipográfica: padrão numérico brasileiro, sem travessão, acentuação correta.
