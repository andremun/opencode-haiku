// Parse CSV text into an array of rows (arrays of strings).
// TODO: this naive version is wrong for quoted fields, escaped quotes, embedded
// newlines and CRLF line endings. See test/csv.test.mjs.
export function parseCSV(text) {
  return text.trim().split('\n').map((line) => line.split(','));
}
