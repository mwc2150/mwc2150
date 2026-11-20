import assert from 'node:assert/strict';
import test from 'node:test';
import { normalizeCalendar, windowFor } from '../scripts/build-snake.mjs';
import { retroSnakeSvg, snakePath } from '../scripts/retro-snake.mjs';

test('the rolling window clamps month ends and follows the New York date', () => {
  assert.deepEqual(windowFor(new Date('2026-05-31T13:00:00Z')), { start: '2026-03-01', end: '2026-05-31' });
  assert.deepEqual(windowFor(new Date('2024-05-31T13:00:00Z')), { start: '2024-03-01', end: '2024-05-31' });
  assert.deepEqual(windowFor(new Date('2026-01-02T02:00:00Z')), { start: '2025-10-02', end: '2026-01-01' });
});

test('the snake visits every slot once, with an orthogonal move at each step', () => {
  for (const width of [13, 14, 15]) {
    const path = snakePath(width);
    assert.equal(new Set(path).size, width * 7);
    for (const [index, slot] of path.entries()) {
      assert.ok(slot >= 0 && slot < width * 7);
      if (index === 0) continue;
      const previous = path[index - 1];
      const dx = Math.abs(Math.floor(slot / 7) - Math.floor(previous / 7));
      const dy = Math.abs(slot % 7 - previous % 7);
      assert.equal(dx + dy, 1);
    }
  }
});

test('both boards show the dated squares, and only the animated board eats activity', () => {
  const range = { start: '2026-11-13', end: '2026-11-16' };
  const input = [
    { date: '2026-11-12', contributionLevel: 'FOURTH_QUARTILE' },
    { date: '2026-11-13', contributionLevel: 'NONE' },
    { date: '2026-11-14', contributionLevel: 'FIRST_QUARTILE' },
    { date: '2026-11-15', contributionLevel: 'FOURTH_QUARTILE' },
    { date: '2026-11-16', contributionLevel: 'SECOND_QUARTILE' },
    { date: '2026-11-17', contributionLevel: 'FOURTH_QUARTILE' },
  ];
  const calendar = normalizeCalendar(range, input);
  const animated = retroSnakeSvg(calendar, true);
  const still = retroSnakeSvg(calendar, false);
  assert.equal((animated.match(/width="13" height="13"/g) ?? []).length, 4);
  assert.equal((still.match(/width="13" height="13"/g) ?? []).length, 4);
  assert.equal((animated.match(/attributeName="fill"/g) ?? []).length, 3);
  assert.equal((animated.match(/<animateTransform\b/g) ?? []).length, 4);
  assert.doesNotMatch(still, /<animate/);
  assert.match(animated, /<text[^>]+>NOV<\/text>/);
  assert.doesNotMatch(animated, />[^<]*Nov 13/);
  assert.throws(() => normalizeCalendar(range, input.slice(0, 4)), /omitted 2026-11-16/);
});
