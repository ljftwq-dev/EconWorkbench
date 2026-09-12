# 论文流水线：项目介绍与实录

> 观点是人出的，工程是机器干的。
> 从一句话 idea 到 referee-ready 初稿，作者只在 G0/G1 签两次名，中间 11 步全自动、可断点续跑、失败即停机。
> 诞生：2026-09-11 一个晚上（立项 SPEC → 骨架 → 验收 → 两轮扩展）。

---

## 一、全景：11 步流水线

```
gate0 ─ data ─ estimate ─ crosscheck ─ lint ─ report ─ draft
     └→ data_audit ─ number_check ─ format_check ─ gate1
        (选题放行)                                    (终稿放行)
        ↑ 人签一次                                    ↑ 人再签一次
```

| 步骤 | 干什么 | 灵感来源 |
|---|---|---|
| gate0 / gate1 | 人工门控：选题放行、终稿放行 | SDD 五道门控 |
| data / estimate | 数据管道、实证脚本（可挂脚本或 manual） | — |
| crosscheck | 双语言对拍：同模型 R/Python 各跑一遍，bit-exact/aligned/FAIL | EconWorkbench v1.0 |
| lint | 研究设计审查（聚类数/交叠DID/预趋势） | EconWorkbench v2.0 |
| report | 结果 CSV → 期刊三线表（tex/docx/png） | EconWorkbench v1.2 |
| draft | 双模板初稿骨架：**Markdown + LaTeX**（ctex+amsmath，\input 直嵌主表） | 用户灵感：计量论文公式多 |
| data_audit | 数据体检：形状/缺失/重复，卡片豁免清单 | SDD G2（pandera 思想） |
| number_check | **正文数字对拍**：溯源 + 重算（est/se→t，正态近似→p） | **statcheck**（Nuijten） |
| format_check | 成稿 docx lint：字体统一/Heading 样式/表格 | statcheck-word |
| --ci 模式 | 挂 GitHub Actions：push 即全链复现，门控暂停=绿、真失败=红 | **showyourwork** |

**铁律**：crosscheck FAIL / lint FLAG / 审查异常 → 一律停机报警，绝不静默降级。

## 二、诞生实录（一晚上发生了什么）

### 1. 先砍掉一个坏主意：不做"论文工厂"

最初的提议是"把它变成论文工厂"。讨论后否决：论文工厂（paper mill）是学术伦理贬义词，
批量灌水会毁掉工具的信用；而真正想要的其实是——**让作者专注观点，工程自动化**。
于是定位改为一句话：**做流水线，不做工厂。方向盘在人手里。**

### 2. brainstorm 的正确打开方式：终点不是共识，是 spec

普通头脑风暴输出"聊天共识"，还要人翻译成代码。本项目的 brainstorm 升级为**漏斗**：
**审稿人最终会问什么，漏斗就先问什么**——四层问题库（贡献/识别/数据/稳健性反向自审稿人 checklist），
把一句大白话逼成一张填满的研究卡片。卡片没填满，禁止进流水线。

### 3. 漏斗实战摘录（验收案例：城市级结果变量）

> **作者**："我觉得房价对消费的影响是分层的。"
>
> **漏斗 L1（贡献层）**："把结果变量换成城市级，会告诉我们什么省级面板看不到的？"
> **作者**："我希望加强论点，所以是稳健性对照。"
> **漏斗**："反事实审稿人说'省级已经够了'，你怎么挡？"
> **作者**（采纳提示后）："省聚合是加权平均，理论传导在城市层级时聚合引入衰减偏误压低系数——城市级是检验识别层级的必要条件。"
>
> **漏斗 L2（识别层）**："时间 FE 用哪个：(a) 全国季 FE (b) 省×季 FE？"
> **作者**："选 b"——（正确：识别的才是同省内部城市间偏差，与主论文层级叙事严丝合缝）
>
> **漏斗 L3（数据层·生死关）**：探测发现 akshare 无城市级社零接口、国家局门户最低省级——
> 70 城季度面板公开不可得，降级为"年度年鉴主案 + 重点城市季度备选"。
>
> **漏斗 L4（稳健性层）**：预注册三分支价值陈述（显著/不显著但量级更大/方向翻转=死穴），结果出来按分支套，零患得患失。

四层问完 → 卡片填满 → 作者签名 G0 → driver 开跑。

## 三、driver 运行实录（真实终端输出）

**门控暂停**（G0 未签名，流水线拒绝开跑）：

```
===== gate0 =====
[gate0] ⏸ 暂停：等待作者在卡片「G0_放行」签名（选题放行）
[STOP] 流水线停于 gate0（状态已落盘，可排查后 --resume）
```

**全链跑通**（G0 签名后）：

```
[gate0] 已放行：李嘉丰 2026-09-11
[crosscheck] py_results vs r_results: bit-exact 3 | aligned 0 | FAIL 0
RESULT: PASS (bit-exact)
[lint] EconWorkbench design lint | clusters: 70
[  OK] CLUSTER  n_clusters=70 >= 50 — asymptotic CRVE acceptable
RESULT: CLEAN
[report] wrote table1.tex / table1.docx / table1.png
[draft] 初稿骨架(md) + 初稿骨架(LaTeX) 双模板生成
[gate1] ⏸ 暂停：等待终稿放行
```

**失败停机 + 豁免续跑**（data_audit 抓到真异常）：

```
house_price_70cities.csv   13090 行 x 8 列 ⚠ 最高缺失率 55%
[data_audit] ✖ 1 份数据异常——停机，人工核查后再跑
（人工核查：原始宽表多列设计性缺失，分析前 dropna，属已知正常）
→ 卡片加 data_audit_exempt: [house_price_70cities.csv]
[data_audit] OK：13 份 CSV 体检通过（1 份豁免）
```

**number_check 拦截编造数字**（statcheck 式重算层）：

```
测试稿："系数 -0.103（t = 1.1, p 实为 0.27）；另有个编造的 t = 9.99"
[number_check] ✖ 正文 1 个数字在结果文件中找不到——停机：
      孤立数字: 9.99
（-0.103 是 CSV 原值；t=1.1 与 p=0.27 由重算池 est/se→t、正态近似→p 放行；
   9.99 两处都找不到 → 拦截。p < .05 阈值表述自动豁免，不算数据数字。）
```

**CI 模式**（showyourwork 式持续验证）：

```
$ python driver.py spec_card.md --ci --reset
[gate1] ⏸ 暂停：等待作者签名
[CI] 停在 gate1（门控等待人工签名）——CI 视为通过   # exit 0
（真失败仍是 exit 1，GitHub Actions 直接亮红）
```

## 四、标杆借鉴对照

| 标杆 | 它怎么干 | 我们搬了什么 |
|---|---|---|
| **statcheck**（"统计量的拼写检查器"，Nuijten et al.，审稿圈在用） | 从论文正文抽 APA 统计报告 → 用统计量+df **重算 p 值** → 比对；分 inconsistency / decision error 两级 | number_check 重算层 + FAIL 判据印证（显著性翻转才 FAIL，英雄所见略同） |
| **showyourwork**（天体物理圈，一篇论文一个 repo） | GitHub Actions 从数据到 PDF 一键重建，build 挂了 PR 不能合并——审查变成**持续验证** | --ci 模式 + ci-driver.yml 模板 |
| great expectations | 声明式 expectation suite | 豁免清单是它的雏形，待演进 |

## 五、下一步

- 城市级案例的真实取数（年度年鉴主案）→ 真实证 → 填初稿 → G1
- 论文 repo 化后挂 ci-driver.yml，push 即全链复现
- 豁免清单 → 声明式 expectation；FAIL 分级（hard/soft）

*文档由 GLM 整理，2026-09-12。运行实录摘自当晚真实终端输出。*
