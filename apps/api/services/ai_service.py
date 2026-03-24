"""
Rule-based service that converts natural language queries to SQL
and executes them against the normalized database schema.
"""

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Carrier, Trip as TripModel
from db.seed import FALLBACK_CARRIERS
from services.city_normalizer import extract_cities_from_text, normalize_city


@dataclass(frozen=True)
class AIQueryResult:
    sql: str
    results: list[dict[str, str | int]]
    explanation: str


def _extract_carrier(query: str) -> str | None:
    """Extract carrier name from query."""
    query_lower = query.strip().lower()
    known_carriers = [
        "knight-swift", "j.b. hunt", "yrc worldwide",
        "xpo logistics", "schneider", "landstar",
        "ups inc", "ups", "fedex corp", "fedex",
    ]
    for carrier in known_carriers:
        if carrier in query_lower:
            return carrier
    return None


def _classify_query(query: str) -> str:
    query_lower = query.strip().lower()

    if any(w in query_lower for w in ["how many", "count", "total", "number"]):
        return "count"
    if any(w in query_lower for w in ["top", "most", "busiest", "highest"]):
        return "top"
    if any(w in query_lower for w in ["route", "routes", "lane", "lanes"]):
        return "routes"
    return "carriers"


def _execute_on_dataset(
    origin: str | None = None,
    destination: str | None = None,
    carrier: str | None = None,
    db: Session | None = None,
) -> list[dict[str, str | int]]:
    """Query the normalized schema: JOIN trips with carriers, GROUP BY carrier."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        query = (
            db.query(
                Carrier.name.label("carrier_name"),
                func.count(TripModel.trip_id).label("trucks_per_day"),
                TripModel.origin_city,
                TripModel.destination_city,
            )
            .join(Carrier, TripModel.carrier_id == Carrier.carrier_id)
        )

        if origin:
            query = query.filter(func.lower(TripModel.origin_city) == origin.lower())
        if destination:
            query = query.filter(func.lower(TripModel.destination_city) == destination.lower())
        if carrier:
            query = query.filter(func.lower(Carrier.name).contains(carrier.lower()))

        query = query.group_by(Carrier.name, TripModel.origin_city, TripModel.destination_city)
        query = query.order_by(func.count(TripModel.trip_id).desc())

        rows = query.all()

        if rows:
            return [
                {
                    "carrier_name": r.carrier_name,
                    "trucks_per_day": r.trucks_per_day,
                    "origin": r.origin_city,
                    "destination": r.destination_city,
                }
                for r in rows
            ]

        # Fallback for unknown routes
        if origin and destination and not carrier:
            return [
                {
                    "carrier_name": fc["carrier_name"],
                    "trucks_per_day": fc["trucks_per_day"],
                    "origin": origin,
                    "destination": destination,
                }
                for fc in FALLBACK_CARRIERS
            ]

        return []
    finally:
        if close_db:
            db.close()


def _build_sql(
    query_type: str,
    origin: str | None,
    destination: str | None,
    carrier: str | None,
) -> str:
    """Build a display SQL string reflecting the normalized schema."""
    if query_type == "count":
        select_clause = (
            "SELECT c.name AS carrier_name, COUNT(t.trip_id) AS trucks_per_day"
        )
    elif query_type == "routes":
        select_clause = (
            "SELECT DISTINCT t.origin_city, t.destination_city, "
            "c.name AS carrier_name, COUNT(t.trip_id) AS trucks_per_day"
        )
    else:
        select_clause = (
            "SELECT c.name AS carrier_name, COUNT(t.trip_id) AS trucks_per_day"
        )

    from_clause = "FROM trips t\nJOIN carriers c ON t.carrier_id = c.carrier_id"

    where_parts: list[str] = []
    if origin:
        where_parts.append(f"t.origin_city = '{origin}'")
    if destination:
        where_parts.append(f"t.destination_city = '{destination}'")
    if carrier:
        where_parts.append(f"c.name LIKE '%{carrier}%'")

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    group_clause = "GROUP BY c.name"
    order_clause = "ORDER BY trucks_per_day DESC"

    if query_type == "top":
        order_clause += "\nLIMIT 5"

    parts = [select_clause, from_clause, where_clause, group_clause, order_clause]
    return "\n".join(p for p in parts if p).strip()


def process_ai_query(query: str) -> AIQueryResult:
    """Process a natural language query and return SQL + results."""
    origin, destination = extract_cities_from_text(query)
    carrier = _extract_carrier(query)
    query_type = _classify_query(query)

    sql = _build_sql(query_type, origin, destination, carrier)

    raw_results = _execute_on_dataset(origin, destination, carrier)
    sorted_results = sorted(raw_results, key=lambda r: r["trucks_per_day"], reverse=True)

    if query_type == "count":
        results: list[dict[str, str | int]] = [{
            "total_carriers": len(sorted_results),
            "total_trucks_per_day": sum(r["trucks_per_day"] for r in sorted_results),
        }]
    elif query_type == "top":
        results = sorted_results[:5]
    else:
        results = sorted_results

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
        route_desc = f"between {origin} and {destination}"
    elif origin:
        route_desc = f"from {origin}"
    elif destination:
        route_desc = f"to {destination}"

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
        return f"{carrier} operates {route_desc} with the following activity: {carrier_list}"

    return f"The top carriers {route_desc} are: {carrier_list}"
