# Changelog

## 1.0.0 (12/09/2026)

- Nasce a skill: condução da perícia contábil judicial do PASEP pelo perito do juízo (CPC arts. 464 a 480; NBC TP 01), inclusive em lote de vários processos, com laudo imparcial que apresenta cenários rotulados por tese (polo, prescrição, modalidade do Tema 1.300/STJ) sem decidir, e aponta para a `pericia-pasep` em todo cálculo.
- Scripts de organização em Python 3.11, só biblioteca padrão e sem cálculo monetário: `lote_pasep.py` (criar, adicionar, atualizar, painel), `checklist_documental_pasep.py` (faltantes por modalidade, termo de diligência, ofício ao BB) e `matriz_quesitos.py` (tema, tipo, seção, evidência, cenário, cobertura).
- References `fundamentacao-legal.md`, `conducao-do-lote.md` e `laudo-e-quesitos.md`; jurisprudência reutilizada da `pericia-pasep` com identificação idêntica (Temas 545, 1.150 e 1.300 do STJ, Súmula 85/STJ, STF Tema 810), sem precedente novo; assets com template do laudo e exemplos fictícios; evals com quatro casos.
