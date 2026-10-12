---
name: pericia-prestacao-contas-covid-saude
description: "Analisar em perícia contábil a prestação de contas de recursos de saúde da covid-19 (FNS, LC 173/2020, fontes vinculadas) em ação civil pública, improbidade ou tomada de contas. Usar quando: (1) montar plano de trabalho, termo de diligência e ofícios; (2) controlar pendências e prazos e peticionar no atraso das partes; (3) conciliar receitas e despesas por fonte, estágio e mês; (4) apontar pagamento sem liquidação e NF anterior ao empenho; (5) testar cada despesa: objeto covid, contratação emergencial, entrega; (6) sinalizar sobrepreço, fracionamento e fornecedor novo ou sancionado; (7) quantificar o sem comprovação e o desvio de finalidade; (8) redigir laudo e quesitos. Acionar ao mencionar: verba da covid, prestação de contas da saúde, FNS, LC 173, fonte de recursos, empenho e liquidação, dispensa emergencial, Lei 13.979, improbidade, termo de diligência, as partes não mandaram os documentos. COMPLEMENTAR a licitacoes-contratos: use ESTA para a prestação de contas; use aquela para PNCP, CEIS e preços."
metadata:
  version: "1.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Perícia contábil em prestação de contas de recursos da covid-19 na saúde

Versão 1.0.0 (12/09/2026).

## Escopo

Perícia contábil judicial sobre a aplicação e a prestação de contas de recursos públicos de saúde recebidos para o enfrentamento da covid-19 (transferências fundo a fundo do Fundo Nacional de Saúde, auxílio financeiro da LC 173/2020, recursos estaduais e recursos próprios vinculados) por município, estado, consórcio, fundação ou entidade conveniada, em ação civil pública, ação de improbidade (Lei 8.429/1992 na redação da Lei 14.230/2021), ação de prestação de contas, ação popular ou tomada de contas. Cobre o planejamento da perícia e as diligências, a conciliação entre recursos recebidos e despesas por fonte, a verificação dos estágios da despesa (Lei 4.320/1964), a aderência de cada gasto à finalidade covid, a regularidade formal das contratações emergenciais (Lei 13.979/2020; Lei 14.133/2021, art. 75, VIII), a evidência de entrega, os indícios de sobrepreço, fracionamento e fornecedor inidôneo, a quantificação do que ficou sem comprovação ou com desvio de finalidade e o laudo com resposta a quesitos. O perito descreve fatos contábeis; a qualificação como improbidade, dolo ou dano é do juízo.

Fora de escopo: pesquisa de preços e consulta ao PNCP, CEIS e CNEP (`licitacoes-contratos`, usada como apoio na etapa 4), capacidade de pagamento do ente (`capag-setor-publico`), rastreamento de lavagem (`pericia-lavagem-dinheiro`), extração massiva de extratos (`analise-extratos-forense`), honorários e proposta (`proposta-pericial-judicial`), leitura panorâmica dos autos (`resumo-autos`, `mapa-processo`) e atualização dos valores apurados (`atualizacao-monetaria`).

## Princípio reitor

Perícia de verba pública começa pela trilha da fonte de recursos. Cada real recebido tem uma fonte (código de fonte ou destinação), uma conta bancária específica (Lei 8.080/1990, art. 33) e um objeto permitido pela norma que o transferiu (LRF, art. 8º, parágrafo único). Por isso o trabalho é uma conciliação em três colunas, recebido por fonte; empenhado, liquidado e pago por fonte; saldo e devoluções, seguida de teste despesa a despesa. Laudo que começa pelas notas fiscais sem fechar a fonte produz achados soltos que o assistente técnico derruba com um extrato.

Sem a documentação da execução orçamentária não há número. A skill trata a requisição de documentos como etapa técnica de primeira classe, com registro, prazo e consequência (CPC, arts. 400 e 473, § 3º), e não como espera: o perito que "aguarda as partes" sem termo de diligência, sem painel de pendências e sem petição ao juízo perde o prazo do art. 477 e entrega um laudo que não declara a própria limitação. Toda lacuna documental vira registro datado no laudo, e a consequência probatória da não exibição fica com o juízo.

## Workflow principal

```
0. Fase zero     -> assets/template_plano_trabalho.md (objeto do saneamento, quesitos, método,
                    amostragem, cronograma, documentos por parte); scripts/checklist_documental_covid.py
                    (painel recebido x pendente, termo de diligência, ofícios, o que peticionar)
1. Fontes        -> inventário dos repasses (Portal FNS, portarias nos autos, LC 173/2020), contas
                    específicas e razão por fonte; transcrever em assets/exemplo_receitas.csv
2. Conciliação   -> scripts/conciliacao_fonte_recurso.py: recebido x empenhado, liquidado e pago
                    por fonte e mês; restos a pagar; devoluções; inconsistências de estágio
3. Testes        -> scripts/matriz_despesas_covid.py: aderência, contratação, NF, atesto, entrega,
                    preço de referência, fracionamento, fornecedor (references/matriz-de-testes-e-red-flags.md)
4. Quantificação -> totais por classe e por fonte; base de eventual ressarcimento (valores nominais)
5. Laudo         -> assets/template_laudo.md; quesitos (references/fundamentacao-legal.md, seção 7);
                    atualização em atualizacao-monetaria; docx só sob pedido em chelfo-docx-brand
```

Executar as etapas 0, 2 e 3 em Python, com os CSV transcritos dos autos. Conciliação de dezenas de empenhos feita à mão perde centavos e, pior, perde a fonte.

## 1. Fase zero: plano de trabalho, termo de diligência e controle de prazo

A perícia nomeada e ainda não iniciada tem quatro entregas antes de qualquer número, nesta ordem:

1. Ler a decisão de saneamento (CPC, art. 357) e a nomeação (art. 465): objeto, pontos controvertidos, prazo do laudo, quesitos já formulados e assistentes indicados no prazo de quinze dias (art. 465, § 1º). Proposta de honorários fica com `proposta-pericial-judicial`.
2. Redigir o plano de trabalho por `assets/template_plano_trabalho.md`: objeto conforme o saneamento, quesitos e pertinência, metodologia (conciliação por fonte e matriz de testes), critério de amostragem (censo abaixo do limite declarado; NBC TA 530 por analogia acima dele), documentos requeridos por parte com prazo, cronograma compatível com os arts. 465 e 477, data e local de início com ciência às partes (art. 474) e acesso dos assistentes às diligências (art. 466, § 2º).
3. Montar o registro de documentos (`assets/exemplo_registro_documentos.json`) e gerar o termo de diligência e as minutas de ofício ao ente, ao FNS ou Ministério da Saúde, ao tribunal de contas e ao banco (`references/roteiro-documental-e-diligencias.md`, seções 2 a 5). Documento em poder de terceiro é requerido por intermédio do juízo (arts. 380 e 401 a 404).
4. Atualizar o painel a cada resposta e peticionar sem esperar o prazo vencer.

```bash
python3 scripts/checklist_documental_covid.py --registro assets/exemplo_registro_documentos.json \
  --gerar todos --data-referencia 12/10/2026 --alerta-dias 20 --saida painel.json --md fase_zero.md
python3 scripts/checklist_documental_covid.py --registro registro.json --gerar oficio --destinatario tce --md oficio_tce.md
```

O painel calcula o limite de cada documento (pedido mais prazo), os dias de atraso, o resumo por responsável e os dias restantes do laudo, e sugere a petição adequada: intimação da parte sob as consequências do art. 400 quando o atraso é de parte; expedição ou reiteração de ofício quando é de terceiro; prorrogação do art. 476 (uma vez, metade do prazo) ou contagem do prazo a partir da juntada quando o laudo está a menos de `--alerta-dias` do vencimento; comunicação imediata com justificativa quando o prazo venceu, porque o art. 468, II, autoriza a substituição do perito que deixa de cumprir o encargo sem motivo legítimo. O que não vier entra no laudo como limitação declarada (`references/roteiro-documental-e-diligencias.md`, seção 6).

## 2. Inventário de fontes de recursos

Listar cada ingresso com data, fonte, origem normativa, documento e valor, no layout de `assets/exemplo_receitas.csv`. Origens típicas: portarias GM/MS de repasse covid citadas nos autos ou obtidas no relatório de repasses do FNS (número e data de cada portaria conferidos no ato, nunca de memória); auxílio financeiro da LC 173/2020, art. 5º, I (saúde e assistência social) e II (livre aplicação), em parcelas; recursos estaduais; rendimentos de aplicação da conta específica; devoluções (valor negativo). O código de fonte segue o plano de contas do ente; os códigos dos exemplos são fictícios.

Confrontar três visões antes de conciliar. Divergência entre elas é o primeiro achado e muda a leitura de tudo o que vem depois. O relatório de gestão e o SIOPS servem de conferência, não de fonte primária (LC 141/2012, arts. 36 a 39 [A VERIFICAR a numeração]).

| Visão | Documento | O que confere | Divergência típica |
|---|---|---|---|
| Repassador | Relatório do FNS por competência e portaria (Portal FNS, consulta por ente [A VERIFICAR URL vigente]); ordens bancárias da STN para a LC 173/2020 | Valor, data e objeto de cada parcela | Parcela creditada em conta diversa da específica; portaria não localizada |
| Banco | Extrato mensal da conta específica, com aplicação financeira | Ingresso efetivo, rendimentos, saídas e devoluções | Saída para conta de livre movimentação; rendimento não contabilizado |
| Contabilidade | Razão analítico por fonte e por conta; relação de empenhos por fonte | Classificação da receita e da despesa por fonte | Despesa em fonte diversa da conta pagadora; receita sem fonte |

## 3. Conciliação por fonte

```bash
python3 scripts/conciliacao_fonte_recurso.py --receitas assets/exemplo_receitas.csv \
  --despesas assets/exemplo_despesas.csv --saida conciliacao.json --md conciliacao.md --csv conciliacao_mensal.csv
python3 scripts/conciliacao_fonte_recurso.py --receitas r.csv --despesas d.csv --data-corte 31/12/2020
```

O script devolve, por fonte: recebido bruto, devolvido, recebido líquido, empenhado, liquidado, pago, saldo financeiro (recebido líquido menos pago), a empenhar, a liquidar e a pagar; por fonte e mês, o mesmo com saldos acumulados; restos a pagar processados e não processados em cada 31/12 presente nos dados (Lei 4.320/1964, art. 36); devoluções e rendimentos; e as inconsistências de estágio por empenho: pagamento sem liquidação (art. 62), liquidação acima do empenho e nota fiscal ou liquidação anterior ao empenho (art. 60), pagamento anterior à liquidação (arts. 62 e 63), liquidação sem documento fiscal (art. 63, § 2º) e despesa em fonte sem receita registrada. No nível da fonte, alerta quando o pago supera o recebido líquido ou o saldo acumulado fica negativo, sinal de uso de outra fonte ou de classificação errada (LRF, art. 8º, parágrafo único).

Teste de sanidade embutido: a soma por fonte e a soma por mês fecham com os totais e a quantidade de registros fecha com os arquivos; o script falha de propósito quando não fecha. Valores nominais; atualização em `atualizacao-monetaria`.

## 4. Testes despesa a despesa

```bash
python3 scripts/matriz_despesas_covid.py --despesas assets/exemplo_despesas.csv \
  --tolerancia-sobrepreco 20 --janela-fracionamento 30 --dias-fornecedor-novo 180 \
  --amostra-limite 50 --saida matriz.json --md matriz.md --csv matriz.csv
```

O mesmo CSV da conciliação recebe as colunas de teste (S/N; aderência admite D de duvidosa): aderência ao objeto da fonte, processo de contratação, pesquisa de preços, contrato, atesto, entrega comprovada, quantidade, preço unitário, preço de referência, data de constituição do fornecedor e sanção em CEIS/CNEP. O preço de referência e a consulta de sanções vêm de `licitacoes-contratos`, com fonte e data anexadas; sem referência o teste de preço não roda, e o script diz isso.

Classificação de cada despesa pelo achado mais grave, nesta ordem: desvio de finalidade (aderência N); sem comprovação (entrega N ou nota fiscal ausente em despesa liquidada ou paga); sobrepreço a apurar (preço unitário acima da referência além da tolerância, base igual à diferença vezes a quantidade); aderência a esclarecer (D); irregularidade formal (sem processo, sem pesquisa, sem contrato, sem atesto, estágio invertido, fracionamento, fornecedor novo ou sancionado); regular. Tolerância, janela e prazo de fornecedor novo são premissas declaradas no JSON, não normas. Fracionamento é agrupamento de empenhos do mesmo CNPJ encadeados dentro da janela, a conferir contra objeto e modalidade (Lei 14.133/2021, art. 75, § 1º). Acima de `--amostra-limite` despesas o script sugere amostra (todos os achados, maiores valores até a materialidade declarada e seleção sistemática dos restantes), que o plano de trabalho declara. Critérios e redação de cada achado em `references/matriz-de-testes-e-red-flags.md`.

## 5. Quantificação

A base de quantificação é o valor pago nas classes desvio de finalidade e sem comprovação, e a diferença de preço vezes a quantidade no sobrepreço a apurar; irregularidade formal e aderência a esclarecer não geram base, só registro. O script totaliza por classe, por fonte e por tipo de achado (não exclusivo) e confere que a soma por classe fecha com o universo. O laudo apresenta os totais como "valor sem comprovação nos autos" e "valor aplicado em objeto estranho à fonte", nominais nas datas de pagamento, e deixa ao juízo a imputação, a solidariedade e o ressarcimento (Lei 8.429/1992, art. 12; Tema 1.089 do STJ para o prosseguimento do ressarcimento quando prescritas as demais sanções).

## 6. Laudo, quesitos e limitações

Redigir pelo template `assets/template_laudo.md`. Cada achado é escrito em quatro partes, fato, evidência (documento e folha), norma contábil ou orçamentária e efeito quantificado, sem o vocabulário da improbidade (dolo, má-fé, enriquecimento) e sem concluir sobre responsabilidade (CPC, art. 473, § 2º). Documento requerido e não fornecido aparece na seção de documentos com a cronologia dos pedidos e na conclusão como limitação, com a indicação do que mudaria se viesse. Como assistente técnico, trocar o título por parecer, declarar a parte assistida e manter a mesma memória.

Checklist antes de entregar:

1. Sanidade OK nos dois scripts, com os JSON de memória em anexo.
2. Relatório do repassador, extratos e razão por fonte confrontados, com a data de cada consulta.
3. Toda despesa testada ou coberta pela amostra declarada no plano de trabalho.
4. Preço de referência e sanções com fonte e data; nenhum sobrepreço sem referência.
5. Achados sem qualificação jurídica; quantificação separada por classe e por fonte.
6. Pendências documentais e todo item `[A VERIFICAR]` listados na seção própria.
7. Valores nominais, com remissão a `atualizacao-monetaria`.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler decisão de saneamento, nomeação, inicial, portarias, extratos e processos de contratação antes de transcrever qualquer CSV; conferir se o PDF tem camada de texto |
| `bash` | Executar os três scripts em Python 3.11; o mesmo CSV de despesas alimenta `conciliacao_fonte_recurso.py` e `matriz_despesas_covid.py` |
| `create_file` | Gravar o registro JSON, os CSV transcritos, as saídas (JSON, Markdown, CSV), o plano de trabalho, o termo, os ofícios e o laudo em `/mnt/user-data/outputs` |
| `web_search` | Conferir, antes de citar, todo item marcado [A VERIFICAR]: portarias GM/MS, vigência da Lei 13.979/2020, artigos da LC 141/2012, URL do Portal FNS, acórdãos do TCU (gov.br/saude, planalto.gov.br, tcu.gov.br, stj.jus.br) |

| Skill | Quando |
|---|---|
| `licitacoes-contratos` | Preço de referência por item, consulta ao PNCP, CEIS, CNEP e CEPIM, análise do processo de dispensa |
| `atualizacao-monetaria` | Atualizar os valores quantificados até a data-base fixada pelo juízo |
| `analise-extratos-forense` | Extrair e estruturar extratos volumosos das contas específicas antes de montar o CSV de receitas |
| `capag-setor-publico` | Contexto fiscal do ente quando o juízo pedir |
| `pericia-lavagem-dinheiro` | Rastreamento do destino dos pagamentos a fornecedores suspeitos, se determinado |
| `proposta-pericial-judicial` | Proposta de honorários na nomeação (CPC, art. 465, § 2º) |
| `chelfo-docx-brand` | Conversão do laudo, do plano ou dos ofícios em `.docx` no padrão institucional, só sob pedido |
| `chelfo-skill-forge` | Manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/checklist_documental_covid.py` | Painel recebido x pendente com dias de atraso, prazo do laudo, termo de diligência, minutas de ofício e sugestão de petição | `python3 scripts/checklist_documental_covid.py --registro assets/exemplo_registro_documentos.json --gerar todos --data-referencia 12/10/2026 --md fase_zero.md` |
| `scripts/conciliacao_fonte_recurso.py` | Recebido x empenhado, liquidado e pago por fonte e mês; restos a pagar; devoluções; inconsistências de estágio; alertas por fonte; sanidade | `python3 scripts/conciliacao_fonte_recurso.py --receitas assets/exemplo_receitas.csv --despesas assets/exemplo_despesas.csv --saida conciliacao.json --md conciliacao.md` |
| `scripts/matriz_despesas_covid.py` | Classificação por despesa, totais por classe e fonte, fracionamento, fornecedores, preço x referência, amostra sugerida, sanidade | `python3 scripts/matriz_despesas_covid.py --despesas assets/exemplo_despesas.csv --saida matriz.json --md matriz.md` |

Todos usam só a biblioteca padrão, `Decimal` com `ROUND_HALF_UP` e arredondamento apenas na apresentação, aceitam número no padrão brasileiro e técnico, gravam `premissas`, `locale`, `arredondamento` e `memoria` no JSON e saem com `ERRO de validação:` quando falta coluna, data ou flag. Nenhum acessa a rede.

## Estrutura do output

Seções obrigatórias do laudo (template completo, com exemplo preenchido, em `assets/template_laudo.md`):

1. Objeto, conforme o saneamento, com a delimitação do que é do juízo.
2. Quesitos do juízo e das partes, com a seção da resposta.
3. Metodologia e amostragem, com as premissas declaradas (tolerância, janela, limite de amostra).
4. Documentos examinados e documentos requeridos e não fornecidos, com cronologia.
5. Inventário de fontes de recursos e confronto repassador x extrato x razão.
6. Conciliação por fonte (quadro resumo e restos a pagar).
7. Matriz de testes: classificação por despesa.
8. Achados, cada um em fato, evidência, norma e efeito.
9. Quantificação por classe e por fonte.
10. Conclusão, com limitações declaradas.
11. Resposta aos quesitos.
12. Encerramento, anexos (JSON, Markdown e CSV dos scripts, consultas, transcrições) e pendências de verificação.

Exemplo de quadro de conciliação (dados fictícios dos assets):

| Fonte | Recebido líquido | Empenhado | Liquidado | Pago | Saldo financeiro |
|---|---|---|---|---|---|
| 214-COVID | R$ 381.250,40 | R$ 347.500,00 | R$ 325.500,00 | R$ 343.500,00 | R$ 37.750,40 |
| 215-COVID | R$ 100.000,00 | R$ 120.000,00 | R$ 120.000,00 | R$ 120.000,00 | R$ -20.000,00 |
| LC173-SAUDE | R$ 240.000,00 | R$ 235.000,00 | R$ 235.000,00 | R$ 235.000,00 | R$ 5.000,00 |
| LC173-LIVRE | R$ 0,00 | R$ 25.000,00 | R$ 25.000,00 | R$ 25.000,00 | R$ -25.000,00 |

Exemplo de resposta a quesito:

> Quesito 3 do autor: "Houve aplicação de recursos vinculados em finalidade estranha ao enfrentamento da covid-19?"
> Resposta: Sim, em um empenho. O empenho E-2020/0158, de 20/05/2020, pago em 10/07/2020 (R$ 85.000,00) à Delta Construções e Pavimentação Ltda., com recursos da fonte LC173-SAUDE, tem por objeto "recapeamento asfáltico da Rua Principal" (processo 2020.0080, fls. [x]), objeto que não se enquadra nas ações e serviços públicos de saúde (LC 141/2012, arts. 2º a 4º) nem na destinação do art. 5º, I, da LC 173/2020. O valor integra a quantificação da seção 9 como "aplicado em objeto estranho à fonte". A qualificação do fato é do juízo.

Exemplo de resposta sobre documentação não fornecida:

> Quesito 2 do réu: "O perito examinou os processos administrativos de todas as contratações?"
> Resposta: Não. Dos 14 processos relacionados na inicial, o Município apresentou 6 (D05 do painel, recebidos em 30/09/2026); os 8 restantes foram requeridos no termo de diligência de 15/09/2026, reiterados por petição de 05/10/2026 e não haviam sido juntados na data deste laudo. Para esses 8 empenhos (R$ [valor]), a matriz registra "sem processo de contratação nos autos", e a classificação poderá mudar com a juntada. A consequência probatória da não exibição (CPC, art. 400) é matéria do juízo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_PrestacaoContasCovid_vN.md`.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- CF/1988: art. 37, caput e §§ 4º e 5º; art. 70, caput e parágrafo único (dever de prestar contas de quem gere dinheiro público); art. 71; art. 74; art. 167-C (regime extraordinário de contratação na calamidade, texto conferido); art. 198, §§ 2º e 3º.
- Lei 4.320/1964: art. 35 (regime da despesa pelo empenho); art. 36 (restos a pagar); arts. 58 a 65 (empenho, liquidação e pagamento; o art. 60 veda despesa sem prévio empenho, o art. 62 condiciona o pagamento à liquidação e o art. 63, § 2º, exige contrato, nota de empenho e comprovante da entrega); arts. 70 a 74 (fundos especiais); arts. 83 a 89 (contabilidade).
- LRF (LC 101/2000): art. 8º, parágrafo único (recurso vinculado só atende ao objeto da vinculação, mesmo em exercício diverso); art. 50, I (disponibilidade por destinação); art. 65 (calamidade).
- Lei 8.080/1990, art. 33, caput e § 4º (conta especial; malversação ou desvio apurado pelo Ministério da Saúde); Lei 8.142/1990, art. 4º (fundo, conselho, plano e relatório de gestão como condições do repasse).
- Lei 13.979/2020, art. 4º e seguintes (dispensa, transparência do § 2º, termo de referência simplificado do art. 4º-E, contratos de até seis meses do art. 4º-H); vigência encerrada [A VERIFICAR a data-limite]. MP 1.047/2021, art. 3º (presunções na dispensa, texto conferido). Lei 14.133/2021: art. 23 (estimativa a preços de mercado), art. 72 (instrução da contratação direta), art. 75, VIII e §§ 1º e 6º (texto conferido), art. 156 (sanções).
- Lei 8.429/1992 na redação da Lei 14.230/2021: arts. 10 e 11 (dolo específico), art. 12 (sanções e ressarcimento), art. 23 (prescrição); CPC/2015: arts. 357, 378 a 380, 396 a 404, 465 a 480 (em especial 473, §§ 2º e 3º, 476 e 477); NBC TP 01 e NBC PP 01 (CFC); NBC TA 530 (amostragem, por analogia).

Jurisprudência verificada (consulta de 12/09/2026; identificação completa e links em `references/fundamentacao-legal.md`, seção 2): STJ, REsp 1.901.271, 1.899.407 e 1.899.455 (Tema 1.089: prossegue o ressarcimento quando prescritas as sanções); TRF5, AC 0800323-81.2021.4.05.8205 (ausência de prestação de contas e desvio de finalidade de recursos federais, orientativo); TCU, Súmula 79 (persuasiva).

Protocolo antifabricação: número e data de portaria GM/MS, valor de parcela da LC 173/2020, artigo da LC 141/2012, data-limite da Lei 13.979/2020, acórdão do TCU, Tema ou Súmula fora da lista verificada e URL de portal exigem verificação em fonte oficial (gov.br/saude, portalfns.saude.gov.br, planalto.gov.br, tcu.gov.br, stj.jus.br, stf.jus.br). Fora da lista, citar somente com `[A VERIFICAR]` ao lado e levar o item à seção "Pendências de verificação" do laudo. Tolerância de sobrepreço, janela de fracionamento e prazo de fornecedor novo são premissas declaradas. Citação inventada em laudo sobre verba pública é dano processual e motivo de impugnação.

Pendências de verificação desta versão: portarias GM/MS de repasse covid (números, datas e valores); data-limite de vigência da Lei 13.979/2020 e efeito de decisão do STF sobre ela; Decreto Legislativo 6/2020; Decreto 7.507/2011; Portaria GM/MS 3.992/2017 e Portaria de Consolidação 6/2017; artigos exatos da LC 141/2012 sobre transferência, relatórios e SIOPS; valores e parcelas da LC 173/2020; incisos dos arts. 10 e 11 e §§ do art. 1º da Lei 8.429/1992; acórdãos do TCU sobre contratações covid; Temas do STF sobre imprescritibilidade e retroatividade da Lei 14.230/2021; Súmulas do STJ sobre competência por verba federal; URL do Portal FNS; norma da STN sobre classificação de fontes; conversão da MP 1.047/2021. Lista completa em `references/fundamentacao-legal.md`, seção 9.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | Normas com dispositivo, jurisprudência verificada com links, precedentes a verificar, ônus da prova, prescrição, limites do perito, roteiro de quesitos, pendências | Fase zero (quesitos), etapa 5 e resposta a quesitos |
| `references/roteiro-documental-e-diligencias.md` | Cronologia da fase zero, documentos por parte e por fonte, fontes públicas de conferência, termo de diligência, ofícios, petições de atraso, amostragem, limitação no laudo | Etapas 0 e 1 |
| `references/matriz-de-testes-e-red-flags.md` | Teste por despesa, regras de classificação, red flags, método de fracionamento e sobrepreço, quantificação, redação do achado | Etapas 3 e 4 |
| `assets/template_plano_trabalho.md` | Plano de trabalho com exemplo preenchido | Etapa 0 |
| `assets/template_laudo.md` | Template do laudo e do parecer com exemplo preenchido | Etapa 5 |
| `assets/exemplo_*.json` e `assets/exemplo_*.csv` | Entradas fictícias dos três scripts | Etapas 0, 2 e 3 |

## Extensão e manutenção

1. Novo teste por despesa (por exemplo, sócio servidor ou contrato prorrogado além do permitido): adicionar uma coluna S/N ao CSV, um bloco em `testar_despesa()` de `scripts/matriz_despesas_covid.py` com código, classe e descrição, a entrada em `DESCRICAO_GENERICA` e a linha correspondente em `references/matriz-de-testes-e-red-flags.md`.
2. Novo tipo de fonte (convênio, emenda parlamentar, recurso estadual com regra própria): o CSV de receitas já aceita qualquer código; documentar o objeto permitido em `references/roteiro-documental-e-diligencias.md`, seção 1, e, se houver norma própria, em `references/fundamentacao-legal.md`.
3. Nova tese ou precedente: só entra em `references/fundamentacao-legal.md`, seção 2, após verificação em fonte oficial; até lá fica na seção 3 com `[A VERIFICAR]`.
4. Consulta automática ao Portal FNS ou ao PNCP: implementar como `--online` opcional em script novo, mantendo o caminho padrão por arquivo com fonte e data; a resposta vai para o anexo do laudo.
5. Versionamento SemVer no frontmatter e no `CHANGELOG.md`: novo teste, nova classe ou novo parâmetro é `minor`; mudança nas colunas obrigatórias dos CSV ou nas chaves do JSON de saída, que quebra o encadeamento, é `major`.

Manutenção desta skill: acionar `chelfo-skill-forge`.
