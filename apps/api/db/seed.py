"""Seed the database with initial trip data. Idempotent: skips if data exists."""

from db.database import Base, engine, SessionLocal
from db.models import Trip

SEED_DATA = [
    # New York -> Washington DC
    ("t001", "TRK-1001", "Knight-Swift Transport Services", "New York", "Washington DC", 10, "2026-03-15"),
    ("t002", "TRK-1002", "J.B. Hunt Transport Services Inc", "New York", "Washington DC", 7, "2026-03-15"),
    ("t003", "TRK-1003", "YRC Worldwide", "New York", "Washington DC", 5, "2026-03-15"),
    # San Francisco -> Los Angeles
    ("t004", "TRK-2001", "XPO Logistics", "San Francisco", "Los Angeles", 9, "2026-03-15"),
    ("t005", "TRK-2002", "Schneider", "San Francisco", "Los Angeles", 6, "2026-03-15"),
    ("t006", "TRK-2003", "Landstar Systems", "San Francisco", "Los Angeles", 2, "2026-03-15"),
]


# Fallback carriers for any route not explicitly in the database
FALLBACK_CARRIERS = [
    {"carrier_name": "UPS Inc.", "trucks_per_day": 11},
    {"carrier_name": "FedEx Corp", "trucks_per_day": 9},
]


def seed_database() -> None:
    """Create tables and seed data if not already present."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_count = db.query(Trip).count()
        if existing_count > 0:
            return

        for row in SEED_DATA:
            trip = Trip(
                trip_id=row[0],
                truck_id=row[1],
                carrier_name=row[2],
                origin_city=row[3],
                destination_city=row[4],
                trucks_per_day=row[5],
                trip_date=row[6],
            )
            db.add(trip)
        db.commit()
    finally:
        db.close()
