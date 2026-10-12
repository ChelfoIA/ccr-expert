---
name: pericia-busca-apreensao-veiculo
description: "Analisar em perícia contábil a busca e apreensão de veículo (DL 911/1969) e a revisional conexa (CDC veículo, CCB). Usar quando: (1) reconstruir a evolução da dívida em cenário contratual e revisado; (2) testar abusividade dos juros contra a taxa média do BACEN; (3) aferir capitalização, duodécuplo e periodicidade diária; (4) tratar tarifas, seguros e IOF no financiado; (5) apurar a purga da mora na liminar pela integralidade (Tema 722); (6) descrever notificação e AR para a mora (Tema 1.132); (7) responder se houve encargo abusivo no período de normalidade; (8) apurar excesso pago e elaborar laudo, parecer ou quesitos. Acionar ao mencionar: busca e apreensão, alienação fiduciária, purga da mora, financiamento de veículo, CDC veículo, CCB, taxa média BACEN, juros abusivos, Tema 722, notificação extrajudicial, AR não procurado. COMPLEMENTAR a pericia-bancaria: use ESTA para busca e apreensão e CDC veículo; use aquela para outros produtos. NÃO usar para defender o credor (use assistencia-tecnica-bancaria)."
metadata:
  version: "1.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Perícia contábil em busca e apreensão de veículo

Versão 1.0.0 (12/09/2026).

## Escopo

Perícia contábil em ação de busca e apreensão de veículo com alienação fiduciária (DL 911/1969) e na revisional conexa do contrato de financiamento (CDC veículo ou cédula de crédito bancário): reconstrução da evolução da dívida, confronto dos juros remuneratórios com a taxa média de mercado do BACEN, capitalização, tarifas e seguros embutidos, encargos moratórios, valor exigível para a purga da mora na data da liminar, descrição factual da constituição em mora, saldo devedor revisado, excesso pago e cenários para o juízo. O papel padrão é o de perito do juízo, com laudo imparcial; a mesma memória serve ao assistente técnico do devedor, com a variante de saída (parecer) declarada no cabeçalho.

Fora de escopo: revisão de outros produtos bancários (`pericia-bancaria`), defesa técnica do credor (`assistencia-tecnica-bancaria`), cartão consignado com RMC ou RCC (`pericia-cartao-rmc`), linhas PRONAMPE (`pericia-pronampe`), embargos à execução (`pericia-embargos-execucao`) e atualização dos valores apurados até a data-base (`atualizacao-monetaria`).

## Princípio reitor

Em busca e apreensão, dois números decidem a lide, e a ordem entre eles importa. O primeiro é binário: havia encargo abusivo no período de normalidade? Se o cenário revisado afasta juros, tarifa ou capitalização cobrados antes do inadimplemento, a mora se descaracteriza (REsp 1.061.530) e a ação perde o pressuposto. O segundo é o valor exigível na data da liminar, pela integralidade da dívida, vencidas e vincendas (Tema 722). Laudo que começa pelo valor e só depois toca na mora inverte a lógica do processo e entrega ao juízo um número que pode não ter objeto.

Por isso a skill produz, por construção, dois cenários lado a lado (A, contratual; B, revisado) para cada pergunta, responde primeiro à mora e depois ao valor, e nunca fabrica o dado que sustenta tudo: a taxa média do BACEN entra por parâmetro, com fonte, série e competência declaradas, ou o cenário B não existe. O perito descreve fatos e números; a qualificação jurídica (mora constituída, cláusula nula, pedido procedente) é do juízo, e o laudo diz isso em cada seção, porque exceder esse limite viola o art. 473, § 2º, do CPC e expõe o laudo à impugnação.

## Workflow principal

```
1. Autos         -> ler contrato, planilha do credor, notificação e AR, pagamentos, liminar;
                    transcrever no formato de assets/exemplo_contrato.json
2. Mora          -> descrever envio, endereço e resultado do AR (references/fundamentacao-legal.md, 2.1)
3. Juros         -> scripts/abusividade_juros.py: contratada x média BACEN (references/taxa-media-bacen.md)
4. Capitalização -> mesmo script: duodécuplo, composta, periodicidade diária
5. Tarifas       -> classificar incluída e contestada (references/sistemas-amortizacao.md, 7)
6. Evolução      -> scripts/evolucao_cdc_veiculo.py: cenários A e B (e C), excesso
7. Purga         -> scripts/purga_mora.py: vencidas + encargos + vincendas, A e B
8. Laudo         -> assets/template_laudo.md; atualização: atualizacao-monetaria
```

Executar as etapas 3, 6 e 7 em Python, encadeando o JSON de saída da etapa 6 na entrada da etapa 7. Conta feita à mão em 36 ou 48 parcelas erra centavos que se acumulam e destroem a credibilidade da memória de cálculo.

## 1. Leitura dos autos e extração do contrato

Ler o contrato e a planilha do credor antes de qualquer cálculo e registrar: data da contratação, valor financiado e sua composição (líquido liberado, tarifas, seguros, IOF), taxa mensal e taxa anual informadas, CET, número de parcelas, data da primeira parcela, cláusula de capitalização e de encargos moratórios, pagamentos realizados e data da liminar. Transcrever tudo no formato de `assets/exemplo_contrato.json`, que é a entrada do script de evolução.

Conferir se a planilha da inicial é reproduzível a partir das cláusulas (checklist em `references/sistemas-amortizacao.md`, seção 11). Diferença de centavos é arredondamento; diferença de reais é taxa, principal ou imputação diversa, e vai para o laudo como "não reproduzível em: ...". Isso importa porque o Tema 722 mede a integralidade pelos valores apresentados e comprovados pelo credor na inicial.

## 2. Constituição em mora: descrição factual

Registrar quatro fatos: data do envio da notificação extrajudicial, endereço de destino comparado ao do contrato, resultado do aviso de recebimento (recebido, "não procurado", "mudou-se", outro) e parcela mais antiga em aberto na data do envio. Não concluir sobre a validade da constituição em mora. A tese do Tema 1.132 (REsp 1.951.662 e 1.951.888) dispensa a prova do recebimento quando a notificação foi enviada ao endereço do contrato, e julgados de 2026 (REsp 2.231.840, 2.230.042 e 2.246.676) tratam o AR "não procurado" como suficiente; a aplicação ao caso é do juízo. A exigência de comprovação da mora é atribuída à Súmula 72/STJ [A VERIFICAR].

| Resultado do AR | Registro no laudo |
|---|---|
| Recebido pelo destinatário ou por terceiro | Data da entrega e quem assinou, sem qualificar |
| "Não procurado" | Devolvido sem retirada; endereço idêntico ou diverso do contrato (REsp 2.231.840, 2.230.042 e 2.246.676) |
| "Mudou-se", "desconhecido", "endereço insuficiente" | Transcrever a anotação e confrontar com o endereço do contrato; não concluir |
| Sem AR nos autos | Registrar a ausência como fato; a prova do envio é do credor (CPC, art. 373, I) |

## 3. Juros remuneratórios, taxa média e capitalização

```bash
python3 scripts/abusividade_juros.py --entrada assets/exemplo_abusividade_juros.json --md teste_juros.md
python3 scripts/abusividade_juros.py --taxa-contratada-mensal 2,90 --taxa-contratada-anual 40,92 \
  --taxa-media-mensal 1,60 --fonte "BACEN/SGS, série validada em dd/mm/aaaa" --competencia 03/2024
```

O referencial é a taxa média de mercado da modalidade "aquisição de veículos" (pessoa física ou jurídica, recursos livres, pré-fixada) no mês da contratação, obtida no SGS do BACEN (`references/taxa-media-bacen.md`). O script converte mensal e anual a juros compostos, calcula razão e spread e aplica o limiar informado (`--limiar`, padrão 1,5), gravado na saída como premissa. O REsp 1.061.530 fala em discrepância substancial e não fixa percentual: o laudo declara o limiar como parâmetro usual e remete a qualificação ao juízo. Taxa acima da média sem alcançar o limiar é descrita exatamente assim, com razão e spread, sem o adjetivo "abusiva".

Capitalização: a pactuação expressa é matéria da Súmula 539/STJ. O script testa três sinais: taxa anual informada superior ao duodécuplo da mensal (orientação atribuída à Súmula 541/STJ [A VERIFICAR]); coincidência da anual informada com a composta (1 + m)^12 - 1; e periodicidade diária sem taxa diária informada, tratada como violação do dever de informação e abusiva no REsp 2.238.832. Sem taxa anual no instrumento, o teste do duodécuplo é inaplicável e a pactuação se busca na cláusula.

O script recusa taxa média sem `--fonte` e `--competencia`. A recusa é proteção contra fabricação: taxa média "de memória" invalida o laudo.

## 4. Tarifas, seguros e IOF

Classificar cada item em duas dimensões: incluído no valor financiado (e, portanto, remunerado pela taxa em todas as parcelas) ou pago à vista; contestado ou não. Item contestado e incluído sai do principal do cenário B, o que reduz todas as parcelas e não apenas devolve o nominal (`references/sistemas-amortizacao.md`, seção 7). Item contestado pago à vista não altera a tabela e entra em lista própria para restituição.

Critérios de contestação que o perito registra sem decidir: tarifa de cadastro no início do relacionamento (Tema 618/STJ [A VERIFICAR]); registro de contrato e avaliação do bem condicionados à prova do serviço (Tema 958/STJ [A VERIFICAR]); seguro prestamista válido quando a adesão é facultativa (REsp 2.232.646; venda casada, Tema 972/STJ [A VERIFICAR]). O IOF é tributo e permanece no principal nos dois cenários; `--excluir-iof` existe para cenário alternativo determinado pelo juízo.

## 5. Evolução da dívida em dois cenários

```bash
python3 scripts/evolucao_cdc_veiculo.py --contrato assets/exemplo_contrato.json \
  --taxa-media-mensal 1,60 --fonte-taxa-media "BACEN/SGS, série validada em dd/mm/aaaa" \
  --competencia-taxa-media 03/2024 --data-referencia 10/09/2025 \
  --saida evolucao.json --csv evolucao.csv --md evolucao.md
```

Cenário A reproduz o contrato (Price, taxa e principal contratados). Cenário B adota a taxa média quando a contratada supera o limiar (ou quando `--forcar-taxa-media` reflete decisão já proferida) e retira do principal as tarifas contestadas incluídas no financiado. `--sem-capitalizacao` acrescenta o cenário C, B sem capitalização pelo MEJS, para a hipótese de o juízo afastar a capitalização. Juros de carência pro rata incidem só sobre os dias em que a primeira parcela excede um mês civil da contratação (`--ignorar-carencia` desliga).

Teste de sanidade embutido em cada cenário: soma das amortizações igual ao principal, último saldo zero e soma das parcelas igual a principal mais juros. O script falha de propósito quando um deles não fecha. A saída traz tabela parcela a parcela, comparativo A x B, total pago contra devido em B nas parcelas pagas (excesso nominal) e a posição de vencidas e vincendas na `--data-referencia`.

## 6. Purga da mora na data da liminar

```bash
python3 scripts/purga_mora.py --evolucao evolucao.json --data-liminar 10/09/2025 \
  --juros-mora-am 1,0 --multa 2,0 --saida purga.json --md purga.md
```

Lê o JSON da etapa 5 e calcula, em cada cenário, as parcelas vencidas e não pagas com juros de mora pro rata die e multa (padrão 2%, CDC, art. 52, § 1º), mais as vincendas pelo valor nominal (padrão, como na planilha do credor) ou a valor presente (`--vincendas valor-presente`, saldo da tabela). A integralidade exigida pelo art. 3º, § 2º, do DL 911/1969 e pelo Tema 722 (REsp 1.418.593; AgInt nos EDcl no REsp 2.164.201) inclui as vincendas; o adimplemento substancial não dispensa o pagamento integral (REsp 2.240.342). Purga parcial só entra como cenário informativo.

`--comissao-permanencia` sinaliza a cláusula sem somar o encargo, porque sua cumulação com juros de mora, multa e correção é vedada (orientação atribuída à Súmula 472/STJ [A VERIFICAR]). Antes do valor, o script lê o cenário B e responde se há sinal técnico de encargo abusivo no período de normalidade, com a consequência prevista no REsp 1.061.530, no REsp 2.239.793 e no REsp 2.134.805 (descaracterização da mora, extinção sem mérito, afastamento da multa), remetida ao juízo.

## 7. Laudo, parecer e quesitos

Redigir pelo template `assets/template_laudo.md`. Responder quesitos com remissão à seção e à tabela, nunca com número solto. Valores apurados são nominais nas datas de pagamento ou da liminar; atualização e juros de mora sobre o excesso ficam com `atualizacao-monetaria`, segundo o critério que o juízo fixar. Como assistente técnico do devedor, trocar o título por parecer, declarar a parte assistida e manter a mesma memória.

Checklist antes de entregar:

1. Sanidade OK nos cenários A e B (soma das amortizações igual ao principal; saldo final zero), com a memória em anexo.
2. Taxa média com fonte, série validada, competência e data de consulta; consulta ao SGS anexada.
3. Limiar declarado como premissa; nenhum "abusivo" sem o sinal técnico correspondente.
4. Resposta à mora antes do valor; fatos da notificação sem conclusão jurídica.
5. Purga com vencidas e vincendas nos dois cenários; purga parcial só como cenário informativo.
6. Todo item fora da jurisprudência verificada com `[A VERIFICAR]` e listado nas pendências.
7. Valores nominais, com remissão a `atualizacao-monetaria` para a data-base.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler contrato, planilha do credor, notificação e AR antes de transcrever o JSON; conferir se o PDF tem camada de texto |
| `bash` | Executar os três scripts em Python 3.11; encadear o JSON de `evolucao_cdc_veiculo.py` em `purga_mora.py` |
| `create_file` | Gravar o JSON do contrato, as saídas (JSON, CSV, Markdown) e o laudo em `/mnt/user-data/outputs` |
| `web_search` | Conferir, antes de citar, todo item marcado [A VERIFICAR] e a série do SGS (stj.jus.br, planalto.gov.br, bcb.gov.br) |

| Skill | Quando |
|---|---|
| `atualizacao-monetaria` | Atualizar excesso pago, purga ou saldo até a data-base, com índice e juros fixados pelo juízo |
| `pericia-bancaria` | Produto diverso de CDC veículo ou CCB de veículo (crédito pessoal, consignado, imobiliário) |
| `assistencia-tecnica-bancaria` | Atuação como assistente técnico do credor |
| `analise-extratos-forense` | Pagamentos a comprovar por extrato bancário em vez de carnê |
| `chelfo-docx-brand` | Conversão do laudo ou parecer em `.docx` no padrão institucional, só sob pedido |
| `chelfo-skill-forge` | Manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/abusividade_juros.py` | Conversão de taxas, razão e spread contra a média BACEN, limiar declarado, sinais de capitalização | `python3 scripts/abusividade_juros.py --entrada assets/exemplo_abusividade_juros.json` |
| `scripts/evolucao_cdc_veiculo.py` | Tabela Price nos cenários A e B (e C pelo MEJS), comparativo, excesso, posição na data de referência | `python3 scripts/evolucao_cdc_veiculo.py --contrato assets/exemplo_contrato.json --taxa-media-mensal 1,60 --fonte-taxa-media "..." --competencia-taxa-media 03/2024 --saida evolucao.json` |
| `scripts/purga_mora.py` | Valor para purga (vencidas com encargos mais vincendas) por cenário, sinal sobre a mora, diferença A x B | `python3 scripts/purga_mora.py --evolucao assets/exemplo_evolucao.json --data-liminar 10/09/2025` |

Todos usam só a biblioteca padrão, `Decimal` com `ROUND_HALF_UP` e arredondamento apenas na apresentação, aceitam número no padrão brasileiro e técnico, gravam `premissas`, `locale`, `arredondamento` e `memoria` no JSON e saem com `ERRO de validação:` quando falta fonte, competência ou dado obrigatório. Nenhum acessa a rede.

## Estrutura do output

Seções obrigatórias do laudo (template completo, com exemplo preenchido, em `assets/template_laudo.md`):

1. Objeto, com a delimitação do que é do juízo.
2. Quesitos, com a seção da resposta.
3. Documentos examinados, incluindo a consulta ao SGS anexada.
4. Metodologia, com os parâmetros de cada cenário (taxa, principal, sistema, limiar).
5. Análise: dados do contrato; mora (fatos); juros e taxa média; capitalização; tarifas, seguros e IOF; evolução (quadro resumo); pagamentos e excesso; purga na liminar; encargo no período de normalidade.
6. Conclusão por cenário, com limitações declaradas.
7. Resposta aos quesitos do juízo, do credor e do devedor.
8. Encerramento, anexos (tabelas, memórias, consulta ao SGS, transcrição das cláusulas) e pendências de verificação.

Exemplo de quadro de cenários (dados fictícios dos assets):

| Item | Cenário A | Cenário B |
|---|---|---|
| Taxa mensal | 2,90% | 1,60% (média) |
| Principal | R$ 38.500,00 | R$ 37.750,00 |
| Parcela (36) | R$ 1.737,23 | R$ 1.387,58 |
| Pago em 14 parcelas / devido em B | R$ 24.321,22 | R$ 19.426,19 |
| Vencidas com encargos (3) | R$ 5.414,37 | R$ 4.324,62 |
| Vincendas nominais (19) | R$ 33.007,37 | R$ 26.364,02 |
| Purga em 10/09/2025 | R$ 38.421,74 | R$ 30.688,64 |

Exemplo de resposta a quesito:

> Quesito 2 do juízo: "No período anterior ao inadimplemento foram cobrados encargos que a revisão afasta?"
> Resposta: Sim, no cenário revisado. Nas parcelas 1 a 14, pagas entre 15/04/2024 e 15/05/2025, o contrato aplicou juros de 2,90% a.m., correspondentes a 1,8125 vez a taxa média de 1,60% a.m. divulgada pelo BACEN para a modalidade em 03/2024 (Anexo IV), e financiou tarifas de registro (R$ 350,00) e de avaliação (R$ 400,00) sem prova do serviço nos autos. Recalculadas as mesmas parcelas pela taxa média e sem essas tarifas, o excesso nominal é de R$ 4.895,03 (seção 5.7). A consequência sobre a mora (REsp 1.061.530; REsp 2.239.793) é matéria do juízo.

Exemplo de resposta sobre a notificação:

> Quesito 5 do réu: "A notificação foi enviada ao endereço do contrato e qual o resultado do AR?"
> Resposta: A notificação de 20/07/2025 (fl. 31) foi dirigida ao endereço idêntico ao da cláusula 1 do contrato; o AR retornou com a anotação "não procurado" (fl. 33). Na data do envio, a parcela 15, vencida em 15/06/2025, era a mais antiga em aberto. A suficiência do envio para a constituição em mora é matéria do Tema 1.132 do STJ e cabe ao juízo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_BuscaApreensao_vN.md`.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- DL 911/1969: art. 2º, § 2º (mora e notificação); art. 3º, caput e §§ 1º a 8º, na redação da Lei 10.931/2004 (liminar, consolidação em cinco dias, pagamento da integralidade, resposta em quinze dias, multa de cinquenta por cento na improcedência, autonomia do procedimento). Alterações da Lei 14.711/2023 [A VERIFICAR o alcance antes de citar].
- Lei 10.931/2004, arts. 26 a 28 (cédula de crédito bancário); MP 2.170-36/2001, art. 5º; Lei 4.595/1964, art. 4º, IX.
- CDC: art. 6º, V e VIII; art. 39, I e V; art. 42, parágrafo único; art. 51, IV e § 1º; art. 52, caput e §§ 1º e 2º.
- CC: art. 406 (juros legais; atualização em `atualizacao-monetaria`) e art. 591. CPC/2015: art. 373 (ônus da prova) e arts. 464 a 480 (perícia; art. 473, § 2º, limites do perito).
- NBC TP 01 e NBC PP 01 (CFC): perícia contábil e perito contábil.

Jurisprudência verificada (consulta de 12/09/2026; identificação completa e links em `references/fundamentacao-legal.md`, seção 2): Súmula 539/STJ; REsp 1.418.593 (Tema 722); REsp 1.951.662 e 1.951.888 (Tema 1.132); REsp 1.061.530; REsp 2.239.793; REsp 2.134.805; REsp 2.238.832; REsp 2.240.342; REsp 2.232.646; REsp 2.231.840, 2.230.042 e 2.246.676; AgInt nos EDcl no REsp 2.164.201.

Protocolo antifabricação: número de Tema, Súmula, REsp, código de série do SGS, taxa média, alíquota de IOF e redação de dispositivo alterado após 2004 exigem verificação em fonte oficial (stj.jus.br, stf.jus.br, planalto.gov.br, bcb.gov.br). Fora da lista verificada, citar somente com `[A VERIFICAR]` ao lado e levar o item à seção "Pendências de verificação" do laudo. O limiar de 1,5 vez a média é premissa declarada, não norma. Citação inventada em laudo de busca e apreensão é dano processual e motivo de impugnação.

Pendências de verificação desta versão: Súmulas 72, 297, 380, 472 e 541 do STJ; Súmula 596/STF; Temas 618, 958 e 972 do STJ; EAREsp 676.608; alcance da Lei 14.711/2023 e da Lei 13.043/2014 no DL 911/1969; prazos prescricionais da revisional e da repetição; códigos das séries do SGS; alíquotas do IOF e norma do CET. Lista completa em `references/fundamentacao-legal.md`, seção 9.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | Normas com dispositivo, jurisprudência verificada com links, precedentes a verificar, ônus da prova, prescrição, limites do perito, roteiro de quesitos, pendências | Etapas 2 e 8; resposta a quesitos |
| `references/taxa-media-bacen.md` | O que é a taxa média, modalidade correta, SGS e API, séries a validar, competência, conversão de bases, limiar como premissa, registro no laudo | Etapa 3 |
| `references/sistemas-amortizacao.md` | Price, SAC, MEJS, carência e pro rata, tarifas e IOF no principal, CET, capitalização diária, encargos moratórios, checklist da planilha do credor, exemplo numérico | Etapas 5, 6 e 7 |
| `assets/template_laudo.md` | Template do laudo e do parecer com exemplo preenchido | Etapa 8 |
| `assets/exemplo_*.json` | Entradas fictícias dos três scripts | Etapas 3, 5 e 6 |

## Extensão e manutenção

1. Novo sistema de amortização (SAC, Gauss, juros simples sobre saldo): adicionar uma função `tabela_<nome>()` em `scripts/evolucao_cdc_veiculo.py` que devolva as mesmas chaves das linhas e passe por `sanidade()`; documentar a fórmula em `references/sistemas-amortizacao.md`.
2. Cálculo do CET por taxa interna de retorno: novo script `scripts/cet_contrato.py` que leia o mesmo JSON do contrato, sem alterar o contrato de saída dos scripts atuais.
3. Nova tese ou precedente: só entra em `references/fundamentacao-legal.md`, seção 2, após verificação em fonte oficial; até lá fica na seção 3 com `[A VERIFICAR]`.
4. Consulta automática ao SGS: implementar como `--online` opcional em `abusividade_juros.py`, mantendo o caminho padrão por parâmetro com fonte; a resposta da API vai para o anexo do laudo.
5. Versionamento SemVer no frontmatter e no `CHANGELOG.md`: nova tese ou parâmetro é `minor`; mudança nas chaves do JSON de saída, que quebra o encadeamento, é `major`.

Manutenção desta skill: acionar `chelfo-skill-forge`.
