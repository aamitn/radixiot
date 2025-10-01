import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Loader2, FileArchive, AlertCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";

export const FtpSection = () => {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleFtpFetch = async () => {
    setIsDownloading(true);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/trigger-ftp-fetch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      // Get the filename from the response headers
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'device_files.zip';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Download Started",
        description: `File ${filename} is being downloaded.`,
      });
      
    } catch (error) {
      console.error('FTP fetch error:', error);
      
      if (error instanceof Error) {
        if (error.message.includes('503')) {
          toast({
            title: "No Gateways Connected",
            description: "No gateways are currently connected to the server.",
            variant: "destructive",
          });
        } else if (error.message.includes('504')) {
          toast({
            title: "Request Timeout",
            description: "Timeout waiting for file from gateway.",
            variant: "destructive",
          });
        } else {
          toast({
            title: "Download Failed",
            description: error.message,
            variant: "destructive",
          });
        }
      } else {
        toast({
          title: "Download Failed",
          description: "An unexpected error occurred while downloading the file.",
          variant: "destructive",
        });
      }
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Card className="bg-dashboard-surface border-dashboard-border">
      <CardHeader>
        <CardTitle className="text-dashboard-text-primary flex items-center gap-2">
          <FileArchive className="h-5 w-5 text-primary" />
          FTP File Downloads
        </CardTitle>
        <CardDescription className="text-dashboard-text-secondary">
          Trigger and download device files from connected gateways
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex flex-col items-center justify-center py-8 space-y-4">
          <div className="p-4 bg-primary/10 rounded-full">
            <Download className="h-8 w-8 text-primary" />
          </div>
          
          <div className="text-center space-y-2">
            <h3 className="text-lg font-semibold text-dashboard-text-primary">
              Download Device Files
            </h3>
            <p className="text-sm text-dashboard-text-secondary max-w-md">
              Click the button below to request the latest device files from connected gateways. 
              The files will be packaged into a ZIP archive and downloaded automatically.
            </p>
          </div>

          <Button 
            onClick={handleFtpFetch}
            disabled={isDownloading}
            size="lg"
            className="min-w-[200px]"
          >
            {isDownloading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Downloading...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Trigger FTP Fetch
              </>
            )}
          </Button>
        </div>

        <div className="bg-warning/10 border border-warning/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-medium text-warning">Important Notes</h4>
              <ul className="text-sm text-dashboard-text-secondary space-y-1">
                <li>• Ensure at least one gateway is connected before triggering FTP fetch</li>
                <li>• The download may take some time depending on file size</li>
                <li>• Files are packaged as a ZIP archive containing device data</li>
                <li>• Check your browser's download folder for the completed file</li>
              </ul>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};