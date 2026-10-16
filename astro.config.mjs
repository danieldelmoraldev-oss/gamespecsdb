// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { readdirSync, readFileSync } from 'node:fs';

// Game pages without own text or performance data are noindex (isThin in src/lib/games.ts): keep them out of the sitemap too.
const THIN = new Set(
  readdirSync('src/data/games')
    .filter((f) => f.endsWith('.json'))
    .filter((f) => {
      const d = JSON.parse(readFileSync(`src/data/games/${f}`, 'utf8'));
      return !d.summary && !d.performance?.modes?.length;
    })
    .map((f) => f.replace(/\.json$/, '')),
);

// https://astro.build/config
export default defineConfig({
  site: 'https://gamespecsdb.com',
  trailingSlash: 'always',
  // ~10 KB of CSS: inlining it removes a render-blocking request on every page.
  build: { inlineStylesheets: 'always' },
  // Keep noindex pages (search, 404) out of the sitemap.
  integrations: [sitemap({ filter: (page) => !/\/(search|404)\/?$/.test(page) && !THIN.has(page.match(/\/games\/([^/]+)\/?$/)?.[1] ?? '') })],
});
