// TripStatusWidget.jsx
import React, { useEffect, useState } from "react";

const TripStatusWidget = ({ wsBaseUrl }) => {
  const [status, setStatus] = useState("HEALTHY");
  const [timestamp, setTimestamp] = useState(new Date().toISOString());
  const [connectionStatus, setConnectionStatus] = useState("connecting");

  useEffect(() => {
    const wsUrl = wsBaseUrl.replace(/^http/, "ws") + "/ws/frontend";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnectionStatus("connected");
      console.log("WebSocket connected:", wsUrl);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "trip_status") {
          setStatus(data.status);
          setTimestamp(data.timestamp);
        }
      } catch (err) {
        console.error("Invalid WebSocket message:", err);
      }
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
      console.warn("WebSocket closed, attempting reconnect in 5s...");
      setTimeout(() => window.location.reload(), 5000);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => ws.close();
  }, [wsBaseUrl]);

  const isTripped = status === "TRIP";
  const statusColor = isTripped ? "#ef4444" : "#10b981";
  const bgColor = isTripped ? "#fef2f2" : "#f0fdf4";

return (
    <div style={{
      backgroundColor: bgColor,
      border: `1px solid ${statusColor}30`,
      borderRadius: "8px",
      padding: "12px",
      width: "160px",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      transition: "all 0.3s ease"
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "8px"
      }}>
        <h3 style={{
          margin: 0,
          fontSize: "10px",
          fontWeight: 600,
          color: "#6b7280",
          textTransform: "uppercase",
          letterSpacing: "0.3px"
        }}>
          Trip Status
        </h3>
        <div style={{
          width: "5px",
          height: "5px",
          borderRadius: "50%",
          backgroundColor: connectionStatus === "connected" ? "#10b981" : "#9ca3af"
        }} />
      </div>
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        marginBottom: "6px"
      }}>
        <div style={{
          width: "8px",
          height: "8px",
          borderRadius: "2px",
          backgroundColor: statusColor
        }} />
        <span style={{
          fontSize: "20px",
          fontWeight: 700,
          color: statusColor,
          letterSpacing: "-0.3px"
        }}>
          {status}
        </span>
      </div>
      <div style={{
        fontSize: "9px",
        color: "#9ca3af",
        fontWeight: 500
      }}>
        {new Date(timestamp).toLocaleString("en-US", {
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit"
        })}
      </div>
    </div>
  );
};

export default TripStatusWidget;