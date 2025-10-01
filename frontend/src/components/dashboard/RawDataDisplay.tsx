import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TemperatureData } from "./RealTimeSection";
import { format } from "date-fns";
import { Clock, Cpu, Thermometer, Hash } from "lucide-react";

interface RawDataDisplayProps {
  data: TemperatureData | null;
}

export const RawDataDisplay = ({ data }: RawDataDisplayProps) => {
  if (!data) {
    return (
      <div className="text-center py-8 text-dashboard-text-muted">
        <p>No raw data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Device Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-dashboard-surface border-dashboard-border">
          <div className="flex items-center gap-3">
            <Cpu className="h-5 w-5 text-primary" />
            <div>
              <p className="text-sm text-dashboard-text-secondary">Device ID</p>
              <p className="font-mono font-medium text-dashboard-text-primary">
                {data.device_id}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-dashboard-surface border-dashboard-border">
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-success" />
            <div>
              <p className="text-sm text-dashboard-text-secondary">Timestamp</p>
              <p className="font-mono text-sm text-dashboard-text-primary">
                {format(new Date(data.timestamp * 1000), 'PPpp')}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-dashboard-surface border-dashboard-border">
          <div className="flex items-center gap-3">
            <Thermometer className="h-5 w-5 text-warning" />
            <div>
              <p className="text-sm text-dashboard-text-secondary">Channels</p>
              <p className="font-medium text-dashboard-text-primary">
                {data.channels.length} Active
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Temperature Data Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-4 bg-dashboard-surface border-dashboard-border">
          <h4 className="text-lg font-semibold text-dashboard-text-primary mb-4 flex items-center gap-2">
            <Thermometer className="h-5 w-5" />
            Temperature Readings
          </h4>
          <div className="space-y-3">
            {data.channels.map((channel, index) => (
              <div key={channel} className="flex items-center justify-between p-3 bg-background/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Badge variant="secondary" className="font-mono">
                    {channel}
                  </Badge>
                  <span className="text-dashboard-text-secondary">Channel {index + 1}</span>
                </div>
                <span className="font-mono text-lg font-bold text-dashboard-text-primary">
                  {data.temperatures[index].toFixed(1)}°C
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4 bg-dashboard-surface border-dashboard-border">
          <h4 className="text-lg font-semibold text-dashboard-text-primary mb-4 flex items-center gap-2">
            <Hash className="h-5 w-5" />
            Raw Register Values
          </h4>
          <div className="space-y-3">
            {data.channels.map((channel, index) => (
              <div key={channel} className="flex items-center justify-between p-3 bg-background/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="font-mono">
                    {channel}
                  </Badge>
                  <span className="text-dashboard-text-secondary">Register {index + 1}</span>
                </div>
                <span className="font-mono text-lg font-bold text-dashboard-text-primary">
                  {data.raw_registers[index]}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* JSON Raw Data */}
      <Card className="p-4 bg-dashboard-surface border-dashboard-border">
        <h4 className="text-lg font-semibold text-dashboard-text-primary mb-4">
          Complete JSON Payload
        </h4>
        <pre className="bg-background/30 p-4 rounded-lg text-sm font-mono text-dashboard-text-secondary overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      </Card>
    </div>
  );
};