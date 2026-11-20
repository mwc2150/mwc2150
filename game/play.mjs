import { calendarLayout, dateRangeLabel, levelColors } from './calendar.mjs';
import { advance, canTurn, createGame } from './snake.mjs';

const board = document.querySelector('#board');
const months = document.querySelector('#months');
const screen = document.querySelector('#screen');
const dateRange = document.querySelector('#date-range');
const score = document.querySelector('#score');
const total = document.querySelector('#total');
const status = document.querySelector('#status');
const action = document.querySelector('#action');
const restart = document.querySelector('#restart');
const directions = [...document.querySelectorAll('[data-direction]')];
const keyDirections = {
  ArrowUp: 'up', w: 'up', ArrowDown: 'down', s: 'down',
  ArrowLeft: 'left', a: 'left', ArrowRight: 'right', d: 'right',
};

let game;
let slots;
let cells;
let waitingTurn;
let timer;
let mode = 'loading';

function renderBoard(showSnake = true) {
  cells.forEach((cell, index) => {
    const day = slots[index];
    const level = game.remaining.has(index) ? day.level : 0;
    cell.style.setProperty('--activity', day ? levelColors[level] : 'transparent');
    cell.classList.toggle('segment', showSnake && game.body.includes(index));
    cell.classList.toggle('head', showSnake && index === game.body[0]);
    cell.classList.toggle('target', showSnake && index === game.target);
  });
  score.textContent = game.score;
}

function setMode(next, message) {
  mode = next;
  status.textContent = message;
  action.textContent = {
    loading: 'Start game', ready: 'Start game', playing: 'Pause', paused: 'Resume',
    lost: 'Play again', won: 'Play again', empty: 'Start game', error: 'Retry',
  }[mode];
  action.disabled = mode === 'empty' || mode === 'loading';
  restart.hidden = mode !== 'playing' && mode !== 'paused';
  directions.forEach(button => { button.disabled = mode !== 'playing'; });
}

function stopTimer() {
  clearInterval(timer);
  waitingTurn = undefined;
}

function play() {
  setMode('playing', 'Eat the glowing square.');
  timer = setInterval(() => {
    game = advance(game, waitingTurn);
    waitingTurn = undefined;
    renderBoard();
    if (game.phase !== 'playing') {
      stopTimer();
      const result = game.phase === 'won' ? 'Board cleared!' : 'Game over.';
      setMode(game.phase, `${result} You cleared ${game.score} of ${game.score + game.remaining.size} squares.`);
    }
  }, 210);
}

function start() {
  stopTimer();
  game = createGame(slots);
  renderBoard();
  play();
}

function pause() {
  stopTimer();
  setMode('paused', 'Paused.');
}

function turn(direction) {
  if (mode === 'playing' && !waitingTurn && canTurn(game.direction, direction) && direction !== game.direction) {
    waitingTurn = direction;
  }
}

async function loadCalendar() {
  setMode('loading', 'Loading the board…');
  dateRange.textContent = 'Loading calendar…';
  try {
    const response = await fetch('./calendar.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`Calendar request returned ${response.status}`);
    const data = await response.json();
    const layout = calendarLayout(data.days);
    slots = layout.slots;
    screen.style.setProperty('--columns', layout.columns);
    const labels = layout.months.map(month => {
      const label = document.createElement('span');
      label.textContent = month.label;
      label.style.gridColumn = month.column + 1;
      return label;
    });
    months.replaceChildren(...labels);
    cells = slots.map(day => {
      const cell = document.createElement('span');
      if (!day) cell.classList.add('padding');
      return cell;
    });
    board.replaceChildren(...cells);
    dateRange.textContent = dateRangeLabel(data.start, data.end);
    game = createGame(slots);
    total.textContent = ` / ${game.remaining.size}`;
    renderBoard(false);
    screen.hidden = false;
    if (game.phase === 'empty') setMode('empty', 'No contributions in this window.');
    else setMode('ready', 'Eat the glowing square to clear a contribution day.');
  } catch {
    dateRange.textContent = 'Calendar unavailable';
    screen.hidden = true;
    setMode('error', 'The contribution board could not load.');
  }
}

action.addEventListener('click', () => {
  if (mode === 'error') loadCalendar();
  else if (mode === 'playing') pause();
  else if (mode === 'paused') play();
  else start();
});
restart.addEventListener('click', start);
directions.forEach(button => button.addEventListener('click', () => turn(button.dataset.direction)));
window.addEventListener('keydown', event => {
  const direction = keyDirections[event.key] ?? keyDirections[event.key.toLowerCase()];
  if (mode !== 'playing' || !direction || event.altKey || event.ctrlKey || event.metaKey) return;
  event.preventDefault();
  turn(direction);
});
document.addEventListener('visibilitychange', () => {
  if (document.hidden && mode === 'playing') pause();
});

loadCalendar();
