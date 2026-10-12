---
name: apuracao-haveres
description: "Calcular e periciar haveres de sócio na dissolução parcial de sociedade (retirada, recesso, exclusão, morte) por balanço de determinação a preço de saída na data da resolução (CPC, arts. 599 a 609; CC, art. 1.031). Usar quando: (1) fixar a data da resolução pelo art. 605; (2) aplicar contrato social válido ou critério legal; (3) reavaliar ativos, passivos e contingências (CPC 25); (4) mensurar fundo de comércio sem projetar fluxo futuro; (5) integrar lucros, JCP e pro labore até a data (art. 608) com prescrição trienal; (6) apurar haveres líquidos, prazo de 90 dias, correção e juros; (7) criticar laudo com DCF ou responder quesitos. Acionar ao mencionar: apuração de haveres, dissolução parcial, balanço de determinação, retirada de sócio, sócio falecido, valor da quota, fundo de comércio, goodwill, aviamento, preço de saída, quanto vale minha parte, o perito usou fluxo de caixa. COMPLEMENTAR a valuation-capital-fechado: use ESTA para a quota do sócio em juízo; use aquela para avaliar a empresa em negociação."
metadata:
  version: "2.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Apuração de haveres na dissolução parcial de sociedade

Versão 2.0.0 (12/09/2026).

## Escopo

Perícia contábil de apuração de haveres quando a sociedade se resolve em relação a um sócio por retirada, recesso, exclusão judicial ou extrajudicial, falecimento ou liquidação da quota a pedido de credor (CPC, arts. 599 a 609; CC, arts. 1.026 a 1.031 e 1.085). A skill fixa a data da resolução por hipótese, aplica a hierarquia de critérios (contrato social válido; na omissão, balanço de determinação), levanta o balanço de determinação a preço de saída com reavaliação de ativos tangíveis e intangíveis, passivos e contingências, mensura o fundo de comércio como intangível existente na data da resolução, integra lucros, JCP e remuneração declarados até essa data, deduz adiantamentos e compensações e entrega os haveres líquidos com prazo de pagamento e termos iniciais de correção e juros. Papel padrão: perito do juízo; variante para assistente técnico de qualquer das partes, inclusive para a crítica de laudo que usou fluxo de caixa descontado.

Fora de escopo: avaliação de empresa para negociação, fusão ou aquisição (`valuation`, `valuation-capital-fechado`), auditoria do espólio e dos bens do sócio falecido (`auditoria-contabil-espolio`), cálculo da correção monetária e dos juros até o pagamento (`atualizacao-monetaria`), análise e redação de cláusulas do contrato social (`contrato-social`), prestação de contas da venda do estoque em cessão de quotas (`pericia-prestacao-contas-estoque`) e extração massiva de extratos (`analise-extratos-forense`).

## Princípio reitor

Haveres não são o que a empresa vale para um comprador: são o que o patrimônio líquido vale na data em que o vínculo se resolveu, dividido pela participação do sócio. O CPC, art. 608, parágrafo único, fecha a porta aos resultados posteriores: depois da data da resolução o ex-sócio tem direito apenas à correção monetária e aos juros. Por isso o fluxo de caixa descontado, que precifica lucros futuros, não serve para apurar haveres, e o STJ o afasta de forma estável desde 2015. O que serve é o balanço de determinação do art. 606: ativo e passivo a preço de saída na data da resolução, com os intangíveis, inclusive o fundo de comércio, mensurados como ativos existentes naquele dia.

Laudos neste domínio quebram por cinco causas, e a skill elimina cada uma por construção: data da resolução no dia da notificação em vez do sexagésimo dia (o script 1 recusa data incompatível com o art. 605); intangível ignorado ou avaliado por projeção (o script 2 exige resultados históricos normalizados e recusa o método DCF com a jurisprudência na mensagem); contingência possível deduzida como provável (o script 1 embute o CPC 25); lucros declarados contados duas vezes ou cobrados depois da prescrição trienal (o script 3 confere a data da deliberação contra a do ajuizamento e alerta para a dupla contagem); juros de 1% ao mês desde a data-base (o script 3 fixa os termos iniciais legais e entrega `parcelas.json` para a `atualizacao-monetaria`, que aplica o regime civil vigente).

## Workflow principal

```
1. PERÍMETRO     -> hipótese de resolução, contrato social consolidado, decisão do art. 604
                    (seção 1; references/fundamentacao-legal.md, seções 1 e 2)
2. DOCUMENTOS    -> termo de diligência, ECD, balancete, laudos, atas, pareceres
                    (references/quesitos-e-checklist.md, seções 1 a 3)
3. BALANÇO       -> scripts/balanco_determinacao.py: preço de saída conta a conta, CPC 25,
                    PL contábil x PL de determinação, sanidade
4. INTANGÍVEL    -> scripts/fundo_comercio.py: lucro excedente ou múltiplo, sensibilidade; DCF recusado
5. HAVERES       -> scripts/haveres_socio.py: quota, lucros e JCP (art. 608), prescrição trienal,
                    deduções, prazo (CC, art. 1.031, § 2º), termos de correção e juros, parcelas.json
6. CENÁRIOS      -> contrato x art. 606; com e sem fundo de comércio; lacunas quantificadas
7. ATUALIZAÇÃO   -> atualizacao-monetaria (regime civil) com parcelas.json
8. DELIVERABLE   -> laudo ou parecer (assets/template_laudo.md) + respostas aos quesitos
```

Executar as etapas 3 a 5 exclusivamente em Python, encadeando o JSON de cada script no seguinte. O balanço de determinação é impugnado conta a conta (CPC, art. 477), e só a memória gerada pelos scripts permite localizar cada ajuste, sua fonte e seu efeito nos haveres.

## 1. Data da resolução e hierarquia de critérios

A data da resolução é o primeiro parâmetro e muda tudo: o balanço é levantado nela, os lucros entram até ela e a correção corre a partir dela. O art. 605 do CPC a fixa por hipótese:

| Hipótese (`hipotese` no JSON) | Data da resolução | Marco documental | Dispositivo |
|---|---|---|---|
| `falecimento` | Data do óbito | Certidão de óbito | CPC, art. 605, I; CC, art. 1.028 |
| `retirada_imotivada` | Sexagésimo dia seguinte ao recebimento da notificação pela sociedade | Notificação com prova de recebimento (`data_notificacao`) | CPC, art. 605, II; CC, art. 1.029 |
| `recesso` | Dia do recebimento da notificação do dissidente | Notificação (`data_notificacao`) | CPC, art. 605, III |
| `retirada_justa_causa` e `exclusao_judicial` | Trânsito em julgado da decisão que dissolver a sociedade | Certidão de trânsito (`data_transito`) | CPC, art. 605, IV; CC, art. 1.030 |
| `exclusao_extrajudicial` | Data da assembleia ou reunião que deliberou a exclusão | Ata (`data_assembleia`) | CPC, art. 605, V; CC, art. 1.085 |

O erro mais comum, repetido pela v1 desta skill, é tratar a retirada imotivada como se a data fosse a do recebimento da notificação: isso vale só para o recesso. O script 1 calcula a data esperada a partir do marco informado e aborta se a `data_resolucao` divergir, porque um balanço levantado em data errada não se corrige por ajuste.

Critério de apuração (CPC, art. 604, II): o contrato social válido prevalece, inclusive quanto à forma e ao prazo de pagamento (CPC, art. 609); na omissão, aplica-se o balanço de determinação do art. 606 (STJ, AREsp 2.883.122; REsp 1.877.331). Quando a parte alega abusividade da cláusula (valor contábil puro, exclusão do intangível, parcelamento longo), o perito não decide: apura os dois cenários e a diferença, porque a validade é do juízo e a data e o critério podem ser revistos até o início da perícia (CPC, art. 607). O juiz determina o depósito da parte incontroversa (art. 604, § 1º), que o ex-sócio pode levantar desde logo (§ 2º) e que entra como dedução no script 3. A nomeação recai preferencialmente sobre especialista em avaliação de sociedades (art. 606, parágrafo único): o laudo declara essa qualificação.

## 2. Balanço de determinação a preço de saída

```bash
python3 scripts/balanco_determinacao.py --entrada assets/exemplo_balanco.json \
  --saida balanco.json --md balanco.md --csv balanco.csv
```

O JSON de entrada traz, para cada conta de ativo e de passivo, o valor contábil, o valor de saída, o fundamento e a fonte (folha dos autos ou documento); o script recusa ajuste sem fundamento. Preço de saída é o valor que a sociedade receberia pela venda do ativo ou pagaria pela transferência do passivo na data da resolução, em transação não forçada (NBC TG 46), e varia por classe:

| Classe | Preço de saída | Base documental |
|---|---|---|
| Caixa e aplicações | Saldo conciliado com rendimentos até a data | Extratos |
| Clientes | Valor de realização: perda real pela aging list e histórico, não a PDD fiscal; valor presente se de longo prazo | Aging list, razão |
| Estoques | Valor realizável líquido; obsoletos e sem giro a valor de liquidação | Inventário valorado, giro |
| Imobilizado | Valor de mercado por laudo (ABNT NBR 14653) ou cotações datadas para bens usados | Laudo, cotações |
| Intangíveis registrados | Custo amortizado se sem evidência de perda; avaliação própria se relevante | Razão, registro no INPI |
| Investimentos em sociedades | Balanço de determinação da investida ou valor de mercado | Demonstrações da investida |
| Passivos | Valor de liquidação na data: encargos contratuais pro rata, tributos com multa e juros, parcelamentos pelo saldo | Contratos, guias, planilhas |
| Contingências | CPC 25: provável provisiona (valor estimado menos o já provisionado); possível divulga; remota só registra | Parecer dos advogados, processos |

A saída traz o quadro contábil x preço de saída x ajuste por conta, as provisões adicionais, o PL contábil, o PL de determinação, os intangíveis já reconhecidos e o PL de determinação tangível (base do script 2). Sanidade embutida e obrigatória: ativo a preço de saída menos passivo a preço de saída menos provisões adicionais é igual ao PL de determinação, conferido por caminho independente (PL contábil mais ajustes de ativo menos ajustes de passivo menos provisões); divergência aborta a execução. Alertas cobrem provisão contábil que não concilia com as contingências informadas, contingência não provável com provisão registrada e PL negativo. Contas de lucros ou dividendos a pagar no passivo são anotadas na memória para evitar dupla contagem com o art. 608. Critérios por classe, tributo diferido sobre a mais-valia e balanço reconstruído sem balancete na data: `references/metodo-balanco-determinacao.md`, seções 1 a 4.

## 3. Fundo de comércio como intangível na data da resolução

```bash
python3 scripts/fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json \
  --balanco balanco.json --metodo lucro-excedente --saida fundo.json --md fundo.md
python3 scripts/fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json --metodo dcf
```

O goodwill gerado internamente não aparece no PL contábil (NBC TG 04), mas o art. 606 manda avaliar os intangíveis, e o STJ inclui fundo de comércio, aviamento e goodwill no balanço de determinação (REsp 2.174.631; REsp 1.892.139; AgInt no AgInt no AREsp 2.903.904). A questão é como medi-lo sem projetar o futuro. A skill usa dois métodos baseados em resultados históricos normalizados:

| Método (`--metodo`) | Fórmula | Parâmetros exigidos com fonte ou fundamento |
|---|---|---|
| `lucro-excedente` (padrão) | (lucro médio normalizado de 3 a 5 exercícios menos PL tangível x taxa de remuneração do capital) x fator | Taxa com fonte (série do SGS ou custo de oportunidade fundamentado); fator com justificativa por setor e dependência do sócio |
| `multiplo` (contraprova) | lucro médio normalizado x múltiplo menos PL tangível | Múltiplo com fundamento (transações ou laudos comparáveis) |
| `dcf` | Recusado com código 1 e mensagem que cita os precedentes | Nenhum: o script não calcula |

Normalização: cada exercício traz o lucro contábil e a lista de ajustes descritos (ganho na venda de imóvel já reavaliado no balanço, multa não recorrente, pro labore fora de mercado). Lucro excedente nulo ou negativo zera o fundo de comércio com alerta: o resultado histórico não remunera sequer o capital tangível, e não há intangível a reconhecer. A saída traz sensibilidade ao fator (mais ou menos um ano) e à taxa (mais ou menos um ponto), e uma nota jurídica para o laudo. Por que não DCF: a projeção precifica lucros posteriores à saída, que pertencem aos sócios que ficam e assumem o risco (CPC, art. 608, parágrafo único); o STJ a considera inadequada (REsp 1.877.331; REsp 1.904.252; REsp 1.900.838; AgInt nos EDcl no REsp 2.160.132). Se o contrato prevê DCF, o laudo registra a cláusula e a controvérsia, e a eficácia dela é do juízo. Sociedade de profissionais com fundo de comércio dependente da pessoa do sócio: `references/metodo-balanco-determinacao.md`, seção 5.

## 4. Lucros, JCP e remuneração até a data da resolução

Integram os haveres a participação nos lucros ou os JCP declarados pela sociedade até a data da resolução e, se for o caso, a remuneração como administrador (CPC, art. 608, caput). Três regras evitam erro:

1. Só o que foi declarado (deliberado) até a data e não pago. O resultado do exercício em curso já está dentro do PL de determinação e chega ao sócio pela quota; somá-lo de novo é dupla contagem.
2. O valor deliberado precisa ter saído do PL para o passivo (lucros a distribuir) no balanço de determinação; o script 3 alerta quando o balanço não tem essa conta.
3. A pretensão aos lucros não distribuídos prescreve em três anos da deliberação (CC, art. 206, § 3º; STJ, REsp 1.904.252), com interrupção retroativa à propositura (CPC, art. 240, § 1º). O script exclui os prescritos, lista o valor e aceita `--incluir-prescritos` quando a decisão determinar.

A sociedade pode pedir indenização compensável com os haveres (CPC, art. 602): entra em `--indenizacao-compensavel` apenas com a decisão que a reconheceu, nunca por alegação.

## 5. Haveres do sócio, pagamento, correção e juros

```bash
python3 scripts/haveres_socio.py --balanco balanco.json --fundo-comercio fundo.json \
  --participacao 25% --data-resolucao 30/06/2025 --data-ajuizamento 15/08/2025 \
  --lucros-declarados assets/exemplo_lucros_declarados.json \
  --remuneracao-administrador assets/exemplo_remuneracao_administrador.json \
  --adiantamentos assets/exemplo_adiantamentos.json --data-liquidacao 10/03/2026 \
  --saida haveres.json --md haveres.md --parcelas parcelas.json
```

Quota patrimonial é o PL de determinação com fundo de comércio multiplicado pela participação e pela fração integralizada (CC, art. 1.031, caput: montante efetivamente realizado). Haveres brutos somam quota, lucros e JCP integrados e remuneração; deduções são adiantamentos (inclusive o levantamento do depósito da parte incontroversa) e indenização compensável; haveres líquidos fecham com a soma das parcelas. O pagamento segue o contrato social e, no silêncio, 90 dias em dinheiro a partir da liquidação (CPC, art. 609; CC, art. 1.031, § 2º); prazo diverso exige `--fundamento-prazo`. A correção monetária corre desde a data da resolução (CPC, art. 608, parágrafo único) e os juros de mora, do dia seguinte ao fim do prazo de pagamento (CC, art. 397), salvo decisão que fixe termo diverso, que entra como premissa declarada. Índice e taxa não são escolhidos aqui: `parcelas.json` sai no formato da `atualizacao-monetaria` (`competencia`, `valor`, `descricao`, deduções com sinal negativo), que aplica o regime civil da Lei 14.905/2024 (CC, arts. 389 e 406) período a período. O "1% ao mês" da v1 não existe mais na skill. PL de determinação negativo zera a quota com alerta; eventual débito do sócio é questão jurídica marcada `[A VERIFICAR]`.

## 6. Crítica de laudo adverso e variante de assistente técnico

O assistente do sócio retirante concentra a crítica em: imobilizado mantido pelo custo histórico, intangível ignorado, provisão excessiva ou contingência possível deduzida, lucros deliberados omitidos. O assistente da sociedade concentra em: data da resolução errada, passivos e encargos não apropriados, resultado com itens não recorrentes na média, dependência pessoal do fundo de comércio, adiantamentos e compensações não deduzidos, lucros prescritos. Contra laudo que usou DCF, a crítica tem três movimentos: demonstrar que o método projeta resultados posteriores à resolução (art. 608, parágrafo único), citar a orientação das duas Turmas do STJ com a identificação completa e sem a palavra "vinculante", e apresentar o parecer divergente com o balanço de determinação e o intangível mensurado pelo script 2, em quadro comparativo que explique a diferença. Em qualquer papel a memória é a dos scripts; mudam as premissas declaradas, nunca o método. Roteiro de quesitos por parte: `references/fundamentacao-legal.md`, seção 10.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler contrato social consolidado, decisão do art. 604, balancete, ECD, laudos de avaliação, atas e pareceres antes de montar os JSON; conferir se o PDF tem camada de texto |
| `bash` | Executar os três scripts em Python e encadear o JSON de um na entrada do seguinte; extrair saldos da ECD com script simples |
| `create_file` | Gravar os JSON de entrada, as saídas (JSON, CSV, Markdown, `parcelas.json`) e o laudo em `/mnt/user-data/outputs` |
| `web_search` | Conferir a redação vigente de artigo, a situação de precedente e a série do SGS antes de citar; nunca para substituir documento dos autos nem para obter taxa de memória |

| Skill complementar | Quando acionar |
|---|---|
| `atualizacao-monetaria` | Atualizar os haveres a partir de `parcelas.json`, regime civil, com os termos iniciais declarados pelo script 3 |
| `valuation-capital-fechado` e `valuation` | Quando a controvérsia for de negociação ou de avaliação econômica da empresa, não de haveres em juízo |
| `contrato-social` | Análise de cláusula de haveres ambígua, de critério contratual ou de previsão de DCF antes de fixar os cenários |
| `auditoria-contabil-espolio` | Falecimento de sócio com necessidade de auditar o espólio e os bens do falecido fora da sociedade |
| `pericia-prestacao-contas-estoque` | Cessão de quotas com cláusula de repasse do produto do estoque |
| `analise-extratos-forense` | Extratos extensos para localizar adiantamentos, retiradas e pagamentos de lucros ao sócio |
| `chelfo-docx-brand` | Conversão do laudo ou parecer em `.docx` no padrão institucional, sob pedido explícito |
| `chelfo-skill-forge` | Qualquer manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/balanco_determinacao.py` | Confere a data da resolução pela hipótese do art. 605; quadro contábil x preço de saída x ajuste por conta; contingências pelo CPC 25; PL contábil, PL de determinação e PL tangível; sanidade e alertas | `python3 scripts/balanco_determinacao.py --entrada assets/exemplo_balanco.json --saida balanco.json --md balanco.md --csv balanco.csv` |
| `scripts/fundo_comercio.py` | Lucro médio normalizado, remuneração do capital, lucro excedente, fundo de comércio por lucro excedente ou múltiplo, sensibilidade, nota jurídica; recusa DCF | `python3 scripts/fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json --balanco balanco.json --metodo lucro-excedente --saida fundo.json --md fundo.md` |
| `scripts/haveres_socio.py` | Quota patrimonial, lucros e JCP com prescrição trienal, remuneração, deduções, haveres brutos e líquidos, prazo e termos de correção e juros, `parcelas.json` | `python3 scripts/haveres_socio.py --balanco balanco.json --fundo-comercio fundo.json --participacao 25% --data-resolucao 30/06/2025 --lucros-declarados lucros.json --adiantamentos adiant.json --data-ajuizamento 15/08/2025 --saida haveres.json --md haveres.md` |

Todos em Python 3.11 com biblioteca padrão, `Decimal` com ROUND_HALF_UP e arredondamento só na apresentação, números no padrão brasileiro ou técnico, datas em dd/mm/aaaa, saída JSON com `premissas`, `locale`, `arredondamento`, `sanidade`, `alertas` e `memoria`. Erro de validação sai com código 1 e mensagem `ERRO de validação:`. Exemplos de entrada: `assets/exemplo_balanco.json` (script 1); `assets/exemplo_fundo_comercio.json` (script 2); `assets/exemplo_lucros_declarados.json`, `exemplo_remuneracao_administrador.json` e `exemplo_adiantamentos.json` (script 3).

## Estrutura do output

Template completo, com exemplo preenchido a partir dos dados fictícios de `assets/`, em `assets/template_laudo.md`. Seções obrigatórias do laudo ou parecer:

1. Objeto e limites (o que é do juízo: validade da cláusula, abusividade, prescrição, consequência da recusa de exibição).
2. Quesitos de cada origem com remissão à seção da resposta.
3. Documentos examinados, com folha e origem, e o que faltou.
4. Hipótese de resolução, data da resolução e critério fixado (CPC, arts. 604 e 605), com a cláusula do contrato transcrita.
5. Metodologia (preço de saída, CPC 25, mensuração do intangível, art. 608, deduções).
6. Balanço de determinação conta a conta, provisões, PL contábil e PL de determinação, sanidade.
7. Fundo de comércio: série normalizada, parâmetros com fonte, resultado e sensibilidade.
8. Lucros, JCP e remuneração até a data, com prescrição.
9. Haveres brutos, deduções e haveres líquidos; prazo de pagamento; termos de correção e juros.
10. Cenários (critério contratual x legal; com e sem fundo de comércio; lacunas) com a diferença em reais.
11. Respostas aos quesitos, uma a uma, com remissão ao quadro ou à memória.
12. Conclusão com os haveres na data da resolução e os termos de atualização.
13. Memória de cálculo e anexos (JSON, CSV e Markdown dos três scripts; `parcelas.json`; comandos executados).
14. Pendências de verificação.

Exemplo de quadro de haveres (saída do script 3 com os exemplos de `assets/`):

| Rubrica | R$ |
|---|---:|
| PL de determinação (CPC, art. 606) | 490.000,00 |
| Fundo de comércio na data da resolução | 353.400,00 |
| Quota patrimonial (25%) | 210.850,00 |
| Lucros declarados e não pagos (art. 608) | 21.000,00 |
| Remuneração como administrador (art. 608) | 16.000,00 |
| Haveres brutos | 247.850,00 |
| Levantamento da parte incontroversa (art. 604, § 2º) | (30.000,00) |
| Haveres líquidos em 30/06/2025 | 217.850,00 |

Exemplo de resposta a quesito:

> Quesito 1 do réu: "Qual a data da resolução da sociedade, considerando que a notificação de retirada foi recebida em 01/05/2025?"
> Resposta: A data da resolução é 30/06/2025. Na retirada imotivada de sociedade por prazo indeterminado, o art. 605, II, do CPC fixa a resolução no sexagésimo dia seguinte ao do recebimento, pela sociedade, da notificação do sócio retirante, e não no dia do recebimento, que é a regra do inciso III, própria do recesso. O balanço de determinação do Anexo I foi levantado em 30/06/2025, com o balancete dessa data conciliado com os extratos (fls. 210 a 252).

Exemplo de crítica a laudo com fluxo de caixa descontado:

> Quesito 3 do autor: "O método de fluxo de caixa descontado adotado pelo assistente da parte é adequado à apuração dos haveres?"
> Resposta: Não. O método projeta resultados de exercícios posteriores a 30/06/2025, enquanto o art. 608, parágrafo único, do CPC limita o ex-sócio, após a data da resolução, à correção monetária e aos juros. A Terceira e a Quarta Turmas do STJ consideram o fluxo de caixa descontado inadequado para apuração de haveres e adotam o balanço de determinação com o fundo de comércio avaliado na data da resolução (REsp 1.877.331, Terceira Turma, j. 13/04/2021; REsp 1.904.252, Quarta Turma, j. 22/08/2023; REsp 2.174.631, Terceira Turma, j. 17/03/2025). Pelo lucro excedente (Anexo II), o fundo de comércio em 30/06/2025 é de R$ 353.400,00, e a quota do autor, de R$ 210.850,00, contra R$ 487.500,00 apurados pelo assistente por projeção de dez anos de lucros.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- CPC/2015: arts. 599 a 609 (dissolução parcial e apuração de haveres; textos dos arts. 602, 604, 605, 606, 608 e 609 verificados em 12/09/2026 e transcritos em `references/fundamentacao-legal.md`), 240, § 1º (interrupção da prescrição retroativa à propositura), 373 e § 1º (ônus e distribuição dinâmica), 396 a 400 (exibição), 420 (exibição integral de livros na liquidação de sociedade e na sucessão por morte de sócio), 464 a 480 (perícia; art. 473, § 2º, limites do perito).
- CC: arts. 1.026, parágrafo único, 1.028, 1.029, 1.030, 1.031 e §§ 1º e 2º, 1.085 (resolução da sociedade em relação a um sócio e liquidação da quota), 206, § 3º (prescrição trienal), 389, parágrafo único, 397 e 406 (correção, mora e taxa legal, Lei 14.905/2024).
- NBC TG 25 (CPC 25, contingências), NBC TG 46 (valor justo), NBC TG 04 (intangível e goodwill gerado internamente), NBC TG 01 (valor recuperável), NBC TG 16 (estoques), NBC TP 01 (R1) e NBC PP 01 (R1); ABNT NBR 14653 (avaliação de bens).

Jurisprudência verificada em 12/09/2026 (somente esta; identificação completa e links em `references/fundamentacao-legal.md`, seção 5): STJ, REsp 1.335.619 (Terceira Turma, j. 03/03/2015); REsp 1.877.331 (Terceira Turma, j. 13/04/2021); REsp 1.904.252 (Quarta Turma, j. 22/08/2023); REsp 1.892.139 (Terceira Turma, j. 08/10/2024); REsp 2.174.631 (Terceira Turma, j. 17/03/2025); REsp 1.900.838 (Terceira Turma, j. 28/04/2025); AgInt nos EDcl no REsp 2.160.132 (Terceira Turma, j. 28/04/2025); AREsp 2.883.122 (Terceira Turma, j. 22/09/2025); AgInt no AgInt no AREsp 2.903.904 (Quarta Turma, j. 08/06/2026); AgInt no AREsp 1.736.426 (Quarta Turma, j. 25/10/2021, orientativo). Todas são decisões de Turma: orientação consolidada, não vinculante.

Protocolo antifabricação: taxa de remuneração do capital, índice de correção, taxa legal, número de Tema, Súmula ou REsp fora da lista acima e redação literal de artigo exigem verificação em fonte oficial (planalto.gov.br, stj.jus.br, bcb.gov.br/SGS, cfc.org.br) na data do laudo. Sem verificação, marcar `[A VERIFICAR]` ao lado e listar na seção de pendências. Toda afirmação sensível ao tempo leva data de referência.

Pendências de verificação desta versão: Informativo STJ 864 (REsp 2.223.719-SP); Enunciados das Jornadas de Direito Comercial do CJF; existência de tema repetitivo sobre haveres; orientação sobre haveres negativos; inciso do § 3º do art. 206 do CC aplicado no REsp 1.904.252; termo inicial dos juros (citação x fim do prazo de pagamento); Lei 6.404/1976, art. 45, para a anônima fechada; tributo diferido sobre a mais-valia; nove precedentes citados pela v1 e não conferidos. Lista consolidada em `references/fundamentacao-legal.md`, seção 12.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | CC e CPC com dispositivo e textos verificados, prova e exibição, normas técnicas, dez precedentes verificados com links, ônus, prescrição, limites do perito, roteiro de quesitos, pendências | Etapa 1, redação do laudo e resposta a quesitos |
| `references/metodo-balanco-determinacao.md` | Preço de saída por classe, passivos e contingências, balanço reconstruído, fundo de comércio (métodos, normalização, parâmetros, limites), lucros até a data sem dupla contagem, exemplo numérico, armadilhas | Etapas 3, 4 e 5 |
| `references/quesitos-e-checklist.md` | Documentos por etapa e detentor, termo de diligência, diligências externas, quesitos com orientação de resposta, checklist de pré-entrega, armadilhas | Etapas 2 e 8 e pré-entrega |
| `assets/template_laudo.md` | Template do laudo e do parecer com exemplo preenchido | Etapa 8 |
| `assets/exemplo_*.json` | Schemas de entrada dos três scripts com dados fictícios encadeáveis | Etapas 3, 4 e 5 |

## Extensão e manutenção

Como estender esta skill sem quebrá-la:

1. Nova hipótese de resolução (por exemplo, liquidação da quota a pedido de credor com marco próprio): adicionar a entrada em `HIPOTESES` de `scripts/balanco_determinacao.py` e de `scripts/haveres_socio.py`, com dispositivo, regra, campo do marco e dias, e a linha na tabela da seção 1.
2. Novo método de mensuração do intangível baseado em resultados históricos (por exemplo, capitalização do lucro excedente a taxa declarada): acrescentar o ramo em `calcular()` de `scripts/fundo_comercio.py` com parâmetros que exijam `fonte` ou `fundamento`, manter a recusa do DCF e a nota jurídica, e incluir a linha na tabela da seção 3.
3. Nova classe de ativo ou passivo com critério específico de preço de saída: acrescentar a linha na tabela da seção 2 e o detalhamento em `references/metodo-balanco-determinacao.md`; o script 1 já aceita qualquer conta com fundamento.
4. Novo precedente conferido: mover da seção 6 ou 12 para a seção 5 de `references/fundamentacao-legal.md`, com identificação completa, data de conferência e link, e retirar da lista de pendências; se a orientação sobre DCF mudar, revisar `RECUSA_DCF` e `NOTA_JURIDICA` no script 2.
5. Versionamento SemVer: novo precedente, nova hipótese ou novo critério por classe é minor; mudança de contrato de saída dos scripts (chaves do JSON, formato de `parcelas.json`) é major.

Manutenção desta skill: acionar `chelfo-skill-forge`.
