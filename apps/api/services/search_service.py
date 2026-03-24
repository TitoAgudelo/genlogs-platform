from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Carrier, Trip as TripModel
from db.seed import FALLBACK_CARRIERS
from services.city_normalizer import normalize_city


@dataclass(frozen=True)
class CarrierResult:
    carrier_name: str
    trucks_per_day: int


def search_carriers(origin: str, destination: str, db: Session | None = None) -> list[CarrierResult]:
    """Count trips per carrier on a route (trucks_per_day = number of trip records).

    If no exact route match is found, returns the fallback carriers.
    """
    normalized_origin = normalize_city(origin)
    normalized_destination = normalize_city(destination)

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        rows = (
            db.query(
                Carrier.name,
                func.count(TripModel.trip_id).label("trucks_per_day"),
            )
            .join(Carrier, TripModel.carrier_id == Carrier.carrier_id)
            .filter(
                func.lower(TripModel.origin_city) == normalized_origin.lower(),
                func.lower(TripModel.destination_city) == normalized_destination.lower(),
            )
            .group_by(Carrier.name)
            .order_by(func.count(TripModel.trip_id).desc())
            .all()
        )

        if rows:
            return [
                CarrierResult(carrier_name=name, trucks_per_day=count)
                for name, count in rows
            ]

        return [
            CarrierResult(
                carrier_name=fc["carrier_name"],
                trucks_per_day=fc["trucks_per_day"],
            )
            for fc in FALLBACK_CARRIERS
        ]
    finally:
        if close_db:
            db.close()
