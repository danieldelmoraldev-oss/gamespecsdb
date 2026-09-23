#!/usr/bin/env python3
"""Daily automatic update, run by .github/workflows/auto-update.yml (or by hand).

1. Refresh the list of Switch 2 games from the eShop sitemap.
2. Read the two cartridge-format sources and add newly listed games whose title
   matches an eShop page exactly. Anything ambiguous goes to data/review.json.
3. Fetch eShop facts: upcoming, recently released and pending games every day,
   every published game on Mondays (or with --full).
4. Refuse suspicious changes (a released game suddenly shrinking, failed fetches)
   and keep the previous data instead.
5. Publish: apply_curated.py + fetch_eshop.py sync (+ upgrade prices on full runs).

Usage: scripts/auto_update.py [--full] [--dry-run]
"""
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_eshop as eshop  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PHYSICAL = ROOT / 'data' / 'physical.json'
REVIEW = ROOT / 'data' / 'review.json'
GAMES = ROOT / 'src' / 'data' / 'games'
TODAY = dt.date.today()

SOURCES = {
    'game-key-card': 'https://nintendoeverything.com/list-of-all-nintendo-switch-2-games-with-a-game-key-card-release/',
    'full-cartridge': 'https://www.nintendolife.com/guides/every-nintendo-switch-2-physical-release-with-the-full-game-on-the-cart',
}
# Notes in the lists that mean the Western physical release is not what the list says.
REGIONAL = re.compile(r'japan|digital-only|digital only|cancel', re.I)
ROMAN = re.compile(r'^(x{0,3})(ix|iv|v?i{0,3})$')
ROMAN_VALUE = {'i': 1, 'v': 5, 'x': 10}


def roman_to_int(tok):
    if not tok or not ROMAN.match(tok):
        return tok
    total, prev = 0, 0
    for ch in reversed(tok):
        v = ROMAN_VALUE[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return str(total)


def norm_tokens(tokens):
    return '-'.join(roman_to_int(t) for t in tokens if t)


def norm_title(title):
    t = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().lower()
    t = t.replace('&', ' and ').replace('+', ' plus ').replace("'", '').replace('’', '')
    return norm_tokens(re.split(r'[^a-z0-9]+', t))


def norm_key(key):
    return norm_tokens(key.removesuffix('-switch-2').split('-'))


def list_items(url, fmt):
    """Titles from a source page, without bracketed notes; regional exceptions skipped."""
    page = eshop.get(url)
    if fmt == 'full-cartridge':
        m = re.search(r'<ul class="games games-style-list">(.*?)</ul>', page, re.S)
        raw = re.findall(r'<li[^>]*>\s*<a[^>]*>(.*?)</a>', m.group(1), re.S) if m else []
    else:
        # The Game-Key Card article is one long plain <ul>; take the biggest list of unlinked items.
        lists = re.findall(r'<ul[^>]*>(.*?)</ul>', page, re.S)
        best = max(lists, key=lambda u: len(re.findall(r'<li>(?:(?!<a).)*?</li>', u, re.S)), default='')
        raw = re.findall(r'<li[^>]*>(.*?)</li>', best, re.S)
    items, skipped = [], []
    for r in raw:
        text = html.unescape(re.sub(r'<[^>]+>', '', r)).replace('\xa0', ' ').strip()
        if not text:
            continue
        note = ' '.join(re.findall(r'[\[(]([^\])]*)[\])]', text))
        title = re.sub(r'\s*[\[(][^\])]*[\])]', '', text).strip()
        (skipped if REGIONAL.search(note) else items).append(title)
    return items, skipped


def match_lists(keys, physical, review):
    by_norm = {}
    for k in keys:
        by_norm.setdefault(norm_key(k), k)
    published = {norm_key(s + '-switch-2') for s in physical}
    added = []
    for fmt, url in SOURCES.items():
        try:
            titles, skipped = list_items(url, fmt)
        except Exception as e:
            review['errors'].append(f'Could not read {url}: {e}')
            continue
        if len(titles) < 20:  # the page layout changed; do not trust a near-empty parse
            review['errors'].append(f'Only {len(titles)} titles parsed from {url}; layout may have changed')
            continue
        for title in titles:
            n = norm_title(title)
            key = by_norm.get(n) or by_norm.get(n + '-nintendo-switch-2-edition') or by_norm.get(n + '-standard-edition')
            if key:
                slug = key.removesuffix('-switch-2')
                if slug not in physical:
                    physical[slug] = {'format': fmt, 'source': url, 'checked': TODAY.isoformat()}
                    added.append((slug, fmt))
                elif physical[slug]['format'] != fmt:
                    review['conflicts'].append(f'{title}: listed as {fmt}, published as {physical[slug]["format"]}')
            elif not any(n in p or p.startswith(n) or n.startswith(p) for p in published):
                words = [w for w in n.split('-') if len(w) > 2][:3]
                hints = [k for k in keys if words and all(w in norm_key(k) for w in words)][:3]
                review['unmatched'].append({'title': title, 'format': fmt, 'candidates': hints})
        review['regional'] += skipped
    return added


def game_file(slug):
    p = GAMES / f'{slug}.json'
    return json.loads(p.read_text()) if p.exists() else None


def fetch(keys, cache, review):
    """Fetch eShop facts, keeping the old entry when the new one looks wrong."""
    changed = 0
    for key in keys:
        old = cache.get(key)
        try:
            new = eshop.parse(key, eshop.get(eshop.BASE + key + '/'))
        except Exception as e:
            review['errors'].append(f'{key}: {e}')
            time.sleep(1.0)
            continue
        if not new:
            continue
        g = game_file(eshop.slugify(key))
        prev = g['fileSize']['currentGB'] if g else None
        if prev and new['sizeGB'] and not new['sizeIsEstimate'] and not g['fileSize'].get('estimate'):
            if new['sizeGB'] < 0.3 * prev or new['sizeGB'] < 0.3:
                review['anomalies'].append(f'{new["title"]}: size {prev} GB -> {new["sizeGB"]} GB, kept {prev} GB')
                time.sleep(1.0)
                continue
        if new.get('upgrade') is None and old and old.get('upgrade'):
            new['upgrade'] = old['upgrade']
        if old is None or {k: v for k, v in old.items() if k != 'checked'} != {k: v for k, v in new.items() if k != 'checked'}:
            changed += 1
        cache[key] = new
        time.sleep(1.0)  # be polite to nintendo.com
    return changed


def main():
    full = '--full' in sys.argv or TODAY.weekday() == 0
    dry = '--dry-run' in sys.argv
    review = {'date': TODAY.isoformat(), 'unmatched': [], 'conflicts': [], 'anomalies': [], 'errors': [], 'regional': []}

    xml = eshop.get('https://www.nintendo.com/us/store/sitemap.xml')
    keys = sorted({k for k in re.findall(r'/us/store/products/([^/<]+-switch-2)/', xml) if not eshop.SKIP.search(k)})
    if len(keys) < 300:
        sys.exit(f'Only {len(keys)} Switch 2 pages in the sitemap; refusing to continue')
    new_keys = sorted(set(keys) - set(eshop.URLS.read_text().split())) if eshop.URLS.exists() else []
    eshop.URLS.write_text('\n'.join(keys) + '\n')

    physical = json.loads(PHYSICAL.read_text())
    added = match_lists(keys, physical, review)
    if not dry:
        PHYSICAL.write_text(json.dumps(dict(sorted(physical.items())), indent=1, ensure_ascii=False) + '\n')

    cache = json.loads(eshop.CACHE.read_text()) if eshop.CACHE.exists() else {}
    soon = (TODAY - dt.timedelta(days=45)).isoformat()
    todo = []
    for slug, entry in physical.items():
        g = game_file(slug)
        if full or g is None or g['releaseDate'] >= soon or g['fileSize'].get('estimate'):
            todo.append(entry.get('eshopKey', slug + '-switch-2'))
    changed = fetch(sorted(set(todo)), cache, review)
    if not dry:
        eshop.CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
        if full:
            eshop.cmd_upgrades()
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'apply_curated.py')], check=True)
        eshop.cmd_sync()
        REVIEW.write_text(json.dumps(review, indent=1, ensure_ascii=False) + '\n')

    summary = (f'{"Full" if full else "Daily"} update: {len(added)} new games, {changed} eShop changes, '
               f'{len(new_keys)} new eShop pages, {len(review["unmatched"])} to review, '
               f'{len(review["anomalies"])} anomalies, {len(review["errors"])} errors')
    print(summary)
    for slug, fmt in added:
        print(f'  + {slug} ({fmt})')
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a') as f:
            f.write(f'summary={summary}\n')
    step = os.environ.get('GITHUB_STEP_SUMMARY')
    if step:
        with open(step, 'a') as f:
            f.write(f'### {summary}\n\n' + ''.join(f'- added `{s}` ({fm})\n' for s, fm in added))
            for kind in ('anomalies', 'conflicts', 'errors'):
                for item in review[kind]:
                    f.write(f'- {kind}: {item}\n')


if __name__ == '__main__':
    main()
