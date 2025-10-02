import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TemperatureGauges } from "./TemperatureGauges";
import { RealTimeChart } from "./RealTimeChart";
import { RawDataDisplay } from "./RawDataDisplay";
import {PollingIntervalCard} from "./PollingIntervalCard";
import { ConnectionStatus } from "./ConnectionStatus";
import toast from "react-hot-toast";
import { WS_BASE_URL,API_BASE_URL } from "@/config/api";

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
  const [pollingInterval, setPollingInterval] = useState<number>(5000);
  const [isSavingInterval, setIsSavingInterval] = useState(false);

  // Fetch current polling interval from backend
  useEffect(() => {
    fetch(`${API_BASE_URL}/polling`)
      .then((res) => res.json())
      .then((data) => {
        if (data.polling_interval_ms) setPollingInterval(data.polling_interval_ms);
      })
      .catch((err) => console.error("Failed to fetch polling interval:", err));
  }, []);

  
  // Save polling interval to backend
  const handleSaveInterval = async () => {
    if (pollingInterval < 200) {
      toast.error("Interval must be >= 200 ms");
      return;
    }
    setIsSavingInterval(true);
    try {
      const res = await fetch(`${API_BASE_URL}/polling`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval_ms: pollingInterval }),
      });
      const data = await res.json();
      if (data.status === "success") toast.success("Polling interval updated");
      else toast.error("Failed to update polling interval");
    } catch (err) {
      console.error(err);
      toast.error("Error updating polling interval");
    } finally {
      setIsSavingInterval(false);
    }
  };


  // ---------------- WebSocket for real-time data ----------------

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

      {/* Polling Interval Control */}
      <PollingIntervalCard
        pollingInterval={pollingInterval}
        setPollingInterval={setPollingInterval}
        handleSaveInterval={handleSaveInterval}
        isSavingInterval={isSavingInterval}
      />


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
