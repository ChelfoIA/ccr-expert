---
name: pericia-previdenciaria-beneficio-pre-cf88
description: "Calcular e revisar em perícia contábil benefício do RGPS concedido antes da CF/88 (CLPS/84): RMI pelos 36 salários de contribuição e valores-teto, art. 58 do ADCT, readequação aos tetos das EC 20/98 e 41/03 (Tema 1.140/STJ), atrasados, prescrição e sucessão. Usar quando: (1) recalcular a RMI da época com coeficientes ORTN/OTN por arquivo; (2) aferir a limitação ao teto na concessão; (3) aplicar o art. 58 do ADCT; (4) readequar aos tetos das emendas e apurar diferenças; (5) cortar a prescrição e informar a decadência; (6) converter em pensão nos óbitos do autor e da pensionista; (7) gerar parcelas para a atualizacao-monetaria e elaborar laudo e quesitos. Acionar ao mencionar: benefício de 1987, aposentadoria antiga, menor valor-teto, maior valor-teto, 20 salários mínimos, art. 58 do ADCT, Tema 1.140, teto da EC 20, revisão de teto, viúva pensionista, habilitação de herdeiros, contribuiu sobre 20 salários e recebe 4. COMPLEMENTAR a calculo-rmi: use aquela para DIB após 1991; use ESTA para DIB anterior à CF/88."
metadata:
  version: "1.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Perícia previdenciária em benefício concedido antes da CF/88

Versão 1.0.0 (12/09/2026).

## Escopo

Perícia contábil previdenciária em revisão de benefício do RGPS concedido antes da Constituição de 1988, sob a CLPS (Decreto 89.312/1984) e a legislação anterior: reconstrução da renda mensal inicial pelas regras da época (36 salários de contribuição, correção dos 24 anteriores aos 12 últimos, menor e maior valor-teto, fração do excedente, coeficiente), verificação do teto de contribuição de 20 salários mínimos, equivalência em salários mínimos do art. 58 do ADCT (04/1989 a 12/1991), readequação aos tetos das EC 20/1998 e 41/2003 pelo Tema 1.140 do STJ, evolução pelos reajustes oficiais, diferenças mensais, prescrição quinquenal, decadência, óbito do segurado com conversão em pensão por morte, óbito da pensionista, habilitação de dependentes ou sucessores e memória de parcelas para a atualização. O papel padrão é o de perito do juízo na Justiça Federal; a mesma memória serve ao assistente técnico do autor ou do INSS, com a variante declarada no cabeçalho.

Fora de escopo: leitura do CNIS, tempo de contribuição e carência (`pericia-previdenciaria-cnis`); RMI de benefício com DIB posterior a 1991 e regras da EC 103/2019 (`calculo-rmi`); atualização monetária e juros das parcelas (`atualizacao-monetaria`); conta do PASEP (`pericia-pasep`); verbas trabalhistas que alterem salários de contribuição (`pericia-trabalhista`).

## Princípio reitor

Em benefício antigo o erro mais comum é comparar salário de contribuição com benefício como se fossem a mesma base: o segurado contribuiu sobre até 20 salários mínimos, mas a renda saiu de uma média corrigida, limitada por dois tetos (o menor e o maior valor-teto) e multiplicada por um coeficiente, e depois foi corroída por reajustes que não preservaram a equivalência. A perícia separa quatro momentos (RMI na concessão; equivalência do art. 58 do ADCT; readequação aos tetos das emendas; reajustes e diferenças) e só então diz quanto faltou, desde quando e para quem. Cada momento tem o seu script e a sua memória, porque juntar os quatro numa única conta esconde qual deles produziu a diferença e deixa o laudo indefensável na impugnação.

Corolário antifabricação: coeficiente ORTN/OTN, salário mínimo histórico, teto e índice de reajuste entram por arquivo com fonte declarada; os scripts abortam sem eles. Os únicos valores padrão são os tetos do texto das emendas (R$ 1.200,00 e R$ 2.400,00), com ressalva de conferência gravada na saída. Índice de 1987 digitado de memória é fabricação e anula o laudo.

Segundo corolário: o teto é limite externo. Benefício não limitado na concessão não tem o que recompor, e a cadeia de scripts prova isso por construção, com teste de diferença zero, em vez de deixar a conclusão ao gosto do perito.

## Workflow principal

```
1. Autos      -> carta de concessão, memória do INSS, relação de SC, HISCRE/HISCON,
                 certidões de óbito, habilitações (references/regime-clps84-e-tetos.md, seção 10)
2. Tabelas    -> CSVs com fonte: coeficientes ORTN/OTN, salário mínimo, tetos, reajustes,
                 cortes de moeda via padroes_monetarios.py da atualizacao-monetaria (seção 6)
3. RMI        -> scripts/rmi_clps84.py: 36 SC, 24 corrigidos, dois tetos, fração, coeficiente, SM
4. Evolução   -> scripts/readequacao_tetos.py: conversões, reajustes, art. 58, emendas, trava,
                 diferença mensal, indicador de limitação (references/regime-clps84-e-tetos.md)
5. Atrasados  -> scripts/atrasados_prescricao.py: blocos titular e pensão, abono, prescrição,
                 decadência informativa, parcelas.json (references/sucessao-processual-e-prescricao.md)
6. Atualizar  -> skill atualizacao-monetaria, regime fazenda_publica, com parcelas.json
7. Laudo      -> assets/template_laudo.md; quesitos em references/fundamentacao-legal.md, seção 7
```

Executar as etapas 3, 4 e 5 exclusivamente em Python, encadeando o JSON de cada script na entrada do seguinte. Uma evolução de 450 competências com cinco moedas feita à mão perde a conversão num corte e produz erro de três ordens de grandeza sem sinal algum no resultado.

## 1. Os quatro momentos e a leitura dos autos

Ler, antes de qualquer conta, a carta de concessão (ou o processo administrativo) e extrair: espécie e DIB; os 36 salários de contribuição com a moeda de cada competência; os coeficientes de correção aplicados; a média; o menor e o maior valor-teto; a parcela do excedente e a fração; o coeficiente; a RMI. Dos extratos HISCRE/HISCON extrair competência, valor pago, espécie, DIB, DIP e cessação; lacunas anteriores à informatização são declaradas, não inferidas. Das certidões e decisões extrair as datas dos óbitos e quem foi habilitado, por que título.

O que a carta não traz entra no laudo como "não localizado nos autos", com pedido de requisição ao INSS. Documento ilegível (microfilme de 1987) é transcrito no que se lê e marcado no resto. O perito não decide decadência, prescrição, regime da pensão nem validade da habilitação (CPC, art. 473, § 2º): apresenta cenários e datas.

## 2. RMI pelas regras da CLPS/84

```bash
python3 scripts/rmi_clps84.py --salarios assets/exemplo_salarios_1987.csv \
  --coeficientes assets/exemplo_coeficientes_ortn.csv --conversoes assets/exemplo_conversoes.csv \
  --dib 03/1987 --menor-teto 12.000,00 --maior-teto 24.000,00 --fonte-tetos "Portaria MPAS" \
  --coeficiente 95 --fracao-excedente 1/30 --grupos-12 24 --fundamento-fracao "[A VERIFICAR: art. 23 CLPS/84]" \
  --salario-minimo-dib 1.200,00 --fonte-sm "Decreto do SM" --saida rmi_1987.json --md rmi_1987.md
```

Mecânica (atribuída aos arts. 21 e 23 da CLPS/84 [A VERIFICAR dispositivos]): período básico dos 36 últimos salários de contribuição em até 48 meses; correção dos 24 anteriores aos 12 últimos pelos coeficientes da portaria do MPAS vigente no mês da DIB (`competencia;coeficiente;fonte`); média aritmética; limitação ao maior valor-teto; parcela até o menor valor-teto por inteiro; excedente na fração informada pelo perito (`--fracao-excedente 1/30` vezes `--grupos-12 N`, grupos de 12 contribuições acima do menor valor-teto na vida contributiva), com `--fundamento-fracao` obrigatório; coeficiente da espécie sobre a base; RMI e número de salários mínimos pelo salário mínimo da DIB (`--salario-minimo-dib` com `--fonte-sm`).

O script aborta se faltar coeficiente para qualquer competência corrigida, se houver competência igual ou posterior à DIB, se a amplitude exceder 48 meses, se a média exceder o menor valor-teto sem fração fundamentada ou se faltar conversão de moeda entre a competência e a DIB. A saída classifica a limitação na concessão em três estados (maior valor-teto; menor valor-teto com excedente fracionado; não limitado) e grava o bloco `para_readequacao` para o script seguinte. Com os assets fictícios: média Cz$ 27.436,11, RMI Cz$ 20.520,00, 17,1 salários mínimos, limitado ao maior valor-teto. Detalhes em `references/regime-clps84-e-tetos.md`, seções 2 a 4.

## 3. Moedas: do cruzeiro ao real

Um benefício de 1987 atravessa Cr$, Cz$, NCz$, Cr$, CR$ e R$. Cada competência declara a moeda; os cortes entram pelo arquivo `--conversoes` (`competencia;divisor;moeda_nova;fonte`), obtido com `scripts/padroes_monetarios.py` da skill `atualizacao-monetaria`, que documenta o diploma de cada corte (Decreto-Lei 2.284/1986, Lei 7.730/1989, Lei 8.024/1990, Lei 8.697/1993, Lei 8.880/1994). O script 1 converte os salários de contribuição para a moeda da DIB antes de corrigir (ou aceita `--coeficientes-embutem-conversao`, quando a tabela oficial já embute o corte); o script 2 aplica o divisor a todas as rendas e ao teto na competência do corte. Totais são apresentados por moeda e nunca somados entre moedas; a conversão é nominal, com a ressalva da tablita herdada da `atualizacao-monetaria`.

## 4. Art. 58 do ADCT

De 04/1989 (sétimo mês da promulgação, parágrafo único) até a implantação dos planos de custeio e benefícios (12/1991 [A VERIFICAR data]), a renda devida é o número de salários mínimos da concessão vezes o salário mínimo da competência (Súmula 25 da TNU: data da concessão, não o mês da última contribuição). O script 2 aplica a janela com `--art58 --salarios-minimos arquivo.csv` (`competencia;valor;moeda;fonte`, linhas nas alterações, com conferência de moeda) e, por coerência, expressa também a média sem teto e o teto projetado em salários mínimos; a partir de 01/1992 as rendas voltam a evoluir pelos índices. A janela é parametrizável (`--art58-inicio`, `--art58-fim`), e o cenário sem art. 58 obtém-se omitindo a flag e declarando a diferença. Passo a passo em `references/regime-clps84-e-tetos.md`, seção 7.

## 5. Readequação aos tetos das emendas (Tema 1.140)

```bash
python3 scripts/readequacao_tetos.py --rmi rmi_1987.json \
  --reajustes assets/exemplo_reajustes.csv --conversoes assets/exemplo_conversoes.csv \
  --tetos assets/exemplo_tetos.csv --pago assets/exemplo_pagamentos.csv \
  --art58 --salarios-minimos assets/exemplo_salario_minimo.csv --fim 12/2024 \
  --saida readequacao.json --md readequacao.md --csv readequacao.csv
```

A tese do Tema 1.140 do STJ (REsp 1.957.733 e 1.958.465, Primeira Seção, Rel. Min. Gurgel de Faria, j. 14/08/2024) manda aplicar, para a adequação dos benefícios anteriores à CF/88 aos tetos das EC 20/1998 e 41/2003, os limitadores vigentes na época da concessão, usando o teto de cada emenda como maior valor-teto e a metade como menor valor-teto. O script evolui três rendas desde a DIB (média sem teto, renda limitada que o INSS pagou e renda devida) pelos reajustes (`competencia;indice_percentual;fonte`) e, em 12/1998 e 12/2003 (`--emendas`, padrão com os tetos do texto das emendas: EC 20/1998, art. 14, R$ 1.200,00; EC 41/2003, art. 5º, R$ 2.400,00, a conferir), recomputa a renda sobre a média evoluída com os dois limitadores, o mesmo coeficiente e a mesma fração da concessão; a renda devida passa a ser a readequada quando esta supera a que vinha sendo devida, fica travada no teto vigente (informado por arquivo ou projetado pelos índices) e é confrontada com a renda paga (HISCRE; na falta, presume a RMI reajustada e avisa).

Com os assets fictícios: em 12/1998 a média evoluída é R$ 1.147,54 e a renda readequada 95% x (600,00 + 0,8 x 547,54) = R$ 986,13, contra R$ 858,27 devidos antes (acréscimo de R$ 127,86); em 12/2003, R$ 1.599,23 contra R$ 1.550,47 (acréscimo de R$ 48,76) e diferença de R$ 249,80 em relação à renda paga. Exemplo numérico completo em `references/regime-clps84-e-tetos.md`, seção 8.

Teste do benefício não limitado: se a média na concessão não excedeu o menor valor-teto, a renda readequada nunca supera a renda paga, e a diferença é zero em toda a evolução. O script implementa o teste de duas formas (critério de limitação e guarda mecânica) e falha de propósito se a cadeia produzir diferença. Segundo exemplo, obrigatório na validação da skill:

```bash
python3 scripts/readequacao_tetos.py --rmi assets/exemplo_rmi_nao_limitado.json \
  --reajustes assets/exemplo_reajustes.csv --conversoes assets/exemplo_conversoes.csv \
  --tetos assets/exemplo_tetos.csv --art58 --salarios-minimos assets/exemplo_salario_minimo.csv \
  --criterio-limitacao qualquer --fim 12/2010 --saida readequacao_nao_limitado.json
```

O critério de limitação é parâmetro: `maior` (padrão) readequa só o benefício limitado ao maior valor-teto, linha da Corte Especial do TRF1 (AC 1018697-75.2023.4.01.3300); `qualquer` alcança também o limitado pelo menor valor-teto com excedente fracionado. Apresentar o cenário adotado e, se controvertido, o alternativo.

## 6. Diferenças, prescrição e decadência

```bash
python3 scripts/atrasados_prescricao.py --diferencas readequacao.json --ajuizamento 15/03/2008 \
  --obito-segurado 15/06/2010 --coeficiente-pensao 100 \
  --fundamento-pensao "Lei 8.213/1991, art. 75, redação da Lei 9.528/1997 [A VERIFICAR regime vigente no óbito]" \
  --pago-pensao assets/exemplo_pagamentos_pensao.csv --obito-pensionista 20/09/2023 \
  --saida atrasados.json --md atrasados.md --csv atrasados.csv --parcelas parcelas.json
```

Prescrição: cinco anos contados da data em que as parcelas deveriam ter sido pagas (Lei 8.213/1991, art. 103, parágrafo único), marco igual ao ajuizamento menos cinco anos, critério `competencia` (padrão) ou `pagamento` (parcela paga no mês seguinte), `--marco-prescricao` com fundamento para requerimento administrativo e `--sem-prescricao` para menores, incapazes e ausentes. Abono anual (art. 40) por bloco e ano, proporcional aos meses, lançado na competência do último mês do bloco no ano (`--sem-abono` desliga). Decadência: o bloco `decadencia` informa os termos do art. 103, caput (benefício anterior a 1997: termo inicial atribuído a 01/08/1997 e final a 01/08/2007 [A VERIFICAR: STF, Tema 313]) e registra que a readequação de teto não revisa o ato de concessão na linha do TRF1, sem concluir. A saída traz parcelas prescritas e devidas por bloco e moeda, testes de sanidade (bruto igual a prescritas mais devidas; soma de `parcelas.json` igual ao devido) e `parcelas.json` no formato `[{"competencia": "mm/aaaa", "valor": ..., "descricao": "..."}]`, pronto para `atualiza.py --regime fazenda_publica` da `atualizacao-monetaria`. Com os assets: prescritas até 02/2003 (R$ 8.163,76 nominais); devidas R$ 120.599,25 em 269 parcelas.

## 7. Óbito do autor, pensão e óbito da pensionista

O mês do óbito do segurado fica com o titular; a pensão começa no mês seguinte, pelo coeficiente do regime vigente na data do óbito, informado por `--coeficiente-pensao` com `--fundamento-pensao` (CLPS/84, Lei 8.213/1991 na redação original, Lei 9.032/1995 e Lei 9.528/1997, EC 103/2019, art. 23: percentuais [A VERIFICAR] em `references/sucessao-processual-e-prescricao.md`, seção 3). A diferença da pensão é o coeficiente sobre a renda devida revisada menos a pensão paga (`--pago-pensao`) ou, na falta, o coeficiente sobre a renda paga ao titular. O óbito da pensionista encerra a cota no mês do óbito (Decreto 3.048/1999, art. 114, I). O valor não recebido em vida vai aos dependentes habilitados à pensão ou, na falta, aos sucessores civis (Lei 8.213/1991, art. 112), com habilitação nos autos (CPC, arts. 110, 313, I, e 687 a 692); o alcance do art. 112 ao que a pensionista não recebeu fica marcado [A VERIFICAR]. O bloco `habilitacao` da saída descreve período, destinatário e fundamento de cada bloco, e o laudo registra quem está habilitado e por que título.

## 8. Laudo, parecer e quesitos

Redigir pelo template `assets/template_laudo.md`. Responder quesitos com remissão ao quadro e ao anexo, nunca com número solto. Valores nominais na moeda de cada competência; atualização e juros ficam com a `atualizacao-monetaria`. Como assistente técnico, trocar o título por parecer, declarar a parte assistida e manter a mesma memória.

Checklist antes de entregar:

1. Sanidade OK nos três scripts (soma do quadro de SC; renda devida nunca inferior à limitada e nunca acima do teto; bruto igual a prescritas mais devidas; `parcelas.json` fechando com o devido).
2. Coeficientes, salário mínimo, tetos, reajustes e conversões com fonte e data de consulta; nenhum valor digitado de memória; tetos das emendas conferidos.
3. Indicador de limitação na concessão declarado; se não limitado, diferença zero demonstrada.
4. Moeda de cada competência declarada; nenhum total somando moedas distintas.
5. Blocos do titular e da pensão com datas dos óbitos, coeficiente e fundamento; destinatário de cada bloco.
6. Prescrição e decadência apresentadas por datas e cenários, sem conclusão sobre a incidência.
7. Todo item fora da jurisprudência verificada com [A VERIFICAR] e listado nas pendências do laudo.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler a carta de concessão, a memória do INSS, os extratos HISCRE/HISCON, as certidões e as decisões de habilitação antes de montar os CSVs; conferir se o PDF tem camada de texto |
| `bash` | Executar os três scripts em Python 3.11, encadeando o JSON de `rmi_clps84.py` em `readequacao_tetos.py` e deste em `atrasados_prescricao.py`; rodar o segundo exemplo (não limitado) como prova do teste |
| `create_file` | Gravar os CSVs de tabelas com fonte, as saídas (JSON, CSV, Markdown), `parcelas.json` e o laudo em `/mnt/user-data/outputs` |
| `web_search` | Conferir, antes de citar, todo item marcado [A VERIFICAR], as portarias de coeficientes e reajustes, o salário mínimo histórico e o status dos Temas (planalto.gov.br, gov.br/inss, stj.jus.br, stf.jus.br, cjf.jus.br) |

| Skill | Quando |
|---|---|
| `atualizacao-monetaria` | Atualizar e aplicar juros às parcelas de `parcelas.json` no regime da Fazenda Pública; obter os cortes de padrão monetário com `padroes_monetarios.py` |
| `calculo-rmi` | Benefício com DIB posterior a 1991 ou cálculo de pensão sob a EC 103/2019; comparação de regimes |
| `pericia-previdenciaria-cnis` | Quando a relação de salários de contribuição precisa ser reconstruída a partir do CNIS ou de vínculos controvertidos |
| `pericia-trabalhista` | Verbas reconhecidas em juízo que alterem os salários de contribuição do período básico |
| `chelfo-docx-brand` | Conversão do laudo ou parecer em `.docx` no padrão institucional, só sob pedido |
| `chelfo-skill-forge` | Manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/rmi_clps84.py` | RMI pela CLPS/84: 36 SC com moeda, conversões, 24 corrigidos, média, dois tetos, fração fundamentada, coeficiente, salários mínimos, indicador de limitação | `python3 scripts/rmi_clps84.py --salarios sc.csv --coeficientes coef.csv --conversoes conv.csv --dib 03/1987 --menor-teto 12.000,00 --maior-teto 24.000,00 --fonte-tetos "..." --coeficiente 95 --fracao-excedente 1/30 --grupos-12 24 --fundamento-fracao "..." --salario-minimo-dib 1.200,00 --fonte-sm "..." --saida rmi.json` |
| `scripts/readequacao_tetos.py` | Evolução mês a mês com conversões, reajustes, art. 58, readequação pelas emendas (Tema 1.140), trava no teto, renda paga, diferença mensal e teste do não limitado | `python3 scripts/readequacao_tetos.py --rmi rmi.json --reajustes reaj.csv --conversoes conv.csv --tetos tetos.csv --pago hiscre.csv --art58 --salarios-minimos sm.csv --fim 12/2024 --saida readequacao.json` |
| `scripts/atrasados_prescricao.py` | Blocos do titular e da pensão, abono anual, prescrição quinquenal, decadência informativa, habilitação, `parcelas.json` | `python3 scripts/atrasados_prescricao.py --diferencas readequacao.json --ajuizamento 15/03/2008 --obito-segurado 15/06/2010 --coeficiente-pensao 100 --fundamento-pensao "..." --obito-pensionista 20/09/2023 --parcelas parcelas.json` |

Todos usam só a biblioteca padrão, `Decimal` com `ROUND_HALF_UP` e arredondamento apenas na apresentação, aceitam número no padrão brasileiro e técnico, gravam `premissas`, `locale`, `arredondamento`, `testes_sanidade` e `memoria` no JSON e saem com `ERRO de validação:` quando falta fonte, coeficiente, conversão, fundamento ou dado obrigatório. Nenhum acessa a rede.

## Estrutura do output

Seções obrigatórias do laudo (template completo, com exemplo preenchido, em `assets/template_laudo.md`):

1. Objeto, com a delimitação do que é do juízo.
2. Quesitos, com a seção da resposta.
3. Documentos examinados, inclusive as tabelas com fonte e data de consulta.
4. Metodologia, com os quatro momentos, os parâmetros e as presunções declaradas.
5. Análise: concessão e RMI; moedas; art. 58; readequação; diferenças e prescrição; óbito, pensão e habilitação; decadência.
6. Conclusão por cenário, com limitações declaradas.
7. Resposta aos quesitos do juízo, do autor ou sucessores e do INSS.
8. Encerramento, anexos (memórias dos scripts, `parcelas.json`, tabelas) e pendências de verificação.

Exemplo de quadro da readequação (dados fictícios dos assets):

| Emenda | Média evoluída | Maior valor-teto | Menor valor-teto | Renda readequada | Renda devida antes | Acréscimo |
|---|---|---|---|---|---|---|
| 12/1998 (EC 20) | R$ 1.147,54 | R$ 1.200,00 | R$ 600,00 | R$ 986,13 | R$ 858,27 | R$ 127,86 |
| 12/2003 (EC 41) | R$ 1.804,25 | R$ 2.400,00 | R$ 1.200,00 | R$ 1.599,23 | R$ 1.550,47 | R$ 48,76 |

Exemplo de resposta a quesito:

> Quesito 2 do INSS: "O benefício foi limitado ao teto na concessão? Em caso negativo, há diferença a apurar?"
> Resposta: Sim, foi limitado ao maior valor-teto. A média dos 36 salários de contribuição corrigidos, de Cz$ 27.436,11 (Anexo I), superou o maior valor-teto de Cz$ 24.000,00 vigente em 03/1987; a renda foi calculada sobre Cz$ 12.000,00 até o menor valor-teto mais 0,8 do excedente de Cz$ 12.000,00, com coeficiente de 95%, resultando em Cz$ 20.520,00. Por isso a readequação dos limitadores aos tetos das EC 20/1998 e 41/2003 produz acréscimos de R$ 127,86 em 12/1998 e de R$ 48,76 em 12/2003 (Anexo III). Registra-se que, se a média não tivesse excedido o menor valor-teto, a mesma rotina produziria diferença zero em toda a evolução, como demonstrado no cenário de controle do Anexo II.

Exemplo de resposta sobre sucessão:

> Quesito 7 do juízo: "Havendo óbito da pensionista, até que competência há parcelas e a quem se destinam?"
> Resposta: Até 09/2023, mês do óbito de Maria da Silva em 20/09/2023, quando cessa a cota (Decreto 3.048/1999, art. 114, I). As parcelas do titular (03/2003 a 06/2010, R$ 27.488,97 nominais) e as da pensão (07/2010 a 09/2023, R$ 93.110,28 nominais), abono anual incluído, destinam-se, na forma do art. 112 da Lei 8.213/1991, à pensionista habilitada e, por seu falecimento, aos sucessores dela, cuja habilitação (CPC, arts. 687 a 692) ainda não consta dos autos. O alcance do art. 112 à pensionista falecida fica como pendência de verificação; o cabimento da habilitação é matéria do juízo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_BeneficioPreCF88_vN.md`.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- CF/88, art. 201, § 4º (preservação do valor real); ADCT, art. 58, caput e parágrafo único (equivalência em salários mínimos da concessão, de 04/1989 até a implantação dos planos).
- Lei 8.213/1991: art. 40 (abono anual); art. 74 e art. 77 (início e cotas da pensão); art. 75 (pensão em percentual da aposentadoria devida na data do óbito); art. 103, caput (decadência decenal) e parágrafo único (prescrição quinquenal, ressalvados menores, incapazes e ausentes); art. 103-A; art. 112 (valor não recebido em vida); art. 144 (buraco negro, que não alcança benefício anterior à CF/88).
- EC 20/1998, art. 14 (teto de R$ 1.200,00); EC 41/2003, art. 5º (teto de R$ 2.400,00). Decreto 3.048/1999, art. 114, I (cessação da cota pela morte do pensionista).
- CPC/2015: art. 110 (sucessão), art. 313, I (suspensão), arts. 687 a 692 (habilitação), art. 373 (ônus da prova), arts. 464 a 480 e art. 473, § 2º (perícia e limites do perito). NBC TP 01 e NBC PP 01 (CFC).
- Regime da época, a conferir: CLPS, Decreto 89.312/1984, arts. 21 e 23 e §§ [A VERIFICAR]; Lei 6.950/1981, art. 4º [A VERIFICAR]; Lei 6.423/1977 [A VERIFICAR].

Jurisprudência verificada (consulta de 12/09/2026; identificação completa, teses e links em `references/fundamentacao-legal.md`, seção 3): STJ, Tema 1.140 (REsp 1.957.733 e 1.958.465, Primeira Seção, Rel. Min. Gurgel de Faria, j. 14/08/2024); STF, Tema 930 (RE 937.595, Pleno, Rel. Min. Luís Roberto Barroso, j. 02/02/2017) e Tema 76 (RE 564.354, Pleno, Rel. Min. Cármen Lúcia, j. 08/09/2010, texto da tese [A VERIFICAR]); TNU, Súmula 25; TRF1, Corte Especial, AC 1018697-75.2023.4.01.3300 (j. 02/12/2024) e Primeira Turma, AC 1004529-73.2020.4.01.3300, AC 1004501-08.2020.4.01.3300, AC 1011367-32.2020.4.01.3300, AC 1007763-79.2019.4.01.3500, AC 1003689-85.2019.4.01.3304 e AC 1021631-40.2022.4.01.3300; TRF4, AC 5045877-11.2019.4.04.7000, AC 5005822-13.2022.4.04.7000, AC 5000027-13.2020.4.04.7027, AC 5002912-94.2019.4.04.7104 e AC 5006913-16.2019.4.04.7107.

Protocolo antifabricação: coeficiente ORTN/OTN, salário mínimo histórico, teto, índice de reajuste, percentual da pensão por regime, número de Tema, Súmula ou REsp fora da lista verificada e redação de dispositivo da CLPS/84 exigem verificação em fonte oficial (planalto.gov.br, gov.br/inss, stj.jus.br, stf.jus.br, cjf.jus.br, trf1.jus.br, trf4.jus.br) na data do laudo. Fora da lista, citar somente com [A VERIFICAR] ao lado e levar o item à seção "Pendências de verificação" do laudo. Toda afirmação sensível ao tempo leva data de referência. Citação inventada em laudo previdenciário é dano processual.

Pendências de verificação desta versão: texto da tese do Tema 76/STF; Súmula 260/TFR; Súmula 85/STJ; STF, Tema 313 (RE 626.489); Lei 6.950/1981, art. 4º; Decreto 89.312/1984, arts. 21 e 23 (fórmula do excedente e fração de 1/30); Lei 6.423/1977; percentuais da pensão por data do óbito (CLPS/84, Lei 8.213/1991 original, Lei 9.032/1995, Lei 9.528/1997, EC 103/2019, art. 23); MP 1.523-9/1997 (introdução da decadência); Decreto 20.910/1932; data de implantação dos planos (12/1991); alcance do art. 112 à pensionista; critério da data de pagamento para a prescrição; tabelas históricas. Lista completa em `references/fundamentacao-legal.md`, seção 9.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | Normas com dispositivo, dispositivos centrais, jurisprudência verificada com links, precedentes a verificar, ônus da prova, prescrição e decadência, quesitos, protocolo antifabricação, pendências | Etapas 1, 6 e 7; resposta a quesitos |
| `references/regime-clps84-e-tetos.md` | Os quatro momentos, mecânica da CLPS/84, dois tetos e fração, moedas, tabelas e onde obtê-las, art. 58 passo a passo, readequação com exemplo numérico, teste do não limitado, leitura da carta, erros recorrentes | Etapas 2 a 4 |
| `references/sucessao-processual-e-prescricao.md` | Óbito do autor, art. 112, coeficientes da pensão por regime, óbito da pensionista, prescrição, decadência, abono, quesitos | Etapa 5 |
| `assets/template_laudo.md` | Template do laudo e do parecer com exemplo preenchido | Etapa 7 |
| `assets/exemplo_*.csv` e `assets/exemplo_*.json` | Entradas fictícias dos três scripts (coluna fonte marcada como exemplo), inclusive o benefício não limitado | Etapas 2 a 5 |

## Extensão e manutenção

1. Nova regra de limitação (por exemplo, fórmula do excedente diversa após conferência do art. 23 da CLPS/84): alterar apenas `readequar()` em `scripts/readequacao_tetos.py` e o bloco da fração em `scripts/rmi_clps84.py`, mantendo as chaves de `para_readequacao` e `para_atrasados`, para que o encadeamento não quebre.
2. Nova emenda ou novo teto constitucional: nenhuma alteração de código; passar `--emendas "mm/aaaa:valor:fonte;..."` e adicionar a linha em `references/fundamentacao-legal.md`, seção 1.
3. Pensão com vários dependentes e cotas reversíveis: adicionar em `atrasados_prescricao.py` um bloco por beneficiário com data de início e fim, sem alterar o formato de `parcelas.json`.
4. Benefício do buraco negro (DIB entre 05/10/1988 e 05/04/1991): o script 2 serve com `--sem-emendas` desligado e sem `--art58`; a RMI vem de `calculo-rmi` (regime da Lei 8.213/1991) e o Tema 930 entra na fundamentação.
5. Versionamento SemVer no frontmatter e no `CHANGELOG.md`: novo parâmetro, precedente verificado ou critério é `minor`; mudança nas chaves do JSON de saída, que quebra o encadeamento, é `major`.

Manutenção desta skill: acionar `chelfo-skill-forge`.
