# CLI Agent Benchmark Report — v2 (2026-08-10)

同模型（deepseek-v4-flash-free）同任务（T1-T6）同日同批，Windows 本机实测。

## 排名（通过率优先，全过者按均耗时）

| 排名 | agent | PASS | 均耗时 | 备注 |
|------|-------|------|--------|------|
| 1 | codex | 6/6 | 36.5s | 需"保留输入文件"约束（系统性删输入文件缺陷） |
| 2 | reasonix | 6/6 | 39.6s | cache 命中 89.8%，实际付费极少 |
| 3 | hermes | 6/6 | 45.3s | 工具集最完整（搜索+生图+skill+fallback） |
| 4 | opencode | 6/6 | 50.6s | 最省心，零额外依赖 |
| 5 | omp | 6/6 | 153.0s | 日志最精简（77行/6任务），一次到位 |
| 6 | mimo | 6/6 | 198.7s | 慢4倍，无独特优势 |

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
