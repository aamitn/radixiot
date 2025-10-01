---RADIX UMX201 ETH----
IP   : 192.168.51.201
Port : 502
MODBUS Device ID : 1/  247 
Point Type : 03: Holding Register
Length : 8
Data Type: Signed 16-bit Integer

curl -X POST http://localhost:8000/trigger-ftp-fetch

GATEWAY WS STREAM : ws://localhost:8000/ws/gateway
FRONTEND WS STREAM : ws://localhost:8000/ws/frontend

API DOCS : http://localhost:8000/docs

uvicorn backend.api:app --reload

{
    "type": "alert",
    "message": "No data for 52053 ms (interval 5000 ms)",
    "last_data_at": "2025-09-29T14:22:12.145362",
    "ts": "2025-09-29T14:23:04.199196"
}


{
    "type": "measurement",
    "device_id": "radix-umx201",
    "payload": {
        "timestamp": 1759155793.1993945,
        "device_id": "radix-umx201",
        "channels": [
            "T1",
            "T2",
            "T3",
            "T4",
            "T5",
            "T6",
            "T7",
            "T8"
        ],
        "temperatures": [
            33.6,
            33.5,
            33.1,
            33.2,
            33.9,
            32.8,
            33.9,
            33.6
        ],
        "raw_registers": [
            336,
            335,
            331,
            332,
            339,
            328,
            339,
            336
        ]
    },
    "received_at": "2025-09-29T14:23:15.296810"
}



