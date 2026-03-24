"""
Trips data access layer backed by SQLite via SQLAlchemy.

Queries join trips → carriers to get carrier names, and count
trip rows per carrier to compute trucks_per_day.
"""

from dataclasses import dataclass

from sqlalchemy import func

from db.database import SessionLocal
from db.models import Carrier, Trip as TripModel


@dataclass(frozen=True)
class TripRecord:
    trip_id: str
    truck_id: str
    carrier_id: str
    carrier_name: str
    origin_city: str
    destination_city: str
    trip_date: str


@dataclass(frozen=True)
class CarrierVolume:
    carrier_name: str
    trucks_per_day: int


def get_all_trips() -> list[TripRecord]:
    db = SessionLocal()
    try:
        rows = (
            db.query(TripModel, Carrier.name)
            .join(Carrier, TripModel.carrier_id == Carrier.carrier_id)
            .all()
        )
        return [
            TripRecord(
                trip_id=trip.trip_id,
                truck_id=trip.truck_id,
                carrier_id=trip.carrier_id,
                carrier_name=name,
                origin_city=trip.origin_city,
                destination_city=trip.destination_city,
                trip_date=trip.trip_date,
            )
            for trip, name in rows
        ]
    finally:
        db.close()


def get_carrier_volumes(origin: str, destination: str) -> list[CarrierVolume]:
    """Count trips per carrier on a route (= trucks per day)."""
    db = SessionLocal()
    try:
        rows = (
            db.query(
                Carrier.name,
                func.count(TripModel.trip_id).label("trucks_per_day"),
            )
            .join(Carrier, TripModel.carrier_id == Carrier.carrier_id)
            .filter(
                func.lower(TripModel.origin_city) == origin.strip().lower(),
                func.lower(TripModel.destination_city) == destination.strip().lower(),
            )
            .group_by(Carrier.name)
            .order_by(func.count(TripModel.trip_id).desc())
            .all()
        )
        return [CarrierVolume(carrier_name=name, trucks_per_day=count) for name, count in rows]
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
