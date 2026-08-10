# CLI 编码 Agent 实测对比 v2（bench2.py 版）

日期：2026-08-10 同日同批重跑
模型：deepseek-v4-flash-free（统一同模型）
方法：6 个本地任务，脚本自动验收，各 CLI 独立沙箱运行（bench2.py）
非交互方式：codex exec / opencode run / mimo run / omp -p / hermes chat -q

## 最终排名（通过率优先，全过者按速度排序）

| 排名 | 工具 | 均耗时 | 通过率 | 总耗时 | 最快 | 最慢 |
|------|------|--------|--------|--------|------|------|
| 1 | **codex** | **36.5s** | 6/6 | 219.0s | 26.0 | 48.9 |
| 2 | **hermes** | **45.3s** | 6/6 | 272.0s | 26.8 | 65.4 |
| 3 | **opencode** | 50.6s | 6/6 | 303.3s | 36.3 | 66.9 |
| 4 | **omp** | 153.0s | 6/6 | 918.0s | 148.2 | 156.6 |
| 5 | **mimo** | 198.7s | 6/6 | 1192.2s | 155.7 | 233.6 |

注：codex 需在 prompt 中统一追加"保留所有输入文件"约束，模拟 AGENTS.md 防护效果。不加约束时 T2/T6 会自删输入文件。

## 关键发现

1. **codex 最快**（36.5s/任务），但需 prompt 约束防止删输入文件。系统性问题：会自行删除任务输入文件（T2 sales.csv、T6 words.txt），已在 AGENTS.md 和 bench2 中加防护。
2. **hermes 第二快**（45.3s/任务），能力最全（唯一有 web 搜索+生图+技能+fallback 链的 agent）。从 2/6 修到 6/6（两处 bench2 调用 bug）。
3. **opencode 最省心**：无额外依赖、稳定、速度第三，6/6 全过不挑场景。
4. **omp 最稳**：148-157s 近乎一条直线，全过，有多模型角色（smol/slow/plan）。
5. **mimo**：功能和 opencode 几乎一样，但慢 4 倍，无独特优势。
6. **通道现状**：20128/20129/8899 全挂，4202（litellm 商汤 4key）唯一活通道。
7. **所有 agent 代码质量一致**：6 任务的产物都是 `defaultdict/Counter` + `sorted` + `if __name__ == "__main__"` 标准结构，无显著质量差异。

## bench2 修复汇总

| 修复 | 问题 | 方案 |
|------|------|------|
| mimo 模型前缀 | 误用 opencode/ → opencode-zen/ | 修正前缀 |
| codex 删输入文件 | 系统性地自删输入文件 | 统一追加"保留输入文件"约束 |
| hermes prompt 传递 | `\n` 转义错位，prompt 只剩路径约束 | 改用纯 cat 无拼接 |
| hermes Windows 路径 | D:/... 盘符被剥掉，落到 ~/work/ | 改用 MSYS /d/... 格式 |
| 防护落地 | codex 在真实工作中也会删文件 | AGENTS.md 加硬边界规则 |

## 能力矩阵

详见 `CAPABILITY_MATRIX.md`。

## 复现

```
D:\work\cli-bench\runner\bench2.py --agent <codex|opencode|mimo|omp|hermes>
D:\work\cli-bench\results2\all5_final.json
D:\work\cli-bench\results2\REPORT.md
D:\work\cli-bench\results2\CAPABILITY_MATRIX.md
```