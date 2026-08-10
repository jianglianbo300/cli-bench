# cli-bench

CLI coding agent benchmark — fair comparison of codex / opencode / mimo / omp / hermes / reasonix on identical tasks with scripted verification.

## What it does

Runs 6 local coding tasks (T1-T6) through each CLI agent in a fresh sandbox, then verifies the output with a Python script. Same model, same tasks, scripted acceptance — no human judgment.

## Tasks

| Task | Description |
|------|-------------|
| T1 | fruit_summary: read data.txt, aggregate counts per fruit |
| T2 | sales_report: read sales.csv, sum revenue by region |
| T3 | bank_tests: implement bank.py, pass unit tests |
| T4 | log_stats: read app.log, count ERROR/INFO lines |
| T5 | dir_scan: recursive scan for files containing SECRET |
| T6 | wordcount: read words.txt, count word frequencies |

## Usage

```bash
python runner/bench2.py --agent <codex|opencode|mimo|omp|hermes|reasonix>
python runner/run_all5.py   # run all agents sequentially
```

## Key findings (2026-08-10)

- codex: fastest (36.5s/task) but systematically deletes input files without a prompt constraint
- reasonix: 39.6s/task, 95%+ prefix-cache hit rate, cheapest to run
- hermes: 45.3s/task, most complete toolset (search + image gen + skills + MCP)
- opencode: 50.6s/task, most reliable, zero extra dependencies
- omp: 153s/task, fewest tool calls, but slow
- mimo: 198.7s/task, no unique advantage over opencode

Ranking rule: pass rate first, then speed among full-pass agents.

## Windows notes

- hermes tools resolve cwd to ~ and strip drive letters from Windows paths — use MSYS `/d/...` paths
- mimo requires `opencode-zen/` model prefix (not `opencode/`)
- codex needs a prompt constraint: "Keep all input files intact"

See `results2/CAPABILITY_MATRIX.md` for the full capability comparison.