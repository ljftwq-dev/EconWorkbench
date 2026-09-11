# -*- coding: utf-8 -*-
"""
crosscheck.py — 计量交叉验证对拍引擎 v2（支持 2~N 份实现，三重验证就传三份 CSV）
借鉴 StatsPAI parity 分级: bit-exact(机器精度) / aligned(容差内) / FAIL(不一致)

输入: 每份实现一个标准化结果 CSV (列: term,estimate,se,pvalue)
      用法: python crosscheck.py r.csv py.csv [stata.csv ...] [--tol-coef 1e-6 --tol-se 1e-4 --tol-p 1e-4]
      第一个 CSV 为基准(建议 R 官方包), 其余各份与基准对拍
输出: 分级对拍矩阵 + 汇总; 退出码 0=全PASS 1=存在FAIL
"""
import sys, csv, argparse, itertools, os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ap = argparse.ArgumentParser()
ap.add_argument("csvs", nargs="+", help="2~N 份结果 CSV, 第一份为基准")
ap.add_argument("--tol-coef", type=float, default=1e-6)
ap.add_argument("--tol-se", type=float, default=1e-4)
ap.add_argument("--tol-p", type=float, default=1e-4)
ap.add_argument("--tol-exact", type=float, default=1e-10, help="bit-exact 判定阈值(机器精度级)")
args = ap.parse_args()

if len(args.csvs) < 2:
    print("[FAIL] 至少需要两份 CSV"); sys.exit(1)


def load(path):
    rows = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            t = r["term"].strip()
            rows[t] = (float(r["estimate"]), float(r["se"]), float(r["pvalue"]))
    return rows


names = [os.path.splitext(os.path.basename(p))[0] for p in args.csvs]
data = [load(p) for p in args.csvs]

# term 集合检查
base_terms = set(data[0])
for i in range(1, len(data)):
    other = set(data[i])
    if base_terms != other:
        print(f"[WARN] {names[0]} 与 {names[i]} term 集合不一致: 仅基准有 {sorted(base_terms-other)} | 仅{names[i]}有 {sorted(other-base_terms)}")
common = sorted(base_terms & set.intersection(*[set(d) for d in data[1:]]))
if not common:
    print("[FAIL] 无共同 term"); sys.exit(1)

GRADES = {"bit-exact": 0, "aligned": 1, "FAIL": 2}


def grade(er, sr, pr, ep, sp, pp):
    dc = abs(er - ep)
    ds = abs(sr - sp) / max(sr, 1e-12)
    dp = abs(pr - pp)
    if not (pr < 0.05) == (pp < 0.05):
        return "FAIL", dc, ds, dp
    if dc > args.tol_coef or dp > args.tol_p:
        return "FAIL", dc, ds, dp
    if dc <= args.tol_exact and ds <= args.tol_exact and dp <= args.tol_exact:
        return "bit-exact", dc, ds, dp
    if ds > args.tol_se:
        return "FAIL", dc, ds, dp
    return "aligned", dc, ds, dp


pairs = [(0, i) for i in range(1, len(data))]
print(f"基准: {names[0]} | 对拍: {[names[i] for _, i in pairs]}")
hdr = f"{'term':<24}" + "".join(f"{names[0]}vs{names[i]:<10}" for _, i in pairs)
print(hdr); print("-" * (24 + 20 * len(pairs)))

worst = 0
for t in common:
    cells = []
    for b, i in pairs:
        g, dc, ds, dp = grade(*data[b][t], *data[i][t])
        worst = max(worst, GRADES[g])
        cells.append(g)
    print(f"{t:<24}" + "".join(f"{c:<20}" for c in cells))

print("-" * (24 + 20 * len(pairs)))
for b, i in pairs:
    stats = {"bit-exact": 0, "aligned": 0, "FAIL": 0}
    for t in common:
        g, *_ = grade(*data[b][t], *data[i][t])
        stats[g] += 1
    print(f"{names[0]} vs {names[i]}: bit-exact {stats['bit-exact']} | aligned {stats['aligned']} | FAIL {stats['FAIL']} (共{len(common)})")

if worst == GRADES["FAIL"]:
    print("\nRESULT: FAIL — 停止解读结果, 排查样本筛选/权重/聚类层级/vcov 设定差异后再跑")
    sys.exit(1)
lvl = "bit-exact" if worst == 0 else "aligned"
print(f"\nRESULT: PASS ({lvl}) — 全部实现对拍一致 (bit-exact=机器精度级, aligned=容差内); 仍需人工检查设定是否正确")
sys.exit(0)
