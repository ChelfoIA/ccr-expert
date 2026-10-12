# Template de laudo pericial contábil: prestação de contas da venda do estoque transferido

Uso: preencher os campos entre colchetes; excluir as seções inaplicáveis. Nenhum número entra sem o JSON dos scripts anexado. Toda citação segue o protocolo antifabricação de `references/fundamentacao-legal.md`, seção 8. Para atuação como assistente técnico, trocar o título por "Parecer técnico contábil", declarar a parte assistida no cabeçalho e manter a mesma memória de cálculo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_PrestacaoContasEstoque_[NomeAbreviado]_v1.md` (por exemplo, `2026-09-12_Laudo_PrestacaoContasEstoque_v1.md`).

---

## Laudo pericial contábil

**Processo nº** [0000000-00.0000.0.00.0000]
**Vara** [juízo]
**Ação** Exigir contas (CPC, arts. 550 a 553), segunda fase
**Autor** [Maria da Silva (autora), vendedora]
**Réu** [Alfa Comércio Ltda. e/ou João de Souza (réu), comprador]
**Perito** [nome], contador, CRC [registro]
**Data-base da transferência** [dd/mm/aaaa]
**Data-base do laudo** [dd/mm/aaaa]

---

## 1. Objeto

A perícia tem por objeto a apuração do saldo da prestação de contas relativa ao estoque transferido em [cessão de quotas / trespasse] formalizada em [data], cuja cláusula [número] destina ao vendedor o produto da venda do estoque existente na data-base, abatidos os impostos. Compreende: delimitação do estoque na data-base, atribuição das vendas posteriores ao estoque transferido, apuração dos tributos incidentes sobre essa receita, conciliação dos repasses e compensações alegados e apuração do saldo em forma mercantil (CPC, arts. 551 e 552).

Não integram o objeto: a validade da cláusula, a licitude das compensações não previstas e a consequência jurídica da falta de exibição de documentos, matérias reservadas ao juízo (CPC, art. 473, § 2º). A atualização monetária e os juros sobre o saldo são apresentados em anexo próprio, com o termo inicial indicado como premissa.

---

## 2. Quesitos

| Origem | Nº | Quesito | Seção da resposta |
|---|---|---|---|
| Juízo | 1 | [transcrever] | [10.1] |
| Autor | 1 | [transcrever] | [10.2] |
| Réu | 1 | [transcrever] | [10.3] |

---

## 3. Documentos examinados

| Nº | Documento | Fls. | Origem | Observação |
|---|---|---|---|---|
| 1 | Contrato de [cessão de quotas / trespasse] de [data], cláusula [N] | | Autor | [base do repasse, o que são impostos, prazo, compensações] |
| 2 | Inventário da data-base [assinado pelas partes / registro H010 do SPED / reconstruído] | | [parte] | [itens, valor a custo] |
| 3 | SPED Fiscal, Blocos 0, C, H e K, de [mm/aaaa] a [mm/aaaa] | | Réu | [TXT original; conferência C170 x C100] |
| 4 | XML das NF-e de saída e de entrada do período | | Réu | [quantidade de documentos; cancelamentos] |
| 5 | PGDAS-D / GIA / DCTF / ECF do período | | Réu | [regime, alíquota efetiva, método do adicional] |
| 6 | Comprovantes de repasse e recibos | | Réu | [quantidade; sem comprovante: N] |
| 7 | Extratos bancários do autor e do réu (lançamentos pertinentes) | | Partes | [conferência dos repasses] |
| 8 | Termo de diligência nº [N] e resposta | | Perito | [entregue / não entregue] |

---

## 4. Metodologia

1. Perímetro contratual: transcrição literal da cláusula do estoque e definição da data-base; leitura adotada no cenário base e leitura alternativa (`references/metodo-peps-tributos-e-sped.md`, seção 5).
2. Delimitação do estoque transferido por item, quantidade e custo, com a fonte e a sua força probatória (seção 2 do mesmo arquivo).
3. Atribuição das vendas posteriores ao estoque antigo ou ao novo pelo método PEPS, item a item, com compras processadas antes das vendas no mesmo dia e quantidade sem lastro destacada (`scripts/peps_estoque_transferido.py`).
4. Apuração dos tributos sobre a receita do estoque antigo conforme o regime do réu, com alíquotas por arquivo e fonte declarada, nos cenários base e amplo (`scripts/tributos_sobre_receita.py`).
5. Conciliação dos repasses e compensações alegados: classificação (comprovado, sem comprovante, fora do contrato, duplicidade), imputação ao mês mais antigo em aberto (CC, arts. 352 a 355), cronologia e saldo nos cenários base, estrito e amplo (`scripts/conciliacao_repasses.py`).
6. Quadro em forma mercantil e respostas aos quesitos. Padrão numérico brasileiro; arredondamento ROUND_HALF_UP a duas casas só na apresentação.

---

## 5. Perímetro contratual e data-base

- Cláusula [N]: "[transcrição literal]".
- Base do repasse: [valor bruto da venda abatidos os impostos].
- Leitura adotada no cenário base: [A: tributos sobre a receita]. Leitura alternativa: [B: inclui IRPJ e CSLL]. Fundamento: seção 5 do reference de método; STJ, Tema 908 (a segunda fase não reescreve o contrato).
- Prazo contratual de repasse: [N dias após o mês da venda / não previsto; premissa de 30 dias declarada].
- Compensações admitidas pelo contrato: [devoluções de clientes / nenhuma / outras].
- Data-base da transferência: [dd/mm/aaaa], fixada por [contrato / averbação / inventário].

---

## 6. Estoque transferido e atribuição PEPS

Fonte do inventário: [assinado / H010 / reconstruído, com a ressalva da seção 5 de `references/roteiro-documental-e-quesitos.md`].

| Item | Descrição | Quantidade na data-base | Custo unitário (R$) | Vendido (antigo) | Remanescente | Receita bruta do antigo (R$) |
|---|---|---:|---:|---:|---:|---:|
| [código] | [descrição] | [qtd] | [custo] | [qtd] | [qtd] | [valor] |
| Total | | | [valor a custo] | | | [valor] |

Receita bruta do estoque antigo por mês: [tabela do script 1]. Movimentos anteriores à data-base ignorados: [lista]. Vendas sem lastro: [lista com NF e quantidade]. Testes de sanidade do script 1: [todos OK].

---

## 7. Tributos sobre a receita e receita líquida devida

Regime do réu no período: [Simples Nacional / Lucro Presumido / Lucro Real], comprovado por [PGDAS-D / DCTF / ECF].

| Mês | Receita bruta (R$) | [ICMS] | [PIS] | [COFINS] | [DAS] | [IRPJ] | [CSLL] | Total tributos (R$) | Receita líquida (R$) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| [mm/aaaa] | | | | | | | | | |
| Total | | | | | | | | | |

Alíquotas e fontes: [tabela "Alíquotas e fontes" do script 2]. Itens marcados `[A VERIFICAR]`: [ICMS no RICMS da UF; faixas do Anexo do Simples]. Diferença entre cenário base e amplo: R$ [valor].

---

## 8. Conciliação dos repasses e quadro em forma mercantil

Itens alegados pelo réu: [N repasses e N compensações], classificados conforme o quadro do script 3.

| Rubrica | | Valor (R$) |
|---|:-:|---:|
| Receita bruta das vendas do estoque transferido | + | [valor] |
| Tributos incidentes sobre essa receita | - | [valor] |
| Receita líquida devida ao vendedor | = | [valor] |
| Compensações previstas no contrato e documentadas | - | [valor] |
| Repasses comprovados e admitidos pelo contrato | - | [valor] |
| Saldo final em [dd/mm/aaaa]: credor [autor / réu] | = | [valor] |

Repasses sem comprovante: [lista]. Itens fora do contrato: [lista]. Duplicidades: [lista]. Cronologia devido x repassado e saldo por mês: anexos [N] e [N].

---

## 9. Cenários

| Cenário | Leitura da cláusula | Itens admitidos | Saldo final (R$) | Credor |
|---|---|---|---:|---|
| Base | [A] | comprovados e previstos no contrato | [valor] | [autor] |
| Estrito | [A] | só repasses bancários comprovados | [valor] | [autor] |
| Amplo | [B] | tudo o que o réu alega, exceto duplicidade de comprovante | [valor] | [réu] |

O cenário base é o sustentado pelo perito; os demais quantificam o efeito das decisões reservadas ao juízo.

---

## 10. Respostas aos quesitos

### 10.1 Quesitos do juízo

> Quesito [N] do juízo: "[transcrição]"
> Resposta: [resposta objetiva com remissão à seção e ao anexo].

### 10.2 Quesitos do autor

### 10.3 Quesitos do réu

---

## 11. Conclusão

Na data-base de [dd/mm/aaaa], o saldo da prestação de contas é de R$ [valor] em favor de [parte] no cenário base, de R$ [valor] no cenário estrito e de R$ [valor] no cenário amplo. [Uma frase sobre a principal causa da diferença entre cenários.] A atualização monetária e os juros constam do anexo [N], calculados pela skill `atualizacao-monetaria` com o termo inicial declarado como premissa.

---

## 12. Memória de cálculo e anexos

- Anexo I: `peps.json`, `atribuicao.csv` e `peps.md` (script 1), com data e comando executado.
- Anexo II: `tributos_base.json` e `tributos_amplo.json` (script 2).
- Anexo III: `conciliacao.json`, `cronologia.csv` e `conciliacao.md` (script 3).
- Anexo IV: relação das NF-e do estoque antigo com chave de acesso.
- Anexo V: memória de atualização monetária.
- Comandos executados: [linhas de comando com os arquivos de entrada].

---

## 13. Pendências de verificação

| Nº | Item | Efeito no laudo | Responsável |
|---|---|---|---|
| 1 | [Alíquota de ICMS no RICMS da UF, ano-calendário das vendas] | [tributos e líquida] | [perito] |
| 2 | [Inventário assinado não localizado: cenário reconstruído] | [quantidade atribuída] | [réu / autor] |
| 3 | [Termo inicial da atualização do saldo] | [anexo V] | [juízo] |

---

## Exemplo preenchido (dados fictícios de `assets/`, resumido)

> **Processo nº** 0000000-00.0000.0.00.0000. **Autora** Maria da Silva (vendedora). **Ré** Alfa Comércio Ltda. (compradora). **Data-base da transferência** 31/03/2025. **Regime da ré** Lucro Presumido.
>
> **Perímetro (seção 5).** Cláusula 4.1: "o valor da venda do estoque existente em 31/03/2025 será repassado à vendedora, abatidos os impostos, até o dia 30 do mês seguinte". Cenário base: leitura A (ICMS, PIS e COFINS). Cenário amplo: leitura B (mais IRPJ e CSLL presumidos), a pedido da ré.
>
> **Estoque (seção 6).** Inventário assinado pelas partes com 5 itens, R$ 32.820,00 a custo. Entre 01/04/2025 e 05/07/2025 a ré emitiu 13 notas de saída dos itens inventariados; a atribuição PEPS imputou ao estoque antigo R$ 44.730,00 de receita bruta (04/2025 R$ 26.935,00; 05/2025 R$ 11.765,00; 06/2025 R$ 6.030,00), R$ 12.137,00 ao estoque novo e R$ 2.745,00 sem lastro (7 m3 de areia além do inventário e 40 telhas não inventariadas), estes últimos listados como alerta. Remanescente do estoque antigo: R$ 1.860,00 a custo.
>
> **Tributos (seção 7).** Leitura A: R$ 9.684,05 (ICMS 18% `[A VERIFICAR no RICMS]`, PIS 0,65%, COFINS 3%); líquida R$ 35.045,95. Leitura B: R$ 11.061,73; líquida R$ 33.668,27.
>
> **Conciliação (seção 8; leitura B, a mais favorável à ré).** Repasses comprovados e admitidos: R$ 25.000,00; o TED de R$ 8.000,00 de 16/06/2025 foi lançado duas vezes pela ré com o mesmo comprovante (fl. 90) e contado uma vez. Devolução da NF 5002 (R$ 2.500,00) admitida como compensação prevista na cláusula 5.2. Fora do cenário base: R$ 3.000,00 em dinheiro sem recibo e R$ 4.000,00 de boleto pago a fornecedor da autora sem previsão contratual, além de multa de R$ 1.200,00 alegada sem cláusula.
>
> **Quadro mercantil.** Receita bruta R$ 44.730,00; tributos R$ 11.061,73; líquida R$ 33.668,27; compensação R$ 2.500,00; repasses R$ 25.000,00; saldo credor da autora R$ 6.168,27 em 30/09/2025.
>
> **Cenários (seção 9).** Estrito R$ 8.668,27 (credora a autora); amplo R$ 2.031,73 (credora a ré). Na leitura A o saldo base sobe para R$ 7.545,95.
>
> **Quesito 4 do juízo (seção 10):** "Quais repasses foram comprovados pelo réu e quais foram alegados sem comprovante?"
> **Resposta:** Foram comprovados três repasses bancários, de R$ 15.000,00 (PIX, 15/05/2025, fl. 88), R$ 8.000,00 (TED, 16/06/2025, fl. 90) e R$ 2.000,00 (PIX, 10/09/2025, fl. 97), que somam R$ 25.000,00. O lançamento de um segundo TED de R$ 8.000,00 em 16/06/2025 repete o mesmo comprovante da fl. 90 e foi desconsiderado como duplicidade. O repasse de R$ 3.000,00 em dinheiro, alegado para 20/07/2025, não tem recibo nem lançamento no extrato da autora e ficou fora do cenário base, integrando apenas o cenário amplo (Anexo III, itens 3 e 5).
>
> **Pendências (seção 13).** (1) Alíquota interna de ICMS para materiais de construção no RICMS da UF em 2025; (2) faixas do Anexo I da LC 123/2006 não se aplicam (ré no Presumido); (3) termo inicial da atualização do saldo.
