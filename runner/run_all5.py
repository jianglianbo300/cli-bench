#!/usr/bin/env python3
"""Run the full fair-core benchmark for all 5 agents sequentially (T1-T6),
writing per-agent summary JSON via bench2.py and a combined progress log."""
import os, sys, time, json, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, 'bench2.py')
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'results2')
LOG = os.path.join(OUT, 'run_all5.log')

AGENTS = ['opencode', 'mimo', 'omp', 'hermes', 'codex']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--agents', default=','.join(AGENTS),
                    help='comma separated subset/order of agents')
    ap.add_argument('--tasks', default='T1,T2,T3,T4,T5,T6')
    ap.add_argument('--timeout', type=int, default=600)
    args = ap.parse_args()
    agents = [a.strip() for a in args.agents.split(',') if a.strip()]

    os.makedirs(OUT, exist_ok=True)
    env = dict(os.environ)
    env['ZEN_API_KEY'] = os.environ.get('ZEN_API_KEY', '')
    final = {}
    with open(LOG, 'a', encoding='utf-8') as lf:
        lf.write(f"\n=== RUN START {time.strftime('%Y-%m-%d %H:%M:%S')} agents={agents} ===\n")
        for agent in agents:
            t0 = time.time()
            cmd = [sys.executable, BENCH, '--agent', agent, '--tasks', args.tasks,
                   '--timeout', str(args.timeout), '--out', 'results2']
            lf.write(f"\n--- [{agent}] launching {time.strftime('%H:%M:%S')} ---\n")
            lf.flush()
            r = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
            dt = round(time.time() - t0, 1)
            tail = (r.stdout or '') + ('\n[stderr]\n' + r.stderr if r.stderr else '')
            lf.write(tail[-4000:] + f"\n  ({agent} wall={dt}s rc={r.returncode})\n")
            lf.flush()
            summ = os.path.join(OUT, f"{agent}_summary.json")
            if os.path.exists(summ):
                with open(summ, encoding='utf-8') as f:
                    final[agent] = json.load(f)
            else:
                final[agent] = {'error': 'no summary', 'rc': r.returncode}
        with open(os.path.join(OUT, 'all5_final.json'), 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=1)
        lf.write(f"\n=== RUN END {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    print('ALL DONE')

if __name__ == '__main__':
    main()
