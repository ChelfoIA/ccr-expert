---
name: auditoria-contabil-espolio
description: "Auditar em perícia contábil a administração do espólio, do óbito à partilha, em inventário ou prestação de contas. Usar quando: (1) Reconstruir o fluxo de caixa por conta, mês e categoria; (2) Apontar saídas sem alvará, sem documento ou a herdeiro e despesa estranha ao espólio; (3) Apurar aluguel contratado, recebido e de mercado por imóvel; (4) Calcular o aluguel devido pelo herdeiro que ocupa imóvel com exclusividade, marco e encargos; (5) Converter rendas de bem em Portugal pela PTAX; (6) Comparar lucros, pró-labore e mútuos de sociedade fechada com o que coube ao espólio; (7) Quantificar o que deixou de entrar e redigir laudo e quesitos. Acionar ao mencionar: espólio, inventariante, prestação de contas do inventário, herdeiro morando no imóvel sem pagar aluguel, desvio de finalidade, sonegados, frutos da herança, imóvel em Portugal, PTAX, lucros da empresa do falecido, quanto o espólio deixou de ganhar. COMPLEMENTAR a apuracao-haveres: use ESTA para frutos e caixa; use aquela para o valor das quotas."
metadata:
  version: "1.0.0"
  author: "Prof. Carlos André Moreira Chelfo (ChelfoIA)"
  updated: "2026-09-12"
---

# Auditoria contábil do espólio: fluxo de caixa, frutos dos bens e desvio de finalidade

Versão 1.0.0 (12/09/2026).

## Escopo

Auditoria contábil e perícia sobre a administração do espólio desde a abertura da sucessão até a partilha (CC, arts. 1.784 e 1.991; CPC, arts. 618 a 622), em inventário judicial, prestação de contas em apenso, ação autônoma de exigir contas ou ação de arbitramento de aluguel. Cobre a reconstrução do fluxo de caixa por conta e categoria, as saídas sem autorização ou sem documento e as despesas estranhas ao espólio, os frutos de cada imóvel (contratado, recebido, de mercado, vacância), o aluguel devido por herdeiro que ocupa imóvel com exclusividade e os encargos desse imóvel, os bens situados em Portugal com fluxo em euro convertido pela PTAX, as participações em sociedades de capital fechado (lucros distribuídos, pró-labore, mútuos, retiradas) e a quantificação do que o espólio deixou de receber. Papel padrão: perito do juízo; variante: assistente técnico de herdeiro, com a mesma memória.

Fora de escopo: avaliação das quotas e dos imóveis (`valuation-capital-fechado`, `apuracao-haveres` e laudo de engenharia), extração massiva de extratos (`analise-extratos-forense`), atualização dos valores apurados (`atualizacao-monetaria`), colação, partilha, remoção do inventariante e pena de sonegados (matéria do juízo), proposta de honorários (`proposta-pericial-judicial`).

## Princípio reitor

Quem administra bens alheios responde por três coisas: o que entrou, o que saiu e o que deveria ter entrado. O inventariante e o herdeiro em posse de bens da herança trazem ao acervo os frutos que perceberam desde a abertura da sucessão, têm direito ao reembolso das despesas necessárias e úteis e respondem pelo dano por dolo ou culpa (CC, art. 2.020); até a partilha, a herança é condomínio, e cada condômino responde aos demais pelos frutos que percebeu (CC, arts. 1.791 e 1.319). O laudo tem, portanto, três colunas em cada quadro: realizado, esperado e diferença, cada uma com documento e premissa.

Quatro erros derrubam laudos neste domínio, e a skill os elimina por construção. Somar sem perímetro (movimento anterior ao óbito, conta fora do acervo, euro com real): os scripts cortam pela data do óbito, exigem saldo inicial documentado e recusam moeda estrangeira não convertida. Escolher o marco inicial do aluguel do ocupante: o script calcula em cada marco documentado e o juízo escolhe. Estimar o que não tem documento (cotação, aluguel de mercado, lucro): os scripts falham sem fonte, porque número estimado em laudo de prestação de contas é impugnação certa. Contar duas vezes a mesma parcela (encargo do imóvel ocupado no fluxo e no quadro de imóveis): o laudo declara em qual quadro cada valor entra (REsp 1.918.125).

## Workflow principal

```
0. Perímetro      -> certidão de óbito (abertura da sucessão), primeiras e últimas declarações,
                     termo de inventariante, alvarás e decisões (CPC, art. 619), extratos com saldo
                     na data do óbito, DIRPF e declarações de espólio; termo de diligência e ofícios
                     (references/roteiro-auditoria-e-documentos.md, seções 1 a 3)
1. Transcrição    -> CSV de movimentos de todas as contas (layout de assets/exemplo_movimentos.csv);
                     conta de uso misto identificada; euro em CSV próprio
2. Conversão      -> scripts/conversao_ptax.py sobre os movimentos em euro, série PTAX por arquivo
                     com fonte; CSV convertido entra na etapa 3
3. Fluxo de caixa -> scripts/fluxo_caixa_espolio.py: DFC mensal, conciliação com o extrato, listas
                     de exceção, saídas por herdeiro ou inventariante, recomposição sugerida
4. Imóveis        -> scripts/rendimentos_imoveis.py: esperado x recebido por imóvel e mês; aluguel
                     devido pelo ocupante em cada marco; encargos; meses sem lastro
5. Sociedades     -> quadro por sociedade (assets/exemplo_sociedades.csv) a partir de balanço, DRE,
                     atas e razão de sócios (references/imoveis-empresas-e-exterior.md, seção 5)
6. Laudo          -> quantificação consolidada sem dupla contagem; assets/template_laudo.md;
                     quesitos (references/fundamentacao-legal.md, seção 7); docx só sob pedido
```

Executar as etapas 2, 3 e 4 em Python, com os CSV transcritos dos extratos e dos autos. Fluxo de trinta meses com dezenas de lançamentos feito à mão perde centavos e, pior, perde o perímetro.

## 1. Perímetro, documentos e transcrição

Ler primeiro a certidão de óbito, as declarações do inventariante e os alvarás, porque a data do óbito é o corte do fluxo (CC, art. 1.784) e os alvarás definem o que foi autorizado (CPC, art. 619). Requisitar os extratos de cada conta do falecido e do espólio desde noventa dias antes do óbito, com saldo, e os da conta do inventariante ou de herdeiro quando usada para o espólio. Documento em poder de terceiro (banco, sociedade, administradora, entidades portuguesas) é requerido por intermédio do juízo (CPC, arts. 401 a 404); o que não vier é limitação declarada, com cronologia, nunca estimativa.

Transcrever um movimento por linha no layout `data;conta;historico;valor;tipo;categoria;beneficiario;vinculo_beneficiario;autorizacao_judicial;documento;imovel_id;empresa_id`, com `moeda` opcional (só BRL). Categoria pela natureza econômica, não pelo nome do favorecido; `autorizacao_judicial` S só com decisão localizada; `documento` vazio significa sem lastro. Conta de uso misto e conta conjunta seguem o critério de segregação de `references/roteiro-auditoria-e-documentos.md`, seção 5, declarado como premissa.

## 2. Fluxo de caixa do espólio

```bash
python3 scripts/fluxo_caixa_espolio.py --movimentos assets/exemplo_movimentos.csv \
  --abertura-sucessao 10/01/2024 --data-referencia 30/06/2026 --saldo-inicial 12.500,00 \
  --saldo-final-extrato 38.430,55 --imoveis-ocupados IM02 --saida fluxo.json --csv dfc.csv --md dfc.md
```

O script exclui os movimentos anteriores à abertura da sucessão (listados em `fora_do_periodo`, porque podem revelar bem não declarado), ordena, reconstrói o saldo movimento a movimento e monta a DFC mensal por categoria, os totais por conta e por vínculo do beneficiário e as saídas por herdeiro ou inventariante. Sanidade embutida: entradas menos saídas igual à variação do saldo; soma das variações mensais igual à variação total; soma das categorias igual aos totais; transferências internas fecham entre contas. Com `--saldo-final-extrato`, a conciliação divergente faz o script falhar de propósito, apontando movimento faltante ou conta fora do perímetro.

Listas de exceção, cada uma com o motivo e o dispositivo: saídas sem autorização fora das despesas de conservação (CPC, art. 619); despesas de conservação sem alvará prévio, separadas porque admitem ratificação na prestação de contas (art. 619, IV); alienação ou pagamento de dívida sem alvará (art. 619, I e III); saídas sem documento; saídas em favor de herdeiro ou inventariante (adiantamento de quinhão, reembolso ou recomposição, conforme a prova); despesas estranhas ao espólio (desvio de finalidade, CC, art. 2.020); encargos de imóvel ocupado por herdeiro pagos pelo espólio (REsp 1.704.528), identificados por `--imoveis-ocupados`. A recomposição sugerida soma despesas pessoais, saídas a herdeiro ou inventariante sem alvará e encargos do imóvel ocupado, cada movimento uma única vez, em valor nominal.

## 3. Achados e desvio de finalidade

Exemplo de quadro de exceções (dados fictícios dos assets, saída de `fluxo_caixa_espolio.py`):

| Lista | Itens | Valor nominal | Tratamento no laudo |
|---|---:|---:|---|
| Saídas sem autorização, fora da conservação | 5 | R$ 21.800,00 | achado por item (CPC, art. 619) |
| Conservação sem alvará prévio | 18 | R$ 24.800,00 | ratificação na prestação de contas (art. 619, IV) |
| Saídas sem documento | 4 | R$ 17.900,00 | não comprovadas nos autos |
| Saídas a herdeiro ou inventariante | 2 | R$ 13.000,00 | recomposição, salvo decisão ou recibo |
| Despesas estranhas ao espólio | 2 | R$ 4.800,00 | recomposição (CC, art. 2.020) |
| Encargos de imóvel ocupado pagos pelo espólio | 13 | R$ 11.400,00 | quadro de imóveis, não aqui |

Achado é fato, evidência, norma e efeito, nessa ordem, no vocabulário de `references/roteiro-auditoria-e-documentos.md`, seção 8: "sem documento nos autos", "sem autorização localizada", "estranha ao espólio", "em favor de". O perito não escreve "desviou" nem "fraudou"; descreve a saída, aponta o dispositivo e diz em que quadro o valor entra. Saída com alvará não é exceção, ainda que o perito a considere cara; vira achado só se o valor pago excede o autorizado ou se o documento não corresponde ao objeto autorizado. Testes por categoria (aluguel, dividendo, venda de bem, tributo, dívida, retirada) em `references/roteiro-auditoria-e-documentos.md`, seção 6; censo para toda saída a herdeiro ou inventariante, toda saída sem documento e toda venda de bem; amostra, por analogia com a NBC TA 530, só para despesas recorrentes de conservação, com critério declarado.

## 4. Frutos dos imóveis e herdeiro ocupante

```bash
python3 scripts/rendimentos_imoveis.py --imoveis assets/exemplo_imoveis.csv \
  --recebimentos assets/exemplo_recebimentos_alugueis.csv --herdeiros 4 \
  --abertura-sucessao 10/01/2024 --data-referencia 30/06/2026 --saida imoveis.json --md imoveis.md
```

Para cada imóvel e mês, o script calcula esperado, recebido e diferença, com mês parcial pro rata die (CC, art. 1.215) e moedas apuradas em separado. A base do esperado depende da situação: locado, o aluguel contratual; ocupado por herdeiro, o aluguel de mercado vezes a fração dos demais coerdeiros; vago, a renda potencial de mercado, que sai em linha informativa porque só vira dano com prova de culpa na administração; uso do espólio, nada. Aluguel de mercado exige `fonte_mercado` (laudo, anúncios datados, índice); sem fonte o script não roda.

Ocupante: devido = aluguel de mercado x (1 - fração do ocupante) x meses desde o marco inicial (CC, arts. 1.319 e 2.020). O marco é parâmetro por imóvel, e o perito calcula em cada data documentada: oposição inequívoca dos demais (REsp 1.583.973), notificação extrajudicial (AREsp 3.121.778/SP), citação (CPC, art. 240) e, como sensibilidade, a abertura da sucessão (`--abertura-sucessao` gera o cenário alternativo). Decisão deferindo o uso antecipado do bem como parte da cota (CPC, art. 647, parágrafo único) ou anuência dos demais afasta o aluguel; a inércia dos demais não configura supressio, e a prescrição só corre após o trânsito em julgado da partilha (AgInt no REsp 2.240.323). IPTU e condomínio posteriores ao óbito ficam com quem usa o bem (REsp 1.704.528); informados em `encargos_pagos_espolio`, aparecem no quadro do imóvel e são subtraídos da recomposição do caixa, nunca cobrados duas vezes (REsp 1.918.125). Sanidade: soma mensal igual a base x meses equivalentes; a fórmula é reproduzida no JSON com cada fator. Linhas do STJ e exceções em `references/imoveis-empresas-e-exterior.md`, seção 1.

## 5. Bens em Portugal e conversão pela PTAX

```bash
python3 scripts/conversao_ptax.py --ptax assets/exemplo_ptax_eur.csv \
  --movimentos assets/exemplo_movimentos_eur.csv --criterio venda \
  --saida ptax.json --csv movimentos_brl.csv --md ptax.md
```

A autoridade brasileira tem competência exclusiva para inventariar e partilhar bens situados no Brasil (CPC, art. 23, II); o bem em Portugal segue a jurisdição local. Para a auditoria isso não muda nada: a renda do imóvel de Lisboa é fruto do espólio desde o óbito (CC, arts. 1.784 e 2.020) e quem a recebeu presta contas dela. O laudo anota a questão em uma frase e segue.

O fluxo em euro é transcrito no mesmo layout e convertido linha a linha pela PTAX da data do movimento, lida de arquivo `data;compra;venda;fonte` com a fonte obrigatória (série do SGS do BCB, código [A VERIFICAR], data da consulta). Sem cotação no dia, o script usa a do dia útil anterior disponível e declara a defasagem; sem cotação em até `--max-defasagem` dias, falha. Critério padrão venda, declarado como premissa; `compra` e `media` recalculam. O script não acessa a rede e não estima; `--online` apenas explica onde obter a série. A série dos assets é fictícia, marcada como tal na coluna `fonte`, e o script avisa quando a encontra. O CSV convertido entra em `fluxo_caixa_espolio.py` com a cotação rastreada na coluna `conversao` de cada exceção. IMI, IRS sobre rendimentos prediais e condomínio são despesas documentadas do imóvel, conferidas contra as notas, sem recálculo; as regras portuguesas são pendência [A VERIFICAR].

## 6. Sociedades de capital fechado

Ler a cláusula de falecimento do contrato social antes de qualquer número (CC, art. 1.028): continuidade com os herdeiros faz do espólio um sócio que participa dos lucros pro rata (CC, art. 1.007), salvo cláusula válida de distribuição desproporcional; liquidação da quota gera crédito de haveres (`apuracao-haveres`) mais os lucros até a data da resolução. O quadro por sociedade segue o layout de `assets/exemplo_sociedades.csv`, preenchido a partir de balanços, DRE, atas, razão das contas de sócios, folha de pró-labore e DIRPF dos sócios, todos requeridos por intermédio do juízo porque a sociedade é terceiro.

Três linhas por sociedade, sem soma automática entre elas: lucros distribuídos devidos ao espólio (distribuído total x participação) menos o recebido; lucro suprimido por retirada (pró-labore acima da referência de mercado com fonte, mútuo sem contrato, despesa pessoal na empresa) na parcela do espólio; lucro acumulado não distribuído como informação, porque depende de deliberação. Sinais de retirada disfarçada e exemplo numérico com os assets em `references/imoveis-empresas-e-exterior.md`, seções 5 e 6. Com os assets: Alfa Comércio Ltda., 60%, distribuiu R$ 100.000,00; devido R$ 60.000,00; recebido R$ 25.000,00; diferença R$ 35.000,00; pró-labore R$ 180.000,00 contra referência de R$ 96.000,00, lucro suprimido na parcela do espólio R$ 50.400,00.

## 7. Quantificação consolidada e laudo

Consolidar pelo quadro de atribuição única de `references/imoveis-empresas-e-exterior.md`, seção 7: cada parcela entra em um único quadro (recomposição do caixa, imóveis, exterior já em reais, sociedades) e o laudo declara qual. Valores nominais nas datas dos movimentos; atualização pela skill `atualizacao-monetaria` quando o juízo fixar o critério. Redigir pelo template `assets/template_laudo.md`; como assistente técnico, trocar o título por parecer e declarar a parte assistida.

Checklist antes de entregar:

1. Sanidade OK nos três scripts, com os JSON de memória em anexo e a conciliação do saldo final.
2. Perímetro declarado: data do óbito, data de referência, contas (com as de uso misto), bens.
3. Marco inicial do aluguel do ocupante calculado em cada data documentada; fração e fonte do aluguel de mercado declaradas.
4. Série PTAX com fonte e data; nenhuma cotação, aluguel ou lucro estimado.
5. Nenhuma parcela em dois quadros; encargos do imóvel ocupado em um só lugar.
6. Achados sem qualificação jurídica; documentos não fornecidos com cronologia e efeito.
7. Todo item `[A VERIFICAR]` listado na seção de pendências.

## Integração sistêmica

| Ferramenta | Uso obrigatório |
|---|---|
| `view` | Ler certidão de óbito, declarações, alvarás, extratos, contratos de locação, contrato social e balanços antes de transcrever qualquer CSV; conferir se o PDF tem camada de texto |
| `bash` | Executar os três scripts em Python 3.11, encadeando o CSV de `conversao_ptax.py` em `fluxo_caixa_espolio.py` |
| `create_file` | Gravar os CSV transcritos, as saídas (JSON, Markdown, CSV), o quadro de sociedades e o laudo em `/mnt/user-data/outputs` |
| `web_search` | Conferir, antes de citar, todo item [A VERIFICAR]: código da série PTAX no SGS, regras portuguesas de IMI e IRS, tema repetitivo sobre aluguel entre coerdeiros, normas da RFB sobre espólio (bcb.gov.br, stj.jus.br, gov.br/receitafederal, portaldasfinancas.gov.pt) |

| Skill | Quando |
|---|---|
| `analise-extratos-forense` | Extrair e estruturar extratos volumosos antes de montar o CSV de movimentos |
| `apuracao-haveres` | Valor da quota do sócio falecido quando o contrato prevê liquidação (CC, arts. 1.028 e 1.031) |
| `valuation-capital-fechado` | Valor das participações para a partilha |
| `atualizacao-monetaria` | Atualizar os valores quantificados até a data-base fixada pelo juízo |
| `pericia-lavagem-dinheiro` | Rastreamento do destino de saídas relevantes a terceiros, se determinado |
| `proposta-pericial-judicial` | Proposta de honorários na nomeação (CPC, art. 465, § 2º) |
| `chelfo-docx-brand` | Conversão do laudo ou do parecer em `.docx` no padrão institucional, só sob pedido |
| `chelfo-skill-forge` | Manutenção, auditoria ou evolução desta skill |

## Scripts disponíveis

| Script | Função | Uso |
|---|---|---|
| `scripts/fluxo_caixa_espolio.py` | DFC mensal por categoria, conta e vínculo; conciliação com o extrato; listas de exceção; recomposição sugerida; sanidade | `python3 scripts/fluxo_caixa_espolio.py --movimentos assets/exemplo_movimentos.csv --abertura-sucessao 10/01/2024 --saldo-inicial 12.500,00 --imoveis-ocupados IM02 --saida fluxo.json --md dfc.md` |
| `scripts/rendimentos_imoveis.py` | Esperado x recebido por imóvel e mês; aluguel devido pelo ocupante (mercado x (1 - fração) x meses) com cenário alternativo de marco; encargos; meses sem lastro | `python3 scripts/rendimentos_imoveis.py --imoveis assets/exemplo_imoveis.csv --recebimentos assets/exemplo_recebimentos_alugueis.csv --herdeiros 4 --abertura-sucessao 10/01/2024 --data-referencia 30/06/2026 --md imoveis.md` |
| `scripts/conversao_ptax.py` | Converte movimentos em euro pela PTAX da data lida de arquivo com fonte; dia útil anterior declarado; CSV pronto para o fluxo | `python3 scripts/conversao_ptax.py --ptax assets/exemplo_ptax_eur.csv --movimentos assets/exemplo_movimentos_eur.csv --criterio venda --csv movimentos_brl.csv` |

Todos usam só a biblioteca padrão, `Decimal` com `ROUND_HALF_UP` e arredondamento apenas na apresentação, aceitam número no padrão brasileiro e técnico, gravam `premissas`, `locale`, `arredondamento` e `memoria` no JSON e saem com `ERRO de validação:` quando falta coluna, data, fonte ou a sanidade não fecha. Nenhum acessa a rede.

## Estrutura do output

Seções obrigatórias do laudo (template completo, com exemplo preenchido, em `assets/template_laudo.md`):

1. Objeto, com a delimitação do que é do juízo (marco, fração, colação, partilha, remoção, sonegados).
2. Quesitos do juízo e das partes, com a seção da resposta.
3. Metodologia e premissas (perímetro, saldo inicial, pro rata, fração, marcos, critério PTAX, segregação de conta mista).
4. Documentos examinados, requeridos e não fornecidos, e perímetro de bens e contas.
5. Fluxo de caixa do espólio, com conciliação e sanidade.
6. Exceções e desvio de finalidade, com os achados em fato, evidência, norma e efeito.
7. Frutos dos imóveis no Brasil e em Portugal, com o aluguel do ocupante em cada marco e a conversão PTAX.
8. Sociedades de capital fechado.
9. Quantificação consolidada sem dupla contagem, em valores nominais.
10. Conclusão, com limitações declaradas.
11. Resposta aos quesitos.
12. Encerramento, anexos e pendências de verificação.

Exemplo de quadro por imóvel (dados fictícios dos assets, referência 30/06/2026):

| Imóvel | Situação | Base mensal | Meses | Esperado | Recebido | Diferença |
|---|---|---:|---:|---:|---:|---:|
| IM01 | locado | R$ 3.000,00 | 29,7097 | R$ 89.129,03 | R$ 81.000,00 | R$ 8.129,03 |
| IM02 | ocupado por herdeiro (1/4) | R$ 3.000,00 | 24,0000 | R$ 72.000,00 | R$ 0,00 | R$ 72.000,00 |
| IM03 | locado (Lisboa) | EUR 1.200,00 | 29,7097 | EUR 35.651,61 | EUR 33.600,00 | EUR 2.051,61 |
| IM04 | vago | R$ 1.500,00 | 18,0000 | R$ 27.000,00 | R$ 0,00 | R$ 27.000,00 (informativa) |

Exemplo de resposta a quesito:

> Quesito 4 do juízo: "Qual o valor devido pelo herdeiro que ocupa a casa de Campinas aos demais coerdeiros, e a partir de quando?"
> Resposta: O valor mensal é de R$ 3.000,00, correspondente ao aluguel de mercado de R$ 4.000,00 (laudo de avaliação de fl. 210) multiplicado pela fração dos demais coerdeiros (3/4). Desde a notificação extrajudicial de 01/07/2024 até 30/06/2026 o total é de R$ 72.000,00 (24 meses); se o juízo adotar a abertura da sucessão (10/01/2024), o total é de R$ 89.129,03 (29,7097 meses, pro rata die no mês parcial), conforme a tabela mensal do Anexo II. O espólio pagou R$ 11.400,00 de condomínio e IPTU desse imóvel após o óbito, encargos a cargo do ocupante (REsp 1.704.528), computados uma única vez no quadro de imóveis (REsp 1.918.125). Valores nominais; a fixação do marco é do juízo.

Exemplo de resposta sobre saída sem documento:

> Quesito 2 do herdeiro requerente: "Houve retirada de recursos do espólio pela inventariante sem autorização?"
> Resposta: Em 10/06/2025 saíram R$ 5.000,00 da conta do espólio no Banco do Brasil por PIX a Maria Alfa, inventariante (linha 52 do CSV), sem alvará, decisão ou recibo nos autos; o pedido de esclarecimento de 15/08/2026 ficou sem resposta. A saída consta da lista de exceções (Anexo I) e integra a recomposição sugerida em valor nominal. Juntada decisão de adiantamento de quinhão ou comprovante de despesa do espólio paga pela inventariante, o valor muda de natureza, matéria do juízo.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_AuditoriaEspolio_vN.md`.

## Fundamentação normativa

Núcleo verificado (citar com dispositivo):

- Código Civil (Lei 10.406/2002): art. 1.784 (saisine); art. 1.791 (indivisibilidade e condomínio até a partilha); art. 1.319 (frutos entre condôminos); art. 1.215 (frutos civis dia a dia); art. 1.991 (administração pelo inventariante); arts. 1.992 a 1.996 (sonegados); art. 2.020 (frutos, reembolso e dano); arts. 884 a 886 (enriquecimento sem causa); arts. 1.007 e 1.008 (lucros na proporção das quotas); arts. 1.028 e 1.031 (morte de sócio e liquidação da quota).
- CPC (Lei 13.105/2015): art. 23, II (jurisdição exclusiva para bens no Brasil); art. 240 (citação e mora); art. 373 (ônus da prova); arts. 396 a 404 (exibição de documento por parte e por terceiro); arts. 464 a 480 (perícia; art. 473, §§ 2º e 3º); arts. 550 a 553 (exigir contas; contas do inventariante em apenso); art. 612 (questões no inventário); arts. 618 e 619 (deveres do inventariante e atos que exigem autorização); arts. 620 a 625 (declarações e remoção); art. 647, parágrafo único (uso antecipado de bem por herdeiro); arts. 659 a 667 (arrolamento).
- LINDB (DL 4.657/1942), art. 10 (lei aplicável à sucessão); Lei 8.245/1991, art. 19 (revisão do aluguel após três anos).
- NBC TP 01 (R1) e NBC PP 01 (R1), CFC; NBC TA 240 e NBC TA 530, por analogia declarada.

Jurisprudência verificada (consulta de 12/09/2026; identificação completa e links em `references/fundamentacao-legal.md`, seção 2; todos orientativos, Turmas do STJ): REsp 1.583.973 (marco na oposição inequívoca); AREsp 3.121.778/SP (marco na notificação extrajudicial; CC, art. 1.319; CPC, art. 240); AgInt no REsp 2.240.323 (uso exclusivo por herdeira; supressio não configurada; prescrição só após o trânsito em julgado da partilha); REsp 1.918.125 (vedação à dupla compensação); REsp 1.704.528 (IPTU e condomínio a cargo de quem usa o imóvel); REsp 2.054.388 (ação autônoma quando há dilação probatória); REsp 1.776.035, REsp 1.931.806 e REsp 1.707.014 (dever legal de prestar contas; apenso; ação autônoma; rito dos arts. 552 e 553); REsp 1.655.720 (retenção de aluguéis pela inventariante meeira); AgInt no AREsp 1.576.301 (cobrança de aluguéis de herdeiro por uso exclusivo).

Protocolo antifabricação: cotação PTAX, código de série do SGS, alíquota ou regra portuguesa, norma da RFB sobre espólio, prazo prescricional entre coerdeiros e qualquer Tema, Súmula ou precedente fora da lista acima exigem verificação em fonte oficial (bcb.gov.br, stj.jus.br, planalto.gov.br, gov.br/receitafederal, portaldasfinancas.gov.pt). Fora da lista, citar somente com `[A VERIFICAR]` ao lado e levar o item à seção "Pendências de verificação" do laudo. Marco inicial, fração do ocupante, critério PTAX e segregação de conta mista são premissas declaradas, não normas. Citação inventada em laudo de prestação de contas é dano processual e motivo de impugnação.

Pendências de verificação desta versão: código da série PTAX euro no SGS do BCB; regras portuguesas de IMI, IRS de não residente e Imposto do Selo; Regulamento (UE) 650/2012; tema repetitivo ou IAC do STJ sobre aluguel entre coerdeiros; prazo prescricional da pretensão de aluguéis entre coerdeiros; precedentes sobre partilha de bens no exterior; enunciados do CJF sobre os arts. 1.319, 1.028 e 2.020; RIR e IN RFB sobre declaração de espólio; lei estadual do ITCMD. Lista completa em `references/fundamentacao-legal.md`, seção 9.

## Referências

| Arquivo | Conteúdo | Quando carregar |
|---|---|---|
| `references/fundamentacao-legal.md` | Normas com dispositivo, onze precedentes verificados com links, pendências, ônus da prova, prescrição, limites do perito, roteiro de quesitos | Etapas 0 e 6 e resposta a quesitos |
| `references/roteiro-auditoria-e-documentos.md` | Perímetro, documentos no Brasil e em Portugal, transcrição do CSV, conta mista, testes por categoria, amostragem, redação de achados, limitações | Etapas 0, 1 e 3 |
| `references/imoveis-empresas-e-exterior.md` | Herdeiro ocupante (marcos, encargos, dupla compensação, prescrição), imóvel locado e vago, Portugal e PTAX, sociedades fechadas, sinais de retirada disfarçada, consolidação sem dupla contagem | Etapas 2, 4, 5 e 6 |
| `assets/template_laudo.md` | Template do laudo e do parecer com exemplo preenchido | Etapa 6 |
| `assets/exemplo_*.csv` | Entradas fictícias dos três scripts e layout do quadro de sociedades | Etapas 2 a 5 |

## Extensão e manutenção

1. Nova categoria de movimento (por exemplo, `precatorio` ou `seguro_vida`): adicionar o nome em `CATEGORIAS_ENTRADA` ou `CATEGORIAS_SAIDA` de `scripts/fluxo_caixa_espolio.py`, decidir se entra em `CATEGORIAS_CONSERVACAO` ou `CATEGORIAS_ALVARA_OBRIGATORIO`, e acrescentar a linha de teste em `references/roteiro-auditoria-e-documentos.md`, seção 6.
2. Nova situação de imóvel (por exemplo, comodato a terceiro): adicionar em `SITUACOES` e no bloco de base do esperado em `processar_imovel()` de `scripts/rendimentos_imoveis.py`, com a natureza declarada no JSON.
3. Nova moeda (dólar, libra): o script de conversão já aceita `--moeda`; basta a série PTAX correspondente por arquivo com fonte; rodar uma vez por moeda.
4. Nova tese ou precedente: só entra em `references/fundamentacao-legal.md`, seção 2, após verificação em fonte oficial; até lá fica na seção 3 com `[A VERIFICAR]`.
5. Versionamento SemVer no frontmatter e no `CHANGELOG.md`: nova categoria, nova situação ou novo parâmetro é `minor`; mudança nas colunas obrigatórias dos CSV ou nas chaves do JSON de saída, que quebra o encadeamento entre scripts, é `major`.

Manutenção desta skill: acionar `chelfo-skill-forge`.
