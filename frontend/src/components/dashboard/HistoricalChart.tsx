import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend, Brush } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { MeasurementRecord } from "./HistoricalSection";
import { format } from "date-fns";

interface HistoricalChartProps {
  data: MeasurementRecord[];
}

const chartConfig = {
  T1: { label: "T1", color: "hsl(var(--chart-1))" },
  T2: { label: "T2", color: "hsl(var(--chart-2))" },
  T3: { label: "T3", color: "hsl(var(--chart-3))" },
  T4: { label: "T4", color: "hsl(var(--chart-4))" },
  T5: { label: "T5", color: "hsl(var(--chart-5))" },
  T6: { label: "T6", color: "hsl(var(--chart-6))" },
  T7: { label: "T7", color: "hsl(var(--chart-7))" },
  T8: { label: "T8", color: "hsl(var(--chart-8))" },
};

export const HistoricalChart = ({ data }: HistoricalChartProps) => {
  if (!data.length) {
    return (
      <div className="h-[500px] flex items-center justify-center text-dashboard-text-muted">
        <p>No data available for chart visualization</p>
      </div>
    );
  }

  // Transform data for chart
  const chartData = data
    .map((record) => {
      const point: any = {
        timestamp: format(new Date(record.received_at), 'MM/dd HH:mm'),
        fullTimestamp: record.received_at,
        time: new Date(record.received_at).getTime(),
      };

      // Add temperature data for each channel
      record.payload.channels.forEach((channel, channelIndex) => {
        point[channel] = record.payload.temperatures[channelIndex];
      });

      return point;
    })
    .sort((a, b) => a.time - b.time); // Sort by time

  // Calculate temperature ranges for better Y-axis scaling
  const allTemps = data.flatMap(record => record.payload.temperatures);
  const minTemp = Math.min(...allTemps);
  const maxTemp = Math.max(...allTemps);
  const tempRange = maxTemp - minTemp;
  const yAxisMin = Math.max(0, minTemp - tempRange * 0.1);
  const yAxisMax = maxTemp + tempRange * 0.1;

  return (
    <div className="space-y-4">
      <ChartContainer config={chartConfig} className="h-[500px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis 
              dataKey="timestamp" 
              tick={{ fontSize: 11 }}
              className="text-dashboard-text-muted"
              angle={-45}
              textAnchor="end"
              height={80}
              interval="preserveStartEnd"
            />
            <YAxis 
              domain={[yAxisMin, yAxisMax]}
              tick={{ fontSize: 12 }}
              className="text-dashboard-text-muted"
              label={{ 
                value: 'Temperature (°C)', 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle' }
              }}
            />
            <ChartTooltip 
              content={<ChartTooltipContent />}
              labelFormatter={(value, payload) => {
                const record = payload?.[0]?.payload;
                if (record?.fullTimestamp) {
                  return `Time: ${format(new Date(record.fullTimestamp), 'PPpp')}`;
                }
                return `Time: ${value}`;
              }}
            />
            <Legend />
            
            {/* Temperature lines for each channel */}
            {Object.entries(chartConfig).map(([channel, config]) => (
              <Line
                key={channel}
                type="monotone"
                dataKey={channel}
                stroke={config.color}
                strokeWidth={1.5}
                dot={{ r: 2, fill: config.color }}
                connectNulls
                name={config.label}
              />
            ))}

            {/* Brush for zooming */}
            <Brush 
              dataKey="timestamp" 
              height={30}
              stroke="hsl(var(--primary))"
              fill="hsl(var(--primary) / 0.1)"
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartContainer>

      {/* Chart Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-dashboard-border">
        <div className="text-center">
          <div className="text-2xl font-bold text-dashboard-text-primary">
            {data.length}
          </div>
          <div className="text-sm text-dashboard-text-secondary">Data Points</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-dashboard-text-primary">
            {minTemp.toFixed(1)}°C
          </div>
          <div className="text-sm text-dashboard-text-secondary">Min Temp</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-dashboard-text-primary">
            {maxTemp.toFixed(1)}°C
          </div>
          <div className="text-sm text-dashboard-text-secondary">Max Temp</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-dashboard-text-primary">
            {(allTemps.reduce((a, b) => a + b, 0) / allTemps.length).toFixed(1)}°C
          </div>
          <div className="text-sm text-dashboard-text-secondary">Avg Temp</div>
        </div>
      </div>
    </div>
  );
};