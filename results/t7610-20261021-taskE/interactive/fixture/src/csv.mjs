// Parse CSV text into an array of rows (arrays of strings).
export function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  let i = 0;

  const endRow = () => {
    if (field !== '' || row.length > 0) {
      row.push(field);
      field = '';
      rows.push(row);
    }
    row = [];
  };

  while (i < text.length) {
    const ch = text[i];

    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i += 1;
        continue;
      }
      field += ch;
      i += 1;
      continue;
    }

    if (ch === '"' && field === '') {
      inQuotes = true;
      i += 1;
      continue;
    }
    if (ch === ',') {
      row.push(field);
      field = '';
      i += 1;
      continue;
    }
    if (ch === '\r') {
      i += 1;
      if (text[i] === '\n') i += 1;
      endRow();
      continue;
    }
    if (ch === '\n') {
      i += 1;
      endRow();
      continue;
    }

    field += ch;
    i += 1;
  }

  if (inQuotes) {
    throw new Error('unterminated quote in CSV input');
  }

  endRow();

  return rows;
}
