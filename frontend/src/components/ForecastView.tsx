import {useEffect, useState} from "react";
import {fetchForecast} from "../api";
import type {ForecastResponse} from "../api";
import {fmt, MAX_DATE, MIN_DATE} from "../format";
import ForecastChart from "./ForecastChart";
import MetricCard from "./MetricCard";

type Result = {date: string; data: ForecastResponse | null; error: string};

export default function ForecastView() {
  const [date, setDate] = useState("2026-01-15");
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchForecast(date)
      .then(data => {
        if (!cancelled) setResult({date, data, error: ""});
      })
      .catch(e => {
        if (!cancelled)
          setResult({
            date,
            data: null,
            error: e instanceof Error ? e.message : "Request failed",
          });
      });
    return () => {
      cancelled = true;
    };
  }, [date]);

  // Derived state: still loading if the stored result is for a different date.
  const loading = result?.date !== date;
  const data = loading ? null : (result?.data ?? null);
  const error = loading ? "" : (result?.error ?? "");
  // Summary values for the metric cards
  const values = data?.points.map(p => p.forecast_mw) ?? [];
  const mean = values.length
    ? values.reduce((a, b) => a + b, 0) / values.length
    : null;

  return (
    <section className='panel'>
      <div className='panel-heading'>
        <div>
          <h2>Day-ahead wind forecast</h2>
          <p>Latest forecast available when buying for the delivery day.</p>
        </div>
        <label>
          Delivery day{" "}
          <input
            type='date'
            value={date}
            min={MIN_DATE}
            max={MAX_DATE}
            onChange={e => e.target.value && setDate(e.target.value)}
          />
        </label>
      </div>

      {loading && <p>Loading forecast…</p>}
      {error && <p className='error'>{error}</p>}

      {data && !loading && (
        <>
          <p className='note'>
            Decision cutoff: {new Date(data.decision_cutoff).toUTCString()} —
            only forecasts published by then are shown.
          </p>
          <section className='metrics-grid'>
            <MetricCard
              title='Average expected wind'
              value={fmt(mean, " MW")}
            />
            <MetricCard
              title='Peak expected wind'
              value={fmt(values.length ? Math.max(...values) : null, " MW")}
            />
            <MetricCard
              title='Lowest expected wind'
              value={fmt(values.length ? Math.min(...values) : null, " MW")}
            />
          </section>
          <ForecastChart
            data={data.points.map(p => ({
              time: p.delivery_start,
              forecast: p.forecast_mw,
            }))}
          />
        </>
      )}
    </section>
  );
}
