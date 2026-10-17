import test from 'node:test';
import assert from 'node:assert/strict';
import { parseCSV } from '../src/csv.mjs';

test('plain rows', () => {
  assert.deepEqual(parseCSV('a,b,c\n1,2,3\n'), [['a', 'b', 'c'], ['1', '2', '3']]);
});
test('empty input has no rows', () => {
  assert.deepEqual(parseCSV(''), []);
  assert.deepEqual(parseCSV('\n'), []);
});
test('empty fields are kept', () => {
  assert.deepEqual(parseCSV('a,,c\n,,\n'), [['a', '', 'c'], ['', '', '']]);
});
test('quoted field containing a comma', () => {
  assert.deepEqual(parseCSV('name,city\n"Smith, Jo",Perth\n'), [['name', 'city'], ['Smith, Jo', 'Perth']]);
});
test('escaped quotes inside a quoted field', () => {
  assert.deepEqual(parseCSV('say\n"he said ""hi"""\n'), [['say'], ['he said "hi"']]);
});
test('newline inside a quoted field stays in the field', () => {
  assert.deepEqual(parseCSV('note,id\n"line1\nline2",7\n'), [['note', 'id'], ['line1\nline2', '7']]);
});
test('CRLF line endings', () => {
  assert.deepEqual(parseCSV('a,b\r\n1,2\r\n'), [['a', 'b'], ['1', '2']]);
});
test('no trailing newline', () => {
  assert.deepEqual(parseCSV('a,b\n1,2'), [['a', 'b'], ['1', '2']]);
});
test('unterminated quote throws', () => {
  assert.throws(() => parseCSV('a\n"oops\n'), /unterminated/i);
});
