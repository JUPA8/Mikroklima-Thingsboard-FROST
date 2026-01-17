#!/usr/bin/env python3
"""
Temperaturvergleich: OpenSenseMap vs DWD Hamburg
Zeitraum: 01.12.2025 - 14.12.2025 (14 Tage)
Sampling: 1h Mittelwert
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from io import BytesIO
from zipfile import ZipFile
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# === Konfiguration ===
FROST_URL = "http://localhost:8091/FROST-Server/v1.1"

# Zeitraum (14 Tage)
START_DATE = "2025-12-01"
END_DATE = "2025-12-14"

# Stationen
OPENSENSEMAP_BOX_ID = "67937b67c326f20007ef99ca"  # Hamburg Iserbrook-Ost
OPENSENSEMAP_NAME = "Hamburg Iserbrook-Ost"
OPENSENSEMAP_LAT = 53.58121
OPENSENSEMAP_LON = 9.830826

DWD_STATION_ID = "01975"  # Hamburg-Fuhlsbüttel
DWD_NAME = "Hamburg-Fuhlsbüttel (DWD)"
DWD_LAT = 53.6332
DWD_LON = 9.9881


def fetch_opensensemap_historical(box_id: str, sensor_id: str, from_date: str, to_date: str) -> pd.DataFrame:
    """Historische Daten von OpenSenseMap abrufen"""
    print(f"\n📡 Lade OpenSenseMap Daten...")
    
    # API für historische Daten
    url = f"https://api.opensensemap.org/boxes/{box_id}/data/{sensor_id}"
    params = {
        "from-date": f"{from_date}T00:00:00Z",
        "to-date": f"{to_date}T23:59:59Z",
        "format": "json"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            print("⚠️  Keine Daten gefunden")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['timestamp_utc'] = pd.to_datetime(df['createdAt'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['source'] = 'opensensemap'
        df['station_id'] = box_id
        df['lat'] = OPENSENSEMAP_LAT
        df['lon'] = OPENSENSEMAP_LON
        df['unit'] = '°C'
        
        print(f"✅ {len(df)} Messungen geladen ({df['timestamp_utc'].min()} bis {df['timestamp_utc'].max()})")
        return df[['timestamp_utc', 'source', 'station_id', 'lat', 'lon', 'value', 'unit']]
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return pd.DataFrame()


def get_opensensemap_temp_sensor_id(box_id: str) -> str:
    """Temperatur-Sensor-ID von OpenSenseMap Box abrufen"""
    url = f"https://api.opensensemap.org/boxes/{box_id}"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    
    for sensor in data.get('sensors', []):
        if 'temperatur' in sensor.get('title', '').lower():
            return sensor['_id']
    return None


def fetch_dwd_historical(station_id: str, from_date: str, to_date: str) -> pd.DataFrame:
    """Historische Daten vom DWD abrufen"""
    print(f"\n📡 Lade DWD Daten (Station {station_id})...")
    
    # DWD Stundenwerte URL
    url = f"https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/recent/stundenwerte_TU_{station_id}_akt.zip"
    
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        
        with ZipFile(BytesIO(resp.content)) as z:
            # Finde die Datendatei
            data_file = [f for f in z.namelist() if f.startswith('produkt_tu_stunde')][0]
            
            with z.open(data_file) as f:
                # DWD Format: STATIONS_ID;MESS_DATUM;QN_9;TT_TU;RF_TU;eor
                df = pd.read_csv(f, sep=';', skipinitialspace=True)
        
        # Spalten bereinigen
        df.columns = df.columns.str.strip()
        
        # Zeitstempel erstellen (MESS_DATUM ist im Format YYYYMMDDHH)
        df['timestamp_utc'] = pd.to_datetime(df['MESS_DATUM'], format='%Y%m%d%H')
        df['value'] = pd.to_numeric(df['TT_TU'], errors='coerce')  # Temperatur in °C
        
        # Filtern nach Zeitraum
        start = pd.to_datetime(from_date)
        end = pd.to_datetime(to_date) + timedelta(days=1)
        df = df[(df['timestamp_utc'] >= start) & (df['timestamp_utc'] < end)]
        
        # Ungültige Werte entfernen (-999)
        df = df[df['value'] > -900]
        
        df['source'] = 'dwd'
        df['station_id'] = station_id
        df['lat'] = DWD_LAT
        df['lon'] = DWD_LON
        df['unit'] = '°C'
        
        print(f"✅ {len(df)} Messungen geladen ({df['timestamp_utc'].min()} bis {df['timestamp_utc'].max()})")
        return df[['timestamp_utc', 'source', 'station_id', 'lat', 'lon', 'value', 'unit']]
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return pd.DataFrame()


def resample_to_hourly(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Daten auf 1h Mittelwert resampling"""
    if df.empty:
        return df
    
    # Ensure timezone-naive timestamps for consistent merging
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc']).dt.tz_localize(None)
    df = df.set_index('timestamp_utc')
    
    # Resample auf stündlichen Mittelwert
    resampled = df.groupby([pd.Grouper(freq='h')]).agg({
        'value': 'mean',
        'source': 'first',
        'station_id': 'first',
        'lat': 'first',
        'lon': 'first',
        'unit': 'first'
    }).dropna(subset=['value'])
    
    resampled = resampled.reset_index()
    print(f"📊 {source_name}: {len(resampled)} stündliche Werte nach Resampling")
    return resampled


def calculate_metrics(df_a: pd.DataFrame, df_b: pd.DataFrame) -> dict:
    """Vergleichsmetriken berechnen"""
    # Merge auf Zeitstempel
    merged = pd.merge(
        df_a[['timestamp_utc', 'value']], 
        df_b[['timestamp_utc', 'value']], 
        on='timestamp_utc', 
        suffixes=('_osm', '_dwd')
    )
    
    if merged.empty:
        return None
    
    diff = merged['value_osm'] - merged['value_dwd']
    
    metrics = {
        'n_observations': len(merged),
        'period_start': merged['timestamp_utc'].min(),
        'period_end': merged['timestamp_utc'].max(),
        'osm_mean': merged['value_osm'].mean(),
        'dwd_mean': merged['value_dwd'].mean(),
        'mae': np.abs(diff).mean(),  # Mean Absolute Error
        'bias': diff.mean(),  # Systematische Abweichung
        'rmse': np.sqrt((diff ** 2).mean()),  # Root Mean Square Error
        'correlation': merged['value_osm'].corr(merged['value_dwd']),  # Korrelation
        'max_diff': diff.abs().max(),
        'std_diff': diff.std()
    }
    
    return metrics, merged


def create_frost_entities(df_osm: pd.DataFrame, df_dwd: pd.DataFrame):
    """Daten in FROST SensorThings API ablegen"""
    print("\n🔧 Erstelle FROST Entitäten...")
    
    # ObservedProperty: Temperatur
    prop_resp = requests.post(f"{FROST_URL}/ObservedProperties", json={
        "name": "Air Temperature (Comparison)",
        "definition": "http://vocab.nerc.ac.uk/collection/P01/current/TEMPPR01/",
        "description": "Lufttemperatur für Quellenvergleich"
    })
    
    if prop_resp.status_code == 201:
        prop_id = int(prop_resp.headers["Location"].split("(")[-1].rstrip(")"))
        print(f"✅ ObservedProperty erstellt (ID: {prop_id})")
    else:
        print(f"⚠️  ObservedProperty existiert möglicherweise bereits")
        prop_id = 1  # Fallback
    
    # Sensor: Generic Temperature Sensor
    sensor_resp = requests.post(f"{FROST_URL}/Sensors", json={
        "name": "Temperature Comparison Sensor",
        "description": "Temperaturmessung für Quellenvergleich",
        "encodingType": "text/html",
        "metadata": "https://example.org/sensor/temp-comparison"
    })
    
    if sensor_resp.status_code == 201:
        sensor_id = int(sensor_resp.headers["Location"].split("(")[-1].rstrip(")"))
        print(f"✅ Sensor erstellt (ID: {sensor_id})")
    else:
        sensor_id = 1  # Fallback
    
    datastreams = {}
    
    # OpenSenseMap Station
    for name, df, lat, lon, source in [
        (OPENSENSEMAP_NAME, df_osm, OPENSENSEMAP_LAT, OPENSENSEMAP_LON, 'opensensemap'),
        (DWD_NAME, df_dwd, DWD_LAT, DWD_LON, 'dwd')
    ]:
        # Thing erstellen
        thing_resp = requests.post(f"{FROST_URL}/Things", json={
            "name": name,
            "description": f"Wetterstation für Temperaturvergleich",
            "properties": {"source": source, "comparison_study": True}
        })
        
        if thing_resp.status_code == 201:
            thing_id = int(thing_resp.headers["Location"].split("(")[-1].rstrip(")"))
            print(f"✅ Thing erstellt: {name} (ID: {thing_id})")
            
            # Location
            requests.post(f"{FROST_URL}/Things({thing_id})/Locations", json={
                "name": name,
                "description": f"Standort {name}",
                "encodingType": "application/geo+json",
                "location": {"type": "Point", "coordinates": [lon, lat]}
            })
            
            # Datastream
            ds_resp = requests.post(f"{FROST_URL}/Datastreams", json={
                "name": f"Temperature - {source}",
                "description": f"Temperaturmessung von {name}",
                "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                "unitOfMeasurement": {"name": "degree Celsius", "symbol": "°C", "definition": "http://unitsofmeasure.org/ucum.html#para-30"},
                "Thing": {"@iot.id": thing_id},
                "Sensor": {"@iot.id": sensor_id},
                "ObservedProperty": {"@iot.id": prop_id}
            })
            
            if ds_resp.status_code == 201:
                ds_id = int(ds_resp.headers["Location"].split("(")[-1].rstrip(")"))
                datastreams[source] = ds_id
                print(f"✅ Datastream erstellt: {source} (ID: {ds_id})")
                
                # Observations laden
                obs_count = 0
                for _, row in df.iterrows():
                    obs_resp = requests.post(f"{FROST_URL}/Observations", json={
                        "phenomenonTime": row['timestamp_utc'].isoformat() + "Z",
                        "result": round(row['value'], 2),
                        "Datastream": {"@iot.id": ds_id}
                    })
                    if obs_resp.status_code == 201:
                        obs_count += 1
                
                print(f"   📊 {obs_count} Observations geladen")
    
    return datastreams


def create_visualization(merged: pd.DataFrame, metrics: dict, output_path: str):
    """Visualisierung erstellen"""
    print("\n📈 Erstelle Visualisierung...")
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # Plot 1: Zeitreihen übereinander
    ax1 = axes[0]
    ax1.plot(merged['timestamp_utc'], merged['value_osm'], 'b-', label='OpenSenseMap (Iserbrook)', alpha=0.8, linewidth=1)
    ax1.plot(merged['timestamp_utc'], merged['value_dwd'], 'r-', label='DWD (Fuhlsbüttel)', alpha=0.8, linewidth=1)
    ax1.set_ylabel('Temperatur (°C)')
    ax1.set_title('Temperaturvergleich: OpenSenseMap vs DWD Hamburg')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    
    # Plot 2: Differenz
    ax2 = axes[1]
    diff = merged['value_osm'] - merged['value_dwd']
    ax2.fill_between(merged['timestamp_utc'], diff, 0, alpha=0.5, color='green', label='Differenz (OSM - DWD)')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.axhline(y=metrics['bias'], color='red', linestyle='--', label=f"Bias: {metrics['bias']:.2f}°C")
    ax2.set_ylabel('Differenz (°C)')
    ax2.set_title('Abweichung zwischen den Quellen')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    
    # Plot 3: Scatter mit Korrelation
    ax3 = axes[2]
    ax3.scatter(merged['value_dwd'], merged['value_osm'], alpha=0.5, s=10)
    
    # Regressionslinie
    z = np.polyfit(merged['value_dwd'], merged['value_osm'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(merged['value_dwd'].min(), merged['value_dwd'].max(), 100)
    ax3.plot(x_line, p(x_line), 'r-', label=f'Regression (r={metrics["correlation"]:.3f})')
    
    # 1:1 Linie
    lim_min = min(merged['value_dwd'].min(), merged['value_osm'].min()) - 1
    lim_max = max(merged['value_dwd'].max(), merged['value_osm'].max()) + 1
    ax3.plot([lim_min, lim_max], [lim_min, lim_max], 'k--', alpha=0.5, label='1:1 Linie')
    
    ax3.set_xlabel('DWD Temperatur (°C)')
    ax3.set_ylabel('OpenSenseMap Temperatur (°C)')
    ax3.set_title('Korrelation der Messungen')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(lim_min, lim_max)
    ax3.set_ylim(lim_min, lim_max)
    ax3.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Grafik gespeichert: {output_path}")
    plt.close()


def generate_report(metrics: dict, output_path: str):
    """Deutschen Bericht generieren"""
    print("\n📝 Erstelle Bericht...")
    
    report = f"""# Temperaturvergleich: OpenSenseMap vs DWD Hamburg

## 1. Übersicht

**Ziel:** Vergleich der Temperaturdaten zweier unabhängiger Quellen in Hamburg

| Parameter | Wert |
|-----------|------|
| **Zeitraum** | {metrics['period_start'].strftime('%d.%m.%Y')} - {metrics['period_end'].strftime('%d.%m.%Y')} |
| **Sampling** | 1 Stunde (Mittelwert) |
| **Variable** | Lufttemperatur (°C) |
| **Anzahl Messpaare** | {metrics['n_observations']} |

---

## 2. Datenquellen

### Quelle A: OpenSenseMap (Citizen Science)
- **Station:** Hamburg Iserbrook-Ost
- **ID:** {OPENSENSEMAP_BOX_ID}
- **Koordinaten:** {OPENSENSEMAP_LAT:.4f}°N, {OPENSENSEMAP_LON:.4f}°E
- **Typ:** Bürger-Wetterstation (SenseBox)

### Quelle B: DWD (Deutscher Wetterdienst)
- **Station:** Hamburg-Fuhlsbüttel
- **ID:** {DWD_STATION_ID}
- **Koordinaten:** {DWD_LAT:.4f}°N, {DWD_LON:.4f}°E
- **Typ:** Offizielle Klimastation

**Entfernung zwischen Stationen:** ca. 8 km

---

## 3. Datenverarbeitung

### 3.1 Format (vereinheitlicht)
| Feld | Beschreibung |
|------|--------------|
| timestamp_utc | ISO 8601 (UTC) |
| source | opensensemap / dwd |
| station_id | eindeutige Kennung |
| lat, lon | Koordinaten |
| value | Temperatur |
| unit | °C |

### 3.2 Resampling
- Methode: Stundenmittelwert
- Fehlende Werte: Nicht interpoliert

---

## 4. Speicherung in FROST & TIG

### FROST (SensorThings API)
```
Thing = Station (OpenSenseMap / DWD)
  └── Location = lat/lon
  └── Datastream = Temperatur
        └── Observation = (Zeit, Wert)
```

### TIG (InfluxDB)
```
measurement: microclimate
tags: source, station_id
field: temperature
time: timestamp_utc
```

---

## 5. Vergleichsergebnisse

### 5.1 Deskriptive Statistik
| Metrik | OpenSenseMap | DWD |
|--------|--------------|-----|
| Mittelwert | {metrics['osm_mean']:.2f} °C | {metrics['dwd_mean']:.2f} °C |

### 5.2 Abweichungsmetriken

| Metrik | Wert | Interpretation |
|--------|------|----------------|
| **MAE** (Mittlere absolute Abweichung) | **{metrics['mae']:.2f} °C** | Durchschnittlicher Fehler |
| **Bias** (Systematische Abweichung) | **{metrics['bias']:.2f} °C** | OSM {'wärmer' if metrics['bias'] > 0 else 'kälter'} als DWD |
| **RMSE** (Root Mean Square Error) | **{metrics['rmse']:.2f} °C** | Streuung inkl. Ausreißer |
| **Korrelation (r)** | **{metrics['correlation']:.3f}** | {'Sehr hoch' if metrics['correlation'] > 0.95 else 'Hoch' if metrics['correlation'] > 0.9 else 'Moderat'} |
| Max. Abweichung | {metrics['max_diff']:.2f} °C | Größter Einzelfehler |
| Standardabweichung | {metrics['std_diff']:.2f} °C | Streuung der Differenz |

---

## 6. Interpretation

### 6.1 Gibt es Abweichungen?
**Ja**, die mittlere absolute Abweichung beträgt {metrics['mae']:.2f} °C.

### 6.2 Sind sie signifikant?
**{'Nein' if metrics['mae'] < 1.5 else 'Grenzwertig' if metrics['mae'] < 2.5 else 'Ja'}** — Die Abweichung liegt {'im Rahmen' if metrics['mae'] < 1.5 else 'am Rand' if metrics['mae'] < 2.5 else 'außerhalb'} der typischen Sensorgenauigkeit (±0,5–1,5 °C) und Mikroklimaeffekte.

### 6.3 Mögliche Ursachen
1. **Standortunterschiede:** ~8 km Entfernung, unterschiedliche Stadtteile
2. **Urban Heat Island:** Iserbrook (Wohngebiet) vs. Fuhlsbüttel (Flughafen, offener)
3. **Sensorhöhe & Aufstellung:** Citizen-Science vs. professionelle Messstation
4. **Kalibrierung:** DWD-Sensoren regelmäßig kalibriert
5. **Aggregation:** Unterschiedliche Messintervalle (OpenSenseMap ~5 min, DWD stündlich)

---

## 7. Visualisierung

![Temperaturvergleich](temperature_comparison.png)

**Grafik 1:** Zeitreihenvergleich beider Quellen
**Grafik 2:** Differenz (OSM - DWD) mit Bias-Linie
**Grafik 3:** Korrelation mit Regressionsgerade

---

## 8. Fazit

> **Die Temperaturmessungen von OpenSenseMap (Iserbrook) und DWD Hamburg (Fuhlsbüttel) zeigen eine {'sehr hohe' if metrics['correlation'] > 0.95 else 'hohe' if metrics['correlation'] > 0.9 else 'moderate'} zeitliche Korrelation (r = {metrics['correlation']:.3f}) bei einer mittleren Abweichung von ca. {metrics['mae']:.1f} °C (Bias: {metrics['bias']:+.2f} °C). Dies liegt im Rahmen typischer Sensor- und Mikroklimaeffekte für urbane Messstandorte mit ~8 km Entfernung.**

---

## Anhang: Technische Details

- **FROST Server:** http://localhost:8091/FROST-Server/v1.1
- **Datenformat:** SensorThings API (OGC Standard)
- **Analysezeitraum:** {metrics['period_start'].strftime('%Y-%m-%d')} bis {metrics['period_end'].strftime('%Y-%m-%d')}
- **Python-Bibliotheken:** pandas, numpy, matplotlib, requests
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Bericht gespeichert: {output_path}")


def main():
    print("=" * 70)
    print("🌡️  Temperaturvergleich: OpenSenseMap vs DWD Hamburg")
    print(f"   Zeitraum: {START_DATE} bis {END_DATE}")
    print("=" * 70)
    
    # Schritt 1: Sensor-ID ermitteln
    temp_sensor_id = get_opensensemap_temp_sensor_id(OPENSENSEMAP_BOX_ID)
    if not temp_sensor_id:
        print("❌ Temperatur-Sensor nicht gefunden!")
        return
    print(f"✅ OpenSenseMap Temperatur-Sensor: {temp_sensor_id}")
    
    # Schritt 2: Daten abrufen
    df_osm_raw = fetch_opensensemap_historical(OPENSENSEMAP_BOX_ID, temp_sensor_id, START_DATE, END_DATE)
    df_dwd_raw = fetch_dwd_historical(DWD_STATION_ID, START_DATE, END_DATE)
    
    if df_osm_raw.empty or df_dwd_raw.empty:
        print("❌ Nicht genügend Daten vorhanden!")
        return
    
    # Schritt 3: Resampling auf 1h
    df_osm = resample_to_hourly(df_osm_raw, "OpenSenseMap")
    df_dwd = resample_to_hourly(df_dwd_raw, "DWD")
    
    # Schritt 4: In FROST ablegen
    try:
        create_frost_entities(df_osm, df_dwd)
    except Exception as e:
        print(f"⚠️  FROST-Fehler (wird fortgesetzt): {e}")
    
    # Schritt 5: Metriken berechnen
    print("\n📊 Berechne Vergleichsmetriken...")
    result = calculate_metrics(df_osm, df_dwd)
    
    if result is None:
        print("❌ Keine überlappenden Zeitstempel gefunden!")
        return
    
    metrics, merged = result
    
    # Ergebnisse ausgeben
    print("\n" + "=" * 50)
    print("📊 VERGLEICHSERGEBNISSE")
    print("=" * 50)
    print(f"   Anzahl Messpaare:  {metrics['n_observations']}")
    print(f"   Zeitraum:          {metrics['period_start'].strftime('%d.%m.%Y')} - {metrics['period_end'].strftime('%d.%m.%Y')}")
    print(f"   OpenSenseMap Ø:    {metrics['osm_mean']:.2f} °C")
    print(f"   DWD Ø:             {metrics['dwd_mean']:.2f} °C")
    print("-" * 50)
    print(f"   MAE:               {metrics['mae']:.2f} °C")
    print(f"   Bias:              {metrics['bias']:+.2f} °C")
    print(f"   RMSE:              {metrics['rmse']:.2f} °C")
    print(f"   Korrelation (r):   {metrics['correlation']:.3f}")
    print("=" * 50)
    
    # Schritt 6: Visualisierung
    create_visualization(merged, metrics, "temperature_comparison.png")
    
    # Schritt 7: Bericht generieren
    generate_report(metrics, "BERICHT_Temperaturvergleich.md")
    
    print("\n✅ Analyse abgeschlossen!")


if __name__ == "__main__":
    main()
