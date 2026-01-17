#!/usr/bin/env python3
"""
FROST SensorThings API Data Loader
Fetches the same environmental data as TIG project and pushes to FROST Server
"""

import requests
import json
from datetime import datetime, timezone

FROST_URL = "http://localhost:8091/FROST-Server/v1.1"

# === Data Sources (same as TIG project) ===
OPENSENSEMAP_BOX_ID = "67937b67c326f20007ef99ca"
OPENSENSEMAP_URL = f"https://api.opensensemap.org/boxes/{OPENSENSEMAP_BOX_ID}"

HAMBURG_HALM_URL = "https://api.hamburg.de/datasets/v1/luftmessnetz/collections/luftmessnetz_messwerte/items?f=json&stationskuerzel=80KT"


def create_thing(name: str, description: str, properties: dict = None) -> int:
    """Create a Thing in FROST and return its ID"""
    payload = {
        "name": name,
        "description": description,
        "properties": properties or {}
    }
    resp = requests.post(f"{FROST_URL}/Things", json=payload)
    if resp.status_code == 201:
        location = resp.headers.get("Location", "")
        thing_id = int(location.split("(")[-1].rstrip(")"))
        print(f"✅ Created Thing: {name} (ID: {thing_id})")
        return thing_id
    else:
        print(f"❌ Failed to create Thing {name}: {resp.status_code} - {resp.text}")
        return None


def create_location(name: str, description: str, lat: float, lon: float, thing_id: int) -> int:
    """Create a Location and link it to a Thing"""
    payload = {
        "name": name,
        "description": description,
        "encodingType": "application/geo+json",
        "location": {
            "type": "Point",
            "coordinates": [lon, lat]
        }
    }
    resp = requests.post(f"{FROST_URL}/Things({thing_id})/Locations", json=payload)
    if resp.status_code == 201:
        location = resp.headers.get("Location", "")
        loc_id = int(location.split("(")[-1].rstrip(")"))
        print(f"✅ Created Location: {name} (ID: {loc_id})")
        return loc_id
    else:
        print(f"❌ Failed to create Location {name}: {resp.status_code} - {resp.text}")
        return None


def create_observed_property(name: str, definition: str, description: str) -> int:
    """Create an ObservedProperty"""
    payload = {
        "name": name,
        "definition": definition,
        "description": description
    }
    resp = requests.post(f"{FROST_URL}/ObservedProperties", json=payload)
    if resp.status_code == 201:
        location = resp.headers.get("Location", "")
        prop_id = int(location.split("(")[-1].rstrip(")"))
        print(f"✅ Created ObservedProperty: {name} (ID: {prop_id})")
        return prop_id
    else:
        print(f"❌ Failed to create ObservedProperty {name}: {resp.status_code} - {resp.text}")
        return None


def create_sensor(name: str, description: str, encoding_type: str = "text/html", metadata: str = "") -> int:
    """Create a Sensor"""
    payload = {
        "name": name,
        "description": description,
        "encodingType": encoding_type,
        "metadata": metadata or f"https://example.org/sensors/{name.replace(' ', '_')}"
    }
    resp = requests.post(f"{FROST_URL}/Sensors", json=payload)
    if resp.status_code == 201:
        location = resp.headers.get("Location", "")
        sensor_id = int(location.split("(")[-1].rstrip(")"))
        print(f"✅ Created Sensor: {name} (ID: {sensor_id})")
        return sensor_id
    else:
        print(f"❌ Failed to create Sensor {name}: {resp.status_code} - {resp.text}")
        return None


def create_datastream(name: str, description: str, thing_id: int, sensor_id: int, 
                      observed_property_id: int, unit_name: str, unit_symbol: str, 
                      unit_definition: str = "") -> int:
    """Create a Datastream"""
    payload = {
        "name": name,
        "description": description,
        "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
        "unitOfMeasurement": {
            "name": unit_name,
            "symbol": unit_symbol,
            "definition": unit_definition or f"http://unitsofmeasure.org/{unit_symbol}"
        },
        "Thing": {"@iot.id": thing_id},
        "Sensor": {"@iot.id": sensor_id},
        "ObservedProperty": {"@iot.id": observed_property_id}
    }
    resp = requests.post(f"{FROST_URL}/Datastreams", json=payload)
    if resp.status_code == 201:
        location = resp.headers.get("Location", "")
        ds_id = int(location.split("(")[-1].rstrip(")"))
        print(f"✅ Created Datastream: {name} (ID: {ds_id})")
        return ds_id
    else:
        print(f"❌ Failed to create Datastream {name}: {resp.status_code} - {resp.text}")
        return None


def create_observation(datastream_id: int, result: float, phenomenon_time: str = None) -> bool:
    """Create an Observation"""
    if phenomenon_time is None:
        phenomenon_time = datetime.now(timezone.utc).isoformat()
    else:
        # Ensure proper ISO format with time
        if 'T' not in phenomenon_time:
            phenomenon_time = f"{phenomenon_time}T00:00:00Z"
    
    payload = {
        "phenomenonTime": phenomenon_time,
        "result": result,
        "Datastream": {"@iot.id": datastream_id}
    }
    resp = requests.post(f"{FROST_URL}/Observations", json=payload)
    if resp.status_code == 201:
        return True
    else:
        print(f"❌ Failed to create Observation: {resp.status_code} - {resp.text}")
        return False


def fetch_opensensemap_data():
    """Fetch data from OpenSenseMap API"""
    print("\n📡 Fetching data from OpenSenseMap...")
    try:
        resp = requests.get(OPENSENSEMAP_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        result = {
            "name": data.get("name", "Unknown"),
            "latitude": data.get("currentLocation", {}).get("coordinates", [0, 0])[1],
            "longitude": data.get("currentLocation", {}).get("coordinates", [0, 0])[0],
            "sensors": {}
        }
        
        # Map sensor indices (from TIG config)
        sensor_mapping = {
            0: "pm10",       # PM10
            1: "pm25",       # PM2.5
            2: "temperature", # Temperature
            3: "humidity",   # Humidity
            4: "pressure"    # Pressure
        }
        
        for sensor in data.get("sensors", []):
            sensor_title = sensor.get("title", "").lower()
            last_measurement = sensor.get("lastMeasurement", {})
            
            if last_measurement:
                value = last_measurement.get("value")
                timestamp = last_measurement.get("createdAt")
                
                # Try to identify sensor by title
                if "pm10" in sensor_title:
                    result["sensors"]["pm10"] = {"value": float(value), "time": timestamp, "unit": "µg/m³"}
                elif "pm2.5" in sensor_title or "pm25" in sensor_title:
                    result["sensors"]["pm25"] = {"value": float(value), "time": timestamp, "unit": "µg/m³"}
                elif "temperatur" in sensor_title or "temperature" in sensor_title:
                    result["sensors"]["temperature"] = {"value": float(value), "time": timestamp, "unit": "°C"}
                elif "luftfeuchte" in sensor_title or "humidity" in sensor_title or "feuchte" in sensor_title:
                    result["sensors"]["humidity"] = {"value": float(value), "time": timestamp, "unit": "%"}
                elif "luftdruck" in sensor_title or "pressure" in sensor_title or "druck" in sensor_title:
                    result["sensors"]["pressure"] = {"value": float(value), "time": timestamp, "unit": "Pa"}
        
        print(f"✅ OpenSenseMap data fetched: {result['name']}")
        for key, val in result["sensors"].items():
            print(f"   - {key}: {val['value']} {val['unit']}")
        
        return result
    except Exception as e:
        print(f"❌ Error fetching OpenSenseMap data: {e}")
        return None


def fetch_hamburg_halm_data():
    """Fetch data from Hamburg Luftmessnetz API"""
    print("\n📡 Fetching data from Hamburg HaLm...")
    try:
        resp = requests.get(HAMBURG_HALM_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        features = data.get("features", [])
        if not features:
            print("❌ No features found in Hamburg HaLm response")
            return None
        
        feature = features[0]
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [0, 0])
        
        result = {
            "name": "Altona-Elbhang (80KT)",
            "latitude": coords[1] if len(coords) > 1 else 0,
            "longitude": coords[0] if len(coords) > 0 else 0,
            "timestamp": props.get("datum"),
            "sensors": {}
        }
        
        # Air quality indices
        if props.get("NO2") is not None:
            result["sensors"]["no2_index"] = {"value": float(props["NO2"]), "unit": "index"}
        if props.get("SO2") is not None:
            result["sensors"]["so2_index"] = {"value": float(props["SO2"]), "unit": "index"}
        if props.get("PM10") is not None:
            result["sensors"]["pm10_index"] = {"value": float(props["PM10"]), "unit": "index"}
        if props.get("O3") is not None:
            result["sensors"]["o3_index"] = {"value": float(props["O3"]), "unit": "index"}
        if props.get("LQI") is not None:
            result["sensors"]["lqi"] = {"value": float(props["LQI"]), "unit": "index"}
        
        print(f"✅ Hamburg HaLm data fetched: {result['name']}")
        for key, val in result["sensors"].items():
            print(f"   - {key}: {val['value']} {val['unit']}")
        
        return result
    except Exception as e:
        print(f"❌ Error fetching Hamburg HaLm data: {e}")
        return None


def setup_frost_entities():
    """Set up all FROST entities (Things, Sensors, ObservedProperties, Datastreams)"""
    print("\n🔧 Setting up FROST entities...")
    
    entities = {}
    
    # === Create ObservedProperties ===
    entities["props"] = {}
    properties_config = [
        ("Temperature", "http://vocab.nerc.ac.uk/collection/P01/current/TEMPPR01/", "Air temperature"),
        ("Humidity", "http://vocab.nerc.ac.uk/collection/P01/current/CRELZZ01/", "Relative humidity"),
        ("Pressure", "http://vocab.nerc.ac.uk/collection/P01/current/CAFSAP01/", "Atmospheric pressure"),
        ("PM10", "http://vocab.nerc.ac.uk/collection/P01/current/PM10WMAS/", "Particulate Matter PM10"),
        ("PM2.5", "http://vocab.nerc.ac.uk/collection/P01/current/PM25WMAS/", "Particulate Matter PM2.5"),
        ("NO2 Index", "https://www.hamburg.de/luftmessnetz/no2", "Nitrogen dioxide air quality index"),
        ("SO2 Index", "https://www.hamburg.de/luftmessnetz/so2", "Sulfur dioxide air quality index"),
        ("PM10 Index", "https://www.hamburg.de/luftmessnetz/pm10", "PM10 air quality index"),
        ("O3 Index", "https://www.hamburg.de/luftmessnetz/o3", "Ozone air quality index"),
        ("LQI", "https://www.hamburg.de/luftmessnetz/lqi", "Air quality index (1-5)")
    ]
    
    for name, definition, description in properties_config:
        prop_id = create_observed_property(name, definition, description)
        if prop_id:
            entities["props"][name] = prop_id
    
    # === Create Sensors ===
    entities["sensors"] = {}
    sensors_config = [
        ("OpenSenseMap Environmental Sensor", "Citizen science environmental sensor from OpenSenseMap"),
        ("Hamburg HaLm Air Quality Sensor", "Official Hamburg air quality monitoring station")
    ]
    
    for name, description in sensors_config:
        sensor_id = create_sensor(name, description)
        if sensor_id:
            entities["sensors"][name] = sensor_id
    
    # === Create Things (Stations) ===
    entities["things"] = {}
    
    # OpenSenseMap Station
    osm_thing_id = create_thing(
        "OpenSenseMap Hamburg",
        "Citizen science environmental monitoring station in Hamburg",
        {
            "source": "OpenSenseMap",
            "station_id": OPENSENSEMAP_BOX_ID,
            "station_type": "citizen_science",
            "city": "Hamburg"
        }
    )
    if osm_thing_id:
        entities["things"]["opensensemap"] = osm_thing_id
        create_location("OpenSenseMap Hamburg", "Hamburg citizen science station", 
                       53.5855, 9.8988, osm_thing_id)  # Approximate coords
    
    # Hamburg HaLm Station
    halm_thing_id = create_thing(
        "Hamburg Altona-Elbhang (80KT)",
        "Official Hamburg air quality monitoring station at Altona-Elbhang",
        {
            "source": "Hamburg_HaLm",
            "station_id": "80KT",
            "station_type": "Hintergrundmessstation",
            "city": "Hamburg"
        }
    )
    if halm_thing_id:
        entities["things"]["halm"] = halm_thing_id
        create_location("Altona-Elbhang", "Hamburg official air quality station", 
                       53.5505, 9.9144, halm_thing_id)  # Approximate coords
    
    # === Create Datastreams ===
    entities["datastreams"] = {}
    
    # OpenSenseMap datastreams
    osm_sensor = entities["sensors"].get("OpenSenseMap Environmental Sensor")
    osm_thing = entities["things"].get("opensensemap")
    
    if osm_sensor and osm_thing:
        datastreams_osm = [
            ("temperature", "Temperature", "Air temperature from OpenSenseMap", "degree Celsius", "°C"),
            ("humidity", "Humidity", "Relative humidity from OpenSenseMap", "percent", "%"),
            ("pressure", "Pressure", "Atmospheric pressure from OpenSenseMap", "Pascal", "Pa"),
            ("pm10", "PM10", "PM10 concentration from OpenSenseMap", "microgram per cubic meter", "µg/m³"),
            ("pm25", "PM2.5", "PM2.5 concentration from OpenSenseMap", "microgram per cubic meter", "µg/m³"),
        ]
        
        for key, prop_name, desc, unit_name, unit_symbol in datastreams_osm:
            prop_id = entities["props"].get(prop_name)
            if prop_id:
                ds_id = create_datastream(f"OSM {prop_name}", desc, osm_thing, osm_sensor, 
                                         prop_id, unit_name, unit_symbol)
                if ds_id:
                    entities["datastreams"][f"osm_{key}"] = ds_id
    
    # Hamburg HaLm datastreams
    halm_sensor = entities["sensors"].get("Hamburg HaLm Air Quality Sensor")
    halm_thing = entities["things"].get("halm")
    
    if halm_sensor and halm_thing:
        datastreams_halm = [
            ("no2_index", "NO2 Index", "NO2 air quality index from Hamburg HaLm", "index", "1-5"),
            ("so2_index", "SO2 Index", "SO2 air quality index from Hamburg HaLm", "index", "1-5"),
            ("pm10_index", "PM10 Index", "PM10 air quality index from Hamburg HaLm", "index", "1-5"),
            ("o3_index", "O3 Index", "O3 air quality index from Hamburg HaLm", "index", "1-5"),
            ("lqi", "LQI", "Overall air quality index from Hamburg HaLm", "index", "1-5"),
        ]
        
        for key, prop_name, desc, unit_name, unit_symbol in datastreams_halm:
            prop_id = entities["props"].get(prop_name)
            if prop_id:
                ds_id = create_datastream(f"HaLm {prop_name}", desc, halm_thing, halm_sensor, 
                                         prop_id, unit_name, unit_symbol)
                if ds_id:
                    entities["datastreams"][f"halm_{key}"] = ds_id
    
    return entities


def load_observations(entities: dict):
    """Fetch data from APIs and create observations in FROST"""
    print("\n📊 Loading observations...")
    
    # Fetch OpenSenseMap data
    osm_data = fetch_opensensemap_data()
    if osm_data:
        sensor_to_ds = {
            "temperature": "osm_temperature",
            "humidity": "osm_humidity",
            "pressure": "osm_pressure",
            "pm10": "osm_pm10",
            "pm25": "osm_pm25"
        }
        
        for sensor_key, ds_key in sensor_to_ds.items():
            if sensor_key in osm_data["sensors"] and ds_key in entities["datastreams"]:
                sensor_data = osm_data["sensors"][sensor_key]
                ds_id = entities["datastreams"][ds_key]
                success = create_observation(ds_id, sensor_data["value"], sensor_data.get("time"))
                if success:
                    print(f"   ✅ {sensor_key}: {sensor_data['value']}")
    
    # Fetch Hamburg HaLm data
    halm_data = fetch_hamburg_halm_data()
    if halm_data:
        sensor_to_ds = {
            "no2_index": "halm_no2_index",
            "so2_index": "halm_so2_index",
            "pm10_index": "halm_pm10_index",
            "o3_index": "halm_o3_index",
            "lqi": "halm_lqi"
        }
        
        timestamp = halm_data.get("timestamp")
        for sensor_key, ds_key in sensor_to_ds.items():
            if sensor_key in halm_data["sensors"] and ds_key in entities["datastreams"]:
                sensor_data = halm_data["sensors"][sensor_key]
                ds_id = entities["datastreams"][ds_key]
                success = create_observation(ds_id, sensor_data["value"], timestamp)
                if success:
                    print(f"   ✅ {sensor_key}: {sensor_data['value']}")


def check_frost_connection():
    """Check if FROST server is available"""
    try:
        resp = requests.get(f"{FROST_URL}", timeout=5)
        if resp.status_code == 200:
            print(f"✅ FROST Server is running at {FROST_URL}")
            return True
        else:
            print(f"❌ FROST Server returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to FROST Server at {FROST_URL}")
        print("   Make sure the server is running (docker compose up -d)")
        return False


def main():
    print("=" * 60)
    print("🌡️  FROST SensorThings API Data Loader")
    print("    Fetching same data as TIG project")
    print("=" * 60)
    
    if not check_frost_connection():
        return
    
    # Set up FROST entities
    entities = setup_frost_entities()
    
    # Load observations
    load_observations(entities)
    
    print("\n" + "=" * 60)
    print("✅ Data loading complete!")
    print(f"   View data at: {FROST_URL}")
    print("=" * 60)


if __name__ == "__main__":
    main()
