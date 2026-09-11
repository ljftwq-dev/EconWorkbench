# Roadmap

v1.0 ✅ Triple-implementation crosscheck engine + Callaway & Sant'Anna (2021) replication + bilingual README

v1.1 🔜 **CI template** — fork and run the Python-side crosscheck in GitHub Actions; `pip install econcrosscheck`
v1.2 **`report/`** — unified regression-table exporter: consume the same result CSVs, emit LaTeX / Word three-line (booktabs) tables, Stata `esttab`-style — one command from estimates to submission-ready table

v2.0 **`design/`** — the reviewer checklist, executable: cluster-count lint (warn when clusters < 50 → suggest wild cluster bootstrap), staggered-DiD detection (suggest CS estimator when treatment timing varies), pre-trend pre-flight — an interpretable linter, not a black-box score
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
