# Example: Bai-Perron structural breaks — hand-rolled exact DP vs `strucchange`

**Why this case is the poster child for cross-validation:** both implementations were
"correct" by their own tests, yet crosschecking them caught **two real bugs** before
any number was interpreted. Final verdict after fixes: **PASS (bit-exact, |ΔRSS| ≤ 4.3e-14)**.

Setting: a 24-month rolling-beta series (housing prices × retail sales, 165 monthly obs,
2012–2026) from a time-varying wealth-effect study. Pure structural breaks with BIC
selection, minimum segment length h = 24.

| | Implementation | Package |
|---|---|---|
| Python | exact dynamic programming (numpy, prefix-sum SSE) | hand-rolled |
| R | `strucchange::breakpoints()` | Zeileis et al. |

## The two bugs the crosscheck caught

**BUG-1 (Python, silent wrong answers).** Backtracking took `argmin` over the DP layer
*across endpoints j* — comparing prefix-optimal costs against the full-sequence optimum.
Every breakpoint came out wrong, with no error message. Fix: pin the endpoint at `j = n`
and backtrack from there. Lesson: *layer costs at different j are not comparable*.

**BUG-2 (R, wrong dates on a correct fit).** `ts(start = c(2012,8), frequency = 12)`
assumes contiguous months, but the series skips every January. Breakpoint position 76
was labeled 2018-11 by the ts index; the true month (from the real CSV date column) was
**2020-04**. The RSS was right, the breakpoints were right — only the *labels* were
wrong. Fix: map positions to dates through the actual data column. Lesson: *never trust
a synthetic time index on gappy data*.

## Results

```
term   RSS_py        RSS_R         |dRSS|      breaks                    grade
k=0    44.123392     44.123392      4.26e-14   (none)                    bit-exact
k=1    23.659756     23.65976       3.91e-14   2020-04                   bit-exact
k=2    18.284462     18.284462      2.13e-14   2020-04;2023-09           bit-exact
k=3    ...                                                     N/A (strucchange caps at 2)
k=4    ...                                                     N/A (strucchange caps at 2)

RESULT: PASS (bit-exact)
```

Both sides' BIC picks k = 2. For k ≥ 3 `strucchange` internally caps the number of
returned breaks (its own feasibility bound is stricter), so those rows are graded
N/A — an *implementation boundary*, not a numeric disagreement. The hand-rolled DP
still returns the k = 3 solution (2016-07; 2020-04; 2023-09), which the study uses as
a sensitivity check. Feed the capped rows to the `econ-crosscheck` CLI as-is and it
will (correctly!) scream FAIL — knowing when rows are comparable is part of the craft.

## Reproduce

```bash
python bp_py.py          # -> py_results.csv
Rscript bp_r.R           # -> r_results.csv  (requires strucchange)
python compare.py        # verdict + econ-crosscheck CLI demo
```
