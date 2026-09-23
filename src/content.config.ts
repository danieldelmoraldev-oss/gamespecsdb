import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// Every fact carries where it came from and when it was last checked.
const sourced = {
  source: z.url(),
  checked: z.iso.date(),
};

const games = defineCollection({
  loader: glob({ pattern: '**/*.json', base: './src/data/games' }),
  schema: z.object({
    title: z.string(),
    publisher: z.string(),
    releaseDate: z.iso.date(),
    // native: built for Switch 2; edition: paid Switch 2 Edition of a Switch 1 game;
    // free-update: Switch 1 game improved on Switch 2 by a free patch
    kind: z.enum(['native', 'edition', 'free-update']),
    genres: z.array(z.string()).default([]),
    // Optional hand-written intro; pages fall back to a lead built from the facts.
    summary: z.string().optional(),
    fileSize: z.object({
      currentGB: z.number().positive(),
      launchGB: z.number().positive().optional(),
      ...sourced,
    }),
    physical: z.object({
      format: z.enum(['full-cartridge', 'game-key-card', 'digital-only', 'unknown']),
      note: z.string().optional(),
      ...sourced,
    }),
    performance: z
      .object({
        handheld: z.object({ resolution: z.string().optional(), fps: z.number().optional() }).optional(),
        docked: z.object({ resolution: z.string().optional(), fps: z.number().optional() }).optional(),
        ...sourced,
      })
      .optional(),
    upgrade: z
      .object({
        priceUSD: z.number().nonnegative(),
        ...sourced,
      })
      .optional(),
    // Written by scripts/fetch_eshop.py sync; never edit by hand.
    eshop: z
      .object({
        url: z.url(),
        priceUSD: z.number().nullable(),
        playModes: z.array(z.string()),
        players: z.object({ system: z.number().optional(), local: z.number().optional(), online: z.number().optional() }),
        languages: z.array(z.string()),
        switch1SizeGB: z.number().nullable(),
        developer: z.string(),
      })
      .optional(),
  }),
});

const guides = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/guides' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    updated: z.iso.date(),
  }),
});

export const collections = { games, guides };
