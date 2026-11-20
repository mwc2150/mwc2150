const STEPS = { up: -1, down: 1, left: -7, right: 7 };
const MAX_LENGTH = 18;

function pickTarget(remaining, body, random) {
  const available = [...remaining].filter(slot => !body.includes(slot));
  return available.length ? available[Math.floor(random() * available.length)] : null;
}

export function createGame(slots, random = Math.random) {
  const head = Math.floor(slots.length / 14) * 7 + 3;
  const body = [head, head - 7, head - 14];
  const remaining = new Set(slots.flatMap((day, index) => day?.level > 0 ? [index] : []));
  return {
    size: slots.length,
    body,
    remaining,
    target: pickTarget(remaining, body, random),
    direction: 'right',
    score: 0,
    phase: remaining.size ? 'playing' : 'empty',
  };
}

export function canTurn(direction, next) {
  return Object.hasOwn(STEPS, next) && STEPS[direction] !== -STEPS[next];
}

export function advance(game, next, random = Math.random) {
  if (game.phase !== 'playing') return game;

  const direction = canTurn(game.direction, next) ? next : game.direction;
  const current = game.body[0];
  const head = current + STEPS[direction];
  const atWall = head < 0 || head >= game.size
    || (direction === 'up' && current % 7 === 0)
    || (direction === 'down' && current % 7 === 6);
  const ate = head === game.target;
  const grows = ate && game.body.length < MAX_LENGTH;
  const body = grows ? game.body : game.body.slice(0, -1);

  if (atWall || body.includes(head)) return { ...game, phase: 'lost' };

  const remaining = ate ? new Set(game.remaining) : game.remaining;
  if (ate) remaining.delete(head);

  return {
    ...game,
    body: [head, ...body],
    direction,
    remaining,
    score: game.score + Number(ate),
    target: ate || game.target === null ? pickTarget(remaining, [head, ...body], random) : game.target,
    phase: remaining.size ? 'playing' : 'won',
  };
}
