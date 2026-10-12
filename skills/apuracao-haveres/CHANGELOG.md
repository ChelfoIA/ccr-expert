# Changelog

## 2.0.0 (12/09/2026)

- Reconstrução pela chelfo-skill-forge (modo forjar) a partir do brief 07, preservando nome e essência: apuração de haveres na dissolução parcial de sociedade (CPC, arts. 599 a 609; CC, arts. 1.028 a 1.031 e 1.085).
- Correções de mérito: data da resolução por hipótese do art. 605 (retirada imotivada no sexagésimo dia após a notificação; recesso no dia do recebimento); fluxo de caixa descontado retirado dos métodos aceitos e recusado pelo script com a jurisprudência do STJ; fundo de comércio mensurado como intangível na data da resolução; lucros, JCP e remuneração até a data (art. 608) com prescrição trienal; correção desde a resolução e juros após o prazo de 90 dias (CC, art. 1.031, § 2º), com atualização delegada à `atualizacao-monetaria` (Lei 14.905/2024) no lugar do "1% ao mês" da v1.
- Scripts reescritos em Python 3.11 com `Decimal`, `argparse`, validação, memória e sanidade: `balanco_determinacao.py`, `fundo_comercio.py` (substitui `calculo_goodwill.py`) e `haveres_socio.py`, que gera `parcelas.json` no formato da `atualizacao-monetaria`; exemplos encadeáveis em `assets/`.
- References substituídas: `fundamentacao-legal.md` (textos verificados dos arts. 602, 604, 605, 606, 608 e 609 do CPC; dez precedentes do STJ verificados em 12/09/2026; pendências), `metodo-balanco-determinacao.md` e `quesitos-e-checklist.md` (funde quesitos_modelo.md e checklist_docs.md); nove precedentes da v1 não conferidos retirados e listados como pendência.
- Novos: template do laudo com exemplo preenchido, `evals/evals.json` com cinco casos, description com gatilhos e diferenciação, integração sistêmica e `RELATORIO_FORJA.md`.

## 1.0.0 (sem data registrada)

- Versão original: SKILL.md de 149 linhas, três scripts em float sem argparse, três references (jurisprudência não verificada, quesitos e checklist), sem assets nem evals.
