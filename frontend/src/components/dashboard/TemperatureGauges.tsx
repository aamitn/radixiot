import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { TemperatureData } from "./RealTimeSection";
import { Thermometer } from "lucide-react";

interface TemperatureGaugesProps {
  data: TemperatureData | null;
}

export const TemperatureGauges = ({ data }: TemperatureGaugesProps) => {
  if (!data) {
    return (
      <div className="text-center py-12 text-dashboard-text-muted">
        <Thermometer className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>Waiting for temperature data...</p>
      </div>
    );
  }

  const getTemperatureColor = (temp: number) => {
    if (temp <= 20) return "text-temp-cold";
    if (temp <= 30) return "text-temp-normal";
    if (temp <= 40) return "text-temp-warm";
    return "text-temp-hot";
  };

  const getTemperatureLevel = (temp: number) => {
    // Normalize temperature to 0-100 scale (assuming 0-60°C range)
    return Math.min(100, Math.max(0, (temp / 60) * 100));
  };

  const getProgressColor = (temp: number) => {
    if (temp <= 20) return "bg-temp-cold";
    if (temp <= 30) return "bg-temp-normal";
    if (temp <= 40) return "bg-temp-warm";
    return "bg-temp-hot";
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {data.channels.map((channel, index) => {
        const temperature = data.temperatures[index];
        const raw = data.raw_registers[index];
        
        return (
          <div
            key={channel}
            className="dashboard-card p-4 space-y-3 animate-data-update"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-dashboard-text-secondary">
                {channel}
              </span>
              <Thermometer className={cn("h-4 w-4", getTemperatureColor(temperature))} />
            </div>
            
            <div className="space-y-2">
              <div className={cn("text-2xl font-bold", getTemperatureColor(temperature))}>
                {temperature.toFixed(1)}°C
              </div>
              
              <Progress 
                value={getTemperatureLevel(temperature)} 
                className="h-2"
              />
              
              <div className="text-xs text-dashboard-text-muted">
                Raw: {raw}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};