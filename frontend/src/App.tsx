import {useState} from "react";
import "./App.css";
import AccuracyView from "./components/AccuracyView";
import ForecastView from "./components/ForecastView";

type Tab = "forecast" | "accuracy";

export default function App() {
  const [tab, setTab] = useState<Tab>("forecast");

  return (
    <main className='dashboard'>
      <header className='dashboard-header'>
        <div>
          <p className='eyebrow'>DAY-AHEAD POWER PROCUREMENT</p>
          <h1>Wind Forecast Portal</h1>
          <p className='subtitle'>
            UK national wind generation · January 2026 · Elexon data
          </p>
        </div>
      </header>

      <nav className='tabs'>
        <button
          className={tab === "forecast" ? "active" : ""}
          onClick={() => setTab("forecast")}
        >
          Day-ahead forecast
        </button>
        <button
          className={tab === "accuracy" ? "active" : ""}
          onClick={() => setTab("accuracy")}
        >
          Forecast accuracy
        </button>
      </nav>

      {tab === "forecast" ? <ForecastView /> : <AccuracyView />}
    </main>
  );
}
