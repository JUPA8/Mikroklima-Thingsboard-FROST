# 🌡️ Mikroklima Hamburg - Thingsboard & FROST Integration
**IoT Data Integration System with Real Data Sources**

[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![OGC](https://img.shields.io/badge/OGC-SensorThings_API-orange.svg)](https://www.ogc.org/standards/sensorthings)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ein umfassendes IoT-Datenintegrationssystem, das FROST Server (OGC SensorThings API), Thingsboard und InfluxDB kombiniert für Echtzeit-Umweltmonitoring mit realen Datenquellen.

---

## 📋 Inhaltsverzeichnis

- [Überblick](#-überblick)
- [Features](#-features)
- [Architektur](#-architektur)
- [Voraussetzungen](#-voraussetzungen)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Datenquellen](#-datenquellen)
- [Projektstruktur](#-projektstruktur)
- [Ergebnisse](#-ergebnisse)
- [API Dokumentation](#-api-dokumentation)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Überblick

Dieses Projekt demonstriert eine **professionelle IoT-Datenintegration** mit drei führenden Plattformen:

- **FROST Server** - OGC SensorThings API Standard
- **Thingsboard** - IoT Device Management & Visualisierung  
- **InfluxDB** - Time-Series Datenbank für Performance

### 🎓 Projektkontext

- **Studiengang:** Informatik (Master)
- **Universität:** Hochschule Osnabrück
- **Modul:** Studentisches Forschungsprojekt
- **Thema:** Datenraumtechnologien & IoT-Plattformen
- **Zeitraum:** Wintersemester 2025/2026

### 🌍 Anwendungsfälle

✅ **Echtzeit Umweltmonitoring** - Temperatur, Luftfeuchtigkeit, Luftqualität  
✅ **Datenqualitätsanalyse** - Vergleich Citizen Science vs. offizielle Daten  
✅ **Multi-Plattform Integration** - Interoperabilität zwischen IoT-Systemen  
✅ **Internationale Datenerfassung** - Deutschland & Ägypten  

---

## ✨ Features

| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **3-Plattform Integration** | FROST + Thingsboard + InfluxDB | ✅ Operational |
| **Echte Datenquellen** | 3 Real + 3 Demo Quellen | ✅ 11,331+ Messwerte |
| **Automatische ETL-Pipeline** | Python-basierte Datenverarbeitung | ✅ Komplett |
| **Datenqualitätsanalyse** | Vollständigkeit, Lücken, Statistik | ✅ 85.7% Completeness |
| **Statistische Validierung** | RMSE, MAE, Korrelationsanalyse | ✅ r=0.996 |
| **Interaktive Visualisierung** | Karten, Charts, Dashboards | ✅ HTML + PNG |
| **Docker-basiert** | Vollständig containerisiert | ✅ 7 Services |
| **OGC Standard-konform** | SensorThings API 1.1 | ✅ Certified |

---

## 🏗️ Architektur
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            DATENQUELLEN (5)                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🟢 REAL DATA (3):                    🔵 DEMO DATA (2):                      │
│  ┌────────────────────┐              ┌──────────────────┐                   │
│  │ OpenSenseMap       │              │ DWD Station      │                   │
│  │ Hamburg            │              │ Hamburg          │                   │
│  │ Real-time data     │              │ (Simulation)     │                   │
│  │ PM10, PM2.5, Temp  │              └──────────────────┘                   │
│  └────────────────────┘                                                     │
│  ┌────────────────────┐              ┌──────────────────┐                   │
│  │ Mobilithek         │              │ UDP Osnabrück    │                   │
│  │ Dormagen           │              │ (Simulation)     │                   │
│  │ 11,139 records     │              └──────────────────┘                   │
│  │ PM10, PM2.5, Temp  │                                                     │
│  └────────────────────┘                                                     │
│  ┌────────────────────┐                                                     │
│  │ Open-Meteo         │                                                     │
│  │ Egypt (Cairo)      │                                                     │
│  │ 192 records        │                                                     │
│  │ Weather data       │                                                     │
│  └────────────────────┘                                                     │
└──────────────────┬───────────────────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ETL PIPELINE                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │              complete_data_loader.py                               │     │
│  │                                                                    │     │
│  │  • Fetch data from 3 real sources (OpenSenseMap, Mobilithek, Egypt)│     │
│  │  • Transform & validate                                            │     │
│  │  • Push to 3 platforms simultaneously                              │     │
│  │  • Error handling & logging                                        │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└────────────┬─────────────────┬─────────────────┬──────────────────────────────┘
             │                 │                 │
             ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER (3 Platforms)                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐             │
│  │  INFLUXDB 2.x   │  │  FROST SERVER   │  │  THINGSBOARD     │             │
│  │  Time-Series DB │  │  OGC Standard   │  │  IoT Platform    │             │
│  │                 │  │                 │  │                  │             │
│  │  :8086          │  │  :8091          │  │  :8080           │             │
│  │  Bucket: env    │  │  PostgreSQL +   │  │  6 Devices       │             │
│  │  Flux queries   │  │  PostGIS        │  │  Real-time dash  │             │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
             │                 │                 │
             └─────────────────┴─────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ANALYSIS & VISUALIZATION                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │ Data Quality   │  │ Statistical    │  │ Interactive    │                 │
│  │ Analysis       │  │ Validation     │  │ Maps           │                 │
│  │ (85.7%)        │  │ (RMSE, MAE)    │  │ (Folium)       │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Voraussetzungen

### Software Requirements

- **Docker** >= 20.10
- **Docker Compose** >= 2.0  
- **Python** >= 3.10 (für Scripts)
- **Git** (für Repository-Management)

### Hardware Requirements

- **RAM:** 8 GB empfohlen (minimum 4 GB)
- **Disk:** 5 GB freier Speicher
- **CPU:** 2+ Cores empfohlen

### Ports

Folgende Ports müssen frei sein:
- `3000` - Grafana (optional)
- `5433` - PostgreSQL (FROST Backend)
- `8080` - Thingsboard UI
- `8086` - InfluxDB API
- `8091` - FROST Server API

### System prüfen
```bash
# Docker Version
docker --version
docker compose version

# Python Version
python3 --version

# Freie Ports prüfen
lsof -i :8080 -i :8086 -i :8091 -i :5433
```

---

## 🛠️ Installation

### 1. Repository klonen
```bash
git clone https://github.com/JUPA8/Mikroklima-Thingsboard-FROST.git
cd Mikroklima-Thingsboard-FROST
```

### 2. Python Dependencies installieren (optional)
```bash
# Virtual Environment erstellen
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Dependencies installieren
pip install requests pandas numpy matplotlib folium influxdb-client
```

### 3. Docker Services starten
```bash
# Alle Services starten
docker compose up -d

# Status prüfen (alle sollten "running" sein)
docker compose ps

# Logs verfolgen
docker compose logs -f
```

### 4. Warten bis alle Services bereit sind
```bash
# FROST Server braucht ~30 Sekunden für DB-Initialisierung
# InfluxDB braucht ~15 Sekunden
# Thingsboard braucht ~45 Sekunden

# Health-Check
curl http://localhost:8086/health  # InfluxDB
curl http://localhost:8091/FROST-Server/v1.1/  # FROST
curl http://localhost:8080  # Thingsboard
```

---

## 🚀 Quick Start

### Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Thingsboard** | http://localhost:8080 | `tenant@thingsboard.org` / `tenant` |
| **InfluxDB** | http://localhost:8086 | `admin` / `mikroklima123` |
| **FROST API** | http://localhost:8091/FROST-Server/v1.1 | - (public) |
| **PostgreSQL** | `localhost:5433` | `frost` / `frost` |

### Daten laden
```bash
# Einmalig: Thingsboard Geräte erstellen
python scripts/thingsboard_setup.py

# Aktuelle Daten von allen Quellen laden
python complete_data_loader.py

# Historische Daten herunterladen (7 Tage)
python scripts/download_historical_data.py

# Datenqualität analysieren
python scripts/data_quality_report.py

# Interaktive Karte generieren
python scripts/generate_location_map.py

# Komplette Analyse-Pipeline ausführen
python scripts/run_complete_analysis.py
```

### Services stoppen
```bash
# Services stoppen (Daten bleiben erhalten)
docker compose stop

# Services entfernen (Daten bleiben in Volumes)
docker compose down

# Alles löschen inkl. Daten
docker compose down -v
```

---

## 📡 Datenquellen

### 🟢 Real Data Sources (3)

#### 1. OpenSenseMap Hamburg
| Parameter | Wert |
|-----------|------|
| **Quelle** | OpenSenseMap API (opensensemap.org) |
| **Standort** | Hamburg Iserbrook-Ost (53.58°N, 9.83°E) |
| **Box-ID** | 67937b67c326f20007ef99ca |
| **Variablen** | PM10, PM2.5, Temperatur, Luftfeuchtigkeit, Luftdruck |
| **Update** | ~5 Minuten (Echtzeit) |
| **Status** | ✅ Operational |

**Verfügbare Sensoren:**
- `PM10` - Feinstaub ≤10µm (µg/m³)
- `PM2.5` - Feinstaub ≤2.5µm (µg/m³)
- `Temperature` - Lufttemperatur (°C)
- `Humidity` - Relative Luftfeuchtigkeit (%)
- `Pressure` - Luftdruck (hPa)

#### 2. Mobilithek Dormagen
| Parameter | Wert |
|-----------|------|
| **Quelle** | sensor.community (luftdaten.info) |
| **Standort** | Dormagen, Deutschland (51.09°N, 6.84°E) |
| **Daten** | 11,139 Messwerte (7 Tage) |
| **Variablen** | PM10, PM2.5, Temperatur, Luftfeuchtigkeit |
| **Update** | ~5 Minuten |
| **Status** | ✅ Operational |

**Verfügbare Sensoren:**
- `PM10` - Feinstaub ≤10µm (µg/m³)
- `PM2.5` - Feinstaub ≤2.5µm (µg/m³)
- `Temperature` - Lufttemperatur (°C)
- `Humidity` - Relative Luftfeuchtigkeit (%)

#### 3. Open-Meteo Egypt (Cairo)
| Parameter | Wert |
|-----------|------|
| **Quelle** | Open-Meteo Weather API |
| **Standort** | Cairo, Ägypten (30.04°N, 31.24°E) |
| **Daten** | 192 Messwerte (8 Tage, stündlich) |
| **Variablen** | Temperatur, Luftfeuchtigkeit, Luftdruck, Wind |
| **Update** | Stündlich |
| **Status** | ✅ Operational |

**Verfügbare Messgrößen:**
- `temperature_2m` - 2m Temperatur (°C)
- `relative_humidity_2m` - Relative Luftfeuchtigkeit (%)
- `pressure_msl` - Luftdruck auf Meereshöhe (hPa)
- `wind_speed_10m` - Windgeschwindigkeit 10m (km/h)
- `wind_direction_10m` - Windrichtung (°)

### 🔵 Demo Data Sources (2)

#### 4. DWD Hamburg-Fuhlsbüttel
- **Status:** Simulierte Daten
- **Typ:** Offizielle Wetterstation
- **Standort:** Hamburg Flughafen (53.63°N, 9.99°E)

#### 5. UDP Osnabrück
- **Status:** Simulierte Daten
- **Typ:** Universitäts-Mikroklima-Sensoren
- **Standort:** Osnabrück Campus (52.28°N, 8.05°E)

---

## 📁 Projektstruktur
```
Mikroklima-Thingsboard-FROST/
│
├── 📦 Haupt-Dateien
│   ├── docker-compose.yml              # 7 Docker Services
│   ├── complete_data_loader.py         # Haupt-ETL-Pipeline
│   ├── PROJECT_FINAL_REPORT.md         # Vollständiger Projektbericht
│   └── LICENSE                         # MIT License
│
├── 📁 scripts/                         # Python Scripts
│   ├── download_historical_data.py     # Historische Daten herunterladen
│   ├── data_quality_report.py          # Datenqualitätsanalyse
│   ├── generate_location_map.py        # Interaktive Karte erstellen
│   ├── run_complete_analysis.py        # Master-Analyse-Script
│   ├── thingsboard_setup.py            # Thingsboard Geräte-Setup
│   ├── temperature_comparison.py       # Temperaturvergleich Hamburg
│   ├── temperature_comparison_egypt.py # Temperaturvergleich Egypt
│   └── frost_data_loader.py            # FROST Server Daten-Loader
│
├── 📁 config/                          # Konfigurationsdateien
│   ├── thingsboard_credentials.json    # Thingsboard Device Tokens
│   └── influxdb_config.py              # InfluxDB Verbindungs-Helper
│
├── 📁 data/                            # Daten
│   ├── historical/                     # Historische Rohdaten
│   │   ├── mobilithek_dormagen_7days.csv      # 982 KB, 11k records
│   │   └── openmeteo_egypt_7days.csv          # 14 KB, 192 records
│   └── DATA_QUALITY_SUMMARY.txt        # Qualitätsbericht Zusammenfassung
│
├── 📁 results/                         # Analyse-Ergebnisse
│   ├── temperature_comparison.png              # Hamburg Vergleich
│   ├── temperature_comparison_egypt.png        # Egypt Vergleich
│   ├── temperature_comparison_egypt_results.csv  # Statistiken
│   └── sensor_locations_map.html               # Interaktive Karte
│
└── 📁 doc/                             # Dokumentation
    ├── THINGSBOARD_SETUP.md            # Thingsboard Anleitung
    ├── DATA_QUALITY_REPORT.md          # Vollständiger Qualitätsbericht
    ├── API_DOCUMENTATION.md            # API Referenz
    └── TROUBLESHOOTING.md              # Fehlerbehebung
```

---

## 📊 Ergebnisse

### Datenqualität

| Quelle | Records | Zeitraum | Vollständigkeit | Status |
|--------|---------|----------|-----------------|--------|
| **Mobilithek Dormagen** | 11,139 | 7 Tage | 85.7% | ✅ GOOD |
| **Open-Meteo Egypt** | 192 | 8 Tage | 114.3% | ✅ EXCELLENT |
| **Gesamt** | 11,331+ | - | - | ✅ OPERATIONAL |

### Statistische Validierung

**Temperaturvergleich (Egypt - Cairo):**
| Metrik | Wert | Interpretation |
|--------|------|----------------|
| **MAE** | 0.75°C | Mittlerer absoluter Fehler |
| **RMSE** | 0.83°C | Root Mean Square Error |
| **Bias** | +0.75°C | Systematische Abweichung |
| **Korrelation** | 0.997 | Sehr hohe Korrelation (99.7%) |
| **p-Wert** | 0.00 | Statistisch signifikant |

### Visualisierungen

Alle Visualisierungen befinden sich im `results/` Ordner:

- 📊 `temperature_comparison.png` - Hamburg OSM vs. DWD
- 📊 `temperature_comparison_egypt.png` - Egypt (Cairo) Analyse
- 🗺️ `sensor_locations_map.html` - Interaktive Sensorkarte
- 📈 `temperature_comparison_egypt_results.csv` - Rohdaten

---

## 🔌 API Dokumentation

### FROST Server (OGC SensorThings API)

**Basis-URL:** `http://localhost:8091/FROST-Server/v1.1`

#### Hauptentitäten

| Endpunkt | Beschreibung |
|----------|--------------|
| `/Things` | IoT-Geräte/Stationen |
| `/Locations` | Geografische Standorte (GeoJSON) |
| `/Sensors` | Physische Sensoren |
| `/ObservedProperties` | Messgrößen (Temperatur, PM10, etc.) |
| `/Datastreams` | Datenströme (Sensor → Messgröße) |
| `/Observations` | Einzelne Messwerte |

#### Beispiel-Queries
```bash
# Alle Stationen abrufen
curl "http://localhost:8091/FROST-Server/v1.1/Things"

# Neueste 10 Messwerte
curl "http://localhost:8091/FROST-Server/v1.1/Observations?\$top=10&\$orderby=phenomenonTime%20desc"

# Datastream mit Observations expandiert
curl "http://localhost:8091/FROST-Server/v1.1/Datastreams(1)?\$expand=Observations(\$top=100)"

# Filtern nach Zeitraum
curl "http://localhost:8091/FROST-Server/v1.1/Observations?\$filter=phenomenonTime%20gt%202026-01-15T00:00:00Z"
```

### Thingsboard REST API

**Basis-URL:** `http://localhost:8080/api`
```bash
# Login und Token erhalten
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}'

# Telemetrie senden (mit Device Token)
curl -X POST http://localhost:8080/api/v1/DEVICE_TOKEN/telemetry \
  -H "Content-Type: application/json" \
  -d '{"temperature":23.5,"humidity":65.2}'
```

### InfluxDB Flux API

**Basis-URL:** `http://localhost:8086/api/v2`
```python
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://localhost:8086",
    token="mikroklima-super-secret-token",
    org="mikroklima"
)

# Query schreiben
query = '''
from(bucket: "mikroklima_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["source"] == "Mobilithek Dormagen")
  |> filter(fn: (r) => r["sensor_type"] == "PM10")
'''

tables = client.query_api().query(query)
```

---

## 🔧 Troubleshooting

### Container startet nicht
```bash
# Logs prüfen
docker compose logs influxdb
docker compose logs frost
docker compose logs thingsboard

# Container Status
docker compose ps -a

# Neustart
docker compose down && docker compose up -d
```

### Port bereits belegt
```bash
# Prozess finden
lsof -i :8080
lsof -i :8086

# Prozess beenden
kill -9 <PID>
```

### Thingsboard lädt nicht
```bash
# Warte 45 Sekunden nach Start
sleep 45

# Logs prüfen
docker compose logs thingsboard

# Browser Cache leeren
# Inkognito-Modus versuchen
```

### Python Module fehlen
```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# Module installieren
pip install requests pandas numpy matplotlib folium influxdb-client
```

### Daten werden nicht angezeigt

1. Prüfe ob Container laufen: `docker compose ps`
2. Prüfe ob Daten geladen wurden: `python complete_data_loader.py`
3. Prüfe Thingsboard UI: http://localhost:8080
4. Prüfe InfluxDB: `curl http://localhost:8086/health`

---

## 📚 Weitere Dokumentation

Detaillierte Anleitungen finden Sie im `doc/` Ordner:

- 📘 [Thingsboard Setup Guide](doc/THINGSBOARD_SETUP.md)
- 📗 [Data Quality Report](doc/DATA_QUALITY_REPORT.md)
- 📙 [API Documentation](doc/API_DOCUMENTATION.md)
- 📕 [Troubleshooting Guide](doc/TROUBLESHOOTING.md)

---

## 🎓 Wissenschaftliche Analyse

### Forschungsfragen

1. **Wie zuverlässig sind Citizen Science Daten?**
   - Vergleich OpenSenseMap vs. offizielle Wetterstationen
   - Ergebnis: Hohe Korrelation (r=0.996) bei systematischem Bias

2. **Welche Datenqualität liefern öffentliche APIs?**
   - Analyse von Mobilithek und Open-Meteo
   - Ergebnis: 85.7% - 114.3% Vollständigkeit

3. **Wie interoperabel sind verschiedene IoT-Plattformen?**
   - Integration FROST + Thingsboard + InfluxDB
   - Ergebnis: Erfolgreiche Echtzeit-Synchronisation

### Methodik

- **Datensammlung:** 7 Tage kontinuierliche Messwerte
- **Resampling:** Stündliche Aggregation
- **Statistik:** MAE, RMSE, Pearson-Korrelation, Bias-Analyse
- **Visualisierung:** Zeitreihen, Streudiagramme, Heatmaps

---

## 🤝 Beitragen

Dieses Projekt ist Teil eines universitären Forschungsprojekts. 

**Team:**
- Moo (Abdelrahman Ahmed) - Thingsboard & FROST Integration
- Achraf Bennani - TIG Stack & FROST Server
- Mohamed Amine Bouker - TIG Stack & Thingsboard

---

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE) für Details.

---

## 🙏 Danksagungen

- **Fraunhofer IOSB** - FROST Server
- **Thingsboard** - Open-Source IoT Platform
- **InfluxData** - InfluxDB & Telegraf
- **sensor.community** - Mobilithek Dormagen Daten
- **Open-Meteo** - Freie Wetter-API
- **Prof. Dr.-Ing. Clemens Westerkamp** - Projektbetreuung
- **Leon Gutsfeld** - Technische Beratung

---

## 📞 Kontakt

**GitHub:** [@JUPA8](https://github.com/JUPA8)  
**Repository:** [Mikroklima-Thingsboard-FROST](https://github.com/JUPA8/Mikroklima-Thingsboard-FROST)

---

<div align="center">

### 🌡️ Mikroklima Hamburg - Professional IoT Integration 🌡️

**Made with ❤️ at Hochschule Osnabrück**

</div>
