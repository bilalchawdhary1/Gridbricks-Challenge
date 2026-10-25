export const fmt = (value: number | null | undefined, suffix = "") =>
  value === null || value === undefined
    ? "N/A"
    : `${value.toLocaleString(undefined, {maximumFractionDigits: 1})}${suffix}`;

export const MIN_DATE = "2026-01-01";
export const MAX_DATE = "2026-01-31";
