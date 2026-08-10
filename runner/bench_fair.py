#!/usr/bin/env python3
"""CLI Agent Benchmark 统一后端版本(sensenova deepseek-v4-flash)"""
import os, subprocess, sys, re, json, shutil

def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()

TASKS = []

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
    prompt="在当前目录创建一个 Python 脚本 fruit_summary.py:读取 data.txt,每行是 水果名 数量,统计每种水果的总数量,按数量降序打印。运行并验证。验收:apple=21, banana=7, orange=7。"))

def t2_setup(d):
    with open(os.path.join(d, 'sales.csv'), 'w') as f:
        f.write("date,region,product,amount\n2026-01-05,North,Widget,120.50\n2026-01-06,South,Gadget,85.00\n2026-01-07,North,Gadget,45.25\n2026-01-08,South,Widget,60.00\n2026-01-09,North,Widget,33.75\n2026-01-10,South,Gadget,150.00\n")
def t2_verify(d):
    p = os.path.join(d, 'sales_report.py')
    if not os.path.exists(p): return False, "缺少 sales_report.py"
    code, out = _run(f'python {p} sales.csv', d)
    if code != 0: return False, f"运行失败: {out}"
    if 'North' not in out or '199.5' not in out and '199.50' not in out: return False, f"North 总额不对: {out}"
    if 'South' not in out or '295' not in out: return False, f"South 总额不对: {out}"
    return True, f"输出正确: {out[:120]}"
TASKS.append(dict(id='T2', name='sales_report', setup=t2_setup, verify=t2_verify,
    prompt="创建 sales_report.py,接收 CSV 文件路径参数,按 region 分组求和 amount,降序打印。验收:North=199.50, South=295.00。"))

def t3_setup(d):
    with open(os.path.join(d, 'bank.py'), 'w') as f:
        f.write("""class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner; self.balance = balance
    def deposit(self, amount): self.balance += amount
    def withdraw(self, amount):
        if amount > self.balance: raise ValueError("insufficient funds")
        self.balance -= amount
    def transfer(self, target, amount):
        self.withdraw(amount); target.deposit(amount)
""")
    with open(os.path.join(d, 'test_bank.py'), 'w') as f:
        f.write("""import unittest; from bank import Account
class TestAccount(unittest.TestCase):
    def test_deposit(self):
        a = Account("alice"); a.deposit(50); self.assertEqual(a.balance, 50)
    def test_withdraw_overdraft(self):
        a = Account("bob", 10)
        with self.assertRaises(ValueError): a.withdraw(20)
    def test_transfer(self):
        a = Account("alice", 100); b = Account("bob")
        a.transfer(b, 40); self.assertEqual(a.balance, 60); self.assertEqual(b.balance, 40)
if __name__ == "__main__": unittest.main()
""")
def t3_verify(d):
    code, out = _run(f'python -m unittest test_bank -v', d)
    if code != 0: return False, f"测试失败: {out[-500:]}"
    if 'OK' not in out: return False, f"测试未通过: {out[-300:]}"
    return True, f"3 个测试全部通过"
TASKS.append(dict(id='T3', name='bank_tests', setup=t3_setup, verify=t3_verify,
    prompt="运行 python -m unittest test_bank -v,如果失败则修复 bank.py(不改 test_bank.py),直到全部通过。"))

def t4_setup(d):
    lines = ["2026-01-15 10:{:02d}:{:02d} [{}] request #{} handler=svc user=u{} msg=processed\n".format(i//60,i%60,"ERROR" if i%3==0 else "INFO",i,i%5) for i in range(200)]
    with open(os.path.join(d, 'app.log'), 'w') as f: f.writelines(lines)
def t4_verify(d):
    p = os.path.join(d, 'log_stats.py')
    if not os.path.exists(p): return False, "缺少 log_stats.py"
    code, out = _run(f'python {p} app.log', d)
    if code != 0: return False, f"运行失败: {out}"
    if not re.search(r'ERROR\D*67', out): return False, f"ERROR 计数不对(应67): {out}"
    return True, f"统计正确: {out[:120]}"
TASKS.append(dict(id='T4', name='log_stats', setup=t4_setup, verify=t4_verify,
    prompt="创建 log_stats.py,接收日志文件路径,统计总行数、ERROR 行数、INFO 行数。验收:总行数200, ERROR=67, INFO=133。"))

def t5_setup(d):
    os.makedirs(os.path.join(d, 'src'), exist_ok=True)
    for i in range(10):
        with open(os.path.join(d, 'src', f'file_{i}.txt'), 'w') as f: f.write(f"content {i}\n" * (i+1))
    with open(os.path.join(d, 'src', 'archive.txt'), 'w') as f: f.write("SECRET\n")
def t5_verify(d):
    p = os.path.join(d, 'scan.py')
    if not os.path.exists(p): return False, "缺少 scan.py"
    code, out = _run(f'python {p} src', d)
    if code != 0: return False, f"运行失败: {out}"
    if '56' not in out: return False, f"总行数不对(应56,含archive.txt): {out}"
    if 'SECRET' not in out: return False, f"应报告含SECRET的文件: {out}"
    return True, f"扫描正确: {out[:150]}"
TASKS.append(dict(id='T5', name='dir_scan', setup=t5_setup, verify=t5_verify,
    prompt="创建 scan.py,接收目录路径,统计所有 .txt 总行数,找出含 SECRET 的文件。验收:总行数56, archive.txt 含 SECRET。"))

def t6_setup(d):
    with open(os.path.join(d, 'words.txt'), 'w') as f: f.write("hello world hello python hello cli benchmark world\n")
def t6_verify(d):
    p = os.path.join(d, 'wordcount.py')
    if not os.path.exists(p): return False, "缺少 wordcount.py"
    code, out = _run(f'python {p} words.txt', d)
    if code != 0: return False, f"运行失败: {out}"
    if not re.search(r'hello\s*[:=]\s*3', out) and 'hello 3' not in out: return False, f"hello 计数不对: {out}"
    if not re.search(r'world\s*[:=]\s*2', out) and 'world 2' not in out: return False, f"world 计数不对: {out}"
    return True, f"词频正确: {out[:150]}"
TASKS.append(dict(id='T6', name='wordcount', setup=t6_setup, verify=t6_verify,
    prompt="创建 wordcount.py,接收文件路径,统计词频,按次数降序同次数字母序打印。验收:hello=3, world=2。"))

def run_task(task, sandbox, agent_cmd, timeout=600):
    sandbox = os.path.abspath(sandbox)
    shutil.rmtree(sandbox, ignore_errors=True); os.makedirs(sandbox)
    task['setup'](sandbox)
    try:
        r = subprocess.run(agent_cmd, cwd=sandbox, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr)[-3000:]; code = r.returncode
    except subprocess.TimeoutExpired:
        return False, "agent 超时", "(timeout)"
    ok, detail = task['verify'](sandbox)
    if code != 0 and ok: detail += f" (agent exit={code})"
    return ok, detail, out[-800:]

if __name__ == '__main__':
    import argparse, time
    ap = argparse.ArgumentParser()
    ap.add_argument('--agent', required=True, choices=['codex','opencode','mimo','omp','hermes','cline'])
    ap.add_argument('--tasks', default='T1,T2,T3,T4,T5,T6')
    ap.add_argument('--out', default='results')
    ap.add_argument('--start', type=int, default=0)
    args = ap.parse_args()

    KEY = os.environ.get('ZEN_API_KEY', '')

    # 统一用 sensenova deepseek-v4-flash
    agent_config = {
        'codex':    ['bash', '-c', 'CODEX_HOME="C:\\Users\\Administrator\\.codex-bench" codex exec -s danger-full-access --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check - < {prompt_file}'],
        'opencode': ['bash', '-c', 'opencode run --pure -m sensenova/deepseek-v4-flash - < {prompt_file}'],
        'mimo':     ['bash', '-c', 'mimo run --pure -m sensenova/deepseek-v4-flash - < {prompt_file}'],
        'omp':      ['bash', '-c', 'omp --model sensenova/deepseek-v4-flash --api-key "$ZEN_API_KEY" -p - < {prompt_file}'],
        'hermes':   ['bash', '-c', 'hermes chat -q "当前工作目录是 {sandbox_abs}。$(cat {prompt_file})\\\n所有文件操作必须用绝对路径 {sandbox_abs}\\\\ 下的文件。" -m "deepseek-v4-flash" --provider "custom:sensenova" -t "file,terminal" --yolo --max-turns 40 --no-restore-cwd 2>&1'],
        'cline':    ['bash', '-c', 'cd {sandbox_abs} && cat {prompt_file} | cline'],
    }

    cmd_tpl = agent_config.get(args.agent, [])
    selected = [t for t in TASKS if t['id'] in args.tasks.split(',')]
    results = {}
    for i, task in enumerate(selected):
        if i < args.start: continue
        sandbox = os.path.abspath(os.path.join('runner', f"{args.agent}_{task['id']}"))
        pf = os.path.abspath(os.path.join('runner', f"{args.agent}_{task['id']}_prompt.txt"))
        with open(pf, 'w', encoding='utf-8') as f: f.write(task['prompt'])
        cmd = [c.replace('{prompt_file}', '"' + pf.replace('\\', '\\\\') + '"').replace('{sandbox_abs}', sandbox.replace('\\', '/')) for c in cmd_tpl]
        t0 = time.time()
        ok, detail, tail = run_task(task, sandbox, cmd)
        dt = round(time.time() - t0, 1)
        results[task['id']] = dict(ok=ok, detail=detail, seconds=dt)
        print(f"[{args.agent}] {task['id']} {task['name']}: {'PASS' if ok else 'FAIL'} ({dt}s) {detail}")
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, f"{args.agent}_{task['id']}.log"), 'w', encoding='utf-8') as f: f.write(tail)
    with open(os.path.join(args.out, f"{args.agent}_summary.json"), 'w', encoding='utf-8') as f: json.dump(results, f, ensure_ascii=False, indent=1)
    print(f"\n{args.agent} 汇总: {json.dumps(results, ensure_ascii=False)}")