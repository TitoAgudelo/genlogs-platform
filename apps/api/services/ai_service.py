"""
Rule-based service that converts natural language queries to SQL
and executes them against the trips dataset.
"""

import re
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Trip as TripModel
from db.seed import FALLBACK_CARRIERS
from data.trips import Trip


@dataclass(frozen=True)
class AIQueryResult:
    sql: str
    results: list[dict[str, str | int]]
    explanation: str


# Known city names for extraction
KNOWN_CITIES = {
    "new york", "washington dc", "san francisco", "los angeles",
    "chicago", "detroit", "dallas", "houston", "miami", "atlanta",
    "seattle", "portland", "boston", "philadelphia", "denver", "salt lake city",
}


def _normalize(text: str) -> str:
    return text.strip().lower()


def _extract_cities(query: str) -> tuple[str | None, str | None]:
    """Extract origin and destination cities from a natural language query, preserving order of appearance."""
    query_lower = _normalize(query)

    # Find all cities with their position in the query
    found: list[tuple[int, str]] = []
    for city in sorted(KNOWN_CITIES, key=len, reverse=True):
        pos = query_lower.find(city)
        if pos != -1:
            found.append((pos, city))
            # Replace to avoid substring re-matching
            query_lower = query_lower[:pos] + ("_" * len(city)) + query_lower[pos + len(city):]

    # Sort by position to respect query order
    found.sort(key=lambda x: x[0])

    if len(found) >= 2:
        return found[0][1], found[1][1]
    if len(found) == 1:
        return found[0][1], None
    return None, None


def _extract_carrier(query: str) -> str | None:
    """Extract carrier name from query."""
    query_lower = _normalize(query)
    known_carriers = [
        "ups", "fedex", "xpo logistics", "schneider",
        "knight-swift", "j.b. hunt", "yrc worldwide",
        "landstar", "ups inc", "fedex corp",
    ]
    for carrier in known_carriers:
        if carrier in query_lower:
            return carrier
    return None


def _title_case_city(city: str) -> str:
    """Convert city name to proper title case."""
    special = {"dc": "DC"}
    words = city.split()
    return " ".join(special.get(w, w.capitalize()) for w in words)


def _execute_on_dataset(
    origin: str | None = None,
    destination: str | None = None,
    carrier: str | None = None,
    db: Session | None = None,
) -> list[Trip]:
    """Filter trips dataset based on criteria using the database.

    Returns fallback carriers when an origin+destination pair has no DB matches.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        query = db.query(TripModel)

        if origin:
            query = query.filter(func.lower(TripModel.origin_city) == _normalize(origin))
        if destination:
            query = query.filter(func.lower(TripModel.destination_city) == _normalize(destination))
        if carrier:
            query = query.filter(func.lower(TripModel.carrier_name) == _normalize(carrier))

        rows = query.all()

        if rows:
            return [
                Trip(
                    trip_id=r.trip_id,
                    truck_id=r.truck_id,
                    carrier_name=r.carrier_name,
                    origin_city=r.origin_city,
                    destination_city=r.destination_city,
                    trucks_per_day=r.trucks_per_day,
                    trip_date=r.trip_date,
                )
                for r in rows
            ]

        # Fallback for unknown routes (only when both origin and destination given)
        if origin and destination and not carrier:
            return [
                Trip(
                    trip_id=f"fallback-{i}",
                    truck_id=f"TRK-FB-{i}",
                    carrier_name=fc["carrier_name"],
                    origin_city=_title_case_city(origin),
                    destination_city=_title_case_city(destination),
                    trucks_per_day=fc["trucks_per_day"],
                    trip_date="2026-03-15",
                )
                for i, fc in enumerate(FALLBACK_CARRIERS)
            ]

        return []
    finally:
        if close_db:
            db.close()


def _classify_query(query: str) -> str:
    """Classify the type of query."""
    query_lower = _normalize(query)

    if any(w in query_lower for w in ["how many", "count", "total", "number"]):
        return "count"
    if any(w in query_lower for w in ["top", "most", "busiest", "highest"]):
        return "top"
    if any(w in query_lower for w in ["route", "routes", "lane", "lanes"]):
        return "routes"
    if any(w in query_lower for w in ["carrier", "carriers", "operate", "which"]):
        return "carriers"
    return "carriers"


def process_ai_query(query: str) -> AIQueryResult:
    """Process a natural language query and return SQL + results."""
    origin, destination = _extract_cities(query)
    carrier = _extract_carrier(query)
    query_type = _classify_query(query)

    # Build SQL
    select_clause = "SELECT carrier_name, trucks_per_day"
    from_clause = "FROM trips"
    where_parts: list[str] = []
    order_clause = "ORDER BY trucks_per_day DESC"

    if origin:
        where_parts.append(f"origin_city = '{_title_case_city(origin)}'")
    if destination:
        where_parts.append(f"destination_city = '{_title_case_city(destination)}'")
    if carrier:
        where_parts.append(f"carrier_name = '{_title_case_city(carrier)}'")

    if query_type == "count":
        select_clause = "SELECT COUNT(*) as total_carriers, SUM(trucks_per_day) as total_trucks"
    elif query_type == "routes":
        select_clause = "SELECT DISTINCT origin_city, destination_city, carrier_name, trucks_per_day"
    elif query_type == "top":
        order_clause = "ORDER BY trucks_per_day DESC\nLIMIT 5"

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    sql = f"{select_clause}\n{from_clause}\n{where_clause}\n{order_clause}".strip()

    # Execute
    trips = _execute_on_dataset(origin, destination, carrier)
    trips_sorted = sorted(trips, key=lambda t: t.trucks_per_day, reverse=True)

    if query_type == "count":
        results: list[dict[str, str | int]] = [{
            "total_carriers": len(trips_sorted),
            "total_trucks_per_day": sum(t.trucks_per_day for t in trips_sorted),
        }]
    elif query_type == "top":
        results = [
            {
                "carrier_name": t.carrier_name,
                "trucks_per_day": t.trucks_per_day,
                "origin": t.origin_city,
                "destination": t.destination_city,
            }
            for t in trips_sorted[:5]
        ]
    else:
        results = [
            {
                "carrier_name": t.carrier_name,
                "trucks_per_day": t.trucks_per_day,
                "origin": t.origin_city,
                "destination": t.destination_city,
            }
            for t in trips_sorted
        ]

    # Generate explanation
    explanation = _generate_explanation(query_type, origin, destination, carrier, results)

    return AIQueryResult(sql=sql, results=results, explanation=explanation)


def _generate_explanation(
    query_type: str,
    origin: str | None,
    destination: str | None,
    carrier: str | None,
    results: list[dict[str, str | int]],
) -> str:
    if not results:
        return "No matching data found for your query. Try a different route or carrier."

    route_desc = ""
    if origin and destination:
        route_desc = f"between {_title_case_city(origin)} and {_title_case_city(destination)}"
    elif origin:
        route_desc = f"from {_title_case_city(origin)}"
    elif destination:
        route_desc = f"to {_title_case_city(destination)}"

    if query_type == "count":
        total = results[0]
        return (
            f"There are {total['total_carriers']} carriers operating {route_desc} "
            f"with a combined {total['total_trucks_per_day']} trucks per day."
        )

    carrier_list = ", ".join(
        f"{r['carrier_name']} ({r['trucks_per_day']} trucks/day)"
        for r in results[:5]
    )

    if carrier:
        return f"{_title_case_city(carrier)} operates {route_desc} with the following activity: {carrier_list}"

    return f"The top carriers {route_desc} are: {carrier_list}"
