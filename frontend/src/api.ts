const API_BASE_URL = "http://127.0.0.1:8000";

export interface AccuracyMatch {
  delivery_start: string;
  actual_mw: number;
  forecast_mw: number;
  absolute_error_mw: number;
}

export interface AccuracyResponse {
  period: {
    start: string;
    end_inclusive: string;
  };
  decision_cutoff: string;
  forecast_source: string;
  actual_intervals_received: number;
  hourly_actual_intervals: number;
  forecast_records_received: number;
  matched_intervals: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  mape_percent: number | null;
  eligible_intervals: number;
  forecast_coverage_percent: number | null;
  matches: AccuracyMatch[];
  evaluation_note: string;
}

export async function fetchAccuracy(
  startDate: string,
  endDate: string,
  decisionCutoff: string,
): Promise<AccuracyResponse> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    decision_cutoff: decisionCutoff,
  });

  const response = await fetch(`${API_BASE_URL}/api/data/accuracy?${params}`);

  if (!response.ok) {
    throw new Error(`Accuracy request failed: ${response.status}`);
  }

  return response.json() as Promise<AccuracyResponse>;
}
