# 📕 Troubleshooting Guide

Common issues and solutions.

---

## 🐳 Docker Issues

### Container won't start

**Problem:** Service fails to start

**Solutions:**
```bash
# Check logs
docker compose logs SERVICE_NAME

# Common services:
docker compose logs influxdb
docker compose logs frost
docker compose logs thingsboard
docker compose logs postgres

# Restart specific service
docker compose restart SERVICE_NAME

# Full restart
docker compose down && docker compose up -d
```

### Port already in use

**Problem:** "Port 8080 is already allocated"

**Solutions:**
```bash
# Find what's using the port
lsof -i :8080
lsof -i :8086
lsof -i :8091

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
services:
  thingsboard:
    ports:
      - "8081:8080"  # Use 8081 instead
```

### Out of disk space

**Problem:** "No space left on device"

**Solutions:**
```bash
# Check Docker disk usage
docker system df

# Clean up
docker system prune -a  # Remove all unused containers, images
docker volume prune     # Remove unused volumes

# Clean up old logs
docker compose logs --tail=0 SERVICE_NAME
```

---

## 🔌 Connection Issues

### Cannot connect to FROST Server

**Problem:** FROST API returns connection error

**Solutions:**
```bash
# Wait 30 seconds after start (DB initialization)
sleep 30

# Check if container is running
docker compose ps frost

# Check logs
docker compose logs frost

# Test connection
curl http://localhost:8091/FROST-Server/v1.1/

# If PostgreSQL not ready:
docker compose restart frost
```

### Cannot connect to InfluxDB

**Problem:** InfluxDB connection refused

**Solutions:**
```bash
# Check health
curl http://localhost:8086/health

# Check if running
docker compose ps influxdb

# Verify token
echo "mikroklima-super-secret-token"

# Test connection
curl -H "Authorization: Token mikroklima-super-secret-token" \
     http://localhost:8086/api/v2/buckets
```

### Thingsboard UI won't load

**Problem:** Browser shows loading or blank page

**Solutions:**
1. Wait 45 seconds after docker-compose up
2. Clear browser cache (Cmd+Shift+R / Ctrl+Shift+R)
3. Try incognito mode
4. Check logs: `docker compose logs thingsboard`
5. Restart: `docker compose restart thingsboard`

---

## 📊 Data Issues

### No data in Thingsboard

**Problem:** Widgets show "No data"

**Solutions:**
```bash
# 1. Verify data is being sent
python complete_data_loader.py

# 2. Check device has data
# Go to: Devices → [Your Device] → Latest telemetry

# 3. Check widget time range
# Set to "Realtime" or "Last hour"

# 4. Verify device token
cat config/thingsboard_credentials.json
```

### FROST Server returns empty

**Problem:** `/Observations` returns empty array

**Solutions:**
```bash
# Check if data was loaded
curl "http://localhost:8091/FROST-Server/v1.1/Observations"

# Run data loader
python complete_data_loader.py

# Check datastreams exist
curl "http://localhost:8091/FROST-Server/v1.1/Datastreams"

# If empty, run frost_data_loader.py
python scripts/frost_data_loader.py
```

### InfluxDB query returns no data

**Problem:** Flux query returns empty

**Solutions:**
```python
# Check bucket exists
curl -H "Authorization: Token mikroklima-super-secret-token" \
     http://localhost:8086/api/v2/buckets

# Verify data exists
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://localhost:8086",
    token="mikroklima-super-secret-token",
    org="Micoklima"
)

# List measurements
query = 'import "influxdata/influxdb/schema"
schema.measurements(bucket: "mikroklima_data")'

tables = client.query_api().query(query)
```

---

## 🐍 Python Issues

### Module not found

**Problem:** `ModuleNotFoundError: No module named 'requests'`

**Solutions:**
```bash
# Install missing modules
pip install requests pandas numpy matplotlib folium influxdb-client

# Or use virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Script fails with error

**Problem:** Python script crashes

**Solutions:**
```bash
# Run with verbose output
python -v scripts/SCRIPT_NAME.py

# Check Python version (need 3.10+)
python3 --version

# Check if services are running
docker compose ps

# Check logs for specific errors
python complete_data_loader.py 2>&1 | tee output.log
```

---

## 🔐 Authentication Issues

### Thingsboard login fails

**Problem:** "Invalid username or password"

**Solutions:**
1. Use default credentials:
   - Username: `tenant@thingsboard.org`
   - Password: `tenant`
2. Wait 45 seconds after container start
3. Check container logs: `docker compose logs thingsboard`
4. Reset by removing volume: `docker compose down -v`

### InfluxDB token invalid

**Problem:** "Unauthorized" error

**Solutions:**
```bash
# Check token in docker-compose.yml
grep INFLUXDB_INIT_ADMIN_TOKEN docker-compose.yml

# Default token:
# mikroklima-super-secret-token

# Get new token from UI:
# http://localhost:8086 → Data → API Tokens
```

---

## 🔄 Reset Everything

### Complete fresh start
```bash
# Stop all containers
docker compose down

# Remove all volumes (DELETES ALL DATA!)
docker compose down -v

# Remove downloaded images
docker compose down --rmi all

# Start fresh
docker compose up -d

# Wait for initialization
sleep 60

# Recreate devices
python scripts/thingsboard_setup.py

# Load initial data
python complete_data_loader.py
```

---

## 📞 Getting Help

### Before asking for help, collect this info:
```bash
# 1. Docker version
docker --version
docker compose version

# 2. Service status
docker compose ps

# 3. Recent logs
docker compose logs --tail=50 SERVICE_NAME

# 4. System info
uname -a  # macOS/Linux
python3 --version

# 5. Disk space
df -h
docker system df
```

### Useful commands for debugging
```bash
# Enter container shell
docker compose exec SERVICE_NAME bash

# Example: Enter InfluxDB container
docker compose exec influxdb bash

# View environment variables
docker compose exec SERVICE_NAME env

# Check network
docker network ls
docker network inspect mikroklima_mikroklima-net
```

---

## ✅ Health Check Checklist

Run these to verify everything works:
```bash
# 1. All containers running
docker compose ps | grep Up

# 2. FROST Server responsive
curl http://localhost:8091/FROST-Server/v1.1/

# 3. InfluxDB healthy
curl http://localhost:8086/health

# 4. Thingsboard accessible
curl -I http://localhost:8080

# 5. Data loader works
python complete_data_loader.py

# 6. Python scripts have dependencies
pip list | grep -E "requests|pandas|influxdb"
```

If all checks pass ✅ - System is operational!

