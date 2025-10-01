import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import toast from "react-hot-toast";

interface DeleteDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function DeleteDataModal({ isOpen, onClose, onSuccess }: DeleteDataModalProps) {
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  const handleDelete = async (type: "count" | "daterange") => {
    setLoading(true);
    try {
      let body = {};
      if (type === "count") {
        body = { count: parseInt(count) };
      } else {
        body = {
          start_datetime: startDate.replace('T', ' '), // Direct string manipulation
          end_datetime: endDate.replace('T', ' '), // Direct string manipulation
        };
      }

      const response = await fetch("http://127.0.0.1:8000/measurements", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        toast.success("Data deleted successfully");
        onSuccess();
        onClose();
      } else {
        throw new Error("Failed to delete data");
      }
    } catch (error) {
      toast.error("Failed to delete data");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Historical Data</DialogTitle>
          <DialogDescription>
            Choose how you want to delete historical data. This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="count">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="count">By Count</TabsTrigger>
            <TabsTrigger value="daterange">By Date Range</TabsTrigger>
          </TabsList>

          <TabsContent value="count" className="space-y-4">
            <div className="space-y-2">
              <Label>Number of records to delete</Label>
              <Input
                type="number"
                min="1"
                value={count}
                onChange={(e) => setCount(e.target.value)}
                placeholder="Enter number of records"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={onClose}>Cancel</Button>
              <Button 
                variant="destructive" 
                onClick={() => handleDelete("count")}
                disabled={loading || !count}
              >
                Delete Records
              </Button>
            </DialogFooter>
          </TabsContent>

          <TabsContent value="daterange" className="space-y-4">
            <div className="space-y-2">
              <Label>Start Date & Time</Label>
              <Input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                max={endDate || undefined}
                step="1"
              />
            </div>
            <div className="space-y-2">
              <Label>End Date & Time</Label>
              <Input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                min={startDate || undefined}
                step="1"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={onClose}>Cancel</Button>
              <Button 
                variant="destructive" 
                onClick={() => handleDelete("daterange")}
                disabled={loading || !startDate || !endDate}
              >
                Delete Range
              </Button>
            </DialogFooter>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

