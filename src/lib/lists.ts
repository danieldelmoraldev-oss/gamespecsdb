import type { Game } from './games';

export interface ListDef {
  slug: string;
  title: string;
  description: string;
  filter: (g: Game) => boolean;
  sort?: (a: Game, b: Game) => number;
}

const bySizeDesc = (a: Game, b: Game) => b.data.fileSize.currentGB - a.data.fileSize.currentGB;
const bySizeAsc = (a: Game, b: Game) => a.data.fileSize.currentGB - b.data.fileSize.currentGB;
const maxFps = (g: Game) => Math.max(0, ...(g.data.performance?.modes ?? []).map((m) => m.fps ?? 0));

export const LISTS: ListDef[] = [
  {
    slug: 'game-key-card-games',
    title: 'Every Switch 2 Game-Key Card game',
    description: 'Physical Switch 2 releases whose cartridge only unlocks a download instead of holding the game.',
    filter: (g) => g.data.physical.format === 'game-key-card',
  },
  {
    slug: 'full-cartridge-games',
    title: 'Switch 2 games with the full game on the cartridge',
    description: 'Physical releases you can play straight from the cartridge without downloading the game first.',
    filter: (g) => g.data.physical.format === 'full-cartridge',
  },
  {
    slug: '60fps-games',
    title: 'Switch 2 games that run at 60 FPS',
    description: 'Games with a documented 60 FPS target in handheld or TV mode.',
    filter: (g) => maxFps(g) >= 60,
  },
  {
    slug: '120fps-games',
    title: 'Switch 2 games that run at 120 FPS',
    description: 'Games with a documented 120 FPS mode.',
    filter: (g) => maxFps(g) >= 120,
  },
  {
    slug: 'largest-games',
    title: 'The biggest Switch 2 games by file size',
    description: 'Switch 2 games ranked by current download size, largest first.',
    filter: () => true,
    sort: bySizeDesc,
  },
  {
    slug: 'smallest-games',
    title: 'The smallest Switch 2 games by file size',
    description: 'Switch 2 games ranked by current download size, smallest first.',
    filter: () => true,
    sort: bySizeAsc,
  },
  {
    slug: 'switch-2-edition-upgrades',
    title: 'Nintendo Switch 2 Edition upgrades and prices',
    description: 'Switch 1 games with a paid Switch 2 Edition upgrade, and what the upgrade costs.',
    filter: (g) => g.data.kind === 'edition',
  },
  {
    slug: 'free-switch-2-updates',
    title: 'Switch 1 games with a free Switch 2 update',
    description: 'Switch 1 games that run better on Switch 2 thanks to a free patch.',
    filter: (g) => g.data.kind === 'free-update',
  },
];
