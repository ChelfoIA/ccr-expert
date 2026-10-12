---
name: pericia-irpf-rendimentos-nao-declarados
description: "Analisar em perícia contábil a cobrança de IRPF por rendimentos não declarados (art. 42 da Lei 9.430/1996, DIRF, acréscimo patrimonial). Usar quando: (1) classificar crédito a crédito a natureza e a prova da origem; (2) aplicar as exclusões do § 3º e a conta conjunta do § 6º; (3) separar renda tributável, exclusiva na fonte, isenta e não rendimento; (4) recalcular o imposto em modo anual e mensal e compensar IRRF; (5) apurar multa de ofício e juros Selic e confrontar com o auto ou a CDA; (6) testar a decadência por ano; (7) elaborar laudo, parecer e quesitos. Acionar ao mencionar: omissão de rendimentos, depósitos de origem não comprovada, art. 42, auto de infração de IRPF, DIRF, documentação hábil e idônea, Tema 842, multa de ofício, acréscimo patrimonial a descoberto, a Receita está cobrando renda que não declarei. COMPLEMENTAR a analise-extratos-forense: use aquela para extrair extratos; use ESTA para a prova da origem e o recálculo. NÃO usar para lavagem de dinheiro (pericia-lavagem-dinheiro)."
metadata:
  version: "1.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Perícia contábil em IRPF por rendimentos não declarados

Versão 1.0.0 (12/09/2026).

## Escopo

Perícia contábil em cobrança de imposto de renda da pessoa física por rendimentos não declarados: lançamento de ofício a partir de DIRF, DIMOB ou e-Financeira (rendimento informado por terceiro e ausente da DIRPF), a partir de depósitos bancários de origem não comprovada (Lei 9.430/1996, art. 42; STF, Tema 842) ou de acréscimo patrimonial a descoberto. A skill examina crédito a crédito a documentação apresentada pelo contribuinte, classifica a natureza de cada rendimento, avalia se a prova é hábil e idônea, aplica as exclusões do § 3º, recalcula o imposto devido com a tabela progressiva fornecida por arquivo, compensa o IRRF, apura a diferença, a multa de ofício e os juros Selic, testa a decadência por ano e confronta tudo com o auto de infração ou a CDA. O papel padrão é o de perito do juízo em ação anulatória ou embargos à execução fiscal; a mesma memória serve ao assistente técnico do contribuinte ou da Fazenda, com a variante declarada no cabeçalho.

Fora de escopo: extração e categorização massiva de extratos (`analise-extratos-forense`, etapa anterior quando há volume), tipificação de lavagem de dinheiro (`pericia-lavagem-dinheiro`), atualização de valores apurados até a data-base (`atualizacao-monetaria`), embargos à execução de títulos privados (`pericia-embargos-execucao`) e reforma tributária do consumo (`reforma-tributaria-2026`).

## Princípio reitor

No art. 42 a presunção é legal e o ônus é do contribuinte, crédito a crédito e com documento (STF, Tema 842; STJ, REsp 1.825.390). Por isso o laudo não pode dizer "a maior parte tem origem lícita": tem de dizer, para cada crédito, qual documento prova a origem e qual a natureza tributária dessa origem. Comprovar a origem não encerra a questão, porque o § 2º manda que o valor de origem comprovada e não tributado se submeta à tributação própria da sua natureza: o aluguel que o contribuinte prova ter recebido deixa de ser presunção e passa a ser rendimento tributável no ajuste.

A skill separa, por construção, três perguntas que a Fazenda costuma fundir e o contribuinte costuma confundir: de onde veio o dinheiro; se o que veio é renda; se essa renda já foi tributada. Cada crédito recebe uma resposta para cada pergunta, com o documento que a sustenta, e o resultado sai em dois cenários: base (só prova suficiente afasta a presunção) e ampliado (prova parcial aceita), para que o juízo veja quanto do lançamento depende de cada decisão probatória. Tabela progressiva, limites de dedução e série Selic entram por arquivo com fonte declarada; os scripts abortam sem eles, porque valor de tabela reconstruído de memória é fabricação e anula o laudo.

## Workflow principal

```
1. Autos        -> auto de infração, demonstrativos, PAF, intimação, DIRPF, extratos
                   (references/roteiro-probatorio-e-quesitos.md, seção 1)
2. Planilha     -> transcrever os créditos imputados no formato de assets/exemplo_rendimentos.csv
3. Classificar  -> scripts/classificar_rendimentos.py: natureza, prova, § 3º, § 6º, cenários
                   (references/natureza-dos-rendimentos.md)
4. Recalcular   -> scripts/recalculo_irpf.py: modos anual e mensal, deduções, IRRF, diferença
5. Encargos     -> scripts/encargos_auto_infracao.py: multa, Selic, confronto com o auto
6. Decadência   -> mesmo script, --ciencia e --fato-gerador, por ano (seção 7)
7. Laudo        -> assets/template_laudo.md; quesitos em references/fundamentacao-legal.md
```

Executar as etapas 3, 4 e 5 exclusivamente em Python, encadeando o JSON de cada script na entrada do seguinte. Classificação de quarenta créditos feita à mão perde a conciliação de data e valor que decide a prova, e a soma das classes deixa de fechar com o total imputado.

## 1. Leitura do auto de infração e do processo administrativo

Ler, antes de qualquer cálculo, o auto de infração e o demonstrativo de apuração, e registrar: a base de cada infração (DIRF, depósitos, patrimônio), os anos-calendário, a tabela usada e a parcela a deduzir, as deduções admitidas, o IRRF compensado, o percentual e o fundamento da multa, a data até a qual os juros foram calculados, a data da ciência e a existência de intimação prévia para comprovar a origem dos créditos (art. 42, caput, exige intimação regular; a regularidade da intimação no PAF é o objeto do REsp 1.825.390). Registrar também se o auto aplicou o § 3º (transferências próprias e créditos de pequeno valor) e o § 6º (conta conjunta), porque esses dois itens concentram a maior parte das diferenças apuradas em laudo.

O que o auto afirma sem o extrato ou a DIRF correspondente entra no laudo como "informado pela autoridade fiscal, não localizado nos autos". A regularidade formal do lançamento e a validade da intimação são matéria do juízo; o perito descreve o que consta e o que falta (CPC, art. 473, § 2º).

## 2. Planilha de créditos e classificação crédito a crédito

```bash
python3 scripts/classificar_rendimentos.py --rendimentos assets/exemplo_rendimentos.csv \
  --ano 2023 --saida classificacao.json --md classificacao.md --csv classificacao.csv
```

Transcrever cada crédito imputado em uma linha do CSV (`id;data;valor;conta;historico;origem_alegada;natureza_alegada;documento;doc_data;doc_valor;doc_terceiro_identificado;transferencia_propria`, mais as opcionais `ja_declarado` e `doc_qualificado`). Um crédito com duas naturezas se desdobra em linhas (ids `10a` e `10b`: principal resgatado e rendimento da aplicação). A `natureza_alegada` vem da tabela de vinte e uma naturezas de `references/natureza-dos-rendimentos.md`, que define para cada uma o tratamento tributário (ajuste, exclusivo na fonte, isento, não rendimento, terceiro), o fundamento, a prova exigida e se a natureza exige prova qualificada (data certa, registro público, ITCMD, decisão judicial).

O script avalia a prova por regras declaradas: data do documento a até 10 dias do crédito (`--tolerancia-dias`), valor coincidente com tolerância de 0,5% (`--tolerancia-valor`), contraparte identificada e, quando a natureza exige, prova qualificada. Prova `suficiente` afasta a presunção nos dois cenários; `parcial` só no cenário ampliado; `ausente` nunca. O resultado traz, para cada crédito, natureza, tratamento em cada cenário, nível de prova com os motivos, fundamento e alerta pericial, e os totais por tratamento, natureza, mês e ano. A sanidade exige que a soma das classes seja igual ao total imputado nos dois cenários; o script falha de propósito quando não fecha.

## 3. Prova hábil e idônea: as três perguntas

Para cada crédito o laudo responde, nesta ordem, com o documento que sustenta cada resposta:

| Pergunta | Resposta no JSON | O que decide |
|---|---|---|
| De onde veio? | `prova` e `motivos_prova` | Coincidência de data, valor e contraparte entre o crédito e o documento; prova qualificada quando a natureza exige |
| É renda? | `natureza` e `tratamento_natural` | Mútuo, venda de bem, transferência própria, estorno e restituição não são acréscimo patrimonial (CTN, art. 43); doação, herança e FGTS são isentos |
| Já foi tributada? | `ja_declarado`, `exclusivo_fonte` | Rendimento de fonte identificada ausente da DIRPF vai para o ajuste (§ 2º); rendimento de aplicação já tributado na fonte não volta à base |

Três armadilhas que derrubam a prova do contribuinte: recibo particular de mútuo ou de doação sem data certa (CPC, art. 409) e sem lastro na DIRPF e na capacidade financeira do mutuante ou doador; transferência de conta conjunta ou de cônjuge tratada como conta própria; PIX de terceiro com "declaração" posterior sem contrato nem DIRPF do terceiro. Nos três casos o script classifica a prova como parcial e explica o motivo; o laudo descreve a lacuna sem opinar sobre boa-fé (`references/roteiro-probatorio-e-quesitos.md`, seção 5).

## 4. Exclusões do § 3º e conta conjunta do § 6º

O § 3º do art. 42 manda analisar os créditos individualizadamente e exclui da presunção as transferências entre contas do próprio titular (inciso I) e, para a pessoa física, os créditos de valor individual até R$ 12.000,00 cuja soma no ano-calendário não ultrapasse R$ 80.000,00 (inciso II, redação da Lei 9.481/1997, art. 4º; RIR/2018, art. 913, § 3º). O script aplica o inciso I pela natureza `transferencia_propria` com extrato da conta de origem, e o inciso II por ano e por cenário, sobre os créditos que permaneceram presumidos: se a soma dos pequenos créditos cabe no limite, todos saem; se excede, nenhum sai. Os limites são de lei, não de tabela anual, e podem ser sobrepostos por `--limite-individual` e `--limite-anual` com registro na memória.

Conta conjunta com declarações apresentadas em separado: `--conta-conjunta "CC 0001-1 Banco Alfa=2"` divide o presumido pelo número de titulares (§ 6º), só para os créditos sem origem comprovada. O rendimento de fonte identificada não se divide, porque pertence a quem o auferiu. Crédito que pertence a terceiro, com interposição de pessoa provada (§ 5º), muda de sujeito passivo e não de natureza: o laudo registra o efeito e não extingue o crédito.

## 5. Recálculo do imposto: modo anual e modo mensal

```bash
python3 scripts/recalculo_irpf.py --classificacao classificacao.json \
  --tabela assets/exemplo_tabela_progressiva.csv --ano 2023 \
  --deducoes assets/exemplo_deducoes.json --rendimentos-declarados 54.000,00 \
  --irrf 225,00 --modo ambos --cenario ambos --saida recalculo.json --md recalculo.md
```

A tabela progressiva entra por CSV (`ano;modo;faixa_inicio;faixa_fim;aliquota;deducao;fonte`) e é validada antes do uso: faixas contíguas, alíquotas não decrescentes, parcela a deduzir coerente com a estrutura das faixas e fonte em toda linha. O script aborta se faltar o ano ou o modo, porque não embute valor algum de tabela. As deduções entram por JSON, item a item, cada um com fonte (valor por dependente, limite de instrução e limite do desconto simplificado são do exercício e vêm de gov.br/receitafederal); o script compara deduções legais e desconto simplificado e adota a maior, salvo `--opcao-deducoes`.

Dois modos, apresentados lado a lado porque a escolha é controvérsia jurídica e não contábil:

| Modo | Mecânica | Fundamento |
|---|---|---|
| `anual` | Rendimentos declarados + rendimento de fonte identificada não declarado + presumido, menos deduções, pela tabela anual | Apuração no ajuste anual; fato gerador em 31/12 atribuído à Súmula CARF 38 [A VERIFICAR] |
| `mensal` | Presumido tributado no mês do crédito pela tabela mensal, sem deduções; o restante no ajuste anual | Lei 9.430/1996, art. 42, §§ 1º e 4º |

Imposto suplementar = imposto devido recalculado menos o imposto apurado na DIRPF original (`--imposto-dirpf`, ou recalculado pela mesma tabela sobre os rendimentos declarados) menos o IRRF compensável ainda não compensado (`--irrf`). Sanidade: soma mensal igual à anual em cada parcela da base; imposto por fatias igual ao da fórmula alíquota vezes base menos parcela a deduzir. Com os assets fictícios, o cenário base produz R$ 95.421,00 (anual) e R$ 93.189,50 (mensal); o ampliado, R$ 6.046,00 e R$ 5.664,50. A diferença entre cenários (R$ 89.375,00 no modo anual) é exatamente o custo probatório da doação de R$ 300.000,00 sem ITCMD e do mútuo de R$ 25.000,00 sem data certa.

## 6. Multa de ofício, juros Selic e confronto com o auto

```bash
python3 scripts/encargos_auto_infracao.py --recalculo recalculo.json --cenario base \
  --modo anual --ano 2023 --vencimento 30/04/2024 --data-referencia 12/09/2026 \
  --multa 75 --selic assets/exemplo_selic.csv --lancado assets/exemplo_lancado.json \
  --ciencia 15/03/2026 --pagamento-antecipado S --cenario-mora --saida encargos.json
```

O principal vem do recálculo (ou de `--principal`). A multa de ofício padrão é de 75% (Lei 9.430/1996, art. 44, I); qualquer outro percentual exige `--fundamento` com o dispositivo e o motivo da qualificação, e a redação vigente dos percentuais após a Lei 14.689/2023 fica marcada [A VERIFICAR]. Os juros seguem o art. 61, § 3º: soma simples das taxas Selic mensais do mês seguinte ao vencimento até o mês anterior ao do pagamento, mais 1% no mês do pagamento, sem capitalização; a série entra por CSV (`competencia;taxa_mensal;fonte`, obtida em bcb.gov.br/SGS) e o script lista as competências faltantes e aborta. Juros sobre a multa só com `--juros-sobre-multa`, com a controvérsia marcada [A VERIFICAR].

O confronto com `--lancado` compara principal, multa, juros e total item a item e, quando o auto informa a data dos seus juros, reproduz o cálculo nessa data: a Selic implícita do auto (juros divididos pelo principal) contra a acumulada da série informada. Diferença de centavos é arredondamento; diferença de pontos percentuais é série, marco inicial ou base diversa, e vai para o laudo como "não reproduzível em: ...". `--cenario-mora` acrescenta o cenário informativo de multa de mora (art. 61, caput e §§ 1º e 2º: 0,33% ao dia, limitada a 20%) para a hipótese de pagamento espontâneo ou de afastamento da multa de ofício pelo juízo.

## 7. Decadência por ano

Com `--ciencia` (data da ciência do lançamento) e `--fato-gerador` (ou `--ano`, que assume 31/12), o script calcula os dois termos finais: cinco anos do fato gerador (CTN, art. 150, § 4º) e cinco anos do primeiro dia do exercício seguinte àquele em que o lançamento poderia ter sido efetuado (CTN, art. 173, I), e diz, para cada regra, se a ciência veio dentro ou fora do prazo. A orientação atribuída à Súmula 555/STJ [A VERIFICAR] aplica o art. 173, I, quando não há pagamento antecipado; havendo imposto pago ou retido no ano e ausente dolo, fraude ou simulação, aplica-se o art. 150, § 4º. Sob o § 4º do art. 42 há tese de fato gerador mensal, que antecipa o termo inicial. O perito apresenta as datas por ano e por regra; a regra aplicável é do juízo.

## 8. Laudo, parecer e quesitos

Redigir pelo template `assets/template_laudo.md`. Responder quesitos com remissão ao quadro crédito a crédito e à seção, nunca com número solto. Valores apurados são nominais na data de referência dos juros; atualização posterior fica com `atualizacao-monetaria`. Como assistente técnico, trocar o título por parecer, declarar a parte assistida e manter a mesma memória.

Checklist antes de entregar:

1. Sanidade OK na classificação (soma das classes igual ao total imputado) e no recálculo (mensal igual ao anual; fatias igual à fórmula).
2. Tabela, deduções e Selic com fonte e data de consulta; nenhum valor de tabela digitado de memória.
3. Cada crédito com documento, nível de prova e motivo; nenhum "a maior parte" sem quadro.
4. Modos anual e mensal apresentados; a escolha remetida ao juízo.
5. Confronto item a item com o auto; juros do auto reproduzidos ou marcados "não reproduzível".
6. Decadência por ano e por regra, sem conclusão sobre a regra aplicável.
7. Todo item fora da jurisprudência verificada com [A VERIFICAR] e listado nas pendências.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler o auto de infração, os demonstrativos, a DIRPF e os extratos antes de transcrever o CSV; conferir se o PDF tem camada de texto |
| `bash` | Executar os três scripts em Python 3.11, encadeando o JSON de `classificar_rendimentos.py` em `recalculo_irpf.py` e deste em `encargos_auto_infracao.py` |
| `create_file` | Gravar o CSV dos créditos, a tabela, as deduções, a Selic, as saídas (JSON, CSV, Markdown) e o laudo em `/mnt/user-data/outputs` |
| `web_search` | Conferir, antes de citar, todo item marcado [A VERIFICAR], a tabela do ano, os limites de dedução e a série Selic (gov.br/receitafederal, bcb.gov.br, stj.jus.br, stf.jus.br, planalto.gov.br) |

| Skill | Quando |
|---|---|
| `analise-extratos-forense` | Extrair e categorizar extratos em volume antes de montar o CSV dos créditos |
| `atualizacao-monetaria` | Atualizar o indébito ou a diferença apurada até a data-base, pelo critério que o juízo fixar |
| `pericia-lavagem-dinheiro` | Quando a imputação deixa de ser tributária e passa à tipificação penal da origem |
| `apuracao-haveres` ou `valuation-capital-fechado` | Lucros distribuídos cuja existência contábil precisa ser demonstrada na sociedade |
| `chelfo-docx-brand` | Conversão do laudo ou parecer em `.docx` no padrão institucional, só sob pedido |
| `chelfo-skill-forge` | Manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/classificar_rendimentos.py` | Natureza, prova, § 3º, § 6º, totais por tratamento, mês e ano em dois cenários | `python3 scripts/classificar_rendimentos.py --rendimentos assets/exemplo_rendimentos.csv --ano 2023 --saida classificacao.json` |
| `scripts/recalculo_irpf.py` | Modos anual e mensal, deduções com fonte, T0 e IRRF, imposto suplementar por cenário | `python3 scripts/recalculo_irpf.py --classificacao classificacao.json --tabela assets/exemplo_tabela_progressiva.csv --ano 2023 --deducoes assets/exemplo_deducoes.json --rendimentos-declarados 54.000,00 --irrf 225,00` |
| `scripts/encargos_auto_infracao.py` | Multa de ofício, Selic acumulada, cenário de multa de mora, confronto com o auto, decadência | `python3 scripts/encargos_auto_infracao.py --recalculo recalculo.json --vencimento 30/04/2024 --data-referencia 12/09/2026 --selic assets/exemplo_selic.csv --lancado assets/exemplo_lancado.json` |

Todos usam só a biblioteca padrão, `Decimal` com `ROUND_HALF_UP` e arredondamento apenas na apresentação, aceitam número no padrão brasileiro e técnico, gravam `premissas`, `locale`, `arredondamento` e `memoria` no JSON e saem com `ERRO de validação:` quando falta fonte, tabela, competência da Selic ou dado obrigatório. Nenhum acessa a rede.

## Estrutura do output

Seções obrigatórias do laudo (template completo, com exemplo preenchido, em `assets/template_laudo.md`):

1. Objeto, com a delimitação do que é do juízo.
2. Quesitos, com a seção da resposta.
3. Documentos examinados, inclusive a tabela, as deduções e a série Selic com fonte.
4. Metodologia, com as regras de prova e os parâmetros de cada cenário e modo.
5. Análise: lançamento e intimação; quadro crédito a crédito; quadro por natureza e tratamento; § 3º e § 6º; recálculo anual e mensal; encargos e confronto; decadência.
6. Conclusão por cenário e modo, com limitações declaradas.
7. Resposta aos quesitos do juízo, do contribuinte e da União.
8. Encerramento, anexos (tabelas e memórias dos scripts, consulta às fontes) e pendências de verificação.

Exemplo de quadro por tratamento (dados fictícios dos assets, ano-calendário 2023):

| Tratamento | Cenário base | Cenário ampliado |
|---|---|---|
| Ajuste (já declarado e não declarado) | R$ 19.500,00 | R$ 19.500,00 |
| Exclusivo na fonte | R$ 500,00 | R$ 500,00 |
| Isento | R$ 12.200,00 | R$ 312.200,00 |
| Não rendimento | R$ 69.700,00 | R$ 94.700,00 |
| Terceiro (§ 5º) | R$ 0,00 | R$ 9.000,00 |
| Presumido (art. 42) | R$ 340.000,00 | R$ 15.000,00 |
| Excluído pelo § 3º, II | R$ 15.650,00 | R$ 6.650,00 |
| Total imputado | R$ 457.550,00 | R$ 457.550,00 |

Exemplo de resposta a quesito:

> Quesito 3 da autora: "A documentação apresentada comprova a origem dos créditos e demonstra que não são base para tributação?"
> Resposta: Em parte. Dos 20 créditos imputados (R$ 457.550,00), 13 têm prova suficiente de origem (quadro 5.2): 5 são rendimentos de fonte identificada (R$ 19.500,00), dos quais R$ 15.000,00 de aluguéis e honorários não constaram da DIRPF e são tributáveis no ajuste por força do § 2º do art. 42; 5 não são rendimento (R$ 69.700,00); 2 são isentos (R$ 12.200,00); 1 foi tributado exclusivamente na fonte (R$ 500,00). Quatro créditos sem documento (R$ 15.650,00) saem da presunção pelo § 3º, II. Três créditos (R$ 340.000,00) têm prova parcial: a doação de R$ 300.000,00 (crédito 7) e o mútuo de R$ 25.000,00 (crédito 5) vieram em declarações particulares sem data certa, sem ITCMD e sem a DIRPF da doadora e do mutuante; o depósito em dinheiro de R$ 15.000,00 (crédito 12) não tem documento. No cenário base esses três permanecem presumidos; a suficiência da prova é matéria do juízo (TRF1, AC 0002129-66.2013.4.01.4200).

Exemplo de resposta sobre os encargos:

> Quesito 2 do juízo: "Os valores de multa e juros do auto estão corretos?"
> Resposta: Não são reproduzíveis pela série informada. Sobre o principal recalculado no cenário base e modo anual (R$ 95.421,00), a multa de 75% é de R$ 71.565,75 e os juros até 12/09/2026, pela Selic acumulada de 29,82% (28 meses cheios mais 1% no mês de referência), são de R$ 28.454,54, total de R$ 195.441,29 (Anexo III). O auto lançou R$ 99.949,75 de principal, R$ 74.962,31 de multa e R$ 29.385,23 de juros até 31/08/2026, o que corresponde a uma Selic implícita de 29,40% contra 28,84% acumulados pela série até aquela data. A diferença total na data do auto é de R$ 9.791,12, dos quais R$ 4.528,75 decorrem do principal (não aplicação do § 3º, II, e não compensação do IRRF de R$ 225,00).

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_IRPF_RendimentosNaoDeclarados_vN.md`.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- CTN: art. 43 (fato gerador: aquisição de disponibilidade econômica ou jurídica de renda e proventos); art. 142 (lançamento como atividade vinculada); art. 150, § 4º, e art. 173, I (decadência); art. 161 (juros de mora); art. 174 (prescrição).
- Lei 9.430/1996: art. 42, caput e §§ 1º a 6º (presunção, mês do crédito, tributação da origem comprovada, exclusões, tabela mensal, terceiro, conta conjunta); art. 44, I (multa de ofício de 75%; percentuais qualificados [A VERIFICAR redação vigente após a Lei 14.689/2023]); art. 61, caput e §§ 1º a 3º (multa de mora e juros Selic).
- Lei 9.481/1997, art. 4º (limites do § 3º, II); RIR/2018 (Decreto 9.580/2018), arts. 35 (isentos e não tributáveis) e 913 (depósitos de origem não comprovada).
- Lei 7.713/1988, art. 3º (rendimento bruto e acréscimo patrimonial) e art. 6º (isenções); Lei 9.250/1995, art. 8º (deduções) e arts. 22 e 23 (ganho de capital de pequeno valor e de imóvel único) [A VERIFICAR valores]; Lei 9.249/1995, art. 10 (lucros e dividendos).
- Decreto 70.235/1972 (processo administrativo fiscal: auto de infração e intimação); LC 105/2001, art. 6º (acesso aos dados bancários pela administração tributária).
- CPC/2015: art. 373 (ônus da prova); art. 409 (data do documento particular); arts. 464 a 480 (perícia; art. 473, § 2º, limites do perito). NBC TP 01 e NBC PP 01 (CFC).

Jurisprudência verificada (consulta de 12/09/2026; identificação completa e links em `references/fundamentacao-legal.md`, seção 2): STF, RE 855.649 (Tema 842, constitucionalidade do art. 42); STJ, REsp 1.825.390 (intimação no PAF e presunção legal); TRF1, AC 0049859-48.2012.4.01.9199, AC 0002129-66.2013.4.01.4200, AC 0002616-81.2012.4.01.3000, AC 0006019-32.2006.4.01.3400 e AC 0005332-52.2006.4.01.3304; TRF2, AC 5019756-46.2020.4.02.5001; TRF4, AC 5006335-97.2021.4.04.7102; TRF3, AC 5000076-80.2020.4.03.6122.

Protocolo antifabricação: valor de tabela progressiva, limite de dedução, taxa Selic, limite de isenção de ganho de capital, número de Tema, Súmula ou REsp fora da lista verificada e redação de dispositivo alterado após 2023 exigem verificação em fonte oficial (gov.br/receitafederal, bcb.gov.br/SGS, planalto.gov.br, stj.jus.br, stf.jus.br, carf.economia.gov.br). Fora da lista, citar somente com [A VERIFICAR] ao lado e levar o item à seção "Pendências de verificação" do laudo. Toda afirmação sensível ao tempo leva data de referência. Citação inventada em laudo tributário é dano processual e motivo de impugnação.

Pendências de verificação desta versão: Súmula 555/STJ (decadência); Súmulas CARF 26, 32, 38 e 61 (art. 42); súmula do CARF sobre juros na multa de ofício; STF, ADI 5.422 (pensão alimentícia) e julgamento sobre o art. 6º da LC 105/2001; redação do art. 44 da Lei 9.430/1996 após a Lei 14.689/2023; valores da tabela progressiva e dos limites de dedução de cada ano; limites de isenção de ganho de capital; Lei 8.981/1995, arts. 65 e 68; Lei 8.134/1990, art. 6º; Lei 7.713/1988, art. 12-A; regime dos dividendos a partir de 2026; Lei 9.065/1995, art. 13. Lista completa em `references/fundamentacao-legal.md`, seção 9.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | Normas com dispositivo, texto do art. 42, jurisprudência verificada com links, precedentes a verificar, ônus da prova, decadência e prescrição, limites do perito, roteiro de quesitos, pendências | Etapas 1, 6 e 7; resposta a quesitos |
| `references/natureza-dos-rendimentos.md` | Tabela natureza, tratamento, fundamento, prova exigida e armadilhas; regras de prova do script; desdobramento de créditos; o § 2º na prática | Etapas 2 e 3 |
| `references/roteiro-probatorio-e-quesitos.md` | Documentação hábil e idônea, cruzamentos (DIRPF das partes, DIRF, DIMOB, e-Financeira, ITCMD, registros), roteiro por tipo de lançamento, acréscimo patrimonial a descoberto, quesitos, redação de "prova insuficiente" | Etapas 1, 2 e 7 |
| `assets/template_laudo.md` | Template do laudo e do parecer com exemplo preenchido | Etapa 7 |
| `assets/exemplo_*.csv` e `assets/exemplo_*.json` | Entradas fictícias dos três scripts, com a coluna fonte marcada como exemplo | Etapas 2, 4 e 5 |

## Extensão e manutenção

1. Nova natureza de rendimento: adicionar a entrada em `NATUREZAS` de `scripts/classificar_rendimentos.py` (tratamento, fundamento, prova, qualificada, alerta) e a linha correspondente em `references/natureza-dos-rendimentos.md`; o tratamento precisa ser um dos sete de `TRATAMENTOS`, para que a sanidade continue a fechar.
2. Acréscimo patrimonial a descoberto por fluxo de caixa mensal: novo script `scripts/fluxo_patrimonial.py` que leia origens e aplicações por mês e devolva o excesso por competência no mesmo schema de `presumido_por_mes`, sem alterar o contrato de `recalculo_irpf.py`.
3. Novo ano-calendário: nenhuma alteração de código; acrescentar as linhas do ano em `exemplo_tabela_progressiva.csv` (ou no CSV do caso) e os limites no JSON de deduções, sempre com fonte.
4. Nova tese ou precedente: só entra em `references/fundamentacao-legal.md`, seção 2, após verificação em fonte oficial; até lá fica na seção 3 com [A VERIFICAR].
5. Versionamento SemVer no frontmatter e no `CHANGELOG.md`: nova natureza, parâmetro ou precedente é `minor`; mudança nas chaves do JSON de saída, que quebra o encadeamento, é `major`.

Manutenção desta skill: acionar `chelfo-skill-forge`.
