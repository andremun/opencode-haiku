import test from 'node:test';
import assert from 'node:assert/strict';
import { summarize } from '../src/report.mjs';

const data = 'category,amount,note\nfood,10.50,"lunch, big"\nrent,1000,\nfood,4.25,snack\nfun,20,\nrent,50.5,late fee\n';

test('groups, sums and counts, sorted by group name', () => {
  assert.deepEqual(summarize(data, { groupBy: 'category', sum: 'amount' }), [
    { group: 'food', total: 14.75, count: 2 },
    { group: 'fun', total: 20, count: 1 },
    { group: 'rent', total: 1050.5, count: 2 },
  ]);
});
test('totals are rounded to two decimals', () => {
  const rows = 'k,v\na,0.1\na,0.2\n';
  assert.deepEqual(summarize(rows, { groupBy: 'k', sum: 'v' }), [{ group: 'a', total: 0.3, count: 2 }]);
});
test('blank lines are ignored', () => {
  assert.deepEqual(summarize('k,v\n\na,1\n\n', { groupBy: 'k', sum: 'v' }), [{ group: 'a', total: 1, count: 1 }]);
});
test('quoted group names are supported', () => {
  assert.deepEqual(summarize('k,v\n"x, y",2\n"x, y",3\n', { groupBy: 'k', sum: 'v' }), [{ group: 'x, y', total: 5, count: 2 }]);
});
test('unknown column throws a helpful error', () => {
  assert.throws(() => summarize(data, { groupBy: 'nope', sum: 'amount' }), /unknown column: nope/);
  assert.throws(() => summarize(data, { groupBy: 'category', sum: 'missing' }), /unknown column: missing/);
});
test('non-numeric amount throws', () => {
  assert.throws(() => summarize('k,v\na,abc\n', { groupBy: 'k', sum: 'v' }), /not a number/i);
});
