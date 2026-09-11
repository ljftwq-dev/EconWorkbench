# EconWorkbench

[![CI](https://github.com/ljftwq-dev/EconWorkbench/actions/workflows/ci.yml/badge.svg)](https://github.com/ljftwq-dev/EconWorkbench/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/econworkbench.svg)](https://pypi.org/project/econworkbench/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[English](README.md) | [中文](README_CN.md)

**From idea to referee-ready — an open workbench for empirical research.**

EconWorkbench is a toolkit for the empirical-research workflow: literature, data, design, estimation, **verification**, and reporting. Research judgment stays with you — the workbench makes each step faster and the numbers trustworthy.

**v1.0 ships the core: `crosscheck/`** — run the *same* model in **R, Python, and Stata**, then diff the results automatically. If the numbers agree, your code is (almost certainly) right. If they don't, you stop interpreting — before a reviewer (or a referee report) stops you.

**v2.0 adds `design/`** — the reviewer checklist, executable. Lint your research design (few clusters, staggered DiD on TWFE, pre-trends) before you interpret a single coefficient.

<p align="center">
  <img src="assets/triple_crosscheck_cs2021.png" alt="R, Python and Stata terminals side by side reproducing Callaway-Sant'Anna (2021), all showing ATT = -0.0399513" width="900">
</p>

*Live screenshot: Callaway & Sant'Anna (2021) staggered DiD on `mpdta`, run independently in R (`did`), Python (`StatsPAI`), and Stata (`csdid`). All three report Overall ATT = **-0.0399513**.*

## Why

AI agents write most of our econometrics code now. But an LLM that writes the wrong `vcov` in two languages — consistently — will hand you confident nonsense. The fix is older than LLMs: **independent implementations of the same estimator should agree**.

- R's `did` (Callaway et al.), Stata's `csdid` (Sant'Anna et al.), and Python ports are written by different teams. Same data + same model + same numbers = implementation is clean.
- One run, one number, no cross-check = you cannot tell a result from a bug.

This is the "double-entry bookkeeping" for regressions — inspired by a 2026 lecture series on AI agents for social-science research (where the speaker, priced out of Stata licenses, could only cross-check R vs Python), and by the [StatsPAI](https://github.com/brycewang-stanford/StatsPAI) parity index, which grades its own estimators against R/Stata references.

## Quick start

Core is zero-dependency (pure stdlib):

```
pip install econworkbench        # or: pip install .[report] for tables

# 1. Run the same model in R / Python / Stata; each script writes a 4-column CSV:
#    term, estimate, se, pvalue
Rscript my_model.R            # -> r_results.csv
python  my_model.py           # -> py_results.csv
"C:\Program Files\Stata19\StataSE-64.exe" /e do my_model.do   # -> stata_results.csv

# 2. Diff them (first CSV is the reference):
econ-crosscheck r_results.csv py_results.csv stata_results.csv
```

Output:

```
term                    r_resultsvspy_resultsr_resultsvsstata_results
--------------------------------------------------------------------
g2004_t2004             bit-exact           aligned
...
overall_simple          bit-exact           aligned
--------------------------------------------------------------------
r_results vs py_results: bit-exact 8 | aligned 0 | FAIL 0
r_results vs stata_results: bit-exact 0 | aligned 8 | FAIL 0
RESULT: PASS (aligned) — exit code 0
```

## Verdicts

| Verdict | Meaning | Default tolerance |
|---|---|---|
| `bit-exact` | Machine-precision agreement | Δ ≤ 1e-10 |
| `aligned` | Agreement within tolerance | Δcoef ≤ 1e-6, ΔSE/SE ≤ 1e-4, Δp ≤ 1e-4 |
| `FAIL` | Significance flips or tolerance breached | — exit code 1 |

Exit codes make it gate-able: wire it into CI, a Makefile, or your SDD pipeline as a release gate.

## Example: Callaway & Sant'Anna (2021) replication

[`examples/cs2021_mpdta/`](examples/cs2021_mpdta/) replicates the canonical staggered-DiD application (minimum-wage effects on teen employment, 2,500 county-year obs) three ways:

| | Implementation | Authors' own package |
|---|---|---|
| R 4.6.1 | `did::att_gt()` + `aggte()` | Callaway & Sant'Anna |
| Python 3.14 | `StatsPAI.callaway_santanna()` | port with its own parity evidence |
| StataNow 19.5 | `csdid` + `csdid_estat simple` | Sant'Anna, Goodman-Bacon & Pedro |

Result: **R ↔ Python bit-exact on all 8 quantities** (7 post-period ATT(g,t) + overall); **R ↔ Stata aligned** (Δ ≈ 1e-7, different DR-IPW optimizers). Overall ATT = -0.0399 matches the published paper.

Run it yourself: each folder contains the three scripts, the shared dataset (`mpdta_data.csv` — one source of truth, all three languages read the same file), and the three result CSVs.

## From estimates to tables (`report/`, v1.2)

The same CSVs that feed `crosscheck` also feed `report` — one command from estimates to a journal-ready three-line table:

```
econ-report r_results.csv py_results.csv stata_results.csv --title "Table 1" --out table1
# -> table1.tex (booktabs) + table1.docx (Word three-line) + table1.png (preview)
```

<p align="center">
  <img src="examples/cs2021_mpdta/table1.png" alt="Three-line regression table comparing R/Python/Stata estimates" width="640">
</p>

Significance stars, SEs in parentheses, top/mid/bottom rules — in all three formats. Column labels sit at the bottom, `esttab`-style.

## Catch design flaws before the referee does (`design/`, v2.0)

`crosscheck` validates your *code*; `design` lints your *research design*. Point it at your Stata/R/Python script and/or an event-study CSV:

```
econ-design --script my_study.do --n-clusters 12 --treatment staggered --results events.csv
# exit 0 = clean (WARN allowed), exit 1 = FLAG found — gate-able like crosscheck
```

Three deterministic, interpretable rules — a linter, not a black-box score. Every finding names the fix and the citation:

| Rule | Triggers on | Recommends |
|---|---|---|
| `CLUSTER` | <30 clusters FLAG, 30-49 WARN | wild cluster bootstrap (Rademacher) — Cameron, Gelbach & Miller (2008) |
| `STAGGER` | TWFE regression under staggered adoption (no csdid/att_gt/sunab found) | Callaway-Sant'Anna / Sun-Abraham — Goodman-Bacon (2021) |
| `PRETREND` | pre-period coefficients individually / jointly significant, or monotone drift | joint test + Rambachan & Roth (2023) sensitivity — Roth (2022) |

The bad study in [`examples/design_demo/`](examples/design_demo/) trips all three rules at once; the good study (csdid + boottest, 230 clusters) comes back CLEAN. Run both to see the lint in action.

## What it does *not* do

- It cannot validate your **identification strategy** — two implementations of a wrong model agree perfectly. `design/` lints the common reviewer checklist (clustering, staggered timing, pre-trends), but identification judgment stays with you.
- It is not a paper factory. Judgment stays with the researcher.

## Related work

- [StatsPAI](https://github.com/brycewang-stanford/StatsPAI) — agent-native Stata/R replacement with a queryable parity index (a superset of this idea, inside one library).
- Sakana AI-Scientist, Agent Laboratory — end-to-end "AI scientist" pipelines (the opposite bet: automation over verification).

## License

MIT
