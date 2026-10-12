# Template de laudo pericial contábil: conta individual do PASEP (perito do juízo)

Uso: preencher os campos entre colchetes; excluir as seções inaplicáveis (por exemplo, os cenários C e D em processo só contra o Banco do Brasil). Nenhum número entra sem a memória gerada pelo motor da skill `pericia-pasep`; nenhum precedente entra fora da lista verificada em `references/fundamentacao-legal.md`, seção 6. Linguagem neutra conforme `references/laudo-e-quesitos.md`, seção 2. Este template é do perito do juízo; para parecer de assistente técnico usar `pericia-pasep/assets/template_parecer.md`.

Nome de arquivo sugerido: `AAAA-MM-DD_Laudo_PASEP_<id do lote>_vN.md` (por exemplo, `2026-10-20_Laudo_PASEP_P-002_v1.md`).

---

## Laudo pericial contábil

**Processo nº** [0000000-00.0000.0.00.0000]
**Juízo** [vara, comarca ou seção judiciária]
**Ação** [procedimento comum: conta individual do PASEP]
**Autor(a)** [nome]
**Réu(s)** [Banco do Brasil S.A. e/ou União]
**Assistentes técnicos** [autor: nome ou "não indicado"; réu: nome ou "não indicado"]
**Perito(a)** [nome], contador(a), CRC [UF] [número]
**Nomeação** [dd/mm/aaaa, fl. N]; **prazo do laudo** [dd/mm/aaaa]
**Data-base dos cálculos** [dd/mm/aaaa]
**Id no lote** [P-00N]; **versão** [v1]

---

## 1. Identificação e encargo

1.1. O(a) signatário(a), [nome], contador(a) inscrito(a) no CRC [UF] sob o nº [número], foi nomeado(a) perito(a) do juízo pela decisão de fl. [N] (CPC art. 465) e cumpre o encargo independentemente de termo de compromisso (CPC art. 466), sem impedimento ou suspeição (CPC art. 148, II).

1.2. Honorários: proposta de fl. [N], arbitrados em R$ [valor] (fl. [N]); [50% levantados em dd/mm/aaaa, CPC art. 465, § 4º].

1.3. O laudo observa os arts. 464 a 480 do CPC, a NBC TP 01 (R2) e a NBC PP 01 (R2).

---

## 2. Objeto fixado no saneamento e quesitos recebidos

2.1. Objeto, conforme a decisão de saneamento de fl. [N]: "[transcrever]".

2.2. Não integram o objeto, por serem matéria de decisão do juízo (CPC art. 473, § 2º): a ocorrência de prescrição, a legitimidade passiva de cada réu, a consequência da ausência de prova sobre cada saída (CPC art. 373), a incidência do CDC e a procedência dos pedidos. Sobre esses pontos o laudo registra fatos, datas e valores por hipótese.

2.3. Quesitos recebidos (matriz completa no anexo IV):

| Origem | Nº | Quesito (síntese) | Tipo | Seção da resposta |
|---|---:|---|---|---|
| Juízo (fl. N) | 1 | [síntese] | fato | 7.1 |
| Autor (fl. N) | 1 | [síntese] | fato | 7.2 |
| Réu (fl. N) | 1 | [síntese] | direito | 7.3 |

---

## 3. Documentos examinados e diligências realizadas

| Nº | Documento | Fls. | Origem | Observação |
|---|---|---|---|---|
| 1 | Extrato analítico da conta PASEP nº [cadastro] | | BB | Cobre [mm/aaaa] a [mm/aaaa] |
| 2 | RAIS ou ficha financeira do órgão empregador | | Autor | Vínculo de [aaaa] a [aaaa]; conta aberta em [aaaa] |
| 3 | Microfilmagem ou recibos das saídas em caixa | | BB | [apresentados / não apresentados apesar do ofício de fl. N] |
| 4 | Contracheques dos meses das saídas em folha | | Autor | [juntados / não juntados apesar da solicitação de fl. N] |
| 5 | Extrato da conta-corrente de destino | | Autor | [se houver saída por crédito em conta] |
| 6 | Decisão de saneamento | | Autos | Objeto e ônus |
| 7 | Consultas ao SGS do Banco Central e tabela do Tesouro Nacional | | Perícia | Anexo II, com data de consulta |

3.1. Lacunas: o extrato não cobre [período]; [documento] não foi apresentado por [quem] apesar de [ofício/solicitação de fl. N e requerimento de exibição de fl. N]. O período não coberto foi excluído da reconstrução e as saídas sem comprovação constam do quadro 5.3 com essa indicação. Dado ausente não foi tratado como zero.

3.2. Diligências: termo de diligência de [dd/mm/aaaa] (fl. N); ofício ao Banco do Brasil de [dd/mm/aaaa] (fl. N), respondido em [dd/mm/aaaa] (fl. N) [ou sem resposta]; solicitação à parte autora de [dd/mm/aaaa] (fl. N). As partes e os assistentes tiveram ciência de cada ato (CPC art. 474).

---

## 4. Metodologia e fontes

4.1. Reconstrução do saldo mês a mês, desde [mm/aaaa], pela valorização oficial do Conselho Diretor na ordem RAC, AM, Juros e RLA, com os percentuais da tabela de valorização do Tesouro Nacional (anexo II), executada por `conciliacao_pasep.py` (skill `pericia-pasep`), e confronto com o saldo do extrato competência a competência.

4.2. Classificação de cada saída por modalidade segundo o código de histórico do extrato e a legenda juntada: saque em caixa (CAIXA-BB), crédito em conta-corrente (CREDITO-CC), folha de pagamento (FOPAG) ou não identificada (OUTROS).

4.3. Cenários de atualização gerados por `cenarios_atualizacao.py` com fatores obtidos por `bcb_loader.py` e `fator_correcao.py`: séries SGS [códigos], consultadas em [dd/mm/aaaa]; cada cenário rotulado pela tese que pressupõe (seção 6). Autoteste do motor (`selftest.py`) executado em [dd/mm/aaaa] com resultado íntegro.

4.4. Precisão: fatores com 8 casas; valores intermediários com 4; apresentação com 2; arredondamento declarado na memória. Conversões de moeda pela tabela oficial.

4.5. Tratamento de lacuna: [critério: exclusão do período; ressalva], com o efeito indicado em cada quadro.

---

## 5. Análise

### 5.1. Datas e marcos de fato

| Marco | Data | Documento (fls.) |
|---|---|---|
| Abertura da conta ou primeiro crédito de cotas | | |
| Cada saída impugnada | | |
| Ato apontado pelo autor como ciência do desfalque | | |
| Última competência com creditamento abaixo do oficial | | |
| Propositura da ação | | |
| Citação de cada réu | | |

### 5.2. Reconstrução do saldo

Quadro resumido por ano (mês a mês no anexo I): saldo do extrato, saldo reconstruído, diferença da competência, diferença acumulada, origem da diferença (índice, saída, omissão de rendimento).

| Competência | Saldo do extrato | Saldo reconstruído | Diferença | Origem |
|---|---:|---:|---:|---|
| [12/aaaa] | R$ | R$ | R$ | |

### 5.3. Saídas, modalidade e comprovação (Tema 1.300/STJ)

| Nº | Data | Valor | Código de histórico | Modalidade | Documento de comprovação nos autos | Situação |
|---:|---|---:|---|---|---|---|
| 1 | | R$ | | CAIXA-BB | [recibo fl. N / nenhum] | [comprovada / sem comprovação apresentada pelo réu] |
| 2 | | R$ | | FOPAG | [contracheque fl. N / nenhum] | [comprovada / sem comprovação apresentada pelo autor] |
| 3 | | R$ | | OUTROS | legenda não apresentada | modalidade não identificada; ônus não atribuído pela perícia |

A situação de cada saída descreve o que consta dos autos; a consequência jurídica da ausência de prova cabe ao juízo (CPC arts. 373 e 479).

### 5.4. Índices, rendimentos e conciliação

Confronto dos percentuais creditados com os oficiais, competência a competência (anexo II), e segregação das diferenças por origem:

| Origem da diferença | Valor histórico | Competências afetadas | Documento |
|---|---:|---|---|
| Saídas sem comprovação apresentada pelo réu | R$ | | quadro 5.3 |
| Percentual creditado abaixo do oficial | R$ | | anexo II |
| Omissão de creditamento de rendimento | R$ | | anexo I |

---

## 6. Cenários de atualização

Cabeçalho: processo [número]; id [P-00N]; data-base [dd/mm/aaaa]; citação [dd/mm/aaaa]; ciência adotada [dd/mm/aaaa, fl. N]; propositura [dd/mm/aaaa].

| Cenário | Tese pressuposta | Critério | Sem corte prescricional | Com o corte da tese | Fundamento rotulado |
|---|---|---|---:|---:|---|
| A | Diferença imputável ao BB | Tesouro até 05/2020; IPCA-E; juros civis | R$ | R$ (decenal desde [data]) | Tema 1.150/STJ; CC arts. 205 e 406; Lei 14.905/2024 |
| B | BB, critério alternativo | SELIC, sem juros adicionais | R$ | R$ | Tema 1.150/STJ |
| C | Diferença imputável à União | EC 113/2021, art. 3º (EC 136/2025); Súmula 85/STJ | R$ | R$ (quinquenal anterior a [data]; parcelas preservadas) | Tema 545/STJ; Súmula 85/STJ; STF Tema 810 |
| D | União, critério alternativo | INPC e juros civis | R$ | R$ | Tema 545/STJ; Súmula 85/STJ |

Ressalvas: (1) a aplicação do regime da EC 136/2025 à fase anterior à expedição do precatório é controvertida; (2) o período [mm/aaaa a mm/aaaa] não coberto pelo extrato está excluído; (3) a saída nº [N], de modalidade não identificada, está [incluída/excluída] na coluna indicada. Impacto entre cenários: [A supera C em x%]. Memória completa no anexo III.

---

## 7. Resposta aos quesitos

### 7.1. Quesitos do juízo

> Quesito 1 do juízo: "[transcrição]"
> Resposta: [resposta com remissão à seção, ao quadro e às folhas].

### 7.2. Quesitos do autor

> Quesito 1 do autor: "[transcrição]"
> Resposta: [resposta].

### 7.3. Quesitos do réu

> Quesito 1 do réu: "[transcrição]"
> Resposta: [resposta].

Quesitos indeferidos pelo juízo (CPC art. 470, I): [relacionar como "prejudicado"]. Quesitos fora do objeto: [relacionar com a fórmula da seção 2.2].

---

## 8. Conclusão

8.1. Fatos apurados: [período coberto; saldo reconstruído e diferença acumulada em 31/05/2020; saídas por modalidade e estado de comprovação; divergências de índice].

8.2. Valores por cenário (seção 6), cada um pressupondo a tese rotulada: A, R$ [sem corte] e R$ [com corte]; [B, C, D].

8.3. Limitações: [lacuna do extrato; documentos não apresentados; data de ciência não documentada e hipóteses alternativas apresentadas].

8.4. Dependem de decisão do juízo: prescrição, polo responsável por cada origem de diferença, consequência da ausência de prova sobre cada saída, incidência do CDC e escolha do cenário.

---

## 9. Encerramento, anexos e pendências de verificação

Anexos: I, memória da reconstrução mês a mês (`conciliacao_pasep.py`); II, tabela do Tesouro e consultas ao SGS com data; III, memória dos cenários (`cenarios_atualizacao.py`); IV, matriz de quesitos (`matriz_quesitos.py`); V, termo de diligência, ofícios e respostas.

Pendências de verificação: [itens citados com [A VERIFICAR], se houver; senão, "nenhuma"].

O que mudou nesta versão: [v1: versão inicial].

[Cidade], [dd/mm/aaaa].
[Nome], contador(a), CRC [UF] [número], perito(a) do juízo.

---

## Exemplo preenchido (dados fictícios dos assets)

**Processo nº** 0000002-00.0000.0.00.0000; **Juízo** 2ª Vara Cível, Comarca fictícia; **Autora** Maria da Silva; **Réu** Banco do Brasil S.A.; **Perita** Perita fictícia, CRC 000000; **Id no lote** P-002; **data-base** 20/10/2026; **versão** v1.

**2.1. Objeto** (saneamento de 28/07/2026, fl. 60): "Verificar os saques lançados na conta PASEP da autora, sua modalidade e comprovação, e apurar o saldo que existiria sem as saídas impugnadas."

**3.1. Lacunas.** O extrato de fls. 88 a 131 cobre 01/1990 a 05/2020; a RAIS de fl. 45 indica cadastro em 1985. O ofício de 12/09/2026 (fl. 140) solicitou o período de 1985 a 12/1989 e a microfilmagem das saídas em caixa; o Banco do Brasil respondeu em 30/09/2026 (fl. 150) que não localizou registros anteriores a 1990 e não apresentou recibos. A solicitação de fl. 141 à autora pelos contracheques de junho e julho de 2011 não foi atendida. O período de 1985 a 12/1989 foi excluído da reconstrução.

**5.1. Marcos.** Saídas impugnadas em 14/08/1998, 03/03/2003, 10/06/2011 e 22/09/2016 (extrato, fls. 95, 102, 118 e 126); ciência alegada pela autora em 10/03/2021, data de emissão do extrato de fl. 22; propositura em 05/05/2023 (fl. 2); citação em 20/06/2023 (fl. 38).

**5.3. Saídas.**

| Nº | Data | Valor | Código | Modalidade | Comprovação nos autos | Situação |
|---:|---|---:|---|---|---|---|
| 1 | 14/08/1998 | R$ 1.250,00 | 21 | CAIXA-BB | nenhuma | sem comprovação apresentada pelo réu |
| 2 | 03/03/2003 | R$ 2.180,00 | 21 | CAIXA-BB | nenhuma | sem comprovação apresentada pelo réu |
| 3 | 10/06/2011 | R$ 940,00 | 33 | FOPAG | nenhuma | sem comprovação apresentada pela autora |
| 4 | 22/09/2016 | R$ 3.100,00 | 47 | OUTROS | legenda não apresentada | modalidade não identificada; ônus não atribuído pela perícia |

**6. Cenários** (processo só contra o BB: cenários A e B; valores fictícios; citação 20/06/2023; ciência adotada 10/03/2021).

| Cenário | Tese pressuposta | Critério | Sem corte | Com o corte da tese | Fundamento rotulado |
|---|---|---|---:|---:|---|
| A | Diferença imputável ao BB | Tesouro até 05/2020; IPCA-E; juros civis | R$ 48.310,22 | R$ 48.310,22 (decenal desde 10/03/2021: nenhuma saída excluída) | Tema 1.150/STJ; CC arts. 205 e 406 |
| A (hipótese) | Ciência na data de cada saque | idem | R$ 48.310,22 | R$ 19.874,60 (saídas 1 e 2 excluídas) | idem |
| B | BB, critério alternativo | SELIC | R$ 45.120,07 | R$ 45.120,07 | Tema 1.150/STJ |

Ressalvas: a saída 4 está incluída nas colunas acima; sem ela, o cenário A sem corte é R$ 31.905,14 (anexo III, quadro 2). Impacto: A supera B em 7,07%.

**7.3. Quesito 1 do réu:** "A pretensão da autora está prescrita, considerando que o primeiro saque impugnado ocorreu em 1998?"
**Resposta:** Trata-se de questão de direito, cuja definição cabe ao juízo. Do ponto de vista contábil, a perícia registra as datas de fato da seção 5.1 e apresenta, na seção 6, o valor de cada cenário sem corte prescricional e com o corte que cada tese pressupõe (decenal contado de 10/03/2021; hipótese alternativa de ciência na data de cada saque), sem adotar nenhum deles.

**8. Conclusão.** Reconstruído o período de 01/1990 a 05/2020, apuram-se quatro saídas, duas em caixa sem recibo apresentado pelo réu, uma em folha sem contracheque apresentado pela autora e uma de modalidade não identificada. O saldo que a conta teria em 31/05/2020 sem as quatro saídas é R$ 14.602,35 (anexo I). Valores por cenário na seção 6. Dependem de decisão do juízo a prescrição, a consequência da ausência de cada prova e a escolha do cenário.

**Pendências de verificação:** nenhuma.
