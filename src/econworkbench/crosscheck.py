# -*- coding: utf-8 -*-
"""
crosscheck.py — EconWorkbench core: cross-language validation engine
One estimator, independent implementations, one verdict.
Supports 2~N implementations (R / Python / Stata / ...); first CSV is the reference.
Grades (StatsPAI-style): bit-exact (<=1e-10) / aligned (tolerance) / FAIL.
Exit code 0 = PASS, 1 = FAIL (gate-able in CI / Makefile / SDD pipelines).
"""
import sys, csv, argparse, os


def build_parser():
    ap = argparse.ArgumentParser(
        prog="econ-crosscheck",
        description="Cross-validate 2~N result CSVs (columns: term,estimate,se,pvalue). First CSV is the reference.")
    ap.add_argument("csvs", nargs="+", help="2~N result CSVs, first is the reference")
    ap.add_argument("--tol-coef", type=float, default=1e-6)
    ap.add_argument("--tol-se", type=float, default=1e-4)
    ap.add_argument("--tol-p", type=float, default=1e-4)
    ap.add_argument("--tol-exact", type=float, default=1e-10, help="bit-exact threshold (machine precision)")
    return ap


GRADES = {"bit-exact": 0, "aligned": 1, "FAIL": 2}


def load(path):
    rows = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            t = r["term"].strip()
            rows[t] = (float(r["estimate"]), float(r["se"]), float(r["pvalue"]))
    return rows


def grade(er, sr, pr, ep, sp, pp, args):
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


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = build_parser()
    args = ap.parse_args(argv)

    if len(args.csvs) < 2:
        print("[FAIL] at least two CSVs are required")
        return 1

    names = [os.path.splitext(os.path.basename(p))[0] for p in args.csvs]
    data = [load(p) for p in args.csvs]

    base_terms = set(data[0])
    for i in range(1, len(data)):
        other = set(data[i])
        if base_terms != other:
            print(f"[WARN] {names[0]} vs {names[i]} term sets differ: "
                  f"ref-only {sorted(base_terms - other)} | {names[i]}-only {sorted(other - base_terms)}")
    common = sorted(base_terms & set.intersection(*[set(d) for d in data[1:]]))
    if not common:
        print("[FAIL] no common terms")
        return 1

    pairs = [(0, i) for i in range(1, len(data))]
    print(f"reference: {names[0]} | checking: {[names[i] for _, i in pairs]}")
    print(f"{'term':<24}" + "".join(f"{names[0]}vs{names[i]:<10}" for _, i in pairs))
    print("-" * (24 + 20 * len(pairs)))

    worst = 0
    for t in common:
        cells = []
        for b, i in pairs:
            g, dc, ds, dp = grade(*data[b][t], *data[i][t], args)
            worst = max(worst, GRADES[g])
            cells.append(g)
        print(f"{t:<24}" + "".join(f"{c:<20}" for c in cells))

    print("-" * (24 + 20 * len(pairs)))
    for b, i in pairs:
        stats = {"bit-exact": 0, "aligned": 0, "FAIL": 0}
        for t in common:
            g, *_ = grade(*data[b][t], *data[i][t], args)
            stats[g] += 1
        print(f"{names[0]} vs {names[i]}: bit-exact {stats['bit-exact']} | "
              f"aligned {stats['aligned']} | FAIL {stats['FAIL']} (of {len(common)})")

    if worst == GRADES["FAIL"]:
        print("\nRESULT: FAIL — stop interpreting; debug sample filters / weights / cluster level / vcov first")
        return 1
    lvl = "bit-exact" if worst == 0 else "aligned"
    print(f"\nRESULT: PASS ({lvl}) — all implementations agree "
          f"(bit-exact = machine precision, aligned = within tolerance); "
          f"identification strategy still needs human review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
