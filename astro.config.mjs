// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://gamespecsdb.com',
  trailingSlash: 'always',
  // ~10 KB of CSS: inlining it removes a render-blocking request on every page.
  build: { inlineStylesheets: 'always' },
  // Keep noindex pages (search, 404) out of the sitemap.
  integrations: [sitemap({ filter: (page) => !/\/(search|404)\/?$/.test(page) })],
});
