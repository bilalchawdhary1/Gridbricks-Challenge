const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface ForecastPoint {
  delivery_start: string;
  forecast_mw: number;
  publish_time: string;
}

export interface ForecastResponse {
  delivery_date: string;
  decision_cutoff: string;
  points: ForecastPoint[];
}

export interface AccuracyMatch {
  delivery_start: string;
  actual_mw: number;
  forecast_mw: number;
  absolute_error_mw: number;
  publish_time: string;
}

export interface AccuracyResponse {
  period: {start: string; end_inclusive: string};
  matched_intervals: number;
  eligible_intervals: number;
  forecast_coverage_percent: number | null;
  mae_mw: number | null;
  rmse_mw: number | null;
  forecast_bias_mw: number | null;
  wape_percent: number | null;
  mape_percent: number | null;
  matches: AccuracyMatch[];
  evaluation_note: string;
}

async function get<T>(
  path: string,
  params: Record<string, string>,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}/api/data/${path}?${new URLSearchParams(params)}`,
  );
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* keep default message */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const fetchForecast = (date: string) =>
  get<ForecastResponse>("forecast", {date});

export const fetchAccuracy = (start_date: string, end_date: string) =>
  get<AccuracyResponse>("accuracy", {start_date, end_date});
