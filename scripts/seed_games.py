#!/usr/bin/env python3
"""One-off: create curated stubs for the launch games, then run fetch_eshop.py sync."""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / 'src' / 'data' / 'games'
CACHE = json.loads((ROOT / 'data' / 'eshop-cache.json').read_text())
TODAY = dt.date.today().isoformat()

NL_FULL = 'https://www.nintendolife.com/guides/every-nintendo-switch-2-physical-release-with-the-full-game-on-the-cart'
DESTRUCTOID = 'https://www.destructoid.com/all-switch-2-game-key-card-titles-listed/'
WESTERN = 'Confirmed for the Western physical release'

PHYSICAL = {
    **{k: ('full-cartridge', NL_FULL, None) for k in [
        'mario-kart-world', 'donkey-kong-bananza', 'kirby-air-riders',
        'pokemon-legends-z-a-nintendo-switch-2-edition', 'metroid-prime-4-beyond-nintendo-switch-2-edition',
        'hyrule-warriors-age-of-imprisonment', 'cyberpunk-2077-ultimate-edition',
        'the-legend-of-zelda-breath-of-the-wild-nintendo-switch-2-edition',
        'the-legend-of-zelda-tears-of-the-kingdom-nintendo-switch-2-edition',
        'super-mario-party-jamboree-nintendo-switch-2-edition-plus-jamboree-tv', 'mario-tennis-fever',
        'splatoon-raiders', 'star-fox', 'animal-crossing-new-horizons-nintendo-switch-2-edition',
        'super-mario-bros-wonder-nintendo-switch-2-edition-plus-meetup-in-bellabel-park',
        'kirby-and-the-forgotten-land-nintendo-switch-2-edition-plus-star-crossed-world',
        'hades-ii-nintendo-switch-2-edition', 'hollow-knight-silksong-nintendo-switch-2-edition',
        'stardew-valley-nintendo-switch-2-edition', 'the-elder-scrolls-iv-oblivion-remastered',
        'indiana-jones-and-the-great-circle', 'stellar-blade-complete-edition',
        'sonic-racing-crossworlds-nintendo-switch-2-edition',
        'fantasy-life-i-the-girl-who-steals-time-nintendo-switch-2-edition',
        'xenoblade-chronicles-3-nintendo-switch-2-edition',
        'xenoblade-chronicles-x-definitive-edition-nintendo-switch-2-edition', 'yoshi-and-the-mysterious-book',
    ]},
    **{k: ('game-key-card', DESTRUCTOID, WESTERN) for k in [
        'hitman-world-of-assassination-signature-edition', 'star-wars-outlaws-gold-edition',
        'yakuza-0-directors-cut', 'sonic-x-shadow-generations',
        'ea-sports-madden-nfl-26', 'bravely-default-flying-fairy-hd-remaster', 'puyo-puyo-tetris-2s',
        'raidou-remastered-the-mystery-of-the-soulless-army',
    ]},
    'street-fighter-6': ('game-key-card', DESTRUCTOID, 'The physical release is Street Fighter 6: Years 1-2 Fighters Edition'),
    'pokemon-pokopia': ('game-key-card', 'https://nintendoeverything.com/pokemon-pokopia-breaks-tradition-for-nintendo-published-switch-2-games-will-be-a-game-key-card/', 'The first Nintendo-published Switch 2 game on a Game-Key Card'),
    'pragmata': ('game-key-card', 'https://www.walmart.com/ip/PRAGMATA-Nintendo-Switch-2-Game/19012714214', 'Retail listing labels it Game-Key Card'),
    'resident-evil-requiem': ('game-key-card', 'https://www.ebay.com/p/9086908171', 'Retail listings label it Game-Key Card'),
    'elden-ring-tarnished-edition': ('game-key-card', 'https://gonintendo.com/contents/59754-elden-ring-tarnished-edition-is-a-game-key-card-release-on-switch-2-and-is-priced-at', None),
}

GAMES.mkdir(parents=True, exist_ok=True)
for key, e in CACHE.items():
    slug = key.removesuffix('-switch-2')
    if slug not in PHYSICAL or not e['sizeGB']:
        print(f'skip {slug}')
        continue
    fmt, src, note = PHYSICAL[slug]
    physical = {'format': fmt, 'source': src, 'checked': TODAY}
    if note:
        physical['note'] = note
    stub = {
        'title': e['title'],
        'publisher': e['publisher'],
        'releaseDate': e['releaseDate'],
        'kind': 'edition' if 'nintendo-switch-2-edition' in slug else 'native',
        'fileSize': {'currentGB': e['sizeGB'], 'source': e['url'], 'checked': e['checked']},
        'physical': physical,
    }
    (GAMES / f'{slug}.json').write_text(json.dumps(stub, indent=2, ensure_ascii=False) + '\n')
print(len(list(GAMES.glob('*.json'))), 'game files')
