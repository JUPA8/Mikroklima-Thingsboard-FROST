#!/usr/bin/env python3
"""
Quick check of data in all platforms
"""

import requests
import json

print("=" * 80)
print("DATA STATUS CHECK - ALL PLATFORMS")
print("=" * 80)
print()

# 1. THINGSBOARD
print("🔷 THINGSBOARD DEVICES")
print("-" * 80)
try:
    # Login
    login_response = requests.post(
        "http://localhost:8080/api/auth/login",
        json={"username": "tenant@thingsboard.org", "password": "tenant"},
        timeout=5
    )
    token = login_response.json()['token']

    # Get devices
    devices_response = requests.get(
        "http://localhost:8080/api/tenant/devices?pageSize=20",
        headers={"X-Authorization": f"Bearer {token}"},
        timeout=5
    )
    devices = devices_response.json()['data']

    print(f"{'Device Name':<45} {'Label':<35} {'Status'}")
    print("-" * 80)
    for device in devices:
        name = device['name']
        label = device.get('label', 'N/A')

        # Get telemetry to check if active
        device_id = device['id']['id']
        telemetry_response = requests.get(
            f"http://localhost:8080/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys=temperature",
            headers={"X-Authorization": f"Bearer {token}"},
            timeout=5
        )

        has_data = len(telemetry_response.json()) > 0
        status = "✅ ACTIVE" if has_data else "⚠️  INACTIVE"
        print(f"{name:<45} {label:<35} {status}")

    print(f"\n Total Devices: {len(devices)}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n")

# 2. INFLUXDB
print("🔶 INFLUXDB DATA")
print("-" * 80)
try:
    from influxdb_client import InfluxDBClient

    client = InfluxDBClient(
        url="http://localhost:8086",
        token="mikroklima-super-secret-token",
        org="mikroklima"
    )

    query_api = client.query_api()

    # Count measurements by source
    query = '''
    from(bucket: "mikroklima_data")
        |> range(start: -24h)
        |> group(columns: ["source"])
        |> count()
        |> group()
    '''

    result = query_api.query(query)

    print(f"{'Source':<45} {'Measurements (24h)'}")
    print("-" * 80)

    sources = {}
    for table in result:
        for record in table.records:
            source = record.values.get('source', 'Unknown')
            count = record.values.get('_value', 0)
            if source in sources:
                sources[source] += count
            else:
                sources[source] = count

    for source, count in sorted(sources.items()):
        print(f"{source:<45} {count:>10}")

    print(f"\n Total Sources: {len(sources)}")
    client.close()
except Exception as e:
    print(f"❌ Error: {e}")

print("\n")

# 3. FROST SERVER
print("🔵 FROST SERVER THINGS")
print("-" * 80)
try:
    response = requests.get(
        "http://localhost:8091/FROST-Server/v1.1/Things?$select=name,description&$count=true",
        timeout=5
    )
    data = response.json()

    things = data.get('value', [])
    total_count = data.get('@iot.count', 0)

    print(f"{'Thing Name':<45} {'Description'}")
    print("-" * 80)
    for thing in things[:10]:  # Show first 10
        name = thing.get('name', 'N/A')
        desc = thing.get('description', 'N/A')[:33]
        print(f"{name:<45} {desc}")

    if total_count > 10:
        print(f"... and {total_count - 10} more")

    print(f"\n Total Things: {total_count}")

    # Get observation count
    obs_response = requests.get(
        "http://localhost:8091/FROST-Server/v1.1/Observations?$count=true&$top=0",
        timeout=5
    )
    obs_count = obs_response.json().get('@iot.count', 0)
    print(f" Total Observations: {obs_count}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n")
print("=" * 80)
print("✅ Check complete!")
print("=" * 80)
print("\n💡 To view data:")
print("  - ThingsBoard Dashboard: http://localhost:8080")
print("  - InfluxDB Data Explorer: http://localhost:8086")
print("  - FROST Server API: http://localhost:8091/FROST-Server/v1.1")
print("\n📖 See VIEW_DATA_GUIDE.md for detailed instructions")
