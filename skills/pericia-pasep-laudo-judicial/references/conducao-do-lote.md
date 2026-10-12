# Condução do lote: rotina, pastas, isolamento de premissas, versões e sigilo

Referência: 12/09/2026. Este arquivo organiza o trabalho da perita que conduz vários processos de PASEP ao mesmo tempo como perita do juízo. O registro do lote é gerado e mantido por `scripts/lote_pasep.py`; o que está aqui é a disciplina em torno dele.

## Sumário

1. Rotina semanal
2. Pastas e nomes de arquivo por processo
3. Isolamento de premissas: o teste do cabeçalho
4. Controle de versões do laudo e dos esclarecimentos
5. Sigilo, LGPD e anonimização
6. Comunicação somente nos autos
7. Prazos: contagem, prorrogação e escusa
8. Checklist de fechamento por processo
9. Encerramento no lote

---

## 1. Rotina semanal

| Dia | Ação | Comando ou arquivo |
|---|---|---|
| Segunda | Painel do lote com a data do dia; ler alertas; definir a próxima ação de cada processo | `python3 scripts/lote_pasep.py painel --registro lote.json --hoje dd/mm/aaaa --md painel.md` |
| Segunda | Consultar os autos de cada processo com alerta ou com diligência pendente (resposta do BB, juntada do autor, decisão sobre prorrogação) | sistema do tribunal |
| Terça a quinta | Trabalho por processo, um de cada vez, na pasta do processo: diligências, `caso.json`, motor, matriz, laudo | seções 2 e 3 |
| Diariamente | Registrar o evento no dia em que ocorre (documento recebido, ofício expedido, prazo alterado) | `python3 scripts/lote_pasep.py atualizar --registro lote.json --id P-00N ...` |
| Sexta | Checklist documental dos processos em diligência; conferir quem ainda não respondeu e o prazo sugerido | `python3 scripts/checklist_documental_pasep.py --registro lote.json --processo P-00N` |
| Sexta | Cópia de segurança do `lote.json` e das pastas dos processos em local com acesso restrito | seção 5 |

Um processo por vez. Abrir dois extratos ao mesmo tempo é a origem típica da contaminação descrita na seção 3.

---

## 2. Pastas e nomes de arquivo por processo

```
lote_pasep/
  lote.json                              registro do lote (scripts/lote_pasep.py)
  painel/2026-09-12_painel.md            painéis datados
  P-001/
    00_autos/                            peças lidas (inicial, contestações, saneamento, extrato)
    01_diligencias/2026-09-12_Termo_Diligencia_P-001_v1.md
    01_diligencias/2026-09-12_Oficio_BB_P-001_v1.md
    02_calculo/caso.json                 entrada do motor da pericia-pasep (schema_caso.json)
    02_calculo/conciliacao.json          saída de conciliacao_pasep.py
    02_calculo/diferencas.json           entrada de cenarios_atualizacao.py
    02_calculo/cenarios.json             saída de cenarios_atualizacao.py
    02_calculo/indices/ipca_e_2020-06_2026-08.json   saída de bcb_loader.py, com data de consulta
    03_quesitos/quesitos.json            quesitos por proponente
    03_quesitos/matriz.md                saída de matriz_quesitos.py
    04_laudo/2026-10-20_Laudo_PASEP_P-001_v1.md
    05_esclarecimentos/2026-11-25_Esclarecimentos_PASEP_P-001_v1.md
  P-002/
    ...
```

Padrão de nome: `AAAA-MM-DD_Tipo_PASEP_<id>_vN.md`, em que `Tipo` é `Laudo`, `Esclarecimentos`, `Termo_Diligencia`, `Oficio_BB` ou `Solicitacao_Autor`, `<id>` é o id do processo no lote (`P-001`) e `vN` é a versão. O número CNJ do processo não entra no nome do arquivo (sigilo e tamanho); ele está no cabeçalho do documento e no registro. O id do lote nunca se repete, mesmo depois de um processo encerrado.

---

## 3. Isolamento de premissas: o teste do cabeçalho

As premissas que mudam de um processo para outro e que, trocadas, invalidam o laudo:

| Premissa | Onde vive | Sintoma de contaminação |
|---|---|---|
| Número do processo, juízo e partes | `lote.json`; cabeçalho do laudo | Laudo do P-002 com o nome do autor do P-001 |
| Período do extrato e data de abertura | `caso.json` (`competencia_inicial`); seção 3 do laudo | Reconstrução começa antes do extrato recebido |
| Modalidade de cada saída | `caso.json` (`modalidade` por exercício); seção 5.3 | Saída em folha tratada como saque em caixa, ônus invertido |
| Datas: ciência, último creditamento, propositura, citação | `caso.json`; seção 5.1 | Corte prescricional de outro processo |
| Polo demandado e teses | `lote.json` (`polo_demandado`); seção 6 | Cenários C e D em processo só contra o BB |
| Fatores e séries | `02_calculo/indices/` com data de consulta | Fator de competência diferente da data de citação do processo |
| Quesitos | `03_quesitos/quesitos.json` | Resposta a quesito que ninguém formulou neste processo |

Teste do cabeçalho, feito antes de protocolar: todo quadro colado no laudo (conciliação, cenários, matriz) traz no cabeçalho o número do processo e o id do lote; conferir que os três coincidem com o cabeçalho do laudo. O motor da `pericia-pasep` grava `titular` e `cadastro_pasep` na saída: conferir também esses dois contra a seção 1. Se qualquer um divergir, o arquivo veio da pasta errada e o laudo não sai.

Regra de pasta: nenhum arquivo é copiado de `P-001/` para `P-002/`. O que se reutiliza é o script e o template, nunca o dado.

---

## 4. Controle de versões do laudo e dos esclarecimentos

- A versão protocolada é sempre a última `vN` da pasta `04_laudo/`; rascunhos ficam com sufixo `_rascunho` e não são protocolados.
- Cada versão nova nasce de uma cópia da anterior com um bloco "O que mudou nesta versão" no início da seção 9, datado, com o motivo (retificação em esclarecimentos; documento juntado depois do laudo; erro material apontado).
- Retificação de valor exige nova saída do motor, novo anexo de memória e novo quadro de cenários; não se edita número no texto.
- O registro do lote recebe `--campo versao_laudo=v2` e `--observacao "v2 protocolada: retificado o quadro 6 pelo extrato de fls. 150 a 162"`.
- Esclarecimentos têm numeração própria (`Esclarecimentos_..._v1`), nunca sobrescrevem o laudo e remetem à versão do laudo que esclarecem.

Hash de integridade: ao protocolar, gravar o SHA-256 do arquivo no `--observacao` do registro (`sha256sum arquivo.md`). Serve para demonstrar que o arquivo juntado é o mesmo que ficou na pasta.

---

## 5. Sigilo, LGPD e anonimização

- Base legal do tratamento: Lei 13.709/2018, art. 7º, II e VI. Finalidade única: a perícia naquele processo.
- Pasta do lote em disco com acesso restrito ao perito e, se houver equipe, a quem assinar termo de confidencialidade; nenhum arquivo em serviço de mensagens ou em nuvem sem controle de acesso.
- Extrato, contracheque e microfilmagem não são encaminhados a terceiros fora dos autos, nem ao assistente técnico: ele os obtém nos autos.
- Qualquer uso didático, exemplo de skill, aula ou publicação usa dados anonimizados: processo `0000000-00.0000.0.00.0000`, CPF `000.000.000-00`, cadastro PASEP `0.000.000.000-0`, nomes fictícios e valores alterados. Os assets desta skill seguem esse padrão.
- Processo em segredo de justiça (CPC art. 189): o laudo não circula e o painel do lote indica `segredo` em `observacoes`.
- Descarte: após o trânsito em julgado e o prazo de guarda adotado pelo perito, apagar os dados pessoais e manter só o registro do lote com os campos de identificação mínimos.

---

## 6. Comunicação somente nos autos

- O perito do juízo não se reúne com uma parte sem a outra; diligência presencial (agência do BB, órgão empregador) é comunicada nos autos com cinco dias de antecedência (CPC art. 466, § 2º, e art. 474).
- Mensagem ou documento recebido fora dos autos é juntado por petição no mesmo dia, com a origem declarada; e-mail do assistente técnico com "sugestão" de critério é respondido só nos esclarecimentos.
- Ofício ao BB e solicitação ao autor saem pelos textos do `checklist_documental_pasep.py`, protocolados nos autos, com cópia para as partes; a resposta do BB enviada ao e-mail do perito é juntada.
- Contato com o cartório para andamento (prazo, intimação) é permitido e registrado em `observacoes`.
- Dúvida sobre o objeto ou sobre quesito indeferido vai ao juízo por petição, não às partes.

---

## 7. Prazos: contagem, prorrogação e escusa

- Prazo em dias, fixado por lei ou pelo juiz, conta-se em dias úteis (CPC art. 219) a partir da intimação; o painel conta dias úteis de segunda a sexta sem feriados, por aproximação. A contagem oficial segue o calendário do tribunal.
- Prorrogação: uma vez, pela metade do prazo original, por motivo justificado (CPC art. 476). Pedir antes do vencimento, com o motivo documentado (ofício ao BB sem resposta, extrato parcial, documento do autor não juntado) e com o estado do trabalho.
- Escusa: motivo legítimo em quinze dias da intimação ou do impedimento superveniente (CPC art. 157, § 1º); depois disso, renúncia ao direito de alegar.
- Descumprimento sem motivo: substituição, multa e comunicação à corporação profissional (CPC art. 468).
- Esclarecimentos: quinze dias da intimação (CPC art. 477, § 2º); registrar com `--status esclarecimentos --prazo-esclarecimentos`.
- Audiência: intimação eletrônica com dez dias de antecedência (CPC art. 477, § 4º); quesitos prévios das partes (§ 3º).

---

## 8. Checklist de fechamento por processo

Antes de `--status laudo_entregue`:

1. `selftest.py` da `pericia-pasep` executado no dia, saída zero.
2. Teste do cabeçalho (seção 3) feito em conciliação, cenários e matriz.
3. `matriz_quesitos.py --rigoroso` com cobertura completa; quesito pendente de diligência convertido em resposta com lacuna declarada.
4. Toda saída impugnada com modalidade e estado de comprovação no quadro 5.3; nenhuma saída sem modalidade atribuída pelo perito (fica OUTROS com ressalva).
5. Quadro 6 com os cenários aplicáveis ao polo demandado, cada um com e sem corte prescricional, com a tese rotulada.
6. Nenhuma frase que decida prescrição, legitimidade, ônus ou CDC; busca por "prescrit", "ilegít", "não provou", "abusiv" no texto.
7. Índices com série, código e data de consulta no anexo; nenhum índice sem origem.
8. Precedentes limitados à lista verificada; `[A VERIFICAR]` só na seção de pendências do laudo, nunca no corpo como afirmação.
9. Nome de arquivo no padrão; versão registrada; SHA-256 em `observacoes`.
10. Conversão para `.docx` só se pedida, pela `chelfo-docx-brand`; o protocolado é o PDF gerado dessa versão.

---

## 9. Encerramento no lote

Processo vai a `encerrado` depois dos esclarecimentos, da audiência (se houver) e do levantamento dos honorários finais, ou quando o juízo dispensar o perito. Registrar `--observacao` com a data da decisão que encerrou a participação e o valor final recebido. Processo encerrado continua no registro (histórico completo), sai do painel de prazos e entra no descarte de dados da seção 5 quando o prazo de guarda vencer.
