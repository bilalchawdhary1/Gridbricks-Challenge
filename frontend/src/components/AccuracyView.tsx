import {useEffect, useState} from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {fetchAccuracy} from "../api";
import type {AccuracyResponse} from "../api";
import {fmt, MAX_DATE, MIN_DATE} from "../format";
import ForecastChart from "./ForecastChart";
import MetricCard from "./MetricCard";

type Result = {key: string; data: AccuracyResponse | null; error: string};

export default function AccuracyView() {
  // Draft values in the inputs
  const [start, setStart] = useState("2026-01-01");
  const [end, setEnd] = useState("2026-01-07");
  // Range that has actually been requested (set by the Evaluate button)
  const [applied, setApplied] = useState({
    start: "2026-01-01",
    end: "2026-01-07",
  });
  const [result, setResult] = useState<Result | null>(null);
  const [inputError, setInputError] = useState("");

  const appliedKey = `${applied.start}|${applied.end}`;

  useEffect(() => {
    let cancelled = false;
    const key = `${applied.start}|${applied.end}`;
    fetchAccuracy(applied.start, applied.end)
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
  }, [applied.start, applied.end]);

  const loading = result?.key !== appliedKey;
  const data = loading ? null : (result?.data ?? null);
  const error = inputError || (loading ? "" : (result?.error ?? ""));

  const handleEvaluate = () => {
    if (end < start) {
      setInputError("End date must be on or after start date.");
      return;
    }
    setInputError("");
    setApplied({start, end});
  };

  // ...keep `const byHour = ...` and everything below it as before
  const byHour = Array.from({length: 24}, (_, h) => ({
    hour: `${h}:00`,
    sum: 0,
    n: 0,
  }));
  data?.matches.forEach(m => {
    const h = new Date(m.delivery_start).getUTCHours();
    byHour[h].sum += m.absolute_error_mw;
    byHour[h].n += 1;
  });
  const hourData = byHour.map(b => ({
    hour: b.hour,
    mae: b.n ? b.sum / b.n : 0,
  }));

  const bias = data?.forecast_bias_mw ?? null;
  const biasDetail =
    bias === null
      ? undefined
      : bias > 0
        ? "Forecast over-predicts wind"
        : "Forecast under-predicts wind";

  return (
    <section className='panel'>
      <div className='panel-heading'>
        <div>
          <h2>Forecast accuracy</h2>
          <p>
            Each day is scored using the forecast available at its day-ahead
            cutoff.
          </p>
        </div>
        <div>
          <input
            type='date'
            value={start}
            min={MIN_DATE}
            max={MAX_DATE}
            onChange={e => e.target.value && setStart(e.target.value)}
          />{" "}
          to{" "}
          <input
            type='date'
            value={end}
            min={MIN_DATE}
            max={MAX_DATE}
            onChange={e => e.target.value && setEnd(e.target.value)}
          />{" "}
          <button onClick={handleEvaluate} disabled={loading}>
            Evaluate
          </button>
        </div>
      </div>

      {loading && <p>Evaluating… large ranges can take a while.</p>}
      {error && <p className='error'>{error}</p>}

      {data &&
        !loading &&
        (data.matched_intervals === 0 ? (
          <p>No matched forecast/actual data for this range.</p>
        ) : (
          <>
            <section className='metrics-grid'>
              <MetricCard
                title='MAE'
                value={fmt(data.mae_mw, " MW")}
                detail='Typical size of the error'
              />
              <MetricCard
                title='RMSE'
                value={fmt(data.rmse_mw, " MW")}
                detail='Penalises large misses'
              />
              <MetricCard
                title='Bias'
                value={fmt(bias, " MW")}
                detail={biasDetail}
              />
              <MetricCard
                title='WAPE'
                value={fmt(data.wape_percent, "%")}
                detail='Error relative to total wind'
              />
              <MetricCard
                title='Coverage'
                value={fmt(data.forecast_coverage_percent, "%")}
                detail={`${data.matched_intervals} of ${data.eligible_intervals} hours`}
              />
            </section>

            <h3>Forecast vs actual</h3>
            <ForecastChart
              showActual
              data={data.matches.map(m => ({
                time: m.delivery_start,
                forecast: m.forecast_mw,
                actual: m.actual_mw,
              }))}
            />

            <h3>Average error by hour of day (UTC)</h3>
            <div style={{width: "100%", height: 260}}>
              <ResponsiveContainer>
                <BarChart data={hourData}>
                  <CartesianGrid strokeDasharray='3 3' />
                  <XAxis dataKey='hour' tick={{fontSize: 11}} />
                  <YAxis width={70} />
                  <Tooltip formatter={v => `${Number(v).toFixed(0)} MW`} />
                  <Bar dataKey='mae' name='MAE (MW)' fill='#2563eb' />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <p className='note'>{data.evaluation_note}</p>
          </>
        ))}
    </section>
  );
}
