## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)

## This project

GameSpecsDB (gamespecsdb.com): sourced Switch 2 game specs, monetised with AdSense.

- Node is not installed on the host. Build inside Docker:
  `docker run --rm -v "$PWD":/app -w /app -u $(id -u):$(id -g) -e HOME=/tmp node:22-alpine npm run build`
- Game data lives in `src/data/games/<slug>.json` (schema in `src/content.config.ts`).
- `scripts/fetch_eshop.py` pulls official facts from the US eShop: `list` refreshes the Switch 2 URL list from
  the store sitemap, `fetch KEY…` caches products, `sync` rewrites eShop-owned fields of existing game files.
  Hand-curated fields (physical format, performance, summary) are never overwritten.
- Curated facts live in `data/physical.json` and `data/performance.json`; `scripts/apply_curated.py` writes
  them into the game files (a game is only published once its cartridge format is in `physical.json`).
- Every fact needs a `source` URL and a `checked` date. Unknown stays `unknown`; never guess.
- Ads stay off until `SITE.adsenseClient` in `src/site.ts` is set.
- `scripts/auto_update.py` runs daily in GitHub Actions (`.github/workflows/auto-update.yml`): adds games newly
  listed in the Game-Key Card / full-cartridge sources when the title matches an eShop page exactly, refreshes
  upcoming and recent games daily and every game on Mondays, rejects suspicious size drops, and writes anything
  that needs a human to `data/review.json`. The bot pushes to `main`, so `git pull` before editing.
