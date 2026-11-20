import { cp, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { calendarLayout, dateRangeLabel, levelColors } from '../game/calendar.mjs';

const DAY = 86_400_000;
const LEVELS = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'];
const eastCoast = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York', year: 'numeric', month: 'numeric', day: 'numeric',
});
const formatDay = timestamp => new Date(timestamp).toISOString().slice(0, 10);

export function windowFor(now) {
  const { year, month, day } = Object.fromEntries(eastCoast.formatToParts(now).map(part => [part.type, Number(part.value)]));
  const targetMonth = month - 4;
  const lastDayOfTargetMonth = new Date(Date.UTC(year, targetMonth + 1, 0)).getUTCDate();
  const threeMonthsAgo = Date.UTC(year, targetMonth, Math.min(day, lastDayOfTargetMonth));
  return { start: formatDay(threeMonthsAgo + DAY), end: formatDay(Date.UTC(year, month - 1, day)) };
}

export function normalizeCalendar(window, contributionDays) {
  const { start, end } = window;
  const levels = new Map();
  for (const { date, contributionLevel } of contributionDays) {
    if (date < start || date > end) continue;
    const level = LEVELS.indexOf(contributionLevel);
    if (level === -1 || levels.has(date)) throw new Error(`Invalid contribution result for ${date}`);
    levels.set(date, level);
  }

  const days = [];
  for (let timestamp = Date.parse(start); timestamp <= Date.parse(end); timestamp += DAY) {
    const date = formatDay(timestamp);
    if (!levels.has(date)) throw new Error(`GitHub omitted ${date} from the contribution calendar`);
    days.push({ date, level: levels.get(date) });
  }

  return { ...window, days };
}

export function previewSvg(data) {
  const { columns, slots, months } = calendarLayout(data.days);
  const width = columns * 24 + 35;
  const range = dateRangeLabel(data.start, data.end);
  const cells = slots.map((day, index) => {
    const x = 20 + 24 * Math.floor(index / 7);
    const y = 64 + 24 * (index % 7);
    return day ? `<rect x="${x}" y="${y}" width="20" height="20" rx="4" fill="${levelColors[day.level]}"/>` : '';
  });
  const labels = months.map(({ column, label }) => `<text x="${20 + 24 * column}" y="54">${label}</text>`);

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} 248" role="img" aria-labelledby="title">
  <title id="title">GitHub contributions for ${range}</title>
  <defs>
    <linearGradient id="screen" x2="0" y2="1">
      <stop stop-color="#1d344b"/><stop offset="1" stop-color="#101b2b"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="${width - 1}" height="247" rx="18" fill="url(#screen)" stroke="#3a566f"/>
  <rect x="20" y="17" width="4" height="16" rx="2" fill="#ffb05e"/>
  <text x="32" y="30" font-family="system-ui, sans-serif" font-size="14" font-weight="700" fill="#eff8fa">${range}</text>
  <g font-family="monospace" font-size="12" fill="#bbd4e1">${labels.join('')}</g>
  <g>${cells.join('')}</g>
</svg>\n`;
}

async function fetchCalendar(window, token) {
  const response = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: `query($from: DateTime!, $to: DateTime!) {
        user(login: "mwc2150") {
          contributionsCollection(from: $from, to: $to) {
            contributionCalendar { weeks { contributionDays { date contributionLevel } } }
          }
        }
      }`,
      variables: { from: `${window.start}T00:00:00Z`, to: `${window.end}T23:59:59Z` },
    }),
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) throw new Error(`GitHub GraphQL returned HTTP ${response.status}`);
  const payload = await response.json();
  const weeks = payload.data?.user?.contributionsCollection?.contributionCalendar?.weeks;
  if (payload.errors?.length || !weeks) {
    throw new Error(`GitHub did not return a complete calendar: ${payload.errors?.map(error => error.message).join('; ') ?? 'missing weeks'}`);
  }

  return normalizeCalendar(window, weeks.flatMap(week => week.contributionDays));
}

async function buildGame(output, token) {
  const data = await fetchCalendar(windowFor(new Date()), token);
  await mkdir(output, { recursive: true });
  await cp(new URL('../game/', import.meta.url), output, { recursive: true });
  await Promise.all([
    cp(new URL('../assets/goku-fishing.webp', import.meta.url), resolve(output, 'goku-fishing.webp')),
    writeFile(resolve(output, 'calendar.json'), `${JSON.stringify(data)}\n`),
    writeFile(resolve(output, 'board.svg'), previewSvg(data)),
  ]);
  console.log(`Prepared the game for ${data.start} through ${data.end} (${data.days.length} days).`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const output = process.argv[2];
  const token = process.env.GH_TOKEN;
  if (!output || !token) throw new Error('Set GH_TOKEN and pass a deployment output directory.');
  await buildGame(resolve(output), token);
}
