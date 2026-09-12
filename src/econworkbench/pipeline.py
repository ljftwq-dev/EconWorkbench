# -*- coding: utf-8 -*-
"""
pipeline.py — EconWorkbench v4.0: the spec2paper driver.
Deterministic 11-step orchestrator from a signed research spec card to a referee-ready
draft skeleton. Two human gates (G0 topic, G1 final); everything else runs, persists
state, resumes from breakpoints, and HALTS LOUDLY on any failure.

Steps: gate0, data, estimate, crosscheck, lint, report, draft,
       data_audit, number_check, format_check, gate1

CLI: econ-pipeline <spec_card.md> [--ci] [--step NAME] [--reset]
  --ci    gates waiting for signature exit 0 (green in CI); real failures still exit 1
Heavy deps (pandas/pyyaml) are imported lazily inside steps — install econworkbench[pipeline].
"""
import json
import os
import re
import subprocess
import sys

STEPS = ["gate0", "data", "estimate", "crosscheck", "lint", "report", "draft",
         "data_audit", "number_check", "format_check", "gate1"]

MOD = f'"{sys.executable}" -m econworkbench.'  # same-package CLI calls, PATH-independent


def _reconf():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load_card(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r"```yaml\n(.*?)```", text, re.S)
    if not m:
        sys.exit("[FATAL] card has no ```yaml ...``` block")
    try:
        import yaml
        card = yaml.safe_load(m.group(1))
    except ImportError:
        sys.exit("[FATAL] pyyaml required (pip install econworkbench[pipeline])")
    for k in ("标题", "workdir", "G0_放行"):
        if not card.get(k):
            sys.exit(f"[FATAL] card missing required field: {k}")
    card["_card_path"] = os.path.abspath(path)
    card["_card_dir"] = os.path.dirname(os.path.abspath(path))
    return card


def state_load(workdir, reset):
    p = os.path.join(workdir, ".pipeline_state.json")
    if reset and os.path.exists(p):
        os.remove(p)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {"done": [], "failed": None, "waiting": None, "log": []}


def state_save(workdir, st):
    json.dump(st, open(os.path.join(workdir, ".pipeline_state.json"), "w",
                       encoding="utf-8"), ensure_ascii=False, indent=1)


def log(st, msg):
    st["log"].append(msg)
    print(msg)


def run_cmd(cmd, cwd):
    print(f"    $ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd)
    return r.returncode


def gate(card, st, which, label):
    ok = card.get(f"G{which}_放行")
    if ok and str(ok).strip() and "空" not in str(ok):
        log(st, f"[gate{which}] signed off: {ok}")
        return True
    st["waiting"] = f"gate{which}"
    log(st, f"[gate{which}] PAUSED: waiting for author signature on G{which}_放行 ({label})")
    return False


def step_data(card, st):
    ds = card.get("data_step") or "manual"
    if ds in ("manual", "skip"):
        log(st, f"[data] {ds} — fetch data by hand, then rerun (or point data_step at a script)")
        return True
    rc = run_cmd(ds, card["workdir"])
    log(st, f"[data] {ds} -> rc={rc}")
    return rc == 0


def step_estimate(card, st):
    es = card.get("estimate_step") or "manual"
    if es in ("manual", "skip"):
        log(st, f"[estimate] {es} — put result CSVs in workdir/results/")
        return True
    rc = run_cmd(es, card["workdir"])
    log(st, f"[estimate] {es} -> rc={rc}")
    return rc == 0


def step_crosscheck(card, st):
    if (card.get("crosscheck_pairs") or "skip") == "skip":
        log(st, "[crosscheck] skip (declared on card)")
        return True
    res = os.path.join(card["workdir"], "results")
    csvs = sorted(f for f in os.listdir(res) if f.endswith(".csv")) if os.path.isdir(res) else []
    if len(csvs) < 2:
        st["failed"] = "crosscheck"
        log(st, f"[crosscheck] FAIL: fewer than 2 CSVs in results/ ({csvs}) — halting")
        return False
    rc = run_cmd(f"{MOD}crosscheck {' '.join(os.path.join(res, c) for c in csvs)}",
                 card["workdir"])
    log(st, f"[crosscheck] {'PASS' if rc == 0 else 'FAIL ✖ halt — do not interpret results'}")
    return rc == 0


def step_lint(card, st):
    cfg = card.get("lint_config") or {}
    if not cfg or cfg.get("skip"):
        log(st, "[lint] skip")
        return True
    cmd = f"{MOD}design --n-clusters {cfg.get('n_clusters', '')}"
    if cfg.get("treatment"):
        cmd += f" --treatment {cfg['treatment']}"
    if cfg.get("script"):
        cmd += f" --script {cfg['script']}"
    rc = run_cmd(cmd.strip(), card["workdir"])
    log(st, f"[lint] {'CLEAN/WARN' if rc == 0 else 'FLAG ✖ halt'}")
    return rc == 0


def step_report(card, st):
    d = os.path.join(card["workdir"], "draft")
    os.makedirs(d, exist_ok=True)  # report does not mkdir; draft step runs after this
    res = os.path.join(card["workdir"], "results")
    csvs = sorted(f for f in os.listdir(res) if f.endswith(".csv")) if os.path.isdir(res) else []
    if not csvs:
        log(st, "[report] no results/*.csv — skipped")
        return True
    title = str(card.get("标题", "Table 1"))[:20]
    rc = run_cmd(f"{MOD}report {' '.join(os.path.join(res, c) for c in csvs)}"
                 f" --title \"{title}\" --out {os.path.join(card['workdir'], 'draft', 'table1')}",
                 card["workdir"])
    log(st, f"[report] -> rc={rc}")
    return rc == 0


DRAFT_TPL = """# {title}

## 一、引言
<!--GLM_FILL: 贡献陈述 {q}；对标文献；拒稿信防御-->

## 二、识别策略
<!--GLM_FILL: {ident}；变异来源；死穴与防御-->

## 三、结果
<!--GLM_FILL: 主表解读（见 draft/table1.*）；系数方向与量级；层级叙事-->

## 四、稳健性
<!--GLM_FILL: 按卡片「必做三件」逐条报告；honest point 单独一段-->

## 五、政策启示
<!--GLM_FILL: 3-4 条，每条=实证发现→机制→启示，不越识别边界-->
"""

DRAFT_TEX = """% {title} —— LaTeX draft skeleton (Overleaf: XeLaTeX + ctex)
\\documentclass[12pt]{{article}}
\\usepackage{{ctex}}
\\usepackage{{amsmath, amssymb}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}
\\usepackage[margin=1in]{{geometry}}
\\title{{{title}}}
\\date{{}}
\\begin{{document}}
\\maketitle

\\section{{引言}}
% GLM_FILL: contribution; benchmark literature; referee-letter defense

\\section{{识别策略}}
% GLM_FILL: identification equation, e.g. TWFE:
% \\begin{{equation}}
%   y_{{it}} = \\beta \\, \\mathrm{{hp}}_{{it}} + \\alpha_i + \\lambda_{{prov \\times t}} + \\gamma' X_{{it}} + \\varepsilon_{{it}}
% \\end{{equation}}

\\section{{结果}}
% GLM_FILL: main-table interpretation
\\begin{{table}}[htbp]\\centering
\\caption{{Main table (auto-generated)}}
\\input{{table1}}
\\end{{table}}

\\section{{稳健性}}
% GLM_FILL: the three mandatory checks + honest point

\\section{{政策启示}}
% GLM_FILL: 3-4 items, finding -> mechanism -> implication, stay inside identification

\\end{{document}}
"""


def step_draft(card, st):
    d = os.path.join(card["workdir"], "draft")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "初稿骨架.md")
    open(p, "w", encoding="utf-8").write(DRAFT_TPL.format(title=card.get("标题", ""),
                                                          q=card.get("一句话发现", ""),
                                                          ident=card.get("识别策略", "")))
    log(st, f"[draft] markdown skeleton -> {p}")
    tex = os.path.join(d, "初稿骨架.tex")
    open(tex, "w", encoding="utf-8").write(DRAFT_TEX.format(title=card.get("标题", "")))
    log(st, f"[draft] LaTeX skeleton -> {tex} (compile on Overleaf; \\\\input embeds the table)")
    return True


def step_data_audit(card, st):
    """G2-style data audit: shape/missing/duplicates per CSV; halts on anomalies.
    Card field data_audit_exempt exempts hand-verified raw wide tables."""
    import pandas as pd
    ddir = os.path.join(card["workdir"], "data")
    if not os.path.isdir(ddir):
        log(st, "[data_audit] no data/ directory — skipped")
        return True
    exempt = set(card.get("data_audit_exempt") or [])
    bad = []
    files = sorted(f for f in os.listdir(ddir) if f.endswith(".csv"))
    for f in files:
        if f in exempt:
            log(st, f"    {f:<28} EXEMPT (card-declared, hand-verified)")
            continue
        try:
            d = pd.read_csv(os.path.join(ddir, f))
        except Exception as e:
            bad.append(f"{f}: unreadable {e}")
            continue
        miss = float(d.isna().mean().max())
        dup = int(d.duplicated().sum())
        note = []
        if miss > 0.5:
            note.append(f"max missing {miss:.0%}")
        if dup > len(d) * 0.05:
            note.append(f"dup rows {dup}")
        flag = " WARN " + "; ".join(note) if note else ""
        log(st, f"    {f:<28} {d.shape[0]:>6} rows x {d.shape[1]:>2} cols{flag}")
        if flag:
            bad.append(f"{f}: {'; '.join(note)}")
    if bad:
        st["failed"] = "data_audit"
        log(st, f"[data_audit] FAIL: {len(bad)} anomalous file(s) — halting")
        for b in bad:
            log(st, f"      - {b}")
        return False
    log(st, f"[data_audit] OK: {len(files)} CSVs pass ({len(exempt)} exempt)")
    return True


def step_number_check(card, st):
    """statcheck-style number audit: every number in draft/*.md must trace back to
    results/*.csv — original values OR recomputed quantities (est/se -> t, normal -> p).
    Threshold idioms like p < .05 are exempted."""
    import math
    import pandas as pd
    ddir = os.path.join(card["workdir"], "draft")
    rdir = os.path.join(card["workdir"], "results")
    mds = sorted(f for f in os.listdir(ddir) if f.endswith(".md")) if os.path.isdir(ddir) else []
    if not mds:
        log(st, "[number_check] no draft/*.md — skipped")
        return True
    text = "".join(open(os.path.join(ddir, f), encoding="utf-8").read() for f in mds)
    body = re.sub(r"<!--GLM_FILL.*?-->", "", text, flags=re.S)
    body = re.sub(r"[pP]\s*[<>≤≥]\s*\.?\d+", "", body)  # p<.05 is a threshold idiom
    nums_in_text = set(re.findall(r"-?\d*\.\d+", body))
    if not nums_in_text and "GLM_FILL" in text:
        log(st, "[number_check] draft is still a skeleton (GLM_FILL unfilled) — pass")
        return True
    csv_nums, recomputed = set(), 0
    if os.path.isdir(rdir):
        for f in os.listdir(rdir):
            if not f.endswith(".csv"):
                continue
            d = pd.read_csv(os.path.join(rdir, f))
            for c in d.columns:
                if pd.api.types.is_numeric_dtype(d[c]):
                    vals = d[c].dropna()
                    csv_nums |= {f"{abs(v):.3f}" for v in vals}
                    csv_nums |= {f"{abs(v):.2f}" for v in vals if abs(v) < 100}
            if {"estimate", "se"}.issubset(d.columns):  # statcheck layer
                for _, row in d.iterrows():
                    try:
                        if row["se"] and abs(row["se"]) > 1e-12:
                            t_hat = abs(row["estimate"] / row["se"])
                            csv_nums |= {f"{t_hat:.2f}", f"{t_hat:.1f}"}
                            p_hat = 2 * (1 - 0.5 * (1 + math.erf(t_hat / math.sqrt(2))))
                            csv_nums |= {f"{p_hat:.3f}", f"{p_hat:.2f}"}
                            recomputed += 2
                    except (TypeError, ValueError):
                        continue
    orphans = [n for n in nums_in_text if f"{abs(float(n)):.3f}" not in csv_nums
               and f"{abs(float(n)):.2f}" not in csv_nums]
    if orphans:
        st["failed"] = "number_check"
        log(st, f"[number_check] FAIL: {len(orphans)} number(s) not traceable — halting:")
        log(st, "      orphans: " + ", ".join(sorted(orphans)[:20]))
        log(st, "      (fix the numbers, or document an exemption on the card and rerun)")
        return False
    log(st, f"[number_check] OK: all {len(nums_in_text)} numbers traceable "
            f"(pool includes {recomputed} recomputed t/p, statcheck-style)")
    return True


def step_format_check(card, st):
    """Final docx format lint: uniform fonts / Heading styles / tables present.
    Only files named 成稿* or final* are audited."""
    ddir = os.path.join(card["workdir"], "draft")
    if not os.path.isdir(ddir):
        log(st, "[format_check] no draft/ — skipped")
        return True
    finals = [f for f in os.listdir(ddir) if f.endswith(".docx")
              and ("成稿" in f or "final" in f.lower())]
    if not finals:
        log(st, "[format_check] no final docx (name must contain 成稿 or final) — "
                "skipped; rerun this step before submission")
        return True
    from docx import Document
    issues = []
    for f in finals:
        doc = Document(os.path.join(ddir, f))
        fonts = set()
        for p in doc.paragraphs:
            for r in p.runs:
                if r.font.name:
                    fonts.add(r.font.name)
        heads = sum(1 for p in doc.paragraphs if p.style.name.startswith("Heading"))
        tables = len(doc.tables)
        log(st, f"    {f}: fonts {sorted(fonts)} | {heads} Heading paras | {tables} tables")
        if len(fonts) > 1:
            issues.append(f"{f}: mixed fonts {sorted(fonts)}")
        if heads == 0:
            issues.append(f"{f}: no Heading styles")
    if issues:
        st["failed"] = "format_check"
        log(st, f"[format_check] FAIL: {len(issues)} issue(s) — halting")
        for i in issues:
            log(st, f"      - {i}")
        return False
    log(st, "[format_check] OK: final docx format clean")
    return True


RUNNERS = {"gate0": lambda c, s: gate(c, s, 0, "topic sign-off"),
           "data": step_data, "estimate": step_estimate, "crosscheck": step_crosscheck,
           "lint": step_lint, "report": step_report, "draft": step_draft,
           "data_audit": step_data_audit, "number_check": step_number_check,
           "format_check": step_format_check,
           "gate1": lambda c, s: gate(c, s, 1, "final draft sign-off")}


def main(argv=None):
    _reconf()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(__doc__)
        return 1
    ci = "--ci" in args
    if ci:
        args = [a for a in args if a != "--ci"]
    card = load_card(args[0])
    only = args[args.index("--step") + 1] if "--step" in args else None
    reset = "--reset" in args
    wd = card["workdir"]
    if not os.path.isabs(wd):
        wd = os.path.join(card["_card_dir"], wd)
        card["workdir"] = wd
    os.makedirs(wd, exist_ok=True)
    st = state_load(wd, reset)
    if st.get("failed"):
        if only != st["failed"]:  # only --step <failed-step> may retry
            print(f"[HALT] last run failed at {st['failed']} — fix, then --reset or --step {st['failed']}")
            return 1
        st["failed"] = None
    for name in ([only] if only else STEPS):
        if name not in RUNNERS:
            sys.exit(f"[FATAL] unknown step {name}; valid: {STEPS}")
        if name in st["done"] and not only:
            print(f"[skip] {name} (done)")
            continue
        print(f"\n===== {name} =====")
        if not RUNNERS[name](card, st):
            state_save(wd, st)
            if ci and (st.get("waiting") or "").startswith("gate"):
                print(f"\n[CI] stopped at {name} (gate awaiting signature) — treated as green")
                return 0
            print(f"\n[STOP] pipeline halted at {name} (state saved; rerun to resume)")
            return 1
        if name not in st["done"]:
            st["done"].append(name)
        st["waiting"] = None
        state_save(wd, st)
    state_save(wd, st)
    print("\n[DONE] pipeline finished (or gate passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
