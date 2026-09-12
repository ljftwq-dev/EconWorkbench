# EconWorkbench

[![CI](https://github.com/ljftwq-dev/EconWorkbench/actions/workflows/ci.yml/badge.svg)](https://github.com/ljftwq-dev/EconWorkbench/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/econworkbench.svg)](https://pypi.org/project/econworkbench/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[English](README.md) | [中文](README_CN.md)

**From idea to referee-ready — an open workbench for empirical research.**

EconWorkbench covers the empirical-research workflow: literature, design, estimation, **verification**, and reporting. Research judgment stays with you — the workbench makes each step faster and the numbers trustworthy.

```mermaid
flowchart LR
    A[📚 Literature\nL0: cards → gap map] --> B[🌀 Funnel\nidea → spec card]
    B -->|sign G0| C[🚀 econ-pipeline]
    C --> D[⚙️ data → estimate]
    D --> E[🔍 crosscheck\nR vs Python vs Stata]
    E --> F[📋 design lint]
    F --> G[📊 three-line tables]
    G --> H[📝 draft md + LaTeX]
    H --> I[🛡️ data / number / format audits]
    I -->|sign G1| J[✅ referee-ready]
    J -.->|push, forever| K[🔁 CI re-verifies]
```

## Modules at a glance

| Module | CLI | What it does | Since |
|---|---|---|---|
| `crosscheck/` | `econ-crosscheck` | Run the *same* model in **R / Python / Stata**, diff results automatically, one verdict: `bit-exact` / `aligned` / `FAIL` | v1.0 |
| `report/` | `econ-report` | Result CSVs → journal-ready three-line tables (`.tex` / `.docx` / `.png`) in one command | v1.2 |
| `design/` | `econ-design` | Research-design lint before you interpret a single coefficient: few clusters, staggered DiD on TWFE, pre-trends | v2.0 |
| `pipeline/` | `econ-pipeline` | The 11-step spec2paper driver: funnel card in, referee-ready skeleton out — two human gates, stop-on-failure, CI mode | v4.0 |

Every CLI exits 0/1, so any module can gate CI, a Makefile, or an SDD pipeline.

---

# The journey: a paper from zero to referee-ready

Every stage below is real — the transcripts are actual terminal output from a live project (housing prices × retail sales, 2011–2026), and every artifact can be regenerated from `examples/`.

## Stage 0 · Literature first ([docs/literature.md](docs/literature.md))

Before the funnel asks "what's your contribution", you need to know the neighborhood. The L0 protocol: structured search → **5-line literature cards** → a gap map.

```
标题: Housing wealth and consumption
问题: Does housing wealth drive household consumption?
方法: regional panel TWFE + IV (supply shifters)
数据: CFPS 2010-2018, city-level prices
结论: MPC out of housing wealth ≈ 0.05; wealth channel confirmed
缝:   city-level *within-province* variation never exploited; no regime breaks
```

> Topic selection = **gap × data availability × your comparative advantage.** The `缝` ("seam") field of each card is the raw material for the gap map — and the gap map feeds the funnel.

## Stage 1 · The funnel: from one sentence to a spec card ([docs/funnel.md](docs/funnel.md))

The funnel is brainstorming with teeth: *whatever a referee will eventually ask, the funnel asks first.* Four layers — contribution / identification / data availability / robustness budget. Real excerpt:

> **Author**: "I think housing affects consumption differently at different levels."
>
> **Funnel (L1)**: "What does city-level data show that provincial panels cannot?"
> **Author**: "A robustness check that strengthens the main claim."
> **Funnel**: "The referee says 'provincial is enough' — your defense?"
> **Author**: "Provincial aggregation is a weighted average; if transmission is city-level, aggregation introduces attenuation bias that shrinks the coefficient — city-level is the *necessary condition* for testing the identification level."
>
> **Funnel (L2)**: "Time FE: (a) quarter FE or (b) province×quarter FE?"
> **Author**: "(b) — that's what makes it *within-province* variation, matching the paper's level-of-identification story."

Out comes a filled **spec card** (YAML, see [`examples/pipeline_demo/spec_card模板.md`](examples/pipeline_demo/spec_card模板.md)) — including pre-registered branches for every possible outcome, so no post-hoc rationalization:

```yaml
honest_point_三分支: |
  ① city-level significant & negative → upgrade main result
  ② insignificant but |β| ≥ provincial → "attenuation explains the missing significance"
  ③ sign flips → the level narrative dies (declared in advance)
```

**No filled card, no pipeline.** The card is the contract.

## Stage 2 · Sign G0, launch

```bash
pip install econworkbench[pipeline]
econ-pipeline my_paper_card.md
```

Unsigned card? The driver refuses to start:

```
===== gate0 =====
[gate0] PAUSED: waiting for author signature on G0_放行 (topic sign-off)

[STOP] pipeline halted at gate0 (state saved; rerun to resume)
```

The author signs the card (`G0_放行: Your Name 2026-09-12`), reruns the same command — and everything from here to G1 is machine work.

## Stage 3 · Estimate, then crosscheck (v1.0)

Your own code runs the model; the **same model runs again in another language**, and the results are diffed automatically:

<p align="center">
  <img src="assets/triple_crosscheck_cs2021.png" alt="R, Python and Stata terminals side by side reproducing Callaway-Sant'Anna (2021), all showing ATT = -0.0399513" width="880">
</p>

*Live screenshot: Callaway & Sant'Anna (2021) staggered DiD on `mpdta`, run independently in R (`did`), Python (`StatsPAI`), and Stata (`csdid`). All three report Overall ATT = **-0.0399513**.*

The habit catches real bugs. In the project's own structural-break engine, two implementations that each looked fine alone disagreed loudly enough to expose a silent Python backtracking bug and an R `ts()` date mislabel — *before any number reached the draft* ([examples/bai_perron_breakpoints](examples/bai_perron_breakpoints/)):

```
term            RSS_py           RSS_R      |dRSS|  breaks                grade
k=2             18.284462        18.284462   2.13e-14  2020-04;2023-09    bit-exact
RESULT: PASS (bit-exact)   (max |ΔRSS| = 4.3e-14 on all comparable k)
```

## Stage 4 · Design lint (v2.0)

Before interpreting a single coefficient, `econ-design` lints the research design:

```
EconWorkbench design lint | clusters: 70 | timing: unknown
[  OK] CLUSTER  n_clusters=70 >= 50 — asymptotic CRVE acceptable
RESULT: CLEAN
```

Three deterministic rules, each with the fix and the citation: `CLUSTER` (<30 FLAG / 30–49 WARN → wild cluster bootstrap), `STAGGER` (TWFE under staggered adoption → Callaway-Sant'Anna / Sun-Abraham), `PRETREND` (drifting pre-periods → joint test + Rambachan & Roth sensitivity).

## Stage 5 · Journal-ready tables (v1.2)

The same CSVs that passed crosscheck feed the table renderer — one command:

```bash
econ-report r_results.csv py_results.csv --title "Table 1" --out table1
# -> table1.tex (booktabs) + table1.docx (Word three-line) + table1.png
```

<p align="center">
  <img src="examples/cs2021_mpdta/table1.png" alt="Three-line regression table comparing R/Python/Stata estimates" width="620">
</p>

## Stage 6 · Draft skeletons in Markdown *and* LaTeX

The draft step emits two skeletons: Markdown for filling with your assistant, LaTeX for submission (top-5 journals all accept LaTeX; AER ships an official class file):

```
[draft] markdown skeleton -> draft/初稿骨架.md
[draft] LaTeX skeleton -> draft/初稿骨架.tex (compile on Overleaf; \input embeds the table)
```

```latex
\section{识别策略}
% GLM_FILL: identification equation, e.g. TWFE:
\begin{equation}
  y_{it} = \beta \, \mathrm{hp}_{it} + \alpha_i + \lambda_{prov \times t} + \gamma' X_{it} + \varepsilon_{it}
\end{equation}
...
\input{table1}   % the auto-generated three-line table, embedded directly
```

## Stage 7 · The three audits (nothing reaches G1 unverified)

**Data audit** — every CSV in `data/` gets a health check; known-raw wide tables can be exempted on the card, explicitly:

```
house_price_70cities.csv   EXEMPT (card-declared, hand-verified)
panel_final.csv            1740 rows x 7 cols
[data_audit] OK: 13 CSVs pass (1 exempt)
```

**Number audit (statcheck-style)** — every number in the draft must trace back to `results/`, either as an original value **or a recomputed one** (est/se → t, normal approx → p). Fabricated numbers halt the pipeline. This actually happened during testing:

```
draft said: "coefficient -0.103 (t = 1.1, p is 0.27); also a made-up t = 9.99"
[number_check] FAIL: 1 number(s) not traceable — halting:
      orphans: 9.99
```

(-0.103 traced to the CSV; t = 1.1 and p = 0.27 were *recomputed* from est/se and let through; 9.99 exists nowhere → halt. Threshold idioms like `p < .05` are exempt.)

**Format audit** — the final docx is linted for font uniformity, Heading styles, table presence; only files named `成稿*`/`final*` are audited, so intermediate drafts aren't nagged.

## Stage 8 · Sign G1 — and stay green forever

The author signs `G1_放行`, and the pipeline delivers. Then drop [`examples/pipeline_demo/ci-driver.yml`](examples/pipeline_demo/ci-driver.yml) into the paper's repo: every `git push` re-runs the whole chain on GitHub Actions — gates awaiting signature count as green, any real failure turns red. Your paper is now a repo that *proves itself* on every push (showyourwork-style continuous verification).

---

## Why

AI agents write most of our econometrics code now. But an LLM that writes the wrong `vcov` in two languages — consistently — will hand you confident nonsense. The fix is older than LLMs: **independent implementations of the same estimator should agree.**

- R's `did` (Callaway et al.), Stata's `csdid` (Sant'Anna et al.), and Python ports are written by different teams. Same data + same model + same numbers = implementation is clean.
- One run, one number, no cross-check = you cannot tell a result from a bug.

This is the "double-entry bookkeeping" for regressions — inspired by a 2026 lecture series on AI agents for social-science research, and by the [StatsPAI](https://github.com/brycewang-stanford/StatsPAI) parity index. The number audit borrows from [statcheck](https://github.com/MicheleNuijten/statcheck) ("a spellchecker for statistics"); the CI posture borrows from [showyourwork](https://github.com/showyourwork/showyourwork).

## Verdicts

| Verdict | Meaning | Default tolerance |
|---|---|---|
| `bit-exact` | Machine-precision agreement | Δ ≤ 1e-10 |
| `aligned` | Agreement within tolerance | Δcoef ≤ 1e-6, ΔSE/SE ≤ 1e-4, Δp ≤ 1e-4 |
| `FAIL` | Significance flips or tolerance breached | — exit code 1 |

## Examples

- [`examples/cs2021_mpdta/`](examples/cs2021_mpdta/) — Callaway & Sant'Anna (2021) replicated three ways; R↔Python bit-exact on all 8 quantities, R↔Stata aligned (Δ≈1e-7), overall ATT matches the published paper.
- [`examples/bai_perron_breakpoints/`](examples/bai_perron_breakpoints/) — hand-rolled exact-DP Bai-Perron vs `strucchange`: PASS (bit-exact) after the comparison itself caught two real bugs.
- [`examples/design_demo/`](examples/design_demo/) — the bad study trips all three lint rules; the good one comes back CLEAN.
- [`examples/pipeline_demo/`](examples/pipeline_demo/) — a runnable pipeline card + CI template. Full transcripts of a real run: [docs/showcase.md](docs/showcase.md).

## What it does *not* do

- It cannot validate your **identification strategy** — two implementations of a wrong model agree perfectly. `design/` lints the common reviewer checklist; identification judgment stays with you.
- It is not a paper factory. The funnel only asks questions; the gates only accept human signatures. Batch production and auto-submission are explicitly out of scope.

## Related work

- [StatsPAI](https://github.com/brycewang-stanford/StatsPAI) — agent-native Stata/R replacement with a queryable parity index.
- [statcheck](https://github.com/MicheleNuijten/statcheck) — the spellchecker for statistics; our number audit is a descendant.
- [showyourwork](https://github.com/showyourwork/showyourwork) — reproducible-article workflows; our CI posture is a descendant.
- Sakana AI-Scientist, Agent Laboratory — end-to-end "AI scientist" pipelines (the opposite bet: automation over verification).

## License

MIT
