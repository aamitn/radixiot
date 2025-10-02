import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { RealTimeSection } from "@/components/dashboard/RealTimeSection";
import { HistoricalSection } from "@/components/dashboard/HistoricalSection";
import { FtpSection } from "@/components/dashboard/FtpSection";
import SystemInfoSection from "@/components/dashboard/SystemInfoSection";
import { Activity, Database, Download, Thermometer, Wifi, LogOut, Info, Bell } from "lucide-react";
import { toast } from "react-hot-toast";
import { NotificationsSection } from "@/components/dashboard/NotificationsSection";

const Dashboard = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("userEmail");
    toast.success("Logged out successfully");
    navigate("/auth");
  };

  return (
    <div className="min-h-screen bg-dashboard-bg">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-dashboard-text-primary flex items-center gap-3">
              <Link to="/">
                <Thermometer className="h-8 w-8 text-primary cursor-pointer hover:text-primary/80 transition-colors" />
              </Link>
              Temperature Monitoring Dashboard
            </h1>
            <p className="text-dashboard-text-secondary">
              Real-time temperature monitoring and historical data analysis
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 bg-success/10 border border-success/20 rounded-lg">
              <Wifi className="h-4 w-4 text-success animate-pulse" />
              <span className="text-success font-medium">Connected</span>
            </div>
            <Button onClick={handleLogout} variant="outline" size="sm">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>

        {/* Main Dashboard Tabs */}
        <Tabs defaultValue="realtime" className="w-full">
          <TabsList className="grid w-full grid-cols-5 bg-dashboard-surface">
            <TabsTrigger 
              value="realtime" 
              className="flex items-center gap-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <Activity className="h-4 w-4" />
              Real-Time
            </TabsTrigger>
            <TabsTrigger 
              value="historical" 
              className="flex items-center gap-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <Database className="h-4 w-4" />
              Historical
            </TabsTrigger>
            <TabsTrigger 
              value="ftp" 
              className="flex items-center gap-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <Download className="h-4 w-4" />
              FTP Downloads
            </TabsTrigger>
            
            <TabsTrigger 
              value="system" 
              className="flex items-center gap-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <Info className="h-4 w-4" />
              System Info
            </TabsTrigger>

            <TabsTrigger 
              value="notifications" 
              className="flex items-center gap-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
          </TabsList>

          <TabsContent value="realtime" className="space-y-6">
            <RealTimeSection />
          </TabsContent>

          <TabsContent value="historical" className="space-y-6">
            <HistoricalSection />
          </TabsContent>

          <TabsContent value="ftp" className="space-y-6">
            <FtpSection />
          </TabsContent>
          
          <TabsContent value="system" className="space-y-6">
            <SystemInfoSection />
          </TabsContent>

          <TabsContent value="notifications" className="space-y-6">
            <NotificationsSection />
          </TabsContent>
          
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;