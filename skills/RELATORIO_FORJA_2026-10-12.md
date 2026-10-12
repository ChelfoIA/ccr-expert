# Relatório de forja: oito skills periciais

Chelfo Skill Forge, modo CRIAR (sete skills) e modo FORJAR (apuracao-haveres v2.0.0). Data de referência normativa: 12/09/2026 (dia da conferência jurisprudencial). Rodada concluída em 12/10/2026.

## 1. Quadro geral

| Skill | Caso de origem | Radiografia | Scan | Description | Scripts |
|---|---|---|---|---|---|
| `pericia-busca-apreensao-veiculo` | 1. Busca e apreensão de veículo: abusividade de juros | 98/100 Quântico | PASS | 1019 | 3, encadeados |
| `pericia-prestacao-contas-estoque` | 2. Prestação de contas na venda de sociedade: repasse do estoque líquido de impostos | 98/100 Quântico | PASS | 1022 | 3, encadeados |
| `pericia-pasep-laudo-judicial` | 3. Três perícias de PASEP (perito do juízo, lote) | 98/100 Quântico | PASS | 1009 | 3 |
| `pericia-prestacao-contas-covid-saude` | 4. Prestação de contas da verba de saúde na covid (primeira nomeação) | 98/100 Quântico | PASS | 1018 | 3 |
| `pericia-irpf-rendimentos-nao-declarados` | 5. IRPF: prova da origem e natureza de rendimentos não declarados | 98/100 Quântico | PASS | 1012 | 3, encadeados |
| `auditoria-contabil-espolio` | 6. Auditoria em inventário: caixa, imóveis, herdeiro ocupante, Portugal, empresas fechadas | 98/100 Quântico | PASS | 1019 | 3 |
| `apuracao-haveres` (v2.0.0) | 7. Apuração de haveres (forja da skill existente) | 70 (Ouro) para 98 (Quântico) | PASS | 1022 | 3, encadeados |
| `pericia-previdenciaria-beneficio-pre-cf88` | 8. Benefício de 1987: contribuição sobre 20 salários mínimos e renda de 4 | 98/100 Quântico | PASS | 1023 | 3, encadeados |

Em todas as oito, a única dimensão abaixo de 10 é D7 (eficiência de contexto), porque o SKILL.md fica entre 216 e 234 linhas (cerca de 5.700 a 7.200 tokens estimados) e o script da radiografia só bonifica corpo abaixo de 4.000 tokens. A faixa adotada segue as convenções da rodada (220 a 350 linhas), que priorizam densidade de domínio sobre brevidade.

## 2. Método

1. Conferência jurisprudencial prévia no JusRatio (12/09/2026), por domínio, com registro da identificação completa (tribunal, classe, número, órgão, relator, datas, link) em um brief por skill. O que não retornou na consulta ficou obrigatoriamente marcado `[A VERIFICAR]`.
2. Documento de convenções único (estrutura canônica, PT-BR com acentuação, zero travessão, Decimal com ROUND_HALF_UP, argparse, try/except, main guard, description de até 1024 caracteres com sete ou mais casos de uso, gatilhos e cláusula de diferenciação, dados fictícios reconhecíveis, nada de índice ou tabela embutidos).
3. Um forjador por skill, com inventário do material parcial de uma rodada interrompida, construção, execução de todos os scripts com os exemplos de `assets/`, verificador de travessão, radiografia, scan de segurança e contagem da description.
4. Conferência independente do orquestrador em cada entrega: reexecução dos scripts encadeados, travessão, description, radiografia, scan, extração de todas as citações (Tema, Súmula, REsp, AREsp, RE, AC) e confronto com a lista verificada do brief, ausência de README e de `__pycache__`.
5. Gate de QA final sobre o conjunto e varredura de acentuação em texto visível (prosa de `.md`, comentários, docstrings e mensagens de `.py`, valores textuais de `.json` e `.csv`): nenhuma ocorrência em texto visível; as dezessete restantes são identificadores de código (valores de enum e variáveis em ASCII, por convenção).

## 3. O que cada skill entrega

### pericia-busca-apreensao-veiculo
Evolução da dívida em três cenários (contratual, taxa média BACEN, juros simples pelo MEJS), teste de abusividade contra a taxa média com limiar declarado como premissa, teste do duodécuplo, purga da mora pela integralidade (Tema 722), constituição em mora pela notificação no endereço contratual (Tema 1.132), sinal técnico de descaracterização da mora por encargo abusivo no período de normalidade (REsp 1.061.530 e acórdãos de 2025 e 2026 da Terceira e da Quarta Turma). Scripts: `evolucao_cdc_veiculo.py`, `abusividade_juros.py`, `purga_mora.py`.

### pericia-prestacao-contas-estoque
Motor PEPS que atribui cada venda ao estoque transferido ou às compras novas, tributos sobre a receita por regime (Simples por arquivo; Presumido com cenário base e amplo; Real por parâmetros), conciliação dos repasses com três cenários (base, estrito, amplo), saldo em forma mercantil (CPC 551 e 552) e parcelas para a `atualizacao-monetaria`. Scripts: `peps_estoque_transferido.py`, `tributos_sobre_receita.py`, `conciliacao_repasses.py`.

### pericia-pasep-laudo-judicial
Papel do perito do juízo (laudo, imparcialidade, CPC 464 a 480) em lote de processos: registro e painel de prazos, checklist documental por modalidade de saída (Tema 1.300), termo de diligência e ofícios, matriz de quesitos que devolve ao juízo as questões de direito (prescrição, polo passivo, ônus) e laudo em cenários por tese. O cálculo continua no motor da `pericia-pasep`, cuja jurisprudência auditada foi reutilizada sem acréscimo. Scripts: `lote_pasep.py`, `checklist_documental_pasep.py`, `matriz_quesitos.py`.

### pericia-prestacao-contas-covid-saude
Fase zero tratada como etapa técnica (plano de trabalho, termo de diligência, ofícios, controle de prazo, petições quando as partes atrasam), conciliação recebido x empenhado, liquidado e pago por fonte de recursos e por mês (Lei 4.320/1964), matriz de testes por despesa com seis classes (desvio de finalidade, sem comprovação, sobrepreço a apurar, aderência a esclarecer, irregularidade formal, regular), fracionamento, fornecedor novo ou sancionado, amostragem e quantificação por classe. Scripts: `checklist_documental_covid.py`, `conciliacao_fonte_recurso.py`, `matriz_despesas_covid.py`.

### pericia-irpf-rendimentos-nao-declarados
Classificação crédito a crédito da natureza e da prova da origem (art. 42 da Lei 9.430/1996; STF Tema 842), exclusões do § 3º, recálculo do imposto nos modos anual e mensal com tabela e deduções por arquivo, IRRF, multa de ofício, juros Selic por série informada, decadência e confronto com o auto de infração. Scripts: `classificar_rendimentos.py`, `recalculo_irpf.py`, `encargos_auto_infracao.py`.

### auditoria-contabil-espolio
Fluxo de caixa do espólio com exceções (sem alvará, sem documento, retiradas de herdeiro e inventariante, despesa pessoal, encargos do imóvel ocupado), rendimentos esperados x recebidos por imóvel, aluguel devido pelo herdeiro ocupante com marco inicial parametrizado (CC 1.319 e 2.020; REsp 1.583.973, AREsp 3.121.778, AgInt no REsp 2.240.323, REsp 1.918.125, REsp 1.704.528), bens em Portugal com conversão PTAX por arquivo e quadro por sociedade fechada. Scripts: `fluxo_caixa_espolio.py`, `rendimentos_imoveis.py`, `conversao_ptax.py`.

### apuracao-haveres v2.0.0
Correções de mérito em relação à v1: data da resolução por hipótese (CPC 605, inclusive o sexagésimo dia na retirada imotivada), hierarquia contrato social x balanço de determinação a preço de saída (CPC 604 e 606), fundo de comércio mensurado como intangível na data da resolução com recusa expressa do fluxo de caixa descontado (REsp 1.335.619, 1.877.331, 1.904.252, 1.892.139, 2.174.631, 1.900.838 e acórdãos de 2025 e 2026), lucros e JCP declarados até a data (CPC 608) com prescrição trienal, pagamento em 90 dias (CC 1.031, § 2º) e juros só depois, parcelas para a `atualizacao-monetaria`. Nove precedentes da v1 não conferidos saíram do corpo e foram para as pendências. O comparativo completo está em `apuracao-haveres/RELATORIO_FORJA.md`.

| Dimensão | v1 | v2 | Delta |
|---|---|---|---|
| D1 Arquitetura estrutural | 9 | 10 | +1 |
| D2 Precisão do gatilho | 6 | 10 | +4 |
| D3 Qualidade das instruções | 7 | 10 | +3 |
| D4 Cobertura de domínio | 9 | 10 | +1 |
| D5 Assets computacionais | 6 | 10 | +4 |
| D6 Especificação de output | 3 | 10 | +7 |
| D7 Eficiência de contexto | 10 | 8 | -2 |
| D8 Integração sistêmica | 4 | 10 | +6 |
| D9 Segurança e robustez | 8 | 10 | +2 |
| D10 Manutenibilidade | 8 | 10 | +2 |
| Total | 70 (Ouro) | 98 (Quântico) | +28 |

### pericia-previdenciaria-beneficio-pre-cf88
RMI pelas regras da CLPS (36 salários de contribuição, correção dos 24 anteriores por coeficientes informados, menor e maior valor-teto, fração do excedente parametrizada e marcada para conferência), readequação aos tetos das EC 20/1998 e 41/2003 pela tese literal do Tema 1.140 do STJ com o teste "benefício não limitado na concessão implica diferença zero" demonstrado em segundo exemplo, art. 58 do ADCT (Súmula 25 da TNU), diferenças mensais em cinco padrões monetários, prescrição quinquenal, conversão em pensão por morte, óbito da pensionista, habilitação de sucessores e parcelas para a `atualizacao-monetaria` (regime da Fazenda Pública). Scripts: `rmi_clps84.py`, `readequacao_tetos.py`, `atrasados_prescricao.py`.

## 4. Antifabricação e pendências

Toda jurisprudência citada sem marcador em qualquer arquivo das oito skills consta da lista verificada do respectivo brief (ou, no caso do PASEP, do arquivo já auditado da `pericia-pasep`). Cada skill traz, em `references/fundamentacao-legal.md`, uma seção "Pendências de verificação" com os itens `[A VERIFICAR]`, que são de três tipos:

- Precedentes que não retornaram na consulta (por exemplo: Súmulas 72, 297, 380, 472 e 541 do STJ e Temas 958 e 972 na busca e apreensão; Súmula 555 do STJ e Súmulas do CARF no IRPF; Tema 313 do STF e Súmula 260 do TFR no benefício pré-CF/88).
- Dispositivos cuja numeração exata não foi conferida (artigos da LC 141/2012 e da LC 173/2020; art. 44 da Lei 9.430/1996 após a Lei 14.689/2023; art. 23 do Decreto 89.312/1984).
- Dados sensíveis ao tempo que nunca entram por memória: tabelas progressivas, Selic, PTAX, coeficientes ORTN/OTN, salário mínimo histórico, tetos e índices de reajuste, códigos de série do SGS, portarias de repasse do Ministério da Saúde. Os CSVs de exemplo são fictícios e rotulados como tal; os scripts abortam sem arquivo com fonte.

Nenhum script acessa rede. A API do BACEN estava bloqueada no ambiente de forja; onde a opção `--online` existe, ela falha com instrução de baixar a série no SGS, sem estimar.

## 5. Instalação e convivência com a biblioteca

- Copiar cada pasta de `skills/` para a biblioteca de skills. A `apuracao-haveres` v2.0.0 substitui a v1 de mesmo nome.
- `pericia-pasep-laudo-judicial` depende da `pericia-pasep` para o cálculo (scripts `bcb_loader.py`, `conciliacao_pasep.py`, `cenarios_atualizacao.py` e `selftest.py`).
- Todas apontam `atualizacao-monetaria` para trazer valores à data-base e `chelfo-docx-brand` para o `.docx` final, sob pedido.
- Padrão de entrega de cada skill: rascunho `.md`; os arquivos de saída dos scripts são JSON, CSV e Markdown.

## 6. Próximos passos recomendados

1. Rodar o modo TESTAR da forja sobre os `evals/evals.json` de cada skill com casos reais anonimizados da perita, para calibrar as expectations.
2. Conferir as pendências `[A VERIFICAR]` de maior impacto antes do primeiro laudo de cada domínio: Temas 958 e 972 (busca e apreensão), art. 23 da CLPS/84 e Tema 313 (pré-CF/88), art. 44 da Lei 9.430/1996 (IRPF), portarias de repasse (covid).
3. Quando a rede ao BACEN estiver disponível, acrescentar a função `--online` real nos scripts que leem PTAX e taxa média, reaproveitando o `bcb_loader.py` da `pericia-pasep`.
