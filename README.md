# Radix UMX201 IoT Gateway - Technical Documentation

- ---RADIX UMX201 ETH----
- IP   : 192.168.51.201
- Port : 502
- MODBUS Device ID : 1/  247 
- Point Type : 03: Holding Register
- Length : 8
- Data Type: Signed 16-bit Integer

## 🚀 Default Creds
Frontend : email: "admin@livelineindia.com" / password: "123456

# Radix Gateway Executables

| Platform | Executable Type | Filename | Download |
|----------|----------------|----------|----------|
| Windows  | GUI            | `gateway-gui-windows.exe`      | [Download](https://github.com/aamitn/radixiot/releases/) |
| Windows  | Headless       | `gateway-headless-windows.exe` | [Download](https://github.com/aamitn/radixiot/releases/) |
| Linux    | GUI            | `gateway-gui-linux`            | [Download](https://github.com/aamitn/radixiot/releases/) |
| Linux    | Headless       | `gateway-headless-linux`       | [Download](https://github.com/aamitn/radixiot/releases/) |
| macOS    | GUI            | `gateway-gui-macos`            | [Download](https://github.com/aamitn/radixiot/releases/) |
| macOS    | Headless       | `gateway-headless-macos`       | [Download](https://github.com/aamitn/radixiot/releases/) |

---

## 🧪 Managed Services

| Platform | URL |
|----------|--------------|
| Dashboard  | [https://iradix.bitmutex.com](https://iradix.bitmutex.com)   |
| Backend    | [https://iradixb.bitmutex.com](https://iradixb.bitmutex.com) |

*Note: The macOS build is currently pending due to dependency issues.*

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Installation & Setup](#installation--setup)
5. [API Documentation](#api-documentation)
6. [Configuration Guide](#configuration-guide)
7. [Development Guide](#development-guide)
8. [Deployment Guide](#deployment-guide)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

---
*** NOTE : If backend build fails in edge/single board computer for headless environemnts, remove pyqtf dependencies from requirements

## 🚀 Project Overview

The **Radix UMX201 IoT Gateway** is a comprehensive end-to-end solution for industrial temperature monitoring using Modbus TCP protocol. The system consists of three main components:

- **Backend API Server** (`api.py`) - FastAPI-based REST/WebSocket server
- **Gateway Applications** - GUI (`gateway.py`) and headless (`gateway_headless.py`) versions
- **Frontend Dashboard** - React-based web interface

### Key Features
- Real-time temperature monitoring from UMX201 devices
- Dual gateway operation (GUI and headless modes)
- WebSocket real-time data streaming
- Excel data logging with configurable options
- FTP file retrieval and management
- Email alert system with configurable thresholds
- Modern React dashboard with real-time charts
- PostgreSQL data persistence
- System health monitoring

---

## 🏗 System Architecture

### High-Level Architecture
```
┌─────────────────┐    WebSocket/REST    ┌──────────────────┐
│   UMX201 Device │◄───────────────────► │   Gateway        │
│   (Modbus TCP)  │                      │  (GUI/Headless)  │
└─────────────────┘                      └──────────────────┘
                                              │
                                              │ HTTP/WebSocket
                                              ▼
┌─────────────────┐    WebSocket/REST    ┌──────────────────┐
│   Frontend      │◄───────────────────► │   Backend API    │
│   Dashboard     │                      │   (FastAPI)      │
└─────────────────┘                      └──────────────────┘
                                              │
                                              │ PostgreSQL
                                              ▼
                                        ┌────────────┐
                                        │  Database  │
                                        └────────────┘
```

### Data Flow
1. **Gateway** polls UMX201 device via Modbus TCP
2. **Gateway** sends data to Backend via REST API or WebSocket
3. **Backend** stores data in PostgreSQL and processes alerts
4. **Frontend** connects via WebSocket for real-time updates
5. **Users** interact with dashboard for monitoring and configuration

---

## 🔧 Component Details

### 1. Backend API Server (`api.py`)

#### Technology Stack
- **Framework**: FastAPI with ASGI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **WebSocket**: Native WebSocket support
- **Authentication**: JWT (planned)
- **Email**: SMTP with TLS

#### Key Endpoints
- `POST /data` - Receive measurement data
- `GET /measurements` - Query historical data
- `WS /ws/gateway` - Gateway WebSocket connection
- `WS /ws/frontend` - Frontend WebSocket connection
- `POST /config/email` - Configure email alerts
- `GET /system-info` - System health monitoring

#### Database Schema
```sql
-- Measurements table
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR,
    payload JSONB,
    received_at TIMESTAMP
);

-- Email configuration
CREATE TABLE email_config (
    id SERIAL PRIMARY KEY,
    enabled BOOLEAN,
    smtp_server VARCHAR,
    smtp_port INTEGER,
    username VARCHAR,
    password VARCHAR,
    from_email VARCHAR,
    to_email VARCHAR
);

-- Channel thresholds
CREATE TABLE channel_thresholds (
    id SERIAL PRIMARY KEY,
    channel VARCHAR UNIQUE,
    enabled BOOLEAN,
    threshold FLOAT,
    alert_interval_sec INTEGER,
    last_alert_ts FLOAT
);
```

### 2. Gateway Applications

#### GUI Gateway (`gateway.py`)
- **Framework**: PyQt5 for desktop interface
- **Modbus**: pymodbus for device communication
- **Real-time**: Matplotlib for temperature graphs
- **Data Export**: Excel logging with pandas
- **WebSocket**: Real-time backend communication

#### Headless Gateway (`gateway_headless.py`)
- **Purpose**: Production deployment without GUI
- **Features**: Same functionality as GUI version
- **Logging**: Comprehensive logging system
- **Configuration**: File-based settings

### 3. Frontend Dashboard

#### Technology Stack
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Charts**: Recharts for data visualization
- **State Management**: TanStack Query
- **Routing**: React Router
- **UI Components**: Custom shadcn/ui components

#### Key Pages
- `/` - Landing page
- `/auth` - Authentication (placeholder)
- `/dashboard` - Main monitoring interface

---

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL 12+
- UMX201 Modbus TCP device

### Backend Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd radix-umx201-gateway
```

2. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

3. **Database Configuration**
```bash
# Environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/gatewaydb"
export SECRET_KEY="your-secret-key"
```

4. **Start Backend**
```bash
python api.py
# or with uvicorn for production
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Environment Configuration**
```bash
# .env file
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

3. **Start Development Server**
```bash
npm run dev
```

### Gateway Setup

1. **GUI Gateway**
```bash
python gateway.py
```

2. **Headless Gateway**
```bash
python gateway_headless.py
```

---

## 📚 API Documentation

### REST Endpoints

#### POST /data
Receive temperature measurements from gateways.

**Request Body:**
```json
{
  "timestamp": 1700000000.0,
  "device_id": "radix-umx201",
  "channels": ["T1", "T2", "T3"],
  "temperatures": [25.5, 26.0, 24.8],
  "raw_registers": [255, 260, 248]
}
```

#### GET /measurements
Query historical measurements with filtering and pagination.

**Query Parameters:**
- `device_id` (optional): Filter by device
- `limit` (default: 100): Records per page
- `offset` (default: 0): Pagination offset
- `start_datetime`, `end_datetime`: Date range filter

#### WebSocket Endpoints

##### /ws/gateway
Gateway connections for real-time data streaming.

**Message Format:**
```json
{
  "type": "measurement",
  "device_id": "radix-umx201",
  "payload": {...},
  "received_at": "2024-01-01T10:00:00Z"
}
```

##### /ws/frontend
Frontend connections for real-time updates.

**Message Types:**
- `measurement` - New temperature data
- `alert` - System alerts
- `ftp_zip` - FTP file notifications

---

## ⚙ Configuration Guide

### Backend Configuration

#### Environment Variables
```python
DATABASE_URL="postgresql://user:pass@localhost:5432/gatewaydb"
DEFAULT_POLLING_INTERVAL=5000  # ms
EMAIL_CONFIG_ENABLED=false
```

#### Email Configuration
```json
{
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your-email@gmail.com",
  "password": "app-password",
  "from_email": "alerts@example.com",
  "to_email": "recipient@example.com"
}
```

### Gateway Configuration

#### Modbus Settings
```python
MODBUS_SETTINGS = {
    'host': '192.168.51.201',
    'port': 502,
    'timeout': 3,
    'register_start': 0,
    'num_channels': 8,
    'poll_interval': 5000,
    'device_id': 'radix-umx201'
}
```

#### API Settings
```python
API_SETTINGS = {
    'enabled': True,
    'base_url': 'http://localhost:8000',
    'method': 'POST',
    'timeout': 10
}
```

---

## 👨‍💻 Development Guide

### Backend Development

#### Adding New Endpoints
```python
@app.post("/new-endpoint")
async def new_endpoint(payload: NewModel):
    # Implementation
    return {"status": "success"}
```

#### Database Operations
```python
# Insert data
query = measurements.insert().values(
    device_id="device123",
    payload=data,
    received_at=datetime.utcnow()
)
await database.execute(query)

# Query data
query = measurements.select().where(
    measurements.c.device_id == "device123"
)
results = await database.fetch_all(query)
```

### Frontend Development

#### Adding New Components
```typescript
const NewComponent: React.FC = () => {
  return (
    <div className="dashboard-card">
      {/* Component content */}
    </div>
  );
};
```

#### WebSocket Integration
```typescript
const useWebSocket = (url: string) => {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };
    return () => ws.close();
  }, [url]);
  
  return data;
};
```

### Gateway Development

#### Adding New Features
```python
class EnhancedModbusGui(ModbusGui):
    def __init__(self):
        super().__init__()
        self.setup_new_features()
    
    def setup_new_features(self):
        # New functionality
        pass
```

---

## 🚀 Deployment Guide

### Production Backend

1. **Use Production Server**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

2. **Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX idx_measurements_device_id ON measurements(device_id);
CREATE INDEX idx_measurements_received_at ON measurements(received_at);
```

3. **Reverse Proxy (nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Frontend Deployment

1. **Build for Production**
```bash
npm run build
```

2. **Serve Static Files**
```bash
npm run preview
# or serve with nginx
```

### Gateway Deployment

#### Headless Gateway as Service
```ini
# /etc/systemd/system/radix-gateway.service
[Unit]
Description=Radix UMX201 Headless Gateway
After=network.target

[Service]
Type=simple
User=gateway
WorkingDirectory=/opt/radix-gateway
ExecStart=/usr/bin/python3 gateway_headless.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 🔧 Troubleshooting

### Common Issues

#### Gateway Connection Issues
1. **Check Modbus Device Connectivity**
```bash
telnet 192.168.51.201 502
```

2. **Verify Network Configuration**
- Ensure gateway and device are on same subnet
- Check firewall settings
- Verify Modbus port (502) is open

#### Database Connection Issues
1. **Test Database Connection**
```python
import psycopg2
try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
```

#### WebSocket Connection Issues
1. **Check WebSocket URL**
```javascript
// Ensure correct WebSocket URL format
const ws = new WebSocket('ws://localhost:8000/ws/frontend');
```

### Logging and Debugging

#### Backend Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Gateway Debug Mode
```python
# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)
```

---

## 🔒 Security Considerations

### Network Security
1. **Use VPN** for remote device access
2. **Firewall Configuration**
   - Restrict Modbus port (502) to internal network
   - Limit API port (8000) access
3. **SSL/TLS** for production deployments

### Application Security
1. **Input Validation**
```python
from pydantic import BaseModel, validator

class DataPayload(BaseModel):
    device_id: str
    temperatures: List[float]
    
    @validator('temperatures')
    def validate_temperatures(cls, v):
        if any(temp < -100 or temp > 300 for temp in v):
            raise ValueError('Temperature out of valid range')
        return v
```

2. **Rate Limiting** (planned)
3. **Authentication & Authorization** (planned)

### Data Security
1. **Database Encryption**
2. **Secure Credential Storage**
3. **Regular Backups**

---

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# API health check
curl http://localhost:8000/health

# Database health
psql $DATABASE_URL -c "SELECT count(*) FROM measurements;"
```

### Performance Monitoring
1. **Database Performance**
```sql
-- Monitor query performance
EXPLAIN ANALYZE SELECT * FROM measurements 
WHERE received_at > NOW() - INTERVAL '1 hour';
```

2. **System Resources**
```bash
# Monitor system resources
htop
iotop -o
```

### Backup Strategy
1. **Database Backups**
```bash
# Daily backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

2. **Configuration Backups**
- Version control for configuration files
- Regular backup of critical settings

---

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write comprehensive docstrings
- Include unit tests for new features

### Testing
```bash
# Backend tests
pytest tests/

# Frontend tests
npm test
```

---

## 📞 Support

### Documentation
- [API Documentation](http://localhost:8000/docs) (when running)
- [Component Documentation](./docs/)
- [Troubleshooting Guide](./docs/troubleshooting.md)

### Community
- GitHub Issues for bug reports
- Discussions for questions and ideas
- Wiki for user guides

### Commercial Support
Contact Bitmutex Technologies for enterprise support and custom development.

---

## 📄 License

This project is proprietary software developed by Bitmutex Technologies. All rights reserved.

---

*Last Updated: January 2024*  
*Version: 1.5*  
*Developed by Bitmutex Technologies*