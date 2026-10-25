import {useEffect, useState} from "react";
import {Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";
import {fetchAccuracy} from "../api";
import type {AccuracyResponse} from "../api";
import {COLORS, fmtMW, fmtPct, MAX_DATE, MIN_DATE, niceAxis, shortDate} from "../format";
import ForecastChart from "./ForecastChart";
import MetricCard from "./MetricCard";

type Result = {key: string; data: AccuracyResponse | null; error: string};

const PRESETS = [
  {label: "First week", start: "2026-01-01", end: "2026-01-07"},
  {label: "Last week", start: "2026-01-25", end: "2026-01-31"},
  {label: "Full month", start: "2026-01-01", end: "2026-01-31"},
];

export default function AccuracyView({visible = true}: {visible?: boolean}) {
  // Draft values in the inputs
  const [start, setStart] = useState("2026-01-01");
  const [end, setEnd] = useState("2026-01-07");
  // Range that has actually been requested
  const [applied, setApplied] = useState({start: "2026-01-01", end: "2026-01-07"});
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const [inputError, setInputError] = useState("");

  const key = `${applied.start}|${applied.end}|${attempt}`;

  useEffect(() => {
    let cancelled = false;
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
  }, [applied.start, applied.end, key]);

  const loading = result?.key !== key;
  const data = loading ? null : (result?.data ?? null);
  const error = loading ? "" : (result?.error ?? "");

  const apply = (s: string, e: string) => {
    if (e < s) {
      setInputError("The end date must be on or after the start date.");
      return;
    }
    setInputError("");
    setApplied({start: s, end: e});
  };

  const choosePreset = (s: string, e: string) => {
    setStart(s);
    setEnd(e);
    apply(s, e);
  };

  // Error by hour of day
  const byHour = Array.from({length: 24}, (_, h) => ({
    hour: `${String(h).padStart(2, "0")}:00`,
    sum: 0,
    n: 0,
  }));
  data?.matches.forEach(m => {
    const h = new Date(m.delivery_start).getUTCHours();
    byHour[h].sum += m.absolute_error_mw;
    byHour[h].n += 1;
  });
  const hourData = byHour.map(b => ({hour: b.hour, mae: b.n ? b.sum / b.n : 0}));
  const hourAxis = niceAxis(Math.max(...hourData.map(h => h.mae)));
  const worstHour = hourData.reduce((a, b) => (b.mae > a.mae ? b : a), hourData[0]);

  // "9 in 10 hours the miss was smaller than ..."
  const sortedErrors = (data?.matches ?? []).map(m => m.absolute_error_mw).sort((a, b) => a - b);
  const p90 = sortedErrors.length
    ? sortedErrors[Math.min(sortedErrors.length - 1, Math.ceil(sortedErrors.length * 0.9) - 1)]
    : null;

  const bias = data?.forecast_bias_mw ?? null;
  const biasWord = bias === null ? "" : bias > 0 ? "too high" : "too low";
  const periodLabel = data
    ? data.period.start === data.period.end_inclusive
      ? shortDate(data.period.start)
      : `${shortDate(data.period.start)} to ${shortDate(data.period.end_inclusive)}`
    : "";

  return (
    <section className='panel' id='panel-accuracy' role='tabpanel' aria-labelledby='tab-accuracy'>
      <h2 className='panel-title'>How accurate was the forecast?</h2>
      <p className='panel-intro'>
        Each delivery day is scored against the forecast that was available at its own day-ahead
        cutoff, then compared with what the wind farms actually generated.
      </p>

      <div className='controls'>
        <label className='field'>
          From
          <input
            type='date'
            value={start}
            min={MIN_DATE}
            max={MAX_DATE}
            onChange={e => e.target.value && setStart(e.target.value)}
          />
        </label>
        <label className='field'>
          To
          <input
            type='date'
            value={end}
            min={MIN_DATE}
            max={MAX_DATE}
            onChange={e => e.target.value && setEnd(e.target.value)}
          />
        </label>
        <button className='btn' onClick={() => apply(start, end)} disabled={loading}>
          {loading ? "Evaluating…" : "Evaluate"}
        </button>
        <div className='presets' role='group' aria-label='Quick ranges'>
          {PRESETS.map(p => (
            <button
              key={p.label}
              className='preset'
              aria-pressed={applied.start === p.start && applied.end === p.end}
              onClick={() => choosePreset(p.start, p.end)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div aria-live='polite'>
        {inputError && (
          <div className='state error' role='alert'>
            <p>{inputError}</p>
          </div>
        )}

        {loading && (
          <div role='status'>
            <p className='sr-only'>Evaluating forecast accuracy…</p>
            <div className='skeleton' aria-hidden='true' />
          </div>
        )}

        {error && (
          <div className='state error' role='alert'>
            <p className='state-title'>Couldn’t evaluate this range</p>
            <p>{error}</p>
            <button className='btn' onClick={() => setAttempt(a => a + 1)}>
              Try again
            </button>
          </div>
        )}

        {data && !loading && data.matched_intervals === 0 && (
          <div className='state'>
            <p className='state-title'>Nothing to compare for {periodLabel}</p>
            <p>No hours had both a forecast and an actual reading. Try a different range.</p>
          </div>
        )}

        {data && !loading && data.matched_intervals > 0 && (
          <>
            <p className='answer'>
              For {periodLabel}, the forecast missed actual wind output by{" "}
              <span className='num'>{fmtMW(data.mae_mw)}</span> in a typical hour
              {bias !== null && (
                <>
                  , and on average ran <span className='num'>{fmtMW(Math.abs(bias))}</span> {biasWord}
                </>
              )}
              .
            </p>
            <p className='answer-detail'>
              {p90 !== null && (
                <>
                  In 9 out of 10 hours the miss was under <span className='num'>{fmtMW(p90)}</span>, a useful
                  margin to plan for when buying.{" "}
                </>
              )}
              {bias !== null && bias > 0 &&
                "Over-forecasting wind means buying less than you need and covering the gap later."}
              {bias !== null && bias <= 0 &&
                "Under-forecasting wind means buying more than you need."}
            </p>

            <div className='stats'>
              <MetricCard label='Typical miss' value={fmtMW(data.mae_mw)} note='Average size of the error (MAE)' />
              <MetricCard
                label='Big-miss measure'
                value={fmtMW(data.rmse_mw)}
                note='Weights large errors more (RMSE)'
              />
              <MetricCard
                label='Average bias'
                value={fmtMW(bias === null ? null : Math.abs(bias))}
                note={bias === null ? undefined : `Forecast ran ${biasWord} on average`}
              />
              <MetricCard
                label='Error vs generation'
                value={fmtPct(data.wape_percent)}
                note='Total error as a share of total wind (WAPE)'
              />
              <MetricCard
                label='Hours compared'
                value={`${data.matched_intervals}`}
                note={`${fmtPct(data.forecast_coverage_percent)} of ${data.eligible_intervals} possible`}
              />
            </div>

            <div className='chart-block'>
              <h3 className='chart-title'>Forecast vs actual</h3>
              <p className='chart-caption'>Hourly wind generation, {periodLabel}.</p>
              {visible && (
              <ForecastChart
                showActual
                data={data.matches.map(m => ({
                  time: m.delivery_start,
                  forecast: m.forecast_mw,
                  actual: m.actual_mw,
                }))}
              />
              )}
            </div>

            <div className='chart-block'>
              <h3 className='chart-title'>Which hours are hardest to forecast?</h3>
              <p className='chart-caption'>
                Average miss by hour of day (UTC). The largest is at {worstHour.hour}, at about{" "}
                {fmtMW(worstHour.mae)}.
              </p>
              {visible && (
              <div className='chart short'>
                <ResponsiveContainer width='100%' height='100%'>
                  <BarChart data={hourData} margin={{top: 8, right: 16, left: 4, bottom: 8}}>
                    <CartesianGrid stroke={COLORS.grid} vertical={false} />
                    <XAxis
                      dataKey='hour'
                      tick={{fontSize: 12, fill: COLORS.axis}}
                      tickLine={false}
                      axisLine={{stroke: COLORS.grid}}
                      interval={2}
                    />
                    <YAxis
                      tick={{fontSize: 12, fill: COLORS.axis}}
                      tickLine={false}
                      axisLine={false}
                      width={64}
                      domain={[0, hourAxis.top]}
                      ticks={hourAxis.ticks}
                      tickFormatter={(v: number) => v.toLocaleString("en-GB")}
                    />
                    <Tooltip
                      cursor={{fill: "#e3f0f0"}}
                      formatter={v => [`${Math.round(Number(v)).toLocaleString("en-GB")} MW`, "Average miss"]}
                    />
                    <Bar dataKey='mae' name='Average miss' fill={COLORS.bar} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              )}
            </div>

            <p className='footnote'>{data.evaluation_note}</p>
          </>
        )}
      </div>
    </section>
  );
}
