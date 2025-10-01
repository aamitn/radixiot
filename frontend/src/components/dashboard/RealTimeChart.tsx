import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { TemperatureData } from "./RealTimeSection";
import { format } from "date-fns";

interface RealTimeChartProps {
  data: TemperatureData[];
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

export const RealTimeChart = ({ data }: RealTimeChartProps) => {
  if (!data.length) {
    return (
      <div className="h-[400px] flex items-center justify-center text-dashboard-text-muted">
        <p>No chart data available yet...</p>
      </div>
    );
  }

  // Transform data for chart
  const chartData = data.map((measurement, index) => {
    const point: any = {
      timestamp: format(new Date(measurement.timestamp * 1000), 'HH:mm:ss'),
      time: measurement.timestamp,
    };

    // Add temperature data for each channel
    measurement.channels.forEach((channel, channelIndex) => {
      point[channel] = measurement.temperatures[channelIndex];
    });

    return point;
  });

  return (
    <ChartContainer config={chartConfig} className="h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis 
            dataKey="timestamp" 
            tick={{ fontSize: 12 }}
            className="text-dashboard-text-muted"
          />
          <YAxis 
            domain={['dataMin - 2', 'dataMax + 2']}
            tick={{ fontSize: 12 }}
            className="text-dashboard-text-muted"
            label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }}
          />
          <ChartTooltip 
            content={<ChartTooltipContent />}
            labelFormatter={(value) => `Time: ${value}`}
          />
          <Legend />
          
          {/* Temperature lines for each channel */}
          {Object.entries(chartConfig).map(([channel, config]) => (
            <Line
              key={channel}
              type="monotone"
              dataKey={channel}
              stroke={config.color}
              strokeWidth={2}
              dot={false}
              connectNulls
              name={config.label}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};