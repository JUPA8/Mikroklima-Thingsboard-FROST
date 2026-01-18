# 📙 API Documentation

Complete API reference for all three platforms.

---

## 🌐 FROST Server API

**Base URL:** `http://localhost:8091/FROST-Server/v1.1`

### Entities

| Endpoint | Description |
|----------|-------------|
| `/Things` | IoT devices/stations |
| `/Locations` | Geographic coordinates (GeoJSON) |
| `/Sensors` | Physical sensors |
| `/ObservedProperties` | Measurement types (Temperature, PM10, etc.) |
| `/Datastreams` | Sensor → Property links |
| `/Observations` | Actual measurements |

### Example Queries
```bash
# Get all stations
curl "http://localhost:8091/FROST-Server/v1.1/Things"

# Latest 10 observations
curl "http://localhost:8091/FROST-Server/v1.1/Observations?\$top=10&\$orderby=phenomenonTime%20desc"

# Get datastream with observations
curl "http://localhost:8091/FROST-Server/v1.1/Datastreams(1)?\$expand=Observations(\$top=100)"
```

---

## 📱 Thingsboard API

**Base URL:** `http://localhost:8080/api`

### Send Telemetry
```bash
curl -X POST http://localhost:8080/api/v1/DEVICE_TOKEN/telemetry \
  -H "Content-Type: application/json" \
  -d '{"temperature":23.5,"humidity":65.2}'
```

### Python Example
```python
import requests

TB_HOST = "http://localhost:8080"
DEVICE_TOKEN = "YOUR_TOKEN"

data = {"temperature": 23.5, "humidity": 65.2}
response = requests.post(f"{TB_HOST}/api/v1/{DEVICE_TOKEN}/telemetry", json=data)
```

---

## 💾 InfluxDB API

**Base URL:** `http://localhost:8086/api/v2`

### Query Example
```python
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://localhost:8086",
    token="mikroklima-super-secret-token",
    org="Micoklima"
)

query = '''
from(bucket: "mikroklima_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["source"] == "Mobilithek Dormagen")
'''

tables = client.query_api().query(query)
```

---

**For complete API documentation, see official docs:**
- FROST: https://fraunhoferiosb.github.io/FROST-Server/
- Thingsboard: https://thingsboard.io/docs/
- InfluxDB: https://docs.influxdata.com/influxdb/v2/
