import { useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ChevronLeft, ChevronRight, Eye, EyeOff } from "lucide-react";
import { format } from "date-fns";
import { MeasurementRecord } from "./HistoricalSection";

interface DataTableProps {
  data: MeasurementRecord[];
}

export const DataTable = ({ data }: DataTableProps) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const itemsPerPage = 10;

  const totalPages = Math.ceil(data.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = data.slice(startIndex, endIndex);

  const toggleRowExpansion = (id: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  if (!data.length) {
    return (
      <div className="text-center py-8 text-dashboard-text-muted">
        <p>No measurement data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-dashboard-border">
              <TableHead className="text-dashboard-text-secondary">ID</TableHead>
              <TableHead className="text-dashboard-text-secondary">Device</TableHead>
              <TableHead className="text-dashboard-text-secondary">Timestamp</TableHead>
              <TableHead className="text-dashboard-text-secondary">Received At</TableHead>
              <TableHead className="text-dashboard-text-secondary">Channels</TableHead>
              <TableHead className="text-dashboard-text-secondary">Avg Temp</TableHead>
              <TableHead className="text-dashboard-text-secondary">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {currentData.map((measurement) => {
              const isExpanded = expandedRows.has(measurement.id);
              const avgTemp = measurement.payload.temperatures.reduce((a, b) => a + b, 0) / measurement.payload.temperatures.length;
              
              return (
                <>
                  <TableRow key={measurement.id} className="border-dashboard-border">
                    <TableCell className="font-mono text-dashboard-text-primary">
                      {measurement.id}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono">
                        {measurement.device_id}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm text-dashboard-text-secondary">
                      {format(new Date(measurement.payload.timestamp * 1000), 'MM/dd HH:mm:ss')}
                    </TableCell>
                    <TableCell className="font-mono text-sm text-dashboard-text-secondary">
                      {format(new Date(measurement.received_at), 'MM/dd HH:mm:ss')}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {measurement.payload.channels.length} channels
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-dashboard-text-primary">
                      {avgTemp.toFixed(1)}°C
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleRowExpansion(measurement.id)}
                      >
                        {isExpanded ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </TableCell>
                  </TableRow>
                  
                  {isExpanded && (
                    <TableRow className="border-dashboard-border">
                      <TableCell colSpan={7} className="p-0">
                        <Card className="m-2 bg-dashboard-surface border-dashboard-border">
                          <div className="p-4 space-y-4">
                            <h4 className="text-sm font-semibold text-dashboard-text-primary">
                              Detailed Measurements
                            </h4>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                              {measurement.payload.channels.map((channel, index) => (
                                <div
                                  key={channel}
                                  className="flex items-center justify-between p-2 bg-background/50 rounded"
                                >
                                  <span className="text-sm text-dashboard-text-secondary font-mono">
                                    {channel}
                                  </span>
                                  <div className="text-right">
                                    <div className="font-mono text-sm font-bold text-dashboard-text-primary">
                                      {measurement.payload.temperatures[index].toFixed(1)}°C
                                    </div>
                                    <div className="text-xs text-dashboard-text-muted">
                                      Raw: {measurement.payload.raw_registers[index]}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>

                            <div className="pt-2 border-t border-dashboard-border">
                              <pre className="text-xs text-dashboard-text-muted font-mono bg-background/30 p-2 rounded overflow-auto">
                                {JSON.stringify(measurement.payload, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </Card>
                      </TableCell>
                    </TableRow>
                  )}
                </>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-dashboard-text-secondary">
          Showing {startIndex + 1}-{Math.min(endIndex, data.length)} of {data.length} measurements
        </p>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          
          <span className="text-sm text-dashboard-text-secondary">
            Page {currentPage} of {totalPages}
          </span>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};