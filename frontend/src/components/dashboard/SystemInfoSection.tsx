import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, Cpu, HardDrive, Database } from "lucide-react";
import { toast } from "react-hot-toast";

interface SystemInfo {
  status: string;
  system: {
    os: string;
    os_version: string;
    machine: string;
    processor: string;
    python_version: string;
  };
  cpu: {
    cores: number;
    usage_percent: number;
  };
  memory: {
    total_gb: number;
    used_gb: number;
    available_gb: number;
    usage_percent: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
  };
}

interface MeasurementCount {
  status: string;
  total_entries: number;
}

const SystemInfoSection = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [measurementCount, setMeasurementCount] = useState<MeasurementCount | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSystemInfo = async () => {
    setIsLoading(true);
    try {
      const [sysResponse, countResponse] = await Promise.all([
        fetch("http://localhost:8000/system-info"),
        fetch("http://127.0.0.1:8000/measurements/count"),
      ]);

      if (sysResponse.ok) {
        const sysData = await sysResponse.json();
        setSystemInfo(sysData);
      } else {
        toast.error("Failed to fetch system info");
      }

      if (countResponse.ok) {
        const countData = await countResponse.json();
        setMeasurementCount(countData);
      } else {
        toast.error("Failed to fetch measurement count");
      }
    } catch (error) {
      toast.error("Error fetching system information");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemInfo();
    const interval = setInterval(fetchSystemInfo, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">System Information</h2>
        <Button onClick={fetchSystemInfo} disabled={isLoading} variant="outline" size="sm">
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {systemInfo && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                <p><span className="font-medium">OS:</span> {systemInfo.system.os} {systemInfo.system.os_version}</p>
                <p><span className="font-medium">Machine:</span> {systemInfo.system.machine}</p>
                <p><span className="font-medium">Python:</span> {systemInfo.system.python_version}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemInfo.cpu.usage_percent}%</div>
              <p className="text-xs text-muted-foreground">
                {systemInfo.cpu.cores} cores
              </p>
              <div className="mt-2 h-2 w-full bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all"
                  style={{ width: `${systemInfo.cpu.usage_percent}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory</CardTitle>
              <HardDrive className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemInfo.memory.usage_percent}%</div>
              <p className="text-xs text-muted-foreground">
                {systemInfo.memory.used_gb.toFixed(2)} / {systemInfo.memory.total_gb.toFixed(2)} GB
              </p>
              <div className="mt-2 h-2 w-full bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all"
                  style={{ width: `${systemInfo.memory.usage_percent}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disk Space</CardTitle>
              <HardDrive className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemInfo.disk.used_gb.toFixed(2)} GB</div>
              <p className="text-xs text-muted-foreground">
                {systemInfo.disk.free_gb.toFixed(2)} GB free of {systemInfo.disk.total_gb.toFixed(2)} GB
              </p>
              <div className="mt-2 h-2 w-full bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all"
                  style={{ width: `${(systemInfo.disk.used_gb / systemInfo.disk.total_gb) * 100}%` }}
                />
              </div>
            </CardContent>
          </Card>

          {measurementCount && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Database Entries</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{measurementCount.total_entries.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">Total measurements</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Processor</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-xs">{systemInfo.system.processor}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default SystemInfoSection;
