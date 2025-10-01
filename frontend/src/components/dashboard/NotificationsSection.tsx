import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Bell, Mail } from "lucide-react";
import toast from "react-hot-toast";
import type { ThresholdConfig, EmailConfig } from "@/types/config";

export const NotificationsSection = () => {
  const [thresholds, setThresholds] = useState<ThresholdConfig[]>([]);
  const [emailConfig, setEmailConfig] = useState<EmailConfig | null>(null);
  const [loading, setLoading] = useState(false);

  // Fetch configurations
  const fetchConfigs = async () => {
    try {
      const [thresholdsRes, emailRes] = await Promise.all([
        fetch('http://localhost:8000/config/thresholds'),
        fetch('http://localhost:8000/config/email')
      ]);
      
      const thresholdsData = await thresholdsRes.json();
      const emailData = await emailRes.json();
      
      setThresholds(thresholdsData.thresholds);
      setEmailConfig(emailData);
    } catch (error) {
      toast.error("Failed to load configurations");
    }
  };

  // Update threshold
const updateThreshold = async (
  channel: string,
  enabled: boolean,
  threshold: number,
  alert_interval_sec?: number | null
) => {
  try {
    const response = await fetch('http://localhost:8000/config/thresholds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel, enabled, threshold, alert_interval_sec })
    });

    if (response.ok) {
      toast.success(`Updated threshold for ${channel}`);
      fetchConfigs();
    }
  } catch (error) {
    toast.error(`Failed to update ${channel} threshold`);
  }
};

  // Update email config
  const updateEmailConfig = async (config: Partial<EmailConfig>) => {
    try {
      const response = await fetch('http://localhost:8000/config/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...emailConfig, ...config })
      });
      
      if (response.ok) {
        toast.success("Email configuration updated");
        fetchConfigs();
      }
    } catch (error) {
      toast.error("Failed to update email configuration");
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Temperature Thresholds
          </CardTitle>
          <CardDescription>
            Configure alert thresholds for each temperature channel
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {thresholds
              .slice() // Create a shallow copy to avoid mutating state directly
              .sort((a, b) => a.channel.localeCompare(b.channel)) // Sort by channel
              .map((threshold) => (
              <div key={threshold.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="space-y-1">
                  <Label>Channel {threshold.channel}</Label>
                  <div className="flex items-center gap-4">
                    <Switch
                      checked={threshold.enabled}
                      onCheckedChange={(enabled) => 
                        updateThreshold(threshold.channel, enabled, threshold.threshold)
                      }
                    />
                    <Input
                      type="number"
                      value={threshold.threshold}
                      onChange={(e) => 
                        updateThreshold(threshold.channel, threshold.enabled, Number(e.target.value))
                      }
                      className="w-24"
                    />
                    <span className="text-sm text-muted-foreground">°C</span>
                    
                    <Input
                        type="number"
                        placeholder="Alert interval sec"
                        value={threshold.alert_interval_sec ?? ''}
                        onChange={(e) =>
                        updateThreshold(
                            threshold.channel,
                            threshold.enabled,
                            threshold.threshold,
                            Number(e.target.value)
                        )
                        }
                        className="w-32"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Notifications
          </CardTitle>
          <CardDescription>
            Configure email settings for alert notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Switch
                checked={emailConfig?.enabled ?? false}
                onCheckedChange={(enabled) => updateEmailConfig({ enabled })}
              />
              <Label>Enable Email Notifications</Label>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>SMTP Server</Label>
                <Input
                  value={emailConfig?.smtp_server ?? ''}
                  onChange={(e) => updateEmailConfig({ smtp_server: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>SMTP Port</Label>
                <Input
                  type="number"
                  value={emailConfig?.smtp_port ?? ''}
                  onChange={(e) => updateEmailConfig({ smtp_port: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-2">
                <Label>Username</Label>
                <Input
                  value={emailConfig?.username ?? ''}
                  onChange={(e) => updateEmailConfig({ username: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Password</Label>
                <Input
                  type="password"
                  value={emailConfig?.password ?? ''}
                  onChange={(e) => updateEmailConfig({ password: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>From Email</Label>
                <Input
                  type="email"
                  value={emailConfig?.from_email ?? ''}
                  onChange={(e) => updateEmailConfig({ from_email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>To Email</Label>
                <Input
                  type="email"
                  value={emailConfig?.to_email ?? ''}
                  onChange={(e) => updateEmailConfig({ to_email: e.target.value })}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
