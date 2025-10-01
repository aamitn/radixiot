import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff, Clock } from "lucide-react";
import { format } from "date-fns";

interface ConnectionStatusProps {
  isConnected: boolean;
  lastUpdate: Date | null;
}

export const ConnectionStatus = ({ isConnected, lastUpdate }: ConnectionStatusProps) => {
  return (
    <Card className="dashboard-card">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Wifi className="h-5 w-5 text-success animate-pulse" />
              ) : (
                <WifiOff className="h-5 w-5 text-destructive" />
              )}
              <Badge 
                variant={isConnected ? "default" : "destructive"}
                className={isConnected ? "bg-success hover:bg-success/80" : ""}
              >
                {isConnected ? "Connected" : "Disconnected"}
              </Badge>
            </div>

            {lastUpdate && (
              <div className="flex items-center gap-2 text-dashboard-text-secondary">
                <Clock className="h-4 w-4" />
                <span className="text-sm">
                  Last update: {format(lastUpdate, 'HH:mm:ss')}
                </span>
              </div>
            )}
          </div>

          <div className="text-sm text-dashboard-text-muted">
            WebSocket: ws://127.0.0.1:8000/ws/frontend
          </div>
        </div>
      </CardContent>
    </Card>
  );
};