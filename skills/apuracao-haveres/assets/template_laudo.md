# Template do laudo pericial de apuração de haveres

Uso: substituir os campos `[ENTRE COLCHETES]`, manter as quatorze seções, anexar as saídas dos três scripts e `parcelas.json`. Para o parecer de assistente técnico, trocar o título por "Parecer técnico divergente" e acrescentar, na seção 10, o quadro comparativo com o laudo oficial. Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_ApuracaoHaveres_vN.md`. Conversão para `.docx` só sob pedido, pela skill `chelfo-docx-brand`.

---

# Laudo pericial contábil: apuração de haveres

**Processo nº** [0000000-00.0000.0.00.0000]
**Juízo** [Vara] da Comarca de [Cidade/UF]
**Ação** Dissolução parcial de sociedade com apuração de haveres (CPC, arts. 599 a 609)
**Autor(a)** [Nome do sócio, espólio ou sucessores]
**Ré** [Razão social da sociedade] (CNPJ [00.000.000/0000-00]) e sócios remanescentes
**Perito(a)** [Nome], contador(a), CRC [UF-000000/O-0], especialista em avaliação de sociedades (CPC, art. 606, parágrafo único)
**Data do laudo** [dd/mm/aaaa]

---

## 1. Objeto e limites

Apurar os haveres de [nome] em razão de [retirada imotivada / recesso / exclusão judicial / exclusão extrajudicial / falecimento] da sociedade [razão social], na data da resolução fixada em [dd/mm/aaaa] e pelo critério definido na decisão de fls. [N] (CPC, art. 604). Ficam fora do exame, por serem matéria do juízo: a validade ou abusividade da cláusula contratual de haveres, a ocorrência de justa causa, a prescrição dos lucros reclamados, a consequência da recusa de exibição de documentos (CPC, art. 400) e a indenização compensável não reconhecida em decisão (CPC, art. 602). O perito não emite opinião além do exame técnico (CPC, art. 473, § 2º).

---

## 2. Quesitos

| Origem | Nº | Resumo do quesito | Resposta na seção |
|---|---|---|---|
| Juízo | 1 | [resumo] | 11.1 |
| Autor | 1 | [resumo] | 11.2 |
| Ré | 1 | [resumo] | 11.3 |

---

## 3. Documentos examinados

| Documento | Folhas ou origem | Uso |
|---|---|---|
| Contrato social consolidado e alterações | fls. [N] | Participação, cláusula de haveres, prazo |
| [Notificação de retirada com recebimento / certidão de óbito / ata de exclusão / certidão de trânsito] | fls. [N] | Data da resolução (CPC, art. 605) |
| Balancete de [dd/mm/aaaa] e ECD de [anos] | fls. [N] | Balanço de partida e DREs |
| Laudo de avaliação do imóvel [endereço] | fls. [N] | Preço de saída |
| Aging list, inventário valorado, contratos de empréstimo | fls. [N] | Ajustes |
| Parecer dos advogados sobre processos | fls. [N] | Contingências |
| Atas de deliberação de lucros e comprovantes de pagamento | fls. [N] | CPC, art. 608 |
| Guia e alvará do depósito da parte incontroversa | fls. [N] | Dedução |

Documentos requisitados e não apresentados: [lista com data do termo de diligência e efeito na seção 10].

---

## 4. Hipótese, data da resolução e critério

Hipótese: [retirada imotivada de sociedade por prazo indeterminado]. Marco documental: [notificação recebida pela sociedade em dd/mm/aaaa, fls. N]. Data da resolução: [dd/mm/aaaa], [sexagésimo dia seguinte ao recebimento (CPC, art. 605, II)], coincidente com a fixada na decisão de fls. [N].

Cláusula [N] do contrato social: "[transcrição literal]". Critério aplicado: [balanço de determinação do art. 606 do CPC, por omissão do contrato / critério contratual, com o cenário legal na seção 10].

---

## 5. Metodologia

Balanço de determinação na data da resolução com ativo e passivo a preço de saída (CPC, art. 606; NBC TG 46), ajustes conta a conta com fundamento e fonte; contingências pelo CPC 25; fundo de comércio mensurado como intangível existente na data pelo método do lucro excedente sobre resultados históricos normalizados, sem projeção de fluxos futuros; lucros, JCP e remuneração declarados até a data (CPC, art. 608) com prescrição trienal; deduções documentadas; prazo de pagamento e termos de correção e juros (CPC, art. 609; CC, art. 1.031, § 2º). Cálculos pelos scripts `balanco_determinacao.py`, `fundo_comercio.py` e `haveres_socio.py` da skill apuracao-haveres v2.0.0, em `Decimal` com arredondamento só na apresentação.

---

## 6. Balanço de determinação

| Conta | Contábil (R$) | Preço de saída (R$) | Ajuste (R$) | Fundamento e fonte |
|---|---:|---:|---:|---|
| [conta do ativo] | [valor] | [valor] | [valor] | [fundamento, fls. N] |
| Total do ativo | [valor] | [valor] | [valor] | |
| [conta do passivo] | [valor] | [valor] | [valor] | [fundamento, fls. N] |
| Total do passivo | [valor] | [valor] | [valor] | |

Contingências (CPC 25): [tabela com descrição, tipo, valor, probabilidade, provisionado, provisão adicional]. Possíveis divulgadas: R$ [valor]; efeito hipotético na quota do autor: R$ [valor].

| Rubrica | R$ |
|---|---:|
| PL contábil | [valor] |
| Ajustes de ativo | [valor] |
| Ajustes de passivo | ([valor]) |
| Provisões adicionais | ([valor]) |
| PL de determinação | [valor] |
| Intangíveis já reconhecidos | [valor] |
| PL de determinação tangível | [valor] |

Sanidade: ativo a preço de saída menos passivo a preço de saída menos provisões adicionais = PL de determinação [OK].

---

## 7. Fundo de comércio

| Exercício | Lucro contábil (R$) | Ajustes (R$) | Lucro ajustado (R$) |
|---|---:|---:|---:|
| [aaaa] | [valor] | [valor] | [valor] |

Lucro médio normalizado R$ [valor]; taxa de remuneração do capital [x%] (fonte: [série e data]); remuneração do capital tangível R$ [valor]; lucro excedente R$ [valor]; fator [n] ([fundamento]); fundo de comércio na data da resolução R$ [valor]. Sensibilidade: fator [n-1] R$ [valor]; fator [n+1] R$ [valor]; múltiplo [m] R$ [valor]. Nota: o valor mensura o intangível existente em [dd/mm/aaaa] e não projeta fluxos posteriores à resolução (CPC, art. 608, parágrafo único; STJ, REsp 1.877.331, REsp 1.904.252, REsp 2.174.631).

---

## 8. Lucros, JCP e remuneração até a data

| Deliberação | Descrição | Valor do sócio (R$) | Pago (R$) | Saldo (R$) | Situação |
|---|---|---:|---:|---:|---|
| [dd/mm/aaaa] | [ata] | [valor] | [valor] | [valor] | [exigível / prescrito] |

Remuneração como administrador devida e não paga: R$ [valor] ([competências]). Prescrição trienal conferida com o ajuizamento em [dd/mm/aaaa] (CC, art. 206, § 3º; CPC, art. 240, § 1º); valores excluídos: R$ [valor].

---

## 9. Haveres, prazo e termos de atualização

| Rubrica | R$ |
|---|---:|
| PL de determinação com fundo de comércio | [valor] |
| Quota patrimonial ([x%], integralizado [y%]) | [valor] |
| Lucros e JCP integrados (art. 608) | [valor] |
| Remuneração como administrador (art. 608) | [valor] |
| Haveres brutos | [valor] |
| Adiantamentos e levantamento da parte incontroversa | ([valor]) |
| Indenização compensável (art. 602, decisão de fls. N) | ([valor]) |
| Haveres líquidos em [dd/mm/aaaa] | [valor] |

Pagamento: [90 dias da liquidação (CC, art. 1.031, § 2º) / cláusula N do contrato]. Correção monetária desde [data da resolução] (CPC, art. 608, parágrafo único). Juros de mora a partir de [dia seguinte ao fim do prazo / termo fixado na decisão]. Índice e taxa: memória da skill `atualizacao-monetaria`, regime civil, anexo [N], a partir de `parcelas.json`.

---

## 10. Cenários

| Cenário | Critério | Fundo de comércio | Haveres líquidos (R$) | Diferença para o base (R$) |
|---|---|---|---:|---:|
| Base | [art. 606] | [incluído, lucro excedente] | [valor] | |
| Contratual | [cláusula N] | [conforme cláusula] | [valor] | [valor] |
| Sem intangível | [art. 606] | excluído | [valor] | [valor] |
| Lacuna [documento] | [art. 606] | [idem] | [valor] | [valor] |

O cenário base é o sustentado pelo perito; os demais quantificam o efeito das decisões reservadas ao juízo.

---

## 11. Respostas aos quesitos

### 11.1 Quesitos do juízo

> Quesito [N] do juízo: "[transcrição]"
> Resposta: [resposta objetiva com remissão à seção e ao anexo].

### 11.2 Quesitos do autor

### 11.3 Quesitos da ré

---

## 12. Conclusão

Na data da resolução de [dd/mm/aaaa], os haveres líquidos de [nome] são de R$ [valor] no cenário base, de R$ [valor] no cenário contratual e de R$ [valor] no cenário sem intangível. [Uma frase sobre a principal causa da diferença.] O valor se corrige desde [data] e vence juros a partir de [termo], conforme anexo [N].

---

## 13. Memória de cálculo e anexos

- Anexo I: `balanco.json`, `balanco.csv` e `balanco.md` (script 1), com comando executado.
- Anexo II: `fundo.json` e `fundo.md` (script 2); `fundo_multiplo.json` (contraprova).
- Anexo III: `haveres.json`, `haveres.md` e `parcelas.json` (script 3).
- Anexo IV: laudos de avaliação, aging list, inventário, pareceres e atas.
- Anexo V: memória de atualização monetária (`atualizacao-monetaria`).
- Comandos executados: [linhas de comando com os arquivos de entrada].

---

## 14. Pendências de verificação

| Nº | Item | Efeito no laudo | Responsável |
|---|---|---|---|
| 1 | [Série do SGS adotada para a taxa de remuneração do capital] | [fundo de comércio] | [perito] |
| 2 | [Parecer jurídico sobre o processo N não apresentado] | [contingência] | [ré] |
| 3 | [Termo inicial dos juros fixado na decisão] | [anexo V] | [juízo] |

---

## Exemplo preenchido (dados fictícios de `assets/`, resumido)

> **Processo nº** 0000000-00.0000.0.00.0000. **Autor** João da Silva, sócio com 25% da **ré** Alfa Comércio Ltda. (CNPJ 00.000.000/0000-00). **Hipótese** retirada imotivada; notificação recebida pela sociedade em 01/05/2025. **Data da resolução** 30/06/2025 (CPC, art. 605, II). **Contrato social** omisso quanto ao critério: aplicado o balanço de determinação do art. 606.
>
> **Balanço de determinação (seção 6).** Ativo contábil R$ 950.000,00 e a preço de saída R$ 1.025.000,00: imóvel sede de R$ 400.000,00 para R$ 550.000,00 (laudo de avaliação, fls. 300 a 340), clientes menos R$ 30.000,00 (aging list), estoques menos R$ 20.000,00 (obsoletos), veículos menos R$ 25.000,00 (cotações). Passivo contábil R$ 470.000,00 e a preço de saída R$ 475.000,00 (encargos pro rata do empréstimo). Contingências: reclamação trabalhista provável de R$ 80.000,00 com R$ 20.000,00 provisionados, provisão adicional de R$ 60.000,00; auto de ICMS de R$ 150.000,00 possível, divulgado; ação cível remota de R$ 50.000,00, registrada. PL contábil R$ 480.000,00; PL de determinação R$ 490.000,00; PL tangível R$ 460.000,00. Sanidade: 1.025.000,00 menos 475.000,00 menos 60.000,00 = 490.000,00.
>
> **Fundo de comércio (seção 7).** Lucros ajustados de 2020 a 2024: R$ 110.000,00 (expurgado ganho de R$ 40.000,00 na venda de imóvel), R$ 180.000,00, R$ 215.000,00 (adicionada multa não recorrente de R$ 15.000,00), R$ 170.000,00 e R$ 190.000,00; média R$ 173.000,00. Remuneração do capital tangível R$ 55.200,00 (12%, taxa fictícia com fonte declarada); lucro excedente R$ 117.800,00; fator 3 (comércio varejista com clientela de rotatividade média); fundo de comércio R$ 353.400,00. Sensibilidade: R$ 235.600,00 (fator 2) a R$ 471.200,00 (fator 4); múltiplo 4 como contraprova: R$ 232.000,00.
>
> **Lucros e remuneração (seção 8).** Deliberações de 30/04/2022 (R$ 12.500,00), 28/04/2023 (R$ 15.000,00 = 25% de R$ 60.000,00) e 30/04/2025 (R$ 10.000,00, pagos R$ 4.000,00). Ajuizamento em 15/08/2025: a parcela de 2022 está prescrita (CC, art. 206, § 3º; REsp 1.904.252) e foi excluída com o valor listado; integrados R$ 21.000,00. Pro labore de maio e junho de 2025 não pago: R$ 16.000,00.
>
> **Haveres (seção 9).** Quota patrimonial (R$ 490.000,00 + R$ 353.400,00) x 25% = R$ 210.850,00; haveres brutos R$ 247.850,00; levantamento da parte incontroversa em 10/09/2025 (alvará, fls. 150) R$ 30.000,00; haveres líquidos R$ 217.850,00 em 30/06/2025. Pagamento em 90 dias da liquidação (CC, art. 1.031, § 2º); correção desde 30/06/2025; juros a partir de 09/06/2026 (liquidação em 10/03/2026). `parcelas.json` com seis lançamentos, soma igual aos haveres líquidos.
>
> **Cenários (seção 10).** Sem intangível: quota R$ 122.500,00 e haveres líquidos R$ 129.500,00. Com o múltiplo como método: quota R$ 180.500,00 e haveres líquidos R$ 187.500,00.
>
> **Quesito 2 da ré (seção 11):** "O lucro de 2021 deliberado em 30/04/2022 ainda pode ser cobrado pelo autor?"
> **Resposta:** Pelo critério adotado, não. A pretensão aos lucros deliberados prescreve em três anos da deliberação (CC, art. 206, § 3º; STJ, REsp 1.904.252, Quarta Turma, j. 22/08/2023). A deliberação é de 30/04/2022 e o ajuizamento, de 15/08/2025, mais de três anos depois, de modo que os R$ 12.500,00 foram excluídos dos haveres e listados no Anexo III. A decisão sobre a prescrição é do juízo; se afastada, o valor se soma aos haveres brutos, que passariam a R$ 260.350,00.
>
> **Pendências (seção 14).** (1) Série do SGS para a taxa de remuneração do capital; (2) termo inicial dos juros se a decisão fixar a citação; (3) parecer jurídico atualizado sobre o auto de ICMS.
