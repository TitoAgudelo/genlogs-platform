from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Trip as TripModel
from db.seed import FALLBACK_CARRIERS


@dataclass(frozen=True)
class CarrierResult:
    carrier_name: str
    trucks_per_day: int


def search_carriers(origin: str, destination: str, db: Session | None = None) -> list[CarrierResult]:
    """Filter trips by origin/destination and return aggregated carrier results.

    If no exact route match is found, returns the fallback carriers
    (UPS Inc. 11 trucks/day, FedEx Corp 9 trucks/day).
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        rows = (
            db.query(TripModel)
            .filter(
                func.lower(TripModel.origin_city) == origin.strip().lower(),
                func.lower(TripModel.destination_city) == destination.strip().lower(),
            )
            .order_by(TripModel.trucks_per_day.desc())
            .all()
        )

        if rows:
            return [
                CarrierResult(
                    carrier_name=row.carrier_name,
                    trucks_per_day=row.trucks_per_day,
                )
                for row in rows
            ]

        # Fallback: return default carriers for unknown routes
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
