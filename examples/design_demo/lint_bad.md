# EconWorkbench design lint

`EconWorkbench design lint | script: examples/design_demo/bad_study.do | results: events_bad.csv | clusters: 12 | timing: staggered`

```
[FLAG] CLUSTER  n_clusters=12 < 30 — cluster-robust SEs unreliable (over-rejection)
              -> wild cluster bootstrap (Rademacher weights): Stata `boottest`, R `fwildclusterboot`, Python `wildboottestgas`
              -> Cameron, Gelbach & Miller (2008), Rev. Econ. Stat. 90(3)
[FLAG] STAGGER  TWFE regression under staggered adoption — already-treated units act as controls; OLS weights can be negative
              -> switch to Callaway-Sant'Anna (csdid / did::att_gt), Sun-Abraham (eventstudyinteract / sunab), or Borusyak et al. (didimputation)
              -> Goodman-Bacon (2021), J. Econometrics 225(2); Sun & Abraham (2021), J. Econometrics 225(2)
[FLAG] PRETREND 2/4 pre-period coefficients individually significant at 5% (rel_-2, rel_-1)
              -> report the joint pre-trend test; consider Rambachan-Roth (2023) honest sensitivity to violations of parallel trends
              -> Roth (2022), AER: Insights 4(3); Rambachan & Roth (2023), Rev. Econ. Stud. 90(5)
[FLAG] PRETREND joint pre-trend Wald chi2 = 25.87 > 95% critical 9.49 (df=4) — parallel trends rejected
              -> Rambachan & Roth (2023) sensitivity analysis; re-examine the identifying assumption
              -> Roth (2022), AER: Insights 4(3)
[WARN] PRETREND monotone drift: estimates move in one direction for 3 consecutive steps
              -> a trend can hide inside joint tests with low power — plot the event study
              -> Roth (2022), AER: Insights 4(3)
```
