#!/usr/bin/env python3
"""Web search for Codex using Bing (no API key, works in China).
Parses Bing SERP: each result is a <li class="b_algo"> block with a <h2> title link.
"""
import urllib.request, urllib.parse, re, sys, json

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='replace')

def unhtml(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    s = s.replace('&#39;', "'").replace('&quot;', '"').replace('&nbsp;', ' ')
    return s.strip()

def search_bing(query, num=5):
    html = fetch(f"https://www.bing.com/search?q={urllib.parse.quote(query)}&mkt=zh-CN")
    results = []
    # Split into b_algo blocks, then extract title link + snippet from each
    for block in re.split(r'<li class="b_algo"', html)[1:]:
        h2 = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not h2:
            continue
        url = h2.group(1)
        title = unhtml(h2.group(2))
        p = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
        snippet = unhtml(p.group(1)) if p else ''
        results.append({"title": title, "url": url, "snippet": snippet})
        if len(results) >= num:
            break
    return results

if __name__ == '__main__':
    q = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not q:
        print("Usage: python web_search.py <query>")
        sys.exit(1)
    results = search_bing(q)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not results:
        print(f'[No results for "{q}"]', file=sys.stderr)