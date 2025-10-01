# app/main.py
import os
import json
import asyncio
import datetime
import tempfile
import zipfile
import sys
from typing import Dict, Any, Optional, Set
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import platform
import psutil
import shutil
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
from pydantic import BaseModel

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sqlalchemy
from sqlalchemy import func
from databases import Database
import asyncio

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


ftp_file_queue: asyncio.Queue[str] = asyncio.Queue()


# -----------------------------
# Config
# -----------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234qwer@localhost:5432/gatewaydb"
)
DEFAULT_POLLING_INTERVAL = 5000  # in ms

# Default configuration values
DEFAULT_EMAIL_CONFIG = {
    'enabled': False,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',
    'from_email': 'alerts@example.com',
    'to_email': 'recipient@example.com'
}

DEFAULT_CHANNELS = [
    {'channel': f'T{i+1}', 'enabled': True, 'threshold': 35.0 }
    for i in range(8)
]

# -----------------------------
# Ensure database exists
# -----------------------------
def ensure_database_exists(url: str):
    parsed = urlparse(url)
    dbname = parsed.path.lstrip("/")
    user = parsed.username
    password = parsed.password
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    conn = psycopg2.connect(
        dbname="postgres",
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (dbname,))
    if not cur.fetchone():
        print(f"Database '{dbname}' does not exist. Creating...")
        cur.execute(f"CREATE DATABASE {dbname}")
        print(f"Database '{dbname}' created successfully.")
    cur.close()
    conn.close()

ensure_database_exists(DATABASE_URL)

# -----------------------------
# DB setup
# -----------------------------
database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

measurements = sqlalchemy.Table(
    "measurements",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("device_id", sqlalchemy.String),
    sqlalchemy.Column("payload", sqlalchemy.JSON),
    sqlalchemy.Column("received_at", sqlalchemy.DateTime, default=datetime.datetime.utcnow)
)

email_config = sqlalchemy.Table(
    "email_config",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("enabled", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("smtp_server", sqlalchemy.String),
    sqlalchemy.Column("smtp_port", sqlalchemy.Integer),
    sqlalchemy.Column("username", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("from_email", sqlalchemy.String),
    sqlalchemy.Column("to_email", sqlalchemy.String),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, default=datetime.datetime.utcnow)
)

channel_thresholds = sqlalchemy.Table(
    "channel_thresholds",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("channel", sqlalchemy.String, unique=True),
    sqlalchemy.Column("enabled", sqlalchemy.Boolean, default=True),
    sqlalchemy.Column("threshold", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("alert_interval_sec", sqlalchemy.Integer, default=6000),  # interval in seconds
    sqlalchemy.Column("last_alert_ts", sqlalchemy.Float, nullable=True),       # unix timestamp
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, default=datetime.datetime.utcnow)
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

# Add after metadata.create_all(engine):
async def initialize_db_tables():
    """Initialize database tables with default values if they're empty"""
    # Email config
    query = email_config.select()
    if not await database.fetch_one(query):
        await database.execute(
            email_config.insert().values(
                enabled=DEFAULT_EMAIL_CONFIG['enabled'],
                smtp_server=DEFAULT_EMAIL_CONFIG['smtp_server'],
                smtp_port=DEFAULT_EMAIL_CONFIG['smtp_port'],
                username=DEFAULT_EMAIL_CONFIG['username'],
                password=DEFAULT_EMAIL_CONFIG['password'],
                from_email=DEFAULT_EMAIL_CONFIG['from_email'],
                to_email=DEFAULT_EMAIL_CONFIG['to_email'],
                updated_at=datetime.datetime.utcnow()
            )
        )
        print("Initialized email configuration with default values")

    # Channel thresholds
    query = channel_thresholds.select()
    existing_channels = await database.fetch_all(query)
    if not existing_channels:
        for ch in DEFAULT_CHANNELS:
            await database.execute(
                channel_thresholds.insert().values(
                    channel=ch['channel'],
                    enabled=ch['enabled'],
                    threshold=ch['threshold'],
                    updated_at=datetime.datetime.utcnow()
                )
            )
        print("Initialized channel thresholds with default values")

# -----------------------------
# Runtime state
# -----------------------------
last_data_time = datetime.datetime.utcnow()
polling_interval_ms = DEFAULT_POLLING_INTERVAL

gateway_clients: Set[WebSocket] = set()
frontend_clients: Set[WebSocket] = set()

# -----------------------------
# Pydantic models
# -----------------------------
class DataPayload(BaseModel):
    timestamp: float
    device_id: str
    channels: list[str]
    temperatures: list[float]
    raw_registers: list[int]

class PollingSet(BaseModel):
    interval_ms: int

class DeleteMeasurementsRequest(BaseModel):
    count: Optional[int] = None  # delete last N entries
    start_datetime: Optional[datetime.datetime] = None
    end_datetime: Optional[datetime.datetime] = None


class EmailConfig(BaseModel):
    enabled: bool
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    to_email: str

class ThresholdConfig(BaseModel):
    channel: str
    enabled: bool
    threshold: Optional[float]
    alert_interval_sec: Optional[int] = 300  # default 5 minutes


# -----------------------------
# Lifespan for FastAPI
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    await initialize_db_tables()  # <-- Add this line
    asyncio.create_task(data_monitor())
    print("Backend started with FastAPI")
    yield
    # Shutdown
    await database.disconnect()
    print("Backend shutdown complete")

app = FastAPI(title="Radix IoT Backend")

app = FastAPI(
    title="Radix IoT Backend",
    description="API that serves both the frotntend and on0edge Radix IoT Gateway",
    version="1.0.0",
    docs_url="/github-url", 
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Health Endpoint
# -----------------------------
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {
        "status": "ok",
        "time": datetime.datetime.utcnow().isoformat(),
        "connected_gateways": len(gateway_clients),
        "connected_frontends": len(frontend_clients)
    }

# -----------------------------
# REST Endpoints
# -----------------------------
@app.post("/data")
async def receive_modbus_data(payload: DataPayload):
    global last_data_time
    last_data_time = datetime.datetime.utcnow()

    # Print received data in CLI nicely
    print(f"\n[{last_data_time.isoformat()}] Received REST data from device: {payload.device_id}")
    print(f"Timestamp: {payload.timestamp}")
    print("Channels / Temperatures / Raw Registers:")
    for ch, temp, reg in zip(payload.channels, payload.temperatures, payload.raw_registers):
        print(f"  {ch:>3} | {temp:>5}°C | Raw: {reg}")

    # Store entire REST payload in DB
    query = measurements.insert().values(
        device_id=payload.device_id,
        payload=payload.dict(),
        received_at=last_data_time
    )
    await database.execute(query)
    await check_temperature_thresholds(payload.dict())

    # Broadcast
    msg = json.dumps({
        "type": "measurement",
        **payload.dict(),
        "received_at": last_data_time.isoformat()
    })
    await broadcast_to_frontend(msg)

    return {"status": "success", "received": payload.dict()}


@app.post("/data-ftp")
async def receive_ftp_zip(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        contents = await file.read()
        tmp.write(contents)
        tmp.flush()
        tmp_path = tmp.name
        tmp.close()

        # Put the ZIP path into the queue so /trigger-ftp-fetch can pick it up
        await ftp_file_queue.put(tmp_path)

        # Optional: broadcast to frontend
        with zipfile.ZipFile(tmp_path, "r") as zipf:
            file_list = [{"filename": zi.filename, "size": zi.file_size} for zi in zipf.infolist()]

        file_size = os.path.getsize(tmp_path)
        msg = json.dumps({
            "type": "ftp_zip",
            "filename": file.filename,
            "total_size": file_size,
            "num_files": len(file_list),
            "files": file_list
        })
        await broadcast_to_frontend(msg)

        print(f"[{datetime.datetime.utcnow()}] Received FTP ZIP {file.filename}, size={file_size} bytes")

        return {"success": True, "message": "File received by backend"}
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=f"Invalid zip file: {str(e)}")


@app.get("/measurements")
async def get_measurements(
    device_id: str = Query(None, description="Filter by a specific device"),
    limit: int = Query(100, ge=1, le=200000, description="Number of records per page"),
    offset: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    start_datetime: Optional[datetime.datetime] = Query(None, description="Start of the date range (ISO format). E.g., 2023-10-27T10:00:00"),
    end_datetime: Optional[datetime.datetime] = Query(None, description="End of the date range (ISO format). E.g., 2023-10-27T12:00:00Z")
):
    """
    Fetch measurements from the database with optional pagination and date range.
    
    The `start_datetime` and `end_datetime` should be in ISO 8601 format.
    URL-encoded examples:
    - `.../measurements?start_datetime=2023-10-27T10:00:00`
    - `.../measurements?start_datetime=2023-10-27T10%3A00%3A00&end_datetime=2023-10-27T11%3A00%3A00`
    
    Query parameters:
    - device_id: filter by a specific device
    - limit: number of records to return per request (default 100)
    - offset: number of records to skip (default 0)
    - start_datetime: filter for records with received_at on or after this datetime
    - end_datetime: filter for records with received_at on or before this datetime
    """
    query = measurements.select().order_by(measurements.c.received_at.desc())
    
    # Apply filters
    if device_id:
        query = query.where(measurements.c.device_id == device_id)
    if start_datetime:
        query = query.where(measurements.c.received_at >= start_datetime)
    if end_datetime:
        query = query.where(measurements.c.received_at <= end_datetime)
        
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    rows = await database.fetch_all(query)
    
    results = [
        {
            "id": row["id"],
            "device_id": row["device_id"],
            "payload": row["payload"],
            "received_at": row["received_at"].isoformat()
        }
        for row in rows
    ]
    
    return {
        "status": "success",
        "count": len(results),
        "limit": limit,
        "offset": offset,
        "measurements": results
    }



@app.delete("/measurements")
async def delete_measurements(req: DeleteMeasurementsRequest = Body(...)):
    """
    Delete measurements from the database.

    Options in the request body:
    - `count`: delete the oldest N records.
    - `start_datetime` & `end_datetime`: delete records in the datetime range.
      The datetime format should be ISO 8601, e.g., `"2023-10-27T10:00:00"`.
    """
    query = measurements.delete()

    if req.count:
        # Delete oldest N records
        query = measurements.delete().where(
            measurements.c.id.in_(
                sqlalchemy.select(measurements.c.id)
                .order_by(measurements.c.received_at.asc())  # ✅ oldest first
                .limit(req.count)
            )
        )
    elif req.start_datetime and req.end_datetime:
        # Delete records in datetime range
        query = query.where(
            measurements.c.received_at.between(req.start_datetime, req.end_datetime)
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="You must provide either 'count' or 'start_datetime' and 'end_datetime'"
        )

    result = await database.execute(query)
    return {"status": "success", "deleted": req.count or f"from {req.start_datetime} to {req.end_datetime}"}


@app.get("/measurements/count")
async def get_measurements_count():
    query = sqlalchemy.select(func.count()).select_from(measurements)
    result = await database.fetch_one(query)
    return {
        "status": "success",
        "total_entries": result[0]
    }


@app.post("/trigger-ftp-fetch")
async def trigger_ftp_fetch():
    if not gateway_clients:
        raise HTTPException(status_code=503, detail="No gateways connected")

    # Send command to gateway(s)
    await broadcast_to_gateways("ftp-fetch")

    try:
        # Wait for the next uploaded file (timeout 60s)
        zip_path = await asyncio.wait_for(ftp_file_queue.get(), timeout=60.0)

        # Return the ZIP file as response
        return FileResponse(zip_path, filename="device_files.zip", media_type="application/zip")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Gateway did not send the file in time")


@app.get("/polling")
async def get_polling_interval():
    return {"status": "success", "polling_interval_ms": polling_interval_ms}

@app.post("/polling")
async def set_polling_interval(ps: PollingSet):
    global polling_interval_ms
    if ps.interval_ms < 200:
        raise HTTPException(status_code=400, detail="Interval must be >= 200 ms")
    polling_interval_ms = ps.interval_ms
    return {"status": "success", "polling_interval_ms": polling_interval_ms}

# -----------------------------
# WebSocket Endpoints
# -----------------------------
@app.websocket("/ws/gateway")
async def ws_gateway(ws: WebSocket):
    await ws.accept()
    gateway_clients.add(ws)
    print(f"Gateway connected: {id(ws)}")

    try:
        while True:
            text = await ws.receive_text()
            try:
                data = json.loads(text)
            except:
                data = {"raw": text}

            global last_data_time
            last_data_time = datetime.datetime.utcnow()

            # Pretty-print measurement data if available
            if isinstance(data, dict) and ("device_id" in data or "data" in data):
                payload = data.get("data", data)

                print(f"\n[{last_data_time.isoformat()}] Received Gateway WebSocket Measurement from Device: {payload.get('device_id')}")
                print(f"Timestamp: {datetime.datetime.fromtimestamp(payload.get('timestamp', 0))}")
                print("Channels:       ", payload.get("channels"))
                print("Temperatures:   ", payload.get("temperatures"))
                print("Raw Registers:  ", payload.get("raw_registers"))

                # Store WS reply in DB
                query = measurements.insert().values(
                    device_id=payload.get("device_id"),
                    payload=payload,
                    received_at=last_data_time
                )
                await database.execute(query)
                await check_temperature_thresholds(payload)

                # Broadcast to frontend
                msg = json.dumps({
                    "type": "measurement",
                    "device_id": payload.get("device_id"),
                    "payload": payload,
                    "received_at": last_data_time.isoformat()
                })
                await broadcast_to_frontend(msg)
            else:
                print(f"\n[{last_data_time.isoformat()}] Gateway Message:")
                print(json.dumps(data, indent=4))
                await broadcast_to_frontend(json.dumps({
                    "type": "gateway_message",
                    "content": data,
                    "received_at": last_data_time.isoformat()
                }))

    except WebSocketDisconnect:
        print(f"Gateway disconnected: {id(ws)}")
    finally:
        gateway_clients.remove(ws)


@app.websocket("/ws/frontend")
async def ws_frontend(ws: WebSocket):
    await ws.accept()
    frontend_clients.add(ws)
    print(f"Frontend connected: {id(ws)}")

    try:
        while True:
            text = await ws.receive_text()
            try:
                data = json.loads(text)
            except:
                data = {"raw": text}

            cmd = data.get("command")
            if cmd == "ftp-fetch":
                await broadcast_to_gateways("ftp-fetch")
            elif cmd == "ping":
                await ws.send_text(json.dumps({"type": "pong", "ts": datetime.datetime.utcnow().isoformat()}))
            else:
                await ws.send_text(json.dumps({"type": "ack", "data": data}))
    except WebSocketDisconnect:
        print(f"Frontend disconnected: {id(ws)}")
    finally:
        frontend_clients.remove(ws)


# -----------------------------
# WebSocket Endpoints
# -----------------------------
@app.get("/system-info")
async def system_info():
    # CPU
    cpu_cores = psutil.cpu_count(logical=True)
    cpu_usage = psutil.cpu_percent(interval=1)

    # Memory
    mem = psutil.virtual_memory()

    # Disk
    disk = shutil.disk_usage("/")
    
    # General
    return {
        "status": "success",
        "system": {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        },
        "cpu": {
            "cores": cpu_cores,
            "usage_percent": cpu_usage
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "usage_percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
        }
    }

# -----------------------------
# Config Endpoints
# -----------------------------
@app.get("/config/email")
async def get_email_config():
    query = email_config.select()
    result = await database.fetch_one(query)
    if result:
        config = dict(result)
        config["password"] = "********"
        return config
    return {"error": "No email configuration found"}

@app.post("/config/email")
async def set_email_config(config: EmailConfig):
    query = email_config.select()
    existing = await database.fetch_one(query)
    if existing:
        if config.password == "********":
            config.password = existing.password
        query = email_config.update().values(
            **config.dict(),
            updated_at=datetime.datetime.utcnow()
        )
    else:
        query = email_config.insert().values(
            **config.dict(),
            updated_at=datetime.datetime.utcnow()
        )
    await database.execute(query)
    return {"status": "success"}

@app.get("/config/thresholds")
async def get_thresholds():
    query = channel_thresholds.select()
    results = await database.fetch_all(query)
    return {"thresholds": [dict(row) for row in results]}

@app.post("/config/thresholds")
async def set_threshold(config: ThresholdConfig):
    query = channel_thresholds.select().where(channel_thresholds.c.channel == config.channel)
    existing = await database.fetch_one(query)
    values = {
        "enabled": config.enabled,
        "threshold": config.threshold,
        "alert_interval_sec": config.alert_interval_sec,
        "updated_at": datetime.datetime.utcnow()
    }
    if existing:
        query = channel_thresholds.update().where(
            channel_thresholds.c.channel == config.channel
        ).values(**values)
    else:
        query = channel_thresholds.insert().values(
            channel=config.channel,
            **values
        )
    await database.execute(query)
    return {"status": "success"}

# -----------------------------
# Helpers
# -----------------------------
async def broadcast_to_frontend(message: str):
    if frontend_clients:
        await asyncio.gather(*[client.send_text(message) for client in frontend_clients], return_exceptions=True)

async def broadcast_to_gateways(message: str):
    if gateway_clients:
        await asyncio.gather(
            *[client.send_text(message) for client in gateway_clients],
            return_exceptions=True
        )

async def send_temperature_alert(channel: str, temp: float, threshold: float, data: dict):
    query = email_config.select()
    email_settings = await database.fetch_one(query)
    if not email_settings or not email_settings.enabled:
        return
    try:
        msg = MIMEMultipart()
        msg['From'] = email_settings.from_email
        msg['To'] = email_settings.to_email
        msg['Subject'] = f"Temperature Alert: {channel} exceeded threshold"
        body = f"""
Temperature Alert

Channel: {channel}
Current Temperature: {temp}°C
Threshold: {threshold}°C
Device ID: {data['device_id']}
Timestamp: {datetime.datetime.fromtimestamp(data['timestamp']).isoformat()}

All Channel Temperatures:
"""
        for ch, t in zip(data['channels'], data['temperatures']):
            body += f"{ch}: {t}°C\n"
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(email_settings.smtp_server, email_settings.smtp_port) as server:
            server.starttls()
            server.login(email_settings.username, email_settings.password)
            server.send_message(msg)
        print(f"Temperature alert email sent for {channel}")
    except Exception as e:
        print(f"Failed to send email alert: {e}")

async def check_temperature_thresholds(data: dict):
    query = channel_thresholds.select()
    thresholds = await database.fetch_all(query)
    if not thresholds:
        return
    threshold_dict = {t['channel']: t for t in thresholds}
    now_ts = time.time()
    for channel, temp in zip(data['channels'], data['temperatures']):
        threshold_config = threshold_dict.get(channel)
        if (
            threshold_config
            and threshold_config['enabled']
            and threshold_config['threshold'] is not None
            and temp > threshold_config['threshold']
        ):
            last_alert_ts = threshold_config.get('last_alert_ts') or 0
            interval = threshold_config.get('alert_interval_sec') or 300
            if now_ts - last_alert_ts >= interval:
                await send_temperature_alert(channel, temp, threshold_config['threshold'], data)
                # Update last_alert_ts in DB
                await database.execute(
                    channel_thresholds.update().where(
                        channel_thresholds.c.channel == channel
                    ).values(last_alert_ts=now_ts)
                )

async def data_monitor():
    """Background monitor for polling interval"""
    global last_data_time
    await asyncio.sleep(1)
    while True:
        diff = (datetime.datetime.utcnow() - last_data_time).total_seconds() * 1000
        if diff > polling_interval_ms:
            msg = json.dumps({
                "type": "alert",
                "message": f"No data for {int(diff)} ms (interval {polling_interval_ms} ms)",
                "last_data_at": last_data_time.isoformat(),
                "ts": datetime.datetime.utcnow().isoformat()
            })
            await broadcast_to_frontend(msg)
            print(f"🚨 ALERT: Data gap {diff} ms", file=sys.stderr)
        await asyncio.sleep(polling_interval_ms / 1000.0 / 2.0)
