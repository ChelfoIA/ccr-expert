# Relatório de forja: apuracao-haveres v1 para v2.0.0

Data de referência: 12/09/2026. Modo: FORJAR (reconstrução de skill existente preservando nome e essência). Ferramenta: chelfo-skill-forge (radiografia.py e scan_seguranca.py). Origem da v1: `/root/.claude/skills/synced/.../apuracao-haveres/`, copiada para `scratchpad/forge/apuracao-haveres-v1/` para o comparativo. Destino da v2: `/home/user/ccr-expert/skills/apuracao-haveres/`.

## Sumário

1. Quadro de radiografia antes (v1)
2. Diagnóstico
3. Intervenções
4. Execução dos scripts com os exemplos de assets
5. Quadro de radiografia depois (v2)
6. Comparativo gerado pela ferramenta
7. Gates de entrega
8. Pendências de verificação
9. Premissas assumidas

---

## 1. Quadro de radiografia antes (v1)

Saída de `radiografia.py scratchpad/forge/apuracao-haveres-v1` (o travessão do cabeçalho da ferramenta foi substituído por dois-pontos, por exigência do gate de tipografia):

```
=================================================================
  CHELFO SKILL FORGE : RADIOGRAFIA
=================================================================
  Skill: apuracao-haveres
  Path:  /tmp/claude-0/-home-user-ccr-expert/53e3e93e-5743-5c48-a9a4-00c33dd17083/scratchpad/forge/apuracao-haveres-v1

── D1_arquitetura ──
  total_linhas: 149
  acima_500: False
  tem_frontmatter: True
  tem_name: True
  tem_description: True
  tem_scripts: True
  tem_references: True
  tem_assets: False
  num_scripts: 3
  num_references: 3
  num_assets: 0
  num_headers: 15
  profundidade_max: 3

── D2_gatilho ──
  comprimento: 424
  num_casos_uso: 6
  tem_usar_quando: True
  tem_palavras_chave: False
  tem_diferenciacao: False
  tem_verbos_acao: True

── D3_instrucoes ──
  tem_imperativos: True
  tem_exemplos: False
  tem_workflow: True
  tem_explicacao_porque: False
  uso_caps_excessivo: 0

── D4_dominio ──
  tem_fundamentacao_legal: True
  tem_jurisprudencia: True
  tem_normas_tecnicas: True
  num_referencias_externas: 1

── D5_scripts ──
  num_scripts: 3
  com_argparse: 0
  com_docstring: 3
  com_try_except: 1
  com_main_guard: 3

── D6_output ──
  tem_template_output: False
  tem_secoes_obrigatorias: False
  tem_exemplo_output: False

── D7_eficiencia ──
  chars_skill_md: 4919
  tokens_estimados: 1229
  headers_duplicados: []
  blocos_codigo_grandes: 0
  referencia_a_references: True

── D8_integracao ──
  menciona_bash: False
  menciona_view: False
  menciona_create_file: False
  menciona_web_search: False
  menciona_outras_skills: False
  menciona_python: False

── D9_seguranca ──
  scripts_com_validacao: 1
  scripts_total: 3
  sem_conteudo_nocivo: True
  tem_failsafe: False
  sem_dados_sensiveis: True

── D10_manutenibilidade ──
  tem_versionamento: False
  modular: True
  naming_consistente: True
  extensivel: False
  scripts_comentados: 3
  tem_referencias_datadas: False

╔══════════════════════════════════╦════════╗
║ DIMENSÃO                        ║ SCORE  ║
╠══════════════════════════════════╬════════╣
║ Arquitetura Estrutural           ║    9/10 ║
║ Precisão do Gatilho              ║    6/10 ║
║ Qualidade das Instruções         ║    7/10 ║
║ Cobertura de Domínio             ║    9/10 ║
║ Assets Computacionais            ║    6/10 ║
║ Especificação de Output          ║    3/10 ║
║ Eficiência de Contexto           ║   10/10 ║
║ Integração Sistêmica             ║    4/10 ║
║ Segurança e Robustez             ║    8/10 ║
║ Manutenibilidade                 ║    8/10 ║
╠══════════════════════════════════╬════════╣
║ TOTAL                           ║  70/100 ║
║ NÍVEL: Ouro                     ║        ║
╚══════════════════════════════════╩════════╝

SUGESTOES:
  > Adicionar lista de palavras-chave na description
  > Diferenciar de skills adjacentes na description
  > Sem exemplos concretos : adicionar pelo menos 2 (input → output)
  > Sem template de output definido : adicionar estrutura do documento/relatório de saída

=================================================================
```

Resumo: 70/100, nível Ouro. Pontos fracos medidos: gatilho sem palavras-chave e sem diferenciação (D2 6/10), scripts sem argparse e sem validação (D5 6/10), nenhum template nem exemplo de output (D6 3/10), nenhuma integração sistêmica (D8 4/10), sem assets, sem versionamento.

---

## 2. Diagnóstico

### 2.1 Gaps críticos (mérito jurídico e técnico)

1. Data da resolução errada na retirada: a v1 fixava a data-base no "recebimento da notificação pela sociedade". O CPC, art. 605, II, fixa o sexagésimo dia seguinte ao recebimento na retirada imotivada; o dia do recebimento vale só para o recesso (inciso III). A v1 também tratava a exclusão judicial como "data da citação ou decisão", quando o inciso IV fixa o trânsito em julgado, e omitia a exclusão extrajudicial (inciso V).
2. Fluxo de caixa descontado apresentado como "método aceito" de goodwill, com script que o calculava (`calculo_goodwill.py`) e precedente não verificado (REsp 1.286.708) afirmando que o DCF pode ser usado. A orientação verificada das duas Turmas do STJ (2015 a 2026) é a oposta: o DCF é inadequado porque projeta lucros futuros; o fundo de comércio entra como intangível no balanço de determinação (CPC, art. 606).
3. Atualização: "juros 1% a.m. (legal)" e "termo inicial: data-base", com cálculo de juros simples embutido no script. Hoje a mora civil segue a taxa legal do CC, art. 406 (Lei 14.905/2024); o CPC, art. 608, parágrafo único, limita o ex-sócio a correção e juros após a resolução; o CC, art. 1.031, § 2º, dá 90 dias da liquidação para o pagamento.
4. Lucros até a data: a v1 ignorava o CPC, art. 608 (lucros, JCP e remuneração declarados até a data integram os haveres) e a prescrição trienal dos lucros não distribuídos (CC, art. 206, § 3º; REsp 1.904.252).
5. Hierarquia de critérios incompleta: a v1 falava em "valor patrimonial contábil (subsidiário)" sem base; faltavam o depósito da parte incontroversa (art. 604, §§ 1º a 3º), a revisão de data e critério até o início da perícia (art. 607), a indenização compensável (art. 602) e a preferência por perito especialista em avaliação de sociedades (art. 606, parágrafo único).
6. Jurisprudência fabricada ou não verificada: `jurisprudencia_stj.md` trazia dez precedentes com trechos entre aspas sem conferência; nenhum consta da lista verificada do brief, e um deles contraria a orientação atual. A v2 retirou todos e os listou como pendência.

### 2.2 Alto impacto (estrutura e engenharia)

7. Scripts em `float`, sem `argparse`, sem JSON de entrada, sem validação, sem memória nem sanidade; `haveres_socio.py` dependia de `python-dateutil` (fora da biblioteca padrão) e trazia dados de exemplo embutidos no código.
8. Sem `assets/` (template do laudo e exemplos de entrada), sem `evals/`, sem `CHANGELOG.md`, sem frontmatter com versão, autor e data.
9. Description com seis casos, sem `Acionar ao mencionar` e sem `COMPLEMENTAR a`; nenhuma diferenciação de `valuation`, `valuation-capital-fechado`, `contrato-social` e `atualizacao-monetaria`.
10. Nenhuma integração sistêmica: sem menção a `bash`, `view`, `create_file`, `web_search` nem a skills vizinhas.

### 2.3 Refinamentos

11. Sem princípio reitor, sem workflow numerado apontando scripts e references, sem estrutura do output nem exemplos input para output, títulos em capitalização de título, travessões em todo o texto, faixas percentuais de probabilidade (">50%", "25-50%", "<25%") atribuídas ao CPC 25 sem constar da norma, e "Modelo de Conclusão" que deixava os critérios de atualização "a serem definidos pelo Juízo" sem indicar os termos legais.

---

## 3. Intervenções

### 3.1 Description

Reescrita com verbo de ação inicial ("Calcular e periciar"), domínio e contexto, sete casos enumerados, doze gatilhos (técnicos e coloquiais, como "quanto vale minha parte" e "o perito usou fluxo de caixa") e diferenciação explícita (`COMPLEMENTAR a valuation-capital-fechado`). Comprimento final: 1.022 caracteres, sem quebra de linha e sem travessão. Frontmatter com `metadata.version "2.0.0"`, autor e `updated "2026-09-12"`.

### 3.2 Corpo do SKILL.md (234 linhas)

Ordem canônica das convenções: escopo com "fora de escopo" nominal, princípio reitor (as cinco causas de quebra de laudo e como cada script as elimina por construção), workflow de oito etapas apontando scripts e references, seis seções de domínio (data da resolução e hierarquia; balanço a preço de saída; fundo de comércio como intangível; lucros até a data; haveres, pagamento, correção e juros; crítica de laudo adverso e variante de assistente), integração sistêmica (quatro ferramentas e oito skills), scripts, estrutura do output com quatorze seções e três exemplos (quadro de haveres, quesito sobre a data do art. 605, II, e quesito sobre DCF), fundamentação com núcleo verificado e dez precedentes do brief, protocolo antifabricação, referências e extensão com SemVer.

### 3.3 Scripts (Python 3.11, biblioteca padrão, Decimal, argparse, try/except, main guard)

| Script | O que faz na v2 | Diferença para a v1 |
|---|---|---|
| `scripts/balanco_determinacao.py` | Lê JSON com ativos, passivos e contingências; confere a `data_resolucao` contra o marco da hipótese do art. 605 e aborta se divergir; exige fundamento em todo ajuste; aplica o CPC 25 (provável provisiona, possível divulga, remota registra); entrega PL contábil, PL de determinação e PL tangível com sanidade por caminho independente; alertas de provisão não conciliada, contingência não provável com provisão, PL negativo e conta de lucros a pagar; saídas JSON, Markdown e CSV | v1: dataclasses em float, exemplo embutido, sem data por hipótese, sem validação |
| `scripts/fundo_comercio.py` (substitui `calculo_goodwill.py`) | Lucro médio normalizado por exercício com ajustes descritos, remuneração do capital tangível com taxa que exige `fonte`, lucro excedente, fundo de comércio por `lucro-excedente` ou `multiplo` com `fundamento`, sensibilidade (fator e taxa), nota jurídica; `--metodo dcf` é recusado com código 1 e mensagem que cita os seis precedentes do STJ; encadeia `--balanco` e confere a data | v1: calculava DCF com WACC e perpetuidade e o apresentava como goodwill |
| `scripts/haveres_socio.py` | Quota pelo PL de determinação com fundo de comércio, participação e fração integralizada; lucros e JCP declarados com prescrição trienal conferida pela data do ajuizamento (interrupção retroativa, CPC, art. 240, § 1º); remuneração como administrador; deduções (adiantamentos, levantamento da parte incontroversa, indenização compensável com fundamento obrigatório); prazo de 90 dias ou contratual com fundamento; termos de correção (data da resolução) e de juros (dia seguinte ao fim do prazo); alerta de dupla contagem; sanidade (brutos menos deduções igual a líquidos igual à soma das parcelas); `parcelas.json` no formato da `atualizacao-monetaria` com valor como número JSON exato, sem float | v1: juros simples de 1% ao mês embutidos, `python-dateutil`, sem lucros do art. 608, sem deduções |

Aproveitamento do material parcial da rodada interrompida: os três scripts já estavam reescritos nas convenções e passaram na execução; foram mantidos com quatro ajustes (emissão de `parcelas.json` sem conversão a float, rótulos acentuados no Markdown do fundo de comércio, alerta de dupla contagem dos lucros declarados e texto do termo dos juros quando há data de liquidação). Os cinco exemplos de `assets/` foram mantidos, com a inclusão da conta "Lucros a distribuir deliberados e não pagos" no balanço de exemplo para demonstrar o tratamento do art. 608 sem dupla contagem.

### 3.4 References

| Arquivo | Conteúdo | Substitui |
|---|---|---|
| `references/fundamentacao-legal.md` (202 linhas) | CC, arts. 1.026 a 1.031, 1.085, 206, § 3º, 389, 397 e 406; CPC, arts. 599 a 609 com os textos verificados dos arts. 602, 604, 605, 606, 608 e 609; prova e exibição de livros (arts. 373, 396 a 400, 420, 464 a 480); normas técnicas; dez precedentes verificados com Turma, relator, data e link; seção sobre os precedentes da v1 não conferidos; ônus; marcos temporais; limites do perito; roteiro de quesitos; protocolo antifabricação; pendências | `jurisprudencia_stj.md` |
| `references/metodo-balanco-determinacao.md` (153 linhas) | Preço de saída por classe, passivos, CPC 25, tributo diferido sobre a mais-valia como cenário, balanço reconstruído, fundo de comércio (por que o intangível entra e o DCF não; lucro excedente; múltiplo; dependência do sócio; contrato com DCF), lucros sem dupla contagem, haveres negativos e integralização, exemplo numérico encadeado, armadilhas | novo |
| `references/quesitos-e-checklist.md` (136 linhas) | Documentos por etapa e detentor, termo de diligência e recusa, diligências externas, quesitos com orientação de resposta, quesitos suplementares, checklist de pré-entrega, armadilhas | `quesitos_modelo.md` e `checklist_docs.md` |

### 3.5 Assets, evals e changelog

`assets/template_laudo.md` com quatorze seções, placeholders entre colchetes, exemplo preenchido com os dados fictícios de `assets/` e seção de pendências; cinco exemplos de entrada encadeáveis; `evals/evals.json` com cinco casos (retirada imotivada com contrato omisso; falecimento com cláusula de valor contábil e alegação de abusividade; crítica de laudo com DCF; lucros declarados há quatro anos e depósito da parte incontroversa; exclusão extrajudicial sem balancete na data); `CHANGELOG.md` v1 para v2.

---

## 4. Execução dos scripts com os exemplos de assets

Comandos executados a partir de `/home/user/ccr-expert/skills/apuracao-haveres/`, encadeando a saída de cada script no seguinte:

```
python3 scripts/balanco_determinacao.py --entrada assets/exemplo_balanco.json \
  --saida balanco.json --md balanco.md --csv balanco.csv
  -> PL contábil R$ 480.000,00 | PL de determinação R$ 490.000,00 | provisões adicionais R$ 60.000,00
     (sanidade: 1.025.000,00 - 475.000,00 - 60.000,00 = 490.000,00; PL tangível 460.000,00)

python3 scripts/fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json \
  --balanco balanco.json --metodo lucro-excedente --saida fundo.json --md fundo.md
  -> Lucro médio normalizado R$ 173.000,00 | fundo de comércio (lucro-excedente) R$ 353.400,00
     (sensibilidade: fator 2 = 235.600,00; fator 4 = 471.200,00; taxa 11% = 367.200,00; 13% = 339.600,00)

python3 scripts/fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json \
  --balanco balanco.json --metodo multiplo --saida fundo_multiplo.json
  -> fundo de comércio (multiplo) R$ 232.000,00

python3 scripts/fundo_comercio.py --entrada assets/exemplo_fundo_comercio.json --metodo dcf
  -> ERRO de validação: método 'dcf' recusado. O fluxo de caixa descontado projeta lucros futuros [...]
     Precedentes (Turmas do STJ, nenhum vinculante): REsp 1.877.331 [...] AgInt no AgInt no AREsp 2.903.904 [...]
     (código de saída 1)

python3 scripts/haveres_socio.py --balanco balanco.json --fundo-comercio fundo.json \
  --participacao 25% --data-resolucao 30/06/2025 --data-ajuizamento 15/08/2025 \
  --lucros-declarados assets/exemplo_lucros_declarados.json \
  --remuneracao-administrador assets/exemplo_remuneracao_administrador.json \
  --adiantamentos assets/exemplo_adiantamentos.json --data-liquidacao 10/03/2026 \
  --saida haveres.json --md haveres.md --parcelas parcelas.json
  -> Haveres brutos R$ 247.850,00 | deduções R$ 30.000,00 | haveres líquidos R$ 217.850,00
     (quota 210.850,00; lucros integrados 21.000,00 e 12.500,00 prescritos; remuneração 16.000,00;
      correção desde 30/06/2025; juros a partir de 09/06/2026; parcelas.json com 6 lançamentos
      somando 217.850,00, lido com sucesso por json.load)
```

Casos de erro propositais conferidos: `data_resolucao` 01/05/2025 com `hipotese retirada_imotivada` e notificação em 01/05/2025 aborta com "incompatível com CPC, art. 605, II [...] = 30/06/2025"; taxa de remuneração sem `fonte` aborta com "a taxa nunca é digitada de memória"; execução do script 3 sem `--fundo-comercio`, sem `--data-ajuizamento` e sem `--data-liquidacao` roda com três alertas explícitos.

---

## 5. Quadro de radiografia depois (v2)

Saída de `radiografia.py /home/user/ccr-expert/skills/apuracao-haveres`:

```
=================================================================
  CHELFO SKILL FORGE : RADIOGRAFIA
=================================================================
  Skill: apuracao-haveres
  Path:  /home/user/ccr-expert/skills/apuracao-haveres

── D1_arquitetura ──
  total_linhas: 235
  acima_500: False
  tem_frontmatter: True
  tem_name: True
  tem_description: True
  tem_scripts: True
  tem_references: True
  tem_assets: True
  num_scripts: 3
  num_references: 3
  num_assets: 6
  num_headers: 16
  profundidade_max: 2

── D2_gatilho ──
  comprimento: 1022
  num_casos_uso: 7
  tem_usar_quando: True
  tem_palavras_chave: True
  tem_diferenciacao: True
  tem_verbos_acao: True

── D3_instrucoes ──
  tem_imperativos: True
  tem_exemplos: True
  tem_workflow: True
  tem_explicacao_porque: True
  uso_caps_excessivo: 0

── D4_dominio ──
  tem_fundamentacao_legal: True
  tem_jurisprudencia: True
  tem_normas_tecnicas: True
  num_referencias_externas: 9

── D5_scripts ──
  num_scripts: 3
  com_argparse: 3
  com_docstring: 3
  com_try_except: 3
  com_main_guard: 3

── D6_output ──
  tem_template_output: True
  tem_secoes_obrigatorias: True
  tem_exemplo_output: True

── D7_eficiencia ──
  chars_skill_md: 29028
  tokens_estimados: 7257
  headers_duplicados: []
  blocos_codigo_grandes: 1
  referencia_a_references: True

── D8_integracao ──
  menciona_bash: True
  menciona_view: True
  menciona_create_file: True
  menciona_web_search: True
  menciona_outras_skills: True
  menciona_python: True

── D9_seguranca ──
  scripts_com_validacao: 3
  scripts_total: 3
  sem_conteudo_nocivo: True
  tem_failsafe: True
  sem_dados_sensiveis: True

── D10_manutenibilidade ──
  tem_versionamento: True
  modular: True
  naming_consistente: True
  extensivel: True
  scripts_comentados: 3
  tem_referencias_datadas: True

╔══════════════════════════════════╦════════╗
║ DIMENSÃO                        ║ SCORE  ║
╠══════════════════════════════════╬════════╣
║ Arquitetura Estrutural           ║   10/10 ║
║ Precisão do Gatilho              ║   10/10 ║
║ Qualidade das Instruções         ║   10/10 ║
║ Cobertura de Domínio             ║   10/10 ║
║ Assets Computacionais            ║   10/10 ║
║ Especificação de Output          ║   10/10 ║
║ Eficiência de Contexto           ║    8/10 ║
║ Integração Sistêmica             ║   10/10 ║
║ Segurança e Robustez             ║   10/10 ║
║ Manutenibilidade                 ║   10/10 ║
╠══════════════════════════════════╬════════╣
║ TOTAL                           ║  98/100 ║
║ NÍVEL: Quântico                 ║        ║
╚══════════════════════════════════╩════════╝

=================================================================
```

Resumo: 98/100, nível Quântico. A única dimensão abaixo de 10 é a eficiência de contexto (D7 8/10), consequência direta das convenções, que pedem corpo de 220 a 350 linhas com fundamentação, exemplos e integração: a ferramenta premia SKILL.md abaixo de 2.000 tokens, incompatível com o padrão exigido.

---

## 6. Comparativo gerado pela ferramenta

Comando pedido: `radiografia.py <v2> --compare <v1>`. A ferramenta rotula o primeiro caminho como "ANTES" e o segundo como "DEPOIS"; logo, nesta saída a coluna ANTES é a v2 e a coluna DEPOIS é a v1:

```
╔══════════════════════════╦══════════╦══════════╦═══════════╗
║ DIMENSÃO                 ║ ANTES    ║ DEPOIS   ║ DELTA     ║
╠══════════════════════════╬══════════╬══════════╬═══════════╣
║ D1                       ║    10/10 ║     9/10 ║ -1       ║
║ D2                       ║    10/10 ║     6/10 ║ -4       ║
║ D3                       ║    10/10 ║     7/10 ║ -3       ║
║ D4                       ║    10/10 ║     9/10 ║ -1       ║
║ D5                       ║    10/10 ║     6/10 ║ -4       ║
║ D6                       ║    10/10 ║     3/10 ║ -7       ║
║ D7                       ║     8/10 ║    10/10 ║ +2        ║
║ D8                       ║    10/10 ║     4/10 ║ -6       ║
║ D9                       ║    10/10 ║     8/10 ║ -2       ║
║ D10                      ║    10/10 ║     8/10 ║ -2       ║
╠══════════════════════════╬══════════╬══════════╬═══════════╣
║ TOTAL                    ║   98/100 ║   70/100 ║ -28      ║
║ NÍVEL                    ║ Quântico ║ Ouro     ║           ║
╚══════════════════════════╩══════════╩══════════╩═══════════╝
```

Mesmo comparativo com os caminhos invertidos (`radiografia.py <v1> --compare <v2>`), para leitura direta (ANTES = v1, DEPOIS = v2):

```
╔══════════════════════════╦══════════╦══════════╦═══════════╗
║ DIMENSÃO                 ║ ANTES    ║ DEPOIS   ║ DELTA     ║
╠══════════════════════════╬══════════╬══════════╬═══════════╣
║ D1                       ║     9/10 ║    10/10 ║ +1        ║
║ D2                       ║     6/10 ║    10/10 ║ +4        ║
║ D3                       ║     7/10 ║    10/10 ║ +3        ║
║ D4                       ║     9/10 ║    10/10 ║ +1        ║
║ D5                       ║     6/10 ║    10/10 ║ +4        ║
║ D6                       ║     3/10 ║    10/10 ║ +7        ║
║ D7                       ║    10/10 ║     8/10 ║ -2       ║
║ D8                       ║     4/10 ║    10/10 ║ +6        ║
║ D9                       ║     8/10 ║    10/10 ║ +2        ║
║ D10                      ║     8/10 ║    10/10 ║ +2        ║
╠══════════════════════════╬══════════╬══════════╬═══════════╣
║ TOTAL                    ║   70/100 ║   98/100 ║ +28       ║
║ NÍVEL                    ║ Ouro     ║ Quântico ║           ║
╚══════════════════════════╩══════════╩══════════╩═══════════╝
```

Ganho líquido: 28 pontos (70 para 98), de Ouro para Quântico, com avanço em nove dimensões e recuo de dois pontos apenas na eficiência de contexto.

---

## 7. Gates de entrega

| Gate | Resultado |
|---|---|
| Verificador de travessão (U+2014 e U+2013) a partir do diretório da skill | `OK sem travessão` |
| Comprimento da description | 1.022 caracteres, sem quebra de linha |
| Palavras em caixa alta no corpo (SEMPRE, NUNCA etc.) | 0 |
| Radiografia v2 | 98/100, Quântico |
| Scan de segurança (`scan_seguranca.py`) | ver abaixo |
| `__pycache__` na pasta | nenhum |
| `evals/evals.json` | JSON válido, 5 casos, 26 expectativas |
| Scripts com os exemplos de `assets/` | os três rodam, encadeiam e fecham; DCF recusado com código 1 |

```
Caminho:              /home/user/ccr-expert/skills/apuracao-haveres
Arquivos escaneados:  15
BLOQUEIA / REVISAR:   0 / 0
COMPROVADO / SUSPEITA_FUNDAMENTADA: 0 / 0
VEREDICTO:            PASS
```

Árvore final:

```
apuracao-haveres/
  SKILL.md
  CHANGELOG.md
  RELATORIO_FORJA.md
  assets/
    exemplo_adiantamentos.json
    exemplo_balanco.json
    exemplo_fundo_comercio.json
    exemplo_lucros_declarados.json
    exemplo_remuneracao_administrador.json
    template_laudo.md
  evals/
    evals.json
  references/
    fundamentacao-legal.md
    metodo-balanco-determinacao.md
    quesitos-e-checklist.md
  scripts/
    balanco_determinacao.py
    fundo_comercio.py
    haveres_socio.py
```

---

## 8. Pendências de verificação

Itens marcados `[A VERIFICAR]` nesta versão (lista consolidada em `references/fundamentacao-legal.md`, seção 12):

1. Informativo STJ 864 (REsp 2.223.719-SP, Terceira Turma, j. 02/09/2025): conteúdo não conferido.
2. Enunciados das Jornadas de Direito Comercial do CJF sobre haveres.
3. Existência de tema repetitivo do STJ sobre critério de apuração de haveres ou fundo de comércio.
4. Orientação do STJ sobre haveres negativos e eventual débito do sócio (alerta do script 3).
5. Inciso do § 3º do art. 206 do CC invocado no REsp 1.904.252 (o brief indica o inciso VI).
6. Termo inicial dos juros de mora nos haveres (citação, liquidação ou 91º dia após a liquidação).
7. Lei 6.404/1976, art. 45: redação vigente e critério de reembolso na anônima fechada.
8. Tributo diferido sobre a mais-valia dos ativos reavaliados: precedente ou doutrina.
9. Nove precedentes citados pela v1 e não conferidos (REsp 1.239.754, 907.014, 1.286.708, 1.303.284, 1.422.934, 1.557.989, 1.602.240, 1.128.431 e 1.606.366).
10. Série do SGS do Banco Central adequada à taxa de remuneração do capital em cada caso.

---

## 9. Premissas assumidas

1. Data de referência 12/09/2026 em todos os arquivos (convenções, brief e demais skills da rodada), embora a sessão de forja tenha ocorrido em 12/10/2026; a v1 não tem data registrada e o CHANGELOG diz isso.
2. Jurisprudência restrita à lista do brief; nenhuma consulta a JusRatio, web ou MCP; o que faltou entrou como `[A VERIFICAR]`.
3. Taxa de remuneração do capital de 12% e fator 3 do exemplo são fictícios e assim declarados no JSON; o script exige fonte e fundamento no caso real.
4. O balanço de exemplo recebeu a conta "Lucros a distribuir deliberados e não pagos" (R$ 90.000,00) para demonstrar o tratamento do art. 608 sem dupla contagem; os totais do exemplo mudaram em relação ao material parcial da rodada anterior (PL de determinação de 580.000,00 para 490.000,00).
5. `parcelas.json` grava o valor como número JSON exato (texto com duas casas), compatível com a leitura de `atualiza.py` da `atualizacao-monetaria`, que converte na entrada; deduções entram com sinal negativo na competência em que ocorreram.
6. Prazo de pagamento de 90 dias contado da liquidação (CC, art. 1.031, § 2º) com juros a partir do dia seguinte ao vencimento; a data da liquidação é parâmetro (`--data-liquidacao`) e, se ausente, o termo é descrito pela regra, nunca estimado.
7. Prescrição trienal contada da deliberação, com interrupção retroativa à data da propositura (CPC, art. 240, § 1º), informada por `--data-ajuizamento`; sem essa data o script alerta e não exclui.
8. O sócio "João da Silva (autor)", a "Alfa Comércio Ltda." e os números de processo, CPF e CNPJ são fictícios conforme as convenções.
