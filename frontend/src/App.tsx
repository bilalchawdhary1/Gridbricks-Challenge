import {useState} from "react";
import "./App.css";
import AccuracyView from "./components/AccuracyView";
import ForecastView from "./components/ForecastView";

type Tab = "forecast" | "accuracy";

export default function App() {
  const [tab, setTab] = useState<Tab>("forecast");

  return (
    <main className='page'>
      <header className='site-header'>
        <h1>Wind forecast for day-ahead buying</h1>
        <p>UK national wind generation, January 2026. Source: Elexon.</p>
      </header>

      <div className='tabs' role='tablist' aria-label='Views'>
        <button
          id='tab-forecast'
          className='tab'
          role='tab'
          aria-selected={tab === "forecast"}
          aria-controls='panel-forecast'
          onClick={() => setTab("forecast")}
        >
          Day-ahead forecast
        </button>
        <button
          id='tab-accuracy'
          className='tab'
          role='tab'
          aria-selected={tab === "accuracy"}
          aria-controls='panel-accuracy'
          onClick={() => setTab("accuracy")}
        >
          Forecast accuracy
        </button>
      </div>

      {/* Both views stay mounted so switching tabs keeps their state. */}
      <div hidden={tab !== "forecast"}>
        <ForecastView visible={tab === "forecast"} />
      </div>
      <div hidden={tab !== "accuracy"}>
        <AccuracyView visible={tab === "accuracy"} />
      </div>
    </main>
  );
}
