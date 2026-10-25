export const MIN_DATE = "2026-01-01";
export const MAX_DATE = "2026-01-31";

// Chart colours (hex, because SVG attributes are safest with literal values)
export const COLORS = {
  forecast: "#0a6f7a",
  actual: "#c8741a",
  bar: "#0a6f7a",
  grid: "#d9e3e2",
  axis: "#566b70",
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const pad = (n: number) => String(n).padStart(2, "0");

/** 1234.5 -> "1,235 MW"; null -> "N/A" */
export const fmtMW = (value: number | null | undefined) =>
  value === null || value === undefined
    ? "N/A"
    : `${Math.round(value).toLocaleString("en-GB")} MW`;

/** 12.34 -> "12.3%"; null -> "N/A" */
export const fmtPct = (value: number | null | undefined) =>
  value === null || value === undefined ? "N/A" : `${value.toFixed(1)}%`;

/** "2026-01-15" -> "15 Jan" */
export const shortDate = (iso: string) => {
  const d = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
};

/** "2026-01-15" -> "Thu 15 Jan 2026" */
export const longDate = (iso: string) => {
  const d = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  return `${WEEKDAYS[d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
};

/** ISO timestamp -> "03:00" (UTC) */
export const utcTime = (iso: string) => {
  const d = new Date(iso);
  return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
};

/** ISO timestamp -> "15 Jan 03:00 UTC" */
export const utcStamp = (iso: string) => {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${utcTime(iso)} UTC`;
};

/** "2026-01-15" + 1 -> "2026-01-16" */
export const addDays = (iso: string, days: number) => {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
};

/** Round-number axis ticks from 0 up to just above `max` (at most ~5 steps). */
export const niceAxis = (max: number) => {
  const steps = [500, 1000, 2000, 2500, 5000, 10000];
  const step = steps.find(s => max / s <= 5) ?? 10000;
  const top = Math.max(step, Math.ceil(max / step) * step);
  const ticks: number[] = [];
  for (let v = 0; v <= top; v += step) ticks.push(v);
  return {top, ticks};
};
