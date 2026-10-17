export function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  let started = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else { quoted = false; }
      } else { field += c; }
    } else if (c === '"') { quoted = true; started = true; }
    else if (c === ',') { row.push(field); field = ''; started = true; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      if (started || field !== '') { row.push(field); rows.push(row); }
      row = []; field = ''; started = false;
    } else { field += c; started = true; }
  }
  if (quoted) throw new Error('unterminated quoted field');
  if (started || field !== '') { row.push(field); rows.push(row); }
  return rows;
}
