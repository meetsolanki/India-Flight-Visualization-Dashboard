"""
India Flight Visualization Dashboard

Matplotlib dashboard for live FlightRadar24 data over India.
Normal dashboards refresh every minute; exact flight tracking refreshes every 10 seconds.
"""

from __future__ import annotations

# ============================================================
# Imports and configuration
# ============================================================

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Polygon

try:
    from FlightRadarAPI import FlightRadar24API
except ImportError as import_error:
    FlightRadar24API = None
    FLIGHTRADAR_IMPORT_ERROR = import_error
else:
    FLIGHTRADAR_IMPORT_ERROR = None


DEFAULT_REFRESH_SECONDS = 60
EXACT_TRACK_REFRESH_SECONDS = 10
DEFAULT_LIMIT = 0
MINIMUM_VISIBLE_FLIGHTS = 100
TABLE_VISIBLE_ROWS = 20
TABLE_SCROLL_STEP = 5
FILTERED_DETAILS_LIMIT = 100
HOVER_DISTANCE_PIXELS = 18
PLANE_MARKER = "\u2708"

# Approximate India airspace bounding box used by FlightRadarAPI.
# Format required by the API: north,south,west,east.
INDIA_NORTH = 37.6
INDIA_SOUTH = 6.5
INDIA_WEST = 68.1
INDIA_EAST = 97.4
INDIA_BOUNDS = f"{INDIA_NORTH},{INDIA_SOUTH},{INDIA_WEST},{INDIA_EAST}"
INDIA_GEOJSON_URL = (
    "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/india.geojson"
)
INDIA_MAP_CACHE = Path(__file__).with_name("india_map_cache.geojson")
AIRLINE_REFERENCE_URL = (
    "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"
)
AIRLINE_REFERENCE_CACHE = Path(__file__).with_name("airline_reference_cache.dat")

AIRLINE_NAME_OVERRIDES = {
    "6E": "IndiGo",
    "AI": "Air India",
    "AKJ": "Akasa Air",
    "AIC": "Air India",
    "AFR": "Air France",
    "ALK": "SriLankan Airlines",
    "AXB": "Air India Express",
    "BAW": "British Airways",
    "BBC": "Biman Bangladesh Airlines",
    "CPA": "Cathay Pacific",
    "DLH": "Lufthansa",
    "EK": "Emirates",
    "ETD": "Etihad Airways",
    "ETH": "Ethiopian Airlines",
    "FDX": "FedEx",
    "GOW": "Go First",
    "IGO": "IndiGo",
    "IX": "Air India Express",
    "KLM": "KLM Royal Dutch Airlines",
    "MAS": "Malaysia Airlines",
    "OMA": "Oman Air",
    "QP": "Akasa Air",
    "QTR": "Qatar Airways",
    "SEJ": "SpiceJet",
    "SG": "SpiceJet",
    "SIA": "Singapore Airlines",
    "SVA": "Saudia",
    "THA": "Thai Airways",
    "UAE": "Emirates",
    "UK": "Vistara",
    "UPS": "UPS Airlines",
    "VTI": "Vistara",
}

AIRLINE_REFERENCE_OVERRIDES = [
    {
        "Airline Name": "Air India",
        "Country": "India",
        "ICAO / ADS-B Callsign": "AIC",
        "IATA Code": "AI",
        "Radio Callsign": "AIR INDIA",
    },
    {
        "Airline Name": "IndiGo",
        "Country": "India",
        "ICAO / ADS-B Callsign": "IGO",
        "IATA Code": "6E",
        "Radio Callsign": "IFLY",
    },
    {
        "Airline Name": "Air India Express",
        "Country": "India",
        "ICAO / ADS-B Callsign": "AXB",
        "IATA Code": "IX",
        "Radio Callsign": "EXPRESS INDIA",
    },
    {
        "Airline Name": "SpiceJet",
        "Country": "India",
        "ICAO / ADS-B Callsign": "SEJ",
        "IATA Code": "SG",
        "Radio Callsign": "SPICEJET",
    },
    {
        "Airline Name": "Vistara",
        "Country": "India",
        "ICAO / ADS-B Callsign": "VTI",
        "IATA Code": "UK",
        "Radio Callsign": "VISTARA",
    },
    {
        "Airline Name": "Akasa Air",
        "Country": "India",
        "ICAO / ADS-B Callsign": "AKJ",
        "IATA Code": "QP",
        "Radio Callsign": "AKASA AIR",
    },
    {
        "Airline Name": "Alliance Air",
        "Country": "India",
        "ICAO / ADS-B Callsign": "LLR",
        "IATA Code": "9I",
        "Radio Callsign": "ALLIED",
    },
    {
        "Airline Name": "Blue Dart Aviation",
        "Country": "India",
        "ICAO / ADS-B Callsign": "BDA",
        "IATA Code": "BZ",
        "Radio Callsign": "BLUE DART",
    },
    {
        "Airline Name": "Star Air",
        "Country": "India",
        "ICAO / ADS-B Callsign": "SDG",
        "IATA Code": "S5",
        "Radio Callsign": "HISTAR",
    },
    {
        "Airline Name": "Emirates",
        "Country": "United Arab Emirates",
        "ICAO / ADS-B Callsign": "UAE",
        "IATA Code": "EK",
        "Radio Callsign": "EMIRATES",
    },
    {
        "Airline Name": "Etihad Airways",
        "Country": "United Arab Emirates",
        "ICAO / ADS-B Callsign": "ETD",
        "IATA Code": "EY",
        "Radio Callsign": "ETIHAD",
    },
    {
        "Airline Name": "Qatar Airways",
        "Country": "Qatar",
        "ICAO / ADS-B Callsign": "QTR",
        "IATA Code": "QR",
        "Radio Callsign": "QATARI",
    },
    {
        "Airline Name": "Singapore Airlines",
        "Country": "Singapore",
        "ICAO / ADS-B Callsign": "SIA",
        "IATA Code": "SQ",
        "Radio Callsign": "SINGAPORE",
    },
    {
        "Airline Name": "Biman Bangladesh Airlines",
        "Country": "Bangladesh",
        "ICAO / ADS-B Callsign": "BBC",
        "IATA Code": "BG",
        "Radio Callsign": "BANGLADESH",
    },
]

COUNTRY_ALIASES = {
    "AMERICA": "UNITEDSTATES",
    "UAE": "UNITEDARABEMIRATES",
    "UK": "UNITEDKINGDOM",
    "USA": "UNITEDSTATES",
}

_AIRLINE_LOOKUP_CACHE: dict[str, str] | None = None
_INDIA_POLYGON_CACHE: list[list[list[list[float]]]] | None = None


# ============================================================
# Map helpers
# ============================================================

def load_india_geojson() -> dict | None:
    """Load India boundary GeoJSON from cache or the public source."""
    if INDIA_MAP_CACHE.exists():
        try:
            return json.loads(INDIA_MAP_CACHE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    try:
        with urlopen(INDIA_GEOJSON_URL, timeout=20) as response:
            data = response.read().decode("utf-8")
        INDIA_MAP_CACHE.write_text(data, encoding="utf-8")
        return json.loads(data)
    except Exception:
        return None


def geometry_to_polygons(geometry: dict) -> list[list[list[list[float]]]]:
    """Convert GeoJSON geometry into polygon rings."""
    if not geometry:
        return []

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        return [coordinates]
    if geometry_type == "MultiPolygon":
        return coordinates
    if geometry_type == "GeometryCollection":
        polygons = []
        for child_geometry in geometry.get("geometries", []):
            polygons.extend(geometry_to_polygons(child_geometry))
        return polygons

    return []


def extract_geojson_polygons(geojson_data: dict | None) -> list[list[list[list[float]]]]:
    """Extract all polygon rings from an India GeoJSON document."""
    if not geojson_data:
        return []

    geojson_type = geojson_data.get("type")
    if geojson_type == "FeatureCollection":
        polygons = []
        for feature in geojson_data.get("features", []):
            polygons.extend(geometry_to_polygons(feature.get("geometry", {})))
        return polygons
    if geojson_type == "Feature":
        return geometry_to_polygons(geojson_data.get("geometry", {}))

    return geometry_to_polygons(geojson_data)


def load_india_polygons() -> list[list[list[list[float]]]]:
    """Load and cache India map polygons."""
    global _INDIA_POLYGON_CACHE

    if _INDIA_POLYGON_CACHE is None:
        _INDIA_POLYGON_CACHE = extract_geojson_polygons(load_india_geojson())

    return _INDIA_POLYGON_CACHE


def point_in_ring(longitude: float, latitude: float, ring: list[list[float]]) -> bool:
    """Return True if a point is inside one polygon ring."""
    inside = False
    if len(ring) < 3:
        return inside

    previous_longitude, previous_latitude = ring[-1][:2]
    for point in ring:
        current_longitude, current_latitude = point[:2]
        crosses_latitude = (current_latitude > latitude) != (previous_latitude > latitude)

        if crosses_latitude:
            slope_longitude = (
                (previous_longitude - current_longitude)
                * (latitude - current_latitude)
                / (previous_latitude - current_latitude)
                + current_longitude
            )
            if longitude < slope_longitude:
                inside = not inside

        previous_longitude, previous_latitude = current_longitude, current_latitude

    return inside


def point_in_polygon(longitude: float, latitude: float, polygon: list[list[list[float]]]) -> bool:
    """Return True if a point is inside a polygon and outside its holes."""
    if not polygon or not point_in_ring(longitude, latitude, polygon[0]):
        return False

    holes = polygon[1:]
    return not any(point_in_ring(longitude, latitude, hole) for hole in holes)


def point_in_india(longitude: float, latitude: float, polygons: list[list[list[list[float]]]]) -> bool:
    """Return True if a coordinate falls inside the India GeoJSON boundary."""
    if not polygons:
        return INDIA_SOUTH <= latitude <= INDIA_NORTH and INDIA_WEST <= longitude <= INDIA_EAST

    return any(point_in_polygon(longitude, latitude, polygon) for polygon in polygons)


def draw_india_boundary(axis: plt.Axes, polygons: list[list[list[list[float]]]]) -> None:
    """Draw the India GeoJSON boundary on a Matplotlib axis."""
    if not polygons:
        axis.text(
            0.5,
            0.08,
            "India map boundary unavailable; using coordinate view.",
            transform=axis.transAxes,
            ha="center",
            fontsize=9,
            color="#475569",
        )
        return

    for polygon in polygons:
        if not polygon:
            continue

        outer_ring = polygon[0]
        map_patch = Polygon(
            outer_ring,
            closed=True,
            facecolor="#dcfce7",
            edgecolor="#166534",
            linewidth=0.75,
            zorder=1,
        )
        axis.add_patch(map_patch)


# ============================================================
# FlightRadarAPI helpers
# ============================================================

def require_flight_radar_api() -> None:
    """Stop with a helpful message if FlightRadarAPI is not installed."""
    if FlightRadar24API is None:
        raise RuntimeError(
            "FlightRadarAPI is not installed. Run: pip install -r requirements.txt"
        ) from FLIGHTRADAR_IMPORT_ERROR


def normalize_text(value: object) -> str:
    """Return a clean display string."""
    if value is None:
        return ""
    return str(value).strip()


def normalize_callsign(value: object) -> str:
    """Normalize ADS-B callsigns without airline code conversion."""
    return normalize_text(value).upper().replace(" ", "")


def get_flight_callsign(flight: object) -> str:
    """Return an ADS-B callsign or flight number fallback."""
    callsign = normalize_callsign(getattr(flight, "callsign", None))
    if callsign:
        return callsign
    return normalize_callsign(getattr(flight, "number", None))


def get_callsign_prefix(flight: object) -> str:
    """Return the alphabetic ADS-B airline prefix from the callsign."""
    callsign = get_flight_callsign(flight)
    prefix = []

    for character in callsign:
        if character.isalpha():
            prefix.append(character)
        else:
            break

    return "".join(prefix)


def numeric_value(value: object) -> float | None:
    """Convert API values to numbers when possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def display_value(value: object, default: str = "N/A") -> str:
    """Return a readable table value."""
    text = normalize_text(value)
    return text if text else default


def fetch_india_flights(api: FlightRadar24API) -> list:
    """Fetch flights inside India's approximate FlightRadar24 bounds."""
    return api.get_flights(bounds=INDIA_BOUNDS)


def is_inside_india_area(flight: object, polygons: list[list[list[list[float]]]]) -> bool:
    """Confirm the flight coordinates are inside India's map boundary."""
    latitude = numeric_value(getattr(flight, "latitude", None))
    longitude = numeric_value(getattr(flight, "longitude", None))
    if latitude is None or longitude is None:
        return False
    return point_in_india(longitude, latitude, polygons)


def try_add_flight_details(api: FlightRadar24API, flight: object) -> None:
    """
    Add route/airline details when FlightRadar24 provides them.

    The dashboard still works if this endpoint is slow or unavailable.
    """
    try:
        details = api.get_flight_details(flight)
        flight.set_flight_details(details)
    except Exception:
        return


def load_airline_lookup(api: FlightRadar24API) -> dict[str, str]:
    """Build a code-to-full-airline-name lookup from FlightRadar24."""
    global _AIRLINE_LOOKUP_CACHE

    if _AIRLINE_LOOKUP_CACHE is not None:
        return _AIRLINE_LOOKUP_CACHE

    lookup = dict(AIRLINE_NAME_OVERRIDES)
    try:
        for airline in api.get_airlines():
            airline_name = normalize_text(airline.get("Name"))
            if not airline_name:
                continue

            for code_key in ("ICAO", "IATA"):
                code = normalize_callsign(airline.get(code_key))
                if code:
                    lookup[code] = airline_name
    except Exception:
        pass

    _AIRLINE_LOOKUP_CACHE = lookup
    return lookup


def airline_for_flight(flight: object, airline_lookup: dict[str, str]) -> str:
    """Return a readable airline name for a flight."""
    airline_name = normalize_text(getattr(flight, "airline_name", None))
    airline_short_name = normalize_text(getattr(flight, "airline_short_name", None))
    airline_icao = normalize_text(getattr(flight, "airline_icao", None))
    airline_iata = normalize_text(getattr(flight, "airline_iata", None))

    if airline_name and normalize_callsign(airline_name) not in airline_lookup:
        return airline_name

    for code in (
        airline_icao,
        airline_iata,
        get_callsign_prefix(flight),
        normalize_callsign(getattr(flight, "number", None))[:2],
    ):
        normalized_code = normalize_callsign(code)
        if normalized_code in airline_lookup:
            return airline_lookup[normalized_code]

    if airline_short_name and normalize_callsign(airline_short_name) not in airline_lookup:
        return airline_short_name

    return display_value(airline_icao or airline_iata or get_callsign_prefix(flight))


def airline_filter_candidates(flight: object, airline_lookup: dict[str, str]) -> list[str]:
    """Return searchable airline values for one flight."""
    candidates = [
        airline_for_flight(flight, airline_lookup),
        getattr(flight, "airline_name", None),
        getattr(flight, "airline_short_name", None),
        getattr(flight, "airline_icao", None),
        getattr(flight, "airline_iata", None),
        get_callsign_prefix(flight),
        get_flight_callsign(flight),
        normalize_callsign(getattr(flight, "number", None))[:2],
    ]
    return [normalize_text(candidate) for candidate in candidates if normalize_text(candidate)]


def flight_matches_airline_filter(
    flight: object,
    airline_lookup: dict[str, str],
    airline_filter: str,
) -> bool:
    """Match a flight against an airline name, airline code, or callsign prefix."""
    normalized_filter = normalize_callsign(airline_filter)
    if not normalized_filter:
        return True

    for candidate in airline_filter_candidates(flight, airline_lookup):
        normalized_candidate = normalize_callsign(candidate)
        if not normalized_candidate:
            continue
        if normalized_candidate == normalized_filter:
            return True
        if normalized_candidate.startswith(normalized_filter):
            return True
        if normalized_filter.startswith(normalized_candidate) and len(normalized_candidate) >= 2:
            return True
        if len(normalized_filter) >= 3 and normalized_filter in normalized_candidate:
            return True

    return False


def flight_matches_exact_callsign(flight: object, exact_callsign: str) -> bool:
    """Return True when a flight exactly matches the entered ADS-B callsign."""
    normalized_exact = normalize_callsign(exact_callsign)
    if not normalized_exact:
        return True

    return get_flight_callsign(flight) == normalized_exact


def route_point(name: object, iata: object, icao: object) -> str:
    """Build one compact airport label using real airport codes."""
    icao_code = normalize_callsign(icao)
    iata_code = normalize_callsign(iata)
    airport_name = normalize_text(name)

    if icao_code:
        return icao_code
    if iata_code:
        return iata_code
    if airport_name:
        return shorten_text(airport_name, 10).upper()
    return "UNKNOWN"


def route_for_flight(flight: object) -> str:
    """Return where the flight is travelling from and to."""
    origin = route_point(
        getattr(flight, "origin_airport_name", None),
        getattr(flight, "origin_airport_iata", None),
        getattr(flight, "origin_airport_icao", None),
    )
    destination = route_point(
        getattr(flight, "destination_airport_name", None),
        getattr(flight, "destination_airport_iata", None),
        getattr(flight, "destination_airport_icao", None),
    )
    return f"{origin}->{destination}"


def flight_row(flight: object, airline_lookup: dict[str, str]) -> dict:
    """Convert one Flight object into a dashboard row."""
    altitude = numeric_value(getattr(flight, "altitude", None))
    speed = numeric_value(getattr(flight, "ground_speed", None))
    latitude = numeric_value(getattr(flight, "latitude", None))
    longitude = numeric_value(getattr(flight, "longitude", None))
    heading = numeric_value(getattr(flight, "heading", None))

    return {
        "Flight": display_value(get_flight_callsign(flight)),
        "Airline": airline_for_flight(flight, airline_lookup),
        "Aircraft": display_value(getattr(flight, "aircraft_code", None)),
        "Travelling": route_for_flight(flight),
        "Altitude": int(altitude) if altitude is not None else "N/A",
        "Speed": int(speed) if speed is not None else "N/A",
        "Latitude": round(latitude, 3) if latitude is not None else "N/A",
        "Longitude": round(longitude, 3) if longitude is not None else "N/A",
        "Heading": heading if heading is not None else 0,
    }


def build_india_dataframe(
    api: FlightRadar24API,
    limit: int | None,
    airline_filter: str,
    exact_callsign: str,
) -> tuple[pd.DataFrame, int, int]:
    """Fetch India flights, enrich visible rows, and return dashboard data."""
    india_polygons = load_india_polygons()
    airline_lookup = load_airline_lookup(api)
    all_flights = fetch_india_flights(api)
    india_flights = [
        flight
        for flight in all_flights
        if is_inside_india_area(flight, india_polygons)
    ]

    normalized_exact = normalize_callsign(exact_callsign)
    flights = list(india_flights)

    # If the exact polygon gives fewer than 100 aircraft, fill from the India
    # map area so the dashboard still has enough live planes to inspect.
    if not normalized_exact and len(flights) < MINIMUM_VISIBLE_FLIGHTS:
        india_flight_ids = {flight.id for flight in india_flights}
        nearby_flights = [
            flight
            for flight in all_flights
            if flight.id not in india_flight_ids
        ]
        flights.extend(nearby_flights[: MINIMUM_VISIBLE_FLIGHTS - len(flights)])

    if normalized_exact:
        filtered_india_count = sum(
            1
            for flight in india_flights
            if flight_matches_exact_callsign(flight, normalized_exact)
        )
        flights = [
            flight
            for flight in flights
            if flight_matches_exact_callsign(flight, normalized_exact)
        ]
    else:
        filtered_india_count = sum(
            1
            for flight in india_flights
            if flight_matches_airline_filter(flight, airline_lookup, airline_filter)
        )
        flights = [
            flight
            for flight in flights
            if flight_matches_airline_filter(flight, airline_lookup, airline_filter)
        ]

    flights.sort(
        key=lambda flight: numeric_value(getattr(flight, "altitude", None)) or -1,
        reverse=True,
    )

    if limit is None:
        visible_flights = flights
    else:
        visible_flights = flights[:limit]

    details_limit = (
        FILTERED_DETAILS_LIMIT
        if airline_filter.strip() or normalized_exact
        else TABLE_VISIBLE_ROWS
    )
    for flight in visible_flights[:details_limit]:
        try_add_flight_details(api, flight)

    dataframe = pd.DataFrame([flight_row(flight, airline_lookup) for flight in visible_flights])
    return dataframe, filtered_india_count, len(flights)


# ============================================================
# Visualization helpers
# ============================================================

def prepare_axis(axis: plt.Axes) -> None:
    """Reset an axis for dashboard drawing."""
    axis.clear()
    axis.set_facecolor("#f8fafc")


def draw_status(fig: plt.Figure, axes: list[plt.Axes], message: str) -> None:
    """Show a readable status message."""
    for axis in axes:
        prepare_axis(axis)
        axis.axis("off")
    axes[0].text(0.5, 0.5, message, ha="center", va="center", fontsize=14)
    fig.suptitle("Planes Over India", fontsize=15, fontweight="bold")


def draw_position_map(
    axis: plt.Axes,
    dataframe: pd.DataFrame,
    exact_india_count: int,
    displayable_count: int,
) -> list[dict]:
    """Draw India map with plane symbols for live flights."""
    axis.set_title("India Map With Live Plane Positions", fontsize=12, fontweight="bold")
    axis.set_facecolor("#e0f2fe")
    axis.set_xlim(INDIA_WEST, INDIA_EAST)
    axis.set_ylim(INDIA_SOUTH, INDIA_NORTH)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.grid(False)
    draw_india_boundary(axis, load_india_polygons())

    numeric_data = dataframe.copy()
    numeric_data["Latitude"] = pd.to_numeric(numeric_data["Latitude"], errors="coerce")
    numeric_data["Longitude"] = pd.to_numeric(numeric_data["Longitude"], errors="coerce")
    numeric_data["Heading"] = pd.to_numeric(numeric_data["Heading"], errors="coerce").fillna(0)
    numeric_data = numeric_data.dropna(subset=["Latitude", "Longitude"])

    if numeric_data.empty:
        axis.text(0.5, 0.5, "No coordinates available", transform=axis.transAxes, ha="center")
        return []

    plane_points = []
    for _, row in numeric_data.iterrows():
        axis.text(
            row["Longitude"],
            row["Latitude"],
            PLANE_MARKER,
            ha="center",
            va="center",
            fontsize=13,
            color="#dc2626",
            rotation=row["Heading"],
            zorder=4,
        )
        plane_points.append(
            {
                "longitude": float(row["Longitude"]),
                "latitude": float(row["Latitude"]),
                "label": f"{display_value(row['Flight'])}  |  {display_value(row['Airline'])}",
            }
        )

    axis.text(
        0.02,
        0.98,
        (
            f"Inside India boundary: {exact_india_count}\n"
            f"Planes shown on map: {len(dataframe)}\n"
            f"Available in map area: {displayable_count}"
        ),
        transform=axis.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1"},
    )
    return plane_points


def shorten_text(value: object, max_length: int) -> str:
    """Shorten long table text so the dashboard stays readable."""
    text = display_value(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def clamp_table_start(start_index: int, total_rows: int) -> int:
    """Keep the table scroll position inside the available rows."""
    max_start = max(total_rows - TABLE_VISIBLE_ROWS, 0)
    return max(0, min(start_index, max_start))


def draw_flight_table(axis: plt.Axes, dataframe: pd.DataFrame, start_index: int) -> None:
    """Draw a scrollable table window backed by all available flights."""
    axis.axis("off")

    total_rows = len(dataframe)
    start_index = clamp_table_start(start_index, total_rows)
    end_index = min(start_index + TABLE_VISIBLE_ROWS, total_rows)
    axis.set_title(
        f"Flights Over India | Showing {start_index + 1}-{end_index} of {total_rows}",
        fontsize=12,
        fontweight="bold",
    )

    table_data = dataframe.iloc[start_index:end_index].copy()
    if table_data.empty:
        axis.text(0.5, 0.5, "No live flights found over India.", ha="center", va="center")
        return

    table_data["Airline"] = table_data["Airline"].map(lambda value: shorten_text(value, 24))
    table_data["Travelling"] = table_data["Travelling"].map(lambda value: shorten_text(value, 38))

    columns = ["Flight", "Airline", "Aircraft", "Travelling", "Altitude", "Speed"]
    table = axis.table(
        cellText=table_data[columns].values,
        colLabels=columns,
        cellLoc="left",
        colLoc="left",
        loc="center",
        colWidths=[0.1, 0.22, 0.1, 0.36, 0.11, 0.11],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.4)
    table.scale(1, 1.35)

    for (row, _column), cell in table.get_celld().items():
        cell.set_edgecolor("#d1d5db")
        if row == 0:
            cell.set_facecolor("#1f2937")
            cell.set_text_props(color="white", weight="bold")
        else:
            cell.set_facecolor("#ffffff" if row % 2 else "#f1f5f9")

    if total_rows > TABLE_VISIBLE_ROWS:
        axis.text(
            0.5,
            0.02,
            "Use mouse wheel over this table to scroll all available flights.",
            transform=axis.transAxes,
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#475569",
        )


def draw_dashboard(
    api: FlightRadar24API,
    limit: int | None,
    initial_airline_filter: str,
    initial_exact_callsign: str,
    refresh_seconds: int,
) -> None:
    """Open a Matplotlib dashboard and refresh it on the selected interval."""
    fig, axes_grid = plt.subplots(
        1,
        2,
        figsize=(16, 8.5),
        gridspec_kw={"width_ratios": [0.95, 1.65]},
    )
    axes = list(axes_grid.flatten())
    fig.subplots_adjust(left=0.04, right=0.98, bottom=0.06, top=0.88, wspace=0.12)
    hover_points = []
    hover_annotation = None
    latest_dataframe = pd.DataFrame()
    table_start_index = 0
    current_airline_filter = normalize_text(initial_airline_filter)
    current_exact_callsign = normalize_callsign(initial_exact_callsign)

    def hide_hover_annotation() -> None:
        if hover_annotation is not None and hover_annotation.get_visible():
            hover_annotation.set_visible(False)
            fig.canvas.draw_idle()

    def on_hover(event) -> None:
        if event.inaxes != axes[0] or event.x is None or event.y is None:
            hide_hover_annotation()
            return

        if hover_annotation is None or not hover_points:
            return

        nearest_point = None
        nearest_distance = HOVER_DISTANCE_PIXELS
        for point in hover_points:
            plane_x, plane_y = axes[0].transData.transform(
                (point["longitude"], point["latitude"])
            )
            distance = ((plane_x - event.x) ** 2 + (plane_y - event.y) ** 2) ** 0.5
            if distance <= nearest_distance:
                nearest_point = point
                nearest_distance = distance

        if nearest_point is None:
            hide_hover_annotation()
            return

        hover_annotation.xy = (nearest_point["longitude"], nearest_point["latitude"])
        hover_annotation.set_text(nearest_point["label"])
        hover_annotation.set_visible(True)
        fig.canvas.draw_idle()

    def on_table_scroll(event) -> None:
        nonlocal table_start_index

        if event.inaxes != axes[1] or latest_dataframe.empty:
            return

        if event.button == "down":
            table_start_index += TABLE_SCROLL_STEP
        else:
            table_start_index -= TABLE_SCROLL_STEP

        table_start_index = clamp_table_start(table_start_index, len(latest_dataframe))
        prepare_axis(axes[1])
        draw_flight_table(axes[1], latest_dataframe, table_start_index)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    fig.canvas.mpl_connect("scroll_event", on_table_scroll)

    def update(_frame: int) -> None:
        nonlocal hover_points, hover_annotation, latest_dataframe, table_start_index

        try:
            dataframe, exact_india_count, displayable_count = build_india_dataframe(
                api,
                limit,
                current_airline_filter,
                current_exact_callsign,
            )
        except Exception as error:
            hover_points = []
            hover_annotation = None
            latest_dataframe = pd.DataFrame()
            table_start_index = 0
            draw_status(fig, axes, f"Unable to refresh FlightRadar24 India data:\n{error}")
            return

        if dataframe.empty:
            hover_points = []
            hover_annotation = None
            latest_dataframe = pd.DataFrame()
            table_start_index = 0
            empty_filter_text = ""
            if current_exact_callsign:
                empty_filter_text = f" for exact callsign: {current_exact_callsign}"
            elif current_airline_filter:
                empty_filter_text = f" for airline filter: {current_airline_filter}"
            draw_status(fig, axes, f"No live flights found over India{empty_filter_text}.")
            return

        latest_dataframe = dataframe
        table_start_index = clamp_table_start(table_start_index, len(latest_dataframe))

        for axis in axes:
            prepare_axis(axis)

        hover_points = draw_position_map(
            axes[0],
            dataframe,
            exact_india_count,
            displayable_count,
        )
        hover_annotation = axes[0].annotate(
            "",
            xy=(0, 0),
            xytext=(0, 22),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#111827",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#ffffff",
                "edgecolor": "#334155",
                "alpha": 0.96,
            },
            arrowprops={"arrowstyle": "->", "color": "#334155", "linewidth": 0.8},
            zorder=10,
        )
        hover_annotation.set_visible(False)
        draw_flight_table(axes[1], latest_dataframe, table_start_index)

        last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if current_exact_callsign:
            filter_text = f"Exact flight {current_exact_callsign}"
        elif current_airline_filter:
            filter_text = current_airline_filter
        else:
            filter_text = "All airlines"
        fig.suptitle(
            f"Planes Over India | Filter: {filter_text} | "
            f"Last refresh: {last_refresh} | Auto-refresh: {refresh_seconds} seconds",
            fontsize=15,
            fontweight="bold",
        )

    update(0)
    animation = FuncAnimation(
        fig,
        update,
        interval=refresh_seconds * 1000,
        cache_frame_data=False,
    )
    fig._india_dashboard_animation = animation
    plt.show()


# ============================================================
# Application entry point
# ============================================================

def print_terminal_menu() -> None:
    """Print the dashboard startup menu."""
    print("=" * 72)
    print("INDIA FLIGHT VISUALIZATION DASHBOARD")
    print("=" * 72)
    print("1. Show airline names and callsign codes")
    print("2. Show all plane details")
    print("3. Show one specific airline only")
    print("4. Track exact flight by callsign")
    print("-" * 72)


def clean_airline_field(value: object) -> str:
    """Clean OpenFlights/FlightRadar airline fields."""
    text = normalize_text(value)
    if text in {"", "\\N", "N/A", "None"}:
        return ""
    return text


def normalize_country(value: object) -> str:
    """Normalize country names for filtering."""
    normalized = "".join(
        character
        for character in normalize_text(value).upper()
        if character.isalnum()
    )
    return COUNTRY_ALIASES.get(normalized, normalized)


def country_matches(row_country: object, country_filter: str) -> bool:
    """Return True when an airline row belongs to the requested country."""
    normalized_filter = normalize_country(country_filter)
    if not normalized_filter:
        return True

    normalized_country = normalize_country(row_country)
    if not normalized_country:
        return False

    return (
        normalized_country == normalized_filter
        or normalized_country.startswith(normalized_filter)
        or normalized_filter in normalized_country
    )


def load_openflight_airline_rows() -> list[dict]:
    """Load country-aware airline reference rows from a cached public dataset."""
    if AIRLINE_REFERENCE_CACHE.exists():
        try:
            data = AIRLINE_REFERENCE_CACHE.read_text(encoding="utf-8")
        except OSError:
            data = ""
    else:
        try:
            with urlopen(AIRLINE_REFERENCE_URL, timeout=20) as response:
                data = response.read().decode("utf-8")
            AIRLINE_REFERENCE_CACHE.write_text(data, encoding="utf-8")
        except Exception:
            data = ""

    rows = []
    for fields in csv.reader(data.splitlines()):
        if len(fields) < 8:
            continue

        airline_name = clean_airline_field(fields[1])
        iata_code = normalize_callsign(clean_airline_field(fields[3]))
        icao_code = normalize_callsign(clean_airline_field(fields[4]))
        radio_callsign = clean_airline_field(fields[5]).upper()
        country = clean_airline_field(fields[6])
        active = clean_airline_field(fields[7]).upper()

        if not airline_name or active == "N":
            continue

        rows.append(
            {
                "Airline Name": airline_name,
                "Country": display_value(country),
                "ICAO / ADS-B Callsign": display_value(icao_code),
                "IATA Code": display_value(iata_code),
                "Radio Callsign": display_value(radio_callsign),
            }
        )

    return rows


def airline_reference_rows(api: FlightRadar24API, country_filter: str) -> list[dict]:
    """Return country-filtered airline names with ICAO/ADS-B and IATA codes."""
    rows = []
    seen_rows = set()

    for row in load_openflight_airline_rows() + AIRLINE_REFERENCE_OVERRIDES:
        if not country_matches(row.get("Country"), country_filter):
            continue

        row_key = (
            row["Airline Name"],
            row["Country"],
            row["ICAO / ADS-B Callsign"],
            row["IATA Code"],
        )
        if row_key in seen_rows:
            continue

        seen_rows.add(row_key)
        rows.append(row)

    try:
        airlines = api.get_airlines()
    except Exception:
        airlines = []

    for airline in airlines:
        airline_name = display_value(airline.get("Name"))
        icao_code = normalize_callsign(airline.get("ICAO"))
        iata_code = normalize_callsign(airline.get("IATA") or airline.get("Code"))

        country = ""
        for override in AIRLINE_REFERENCE_OVERRIDES:
            override_codes = {
                normalize_callsign(override["ICAO / ADS-B Callsign"]),
                normalize_callsign(override["IATA Code"]),
            }
            if icao_code in override_codes or iata_code in override_codes:
                country = override["Country"]
                break

        if country_filter and not country_matches(country, country_filter):
            continue

        row_key = (airline_name, display_value(country), icao_code, iata_code)

        if row_key in seen_rows:
            continue

        seen_rows.add(row_key)
        rows.append(
            {
                "Airline Name": airline_name,
                "Country": display_value(country),
                "ICAO / ADS-B Callsign": display_value(icao_code),
                "IATA Code": display_value(iata_code),
                "Radio Callsign": "N/A",
            }
        )

    rows.sort(
        key=lambda row: (
            row["Country"],
            row["Airline Name"],
            row["ICAO / ADS-B Callsign"],
        )
    )
    return rows


def show_airline_reference(api: FlightRadar24API) -> None:
    """Display airline names and their callsign codes in the terminal."""
    country_filter = input(
        "Enter country name for airline list (example: India, UAE, United States). "
        "Leave blank for all: "
    ).strip()
    print("\nFetching airline name and callsign information...\n")
    rows = airline_reference_rows(api, country_filter)

    if not rows:
        if country_filter:
            print(f"No airline information found for country: {country_filter}")
        else:
            print("Unable to fetch airline information right now.")
        input("\nPress Enter to return to the menu...")
        return

    dataframe = pd.DataFrame(rows)
    with pd.option_context(
        "display.max_rows",
        None,
        "display.max_columns",
        None,
        "display.width",
        160,
    ):
        print(dataframe.to_string(index=False))

    print(f"\nTotal airlines shown: {len(rows)}")
    if country_filter:
        print(f"Country filter: {country_filter}")
    print("Use the ICAO / ADS-B callsign code for filters like IGO, AIC, UAE, ETD.")
    input("\nPress Enter to return to the menu...")


def parse_args() -> argparse.Namespace:
    """Parse dashboard settings."""
    parser = argparse.ArgumentParser(
        description="Live FlightRadarAPI dashboard for planes currently over India."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Optional maximum flights to show. Default 0 shows all available flights.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the India-focused visualization dashboard."""
    require_flight_radar_api()
    args = parse_args()
    limit = None if args.limit <= 0 else max(MINIMUM_VISIBLE_FLIGHTS, args.limit)
    api = FlightRadar24API()

    while True:
        print_terminal_menu()
        try:
            choice = input("Select option (1-4): ").strip()
        except EOFError:
            return

        if choice == "1":
            show_airline_reference(api)
        elif choice == "2":
            draw_dashboard(api, limit, "", "", DEFAULT_REFRESH_SECONDS)
        elif choice == "3":
            airline_filter = input(
                "Enter airline name/code (example: IndiGo, Air India, IGO, AIC): "
            ).strip()
            if not airline_filter:
                print("Airline name/code cannot be blank.\n")
                continue
            draw_dashboard(api, limit, airline_filter, "", DEFAULT_REFRESH_SECONDS)
        elif choice == "4":
            exact_callsign = input(
                "Enter exact ADS-B flight callsign (example: IGO6507, AIC101, UAE203): "
            ).strip()
            if not exact_callsign:
                print("Exact flight callsign cannot be blank.\n")
                continue
            draw_dashboard(api, limit, "", exact_callsign, EXACT_TRACK_REFRESH_SECONDS)
        else:
            print("Invalid option. Please enter 1, 2, 3, or 4.\n")


if __name__ == "__main__":
    main()
