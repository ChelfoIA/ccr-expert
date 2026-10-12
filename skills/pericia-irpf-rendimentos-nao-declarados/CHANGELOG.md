# Changelog

## 1.0.0 (12/09/2026)

- Nasce a skill: perícia contábil em cobrança de IRPF por rendimentos não declarados (lançamento a partir de DIRF e fontes pagadoras, depósitos de origem não comprovada do art. 42 da Lei 9.430/1996 e acréscimo patrimonial a descoberto), com classificação crédito a crédito da natureza e da prova da origem, exclusões do § 3º e conta conjunta do § 6º, recálculo do imposto em modo anual e mensal, encargos do auto e decadência por ano.
- Scripts em Python 3.11, só biblioteca padrão e `Decimal`: `classificar_rendimentos.py`, `recalculo_irpf.py` e `encargos_auto_infracao.py`, encadeados por JSON, com sanidade embutida (soma das classes igual ao total imputado; imposto por fatias igual ao da fórmula; total igual a principal mais multa mais juros). Tabela progressiva, limites de dedução e série Selic entram por arquivo com fonte; o script aborta se faltarem.
- References `fundamentacao-legal.md`, `natureza-dos-rendimentos.md` e `roteiro-probatorio-e-quesitos.md`; assets com template de laudo e exemplos fictícios de entrada; evals com quatro casos.
