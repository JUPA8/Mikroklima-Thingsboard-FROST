# 📘 Thingsboard Setup & Configuration Guide

Complete guide for setting up Thingsboard with FROST Server integration.

---

## 📋 Table of Contents

- [Installation](#installation)
- [Initial Configuration](#initial-configuration)
- [Device Management](#device-management)
- [Data Integration](#data-integration)
- [Dashboard Creation](#dashboard-creation)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Installation

### Prerequisites

- Docker & Docker Compose installed
- Ports 8080 and 5432 available
- Minimum 2GB RAM

### Start Thingsboard
```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# Wait for Thingsboard to initialize (~45 seconds)
docker compose logs -f thingsboard
```

### Access Thingsboard UI

1. Open browser: http://localhost:8080
2. Login credentials:
   - **Username:** `tenant@thingsboard.org`
   - **Password:** `tenant`

---

## ⚙️ Initial Configuration

### 1. Change Default Password

1. Click profile icon (top right)
2. Select "Profile"
3. Click "Change password"
4. Enter new secure password

### 2. Configure Organization

1. Go to "Settings" → "Home settings"
2. Update organization name
3. Add logo (optional)

---

## 📱 Device Management

### Automatic Device Creation

Use the provided Python script:
```bash
python scripts/thingsboard_setup.py
```

This creates 6 devices:
- OpenSenseMap_5df93d3b39652b001b8cd9d2
- DWD_01975
- Hamburg_Luftmessnetz
- UDP_Osnabrueck
- Tunisia
- Egypt

Device credentials are saved to `config/thingsboard_credentials.json`

### Manual Device Creation

1. Navigate to **Entities → Devices**
2. Click **"+"** button
3. Fill in:
   - **Name:** Device name (e.g., "Mobilithek_Dormagen")
   - **Label:** Descriptive label
   - **Device type:** sensor type (e.g., "air_quality")
4. Click **"Add"**

### Get Device Token

1. Click on device name
2. Click **"Copy access token"** button
3. Save token to `config/thingsboard_credentials.json`

---

## 🔌 Data Integration

### Send Telemetry Data

#### Using Python:
```python
import requests

THINGSBOARD_HOST = "http://localhost:8080"
ACCESS_TOKEN = "YOUR_DEVICE_TOKEN"

# Telemetry data
data = {
    "temperature": 23.5,
    "humidity": 65.2,
    "pm10": 18.7
}

# Send to Thingsboard
url = f"{THINGSBOARD_HOST}/api/v1/{ACCESS_TOKEN}/telemetry"
response = requests.post(url, json=data)

print(f"Status: {response.status_code}")  # 200 = Success
```

#### Using curl:
```bash
curl -X POST http://localhost:8080/api/v1/YOUR_TOKEN/telemetry \
  -H "Content-Type: application/json" \
  -d '{"temperature":23.5,"humidity":65.2}'
```

### Integration with FROST Server

The `complete_data_loader.py` script automatically pushes data to both platforms:
```python
# Fetch from source
data = fetch_mobilithek_dormagen_data()

# Push to FROST Server
push_to_frost(data)

# Push to Thingsboard
push_to_thingsboard("Mobilithek Dormagen", data)

# Push to InfluxDB
push_to_influxdb(data)
```

---

## 📊 Dashboard Creation

### Create New Dashboard

1. Go to **Dashboards**
2. Click **"+"** → **"Create new dashboard"**
3. Enter dashboard name
4. Click **"Add"**

### Add Widgets

1. Click **"Enter edit mode"** (pencil icon)
2. Click **"Add new widget"** or drag widget from library
3. Configure widget:
   - **Data source:** Select device
   - **Keys:** Select telemetry keys (temperature, humidity, etc.)
   - **Time window:** Set range (e.g., Last hour)
4. Customize appearance (colors, labels, etc.)
5. Click **"Add"**

### Widget Types

| Widget Type | Use Case |
|-------------|----------|
| **Gauge** | Single value display (current temperature) |
| **Chart** | Time series data (temperature over time) |
| **Map** | Geographic location of sensors |
| **Table** | Multiple values in table format |
| **Cards** | Multiple metrics in card layout |

### Example Dashboard Layout
```
┌─────────────────────────────────────────────────┐
│  Temperature Gauge  │  Humidity Gauge           │
├─────────────────────────────────────────────────┤
│            Temperature Timeline                  │
│            (Last 24 hours)                       │
├─────────────────────────────────────────────────┤
│  PM10 Chart         │  PM2.5 Chart              │
└─────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Device Not Receiving Data

**Problem:** Telemetry sent but not visible in UI

**Solutions:**
1. Check device token is correct
2. Verify data format is valid JSON
3. Check time window in widget (set to "Realtime")
4. Clear browser cache
5. Check device activity: Devices → [Device] → Latest telemetry

### Dashboard Shows No Data

**Problem:** Widgets empty or show "No data"

**Solutions:**
1. Verify device has received data (Latest telemetry tab)
2. Adjust time window (try "Realtime" or "Last hour")
3. Check widget configuration (correct device & keys selected)
4. Ensure data is being sent: `python complete_data_loader.py`

### Login Failed

**Problem:** Cannot login to Thingsboard

**Solutions:**
1. Wait 45 seconds after `docker compose up` (initialization time)
2. Check container status: `docker compose ps`
3. Check logs: `docker compose logs thingsboard`
4. Reset password: Use default credentials first
5. Restart: `docker compose restart thingsboard`

### Port 8080 Already in Use

**Problem:** "Port 8080 is already allocated"

**Solutions:**
```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8081:8080"  # Use 8081 instead
```

---

## 📚 Additional Resources

- **Thingsboard Docs:** https://thingsboard.io/docs/
- **REST API Reference:** https://thingsboard.io/docs/reference/rest-api/
- **MQTT API:** https://thingsboard.io/docs/reference/mqtt-api/
- **Rule Engine:** https://thingsboard.io/docs/user-guide/rule-engine-2-0/re-getting-started/

---

## ✅ Checklist

- [ ] Thingsboard UI accessible at http://localhost:8080
- [ ] Default password changed
- [ ] 6 devices created (or use `thingsboard_setup.py`)
- [ ] Device tokens saved to `config/thingsboard_credentials.json`
- [ ] Test data sent successfully
- [ ] Dashboard created with widgets
- [ ] Widgets showing real-time data

---

**Next Steps:** Check [DATA_QUALITY_REPORT.md](DATA_QUALITY_REPORT.md) for data analysis results.
