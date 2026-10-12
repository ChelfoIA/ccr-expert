# Método: PEPS, leitura da cláusula "abatidos os impostos", regime tributário e SPED

Referência: 12/09/2026. Este arquivo sustenta as etapas 2 e 3 do workflow. As alíquotas aqui mencionadas são as de lei federal consolidada; ICMS, faixas do Simples e alíquota efetiva do PGDAS-D entram sempre por arquivo com fonte.

## Sumário

1. Por que PEPS para atribuir as vendas ao estoque antigo
2. Delimitação do estoque na data-base: hierarquia de fontes
3. SPED Fiscal: registros que interessam
4. NF-e: o que extrair do XML
5. A cláusula "abatidos os impostos": três leituras
6. Efeito do regime tributário do comprador
7. Exemplo numérico curto
8. Armadilhas recorrentes

---

## 1. Por que PEPS para atribuir as vendas ao estoque antigo

A pergunta da perícia não é "qual o custo das mercadorias vendidas", mas "quais unidades vendidas eram do vendedor". É uma questão de fluxo físico, não de custeio. Para itens intercambiáveis (saco de cimento, barra de vergalhão) a escrituração não identifica a unidade, e é preciso uma convenção de ordem de saída.

- PEPS (primeiro a entrar, primeiro a sair) assume que as unidades mais antigas saem primeiro. É a convenção que corresponde ao fluxo físico normal do comércio, é admitida pela NBC TG 16 (R2) para estoques intercambiáveis e é a leitura natural da expressão "venda do estoque": o que existia na data-base é vendido antes do que foi comprado depois.
- Custo médio ponderado mistura lotes e não responde à pergunta: dilui o estoque antigo nas compras novas e nunca o esgota por completo. Serve ao custeio, não à atribuição.
- UEPS (último a entrar, primeiro a sair) não é admitido pela NBC TG 16 nem pela legislação do imposto de renda e, aplicado aqui, favoreceria sistematicamente o comprador ao empurrar o estoque antigo para o fim.
- Identificação específica prevalece quando existe: item com número de série, lote ou nota de transferência individual. Nesse caso a atribuição é documental e o PEPS só cobre o resíduo.

Regra operacional do script `peps_estoque_transferido.py`: o inventário da data-base forma a primeira camada de cada item; cada compra posterior forma nova camada; cada venda consome as camadas na ordem. Quantidade vendida além das camadas é "sem lastro" e nunca é redistribuída, porque redistribuir esconderia inventário subavaliado ou compra não informada. A premissa fica declarada na saída e no laudo; critério diverso só por cláusula contratual.

Sensibilidade: quando o réu sustentar que vendeu o estoque novo primeiro, o perito apresenta o efeito como cenário alternativo descrito (quantidade do estoque antigo que deixaria de ser atribuída), sem adotá-lo, porque a cláusula destina ao vendedor o produto do estoque transferido, e a ordem de saída que esvazia a cláusula não é a interpretação que preserva o contrato.

---

## 2. Delimitação do estoque na data-base: hierarquia de fontes

| Ordem | Fonte | Força probatória | Ressalva obrigatória |
|---|---|---|---|
| 1 | Inventário físico assinado pelas partes na data-base (ou anexo do contrato) | Plena: prova produzida pelas duas partes | Conferir aritmética (quantidade x custo) e unidade de medida |
| 2 | Registro H010 do SPED Fiscal com H005 na data-base ou próximo | Alta: declaração do contribuinte ao fisco, prova contra ele (CPC, art. 417) | O H010 é anual (31/12) ou por mudança de regime; data distinta exige rolagem |
| 3 | Rolagem: último inventário disponível mais entradas (NF-e, CFOP de compra) menos saídas (NF-e, CFOP de venda) até a data-base, por item | Média: reconstrução pericial | Declarar o ponto de partida, o período rolado e as notas usadas; apresentar como cenário "reconstruído" |
| 4 | Balancete ou balanço na data-base (conta Estoques, valor total) | Baixa: só valor, sem quantidade por item | Serve de teto de valor e de teste de razoabilidade; não permite PEPS por item |
| 5 | Registro K200 do Bloco K (estoque escriturado mensal) | Alta quando existe (obrigatório só para alguns perfis) | Conferir obrigatoriedade do Bloco K para o contribuinte no período |

Quando só existe a fonte 4, o laudo informa que a atribuição por item é impossível e apresenta o cenário de valor: receita do estoque antigo estimada pela relação entre o valor do inventário a custo e a margem média praticada, com ressalva expressa de que se trata de estimativa e de que a lacuna é do réu (ver `references/roteiro-documental-e-quesitos.md`, seção 5).

---

## 3. SPED Fiscal: registros que interessam

| Registro | Conteúdo | Uso na perícia |
|---|---|---|
| 0200 | Cadastro de itens (código, descrição, unidade, NCM) | Casar o código do inventário com o código das notas; conversão de unidade |
| C100 | Documento fiscal (NF-e): chave, data de emissão e de saída, valor total, situação | Universo de vendas; filtrar situação (00 regular, 02 cancelado) e CFOP |
| C170 | Itens do documento: código, quantidade, valor unitário, CFOP, CST | Base do CSV de vendas e de compras por item |
| H005 | Totais do inventário: data e valor total | Data-base do H010 |
| H010 | Inventário por item: código, unidade, quantidade, valor unitário, valor do item, indicador de propriedade | Estoque na data-base; indicador de propriedade distingue mercadoria própria em poder de terceiros e mercadoria de terceiros em poder do informante |
| K200 | Estoque escriturado por item no fim do período de apuração | Confirmação mensal da rolagem, quando o Bloco K é obrigatório |

Campos e códigos dos indicadores: `[A VERIFICAR no Guia Prático da EFD ICMS/IPI vigente no período]`. O perito requisita o arquivo TXT do SPED (não só o recibo) e extrai os registros com script simples; o Bloco H de um ano e o C170 do período costumam ter dezenas de milhares de linhas, o que é tratável em Python.

Regra de cruzamento: soma de C170 por documento = valor do C100; soma de C100 de saída do mês = receita do Razão (conta Vendas) e da apuração do tributo (GIA, PGDAS-D ou DCTF). Diferença acima de 0,5% da receita exige explicação antes de qualquer PEPS.

---

## 4. NF-e: o que extrair do XML

| Elemento | Campo | Uso |
|---|---|---|
| `ide` | `dhEmi`, `nNF`, `serie`, `tpNF` (0 entrada, 1 saída), `finNFe` | Data, número, direção, finalidade (devolução tem finalidade própria) |
| `emit` e `dest` | CNPJ e nome | Quem vende e quem compra |
| `det/prod` | `cProd`, `xProd`, `NCM`, `CFOP`, `uCom`, `qCom`, `vUnCom`, `vProd`, `vDesc` | Item, quantidade, preço unitário, desconto incondicional |
| `det/imposto` | ICMS (`CST` ou `CSOSN`, `vBC`, `pICMS`, `vICMS`), PIS e COFINS | Confirmar alíquota praticada e substituição tributária por item |
| `total/ICMSTot` | `vProd`, `vDesc`, `vNF` | Conferência do documento |
| Eventos | Cancelamento, carta de correção, manifestação do destinatário | Excluir canceladas; registrar correções que afetem quantidade ou preço |

CFOP usuais de venda de mercadoria adquirida de terceiros: 5.102 (dentro do estado) e 6.102 (interestadual); venda de mercadoria sujeita à substituição tributária pelo substituído: 5.405; devolução de venda recebida: 1.202 e 2.202; devolução de compra: 5.202 e 6.202. Conferir a tabela oficial de CFOP vigente antes de filtrar, porque a tabela sofre alterações por Ajuste SINIEF.

Descontos incondicionais (`vDesc`) reduzem a receita bruta (DL 1.598/1977, art. 12, § 1º): no CSV de vendas, informar o preço unitário líquido do desconto e anotar a origem. Devoluções de venda do estoque antigo entram no script 3 como compensação prevista no contrato (ou não prevista, se a cláusula silenciar), com a NF de devolução como documento.

---

## 5. A cláusula "abatidos os impostos": três leituras

| Leitura | O que se abate | Fundamento | Cenário no script 2 |
|---|---|---|---|
| A. Tributos sobre a receita | ICMS, PIS e COFINS (regime geral) ou DAS (Simples) | São os tributos que incidem sobre a própria venda e que o comprador recolhe por ter vendido; sem eles o repasse seria do valor bruto que o comprador nunca reteve | `--cenario base` |
| B. Tributos sobre a receita mais IRPJ e CSLL | Acrescenta IRPJ e CSLL presumidos (ou efetivos no Lucro Real) | IRPJ e CSLL incidem sobre o lucro, não sobre a receita; só entram se o contrato disser "tributos" em sentido amplo, se as partes assim praticaram nos repasses anteriores, ou se o juízo assim decidir | `--cenario amplo` |
| C. Receita líquida contábil | Leitura A mais devoluções e descontos incondicionais | DL 1.598/1977, art. 12, § 1º; é a receita líquida da DRE | `--cenario base` com devoluções no script 3 e descontos já no preço do CSV |

O cenário base da skill é a leitura A, porque "impostos" sobre uma venda, na linguagem comum do comerciante, são os que vêm destacados ou embutidos no preço, e porque a leitura mais restritiva é a que menos reescreve o contrato na segunda fase (STJ, Tema 908). A leitura B vai sempre no laudo como cenário alternativo com o valor da diferença, para que o juízo decida. O custo da mercadoria (CMV) nunca é abatido, salvo cláusula que fale em "lucro" e não em "valor da venda": o estoque já era do vendedor.

Pontos de atenção:

- No Simples Nacional o DAS reúne também a CPP (contribuição patronal), que não é tributo sobre a receita em sentido estrito; como o DAS é indivisível e calculado sobre a receita, abate-se o DAS inteiro e registra-se a composição na memória.
- ICMS é tributo "por dentro": a alíquota aplica-se sobre o preço de venda, que já contém o imposto. O script aplica a alíquota sobre a receita bruta, como na apuração fiscal.
- Substituição tributária: a venda pelo substituído não gera ICMS próprio. Itens em ST ficam com ICMS zero e justificativa no arquivo de parâmetros; se o estoque mistura itens com e sem ST, separar a receita por grupo (CSV `mes;receita_bruta` por grupo a partir do quadro por item do script 1) e rodar o script 2 por grupo.
- Tributo devido e tributo pago: a cláusula abate o tributo que incide sobre a venda, apurado pela regra do regime; o comprovante de recolhimento (DAS, DARF, GNRE) confirma o regime e a alíquota, mas a falta de recolhimento não amplia o repasse nem o reduz. Divergência entre o apurado e o recolhido vai ao laudo.

---

## 6. Efeito do regime tributário do comprador

| Regime | Tributos sobre a receita (leitura A) | Acréscimo da leitura B | Origem obrigatória dos parâmetros |
|---|---|---|---|
| Simples Nacional | DAS pela alíquota efetiva do mês: (RBT12 x alíquota nominal menos parcela a deduzir) dividido por RBT12 (LC 123/2006, art. 18, § 1º-A) | Nenhum: o DAS já contém IRPJ e CSLL (art. 13) | PGDAS-D de cada competência (alíquota efetiva) e, para conferência, Anexo do ano-calendário `[A VERIFICAR]` |
| Lucro Presumido | ICMS (por arquivo), PIS 0,65% (Lei 9.715/1998, art. 8º, I), COFINS 3% (Lei 9.718/1998, art. 8º) | IRPJ: 8% x 15% mais adicional de 10% sobre a parcela da base que exceder R$ 20.000,00 por mês (Lei 9.249/1995, arts. 15 e 3º); CSLL: 12% x 9% (art. 20; Lei 7.689/1988, art. 3º) | RICMS da UF `[A VERIFICAR]`; ECF do período para o método do adicional |
| Lucro Real | ICMS, PIS 1,65% e COFINS 7,6% não cumulativos (Leis 10.637/2002 e 10.833/2003), líquidos de crédito: informar alíquota efetiva | IRPJ e CSLL pela alíquota efetiva do período sobre a receita, extraída da ECF | Apuração do contribuinte; créditos sobre o estoque transferido `[A VERIFICAR]` |

Adicional de IRPJ no presumido: três métodos, todos declarados pelo parâmetro `adicional_metodo`: `nenhum` (a receita do estoque não eleva a base acima do limite), `integral` (o comprador já ultrapassa o limite com as demais receitas, logo a receita marginal sofre 25%) e `faixa_mensal` (limite aplicado só sobre a receita do estoque, como se fosse a única). O método `integral` é o mais frequente em comprador de porte médio e exige justificativa com a ECF.

Em cessão de quotas, o regime é o da própria sociedade vendida, que continuou vendendo. Em trespasse, o regime é o do adquirente, e a transferência do estoque gera nota de saída do alienante (com os tributos dessa operação, que não são abatidos do repasse por não incidirem sobre a venda a terceiros).

---

## 7. Exemplo numérico curto

Dados fictícios de `assets/` (Alfa Comércio Ltda., data-base 31/03/2025, Lucro Presumido, ICMS hipotético de 18%):

| Etapa | Resultado | Fonte |
|---|---|---|
| Inventário na data-base | 5 itens, R$ 32.820,00 a custo | `exemplo_inventario.csv` |
| Vendas processadas | 13, das quais 10 com estoque antigo; 2 movimentos anteriores à data-base ignorados com alerta | `exemplo_vendas.csv`, `exemplo_compras.csv` |
| Receita bruta do estoque antigo | R$ 44.730,00 (04/2025 R$ 26.935,00; 05/2025 R$ 11.765,00; 06/2025 R$ 6.030,00) | script 1 |
| Receita de estoque novo (fora das contas) | R$ 12.137,00 | script 1 |
| Receita sem lastro (alerta: 7 m3 de areia e 40 telhas sem inventário) | R$ 2.745,00 | script 1 |
| Tributos leitura A (ICMS 18%, PIS 0,65%, COFINS 3%) | R$ 9.684,05; líquida R$ 35.045,95 | script 2, `--cenario base` |
| Tributos leitura B (mais IRPJ 8% x 25% e CSLL 12% x 9%) | R$ 11.061,73; líquida R$ 33.668,27 | script 2, `--cenario amplo` |
| Repasses comprovados e admitidos | R$ 25.000,00 (um TED de R$ 8.000,00 lançado duas vezes com o mesmo comprovante foi excluído) | script 3 |
| Compensação prevista no contrato (devolução NF 77) | R$ 2.500,00 | script 3 |
| Saldo cenário base (leitura B) | R$ 6.168,27 credor do vendedor | script 3 |
| Saldo cenário estrito (sem compensação) | R$ 8.668,27 | script 3 |
| Saldo cenário amplo (tudo o que o réu alega, inclusive R$ 3.000,00 sem recibo e R$ 5.200,00 fora do contrato) | R$ 2.031,73 credor do comprador | script 3 |

Conferência de abril (leitura A): 26.935,00 x 18% = 4.848,30; x 0,65% = 175,08; x 3% = 808,05; soma 5.831,43; líquida 21.103,57. Leitura B acrescenta IRPJ 538,70 (2.154,80 x 25%) e CSLL 290,90 (3.232,20 x 9%): líquida 20.273,97.

---

## 8. Armadilhas recorrentes

1. Movimentos com data igual ou anterior à data-base entram na planilha do réu "para completar o mês". O inventário da data-base já os reflete; o script os ignora e lista.
2. Compra e venda do mesmo item no mesmo dia: processar a compra antes, senão a venda consome estoque antigo que a compra deveria preservar. O script fixa essa ordem.
3. Item vendido com código diferente do inventário (recadastro no 0200): casar códigos antes de rodar, ou o PEPS classifica como sem lastro.
4. Unidade de medida diversa (inventário em milheiro, venda em unidade): converter no CSV e anotar.
5. Preço de venda abaixo do custo do inventário sem explicação: indício de venda a parte relacionada ou de desconto não documentado; listar e questionar.
6. Alíquota de ICMS "média da empresa" aplicada a todos os itens: não serve; a alíquota é por produto e UF de destino.
7. Abater IRPJ e CSLL sem cláusula que os inclua, ou abater o CMV: reescreve o contrato na segunda fase.
8. Aceitar "repasse" por pagamento de dívida do vendedor a terceiro sem previsão contratual: entra no cenário amplo, não no base.
9. Somar repasses pelo total da planilha do réu sem conferir documento a documento: duplicidades de comprovante passam despercebidas.
10. Atualizar o saldo com índice "de praxe": a atualização é da skill `atualizacao-monetaria`, com série oficial e termo inicial declarado como pendência jurídica.
