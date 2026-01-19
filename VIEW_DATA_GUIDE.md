# How to View Data in All Platforms

## 🎯 ThingsBoard (Interactive Dashboard)

**Access:** http://localhost:8080
**Login:** `tenant@thingsboard.org` / `tenant`

### View Device Data:
1. Click **"Devices"** in left menu
2. All devices should now show **"Active"** status
3. Click on any device name (e.g., "Egypt")
4. Click **"Latest telemetry"** tab to see current values
5. Click **"Attributes"** tab for device metadata

### Create Visualization Dashboard:
1. Go to **"Dashboards"** in left menu
2. Click **"+"** button → **"Create new dashboard"**
3. Name it "Mikroklima Dashboard"
4. Click **"Open dashboard"**
5. Click **"Enter edit mode"** (pencil icon)
6. Click **"+ Add widget"**
7. Select widget type:
   - **"Cards"** → "Simple card" for current values
   - **"Charts"** → "Timeseries line chart" for trends
   - **"Maps"** → "OpenStreet map" for locations
8. Select device (e.g., "Egypt")
9. Select data keys (e.g., "temperature", "humidity")
10. Click **"Add"**

---

## 📊 InfluxDB (Data Explorer)

**Access:** http://localhost:8086
**Login:** `admin` / `admin123`
**Organization:** `mikroklima`

### View Data in Data Explorer:
1. Click **"Data Explorer"** (graph icon) in left menu
2. Select bucket: **"mikroklima_data"**
3. Click on **"microclimate"** measurement
4. Select filters:
   - **source**: Choose device (e.g., "DWD Station Hamburg")
   - **sensor_type**: Choose sensor (e.g., "Temperature")
5. Click **"Submit"** button
6. You'll see a time-series graph!

### Create Dashboard:
1. Click **"Dashboards"** in left menu
2. Click **"Create Dashboard"** button
3. Click **"Add Cell"**
4. Build your query in Data Explorer
5. Click **"Save As"** → Save to dashboard

### Export Data:
1. In Data Explorer, after running a query
2. Click **"CSV"** button to download data
3. Or use **"Raw Data"** tab to see table view

---

## 🌐 FROST Server (JSON API)

**Access:** http://localhost:8091/FROST-Server/v1.1

### View All Devices (Things):
```bash
curl "http://localhost:8091/FROST-Server/v1.1/Things"
```

Or open in browser:
```
http://localhost:8091/FROST-Server/v1.1/Things
```

### View Specific Device:
```bash
# Get Thing by name
curl "http://localhost:8091/FROST-Server/v1.1/Things?\$filter=name eq 'Egypt Weather Station'"
```

### View All Sensors (Datastreams):
```bash
curl "http://localhost:8091/FROST-Server/v1.1/Datastreams"
```

### View Recent Measurements (Observations):
```bash
# Get last 10 observations
curl "http://localhost:8091/FROST-Server/v1.1/Observations?\$top=10&\$orderby=phenomenonTime desc"
```

### Pretty Print JSON (using jq):
```bash
curl "http://localhost:8091/FROST-Server/v1.1/Things" | jq '.'
```

### Python Script to Query FROST:
```python
import requests
import json

# Get all devices
response = requests.get("http://localhost:8091/FROST-Server/v1.1/Things")
things = response.json()

print("Devices in FROST Server:")
for thing in things['value']:
    print(f"- {thing['name']}: {thing['description']}")
```

### FROST Web Interface:
FROST Server doesn't have a built-in web UI, but you can use:
- **Browser**: Visit URLs directly (gets JSON)
- **Postman**: Import URLs for testing
- **Python/curl**: Query programmatically

---

## 🔄 Automated Data Collection

### Run Complete Data Loader (All Real Sources):
```bash
python3 complete_data_loader.py
```

### Activate All Devices (Including Demo):
```bash
python3 activate_all_devices.py
```

### Run Continuously (Every 5 minutes):
```bash
while true; do
    python3 complete_data_loader.py
    echo "Waiting 5 minutes..."
    sleep 300
done
```

---

## 📈 Quick Data Summary Commands

### Check ThingsBoard Devices:
```bash
curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}' \
  | jq -r '.token' | xargs -I {} \
  curl -s -H "X-Authorization: Bearer {}" \
  "http://localhost:8080/api/tenant/devices" | jq '.data[] | {name, label}'
```

### Check InfluxDB Data Count:
```bash
curl -s -XPOST "http://localhost:8086/api/v2/query?org=mikroklima" \
  -H "Authorization: Token mikroklima-super-secret-token" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket:"mikroklima_data") |> range(start: -24h) |> count()'
```

### Check FROST Server Things:
```bash
curl -s "http://localhost:8091/FROST-Server/v1.1/Things?\$count=true" | jq '{count: ."@iot.count", things: [.value[] | .name]}'
```

---

## 💡 Tips

1. **ThingsBoard**: Best for real-time monitoring and interactive dashboards
2. **InfluxDB**: Best for time-series analysis and data queries
3. **FROST Server**: Best for OGC-compliant API access and interoperability

4. **Refresh Data**: Run `python3 activate_all_devices.py` to send fresh data to all devices

5. **Device Status**: Devices become "Inactive" if no data received for ~10 minutes
