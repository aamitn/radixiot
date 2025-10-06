import React, { useEffect, useState, useRef } from "react";
import { AlertCircle, CheckCircle2, Loader2, WifiOff } from "lucide-react";
import { motion } from "motion/react";
import { WS_BASE_URL } from "@/config/api";

const MinimalGatewayHealthStatus = () => {
  const [health, setHealth] = useState({
    status: "UNKNOWN",
  });
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // --- WebSocket Logic (Optimized for brevity) ---
  useEffect(() => {
    const connectWS = () => {
      // NOTE: Using localhost:8000 as per original code
      const ws = new WebSocket(`${WS_BASE_URL}/ws/frontend`);
      wsRef.current = ws;

      ws.onopen = () => setWsConnected(true);

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "gateway_health") {
            setHealth({ status: msg.status });
          }
        } catch (err) {
          console.error("WS parse error:", err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        wsRef.current = null;
        setTimeout(connectWS, 3000); // Reconnect logic
      };

      ws.onerror = (err) => ws.close();
    };

    connectWS();
    return () => wsRef.current?.close();
  }, []);
  // --- End WebSocket Logic ---

  // Determine visual styles and icon based on health status
  const { icon: StatusIcon, colorClass } = (() => {
    switch (health.status) {
      case "UP":
        return {
          icon: CheckCircle2,
          colorClass: "text-green-500",
        };
      case "DOWN":
        return {
          icon: AlertCircle,
          colorClass: "text-red-500",
        };
      default:
        // Use a "loader" for unknown status if WS is connected, otherwise WifiOff
        const Icon = wsConnected ? Loader2 : WifiOff;
        const color = wsConnected ? "text-yellow-500" : "text-gray-400";
        return {
          icon: Icon,
          colorClass: color,
        };
    }
  })();

  // Simplified transition for the icon swap
  const transition = { type: "tween", duration: 0.2 };

  return (
    // Minimal display: Just the icon, status, and WS indicator in a single line
    <div className="flex items-center gap-3 p-2 bg-white rounded-lg border shadow-sm max-w-xs mx-auto">
      {/* Main Status Indicator (Animated) */}
      <motion.div
        key={health.status} // Key ensures animation on status change
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={transition}
      >
        <StatusIcon
          className={`w-6 h-6 ${colorClass} ${
            health.status === "UNKNOWN" && wsConnected ? "animate-spin" : ""
          }`}
        />
      </motion.div>

      {/* Status Text */}
      <span className={`text-md font-semibold text-gray-700`}>
        Gateway:{" "}
        <strong className={`${colorClass}`}>
          {health.status === "UP" ? "Operational" : health.status.toLowerCase()}
        </strong>
      </span>

      {/* Minimal WS Connection Indicator */}
      <div
        title={wsConnected ? "WebSocket Connected" : "WebSocket Reconnecting"}
        className={`ml-auto w-2 h-2 rounded-full ${
          wsConnected ? "bg-green-500" : "bg-yellow-500 animate-pulse"
        }`}
      />
    </div>
  );
};

export default MinimalGatewayHealthStatus;