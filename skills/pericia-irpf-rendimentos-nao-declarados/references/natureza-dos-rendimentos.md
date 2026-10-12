# Natureza dos rendimentos: tratamento, fundamento, prova exigida e armadilhas

Referência: 12/09/2026. Este arquivo é a tabela de decisão de `scripts/classificar_rendimentos.py` (dicionário `NATUREZAS`) e explica como preencher o CSV dos créditos. Dispositivos marcados `[A VERIFICAR]` seguem o protocolo de `references/fundamentacao-legal.md`.

## Sumário

1. As três perguntas e os sete tratamentos
2. Tabela das naturezas
3. Regras de prova do script
4. Desdobramento de créditos e casos especiais
5. O § 2º na prática: origem comprovada e tributação própria
6. Mecânica do § 3º e do § 6º
7. Como preencher o CSV

---

## 1. As três perguntas e os sete tratamentos

Cada crédito recebe três respostas: de onde veio (prova da origem), se é renda (natureza) e se já foi tributado (DIRPF, IRRF, fonte). O cruzamento das respostas produz um dos sete tratamentos do script:

| Tratamento | Significado | Entra na base do recálculo? |
|---|---|---|
| `ajuste` | Rendimento tributável na declaração de ajuste anual | Sim, se `ja_declarado` for N; não, se já constou da DIRPF |
| `exclusivo_fonte` | Rendimento tributado exclusivamente na fonte (renda fixa, 13º, prêmios) | Não |
| `isento` | Rendimento isento ou não tributável (doação, herança, FGTS, dividendos, indenização) | Não |
| `nao_rendimento` | Crédito sem acréscimo patrimonial (mútuo, venda de bem, transferência própria, resgate de principal, estorno, restituição) | Não |
| `terceiro` | Valor que pertence a terceiro, com interposição provada (§ 5º) | Não para o titular; lançável contra o terceiro |
| `presumido_omissao` | Origem não comprovada (art. 42, caput) | Sim: no ajuste (modo anual) ou no mês do crédito (modo mensal) |
| `excluido_par3` | Crédito presumido excluído pelo § 3º, II (pequeno valor) | Não |

O tratamento natural de cada natureza só se aplica quando a prova afasta a presunção; sem prova, qualquer natureza alegada vira `presumido_omissao` no cenário correspondente.

---

## 2. Tabela das naturezas

| Natureza (`natureza_alegada`) | Tratamento | Fundamento | Prova exigida | Qualificada | Armadilhas |
|---|---|---|---|---|---|
| `salario` | ajuste | CTN, art. 43; Lei 7.713/1988, art. 3º; Lei 9.250/1995, art. 8º | Contracheque, DIRF ou informe de rendimentos conciliado ao crédito líquido | Não | IRRF compensável; conferir se já constou da DIRPF; crédito líquido difere do bruto informado em DIRF |
| `prolabore` | ajuste | CTN, art. 43; Lei 7.713/1988, art. 3º | Informe da pessoa jurídica, DIRF, folha ou contabilidade | Não | Valor sem registro contábil na empresa sugere distribuição disfarçada |
| `aluguel` | ajuste | Lei 7.713/1988, art. 3º, § 1º; carnê-leão quando o pagador é pessoa física | Contrato de locação, DIMOB da administradora, recibos, DIRF quando o locatário é pessoa jurídica | Não | Deduzir do bruto, com comprovante, encargos pagos pelo locador e comissão da administradora |
| `honorarios` | ajuste | Lei 7.713/1988, art. 3º; carnê-leão | Recibo ou nota, contrato, DIRF quando o pagador é pessoa jurídica | Não | Livro-caixa só com escrituração `[A VERIFICAR: Lei 8.134/1990, art. 6º]` |
| `dividendos` | isento | Lei 9.249/1995, art. 10; RIR/2018, art. 35 | Informe da pessoa jurídica, ata ou deliberação, ECF e contabilidade com lucro apurado | Não | Distribuição sem lucro contábil é tributável; regime a partir de 2026 `[A VERIFICAR: Lei 15.270/2025]` |
| `doacao` | isento | Lei 7.713/1988, art. 6º, XVI; RIR/2018, art. 35 | ITCMD pago, declarado ou isenção reconhecida; DIRPF do doador (ficha de doações); transferência bancária do doador | Sim | Recibo particular sem data certa (CPC, art. 409) e doador sem capacidade financeira não comprovam |
| `heranca` | isento | Lei 7.713/1988, art. 6º, XVI; RIR/2018, art. 35 | Formal de partilha, alvará ou escritura de inventário; ITCMD; DIRPF do espólio | Sim | Valor acima do quinhão declarado é acréscimo a comprovar |
| `indenizacao_trabalhista` | isento | Lei 7.713/1988, art. 6º, V (parcela indenizatória) | TRCT, sentença ou acordo homologado com discriminação das verbas, alvará | Não | Verbas remuneratórias do acordo são tributáveis `[A VERIFICAR: Lei 7.713/1988, art. 12-A]`: separar por rubrica |
| `fgts` | isento | Lei 7.713/1988, art. 6º, V | Extrato da conta vinculada com o saque; TRCT ou alvará | Não | Conferir data e valor no extrato da Caixa |
| `poupanca` | isento | Isenção da poupança `[A VERIFICAR: Lei 8.981/1995, art. 68, III]` | Extrato da poupança com o crédito de rendimento | Não | Crédito vindo da poupança própria é `transferencia_propria`, não rendimento |
| `aplicacao_financeira` | exclusivo_fonte | Tributação exclusiva de renda fixa `[A VERIFICAR: Lei 8.981/1995, art. 65]` | Informe da instituição ou nota de resgate com IRRF destacado | Não | Só o rendimento; o principal é `resgate_principal`; renda variável tem apuração mensal própria |
| `resgate_principal` | nao_rendimento | CTN, art. 43 (sem acréscimo) | Nota de resgate ou extrato da aplicação com a origem identificada; DIRPF (bens e direitos) | Não | Aplicação sem lastro declarado desloca o problema para a data da aplicação |
| `mutuo_recebido` | nao_rendimento | CC, art. 586; CPC, art. 409; Lei 9.430/1996, art. 42, § 2º | Contrato com data certa, DIRPF do mutuante e do mutuário, transferência do mutuante, capacidade financeira, devolução posterior | Sim | Contrato sem data certa, mutuante sem lastro ou sem devolução reduzem a prova a parcial |
| `venda_bem` | nao_rendimento | Preço não é renda; ganho de capital apurado em separado `[A VERIFICAR: Lei 9.250/1995, arts. 22 e 23]` | Escritura ou registro, CRLV e ATPV, contrato com data certa, DIRPF com a baixa, GCAP e DARF | Sim | Preço acima do valor declarado é acréscimo; sem DARF ou isenção, o ganho é lançável em separado |
| `transferencia_propria` | nao_rendimento | Lei 9.430/1996, art. 42, § 3º, I | Extrato da conta de origem, do mesmo titular, com débito de igual data e valor | Não | Conta conjunta ou de cônjuge não é conta própria: § 6º ou prova da titularidade do recurso |
| `pensao_alimenticia` | isento | Não incidência `[A VERIFICAR: STF, ADI 5.422 e eficácia]` | Decisão judicial ou escritura pública e comprovante do alimentante | Não | Antes da decisão do STF o valor era tributável: verificar a data do crédito |
| `seguro` | isento | Lei 7.713/1988, art. 6º (capital de apólice e indenização) | Apólice, aviso de sinistro, comprovante da seguradora | Não | Indenização que excede o dano pode ser tributável |
| `restituicao_ir` | nao_rendimento | CTN, art. 165 | Consulta de restituição da RFB (lote e valor); DIRPF do exercício | Não | Conferir se o crédito coincide com o lote |
| `estorno` | nao_rendimento | CTN, art. 43 (sem acréscimo) | Lançamento de débito correspondente no mesmo extrato, anterior ao crédito | Não | Estorno sem débito prévio identificado é crédito sem origem |
| `terceiro` | terceiro | Lei 9.430/1996, art. 42, §§ 5º e 6º | Mandato ou procuração, DIRPF do terceiro com o rendimento, extratos do terceiro, contrato que explique a passagem | Sim | O § 5º exige prova, não alegação; o efeito é o lançamento contra o terceiro |
| `sem_prova` | presumido_omissao | Lei 9.430/1996, art. 42, caput e § 4º | Nenhuma | Não | Candidato ao § 3º, II, quando de pequeno valor |

---

## 3. Regras de prova do script

O script não "acredita" em documento: concilia. Os critérios, todos declarados na memória de cálculo e ajustáveis por linha de comando:

| Critério | Regra padrão | Parâmetro | Motivo registrado quando falha |
|---|---|---|---|
| Data | Documento datado a até 10 dias do crédito | `--tolerancia-dias` | "data do documento fora da tolerância" |
| Valor | Valor do documento igual ao do crédito, com tolerância de 0,5% (mínimo R$ 1,00) | `--tolerancia-valor` | "valor do documento não coincide" |
| Contraparte | Depositante ou fonte pagadora identificada no documento (`doc_terceiro_identificado` = S); na transferência própria, a conta de origem do titular | nenhum | "contraparte não identificada" |
| Prova qualificada | Data certa, registro público, ITCMD ou decisão judicial, quando a natureza exige (`doc_qualificado` = S) | nenhum | "natureza exige prova qualificada não apresentada" |

Níveis: `suficiente` (todos os critérios atendidos), `parcial` (documento existe, mas falha em ao menos um critério), `ausente` (sem documento ou natureza `sem_prova`). Cenário base: só `suficiente` afasta a presunção. Cenário ampliado: `parcial` também afasta. A diferença entre os cenários mede quanto do lançamento depende de cada decisão probatória do juízo, e é o número que mais interessa ao laudo.

Por que a data certa importa: declaração particular de doação ou de mútuo assinada depois da intimação fiscal prova apenas que as partes afirmam hoje o que afirmam; em relação à Fazenda (terceiro), o documento particular se considera datado do registro, da apresentação em repartição pública ou de outro evento do art. 409 do CPC. Sem isso, a prova fica parcial, e o laudo diz exatamente o que falta.

---

## 4. Desdobramento de créditos e casos especiais

| Situação | Como lançar no CSV | Efeito |
|---|---|---|
| Resgate de aplicação (principal mais rendimento) | Duas linhas (`10a` `resgate_principal`, `10b` `aplicacao_financeira`) com os valores da nota de resgate | Principal sai como não rendimento; rendimento como exclusivo na fonte |
| Acordo trabalhista com verbas mistas | Uma linha por rubrica (indenizatória `indenizacao_trabalhista`; remuneratória `salario` com `ja_declarado` conforme o caso) | Só a parte indenizatória é isenta |
| Cheque devolvido creditado e estornado | Linha `estorno` com `doc_data` do débito de devolução | Não há disponibilidade (TRF2, AC 5019756-46.2020.4.02.5001, trata do tema) |
| Transferência da poupança do próprio titular | `transferencia_propria`, `transferencia_propria` = S, `doc_terceiro_identificado` = S (conta de origem identificada) | § 3º, I |
| Transferência de conta conjunta ou do cônjuge | Não é `transferencia_propria`; usar a natureza do recurso original (ex.: `salario` do cônjuge como `terceiro`) ou `--conta-conjunta` | § 6º ou § 5º |
| PIX de terceiro com "declaração" posterior | Natureza alegada (`mutuo_recebido`, `doacao`, `terceiro`) com `doc_qualificado` = N | Prova parcial; o laudo descreve a lacuna |
| Operações com criptoativos | `venda_bem` (alienação) ou `resgate_principal` (saque da corretora), com extrato da corretora e DIRPF | Ganho de capital apurado em separado |
| Rendimento já declarado | `ja_declarado` = S | Fica fora da base adicional, mas compõe o quadro |
| Depósito em dinheiro sem documento | `sem_prova` | Presumido; candidato ao § 3º, II |

---

## 5. O § 2º na prática: origem comprovada e tributação própria

| Origem comprovada | Já tributada? | Consequência no recálculo |
|---|---|---|
| Aluguel informado em DIMOB, ausente da DIRPF | Não | Sai da presunção e entra no ajuste anual como `ajuste` não declarado; IRRF da locatária compensável |
| Honorários de pessoa física sem carnê-leão | Não | Ajuste anual; o carnê-leão não recolhido não é multa de ofício por omissão presumida, mas falta de recolhimento mensal `[A VERIFICAR percentual de multa aplicável]` |
| Rendimento de CDB com IRRF destacado | Sim, exclusivamente | Não entra na base; o auto que o inclui tributa duas vezes |
| Lucros distribuídos com lucro contábil apurado | Isentos | Não entram; sem lucro apurado, viram `ajuste` |
| Principal de aplicação declarada em 31/12 anterior | Não é renda | Não entra; se a aplicação não constava da DIRPF, o problema é o ano da aplicação |
| Preço de venda de veículo com baixa na DIRPF | Não é renda | Não entra; ganho de capital, se houver, apurado em separado |

Erro frequente do contribuinte: provar a origem e parar. Erro frequente da Fazenda: aceitar a origem e manter a presunção. O laudo evita os dois ao responder as três perguntas para cada crédito.

---

## 6. Mecânica do § 3º e do § 6º

Inciso I (transferência própria): a exclusão exige o extrato da conta de origem, do mesmo titular, com débito de igual data e valor. Transferência "da conta da empresa" ou "da conta do marido" não é própria.

Inciso II (pequeno valor, pessoa física): por ano-calendário e por cenário, o script separa os créditos que permaneceram presumidos com valor individual até R$ 12.000,00, soma e compara com R$ 80.000,00. Se a soma cabe, todos saem (`excluido_par3`); se excede, nenhum sai. A regra é por ano, não por conta. Os limites são da Lei 9.481/1997, art. 4º, e podem ser sobrepostos por `--limite-individual` e `--limite-anual`, com registro na memória. O auto que ignora o inciso II é a divergência mais comum em laudo.

Parágrafo 6º (conta conjunta): `--conta-conjunta "CONTA=N"` divide por N o presumido dos créditos dessa conta, só quando as declarações dos titulares foram apresentadas em separado e não há prova da origem. Rendimento de fonte identificada não se divide.

---

## 7. Como preencher o CSV

| Coluna | Conteúdo | Exemplo |
|---|---|---|
| `id` | Identificador único; sufixos `a`, `b` para desdobramento | `10a` |
| `data` | Data do crédito no extrato, dd/mm/aaaa | `02/06/2023` |
| `valor` | Valor do crédito, padrão brasileiro ou técnico | `12.000,00` |
| `conta` | Identificação da conta (usada no § 6º) | `CC 0001-1 Banco Alfa` |
| `historico` | Histórico do extrato, transcrito | `TED Ana da Silva` |
| `origem_alegada` | O que o contribuinte alega | `doação da mãe` |
| `natureza_alegada` | Código da seção 2 | `doacao` |
| `documento` | Documento apresentado, com folha dos autos; vazio se não há | `declaração particular fl. 70` |
| `doc_data` | Data do documento ou do fato que ele prova | `03/04/2023` |
| `doc_valor` | Valor constante do documento | `300.000,00` |
| `doc_terceiro_identificado` | S se o documento identifica a contraparte (ou a conta de origem própria) | `S` |
| `transferencia_propria` | S se o crédito veio de conta do próprio titular | `N` |
| `ja_declarado` (opcional) | S se o rendimento já constou da DIRPF | `N` |
| `doc_qualificado` (opcional) | S se há data certa, registro, ITCMD ou decisão | `N` |

Exemplo completo em `assets/exemplo_rendimentos.csv`.
