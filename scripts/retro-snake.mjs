import { calendarLayout } from './calendar.mjs';

const COLORS = ['#223950', '#28726f', '#2fa599', '#5ad4b4', '#a5f5d5'];
const CELL = 16;
const ORIGIN_X = 20;
const ORIGIN_Y = 33;
const STEP_SECONDS = 0.12;
const INTRO_STEPS = 5;
const PAUSE_STEPS = 14;
const SEGMENT_COLORS = ['#ffbc62', '#f29242', '#e57c39', '#ce6532'];

export function snakePath(columns) {
  return Array.from({ length: columns * 7 }, (_, step) => {
    const column = Math.floor(step / 7);
    const row = step % 7;
    return column * 7 + (column % 2 ? 6 - row : row);
  });
}

function position(slot) {
  return `${ORIGIN_X + Math.floor(slot / 7) * CELL} ${ORIGIN_Y + (slot % 7) * CELL}`;
}

export function retroSnakeSvg(data, animated) {
  const { columns, slots, months } = calendarLayout(data.days);
  const width = columns * CELL + ORIGIN_X * 2 - 3;
  const height = 156;
  const path = snakePath(columns);
  const visits = new Map(path.map((slot, index) => [slot, INTRO_STEPS + index]));
  const totalSteps = INTRO_STEPS + path.length + SEGMENT_COLORS.length + PAUSE_STEPS;
  const seconds = (totalSteps * STEP_SECONDS).toFixed(2);
  const keyTime = step => (step / totalSteps).toFixed(6);

  const cells = slots.map((day, slot) => {
    if (!day) return '';

    const [x, y] = position(slot).split(' ');
    const fill = COLORS[day.level];
    const clear = animated && day.level > 0
      ? `<animate attributeName="fill" values="${fill};${COLORS[0]};${fill}" keyTimes="0;${keyTime(visits.get(slot))};1" calcMode="discrete" dur="${seconds}s" repeatCount="indefinite"/>`
      : '';
    return `<rect x="${x}" y="${y}" width="13" height="13" fill="${fill}">${clear}</rect>`;
  });

  const labels = months.map(({ column, label }) =>
    `<text x="${ORIGIN_X + column * CELL}" y="24">${label.toUpperCase()}</text>`);

  const segments = [];
  if (animated) {
    const frames = Array.from({ length: totalSteps + 1 }, (_, step) => step);
    const times = frames.map(keyTime).join(';');
    for (const [index, color] of SEGMENT_COLORS.entries()) {
      const positions = frames.map(step => {
        const slot = path[step - INTRO_STEPS - index];
        return slot === undefined ? '-24 -24' : position(slot);
      }).join(';');
      const face = index === 0 ? '<path d="M3 4h2v3H3zm5 0h2v3H8zM5 9h3v1H5z" fill="#422724"/>' : '';
      segments.unshift(`<g transform="translate(-24 -24)">
      <animateTransform attributeName="transform" type="translate" values="${positions}" keyTimes="${times}" calcMode="discrete" dur="${seconds}s" repeatCount="indefinite"/>
      <path d="M2 0h9v2h2v9h-2v2H2v-2H0V2h2z" fill="${color}"/>
      ${face}
    </g>`);
    }
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title">
  <title id="title">${animated ? 'Pixel snake eating' : 'Pixel arcade board of'} GitHub contributions over the last three months</title>
  <desc>${slots.filter(Boolean).length} days from ${data.start} through ${data.end}</desc>
  <g shape-rendering="crispEdges">
    <path d="M6 0h${width - 12}v3h3v3h3v${height - 12}h-3v3h-3v3H6v-3H3v-3H0V6h3V3h3z" fill="#426783"/>
    <path d="M7 3h${width - 14}v3h4v${height - 12}H${width - 7}v3H7v-3H3V6h4z" fill="#182c43"/>
    <rect x="13" y="11" width="${width - 26}" height="134" fill="#101c30"/>
    <path d="M7 20h3v3H7zm0 6h3v3H7zm${width - 17} 100h3v3h-3zm0 6h3v3h-3z" fill="#ed9853"/>
    ${cells.join('\n    ')}
    ${segments.join('\n    ')}
  </g>
  <g font-family="monospace" font-weight="bold" font-size="8" letter-spacing="0.8" fill="#a2c3d2">${labels.join('')}</g>
</svg>\n`;
}
