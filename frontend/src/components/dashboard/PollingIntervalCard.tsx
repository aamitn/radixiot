import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";

interface PollingIntervalCardProps {
  pollingInterval: number;
  setPollingInterval: (val: number) => void;
  handleSaveInterval: () => void;
  isSavingInterval: boolean;
}

export const PollingIntervalCard = ({
  pollingInterval,
  setPollingInterval,
  handleSaveInterval,
  isSavingInterval,
}: PollingIntervalCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <Card className="bg-slate-800 dark:bg-gray-900 border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader 
        className="flex flex-row justify-between items-center cursor-pointer py-3 px-4" 
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="space-y-0.5">
          <CardTitle className="text-sm font-medium text-gray-300 dark:text-gray-100">
            Polling Interval
          </CardTitle>
          {!isExpanded && (
            <CardDescription className="text-xs text-gray-500 dark:text-gray-500">
              {pollingInterval}ms
            </CardDescription>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-gray-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-400" />
        )}
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="px-4 pb-4 pt-0">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
            Data refresh interval in milliseconds
          </p>
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={pollingInterval}
              onChange={(e) => setPollingInterval(Number(e.target.value))}
              className="border border-gray-200 dark:border-gray-700 px-2.5 py-1.5 rounded text-sm w-28 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              min={200}
            />
            <button
              className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              onClick={handleSaveInterval}
              disabled={isSavingInterval}
            >
              {isSavingInterval ? "Saving..." : "Save"}
            </button>
          </div>
        </CardContent>
      )}
    </Card>
  );
};