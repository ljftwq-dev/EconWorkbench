# -*- coding: utf-8 -*-
"""
design.py — EconWorkbench v2.0: the reviewer checklist, executable
Lint research-design choices BEFORE interpreting estimates.
Rules (deterministic, interpretable — a linter, not a black-box score):
  CLUSTER  — few clusters (<30 FLAG, 30-49 WARN) -> wild cluster bootstrap
  STAGGER  — TWFE under staggered adoption -> Callaway-Sant'Anna / Sun-Abraham
  PRETREND — event-study pre-coefficients individually / jointly significant
Inputs: --script (.do/.R/.py, static scan) and/or --results events.csv
        (columns: term,estimate,se,pvalue) plus --n-clusters / --treatment.
Exit code 0 = no FLAG (WARN allowed), 1 = FLAG found (gate-able in CI/SDD).
Every finding carries an actionable fix and a citation. Research judgment
stays with the researcher.
"""
import sys, re, csv, argparse, os

# ---------------------------------------------------------------- script scan
TWFE_RX = [
    ("stata", r"\breghdfe\b|\bxtreg\b|\bareg\b|\bivregress\b|\bregress\b|\breg\b"),
    ("R", r"\bfeols\b|\bfelm\b|\blm\s*\(|\blmrobust\b"),
    ("python", r"\bPanelOLS\b|\bpyfixest\b|\bFixedEffects\b"),
]
CLUSTER_RX = [
    ("stata", r"vce\s*\(\s*cluster|cluster\s*\("),
    ("R", r"cluster\s*=|cluster\s*\("),
    ("python", r"cov_type\s*=\s*[\"']clustered|cluster\s*="),
]
MODERN_RX = [
    ("stata", r"\bcsdid\b|\bdid_multiplegt\b|\beventstudyinteract\b|\bjwdid\b|\bcsdid2\b"),
    ("R", r"\batt_gt\b|\bdid::\s*\w+|\bsunab\s*\(|\bdidimputation\b|\bdid2s\b"),
    ("python", r"\bdifferences\b|\bcsdid\b|\batt_gt\b"),
]


def scan_script(path):
    """Static scan of a .do/.R/.py file -> dict of detected features."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
    except OSError as e:
        return {"error": str(e)}
    # strip Stata comments so `* not reghdfe` does not trigger
    stata_comment = re.compile(r"^\s*\*.*$", re.M)
    body = stata_comment.sub("", src)
    hits = lambda table: {lang for lang, rx in table if re.search(rx, body, re.I)}
    return {
        "twfe": hits(TWFE_RX),
        "cluster": hits(CLUSTER_RX),
        "modern": hits(MODERN_RX),
        "ext": os.path.splitext(path)[1].lower(),
    }


# ---------------------------------------------------------------- rules
def rule_cluster(n_clusters, has_cluster_call, lines):
    if n_clusters is None:
        if has_cluster_call:
            lines.append(finding("WARN", "CLUSTER",
                "clustered SEs detected in script but cluster count not supplied",
                "pass --n-clusters N to enable the CLUSTER rule",
                ""))
        return
    if n_clusters >= 50:
        lines.append(finding("OK", "CLUSTER",
            f"n_clusters={n_clusters} >= 50 — asymptotic CRVE acceptable",
            "", ""))
    elif n_clusters >= 30:
        lines.append(finding("WARN", "CLUSTER",
            f"n_clusters={n_clusters} in 30-49 — asymptotics marginal",
            "report wild cluster bootstrap p-values (Rademacher weights): "
            "Stata `boottest`, R `fwildclusterboot`, Python `wildboottestgas`",
            "Cameron, Gelbach & Miller (2008), Rev. Econ. Stat. 90(3)"))
    else:
        lines.append(finding("FLAG", "CLUSTER",
            f"n_clusters={n_clusters} < 30 — cluster-robust SEs unreliable (over-rejection)",
            "wild cluster bootstrap (Rademacher weights): Stata `boottest`, "
            "R `fwildclusterboot`, Python `wildboottestgas`",
            "Cameron, Gelbach & Miller (2008), Rev. Econ. Stat. 90(3)"))


def rule_stagger(scan, treatment, lines):
    if scan is None:
        return
    if scan["modern"]:
        lines.append(finding("OK", "STAGGER",
            "modern staggered-DiD estimator detected (csdid / att_gt / sunab / ...)",
            "", "Callaway & Sant'Anna (2021), J. Econometrics 225(2)"))
        return
    if not scan["twfe"]:
        lines.append(finding("WARN", "STAGGER",
            "no regression command recognized in script — TWFE check skipped", "", ""))
        return
    if treatment == "staggered":
        lines.append(finding("FLAG", "STAGGER",
            "TWFE regression under staggered adoption — already-treated units "
            "act as controls; OLS weights can be negative",
            "switch to Callaway-Sant'Anna (csdid / did::att_gt), "
            "Sun-Abraham (eventstudyinteract / sunab), or Borusyak et al. (didimputation)",
            "Goodman-Bacon (2021), J. Econometrics 225(2); "
            "Sun & Abraham (2021), J. Econometrics 225(2)"))
    elif treatment == "unknown":
        lines.append(finding("WARN", "STAGGER",
            "TWFE regression found, treatment timing unknown",
            "if adoption is staggered (groups treated in different periods), "
            "TWFE is biased — pass --treatment staggered to see the full finding",
            "Goodman-Bacon (2021), J. Econometrics 225(2)"))
    else:  # common
        lines.append(finding("OK", "STAGGER",
            "TWFE with common treatment timing — no negative-weight problem "
            "(anticipation / spillovers still need human review)", "", ""))


# chi2 95% critical values df=1..15; Wilson-Hilferty approximation beyond
_CHI2_95 = [3.841, 5.991, 7.815, 9.488, 11.070, 12.592, 14.067, 15.507,
            16.919, 18.307, 19.675, 21.026, 22.362, 23.685, 25.000]


def chi2_95(df):
    if df <= 15:
        return _CHI2_95[df - 1]
    z = 1.6449
    return df * (1 - 2 / (9 * df) + z * (2 / (9 * df)) ** 0.5) ** 3


def parse_pre_terms(rows, custom_pattern):
    """Classify result rows into pre-period coefficients (k < 0)."""
    pre = []
    for t, (est, se, p) in rows.items():
        k = None
        if custom_pattern:
            m = re.fullmatch(custom_pattern, t)
            if m and m.groupdict().get("k"):
                k = float(m.group("k"))
        else:
            m = re.fullmatch(r"(?:lead|pre|rel|rm)[_-]?(-?\d+)", t, re.I)
            if m:
                k = float(m.group(1))
            else:
                m = re.fullmatch(r"g(\d+)[_-]t(\d+)", t, re.I)
                if m:
                    g, tt = float(m.group(1)), float(m.group(2))
                    k = tt - g  # group-time notation: t < g is a pre-period
        if k is not None and k < 0:
            pre.append((k, t, est, se, p))
    pre.sort()
    return pre


def rule_pretrend(path, custom_pattern, lines):
    rows = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows[r["term"].strip()] = (float(r["estimate"]), float(r["se"]), float(r["pvalue"]))
    pre = parse_pre_terms(rows, custom_pattern)
    if len(pre) < 2:
        lines.append(finding("WARN", "PRETREND",
            f"only {len(pre)} pre-period coefficient(s) recognized — pre-trend not testable",
            "use terms like lead_k / pre_k / rel_k / gYYYY_tYYYY (k<0 = pre), "
            "or pass --pre-pattern with a named group (?P<k>...)", ""))
        return
    flagged = False
    sig = [(k, t) for k, t, est, se, p in pre if p < 0.05]
    if len(sig) >= 2 or (len(pre) >= 4 and len(sig) > 0.25 * len(pre)):
        lines.append(finding("FLAG", "PRETREND",
            f"{len(sig)}/{len(pre)} pre-period coefficients individually significant "
            f"at 5% ({', '.join(t for _, t in sig)})",
            "report the joint pre-trend test; consider Rambachan-Roth (2023) "
            "honest sensitivity to violations of parallel trends",
            "Roth (2022), AER: Insights 4(3); Rambachan & Roth (2023), Rev. Econ. Stud. 90(5)"))
        flagged = True
    W = sum((est / se) ** 2 for _, _, est, se, _ in pre)
    crit = chi2_95(len(pre))
    if W > crit:
        lines.append(finding("FLAG", "PRETREND",
            f"joint pre-trend Wald chi2 = {W:.2f} > 95% critical {crit:.2f} (df={len(pre)}) — "
            "parallel trends rejected",
            "Rambachan & Roth (2023) sensitivity analysis; re-examine the identifying assumption",
            "Roth (2022), AER: Insights 4(3)"))
        flagged = True
    run, best = 1, 1
    for i in range(1, len(pre)):
        d = pre[i][2] - pre[i - 1][2]
        pd = pre[i - 1][2] - (pre[i - 2][2] if i >= 2 else pre[i - 1][2])
        if d * pd > 0:
            run += 1
        else:
            run = 1
        best = max(best, run)
    if best >= 3:
        lines.append(finding("WARN", "PRETREND",
            f"monotone drift: estimates move in one direction for {best} consecutive steps",
            "a trend can hide inside joint tests with low power — plot the event study",
            "Roth (2022), AER: Insights 4(3)"))
    if not flagged:
        lines.append(finding("OK", "PRETREND",
            f"{len(pre)} pre-period coefficients: none individually significant, "
            f"joint Wald chi2 = {W:.2f} <= {crit:.2f}",
            "power caveat: failing to reject != parallel trends hold",
            "Roth (2022), AER: Insights 4(3)"))


# ---------------------------------------------------------------- output
def finding(level, rule, msg, action, cite):
    s = f"[{level:>4}] {rule:<8} {msg}"
    if action:
        s += f"\n              -> {action}"
    if cite:
        s += f"\n              -> {cite}"
    return s


def build_parser():
    ap = argparse.ArgumentParser(
        prog="econ-design",
        description="Reviewer-checklist lint: CLUSTER / STAGGER / PRETREND. "
                    "Exit 0 = no FLAG, 1 = FLAG found.")
    ap.add_argument("--script", help="Stata .do / R / Python script to scan")
    ap.add_argument("--results", help="event-study result CSV (term,estimate,se,pvalue)")
    ap.add_argument("--n-clusters", type=int, help="number of clusters")
    ap.add_argument("--treatment", choices=["staggered", "common", "unknown"],
                    default="unknown", help="treatment timing (default: unknown)")
    ap.add_argument("--pre-pattern",
                    help="custom regex for pre-period terms, needs named group (?P<k>...) with k<0 = pre")
    ap.add_argument("--out", help="also write the lint report to this file (markdown)")
    return ap


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = build_parser()
    args = ap.parse_args(argv)

    if not args.script and not args.results and args.n_clusters is None:
        print("[FAIL] nothing to lint: pass --script and/or --results (+ --n-clusters)")
        return 2

    scan = scan_script(args.script) if args.script else None
    if scan and "error" in scan:
        print(f"[FAIL] cannot read script: {scan['error']}")
        return 2

    lines = []
    rule_cluster(args.n_clusters, bool(scan and scan["cluster"]), lines)
    rule_stagger(scan, args.treatment, lines)
    if args.results:
        try:
            rule_pretrend(args.results, args.pre_pattern, lines)
        except (OSError, KeyError, ValueError) as e:
            print(f"[FAIL] cannot parse results CSV: {e}")
            return 2

    header = (f"EconWorkbench design lint | script: {args.script or '-'} | "
              f"results: {os.path.basename(args.results) if args.results else '-'} | "
              f"clusters: {args.n_clusters if args.n_clusters is not None else '-'} | "
              f"timing: {args.treatment}")
    sep = "=" * 78
    print(header)
    print(sep)
    report = "\n".join(lines)
    print(report)
    print("-" * 78)

    md = [f"# EconWorkbench design lint", "", f"`{header}`", "", "```", report, "```"]
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")

    if "[FLAG]" in report:
        print("RESULT: FLAG — fix design issues before interpreting estimates "
              "(each finding above names the fix and the citation)")
        return 1
    print("RESULT: CLEAN — no FLAG (WARN items are advisory; judgment stays with you)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
