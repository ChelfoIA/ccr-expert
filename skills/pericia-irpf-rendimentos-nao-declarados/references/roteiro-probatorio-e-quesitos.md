# Roteiro probatório: documentação hábil e idônea, cruzamentos, tipos de lançamento e quesitos

Referência: 12/09/2026. Este arquivo orienta a leitura dos autos (etapa 1), a montagem da planilha (etapa 2) e a redação do laudo (etapa 7). A tabela de naturezas está em `references/natureza-dos-rendimentos.md`; a fundamentação, em `references/fundamentacao-legal.md`.

## Sumário

1. Leitura do auto e do processo administrativo: checklist
2. O que é documentação hábil e idônea
3. Cruzamentos obrigatórios
4. Roteiro por tipo de lançamento
5. Como redigir "prova insuficiente" sem opinar sobre boa-fé
6. Armadilhas do auto de infração
7. Técnica de resposta e quesitos por tipo de lançamento

---

## 1. Leitura do auto e do processo administrativo: checklist

| Item | Onde está | Para que serve |
|---|---|---|
| Base de cada infração (DIRF, depósitos, patrimônio) | Descrição dos fatos e enquadramento legal do auto | Define o roteiro da seção 4 |
| Anos-calendário e meses dos créditos | Demonstrativo de apuração | Tabela do ano; decadência por ano |
| Relação dos créditos imputados | Anexo do auto ou termo de intimação | Linhas do CSV; conferir se o auto já excluiu transferências e pequenos valores |
| Tabela usada e parcela a deduzir | Demonstrativo de apuração | Reproduzir no CSV da tabela, com fonte |
| Deduções admitidas | Demonstrativo | JSON de deduções |
| IRRF compensado e imposto da DIRPF original | Demonstrativo e DIRPF | `--irrf` e `--imposto-dirpf` |
| Percentual e fundamento da multa | Enquadramento legal | `--multa` e `--fundamento` |
| Data até a qual os juros foram calculados | Demonstrativo de multa e juros | `data_juros` do JSON do lançado |
| Termo de intimação para comprovar a origem e a resposta do contribuinte | PAF | Pressuposto do caput do art. 42; REsp 1.825.390 |
| Data da ciência do auto | AR, termo ou domicílio eletrônico | `--ciencia` |
| Contas examinadas e período dos extratos | Termo de início e RMF | Conferir se há conta não examinada ou extrato incompleto |

Transcrever tudo em `assets/exemplo_lancado.json` (modelo) antes de rodar os scripts. O que o auto afirma sem o documento correspondente entra no laudo como "informado pela autoridade fiscal, não localizado nos autos".

---

## 2. O que é documentação hábil e idônea

O caput do art. 42 não define a expressão; a prática administrativa e judicial a preenche com três exigências cumulativas, que o script traduz em critérios:

1. Individualização: o documento se refere àquele crédito (data e valor conciliáveis), não a um conjunto. Planilha do próprio contribuinte não é documento.
2. Contraparte identificada: quem pagou ou de onde veio consta do documento (nome e CPF ou CNPJ, ou conta de origem do titular).
3. Autenticidade e data: documento emitido por terceiro (banco, fonte pagadora, cartório, RFB, Justiça) ou documento particular com data certa (CPC, art. 409). Declaração particular produzida depois da intimação tem valor reduzido, e o laudo diz isso descrevendo a data, não adjetivando.

Hierarquia prática, da mais forte para a mais fraca: documento público ou judicial; documento de terceiro com dever de informar ao Fisco (DIRF, DIMOB, informe de rendimentos, e-Financeira); extrato bancário da contraparte; contrato registrado ou com firma reconhecida à época; contrato particular sem data certa; recibo ou declaração posterior; alegação.

---

## 3. Cruzamentos obrigatórios

| Cruzamento | Documento | O que confirma |
|---|---|---|
| DIRPF do contribuinte (bens, dívidas, rendimentos isentos, doações) | Declarações dos anos do caso e do anterior | Aplicação resgatada constava em 31/12 anterior; mútuo declarado como dívida; doação recebida na ficha própria; veículo baixado |
| DIRPF do doador, mutuante ou terceiro | Declaração da outra parte | Doação ou empréstimo constam da ficha correspondente; capacidade financeira |
| DIRF e informe de rendimentos | Fonte pagadora | Rendimento e IRRF por mês; crédito líquido igual a bruto menos IRRF |
| DIMOB | Administradora de imóveis | Aluguel por mês e locatário |
| e-Financeira | Instituição financeira | Totais mensais de créditos; conferir se o auto partiu deles ou dos extratos |
| ITCMD | Secretaria de Fazenda estadual | Doação ou herança declarada e paga ou isenta |
| DOI, matrícula, Renavam ou ATPV | Cartório ou Detran | Venda de bem com data e valor |
| Contabilidade e ECF da pessoa jurídica | Empresa pagadora | Lucro apurado que lastreia a distribuição; pró-labore registrado |
| Extrato da conta de origem | Banco | Transferência própria (débito de igual data e valor) |
| Extrato da corretora ou exchange | Corretora | Saque de criptoativos ou de renda variável |
| Consulta de restituição | RFB | Lote e valor da restituição |

Sem o cruzamento, a prova é no máximo parcial. O laudo lista, por crédito, qual cruzamento faltou, porque essa lista é o que o advogado precisa para completar a instrução e o que o juízo precisa para decidir sobre a suficiência.

---

## 4. Roteiro por tipo de lançamento

### 4.1. Rendimento informado por terceiro (DIRF, DIMOB, e-Financeira) e ausente da DIRPF

Natureza da imputação: rendimento de fonte identificada, não presunção. O roteiro é conferir a fonte, o valor bruto, o IRRF e o mês. Três verificações decidem o caso: o rendimento é mesmo do contribuinte (CPF correto, conta própria); o valor informado é bruto e o crédito é líquido (a diferença é o IRRF compensável); o auto compensou o IRRF e aplicou a tabela correta. Rendimento de fonte identificada entra como `ajuste` com `ja_declarado` = N, e a prova é a própria DIRF. O erro do auto que trata esse rendimento como omissão presumida do art. 42 e não compensa o IRRF é frequente e mensurável.

### 4.2. Depósitos de origem não comprovada (art. 42)

Roteiro: (1) conferir a intimação e se ela discriminou os créditos; (2) montar o CSV com todos os créditos imputados, inclusive os que o auto já excluiu, para reproduzir o lançamento; (3) classificar; (4) aplicar o § 3º e o § 6º; (5) recalcular nos dois modos; (6) confrontar. O quadro crédito a crédito é o núcleo do laudo. Nos casos com dezenas ou centenas de créditos, extrair e categorizar primeiro com `analise-extratos-forense` e importar o resultado no CSV.

### 4.3. Acréscimo patrimonial a descoberto

Natureza da imputação: variação patrimonial não coberta por rendimentos declarados, tributáveis, isentos ou não tributáveis. Método do fluxo de caixa mensal: para cada mês, origens (rendimentos recebidos, resgates, vendas, empréstimos recebidos, saldo inicial) contra aplicações (aquisições de bens, aplicações financeiras, pagamentos de dívidas, despesas comprovadas); o excesso de aplicações sobre origens em cada mês é o acréscimo a descoberto. Erros típicos do auto: considerar a aquisição pelo valor de mercado em vez do custo; ignorar o saldo de caixa de meses anteriores; contar duas vezes o mesmo recurso (resgate e aplicação); desconsiderar rendimento isento comprovado. A skill não traz script para o fluxo mensal (extensão prevista no SKILL.md); o perito monta a planilha e usa `classificar_rendimentos.py` para a prova das origens alegadas, alimentando `recalculo_irpf.py` com o excesso mensal no schema de `presumido_por_mes`.

---

## 5. Como redigir "prova insuficiente" sem opinar sobre boa-fé

O perito descreve o que o documento é, o que ele prova e o que falta. Modelos:

- "O crédito 7, de R$ 300.000,00 em 03/04/2023, vem acompanhado de declaração particular de doação datada de 03/04/2023 (fl. 70), sem registro, sem firma reconhecida, sem guia de ITCMD e sem a declaração de ajuste da doadora. O documento identifica a contraparte e coincide em data e valor; não há elemento que lhe confira data certa em relação a terceiros (CPC, art. 409) nem prova da capacidade financeira da doadora. Prova classificada como parcial; no cenário base o crédito permanece presumido."
- "O crédito 5, de R$ 25.000,00, é atribuído a mútuo de João da Silva. O contrato de fl. 60 não tem registro nem firma reconhecida; a dívida não consta da ficha de dívidas da DIRPF 2024 da autora, e não há extrato do mutuante nem comprovante de devolução. Prova parcial."
- "O crédito 12, de R$ 15.000,00 em dinheiro, não vem acompanhado de documento. Prova ausente."

Evitar: "a doação é verossímil", "não há indício de fraude", "a autora agiu de boa-fé", "trata-se de simulação". Essas expressões são juízo de valor e extrapolam o art. 473, § 2º, do CPC.

---

## 6. Armadilhas do auto de infração

| Armadilha | Como verificar | Efeito no recálculo |
|---|---|---|
| § 3º, II, não aplicado | Somar os presumidos até R$ 12.000,00 por ano | Exclusão integral quando a soma cabe em R$ 80.000,00 |
| Transferência própria tributada | Extrato da conta de origem | § 3º, I |
| Rendimento de fonte identificada tratado como presunção | DIRF ou DIMOB | Vai para o ajuste com IRRF compensável |
| Rendimento de aplicação já tributado na fonte incluído na base | Informe da instituição | Dupla tributação; exclusão |
| Mesmo recurso contado duas vezes (resgate e reaplicação; cheque devolvido) | Extrato completo | Estorno ou transferência |
| Conta conjunta não dividida | Cadastro da conta e DIRPF dos titulares | § 6º |
| Tabela ou parcela a deduzir errada | Reproduzir pela tabela oficial do ano | Diferença de imposto |
| IRRF não compensado | DIRF e DIRPF | Diferença de imposto |
| Juros com marco inicial ou série diversa | Selic implícita do auto contra a série oficial | "Não reproduzível em: ..." |
| Multa qualificada sem fundamento descrito | Enquadramento legal | `--fundamento` e `[A VERIFICAR]` da redação do art. 44 |
| Intimação genérica ou ausente | PAF | Fato a descrever; consequência jurídica do juízo |

---

## 7. Técnica de resposta e quesitos por tipo de lançamento

Técnica: responder primeiro com sim, não ou em parte; em seguida o número, com remissão ao quadro e ao anexo; por fim a limitação (documento faltante, item [A VERIFICAR], escolha que cabe ao juízo). Nunca responder com valor solto sem a seção que o produziu. Quando o quesito pede opinião jurídica (validade da intimação, nulidade, decadência), responder com o fato e a data e registrar que a qualificação é do juízo.

Quesitos adicionais por tipo de lançamento, para quem formula ou para quem responde:

Lançamento por DIRF ou DIMOB:
1. O rendimento informado pela fonte pagadora foi creditado em conta do contribuinte e em que valor líquido?
2. O imposto retido na fonte informado em DIRF foi compensado no lançamento?
3. O rendimento foi tributado como omissão presumida do art. 42 ou como rendimento de fonte identificada?

Lançamento por depósitos:
1. O termo de intimação discriminou os créditos por data e valor?
2. Quais créditos o auto já excluiu como transferências próprias ou pequeno valor, e quais deveria ter excluído?
3. Quais créditos foram desdobrados em principal e rendimento e com que documento?
4. Qual a diferença de imposto entre a apuração anual e a tributação mensal do § 4º?

Lançamento por acréscimo patrimonial:
1. O fluxo de caixa do auto considerou o saldo inicial e as origens isentas comprovadas?
2. As aquisições foram consideradas pelo custo ou pelo valor de mercado?
3. Há recurso contado duas vezes (resgate e reaplicação) no fluxo?

Impugnação de laudo ou parecer adverso: verificar se o documento adverso concilia data e valor por crédito, se aplica o § 2º às origens comprovadas, se apresenta os dois cenários e os dois modos, se a tabela e a Selic têm fonte e se cita precedente sem identificação completa. A ausência de qualquer desses itens é apontada como limitação metodológica, sem adjetivos.
