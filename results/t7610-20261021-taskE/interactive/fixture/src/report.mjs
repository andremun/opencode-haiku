import { parseCSV } from './csv.mjs';

// summarize(csvText, { groupBy, sum }) -> [{ group, total, count }]
export function version() {
  return '1.0.0';
}

export function summarize(csvText, options) {
  const { groupBy, sum } = options;
  const rows = parseCSV(csvText);

  if (rows.length === 0) return [];

  const header = rows[0];
  const groupIndex = header.indexOf(groupBy);
  if (groupIndex === -1) {
    throw new Error(`unknown column: ${groupBy}`);
  }
  const sumIndex = header.indexOf(sum);
  if (sumIndex === -1) {
    throw new Error(`unknown column: ${sum}`);
  }

  const groups = new Map();

  for (let r = 1; r < rows.length; r += 1) {
    const row = rows[r];
    const group = row[groupIndex];
    const raw = row[sumIndex];
    const value = Number(raw);

    if (raw.trim() === '' || Number.isNaN(value)) {
      throw new Error(`not a number: ${raw}`);
    }

    const entry = groups.get(group) || { group, total: 0, count: 0 };
    entry.total += value;
    entry.count += 1;
    groups.set(group, entry);
  }

  return [...groups.values()]
    .map((entry) => ({
      group: entry.group,
      total: Math.round(entry.total * 100) / 100,
      count: entry.count,
    }))
    .sort((a, b) => (a.group < b.group ? -1 : a.group > b.group ? 1 : 0));
}
