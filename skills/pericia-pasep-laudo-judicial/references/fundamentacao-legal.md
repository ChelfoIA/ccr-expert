# Fundamentação legal da perícia judicial do PASEP: procedimento, laudo, ônus e jurisprudência verificada

Referência: 12/09/2026. Todo item marcado `[A VERIFICAR]` exige conferência em fonte oficial (planalto.gov.br, stj.jus.br, stf.jus.br, cfc.org.br, cnj.jus.br) antes de entrar no laudo. A jurisprudência da seção 6 foi copiada, com identificação idêntica, de `pericia-pasep/references/jurisprudencia.md`, auditada em fontes primárias em 13/06/2026 e 04/08/2026; nenhum precedente foi acrescentado a essa lista. O que está fora dela é pendência.

## Sumário

1. Papel e deveres do perito do juízo
2. Procedimento da prova pericial, artigo a artigo
3. Honorários e gratuidade
4. Conteúdo do laudo e normas do CFC
5. Ônus da prova por modalidade de saída
6. Jurisprudência verificada
7. Prescrição como premissa de cenário
8. Regime de atualização por polo
9. Sigilo e dados pessoais
10. Roteiro de quesitos que o juízo costuma pedir ao perito
11. Protocolo antifabricação aplicado ao domínio
12. Pendências de verificação

---

## 1. Papel e deveres do perito do juízo

O perito é auxiliar da justiça nomeado quando a prova do fato depende de conhecimento técnico (CPC art. 156, caput), escolhido entre profissionais habilitados inscritos no cadastro do tribunal (art. 156, § 1º). Sujeita-se aos motivos de impedimento e suspeição do juiz (art. 148, II) e pode escusar-se por motivo legítimo em quinze dias da intimação (art. 157, § 1º). Responde por dolo ou culpa quando presta informação inverídica, com inabilitação de dois a cinco anos para outras perícias (art. 158). Cumpre o encargo independentemente de termo de compromisso (art. 466, caput).

Três consequências práticas no PASEP:

| Dever | Fundamento | Como a skill o atende |
|---|---|---|
| Diligência no prazo | CPC arts. 157 e 468, II | Painel do lote ordenado por prazo, com histórico datado de cada ato |
| Imparcialidade e limite do objeto | CPC art. 473, § 2º; NBC PP 01 (R2) | Cenários rotulados por tese; questão de direito devolvida ao juízo |
| Veracidade e rastreabilidade | CPC art. 158; NBC TP 01 (R2) | Índices com fonte e data; memória do motor em anexo; nenhuma citação fora da lista verificada |

O assistente técnico é de confiança da parte, não se sujeita a impedimento ou suspeição (art. 466, § 1º) e tem direito de acompanhar diligências com aviso prévio de cinco dias comprovado nos autos (art. 466, § 2º). O perito do juízo não discute com ele fora dos autos; responde ao parecer nos esclarecimentos (art. 477, § 2º, II).

---

## 2. Procedimento da prova pericial, artigo a artigo

| Artigo do CPC | O que dispõe | O que a perita faz | Registro no lote |
|---|---|---|---|
| 464 | Prova pericial: exame, vistoria ou avaliação; indeferimento quando desnecessária | Confirmar que o objeto é técnico (reconstrução de saldo, modalidade de saída) e não jurídico | `objeto_saneamento` |
| 465, caput | Nomeação de perito especializado e fixação imediata do prazo do laudo | Anotar prazo e data da nomeação; contar em dias úteis (art. 219) | `data_nomeacao`, `prazo_laudo`, status `nomeado` |
| 465, § 1º | Partes têm 15 dias para arguir impedimento, indicar assistente e apresentar quesitos | Aguardar o decurso antes de fechar a matriz de quesitos | `quesitos`, `assistente_autor`, `assistente_reu` |
| 465, § 2º | Perito tem 5 dias para proposta de honorários, currículo e contatos | Proposta pela skill `proposta-pericial-judicial` | status `proposta_entregue`, `honorarios` |
| 465, §§ 3º e 4º | Partes se manifestam em 5 dias; juiz arbitra; levantamento de até 50% no início | Requerer o levantamento; o restante só após laudo e esclarecimentos | `honorarios` |
| 465, § 5º | Perícia inconclusiva ou deficiente: redução dos honorários | Entregar cenários completos; nunca "depende da tese" sem valor | n/a |
| 466 | Encargo sem termo de compromisso; assistentes acompanham diligências com aviso de 5 dias | Comunicar diligência nos autos com antecedência | `historico` |
| 467 | Escusa ou recusa por impedimento ou suspeição; novo perito | Checar vínculo com partes e advogados antes do primeiro ato | `observacoes` |
| 468 | Substituição por falta de conhecimento ou por descumprir prazo sem motivo; multa; devolução em 15 dias | Pedir prorrogação antes do vencimento (art. 476) | painel: alerta |
| 469 | Quesitos suplementares durante a diligência | Incluir na matriz com a origem "suplementar" | `quesitos` |
| 470 | Juiz indefere quesitos impertinentes e formula os seus | Matriz registra indeferidos como "prejudicado" | `quesitos.juizo` |
| 471 | Perícia consensual: partes escolhem o perito | Mesmo procedimento; conferir se o juízo fixou prazo | n/a |
| 473 | Conteúdo do laudo: objeto, análise, método, resposta conclusiva a todos os quesitos; linguagem simples; vedação de opinião além do objeto; solicitação de documentos a partes, terceiros e repartições | Template do laudo; termo de diligência e ofício ao BB (§ 3º) | status `diligencia`, `calculo` |
| 474 | Partes têm ciência de data e local da produção da prova | Toda diligência comunicada nos autos | `historico` |
| 476 | Prorrogação, uma vez, pela metade do prazo, por motivo justificado | Requerer com antecedência, com o motivo (extrato não juntado pelo BB) | `prazo_laudo` atualizado |
| 477, caput | Laudo protocolado no prazo e ao menos 20 dias antes da audiência | Protocolo; nome de arquivo versionado | status `laudo_entregue`, `versao_laudo` |
| 477, § 1º | Partes se manifestam em 15 dias; assistentes apresentam parecer | Aguardar; ler parecer do assistente | n/a |
| 477, § 2º | Perito esclarece em 15 dias divergência ou dúvida das partes, do juiz, do MP e ponto divergente do parecer | Esclarecimentos ponto a ponto; nova versão se retificar | status `esclarecimentos`, `prazo_esclarecimentos` |
| 477, §§ 3º e 4º | Esclarecimento em audiência, com quesitos prévios; intimação eletrônica com 10 dias | Preparar respostas por quesito | `observacoes` |
| 479 | Juiz aprecia a prova pericial livremente (art. 371), indicando os motivos | O laudo informa; não valora ônus nem decide tese | n/a |
| 480 | Segunda perícia quando a matéria não estiver esclarecida; não substitui a primeira | Entregar memória completa para que a segunda perícia seja desnecessária | status `encerrado` |

Exibição de documento: o juiz pode ordenar que a parte exiba documento ou coisa em seu poder (CPC art. 396); a recusa injustificada autoriza a presunção de veracidade dos fatos que a parte pretendia provar com o documento (art. 400). Terceiro (órgão empregador, outro banco) é intimado a exibir (arts. 401 a 404). O perito solicita diretamente (art. 473, § 3º) e, sem resposta, requer ao juízo a ordem de exibição.

---

## 3. Honorários e gratuidade

Cada parte adianta a remuneração do seu assistente; a do perito é adiantada por quem requereu a perícia ou rateada quando determinada de ofício ou requerida por ambas (CPC art. 95, caput). O juiz pode determinar o depósito em juízo (art. 95, § 1º). Quando o responsável é beneficiário de gratuidade, a perícia pode ser paga com recursos do orçamento, conforme tabela do tribunal ou do CNJ, ou realizada por entidade pública (art. 95, § 3º); os honorários do perito estão entre as despesas cobertas pela gratuidade (art. 98, § 1º, VI). A tabela de valores da gratuidade é atribuída à Resolução CNJ 232/2016 `[A VERIFICAR número e valores vigentes]`; o cadastro de peritos (art. 156, § 1º) é atribuído à Resolução CNJ 233/2016 `[A VERIFICAR]`.

Em lote, registrar por processo: proposta apresentada, valor arbitrado, percentual levantado e condição do saldo. Honorários finais só depois dos esclarecimentos (art. 465, § 4º).

---

## 4. Conteúdo do laudo e normas do CFC

O art. 473 do CPC exige quatro conteúdos: (I) exposição do objeto; (II) análise técnica; (III) indicação do método, demonstrando que é predominantemente aceito pelos especialistas da área; (IV) resposta conclusiva a todos os quesitos do juiz, das partes e do Ministério Público. O § 1º impõe fundamentação em linguagem simples e com coerência lógica, indicando como se chegou às conclusões. O § 2º veda ultrapassar os limites da designação e emitir opinião pessoal que exceda o exame técnico.

A NBC TP 01 (R2) disciplina a perícia contábil (planejamento, diligências, termo de diligência, laudo e parecer, estrutura com identificação, objeto, método, diligências, transcrição e resposta aos quesitos, conclusão, encerramento e anexos) e a NBC PP 01 (R2) disciplina o perito contábil (independência, impedimento e suspeição, responsabilidade, sigilo, honorários). A numeração dos itens dessas normas não é citada de memória nesta skill: `[A VERIFICAR o item na redação vigente em cfc.org.br antes de citar número de item]`. Citar a norma pelo nome e pelo assunto do item é suficiente para o laudo.

Correspondência adotada no `assets/template_laudo_pasep.md`:

| Seção do template | Art. 473 | NBC TP 01 (R2), assunto |
|---|---|---|
| 1 Identificação e encargo | caput | identificação do processo, das partes e do perito |
| 2 Objeto e quesitos recebidos | I e IV | síntese do objeto; transcrição dos quesitos |
| 3 Documentos e diligências | § 3º | diligências e documentos examinados |
| 4 Metodologia e fontes | III | método, critérios e fontes |
| 5 Análise | II | análise técnica |
| 6 Cenários | II e § 1º | demonstração dos resultados por hipótese |
| 7 Resposta aos quesitos | IV | resposta a cada quesito |
| 8 Conclusão | § 1º | conclusão |
| 9 Encerramento e anexos | § 3º | termo de encerramento, apêndices e anexos |

---

## 5. Ônus da prova por modalidade de saída

Regra geral: o autor prova o fato constitutivo; o réu, o fato impeditivo, modificativo ou extintivo (CPC art. 373, I e II). O juiz pode redistribuir o ônus por decisão fundamentada (art. 373, § 1º), inclusive no saneamento (art. 357, III). No PASEP, o Tema 1.300/STJ fixou a distribuição por modalidade e afastou, para crédito em conta e FOPAG, a inversão do art. 6º, VIII, do CDC e a redistribuição do art. 373, § 1º.

| Modalidade | Fato a provar | Quem prova | Prova típica | Como o laudo registra a falta |
|---|---|---|---|---|
| CAIXA-BB | Pagamento ao titular (extintivo) | BB | Recibo assinado, identificação do recebedor, registro biométrico (CC art. 320) | "Saída sem comprovação apresentada pelo réu" |
| CREDITO-CC | Não entrada do valor na conta de destino (constitutivo) | Participante | Extrato da conta de destino | "Saída sem comprovação apresentada pelo autor" |
| FOPAG | Não entrada do valor na folha (constitutivo) | Participante | Contracheques ou ficha financeira | "Saída sem comprovação apresentada pelo autor" |
| Não identificada | Pressuposto: identificar a modalidade | BB (legenda dos códigos) | Legenda do extrato; ofício | "Modalidade não identificada; ônus não atribuído pela perícia" |

O perito classifica e registra; a consequência da falta (presunção, improcedência do ponto) é do juízo (CPC arts. 373 e 479). A relação de consumo entre cotista e BB é controvertida entre tribunais (registro em `pericia-pasep/references/jurisprudencia.md`, seção 7): o laudo não afirma nem nega a incidência do CDC.

---

## 6. Jurisprudência verificada

Fonte da auditoria: `pericia-pasep/references/jurisprudencia.md` (reverificação de 04/08/2026 em base jurisprudencial estruturada; verificação cruzada de 13/06/2026). Citar com a identificação abaixo, sem alteração.

**STJ, Tema 545.** Paradigma: REsp 1.205.277/PB. Relator: Min. Teori Albino Zavascki. Órgão: Primeira Seção. Rito: art. 543-C do CPC/1973. Julgamento: 27/06/2012. DJe 01/08/2012. Tese: é de cinco anos o prazo prescricional da ação promovida contra a União Federal por titulares de contas vinculadas ao PIS/PASEP visando à cobrança de diferenças de correção monetária incidente sobre o saldo dessas contas, nos termos do art. 1º do Decreto-Lei 20.910/1932. Termo inicial: data a partir da qual deixou de ser feito o creditamento da última diferença pleiteada. Grafia oficial do paradigma: /PB (Paraíba), nunca /PE. Portal de repetitivos: `https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true&tipo_pesquisa=T&cod_tema_inicial=545&cod_tema_final=545`.

**STJ, Tema 1.150.** Paradigmas: REsp 1.895.936/TO, REsp 1.895.941/TO e REsp 1.951.931/DF (origem TJTO). Relator: Min. Herman Benjamin. Órgão: Primeira Seção, por unanimidade. Afetação: 06/05/2022. Julgamento: 13/09/2023. Acórdão publicado (DJe): 21/09/2023. Trânsito em julgado registrado em 25/10/2025 `[A VERIFICAR a data exata no andamento antes de afirmá-la em peça]`. Teses: (i) o Banco do Brasil tem legitimidade passiva ad causam para figurar em demanda na qual se discute eventual falha na prestação do serviço quanto a conta vinculada ao PASEP, saques indevidos e desfalques, além da ausência de aplicação dos rendimentos estabelecidos pelo Conselho Diretor; (ii) a pretensão ao ressarcimento dos danos havidos em razão dos desfalques em conta individual vinculada ao PASEP submete-se ao prazo prescricional decenal do art. 205 do Código Civil; (iii) o termo inicial é o dia em que o titular comprovadamente toma ciência dos desfalques na conta (actio nata).

**STJ, Tema 1.300.** Paradigmas: REsp 2.162.222/PE, REsp 2.162.223/PE, REsp 2.162.198/PE e REsp 2.162.323/PE (origem TJPE). Relatora: Min. Maria Thereza de Assis Moura. Órgão: Primeira Seção, por maioria. Afetação: 16/12/2024. Julgamento: 10/09/2025. Acórdão publicado: 18/09/2025. Embargos de declaração rejeitados pela Primeira Seção (j. 12/11/2025, DJe 19/11/2025, registro da auditoria de 08/2026; conferir o andamento antes de citar). Tese: nas ações em que o participante contesta saques em sua conta individualizada do PASEP, o ônus de provar cabe ao participante quanto aos saques sob as formas de crédito em conta e de pagamento por folha de pagamento (PASEP-FOPAG), por ser fato constitutivo de seu direito (art. 373, I, do CPC), sendo incabível a inversão (art. 6º, VIII, do CDC) ou a redistribuição (art. 373, § 1º, do CPC); e ao réu quanto aos saques sob a forma de saque em caixa das agências do BB, por ser fato extintivo do direito do autor (art. 373, II, do CPC).

**Súmula 85/STJ.** Nas relações jurídicas de trato sucessivo em que a Fazenda Pública figure como devedora, quando não tiver sido negado o próprio direito reclamado, a prescrição atinge apenas as prestações vencidas antes do quinquênio anterior à propositura da ação. Incide na parcela contra a União (Tema 545); não incide contra o BB.

**STF, Tema 810 (RE 870.947/SE).** Constitucionalidade do art. 1º-F da Lei 9.494/1997: atualização de débitos da Fazenda Pública. Relevante apenas para a parcela contra a União, no período anterior à EC 113/2021.

Inexistência registrada na auditoria: não há Tema de Repercussão Geral do STF sobre prescrição em ações PASEP; o "RE 1.220.711/STF" é citação apócrifa. Ambos não entram em laudo.

Correlatos registrados na `pericia-pasep` e não incorporados a esta lista: STJ Tema 1.309 (inversão e redistribuição do ônus, mesma sessão de 10/09/2025) `[A VERIFICAR antes de citar]`; STJ Tema 905 (correção e juros contra a Fazenda) `[A VERIFICAR antes de citar]`; IRDR 16 do TJDFT `[A VERIFICAR antes de citar; só para causas no DF]`.

---

## 7. Prescrição como premissa de cenário

O perito não declara prescrição. Ele registra as datas de fato e calcula cada cenário com e sem o corte que a tese pressupõe:

| Polo da tese | Prazo | Fundamento | Termo inicial (fato a registrar) | Corte no cenário |
|---|---|---|---|---|
| BB (Tema 1.150) | Decenal | CC art. 205 | Dia em que o titular comprovadamente tomou ciência do desfalque (documento, fls.) | Diferenças cuja ciência seja anterior a dez anos da propositura ficam em coluna separada |
| União (Tema 545) | Quinquenal | DL 20.910/1932, art. 1º | Data em que deixou de ser feito o creditamento da última diferença | Com Súmula 85/STJ: preservadas as parcelas dos cinco anos anteriores à propositura |
| Litisconsórcio | Dupla | Temas 1.150 e 545 | Cada diferença com a sua origem | Corte por origem; soma por polo |

Datas que o laudo precisa registrar na seção 5.1, cada uma com o documento: abertura da conta; cada saída impugnada; emissão do extrato ou outro ato que o autor aponta como ciência; último creditamento omitido (parcela contra a União); propositura; citação de cada réu. Sem a data de ciência nos autos, o cenário A apresenta o corte em hipóteses alternativas (ciência na data do extrato; ciência na data de cada saque) e declara a lacuna.

---

## 8. Regime de atualização por polo

Fonte: `pericia-pasep/references/legislacao.md` e `SKILL.md` daquela skill (cenários A a D). O motor aplica; o laudo rotula.

| Polo | Correção | Juros | Fundamento | Ressalva obrigatória |
|---|---|---|---|---|
| BB | Percentuais oficiais do Tesouro até 31/05/2020; IPCA-E depois (cenário A) ou SELIC (cenário B) | Civis: 1% a.m. simples até 29/08/2024 e taxa legal do art. 406, § 1º, do CC (Lei 14.905/2024) depois; SELIC não cumula com juros | CC arts. 205 e 406; Lei 14.905/2024; Res. CMN 5.171/2024 | BB é sociedade de economia mista: não se aplicam DL 20.910/1932, EC 113/2021 nem EC 136/2025 |
| União | Regime intertemporal: IPCA-E e poupança até 08/12/2021; SELIC de 12/2021 a 08/2025; IPCA + 2% a.a. simples a partir de 09/2025, com a SELIC como teto (cenário C) ou INPC (cenário D) | No fator (C) ou civis (D) | EC 113/2021, art. 3º, na redação da EC 136/2025; Súmula 85/STJ; STF Tema 810 | Aplicação do novo art. 3º à fase anterior à expedição do precatório é operacional e controvertida; tema pendente no STF `[A VERIFICAR o andamento]` |

Regras de redação: nunca cumular SELIC com juros adicionais; registrar série SGS, código e data de consulta de cada fator; declarar o critério de tratamento de lacuna; apresentar o impacto percentual entre cenários sem indicar o "correto".

---

## 9. Sigilo e dados pessoais

Os autos contêm CPF, cadastro PASEP, extratos bancários e contracheques. O tratamento desses dados pelo perito tem base no exercício regular de direitos em processo judicial (Lei 13.709/2018, art. 7º, VI) e no cumprimento de obrigação legal do auxiliar da justiça (art. 7º, II). Medidas mínimas: pasta por processo com acesso restrito; nenhum dado em serviço de nuvem sem controle de acesso; anonimização completa em qualquer uso didático ou de exemplo (processo `0000000-00.0000.0.00.0000`, CPF `000.000.000-00`, nomes fictícios); descarte seguro depois do trânsito em julgado e do prazo de guarda que o perito adotar. Segredo de justiça (CPC art. 189) restringe o acesso aos autos às partes e aos procuradores: o laudo não circula fora do processo. A NBC PP 01 (R2) trata do sigilo profissional do perito `[A VERIFICAR o item]`.

---

## 10. Roteiro de quesitos que o juízo costuma pedir ao perito

Quando o juízo pede ao perito sugestão de quesitos (CPC art. 470, II) ou quando a decisão de saneamento é genérica, propor os seguintes, todos de fato:

1. Qual o período coberto pelo extrato analítico juntado e qual a data de abertura da conta? Há lacuna?
2. Qual a evolução do saldo, mês a mês, pela valorização oficial do Conselho Diretor, e qual a diferença em relação ao saldo do extrato em cada competência?
3. Quais são as saídas lançadas na conta, com data, valor e modalidade (saque em caixa, crédito em conta, folha de pagamento ou não identificada)?
4. Para cada saída, há nos autos recibo, identificação do recebedor, registro biométrico, extrato da conta de destino ou contracheque? Indicar as folhas.
5. Os índices creditados correspondem aos percentuais oficiais do Tesouro Nacional e, após 31/05/2020, ao regime aplicável? Indicar divergências e fontes.
6. Em que datas constam dos autos: a ciência do desfalque alegada pelo autor, o último creditamento omitido, a propositura e a citação de cada réu?
7. Qual o valor das diferenças apuradas em cada cenário de atualização, segregado por origem (saque, índice, omissão de rendimento) e com e sem o corte prescricional que cada tese pressupõe?
8. Há documento que a perícia solicitou e não foi apresentado? Qual o efeito da falta sobre o cálculo?

Quesitos que o perito devolve como questão de direito quando formulados: "está prescrito?", "o BB é parte legítima?", "o autor se desincumbiu do ônus?", "aplica-se o CDC?", "houve má gestão?". Resposta padrão em `references/laudo-e-quesitos.md`, seção 4.

---

## 11. Protocolo antifabricação aplicado ao domínio

1. Precedente: somente os da seção 6, com a identificação copiada. Qualquer outro entra como `[A VERIFICAR]` e na seção 12.
2. Norma: CPC, CC, DL 20.910/1932, LC 8/1970, LC 26/1975 e LGPD citadas com dispositivo. Item de NBC, resolução do CNJ e portaria entram com `[A VERIFICAR]` no número.
3. Índice, percentual de valorização e fator: só por arquivo gerado pelo motor da `pericia-pasep`, com série, código SGS e data de consulta. Nenhum número de memória.
4. Data sensível ao tempo (trânsito em julgado, publicação, andamento de tema pendente): referência 12/09/2026 e conferência no portal antes de protocolar.
5. Dado ausente nunca vira zero: vira ressalva com o período ou a saída afetada.
6. Toda afirmação do laudo remete a folhas dos autos ou a anexo gerado por script.

---

## 12. Pendências de verificação

| Item | O que conferir | Onde |
|---|---|---|
| NBC TP 01 (R2) e NBC PP 01 (R2) | Numeração dos itens sobre laudo, termo de diligência, sigilo e independência na redação vigente | cfc.org.br |
| Resolução CNJ 232/2016 | Número, vigência e tabela de honorários na gratuidade | cnj.jus.br |
| Resolução CNJ 233/2016 | Número e regras do cadastro de peritos (CPC art. 156, § 1º) | cnj.jus.br |
| STJ Tema 1.150 | Data exata do trânsito em julgado (registro de 25/10/2025 apoiado em fonte secundária) | stj.jus.br, andamento dos REsp 1.895.936/TO, 1.895.941/TO e 1.951.931/DF |
| STJ Tema 1.300 | Andamento após os embargos de declaração rejeitados em 12/11/2025 | stj.jus.br |
| STJ Tema 1.309 | Teor e aplicabilidade ao PASEP antes de qualquer citação | stj.jus.br |
| STJ Tema 905 | Teor e alcance temporal frente às EC 113/2021 e 136/2025 | stj.jus.br |
| IRDR 16 do TJDFT | Teor; só para causas no DF | tjdft.jus.br |
| EC 136/2025 na fase pré-precatório | Tema pendente no STF sobre o alcance do novo art. 3º da EC 113/2021 | stf.jus.br |
| Lei 13.709/2018, art. 7º, VI | Redação vigente e eventual orientação da ANPD para auxiliares da justiça | planalto.gov.br, gov.br/anpd |
