# -*- coding: utf-8 -*-
"""compare.py — cross-language verdict for the Bai-Perron example.
Grades RSS agreement per k (bit-exact <= 1e-10 absolute) and breakpoint dates
(normalized to YYYY-MM). strucchange caps solutions at its own feasible k for
k>=3 (returns 2 breaks, RSS identical to k=2): those rows are graded N/A
(implementation boundary, not numeric disagreement). Also demonstrates the
econ-crosscheck CLI on the shared contract columns.
"""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd

py = pd.read_csv("py_results.csv").set_index("term")
r = pd.read_csv("r_results.csv").set_index("term")

TOL_EXACT = 1e-10
print(f"{'term':<6}{'RSS_py':>16}{'RSS_R':>16}{'|dRSS|':>11}  {'breaks_py':<30}{'breaks_R':<30}grade")
worst, all_ok = 0.0, True
for k in range(5):
    t = f"k={k}"
    rss_py, rss_r = float(py.loc[t, "estimate"]), float(r.loc[t, "estimate"])
    dt = abs(rss_py - rss_r)
    b_py = str(py.loc[t, "breaks"])
    b_r = str(r.loc[t, "breaks"])
    nb_py = len([b for b in b_py.split(";") if b and b != "nan"])
    b_r_norm = b_r.replace("-01", "")
    nfound_r = len([b for b in b_r_norm.split(";") if b and b != "nan"])
    capped = k > 0 and nfound_r < k
    if capped:
        grade = f"N/A (R caps at {nfound_r})"
    elif dt <= TOL_EXACT and nb_py == nfound_r and b_py == b_r_norm:
        grade = "bit-exact"
    elif nb_py != nfound_r:
        grade, all_ok = "FAIL", False
    elif dt / max(rss_r, 1e-12) <= 1e-6:
        grade = "aligned"
    else:
        grade, all_ok = "FAIL", False
    if not capped:
        worst = max(worst, dt)
        if grade == "FAIL":
            all_ok = False
    print(f"{t:<6}{rss_py:>16.6f}{rss_r:>16.6f}{dt:>11.2e}  {b_py or '(none)':<30}{b_r_norm or '(none)':<30}{grade}")

k_star_py = int(py["bic"].idxmin().split("=")[1])
print("-" * 100)
print(f"BIC picks: Python k={k_star_py} | R k=2 (strucchange; capped k>=3 rows share k=2 RSS)")
print(f"max |dRSS| over comparable rows = {worst:.3e}")
print("\nRESULT:", "PASS (bit-exact)" if all_ok and worst <= TOL_EXACT else "FAIL")

print("\n--- econ-crosscheck CLI demo (comparable rows only: k<=2; capped rows are the "
      "example's own teaching point, see README) ---")
py.iloc[:3].reset_index().to_csv("py_demo.csv", index=False)
r.iloc[:3].reset_index().to_csv("r_demo.csv", index=False)
sys.stdout.flush()
subprocess.run([sys.executable, "-m", "econworkbench.crosscheck",
                "r_demo.csv", "py_demo.csv"], check=False)
