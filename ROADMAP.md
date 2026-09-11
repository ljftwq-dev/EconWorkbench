# Roadmap

v1.0 ✅ Triple-implementation crosscheck engine + Callaway & Sant'Anna (2021) replication + bilingual README

v1.1 ✅ pip-installable package (`econ-crosscheck` / `econ-report` CLIs) + GitHub Actions CI (positive & negative smoke tests)
v1.2 ✅ **`report/`** — unified regression-table exporter: LaTeX / Word three-line (booktabs) tables, PNG preview — one command from estimates to submission-ready table; **published to PyPI as `econworkbench` 1.2.0**

v2.0 ✅ **`design/`** — the reviewer checklist, executable: cluster-count lint (FLAG <30 / WARN <50 → wild cluster bootstrap), staggered-DiD detection (FLAG TWFE under staggered adoption → CS/SA estimators), pre-trend pre-flight (individual + joint chi2 + monotone drift) — every finding carries the fix and the citation; `econ-design` CLI; published as 2.0.0
v2.1 **`lit/`** — NBER / SSRN / RePEc search wrappers to close the social-science literature gap (arXiv coverage is STEM-only)
v2.2 **`data/`** — CFPS / CHFS ingestion pipelines (pipes only, never the data — respect licenses)

v3.0 **Integration validation** — one real paper (housing-market index × domestic demand, time-varying relationship) driven through the full chain: idea → literature → data → design → estimation → crosscheck → review → writing

## How we differ

- vs. end-to-end "AI scientists" (Sakana AI-Scientist, Agent Laboratory): they bet on **generation**; we bet on **verification**. Their pipelines produce papers nobody can trust without the checks we provide.
- vs. StatsPAI: they are a 350k-LOC library replacing Stata/R; we are a **small, embeddable component** — keep your Stata workflow, add the crosscheck.
- Research judgment (taste, identification strategy) stays with the researcher. We are a quality gate, not a paper factory.

## Non-goals

- Fully autonomous paper generation.
- Validating identification strategies (two implementations of a wrong model agree perfectly).
- Shipping any dataset we do not own.
