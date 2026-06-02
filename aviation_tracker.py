"""
Aviation Tracking System

Menu-driven console dashboard powered by FlightRadarAPI.
"""

from __future__ import annotations

# ============================================================
# Imports and configuration
# ============================================================

import os
import sys
import time
from datetime import datetime
from typing import Iterable, Optional

import pandas as pd

try:
    from FlightRadarAPI import FlightRadar24API
except ImportError as import_error:
    FlightRadar24API = None
    FLIGHTRADAR_IMPORT_ERROR = import_error
else:
    FLIGHTRADAR_IMPORT_ERROR = None


TRACK_REFRESH_SECONDS = 15


# ============================================================
# Console helpers
# ============================================================

def clear_screen() -> None:
    """Clear the Windows console screen."""
    os.system("cls")


def print_header(title: str) -> None:
    """Print a clean dashboard header."""
    print("=" * 72)
    print(" " * 20 + "LIVE AVIATION TRACKING SYSTEM")
    print("=" * 72)
    print(f"{title}")
    print("-" * 72)


def pause() -> None:
    """Pause until the user presses Enter."""
    input("\nPress Enter to return to the main menu...")


def require_flight_radar_api() -> None:
    """Stop with a helpful message if FlightRadarAPI is not installed."""
    if FlightRadar24API is None:
        raise RuntimeError(
            "FlightRadarAPI is not installed. Run: pip install -r requirements.txt"
        ) from FLIGHTRADAR_IMPORT_ERROR


# ============================================================
# Flight data helpers
# ============================================================

def normalize_callsign(value: object) -> str:
    """Normalize ADS-B callsigns without converting airline codes."""
    if value is None:
        return ""
    return str(value).strip().upper().replace(" ", "")


def display_value(value: object, default: str = "N/A") -> object:
    """Return a printable value for tables."""
    if value is None or value == "":
        return default
    return value


def get_flight_callsign(flight: object) -> str:
    """Return the ADS-B callsign if present; otherwise fall back to number."""
    callsign = normalize_callsign(getattr(flight, "callsign", None))
    if callsign:
        return callsign
    return normalize_callsign(getattr(flight, "number", None))


def fetch_live_flights(api: FlightRadar24API) -> list:
    """Fetch live flights from FlightRadar24."""
    return api.get_flights()


def filter_by_airline_callsign(flights: Iterable[object], airline_code: str) -> list:
    """Filter flights whose ADS-B callsign starts with the entered airline code."""
    normalized_code = normalize_callsign(airline_code)
    return [
        flight
        for flight in flights
        if get_flight_callsign(flight).startswith(normalized_code)
    ]


def find_exact_callsign(flights: Iterable[object], exact_callsign: str) -> Optional[object]:
    """Find one live flight by exact ADS-B callsign."""
    normalized_exact = normalize_callsign(exact_callsign)
    for flight in flights:
        if get_flight_callsign(flight) == normalized_exact:
            return flight
    return None


def try_add_flight_details(api: FlightRadar24API, flight: object) -> None:
    """
    Enrich a flight with details when available.

    Tracking still works if the details endpoint is temporarily unavailable.
    """
    try:
        details = api.get_flight_details(flight)
        flight.set_flight_details(details)
    except Exception:
        return


# ============================================================
# Table builders
# ============================================================

def airline_table_record(flight: object) -> dict:
    """Build one table row for airline search results."""
    return {
        "Flight Number": display_value(get_flight_callsign(flight)),
        "Aircraft Type": display_value(getattr(flight, "aircraft_code", None)),
        "Airline ICAO Code": display_value(getattr(flight, "airline_icao", None)),
        "Altitude": display_value(getattr(flight, "altitude", None)),
        "Speed": display_value(getattr(flight, "ground_speed", None)),
    }


def tracking_table_record(flight: object) -> dict:
    """Build one table row for exact flight tracking."""
    airline_name = getattr(flight, "airline_name", None)
    airline_icao = getattr(flight, "airline_icao", None)
    return {
        "Flight Number": display_value(get_flight_callsign(flight)),
        "Airline": display_value(airline_name or airline_icao),
        "Aircraft Type": display_value(getattr(flight, "aircraft_code", None)),
        "Altitude": display_value(getattr(flight, "altitude", None)),
        "Speed": display_value(getattr(flight, "ground_speed", None)),
        "Latitude": display_value(getattr(flight, "latitude", None)),
        "Longitude": display_value(getattr(flight, "longitude", None)),
    }


def print_dataframe(records: list[dict]) -> None:
    """Display records in pandas DataFrame table format."""
    if not records:
        print("No matching live flights found.")
        return

    dataframe = pd.DataFrame(records)
    with pd.option_context(
        "display.max_rows",
        None,
        "display.max_columns",
        None,
        "display.width",
        140,
    ):
        print(dataframe.to_string(index=False))


# ============================================================
# Dashboard options
# ============================================================

def show_airline_flights(api: FlightRadar24API) -> None:
    """Menu option 1: show all flights for an entered ADS-B airline callsign code."""
    clear_screen()
    print_header("SHOW AIRLINE FLIGHTS")

    airline_code = input("Enter ADS-B airline callsign code (example: IGO, AIC, UAE): ")
    airline_code = normalize_callsign(airline_code)

    if not airline_code:
        print("\nAirline callsign code cannot be blank.")
        pause()
        return

    try:
        print(f"\nFetching live flights for callsign prefix: {airline_code}")
        flights = fetch_live_flights(api)
        matched_flights = filter_by_airline_callsign(flights, airline_code)
        records = [airline_table_record(flight) for flight in matched_flights]

        print(f"\nTotal matching flights: {len(records)}\n")
        print_dataframe(records)
    except Exception as error:
        print(f"\nUnable to fetch airline flights: {error}")

    pause()


def track_exact_flight(api: FlightRadar24API) -> None:
    """Menu option 2: continuously track one exact ADS-B callsign."""
    clear_screen()
    print_header("TRACK EXACT FLIGHT")

    exact_callsign = input(
        "Enter exact ADS-B flight callsign (example: IGO6507, AIC101, UAE203): "
    )
    exact_callsign = normalize_callsign(exact_callsign)

    if not exact_callsign:
        print("\nFlight callsign cannot be blank.")
        pause()
        return

    try:
        while True:
            clear_screen()
            print_header(f"TRACKING EXACT FLIGHT: {exact_callsign}")
            print(f"Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Refresh interval: {TRACK_REFRESH_SECONDS} seconds")
            print("Press CTRL + C to stop live tracking.")
            print("-" * 72)

            try:
                flights = fetch_live_flights(api)
                target_flight = find_exact_callsign(flights, exact_callsign)

                if target_flight is None:
                    print(f"No live flight found for exact callsign: {exact_callsign}")
                else:
                    try_add_flight_details(api, target_flight)
                    print_dataframe([tracking_table_record(target_flight)])

            except Exception as error:
                print(f"Runtime/API error while tracking flight: {error}")

            time.sleep(TRACK_REFRESH_SECONDS)

    except KeyboardInterrupt:
        print("\n\nLive tracking stopped. Returning to the main menu...")
        time.sleep(2)


def print_main_menu() -> None:
    """Print the requested three-option console dashboard."""
    clear_screen()
    print_header("MAIN MENU")
    print("1. Show Airline Flights")
    print("2. Track Exact Flight")
    print("3. Exit Application")
    print("-" * 72)


# ============================================================
# Application entry point
# ============================================================

def main() -> None:
    """Run the aviation tracking console dashboard."""
    try:
        require_flight_radar_api()
        api = FlightRadar24API()
    except Exception as error:
        print(f"Startup error: {error}")
        sys.exit(1)

    while True:
        print_main_menu()
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            show_airline_flights(api)
        elif choice == "2":
            track_exact_flight(api)
        elif choice == "3":
            clear_screen()
            print_header("EXIT")
            print("Thank you for using the Aviation Tracking System.")
            break
        else:
            print("\nInvalid option. Please select 1, 2, or 3.")
            time.sleep(1.5)


if __name__ == "__main__":
    main()
