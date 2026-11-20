import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { retroSnakeSvg } from './retro-snake.mjs';

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

async function buildSnake(output, token) {
  const data = await fetchCalendar(windowFor(new Date()), token);
  await mkdir(output, { recursive: true });
  await Promise.all([
    writeFile(resolve(output, 'snake.svg'), retroSnakeSvg(data, true)),
    writeFile(resolve(output, 'snake-still.svg'), retroSnakeSvg(data, false)),
    writeFile(resolve(output, 'index.html'), `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=https://github.com/mwc2150">
  <title>Contribution Snake</title>
</head>
<body><p><a href="https://github.com/mwc2150">See Contribution Snake on my GitHub profile</a></p></body>
</html>\n`),
  ]);
  console.log(`Prepared the contribution snake for ${data.start} through ${data.end} (${data.days.length} days).`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const output = process.argv[2];
  const token = process.env.GH_TOKEN;
  if (!output || !token) throw new Error('Set GH_TOKEN and pass a deployment output directory.');
  await buildSnake(resolve(output), token);
}
