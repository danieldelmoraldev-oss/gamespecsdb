#!/usr/bin/env python3
"""Pull official facts for Switch 2 games from the US Nintendo eShop.

Usage:
  scripts/fetch_eshop.py list                 # refresh data/eshop-switch2-urls.txt from the store sitemap
  scripts/fetch_eshop.py fetch KEY [KEY ...]  # fetch products by urlKey into data/eshop-cache.json
  scripts/fetch_eshop.py sync                 # update src/data/games/*.json from the cache

Only eShop-owned fields are overwritten on sync; hand-curated fields
(physical format, performance, summary) are kept.
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URLS = ROOT / 'data' / 'eshop-switch2-urls.txt'
CACHE = ROOT / 'data' / 'eshop-cache.json'
GAMES = ROOT / 'src' / 'data' / 'games'
BASE = 'https://www.nintendo.com/us/store/products/'
UA = 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0'
GIB = 1024 ** 3  # the eShop's "GB" is GiB: 23845666816 bytes shows as 22.2 GB
SKIP = re.compile(r'dlc|pass|pack|bundle|upgrade|costume|expansion|voucher|points|coins|currency|season|soundtrack|-set-|\d{14}')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def cmd_list():
    xml = get('https://www.nintendo.com/us/store/sitemap.xml')
    keys = sorted({k for k in re.findall(r'/us/store/products/([^/<]+-switch-2)/', xml) if not SKIP.search(k)})
    URLS.write_text('\n'.join(keys) + '\n')
    print(f'{len(keys)} Switch 2 game pages -> {URLS.relative_to(ROOT)}')


def clean(name):
    return re.sub(r'[™®©]', '', name).replace(' ', ' ').strip()


def parse(key, html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    state = json.loads(m.group(1))['props']['pageProps']['initialApolloState']
    p = next(v for k, v in state.items() if k.startswith('Product:') and v.get('urlKey') == key)
    if p.get('dlcType') or (p.get('topLevelCategory') or {}).get('code') != 'GAMES':
        return None
    roms = {r['platform']: r for r in (p.get('softwareDetails') or {}).get('romSizes') or []}
    s2 = roms.get('BEE') or {}
    size = s2.get('totalRomSize') or s2.get('estimatedRomSize')
    s1 = (roms.get('HAC') or {}).get('totalRomSize')
    price = next((v for k, v in p.items() if k.startswith('prices(')), None) or {}
    players = p.get('numberOfPlayers') or {}
    return {
        'key': key,
        'url': BASE + key + '/',
        'title': clean(p['name']),
        'publisher': clean(p.get('softwarePublisher') or ''),
        'developer': clean(p.get('softwareDeveloper') or ''),
        'releaseDate': (p.get('releaseDate') or '')[:10],
        'isUpgrade': bool(p.get('isUpgrade')),
        'sizeGB': round(int(size) / GIB, 1) if size else None,
        'sizeIsEstimate': not s2.get('totalRomSize') and bool(size),
        'switch1SizeGB': round(int(s1) / GIB, 1) if s1 else None,
        'priceUSD': price.get('regularPrice'),
        'playModes': [m['label'] for m in p.get('playModes') or [] if 'mode' in (m.get('label') or '').lower()],
        'players': {k: (players.get(k) or {}).get('max') for k in ('system', 'local', 'online') if (players.get(k) or {}).get('max')},
        'languages': p.get('supportedLanguages') or [],
        'checked': dt.date.today().isoformat(),
    }


def cmd_fetch(keys):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for i, key in enumerate(keys):
        try:
            item = parse(key, get(BASE + key + '/'))
        except Exception as e:  # keep going; report at the end
            print(f'! {key}: {e}')
            continue
        if item:
            cache[key] = item
            print(f'{i + 1}/{len(keys)} {item["title"]}: {item["sizeGB"]} GB')
        else:
            print(f'{i + 1}/{len(keys)} {key}: not a game, skipped')
        CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
        time.sleep(1.0)  # be polite to nintendo.com


def slugify(key):
    return re.sub(r'-switch-2$', '', key)


def cmd_sync():
    cache = json.loads(CACHE.read_text())
    GAMES.mkdir(parents=True, exist_ok=True)
    for key, e in cache.items():
        if not e['sizeGB']:
            continue
        path = GAMES / f'{slugify(key)}.json'
        g = json.loads(path.read_text()) if path.exists() else None
        if g is None:
            continue  # only curated games are published; add a stub file to publish one
        g['title'] = g.get('title') or e['title']
        g['publisher'] = e['publisher'] or g.get('publisher')
        g['releaseDate'] = e['releaseDate'] or g.get('releaseDate')
        g['fileSize'] = {**g.get('fileSize', {}), 'currentGB': e['sizeGB'], 'source': e['url'], 'checked': e['checked']}
        g['eshop'] = {k: e[k] for k in ('url', 'priceUSD', 'playModes', 'players', 'languages', 'switch1SizeGB', 'developer')}
        path.write_text(json.dumps(g, indent=2, ensure_ascii=False) + '\n')
        print(f'synced {path.name}')


if __name__ == '__main__':
    cmd, *args = sys.argv[1:] or ['help']
    if cmd == 'list':
        cmd_list()
    elif cmd == 'fetch':
        cmd_fetch(args or URLS.read_text().split())
    elif cmd == 'sync':
        cmd_sync()
    else:
        print(__doc__)
