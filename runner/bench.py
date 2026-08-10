#!/usr/bin/env python3
"""CLI Agent Benchmark 任务集定义 + 验收脚本。

每个任务:
  - setup(dir): 在沙箱目录准备起始文件
  - prompt: 给 agent 的任务描述(中文,标注验收标准)
  - verify(dir): 验收,返回 (bool, 详情字符串)

任务风格参照 Terminal-Bench:文件操作/数据处理/脚本编写/系统管理,
全部在本地可跑,自动验收,不依赖网络。
"""
import os, subprocess, sys, re, json, shutil

# ---------------------------------------------------------------- 任务定义

def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()

TASKS = []

# ---------- T1: 脚本编写 + 测试 ----------
def t1_setup(d):
    with open(os.path.join(d, 'data.txt'), 'w') as f:
        f.write("apple 10\nbanana 5\napple 3\norange 7\nbanana 2\napple 8\n")
def t1_verify(d):
    p = os.path.join(d, 'fruit_summary.py')
    if not os.path.exists(p): return False, "缺少 fruit_summary.py"
    code, out = _run(f'python {p}', d)
    if code != 0: return False, f"运行失败: {out}"
    if 'apple' not in out or '21' not in out: return False, f"输出不含 apple=21: {out}"
    if 'banana' not in out or '7' not in out: return False, f"输出不含 banana=7: {out}"
    if 'orange' not in out or '7' not in out: return False, f"输出不含 orange=7: {out}"
    return True, f"输出正确: {out[:100]}"

TASKS.append(dict(id='T1', name='fruit_summary', setup=t1_setup, verify=t1_verify,
    prompt="""在当前目录创建一个 Python 脚本 fruit_summary.py:
读取 data.txt,每行是 "水果名 数量",统计每种水果的总数量,按数量降序打印。
输出格式:每行 "水果名 数量",例如 "apple 21"。
运行你的脚本并确保输出正确。验收标准:脚本能运行,apple=21, banana=7, orange=7。"""))

# ---------- T2: 数据处理 CSV ----------
def t2_setup(d):
    with open(os.path.join(d, 'sales.csv'), 'w') as f:
        f.write("date,region,product,amount\n2026-01-05,North,Widget,120.50\n2026-01-06,South,Gadget,85.00\n2026-01-07,North,Gadget,45.25\n2026-01-08,South,Widget,60.00\n2026-01-09,North,Widget,33.75\n2026-01-10,South,Gadget,150.00\n")
def t2_verify(d):
    p = os.path.join(d, 'sales_report.py')
    if not os.path.exists(p): return False, "缺少 sales_report.py"
    code, out = _run(f'python {p} sales.csv', d)
    if code != 0: return False, f"运行失败: {out}"
    # North = 120.50+45.25+33.75 = 199.50; South = 85+60+150 = 295.00
    if 'North' not in out or '199.5' not in out and '199.50' not in out: return False, f"North 总额不对: {out}"
    if 'South' not in out or '295' not in out: return False, f"South 总额不对: {out}"
    return True, f"输出正确: {out[:120]}"

TASKS.append(dict(id='T2', name='sales_report', setup=t2_setup, verify=t2_verify,
    prompt="""在当前目录创建一个 Python 脚本 sales_report.py:
接收一个 CSV 文件路径参数(如 sales_report.py sales.csv),CSV 含列 date,region,product,amount。
按 region 分组求和 amount,按总额降序打印 "region 总额"。
验收标准:North=199.50, South=295.00(用任意格式的浮点数表示均可)。"""))

# ---------- T3: 多文件脚本 + 单元测试 ----------
def t3_setup(d):
    with open(os.path.join(d, 'bank.py'), 'w') as f:
        f.write("""class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("insufficient funds")
        self.balance -= amount

    def transfer(self, target, amount):
        self.withdraw(amount)
        target.deposit(amount)
""")
    with open(os.path.join(d, 'test_bank.py'), 'w') as f:
        f.write("""import unittest
from bank import Account

class TestAccount(unittest.TestCase):
    def test_deposit(self):
        a = Account("alice")
        a.deposit(50)
        self.assertEqual(a.balance, 50)

    def test_withdraw_overdraft(self):
        a = Account("bob", 10)
        with self.assertRaises(ValueError):
            a.withdraw(20)

    def test_transfer(self):
        a = Account("alice", 100)
        b = Account("bob")
        a.transfer(b, 40)
        self.assertEqual(a.balance, 60)
        self.assertEqual(b.balance, 40)

if __name__ == "__main__":
    unittest.main()
""")
def t3_verify(d):
    code, out = _run(f'python -m unittest test_bank -v', d)
    if code != 0: return False, f"测试失败: {out[-500:]}"
    if 'OK' not in out: return False, f"测试未通过: {out[-300:]}"
    return True, f"3 个测试全部通过"

TASKS.append(dict(id='T3', name='bank_tests', setup=t3_setup, verify=t3_verify,
    prompt="""当前目录有 bank.py(银行账户类)和 test_bank.py(单元测试)。
运行单元测试:python -m unittest test_bank -v
如果测试失败,修复 bank.py 中的代码(不要修改测试文件),直到所有测试通过。
验收标准:unittest 输出 OK,3 个测试全部通过。"""))

# ---------- T4: 系统管理 - 日志分析 ----------
def t4_setup(d):
    lines = []
    for i in range(200):
        level = "INFO" if i % 3 else "ERROR"
        lines.append(f"2026-01-15 10:{i//60:02d}:{i%60:02d} [{level}] request #{i} handler=svc user=u{i%5} msg=processed\n")
    with open(os.path.join(d, 'app.log'), 'w') as f:
        f.writelines(lines)
def t4_verify(d):
    p = os.path.join(d, 'log_stats.py')
    if not os.path.exists(p): return False, "缺少 log_stats.py"
    code, out = _run(f'python {p} app.log', d)
    if code != 0: return False, f"运行失败: {out}"
    m = re.search(r'ERROR\D+(\d+)', out)
    if not m or int(m.group(1)) != 67: return False, f"ERROR 计数不对(应67): {out}"
    return True, f"统计正确: {out[:120]}"

TASKS.append(dict(id='T4', name='log_stats', setup=t4_setup, verify=t4_verify,
    prompt="""当前目录有 app.log,每行含 [LEVEL] 标记(INFO/ERROR)。
创建 Python 脚本 log_stats.py,接收日志文件路径参数,统计:
1. 总行数
2. ERROR 行数(200行中 i%3==0 的,即 index 0,3,6... 共 67 行)
3. INFO 行数
打印三行 "总行数: N" / "ERROR: N" / "INFO: N"。
验收标准:ERROR 计数为 67,总行数 200。"""))

# ---------- T5: 脚本 + 文件系统操作 ----------
def t5_setup(d):
    os.makedirs(os.path.join(d, 'src'), exist_ok=True)
    for i in range(10):
        with open(os.path.join(d, 'src', f'file_{i}.txt'), 'w') as f:
            f.write(f"content {i}\n" * (i + 1))
    # 一个隐藏的归档
    with open(os.path.join(d, 'src', 'archive.txt'), 'w') as f:
        f.write("SECRET\n")
def t5_verify(d):
    p = os.path.join(d, 'scan.py')
    if not os.path.exists(p): return False, "缺少 scan.py"
    code, out = _run(f'python {p} src', d)
    if code != 0: return False, f"运行失败: {out}"
    if '56' not in out: return False, f"总行数不对(应56,含archive.txt): {out}"
    if 'SECRET' not in out: return False, f"应报告含 SECRET 的文件: {out}"
    return True, f"扫描正确: {out[:150]}"

TASKS.append(dict(id='T5', name='dir_scan', setup=t5_setup, verify=t5_verify,
    prompt="""当前目录有 src/ 文件夹,内含 file_0.txt 到 file_9.txt(行数 = 编号+1)和 archive.txt。
创建 Python 脚本 scan.py,接收目录路径参数:
1. 统计该目录下所有 .txt 文件的总行数
2. 找出内容包含 "SECRET" 的文件并打印文件名
打印 "总行数: N" 和 "含SECRET: 文件名"。
验收标准:总行数 56(含 archive.txt 的 1 行),报告 archive.txt 含 SECRET。"""))

# ---------- T6: 综合 - 构建小工具 + 验收 ----------
def t6_setup(d):
    with open(os.path.join(d, 'words.txt'), 'w') as f:
        f.write("hello world hello python hello cli benchmark world\n")
def t6_verify(d):
    p = os.path.join(d, 'wordcount.py')
    if not os.path.exists(p): return False, "缺少 wordcount.py"
    code, out = _run(f'python {p} words.txt', d)
    if code != 0: return False, f"运行失败: {out}"
    # 兼容各种输出格式: hello:3, hello=3, hello  3 等
    if not re.search(r'hello\s*[:=]\s*3', out) and 'hello 3' not in out:
        return False, f"hello 计数不对: {out}"
    if not re.search(r'world\s*[:=]\s*2', out) and 'world 2' not in out:
        return False, f"world 计数不对: {out}"
    return True, f"词频正确: {out[:150]}"

TASKS.append(dict(id='T6', name='wordcount', setup=t6_setup, verify=t6_verify,
    prompt="""当前目录有 words.txt 一行文本。
创建 Python 脚本 wordcount.py,接收文件路径参数,统计每个单词出现次数,
按次数降序、同次数按字母序打印 "单词: 次数"。
验收标准:hello: 3, world: 2(其余各1),顺序按频次降序。"""))

# ---------------------------------------------------------------- 运行器

def run_task(task, sandbox, agent_cmd, timeout=600):
    """在 sandbox 目录跑一个任务的 agent 调用。返回 (verified, detail, output_tail)"""
    sandbox = os.path.abspath(sandbox)
    shutil.rmtree(sandbox, ignore_errors=True)
    os.makedirs(sandbox, exist_ok=True)
    task['setup'](sandbox)
    try:
        r = subprocess.run(agent_cmd, cwd=sandbox, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr)[-3000:]
        code = r.returncode
    except subprocess.TimeoutExpired:
        return False, "agent 超时", "(timeout)"
    ok, detail = task['verify'](sandbox)
    if code != 0 and ok:
        # 有点怪但验收过了就算过;记下 exit code
        detail += f" (agent exit={code})"
    return ok, detail, out[-800:]

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--agent', required=True, choices=['codex', 'opencode', 'mimo', 'omp', 'cline', 'hermes'])
    ap.add_argument('--tasks', default='T1,T2,T3,T4,T5,T6')
    ap.add_argument('--out', default='results')
    ap.add_argument('--start', type=int, default=0)
    args = ap.parse_args()

    KEY = os.environ.get('ZEN_API_KEY', '')
    if args.agent == 'codex':
        cmd_tpl = ['bash', '-c', 'CODEX_HOME="C:\\Users\\Administrator\\.codex-bench" codex exec -s danger-full-access --skip-git-repo-check - < {prompt_file}']
    elif args.agent == 'mimo':
        cmd_tpl = ['bash', '-c', 'mimo run --pure -m opencode-zen/deepseek-v4-flash-free - < {prompt_file}']
    elif args.agent == 'omp':
        cmd_tpl = ['bash', '-c', 'omp --model opencode-zen/deepseek-v4-flash-free --api-key "$ZEN_API_KEY" -p - < {prompt_file}']
    elif args.agent == 'cline':
        cmd_tpl = ['bash', '-c', 'cd {sandbox_abs} && cat {prompt_file} | cline']
    elif args.agent == 'hermes':
        # hermes 的 terminal 固化为 Desktop cwd,必须显式告知绝对路径
        cmd_tpl = ['bash', '-c', 'hermes chat -q "当前工作目录是 {sandbox_abs}。$(cat {prompt_file})\\n\\n所有文件操作必须使用绝对路径 {sandbox_abs}\\\\ 下的文件,把脚本保存为 {sandbox_abs}\\\\下的指定文件名(不要用临时文件验证,不要清理产物)。" -m "deepseek-v4-flash-free" --provider "custom:opencode-zen" -t "file,terminal" --yolo --max-turns 40 --no-restore-cwd 2>&1']
    else:
        cmd_tpl = ['bash', '-c', 'opencode run --pure -m opencode/deepseek-v4-flash-free - < {prompt_file}']

    selected = [t for t in TASKS if t['id'] in args.tasks.split(',')]
    results = {}
    for i, task in enumerate(selected):
        if i < args.start: continue
        sandbox = os.path.abspath(os.path.join('runner', f"{args.agent}_{task['id']}"))
        prompt = task['prompt']
        # 写 prompt 到临时文件,避免引号转义
        pf = os.path.abspath(os.path.join('runner', f"{args.agent}_{task['id']}_prompt.txt"))
        with open(pf, 'w', encoding='utf-8') as f:
            f.write(prompt)
        cmd = [c.replace('{prompt_file}', '"' + pf.replace('\\', '\\\\') + '"').replace('{sandbox_abs}', sandbox.replace('\\', '/')) for c in cmd_tpl]
        import time
        t0 = time.time()
        ok, detail, tail = run_task(task, sandbox, cmd)
        dt = round(time.time() - t0, 1)
        results[task['id']] = dict(ok=ok, detail=detail, seconds=dt)
        print(f"[{args.agent}] {task['id']} {task['name']}: {'PASS' if ok else 'FAIL'} ({dt}s) {detail}")
        # 保存输出尾巴
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, f"{args.agent}_{task['id']}.log"), 'w', encoding='utf-8') as f:
            f.write(tail)
    with open(os.path.join(args.out, f"{args.agent}_summary.json"), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(f"\n{args.agent} 汇总: " + json.dumps(results, ensure_ascii=False))
