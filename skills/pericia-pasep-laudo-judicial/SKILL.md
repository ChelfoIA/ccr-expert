---
name: pericia-pasep-laudo-judicial
description: "Elaborar o laudo e conduzir, como perito do juízo, a perícia contábil do PASEP contra o Banco do Brasil e a União (CPC arts. 464 a 480), também em lote. Usar quando: (1) registrar o lote com painel de prazos e status; (2) triar os autos e o objeto do saneamento; (3) montar checklist, termo de diligência e ofício ao BB por extrato e microfilmagem; (4) encadear o cálculo no motor da pericia-pasep, uma premissa por processo; (5) apresentar cenários por tese (polo, prescrição, modalidade) sem decidir; (6) montar a matriz de quesitos e devolver questão de direito ao juízo; (7) redigir laudo, esclarecimentos (CPC art. 477) e pós-laudo. Acionar ao mencionar: fui nomeada perita, perito do juízo, laudo PASEP, lote de processos, prazo do laudo, termo de diligência, ofício ao Banco do Brasil, extrato analítico, microfilmagem, quesitos do juízo, esclarecimentos. COMPLEMENTAR a pericia-pasep: use ESTA para laudo, lote e condução do procedimento; use aquela para parecer de assistente técnico, MIPD e cálculo."
metadata:
  version: "1.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Perícia judicial do PASEP: laudo do perito do juízo e condução do lote

Versão 1.0.0 (12/09/2026).

## Escopo

Condução da perícia contábil judicial, pelo perito nomeado pelo juízo, em ações sobre conta individual do PASEP contra o Banco do Brasil e/ou a União: do recebimento da nomeação à entrega do laudo e dos esclarecimentos, inclusive quando a perita acumula vários processos ao mesmo tempo. Cobre a triagem dos autos e do objeto fixado no saneamento, a proposta de honorários, o termo de diligência e os ofícios para obter o extrato analítico completo, a classificação das saídas por modalidade, o encadeamento do cálculo pelo motor da `pericia-pasep`, os cenários por tese jurídica, a redação do laudo em linguagem neutra, a resposta aos quesitos das três origens (juízo, autor, BB e União), os esclarecimentos do art. 477 do CPC e o controle de prazos e status por processo.

Fora de escopo: parecer de assistente técnico, MIPD, impugnação de laudo e o próprio motor de cálculo (`pericia-pasep`); PIS da Caixa e FGTS (`quitacao-fgts-tema-1176`); resumo e mapa dos autos (`resumo-autos`, `mapa-processo`); precificação da proposta de honorários (`proposta-pericial-judicial`); gestão geral da carteira do escritório (`gestao-pericial-peritos`); atualização de valores fora dos cenários do motor (`atualizacao-monetaria`).

## Princípio reitor

O perito do juízo não escolhe tese. Ele apura fatos (saldo reconstruído, saídas e sua modalidade, índices creditados, datas) e entrega cenários rotulados pela tese que cada um pressupõe: polo passivo BB ou União, termo inicial da prescrição, ônus de prova por modalidade do Tema 1.300/STJ. Dizer que a pretensão está prescrita, que o BB é parte ilegítima ou que o autor não se desincumbiu do ônus é decidir a causa, e isso o art. 473, § 2º, do CPC veda ao perito. O laudo que escolhe tese é impugnado pelas duas partes e devolvido pelo juízo; o laudo que apresenta o fato e o valor de cada hipótese é o que a sentença usa.

Em lote, o risco muda de natureza: deixa de ser o erro de cálculo e passa a ser a contaminação, a premissa de um processo que vaza para outro (data de citação, modalidade de saque, extrato, quadro de cenários). A skill elimina isso por construção: cada processo tem registro próprio no lote, pasta própria, `caso.json` próprio e quadro de cenários próprio, gerados pelo mesmo motor com parâmetros próprios, e o painel mostra prazo, documentos pendentes e próxima ação de cada um separadamente.

## Workflow principal

```
1. Lote        -> scripts/lote_pasep.py criar e adicionar: um registro por processo (references/conducao-do-lote.md)
2. Triagem     -> ler inicial, contestação, réplica, saneamento (objeto, ônus, quesitos) e documentos (seção 2)
3. Honorários  -> proposta em 5 dias (CPC art. 465, § 2º) pela skill proposta-pericial-judicial (seção 3)
4. Diligências -> scripts/checklist_documental_pasep.py: faltantes, termo de diligência, ofício ao BB (seção 4)
5. Cálculo     -> motor da pericia-pasep: selftest, bcb_loader, conciliacao_pasep, cenarios_atualizacao (seção 5)
6. Cenários    -> quadro A a D rotulado por tese, sem escolher (seção 6; references/laudo-e-quesitos.md)
7. Quesitos    -> scripts/matriz_quesitos.py: tema, tipo, seção, evidência, cenário, cobertura (seção 7)
8. Laudo       -> assets/template_laudo_pasep.md; lote_pasep.py atualizar --status laudo_entregue
9. Pós-laudo   -> esclarecimentos em 15 dias (CPC art. 477, § 2º), audiência, honorários finais (seção 8)
```

Executar as etapas 1, 4 e 7 em Python e a etapa 5 pelos scripts da `pericia-pasep`, porque um lote de três processos com trinta quesitos e quatro cenários cada um não se controla de cabeça: quesito sem resposta anula o laudo (CPC art. 473, IV) e prazo perdido sem motivo autoriza a substituição do perito (CPC art. 468, II).

## 1. Registro do lote e painel de prazos

```bash
python3 scripts/lote_pasep.py criar --registro lote.json --perito "Nome, CRC UF 000000"
python3 scripts/lote_pasep.py adicionar --registro lote.json --processo assets/exemplo_processos_lote.json
python3 scripts/lote_pasep.py atualizar --registro lote.json --id P-002 --status diligencia \
  --documento extrato_analitico=parcial --quesitos reu=6 --proxima-acao "Expedir ofício ao BB"
python3 scripts/lote_pasep.py painel --registro lote.json --hoje 12/09/2026 --md painel.md
```

Cada processo entra com número, juízo, partes, polo demandado (`BB`, `UNIAO` ou `LITISCONSORCIO`), data da nomeação, prazo do laudo, modalidades alegadas, quesitos por proponente, estado de cada documento (`recebido`, `pendente`, `parcial`, `nao_aplicavel`), status, próxima ação e histórico datado de alterações. O painel ordena pelo prazo vigente (laudo ou esclarecimentos), mostra dias corridos e dias úteis aproximados e marca alerta abaixo de 15 dias corridos e prazo vencido quando a data passou. A contagem oficial em dias úteis segue o calendário do tribunal (CPC art. 219); o painel avisa, não decide.

Status admitidos, na ordem natural do procedimento: `nomeado`, `proposta_entregue`, `diligencia`, `calculo`, `laudo_entregue`, `esclarecimentos`, `encerrado`. Atualizar o registro no dia do evento, nunca em bloco no fim da semana, porque o histórico datado é o que prova a diligência do perito se o prazo for questionado (CPC arts. 157 e 468). O subcomando `atualizar` grava só alterações efetivas: repetir um valor já registrado aparece como "sem efeito" e não polui o histórico.

## 2. Triagem dos autos e do objeto fixado no saneamento

Ler, nesta ordem, a inicial (causa de pedir: saques não reconhecidos, má gestão, índices ou expurgos), a contestação de cada réu (prescrição alegada, modalidade atribuída a cada saída, documentos juntados), a réplica e a decisão de saneamento. Do saneamento extrair três coisas e transcrevê-las no registro do lote (`--campo objeto_saneamento=...`): o objeto da perícia, a distribuição do ônus da prova que o juízo tenha fixado (CPC art. 357, III) e os quesitos deferidos ou indeferidos (CPC art. 470).

Identificar na triagem: (a) a modalidade alegada de cada saída impugnada, porque ela define o documento a pedir e a quem (seção 4); (b) a tese de cada parte, porque ela define os cenários (seção 6); (c) se existe laudo ou parecer anterior nos autos, porque o laudo novo precisa dialogar com ele sem o adotar; (d) a data de abertura da conta e o período do extrato já juntado, porque a lacuna entre os dois é a primeira diligência. Verificar impedimento e suspeição (CPC art. 148, II) antes de qualquer ato: contato anterior com o autor ou trabalho para o BB em outro processo é motivo de escusa (CPC art. 467).

## 3. Honorários, encargo e comunicação nos autos

Apresentar em cinco dias a proposta de honorários, o currículo e os contatos (CPC art. 465, § 2º) pela skill `proposta-pericial-judicial`; esta skill só registra o status (`proposta_entregue`) e a condição do pagamento (`--campo honorarios=...`). Com a proposta arbitrada, requerer o levantamento de até metade (CPC art. 465, § 4º) e registrar o restante como condicionado à entrega do laudo e dos esclarecimentos. Perícia inconclusiva ou deficiente autoriza a redução dos honorários (CPC art. 465, § 5º): mais um motivo para o laudo trazer cenários completos em vez de "depende da tese".

O perito cumpre o encargo independentemente de termo de compromisso (CPC art. 466) e comunica-se com as partes somente nos autos: os assistentes técnicos têm direito de acompanhar as diligências, com aviso prévio de cinco dias comprovado nos autos (CPC art. 466, § 2º, e art. 474). Reunião, mensagem ou documento recebido fora dos autos vira petição de juntada no mesmo dia, para que a outra parte tenha ciência.

## 4. Diligências: checklist documental, termo e ofício

```bash
python3 scripts/checklist_documental_pasep.py --documentos assets/exemplo_documentos.json --hoje 12/09/2026 --md termo_P-002.md
python3 scripts/checklist_documental_pasep.py --registro lote.json --processo P-002 --prazo-dias 15 --saida checklist_P-002.json
```

O script cruza o estado de cada documento com o que a perícia exige e devolve a lista de faltantes, quem deve fornecê-los, o fundamento do ônus e a consequência da falta, além dos textos prontos do termo de diligência, do ofício ao Banco do Brasil e da solicitação à parte autora, com prazo sugerido em dias úteis. A exigência muda com a modalidade alegada, e esse é o ponto que mais derruba laudo de PASEP:

| Modalidade da saída | Documento exigido | Quem fornece | Ônus (CPC art. 373; Tema 1.300/STJ) |
|---|---|---|---|
| Qualquer | Extrato analítico completo desde a abertura; RAIS ou ficha financeira | BB; autor ou órgão empregador | Base da reconstrução; exibição pelos arts. 396 a 400 |
| CAIXA-BB | Microfilmagem ou recibo assinado, identificação do recebedor, registro biométrico | BB | Réu, fato extintivo (art. 373, II; CC art. 320) |
| CREDITO-CC | Extrato da conta-corrente de destino no mês da saída e no seguinte | Autor | Participante, fato constitutivo (art. 373, I), sem inversão |
| FOPAG | Contracheques ou fichas financeiras do mês da saída e do seguinte | Autor ou órgão empregador | Participante, fato constitutivo (art. 373, I), sem inversão |
| Não identificada | Legenda dos códigos de histórico e identificação da modalidade | BB | Pressuposto do Tema 1.300; sem ela, a saída entra como OUTROS com ressalva |

Extrato parcial gera aviso com o período coberto e o não coberto; o laudo reconstrói só o período coberto e ressalva o resto, nunca preenche com zero. Documento não entregue no prazo vira requerimento ao juízo para determinar a exibição (CPC arts. 396 a 400) e, persistindo a falta, o laudo sai com a lacuna declarada e a saída registrada como "sem comprovação apresentada por" quem devia apresentá-la, sem valorar o ônus: a valoração é do juízo (CPC art. 479).

## 5. Cálculo pelo motor da pericia-pasep

Esta skill não calcula. O cálculo corre nos scripts da `pericia-pasep`, com um `caso.json` por processo no schema de `pericia-pasep/assets/schema_caso.json`, gravado na pasta do processo:

```bash
python3 <pericia-pasep>/scripts/selftest.py                                      # antes de qualquer entrega
python3 <pericia-pasep>/scripts/bcb_loader.py --serie ipca_e --inicio 01/06/2020 --fim 31/08/2026
python3 <pericia-pasep>/scripts/conciliacao_pasep.py --arquivo P-002/caso.json
python3 <pericia-pasep>/scripts/cenarios_atualizacao.py --arquivo P-002/diferencas.json
```

Encadeamento: `conciliacao_pasep.py` reconstrói o saldo mês a mês na ordem oficial de valorização, confronta com o extrato e classifica cada saída por modalidade e polo; o quadro de diferenças alimenta `cenarios_atualizacao.py`, que gera os cenários A a D com os fatores obtidos por `bcb_loader.py` e `fator_correcao.py`. Índice nunca entra de memória: o script recebe o fator com série, código SGS e data de consulta, e o laudo transcreve essa origem no anexo. Se a API do BCB estiver indisponível, o cálculo para e o laudo não sai com índice estimado.

Isolamento de premissas em lote: data de citação, data de ciência do desfalque, último creditamento omitido, modalidades e corte prescricional são campos do `caso.json` de cada processo e aparecem no cabeçalho do quadro de cenários; antes de colar um quadro no laudo, conferir que o número do processo no cabeçalho é o do laudo (`references/conducao-do-lote.md`, seção 3).

## 6. Cenários por tese, sem escolher tese

O quadro de cenários é o coração do laudo do perito do juízo. Cada linha nomeia a tese que pressupõe, e o perito não diz qual é a correta:

| Cenário | Tese pressuposta | Correção e juros (motor da pericia-pasep) | Corte prescricional aplicado |
|---|---|---|---|
| A | Diferença imputável ao BB (Tema 1.150) | Percentuais oficiais do Tesouro até 31/05/2020, IPCA-E depois; juros civis (CC art. 406; Lei 14.905/2024) | Decenal, contado da ciência do desfalque informada nos autos |
| B | BB, critério alternativo | SELIC, sem juros adicionais | Idem A |
| C | Diferença imputável à União (Tema 545) | Regime intertemporal da Fazenda (EC 113/2021, art. 3º, na redação da EC 136/2025); Súmula 85/STJ | Quinquenal, com preservação das parcelas do quinquênio anterior à propositura |
| D | União, critério alternativo | INPC e juros civis | Idem C |

Para cada cenário o laudo apresenta duas colunas de valor: com o corte prescricional da tese e sem corte, para que o juízo veja o efeito da decisão sobre a prescrição. Quando a causa de pedir mistura saque e índice (litisconsórcio), o motor segrega cada diferença por origem e o laudo soma por polo. O perito ressalva no quadro que a aplicação do regime da EC 136/2025 à fase anterior ao precatório é controvertida (ressalva do cenário C na `pericia-pasep`). O que não entra no laudo: "a pretensão está prescrita", "o BB é parte ilegítima", "o autor não provou". Entram as datas, os documentos e os valores de cada hipótese (`references/laudo-e-quesitos.md`, seção 3).

## 7. Quesitos: matriz e respostas neutras

```bash
python3 scripts/matriz_quesitos.py --quesitos assets/exemplo_quesitos.json --documentos assets/exemplo_documentos.json --md matriz.md
python3 scripts/matriz_quesitos.py --quesitos P-002/quesitos.json --registro lote.json --processo P-002 --rigoroso
```

O script classifica cada quesito por tema (saldo, saques, índices, juros, prescrição, polo) e por tipo (fato contábil, questão de direito, misto, fora do objeto), sugere a seção do laudo, a evidência e o cenário em que a resposta se apoia, marca como pendente de diligência o quesito cujo documento ainda falta, detecta quesito repetido entre proponentes (resposta por remissão) e checa a cobertura: nenhum quesito sem seção nem sem resposta prevista. Com `--rigoroso`, cobertura incompleta sai com erro, para rodar antes de protocolar.

A classificação por palavra-chave é auxiliar e a leitura do perito prevalece. Quesito que pergunta "se" (está prescrito, é responsável, cabe o ônus) é questão de direito e recebe a abertura "Trata-se de questão de direito, cuja definição cabe ao juízo. Do ponto de vista contábil, ..." seguida do fato ou do cenário que a perícia apurou. Quesito de dano moral, honorários ou FGTS é fora do objeto e assim se declara (CPC art. 473, § 2º). Banco de respostas neutras em `references/laudo-e-quesitos.md`, seção 4.

## 8. Laudo, esclarecimentos e pós-laudo

Redigir pelo `assets/template_laudo_pasep.md`, que segue o art. 473 do CPC (objeto, análise, método e resposta conclusiva a todos os quesitos) e a NBC TP 01 (R2). Protocolar no prazo e com antecedência mínima de 20 dias da audiência (CPC art. 477, caput); prorrogação, uma vez e pela metade do prazo, só por motivo justificado (CPC art. 476). Depois do protocolo: `lote_pasep.py atualizar --status laudo_entregue --campo versao_laudo=v1`.

As partes têm 15 dias para se manifestar e os assistentes para apresentar parecer (CPC art. 477, § 1º); o perito tem 15 dias para esclarecer divergência ou dúvida de qualquer das partes, do juiz ou do Ministério Público e ponto divergente do parecer do assistente (CPC art. 477, § 2º). Registrar o prazo com `--status esclarecimentos --prazo-esclarecimentos dd/mm/aaaa`. Esclarecimento responde ponto a ponto, sem refazer o laudo e sem polemizar com o assistente: ou mantém com o fundamento, ou retifica com nova memória e nova versão (`v2`), declarando o que mudou. Audiência só por intimação eletrônica com dez dias de antecedência (CPC art. 477, §§ 3º e 4º); segunda perícia, se determinada, não substitui a primeira (CPC art. 480, § 3º). Roteiro em `references/laudo-e-quesitos.md`, seções 5 a 7.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler inicial, contestação, saneamento, extrato e documentos antes de registrar o processo; conferir se o extrato em PDF tem camada de texto ou é imagem |
| `bash` | Executar os três scripts desta skill em Python 3.11 e os scripts do motor da `pericia-pasep`, um `caso.json` por processo |
| `create_file` | Gravar registro do lote, checklists, matriz, laudo e esclarecimentos na pasta do processo em `/mnt/user-data/outputs` |
| `web_search` | Conferir, antes de citar, todo item marcado [A VERIFICAR] e o andamento dos temas pendentes (stj.jus.br, stf.jus.br, planalto.gov.br, cfc.org.br) |

| Skill | Quando |
|---|---|
| `pericia-pasep` | Todo cálculo: reconstrução, conciliação, fatores, cenários e autoteste; jurisprudência auditada; parecer de assistente técnico, MIPD e impugnação quando o papel for esse |
| `proposta-pericial-judicial` | Proposta de honorários, currículo e estimativa de horas na nomeação |
| `resumo-autos` e `mapa-processo` | Autos volumosos: resumo e linha do tempo antes da triagem |
| `quitacao-fgts-tema-1176` | Discussão de FGTS ou PIS da Caixa que apareça nos mesmos autos |
| `atualizacao-monetaria` | Atualização de valores por critério fixado pelo juízo fora dos cenários A a D (liquidação) |
| `gestao-pericial-peritos` | Carteira do escritório além do lote de PASEP (honorários, agenda, produtividade) |
| `entrega-finalizacao-pericial` | Checklist de fechamento e protocolo do laudo |
| `chelfo-docx-brand` | Conversão do laudo em `.docx` no padrão institucional, só sob pedido |
| `chelfo-skill-forge` | Manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/lote_pasep.py` | Registro do lote (criar, adicionar, atualizar) e painel ordenado por prazo com alerta, em JSON, Markdown e CSV | `python3 scripts/lote_pasep.py painel --registro lote.json --hoje 12/09/2026 --md painel.md` |
| `scripts/checklist_documental_pasep.py` | Faltantes por modalidade, termo de diligência, ofício ao BB e solicitação ao autor, com prazo em dias úteis | `python3 scripts/checklist_documental_pasep.py --documentos assets/exemplo_documentos.json --md termo.md` |
| `scripts/matriz_quesitos.py` | Matriz quesito, tema, tipo, seção, evidência, cenário, status; aberturas neutras; checagem de cobertura | `python3 scripts/matriz_quesitos.py --quesitos assets/exemplo_quesitos.json --documentos assets/exemplo_documentos.json --md matriz.md` |

Os três são de organização: só biblioteca padrão, sem rede, sem `Decimal` porque não há valor monetário, datas em `dd/mm/aaaa`, saída JSON com `premissas`, `locale`, `arredondamento` e `memoria`, erro de validação com `ERRO de validação:` e código 1, e um teste de sanidade embutido (uma linha por processo ou por quesito, ids únicos, todo faltante presente no termo). Exemplos de entrada em `assets/`.

## Estrutura do output

Seções obrigatórias do laudo (template completo, com exemplo preenchido, em `assets/template_laudo_pasep.md`):

1. Identificação e encargo (processo, juízo, partes, perito, nomeação, encargo do art. 466).
2. Objeto fixado no saneamento, limites (CPC art. 473, § 2º) e quadro dos quesitos recebidos com a seção da resposta.
3. Documentos examinados e diligências realizadas, com o período coberto pelo extrato e as lacunas.
4. Metodologia e fontes: motor, ordem de valorização, séries SGS e tabela do Tesouro com data de consulta.
5. Análise: 5.1 datas e marcos de fato; 5.2 reconstrução do saldo; 5.3 saídas, modalidade e comprovação (Tema 1.300/STJ); 5.4 índices, rendimentos e conciliação.
6. Cenários de atualização A a D, rotulados pela tese pressuposta, com e sem corte prescricional.
7. Resposta a todos os quesitos (juízo, autor, réus), com remissão à seção e ao documento.
8. Conclusão neutra e limitações.
9. Encerramento, anexos (memória do motor, consultas ao SGS, tabela do Tesouro, matriz de quesitos) e pendências de verificação.

Exemplo de resposta a quesito de fato (dados fictícios dos assets):

> Quesito 2 do juízo: "Classifique cada saída lançada na conta por modalidade e informe se há nos autos a comprovação correspondente."
> Resposta: O extrato analítico (fls. 88 a 131) registra quatro saídas: 14/08/1998, R$ 1.250,00, código de histórico de saque em caixa (CAIXA-BB); 03/03/2003, R$ 2.180,00, CAIXA-BB; 10/06/2011, R$ 940,00, pagamento em folha (FOPAG); 22/09/2016, R$ 3.100,00, código não identificado na legenda juntada (OUTROS). Para as duas saídas em caixa, o Banco do Brasil não apresentou recibo, identificação do recebedor ou registro biométrico, apesar do ofício de 12/09/2026 (fl. 140); para a saída em folha, a autora não juntou contracheques de junho e julho de 2011, apesar da solicitação de fl. 141. O quadro 5.3 consolida o resultado. A consequência da ausência de cada prova é matéria do art. 373 do CPC e do Tema 1.300/STJ e cabe ao juízo.

Exemplo de resposta a quesito de direito:

> Quesito 1 do réu: "A pretensão da autora está prescrita, considerando que o primeiro saque impugnado ocorreu em 1998?"
> Resposta: Trata-se de questão de direito, cuja definição cabe ao juízo. Do ponto de vista contábil, a perícia registra as datas de fato relevantes: saques impugnados em 14/08/1998 e 03/03/2003; ciência do desfalque alegada pela autora em 10/03/2021, data da emissão do extrato de fl. 22; propositura em 05/05/2023; citação em 20/06/2023. O quadro 6 apresenta, para cada cenário, o valor sem corte prescricional e o valor com o corte que cada tese pressupõe (decenal contado de 10/03/2021 no cenário A; quinquenal anterior a 05/05/2018 no cenário C), sem adotar nenhum deles.

Exemplo de linha do painel (saída de `lote_pasep.py painel` com os assets):

```
| 1 | P-002 | 0000002-00.0000.0.00.0000 | 2ª Vara Cível, Comarca fictícia | BB | diligencia | laudo | 25/09/2026 | 13 | 10 | alerta: menos de 15 dias | 13 | extrato_analitico, microfilmagem, contracheques | Expedir ofício ao BB |
```

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_PASEP_<id>_vN.md` (por exemplo, `2026-10-20_Laudo_PASEP_P-002_v1.md`); esclarecimentos como `AAAA-MM-DD_Esclarecimentos_PASEP_<id>_vN.md`.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- CPC/2015: art. 148, II (impedimento e suspeição do perito); arts. 156 a 158 (nomeação, dever de diligência, escusa e responsabilidade); art. 219 (prazo em dias úteis); art. 357, III (ônus da prova no saneamento); art. 373, I e II (ônus da prova); arts. 396 a 400 (exibição de documento); arts. 464 a 480 (prova pericial: 465 nomeação, prazo, assistentes e quesitos, proposta em 5 dias e levantamento de 50%; 466 encargo sem compromisso e acesso dos assistentes; 467 escusa; 468 substituição; 469 quesitos suplementares; 470 quesitos do juiz; 471 perícia consensual; 473 conteúdo do laudo e limites; 474 ciência das diligências; 476 prorrogação; 477 prazo, manifestação e esclarecimentos; 479 apreciação; 480 segunda perícia); art. 927, III (vinculação dos repetitivos).
- CC: art. 205 (prescrição decenal, fundamento do Tema 1.150); art. 320 (quitação); art. 406 (juros, redação da Lei 14.905/2024). DL 20.910/1932, art. 1º (prescrição quinquenal contra a Fazenda, fundamento do Tema 545).
- LC 8/1970 e LC 26/1975, art. 3º (PASEP e juros mínimos); Lei 9.365/1996, art. 12 (TJLP); EC 113/2021, art. 3º, na redação da EC 136/2025 (regime de atualização da União). Detalhe em `pericia-pasep/references/legislacao.md`.
- NBC TP 01 (R2) (perícia contábil: planejamento, diligências, laudo) e NBC PP 01 (R2) (perito contábil: independência, impedimento, sigilo, honorários). Lei 13.709/2018 (LGPD), art. 7º, VI (tratamento para exercício de direitos em processo).

Jurisprudência verificada (identificação copiada de `pericia-pasep/references/jurisprudencia.md`, auditada em fontes primárias em 13/06/2026 e 04/08/2026): STJ Tema 545 (REsp 1.205.277/PB, Rel. Min. Teori Albino Zavascki, Primeira Seção, j. 27/06/2012); STJ Tema 1.150 (REsp 1.895.936/TO, 1.895.941/TO e 1.951.931/DF, Rel. Min. Herman Benjamin, Primeira Seção, j. 13/09/2023, DJe 21/09/2023); STJ Tema 1.300 (REsp 2.162.222/PE, 2.162.223/PE, 2.162.198/PE e 2.162.323/PE, Rel. Min. Maria Thereza de Assis Moura, Primeira Seção, j. 10/09/2025, acórdão publicado em 18/09/2025); Súmula 85/STJ; STF Tema 810 (RE 870.947/SE). Teses e aplicação em `references/fundamentacao-legal.md`, seção 6.

Protocolo antifabricação: número de Tema, Súmula, REsp, item de norma do CFC, resolução do CNJ, código de série do SGS e percentual de valorização exigem verificação em fonte oficial (stj.jus.br, stf.jus.br, planalto.gov.br, cfc.org.br, cnj.jus.br, bcb.gov.br, tesouro.gov.br). Fora da lista verificada, citar somente com `[A VERIFICAR]` ao lado e levar o item à seção "Pendências de verificação" do laudo. O perito do juízo que cita precedente inexistente responde pelo art. 158 do CPC; a citação apócrifa "RE 1.220.711/STF" e a suposta repercussão geral do STF sobre prescrição do PASEP não existem e não entram em laudo.

Pendências de verificação desta versão: numeração dos itens da NBC TP 01 (R2) e da NBC PP 01 (R2); Resolução CNJ 233/2016 (cadastro de peritos) e Resolução CNJ 232/2016 (tabela de honorários na gratuidade); STJ Tema 1.309 e Tema 905, registrados na `pericia-pasep` como correlatos; data do trânsito em julgado do Tema 1.150; tema pendente no STF sobre o regime da EC 136/2025 na fase anterior ao precatório. Lista completa em `references/fundamentacao-legal.md`, seção 12.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | Procedimento da prova pericial artigo a artigo, deveres do perito, honorários, estrutura do laudo, ônus por modalidade, jurisprudência verificada, prescrição e atualização como premissas de cenário, LGPD, roteiro de quesitos do juízo, pendências | Etapas 2, 3, 6, 7 e 8 |
| `references/conducao-do-lote.md` | Rotina semanal, pastas e nomes de arquivo por processo, isolamento de premissas, controle de versões, sigilo e anonimização, comunicação só nos autos, checklist de fechamento | Etapas 1, 5 e 8 |
| `references/laudo-e-quesitos.md` | Estrutura do laudo (art. 473 e NBC TP 01), linguagem neutra, quadro de cenários sem escolher tese, banco de respostas neutras a quesitos recorrentes do BB, da União e do autor, roteiro de esclarecimentos e de audiência | Etapas 6, 7, 8 e 9 |
| `assets/template_laudo_pasep.md` | Template do laudo com exemplo preenchido e pendências | Etapa 8 |
| `assets/exemplo_*.json` | Entradas fictícias dos três scripts e registro de lote de exemplo | Etapas 1, 4 e 7 |

## Extensão e manutenção

1. Novo documento exigido (por exemplo, extrato do FGTS após a migração de 2020): adicionar a entrada em `EXIGENCIAS_BASE` ou `EXIGENCIAS_POR_MODALIDADE` de `scripts/checklist_documental_pasep.py` e a chave em `DOCUMENTOS_PADRAO` de `scripts/lote_pasep.py`; o termo e o ofício passam a incluí-lo sem outra alteração.
2. Novo status do procedimento (por exemplo, `audiencia`): incluir em `STATUS_VALIDOS` e, se tiver prazo próprio, tratar em `prazo_vigente()` de `scripts/lote_pasep.py`.
3. Novo tema ou palavra-chave de quesito: acrescentar em `TEMA_KW`, `MAPA_TEMA`, `COMPLEMENTO_DIREITO` e `COMPLEMENTO_FATO` de `scripts/matriz_quesitos.py`, mantendo a numeração de seções do template.
4. Novo precedente: só entra em `references/fundamentacao-legal.md`, seção 6, depois de constar como verificado em `pericia-pasep/references/jurisprudencia.md`; até lá, fica na seção 12 com `[A VERIFICAR]`.
5. Versionamento SemVer no frontmatter e no `CHANGELOG.md`: novo status, documento ou palavra-chave é `minor`; mudança nas chaves do registro do lote ou do JSON de saída, que quebra o encadeamento, é `major`.

Manutenção desta skill: acionar `chelfo-skill-forge`.
