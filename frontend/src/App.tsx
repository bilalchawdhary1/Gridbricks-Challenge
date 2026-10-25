import {useEffect, useState} from "react";
import "./App.css";
import {fetchAccuracy} from "./api";
import type {AccuracyResponse} from "./api";
import ForecastChart from "./components/ForecastChart";

function App() {
  const [data, setData] = useState<AccuracyResponse | null>(null);
  const [status, setStatus] = useState("Loading...");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAccuracy("2026-10-20", "2026-10-20", "2026-10-20T10:30:00Z")
      .then(result => {
        setData(result);
        setStatus("Connected");
      })
      .catch((err: unknown) => {
        setStatus("Disconnected");
        setError(err instanceof Error ? err.message : "Request failed");
      });
  }, []);

  const formatNumber = (value: number | null, suffix = "") =>
    value === null
      ? "N/A"
      : `${value.toLocaleString(undefined, {
          maximumFractionDigits: 2,
        })}${suffix}`;

  return (
    <main className='dashboard'>
      <header className='dashboard-header'>
        <div>
          <p className='eyebrow'>ENERGY ANALYTICS</p>
          <h1>Gridbricks Challenge</h1>
          <p className='subtitle'>Wind generation forecast accuracy</p>
        </div>

        <span className={`status ${data ? "online" : "offline"}`}>
          <span className='status-dot' />
          Backend: {status}
        </span>
      </header>

      {error && <p className='error'>{error}</p>}

      {data && (
        <>
          <section className='metrics-grid'>
            <MetricCard
              title='Mean Absolute Error'
              value={formatNumber(data.mae_mw, " MW")}
            />
            <MetricCard
              title='Root Mean Squared Error'
              value={formatNumber(data.rmse_mw, " MW")}
            />
            <MetricCard
              title='Mean Absolute Percentage Error'
              value={formatNumber(data.mape_percent, "%")}
            />
            <MetricCard
              title='Forecast Coverage'
              value={formatNumber(data.forecast_coverage_percent, "%")}
              detail={`${data.matched_intervals} of ${data.eligible_intervals} eligible hours`}
            />
          </section>

          <section className='panel'>
            <div className='panel-heading'>
              <div>
                <h2>Hourly Forecast vs Actual</h2>
                <p>
                  {data.period.start} · Cutoff{" "}
                  {new Date(data.decision_cutoff).toLocaleString()}
                </p>
              </div>
              <span className='record-count'>
                {data.matches.length} matched hours
              </span>
            </div>
            <ForecastChart matches={data.matches} />
            <div className='table-wrapper'>
              <table>
                <thead>
                  <tr>
                    <th>Delivery (UTC)</th>
                    <th>Actual (MW)</th>
                    <th>Forecast (MW)</th>
                    <th>Absolute Error (MW)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.matches.map(match => (
                    <tr key={match.delivery_start}>
                      <td>
                        {new Date(match.delivery_start)
                          .toISOString()
                          .replace("T", " ")
                          .slice(0, 16)}
                      </td>
                      <td>{formatNumber(match.actual_mw)}</td>
                      <td>{formatNumber(match.forecast_mw)}</td>
                      <td className='error-value'>
                        {formatNumber(match.absolute_error_mw)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <p className='note'>{data.evaluation_note}</p>
        </>
      )}
    </main>
  );
}

type MetricCardProps = {
  title: string;
  value: string;
  detail?: string;
};

function MetricCard({title, value, detail}: MetricCardProps) {
  return (
    <article className='metric-card'>
      <p>{title}</p>
      <h2>{value}</h2>
      {detail && <span>{detail}</span>}
    </article>
  );
}

export default App;
