# CLI Agent 能力矩阵（2026-08-10 · 本机实测/配置）

标注：✅ 本机实测可用 · ◐ 配置支持/本机受限 · ❌ 不支持 · ❓ 未验证

## 核心工具集

| 能力 | codex | reasonix | freebuff | hermes | opencode | omp | mimo |
|------|-------|----------|----------|--------|----------|-----|------|
| 文件读写 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 终端/命令 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 联网搜索 | ✅ Keenable MCP | ❌ | ✅ 内置web research | ✅ Keenable | ❌ | ❌ | ❌ |
| 浏览器自动化 | ❌ browser_use不暴露 | ❌ | ✅ 内置browser use | ◐ 有但糙 | ❌ | ❌ | ❌ |
| 生图 | ❌ image_gen不暴露 | ❌ | ❌ | ✅ FAL | ❌ | ❌ | ❌ |
| MCP | ✅ | ❌ | ❓ | ✅ | ✅ | ❌ | ❌ |
| 技能系统 | ✅ skills | ❌ | ❌ | ✅ 深集成 | ✅ plugin | ❌ | ❌ |

## 模型 / 通道

| agent | 模型来源 | 免费性 |
|-------|---------|--------|
| codex | 自配 (4202 omniroute) | 工具免费，模型自付 |
| reasonix | 自配 (4202 + OMNIROUTE_API_KEY) | 工具免费，模型自付 |
| freebuff | 内置 DeepSeek V4 Pro/MiMo/MiniMax M3 | ✅ 广告支持全免费（limited模式6次/天） |
| hermes | 自配 (omniroute 4202 + fallback链) | 工具免费，模型自付 |
| opencode | 自配 (opencode-zen) | 工具免费，模型自付 |
| omp | 自配 (sensenova/deepseek) | 工具免费，模型自付 |
| mimo | 自配 (opencode-zen) | 工具免费，模型自付 |

## 工作流 / 增强功能

| 功能 | codex | reasonix | freebuff | hermes | opencode | omp | mimo |
|------|-------|----------|----------|--------|----------|-----|------|
| fallback链 | ◐ config支持 | ❌ | ❌ | ✅ 自动切 | ❌ | ❌ | ❌ |
| 多模型角色 | ❌ | ❌ | ✅ V4 Pro/Flash/MiMo/M3切换 | ❌ | ❌ | ✅ smol/slow/plan | ❌ |
| cron/定时 | ✅ | ✅ scheduler | ❌ | ✅ 原生 | ❌ | ❌ | ❌ |
| 飞书/微信IM | ❌ | ✅ | ❌ | ✅ gateway | ❌ | ❌ | ❌ |
| 会话恢复 | ✅ | ✅ | ✅ --continue | ✅ | ✅ | ✅ | ✅ |

## 使用门槛

| agent | 安装 | 配置成本 | 注意事项 |
|-------|------|---------|---------|
| codex | npm i -g @openai/codex | 中（provider+key） | 需"保留输入文件"约束；会自删文件 |
| reasonix | npm i -g reasonix | 中（config.toml+key） | stdin不读管道，需run "prompt" |
| freebuff | npm i -g freebuff | **零配置，开箱即用** | 广告支持；中国=limited模式6次/天 |
| hermes | 官方安装器 | 低（开箱即用） | Windows路径须MSYS /d/格式 |
| opencode | npm i -g opencode | 低 | 需zen云key，失效需重登 |
| omp | bun安装 | 低 | 走sensenova/pi |
| mimo | npm i -g | 低 | 慢4倍 |

## 速度排名（2026-08-10，全6/6通过）

| 排名 | agent | 均耗时 |
|------|-------|--------|
| 1 | codex | 36.5s |
| 2 | reasonix | 39.6s |
| 3 | freebuff | 44.4s |
| 4 | hermes | 45.3s |
| 5 | opencode | 50.6s |
| 6 | omp | 153.0s |
| 7 | mimo | 198.7s |

> cline：3轮调试后6/6，稳定性存疑未入榜。排名规则=通过率优先，全过者按速度。

## 命中率 / 省钱维度

| agent | 日志行数(6任务) | token消耗 | 评价 |
|-------|----------------|-----------|------|
| omp | 77 | 无报告(全额付费) | ⭐⭐⭐⭐⭐ 最精简，1-2步/任务 |
| reasonix | 144 | cache 89.8% | ⭐⭐⭐⭐⭐ 实际付费10% |
| opencode | 233 | 无报告 | ⭐⭐⭐ 中等 |
| mimo | 233 | 无报告 | ⭐⭐⭐ 与opencode持平 |
| freebuff | 未测 | 未测 | ❓ 待测 |
| codex | 325 | 460,579全额 | ⭐⭐ 自我验证多 |
| hermes | 343 | 无报告 | ⭐⭐ 日志最密集 |

## 选型结论

- **速度**：codex（36.5s）
- **省钱**：reasonix（cache 89.8%）+ omp（77行最精简）
- **免费白嫖**：freebuff（广告支持，零配置，limited模式6次/天）
- **能力最全**：hermes（唯一搜索+生图+skill+fallback）
- **省心**：opencode（零额外依赖）
- **不建议**：mimo（慢4倍无优势）
