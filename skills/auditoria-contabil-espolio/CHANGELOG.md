# Changelog

## 1.0.0 (12/09/2026)

- Nasce a skill: auditoria contábil e perícia sobre a administração do espólio desde a abertura da sucessão, com fluxo de caixa por conta, mês e categoria, listas de exceção (sem alvará, sem documento, em favor de herdeiro ou inventariante, despesa estranha ao espólio), frutos de cada imóvel, aluguel devido por herdeiro ocupante com marco parametrizado, bens em Portugal convertidos pela PTAX por arquivo e quadro por sociedade de capital fechado.
- Scripts em Python 3.11, só biblioteca padrão e `Decimal`: `fluxo_caixa_espolio.py` (sanidade: entradas menos saídas igual à variação do saldo; conciliação com o extrato), `rendimentos_imoveis.py` (sanidade: soma mensal igual a base x meses; ocupante: mercado x (1 - fração) x meses) e `conversao_ptax.py` (cotação do dia ou do dia útil anterior declarada; nunca estima; sem rede).
- References `fundamentacao-legal.md` (onze precedentes verificados do STJ com links), `roteiro-auditoria-e-documentos.md` e `imoveis-empresas-e-exterior.md`; assets com template de laudo, exemplos fictícios de entrada dos três scripts e layout do quadro de sociedades; evals com cinco casos.
