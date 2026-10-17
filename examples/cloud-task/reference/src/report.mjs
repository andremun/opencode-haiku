import { parseCSV } from './csv.mjs';

export function summarize(csvText, { groupBy, sum }) {
  const rows = parseCSV(csvText);
  const header = rows[0] ?? [];
  const g = header.indexOf(groupBy);
  const s = header.indexOf(sum);
  if (g < 0) throw new Error(`unknown column: ${groupBy}`);
  if (s < 0) throw new Error(`unknown column: ${sum}`);
  const groups = new Map();
  for (const row of rows.slice(1)) {
    const value = Number(row[s]);
    if (row[s] === '' || Number.isNaN(value)) throw new Error(`not a number: ${row[s]}`);
    const entry = groups.get(row[g]) ?? { group: row[g], total: 0, count: 0 };
    entry.total += value;
    entry.count += 1;
    groups.set(row[g], entry);
  }
  return [...groups.values()]
    .map((e) => ({ ...e, total: Math.round(e.total * 100) / 100 }))
    .sort((a, b) => (a.group < b.group ? -1 : a.group > b.group ? 1 : 0));
}
