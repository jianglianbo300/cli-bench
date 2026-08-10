#!/usr/bin/env python3
"""CLI Agent Benchmark v2 - every agent actually does the work + uniform verify.

Fixes over bench.py / bench_fair.py:
  1. Prompts are ENGLISH.  Chinese-via-stdin hangs cline (2~3s exit, no file).
  2. EVERY agent runs inside its own sandbox dir (cd first) -> no stray-file bug.
  3. The absolute sandbox path is injected into every prompt (hermes terminal
     cwd is pinned to Desktop; cline used to drop files in the wrong dir).
  4. Each agent gets its own correct, non-interactive invocation.
  5. FAIR core = opencode-zen/deepseek-v4-flash-free for codex/opencode/mimo/
     omp/hermes.  cline CANNOT use that provider (tool protocol mismatch), so
     it runs on its own OAuth channel and is reported SEPARATELY, never ranked
     inside the same-model table.

Usage (from D:\\work\\cli-bench, with ZEN_API_KEY exported and, for codex,
the local gateway at :8899 up):
    python runner\\bench2.py --agent codex|opencode|mimo|omp|hermes|cline

Preflight (no key / no gateway) aborts with a clear message instead of a
silent 2-second "FAIL".
"""
import os, re, sys, json, shutil, time, subprocess, argparse

# ---------------------------------------------------------------- tasks
def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True,
                       timeout=120, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout + r.stderr).strip()

def t1_setup(d):
    with open(os.path.join(d, 'data.txt'), 'w') as f:
        f.write("apple 10\nbanana 5\napple 3\norange 7\nbanana 2\napple 8\n")
def t1_verify(d):
    p = os.path.join(d, 'fruit_summary.py')
    if not os.path.exists(p): return False, "missing fruit_summary.py"
    code, out = _run(f'python {p}', d)
    if code != 0: return False, f"run error: {out}"
    if 'apple' not in out or '21' not in out: return False, f"no apple=21: {out}"
    if 'banana' not in out or '7' not in out: return False, f"no banana=7: {out}"
    if 'orange' not in out or '7' not in out: return False, f"no orange=7: {out}"
    return True, f"output ok: {out[:100]}"
def t1_prompt(sandbox):
    return (f"WORKING DIRECTORY (absolute path, files MUST be created here): {sandbox}\n"
            "Create a Python script named fruit_summary.py in this directory. It must read "
            "data.txt (each line: '<fruit> <count>') and print the total count per fruit, "
            "sorted by count descending, format '<fruit> <count>' on each line, e.g. 'apple 21'. "
            "Run your script and make sure the output is correct.\n"
            "Acceptance: script runs and prints apple=21, banana=7, orange=7.")

def t2_setup(d):
    with open(os.path.join(d, 'sales.csv'), 'w') as f:
        f.write("date,region,product,amount\n2026-01-05,North,Widget,120.50\n"
                "2026-01-06,South,Gadget,85.00\n2026-01-07,North,Gadget,45.25\n"
                "2026-01-08,South,Widget,60.00\n2026-01-09,North,Widget,33.75\n"
                "2026-01-10,South,Gadget,150.00\n")
def t2_verify(d):
    p = os.path.join(d, 'sales_report.py')
    if not os.path.exists(p): return False, "missing sales_report.py"
    code, out = _run(f'python {p} sales.csv', d)
    if code != 0: return False, f"run error: {out}"
    if 'North' not in out or ('199.5' not in out and '199.50' not in out):
        return False, f"North total wrong: {out}"
    if 'South' not in out or '295' not in out: return False, f"South total wrong: {out}"
    return True, f"output ok: {out[:120]}"
def t2_prompt(sandbox):
    return (f"WORKING DIRECTORY (absolute path, files MUST be created here): {sandbox}\n"
            "Create a Python script named sales_report.py. It takes a CSV path argument "
            "(run as: python sales_report.py sales.csv). The CSV has columns "
            "date,region,product,amount. Group amount by region, sum it, and print "
            "'<region> <sum>' per region sorted by sum descending.\n"
            "Acceptance: North=199.50, South=295.00 (any float format ok).")

def t3_setup(d):
    with open(os.path.join(d, 'bank.py'), 'w') as f:
        f.write("""class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner; self.balance = balance
    def deposit(self, amount): self.balance += amount
    def withdraw(self, amount):
        if amount > self.balance: raise ValueError("insufficient funds")
        self.balance -= amount
    def transfer(self, target, amount): self.withdraw(amount); target.deposit(amount)
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
    code, out = _run('python -m unittest test_bank -v', d)
    if code != 0: return False, f"tests failed: {out[-500:]}"
    if 'OK' not in out: return False, f"not OK: {out[-300:]}"
    return True, "3 tests passed"
def t3_prompt(sandbox):
    return (f"WORKING DIRECTORY (absolute path): {sandbox}\n"
            "Run 'python -m unittest test_bank -v' in this directory. There is a bug in "
            "bank.py (an Account class with deposit/withdraw/transfer). Fix ONLY bank.py "
            "(do NOT modify test_bank.py) until all unit tests pass.\n"
            "Acceptance: all 3 tests pass.")


def t4_setup(d):
    lines = ["2026-01-15 10:{:02d}:{:02d} [{}] request #{} handler=svc user=u{} msg=processed\n"
             .format(i//60, i%60, "ERROR" if i%3==0 else "INFO", i, i%5) for i in range(200)]
    with open(os.path.join(d, 'app.log'), 'w') as f: f.writelines(lines)
def t4_verify(d):
    p = os.path.join(d, 'log_stats.py')
    if not os.path.exists(p): return False, "missing log_stats.py"
    code, out = _run(f'python {p} app.log', d)
    if code != 0: return False, f"run error: {out}"
    if '200' not in out: return False, f"no total 200: {out}"
    if '67' not in out: return False, f"no ERROR 67: {out}"
    if '133' not in out: return False, f"no INFO 133: {out}"
    return True, f"stats ok: {out[:120]}"
def t4_prompt(sandbox):
    return (f"WORKING DIRECTORY (absolute path, files MUST be created here): {sandbox}\n"
            "Create a Python script named log_stats.py. It takes a log file path argument "
            "(run as: python log_stats.py app.log). Each line has a [LEVEL] tag (INFO/ERROR). "
            "Print three lines: 'Total lines: N', 'ERROR: N', 'INFO: N'.\n"
            "Acceptance: Total lines=200, ERROR=67, INFO=133.")

def t5_setup(d):
    os.makedirs(os.path.join(d, 'src'), exist_ok=True)
    open(os.path.join(d, 'src', 'archive.txt'), 'w').write("SECRET=abc")
    for i in range(10):
        open(os.path.join(d, 'src', f'file_{i}.txt'), 'w').write("line " * (i + 1))
def t5_verify(d):
    p = os.path.join(d, 'scan.py')
    if not os.path.exists(p): return False, "missing scan.py"
    code, out = _run(f'python {p} src', d)
    if code != 0: return False, f"run error: {out}"
    if 'archive.txt' not in out: return False, f"archive.txt not listed: {out}"
    return True, f"scan ok: {out[:120]}"
def t5_prompt(sandbox):
    return (f"WORKING DIRECTORY (absolute path, files MUST be created here): {sandbox}\n"
            "Create a Python script named scan.py. It takes a directory path argument "
            "(run as: python scan.py src). Recursively scan it and print the total number of "
            "lines across all files, then list every file whose content contains 'SECRET'.\n"
            "Acceptance: it reports archive.txt as containing SECRET.")

def t6_setup(d):
    with open(os.path.join(d, 'words.txt'), 'w') as f:
        f.write("hello world hello python hello cli benchmark world\n")
def t6_verify(d):
    p = os.path.join(d, 'wordcount.py')
    if not os.path.exists(p): return False, "missing wordcount.py"
    code, out = _run(f'python {p} words.txt', d)
    if code != 0: return False, f"run error: {out}"
    if not re.search(r'hello\s*[:=]\s*3', out): return False, f"hello count wrong: {out}"
    if not re.search(r'world\s*[:=]\s*2', out): return False, f"world count wrong: {out}"
    return True, f"wordcount ok: {out[:150]}"
def t6_prompt(sandbox):
    return (f"WORKING DIRECTORY (absolute path, files MUST be created here): {sandbox}\n"
            "IMPORTANT: Keep all input files (words.txt) intact. Do NOT delete or overwrite existing files.\n"
            "Create a Python script named wordcount.py. It takes a file path argument "
            "(run as: python wordcount.py words.txt). Count word frequencies, print "
            "'<word>: <count>' sorted by count descending then alphabetically for ties.\n"
            "Acceptance: hello: 3, world: 2.")

TASKS = [
    ('T1','fruit_summary',t1_setup,t1_verify,t1_prompt),
    ('T2','sales_report', t2_setup,t2_verify,t2_prompt),
    ('T3','bank_tests',   t3_setup,t3_verify,t3_prompt),
    ('T4','log_stats',    t4_setup,t4_verify,t4_prompt),
    ('T5','dir_scan',     t5_setup,t5_verify,t5_prompt),
    ('T6','wordcount',    t6_setup,t6_verify,t6_prompt),
]


# ---------------------------------------------------------------- harness
def _run_cmd(cmd, cwd, timeout):
    """Run a command, guaranteeing return within `timeout` seconds by
    force-killing the WHOLE process tree on Windows (grandchildren like
    node/mimo otherwise keep the stdout pipe open and deadlock the read)."""
    import threading
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True,
                             encoding='utf-8', errors='replace',
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    except Exception as e:
        return -1, f"launch error: {e}"
    buf = {'out': [], 'err': []}
    def _read(stream, key):
        try:
            for line in iter(stream.readline, ''):
                buf[key].append(line)
        except Exception:
            pass
        try: stream.close()
        except Exception: pass
    t1 = threading.Thread(target=_read, args=(p.stdout, 'out')); t1.daemon = True
    t2 = threading.Thread(target=_read, args=(p.stderr, 'err')); t2.daemon = True
    t1.start(); t2.start()
    try:
        rc = p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(p.pid)],
                       capture_output=True, shell=False)
        try: rc = p.wait(timeout=20)
        except Exception: rc = -1
    t1.join(timeout=5); t2.join(timeout=5)
    tail = ''.join(buf['out']) + ''.join(buf['err'])
    return rc, tail[-3000:]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--agent', required=True,
                        choices=['codex','opencode','reasonix','mimo','omp','hermes','cline'])
    ap.add_argument('--tasks', default='T1,T2,T3,T4,T5,T6')
    ap.add_argument('--out', default='results2')
    ap.add_argument('--timeout', type=int, default=600, help='per-task timeout (s)')
    args = ap.parse_args()
    agent = args.agent
    KEY = os.environ.get('ZEN_API_KEY', '')

    bashwrap = lambda body: ['C:/Program Files/Git/bin/bash.exe','-lc', body]
    _set_cmd = 'export PATH="/c/Users/Administrator/AppData/Roaming/npm:$PATH"; '
    cfg = {
        # codex: needs its own gateway at :8899 (galaxy-yearn / bench-zen).
        'codex': bashwrap(
            _set_cmd + 'cd "{sb}" && CODEX_HOME="C:\\Users\\Administrator\\.codex-bench" '
            'codex exec -s danger-full-access --dangerously-bypass-approvals-and-sandbox '
            '--skip-git-repo-check - < "{pf}"'),
        'opencode': bashwrap(
                    _set_cmd + 'cd "{sb}" && opencode run --pure -m opencode/deepseek-v4-flash-free - < "{pf}"'),
                'reasonix': bashwrap(
                    _set_cmd + 'cd "{sb}" && reasonix run "$(cat {pf})" '
                    '--permission-mode bypassPermissions --model omniroute --dir "{sb}" --print '
                    '--metrics "{sb}/reasonix_metrics.json" 2>&1'),
        'mimo': bashwrap(
            _set_cmd + 'cd "{sb}" && mimo run --pure -m opencode-zen/deepseek-v4-flash-free - < "{pf}"'),
        'omp': bashwrap(
            _set_cmd + 'cd "{sb}" && omp --model sensenova/deepseek-v4-flash '
            '--api-key "$ZEN_API_KEY" -p - < "{pf}"'),
        'hermes': bashwrap(
            _set_cmd + 'cd "{sb}" && hermes chat -q "$(cat {pf})" '
            '-m omniroute-deepseek-v4-flash '
            '--provider custom:omniroute -t file,terminal --yolo --max-turns 40 '
            '--no-restore-cwd 2>&1'),
        'cline': bashwrap(
            _set_cmd + 'cd "{sb}" && cline -P cline --cwd "{sb}" "$(cat \'{pf}\')"'),
    }

    # ---- preflight: refuse silent 2s failures ----
    if agent == 'omp' and not KEY:
        sys.exit("[preflight] omp needs ZEN_API_KEY env var (currently empty). Abort.")
    if agent == 'codex':
        try:
            sock = __import__('socket').socket()
            sock.settimeout(1.0); sock.connect(('127.0.0.1', 4202)); sock.close()
        except Exception:
            sys.exit("[preflight] codex gateway (:4202) NOT reachable. Abort.")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # D:\work\cli-bench
    outdir = os.path.join(root, args.out)
    os.makedirs(outdir, exist_ok=True)

    results = {}
    for tid, name, ssetup, sverify, sprompt in TASKS:
        if tid not in args.tasks.split(','): continue
        sb = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          f"{agent}_{tid}"))
        shutil.rmtree(sb, ignore_errors=True); os.makedirs(sb, exist_ok=True)
        ssetup(sb)
        pf = os.path.join(os.path.dirname(sb), f"{agent}_{tid}_prompt.txt")
        # hermes file/terminal tools resolve the cwd to ~ (C:\Users\Administrator)
        # and strip the drive letter from Windows paths (D:\x -> \x relative to ~).
        # MSYS /d/... paths are the only format its tools resolve correctly.
        disp = sb
        if agent == 'hermes':
            disp = '/' + sb[0].lower() + sb[2:].replace('\\', '/')
        with open(pf, 'w', encoding='utf-8') as f: f.write(sprompt(disp))
        # codex: 统一追加"保留输入文件"约束（模拟 AGENTS.md 防护效果）
        if agent == 'codex':
            with open(pf, 'a', encoding='utf-8') as f:
                f.write("\nIMPORTANT: Keep all existing input files. Do NOT delete or overwrite any file in the working directory.\n")
        cmd = cfg[agent].copy()
        cmd[-1] = cmd[-1].replace('{sb}', disp).replace('{pf}', pf.replace('\\','/'))
        # free-tier upstreams flake (UnknownError/server error/429) — retry only
        # on transient signals, on a FRESH sandbox each attempt.
        TRANSIENT = ('unknown error','server error','unexpected server','rate limit',
                     '429','too many','timed out','timeout','etimedout','econnreset',
                     'econnrefused','temporarily','5 0 3','internal server')
        ok, detail, tail = False, '', ''
        attempts = 0; dt = 0.0
        while attempts < 3 and not ok:
            shutil.rmtree(sb, ignore_errors=True); os.makedirs(sb, exist_ok=True)
            ssetup(sb)
            t0 = time.time()
            code, tail = _run_cmd(cmd, sb, args.timeout)
            ok, detail = sverify(sb)
            dt += round(time.time() - t0, 1)
            attempts += 1
            if not ok and not any(k in (tail or '').lower() for k in TRANSIENT):
                break  # deterministic failure — don't waste retries on it
        results[tid] = dict(ok=ok, detail=detail, seconds=dt, attempts=attempts)
        print(f"[{agent}] {tid} {name}: {'PASS' if ok else 'FAIL'} ({dt}s, {attempts} attempt(s)) {detail}")
        with open(os.path.join(outdir, f"{agent}_{tid}.log"), 'w', encoding='utf-8') as f:
            f.write(tail)
    with open(os.path.join(outdir, f"{agent}_summary.json"), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(f"\n{agent} summary: {json.dumps(results, ensure_ascii=False)}")

if __name__ == '__main__':
    main()

