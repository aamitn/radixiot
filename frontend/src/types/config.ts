export interface ThresholdConfig {
  id: number;
  channel: string;
  enabled: boolean;
  threshold: number;
  alert_interval_sec?: number | null;
  last_alert_ts?: string | null;
  updated_at?: string;
}
export interface EmailConfig {
  id: number;
  enabled: boolean;
  smtp_server: string;
  smtp_port: number;
  username: string;
  password: string;
  from_email: string;
  to_email: string;
  updated_at: string;
}
