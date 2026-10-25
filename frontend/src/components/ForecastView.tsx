import {useEffect, useState} from "react";
import {fetchForecast} from "../api";
import type {ForecastResponse} from "../api";
import {addDays, fmtMW, longDate, MAX_DATE, MIN_DATE, utcStamp, utcTime} from "../format";
import ForecastChart from "./ForecastChart";
import MetricCard from "./MetricCard";

type Result = {key: string; data: ForecastResponse | null; error: string};

export default function ForecastView({visible = true}: {visible?: boolean}) {
  const [date, setDate] = useState("2026-01-15");
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<Result | null>(null);

  const key = `${date}|${attempt}`;

  useEffect(() => {
    let cancelled = false;
    fetchForecast(date)
      .then(data => {
        if (!cancelled) setResult({key, data, error: ""});
      })
      .catch(e => {
        if (!cancelled)
          setResult({
            key,
            data: null,
            error: e instanceof Error ? e.message : "Request failed",
          });
      });
    return () => {
      cancelled = true;
    };
  }, [date, key]);

  const loading = result?.key !== key;
  const data = loading ? null : (result?.data ?? null);
  const error = loading ? "" : (result?.error ?? "");

  const points = data?.points ?? [];
  const values = points.map(p => p.forecast_mw);
  const mean = values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  const peak = points.length ? points.reduce((a, b) => (b.forecast_mw > a.forecast_mw ? b : a)) : null;
  const low = points.length ? points.reduce((a, b) => (b.forecast_mw < a.forecast_mw ? b : a)) : null;
  const newestPublish = points.length
    ? points.reduce((a, b) => (b.publish_time > a.publish_time ? b : a)).publish_time
    : null;

  return (
    <section className='panel' id='panel-forecast' role='tabpanel' aria-labelledby='tab-forecast'>
      <h2 className='panel-title'>Day-ahead wind forecast</h2>
      <p className='panel-intro'>
        The wind forecast you would have had in hand when buying power for the delivery day.
      </p>

      <div className='controls'>
        <button
          className='btn secondary icon'
          aria-label='Previous day'
          disabled={date <= MIN_DATE}
          onClick={() => setDate(addDays(date, -1))}
        >
          ‹
        </button>
        <label className='field'>
          Delivery day
          <input
            type='date'
            value={date}
            min={MIN_DATE}
            max={MAX_DATE}
            onChange={e => e.target.value && setDate(e.target.value)}
          />
        </label>
        <button
          className='btn secondary icon'
          aria-label='Next day'
          disabled={date >= MAX_DATE}
          onClick={() => setDate(addDays(date, 1))}
        >
          ›
        </button>
      </div>

      <div aria-live='polite'>
        {loading && (
          <div role='status'>
            <p className='sr-only'>Loading forecast…</p>
            <div className='skeleton' aria-hidden='true' />
          </div>
        )}

        {error && (
          <div className='state error' role='alert'>
            <p className='state-title'>Couldn’t load the forecast</p>
            <p>{error}</p>
            <button className='btn' onClick={() => setAttempt(a => a + 1)}>
              Try again
            </button>
          </div>
        )}

        {data && !loading && points.length === 0 && (
          <div className='state'>
            <p className='state-title'>No forecast for {longDate(data.delivery_date)}</p>
            <p>No forecast had been published before the decision cutoff. Try another day.</p>
          </div>
        )}

        {data && !loading && peak && low && (
          <>
            <p className='answer'>
              On {longDate(data.delivery_date)}, wind is forecast to average{" "}
              <span className='num'>{fmtMW(mean)}</span>, peaking at{" "}
              <span className='num'>{fmtMW(peak.forecast_mw)}</span> around {utcTime(peak.delivery_start)} UTC.
            </p>
            <p className='answer-detail'>
              Based on the latest forecast published before the decision cutoff of{" "}
              {utcStamp(data.decision_cutoff)}
              {newestPublish ? ` (newest forecast used: published ${utcStamp(newestPublish)})` : ""}. Anything
              published later would not have been available when buying.
            </p>

            <div className='stats'>
              <MetricCard label='Average expected wind' value={fmtMW(mean)} note='Across the 24 hours' />
              <MetricCard
                label='Highest hour'
                value={fmtMW(peak.forecast_mw)}
                note={`At ${utcTime(peak.delivery_start)} UTC`}
              />
              <MetricCard
                label='Lowest hour'
                value={fmtMW(low.forecast_mw)}
                note={`At ${utcTime(low.delivery_start)} UTC. Expect to buy the most here.`}
              />
            </div>

            {visible && (
              <ForecastChart data={points.map(p => ({time: p.delivery_start, forecast: p.forecast_mw}))} />
            )}
          </>
        )}
      </div>
    </section>
  );
}
