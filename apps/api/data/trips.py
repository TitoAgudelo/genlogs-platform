"""
Trips data access layer backed by SQLite via SQLAlchemy.

The Trip dataclass is kept for backward compatibility with services
that expect Trip objects rather than ORM model instances.
"""

from dataclasses import dataclass

from sqlalchemy import func

from db.database import SessionLocal
from db.models import Trip as TripModel


@dataclass(frozen=True)
class Trip:
    trip_id: str
    truck_id: str
    carrier_name: str
    origin_city: str
    destination_city: str
    trucks_per_day: int
    trip_date: str


def _model_to_dataclass(model: TripModel) -> Trip:
    return Trip(
        trip_id=model.trip_id,
        truck_id=model.truck_id,
        carrier_name=model.carrier_name,
        origin_city=model.origin_city,
        destination_city=model.destination_city,
        trucks_per_day=model.trucks_per_day,
        trip_date=model.trip_date,
    )


def get_all_trips() -> list[Trip]:
    db = SessionLocal()
    try:
        rows = db.query(TripModel).all()
        return [_model_to_dataclass(r) for r in rows]
    finally:
        db.close()


def get_unique_cities() -> list[str]:
    db = SessionLocal()
    try:
        origins = db.query(TripModel.origin_city).distinct().all()
        destinations = db.query(TripModel.destination_city).distinct().all()
        cities = {row[0] for row in origins} | {row[0] for row in destinations}
        return sorted(cities)
    finally:
        db.close()


def get_unique_routes() -> list[dict[str, str]]:
    db = SessionLocal()
    try:
        routes = (
            db.query(TripModel.origin_city, TripModel.destination_city)
            .distinct()
            .all()
        )
        return [
            {"origin": origin, "destination": destination}
            for origin, destination in sorted(routes)
        ]
    finally:
        db.close()
