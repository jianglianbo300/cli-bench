# CLI Agent Benchmark Report — v2 (2026-08-10)

同模型（deepseek-v4-flash-free）同任务（T1-T6）同日同批，Windows 本机实测。

## 排名（通过率优先，全过者按均耗时）

| 排名 | agent | PASS | 均耗时 | 备注 |
|------|-------|------|--------|------|
| 1 | codex | 6/6 | 36.5s | 需"保留输入文件"约束（系统性删输入文件缺陷） |
| 2 | reasonix | 6/6 | 39.6s | cache 命中 89.8%，实际付费极少 |
| 3 | freebuff | 6/6 | 44.4s | 结果误存为codebuddy_summary.json，2026-08-10补录 |
| 4 | hermes | 6/6 | 45.3s | 工具集最完整（搜索+生图+skill+fallback） |
| 5 | opencode | 6/6 | 50.6s | 最省心，零额外依赖 |
| 6 | omp | 6/6 | 153.0s | 日志最精简（77行/6任务），一次到位 |
| 7 | mimo | 6/6 | 198.7s | 慢4倍，无独特优势 |

> cline：3轮调试后才全过（英文提示/环境适配问题），修复后6/6。2026-08-10第二轮独立首跑6/6，稳定性疑虑解除，正式入榜。

## 第二轮：Codex 总指挥全量跑（2026-08-10 12:40）

由 Codex 执行 run_all5.py 跑全部 7 家（codex→opencode→reasonix→mimo→omp→hermes→cline），
模型 omniroute-deepseek-v4-flash via 4202，运行 11:31→12:40。

| agent | PASS | 总耗时 | 均耗时 | 备注 |
|-------|------|--------|--------|------|
| codex | 6/6 | 280.9s | 46.8s | 最快 |
| reasonix | 6/6 | 285.0s | 47.5s | 与 codex 几乎持平 |
| cline | 6/6 | 450.2s | 75.0s | 首次独立跑即全过 |
| hermes | 6/6 | 454.2s | 75.7s | 2/6→6/6 进步最大 |
| opencode | 6/6 | 582.7s | 97.1s | T5 卡239s，zen key 疑失效重试 |
| omp | 6/6 | 949.0s | 158.2s | 稳定 |
| mimo | 6/6 | 1148.7s | 191.4s | 最慢 |

**总计 42/42 PASS 零失败**（首次全通）。

**对比第一轮（直接跑）**：代理执行有 20-30% 开销，绝对值变慢但排名不变：
- codex 36.5→46.8s、reasonix 39.6→47.5s（+20-28%，代理开销）
- hermes 45.3→75.7s、opencode 50.6→97.1s（opencode 异常，T5 从 47s→239s）
- mimo 提速 11%（198.7→191.4s）

**结论**：通过率优先排名稳定；opencode 的 T5 波动需单独复测（疑 zen key 失效触发重试路径）。

## 命中率 / 省钱维度（2026-08-10 新增）

"命中率" = 一次写对不返工。衡量指标：日志密集度（动作往返次数） + 实际 token 消耗。

| agent | 日志行数(6任务) | token 消耗 | 命中率评价 |
|-------|----------------|-----------|-----------|
| omp | 77 | 无报告(全额付费) | ⭐⭐⭐⭐⭐ 最精简，1-2步/任务，一次到位 |
| reasonix | 144 | 总884K hit + 101K miss（89.8% cache） | ⭐⭐⭐⭐⭐ cache 命中让实际付费极少 |
| opencode | 233 | 无报告 | ⭐⭐⭐ 中等，直接执行 |
| mimo | 233 | 无报告 | ⭐⭐⭐ 与 opencode 持平 |
| codex | 325 | 460,579 tokens（全额付费） | ⭐⭐ 会自我验证（写文件后自己跑测试），烧 token |
| hermes | 343 | 无报告 | ⭐⭐ 日志最密集，自我验证多，安全感高但多烧 |

**结论**：
- 省钱最优 = **reasonix**（cache 89.8%，付费 token 只有 10%）+ **omp**（日志最少，token 少）
- 速度最优 = codex（36.5s）
- 能力最全 = hermes（唯一有搜索+生图+skill+fallback 的）
- 命中率高 ≠ 速度快（omp 一次到位但慢在模型推理本身）

## 各任务验收输出

- T1 fruit_summary → apple 21 / banana 7 / orange 7
- T2 sales_report → South 295.0 / North 199.5
- T3 bank_tests → 3 tests passed
- T4 log_stats → Total lines: 200, ERROR: 67, INFO: 133
- T5 dir_scan → src\archive.txt
- T6 wordcount → hello: 3, world: 2

## 关键缺陷记录

1. **codex 自删输入文件**（系统性）：T2 删 sales.csv、T6 删 words.txt，多次复现。修复=prompt 统一加"保留输入文件"约束（模拟 AGENTS.md 防护）。
2. **hermes Windows 路径 bug**：terminal/file 工具 cwd 锁死 ~，D:\ 盘符被剥成相对路径。修复=统一用 MSYS /d/... 格式。
3. **hermes prompt 转义 bug**：`\n` 在 bashwrap 里是字面量非换行。修复=纯 cat 无拼接。
4. **mimo 模型前缀**：`opencode/` 应为 `opencode-zen/`。
5. **reasonix stdin 不读管道**：需 `reasonix run "prompt"` 直接传参。

## 通道现状

- 4202（litellm 商汤 4key）唯一活通道，只认 omniroute-deepseek-v4-flash
- 20128/20129/8899 全挂
- reasonix 走 4202 + OMNIROUTE_API_KEY
