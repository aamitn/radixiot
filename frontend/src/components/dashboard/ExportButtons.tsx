import { Button } from "@/components/ui/button";
import { Download, FileSpreadsheet, FileText } from "lucide-react";
import { MeasurementRecord } from "./HistoricalSection";
import * as XLSX from "xlsx";
import { format } from "date-fns";
import toast from "react-hot-toast";

interface ExportButtonsProps {
  data: MeasurementRecord[];
}

export const ExportButtons = ({ data }: ExportButtonsProps) => {
  const exportToCSV = () => {
    if (!data.length) {
      toast.error("No data to export");
      return;
    }

    // Prepare CSV headers
    const headers = [
      "ID",
      "Device ID", 
      "Timestamp",
      "Received At",
      ...data[0].payload.channels.map(channel => `${channel} (°C)`),
      ...data[0].payload.channels.map(channel => `${channel} Raw`),
    ];

    // Prepare CSV rows
    const rows = data.map(record => {
      const row = [
        record.id,
        record.device_id,
        format(new Date(record.payload.timestamp * 1000), 'yyyy-MM-dd HH:mm:ss'),
        format(new Date(record.received_at), 'yyyy-MM-dd HH:mm:ss'),
        ...record.payload.temperatures,
        ...record.payload.raw_registers,
      ];
      return row;
    });

    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `temperature_measurements_${format(new Date(), 'yyyy-MM-dd_HH-mm-ss')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.success(`Exported ${data.length} measurements to CSV`);
  };

  const exportToExcel = () => {
    if (!data.length) {
      toast.error("No data to export");
      return;
    }

    // Prepare Excel data
    const excelData = data.map(record => {
      const row: any = {
        ID: record.id,
        'Device ID': record.device_id,
        'Timestamp': format(new Date(record.payload.timestamp * 1000), 'yyyy-MM-dd HH:mm:ss'),
        'Received At': format(new Date(record.received_at), 'yyyy-MM-dd HH:mm:ss'),
      };

      // Add temperature columns
      record.payload.channels.forEach((channel, index) => {
        row[`${channel} (°C)`] = record.payload.temperatures[index];
        row[`${channel} Raw`] = record.payload.raw_registers[index];
      });

      return row;
    });

    // Create workbook
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(excelData);

    // Auto-size columns
    const colWidths = Object.keys(excelData[0] || {}).map(key => ({
      wch: Math.max(key.length, 12)
    }));
    ws['!cols'] = colWidths;

    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Temperature Data');

    // Save file
    const fileName = `temperature_measurements_${format(new Date(), 'yyyy-MM-dd_HH-mm-ss')}.xlsx`;
    XLSX.writeFile(wb, fileName);

    toast.success(`Exported ${data.length} measurements to Excel`);
  };

  const exportToJSON = () => {
    if (!data.length) {
      toast.error("No data to export");
      return;
    }

    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `temperature_measurements_${format(new Date(), 'yyyy-MM-dd_HH-mm-ss')}.json`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.success(`Exported ${data.length} measurements to JSON`);
  };

  return (
    <div className="flex flex-wrap gap-3">
      <Button onClick={exportToCSV} variant="outline" className="flex items-center gap-2">
        <FileText className="h-4 w-4" />
        Export CSV
      </Button>

      <Button onClick={exportToExcel} variant="outline" className="flex items-center gap-2">
        <FileSpreadsheet className="h-4 w-4" />
        Export Excel
      </Button>

      <Button onClick={exportToJSON} variant="outline" className="flex items-center gap-2">
        <Download className="h-4 w-4" />
        Export JSON
      </Button>

      <div className="flex items-center text-sm text-dashboard-text-secondary ml-4">
        Ready to export {data.length} measurement records
      </div>
    </div>
  );
};