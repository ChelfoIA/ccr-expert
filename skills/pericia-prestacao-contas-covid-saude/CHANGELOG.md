# Changelog

## 1.0.0 (12/09/2026)

- Nasce a skill: perícia contábil judicial sobre a aplicação e a prestação de contas de recursos de saúde recebidos para o enfrentamento da covid-19 (FNS fundo a fundo, LC 173/2020, fontes vinculadas), com a fase zero (plano de trabalho, termo de diligência, ofícios, painel de prazos e petições de atraso) tratada como etapa técnica, conciliação por fonte e mês, matriz de testes despesa a despesa e quantificação por classe.
- Scripts em Python 3.11, só biblioteca padrão e `Decimal`: `checklist_documental_covid.py`, `conciliacao_fonte_recurso.py` e `matriz_despesas_covid.py`, com teste de sanidade embutido (soma por fonte e por mês fecha com o total; soma por classe fecha com o universo).
- References `fundamentacao-legal.md`, `roteiro-documental-e-diligencias.md` e `matriz-de-testes-e-red-flags.md`; assets com template de laudo, template de plano de trabalho e exemplos fictícios de entrada; evals com quatro casos.
