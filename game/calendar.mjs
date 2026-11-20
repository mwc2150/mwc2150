export const levelColors = ['#263c52', '#2e6777', '#349c9c', '#63cabb', '#a0f4d3'];

export function calendarLayout(days) {
  const first = new Date(`${days[0].date}T00:00:00Z`).getUTCDay();
  const columns = Math.ceil((first + days.length) / 7);
  const slots = Array(columns * 7).fill(null);
  const months = [];
  let lastMonth;

  days.forEach((day, index) => {
    const slot = first + index;
    slots[slot] = day;
    const month = day.date.slice(0, 7);
    if (month !== lastMonth) {
      const label = new Date(`${day.date}T00:00:00Z`).toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' });
      months.push({ column: Math.floor(slot / 7), label });
      lastMonth = month;
    }
  });

  // The first two month marks can occupy the same week on short partial months.
  return { columns, slots, months: months.filter((month, index) => months[index + 1]?.column !== month.column) };
}

export function dateRangeLabel(start, end) {
  const from = new Date(`${start}T00:00:00Z`);
  const to = new Date(`${end}T00:00:00Z`);
  const format = (date, showYear) => date.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', timeZone: 'UTC', ...(showYear && { year: 'numeric' }),
  });
  return `${format(from, from.getUTCFullYear() !== to.getUTCFullYear())} – ${format(to, true)}`;
}
