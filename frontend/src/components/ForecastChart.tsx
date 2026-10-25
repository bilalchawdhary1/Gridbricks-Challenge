import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {AccuracyMatch} from "../api";

type ForecastChartProps = {
  matches: AccuracyMatch[];
};

export default function ForecastChart({matches}: ForecastChartProps) {
  const chartData = matches.map(match => ({
    time: new Date(match.delivery_start).toISOString().slice(11, 16),
    actual: match.actual_mw,
    forecast: match.forecast_mw,
  }));

  if (chartData.length === 0) {
    return <p>No matched forecast data available to chart.</p>;
  }

  return (
    <div style={{width: "100%", height: 360}}>
      <ResponsiveContainer width='100%' height='100%'>
        <LineChart
          data={chartData}
          margin={{top: 12, right: 20, left: 12, bottom: 8}}
        >
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis
            dataKey='time'
            tick={{fontSize: 12}}
            label={{
              value: "Delivery time (UTC)",
              position: "insideBottom",
              offset: -5,
            }}
          />
          <YAxis
            tick={{fontSize: 12}}
            domain={["auto", "auto"]}
            width={75}
            label={{
              value: "Generation (MW)",
              angle: -90,
              position: "insideLeft",
            }}
          />
          <Tooltip
            formatter={(value, name) => [
              `${Number(value).toLocaleString()} MW`,
              name === "actual" ? "Actual" : "Forecast",
            ]}
          />
          <Legend />
          <Line
            type='monotone'
            dataKey='actual'
            name='Actual generation'
            stroke='#16a34a'
            strokeWidth={2.5}
            dot={{r: 3}}
          />
          <Line
            type='monotone'
            dataKey='forecast'
            name='Forecast generation'
            stroke='#2563eb'
            strokeWidth={2.5}
            dot={{r: 3}}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
