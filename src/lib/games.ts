import { getCollection, type CollectionEntry } from 'astro:content';

export type Game = CollectionEntry<'games'>;

export const FORMAT_LABEL: Record<Game['data']['physical']['format'], string> = {
  'full-cartridge': 'Full game on cartridge',
  'game-key-card': 'Game-Key Card (download required)',
  'digital-only': 'Digital only',
  unknown: 'Unknown',
};

export const KIND_LABEL: Record<Game['data']['kind'], string> = {
  native: 'Native Switch 2 game',
  edition: 'Nintendo Switch 2 Edition',
  'free-update': 'Switch 1 game with free Switch 2 update',
};

export async function allGames(): Promise<Game[]> {
  const games = await getCollection('games');
  return games.sort((a, b) => a.data.title.localeCompare(b.data.title));
}

export function formatGB(gb: number): string {
  return gb < 1 ? `${Math.round(gb * 1024)} MB` : `${gb.toFixed(1)} GB`;
}

export function formatDate(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  });
}

// The newest "checked" date across all sourced facts of a game.
export function lastChecked(game: Game): string {
  const d = game.data;
  return [d.fileSize.checked, d.physical.checked, d.performance?.checked, d.upgrade?.checked]
    .filter((x): x is string => Boolean(x))
    .sort()
    .at(-1)!;
}
