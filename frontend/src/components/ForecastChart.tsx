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

export type ChartPoint = {time: string; forecast: number; actual?: number};

type Props = {data: ChartPoint[]; showActual?: boolean};

export default function ForecastChart({data, showActual = false}: Props) {
  if (data.length === 0) return <p>No data available for this selection.</p>;

  return (
    <div style={{width: "100%", height: 360}}>
      <ResponsiveContainer width='100%' height='100%'>
        <LineChart
          data={data}
          margin={{top: 12, right: 20, left: 12, bottom: 24}}
        >
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis
            dataKey='time'
            tick={{fontSize: 11}}
            minTickGap={40}
            tickFormatter={(t: string) => t.slice(5, 16).replace("T", " ")}
            label={{
              value: "Delivery time (UTC)",
              position: "insideBottom",
              offset: -12,
            }}
          />
          <YAxis
            tick={{fontSize: 12}}
            width={80}
            label={{
              value: "Wind generation (MW)",
              angle: -90,
              position: "insideLeft",
            }}
          />
          <Tooltip formatter={v => `${Number(v).toLocaleString()} MW`} />
          <Legend verticalAlign='top' />
          <Line
            type='monotone'
            dataKey='forecast'
            name='Forecast'
            stroke='#2563eb'
            strokeWidth={2.5}
            dot={false}
          />
          {showActual && (
            <Line
              type='monotone'
              dataKey='actual'
              name='Actual'
              stroke='#16a34a'
              strokeWidth={2.5}
              dot={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
