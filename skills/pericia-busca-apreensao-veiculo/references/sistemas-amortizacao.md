# Sistemas de amortização, pro rata, tarifas, IOF e capitalização

Referência: 12/09/2026. Fórmulas e convenções usadas pelos scripts desta skill, com as escolhas de método explicitadas para que o laudo as declare. Toda operação monetária nos scripts é feita em `Decimal`, com arredondamento só na apresentação.

## Sumário

1. Notação
2. Tabela Price
3. SAC
4. Juros simples e o MEJS
5. Juros compostos versus simples: o que muda
6. Pro rata, carência e primeira parcela
7. Tarifas, seguros e IOF no principal
8. Custo efetivo total (CET)
9. Capitalização mensal versus diária
10. Encargos moratórios
11. Conferência da planilha do credor
12. Exemplo numérico dos assets

---

## 1. Notação

| Símbolo | Significado |
|---|---|
| PV | Principal financiado (valor presente) |
| i | Taxa de juros por período, em decimal (2,90% a.m. = 0,029) |
| n | Número de parcelas |
| PMT | Prestação constante |
| k | Ordem da parcela (1 a n) |
| S(k) | Saldo devedor após a parcela k |
| J(k), A(k) | Juros e amortização embutidos na parcela k |

---

## 2. Tabela Price

Prestação constante, juros decrescentes, amortização crescente. É o sistema padrão de CDC veículo e CCB de veículo.

```
PMT  = PV x i / (1 - (1 + i)^-n)
J(k) = S(k-1) x i
A(k) = PMT - J(k)
S(k) = S(k-1) - A(k)
```

Propriedades que servem de teste de sanidade: a soma das amortizações é igual a PV; o saldo após a parcela n é zero; a soma das parcelas é igual a PV mais a soma dos juros. Os scripts falham por desenho quando um desses testes não fecha.

Sobre capitalização: na Price os juros de cada mês são pagos na parcela, e não incorporados ao saldo, quando a parcela é paga em dia. A tese de que a Price embute juros sobre juros decorre da própria fórmula, que aplica juros compostos no cálculo da prestação. A perícia não decide a tese; declara o sistema, mostra a tabela e, se o juízo determinar recálculo sem capitalização, aplica o método da seção 4.

---

## 3. SAC

Amortização constante, parcelas decrescentes. Raro em veículo, comum em imobiliário. Fica aqui para confronto quando o contrato o adotar.

```
A    = PV / n
J(k) = S(k-1) x i
PMT(k) = A + J(k)
```

---

## 4. Juros simples e o MEJS

Quando o juízo afasta a capitalização (ausência de pactuação expressa, Súmula 539/STJ, ou vício de informação, REsp 2.238.832), o recálculo exige um sistema a juros simples. Não há um único método consagrado; a perícia escolhe, declara e aplica com coerência. O script `evolucao_cdc_veiculo.py` implementa, no cenário C, o Método de Equivalência a Juros Simples (MEJS): a prestação constante cujo valor presente a juros simples iguala o principal.

```
PV   = soma[k=1..n] PMT / (1 + i x k)
PMT  = PV / soma[k=1..n] 1 / (1 + i x k)
A(k) = PMT / (1 + i x k)
J(k) = PMT - A(k)
S(k) = S(k-1) - A(k)
```

Propriedades: a soma das amortizações é igual a PV e o saldo final é zero, o que preserva o teste de sanidade. Os juros embutidos crescem com k, porque cada parcela remunera o capital desde a data zero a juros simples; é característica do método, não erro.

Alternativas que a perita pode preferir, declarando a escolha: Método de Gauss (soma dos dígitos) e amortização a juros simples sobre saldo (juros calculados sobre o saldo sem incorporação). Qualquer troca de método é extensão do script, com nova função de tabela e o mesmo teste de sanidade.

---

## 5. Juros compostos versus simples: o que muda

```
Montante composto: M = PV x (1 + i)^n
Montante simples:  M = PV x (1 + i x n)
```

Exemplo com PV de R$ 10.000,00, i de 2% a.m. e n de 12: composto R$ 12.682,42; simples R$ 12.400,00; diferença R$ 282,42. A diferença cresce com a taxa e com o prazo; em 36 ou 48 parcelas de veículo, a diferença de juros totais entre Price e MEJS costuma ficar entre 10% e 20% dos juros.

---

## 6. Pro rata, carência e primeira parcela

Quando a primeira parcela vence mais de um mês depois da contratação, o credor costuma cobrar juros de carência sobre os dias excedentes, incorporando-os ao principal antes de aplicar a Price. Duas convenções:

```
Exponencial: J = PV x ((1 + i)^(d/30) - 1)
Linear:      J = PV x i x d / 30
```

O script usa a exponencial nos cenários com capitalização (A e B) e a linear no cenário sem capitalização (C), sobre os dias que excedem um mês civil contado da contratação. Primeira parcela exatamente um mês depois não gera carência. A flag `--ignorar-carencia` desliga o cálculo quando o contrato ou a planilha do credor não o praticam. A convenção adotada vai na memória de cálculo.

---

## 7. Tarifas, seguros e IOF no principal

Em CDC veículo é usual que tarifa de cadastro, registro de contrato, avaliação do bem, seguro prestamista e IOF sejam somados ao valor líquido liberado e financiados na mesma taxa. Efeitos:

- O principal cresce e, com ele, os juros de todas as parcelas. Excluir uma tarifa de R$ 400,00 do principal de um contrato de 36 parcelas a 2,90% a.m. reduz a soma das parcelas em bem mais de R$ 400,00.
- Por isso o cenário B remove do principal as tarifas contestadas que foram incluídas no financiado, e não apenas as devolve nominalmente.
- Tarifa contestada paga à vista (fora do financiado) não altera a tabela; entra como valor a restituir, listado à parte.
- O IOF é tributo, não tarifa, e permanece no principal nos dois cenários por padrão. O financiamento do IOF é matéria do Tema 958 `[A VERIFICAR]`. A flag `--excluir-iof` existe para cenário alternativo determinado pelo juízo.
- Alíquotas do IOF sobre operações de crédito: Decreto 6.306/2007 e alterações; conferir a redação vigente na data da contratação em gov.br/receitafederal `[A VERIFICAR]`. Nunca recalcular IOF de memória; usar o valor do contrato e, se contestado, indicar a norma para conferência.

Regra de validação do script: a soma de tarifas, seguros e IOF marcados como incluídos não pode superar o valor financiado.

---

## 8. Custo efetivo total (CET)

O CET é a taxa que iguala o valor líquido recebido pelo devedor ao fluxo de parcelas, incluindo juros, tarifas, seguros e IOF. É maior que a taxa de juros e não é comparável com a taxa média do BACEN, que mede apenas juros. Norma de regência do CET: resoluções do Conselho Monetário Nacional `[A VERIFICAR a resolução vigente na data do contrato]`.

Uso pericial do CET: (a) conferir se o CET informado no contrato é coerente com o fluxo, o que revela tarifas não declaradas; (b) demonstrar o peso das tarifas embutidas. O cálculo do CET é uma taxa interna de retorno; não está implementado nos scripts desta versão e entra como extensão.

---

## 9. Capitalização mensal versus diária

```
mensal equivalente = (1 + diária)^30 - 1
anual equivalente  = (1 + mensal)^12 - 1
```

Sinais que o script `abusividade_juros.py` testa:

| Situação | Sinal |
|---|---|
| Taxa anual informada maior que 12 vezes a mensal | Pactuação de capitalização mensal (orientação atribuída à Súmula 541/STJ `[A VERIFICAR]`) |
| Taxa anual informada igual à composta (1 + m)^12 - 1 | Coerência entre as taxas informadas |
| Taxa anual informada igual ao duodécuplo | Taxa linear; a pactuação depende da cláusula |
| Taxa anual não informada | Teste inaplicável; buscar a cláusula (Súmula 539/STJ) |
| Capitalização diária sem taxa diária informada | Violação do dever de informação, tratada como abusiva no REsp 2.238.832 |
| Capitalização diária com taxa diária informada | Conferir se (1 + d)^30 - 1 coincide com a mensal contratada |

A capitalização diária com taxa diária informada produz, em parcela mensal, o mesmo resultado que a mensal equivalente; a diferença aparece em atrasos e em pro rata.

---

## 10. Encargos moratórios

| Encargo | Parâmetro usual | Fundamento | Tratamento no script |
|---|---|---|---|
| Juros de mora | 1% a.m., pro rata die sobre 30 dias | Cláusula contratual; na falta, CC, art. 406 | `--juros-mora-am` (padrão 1,0) |
| Multa moratória | Até 2% sobre a parcela vencida | CDC, art. 52, § 1º | `--multa` (padrão 2,0) |
| Comissão de permanência | Não cumulável com juros, multa e correção | Súmula 472/STJ `[A VERIFICAR]` | `--comissao-permanencia` apenas sinaliza; nunca soma |
| Correção monetária | Índice contratual, quando houver | Cláusula | Fora do script; usar `atualizacao-monetaria` |

Os encargos moratórios incidem só sobre as parcelas vencidas e não pagas. As vincendas entram na purga pelo valor nominal (padrão) ou pelo valor presente (`--vincendas valor-presente`), nunca com encargo de mora, porque não estão em atraso.

---

## 11. Conferência da planilha do credor

Checklist para reproduzir a planilha apresentada na inicial:

1. O principal da planilha é igual ao valor financiado do contrato (incluindo tarifas, seguros e IOF)?
2. A prestação da planilha coincide com a Price calculada com a taxa mensal do contrato? Diferença de centavos é arredondamento; diferença de reais é taxa ou principal diverso.
3. As datas de vencimento seguem o dia da primeira parcela, mês a mês?
4. Os pagamentos foram imputados na parcela correta e na data correta?
5. Os encargos moratórios seguem a cláusula (percentual, base de cálculo, pro rata)?
6. Há comissão de permanência ou outro encargo somado aos juros de mora e à multa?
7. As vincendas foram lançadas pelo nominal ou pelo valor presente, e a inicial diz qual?
8. O total da inicial fecha com a soma das partes? Registrar qualquer diferença como "não reproduzível".

---

## 12. Exemplo numérico dos assets

Contrato fictício de `assets/exemplo_contrato.json`: valor financiado R$ 38.500,00, 36 parcelas, 2,90% a.m., primeira parcela um mês após a contratação, tarifas contestadas de R$ 750,00 incluídas no financiado, taxa média (fictícia) de 1,60% a.m.

| Item | Cenário A | Cenário B | Cenário C (MEJS) |
|---|---|---|---|
| Principal | R$ 38.500,00 | R$ 37.750,00 | R$ 37.750,00 |
| Taxa mensal | 2,90% | 1,60% | 1,60% |
| Parcela | R$ 1.737,23 | R$ 1.387,58 | R$ 1.336,35 |
| Juros totais | R$ 24.040,37 | R$ 12.203,06 | R$ 10.358,44 |
| Excesso pago em 14 parcelas | R$ 4.895,03 sobre B | | |
| Purga em 10/09/2025 (3 vencidas + 19 vincendas nominais) | R$ 38.421,74 | R$ 30.688,64 | |

Reproduzível com os comandos da seção "Scripts disponíveis" do SKILL.md.
