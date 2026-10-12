# Óbito do autor, pensão derivada, sucessão processual, prescrição e decadência

Referência: 12/09/2026. Casos antigos atravessam décadas de tramitação: o segurado morre, a viúva se habilita, a viúva morre, e o processo chega à perícia com três gerações de interessados. Este arquivo organiza o que o perito precisa documentar e calcular em cada passagem, sem decidir o que é do juízo.

## Sumário

1. Óbito do autor: suspensão, sucessão e habilitação
2. Quem recebe o que o segurado não recebeu em vida (art. 112)
3. Pensão derivada da renda revisada: coeficiente por data do óbito
4. Óbito da pensionista
5. Prescrição quinquenal
6. Decadência
7. Abono anual nas diferenças
8. Quesitos sobre sucessão e prescrição
9. Pendências de verificação

---

## 1. Óbito do autor: suspensão, sucessão e habilitação

| Passo | Dispositivo | O que o perito confere nos autos |
|---|---|---|
| Suspensão do processo pela morte | CPC/2015, art. 313, I | Data do óbito (certidão), data da comunicação ao juízo |
| Sucessão pelo espólio ou sucessores | CPC/2015, art. 110 | Decisão que admitiu a sucessão |
| Habilitação | CPC/2015, arts. 687 a 692 | Petição de habilitação, documentos de dependência ou sucessão, citação dos interessados, decisão |
| Legitimidade para o crédito previdenciário | Lei 8.213/1991, art. 112 | Quem foi habilitado: dependentes da pensão ou sucessores civis |

O perito não decide a habilitação; descreve quem está habilitado, por que título (dependente habilitado à pensão ou sucessor civil) e a partir de qual decisão, e atribui a cada bloco de parcelas o destinatário correspondente. Na falta de habilitação, calcula os blocos e registra a pendência.

---

## 2. Quem recebe o que o segurado não recebeu em vida (art. 112)

O art. 112 da Lei 8.213/1991 manda pagar o valor não recebido em vida pelo segurado aos dependentes habilitados à pensão por morte ou, na falta deles, aos sucessores na forma da lei civil, independentemente de inventário ou arrolamento. Consequências para o cálculo:

- Bloco do titular (DIB ou primeira competência devida até o mês do óbito, inclusive): destinatário é a pensionista habilitada (viúva) enquanto viva; falecida a viúva, os sucessores dela quanto ao que ela não recebeu `[A VERIFICAR alcance do art. 112 à pensionista]`, ou os demais dependentes.
- O mês do óbito fica com o titular (a prestação do mês é devida por inteiro aos dependentes como resíduo); a pensão começa no mês seguinte. Premissa declarada no script; se o juízo fixar o pro rata, ajustar.
- Havendo outros dependentes (filhos menores na época do óbito), a cota da pensão se rateia (Lei 8.213/1991, art. 77) e reverte aos remanescentes quando cessa o direito de um; o script calcula a pensão total e o rateio é apresentado no laudo com os documentos de dependência.

---

## 3. Pensão derivada da renda revisada: coeficiente por data do óbito

A pensão é percentual da aposentadoria que o segurado recebia ou daquela a que teria direito na data do óbito (Lei 8.213/1991, art. 75). Revisada a aposentadoria, a pensão se revisa na mesma proporção. O percentual depende do regime vigente na data do óbito, e o script o recebe por `--coeficiente-pensao` com `--fundamento-pensao`:

| Data do óbito | Regime | Coeficiente | Marcador |
|---|---|---|---|
| Antes de 24/07/1991 | CLPS, Decreto 89.312/1984 | Cota familiar mais cotas por dependente, até 100% | `[A VERIFICAR dispositivo e percentuais]` |
| De 24/07/1991 até a Lei 9.032/1995 | Lei 8.213/1991, art. 75, redação original | Cota familiar mais cotas por dependente, até 100% | `[A VERIFICAR percentuais]` |
| Da Lei 9.032/1995 até 13/11/2019 | Lei 8.213/1991, art. 75, redação da Lei 9.032/1995 e da Lei 9.528/1997 | 100% | `[A VERIFICAR dispositivo e vigência]` |
| A partir de 14/11/2019 | EC 103/2019, art. 23 | 50% mais 10 pontos por dependente, até 100%; 100% com dependente inválido | `[A VERIFICAR percentuais e regras]` |

Diferença da pensão em cada competência: coeficiente vezes a renda devida revisada menos a pensão efetivamente paga (`--pago-pensao`, HISCRE da pensão) ou, na falta, o coeficiente sobre a renda paga ao titular (presunção declarada). Se a pensão paga já embutir alguma revisão, a diferença cai e o script registra a origem informada.

---

## 4. Óbito da pensionista

A cota individual da pensão cessa pela morte do pensionista (Decreto 3.048/1999, art. 114, I). No script, `--obito-pensionista` encerra o bloco da pensão no mês do óbito. As parcelas da pensão vencidas e não pagas até o óbito destinam-se aos sucessores da pensionista (nova habilitação, CPC, arts. 687 a 692), por aplicação do art. 112 `[A VERIFICAR alcance]`. Se havia outros pensionistas, a cota reverte a eles (art. 77) e o bloco continua para eles; o perito separa os blocos por beneficiário quando os autos permitirem.

Documentos: certidão de óbito da pensionista, certidão de dependentes ou de inexistência, decisão de habilitação dos sucessores, extrato de pagamento da pensão com a data de cessação.

---

## 5. Prescrição quinquenal

Regra: prescrevem em cinco anos, contados da data em que deveriam ter sido pagas, as prestações vencidas e diferenças devidas pela Previdência, ressalvados menores, incapazes e ausentes (Lei 8.213/1991, art. 103, parágrafo único). Em relação de trato sucessivo a prescrição atinge só as parcelas anteriores ao quinquênio, não o fundo de direito (orientação atribuída à Súmula 85 do STJ `[A VERIFICAR]`). A Corte Especial do TRF1 (AC 1018697-75.2023.4.01.3300) aplica a prescrição quinquenal à revisão de benefício anterior à CF/88.

No script:

| Parâmetro | Efeito |
|---|---|
| `--ajuizamento dd/mm/aaaa` | Marco igual ao ajuizamento menos cinco anos |
| `--criterio-prescricao competencia` (padrão) | Prescrita a parcela cuja competência é anterior ao mês do marco |
| `--criterio-prescricao pagamento` | Considera a parcela paga no mês seguinte à competência; prescrita se esse mês é anterior ao mês do marco |
| `--marco-prescricao dd/mm/aaaa` com `--fundamento-prescricao` | Substitui o ajuizamento (por exemplo, requerimento administrativo de revisão que interrompe ou suspende o prazo, Decreto 20.910/1932 `[A VERIFICAR aplicabilidade]`) |
| `--sem-prescricao` com `--fundamento-prescricao` | Afasta a prescrição (dependente menor, incapaz ou ausente) |

Exemplo dos assets: ajuizamento em 15/03/2008, marco 15/03/2003, critério da competência: prescritas as competências até 02/2003; devidas de 03/2003 em diante. O abono anual segue a competência em que foi lançado.

O perito apresenta os dois quadros (prescritas e devidas) e o critério; a aplicação é do juízo.

---

## 6. Decadência

Regra: dez anos para a revisão do ato de concessão, do dia primeiro do mês seguinte ao do recebimento da primeira prestação (Lei 8.213/1991, art. 103, caput). Para benefícios anteriores à MP 1.523-9/1997, a orientação atribuída ao STF (Tema 313, RE 626.489) fixa o termo inicial em 01/08/1997 e o final em 01/08/2007 `[A VERIFICAR tese e alcance]`.

Duas linhas que o laudo registra sem decidir:

1. A readequação aos tetos das emendas não revisa o ato de concessão: aplica limite externo posterior. A Corte Especial do TRF1 (AC 1018697-75.2023.4.01.3300, j. 02/12/2024) afasta a decadência nessa hipótese; a Primeira Turma segue a mesma linha nas apelações listadas em `references/fundamentacao-legal.md`, seção 3.
2. A reconstrução da RMI (coeficientes, tetos da época, fração do excedente) revisa o ato de concessão e, em tese, se sujeita ao art. 103, caput; se o ajuizamento foi após 01/08/2007, o perito apresenta o cenário "só readequação das emendas" ao lado do cenário "RMI recalculada mais readequação", e o juízo escolhe.

O bloco `decadencia` de `atrasados_prescricao.py` informa os termos e se o ajuizamento ocorreu dentro do decênio; não conclui.

---

## 7. Abono anual nas diferenças

O abono anual (Lei 8.213/1991, art. 40) é devido a quem recebeu renda mensal durante o ano, proporcional aos meses. A diferença revisional gera diferença de abono. O script lança, por bloco e por ano, uma parcela na competência do último mês do bloco no ano, no valor da diferença daquele mês multiplicada pelos meses do bloco no ano sobre doze (`--sem-abono` desliga). Premissa: a renda do último mês representa o abono; se o juízo mandar usar a média, declarar e ajustar.

---

## 8. Quesitos sobre sucessão e prescrição

1. Quem está habilitado nos autos, por que título e a partir de que decisão?
2. Qual o período das parcelas do titular e qual o da pensão, considerados os óbitos documentados?
3. Qual o coeficiente da pensão na data do óbito do segurado e qual o seu fundamento?
4. Quais parcelas são anteriores ao quinquênio que antecede o ajuizamento e qual o critério adotado?
5. A revisão pretendida (reconstrução da RMI ou readequação das emendas) revisa o ato de concessão? Quais as datas relevantes para a decadência?
6. Há dependente menor, incapaz ou ausente que afaste a prescrição?
7. O INSS já pagou alguma revisão ou acordo que deva ser abatido?

Modelo de resposta: "As parcelas do titular (bloco 03/2003 a 06/2010, Anexo IV) destinam-se à pensionista habilitada em [data] e, por seu falecimento em 20/09/2023, aos sucessores dela, cuja habilitação consta de [fls.]; as da pensão (07/2010 a 09/2023) seguem o mesmo destino. O cabimento da habilitação e o alcance do art. 112 à pensionista são matéria do juízo."

---

## 9. Pendências de verificação

1. Súmula 85 do STJ: texto.
2. STF, Tema 313 (RE 626.489): tese e alcance.
3. Decreto 89.312/1984: coeficiente da pensão por morte no regime anterior.
4. Lei 8.213/1991, art. 75, redação original: percentuais; Lei 9.032/1995 e Lei 9.528/1997: redações e vigências.
5. EC 103/2019, art. 23: cotas.
6. Alcance do art. 112 da Lei 8.213/1991 ao valor não recebido em vida pela pensionista.
7. Decreto 20.910/1932: aplicabilidade à interrupção ou suspensão da prescrição por requerimento administrativo.
8. Critério da data em que a parcela "deveria ter sido paga" para o art. 103, parágrafo único.
