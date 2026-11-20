import assert from 'node:assert/strict';
import test from 'node:test';
import { calendarLayout } from '../game/calendar.mjs';
import { advance, canTurn, createGame } from '../game/snake.mjs';
import { normalizeCalendar, previewSvg, windowFor } from '../scripts/build-game.mjs';

test('the rolling window clamps month ends and follows the New York date', () => {
  assert.deepEqual(windowFor(new Date('2026-05-31T13:00:00Z')), { start: '2026-03-01', end: '2026-05-31' });
  assert.deepEqual(windowFor(new Date('2024-05-31T13:00:00Z')), { start: '2024-03-01', end: '2024-05-31' });
  assert.deepEqual(windowFor(new Date('2026-01-02T02:00:00Z')), { start: '2025-10-02', end: '2026-01-01' });
});

test('the SVG and game board use the same dated cells and exclude padding', () => {
  const range = { start: '2026-11-13', end: '2026-11-16' };
  const input = [
    { date: '2026-11-12', contributionLevel: 'FOURTH_QUARTILE' },
    { date: '2026-11-13', contributionLevel: 'NONE' },
    { date: '2026-11-14', contributionLevel: 'FIRST_QUARTILE' },
    { date: '2026-11-15', contributionLevel: 'THIRD_QUARTILE' },
    { date: '2026-11-16', contributionLevel: 'SECOND_QUARTILE' },
    { date: '2026-11-17', contributionLevel: 'FOURTH_QUARTILE' },
  ];
  const data = normalizeCalendar(range, input);
  const { columns, slots } = calendarLayout(data.days);
  assert.equal(columns, 2);
  assert.deepEqual(slots.slice(5, 9).map(day => day.level), [0, 1, 3, 2]);
  assert.equal((previewSvg(data).match(/width="20" height="20"/g) ?? []).length, data.days.length);
  assert.throws(() => normalizeCalendar(range, input.slice(0, 4)), /omitted 2026-11-16/);
});

test('only the highlighted square scores, grows the snake, and can win a run', () => {
  const slots = Array(98).fill(null);
  slots[59] = { level: 4 };
  const game = createGame(slots, () => 0);
  assert.equal(game.target, 59);
  const won = advance(game, 'left');
  assert.equal(won.phase, 'won');
  assert.equal(won.direction, 'right');
  assert.equal(won.score, 1);
  assert.equal(won.body.length, 4);
  assert.equal(won.target, null);
  assert.equal(game.remaining.size, 1);
});

test('movement stops at walls and body segments but can enter a vacating tail', () => {
  const game = { ...createGame(Array(98).fill({ level: 1 })), direction: 'right', target: 17 };
  assert.equal(advance({ ...game, body: [84, 77, 70] }, 'up').phase, 'lost');
  assert.equal(advance({ ...game, body: [10, 3, 2, 9, 16] }, 'up').phase, 'lost');
  const moved = advance({ ...game, body: [10, 3, 2, 9] }, 'up');
  assert.equal(moved.phase, 'playing');
  assert.deepEqual(moved.body, [9, 10, 3, 2]);
  assert.equal(moved.score, 0);
  assert.equal(canTurn('up', 'down'), false);
});

test('an occupied target waits for the tail, and zero-contribution boards are empty', () => {
  const slots = Array(98).fill(null);
  assert.equal(createGame(slots).phase, 'empty');
  slots[38] = { level: 1 };
  const game = createGame(slots);
  assert.equal(game.target, null);
  assert.equal(advance(game, 'right').target, 38);
});

test('scoring at the length cap keeps the board playable', () => {
  const game = {
    ...createGame(Array(98).fill({ level: 1 })), target: 59,
    body: [52, 45, 38, 31, 24, 17, 10, 11, 18, 25, 32, 39, 46, 53, 60, 67, 66, 65],
  };
  const moved = advance(game, 'right', () => 0);
  assert.equal(moved.body.length, 18);
  assert.equal(moved.score, 1);
  assert.equal(moved.phase, 'playing');
});
