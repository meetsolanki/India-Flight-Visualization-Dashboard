# Aviation Tracking System

Python-based aviation tracking project using FlightRadarAPI, pandas, and Matplotlib.

## Install

```powershell
pip install -r requirements.txt
```

## Console Tracker

```powershell
python aviation_tracker.py
```

Menu options:

1. Show Airline Flights
2. Track Exact Flight
3. Exit Application

The airline search asks for an ADS-B airline callsign prefix directly, such as `IGO`, `AIC`, or `UAE`. Exact flight tracking asks for the full ADS-B style callsign, such as `IGO6507`, `AIC101`, or `UAE203`, and refreshes every 15 seconds until `CTRL + C` is pressed.

## India Visualization Dashboard

```powershell
python visualization_dashboard.py
```

By default, the dashboard shows all available flights returned for the India map area. To cap the number of flights:

```powershell
python visualization_dashboard.py --limit 150
```

After running the dashboard script, the terminal asks:

1. Show airline names and callsign codes
2. Show all plane details
3. Show one specific airline only
4. Track exact flight by callsign

Option 1 asks for a country name first. For example, enter `India` to show Indian airlines with their ICAO / ADS-B callsign codes, IATA codes, and radio callsigns.

For option 3, enter an airline name/code such as `IndiGo`, `Air India`, `IGO`, or `AIC`. The map and table then open with that airline filter applied.

For option 4, enter an exact ADS-B flight callsign such as `IGO6507`, `AIC101`, or `UAE203`. The dashboard tracks that exact flight on the map and in the table with a 10-second refresh interval.

The normal dashboard views refresh every 1 minute and focus on planes over India. It uses an India GeoJSON map, shows at least 100 aircraft when FlightRadar24 returns enough live flights, and displays full airline names wherever FlightRadar24 provides them.

Routes in the table use compact airport ICAO codes, such as `VAAH->VIDP`.

Hover over any plane symbol on the India map to see the flight number and airline above the aircraft.

Use the mouse wheel over the table to scroll through all available flights.

On the first run, the dashboard downloads and caches the India map as `india_map_cache.geojson`.
