# Regime da CLPS/84, tabelas históricas, art. 58 do ADCT e readequação aos tetos das emendas

Referência: 12/09/2026. Este arquivo descreve a mecânica do cálculo antigo e da readequação com os números dos assets fictícios da skill. Nenhum coeficiente, salário mínimo, teto ou índice aqui é oficial: os valores reais entram por arquivo com fonte.

## Sumário

1. Os quatro momentos do benefício antigo
2. Período básico e correção dos 24 salários de contribuição
3. Menor valor-teto, maior valor-teto e fração do excedente
4. Coeficiente da espécie
5. Moedas e cortes de padrão monetário
6. Tabelas necessárias e onde obtê-las
7. Art. 58 do ADCT passo a passo
8. Readequação aos tetos das emendas (Tema 1.140) com exemplo numérico
9. O teste do benefício não limitado
10. Leitura da carta de concessão e dos extratos de pagamento
11. Erros recorrentes

---

## 1. Os quatro momentos do benefício antigo

| Momento | Pergunta | Script | Insumo |
|---|---|---|---|
| Concessão | Qual a RMI pelas regras da época e quantos salários mínimos representava? | `scripts/rmi_clps84.py` | 36 SC com moeda, coeficientes ORTN/OTN, tetos da DIB, coeficiente, fração do excedente, salário mínimo da DIB |
| Equivalência (04/1989 a 12/1991) | A renda paga preservou o número de salários mínimos da concessão? | `scripts/readequacao_tetos.py --art58` | Salário mínimo por competência |
| Readequação (12/1998 e 12/2003) | Com os limitadores da época e os tetos das emendas, qual a renda devida? | `scripts/readequacao_tetos.py` | Reajustes oficiais, conversões de moeda, tetos, renda paga |
| Reajustes e diferenças | Quanto faltou em cada competência, desde quando, para quem? | `scripts/atrasados_prescricao.py` | Ajuizamento, óbitos, coeficiente da pensão |

Misturar os momentos produz o erro clássico: comparar 20 salários mínimos de contribuição com 4 salários mínimos de benefício como se fossem a mesma base. O segurado contribuiu sobre até 20 salários mínimos (Lei 6.950/1981, art. 4º `[A VERIFICAR]`), mas a renda saiu de uma média corrigida, limitada por dois tetos e multiplicada por um coeficiente; depois foi corroída por reajustes que não preservaram a equivalência, recomposta parcialmente pelo art. 58 do ADCT e, por fim, pode ter direito à readequação das emendas se foi limitada na concessão.

---

## 2. Período básico e correção dos 24 salários de contribuição

Mecânica atribuída ao art. 21 da CLPS (Decreto 89.312/1984) `[A VERIFICAR dispositivo]`:

1. Período básico: os 36 últimos salários de contribuição, apurados em período não superior a 48 meses imediatamente anterior ao mês da DIB. O perito seleciona as 36 competências a partir da relação de salários de contribuição (CTPS, carta de concessão, processo administrativo) e as grava no CSV `competencia;salario_contribuicao;moeda`.
2. Correção: os 24 salários anteriores aos 12 últimos são corrigidos pelos coeficientes publicados em portaria do extinto MPAS (ORTN, depois OTN), um coeficiente por competência de origem, vigente no mês da DIB. Os 12 últimos entram pelo valor nominal.
3. Média: soma dos 36 valores dividida por 36 (salário de benefício).

Comandos do script: `--n-sc 36 --n-corrigidos 24` (padrão). O script aborta se faltar coeficiente para qualquer competência corrigida, se houver competência igual ou posterior à DIB ou se a amplitude do período exceder 48 meses; avisa quando o período não é contínuo (meses sem contribuição) e quando há coeficiente informado para competência não corrigida.

Com os assets fictícios (DIB 03/1987): soma dos SC corrigidos Cz$ 987.700,00; média Cz$ 27.436,11.

---

## 3. Menor valor-teto, maior valor-teto e fração do excedente

O regime anterior à CF/88 limitava o salário de benefício por dois tetos, mecânica atribuída ao art. 23 da CLPS/84 `[A VERIFICAR dispositivo e fórmula]`:

| Faixa do salário de benefício | Tratamento |
|---|---|
| Até o menor valor-teto | Integra a base da renda por inteiro |
| Entre o menor e o maior valor-teto (excedente) | Integra a base em fração: 1/30 por grupo de 12 contribuições acima do menor valor-teto, limitada a 30/30 `[A VERIFICAR]` |
| Acima do maior valor-teto | Desprezado |

No regime, o menor valor-teto correspondia à metade do maior (10 e 20 salários mínimos), o que explica a tese do Tema 1.140 ao mandar usar a metade do teto da emenda como menor valor-teto `[A VERIFICAR definição legal dos dois tetos]`.

O script recebe `--menor-teto`, `--maior-teto` e `--fonte-tetos` (valores na DIB, na moeda da DIB) e a fração por `--fracao-excedente` (ex.: `1/30`) com `--grupos-12 N` (número de grupos de 12 contribuições acima do menor valor-teto, apurado pelo perito na vida contributiva) e `--fundamento-fracao`. A fração efetiva é o produto; acima de 1 o script limita a 1 e avisa. Sem fundamento, o script recusa.

Exemplo dos assets: média Cz$ 27.436,11 supera o maior valor-teto (Cz$ 24.000,00); parcela até o menor valor-teto Cz$ 12.000,00; excedente Cz$ 12.000,00; fração 1/30 x 24 grupos = 0,8; parcela do excedente Cz$ 9.600,00; base Cz$ 21.600,00. Limitação: maior valor-teto.

---

## 4. Coeficiente da espécie

O coeficiente vem da carta de concessão ou do regime da espécie (por exemplo, aposentadoria por tempo de serviço com 35 anos: 95% `[A VERIFICAR dispositivo da CLPS/84]`; por invalidez e por velhice: coeficientes próprios). O script recebe `--coeficiente` em percentual e aplica sobre a base (parcela até o menor valor-teto mais a parcela fracionada do excedente). Se a carta de concessão informar que o coeficiente incidia de outra forma, ajustar e declarar `[A VERIFICAR contra o art. 23 da CLPS/84]`.

Exemplo: RMI = 95% x Cz$ 21.600,00 = Cz$ 20.520,00 = 17,1 salários mínimos de Cz$ 1.200,00 (fictício).

---

## 5. Moedas e cortes de padrão monetário

Um benefício de 1987 atravessa cinco padrões monetários até o real. Cada competência declara a moeda; a conversão entre padrões é feita pelo arquivo de conversões (`competencia;divisor;moeda_nova;fonte`), obtido com `scripts/padroes_monetarios.py` da skill `atualizacao-monetaria`, que documenta os diplomas de cada corte. Os assets trazem `exemplo_conversoes.csv` com os cinco cortes posteriores a 1986 (03/1986 Cz$, 01/1989 NCz$, 03/1990 Cr$, 08/1993 CR$, 07/1994 R$), a conferir antes do uso.

Regras: o script 1 converte os SC para a moeda da DIB antes de aplicar o coeficiente (ou aceita a declaração `--coeficientes-embutem-conversao`); o script 2 aplica o divisor a todas as rendas e ao teto na competência do corte; totais são apresentados por moeda e nunca somados entre moedas. A ressalva da `atualizacao-monetaria` sobre a tablita dos planos econômicos vale aqui: a conversão é nominal.

---

## 6. Tabelas necessárias e onde obtê-las

| Tabela | Uso | Fonte a consultar e citar |
|---|---|---|
| Coeficientes de correção dos salários de contribuição (ORTN/OTN) por mês de DIB | Script 1, `--coeficientes` | Portarias do extinto MPAS publicadas no DOU; tabelas da DATAPREV; processo administrativo de concessão (o INSS anexava a tabela aplicada) |
| Salário mínimo histórico (valor e moeda por vigência) | Script 1, `--salario-minimo-dib`; script 2, `--salarios-minimos` | Decretos e leis do salário mínimo e do piso nacional de salários (planalto.gov.br); séries históricas do IPEA e do DIEESE como conferência |
| Menor e maior valor-teto na DIB | Script 1, `--menor-teto`, `--maior-teto` | Portarias do MPAS de reajuste dos benefícios e dos tetos; carta de concessão |
| Índices de reajuste dos benefícios | Script 2, `--reajustes` | Portarias do MPAS, MPS e INSS de reajuste dos benefícios; anexos com o primeiro reajuste proporcional |
| Tetos dos benefícios por competência | Script 2, `--tetos` | Portarias interministeriais MPS/MF; EC 20/1998, art. 14; EC 41/2003, art. 5º |
| Renda paga (HISCRE/HISCON) | Script 2, `--pago`; script 3, `--pago-pensao` | Extratos de pagamento do INSS juntados aos autos ou requisitados |
| Cortes de padrão monetário | Scripts 1 e 2, `--conversoes` | `padroes_monetarios.py` da `atualizacao-monetaria` |

Formato de todos os CSVs: separador `;`, números no padrão brasileiro ou técnico, linhas iniciadas por `#` ignoradas, coluna `fonte` obrigatória nas tabelas. Os exemplos de `assets/` levam a fonte "EXEMPLO FICTÍCIO: substituir pela tabela oficial" e servem apenas para rodar a cadeia.

---

## 7. Art. 58 do ADCT passo a passo

1. Apurar a RMI na DIB e o salário mínimo vigente na DIB; o quociente é o número de salários mínimos da concessão (Súmula 25 da TNU: data da concessão, não o mês da última contribuição). No exemplo: 20.520,00 / 1.200,00 = 17,1.
2. Para cada competência de 04/1989 (sétimo mês da promulgação, art. 58, parágrafo único) até a implantação dos planos de custeio e benefícios (12/1991 `[A VERIFICAR]`), a renda devida é 17,1 vezes o salário mínimo da competência, na moeda da competência.
3. Confrontar com a renda paga no mesmo período (HISCRE, se existir; para 1989 a 1991 é comum não existir, e o script presume a RMI reajustada pelos índices informados).
4. A partir de 01/1992, a renda devida passa a evoluir pelos índices oficiais, partindo do valor de 12/1991.

O script aplica o mesmo critério à média sem teto (média em salários mínimos vezes o salário mínimo da competência) e ao teto projetado, para que a readequação das emendas parta de uma trajetória coerente. Premissa declarada na saída; cenário alternativo (média evoluída só pelos índices) obtém-se rodando sem `--art58` e declarando a diferença.

---

## 8. Readequação aos tetos das emendas (Tema 1.140) com exemplo numérico

Mecânica (STJ, Tema 1.140; STF, Temas 76 e 930):

1. Evoluir a média sem limitação (salário de benefício "sem teto") desde a DIB pelos mesmos índices dos benefícios, com as conversões de moeda e, se aplicada, a equivalência do art. 58.
2. Na competência de cada emenda, aplicar os limitadores da época sobre a média evoluída: maior valor-teto igual ao teto da emenda; menor valor-teto igual à metade; parcela até o menor por inteiro; excedente até o maior na mesma fração efetiva da concessão; coeficiente da espécie sobre a base.
3. A renda devida passa a ser a readequada quando esta supera a renda que vinha sendo devida; entre emendas, evolui pelos índices e fica travada no teto vigente.
4. A diferença mensal é a renda devida menos a renda paga (HISCRE; na falta, a RMI reajustada).

Exemplo com os assets fictícios (DIB 03/1987, RMI Cz$ 20.520,00, média Cz$ 27.436,11, coeficiente 95%, fração 0,8):

| Competência | Média evoluída | Maior valor-teto | Menor valor-teto | Base readequada | Renda readequada | Renda devida antes | Acréscimo |
|---|---|---|---|---|---|---|---|
| 12/1998 (EC 20) | R$ 1.147,54 | R$ 1.200,00 | R$ 600,00 | 600,00 + 0,8 x 547,54 = 1.038,03 | 95% x 1.038,03 = R$ 986,13 | R$ 858,27 | R$ 127,86 |
| 12/2003 (EC 41) | R$ 1.804,25 | R$ 2.400,00 | R$ 1.200,00 | 1.200,00 + 0,8 x 604,25 = 1.683,40 | 95% x 1.683,40 = R$ 1.599,23 | R$ 1.550,47 | R$ 48,76 |

Em 12/2003 a renda devida antes (R$ 1.550,47) é a renda readequada em 12/1998 evoluída pelos índices de 1999 a 2003; a diferença em relação à renda paga naquela competência (R$ 1.349,43) é de R$ 249,80, porque a renda paga vinha da RMI reajustada, sem a readequação de 1998.

Critério de limitação: por padrão (`--criterio-limitacao maior`) só o benefício limitado ao maior valor-teto na concessão recebe readequação, linha da Corte Especial do TRF1; com `qualquer`, também o limitado pelo menor valor-teto com excedente fracionado. Apresentar o cenário adotado e, se controvertido, o alternativo.

---

## 9. O teste do benefício não limitado

Se a média na concessão não excedeu o menor valor-teto, a RMI foi o coeficiente sobre a média inteira, e nenhuma emenda pode acrescentar nada: a renda readequada (coeficiente sobre a média evoluída limitada) é, no máximo, igual à renda que vinha sendo paga. O script implementa isso de duas formas: pelo critério de limitação (readequação não aplicável) e pela guarda mecânica (renda devida nunca inferior à renda limitada evoluída, e readequada só substitui quando supera). O teste de sanidade "benefício não limitado na concessão: diferença zero em toda a evolução" falha de propósito se a cadeia produzir diferença.

Segundo exemplo dos assets (`exemplo_rmi_nao_limitado.json`: média Cz$ 10.000,00, menor valor-teto Cz$ 12.000,00, RMI Cz$ 9.500,00): em 12/1998 a média evoluída é R$ 418,26, a renda readequada 95% x 418,26 = R$ 397,35, igual à renda limitada evoluída; diferença zero em todas as competências, com `--criterio-limitacao maior` ou `qualquer`.

---

## 10. Leitura da carta de concessão e dos extratos de pagamento

Da carta de concessão (ou do processo administrativo) extrair: espécie e DIB; relação dos 36 salários de contribuição com os coeficientes aplicados; média; menor e maior valor-teto aplicados; parcela do excedente e fração; coeficiente; RMI. Quando o INSS informa a "média limitada ao teto" sem a média inteira, o perito reconstrói a média pelos SC e registra a divergência. Do HISCRE/HISCON extrair: competência, valor pago, espécie (aposentadoria ou pensão), DIB e DIP, cessação. Lacunas do extrato (anteriores à informatização) são declaradas e supridas pela presunção do script, com aviso.

Documentos para a sucessão: certidão de óbito do segurado, certidão de casamento ou prova de dependência, carta de concessão da pensão, certidão de óbito da pensionista, decisão de habilitação, certidão de inexistência de dependentes ou inventário.

---

## 11. Erros recorrentes

1. Comparar salário de contribuição com benefício (20 x 4 salários mínimos) sem reconstruir a RMI.
2. Digitar coeficiente ORTN/OTN ou salário mínimo de memória: fabricação; o script exige arquivo com fonte.
3. Somar Cz$ com NCz$ ou Cr$ com R$: o script apresenta totais por moeda.
4. Aplicar a readequação a benefício não limitado na concessão: diferença zero por construção.
5. Usar o teto da emenda como limite único, sem o menor valor-teto: contraria o Tema 1.140.
6. Esquecer a trava no teto vigente entre emendas e o primeiro reajuste proporcional.
7. Incluir parcelas prescritas no total ou ignorar o abono anual.
8. Continuar as parcelas do titular após o óbito, sem converter em pensão pelo coeficiente da data do óbito.
9. Continuar a pensão após o óbito da pensionista (Decreto 3.048/1999, art. 114, I).
10. Concluir sobre decadência ou prescrição: o perito apresenta datas e cenários; a incidência é do juízo.
