# Changelog

## 1.0.0 (12/09/2026)

- Nasce a skill: perícia contábil previdenciária em revisão de benefício do RGPS concedido antes da CF/88 (regime da CLPS, Decreto 89.312/1984), com reconstrução da RMI pelos 36 salários de contribuição e dois valores-teto, equivalência em salários mínimos do art. 58 do ADCT, readequação aos tetos das EC 20/1998 e 41/2003 pelo Tema 1.140 do STJ, diferenças mensais, prescrição quinquenal, decadência informativa, óbito do segurado com conversão em pensão, óbito da pensionista e habilitação de sucessores.
- Scripts em Python 3.11, só biblioteca padrão e `Decimal`: `rmi_clps84.py`, `readequacao_tetos.py` e `atrasados_prescricao.py`, encadeados por JSON e com `parcelas.json` no formato da `atualizacao-monetaria`; coeficientes ORTN/OTN, salário mínimo, tetos, reajustes e cortes de moeda entram por arquivo com fonte; fração do excedente parametrizada com fundamento; teste embutido de diferença zero para benefício não limitado na concessão, demonstrado em segundo exemplo.
- References `fundamentacao-legal.md`, `regime-clps84-e-tetos.md` e `sucessao-processual-e-prescricao.md`; assets com template de laudo, exemplos fictícios de entrada de cada script e exemplo de benefício não limitado; evals com quatro casos.
