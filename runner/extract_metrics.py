import re, os

logs_dir = r"D:\work\cli-bench\results2"
agents = ['codex', 'hermes', 'opencode', 'omp', 'mimo']
tasks = [f'T{i}' for i in range(1,7)]

patterns = {
    'codex':   {'tokens': r'tokens used\s*[: ]*([\d,]+)', 'actions': r'token'},
    'hermes':  {'tokens': r'tokens? used|token usage', 'actions': r'✍️.*write|💻.*\$'},
    'opencode':{'tokens': r'tokens? used', 'actions': r'→\s|←\s|\$\s'},
    'omp':     {'tokens': r'tokens? used', 'actions': r'python|write|Done'},
    'mimo':    {'tokens': r'tokens? used', 'actions': r'→\s|←\s|\$\s'},
}

print(f"{'agent':<10}{'task':<6}{'lines':<7}{'actions':<9}{'tokens'}")
print("-"*45)
for a in agents:
    for t in tasks:
        path = os.path.join(logs_dir, f"{a}_{t}.log")
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8', errors='replace') as f:
            content = f.read()
        lines = content.count('\n') + 1
        actions = len(re.findall(patterns[a]['actions'], content))
        tok = re.findall(patterns[a]['tokens'], content)
        tok_str = tok[0] if tok else '-'
        print(f"{a:<10}{t:<6}{lines:<7}{actions:<9}{tok_str}")