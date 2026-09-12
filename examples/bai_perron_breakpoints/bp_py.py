# -*- coding: utf-8 -*-
"""bp_py.py — Bai-Perron pure structural breaks, hand-rolled exact DP (numpy)
Estimates breakpoints on a rolling-beta series (from housing x retail research),
k = 0..4, min segment size 24. Writes py_results.csv in crosscheck contract:
  term, estimate(RSS), se(0), pvalue(0), breaks(date list), bic
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import pandas as pd


def bai_perron_fixed(x, k, min_size=24):
    """Exact DP for a fixed number of breaks (l2/SSE objective = Bai-Perron pure breaks).
    Backtracking pins the endpoint at j = n (see BUG-1 note in README)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    c = np.concatenate([[0.0], np.cumsum(x)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x)])

    def sse(i, j):  # SSE of segment [i, j)
        s = c[j] - c[i]
        return c2[j] - c2[i] - s * s / (j - i)

    layers = [({j: sse(0, j) for j in range(min_size, n + 1)}, {})]
    for kk in range(1, k + 1):
        prev_cost = layers[kk - 1][0]
        cur_cost, cur_choice = {}, {}
        for j in range((kk + 1) * min_size, n + 1):
            bestv, besti = np.inf, None
            for i, ci in prev_cost.items():
                if i <= j - min_size:
                    v = ci + sse(i, j)
                    if v < bestv:
                        bestv, besti = v, i
            if besti is not None:
                cur_cost[j], cur_choice[j] = bestv, besti
        layers.append((cur_cost, cur_choice))
    if len(layers) <= k or n not in layers[k][0]:
        return []
    j = n  # BUG-1 fix: endpoint pinned at n; cross-j argmin silently drops the tail
    bkps = []
    for kk in range(k, 0, -1):
        i = layers[kk][1][j]
        bkps.append(i)
        j = i
    return sorted(bkps)


d = pd.read_csv("rb_series.csv")
x = d["beta"].values.astype(float)
n = len(x)
dates = [str(s)[:7] for s in d["date"]]

rows = []
for k in range(0, 5):
    if k == 0:
        rss = float(((x - x.mean()) ** 2).sum())
        bk = []
    else:
        bk = bai_perron_fixed(x, k, min_size=24)
        segs = np.split(np.arange(n), bk)
        rss = float(sum(((x[s] - x[s].mean()) ** 2).sum() for s in segs))
    bic = n * np.log(rss / n) + ((k + 1) + k) * np.log(n)
    rows.append({"term": f"k={k}", "estimate": rss, "se": 0.0, "pvalue": 0.0,
                 "breaks": ";".join(dates[i] for i in bk), "bic": bic})

out = pd.DataFrame(rows)
out.to_csv("py_results.csv", index=False)
print(out.to_string(index=False))
print("Py done")
