#!/usr/bin/env python3
"""Publish curated games into src/data/games from hand-checked data files:

- data/physical.json: cartridge format per game (a game is published only if listed here)
- data/performance.json: resolution / FPS modes per game (optional)

Creates a game file for every curated slug that has eShop data and refreshes the
curated blocks of existing ones. Run fetch_eshop.py sync afterwards for eShop fields.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / 'src' / 'data' / 'games'
physical = json.loads((ROOT / 'data' / 'physical.json').read_text())
performance = json.loads((ROOT / 'data' / 'performance.json').read_text())
cache = {k.removesuffix('-switch-2'): v for k, v in json.loads((ROOT / 'data' / 'eshop-cache.json').read_text()).items()}

GAMES.mkdir(parents=True, exist_ok=True)
created = updated = 0
for slug, phys in physical.items():
    e = cache.get(slug)
    path = GAMES / f'{slug}.json'
    if path.exists():
        g = json.loads(path.read_text())
        updated += 1
    elif e and e['sizeGB']:
        g = {
            'title': e['title'],
            'publisher': e['publisher'],
            'releaseDate': e['releaseDate'],
            'kind': 'edition' if 'nintendo-switch-2-edition' in slug else 'native',
            'fileSize': {'currentGB': e['sizeGB'], 'source': e['url'], 'checked': e['checked']},
        }
        created += 1
    else:
        print(f'no eShop data yet: {slug}')
        continue
    g['physical'] = phys
    if slug in performance:
        g['performance'] = performance[slug]
    path.write_text(json.dumps(g, indent=2, ensure_ascii=False) + '\n')
print(f'{created} created, {updated} updated, {len(list(GAMES.glob("*.json")))} games total')
