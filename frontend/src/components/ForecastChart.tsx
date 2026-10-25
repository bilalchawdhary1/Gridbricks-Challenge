import type {CSSProperties} from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {COLORS, niceAxis, shortDate, utcStamp, utcTime} from "../format";

export type ChartPoint = {time: string; forecast: number; actual?: number};

type Props = {data: ChartPoint[]; showActual?: boolean};

export default function ForecastChart({data, showActual = false}: Props) {
  if (data.length === 0) {
    return <p className='state'>No data available for this selection.</p>;
  }

  const maxValue = Math.max(...data.map(d => Math.max(d.forecast, d.actual ?? 0)));
  const axis = niceAxis(maxValue);
  const multiDay = data[0].time.slice(0, 10) !== data[data.length - 1].time.slice(0, 10);

  return (
    <div>
      <div className='legend' aria-hidden='true'>
        <span style={{"--swatch": COLORS.forecast} as CSSProperties}>Forecast</span>
        {showActual && (
          <span style={{"--swatch": COLORS.actual} as CSSProperties}>Actual</span>
        )}
      </div>
      <div className='chart'>
        <ResponsiveContainer width='100%' height='100%'>
          <LineChart data={data} margin={{top: 8, right: 16, left: 4, bottom: 8}}>
            <CartesianGrid stroke={COLORS.grid} vertical={false} />
            <XAxis
              dataKey='time'
              tick={{fontSize: 12, fill: COLORS.axis}}
              tickLine={false}
              axisLine={{stroke: COLORS.grid}}
              minTickGap={multiDay ? 56 : 36}
              tickFormatter={(t: string) => (multiDay ? shortDate(t) : utcTime(t))}
              label={{
                value: multiDay ? "Delivery date" : "Delivery hour (UTC)",
                position: "insideBottom",
                offset: -4,
                fill: COLORS.axis,
                fontSize: 12,
              }}
              height={48}
            />
            <YAxis
              tick={{fontSize: 12, fill: COLORS.axis}}
              tickLine={false}
              axisLine={false}
              width={64}
              domain={[0, axis.top]}
              ticks={axis.ticks}
              tickFormatter={(v: number) => v.toLocaleString("en-GB")}
              label={{
                value: "Wind generation (MW)",
                angle: -90,
                position: "insideLeft",
                offset: 4,
                fill: COLORS.axis,
                fontSize: 12,
                style: {textAnchor: "middle"},
              }}
            />
            <Tooltip
              labelFormatter={(t) => utcStamp(String(t))}
              formatter={(v, name) => [`${Math.round(Number(v)).toLocaleString("en-GB")} MW`, name]}
            />
            <Line
              type='monotone'
              dataKey='forecast'
              name='Forecast'
              stroke={COLORS.forecast}
              strokeWidth={2.5}
              dot={false}
              isAnimationActive={false}
            />
            {showActual && (
              <Line
                type='monotone'
                dataKey='actual'
                name='Actual'
                stroke={COLORS.actual}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
