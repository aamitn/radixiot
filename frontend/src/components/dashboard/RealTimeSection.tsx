import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TemperatureGauges } from "./TemperatureGauges";
import { RealTimeChart } from "./RealTimeChart";
import { RawDataDisplay } from "./RawDataDisplay";
import { ConnectionStatus } from "./ConnectionStatus";
import toast from "react-hot-toast";
import { WS_BASE_URL } from "@/config/api";

export interface TemperatureData {
  timestamp: number;
  device_id: string;
  channels: string[];
  temperatures: number[];
  raw_registers: number[];
}

export interface WebSocketMessage {
  type: "measurement" | "alert";
  device_id?: string;
  payload?: TemperatureData;
  received_at?: string;
  message?: string;
}

export const RealTimeSection = () => {
  const [currentData, setCurrentData] = useState<TemperatureData | null>(null);
  const [chartData, setChartData] = useState<TemperatureData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [showAlerts, setShowAlerts] = useState(false); 


  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/frontend`);

    ws.onopen = () => {
      setIsConnected(true);
      if (showAlerts) toast.success("Connected to real-time data feed");
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (message.type === "measurement" && message.payload) {
          setCurrentData(message.payload);
          setLastUpdate(new Date());

          setChartData((prev) => {
            const newData = [...prev, message.payload!];
            return newData.slice(-50);
          });
        } else if (message.type === "alert") {
          if (showAlerts) {
            toast((message.message || "Data alert received"), {
              icon: '⚠️',
            });
          }
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (showAlerts) toast.error("Disconnected from real-time data feed");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
      if (showAlerts) toast.error("WebSocket connection error");
    };

    return () => {
      ws.close();
    };
  }, [showAlerts]);

  return (
    <div className="space-y-6">

      {/* ✅ Checkbox to toggle Alert Toasts */}
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="show-alerts"
          checked={showAlerts}
          onChange={(e) => setShowAlerts(e.target.checked)}
        />
        <label htmlFor="show-alerts" className="text-sm font-medium">
          Show Alert Toast Messages
        </label>
      </div>

      {/* Connection Status */}
      <ConnectionStatus isConnected={isConnected} lastUpdate={lastUpdate} />

      {/* Temperature Gauges */}
      <Card className="dashboard-card">
        <CardHeader>
          <CardTitle className="text-dashboard-text-primary">Temperature Gauges</CardTitle>
          <CardDescription className="text-dashboard-text-secondary">
            Current temperature readings from all 8 channels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TemperatureGauges data={currentData} />
        </CardContent>
      </Card>

      {/* Real-time Chart */}
      <Card className="dashboard-card">
        <CardHeader>
          <CardTitle className="text-dashboard-text-primary">Real-Time Temperature Chart</CardTitle>
          <CardDescription className="text-dashboard-text-secondary">
            Live temperature trends across all channels (last 50 readings)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RealTimeChart data={chartData} />
        </CardContent>
      </Card>

      {/* Raw Data Display */}
      <Card className="dashboard-card">
        <CardHeader>
          <CardTitle className="text-dashboard-text-primary">Raw Data</CardTitle>
          <CardDescription className="text-dashboard-text-secondary">
            Latest measurement data and register values
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RawDataDisplay data={currentData} />
        </CardContent>
      </Card>
    </div>
  );
};
