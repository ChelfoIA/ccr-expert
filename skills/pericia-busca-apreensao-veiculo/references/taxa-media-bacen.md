# Taxa média de mercado do BACEN: obtenção, conversão e registro

Referência: 12/09/2026. Este arquivo explica o que é a taxa média usada como referencial de abusividade (REsp 1.061.530), onde obtê-la, como converter unidades e como registrar a fonte no laudo. Nenhum código de série é dado como certo: o perito valida cada código na própria API antes de citar.

## Sumário

1. O que é a taxa média e por que ela é o referencial
2. Modalidade correta para financiamento de veículo
3. Onde obter: SGS do BACEN, portal e API
4. Códigos de série sugeridos (todos a verificar)
5. Competência de referência
6. Conversão entre bases
7. Limiar de 1,5 vez: premissa, não norma
8. Registro obrigatório no laudo
9. Armadilhas frequentes
10. Ambiente sem rede

---

## 1. O que é a taxa média e por que ela é o referencial

O Banco Central divulga, mensalmente, a taxa média de juros das novas operações de crédito contratadas no mês, por modalidade, segmento (pessoa física ou jurídica), origem dos recursos (livres ou direcionados) e tipo de taxa (pré-fixada, pós-fixada, flutuante). É a média ponderada pelo volume das concessões informadas pelas instituições financeiras ao BACEN.

O STJ, no REsp 1.061.530 (Segunda Seção, j. 22/10/2008), adotou a taxa média de mercado como referencial para aferir abusividade dos juros remuneratórios: a abusividade só se caracteriza quando a taxa contratada discrepa substancialmente da média da modalidade à época da contratação. Sem a taxa média correta, o teste de abusividade não existe.

---

## 2. Modalidade correta para financiamento de veículo

| Elemento | Escolha correta para CDC veículo e CCB de veículo | Erro comum |
|---|---|---|
| Modalidade | Aquisição de veículos | Crédito pessoal não consignado, aquisição de outros bens |
| Segmento | Pessoa física, se o devedor for pessoa natural; pessoa jurídica, se empresa | Usar a série de PF para financiamento a empresa |
| Recursos | Livres | Séries de recursos direcionados |
| Tipo de taxa | Pré-fixada, que é a regra em financiamento de veículo | Séries de pós-fixado ou de taxa consolidada |
| Estatística | Taxa média das novas concessões do mês | Taxa média do estoque ou taxa máxima |
| Unidade | Anotar se a série é % a.a. ou % a.m. | Comparar % a.a. da média com % a.m. do contrato |

Leasing, arrendamento mercantil e consórcio têm séries e lógica próprias e não são objeto desta skill.

---

## 3. Onde obter: SGS do BACEN, portal e API

Portal: Sistema Gerenciador de Séries Temporais, em bcb.gov.br (menu Estatísticas, séries temporais). Na busca, digitar "aquisição de veículos" e filtrar por "taxa média de juros". O resultado lista séries em % a.a. e em % a.m., para pessoa física e para pessoa jurídica.

API pública (sem autenticação):

```
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial=01/03/2024&dataFinal=31/03/2024
```

Substituir `{codigo}` pelo código validado. O retorno é uma lista de objetos com `data` (dd/mm/aaaa) e `valor` (texto com ponto decimal). Para série mensal, o registro do mês vem datado no primeiro dia do mês.

Validação obrigatória: abrir a série no portal, ler o nome completo, a unidade, a periodicidade e a fonte, e comparar com o esperado na tabela da seção 2. Só então citar o código.

---

## 4. Códigos de série sugeridos (todos a verificar)

Os códigos abaixo são os que costumam corresponder às séries de aquisição de veículos com recursos livres e taxa pré-fixada na metodologia vigente desde 2011. Nenhum foi conferido nesta forja, porque a rede para o BACEN estava bloqueada. Tratar cada um como `[A VERIFICAR]`.

| Série provável | Segmento | Unidade | Código sugerido |
|---|---|---|---|
| Taxa média de juros, recursos livres, aquisição de veículos | Pessoa física | % a.a. | 25471 `[A VERIFICAR]` |
| Taxa média de juros, recursos livres, aquisição de veículos | Pessoa física | % a.m. | 20749 `[A VERIFICAR]` |
| Taxa média de juros, recursos livres, aquisição de veículos | Pessoa jurídica | % a.a. | 25470 `[A VERIFICAR]` |
| Taxa média de juros, recursos livres, aquisição de veículos | Pessoa jurídica | % a.m. | 20748 `[A VERIFICAR]` |

Contratos anteriores a 03/2011 caem em séries da metodologia antiga, com códigos e nomes distintos; localizar pela busca textual no portal e registrar a série efetivamente usada.

---

## 5. Competência de referência

O mês da assinatura do contrato. O REsp 1.061.530 fala na taxa média à época da contratação; a série mensal do SGS entrega um valor por mês, e o valor correto é o do mês em que a operação foi contratada, não o da data do laudo nem o da propositura da ação.

Casos de fronteira: contrato assinado nos últimos dias do mês e liberado no mês seguinte: usar o mês da assinatura e registrar a dúvida; aditivo ou renegociação: cada instrumento tem a sua própria competência de referência.

---

## 6. Conversão entre bases

Juros compostos, que é a convenção do BACEN e dos contratos com capitalização mensal:

```
anual  = (1 + mensal)^12 - 1
mensal = (1 + anual)^(1/12) - 1
mensal = (1 + diária)^30 - 1
```

Exemplo: média de 1,60% a.m. equivale a 20,98% a.a.; contratada de 2,90% a.m. equivale a 40,92% a.a. Comparar sempre na mesma base. O script `scripts/abusividade_juros.py` faz a conversão e registra a memória.

O duodécuplo (12 vezes a taxa mensal) não é conversão financeira; é o teste linear cuja superação pela taxa anual informada sinaliza pactuação de capitalização (orientação atribuída à Súmula 541/STJ `[A VERIFICAR]`).

---

## 7. Limiar de 1,5 vez: premissa, não norma

O STJ não fixou percentual. O REsp 1.061.530 fala em discrepância substancial e remete ao caso concreto. Na prática forense, tribunais estaduais adotam com frequência o parâmetro de uma vez e meia a média, e alguns julgados usam o dobro ou um spread absoluto. Por isso:

- O script recebe o limiar por parâmetro (`--limiar`, padrão 1,5) e o grava na saída como premissa.
- O laudo declara: "adotou-se, como premissa deste laudo, o parâmetro de 1,5 vez a taxa média, usual na jurisprudência estadual; a qualificação da discrepância como substancial cabe ao juízo".
- Quando a taxa contratada supera a média sem alcançar o limiar, o laudo diz exatamente isso, com a razão e o spread, e não declara abusividade.
- Quando o juízo já fixou o critério na decisão saneadora, usar o critério da decisão e a flag `--forcar-taxa-media` do script de evolução, se for o caso.

---

## 8. Registro obrigatório no laudo

Tabela mínima que acompanha qualquer citação de taxa média:

| Campo | Exemplo |
|---|---|
| Fonte | Banco Central do Brasil, Sistema Gerenciador de Séries Temporais (SGS) |
| Série | Taxa média de juros das operações de crédito com recursos livres, pessoas físicas, aquisição de veículos, pré-fixado |
| Código | [código validado na API em dd/mm/aaaa] |
| Unidade | % a.m. (ou % a.a., com a conversão declarada) |
| Competência | 03/2024 |
| Valor | 1,60% a.m. |
| Data da consulta | 12/09/2026 |
| Anexo | Impressão da tela do SGS ou CSV exportado, anexado ao laudo |

O JSON e o CSV brutos da API vão para o anexo do laudo. A perita responde pela reprodução do dado, e o anexo permite ao assistente técnico adverso refazer a consulta.

---

## 9. Armadilhas frequentes

1. Comparar o CET com a taxa média. O CET inclui tarifas, seguros e IOF; a taxa média do BACEN é taxa de juros. Comparar juros com juros.
2. Usar a série de pessoa física para devedor pessoa jurídica, ou vice-versa.
3. Usar a média do mês do laudo ou do ajuizamento em vez do mês da contratação.
4. Misturar unidades: média em % a.a. contra contratada em % a.m.
5. Tomar a taxa anual informada no contrato como taxa efetiva sem conferir se é o duodécuplo ou a composta.
6. Citar código de série sem abrir a série no portal.
7. Estimar a taxa média "de memória" ou por interpolação. É fabricação e invalida o laudo.
8. Ignorar que renegociações e aditivos criam novas competências de referência.

---

## 10. Ambiente sem rede

Os scripts desta skill não acessam a internet. Quando o ambiente de execução não tiver rede (caso do ambiente de forja, em que o acesso ao BACEN estava bloqueado), a perita consulta o SGS por outro meio, anota fonte, código, competência, valor e data, e passa o valor por parâmetro (`--taxa-media-mensal` ou `--taxa-media-anual`, com `--fonte` e `--competencia`). Os scripts recusam taxa média sem fonte e competência, por desenho: a recusa é uma proteção contra fabricação, não um defeito.
