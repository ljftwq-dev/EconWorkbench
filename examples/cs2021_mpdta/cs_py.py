# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import re
import pandas as pd
import statspai as sp

d = pd.read_csv("mpdta_data.csv").rename(columns={"first.treat": "first_treat"})
gt = sp.callaway_santanna(data=d, y="lemp", t="year", i="countyreal", g="first_treat")
agg = sp.aggte(gt, type="simple", bstrap=False)

t = gt.tidy()
term_raw = t["term"]
est = t["estimate"]
se = t["std_error"]
pval = t["p_value"]

rows = []
for tr, e, s, p in zip(term_raw, est, se, pval):
    m = re.match(r"att\(g=(\d+)\.0,t=(\d+)\.0\)", str(tr))
    if not m:
        continue
    g, tt = int(m.group(1)), int(m.group(2))
    if tt >= g:  # 只取 post 期(约定一致区)
        rows.append((f"g{g}_t{tt}", e, s, p))
rows.append(("overall_simple", float(agg.estimate), float(agg.se),
             float(getattr(agg, "pvalue", float("nan")))))

out = pd.DataFrame(rows, columns=["term", "estimate", "se", "pvalue"])
out.to_csv("py_results.csv", index=False)
print("Py done:", len(out), "rows")
print(out.to_string(index=False))
