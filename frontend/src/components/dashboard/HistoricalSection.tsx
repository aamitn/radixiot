import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DataTable } from "./DataTable";
import { HistoricalChart } from "./HistoricalChart";
import { ExportButtons } from "./ExportButtons";
import { Download, Filter, BarChart3, Trash2 } from "lucide-react";
import { format, startOfDay, endOfDay } from "date-fns";
import toast from "react-hot-toast";
import { DeleteDataModal } from "./DeleteDataModal";
import { API_BASE_URL } from "@/config/api";

export interface MeasurementRecord {
  id: number;
  device_id: string;
  payload: {
    timestamp: number;
    device_id: string;
    channels: string[];
    temperatures: number[];
    raw_registers: number[];
  };
  received_at: string;
}

export const HistoricalSection = () => {
  const [measurements, setMeasurements] = useState<MeasurementRecord[]>([]);
  const [filteredData, setFilteredData] = useState<MeasurementRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [deviceFilter, setDeviceFilter] = useState<string>("all");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [limit, setLimit] = useState<string>("100");
  const [isCustomLimit, setIsCustomLimit] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);


  const fetchMeasurements = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (deviceFilter !== "all") {
        params.append("device_id", deviceFilter);
      }
      params.append("limit", limit);

      // TODO: Replace with your actual backend URL
      const response = await fetch(`${API_BASE_URL}/measurements?${params}`);
      const data = await response.json();
      
      if (data.status === "success") {
        setMeasurements(data.measurements);
        setFilteredData(data.measurements);
        toast.success(`Loaded ${data.measurements.length} measurements`);
      } else {
        toast.error("Failed to fetch measurements");
      }
    } catch (error) {
      console.error("Error fetching measurements:", error);
      toast.error("Error connecting to backend");
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...measurements];

    // Apply device filter
    if (deviceFilter !== "all") {
      filtered = filtered.filter(m => m.device_id === deviceFilter);
    }

    // Apply date filters
    if (startDate || endDate) {
      filtered = filtered.filter(measurement => {
        const measurementDate = new Date(measurement.received_at);
        let inRange = true;

        if (startDate) {
          const start = startOfDay(new Date(startDate));
          inRange = inRange && measurementDate >= start;
        }

        if (endDate) {
          const end = endOfDay(new Date(endDate));
          inRange = inRange && measurementDate <= end;
        }

        return inRange;
      });
    }

    setFilteredData(filtered);
    toast.success(`Filtered to ${filtered.length} measurements`);
  };

  const clearFilters = () => {
    setDeviceFilter("all");
    setStartDate("");
    setEndDate("");
    setFilteredData(measurements);
    toast.success("Filters cleared");
  };

  const uniqueDevices = Array.from(new Set(measurements.map(m => m.device_id)));

  const handleLimitChange = (value: string) => {
    if (value === "custom") {
      setIsCustomLimit(true);
      return;
    }
    setIsCustomLimit(false);
    setLimit(value);
  };

  // Debounced fetch implementation
  const debouncedFetch = useCallback(
    (() => {
      let timeout: NodeJS.Timeout;
      return (value: string) => {
        if (timeout) clearTimeout(timeout);
        timeout = setTimeout(() => {
          setLimit(value);
          fetchMeasurements();
        }, 800); // 800ms delay
      };
    })(),
    [/* dependencies */]
  );

  const handleCustomLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const numValue = parseInt(value);
    if (!isNaN(numValue) && numValue > 0) {
      setLimit(value); // Update UI immediately
      debouncedFetch(value); // Trigger API call after delay
    }
  };

  useEffect(() => {
    fetchMeasurements();
  }, [limit, deviceFilter]);

  return (
    <div className="space-y-6">
      {/* Filters Section */}
      <Card className="dashboard-card">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-dashboard-text-primary flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Data Filters
            </CardTitle>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDeleteModal(true)}
              className="flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Delete Data
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="space-y-2">
              <Label>Device ID</Label>
              <Select value={deviceFilter} onValueChange={setDeviceFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Devices</SelectItem>
                  {uniqueDevices.map(device => (
                    <SelectItem key={device} value={device}>{device}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Limit</Label>
              {isCustomLimit ? (
                <div className="flex gap-2">
                  <Input
                    type="number"
                    min="1"
                    max="1000000"
                    value={limit}
                    onChange={handleCustomLimitChange}
                    className="w-[120px]"
                    placeholder="Enter limit..."
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setIsCustomLimit(false)}
                    disabled={loading}
                  >
                    ↩
                  </Button>
                </div>
              ) : (
                <Select value={limit} onValueChange={handleLimitChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="25">25</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="500">500</SelectItem>
                     <SelectItem value="10000">10000</SelectItem>
                    <SelectItem value="custom">Custom limit...</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="flex items-end gap-2">
              <Button onClick={fetchMeasurements} disabled={loading} className="flex-1">
                {loading ? "Loading..." : "Refresh"}
              </Button>
              <Button onClick={applyFilters} variant="secondary">
                Apply Filters
              </Button>
              <Button onClick={clearFilters} variant="outline">
                Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Delete Modal */}
      <DeleteDataModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onSuccess={fetchMeasurements}
      />

      {/* Chart Section */}
      <Card className="dashboard-card">
        <CardHeader>
          <CardTitle className="text-dashboard-text-primary flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Historical Temperature Chart
          </CardTitle>
          <CardDescription className="text-dashboard-text-secondary">
            Temperature trends over time ({filteredData.length} data points)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <HistoricalChart data={filteredData} />
        </CardContent>
      </Card>

      {/* Export Section */}
      <Card className="dashboard-card">
        <CardHeader>
          <CardTitle className="text-dashboard-text-primary flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export Data
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ExportButtons data={filteredData} />
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card className="dashboard-card">
        <CardHeader>
          <CardTitle className="text-dashboard-text-primary">Measurement Data</CardTitle>
          <CardDescription className="text-dashboard-text-secondary">
            Detailed view of measurement records ({filteredData.length} records)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable data={filteredData} />
        </CardContent>
      </Card>
    </div>
  );
};