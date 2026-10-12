---
name: pericia-prestacao-contas-estoque
description: "Calcular e periciar o saldo da prestação de contas da venda do estoque transferido em cessão de quotas ou trespasse (CPC, arts. 550 a 553), quando o comprador deve repassar ao vendedor a venda do estoque abatidos os impostos. Usar quando: (1) delimitar o estoque na data-base por inventário, balancete ou Bloco H; (2) atribuir cada venda ao estoque antigo ou ao novo pelo PEPS; (3) apurar ICMS, PIS, COFINS, DAS, IRPJ e CSLL sobre essa receita; (4) ler a cláusula abatidos os impostos em cenários; (5) conciliar repasses e compensações com o devido; (6) apurar saldo credor ou devedor em forma mercantil (CPC, arts. 551 e 552); (7) elaborar laudo, parecer ou quesitos. Acionar ao mencionar: prestação de contas, exigir contas, venda do estoque, estoque transferido, trespasse, cessão de quotas, repasse do estoque, abatidos os impostos, PEPS, Bloco H, o réu diz que repassou tudo, não recebi a venda do estoque. COMPLEMENTAR a apuracao-haveres: use ESTA para o repasse do estoque vendido; use aquela para a quota do sócio."
metadata:
  version: "1.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Perícia contábil na prestação de contas da venda do estoque transferido

Versão 1.0.0 (12/09/2026).

## Escopo

Perícia contábil na segunda fase da ação de exigir contas (CPC, arts. 550 a 553) decorrente de venda de sociedade ou de estabelecimento (cessão de quotas ou trespasse, CC, arts. 1.142 a 1.149) em que o comprador ficou obrigado a repassar ao vendedor o produto da venda do estoque preexistente, líquido de tributos. A skill delimita o estoque transferido na data-base, rastreia as vendas desse estoque pelo método PEPS, apura os tributos incidentes sobre essa receita conforme o regime tributário e a cláusula, concilia os repasses efetivamente feitos e apura o saldo credor ou devedor em forma mercantil (CPC, arts. 551 e 552). Papel padrão: perito do juízo; variante para assistente técnico de qualquer das partes.

Fora de escopo: liquidação da quota do sócio que se retira (`apuracao-haveres`), redação e análise de cláusulas do contrato (`contrato-social`), extração massiva de extratos bancários (`analise-extratos-forense`, usada como apoio na conciliação), atualização monetária e juros do saldo (`atualizacao-monetaria`), avaliação da empresa (`valuation`) e prestação de contas condominial (`pericia-prestacao-contas-condominio`).

## Princípio reitor

Prestação de contas não se julga por narrativa: julga-se por reconciliação de três conjuntos que precisam fechar entre si, ao centavo e com documento: o estoque que existia na data-base, o que dele foi vendido e por quanto, e o que foi repassado. Quem administra bens alheios, como o comprador quanto ao estoque do vendedor, tem o dever de apresentar as contas na forma adequada, com receitas, despesas e documentos justificativos (CPC, art. 551; CC, art. 668). Laudos neste domínio quebram por quatro causas: estoque antigo misturado com compras novas sem critério de ordem de saída, "impostos" abatidos sem dizer quais, repasses somados pelo total da planilha do réu sem conferência documento a documento, e lacuna documental convertida em zero ou no valor pedido pelo autor.

A skill elimina as quatro por construção. O script 1 atribui cada venda ao lote antigo ou ao novo pelo PEPS, item a item, com teste de sanidade que falha se a atribuição exceder o inventário. O script 2 só aceita alíquota acompanhada de fonte e entrega a leitura restritiva e a ampla da cláusula como cenários numerados. O script 3 classifica cada repasse (comprovado, sem comprovante, fora do contrato, duplicidade) antes de somar. E a lacuna vira cenário declarado, com o ônus apontado (CPC, art. 373, § 1º) e a diferença quantificada, porque decidir a consequência da lacuna é do juízo (CPC, art. 400), não do perito.

## Workflow principal

```
1. PERÍMETRO     -> contrato (cláusula do estoque, base, prazo, compensações), data-base,
                    documentos de cada parte (references/roteiro-documental-e-quesitos.md, seções 1 a 4)
2. ESTOQUE       -> inventário assinado, H010 ou reconstrução com ressalva
                    (references/metodo-peps-tributos-e-sped.md, seção 2)
3. ATRIBUIÇÃO    -> scripts/peps_estoque_transferido.py: receita bruta do estoque antigo por mês
4. TRIBUTOS      -> scripts/tributos_sobre_receita.py: cenário base (leitura A) e amplo (leitura B)
5. CONCILIAÇÃO   -> scripts/conciliacao_repasses.py: classificação, imputação, cronologia, saldo
6. CENÁRIOS      -> base, estrito e amplo; diferença entre leituras da cláusula
7. ATUALIZAÇÃO   -> atualizacao-monetaria (regime civil) com parcelas_para_atualizacao do script 3
8. DELIVERABLE   -> laudo ou parecer em forma mercantil (assets/template_laudo.md) + quesitos
```

Executar as etapas 3 a 5 exclusivamente em Python e encadear o JSON de cada script no seguinte. Atribuição PEPS de dezenas de itens e centenas de notas feita à mão não é auditável, e a impugnação específica do art. 550, § 3º, exige que cada lançamento seja localizável.

## 1. Perímetro contratual e data-base

Antes de qualquer conta, transcrever literalmente a cláusula do estoque e fixar quatro parâmetros, porque cada um muda o resultado:

| Parâmetro | Pergunta | Efeito na apuração |
|---|---|---|
| Base do repasse | Valor da venda, valor líquido, ou lucro? | Define se o CMV entra (só se a cláusula falar em lucro) |
| O que são "impostos" | Tributos sobre a receita, ou também IRPJ e CSLL? | Cenário base (leitura A) versus amplo (leitura B) |
| Prazo de repasse | Dias após o mês da venda, ou outro marco? | Vencimento de cada parcela na lista para atualização |
| Compensações admitidas | Devoluções, despesas de venda, dívidas do vendedor? | Quais abatimentos entram no cenário base |

A data-base é a do contrato, da averbação na Junta (CC, art. 1.144) ou do inventário, nesta ordem de preferência quando divergirem; a escolha vai na memória. Em cessão de quotas a pessoa jurídica é a mesma e o regime tributário é o dela; em trespasse o regime é o do adquirente e a transferência gera nota de saída do alienante. Documentos a requisitar de cada parte, termo de diligência e tratamento da recusa de exibição (CPC, arts. 396 a 400; CC, art. 1.191): `references/roteiro-documental-e-quesitos.md`.

## 2. Estoque transferido e atribuição PEPS

```bash
python3 scripts/peps_estoque_transferido.py --inventario assets/exemplo_inventario.csv \
  --compras assets/exemplo_compras.csv --vendas assets/exemplo_vendas.csv \
  --data-base 31/03/2025 --saida peps.json --csv atribuicao.csv --md peps.md
```

Hierarquia de fontes do inventário: assinado pelas partes; registro H010 do SPED Fiscal na data-base; rolagem item a item a partir do último H010 com as notas de entrada e saída; balancete apenas como teste de ordem de grandeza. Sem inventário assinado, o laudo apresenta o estoque como cenário "reconstruído" com a ressalva padrão da seção 5 do roteiro documental, e nunca como fato.

O script monta uma camada por item com o inventário, acrescenta uma camada por compra posterior e consome as camadas na ordem a cada venda (PEPS). Regras fixas, declaradas na saída: movimentos com data igual ou anterior à data-base são ignorados e listados (o inventário já os reflete); no mesmo dia a compra é processada antes da venda; quantidade vendida além das camadas é "sem lastro" e nunca redistribuída. Saída: receita bruta do estoque antigo por mês e por item, CMV do estoque antigo, remanescente a custo, receita de estoque novo (fora das contas) e alertas. Teste de sanidade embutido: a atribuição ao estoque antigo nunca excede o inventário e a soma antigo + novo + sem lastro é igual à quantidade vendida, venda a venda; falha de sanidade aborta a execução.

Por que PEPS e não custo médio: a pergunta é física ("quais unidades eram do vendedor"), não de custeio; o custo médio dilui o lote antigo e nunca o esgota; o UEPS não é admitido pela NBC TG 16 e esvaziaria a cláusula. Identificação específica prevalece quando existir lote ou série. Detalhes e sensibilidade: `references/metodo-peps-tributos-e-sped.md`, seção 1.

## 3. Tributos sobre a receita e leitura da cláusula

```bash
python3 scripts/tributos_sobre_receita.py --receitas peps.json --regime presumido \
  --parametros assets/exemplo_parametros_tributos.json --cenario amplo --saida tributos_amplo.json --md tributos.md
python3 scripts/tributos_sobre_receita.py --receitas assets/exemplo_receitas_mensais.csv --regime simples \
  --parametros assets/exemplo_parametros_simples.json --saida tributos_simples.json
```

| Regime | Cenário base (leitura A: tributos sobre a receita) | Cenário amplo (leitura B) | Parâmetros obrigatórios por arquivo |
|---|---|---|---|
| Simples Nacional | DAS pela alíquota efetiva do PGDAS-D de cada mês, ou calculada por RBT12 e faixas (LC 123/2006, art. 18, § 1º-A) | Igual ao base: o DAS já contém IRPJ e CSLL (art. 13) | Alíquota efetiva ou RBT12 e faixas, com fonte |
| Lucro Presumido | ICMS (por arquivo), PIS 0,65% (Lei 9.715/1998, art. 8º, I), COFINS 3% (Lei 9.718/1998, art. 8º) | IRPJ 8% x 15% mais adicional de 10% pelo método declarado; CSLL 12% x 9% (Lei 9.249/1995, arts. 15, 3º e 20) | ICMS com fonte; método do adicional com justificativa |
| Lucro Real | ICMS, PIS e COFINS por alíquota efetiva informada | IRPJ e CSLL por alíquota efetiva da apuração | Tudo por arquivo; nenhum padrão embutido |

Rodar também com `--cenario base` (leitura A) e gravar os dois JSON. O script embute como padrão apenas alíquotas de lei federal consolidada (PIS, COFINS, presunções e alíquotas de IRPJ e CSLL) e exige o campo `fonte` em todo bloco; ICMS, DAS e faixas do Simples entram sempre pelo arquivo, marcados `[A VERIFICAR]` até a conferência no RICMS da UF e no Anexo do ano-calendário. Cada tributo mensal é apurado em centavos, como no documento de arrecadação, para que o quadro feche. A leitura A é o cenário base porque é a que menos reescreve o contrato na segunda fase (STJ, Tema 908); a leitura B vai ao laudo com o valor da diferença, e a leitura C (receita líquida contábil, DL 1.598/1977, art. 12, § 1º) se obtém com devoluções no script 3 e descontos incondicionais já no preço do CSV. Substituição tributária, ICMS por dentro e CPP dentro do DAS: `references/metodo-peps-tributos-e-sped.md`, seções 5 e 6.

## 4. Conciliação dos repasses e saldo

```bash
python3 scripts/conciliacao_repasses.py --devido tributos_amplo.json \
  --repasses assets/exemplo_repasses.csv --compensacoes assets/exemplo_compensacoes.csv \
  --prazo-dias 30 --saida conciliacao.json --md conciliacao.md --csv cronologia.csv
```

Cada item alegado pelo réu é classificado antes de somar:

| Classe | Critério | Cenário em que entra |
|---|---|---|
| Admitido | Comprovante presente, previsto no contrato, sem duplicidade | base, estrito (repasses) e amplo |
| Sem comprovante | Campo `documento` vazio | só amplo |
| Fora do contrato | `aceito_pelo_contrato` ou `previsto_no_contrato` = N | só amplo |
| Duplicidade comprovada | Mesmo documento repetido | nenhum |
| Duplicidade provável | Mesma data e valor, documento distinto ou ausente | só amplo, com alerta |

Os itens admitidos são imputados ao mês mais antigo com saldo em aberto (CC, arts. 352 a 355), e a saída traz cronologia devido x repassado com saldo acumulado, saldo por mês com situação (quitado, parcial, em aberto), saldo final nos três cenários com indicação do credor, listas de itens sem comprovante, fora do contrato e em duplicidade, quadro em forma mercantil e a lista `parcelas_para_atualizacao` (devido no vencimento com sinal positivo, repasses na data com sinal negativo) para a skill `atualizacao-monetaria`. Sanidade: saldo final = devido menos admitidos; soma das imputações = total admitido; último saldo da cronologia = saldo final; ordem estrito maior ou igual a base maior ou igual a amplo.

Compensação não prevista no contrato nunca entra no cenário base: admiti-la é decisão do juízo, e a segunda fase apura o saldo nos termos do contrato (STJ, Tema 908). O perito quantifica o efeito no cenário amplo e para por aí (CPC, art. 473, § 2º).

## 5. Laudo em forma mercantil, cenários e atualização

O quadro do art. 551 do CPC parte da receita bruta, deduz os tributos, chega à receita líquida devida, abate compensações admitidas e repasses comprovados, e termina no saldo com data e credor. Três cenários acompanham o quadro: base (sustentado pelo perito), estrito (só repasses bancários comprovados; tese do vendedor) e amplo (tudo o que o réu alega, exceto duplicidade de comprovante; tese do comprador). A diferença entre leituras A e B da cláusula vai em linha própria. Atualização monetária e juros: executar `atualizacao-monetaria` no regime civil com `parcelas_para_atualizacao`; o termo inicial (data de cada repasse omitido, citação ou sentença) é pendência jurídica e entra como premissa declarada. Verificar o exame dos livros do comprador dentro do limite das transações entre os litigantes (STF, Súmula 260): vendas de estoque novo entram só para a atribuição PEPS e não são valoradas.

## 6. Variante: assistente técnico

O assistente do vendedor concentra a crítica em três pontos: inventário subavaliado ou item omitido (vendas sem lastro do script 1 são o indício), tributos abatidos além da leitura A sem cláusula, e repasses sem comprovante ou em duplicidade. O assistente do comprador concentra em: itens do inventário inexistentes ou invendáveis, devoluções e descontos incondicionais não deduzidos, alíquota efetiva real do regime (inclusive adicional de IRPJ) e repasses por meios não bancários documentados. Em ambos os casos a memória de cálculo é a mesma dos scripts; mudam as premissas declaradas, nunca o método. Roteiro de quesitos por parte: `references/fundamentacao-legal.md`, seção 7.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler contrato, inventário, SPED (TXT), XML e comprovantes antes de montar os CSV; conferir se o PDF do contrato tem camada de texto |
| `bash` | Executar os três scripts em Python e encadear o JSON de um na entrada do seguinte; extrair registros do SPED com script simples |
| `create_file` | Gravar os CSV de entrada, os JSON e Markdown de saída e o laudo em `/mnt/user-data/outputs` |
| `web_search` | Conferir RICMS da UF, Anexo do Simples do ano-calendário, redação vigente de artigo e situação de Tema antes de citar; nunca para substituir documento dos autos |

| Skill complementar | Quando acionar |
|---|---|
| `atualizacao-monetaria` | Atualizar o saldo e calcular juros a partir de `parcelas_para_atualizacao`, regime civil |
| `analise-extratos-forense` | Extrair e cruzar extratos bancários extensos das partes para localizar repasses e vendas em dinheiro |
| `apuracao-haveres` | Quando a controvérsia envolver também a liquidação da quota do sócio retirante |
| `contrato-social` | Análise de cláusula ambígua do contrato de venda antes de fixar as leituras A e B |
| `chelfo-docx-brand` | Conversão do laudo ou parecer em `.docx` no padrão institucional, sob pedido explícito |
| `chelfo-skill-forge` | Qualquer manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/peps_estoque_transferido.py` | Atribui cada venda ao estoque antigo ou ao novo pelo PEPS; receita bruta do antigo por mês e por item; CMV; remanescente; alertas; sanidade | `python3 scripts/peps_estoque_transferido.py --inventario inv.csv --compras compras.csv --vendas vendas.csv --data-base 31/03/2025 --saida peps.json --csv atribuicao.csv --md peps.md` |
| `scripts/tributos_sobre_receita.py` | Tributos sobre a receita do estoque antigo por regime e cenário; receita líquida devida; alíquotas com fonte | `python3 scripts/tributos_sobre_receita.py --receitas peps.json --regime presumido --parametros parametros.json --cenario amplo --saida tributos.json --md tributos.md` |
| `scripts/conciliacao_repasses.py` | Classifica repasses e compensações, imputa, monta cronologia, saldo por mês, três cenários, quadro mercantil e parcelas para atualização | `python3 scripts/conciliacao_repasses.py --devido tributos.json --repasses repasses.csv --compensacoes compensacoes.csv --prazo-dias 30 --saida conciliacao.json --md conciliacao.md` |

Todos em Python 3.11 com biblioteca padrão, `Decimal` com ROUND_HALF_UP e arredondamento só na apresentação, números no padrão brasileiro ou técnico, datas em dd/mm/aaaa, saída JSON com `premissas`, `locale`, `arredondamento`, `sanidade` e `memoria`. Erro de validação sai com código 1 e mensagem `ERRO de validação:`. Exemplos de entrada: `assets/exemplo_inventario.csv`, `exemplo_compras.csv` e `exemplo_vendas.csv` (script 1); `exemplo_parametros_tributos.json`, `exemplo_parametros_simples.json` e `exemplo_receitas_mensais.csv` (script 2); `exemplo_repasses.csv` e `exemplo_compensacoes.csv` (script 3).

## Estrutura do output

Template completo, com exemplo preenchido a partir dos dados fictícios de `assets/`, em `assets/template_laudo.md`. Seções obrigatórias do laudo ou parecer:

1. Objeto e limites (o que é do juízo: validade da cláusula, licitude de compensação, consequência da recusa de exibição).
2. Quesitos de cada origem com remissão à seção da resposta.
3. Documentos examinados, com folha, origem e o que faltou.
4. Metodologia (PEPS, leituras da cláusula, classificação dos repasses, imputação).
5. Perímetro contratual e data-base, com a cláusula transcrita.
6. Estoque transferido e atribuição PEPS: quadro por item e por mês, alertas, sanidade.
7. Tributos sobre a receita e receita líquida devida, com alíquotas e fontes.
8. Conciliação dos repasses e quadro em forma mercantil (CPC, art. 551), fechando ao centavo com a cronologia.
9. Cenários base, estrito e amplo, com credor e diferença entre leituras A e B.
10. Respostas aos quesitos, uma a uma, com remissão ao quadro ou à memória.
11. Conclusão com saldo, data e credor por cenário.
12. Memória de cálculo e anexos (JSON, CSV e Markdown dos três scripts; relação de NF-e com chave de acesso).
13. Pendências de verificação.

Exemplo de quadro em forma mercantil (saída do script 3 com os exemplos de `assets/`, leitura B):

```
| Rubrica                                  |   | R$        |
|------------------------------------------|---|----------:|
| Receita bruta das vendas do estoque antigo| + | 44.730,00 |
| Tributos incidentes sobre essa receita   | - | 11.061,73 |
| Receita líquida devida ao vendedor       | = | 33.668,27 |
| Compensações previstas no contrato       | - |  2.500,00 |
| Repasses comprovados e admitidos         | - | 25.000,00 |
| Saldo final: credor do autor (vendedor)  | = |  6.168,27 |
```

Exemplo de resposta a quesito:

> Quesito 2 do autor: "O réu vendeu itens do estoque transferido antes de vender itens adquiridos depois da data-base? Como se demonstra?"
> Resposta: Sim, por força do método adotado. A atribuição seguiu o PEPS item a item (Anexo I): as 400 unidades de cimento do inventário de 31/03/2025 foram consumidas pelas NF 5001, 5003 e 5006 (150, 200 e 50 unidades), e só então as 300 unidades compradas pela NF 1201 de 10/04/2025 começaram a ser atribuídas às vendas (70 unidades da própria NF 5006 e 100 da NF 5013). A receita bruta do estoque antigo é de R$ 44.730,00 e a de estoque novo, fora das contas, de R$ 12.137,00. Critério diverso de ordem de saída exigiria cláusula contratual, que não existe, e esvaziaria a destinação do produto do estoque ao autor.

Exemplo de tratamento de lacuna documental:

> Quesito 5 do autor: "Os repasses alegados têm comprovante bancário? Há lançamentos em duplicidade?"
> Resposta: Três repasses têm comprovante (fls. 88, 90 e 97) e somam R$ 25.000,00. O lançamento de um segundo TED de R$ 8.000,00 em 16/06/2025 repete o comprovante da fl. 90 e foi excluído como duplicidade comprovada. O repasse de R$ 3.000,00 em dinheiro alegado para 20/07/2025 não tem recibo nem reflexo no extrato da autora: ficou fora do cenário base e integra apenas o cenário amplo (Anexo III, item 5). A consequência da falta do comprovante é matéria do juízo; o efeito dela no saldo é de R$ 3.000,00.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- CPC/2015: arts. 550 (titular do direito de exigir contas; § 3º impugnação específica; §§ 5º e 6º duas fases e perícia), 551 (forma adequada: receitas, despesas, documentos; § 2º saldo), 552 (sentença apura o saldo e é título executivo), 553 (contas de administradores), 373, I, II e § 1º (ônus e distribuição dinâmica), 396 a 400 (exibição e presunção), 417 e 418 (livros empresariais), 420 e 421 (exibição integral e parcial), 465, 469, 470, 473 e 477 (perícia).
- CC: arts. 1.142 a 1.149 (estabelecimento e trespasse), 1.190 e 1.191 (exibição de livros; gestão à conta de outrem), 668 (mandatário presta contas), 884 (enriquecimento sem causa), 352 a 355 (imputação do pagamento).
- CTN, art. 133 (responsabilidade do adquirente de estabelecimento pelos tributos até a data do ato).
- Lei 9.715/1998, art. 8º, I (PIS 0,65%); Lei 9.718/1998, art. 8º (COFINS 3%); Lei 9.249/1995, arts. 15, 3º e 20 (presunções, IRPJ e adicional, base da CSLL); Lei 7.689/1988, art. 3º (CSLL de 9%); LC 123/2006, arts. 13 e 18 (DAS e alíquota efetiva); DL 1.598/1977, art. 12 (receita bruta e líquida).
- NBC TG 16 (R2) (estoques: PEPS, média ponderada e identificação específica), NBC TP 01 (R1) e NBC PP 01 (R1).

Jurisprudência verificada em 12/09/2026 (somente esta; identificação completa e links em `references/fundamentacao-legal.md`, seção 2): STJ, REsp 1.117.614, Tema 449 (decadência do art. 26 do CDC não se aplica à prestação de contas); STJ, REsp 1.293.558, Tema 528 (no mútuo não há interesse de agir; aqui há, porque há administração de bem alheio); STJ, REsp 1.497.831, Tema 908 (a segunda fase não revisa encargos: apura o saldo nos termos do contrato); STF, Súmula 260 (exame de livros limitado às transações entre os litigantes); TJMG, AI 2619689-36.2025.8.13.0000; TJRS, AC 5048744-73.2023.8.21.0001; TJMT, AI 1010883-69.2024.8.11.0000; Enunciado 177 do FPPC (orientativos).

Protocolo antifabricação: alíquota de ICMS, faixa do Simples, alíquota efetiva do PGDAS-D, número de Tema, Súmula ou REsp fora da lista acima e redação literal de artigo exigem verificação em fonte oficial (planalto.gov.br, stj.jus.br, stf.jus.br, sefaz da UF, gov.br/receitafederal) na data do laudo. Sem verificação, marcar `[A VERIFICAR]` ao lado e listar na seção de pendências. Toda afirmação sensível ao tempo leva data de referência.

Pendências de verificação desta versão: precedente do STJ sobre trespasse e sucessão de estoque; Tema ou precedente do STJ sobre o termo inicial da correção do saldo em prestação de contas; prazo prescricional decenal da pretensão de exigir contas; Súmula 150 do STF; alíquotas de ICMS por UF; faixas do Simples do ano-calendário; inciso do art. 3º da Lei 7.689/1988; layout do Guia Prático da EFD; créditos de PIS e COFINS sobre estoque transferido em trespasse. Lista consolidada em `references/fundamentacao-legal.md`, seção 9.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | Normas com dispositivo, jurisprudência verificada com links, ônus da prova e exibição de livros, prescrição, limites do perito, roteiro de quesitos, pendências | Etapa 1, redação do laudo e resposta a quesitos |
| `references/metodo-peps-tributos-e-sped.md` | PEPS versus custo médio, hierarquia de fontes do inventário, registros do SPED e campos do XML, três leituras da cláusula, efeito do regime, exemplo numérico, armadilhas | Etapas 2, 3 e 4 |
| `references/roteiro-documental-e-quesitos.md` | Documentos por parte, ofícios, termo de diligência, reconstrução sem inventário assinado, amostragem de NF-e, quesitos suplementares, checklist | Etapas 1 e 2 e pré-entrega |
| `assets/template_laudo.md` | Template do laudo e do parecer com exemplo preenchido | Etapa 8 |
| `assets/exemplo_*.csv` e `assets/exemplo_*.json` | Schemas de entrada dos três scripts com dados fictícios | Etapas 3, 4 e 5 |

## Extensão e manutenção

Como estender esta skill sem quebrá-la:

1. Novo tributo ou novo regime: adicionar o bloco em `PADROES_PRESUMIDO` ou o ramo em `calcular()` de `scripts/tributos_sobre_receita.py`, sempre com exigência de `fonte`, e a linha na tabela da seção 3.
2. Novo critério de atribuição (identificação específica por lote ou série): acrescentar coluna `lote` nos CSV e uma etapa anterior ao PEPS em `processar()` de `scripts/peps_estoque_transferido.py`, mantendo os testes de sanidade.
3. Nova classe de item na conciliação (por exemplo, repasse condicionado a evento): adicionar o critério em `classificar()` de `scripts/conciliacao_repasses.py` e a linha na tabela da seção 4; a sanidade de ordem dos cenários precisa continuar a passar.
4. Novo precedente conferido: mover da seção 3 para a seção 2 de `references/fundamentacao-legal.md`, com identificação completa e data de conferência, e retirar da lista de pendências.
5. Versionamento SemVer: alíquota de lei consolidada ou tabela normativa é minor; mudança de contrato de saída dos scripts (chaves do JSON) é major.

Manutenção desta skill: acionar `chelfo-skill-forge`.
