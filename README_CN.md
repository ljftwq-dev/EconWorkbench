# EconWorkbench（中文版）

**同一个估计量，独立实现，一个结论。**

[English](README.md) | 中文

[![CI](https://github.com/ljftwq-dev/EconWorkbench/actions/workflows/ci.yml/badge.svg)](https://github.com/ljftwq-dev/EconWorkbench/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/econworkbench.svg)](https://pypi.org/project/econworkbench/)

EconWorkbench 是一个面向实证研究全流程的开源工作台：文献、数据、设计、估计、**验证**、成表。研究的判断权永远在你手里——工作台负责让每一步更快、让数字可信。

**v1.0 交付核心模块：`crosscheck/`**——把*同一个*模型分别在 **R、Python、Stata** 里跑一遍，自动对比结果。数字一致，说明你的代码（几乎肯定）没问题；数字不一致，先别解读结果——赶在审稿人发现之前，自己先发现。

**v2.0 新增 `design/`**——审稿人 checklist，可执行。在解读任何系数之前，先给你的研究设计做 lint（聚类太少、交叠 DID 用 TWFE、预趋势）。

<p align="center">
  <img src="assets/triple_crosscheck_cs2021.png" alt="R、Python、Stata 三个终端并排复现 Callaway-Sant'Anna (2021)，三者均显示 ATT = -0.0399513" width="900">
</p>

*真实截图：Callaway & Sant'Anna (2021) 交叠 DID（mpdta 数据），在 R（`did` 包）、Python（`StatsPAI`）、Stata（`csdid`）中独立实现，三者 Overall ATT 均为 **-0.0399513**。*

## 为什么需要它

现在的计量代码大部分是 AI 写的。但如果一个大模型在两种语言里**一致地**写错了 `vcov`——它会给你一个自信的、但错误的结果。解法比大模型古老得多：**同一估计量的独立实现应当一致**。

- R 的 `did`（Callaway 团队）、Stata 的 `csdid`（Sant'Anna 团队）、Python 的移植版，是三拨人各自写的。同一份数据 + 同一个模型 + 同样的数字 = 实现是干净的。
- 只跑一遍、只看一个数字 = 你无法区分"结果"和"bug"。

这相当于回归分析里的**复式记账法**——灵感来自 2026 年一个"AI 智能体赋能社科研究"系列讲座（主讲人因 Stata 授权费所限，只能做 R 与 Python 的双实现对拍），以及 [StatsPAI](https://github.com/brycewang-stanford/StatsPAI) 的 parity index（它给自己的每个估计量都标注了与 R/Stata 参照的对齐证据）。

## 快速上手

核心零依赖（纯标准库）：

```
pip install econworkbench        # 或: pip install .[report] 一步带表格功能

# 1. 同一模型在 R / Python / Stata 各跑一遍，每个脚本输出四列 CSV：
#    term, estimate, se, pvalue
Rscript my_model.R            # -> r_results.csv
python  my_model.py           # -> py_results.csv
"C:\Program Files\Stata19\StataSE-64.exe" /e do my_model.do   # -> stata_results.csv

# 2. 对拍（第一个 CSV 是基准）：
econ-crosscheck r_results.csv py_results.csv stata_results.csv
```

输出：

```
term                    r_resultsvspy_resultsr_resultsvsstata_results
--------------------------------------------------------------------
g2004_t2004             bit-exact           aligned
...
overall_simple          bit-exact           aligned
--------------------------------------------------------------------
r_results vs py_results: bit-exact 8 | aligned 0 | FAIL 0
r_results vs stata_results: bit-exact 0 | aligned 8 | FAIL 0
RESULT: PASS (aligned) — 退出码 0
```

## 判定等级

| 判定 | 含义 | 默认容差 |
|---|---|---|
| `bit-exact` | 机器精度级一致 | Δ ≤ 1e-10 |
| `aligned` | 容差内一致 | Δ系数 ≤ 1e-6，ΔSE/SE ≤ 1e-4，Δp ≤ 1e-4 |
| `FAIL` | 显著性翻转或超出容差 | — 退出码 1 |

退出码可接入门控：CI、Makefile，或你自己的 SDD 流水线，当发布门用。

## 示例：Callaway & Sant'Anna (2021) 复现

[`examples/cs2021_mpdta/`](examples/cs2021_mpdta/) 用三套实现复现了交叠 DID 的经典应用（最低工资对青少年就业的影响，2,500 个县-年观测）：

| | 实现 | 作者自己的包 |
|---|---|---|
| R 4.6.1 | `did::att_gt()` + `aggte()` | Callaway & Sant'Anna |
| Python 3.14 | `StatsPAI.callaway_santanna()` | 带 parity 证据的移植 |
| StataNow 19.5 | `csdid` + `csdid_estat simple` | Sant'Anna, Goodman-Bacon & Pedro |

结果：**R ↔ Python 在全部 8 个量上 bit-exact**（7 个 post 期 ATT(g,t) + overall）；**R ↔ Stata 全部 aligned**（Δ ≈ 1e-7，源于 DR-IPW 优化器不同）。Overall ATT = -0.0399 与原论文一致。

你可以自己复跑：目录里有三个脚本、共享数据集（`mpdta_data.csv`——单一数据源，三种语言读同一份文件）、以及三份结果 CSV。

## 示例：Bai-Perron 结构断点——对拍抓的就是你自己的虫

[`examples/bai_perron_breakpoints/`](examples/bai_perron_breakpoints/) 用手写精确 DP（numpy）对拍 `strucchange::breakpoints()`，数据是滚动β序列（房地产×社零，165 个月度观测）：

- 修复后 **PASS (bit-exact)**：可比的 k 上 |ΔRSS| ≤ 4.3e-14，断点完全一致，双侧 BIC 同选 k=2
- **路上抓到两个真虫**：① Python DP 回溯跨 j 取 argmin，静默返回错误断点；② R `ts()` 假设月份连续，而序列每年缺 1 月——断点*日期*被标错（2018-11 vs 真实 2020-04），拟合本身却是对的
- **实现边界也是裁决的一部分**：k≥3 时 strucchange 内部封顶只回 2 个断点，`compare.py` 将这些行判 N/A 而非 FAIL——两者的区别 README 里有讲

这就是催生本项目的案例：两套单独看都"对"的实现，只有被放在一起比对，才会吵得足够响、把虫逼出来。

## 从估计值到论文表格（`report/`，v1.2）

喂给 `crosscheck` 的同一批 CSV，直接喂给 `report`——一条命令，从估计值到期刊级三线表：

```
econ-report r_results.csv py_results.csv stata_results.csv --title "表1" --out table1
# -> table1.tex（booktabs）+ table1.docx（Word 三线表）+ table1.png（预览图）
```

<p align="center">
  <img src="examples/cs2021_mpdta/table1.png" alt="R/Python/Stata 三列估计对照的三线表" width="640">
</p>

显著性星号、括号内标准误、顶线/栏目线/底线，三种格式一致。列名置于表底（`esttab` 惯例）。

## 赶在审稿人之前发现设计缺陷（`design/`，v2.0）

`crosscheck` 验证的是*代码*；`design` lint 的是*研究设计*。指向你的 Stata/R/Python 脚本和/或事件研究 CSV：

```
econ-design --script my_study.do --n-clusters 12 --treatment staggered --results events.csv
# 退出码 0 = 干净（允许 WARN），1 = 发现 FLAG——与 crosscheck 一样可接入门控
```

三条确定性、可解释的规则——是 linter，不是黑盒打分。每条 finding 都写明修复动作和引文：

| 规则 | 触发条件 | 建议 |
|---|---|---|
| `CLUSTER` | 聚类数 <30 FLAG，30-49 WARN | wild cluster bootstrap（Rademacher）——Cameron, Gelbach & Miller (2008) |
| `STAGGER` | 交叠 DID 却用 TWFE（脚本里没有 csdid/att_gt/sunab） | 换 Callaway-Sant'Anna / Sun-Abraham——Goodman-Bacon (2021) |
| `PRETREND` | 前期系数个体/联合显著，或单调漂移 | 报告联合检验 + Rambachan & Roth (2023) 敏感性——Roth (2022) |

[`examples/design_demo/`](examples/design_demo/) 里的坏研究一次性踩中全部三条规则；好研究（csdid + boottest、230 个聚类）返回 CLEAN。两个都跑一遍就能看懂 lint 的行为。

## 它*不*做什么

- 它验证不了你的**识别策略**——错误模型的两个实现会完美一致。`design/` 只 lint 审稿人 checklist 的常见项（聚类、交叠时点、预趋势），识别的判断权在你。
- 它不是论文工厂。选题与判断，永远留在研究者手里。

## 相关工作

- [StatsPAI](https://github.com/brycewang-stanford/StatsPAI) —— agent 原生的 Stata/R 替代品，带可查询的 parity index（本想法的超集，封装在一个库内）。
- Sakana AI-Scientist、Agent Laboratory —— 端到端"AI 科学家"流水线（相反的押注：自动化优先于验证）。

## 许可

MIT
